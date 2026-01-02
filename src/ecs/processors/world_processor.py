"""World processor - handles stairs, level transitions, room activation, and world interactions."""

import esper
import random

from ..components import Position, PartyMember, PlayerControlled, Selected, Dead
from ...core.events import EventBus, Event, EventType
from ...core.constants import TileType


class WorldProcessor(esper.Processor):
    """Handles world interactions like stairs and level transitions.
    
    Also handles room-based enemy spawning.
    """
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.dungeon = None
        self.dungeon_level = 1
        self.use_stairs_requested = False  # Set by input when E is pressed
        
        # Cooldown to prevent rapid level changes
        self.stairs_cooldown = 0.5
        
        # Room activation check throttle
        self.room_check_timer = 0.0
    
    def set_dungeon(self, dungeon):
        """Set the dungeon reference."""
        self.dungeon = dungeon
    
    def set_dungeon_level(self, level: int):
        """Set current dungeon level for enemy scaling."""
        self.dungeon_level = level
    
    def request_use_stairs(self):
        """Called by input processor when player presses E."""
        self.use_stairs_requested = True
    
    def process(self, dt: float):
        """Check for stairs and room activations."""
        if not self.dungeon:
            return
        
        # Update cooldown
        if self.stairs_cooldown > 0:
            self.stairs_cooldown -= dt
        
        # Check room activation every 0.2 seconds
        self.room_check_timer += dt
        if self.room_check_timer >= 0.2:
            self.room_check_timer = 0.0
            self._check_room_activation()
        
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
    
    def _check_room_activation(self):
        """Check if any party member entered a new room and spawn enemies."""
        for ent, (pos, _) in esper.get_components(Position, PartyMember):
            if esper.has_component(ent, Dead):
                continue
            
            room_idx = self.dungeon.get_room_at(pos.x, pos.y)
            if room_idx is not None and not self.dungeon.is_room_activated(room_idx):
                spawn_points = self.dungeon.activate_room(room_idx)
                
                if spawn_points:
                    self._spawn_room_enemies(spawn_points, room_idx)
    
    def _spawn_room_enemies(self, spawn_points: list, room_idx: int):
        """Spawn enemies at the given spawn points."""
        from ..factories.enemies import create_enemy
        
        # Enemy types by level
        enemy_tables = {
            (1, 3): [("skeleton", 60), ("goblin", 25), ("spider", 15)],
            (4, 6): [("skeleton", 40), ("goblin", 20), ("zombie", 25), ("orc", 15)],
            (7, 99): [("skeleton", 25), ("zombie", 25), ("orc", 25), ("demon", 25)],
        }
        
        # Find appropriate enemy table
        enemies = [("skeleton", 100)]
        for (min_lvl, max_lvl), table in enemy_tables.items():
            if min_lvl <= self.dungeon_level <= max_lvl:
                enemies = table
                break
        
        # Spawn enemies at each point
        for x, y in spawn_points:
            # Random enemy from table
            total_weight = sum(w for _, w in enemies)
            roll = random.randint(1, total_weight)
            cumulative = 0
            enemy_id = "skeleton"
            
            for eid, weight in enemies:
                cumulative += weight
                if roll <= cumulative:
                    enemy_id = eid
                    break
            
            create_enemy(enemy_id, x + 0.5, y + 0.5, self.dungeon_level)
        
        # Notification
        room = self.dungeon.rooms[room_idx]
        self.event_bus.emit(Event(EventType.NOTIFICATION, {
            "text": f"Enemies appeared!",
            "color": (255, 100, 100)
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

