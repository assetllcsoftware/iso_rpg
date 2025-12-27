"""Equipment and inventory components."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


@dataclass
class Equipment:
    """Equipped items by slot."""
    slots: Dict[str, Optional[str]] = field(default_factory=lambda: {
        "head": None,
        "chest": None,
        "hands": None,
        "legs": None,
        "feet": None,
        "main_hand": None,
        "off_hand": None,
        "ring_1": None,
        "ring_2": None,
        "amulet": None,
    })
    
    def get(self, slot: str) -> Optional[str]:
        return self.slots.get(slot)
    
    def equip(self, slot: str, item_id: str) -> Optional[str]:
        """Equip item, return previously equipped item."""
        previous = self.slots.get(slot)
        self.slots[slot] = item_id
        return previous
    
    def unequip(self, slot: str) -> Optional[str]:
        """Unequip item from slot, return item."""
        item = self.slots.get(slot)
        self.slots[slot] = None
        return item


@dataclass
class InventoryItem:
    """A single inventory item."""
    item_id: str
    quantity: int = 1
    # Runtime item data (rarity, bonuses, etc.)
    data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Inventory:
    """Character inventory."""
    items: List[InventoryItem] = field(default_factory=list)
    max_size: int = 30
    
    @property
    def is_full(self) -> bool:
        return len(self.items) >= self.max_size
    
    def add(self, item_id: str, quantity: int = 1, data: Dict = None) -> bool:
        """Add item to inventory. Returns False if full."""
        # Try to stack with existing
        for item in self.items:
            if item.item_id == item_id and item.data == (data or {}):
                item.quantity += quantity
                return True
        
        # Add new slot
        if self.is_full:
            return False
        
        self.items.append(InventoryItem(item_id, quantity, data or {}))
        return True
    
    def remove(self, item_id: str, quantity: int = 1) -> bool:
        """Remove item from inventory. Returns False if not enough."""
        for i, item in enumerate(self.items):
            if item.item_id == item_id:
                if item.quantity >= quantity:
                    item.quantity -= quantity
                    if item.quantity <= 0:
                        self.items.pop(i)
                    return True
        return False


@dataclass
class Gold:
    """Gold currency."""
    amount: int = 0

