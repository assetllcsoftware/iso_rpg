"""Enemy entities."""

import math
import random
from .entity import Entity
from ..engine.constants import AI_IDLE, AI_PATROL, AI_ATTACK, AI_FLEE


class Enemy(Entity):
    """An enemy creature."""
    
    ENEMY_TYPES = {
        'goblin': {
            'health': 50,
            'damage': 5,
            'speed': 2.5,
            'xp': 20,
            'color': (100, 150, 80),
            'aggro_range': 5.0,
        },
        'skeleton': {
            'health': 70,
            'damage': 8,
            'speed': 2.0,
            'xp': 30,
            'color': (200, 195, 180),
            'aggro_range': 6.0,
        },
        'orc': {
            'health': 130,
            'damage': 12,
            'speed': 2.2,
            'xp': 50,
            'color': (80, 120, 70),
            'aggro_range': 5.0,
        },
        'spider': {
            'health': 40,
            'damage': 6,
            'speed': 3.5,
            'xp': 25,
            'color': (60, 50, 70),
            'aggro_range': 4.0,
        },
        'troll': {
            'health': 240,
            'damage': 20,
            'speed': 1.5,
            'xp': 100,
            'color': (100, 130, 100),
            'aggro_range': 4.0,
        },
        'dark_mage': {
            'health': 50,
            'damage': 15,
            'speed': 2.0,
            'xp': 75,
            'color': (80, 50, 100),
            'aggro_range': 7.0,
            'attack_range': 5.0,
        },
    }
    
    def __init__(self, enemy_type, x=0.0, y=0.0, level=1):
        super().__init__(x, y)
        
        self.enemy_type = enemy_type
        stats = self.ENEMY_TYPES.get(enemy_type, self.ENEMY_TYPES['goblin'])
        
        self.name = enemy_type.replace('_', ' ').title()
        self.level = level
        
        # Scale stats by level
        level_mult = 1 + (level - 1) * 0.15
        
        self.max_health = int(stats['health'] * level_mult)
        self.health = self.max_health
        self.base_damage = int(stats['damage'] * level_mult)
        self.speed = stats['speed']
        self.xp_value = int(stats['xp'] * level_mult)
        self.color = stats['color']
        
        self.aggro_range = stats['aggro_range']
        self.attack_range = stats.get('attack_range', 1.5)
        self.attack_cooldown = 0.0
        self.attack_speed = 1.0
        
        # AI
        self.ai_state = AI_IDLE
        self.target = None
        self.home_position = (x, y)
        self.patrol_points = []
        self.patrol_index = 0
        self.idle_timer = 0.0
        
        # Combat
        self.in_combat = False
        self.leash_range = 15.0  # How far from home before giving up
    
    @property
    def damage(self):
        return self.base_damage
    
    def can_attack(self):
        return self.attack_cooldown <= 0 and self.health > 0
    
    def attack(self, target):
        """Perform attack on target."""
        if not self.can_attack():
            return 0
        
        self.attack_cooldown = 1.0 / self.attack_speed
        return self.damage
    
    def take_damage(self, amount, attacker=None):
        """Take damage and potentially aggro."""
        self.health = max(0, self.health - amount)
        
        if attacker and self.ai_state != AI_ATTACK:
            self.target = attacker
            self.ai_state = AI_ATTACK
            self.in_combat = True
        
        return amount
    
    def find_nearest_enemy(self, characters):
        """Find nearest character in aggro range."""
        nearest = None
        nearest_dist = self.aggro_range
        
        for char in characters:
            if char.health <= 0:
                continue
            dist = self.distance_to(char)
            if dist < nearest_dist:
                nearest = char
                nearest_dist = dist
        
        return nearest
    
    def update(self, dt, characters=None, combat_events=None):
        """Update enemy AI and state."""
        super().update(dt)
        
        self.combat_events = combat_events  # Store reference for attack events
        
        if self.health <= 0:
            return
        
        # Update cooldowns
        if self.attack_cooldown > 0:
            self.attack_cooldown -= dt
        
        # AI State machine
        if self.ai_state == AI_IDLE:
            self._update_idle(dt, characters)
        elif self.ai_state == AI_PATROL:
            self._update_patrol(dt, characters)
        elif self.ai_state == AI_ATTACK:
            self._update_attack(dt, characters)
        elif self.ai_state == AI_FLEE:
            self._update_flee(dt)
    
    def _update_idle(self, dt, characters):
        """Idle behavior - look for targets."""
        self.idle_timer -= dt
        
        if characters:
            target = self.find_nearest_enemy(characters)
            if target:
                self.target = target
                self.ai_state = AI_ATTACK
                self.in_combat = True
                return
        
        # Occasionally start patrolling
        if self.idle_timer <= 0:
            self.idle_timer = random.uniform(2.0, 5.0)
            if random.random() < 0.3 and self.patrol_points:
                self.ai_state = AI_PATROL
    
    def _update_patrol(self, dt, characters):
        """Patrol between points."""
        if characters:
            target = self.find_nearest_enemy(characters)
            if target:
                self.target = target
                self.ai_state = AI_ATTACK
                self.in_combat = True
                return
        
        if not self.patrol_points:
            self.ai_state = AI_IDLE
            return
        
        target = self.patrol_points[self.patrol_index]
        if self.distance_to(target) < 0.5:
            self.patrol_index = (self.patrol_index + 1) % len(self.patrol_points)
            self.idle_timer = random.uniform(1.0, 2.0)
            self.ai_state = AI_IDLE
        else:
            if not self.path:
                self.set_path([target])
    
    def _update_attack(self, dt, characters):
        """Chase and attack target."""
        if not self.target or self.target.health <= 0:
            self.target = None
            self.ai_state = AI_IDLE
            self.in_combat = False
            return
        
        # Check leash range
        home_dist = self.distance_to(self.home_position)
        if home_dist > self.leash_range:
            self.target = None
            self.ai_state = AI_IDLE
            self.in_combat = False
            self.set_path([self.home_position])
            return
        
        dist = self.distance_to(self.target)
        
        if dist <= self.attack_range:
            # Attack!
            if self.can_attack():
                damage = self.attack(self.target)
                self.target.take_damage(damage)
                
                # Emit combat event for visual effect
                if self.combat_events is not None:
                    attack_type = 'ranged' if self.attack_range > 2 else 'melee'
                    self.combat_events.append({
                        'type': attack_type,
                        'attacker': self,
                        'target': self.target,
                        'damage': damage,
                    })
            # Stop moving
            self.path = []
        else:
            # Chase
            if not self.path or self.distance_to(self.path[-1]) > 1:
                self.set_path([(self.target.x, self.target.y)])
    
    def _update_flee(self, dt):
        """Run away from danger."""
        if not self.path:
            # Run towards home
            self.set_path([self.home_position])
        
        if self.distance_to(self.home_position) < 1:
            self.ai_state = AI_IDLE
            self.health = min(self.health + 10, self.max_health)
    
    def drop_loot(self):
        """Generate loot drops on death."""
        from .item import generate_loot
        return generate_loot(self.level, self.enemy_type)

