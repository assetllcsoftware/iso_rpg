"""Combat processor - handles all attacks and damage."""

import esper
from typing import Optional, Tuple

from ..components import (
    Position, Health, Mana, CombatStats, CombatTarget, AttackCooldown,
    AttackIntent, Weapon, Resistances, InCombat, Downed, Dead,
    Facing, Direction, Animation, AnimationState,
    PlayerControlled, PartyMember, Enemy, Ally,
    Attributes, SkillLevels, SkillXP
)
from ..components.rendering import DamageNumber
from ...core.events import EventBus, Event, EventType
from ...core.formulas import (
    calculate_physical_damage, calculate_elemental_damage,
    distance, in_range,
    XP_MELEE_HIT, XP_RANGED_HIT, XP_KILL_BONUS
)
from ...core.constants import ATTACK_RANGE_MELEE


class CombatProcessor(esper.Processor):
    """Processes combat for ALL entities (players, allies, and enemies).
    
    This is THE combat update path. Everyone uses this.
    """
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.dungeon = None
        self.wipe_cooldown = 0.0  # Prevent multiple wipe events
    
    def set_dungeon(self, dungeon):
        """Set dungeon reference for line-of-sight checks."""
        self.dungeon = dungeon
    
    def process(self, dt: float):
        """Process combat each frame."""
        from ...core.perf_monitor import perf
        perf.mark("CombatProcessor")
        
        # Update wipe cooldown
        if self.wipe_cooldown > 0:
            self.wipe_cooldown -= dt
        
        # Update attack cooldowns
        self._update_cooldowns(dt)
        
        # Update in-combat timers
        self._update_combat_state(dt)
        
        # Process attack intents
        self._process_attacks(dt)
        
        # Check for deaths
        self._check_deaths()
        
        # Check for out-of-combat revives
        self._check_revives()
        
        perf.measure("CombatProcessor")
    
    def _update_cooldowns(self, dt: float):
        """Tick down attack cooldowns."""
        for ent, (cooldown,) in esper.get_components(AttackCooldown):
            if cooldown.remaining > 0:
                cooldown.remaining -= dt
    
    def _update_combat_state(self, dt: float):
        """Update in-combat timers."""
        for ent, (in_combat,) in esper.get_components(InCombat):
            in_combat.timer += dt
            
            if in_combat.timer >= InCombat.COMBAT_TIMEOUT:
                # Leave combat
                esper.remove_component(ent, InCombat)
                self.event_bus.emit(Event(EventType.COMBAT_ENDED, {
                    "entity": ent
                }))
    
    def _process_attacks(self, dt: float):
        """Process attack intents and execute attacks."""
        for ent, (pos, stats, cooldown, intent) in esper.get_components(
            Position, CombatStats, AttackCooldown, AttackIntent
        ):
            # Dead/downed entities can't attack
            if esper.has_component(ent, Dead) or esper.has_component(ent, Downed):
                esper.remove_component(ent, AttackIntent)
                continue
            
            target_id = intent.target_id
            if target_id < 0:
                continue
            
            # Check if target exists and is valid
            if not esper.entity_exists(target_id):
                esper.remove_component(ent, AttackIntent)
                continue
            
            # Check if target is dead/downed
            if esper.has_component(target_id, Dead):
                esper.remove_component(ent, AttackIntent)
                continue
            
            if esper.has_component(target_id, Downed):
                # Can't attack downed allies
                if not esper.has_component(target_id, Enemy):
                    esper.remove_component(ent, AttackIntent)
                    continue
            
            # Get target position
            if not esper.has_component(target_id, Position):
                continue
            target_pos = esper.component_for_entity(target_id, Position)
            
            # Check range
            attack_range = stats.attack_range
            if esper.has_component(ent, Weapon):
                weapon = esper.component_for_entity(ent, Weapon)
                attack_range = weapon.attack_range
            
            dist = distance(pos.x, pos.y, target_pos.x, target_pos.y)
            if dist > attack_range:
                # Out of range - set target to move toward
                if esper.has_component(ent, CombatTarget):
                    combat_target = esper.component_for_entity(ent, CombatTarget)
                    combat_target.target_id = target_id
                continue
            
            # Check line of sight
            if self.dungeon and not self.dungeon.has_line_of_sight(
                pos.x, pos.y, target_pos.x, target_pos.y
            ):
                continue  # Can't attack through walls
            
            # Check cooldown
            if not cooldown.ready:
                continue
            
            # Execute attack!
            self._execute_attack(ent, target_id, stats)
            
            # Set cooldown
            attack_speed = stats.attack_speed
            if esper.has_component(ent, Weapon):
                weapon = esper.component_for_entity(ent, Weapon)
                attack_speed = weapon.attack_speed
            
            cooldown.remaining = 1.0 / attack_speed
            
            # Update facing
            dx = target_pos.x - pos.x
            dy = target_pos.y - pos.y
            if esper.has_component(ent, Facing):
                facing = esper.component_for_entity(ent, Facing)
                if abs(dx) > abs(dy):
                    facing.direction = Direction.RIGHT if dx > 0 else Direction.LEFT
                else:
                    facing.direction = Direction.DOWN if dy > 0 else Direction.UP
            
            # Set animation
            if esper.has_component(ent, Animation):
                anim = esper.component_for_entity(ent, Animation)
                anim.state = AnimationState.ATTACK
                anim.frame = 0
                anim.timer = 0.0
            
            # Enter combat
            self._enter_combat(ent)
            self._enter_combat(target_id)
    
    def _execute_attack(self, attacker: int, target: int, stats: CombatStats):
        """Execute an attack and deal damage."""
        # Get attacker stats
        strength = 10
        dexterity = 10
        if esper.has_component(attacker, Attributes):
            attrs = esper.component_for_entity(attacker, Attributes)
            strength = attrs.strength
            dexterity = attrs.dexterity
        
        # Get weapon damage
        weapon_damage = stats.damage
        weapon_type = "melee"
        fire_damage = 0
        ice_damage = 0
        lightning_damage = 0
        poison_damage = 0
        
        if esper.has_component(attacker, Weapon):
            weapon = esper.component_for_entity(attacker, Weapon)
            weapon_damage = weapon.damage
            weapon_type = weapon.weapon_type
            fire_damage = weapon.fire_damage
            ice_damage = weapon.ice_damage
            lightning_damage = weapon.lightning_damage
            poison_damage = weapon.poison_damage
        
        # Get target armor and resistances
        target_armor = 0
        if esper.has_component(target, CombatStats):
            target_stats = esper.component_for_entity(target, CombatStats)
            target_armor = target_stats.armor
        
        resistances = Resistances()
        if esper.has_component(target, Resistances):
            resistances = esper.component_for_entity(target, Resistances)
        
        # Calculate physical damage
        physical_damage, is_crit = calculate_physical_damage(
            weapon_damage, strength, target_armor, dexterity
        )
        
        # Calculate elemental damage
        total_elemental = 0
        if fire_damage > 0:
            total_elemental += calculate_elemental_damage(fire_damage, resistances.fire)
        if ice_damage > 0:
            total_elemental += calculate_elemental_damage(ice_damage, resistances.ice)
        if lightning_damage > 0:
            total_elemental += calculate_elemental_damage(lightning_damage, resistances.lightning)
        if poison_damage > 0:
            total_elemental += calculate_elemental_damage(poison_damage, resistances.poison)
        
        total_damage = physical_damage + total_elemental
        
        # Apply damage
        if esper.has_component(target, Health):
            health = esper.component_for_entity(target, Health)
            health.current = max(0, health.current - total_damage)
        
        # Create damage number (red if hitting a party member)
        if esper.has_component(target, Position):
            target_pos = esper.component_for_entity(target, Position)
            is_player_dmg = esper.has_component(target, PartyMember)
            esper.create_entity(
                Position(x=target_pos.x, y=target_pos.y - 0.5),
                DamageNumber(value=total_damage, is_crit=is_crit, is_player_damage=is_player_dmg)
            )
        
        # Award XP
        xp_amount = XP_MELEE_HIT if weapon_type == "melee" else XP_RANGED_HIT
        skill_name = "melee" if weapon_type == "melee" else "ranged"
        
        if esper.has_component(attacker, SkillXP):
            skill_xp = esper.component_for_entity(attacker, SkillXP)
            skill_xp.add(skill_name, xp_amount)
        
        # Emit event
        self.event_bus.emit(Event(EventType.DAMAGE_DEALT, {
            "attacker": attacker,
            "target": target,
            "amount": total_damage,
            "is_crit": is_crit,
            "damage_type": "physical"
        }))
    
    def _enter_combat(self, entity: int):
        """Put entity into combat state."""
        if esper.has_component(entity, InCombat):
            in_combat = esper.component_for_entity(entity, InCombat)
            in_combat.timer = 0.0
        else:
            esper.add_component(entity, InCombat(timer=0.0))
            self.event_bus.emit(Event(EventType.COMBAT_STARTED, {
                "entity": entity
            }))
    
    def _check_deaths(self):
        """Check for and handle deaths."""
        for ent, (health,) in esper.get_components(Health):
            if health.current <= 0:
                # Skip if already dead/downed
                if esper.has_component(ent, Dead):
                    continue
                if esper.has_component(ent, Downed):
                    continue
                
                # Party member -> downed (can be revived)
                if esper.has_component(ent, PartyMember):
                    esper.add_component(ent, Downed(timer=0.0))
                    
                    # Set animation
                    if esper.has_component(ent, Animation):
                        anim = esper.component_for_entity(ent, Animation)
                        anim.state = AnimationState.DOWNED
                    
                    self.event_bus.emit(Event(EventType.ENTITY_DOWNED, {
                        "entity": ent
                    }))
                    
                    # Check party wipe
                    self._check_party_wipe()
                
                # Enemy -> dead (drop loot, give XP)
                elif esper.has_component(ent, Enemy):
                    esper.add_component(ent, Dead())
                    
                    if esper.has_component(ent, Animation):
                        anim = esper.component_for_entity(ent, Animation)
                        anim.state = AnimationState.DEATH
                    
                    self.event_bus.emit(Event(EventType.ENTITY_DIED, {
                        "entity": ent
                    }))
    
    def _check_party_wipe(self):
        """Check if all party members are downed."""
        # Don't trigger wipe if we're still on cooldown (just respawned)
        if self.wipe_cooldown > 0:
            return
        
        for ent, (member,) in esper.get_components(PartyMember):
            if not esper.has_component(ent, Downed):
                return  # At least one is still up
        
        # All downed! Set cooldown to prevent rapid re-triggers
        self.wipe_cooldown = 2.0  # 2 second cooldown
        self.event_bus.emit(Event(EventType.PARTY_WIPED))
    
    def _check_revives(self):
        """Revive downed party members when out of combat."""
        from ..components import Position
        from ...core.formulas import distance
        
        # Check if any party member is still up
        any_alive = False
        for ent, (member,) in esper.get_components(PartyMember):
            if not esper.has_component(ent, Downed):
                any_alive = True
                break
        
        if not any_alive:
            return  # No one to revive from
        
        # Check if any enemies are nearby (within aggro range)
        enemies_nearby = False
        for party_ent, (party_pos, _) in esper.get_components(Position, PartyMember):
            if esper.has_component(party_ent, Downed):
                continue
            
            for enemy_ent, (enemy_pos, _) in esper.get_components(Position, Enemy):
                if esper.has_component(enemy_ent, Dead):
                    continue
                dist = distance(party_pos.x, party_pos.y, enemy_pos.x, enemy_pos.y)
                if dist < 10.0:  # Enemies within 10 tiles = in combat
                    enemies_nearby = True
                    break
            if enemies_nearby:
                break
        
        if enemies_nearby:
            return  # Still in combat
        
        # Revive all downed party members
        for ent, (member, health, downed) in esper.get_components(PartyMember, Health, Downed):
            # Revive with 25% health
            health.current = max(1, health.maximum // 4)
            
            # Remove downed status
            esper.remove_component(ent, Downed)
            
            # Reset animation
            if esper.has_component(ent, Animation):
                anim = esper.component_for_entity(ent, Animation)
                anim.state = AnimationState.IDLE
            
            self.event_bus.emit(Event(EventType.NOTIFICATION, {
                "text": "Party member revived!",
                "color": (100, 255, 100)
            }))
