"""Shop UI - buy/sell interface reusing the InventoryUI."""

import pygame
import esper
from typing import Optional, List, Dict, Tuple

from ..core.constants import (
    COLOR_UI_BG, COLOR_UI_BORDER, COLOR_UI_ACCENT,
    COLOR_TEXT, COLOR_TEXT_DIM, COLOR_GOLD, RARITY_COLORS
)
from ..core.events import EventBus, Event, EventType
from ..ecs.components import (
    PartyMember, Gold, Inventory as InventoryComp, Equipment, CharacterName
)
from ..data.loader import data_loader
from .inventory import InventoryUI


class ShopUI:
    """Shop interface - left side shows stock, right side uses InventoryUI."""
    
    def __init__(self, screen: pygame.Surface, event_bus: EventBus):
        self.screen = screen
        self.event_bus = event_bus
        self.visible = False
        self.shop_type = 'blacksmith'  # 'blacksmith', 'alchemist'
        self.dungeon_level = 1
        
        # Embed the real InventoryUI for the right panel
        self.inventory_ui = InventoryUI(screen)
        self.inventory_ui.sell_mode = True  # We'll add this flag
        
        # Selection state for shop panel
        self.hover_shop_idx = -1
        self.shop_scroll = 0
        
        # Fonts
        pygame.font.init()
        self.font = pygame.font.Font(None, 28)
        self.font_small = pygame.font.Font(None, 22)
        self.font_title = pygame.font.Font(None, 36)
        
        # Layout - will be recalculated in render()
        self.left_panel = pygame.Rect(0, 0, 400, 500)
        
        # Generate shop inventory
        self.shop_items: List[dict] = []
    
    def show(self, shop_type: str, dungeon_level: int = 1):
        """Open shop UI."""
        self.visible = True
        self.shop_type = shop_type
        self.dungeon_level = dungeon_level
        self.shop_scroll = 0
        self.hover_shop_idx = -1
        
        # Show embedded inventory UI
        self.inventory_ui.visible = True
        self.inventory_ui.sell_mode = True
        self.inventory_ui._refresh_party()
        
        # Ensure selected entity is valid
        if self.inventory_ui.party_entities:
            if self.inventory_ui.selected_entity not in self.inventory_ui.party_entities:
                self.inventory_ui.selected_entity = self.inventory_ui.party_entities[0]
        
        self._generate_shop_inventory()
    
    def hide(self):
        """Close shop UI."""
        self.visible = False
        self.inventory_ui.visible = False
        self.inventory_ui.sell_mode = False
    
    def _generate_shop_inventory(self):
        """Generate items for sale based on shop type and level."""
        self.shop_items = []
        all_items = data_loader.get_all_items()
        
        for item_id, item_data in all_items.items():
            item_type = item_data.get('type', '')
            
            # Filter by shop type
            if self.shop_type == 'blacksmith':
                if item_type not in ('weapon', 'armor', 'accessory'):
                    continue
            elif self.shop_type == 'alchemist':
                if item_type != 'consumable':
                    continue
            
            # Check level requirement
            min_level = item_data.get('min_level', 1)
            
            # Show items within level range
            if min_level <= self.dungeon_level + 3:
                base_value = item_data.get('value', 10)
                buy_price = int(base_value * 1.5)  # 150% markup
                
                self.shop_items.append({
                    'id': item_id,
                    'name': item_data.get('name', item_id),
                    'type': item_type,
                    'slot': item_data.get('slot', ''),
                    'price': buy_price,
                    'rarity': item_data.get('rarity', 0),
                    'damage': item_data.get('damage', 0),
                    'armor': item_data.get('armor', 0),
                    'effect_type': item_data.get('effect_type', ''),
                    'effect_value': item_data.get('effect_value', 0),
                })
        
        # Sort by rarity then price
        self.shop_items.sort(key=lambda i: (i['rarity'], i['price']))
    
    def _get_player_gold(self) -> int:
        """Get player's current gold."""
        for ent, (member, gold) in esper.get_components(PartyMember, Gold):
            if member.party_index == 0:
                return gold.amount
        return 0
    
    def _get_player_inventory(self) -> List[Tuple[int, dict]]:
        """Get player's inventory items with sell prices."""
        items = []
        
        for ent, (member,) in esper.get_components(PartyMember):
            if member.party_index == 0 and esper.has_component(ent, InventoryComp):
                inv = esper.component_for_entity(ent, InventoryComp)
                for idx, inv_item in enumerate(inv.items):
                    item_data = data_loader.get_item(inv_item.item_id)
                    if item_data:
                        base_value = item_data.get('value', 10)
                        sell_price = max(1, int(base_value * 0.5))  # 50% of value
                        
                        items.append((idx, {
                            'id': inv_item.item_id,
                            'name': item_data.get('name', inv_item.item_id),
                            'type': item_data.get('type', ''),
                            'price': sell_price,
                            'quantity': inv_item.quantity,
                            'rarity': item_data.get('rarity', 0),
                        }))
                break
        
        return items
    
    def _buy_item(self, item: dict):
        """Buy an item from the shop - adds to currently selected character."""
        price = item['price']
        
        # Get gold from party leader
        for ent, (member, gold) in esper.get_components(PartyMember, Gold):
            if member.party_index == 0:
                if gold.amount >= price:
                    gold.amount -= price
                    
                    # Add to currently selected character's inventory
                    target_ent = self.inventory_ui.selected_entity
                    if target_ent >= 0 and esper.has_component(target_ent, InventoryComp):
                        inv = esper.component_for_entity(target_ent, InventoryComp)
                        inv.add(item['id'], 1)
                        
                        # Get character name for notification
                        char_name = "inventory"
                        if esper.has_component(target_ent, CharacterName):
                            char_name = esper.component_for_entity(target_ent, CharacterName).name + "'s inventory"
                        
                        self.event_bus.emit(Event(EventType.NOTIFICATION, {
                            "text": f"Bought {item['name']} → {char_name}",
                            "color": (100, 255, 100)
                        }))
                    else:
                        self.event_bus.emit(Event(EventType.NOTIFICATION, {
                            "text": f"Bought {item['name']}",
                            "color": (100, 255, 100)
                        }))
                else:
                    self.event_bus.emit(Event(EventType.NOTIFICATION, {
                        "text": "Not enough gold!",
                        "color": (255, 100, 100)
                    }))
                return
    
    def _sell_item(self, entity: int, inv_idx: int):
        """Sell an item from a specific entity's inventory."""
        if not esper.has_component(entity, InventoryComp):
            return
            
        inv = esper.component_for_entity(entity, InventoryComp)
        if inv_idx >= len(inv.items):
            return
        
        inv_item = inv.items[inv_idx]
        item_id = inv_item.item_id if hasattr(inv_item, 'item_id') else str(inv_item)
        item_data = data_loader.get_item(item_id) or {}
        
        # Calculate sell price (50% of value)
        value = item_data.get('value', 10)
        price = max(1, value // 2)
        
        # Add gold to party leader
        for ent, (member, gold) in esper.get_components(PartyMember, Gold):
            if member.party_index == 0:
                gold.amount += price
                break
        
        # Remove item
        item_name = item_data.get('name', item_id)
        inv_item.quantity -= 1
        if inv_item.quantity <= 0:
            inv.items.pop(inv_idx)
        
        self.event_bus.emit(Event(EventType.NOTIFICATION, {
            "text": f"Sold {item_name} for {price}g",
            "color": (255, 215, 0)
        }))
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle input events."""
        if not self.visible:
            return False
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.hide()
                return True
            # Tab to switch party members
            elif event.key == pygame.K_TAB:
                if len(self.inventory_ui.party_entities) > 1:
                    self.inventory_ui._cycle_party_member()
                    # Show which character is now selected
                    ent = self.inventory_ui.selected_entity
                    if ent >= 0 and esper.has_component(ent, CharacterName):
                        name = esper.component_for_entity(ent, CharacterName).name
                        self.event_bus.emit(Event(EventType.NOTIFICATION, {
                            "text": f"Viewing {name}'s inventory",
                            "color": (150, 200, 255)
                        }))
                return True
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                return self._handle_click(event.pos)
            elif event.button == 4:  # Scroll up
                if self.left_panel.collidepoint(event.pos):
                    self.shop_scroll = max(0, self.shop_scroll - 1)
                return True
            elif event.button == 5:  # Scroll down
                if self.left_panel.collidepoint(event.pos):
                    self.shop_scroll = min(len(self.shop_items) - 1, self.shop_scroll + 1)
                return True
        
        elif event.type == pygame.MOUSEWHEEL:
            mouse_pos = pygame.mouse.get_pos()
            if self.left_panel.collidepoint(mouse_pos):
                self.shop_scroll = max(0, self.shop_scroll - event.y)
            return True
        
        elif event.type == pygame.MOUSEMOTION:
            self._update_hover(event.pos)
            # Update inventory hover for tooltip
            self.inventory_ui._update_hover(event.pos)
        
        return True  # Consume all events when visible
    
    def _handle_click(self, pos: Tuple[int, int]) -> bool:
        """Handle mouse click."""
        screen_w, screen_h = self.screen.get_size()
        
        # Check party tabs in inventory UI
        for i, ent in enumerate(self.inventory_ui.party_entities):
            tab_rect = pygame.Rect(
                self.inventory_ui.right_panel.x + i * 80, 
                self.inventory_ui.right_panel.y - 35,
                75, 30
            )
            if tab_rect.collidepoint(pos):
                self.inventory_ui.selected_entity = ent
                return True
        
        # Check shop items (left panel - list view)
        if self.left_panel.collidepoint(pos):
            item_height = 55
            start_y = self.left_panel.y + 60
            
            for i, item in enumerate(self.shop_items[self.shop_scroll:self.shop_scroll + 7]):
                item_rect = pygame.Rect(
                    self.left_panel.x + 10,
                    start_y + i * item_height,
                    self.left_panel.width - 20,
                    item_height - 5
                )
                if item_rect.collidepoint(pos):
                    self._buy_item(item)
                    return True
        
        # Check inventory slots for selling
        for i, rect in enumerate(self.inventory_ui.inv_slots):
            if rect.collidepoint(pos):
                ent = self.inventory_ui.selected_entity
                if ent >= 0 and esper.has_component(ent, InventoryComp):
                    inv = esper.component_for_entity(ent, InventoryComp)
                    if i < len(inv.items):
                        self._sell_item(ent, i)
                        return True
        
        return True
    
    def _update_hover(self, pos: Tuple[int, int]):
        """Update hover state based on mouse position."""
        self.hover_shop_idx = -1
        
        # Check shop items (list view)
        if self.left_panel.collidepoint(pos):
            item_height = 55
            start_y = self.left_panel.y + 60
            for i in range(7):
                item_rect = pygame.Rect(
                    self.left_panel.x + 10,
                    start_y + i * item_height,
                    self.left_panel.width - 20,
                    item_height - 5
                )
                if item_rect.collidepoint(pos):
                    self.hover_shop_idx = self.shop_scroll + i
                    break
    
    def render(self):
        """Render shop UI with 3 panels: Shop | Equipment | Inventory."""
        if not self.visible:
            return
        
        screen_w, screen_h = self.screen.get_size()
        
        # 3-panel layout: Shop (left), Equipment (middle), Inventory (right)
        shop_w = 380
        equip_w = 280
        inv_w = 280
        panel_h = 500
        gap = 20
        
        total_w = shop_w + equip_w + inv_w + gap * 2
        start_x = (screen_w - total_w) // 2
        panel_y = (screen_h - panel_h) // 2
        
        self.left_panel = pygame.Rect(start_x, panel_y, shop_w, panel_h)
        self.equip_panel = pygame.Rect(start_x + shop_w + gap, panel_y, equip_w, panel_h)
        
        # Position the embedded inventory UI's right panel
        self.inventory_ui.right_panel = pygame.Rect(
            start_x + shop_w + equip_w + gap * 2,
            panel_y,
            inv_w,
            panel_h
        )
        # Re-setup inventory slots based on new position
        self.inventory_ui._setup_inv_slots()
        
        # Setup equipment slots for the middle panel
        self._setup_equip_panel_slots()
        
        # Dim background
        overlay = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        
        # Title
        shop_names = {
            'blacksmith': 'Blacksmith - Equipment',
            'alchemist': 'Alchemist - Potions'
        }
        title = self.font_title.render(shop_names.get(self.shop_type, 'Shop'), True, COLOR_TEXT)
        self.screen.blit(title, (screen_w // 2 - title.get_width() // 2, self.left_panel.y - 50))
        
        # Gold display
        gold = self._get_player_gold()
        gold_text = self.font.render(f"Gold: {gold}", True, COLOR_GOLD)
        self.screen.blit(gold_text, (screen_w // 2 - gold_text.get_width() // 2, self.left_panel.y - 20))
        
        # Party tabs (above equipment panel)
        self._render_party_tabs_top()
        
        # Left panel - Shop stock
        self._render_shop_panel()
        
        # Middle panel - Character equipment (what you're wearing)
        self._render_equipment_panel()
        
        # Right panel - Inventory grid
        self._render_inventory_with_tabs()
        
        # Instructions
        hint = self.font_small.render("Click item to buy/sell | TAB: switch character | ESC: close", True, COLOR_TEXT_DIM)
        self.screen.blit(hint, (screen_w // 2 - hint.get_width() // 2, self.left_panel.bottom + 15))
    
    def _setup_equip_panel_slots(self):
        """Setup equipment slot positions for the middle panel."""
        panel = self.equip_panel
        cx = panel.x + panel.width // 2
        cy = panel.y + 200
        slot_size = 44
        
        self.equip_slots = {
            'head': pygame.Rect(cx - 22, cy - 100, slot_size, slot_size),
            'amulet': pygame.Rect(cx + 35, cy - 70, slot_size, slot_size),
            'chest': pygame.Rect(cx - 22, cy - 40, slot_size, slot_size),
            'main_hand': pygame.Rect(cx - 75, cy - 30, slot_size, slot_size),
            'off_hand': pygame.Rect(cx + 35, cy - 30, slot_size, slot_size),
            'hands': pygame.Rect(cx - 75, cy + 25, slot_size, slot_size),
            'ring_1': pygame.Rect(cx - 75, cy + 80, slot_size, slot_size),
            'ring_2': pygame.Rect(cx + 35, cy + 80, slot_size, slot_size),
            'legs': pygame.Rect(cx - 22, cy + 25, slot_size, slot_size),
            'feet': pygame.Rect(cx - 22, cy + 80, slot_size, slot_size),
        }
    
    def _render_party_tabs_top(self):
        """Render party tabs above the equipment panel."""
        panel = self.equip_panel
        ent = self.inventory_ui.selected_entity
        
        for i, party_ent in enumerate(self.inventory_ui.party_entities):
            tab_rect = pygame.Rect(panel.x + i * 90, panel.y - 40, 85, 32)
            
            is_selected = party_ent == ent
            if is_selected:
                pygame.draw.rect(self.screen, (80, 70, 100), tab_rect, border_radius=6)
                pygame.draw.rect(self.screen, COLOR_UI_ACCENT, tab_rect, 2, border_radius=6)
            else:
                pygame.draw.rect(self.screen, (50, 45, 60), tab_rect, border_radius=6)
                pygame.draw.rect(self.screen, (80, 75, 95), tab_rect, 1, border_radius=6)
            
            # Character name
            name = "???"
            if esper.has_component(party_ent, CharacterName):
                name = esper.component_for_entity(party_ent, CharacterName).name
            name_surf = self.font_small.render(name[:10], True, COLOR_TEXT)
            self.screen.blit(name_surf, (tab_rect.x + 8, tab_rect.y + 9))
    
    def _render_equipment_panel(self):
        """Render the equipment/paperdoll panel in the middle."""
        from .icons import icon_generator
        
        panel = self.equip_panel
        ent = self.inventory_ui.selected_entity
        
        # Background
        pygame.draw.rect(self.screen, COLOR_UI_BG, panel, border_radius=10)
        pygame.draw.rect(self.screen, (100, 150, 100), panel, 2, border_radius=10)  # Green for equipped
        
        # Header with character name
        char_name = "Equipment"
        if ent >= 0 and esper.has_component(ent, CharacterName):
            char_name = f"{esper.component_for_entity(ent, CharacterName).name}'s Gear"
        header = self.font.render(char_name, True, COLOR_TEXT)
        self.screen.blit(header, (panel.x + 10, panel.y + 10))
        
        hint = self.font_small.render("(currently wearing)", True, COLOR_TEXT_DIM)
        self.screen.blit(hint, (panel.x + 10, panel.y + 32))
        
        # Get equipment
        equipment = None
        if ent >= 0 and esper.has_component(ent, Equipment):
            equipment = esper.component_for_entity(ent, Equipment)
        
        # Draw character silhouette
        cx = panel.x + panel.width // 2
        cy = panel.y + 200
        # Simple humanoid outline
        pygame.draw.circle(self.screen, (60, 60, 70), (cx, cy - 70), 25, 2)  # Head
        pygame.draw.line(self.screen, (60, 60, 70), (cx, cy - 45), (cx, cy + 40), 2)  # Body
        pygame.draw.line(self.screen, (60, 60, 70), (cx - 40, cy - 10), (cx + 40, cy - 10), 2)  # Arms
        pygame.draw.line(self.screen, (60, 60, 70), (cx, cy + 40), (cx - 20, cy + 100), 2)  # Left leg
        pygame.draw.line(self.screen, (60, 60, 70), (cx, cy + 40), (cx + 20, cy + 100), 2)  # Right leg
        
        # Draw equipment slots
        slot_labels = {
            'head': 'Head', 'amulet': 'Neck', 'chest': 'Chest',
            'main_hand': 'Weapon', 'off_hand': 'Shield',
            'hands': 'Gloves', 'legs': 'Legs', 'feet': 'Boots',
            'ring_1': 'Ring', 'ring_2': 'Ring'
        }
        
        for slot_name, rect in self.equip_slots.items():
            item_id = None
            if equipment:
                item_id = equipment.get(slot_name)
            
            # Slot background
            pygame.draw.rect(self.screen, (35, 30, 45), rect)
            pygame.draw.rect(self.screen, (80, 80, 90), rect, 1)
            
            if item_id:
                item_data = data_loader.get_item(item_id) or {}
                rarity = item_data.get('rarity', 0)
                rarity_color = RARITY_COLORS.get(rarity, (180, 180, 180))
                
                # Rarity border
                inner = rect.inflate(-4, -4)
                pygame.draw.rect(self.screen, (*rarity_color[:3], 100), inner)
                pygame.draw.rect(self.screen, rarity_color, inner, 2)
                
                # Icon
                icon_size = rect.width - 8
                icon = icon_generator.get_item_icon(item_id, rarity, icon_size)
                icon_rect = icon.get_rect(center=rect.center)
                self.screen.blit(icon, icon_rect)
                
                # Hover tooltip
                if rect.collidepoint(pygame.mouse.get_pos()):
                    pygame.draw.rect(self.screen, (255, 255, 255), rect, 2)
                    self._render_equip_tooltip(item_data, rect)
            else:
                # Empty slot label
                label = self.font_small.render(slot_labels.get(slot_name, slot_name)[:3], True, (80, 80, 90))
                self.screen.blit(label, (rect.x + 5, rect.y + rect.height // 2 - 6))
        
        # Stats summary at bottom
        self._render_stats_summary(panel, ent)
    
    def _render_equip_tooltip(self, item_data: dict, slot_rect: pygame.Rect):
        """Render tooltip for equipped item."""
        name = item_data.get('name', '???')
        rarity = item_data.get('rarity', 0)
        rarity_color = RARITY_COLORS.get(rarity, (180, 180, 180))
        damage = item_data.get('damage', 0)
        armor = item_data.get('armor', 0)
        
        lines = [name]
        line_colors = [rarity_color]
        
        if damage > 0:
            lines.append(f"Damage: {damage}")
            line_colors.append((255, 180, 100))
        if armor > 0:
            lines.append(f"Armor: {armor}")
            line_colors.append((150, 200, 255))
        
        # Calculate tooltip size
        padding = 8
        line_height = 20
        max_width = max(self.font_small.size(line)[0] for line in lines)
        tip_w = max_width + padding * 2
        tip_h = len(lines) * line_height + padding * 2
        
        # Position tooltip
        tip_x = slot_rect.right + 5
        tip_y = slot_rect.y
        
        # Keep on screen
        screen_w = self.screen.get_width()
        if tip_x + tip_w > screen_w - 10:
            tip_x = slot_rect.left - tip_w - 5
        
        # Draw tooltip
        tip_rect = pygame.Rect(tip_x, tip_y, tip_w, tip_h)
        pygame.draw.rect(self.screen, (20, 20, 30), tip_rect)
        pygame.draw.rect(self.screen, COLOR_UI_BORDER, tip_rect, 1)
        
        for i, (line, color) in enumerate(zip(lines, line_colors)):
            text = self.font_small.render(line, True, color)
            self.screen.blit(text, (tip_x + padding, tip_y + padding + i * line_height))
    
    def _render_stats_summary(self, panel: pygame.Rect, ent: int):
        """Render stats summary at bottom of equipment panel."""
        from ..ecs.components import Attributes
        
        if ent < 0 or not esper.entity_exists(ent):
            return
        
        y = panel.bottom - 100
        x = panel.x + 15
        
        # Calculate total stats from equipment
        total_armor = 0
        total_damage = 0
        
        if esper.has_component(ent, Equipment):
            equip = esper.component_for_entity(ent, Equipment)
            for slot_name, item_id in equip.slots.items():
                if item_id:
                    item_data = data_loader.get_item(item_id) or {}
                    total_armor += item_data.get('armor', 0)
                    total_damage += item_data.get('damage', 0)
        
        # Display
        stats_header = self.font_small.render("── Stats ──", True, COLOR_TEXT_DIM)
        self.screen.blit(stats_header, (panel.centerx - stats_header.get_width() // 2, y))
        
        y += 22
        armor_text = self.font_small.render(f"Total Armor: {total_armor}", True, (150, 200, 255))
        self.screen.blit(armor_text, (x, y))
        
        y += 18
        damage_text = self.font_small.render(f"Weapon Dmg: {total_damage}", True, (255, 180, 100))
        self.screen.blit(damage_text, (x, y))
    
    def _render_shop_panel(self):
        """Render shop stock panel."""
        panel = self.left_panel
        
        # Background
        pygame.draw.rect(self.screen, COLOR_UI_BG, panel, border_radius=10)
        pygame.draw.rect(self.screen, COLOR_UI_ACCENT, panel, 2, border_radius=10)
        
        # Header
        header = self.font.render("FOR SALE", True, COLOR_TEXT)
        self.screen.blit(header, (panel.x + 10, panel.y + 10))
        
        # Subheader with count
        count_text = self.font_small.render(f"{len(self.shop_items)} items", True, COLOR_TEXT_DIM)
        self.screen.blit(count_text, (panel.x + 10, panel.y + 35))
        
        # Item list
        item_height = 55
        start_y = panel.y + 60
        visible_count = min(7, len(self.shop_items) - self.shop_scroll)
        
        for i in range(visible_count):
            idx = self.shop_scroll + i
            if idx >= len(self.shop_items):
                break
            
            item = self.shop_items[idx]
            self._render_item_row(
                panel.x + 10, start_y + i * item_height,
                panel.width - 20, item_height - 5,
                item, is_shop=True, hover=(idx == self.hover_shop_idx)
            )
        
        # Scroll indicators
        if self.shop_scroll > 0:
            arrow = self.font.render("▲ more", True, COLOR_TEXT_DIM)
            self.screen.blit(arrow, (panel.centerx - arrow.get_width() // 2, panel.y + 55))
        
        if self.shop_scroll + 7 < len(self.shop_items):
            arrow = self.font.render("▼ more", True, COLOR_TEXT_DIM)
            self.screen.blit(arrow, (panel.centerx - arrow.get_width() // 2, panel.bottom - 25))
    
    def _render_inventory_with_tabs(self):
        """Render inventory panel (no tabs, they're above equipment panel)."""
        panel = self.inventory_ui.right_panel
        ent = self.inventory_ui.selected_entity
        
        # Background panel
        pygame.draw.rect(self.screen, COLOR_UI_BG, panel, border_radius=10)
        pygame.draw.rect(self.screen, (150, 100, 50), panel, 2, border_radius=10)  # Sell color (orange)
        
        # Header
        char_name = "Bag"
        if ent >= 0 and esper.has_component(ent, CharacterName):
            char_name = f"{esper.component_for_entity(ent, CharacterName).name}'s Bag"
        header = self.font.render(char_name, True, COLOR_TEXT)
        self.screen.blit(header, (panel.x + 10, panel.y + 10))
        
        hint = self.font_small.render("(click to sell)", True, COLOR_TEXT_DIM)
        self.screen.blit(hint, (panel.x + 10, panel.y + 35))
        
        # Render inventory grid using InventoryUI's method (but we do it ourselves for sell mode)
        self._render_sell_inventory_grid()
    
    def _render_sell_inventory_grid(self):
        """Render inventory grid with sell functionality."""
        from .icons import icon_generator
        
        panel = self.inventory_ui.right_panel
        ent = self.inventory_ui.selected_entity
        
        if ent < 0 or not esper.entity_exists(ent):
            empty = self.font_small.render("No character selected", True, COLOR_TEXT_DIM)
            self.screen.blit(empty, (panel.centerx - empty.get_width() // 2, panel.centery))
            return
        
        # Get items
        items = []
        if esper.has_component(ent, InventoryComp):
            inv = esper.component_for_entity(ent, InventoryComp)
            items = inv.items
        
        # Render slots
        for i, rect in enumerate(self.inventory_ui.inv_slots):
            # Slot background
            pygame.draw.rect(self.screen, (35, 30, 45), rect)
            pygame.draw.rect(self.screen, COLOR_UI_BORDER, rect, 1)
            
            if i < len(items):
                item = items[i]
                item_id = item.item_id if hasattr(item, 'item_id') else str(item)
                item_data = data_loader.get_item(item_id) or {}
                
                rarity = item_data.get('rarity', 0)
                rarity_color = RARITY_COLORS.get(rarity, (180, 180, 180))
                
                # Rarity highlight
                inner = rect.inflate(-4, -4)
                pygame.draw.rect(self.screen, (*rarity_color[:3], 100), inner)
                pygame.draw.rect(self.screen, rarity_color, inner, 2)
                
                # Icon
                icon_size = self.inventory_ui.slot_size - 8
                icon = icon_generator.get_item_icon(item_id, rarity, icon_size)
                icon_rect = icon.get_rect(center=rect.center)
                self.screen.blit(icon, icon_rect)
                
                # Quantity badge
                quantity = getattr(item, 'quantity', 1)
                if quantity > 1:
                    qty_text = self.font_small.render(str(quantity), True, (255, 255, 255))
                    qty_bg = pygame.Rect(rect.right - 16, rect.bottom - 14, 14, 12)
                    pygame.draw.rect(self.screen, (0, 0, 0), qty_bg)
                    self.screen.blit(qty_text, (rect.right - 14, rect.bottom - 14))
                
                # Hover highlight
                if rect.collidepoint(pygame.mouse.get_pos()):
                    pygame.draw.rect(self.screen, (255, 255, 255), rect, 2)
                    # Show tooltip
                    self._render_sell_tooltip(item_data, rect)
        
        if len(items) == 0:
            empty = self.font_small.render("Inventory empty", True, COLOR_TEXT_DIM)
            self.screen.blit(empty, (panel.centerx - empty.get_width() // 2, panel.centery))
    
    def _render_sell_tooltip(self, item_data: dict, slot_rect: pygame.Rect):
        """Render tooltip with sell price."""
        name = item_data.get('name', '???')
        rarity = item_data.get('rarity', 0)
        rarity_color = RARITY_COLORS.get(rarity, (180, 180, 180))
        value = item_data.get('value', 10)
        sell_price = max(1, value // 2)
        damage = item_data.get('damage', 0)
        armor = item_data.get('armor', 0)
        
        lines = [name]
        line_colors = [rarity_color]
        
        if damage > 0:
            lines.append(f"Damage: {damage}")
            line_colors.append((255, 180, 100))
        if armor > 0:
            lines.append(f"Armor: {armor}")
            line_colors.append((150, 200, 255))
        
        lines.append(f"Sell for: {sell_price}g")
        line_colors.append(COLOR_GOLD)
        
        # Position
        mouse_pos = pygame.mouse.get_pos()
        width = max(self.font_small.size(line)[0] for line in lines) + 20
        height = len(lines) * 18 + 10
        
        x = min(mouse_pos[0] + 15, self.screen.get_width() - width - 10)
        y = min(mouse_pos[1] + 15, self.screen.get_height() - height - 10)
        
        pygame.draw.rect(self.screen, (20, 18, 25), (x, y, width, height))
        pygame.draw.rect(self.screen, rarity_color, (x, y, width, height), 1)
        
        for i, line in enumerate(lines):
            color = line_colors[i] if i < len(line_colors) else COLOR_TEXT_DIM
            text = self.font_small.render(line, True, color)
            self.screen.blit(text, (x + 10, y + 5 + i * 18))
    
    def _render_item_row(self, x: int, y: int, w: int, h: int, 
                         item: dict, is_shop: bool, hover: bool):
        """Render a single item row."""
        rect = pygame.Rect(x, y, w, h)
        rarity = item.get('rarity', 0)
        rarity_color = RARITY_COLORS.get(rarity, (150, 150, 150))
        
        # Background
        if hover:
            bg_color = (70, 65, 80)
        else:
            bg_color = (45, 42, 55)
        
        pygame.draw.rect(self.screen, bg_color, rect, border_radius=5)
        pygame.draw.rect(self.screen, rarity_color, rect, 1, border_radius=5)
        
        # Item name
        name = item.get('name', '???')
        name_surf = self.font_small.render(name, True, rarity_color)
        self.screen.blit(name_surf, (x + 8, y + 5))
        
        # Item type/stats
        item_type = item.get('type', '')
        slot = item.get('slot', '')
        damage = item.get('damage', 0)
        armor = item.get('armor', 0)
        effect = item.get('effect_type', '')
        effect_val = item.get('effect_value', 0)
        quantity = item.get('quantity', 1)
        
        stat_parts = []
        if slot:
            stat_parts.append(slot.replace('_', ' ').title())
        elif item_type:
            stat_parts.append(item_type.title())
        
        if damage > 0:
            stat_parts.append(f"Dmg: {damage}")
        if armor > 0:
            stat_parts.append(f"Armor: {armor}")
        if effect and effect_val:
            stat_parts.append(f"{effect}: +{effect_val}")
        if not is_shop and quantity > 1:
            stat_parts.append(f"x{quantity}")
        
        stat_str = " | ".join(stat_parts) if stat_parts else ""
        stat_surf = self.font_small.render(stat_str, True, COLOR_TEXT_DIM)
        self.screen.blit(stat_surf, (x + 8, y + 25))
        
        # Price
        price = item.get('price', 0)
        if is_shop:
            price_str = f"Buy: {price}g"
            price_color = COLOR_GOLD
        else:
            price_str = f"Sell: {price}g"
            price_color = (200, 150, 50)
        
        price_surf = self.font_small.render(price_str, True, price_color)
        self.screen.blit(price_surf, (rect.right - price_surf.get_width() - 8, y + 15))

