"""Item and loot entity factories."""

import esper
import random
from typing import Optional, Dict, Any

from ..components import (
    Position, Velocity,
    Sprite, Animation, AnimationState,
    ItemDrop, DroppedItem, GoldDrop, PickupRadius, Loot
)
from ...data.loader import data_loader
from ...core.formulas import rarity_chances, roll_gold_drop


def create_item_drop(
    item_id: str,
    x: float,
    y: float,
    quantity: int = 1,
    data: Dict[str, Any] = None
) -> int:
    """Create an item drop on the ground.
    
    Args:
        item_id: Item ID from items.yaml
        x, y: Position
        quantity: Stack size
        data: Additional item data (rarity, bonuses, etc.)
    
    Returns:
        Entity ID
    """
    item_data = data_loader.get_item(item_id)
    sprite = item_data.get("sprite", "item_default") if item_data else "item_default"
    rarity = (data or {}).get("rarity", item_data.get("rarity", 0) if item_data else 0)
    
    # Create a simple item object for the DroppedItem component
    class DroppedItemData:
        def __init__(self, name, item_id, rarity):
            self.name = name
            self.item_id = item_id
            self.rarity = rarity
    
    item_name = item_data.get("name", item_id) if item_data else item_id
    dropped_data = DroppedItemData(item_name, item_id, rarity)
    
    entity = esper.create_entity(
        Position(x=x, y=y),
        Velocity(),
        Sprite(sprite_set=sprite, width=32, height=32, layer=0),
        ItemDrop(item_id=item_id, quantity=quantity, data=data or {}),
        DroppedItem(item=dropped_data, rarity=rarity),
        PickupRadius(radius=1.0),
        Loot(),
    )
    
    return entity


def create_gold_drop(
    amount: int,
    x: float,
    y: float
) -> int:
    """Create a gold drop on the ground.
    
    Args:
        amount: Gold amount
        x, y: Position
    
    Returns:
        Entity ID
    """
    entity = esper.create_entity(
        Position(x=x, y=y),
        Velocity(),
        Sprite(sprite_set="gold", width=24, height=24, layer=0),
        GoldDrop(amount=amount),
        PickupRadius(radius=1.5),  # Slightly larger for gold
        Loot(),
    )
    
    return entity


def roll_loot_drops(
    loot_table_id: str,
    x: float,
    y: float,
    dungeon_level: int = 1
) -> list:
    """Roll loot from a loot table and create drops.
    
    Args:
        loot_table_id: Loot table ID from loot_tables.yaml
        x, y: Position for drops
        dungeon_level: Level for rarity scaling
    
    Returns:
        List of created entity IDs
    """
    loot_table = data_loader.get_loot_table(loot_table_id)
    if not loot_table:
        return []
    
    entities = []
    
    # Gold drop
    gold_config = loot_table.get("gold", {})
    if gold_config:
        gold_min = gold_config.get("min", 1)
        gold_max = gold_config.get("max", 5)
        gold_amount = roll_gold_drop(gold_min, gold_max, dungeon_level)
        if gold_amount > 0:
            # Offset position slightly
            gx = x + random.uniform(-0.3, 0.3)
            gy = y + random.uniform(-0.3, 0.3)
            entities.append(create_gold_drop(gold_amount, gx, gy))
    
    # Item drops
    drops = loot_table.get("drops", [])
    for drop in drops:
        chance = drop.get("chance", 0.1)
        if random.random() < chance:
            # Direct item drop
            if "item" in drop:
                item_id = drop["item"]
                ix = x + random.uniform(-0.3, 0.3)
                iy = y + random.uniform(-0.3, 0.3)
                entities.append(create_item_drop(item_id, ix, iy))
            
            # Table reference
            elif "table" in drop:
                sub_table_id = drop["table"]
                sub_table = data_loader.get_loot_table(sub_table_id)
                if sub_table and "items" in sub_table:
                    # Weighted random selection
                    items = sub_table["items"]
                    total_weight = sum(i.get("weight", 1) for i in items)
                    roll = random.uniform(0, total_weight)
                    
                    cumulative = 0
                    for item in items:
                        cumulative += item.get("weight", 1)
                        if roll <= cumulative:
                            item_id = item["id"]
                            ix = x + random.uniform(-0.3, 0.3)
                            iy = y + random.uniform(-0.3, 0.3)
                            
                            # Check for rarity override
                            item_data = {}
                            if "rarity_override" in item:
                                item_data["rarity"] = item["rarity_override"]
                            
                            entities.append(create_item_drop(
                                item_id, ix, iy, data=item_data
                            ))
                            break
    
    return entities

