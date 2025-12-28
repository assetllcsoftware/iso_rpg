"""Magic processor - handles spellcasting, projectiles, and effects."""

import esper
import math
from typing import Optional

from ..components import (
    Position, Velocity, Health, Mana, Facing, Direction,
    SpellBook, CastIntent, Casting, Projectile, AreaEffect,
    StatusEffect, StatusEffects, ActiveAbility, LeapingAbility,
    GlobalCooldown,
    Attributes, SkillLevels, SkillXP,
    Animation, AnimationState, VisualEffect, RenderOffset,
    PartyMember, Enemy, Downed, Dead,
    CollisionRadius, Resistances
)
from ..components.rendering import DamageNumber
from ..components.tags import ToRemove
from ...core.events import EventBus, Event, EventType
from ...core.formulas import (
    calculate_spell_damage, calculate_heal_amount, calculate_elemental_damage,
    distance, XP_SPELL_HIT, XP_HEAL_CAST
)
from ...data.loader import data_loader


class MagicProcessor(esper.Processor):
    """Processes magic for ALL entities (players, allies, and enemies).
    
    This is THE magic update path. Everyone uses this.
    """
    
    # Map spell animation names to AnimationState
    ANIMATION_MAP = {
        'spin': AnimationState.SPIN,
        'leap': AnimationState.LEAP,
        'heavy': AnimationState.HEAVY,
        'bash': AnimationState.BASH,
        'channel': AnimationState.CHANNEL,
        'cast': AnimationState.CAST,
        'attack': AnimationState.ATTACK,
    }
    
    # Default GCD for spells without animation_duration
    DEFAULT_GCD = 0.5
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.dungeon = None
        
        # Subscribe to cast requests
        event_bus.subscribe(EventType.SPELL_CAST_REQUESTED, self._on_cast_requested)
    
    def _get_animation_state(self, spell_data: dict, default: AnimationState = AnimationState.ATTACK) -> AnimationState:
        """Get the animation state for a spell from its data."""
        anim_name = spell_data.get('animation', '')
        return self.ANIMATION_MAP.get(anim_name, default)
    
    def set_dungeon(self, dungeon):
        """Set dungeon reference for line-of-sight checks."""
        self.dungeon = dungeon
    
    def _on_cast_requested(self, event: Event):
        """Handle spell cast request from input."""
        caster = event.data.get("caster", -1)
        slot = event.data.get("slot", 0)
        target_id = event.data.get("target_id", -1)
        target_x = event.data.get("target_x", 0.0)
        target_y = event.data.get("target_y", 0.0)
        
        if not esper.entity_exists(caster):
            return
        
        # Check global cooldown - can't cast if on GCD
        if esper.has_component(caster, GlobalCooldown):
            gcd = esper.component_for_entity(caster, GlobalCooldown)
            if not gcd.ready:
                return  # Still on GCD, can't cast yet
        
        # Get spellbook
        if not esper.has_component(caster, SpellBook):
            return
        
        spellbook = esper.component_for_entity(caster, SpellBook)
        spells = list(spellbook.known_spells)
        
        if slot >= len(spells):
            return
        
        spell_id = spells[slot]
        
        # Set cast intent
        if esper.has_component(caster, CastIntent):
            intent = esper.component_for_entity(caster, CastIntent)
            intent.spell_id = spell_id
            intent.target_id = target_id
            intent.target_x = target_x
            intent.target_y = target_y
        else:
            esper.add_component(caster, CastIntent(
                spell_id=spell_id,
                target_id=target_id,
                target_x=target_x,
                target_y=target_y
            ))
    
    def process(self, dt: float):
        """Process magic each frame."""
        from ...core.perf_monitor import perf
        perf.mark("MagicProcessor")
        
        # Update spell cooldowns
        self._update_cooldowns(dt)
        
        # Process cast intents
        self._process_cast_intents(dt)
        
        # Process active casts
        self._process_casting(dt)
        
        # Process active multi-hit abilities (like whirlwind)
        self._process_active_abilities(dt)
        
        # Process leaping abilities (like leap strike)
        self._process_leaping_abilities(dt)
        
        # Update projectiles
        self._update_projectiles(dt)
        
        # Update area effects
        self._update_area_effects(dt)
        
        # Update status effects
        self._update_status_effects(dt)
        
        perf.measure("MagicProcessor")
    
    def _process_active_abilities(self, dt: float):
        """Process ongoing multi-hit abilities like whirlwind."""
        for ent, (pos, ability) in esper.get_components(Position, ActiveAbility):
            ability.next_hit_timer -= dt
            ability.total_duration -= dt
            
            # Time for next hit?
            if ability.next_hit_timer <= 0 and ability.hits_remaining > 0:
                ability.hits_remaining -= 1
                ability.next_hit_timer = ability.hit_interval
                
                # Deal damage to all enemies in radius
                is_caster_party = esper.has_component(ent, PartyMember)
                
                for target_ent, (target_pos, health) in esper.get_components(Position, Health):
                    if target_ent == ent:
                        continue
                    
                    is_target_party = esper.has_component(target_ent, PartyMember)
                    if is_caster_party == is_target_party:
                        continue  # Don't hurt allies
                    
                    if esper.has_component(target_ent, Dead):
                        continue
                    
                    dist = distance(pos.x, pos.y, target_pos.x, target_pos.y)
                    if dist > ability.radius:
                        continue
                    
                    # Apply damage
                    health.current = max(0, health.current - ability.damage_per_hit)
                    
                    # Create damage number (red if hitting party member)
                    is_player_dmg = esper.has_component(target_ent, PartyMember)
                    esper.create_entity(
                        Position(x=target_pos.x, y=target_pos.y - 0.5),
                        DamageNumber(value=ability.damage_per_hit, is_player_damage=is_player_dmg)
                    )
                    
                    self.event_bus.emit(Event(EventType.DAMAGE_DEALT, {
                        "attacker": ent,
                        "target": target_ent,
                        "amount": ability.damage_per_hit,
                        "damage_type": "physical"
                    }))
            
            # Ability finished?
            if ability.hits_remaining <= 0 or ability.total_duration <= 0:
                esper.remove_component(ent, ActiveAbility)
    
    def _process_leaping_abilities(self, dt: float):
        """Process leap attacks - physically move the hero through the air."""
        import math
        
        for ent, (pos, leap) in esper.get_components(Position, LeapingAbility):
            leap.elapsed += dt
            progress = min(1.0, leap.elapsed / leap.duration)
            
            # Smooth easing - fast start, slow at apex, fast landing
            # Use sine curve for natural arc feel
            ease = math.sin(progress * math.pi / 2) if progress < 0.5 else 1.0 - math.sin((1 - progress) * math.pi / 2) * 0.3
            
            # Calculate current position along the path
            pos.x = leap.start_x + (leap.target_x - leap.start_x) * ease
            pos.y = leap.start_y + (leap.target_y - leap.start_y) * ease
            
            # Calculate height in arc (parabolic - high in middle, zero at start/end)
            # Max height at progress=0.5, scales with leap distance
            base_height = 80  # Base max height in pixels
            dist = math.sqrt((leap.target_x - leap.start_x)**2 + (leap.target_y - leap.start_y)**2)
            height_mult = min(2.0, 0.5 + dist * 0.25)  # Longer leaps go higher
            arc_height = math.sin(progress * math.pi) * base_height * height_mult
            
            # Apply visual height offset (negative Y = up on screen)
            # Baseline offset is -16 for sprite centering, we add leap height on top
            baseline_offset = -16
            if esper.has_component(ent, RenderOffset):
                offset = esper.component_for_entity(ent, RenderOffset)
                offset.y = baseline_offset - arc_height
            else:
                esper.add_component(ent, RenderOffset(x=0, y=baseline_offset - arc_height))
            
            # Update facing direction toward target
            if esper.has_component(ent, Facing):
                facing = esper.component_for_entity(ent, Facing)
                dx = leap.target_x - pos.x
                dy = leap.target_y - pos.y
                if abs(dx) > abs(dy):
                    facing.direction = Direction.RIGHT if dx > 0 else Direction.LEFT
                else:
                    facing.direction = Direction.DOWN if dy > 0 else Direction.UP
            
            # Landing! (progress >= 1.0 and haven't landed yet)
            if progress >= 1.0 and not leap.has_landed:
                leap.has_landed = True
                
                # Snap to final position - but validate it's walkable first!
                final_x, final_y = leap.target_x, leap.target_y
                if self.dungeon:
                    if not self.dungeon.is_walkable(int(final_x), int(final_y)):
                        # Target became invalid - use clamp_position to find nearest valid
                        final_x, final_y = self.dungeon.clamp_position(final_x, final_y)
                    else:
                        # Snap to tile center if too close to edges (prevents getting stuck)
                        tile_x, tile_y = int(final_x), int(final_y)
                        frac_x = final_x - tile_x
                        frac_y = final_y - tile_y
                        
                        # If within 0.2 of any edge, snap to center
                        if frac_x < 0.2 or frac_x > 0.8 or frac_y < 0.2 or frac_y > 0.8:
                            # Check if adjacent tile in that direction is a wall
                            needs_snap = False
                            if frac_x < 0.2 and not self.dungeon.is_walkable(tile_x - 1, tile_y):
                                needs_snap = True
                            if frac_x > 0.8 and not self.dungeon.is_walkable(tile_x + 1, tile_y):
                                needs_snap = True
                            if frac_y < 0.2 and not self.dungeon.is_walkable(tile_x, tile_y - 1):
                                needs_snap = True
                            if frac_y > 0.8 and not self.dungeon.is_walkable(tile_x, tile_y + 1):
                                needs_snap = True
                            
                            if needs_snap:
                                final_x = tile_x + 0.5
                                final_y = tile_y + 0.5
                
                pos.x = final_x
                pos.y = final_y
                
                # Deal damage to main target
                if leap.target_id >= 0 and esper.entity_exists(leap.target_id):
                    if esper.has_component(leap.target_id, Health):
                        health = esper.component_for_entity(leap.target_id, Health)
                        health.current = max(0, health.current - leap.damage)
                        
                        # Damage number (red if hitting party member)
                        if esper.has_component(leap.target_id, Position):
                            tpos = esper.component_for_entity(leap.target_id, Position)
                            is_player_dmg = esper.has_component(leap.target_id, PartyMember)
                            esper.create_entity(
                                Position(x=tpos.x, y=tpos.y - 0.5),
                                DamageNumber(value=leap.damage, is_player_damage=is_player_dmg)
                            )
                        
                        # Stun
                        if leap.stun_duration > 0:
                            stun_effect = StatusEffect(
                                effect_type="stun",
                                duration=leap.stun_duration,
                                source_id=ent
                            )
                            if esper.has_component(leap.target_id, StatusEffects):
                                effects = esper.component_for_entity(leap.target_id, StatusEffects)
                                effects.add(stun_effect)
                            else:
                                esper.add_component(leap.target_id, StatusEffects(effects=[stun_effect]))
                        
                        self.event_bus.emit(Event(EventType.DAMAGE_DEALT, {
                            "attacker": ent,
                            "target": leap.target_id,
                            "amount": leap.damage,
                            "damage_type": "physical"
                        }))
                
                # AoE damage on impact
                if leap.aoe_radius > 0 and leap.aoe_damage > 0:
                    self._apply_aoe_damage_at(ent, pos.x, pos.y, leap.aoe_radius, leap.aoe_damage, [leap.target_id])
            
            # Remove leap component after landing + small delay for animation
            if leap.has_landed and leap.elapsed >= leap.duration + 0.3:
                esper.remove_component(ent, LeapingAbility)
                # Reset render offset to baseline (entities start with y=-16 for centering)
                if esper.has_component(ent, RenderOffset):
                    offset = esper.component_for_entity(ent, RenderOffset)
                    offset.y = -16  # Baseline offset for sprite centering
    
    def _find_nearest_enemy(self, caster: int, caster_pos, max_range: float) -> int:
        """Find the nearest enemy within range and line of sight."""
        is_caster_party = esper.has_component(caster, PartyMember)
        
        nearest = -1
        nearest_dist = max_range + 1
        
        for ent, (pos, health) in esper.get_components(Position, Health):
            if ent == caster:
                continue
            
            # Skip dead/downed
            if esper.has_component(ent, Dead) or esper.has_component(ent, Downed):
                continue
            
            # Must be opposite faction
            is_target_party = esper.has_component(ent, PartyMember)
            if is_caster_party == is_target_party:
                continue  # Same faction, skip
            
            dist = distance(caster_pos.x, caster_pos.y, pos.x, pos.y)
            if dist <= max_range and dist < nearest_dist:
                # Check line of sight
                if self.dungeon and not self.dungeon.has_line_of_sight(
                    caster_pos.x, caster_pos.y, pos.x, pos.y
                ):
                    continue  # Can't see through walls
                
                nearest_dist = dist
                nearest = ent
        
        return nearest
    
    def _find_nearest_ally(self, caster: int, caster_pos, max_range: float) -> int:
        """Find the nearest ally within range (for heals)."""
        is_caster_party = esper.has_component(caster, PartyMember)
        
        # Default to self for ally-targeting spells
        lowest_health_ent = caster
        lowest_health_pct = 1.0
        
        for ent, (pos, health) in esper.get_components(Position, Health):
            # Skip dead/downed
            if esper.has_component(ent, Dead) or esper.has_component(ent, Downed):
                continue
            
            # Must be same faction
            is_target_party = esper.has_component(ent, PartyMember)
            if is_caster_party != is_target_party:
                continue  # Different faction, skip
            
            dist = distance(caster_pos.x, caster_pos.y, pos.x, pos.y)
            if dist <= max_range:
                # Prefer lowest health ally
                health_pct = health.percent
                if health_pct < lowest_health_pct:
                    lowest_health_pct = health_pct
                    lowest_health_ent = ent
        
        return lowest_health_ent
    
    def _update_cooldowns(self, dt: float):
        """Tick down spell cooldowns and global cooldowns."""
        for ent, (spellbook,) in esper.get_components(SpellBook):
            spellbook.update_cooldowns(dt)
        
        # Update global cooldowns
        for ent, (gcd,) in esper.get_components(GlobalCooldown):
            if gcd.remaining > 0:
                gcd.remaining -= dt
    
    def _process_cast_intents(self, dt: float):
        """Process cast intents and start casting."""
        for ent, (pos, intent, spellbook, mana) in esper.get_components(
            Position, CastIntent, SpellBook, Mana
        ):
            spell_id = intent.spell_id
            if not spell_id:
                esper.remove_component(ent, CastIntent)
                continue
            
            # Check if can cast
            if not spellbook.can_cast(spell_id):
                esper.remove_component(ent, CastIntent)
                continue
            
            # Get spell data
            spell_data = data_loader.get_spell(spell_id)
            if not spell_data:
                esper.remove_component(ent, CastIntent)
                continue
            
            # Check mana
            mana_cost = spell_data.get("mana_cost", 10)
            if mana.current < mana_cost:
                esper.remove_component(ent, CastIntent)
                continue
            
            # Check range and find target if needed
            spell_range = spell_data.get("range", 8.0)
            targeting = spell_data.get("targeting", "enemy")
            
            # Auto-find target if not specified
            if intent.target_id < 0 and targeting == "enemy":
                # Find nearest enemy in range
                intent.target_id = self._find_nearest_enemy(ent, pos, spell_range)
            elif intent.target_id < 0 and targeting == "ally":
                # Find nearest ally in range (for heals)
                intent.target_id = self._find_nearest_ally(ent, pos, spell_range)
            
            if targeting == "enemy" or targeting == "ally":
                if intent.target_id >= 0:
                    if not esper.entity_exists(intent.target_id):
                        esper.remove_component(ent, CastIntent)
                        continue
                    
                    target_pos = esper.component_for_entity(intent.target_id, Position)
                    dist = distance(pos.x, pos.y, target_pos.x, target_pos.y)
                    
                    if dist > spell_range:
                        # Out of range - skip for now
                        esper.remove_component(ent, CastIntent)
                        continue
                    
                    # Check line of sight - can't cast through walls
                    if self.dungeon and not self.dungeon.has_line_of_sight(
                        pos.x, pos.y, target_pos.x, target_pos.y
                    ):
                        esper.remove_component(ent, CastIntent)
                        continue
                    
                    # Update target position for projectile aiming
                    intent.target_x = target_pos.x
                    intent.target_y = target_pos.y
                else:
                    # No valid target found, use ground targeting
                    pass
            elif targeting == "ground":
                dist = distance(pos.x, pos.y, intent.target_x, intent.target_y)
                if dist > spell_range:
                    esper.remove_component(ent, CastIntent)
                    continue
            elif targeting == "self":
                # Self-centered spells always work
                intent.target_x = pos.x
                intent.target_y = pos.y
            
            # Consume mana
            mana.current -= mana_cost
            
            # Start cooldown
            cooldown = spell_data.get("cooldown", 1.0)
            spellbook.start_cooldown(spell_id, cooldown)
            
            # Set global cooldown based on animation duration (prevents spam)
            anim_duration = spell_data.get("animation_duration", 0.5)
            if esper.has_component(ent, GlobalCooldown):
                gcd = esper.component_for_entity(ent, GlobalCooldown)
                gcd.remaining = anim_duration
            else:
                esper.add_component(ent, GlobalCooldown(remaining=anim_duration))
            
            # Instant cast or channeled?
            cast_time = spell_data.get("cast_time", 0.0)
            
            if cast_time <= 0:
                # Instant cast
                self._execute_spell(ent, spell_id, spell_data, intent)
            else:
                # Start casting
                esper.add_component(ent, Casting(
                    spell_id=spell_id,
                    target_id=intent.target_id,
                    target_x=intent.target_x,
                    target_y=intent.target_y,
                    cast_time=cast_time
                ))
                
                if esper.has_component(ent, Animation):
                    anim = esper.component_for_entity(ent, Animation)
                    # Use spell-specific animation if defined
                    anim.state = self._get_animation_state(spell_data, AnimationState.CAST)
                    anim.frame = 0
            
            # Clear intent
            esper.remove_component(ent, CastIntent)
    
    def _process_casting(self, dt: float):
        """Update active spell casts."""
        for ent, (pos, casting) in esper.get_components(Position, Casting):
            casting.cast_time -= dt
            
            if casting.cast_time <= 0:
                spell_data = data_loader.get_spell(casting.spell_id)
                if spell_data:
                    self._execute_spell(ent, casting.spell_id, spell_data, casting)
                
                esper.remove_component(ent, Casting)
    
    def _execute_spell(self, caster: int, spell_id: str, spell_data: dict, intent):
        """Execute a spell effect."""
        caster_pos = esper.component_for_entity(caster, Position)
        spell_type = spell_data.get("type", "projectile")
        
        if spell_type == "projectile":
            self._create_projectile(caster, spell_id, spell_data, intent, caster_pos)
        
        elif spell_type == "instant":
            # Check if this is a melee ability with damage multiplier
            if spell_data.get("damage_multiplier", 0) > 0:
                self._apply_melee_ability(caster, spell_data, intent)
            else:
                self._apply_instant_effect(caster, spell_data, intent)
        
        elif spell_type == "aoe":
            # AoE can also have damage_multiplier for melee abilities like whirlwind
            if spell_data.get("targeting") == "self":
                self._apply_melee_aoe(caster, spell_data, intent, caster_pos)
            else:
                self._create_aoe(caster, spell_id, spell_data, intent, caster_pos)
        
        elif spell_type == "chain":
            self._apply_chain_effect(caster, spell_data, intent)
        
        elif spell_type == "buff":
            self._apply_buff(caster, spell_data, intent)
        
        elif spell_type == "cone":
            self._apply_cone_attack(caster, spell_data, intent, caster_pos)
        
        elif spell_type == "party_heal":
            self._apply_party_heal(caster, spell_data)
        
        # Update facing
        if intent.target_id >= 0 and esper.entity_exists(intent.target_id):
            target_pos = esper.component_for_entity(intent.target_id, Position)
            dx = target_pos.x - caster_pos.x
            dy = target_pos.y - caster_pos.y
        else:
            dx = intent.target_x - caster_pos.x
            dy = intent.target_y - caster_pos.y
        
        if esper.has_component(caster, Facing):
            facing = esper.component_for_entity(caster, Facing)
            if abs(dx) > abs(dy):
                facing.direction = Direction.RIGHT if dx > 0 else Direction.LEFT
            else:
                facing.direction = Direction.DOWN if dy > 0 else Direction.UP
        
        # Award XP
        school = spell_data.get("school", "combat_magic")
        if esper.has_component(caster, SkillXP):
            skill_xp = esper.component_for_entity(caster, SkillXP)
            skill_xp.add(school, XP_SPELL_HIT)
        
        # Create cast visual effect at caster
        damage_type = spell_data.get("damage_type", "fire")
        school = spell_data.get("school", "combat_magic")
        
        # Choose effect type based on school/damage
        if "nature" in school or spell_data.get("heal_amount", 0) > 0 or spell_data.get("heal", 0) > 0:
            effect_type = "heal_cast"
        else:
            effect_type = f"cast_{damage_type}"
        
        esper.create_entity(
            Position(x=caster_pos.x, y=caster_pos.y - 0.3),
            VisualEffect(effect_type=effect_type, timer=0.4)
        )
        
        self.event_bus.emit(Event(EventType.SPELL_CAST, {
            "caster": caster,
            "spell_id": spell_id
        }))
    
    def _create_projectile(self, caster: int, spell_id: str, spell_data: dict, intent, caster_pos):
        """Create a spell projectile."""
        damage = spell_data.get("damage", 20)
        damage_type = spell_data.get("damage_type", "fire")
        speed = spell_data.get("projectile_speed", 12.0)
        
        # Calculate scaled damage
        intelligence = 10
        skill_level = 1
        if esper.has_component(caster, Attributes):
            intelligence = esper.component_for_entity(caster, Attributes).intelligence
        if esper.has_component(caster, SkillLevels):
            skills = esper.component_for_entity(caster, SkillLevels)
            school = spell_data.get("school", "combat_magic")
            skill_level = skills.get(school)
        
        scaled_damage = calculate_spell_damage(damage, intelligence, skill_level)
        
        # Determine target position
        if intent.target_id >= 0 and esper.entity_exists(intent.target_id):
            target_pos = esper.component_for_entity(intent.target_id, Position)
            tx, ty = target_pos.x, target_pos.y
        else:
            tx, ty = intent.target_x, intent.target_y
        
        # Calculate direction
        dx = tx - caster_pos.x
        dy = ty - caster_pos.y
        dist = max(0.1, distance(caster_pos.x, caster_pos.y, tx, ty))
        
        esper.create_entity(
            Position(x=caster_pos.x, y=caster_pos.y),
            Velocity(dx=(dx / dist) * speed, dy=(dy / dist) * speed),
            Projectile(
                spell_id=spell_id,
                caster_id=caster,
                target_id=intent.target_id,
                target_x=tx,
                target_y=ty,
                speed=speed,
                damage=scaled_damage,
                damage_type=damage_type
            ),
            CollisionRadius(radius=0.3),
            VisualEffect(effect_type=f"projectile_{damage_type}")
        )
        
        self.event_bus.emit(Event(EventType.PROJECTILE_CREATED, {
            "caster": caster,
            "spell_id": spell_id
        }))
    
    def _apply_instant_effect(self, caster: int, spell_data: dict, intent):
        """Apply instant spell effect (heal, damage, etc.)."""
        target_id = intent.target_id
        if target_id < 0 or not esper.entity_exists(target_id):
            return
        
        # Healing spell (check both heal and heal_amount for compatibility)
        heal_value = spell_data.get("heal", 0) or spell_data.get("heal_amount", 0)
        if heal_value > 0:
            heal_amount = heal_value
            
            # Scale healing
            intelligence = 10
            skill_level = 1
            if esper.has_component(caster, Attributes):
                intelligence = esper.component_for_entity(caster, Attributes).intelligence
            if esper.has_component(caster, SkillLevels):
                skills = esper.component_for_entity(caster, SkillLevels)
                skill_level = skills.get("nature_magic")
            
            scaled_heal = calculate_heal_amount(heal_amount, intelligence, skill_level)
            
            if esper.has_component(target_id, Health):
                health = esper.component_for_entity(target_id, Health)
                health.current = min(health.maximum, health.current + scaled_heal)
            
            # Create heal number
            if esper.has_component(target_id, Position):
                pos = esper.component_for_entity(target_id, Position)
                esper.create_entity(
                    Position(x=pos.x, y=pos.y - 0.5),
                    DamageNumber(value=scaled_heal, is_heal=True)
                )
            
            self.event_bus.emit(Event(EventType.HEALTH_RESTORED, {
                "healer": caster,
                "target": target_id,
                "amount": scaled_heal
            }))
        
        # Damage spell
        if spell_data.get("damage", 0) > 0:
            self._apply_spell_damage(caster, target_id, spell_data)
    
    def _apply_party_heal(self, caster: int, spell_data: dict):
        """Heal all party members."""
        heal_value = spell_data.get("heal", 0) or spell_data.get("heal_amount", 0)
        if heal_value <= 0:
            return
        
        # Get caster stats for scaling
        intelligence = 10
        skill_level = 1
        if esper.has_component(caster, Attributes):
            intelligence = esper.component_for_entity(caster, Attributes).intelligence
        if esper.has_component(caster, SkillLevels):
            skills = esper.component_for_entity(caster, SkillLevels)
            skill_level = skills.get("nature_magic")
        
        scaled_heal = calculate_heal_amount(heal_value, intelligence, skill_level)
        
        # Heal all party members
        for ent, (member, health) in esper.get_components(PartyMember, Health):
            old_health = health.current
            health.current = min(health.maximum, health.current + scaled_heal)
            actual_heal = health.current - old_health
            
            if actual_heal > 0:
                # Create heal number
                if esper.has_component(ent, Position):
                    pos = esper.component_for_entity(ent, Position)
                    esper.create_entity(
                        Position(x=pos.x, y=pos.y - 0.5),
                        DamageNumber(value=actual_heal, is_heal=True)
                    )
                
                self.event_bus.emit(Event(EventType.HEALTH_RESTORED, {
                    "healer": caster,
                    "target": ent,
                    "amount": actual_heal
                }))
        
        # Award XP for healing
        if esper.has_component(caster, SkillXP):
            skill_xp = esper.component_for_entity(caster, SkillXP)
            skill_xp.add("nature_magic", XP_HEAL_CAST)
    
    def _create_aoe(self, caster: int, spell_id: str, spell_data: dict, intent, caster_pos):
        """Create an area of effect."""
        radius = spell_data.get("radius", 3.0)
        duration = spell_data.get("duration", 0.0)
        damage = spell_data.get("damage", 20)
        damage_type = spell_data.get("damage_type", "fire")
        
        # Target position
        if intent.target_id >= 0 and esper.entity_exists(intent.target_id):
            target_pos = esper.component_for_entity(intent.target_id, Position)
            tx, ty = target_pos.x, target_pos.y
        else:
            tx, ty = intent.target_x, intent.target_y
        
        # Instant AoE damage
        self._apply_aoe_damage(caster, tx, ty, radius, damage, damage_type, spell_data)
        
        # Create persistent effect if has duration
        if duration > 0:
            tick_damage = spell_data.get("tick_damage", damage // 2)
            tick_interval = spell_data.get("tick_interval", 0.5)
            
            esper.create_entity(
                Position(x=tx, y=ty),
                AreaEffect(
                    spell_id=spell_id,
                    caster_id=caster,
                    radius=radius,
                    duration=duration,
                    tick_interval=tick_interval,
                    next_tick=tick_interval,
                    damage_per_tick=tick_damage,
                    damage_type=damage_type
                ),
                VisualEffect(effect_type=f"aoe_{damage_type}", timer=duration)
            )
    
    def _apply_aoe_damage(self, caster: int, cx: float, cy: float, radius: float,
                          damage: int, damage_type: str, spell_data: dict):
        """Apply damage to all valid targets in area."""
        is_caster_party = esper.has_component(caster, PartyMember)
        
        for ent, (pos, health) in esper.get_components(Position, Health):
            if ent == caster:
                continue
            
            # Check if valid target
            is_target_party = esper.has_component(ent, PartyMember)
            if is_caster_party == is_target_party:
                continue  # Don't hurt allies
            
            if esper.has_component(ent, Dead):
                continue
            
            # Check range
            dist = distance(pos.x, pos.y, cx, cy)
            if dist > radius:
                continue
            
            # Apply damage
            self._apply_spell_damage(caster, ent, spell_data)
    
    def _apply_chain_effect(self, caster: int, spell_data: dict, intent):
        """Apply chain lightning effect."""
        targets = spell_data.get("targets", 3)
        damage = spell_data.get("damage", 25)
        chain_range = spell_data.get("chain_range", 5.0)
        damage_falloff = spell_data.get("damage_falloff", 0.8)
        
        is_caster_party = esper.has_component(caster, PartyMember)
        hit_entities = set()
        current_target = intent.target_id
        current_damage = damage
        
        for _ in range(targets):
            if current_target < 0 or not esper.entity_exists(current_target):
                break
            
            if current_target in hit_entities:
                break
            
            hit_entities.add(current_target)
            
            # Apply damage
            modified_spell_data = dict(spell_data)
            modified_spell_data["damage"] = current_damage
            self._apply_spell_damage(caster, current_target, modified_spell_data)
            
            # Find next target
            current_pos = esper.component_for_entity(current_target, Position)
            next_target = -1
            next_dist = float('inf')
            
            for ent, (pos, health) in esper.get_components(Position, Health):
                if ent in hit_entities:
                    continue
                
                is_target_party = esper.has_component(ent, PartyMember)
                if is_caster_party == is_target_party:
                    continue
                
                if esper.has_component(ent, Dead):
                    continue
                
                dist = distance(pos.x, pos.y, current_pos.x, current_pos.y)
                if dist < next_dist and dist <= chain_range:
                    next_dist = dist
                    next_target = ent
            
            current_target = next_target
            current_damage = int(current_damage * damage_falloff)
    
    def _apply_buff(self, caster: int, spell_data: dict, intent):
        """Apply a buff spell."""
        target_id = intent.target_id
        if target_id < 0:
            target_id = caster  # Self-buff
        
        if not esper.entity_exists(target_id):
            return
        
        # Create status effect
        effect_type = spell_data.get("effect_type", "regen")
        duration = spell_data.get("duration", 10.0)
        
        effect = StatusEffect(
            effect_type=effect_type,
            duration=duration,
            source_id=caster,
            heal_per_second=spell_data.get("heal_per_second", 0.0),
            slow_amount=spell_data.get("slow_amount", 0.0),
            damage_per_second=spell_data.get("damage_per_second", 0.0)
        )
        
        if esper.has_component(target_id, StatusEffects):
            effects = esper.component_for_entity(target_id, StatusEffects)
            effects.add(effect)
        else:
            esper.add_component(target_id, StatusEffects(effects=[effect]))
        
        self.event_bus.emit(Event(EventType.STATUS_APPLIED, {
            "source": caster,
            "target": target_id,
            "effect_type": effect_type
        }))
    
    def _apply_melee_ability(self, caster: int, spell_data: dict, intent):
        """Apply a melee ability with damage multiplier."""
        target_id = intent.target_id
        if target_id < 0 or not esper.entity_exists(target_id):
            return
        
        # Get caster's weapon damage
        base_damage = 10
        if esper.has_component(caster, Attributes):
            attrs = esper.component_for_entity(caster, Attributes)
            base_damage += attrs.strength // 2
        
        from ..components import Weapon, CombatStats
        if esper.has_component(caster, Weapon):
            weapon = esper.component_for_entity(caster, Weapon)
            base_damage = weapon.damage
        elif esper.has_component(caster, CombatStats):
            stats = esper.component_for_entity(caster, CombatStats)
            base_damage = stats.damage
        
        # Apply multiplier
        multiplier = spell_data.get("damage_multiplier", 1.5)
        flat_damage = spell_data.get("damage_flat", 0)
        final_damage = int(base_damage * multiplier) + flat_damage
        
        # Check if this is a LEAP ability - hero physically moves to target
        anim_type = spell_data.get("animation", "")
        if anim_type == "leap":
            # Start a leaping attack instead of instant damage
            if not esper.has_component(caster, Position):
                return
            caster_pos = esper.component_for_entity(caster, Position)
            
            if not esper.has_component(target_id, Position):
                return
            target_pos = esper.component_for_entity(target_id, Position)
            
            # Check line of sight - can't leap through walls
            if self.dungeon and not self.dungeon.has_line_of_sight(
                caster_pos.x, caster_pos.y, target_pos.x, target_pos.y
            ):
                return  # Can't target through walls
            
            # Calculate AoE damage
            aoe_data = spell_data.get("aoe_on_impact", {})
            aoe_radius = aoe_data.get("radius", 0) if aoe_data else 0
            aoe_mult = aoe_data.get("damage_multiplier", 0.5) if aoe_data else 0
            aoe_damage = int(base_damage * aoe_mult) if aoe_radius > 0 else 0
            
            # Get stun duration
            effect_data = spell_data.get("effect", {})
            stun_duration = effect_data.get("duration", 0) if effect_data.get("type") == "stun" else 0
            
            # Land slightly in front of target (not on top)
            import math
            dx = target_pos.x - caster_pos.x
            dy = target_pos.y - caster_pos.y
            dist = math.sqrt(dx*dx + dy*dy)
            if dist > 0.5:
                # Land 0.8 tiles away from target
                land_dist = max(0, dist - 0.8)
                land_x = caster_pos.x + (dx / dist) * land_dist
                land_y = caster_pos.y + (dy / dist) * land_dist
            else:
                land_x, land_y = target_pos.x, target_pos.y
            
            # Ensure landing position is walkable
            if self.dungeon and not self.dungeon.is_walkable(int(land_x), int(land_y)):
                # Try landing at target position instead
                if self.dungeon.is_walkable(int(target_pos.x), int(target_pos.y)):
                    land_x, land_y = target_pos.x, target_pos.y
                else:
                    # Find nearest walkable tile
                    for offset in [(0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (-1, 1), (1, -1), (-1, -1)]:
                        check_x = int(target_pos.x) + offset[0]
                        check_y = int(target_pos.y) + offset[1]
                        if self.dungeon.is_walkable(check_x, check_y):
                            land_x, land_y = check_x + 0.5, check_y + 0.5
                            break
                    else:
                        # Last resort: stay where we are
                        land_x, land_y = caster_pos.x, caster_pos.y
            
            # Add LeapingAbility component
            esper.add_component(caster, LeapingAbility(
                spell_id=spell_data.get("id", ""),
                target_id=target_id,
                start_x=caster_pos.x,
                start_y=caster_pos.y,
                target_x=land_x,
                target_y=land_y,
                duration=spell_data.get("animation_duration", 0.8),
                elapsed=0.0,
                damage=final_damage,
                aoe_radius=aoe_radius,
                aoe_damage=aoe_damage,
                stun_duration=stun_duration,
                has_landed=False
            ))
            
            # Set animation
            if esper.has_component(caster, Animation):
                anim = esper.component_for_entity(caster, Animation)
                anim.state = AnimationState.LEAP
                anim.frame = 0
            
            return  # Don't do instant damage - leap handles it
        
        # Regular instant melee ability (not a leap)
        # Apply damage
        if esper.has_component(target_id, Health):
            health = esper.component_for_entity(target_id, Health)
            health.current = max(0, health.current - final_damage)
        
        # Create damage number (red if hitting party member)
        if esper.has_component(target_id, Position):
            pos = esper.component_for_entity(target_id, Position)
            is_player_dmg = esper.has_component(target_id, PartyMember)
            esper.create_entity(
                Position(x=pos.x, y=pos.y - 0.5),
                DamageNumber(value=final_damage, is_player_damage=is_player_dmg)
            )
        
        # Apply stun/stagger effect if specified
        effect_data = spell_data.get("effect", {})
        effect_type = effect_data.get("type", "")
        if effect_type in ("stun", "stagger"):
            effect_duration = effect_data.get("duration", 1.0)
            status_effect = StatusEffect(
                effect_type=effect_type,
                duration=effect_duration,
                source_id=caster
            )
            if esper.has_component(target_id, StatusEffects):
                effects = esper.component_for_entity(target_id, StatusEffects)
                effects.add(status_effect)
            else:
                esper.add_component(target_id, StatusEffects(effects=[status_effect]))
        
        # Apply knockback if specified
        knockback_dist = effect_data.get("knockback", 0)
        if knockback_dist > 0 and esper.has_component(caster, Position) and esper.has_component(target_id, Position):
            caster_pos = esper.component_for_entity(caster, Position)
            target_pos = esper.component_for_entity(target_id, Position)
            
            # Calculate knockback direction (away from caster)
            dx = target_pos.x - caster_pos.x
            dy = target_pos.y - caster_pos.y
            dist = (dx*dx + dy*dy) ** 0.5
            if dist > 0.1:
                # Normalize and apply knockback
                dx /= dist
                dy /= dist
                
                # Try progressively shorter knockback distances until we find a valid position
                for mult in [1.0, 0.75, 0.5, 0.25, 0]:
                    test_x = target_pos.x + dx * knockback_dist * mult
                    test_y = target_pos.y + dy * knockback_dist * mult
                    
                    if self.dungeon:
                        # Check if path to new position is clear (using LOS)
                        if self.dungeon.is_walkable(int(test_x), int(test_y)) and \
                           self.dungeon.has_line_of_sight(target_pos.x, target_pos.y, test_x, test_y):
                            target_pos.x = test_x
                            target_pos.y = test_y
                            break
                    else:
                        # No dungeon, just apply knockback
                        target_pos.x = test_x
                        target_pos.y = test_y
                        break
        
        # Apply AoE on impact if specified (for crushing blow ground crack)
        aoe_data = spell_data.get("aoe_on_impact", {})
        if aoe_data and esper.has_component(target_id, Position):
            aoe_radius = aoe_data.get("radius", 1.5)
            aoe_mult = aoe_data.get("damage_multiplier", 0.4)
            aoe_damage = int(base_damage * aoe_mult)
            impact_pos = esper.component_for_entity(target_id, Position)
            self._apply_aoe_damage_at(caster, impact_pos.x, impact_pos.y, aoe_radius, aoe_damage, [target_id])
        
        # Update animation
        if esper.has_component(caster, Animation):
            anim = esper.component_for_entity(caster, Animation)
            anim.state = self._get_animation_state(spell_data, AnimationState.ATTACK)
            anim.frame = 0
        
        self.event_bus.emit(Event(EventType.DAMAGE_DEALT, {
            "attacker": caster,
            "target": target_id,
            "amount": final_damage,
            "damage_type": "physical"
        }))
    
    def _apply_melee_aoe(self, caster: int, spell_data: dict, intent, caster_pos):
        """Apply a melee AoE attack (like whirlwind)."""
        radius = spell_data.get("radius", 2.5)
        multiplier = spell_data.get("damage_multiplier", 1.0)
        
        # Get caster's weapon damage
        base_damage = 10
        if esper.has_component(caster, Attributes):
            attrs = esper.component_for_entity(caster, Attributes)
            base_damage += attrs.strength // 2
        
        from ..components import Weapon, CombatStats
        if esper.has_component(caster, Weapon):
            weapon = esper.component_for_entity(caster, Weapon)
            base_damage = weapon.damage
        elif esper.has_component(caster, CombatStats):
            stats = esper.component_for_entity(caster, CombatStats)
            base_damage = stats.damage
        
        final_damage = int(base_damage * multiplier)
        
        # Check for multi-hit ability
        hits = spell_data.get("hits", 1)
        if hits > 1:
            # Create ActiveAbility for multi-hit damage over time
            hit_interval = spell_data.get("hit_interval", 0.5)
            total_duration = spell_data.get("animation_duration", hits * hit_interval)
            
            esper.add_component(caster, ActiveAbility(
                spell_id=spell_data.get("id", ""),
                hits_remaining=hits,
                hit_interval=hit_interval,
                next_hit_timer=0.0,  # First hit immediately
                radius=radius,
                damage_per_hit=final_damage,
                total_duration=total_duration
            ))
            
            # Set animation
            if esper.has_component(caster, Animation):
                anim = esper.component_for_entity(caster, Animation)
                anim.state = self._get_animation_state(spell_data, AnimationState.ATTACK)
                anim.frame = 0
            
            return  # Don't do single-hit damage
        
        is_caster_party = esper.has_component(caster, PartyMember)
        
        # Hit all enemies in radius
        for ent, (pos, health) in esper.get_components(Position, Health):
            if ent == caster:
                continue
            
            is_target_party = esper.has_component(ent, PartyMember)
            if is_caster_party == is_target_party:
                continue  # Don't hurt allies
            
            if esper.has_component(ent, Dead):
                continue
            
            dist = distance(caster_pos.x, caster_pos.y, pos.x, pos.y)
            if dist > radius:
                continue
            
            # Apply damage
            health.current = max(0, health.current - final_damage)
            
            # Create damage number (red if hitting party member)
            is_player_dmg = esper.has_component(ent, PartyMember)
            esper.create_entity(
                Position(x=pos.x, y=pos.y - 0.5),
                DamageNumber(value=final_damage, is_player_damage=is_player_dmg)
            )
            
            self.event_bus.emit(Event(EventType.DAMAGE_DEALT, {
                "attacker": caster,
                "target": ent,
                "amount": final_damage,
                "damage_type": "physical"
            }))
        
        # Animation - use spell-specific animation
        if esper.has_component(caster, Animation):
            anim = esper.component_for_entity(caster, Animation)
            anim.state = self._get_animation_state(spell_data, AnimationState.ATTACK)
            anim.frame = 0
    
    def _apply_aoe_damage_at(self, caster: int, x: float, y: float, radius: float, damage: int, exclude: list = None):
        """Apply AoE damage at a specific position."""
        if exclude is None:
            exclude = []
        
        is_caster_party = esper.has_component(caster, PartyMember)
        
        for ent, (pos, health) in esper.get_components(Position, Health):
            if ent == caster or ent in exclude:
                continue
            
            is_target_party = esper.has_component(ent, PartyMember)
            if is_caster_party == is_target_party:
                continue  # Don't hurt allies
            
            if esper.has_component(ent, Dead):
                continue
            
            dist = distance(x, y, pos.x, pos.y)
            if dist > radius:
                continue
            
            # Apply damage
            health.current = max(0, health.current - damage)
            
            # Create damage number (red if hitting party member)
            is_player_dmg = esper.has_component(ent, PartyMember)
            esper.create_entity(
                Position(x=pos.x, y=pos.y - 0.5),
                DamageNumber(value=damage, is_player_damage=is_player_dmg)
            )
            
            self.event_bus.emit(Event(EventType.DAMAGE_DEALT, {
                "attacker": caster,
                "target": ent,
                "amount": damage,
                "damage_type": "physical"
            }))
    
    def _apply_cone_attack(self, caster: int, spell_data: dict, intent, caster_pos):
        """Apply a cone attack (like cleave)."""
        cone_range = spell_data.get("range", 2.5)
        cone_angle = spell_data.get("cone_angle", 90)
        multiplier = spell_data.get("damage_multiplier", 1.0)
        
        # Get facing direction
        facing_angle = 0.0
        if esper.has_component(caster, Facing):
            facing = esper.component_for_entity(caster, Facing)
            if facing.direction == Direction.RIGHT:
                facing_angle = 0
            elif facing.direction == Direction.DOWN:
                facing_angle = 90
            elif facing.direction == Direction.LEFT:
                facing_angle = 180
            elif facing.direction == Direction.UP:
                facing_angle = 270
        
        # Get caster's weapon damage
        base_damage = 10
        from ..components import Weapon, CombatStats
        if esper.has_component(caster, Weapon):
            weapon = esper.component_for_entity(caster, Weapon)
            base_damage = weapon.damage
        elif esper.has_component(caster, CombatStats):
            stats = esper.component_for_entity(caster, CombatStats)
            base_damage = stats.damage
        
        final_damage = int(base_damage * multiplier)
        is_caster_party = esper.has_component(caster, PartyMember)
        
        # Hit all enemies in cone
        for ent, (pos, health) in esper.get_components(Position, Health):
            if ent == caster:
                continue
            
            is_target_party = esper.has_component(ent, PartyMember)
            if is_caster_party == is_target_party:
                continue
            
            if esper.has_component(ent, Dead):
                continue
            
            # Check distance
            dist = distance(caster_pos.x, caster_pos.y, pos.x, pos.y)
            if dist > cone_range:
                continue
            
            # Check angle
            dx = pos.x - caster_pos.x
            dy = pos.y - caster_pos.y
            angle_to_target = math.degrees(math.atan2(dy, dx))
            angle_diff = abs((angle_to_target - facing_angle + 180) % 360 - 180)
            
            if angle_diff > cone_angle / 2:
                continue
            
            # Apply damage
            health.current = max(0, health.current - final_damage)
            
            # Create damage number (red if hitting party member)
            is_player_dmg = esper.has_component(ent, PartyMember)
            esper.create_entity(
                Position(x=pos.x, y=pos.y - 0.5),
                DamageNumber(value=final_damage, is_player_damage=is_player_dmg)
            )
            
            self.event_bus.emit(Event(EventType.DAMAGE_DEALT, {
                "attacker": caster,
                "target": ent,
                "amount": final_damage,
                "damage_type": "physical"
            }))
        
        # Animation - use spell-specific animation
        if esper.has_component(caster, Animation):
            anim = esper.component_for_entity(caster, Animation)
            anim.state = self._get_animation_state(spell_data, AnimationState.ATTACK)
            anim.frame = 0

    def _apply_spell_damage(self, caster: int, target: int, spell_data: dict):
        """Apply spell damage to a target."""
        damage = spell_data.get("damage", 20)
        damage_type = spell_data.get("damage_type", "fire")
        
        # Scale damage
        intelligence = 10
        skill_level = 1
        if esper.has_component(caster, Attributes):
            intelligence = esper.component_for_entity(caster, Attributes).intelligence
        if esper.has_component(caster, SkillLevels):
            skills = esper.component_for_entity(caster, SkillLevels)
            school = spell_data.get("school", "combat_magic")
            skill_level = skills.get(school)
        
        scaled_damage = calculate_spell_damage(damage, intelligence, skill_level)
        
        # Get resistance
        resistance = 0.0
        if esper.has_component(target, Resistances):
            res = esper.component_for_entity(target, Resistances)
            resistance = getattr(res, damage_type, 0.0)
        
        final_damage = calculate_elemental_damage(scaled_damage, resistance)
        
        # Apply damage
        if esper.has_component(target, Health):
            health = esper.component_for_entity(target, Health)
            health.current = max(0, health.current - final_damage)
        
        # Create damage number (red if hitting party member)
        if esper.has_component(target, Position):
            pos = esper.component_for_entity(target, Position)
            is_player_dmg = esper.has_component(target, PartyMember)
            esper.create_entity(
                Position(x=pos.x, y=pos.y - 0.5),
                DamageNumber(value=final_damage, is_player_damage=is_player_dmg)
            )
        
        self.event_bus.emit(Event(EventType.DAMAGE_DEALT, {
            "attacker": caster,
            "target": target,
            "amount": final_damage,
            "damage_type": damage_type
        }))
    
    def _update_projectiles(self, dt: float):
        """Update projectile positions and check for hits."""
        for ent, (pos, vel, proj) in esper.get_components(Position, Velocity, Projectile):
            # Check if projectile hit a wall
            if self.dungeon and not self.dungeon.is_walkable(int(pos.x), int(pos.y)):
                # Hit a wall - destroy projectile
                esper.add_component(ent, ToRemove())
                continue
            
            # Homing: Update velocity to track target
            if proj.target_id >= 0 and esper.entity_exists(proj.target_id):
                target_pos = esper.component_for_entity(proj.target_id, Position)
                dist = distance(pos.x, pos.y, target_pos.x, target_pos.y)
                
                # Update velocity to home toward target
                if dist > 0.1:
                    dx = target_pos.x - pos.x
                    dy = target_pos.y - pos.y
                    vel.dx = (dx / dist) * proj.speed
                    vel.dy = (dy / dist) * proj.speed
                
                # Check for hit
                if dist < 0.6:  # Hit!
                    spell_data = data_loader.get_spell(proj.spell_id) or {}
                    spell_data["damage"] = proj.damage
                    spell_data["damage_type"] = proj.damage_type
                    self._apply_spell_damage(proj.caster_id, proj.target_id, spell_data)
                    
                    # Create hit effect
                    esper.create_entity(
                        Position(x=pos.x, y=pos.y),
                        VisualEffect(effect_type=f"hit_{proj.damage_type}", timer=0.3)
                    )
                    
                    self.event_bus.emit(Event(EventType.PROJECTILE_HIT, {
                        "projectile": ent,
                        "target": proj.target_id
                    }))
                    
                    esper.add_component(ent, ToRemove())
                    continue
            else:
                # Ground-targeted - check if reached destination
                dist = distance(pos.x, pos.y, proj.target_x, proj.target_y)
                if dist < 0.5:
                    # Create impact effect for ground-targeted spells
                    esper.create_entity(
                        Position(x=pos.x, y=pos.y),
                        VisualEffect(effect_type=f"impact_{proj.damage_type}", timer=0.4)
                    )
                    esper.add_component(ent, ToRemove())
                    continue
            
            # Timeout - destroy projectile if it's been flying too long
            proj.lifetime = getattr(proj, 'lifetime', 5.0) - dt
            if proj.lifetime <= 0:
                esper.add_component(ent, ToRemove())
    
    def _update_area_effects(self, dt: float):
        """Update persistent area effects."""
        for ent, (pos, effect) in esper.get_components(Position, AreaEffect):
            effect.duration -= dt
            
            if effect.duration <= 0:
                esper.add_component(ent, ToRemove())
                continue
            
            effect.next_tick -= dt
            if effect.next_tick <= 0:
                effect.next_tick = effect.tick_interval
                
                # Apply tick damage
                spell_data = {
                    "damage": effect.damage_per_tick,
                    "damage_type": effect.damage_type,
                    "school": "combat_magic"
                }
                
                self._apply_aoe_damage(
                    effect.caster_id,
                    pos.x, pos.y,
                    effect.radius,
                    effect.damage_per_tick,
                    effect.damage_type,
                    spell_data
                )
    
    def _update_status_effects(self, dt: float):
        """Update status effects on entities."""
        for ent, (effects, health) in esper.get_components(StatusEffects, Health):
            for effect in effects.effects:
                effect.duration -= dt
                
                # Apply healing
                if effect.heal_per_second > 0:
                    heal = int(effect.heal_per_second * dt)
                    health.current = min(health.maximum, health.current + heal)
                
                # Apply damage
                if effect.damage_per_second > 0:
                    damage = int(effect.damage_per_second * dt)
                    health.current = max(0, health.current - damage)
            
            # Remove expired effects
            effects.remove_expired()
