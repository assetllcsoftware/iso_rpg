"""Character stats and progression components."""

from dataclasses import dataclass, field
from typing import Dict


@dataclass
class Attributes:
    """Primary attributes (STR/DEX/INT)."""
    strength: int = 10
    dexterity: int = 10
    intelligence: int = 10


@dataclass
class SkillLevels:
    """Skill levels for the 4 skills."""
    melee: int = 0
    ranged: int = 0
    combat_magic: int = 0
    nature_magic: int = 0
    
    def get(self, skill_name: str) -> int:
        return getattr(self, skill_name, 0)
    
    def total(self) -> int:
        return self.melee + self.ranged + self.combat_magic + self.nature_magic


@dataclass
class SkillXP:
    """XP progress for each skill."""
    melee: int = 0
    ranged: int = 0
    combat_magic: int = 0
    nature_magic: int = 0
    
    def get(self, skill_name: str) -> int:
        return getattr(self, skill_name, 0)
    
    def add(self, skill_name: str, amount: int):
        current = getattr(self, skill_name, 0)
        setattr(self, skill_name, current + amount)


@dataclass
class CharacterLevel:
    """Character level (derived from skills)."""
    level: int = 1


@dataclass
class CharacterClass:
    """Character class type."""
    class_name: str = "warrior"  # warrior, mage, ranger, cleric


@dataclass
class CharacterName:
    """Display name for character."""
    name: str = "Unknown"

