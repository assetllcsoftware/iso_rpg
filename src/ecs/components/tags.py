"""Tag components (markers with no data)."""

from dataclasses import dataclass


@dataclass
class PlayerControlled:
    """This entity is controlled by the player."""
    pass


@dataclass
class Selected:
    """This entity is currently selected by the player."""
    pass


@dataclass
class PartyMember:
    """This entity is a party member (player or ally)."""
    party_index: int = 0  # 0 = leader, 1+ = allies


@dataclass
class Enemy:
    """This entity is hostile."""
    pass


@dataclass
class Ally:
    """This entity is friendly (AI-controlled party member)."""
    pass


@dataclass
class Loot:
    """This entity is lootable (item on ground)."""
    pass


@dataclass
class Interactable:
    """This entity can be interacted with."""
    interaction_type: str = ""  # "stairs", "shrine", "chest"


@dataclass
class ToRemove:
    """Mark entity for removal at end of frame."""
    pass
