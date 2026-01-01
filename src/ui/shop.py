"""Shop UI - buy/sell interface using inventory-style grid."""

import pygame
import esper
from typing import Optional, List, Dict, Tuple

from ..core.constants import (
    COLOR_UI_BG, COLOR_UI_BORDER, COLOR_UI_ACCENT,
    COLOR_TEXT, COLOR_TEXT_DIM, COLOR_GOLD, RARITY_COLORS
)
from ..core.events import EventBus, Event, EventType
from ..ecs.components import (
    PartyMember, Gold, Inventory as InventoryComp, Equipment
)
from ..data.loader import data_loader


class ShopUI:
    """Shop interface - left side shows stock, right side shows player inventory."""
    
    def __init__(self, screen: pygame.Surface, event_bus: EventBus):
        self.screen = screen
        self.event_bus = event_bus
        self.visible = False
        self.shop_type = 'blacksmith'  # 'blacksmith', 'alchemist'
        self.dungeon_level = 1
        
        # Selection state
        self.hover_shop_idx = -1
        self.hover_inv_idx = -1
        self.shop_scroll = 0
        self.inv_scroll = 0
        
        # Fonts
        pygame.font.init()
        self.font = pygame.font.Font(None, 28)
        self.font_small = pygame.font.Font(None, 22)
        self.font_title = pygame.font.Font(None, 36)
        
        # Layout
        screen_w, screen_h = screen.get_size()
        panel_w = min(450, screen_w // 2 - 40)
        panel_h = min(500, screen_h - 100)
        
        self.left_panel = pygame.Rect(
            screen_w // 2 - panel_w - 20, 
            (screen_h - panel_h) // 2,
            panel_w, panel_h
        )
        self.right_panel = pygame.Rect(
            screen_w // 2 + 20,
            (screen_h - panel_h) // 2,
            panel_w, panel_h
        )
        
        self.slot_size = 50
        self.cols = 5
        self.rows = 6
        
        # Generate shop inventory
        self.shop_items: List[dict] = []
    
    def show(self, shop_type: str, dungeon_level: int = 1):
        """Open shop UI."""
        self.visible = True
        self.shop_type = shop_type
        self.dungeon_level = dungeon_level
        self.shop_scroll = 0
        self.inv_scroll = 0
        self.hover_shop_idx = -1
        self.hover_inv_idx = -1
        self._generate_shop_inventory()
    
    def hide(self):
        """Close shop UI."""
        self.visible = False
    
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
        """Buy an item from the shop."""
        price = item['price']
        
        for ent, (member, gold) in esper.get_components(PartyMember, Gold):
            if member.party_index == 0:
                if gold.amount >= price:
                    gold.amount -= price
                    
                    if esper.has_component(ent, InventoryComp):
                        inv = esper.component_for_entity(ent, InventoryComp)
                        inv.add(item['id'], 1)
                    
                    self.event_bus.emit(Event(EventType.NOTIFICATION, {
                        "text": f"Bought {item['name']} for {price}g",
                        "color": (100, 255, 100)
                    }))
                else:
                    self.event_bus.emit(Event(EventType.NOTIFICATION, {
                        "text": "Not enough gold!",
                        "color": (255, 100, 100)
                    }))
                return
    
    def _sell_item(self, inv_idx: int, item: dict):
        """Sell an item from inventory."""
        price = item['price']
        
        for ent, (member, gold) in esper.get_components(PartyMember, Gold):
            if member.party_index == 0:
                gold.amount += price
                
                if esper.has_component(ent, InventoryComp):
                    inv = esper.component_for_entity(ent, InventoryComp)
                    if inv_idx < len(inv.items):
                        inv_item = inv.items[inv_idx]
                        inv_item.quantity -= 1
                        if inv_item.quantity <= 0:
                            inv.items.pop(inv_idx)
                
                self.event_bus.emit(Event(EventType.NOTIFICATION, {
                    "text": f"Sold {item['name']} for {price}g",
                    "color": (255, 215, 0)
                }))
                return
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle input events."""
        if not self.visible:
            return False
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.hide()
                return True
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                return self._handle_click(event.pos)
            elif event.button == 4:  # Scroll up
                if self.left_panel.collidepoint(event.pos):
                    self.shop_scroll = max(0, self.shop_scroll - 1)
                elif self.right_panel.collidepoint(event.pos):
                    self.inv_scroll = max(0, self.inv_scroll - 1)
                return True
            elif event.button == 5:  # Scroll down
                if self.left_panel.collidepoint(event.pos):
                    self.shop_scroll = min(len(self.shop_items) - 1, self.shop_scroll + 1)
                elif self.right_panel.collidepoint(event.pos):
                    inv_items = self._get_player_inventory()
                    self.inv_scroll = min(len(inv_items) - 1, self.inv_scroll + 1)
                return True
        
        elif event.type == pygame.MOUSEWHEEL:
            mouse_pos = pygame.mouse.get_pos()
            if self.left_panel.collidepoint(mouse_pos):
                self.shop_scroll = max(0, self.shop_scroll - event.y)
            elif self.right_panel.collidepoint(mouse_pos):
                self.inv_scroll = max(0, self.inv_scroll - event.y)
            return True
        
        elif event.type == pygame.MOUSEMOTION:
            self._update_hover(event.pos)
        
        return True  # Consume all events when visible
    
    def _handle_click(self, pos: Tuple[int, int]) -> bool:
        """Handle mouse click."""
        # Check close button or outside panels
        screen_w, screen_h = self.screen.get_size()
        total_rect = pygame.Rect(
            self.left_panel.x - 20, self.left_panel.y - 60,
            self.right_panel.right - self.left_panel.x + 40,
            self.left_panel.height + 80
        )
        
        if not total_rect.collidepoint(pos):
            self.hide()
            return True
        
        # Check shop items (left panel)
        if self.left_panel.collidepoint(pos):
            item_height = 55
            start_y = self.left_panel.y + 80
            
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
        
        # Check inventory items (right panel)
        if self.right_panel.collidepoint(pos):
            inv_items = self._get_player_inventory()
            item_height = 55
            start_y = self.right_panel.y + 80
            
            for i, (inv_idx, item) in enumerate(inv_items[self.inv_scroll:self.inv_scroll + 7]):
                item_rect = pygame.Rect(
                    self.right_panel.x + 10,
                    start_y + i * item_height,
                    self.right_panel.width - 20,
                    item_height - 5
                )
                if item_rect.collidepoint(pos):
                    self._sell_item(inv_idx, item)
                    return True
        
        return True
    
    def _update_hover(self, pos: Tuple[int, int]):
        """Update hover state based on mouse position."""
        self.hover_shop_idx = -1
        self.hover_inv_idx = -1
        
        item_height = 55
        
        # Check shop items
        if self.left_panel.collidepoint(pos):
            start_y = self.left_panel.y + 80
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
        
        # Check inventory items
        elif self.right_panel.collidepoint(pos):
            start_y = self.right_panel.y + 80
            for i in range(7):
                item_rect = pygame.Rect(
                    self.right_panel.x + 10,
                    start_y + i * item_height,
                    self.right_panel.width - 20,
                    item_height - 5
                )
                if item_rect.collidepoint(pos):
                    self.hover_inv_idx = self.inv_scroll + i
                    break
    
    def render(self):
        """Render shop UI."""
        if not self.visible:
            return
        
        screen_w, screen_h = self.screen.get_size()
        
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
        
        # Left panel - Shop stock
        self._render_shop_panel()
        
        # Right panel - Player inventory
        self._render_inventory_panel()
        
        # Instructions
        hint = self.font_small.render("Click to buy/sell | ESC to close | Scroll for more", True, COLOR_TEXT_DIM)
        self.screen.blit(hint, (screen_w // 2 - hint.get_width() // 2, self.left_panel.bottom + 10))
    
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
    
    def _render_inventory_panel(self):
        """Render player inventory panel."""
        panel = self.right_panel
        
        # Background
        pygame.draw.rect(self.screen, COLOR_UI_BG, panel, border_radius=10)
        pygame.draw.rect(self.screen, (150, 100, 50), panel, 2, border_radius=10)  # Brown for sell
        
        # Header
        header = self.font.render("YOUR INVENTORY", True, COLOR_TEXT)
        self.screen.blit(header, (panel.x + 10, panel.y + 10))
        
        inv_items = self._get_player_inventory()
        
        # Subheader with count
        count_text = self.font_small.render(f"{len(inv_items)} items", True, COLOR_TEXT_DIM)
        self.screen.blit(count_text, (panel.x + 10, panel.y + 35))
        
        # Item list
        item_height = 55
        start_y = panel.y + 60
        visible_count = min(7, len(inv_items) - self.inv_scroll)
        
        for i in range(visible_count):
            idx = self.inv_scroll + i
            if idx >= len(inv_items):
                break
            
            inv_idx, item = inv_items[idx]
            self._render_item_row(
                panel.x + 10, start_y + i * item_height,
                panel.width - 20, item_height - 5,
                item, is_shop=False, hover=(idx == self.hover_inv_idx)
            )
        
        if len(inv_items) == 0:
            empty = self.font_small.render("Inventory empty", True, COLOR_TEXT_DIM)
            self.screen.blit(empty, (panel.centerx - empty.get_width() // 2, panel.centery))
        
        # Scroll indicators
        if self.inv_scroll > 0:
            arrow = self.font.render("▲ more", True, COLOR_TEXT_DIM)
            self.screen.blit(arrow, (panel.centerx - arrow.get_width() // 2, panel.y + 55))
        
        if self.inv_scroll + 7 < len(inv_items):
            arrow = self.font.render("▼ more", True, COLOR_TEXT_DIM)
            self.screen.blit(arrow, (panel.centerx - arrow.get_width() // 2, panel.bottom - 25))
    
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

