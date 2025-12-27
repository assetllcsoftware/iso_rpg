"""Town scene - merchant, stash, inn, etc."""

import pygame
import esper
from typing import Optional, List, Dict

from ..core.constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    COLOR_UI_BG, COLOR_UI_BORDER, COLOR_UI_ACCENT,
    COLOR_TEXT, COLOR_TEXT_DIM, COLOR_GOLD
)
from ..core.events import EventBus, Event, EventType
from ..ecs.components import PartyMember, Health, Mana, Gold, Inventory, CharacterName


class TownScene:
    """Town scene for trading, healing, and stashing items."""
    
    def __init__(self, screen: pygame.Surface, event_bus: EventBus):
        self.screen = screen
        self.event_bus = event_bus
        self.active = False
        
        pygame.font.init()
        self.font = pygame.font.Font(None, 32)
        self.font_small = pygame.font.Font(None, 24)
        self.font_title = pygame.font.Font(None, 64)
        
        # Selected building
        self.selected_building: Optional[str] = None
        
        # Buildings
        self.buildings = [
            {
                "id": "inn",
                "name": "Wanderer's Rest",
                "desc": "Rest to fully heal your party",
                "cost": 10,
                "icon": "🏨"
            },
            {
                "id": "merchant",
                "name": "Blacksmith",
                "desc": "Buy and sell weapons and armor",
                "cost": 0,
                "icon": "⚔️"
            },
            {
                "id": "potion_shop",
                "name": "Alchemist",
                "desc": "Stock up on potions",
                "cost": 0,
                "icon": "🧪"
            },
            {
                "id": "stash",
                "name": "Storage",
                "desc": "Store items safely",
                "cost": 0,
                "icon": "📦"
            },
            {
                "id": "dungeon",
                "name": "Dungeon Entrance",
                "desc": "Descend into the depths",
                "cost": 0,
                "icon": "🚪"
            },
        ]
        
        # Building positions for clicking
        self.building_rects: List[pygame.Rect] = []
        
        # Stash contents (shared)
        self.stash_items: List = []
        self.stash_max = 50
        
        # Merchant inventory
        self.merchant_items = [
            {"id": "health_potion", "name": "Health Potion", "price": 25},
            {"id": "mana_potion", "name": "Mana Potion", "price": 20},
            {"id": "iron_sword", "name": "Iron Sword", "price": 100},
            {"id": "leather_armor", "name": "Leather Armor", "price": 75},
        ]
    
    def show(self):
        """Show the town scene."""
        self.active = True
        self.selected_building = None
        
        # Heal party when entering town
        for ent, (member, health) in esper.get_components(PartyMember, Health):
            health.current = health.maximum
            if esper.has_component(ent, Mana):
                mana = esper.component_for_entity(ent, Mana)
                mana.current = mana.maximum
        
        self.event_bus.emit(Event(EventType.NOTIFICATION, {
            "text": "Welcome to Town! Your party has been healed.",
            "color": (100, 255, 150)
        }))
    
    def hide(self):
        """Hide the town scene."""
        self.active = False
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle input events."""
        if not self.active:
            return False
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self.selected_building:
                    self.selected_building = None
                else:
                    self.hide()
                return True
            elif event.key == pygame.K_1:
                self._interact_building(0)
                return True
            elif event.key == pygame.K_2:
                self._interact_building(1)
                return True
            elif event.key == pygame.K_3:
                self._interact_building(2)
                return True
            elif event.key == pygame.K_4:
                self._interact_building(3)
                return True
            elif event.key == pygame.K_5:
                self._interact_building(4)
                return True
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                return self._handle_click(event.pos)
        
        return False
    
    def _interact_building(self, index: int):
        """Interact with a building by index."""
        if index < 0 or index >= len(self.buildings):
            return
        
        building = self.buildings[index]
        
        if building["id"] == "dungeon":
            self._enter_dungeon()
        elif building["id"] == "inn":
            self._rest_at_inn()
        else:
            self.selected_building = building["id"]
    
    def _handle_click(self, pos) -> bool:
        """Handle mouse click."""
        for i, rect in enumerate(self.building_rects):
            if rect.collidepoint(pos):
                self._interact_building(i)
                return True
        return False
    
    def _rest_at_inn(self):
        """Rest at the inn."""
        cost = 10
        
        # Find party gold
        for ent, (member, gold) in esper.get_components(PartyMember, Gold):
            if member.party_index == 0:
                if gold.amount >= cost:
                    gold.amount -= cost
                    
                    # Full heal
                    for heal_ent, (_, health) in esper.get_components(PartyMember, Health):
                        health.current = health.maximum
                        if esper.has_component(heal_ent, Mana):
                            mana = esper.component_for_entity(heal_ent, Mana)
                            mana.current = mana.maximum
                    
                    self.event_bus.emit(Event(EventType.NOTIFICATION, {
                        "text": "Party fully rested!",
                        "color": (100, 255, 150)
                    }))
                else:
                    self.event_bus.emit(Event(EventType.NOTIFICATION, {
                        "text": "Not enough gold!",
                        "color": (255, 100, 100)
                    }))
                return
    
    def _enter_dungeon(self):
        """Leave town and enter dungeon."""
        self.hide()
        self.event_bus.emit(Event(EventType.TOWN_LEFT, {
            "target_level": 1
        }))
    
    def render(self):
        """Render the town scene."""
        if not self.active:
            return
        
        # Background
        self.screen.fill((20, 25, 35))
        
        # Draw night sky with stars
        import random
        random.seed(42)  # Consistent stars
        for _ in range(100):
            x = random.randint(0, SCREEN_WIDTH)
            y = random.randint(0, SCREEN_HEIGHT // 2)
            brightness = random.randint(100, 255)
            pygame.draw.circle(self.screen, (brightness, brightness, brightness), (x, y), 1)
        
        # Title
        title = self.font_title.render("⚔️ SANCTUARY ⚔️", True, COLOR_UI_ACCENT)
        title_rect = title.get_rect(centerx=SCREEN_WIDTH // 2, y=30)
        self.screen.blit(title, title_rect)
        
        # Party gold
        gold = 0
        for ent, (member, gold_comp) in esper.get_components(PartyMember, Gold):
            if member.party_index == 0:
                gold = gold_comp.amount
                break
        
        gold_text = self.font.render(f"Gold: {gold}", True, COLOR_GOLD)
        self.screen.blit(gold_text, (SCREEN_WIDTH - 200, 40))
        
        # Buildings
        self.building_rects.clear()
        self._render_buildings()
        
        # Selected building submenu
        if self.selected_building:
            self._render_submenu()
        
        # Instructions
        hint = self.font_small.render(
            "Press 1-5 or click to interact, ESC to close",
            True, COLOR_TEXT_DIM
        )
        hint_rect = hint.get_rect(centerx=SCREEN_WIDTH // 2, y=SCREEN_HEIGHT - 40)
        self.screen.blit(hint, hint_rect)
    
    def _render_buildings(self):
        """Render town buildings."""
        start_y = 150
        building_height = 100
        building_width = 300
        spacing = 20
        
        for i, building in enumerate(self.buildings):
            x = (SCREEN_WIDTH - building_width) // 2
            y = start_y + i * (building_height + spacing)
            
            rect = pygame.Rect(x, y, building_width, building_height)
            self.building_rects.append(rect)
            
            # Background
            is_hovered = rect.collidepoint(pygame.mouse.get_pos())
            bg_color = (45, 50, 65) if is_hovered else COLOR_UI_BG
            pygame.draw.rect(self.screen, bg_color, rect, border_radius=8)
            pygame.draw.rect(self.screen, COLOR_UI_BORDER, rect, 2, border_radius=8)
            
            # Hotkey number
            num_surf = self.font.render(str(i + 1), True, COLOR_UI_ACCENT)
            self.screen.blit(num_surf, (x + 15, y + 10))
            
            # Icon (using text emoji)
            icon_surf = self.font_title.render(building["icon"], True, COLOR_TEXT)
            self.screen.blit(icon_surf, (x + 50, y + 25))
            
            # Name
            name_surf = self.font.render(building["name"], True, COLOR_TEXT)
            self.screen.blit(name_surf, (x + 120, y + 20))
            
            # Description
            desc_surf = self.font_small.render(building["desc"], True, COLOR_TEXT_DIM)
            self.screen.blit(desc_surf, (x + 120, y + 55))
            
            # Cost (if applicable)
            if building["cost"] > 0:
                cost_surf = self.font_small.render(
                    f"{building['cost']} gold", True, COLOR_GOLD
                )
                self.screen.blit(cost_surf, (x + building_width - 80, y + 20))
    
    def _render_submenu(self):
        """Render submenu for selected building."""
        # Semi-transparent overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        
        # Submenu panel
        panel_w, panel_h = 500, 400
        panel_x = (SCREEN_WIDTH - panel_w) // 2
        panel_y = (SCREEN_HEIGHT - panel_h) // 2
        panel_rect = pygame.Rect(panel_x, panel_y, panel_w, panel_h)
        
        pygame.draw.rect(self.screen, COLOR_UI_BG, panel_rect, border_radius=8)
        pygame.draw.rect(self.screen, COLOR_UI_ACCENT, panel_rect, 3, border_radius=8)
        
        # Title based on building
        building_name = self.selected_building.replace("_", " ").title()
        title = self.font.render(building_name, True, COLOR_UI_ACCENT)
        self.screen.blit(title, (panel_x + 20, panel_y + 20))
        
        # Content based on building
        if self.selected_building == "merchant":
            self._render_merchant_menu(panel_x, panel_y, panel_w, panel_h)
        elif self.selected_building == "potion_shop":
            self._render_potion_menu(panel_x, panel_y, panel_w, panel_h)
        elif self.selected_building == "stash":
            self._render_stash_menu(panel_x, panel_y, panel_w, panel_h)
        
        # Close hint
        close_hint = self.font_small.render("Press ESC to close", True, COLOR_TEXT_DIM)
        self.screen.blit(close_hint, (panel_x + 20, panel_y + panel_h - 30))
    
    def _render_merchant_menu(self, x, y, w, h):
        """Render merchant buy/sell menu."""
        subtitle = self.font_small.render("Buy weapons and armor", True, COLOR_TEXT_DIM)
        self.screen.blit(subtitle, (x + 20, y + 60))
        
        # List items for sale
        item_y = y + 100
        for item in self.merchant_items:
            item_text = f"{item['name']} - {item['price']} gold"
            item_surf = self.font_small.render(item_text, True, COLOR_TEXT)
            self.screen.blit(item_surf, (x + 40, item_y))
            item_y += 30
        
        # "Coming Soon" message
        msg = self.font.render("Full trading coming soon!", True, COLOR_TEXT_DIM)
        self.screen.blit(msg, (x + 100, y + 300))
    
    def _render_potion_menu(self, x, y, w, h):
        """Render potion shop menu."""
        subtitle = self.font_small.render("Stock up on potions", True, COLOR_TEXT_DIM)
        self.screen.blit(subtitle, (x + 20, y + 60))
        
        potions = [
            {"name": "Health Potion", "price": 25, "desc": "Restore 50 HP"},
            {"name": "Mana Potion", "price": 20, "desc": "Restore 30 MP"},
            {"name": "Greater Health", "price": 75, "desc": "Restore 150 HP"},
        ]
        
        item_y = y + 100
        for potion in potions:
            item_text = f"{potion['name']} ({potion['price']}g) - {potion['desc']}"
            item_surf = self.font_small.render(item_text, True, COLOR_TEXT)
            self.screen.blit(item_surf, (x + 40, item_y))
            item_y += 35
        
        msg = self.font.render("Full trading coming soon!", True, COLOR_TEXT_DIM)
        self.screen.blit(msg, (x + 100, y + 300))
    
    def _render_stash_menu(self, x, y, w, h):
        """Render stash menu."""
        subtitle = self.font_small.render(
            f"Items stored: {len(self.stash_items)}/{self.stash_max}",
            True, COLOR_TEXT_DIM
        )
        self.screen.blit(subtitle, (x + 20, y + 60))
        
        if not self.stash_items:
            empty_msg = self.font.render("Stash is empty", True, COLOR_TEXT_DIM)
            self.screen.blit(empty_msg, (x + 150, y + 200))
        else:
            # List stashed items
            item_y = y + 100
            for item in self.stash_items[:10]:  # Show first 10
                name = getattr(item, 'name', 'Unknown Item')
                item_surf = self.font_small.render(f"• {name}", True, COLOR_TEXT)
                self.screen.blit(item_surf, (x + 40, item_y))
                item_y += 25

