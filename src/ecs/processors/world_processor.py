"""World processor - handles stairs, level transitions, and world interactions."""

import esper

from ..components import Position, PartyMember, PlayerControlled, Selected
from ...core.events import EventBus, Event, EventType
from ...core.constants import TileType


class WorldProcessor(esper.Processor):
    """Handles world interactions like stairs and level transitions.
    
    Stairs now require pressing E key instead of automatic triggering.
    """
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.dungeon = None
        self.use_stairs_requested = False  # Set by input when E is pressed
        
        # Cooldown to prevent rapid level changes
        self.stairs_cooldown = 0.5
    
    def set_dungeon(self, dungeon):
        """Set the dungeon reference."""
        self.dungeon = dungeon
    
    def request_use_stairs(self):
        """Called by input processor when player presses E."""
        self.use_stairs_requested = True
    
    def process(self, dt: float):
        """Check for stairs interactions."""
        if not self.dungeon:
            return
        
        # Update cooldown
        if self.stairs_cooldown > 0:
            self.stairs_cooldown -= dt
        
        # Only check stairs if player pressed E
        if not self.use_stairs_requested:
            return
        
        self.use_stairs_requested = False
        
        # Don't allow if cooldown active
        if self.stairs_cooldown > 0:
            return
        
        # Check if selected party member is on stairs
        for ent, (pos, _, _) in esper.get_components(Position, PartyMember, Selected):
            tile_x = int(pos.x)
            tile_y = int(pos.y)
            
            tile = self.dungeon.get_tile(tile_x, tile_y)
            
            if tile == TileType.STAIRS_DOWN:
                self._request_level_change(1)
                return
            
            elif tile == TileType.STAIRS_UP:
                self._request_level_change(-1)
                return
            
            else:
                # Not on stairs
                self.event_bus.emit(Event(EventType.NOTIFICATION, {
                    "text": "No stairs here",
                    "color": (200, 150, 150)
                }))
    
    def _request_level_change(self, direction: int):
        """Request a level change."""
        self.stairs_cooldown = 0.5  # Half second cooldown
        
        self.event_bus.emit(Event(EventType.STAIRS_USED, {
            "direction": direction
        }))
        
        if direction > 0:
            self.event_bus.emit(Event(EventType.NOTIFICATION, {
                "text": "Descending deeper...",
                "color": (180, 150, 220)
            }))
        else:
            self.event_bus.emit(Event(EventType.NOTIFICATION, {
                "text": "Ascending...",
                "color": (220, 200, 150)
            }))


class DroppedItemProcessor(esper.Processor):
    """Handles dropped items - despawning, glow animation, auto-pickup."""
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
    
    def process(self, dt: float):
        """Update dropped items."""
        from ..components import DroppedItem, Inventory as InventoryComp
        from ...core.formulas import distance
        
        # Update all dropped items
        items_to_remove = []
        
        for ent, (pos, dropped) in esper.get_components(Position, DroppedItem):
            # Update glow animation
            dropped.glow_timer += dt
            if dropped.glow_timer > 2.0:
                dropped.glow_timer = 0.0
            
            # Update despawn timer
            dropped.despawn_timer -= dt
            if dropped.despawn_timer <= 0:
                items_to_remove.append(ent)
                continue
            
            # Check for auto-pickup (gold only)
            if hasattr(dropped, 'is_gold') and dropped.is_gold:
                for player_ent, (player_pos, _) in esper.get_components(Position, PartyMember):
                    dist = distance(pos.x, pos.y, player_pos.x, player_pos.y)
                    if dist < 1.5:  # Auto-pickup range
                        # Pickup gold
                        from ..components import Gold
                        if esper.has_component(player_ent, Gold):
                            gold = esper.component_for_entity(player_ent, Gold)
                            gold.amount += getattr(dropped, 'gold_amount', 0)
                            
                            self.event_bus.emit(Event(EventType.GOLD_CHANGED, {
                                "entity": player_ent,
                                "amount": getattr(dropped, 'gold_amount', 0)
                            }))
                        
                        items_to_remove.append(ent)
                        break
        
        # Remove expired/picked up items
        for ent in items_to_remove:
            if esper.entity_exists(ent):
                esper.delete_entity(ent)

