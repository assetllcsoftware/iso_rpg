"""AI behavior components."""

from dataclasses import dataclass, field
from typing import Tuple, Optional, List

from ...core.constants import AIState


@dataclass
class AIController:
    """AI state and behavior."""
    state: AIState = AIState.IDLE
    
    # Targeting
    target_id: int = -1
    
    # Spawn point (for leashing)
    home_x: float = 0.0
    home_y: float = 0.0
    
    # Timers
    state_timer: float = 0.0
    decision_timer: float = 0.0  # Time until next decision
    stuck_timer: float = 0.0


@dataclass
class AggroRange:
    """Range at which entity will aggro."""
    range: float = 6.0


@dataclass
class LeashRange:
    """Range before entity returns home."""
    range: float = 15.0


@dataclass
class AllyAI:
    """Marker for ally AI (follows player, helps in combat)."""
    leader_id: int = -1  # Entity to follow
    formation_offset: Tuple[float, float] = (0.0, 0.0)
    
    # Mage AI spell timing
    spell_ready_timers: dict = field(default_factory=dict)


@dataclass
class EnemyAI:
    """Marker for enemy AI (patrols, attacks player)."""
    enemy_type: str = "skeleton"
    
    # Patrol (optional)
    patrol_points: List[Tuple[float, float]] = field(default_factory=list)
    patrol_index: int = 0


@dataclass
class PatrolPath:
    """Patrol waypoints for enemies."""
    points: List[Tuple[float, float]] = field(default_factory=list)
    current_index: int = 0
    wait_timer: float = 0.0
    wait_time: float = 2.0  # Time to wait at each point


@dataclass
class Summon:
    """Marker for summoned creatures."""
    summoner_id: int = -1
    duration: float = 30.0  # Time until despawn

