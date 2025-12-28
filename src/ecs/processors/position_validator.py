"""Position validation processor - LAST LINE OF DEFENSE.

This processor runs at the END of every frame and ensures NO entity
is ever left in an invalid position. If any entity somehow ends up
in a non-walkable tile, it gets clamped back to the nearest valid position.

This should NEVER trigger if other code is working correctly, but it
prevents soft-locks and off-map glitches.
"""

import esper
from typing import Tuple

from ..components import Position, PartyMember, Enemy, Dead, ToRemove
from ...core.events import EventBus, Event, EventType


class PositionValidator(esper.Processor):
    """Validates all entity positions every frame.
    
    Run this LAST in the processor chain to catch any position bugs.
    """
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.dungeon = None
        self._last_valid_positions = {}  # ent -> (x, y)
    
    def set_dungeon(self, dungeon):
        """Set dungeon reference for validation."""
        self.dungeon = dungeon
        self._last_valid_positions.clear()
    
    def process(self, dt: float):
        """Validate all positions and fix any that are invalid."""
        from ...core.perf_monitor import perf
        perf.mark("PositionValidator")
        
        if not self.dungeon:
            perf.measure("PositionValidator")
            return
        
        for ent, (pos,) in esper.get_components(Position):
            # Skip dead entities - they might be in walls for death animation
            if esper.has_component(ent, Dead):
                continue
            
            # Check if current position is valid
            is_valid = self.dungeon.is_walkable(int(pos.x), int(pos.y))
            
            if is_valid:
                # Store this as a valid fallback position
                self._last_valid_positions[ent] = (pos.x, pos.y)
                
                # Also check if entity is "stuck" - too close to walls to move
                # This happens when corners overlap walls even though center is valid
                if esper.has_component(ent, PartyMember):
                    self._unstick_if_needed(ent, pos)
            else:
                # INVALID POSITION - FIX IT
                self._fix_invalid_position(ent, pos)
        
        perf.measure("PositionValidator")
    
    def _unstick_if_needed(self, ent: int, pos: Position):
        """Check if entity is stuck against walls and nudge them free."""
        # Check if any corners are in non-walkable tiles
        radius = 0.3
        corners_blocked = []
        
        for dx, dy in [(-1, -1), (1, -1), (-1, 1), (1, 1)]:
            check_x = pos.x + dx * radius
            check_y = pos.y + dy * radius
            if not self.dungeon.is_walkable(int(check_x), int(check_y)):
                corners_blocked.append((dx, dy))
        
        if not corners_blocked:
            return  # Not stuck
        
        # Nudge away from blocked corners
        nudge_x = 0.0
        nudge_y = 0.0
        for dx, dy in corners_blocked:
            nudge_x -= dx * 0.05  # Move opposite to blocked corner
            nudge_y -= dy * 0.05
        
        new_x = pos.x + nudge_x
        new_y = pos.y + nudge_y
        
        # Only apply if the new position is still walkable
        if self.dungeon.is_walkable(int(new_x), int(new_y)):
            pos.x = new_x
            pos.y = new_y
    
    def _fix_invalid_position(self, ent: int, pos: Position):
        """Fix an entity that's in an invalid position."""
        # Try 1: Use last known valid position
        if ent in self._last_valid_positions:
            last_x, last_y = self._last_valid_positions[ent]
            if self.dungeon.is_walkable(int(last_x), int(last_y)):
                pos.x = last_x
                pos.y = last_y
                print(f"[PositionValidator] Entity {ent} reset to last valid: ({last_x:.1f}, {last_y:.1f})")
                return
        
        # Try 2: Search for nearest walkable tile
        best_x, best_y = self._find_nearest_walkable(pos.x, pos.y)
        if best_x is not None:
            pos.x = best_x
            pos.y = best_y
            self._last_valid_positions[ent] = (best_x, best_y)
            print(f"[PositionValidator] Entity {ent} moved to nearest walkable: ({best_x:.1f}, {best_y:.1f})")
            return
        
        # Try 3: Party members get teleported to spawn point
        if esper.has_component(ent, PartyMember):
            spawn = self.dungeon.get_player_spawn()
            if spawn:
                pos.x = spawn[0] + 0.5
                pos.y = spawn[1] + 0.5
                self._last_valid_positions[ent] = (pos.x, pos.y)
                print(f"[PositionValidator] Party member {ent} emergency teleported to spawn!")
                return
        
        # Try 4: Enemies get deleted if stuck
        if esper.has_component(ent, Enemy):
            esper.add_component(ent, ToRemove())
            print(f"[PositionValidator] Enemy {ent} was stuck off-map and removed!")
            return
        
        print(f"[PositionValidator] WARNING: Could not fix entity {ent} at ({pos.x:.1f}, {pos.y:.1f})")
    
    def _find_nearest_walkable(self, x: float, y: float) -> Tuple[float, float]:
        """Find nearest walkable tile using expanding search."""
        for radius in range(1, 15):
            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):
                    # Only check the perimeter of each radius
                    if abs(dx) != radius and abs(dy) != radius:
                        continue
                    
                    check_x = int(x) + dx
                    check_y = int(y) + dy
                    
                    if self.dungeon.is_walkable(check_x, check_y):
                        return check_x + 0.5, check_y + 0.5
        
        return None, None
    
    def validate_position(self, x: float, y: float) -> bool:
        """Check if a position is valid (can be called by other code)."""
        if not self.dungeon:
            return True
        return self.dungeon.is_walkable(int(x), int(y))
    
    def clamp_position(self, x: float, y: float) -> Tuple[float, float]:
        """Clamp a position to the nearest valid tile."""
        if not self.dungeon:
            return x, y
        
        if self.dungeon.is_walkable(int(x), int(y)):
            return x, y
        
        result = self._find_nearest_walkable(x, y)
        if result[0] is not None:
            return result
        
        return x, y  # Can't fix, return as-is

