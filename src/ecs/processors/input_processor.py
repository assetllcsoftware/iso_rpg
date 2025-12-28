"""Input processor - handles player input and converts to intents."""

import pygame
import esper

from ..components import (
    Position, MoveIntent, TargetPosition, AttackIntent, CastIntent,
    PlayerControlled, Selected, Facing, Direction, PartyMember, SpellBook,
    Enemy, Dead, Downed, Health
)
from ...core.events import EventBus, Event, EventType
from ...core.formulas import distance


# Spell key bindings per party member (party_index -> key list)
SPELL_KEY_BINDINGS = {
    0: [pygame.K_q, pygame.K_w, pygame.K_e, pygame.K_r, pygame.K_t],  # Hero
    1: [pygame.K_a, pygame.K_s, pygame.K_d, pygame.K_f, pygame.K_g],  # Lyra
    2: [pygame.K_z, pygame.K_x, pygame.K_c, pygame.K_v, pygame.K_b],  # Third member
}


class InputProcessor(esper.Processor):
    """Processes player input and converts to component-based intents.
    
    This processor reads input and sets intent components - it does NOT
    execute the actions. Other processors (MovementProcessor, CombatProcessor)
    read those intents.
    """
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        
        # Input state
        self.keys_held = set()
        self.mouse_pos = (0, 0)
        self.mouse_buttons = [False, False, False]  # Left, Middle, Right
        self.mouse_clicked = [False, False, False]
        
        # Camera reference (set by game)
        self.camera = None
        
        # Save/load processor reference (set by game)
        self.save_load_processor = None
        
        # World processor reference (set by game) for stairs
        self.world_processor = None
        
        # Dungeon reference for LOS checks
        self.dungeon = None
    
    def set_dungeon(self, dungeon):
        """Set dungeon reference for LOS checks."""
        self.dungeon = dungeon
    
    def handle_event(self, event: pygame.event.Event):
        """Called from game loop to process pygame events."""
        if event.type == pygame.KEYDOWN:
            self.keys_held.add(event.key)
            self._handle_key_press(event.key)
        
        elif event.type == pygame.KEYUP:
            self.keys_held.discard(event.key)
        
        elif event.type == pygame.MOUSEMOTION:
            self.mouse_pos = event.pos
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            self.mouse_buttons[event.button - 1] = True
            self.mouse_clicked[event.button - 1] = True
        
        elif event.type == pygame.MOUSEBUTTONUP:
            self.mouse_buttons[event.button - 1] = False
        
        elif event.type == pygame.MOUSEWHEEL:
            self._handle_scroll(event.y)
    
    def _handle_key_press(self, key: int):
        """Handle single key press events."""
        # Check spell keys for all party members
        for party_idx, keys in SPELL_KEY_BINDINGS.items():
            if key in keys:
                slot = keys.index(key)
                self._try_cast_spell_for_party_member(party_idx, slot)
                return
        
        # Game controls
        if key == pygame.K_ESCAPE:
            self.event_bus.emit(Event(EventType.GAME_PAUSED))
        elif key == pygame.K_i:
            self.event_bus.emit(Event(EventType.MENU_OPENED, {"menu": "inventory"}))
        elif key == pygame.K_k:
            self.event_bus.emit(Event(EventType.MENU_OPENED, {"menu": "skill_tree"}))
        elif key == pygame.K_m:
            self.event_bus.emit(Event(EventType.MENU_OPENED, {"menu": "map"}))
        elif key == pygame.K_TAB:
            self._cycle_character_selection()
        elif key == pygame.K_1:
            # 1 = Health potion
            self._use_action_bar_slot(0)
        elif key == pygame.K_2:
            # 2 = Mana potion
            self._use_action_bar_slot(1)
        elif key == pygame.K_SPACE:
            # Space tries to use stairs first, then attacks if not on stairs
            self._use_stairs_or_attack()
        elif key == pygame.K_g:
            self._pickup_items()
        elif key == pygame.K_RETURN or key == pygame.K_KP_ENTER:
            self._use_stairs()
        elif key == pygame.K_F5:
            self.event_bus.emit(Event(EventType.GAME_SAVE_REQUESTED))
        elif key == pygame.K_F9:
            self.event_bus.emit(Event(EventType.GAME_LOAD_REQUESTED))
        # Action bar keys (1-8) - use from action bar, not party select
        elif key >= pygame.K_1 and key <= pygame.K_8:
            # This is handled by party member select above for 1-3
            # Action bar slots 4-8 will be handled by action bar
            action_slot = key - pygame.K_1
            if action_slot >= 3:  # 1-3 are party, 4-8 are action bar
                self.event_bus.emit(Event(EventType.ACTION_BAR_USED, {
                    "slot": action_slot
                }))
    
    def _handle_scroll(self, direction: int):
        """Handle mouse wheel scroll."""
        self.event_bus.emit(Event(EventType.CAMERA_ZOOMED, {
            "direction": direction
        }))
    
    def _try_cast_spell_for_party_member(self, party_idx: int, slot: int):
        """Attempt to cast spell in given slot for a specific party member."""
        # Find the party member with this index
        for ent, (member,) in esper.get_components(PartyMember):
            if member.party_index == party_idx:
                # Check if they have a spellbook with a spell in this slot
                if esper.has_component(ent, SpellBook):
                    spellbook = esper.component_for_entity(ent, SpellBook)
                    spells = list(spellbook.known_spells)
                    if slot < len(spells):
                        # Get target from mouse position
                        world_x, world_y = self._screen_to_world(self.mouse_pos)
                        target_id = self._get_entity_at(world_x, world_y)
                        
                        self.event_bus.emit(Event(EventType.SPELL_CAST_REQUESTED, {
                            "caster": ent,
                            "spell_id": spells[slot],
                            "slot": slot,
                            "target_id": target_id,
                            "target_x": world_x,
                            "target_y": world_y
                        }))
                return
    
    def _select_party_member(self, party_idx: int):
        """Select a specific party member by index."""
        self.event_bus.emit(Event(EventType.CHARACTER_SELECTED, {
            "party_index": party_idx
        }))
    
    def _cycle_character_selection(self):
        """Cycle selection to next party member."""
        self.event_bus.emit(Event(EventType.CHARACTER_SELECTED, {
            "cycle": True
        }))
    
    def _use_action_bar_slot(self, slot: int):
        """Use an item/spell from the action bar."""
        self.event_bus.emit(Event(EventType.ACTION_BAR_USED, {
            "slot": slot
        }))
    
    def _attack_nearest_enemy(self):
        """Attack the nearest enemy to the selected character."""
        # Find selected character
        for ent, (pos, _, _) in esper.get_components(Position, PlayerControlled, Selected):
            nearest_enemy = self._find_nearest_enemy(pos)
            if nearest_enemy >= 0:
                if esper.has_component(ent, AttackIntent):
                    attack = esper.component_for_entity(ent, AttackIntent)
                    attack.target_id = nearest_enemy
                else:
                    esper.add_component(ent, AttackIntent(target_id=nearest_enemy))
            return
    
    def _find_nearest_enemy(self, player_pos) -> int:
        """Find nearest enemy to position."""
        nearest = -1
        nearest_dist = 15.0  # Max targeting range
        
        for ent, (pos, _) in esper.get_components(Position, Enemy):
            # Skip dead enemies
            if esper.has_component(ent, Dead) or esper.has_component(ent, Downed):
                continue
            
            dist = distance(player_pos.x, player_pos.y, pos.x, pos.y)
            if dist < nearest_dist:
                # Check line of sight - can't target through walls
                if self.dungeon and not self.dungeon.has_line_of_sight(
                    player_pos.x, player_pos.y, pos.x, pos.y
                ):
                    continue
                
                nearest_dist = dist
                nearest = ent
        
        return nearest
    
    def _use_stairs(self):
        """Request to use stairs."""
        if self.world_processor:
            self.world_processor.request_use_stairs()
    
    def _use_stairs_or_attack(self):
        """Try to use stairs if on them, otherwise attack nearest enemy."""
        # Check if standing on stairs
        from ...core.constants import TileType
        
        on_stairs = False
        if self.world_processor and self.world_processor.dungeon:
            for ent, (pos, _, _) in esper.get_components(Position, PlayerControlled, Selected):
                tile_x = int(pos.x)
                tile_y = int(pos.y)
                tile = self.world_processor.dungeon.get_tile(tile_x, tile_y)
                if tile in (TileType.STAIRS_UP, TileType.STAIRS_DOWN):
                    on_stairs = True
                break
        
        if on_stairs:
            self._use_stairs()
        else:
            self._attack_nearest_enemy()
    
    def _pickup_items(self):
        """Pickup nearby dropped items."""
        from ..components import DroppedItem, Inventory as InventoryComp
        
        # Find selected character
        for ent, (pos, _, _) in esper.get_components(Position, PlayerControlled, Selected):
            pickup_radius = 2.0
            
            # Find nearby dropped items
            items_to_pickup = []
            for item_ent, (item_pos, dropped) in esper.get_components(Position, DroppedItem):
                dist = distance(pos.x, pos.y, item_pos.x, item_pos.y)
                if dist <= pickup_radius:
                    items_to_pickup.append((dist, item_ent, dropped))
            
            # Sort by distance (closest first)
            items_to_pickup.sort(key=lambda x: x[0])
            
            # Pickup items
            for _, item_ent, dropped in items_to_pickup:
                if not esper.has_component(ent, InventoryComp):
                    continue
                
                inv = esper.component_for_entity(ent, InventoryComp)
                
                # Check weight
                if hasattr(dropped, 'item') and dropped.item:
                    item_weight = getattr(dropped.item, 'weight', 1)
                    if inv.current_weight + item_weight > inv.max_weight:
                        self.event_bus.emit(Event(EventType.NOTIFICATION, {
                            "text": "Inventory full!",
                            "color": (255, 200, 100)
                        }))
                        break
                    
                    # Add to inventory
                    inv.items.append(dropped.item)
                    inv.current_weight += item_weight
                    
                    item_name = getattr(dropped.item, 'name', 'Item')
                    self.event_bus.emit(Event(EventType.ITEM_PICKED_UP, {
                        "entity": ent,
                        "item": item_name
                    }))
                    self.event_bus.emit(Event(EventType.NOTIFICATION, {
                        "text": f"Picked up {item_name}",
                        "color": (255, 255, 150)
                    }))
                
                # Remove dropped item entity
                esper.delete_entity(item_ent)
            
            return
    
    def _screen_to_world(self, screen_pos: tuple) -> tuple:
        """Convert screen coordinates to world coordinates."""
        if self.camera:
            return self.camera.screen_to_world(screen_pos[0], screen_pos[1])
        return (0.0, 0.0)
    
    def _get_entity_at(self, world_x: float, world_y: float) -> int:
        """Get entity ID at world position, or -1 if none."""
        from ...core.formulas import distance
        from ..components import Health, CollisionRadius
        
        closest = -1
        closest_dist = 2.0  # Max click radius (2 tiles - generous for clicking)
        
        for ent, (pos,) in esper.get_components(Position):
            # Skip entities without health (probably not targetable)
            if not esper.has_component(ent, Health):
                continue
            
            # Get collision radius for better clicking
            entity_radius = 0.5
            if esper.has_component(ent, CollisionRadius):
                entity_radius = esper.component_for_entity(ent, CollisionRadius).radius
            
            dist = distance(pos.x, pos.y, world_x, world_y)
            # Use entity radius to make clicking easier
            effective_dist = dist - entity_radius
            
            if effective_dist < closest_dist:
                closest_dist = effective_dist
                closest = ent
        
        return closest
    
    def process(self, dt: float):
        """Process input each frame."""
        # Get player-controlled entities
        for ent, (pos, _, selected) in esper.get_components(Position, PlayerControlled, Selected):
            # Arrow keys for movement
            dx, dy = 0.0, 0.0
            
            if pygame.K_UP in self.keys_held:
                dy -= 1.0
            if pygame.K_DOWN in self.keys_held:
                dy += 1.0
            if pygame.K_LEFT in self.keys_held:
                dx -= 1.0
            if pygame.K_RIGHT in self.keys_held:
                dx += 1.0
            
            # Normalize diagonal movement
            if dx != 0 and dy != 0:
                dx *= 0.707
                dy *= 0.707
            
            # Set move intent
            if esper.has_component(ent, MoveIntent):
                move = esper.component_for_entity(ent, MoveIntent)
                move.dx = dx
                move.dy = dy
            else:
                esper.add_component(ent, MoveIntent(dx=dx, dy=dy))
            
            # Update facing direction
            if dx != 0 or dy != 0:
                if esper.has_component(ent, Facing):
                    facing = esper.component_for_entity(ent, Facing)
                    if abs(dx) > abs(dy):
                        facing.direction = Direction.RIGHT if dx > 0 else Direction.LEFT
                    else:
                        facing.direction = Direction.DOWN if dy > 0 else Direction.UP
            
            # Right-click to move to position
            if self.mouse_clicked[2]:  # Right click
                world_x, world_y = self._screen_to_world(self.mouse_pos)
                
                if esper.has_component(ent, TargetPosition):
                    target = esper.component_for_entity(ent, TargetPosition)
                    target.x = world_x
                    target.y = world_y
                else:
                    esper.add_component(ent, TargetPosition(x=world_x, y=world_y))
            
            # Left-click to attack
            if self.mouse_clicked[0]:  # Left click
                world_x, world_y = self._screen_to_world(self.mouse_pos)
                target_id = self._get_entity_at(world_x, world_y)
                
                if target_id >= 0 and target_id != ent:
                    if esper.has_component(ent, AttackIntent):
                        attack = esper.component_for_entity(ent, AttackIntent)
                        attack.target_id = target_id
                    else:
                        esper.add_component(ent, AttackIntent(target_id=target_id))
        
        # Clear single-frame inputs
        self.mouse_clicked = [False, False, False]
