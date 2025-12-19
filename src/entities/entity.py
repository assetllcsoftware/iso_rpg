"""Base entity class."""

import math


class Entity:
    """Base class for all game entities."""
    
    _next_id = 0
    
    def __init__(self, x=0.0, y=0.0):
        self.id = Entity._next_id
        Entity._next_id += 1
        
        self.x = float(x)
        self.y = float(y)
        self.target_x = self.x
        self.target_y = self.y
        
        self.speed = 3.0  # Tiles per second
        self.is_moving = False
        self.path = []
        
        self.color = (200, 200, 200)
        self.active = True
        
        # Collision
        self.radius = 0.4  # Collision radius in tiles
        self.pushable = True  # Can be pushed by others
        self.blocks_movement = True  # Blocks other entities
    
    @property
    def position(self):
        return (self.x, self.y)
    
    @property
    def tile_position(self):
        return (int(self.x), int(self.y))
    
    def distance_to(self, other):
        """Calculate distance to another entity or position."""
        if isinstance(other, Entity):
            ox, oy = other.x, other.y
        else:
            ox, oy = other
        return math.sqrt((self.x - ox) ** 2 + (self.y - oy) ** 2)
    
    def move_towards(self, target_x, target_y, dt):
        """Move towards a target position."""
        dx = target_x - self.x
        dy = target_y - self.y
        distance = math.sqrt(dx * dx + dy * dy)
        
        if distance < 0.05:
            self.x = target_x
            self.y = target_y
            self.is_moving = False
            return True
        
        # Normalize and move
        move_dist = self.speed * dt
        if move_dist >= distance:
            self.x = target_x
            self.y = target_y
            self.is_moving = False
            return True
        
        self.x += (dx / distance) * move_dist
        self.y += (dy / distance) * move_dist
        self.is_moving = True
        return False
    
    def set_path(self, path):
        """Set a path to follow."""
        self.path = list(path)
        if self.path:
            self.target_x, self.target_y = self.path[0]
    
    def update_movement(self, dt):
        """Follow the current path."""
        if not self.path:
            self.is_moving = False
            return
        
        target = self.path[0]
        if self.move_towards(target[0], target[1], dt):
            self.path.pop(0)
            if self.path:
                self.target_x, self.target_y = self.path[0]
    
    def apply_separation(self, other_entities, dt):
        """Push away from overlapping entities."""
        if not self.pushable:
            return
        
        push_x = 0.0
        push_y = 0.0
        
        for other in other_entities:
            if other is self:
                continue
            if not other.blocks_movement:
                continue
            if hasattr(other, 'health') and other.health <= 0:
                continue
            
            dx = self.x - other.x
            dy = self.y - other.y
            dist = math.sqrt(dx * dx + dy * dy)
            
            min_dist = self.radius + other.radius
            
            if dist < min_dist and dist > 0.01:
                # Calculate push force (stronger when closer)
                overlap = min_dist - dist
                push_strength = overlap * 5.0  # Push force multiplier
                
                # Normalize and apply
                push_x += (dx / dist) * push_strength
                push_y += (dy / dist) * push_strength
        
        # Apply push
        if abs(push_x) > 0.01 or abs(push_y) > 0.01:
            self.x += push_x * dt
            self.y += push_y * dt
    
    def update(self, dt):
        """Update entity state."""
        self.update_movement(dt)

