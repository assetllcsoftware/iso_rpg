"""Loot processor - handles item pickup and drops."""

import esper

from ..components import (
    Position, Inventory, Gold, ItemDrop, GoldDrop, PickupRadius,
    PartyMember, Enemy, Dead, Loot
)
from ..components.ai import EnemyAI
from ..components.tags import ToRemove
from ..factories.items import roll_loot_drops
from ...core.events import EventBus, Event, EventType
from ...core.formulas import distance


class LootProcessor(esper.Processor):
    """Handles loot dropping and pickup."""
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        
        # Subscribe to enemy death
        event_bus.subscribe(EventType.ENTITY_DIED, self._on_entity_died)
        
        # Track dungeon level for loot scaling
        self.dungeon_level = 1
    
    def _on_entity_died(self, event: Event):
        """Handle enemy death - drop loot."""
        ent = event.data.get("entity", -1)
        if ent < 0:
            return
        
        if not esper.has_component(ent, Enemy):
            return
        
        if not esper.has_component(ent, Position):
            return
        
        pos = esper.component_for_entity(ent, Position)
        
        # Get enemy type for loot table
        enemy_type = "skeleton"
        if esper.has_component(ent, EnemyAI):
            enemy_type = esper.component_for_entity(ent, EnemyAI).enemy_type
        
        loot_table_id = f"{enemy_type}_loot"
        
        # Roll loot
        roll_loot_drops(loot_table_id, pos.x, pos.y, self.dungeon_level)
    
    def process(self, dt: float):
        """Process loot pickup."""
        # Get all party member positions
        party_positions = []
        party_inventories = []
        party_gold = []
        
        for ent, (pos, member) in esper.get_components(Position, PartyMember):
            inv = None
            gold_comp = None
            if esper.has_component(ent, Inventory):
                inv = esper.component_for_entity(ent, Inventory)
            if esper.has_component(ent, Gold):
                gold_comp = esper.component_for_entity(ent, Gold)
            
            party_positions.append((ent, pos))
            party_inventories.append(inv)
            party_gold.append(gold_comp)
        
        # Check loot entities
        for loot_ent, (pos, pickup) in esper.get_components(Position, PickupRadius):
            if not esper.has_component(loot_ent, Loot):
                continue
            
            # Check distance to each party member
            for i, (party_ent, party_pos) in enumerate(party_positions):
                dist = distance(pos.x, pos.y, party_pos.x, party_pos.y)
                
                if dist <= pickup.radius:
                    # Pick up!
                    if esper.has_component(loot_ent, ItemDrop):
                        item_drop = esper.component_for_entity(loot_ent, ItemDrop)
                        
                        if party_inventories[i]:
                            added = party_inventories[i].add(
                                item_drop.item_id,
                                item_drop.quantity,
                                item_drop.data
                            )
                            
                            if added:
                                esper.add_component(loot_ent, ToRemove())
                                self.event_bus.emit(Event(EventType.ITEM_PICKED_UP, {
                                    "entity": party_ent,
                                    "item_id": item_drop.item_id,
                                    "quantity": item_drop.quantity
                                }))
                    
                    elif esper.has_component(loot_ent, GoldDrop):
                        gold_drop = esper.component_for_entity(loot_ent, GoldDrop)
                        
                        if party_gold[i]:
                            party_gold[i].amount += gold_drop.amount
                            esper.add_component(loot_ent, ToRemove())
                            
                            self.event_bus.emit(Event(EventType.GOLD_CHANGED, {
                                "entity": party_ent,
                                "amount": gold_drop.amount,
                                "total": party_gold[i].amount
                            }))
                    
                    break  # Only one party member picks up
