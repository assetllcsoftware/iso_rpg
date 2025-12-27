"""Item components (for items on the ground)."""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional


@dataclass
class ItemDrop:
    """An item on the ground (by item_id)."""
    item_id: str = ""
    quantity: int = 1
    data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DroppedItem:
    """An item entity dropped on the ground."""
    item: Any = None  # The actual item data
    despawn_timer: float = 60.0  # Seconds until despawn
    glow_timer: float = 0.0  # For glow animation
    rarity: int = 0  # For glow color


@dataclass 
class GoldDrop:
    """Gold on the ground."""
    amount: int = 0


@dataclass
class PickupRadius:
    """Radius for auto-pickup."""
    radius: float = 1.0

