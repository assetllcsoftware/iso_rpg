"""Transform components - Position, Velocity, Facing."""

from dataclasses import dataclass, field
from typing import List, Tuple, Optional
from enum import IntEnum


class Direction(IntEnum):
    """Facing direction for sprites."""
    DOWN = 0   # Facing camera (south)
    LEFT = 1   # Facing left (west)
    RIGHT = 2  # Facing right (east)
    UP = 3     # Facing away (north)


@dataclass
class Position:
    """World position in tile coordinates."""
    x: float = 0.0
    y: float = 0.0


@dataclass
class Velocity:
    """Movement velocity in tiles per second."""
    dx: float = 0.0
    dy: float = 0.0


@dataclass
class Facing:
    """Direction the entity is facing."""
    direction: Direction = Direction.DOWN


@dataclass
class Speed:
    """Movement speed in tiles per second."""
    value: float = 5.0


@dataclass
class CollisionRadius:
    """Collision circle radius for entity."""
    radius: float = 0.4


@dataclass
class Path:
    """Pathfinding path to follow."""
    waypoints: List[Tuple[float, float]] = field(default_factory=list)
    current_index: int = 0
    
    @property
    def has_path(self) -> bool:
        return len(self.waypoints) > self.current_index
    
    @property
    def current_target(self) -> Optional[Tuple[float, float]]:
        if self.has_path:
            return self.waypoints[self.current_index]
        return None


@dataclass
class MoveIntent:
    """Requested movement direction (from input or AI)."""
    dx: float = 0.0
    dy: float = 0.0


@dataclass
class TargetPosition:
    """Target position to move towards (click-to-move)."""
    x: float = 0.0
    y: float = 0.0


@dataclass
class Knockback:
    """Forced movement impulse (knockback)."""
    target_x: float = 0.0
    target_y: float = 0.0
    duration: float = 0.2
    elapsed: float = 0.0
    start_x: float = 0.0
    start_y: float = 0.0
