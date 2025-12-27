"""Combat-related components."""

from dataclasses import dataclass, field
from typing import Optional, Dict
from enum import Enum, auto

from ...core.constants import DamageType


@dataclass
class CombatStats:
    """Base combat statistics."""
    damage: int = 10
    armor: int = 0
    attack_speed: float = 1.0  # Attacks per second
    attack_range: float = 1.5  # Tiles


@dataclass
class CombatTarget:
    """Current combat target (entity ID)."""
    target_id: int = -1
    
    @property
    def has_target(self) -> bool:
        return self.target_id >= 0


@dataclass
class AttackCooldown:
    """Time until next attack is ready."""
    remaining: float = 0.0
    
    @property
    def ready(self) -> bool:
        return self.remaining <= 0


@dataclass
class AttackIntent:
    """Intent to attack a target (set by input/AI)."""
    target_id: int = -1


@dataclass
class Weapon:
    """Equipped weapon stats."""
    item_id: str = ""
    damage: int = 10
    attack_range: float = 1.5
    attack_speed: float = 1.0
    weapon_type: str = "melee"  # melee, ranged, magic
    
    # Elemental damage
    fire_damage: int = 0
    ice_damage: int = 0
    lightning_damage: int = 0
    poison_damage: int = 0


@dataclass
class Resistances:
    """Damage resistances (-1.0 to 1.0)."""
    fire: float = 0.0
    ice: float = 0.0
    lightning: float = 0.0
    poison: float = 0.0
    holy: float = 0.0


@dataclass
class InCombat:
    """Marker for entities currently in combat."""
    timer: float = 0.0  # Time since last combat action
    
    # Combat ends after 5 seconds of no action
    COMBAT_TIMEOUT = 5.0
