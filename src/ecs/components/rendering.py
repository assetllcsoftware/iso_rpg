"""Rendering and animation components."""

from dataclasses import dataclass
from enum import Enum, auto


class AnimationState(Enum):
    """Animation states."""
    IDLE = auto()
    WALK = auto()
    ATTACK = auto()
    CAST = auto()
    DEATH = auto()
    DOWNED = auto()
    # Hero special abilities
    SPIN = auto()       # Whirlwind spin attack
    LEAP = auto()       # Jump strike 
    HEAVY = auto()      # Heavy/crushing blow wind-up and strike
    BASH = auto()       # Shield bash (step forward + shield thrust)
    # Mage channeling
    CHANNEL = auto()    # Channeling a spell (Lyra)


@dataclass
class Sprite:
    """Sprite rendering info."""
    sprite_set: str = "hero"  # Which sprite set to use
    width: int = 48
    height: int = 48
    
    # Render layer (higher = on top)
    layer: int = 1


@dataclass
class Animation:
    """Animation state."""
    state: AnimationState = AnimationState.IDLE
    frame: int = 0
    timer: float = 0.0
    
    # Frame timing
    frame_duration: float = 0.10 # Faster animations (Was 0.15)


@dataclass
class RenderOffset:
    """Offset for rendering (centering, etc.)."""
    x: int = 0
    y: int = -16  # Offset up to center on tile


@dataclass
class HealthBar:
    """Marker to render health bar above entity."""
    show: bool = True
    offset_y: int = -40


@dataclass
class DamageNumber:
    """Floating damage number."""
    value: int = 0
    is_crit: bool = False
    is_heal: bool = False
    is_player_damage: bool = False  # True if damage to party member (red)
    timer: float = 1.5
    rise_speed: float = 120.0  # Much faster rise


@dataclass
class VisualEffect:
    """A visual effect (spell impact, etc.)."""
    effect_type: str = ""  # fire_explosion, ice_shatter, etc.
    timer: float = 0.5
    frame: int = 0

