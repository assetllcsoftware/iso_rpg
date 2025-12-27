"""Health and Mana components."""

from dataclasses import dataclass


@dataclass
class Health:
    """Entity health points."""
    current: int = 100
    maximum: int = 100
    
    @property
    def is_alive(self) -> bool:
        return self.current > 0
    
    @property
    def percent(self) -> float:
        if self.maximum <= 0:
            return 0.0
        return self.current / self.maximum


@dataclass
class Mana:
    """Entity mana points for spellcasting."""
    current: int = 100
    maximum: int = 100
    
    @property
    def percent(self) -> float:
        if self.maximum <= 0:
            return 0.0
        return self.current / self.maximum


@dataclass
class Regeneration:
    """Health and mana regeneration rates."""
    health_per_second: float = 0.0
    mana_per_second: float = 2.0
    in_combat: bool = False


@dataclass
class Downed:
    """Marker for downed (but revivable) party members."""
    timer: float = 0.0  # Time spent downed


@dataclass
class Dead:
    """Marker for permanently dead entities (enemies)."""
    timer: float = 0.0  # Time since death, for corpse removal
