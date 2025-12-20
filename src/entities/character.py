"""Player character and party members."""

import math
from .entity import Entity
from ..engine.constants import (
    SKILL_MELEE, SKILL_RANGED, SKILL_COMBAT_MAGIC, SKILL_NATURE_MAGIC,
    ALL_SLOTS, AI_FOLLOW, AI_ATTACK, AI_IDLE,
    ATTACK_RANGE_MELEE, ATTACK_RANGE_RANGED, ATTACK_RANGE_MAGIC
)


class Character(Entity):
    """A playable character with RPG stats."""
    
    def __init__(self, name, x=0.0, y=0.0):
        super().__init__(x, y)
        
        self.name = name
        self.color = (140, 180, 220)  # Friendly blue
        
        # Core stats
        self.level = 1
        self.experience = 0
        
        # Vitals (increased for longer fights)
        self.max_health = 150
        self.health = self.max_health
        self.max_mana = 100
        self.mana = self.max_mana
        
        # Attributes (DS1 style - usage based)
        self.strength = 10      # Melee damage, carry weight
        self.dexterity = 10     # Ranged damage, attack speed
        self.intelligence = 10  # Magic damage, mana pool
        
        # Skills (level up through use, DS1 style)
        self.skills = {
            SKILL_MELEE: 0,
            SKILL_RANGED: 0,
            SKILL_COMBAT_MAGIC: 0,
            SKILL_NATURE_MAGIC: 0,
        }
        self.skill_xp = {skill: 0 for skill in self.skills}
        
        # Combat
        self.attack_cooldown = 0.0
        self.attack_speed = 1.0  # Attacks per second
        self.target = None
        self.in_combat = False
        
        # Equipment
        self.equipment = {slot: None for slot in ALL_SLOTS}
        
        # Inventory
        self.inventory = []
        self.max_weight = 100
        self.gold = 0
        
        # Party AI
        self.is_player_controlled = False
        self.ai_state = AI_FOLLOW
        self.follow_target = None
        self.formation_offset = (0, 0)
        self.path_recalc_timer = 0.0  # Timer for periodic path recalculation
        self.stuck_timer = 0.0  # Timer to detect being stuck
        self.last_pos = (0, 0)  # Last position for stuck detection
        
        # Spells known
        self.spells = []
        
        # Level up tracking for notifications
        self.pending_level_ups = []  # List of skill names that leveled up
        
        # Downed state (revivable instead of dead)
        self.is_downed = False
        self.down_timer = 0.0
        self.max_down_time = 60.0  # Seconds before permanent death
        
        # AI spell delay (allies wait before auto-casting so player can trigger manually)
        self.ai_spell_timers = {}  # spell_id -> time since last player could cast
    
    @property
    def current_weight(self):
        """Calculate total inventory weight."""
        weight = sum(item.weight for item in self.inventory)
        for slot, item in self.equipment.items():
            if item:
                weight += item.weight
        return weight
    
    @property
    def attack_range(self):
        """Get attack range based on equipped weapon."""
        weapon = self.equipment.get('main_hand')
        if weapon:
            return weapon.attack_range
        return ATTACK_RANGE_MELEE
    
    @property
    def damage(self):
        """Calculate base damage."""
        weapon = self.equipment.get('main_hand')
        base_damage = 5
        
        if weapon:
            base_damage = weapon.damage
            if weapon.weapon_type == 'ranged':
                base_damage += self.dexterity // 3
            elif weapon.weapon_type == 'magic':
                base_damage += self.intelligence // 3
            else:
                base_damage += self.strength // 3
        else:
            base_damage += self.strength // 5
        
        return base_damage
    
    @property
    def armor(self):
        """Calculate total armor value."""
        total = 0
        for slot, item in self.equipment.items():
            if item and hasattr(item, 'armor'):
                total += item.armor
        return total
    
    @property
    def dominant_skill(self):
        """Get the highest skill (determines character class display)."""
        return max(self.skills, key=self.skills.get)
    
    @property
    def character_class(self):
        """Get class name based on dominant skill."""
        skill = self.dominant_skill
        level = self.skills[skill]
        
        class_names = {
            SKILL_MELEE: ['Fighter', 'Warrior', 'Champion'],
            SKILL_RANGED: ['Archer', 'Ranger', 'Sharpshooter'],
            SKILL_COMBAT_MAGIC: ['Mage', 'Sorcerer', 'Archmage'],
            SKILL_NATURE_MAGIC: ['Druid', 'Shaman', 'Hierophant'],
        }
        
        tier = min(2, level // 10)
        return class_names.get(skill, ['Adventurer'])[tier]
    
    def gain_skill_xp(self, skill, amount):
        """Gain experience in a skill (DS1 style leveling)."""
        if skill not in self.skill_xp:
            return
        
        self.skill_xp[skill] += amount
        
        # Level up skill
        xp_needed = int(50 * ((self.skills[skill] + 1) ** 1.5))
        while self.skill_xp[skill] >= xp_needed:
            self.skill_xp[skill] -= xp_needed
            self.skills[skill] += 1
            self._on_skill_level_up(skill)
            xp_needed = int(50 * ((self.skills[skill] + 1) ** 1.5))
    
    def _on_skill_level_up(self, skill):
        """Handle skill level up bonuses."""
        # Increase related attribute
        if skill == SKILL_MELEE:
            self.strength += 1
            self.max_health += 5
            skill_name = "Melee"
        elif skill == SKILL_RANGED:
            self.dexterity += 1
            self.max_health += 3
            skill_name = "Ranged"
        elif skill == SKILL_COMBAT_MAGIC:
            self.intelligence += 1
            self.max_mana += 5
            skill_name = "Combat Magic"
        elif skill == SKILL_NATURE_MAGIC:
            self.intelligence += 1
            self.max_mana += 3
            self.max_health += 2
            skill_name = "Nature Magic"
        else:
            skill_name = skill
        
        # Track for notification
        self.pending_level_ups.append({
            'skill': skill_name,
            'new_level': self.skills[skill]
        })
        
        # Learn new spells at certain skill levels
        self._check_learn_spells(skill)
        
        # Recalculate level (average of skills / 2)
        old_level = self.level
        total_skills = sum(self.skills.values())
        self.level = max(1, total_skills // 2)
        
        if self.level > old_level:
            self.pending_level_ups.append({
                'skill': 'CHARACTER',
                'new_level': self.level
            })
    
    def take_damage(self, amount, damage_type='physical'):
        """Take damage, reduced by armor."""
        if self.is_downed:
            return 0  # Can't damage downed characters
            
        if damage_type == 'physical':
            reduction = self.armor / (self.armor + 50)
            amount = int(amount * (1 - reduction))
        
        self.health = max(0, self.health - amount)
        
        # Go into downed state instead of dying (except player)
        if self.health <= 0 and not self.is_player_controlled:
            self.is_downed = True
            self.down_timer = 0.0
            self.health = 0
        
        return amount
    
    def heal(self, amount):
        """Heal health."""
        if self.is_downed:
            return  # Can't heal downed characters normally
        self.health = min(self.max_health, self.health + amount)
    
    def revive(self, heal_percent=50):
        """Revive from downed state."""
        if self.is_downed:
            self.is_downed = False
            self.down_timer = 0.0
            self.health = int(self.max_health * heal_percent / 100)
            self.pending_level_ups.append({
                'skill': 'REVIVED',
                'new_level': 0
            })
    
    def _check_learn_spells(self, skill):
        """Learn new spells when reaching required skill levels."""
        if not hasattr(self, 'spellbook'):
            return
        
        # Spells unlocked at each skill level
        COMBAT_MAGIC_SPELLS = {
            2: 'lightning_bolt',
            3: 'chain_lightning',
            5: 'meteor',
        }
        NATURE_MAGIC_SPELLS = {
            2: 'poison_cloud',
            3: 'revive',
            4: 'regeneration',
            5: 'group_heal',
            8: 'summon_wolf',
        }
        
        current_level = self.skills.get(skill, 0)
        
        if skill == SKILL_COMBAT_MAGIC:
            spell_table = COMBAT_MAGIC_SPELLS
        elif skill == SKILL_NATURE_MAGIC:
            spell_table = NATURE_MAGIC_SPELLS
        else:
            return
        
        # Check if we just reached a level that unlocks a spell
        if current_level in spell_table:
            spell_id = spell_table[current_level]
            if spell_id not in self.spellbook.spells:
                self.spellbook.learn_spell(spell_id)
                self.pending_level_ups.append({
                    'skill': f'LEARNED: {spell_id.replace("_", " ").title()}',
                    'new_level': 0
                })
    
    def restore_mana(self, amount):
        """Restore mana."""
        self.mana = min(self.max_mana, self.mana + amount)
    
    def can_attack(self):
        """Check if character can attack."""
        return self.attack_cooldown <= 0 and self.health > 0
    
    def attack(self, target):
        """Perform an attack on target."""
        if not self.can_attack():
            return 0
        
        # Reset cooldown
        self.attack_cooldown = 1.0 / self.attack_speed
        
        # Calculate damage
        damage = self.damage
        
        # Determine skill used
        weapon = self.equipment.get('main_hand')
        if weapon:
            if weapon.weapon_type == 'ranged':
                skill = SKILL_RANGED
            elif weapon.weapon_type == 'magic':
                skill = SKILL_COMBAT_MAGIC
            else:
                skill = SKILL_MELEE
        else:
            skill = SKILL_MELEE
        
        # Gain skill XP
        self.gain_skill_xp(skill, 10)
        
        return damage
    
    def equip(self, item):
        """Equip an item."""
        if not hasattr(item, 'slot'):
            return False
        
        slot = item.slot
        if slot not in self.equipment:
            return False
        
        # Unequip existing
        old_item = self.equipment[slot]
        if old_item:
            self.inventory.append(old_item)
        
        # Equip new
        if item in self.inventory:
            self.inventory.remove(item)
        self.equipment[slot] = item
        
        return True
    
    def unequip(self, slot):
        """Unequip item from slot."""
        item = self.equipment.get(slot)
        if item:
            self.equipment[slot] = None
            self.inventory.append(item)
            return item
        return None
    
    def update(self, dt):
        """Update character state."""
        # Handle downed state
        if self.is_downed:
            self.down_timer += dt
            if self.down_timer >= self.max_down_time:
                # Permanent death - remove from party
                self.health = -1  # Mark for removal
            return  # Don't do anything else while downed
        
        super().update(dt)
        
        # Update cooldowns
        if self.attack_cooldown > 0:
            self.attack_cooldown -= dt
        
        # Regeneration (slow)
        if not self.in_combat:
            self.health = min(self.max_health, self.health + 0.5 * dt)
            self.mana = min(self.max_mana, self.mana + 8.0 * dt)  # Fast mana regen
        
        # AI behavior
        if not self.is_player_controlled:
            self._update_ai(dt)
    
    def _update_ai(self, dt):
        """Update AI behavior for party members."""
        # Look for nearby enemies to auto-engage
        nearest_enemy = self._find_nearest_enemy()
        if nearest_enemy:
            self.target = nearest_enemy
            self.ai_state = AI_ATTACK
        elif self.ai_state == AI_ATTACK and not self.target:
            # No enemy, go back to following
            self.ai_state = AI_FOLLOW
            # Reset combat timer for next fight
            self.ai_spell_timers.clear()
        
        if self.ai_state == AI_ATTACK and self.target:
            if self.target.health <= 0:
                self.target = None
                self.ai_state = AI_FOLLOW
                # Reset combat timer so we wait again next fight
                self.ai_spell_timers.clear()
                return
            
            dist = self.distance_to(self.target)
            
            # Class-specific AI behavior
            char_class = getattr(self, 'char_class', 'warrior')
            
            if char_class == 'mage':
                # Mage AI: Wait 3x cooldown before EVERY auto-cast
                # Mages NEVER do weapon attacks - only spells
                
                # Tick up all spell timers
                for sid in list(self.ai_spell_timers.keys()):
                    self.ai_spell_timers[sid] += dt
                
                casted_this_frame = False
                
                if dist <= 6.0 and hasattr(self, 'spellbook') and not casted_this_frame:
                    for spell_id, spell in self.spellbook.spells.items():
                        if spell.damage <= 0:
                            continue
                        
                        if spell_id not in self.ai_spell_timers:
                            self.ai_spell_timers[spell_id] = 0
                        
                        required_wait = spell.cooldown * 3.0  # 3x cooldown
                        waited = self.ai_spell_timers[spell_id]
                        can_cast_spell = self.spellbook.can_cast(spell_id, self)
                        can_atk = self.can_attack()
                        
                        if can_cast_spell and waited >= required_wait and can_atk:
                            print(f"*** {self.name} AUTO-CAST {spell_id} (waited {waited:.1f}s >= {required_wait:.1f}s) ***")
                            self.mana -= spell.mana_cost
                            self.attack_cooldown = spell.cooldown
                            self.spellbook.cooldowns[spell_id] = spell.cooldown
                            self.ai_spell_timers[spell_id] = 0
                            
                            damage = spell.get_damage(self)
                            # Don't apply damage here - let the projectile effect do it on impact
                            self.gain_skill_xp(SKILL_COMBAT_MAGIC, 15)
                            
                            if self._world_ref:
                                self._world_ref.combat_events.append({
                                    'type': 'spell',
                                    'spell_id': spell_id,
                                    'attacker': self,
                                    'target': self.target,
                                    'damage': damage,  # Damage to apply on impact
                                    'spell_color': spell.color,
                                    'delayed_damage': True  # Flag for delayed damage
                                })
                            casted_this_frame = True
                            break
                
                # Move closer if too far (but don't attack)
                if dist > 6.0:
                    self.set_path([(self.target.x, self.target.y)])
                elif dist < 3.0 and self.follow_target:
                    self.set_path([(self.follow_target.x, self.follow_target.y)])
                
                # IMPORTANT: Return here so mage doesn't fall through to other AI
                return
                    
            elif char_class == 'ranger':
                # Ranger: ranged attacks, medium distance
                if dist <= self.attack_range:
                    if self.can_attack():
                        damage = self.attack(self.target)
                        self.target.take_damage(damage)
                        self.gain_skill_xp(SKILL_RANGED, 10)
                else:
                    self.set_path([(self.target.x, self.target.y)])
                    
            elif char_class == 'cleric':
                # Cleric: heal allies, support
                if self.follow_target and self.follow_target.health < self.follow_target.max_health * 0.6 and self.mana >= 20:
                    # Heal ally
                    self.mana -= 20
                    heal_amount = 25 + self.intelligence
                    self.follow_target.health = min(self.follow_target.max_health, self.follow_target.health + heal_amount)
                    self.gain_skill_xp(SKILL_NATURE_MAGIC, 15)
                elif self.health < self.max_health * 0.5 and self.mana >= 20:
                    # Self heal
                    self.mana -= 20
                    heal_amount = 25 + self.intelligence
                    self.health = min(self.max_health, self.health + heal_amount)
                    self.gain_skill_xp(SKILL_NATURE_MAGIC, 15)
                # Basic melee
                elif dist <= self.attack_range:
                    if self.can_attack():
                        damage = self.attack(self.target)
                        self.target.take_damage(damage)
            else:
                # Warrior: melee focused
                if dist <= self.attack_range:
                    if self.can_attack():
                        damage = self.attack(self.target)
                        self.target.take_damage(damage)
                        self.gain_skill_xp(SKILL_MELEE, 10)
                else:
                    self.set_path([(self.target.x, self.target.y)])
        
        # Following behavior when not in combat
        if self.ai_state == AI_FOLLOW and self.follow_target:
            target_x = self.follow_target.x + self.formation_offset[0]
            target_y = self.follow_target.y + self.formation_offset[1]
            
            player_dist = self.distance_to(self.follow_target)
            dist = self.distance_to((target_x, target_y))
            
            # Stuck detection - if we haven't moved much and far from player
            moved = ((self.x - self.last_pos[0]) ** 2 + (self.y - self.last_pos[1]) ** 2) ** 0.5
            if moved < 0.5:
                self.stuck_timer += dt
            else:
                self.stuck_timer = 0.0
            self.last_pos = (self.x, self.y)
            
            # Teleport to player if stuck for 2+ seconds and far away
            if self.stuck_timer > 2.0 and player_dist > 4.0:
                print(f"[DEBUG] {self.name} TELEPORTING - stuck {self.stuck_timer:.1f}s, dist {player_dist:.1f}")
                # Find a walkable spot near player
                teleported = False
                if hasattr(self, '_world_ref') and self._world_ref:
                    for offset in [(1.5, 0), (0, 1.5), (-1.5, 0), (0, -1.5), (1, 1), (-1, 1), (1, -1), (-1, -1)]:
                        new_x = self.follow_target.x + offset[0]
                        new_y = self.follow_target.y + offset[1]
                        if self._world_ref.is_walkable(int(new_x), int(new_y)):
                            self.x = new_x
                            self.y = new_y
                            self.path = []
                            self.stuck_timer = 0.0
                            teleported = True
                            print(f"[DEBUG] {self.name} teleported to ({new_x:.1f}, {new_y:.1f})")
                            break
                if not teleported:
                    # Force teleport to player position as last resort
                    self.x = self.follow_target.x + 1
                    self.y = self.follow_target.y + 1
                    self.path = []
                    self.stuck_timer = 0.0
                    print(f"[DEBUG] {self.name} FORCE teleported next to player")
            
            # Step aside if too close to player
            if player_dist < 1.0:
                dx = self.x - self.follow_target.x
                dy = self.y - self.follow_target.y
                if player_dist > 0.1:
                    self.x += (dx / player_dist) * 2.0 * dt
                    self.y += (dy / player_dist) * 2.0 * dt
            
            # Periodic path recalculation (every 1.5 seconds) to unstick
            self.path_recalc_timer += dt
            should_recalc = self.path_recalc_timer >= 1.5
            
            # Also recalc if stuck (not moving but have a path and far from target)
            if self.path and not self.is_moving and dist > 3.0:
                should_recalc = True
            
            if dist > 2.0 and (not self.path or should_recalc):
                self.path_recalc_timer = 0.0
                # Use A* pathfinding if available
                if hasattr(self, '_world_ref') and self._world_ref:
                    new_path = self._world_ref.find_path(
                        (int(self.x), int(self.y)),
                        (int(target_x), int(target_y))
                    )
                    if new_path:
                        self.set_path(new_path)
                    else:
                        # Fallback to direct path
                        self.set_path([(target_x, target_y)])
                else:
                    self.set_path([(target_x, target_y)])
    
    def _find_nearest_enemy(self):
        """Find nearest enemy within aggro range."""
        if not hasattr(self, '_world_ref') or not self._world_ref:
            return None
        
        aggro_range = 8.0  # Increased so allies engage from further
        nearest = None
        nearest_dist = aggro_range
        
        for enemy in self._world_ref.enemies:
            if enemy.health <= 0:
                continue
            dist = self.distance_to(enemy)
            if dist < nearest_dist:
                nearest_dist = dist
                nearest = enemy
        
        return nearest

