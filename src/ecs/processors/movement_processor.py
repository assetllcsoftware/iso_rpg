"""Movement processor - handles all entity movement.

Simple, reliable movement system:
1. Read velocity/intent
2. Apply tile collision
3. Soft entity collision (no pushing, just blocking)
"""

import esper
import math
from typing import Optional, List, Tuple

from ..components import (
    Position, Velocity, Speed, MoveIntent, TargetPosition, Path,
    CollisionRadius, Facing, Direction, StatusEffects, Dead, Downed,
    PlayerControlled, Selected, PartyMember, Enemy
)
from ...core.events import EventBus, Event, EventType
from ...core.formulas import distance


class MovementProcessor(esper.Processor):
    """Processes movement for all entities.
    
    Simple approach:
    - Convert intents to velocity
    - Apply velocity with tile collision
    - No entity-to-entity pushing (causes problems)
    """
    
    def __init__(self, event_bus: EventBus, dungeon=None):
        self.event_bus = event_bus
        self.dungeon = dungeon
    
    def set_dungeon(self, dungeon):
        """Set the dungeon reference for collision detection."""
        self.dungeon = dungeon
    
    def process(self, dt: float):
        """Process movement for all entities."""
        if not self.dungeon:
            return
        
        # Convert intents to velocities
        self._process_move_intents(dt)
        self._process_path_following(dt)
        self._process_target_positions(dt)
        
        # Apply velocities with collision
        self._apply_velocities(dt)
    
    def _process_move_intents(self, dt: float):
        """Convert MoveIntent to Velocity."""
        for ent, (pos, intent, speed) in esper.get_components(
            Position, MoveIntent, Speed
        ):
            # Dead/downed don't move
            if esper.has_component(ent, Dead) or esper.has_component(ent, Downed):
                continue
            
            # Get slow multiplier from status effects
            slow_mult = 1.0
            if esper.has_component(ent, StatusEffects):
                effects = esper.component_for_entity(ent, StatusEffects)
                slow_mult = effects.get_slow_multiplier()
            
            final_speed = speed.value * slow_mult
            
            if esper.has_component(ent, Velocity):
                vel = esper.component_for_entity(ent, Velocity)
                vel.dx = intent.dx * final_speed
                vel.dy = intent.dy * final_speed
            else:
                esper.add_component(ent, Velocity(
                    dx=intent.dx * final_speed,
                    dy=intent.dy * final_speed
                ))
            
            # Update facing direction
            if (intent.dx != 0 or intent.dy != 0) and esper.has_component(ent, Facing):
                facing = esper.component_for_entity(ent, Facing)
                if abs(intent.dx) > abs(intent.dy):
                    facing.direction = Direction.RIGHT if intent.dx > 0 else Direction.LEFT
                else:
                    facing.direction = Direction.DOWN if intent.dy > 0 else Direction.UP
    
    def _process_path_following(self, dt: float):
        """Follow path waypoints."""
        for ent, (pos, path, speed) in esper.get_components(
            Position, Path, Speed
        ):
            if esper.has_component(ent, Dead) or esper.has_component(ent, Downed):
                continue
            
            if not path.has_path:
                continue
            
            target = path.current_target
            if not target:
                continue
            
            dx = target[0] - pos.x
            dy = target[1] - pos.y
            dist = distance(pos.x, pos.y, target[0], target[1])
            
            if dist < 0.3:  # Reached waypoint
                path.current_index += 1
                continue
            
            slow_mult = 1.0
            if esper.has_component(ent, StatusEffects):
                effects = esper.component_for_entity(ent, StatusEffects)
                slow_mult = effects.get_slow_multiplier()
            
            final_speed = speed.value * slow_mult
            
            if esper.has_component(ent, Velocity):
                vel = esper.component_for_entity(ent, Velocity)
                vel.dx = (dx / dist) * final_speed
                vel.dy = (dy / dist) * final_speed
            
            if esper.has_component(ent, Facing):
                facing = esper.component_for_entity(ent, Facing)
                if abs(dx) > abs(dy):
                    facing.direction = Direction.RIGHT if dx > 0 else Direction.LEFT
                else:
                    facing.direction = Direction.DOWN if dy > 0 else Direction.UP
    
    def _process_target_positions(self, dt: float):
        """Move toward target position (click-to-move)."""
        for ent, (pos, target, speed) in esper.get_components(
            Position, TargetPosition, Speed
        ):
            if esper.has_component(ent, Dead) or esper.has_component(ent, Downed):
                esper.remove_component(ent, TargetPosition)
                continue
            
            dx = target.x - pos.x
            dy = target.y - pos.y
            dist = distance(pos.x, pos.y, target.x, target.y)
            
            if dist < 0.2:
                esper.remove_component(ent, TargetPosition)
                if esper.has_component(ent, Velocity):
                    vel = esper.component_for_entity(ent, Velocity)
                    vel.dx = 0
                    vel.dy = 0
                continue
            
            slow_mult = 1.0
            if esper.has_component(ent, StatusEffects):
                effects = esper.component_for_entity(ent, StatusEffects)
                slow_mult = effects.get_slow_multiplier()
            
            final_speed = speed.value * slow_mult
            
            if esper.has_component(ent, Velocity):
                vel = esper.component_for_entity(ent, Velocity)
                vel.dx = (dx / dist) * final_speed
                vel.dy = (dy / dist) * final_speed
            
            if esper.has_component(ent, Facing):
                facing = esper.component_for_entity(ent, Facing)
                if abs(dx) > abs(dy):
                    facing.direction = Direction.RIGHT if dx > 0 else Direction.LEFT
                else:
                    facing.direction = Direction.DOWN if dy > 0 else Direction.UP
    
    def _apply_velocities(self, dt: float):
        """Apply velocities to positions with tile collision."""
        for ent, (pos, vel) in esper.get_components(Position, Velocity):
            # Dead entities don't move
            if esper.has_component(ent, Dead) or esper.has_component(ent, Downed):
                vel.dx = 0
                vel.dy = 0
                continue
            
            if vel.dx == 0 and vel.dy == 0:
                continue
            
            # Get collision radius
            radius = 0.3
            if esper.has_component(ent, CollisionRadius):
                radius = esper.component_for_entity(ent, CollisionRadius).radius
            
            # Try X movement first
            new_x = pos.x + vel.dx * dt
            if self._can_move_to(new_x, pos.y, radius):
                pos.x = new_x
            else:
                vel.dx = 0  # Stop X velocity on collision
            
            # Then Y movement
            new_y = pos.y + vel.dy * dt
            if self._can_move_to(pos.x, new_y, radius):
                pos.y = new_y
            else:
                vel.dy = 0  # Stop Y velocity on collision
    
    def _can_move_to(self, x: float, y: float, radius: float) -> bool:
        """Check if position is valid (tile collision only)."""
        if not self.dungeon:
            return True
        
        # Check bounds
        if x < radius or y < radius:
            return False
        if x >= self.dungeon.width - radius or y >= self.dungeon.height - radius:
            return False
        
        # Check center tile
        if not self.dungeon.is_walkable(int(x), int(y)):
            return False
        
        # Check corners with smaller radius to avoid getting stuck
        check_r = radius * 0.8
        corners = [
            (x - check_r, y - check_r),
            (x + check_r, y - check_r),
            (x - check_r, y + check_r),
            (x + check_r, y + check_r),
        ]
        
        for cx, cy in corners:
            if not self.dungeon.is_walkable(int(cx), int(cy)):
                return False
        
        return True
