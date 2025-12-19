"""Heads-up display and UI elements."""

import pygame
from ..engine.constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    COLOR_UI_BG, COLOR_UI_BORDER, COLOR_UI_ACCENT,
    COLOR_HEALTH, COLOR_MANA, COLOR_XP, COLOR_GOLD,
    COLOR_TEXT, COLOR_TEXT_DIM, RARITY_COLORS
)


class HUD:
    """In-game heads-up display."""
    
    def __init__(self, screen):
        self.screen = screen
        
        # Try to load a font
        pygame.font.init()
        try:
            self.font = pygame.font.Font(None, 24)
            self.font_large = pygame.font.Font(None, 32)
            self.font_small = pygame.font.Font(None, 18)
        except:
            self.font = pygame.font.SysFont('arial', 20)
            self.font_large = pygame.font.SysFont('arial', 28)
            self.font_small = pygame.font.SysFont('arial', 14)
        
        # UI dimensions
        self.portrait_size = 80
        self.bar_width = 160
        self.bar_height = 16
        self.padding = 10
        
        # Party panel (left side)
        self.party_panel_width = 200
        
        # Action bar (bottom center)
        self.action_bar_height = 70
        self.action_slot_size = 50
        self.num_action_slots = 8
        
        # Minimap (top right)
        self.minimap_size = 150
        self.minimap_surface = pygame.Surface((self.minimap_size, self.minimap_size))
    
    def render(self, game_state):
        """Render all HUD elements."""
        self._render_party_panel(game_state)
        # Action bar is now rendered separately by game.action_bar
        self._render_minimap(game_state)
        self._render_target_info(game_state)
        self._render_notifications(game_state)
        self._render_gold(game_state)
    
    def _render_gold(self, game_state):
        """Render gold display."""
        gold = game_state.get('gold', 0)
        x = SCREEN_WIDTH // 2 + 220
        y = SCREEN_HEIGHT - 50
        gold_text = self.font.render(f"Gold: {gold}", True, COLOR_GOLD)
        self.screen.blit(gold_text, (x, y))
    
    def _render_party_panel(self, game_state):
        """Render party member status on left side."""
        x = self.padding
        y = self.padding
        
        for i, char in enumerate(game_state.get('party', [])):
            self._render_character_panel(char, x, y, i == 0)
            y += self.portrait_size + self.padding
    
    def _render_character_panel(self, char, x, y, is_selected):
        """Render a single character's status panel."""
        panel_width = self.party_panel_width
        panel_height = self.portrait_size
        
        # Background
        panel_rect = pygame.Rect(x, y, panel_width, panel_height)
        pygame.draw.rect(self.screen, COLOR_UI_BG, panel_rect)
        
        border_color = COLOR_UI_ACCENT if is_selected else COLOR_UI_BORDER
        pygame.draw.rect(self.screen, border_color, panel_rect, 2)
        
        # Portrait placeholder
        portrait_rect = pygame.Rect(x + 4, y + 4, panel_height - 8, panel_height - 8)
        pygame.draw.rect(self.screen, char.color, portrait_rect)
        pygame.draw.rect(self.screen, COLOR_UI_BORDER, portrait_rect, 1)
        
        # Name and class
        name_x = x + panel_height + 4
        name_text = self.font.render(char.name, True, COLOR_TEXT)
        self.screen.blit(name_text, (name_x, y + 4))
        
        class_text = self.font_small.render(
            f"Lv.{char.level} {char.character_class}", True, COLOR_TEXT_DIM
        )
        self.screen.blit(class_text, (name_x, y + 22))
        
        # Health bar
        bar_x = name_x
        bar_y = y + 40
        bar_w = panel_width - panel_height - 12
        
        self._render_bar(bar_x, bar_y, bar_w, 12, 
                        char.health, char.max_health, COLOR_HEALTH)
        
        # Mana bar
        bar_y += 14
        self._render_bar(bar_x, bar_y, bar_w, 10,
                        char.mana, char.max_mana, COLOR_MANA)
    
    def _render_bar(self, x, y, width, height, value, max_value, color):
        """Render a status bar."""
        # Background
        pygame.draw.rect(self.screen, (30, 25, 35), (x, y, width, height))
        
        # Fill
        if max_value > 0:
            fill_width = int(width * (value / max_value))
            pygame.draw.rect(self.screen, color, (x, y, fill_width, height))
        
        # Border
        pygame.draw.rect(self.screen, COLOR_UI_BORDER, (x, y, width, height), 1)
    
    def _render_action_bar(self, game_state):
        """Render action bar at bottom center."""
        total_width = self.num_action_slots * (self.action_slot_size + 4) + 8
        x = (SCREEN_WIDTH - total_width) // 2
        y = SCREEN_HEIGHT - self.action_bar_height - self.padding
        
        # Background
        bar_rect = pygame.Rect(x, y, total_width, self.action_bar_height)
        pygame.draw.rect(self.screen, COLOR_UI_BG, bar_rect)
        pygame.draw.rect(self.screen, COLOR_UI_BORDER, bar_rect, 2)
        
        # Slots
        slot_x = x + 6
        slot_y = y + 6
        
        for i in range(self.num_action_slots):
            slot_rect = pygame.Rect(slot_x, slot_y, 
                                   self.action_slot_size, self.action_slot_size)
            pygame.draw.rect(self.screen, (40, 35, 50), slot_rect)
            pygame.draw.rect(self.screen, COLOR_UI_BORDER, slot_rect, 1)
            
            # Slot number
            num_text = self.font_small.render(str(i + 1), True, COLOR_TEXT_DIM)
            self.screen.blit(num_text, (slot_x + 2, slot_y + 2))
            
            slot_x += self.action_slot_size + 4
        
        # Gold display
        gold = game_state.get('gold', 0)
        gold_text = self.font.render(f"Gold: {gold}", True, COLOR_GOLD)
        self.screen.blit(gold_text, (x + total_width + 20, y + 25))
    
    def _render_minimap(self, game_state):
        """Render minimap in top right corner."""
        x = SCREEN_WIDTH - self.minimap_size - self.padding
        y = self.padding
        
        # Background
        self.minimap_surface.fill((20, 18, 25))
        
        world = game_state.get('world')
        if world and world.tiles is not None:
            # Draw tiles
            scale_x = self.minimap_size / world.width
            scale_y = self.minimap_size / world.height
            
            for ty in range(world.height):
                for tx in range(world.width):
                    tile = world.tiles[ty, tx]
                    if tile == 1:  # Floor
                        color = (60, 55, 70)
                    elif tile == 2:  # Wall
                        color = (90, 80, 100)
                    else:
                        continue
                    
                    mx = int(tx * scale_x)
                    my = int(ty * scale_y)
                    pygame.draw.rect(self.minimap_surface, color,
                                   (mx, my, max(1, int(scale_x)), max(1, int(scale_y))))
            
            # Draw party
            for char in game_state.get('party', []):
                mx = int(char.x * scale_x)
                my = int(char.y * scale_y)
                pygame.draw.circle(self.minimap_surface, (100, 180, 255), (mx, my), 3)
            
            # Draw enemies
            for enemy in world.enemies:
                if enemy.health > 0:
                    mx = int(enemy.x * scale_x)
                    my = int(enemy.y * scale_y)
                    pygame.draw.circle(self.minimap_surface, (255, 80, 80), (mx, my), 2)
        
        self.screen.blit(self.minimap_surface, (x, y))
        pygame.draw.rect(self.screen, COLOR_UI_BORDER, 
                        (x, y, self.minimap_size, self.minimap_size), 2)
    
    def _render_target_info(self, game_state):
        """Render info about current target."""
        target = game_state.get('target')
        if not target:
            return
        
        # Position below minimap
        x = SCREEN_WIDTH - 180 - self.padding
        y = self.padding + self.minimap_size + 10
        
        # Background
        panel_rect = pygame.Rect(x, y, 180, 60)
        pygame.draw.rect(self.screen, COLOR_UI_BG, panel_rect)
        pygame.draw.rect(self.screen, COLOR_UI_BORDER, panel_rect, 2)
        
        # Name
        name = getattr(target, 'name', 'Unknown')
        level = getattr(target, 'level', 1)
        name_text = self.font.render(f"Lv.{level} {name}", True, COLOR_TEXT)
        self.screen.blit(name_text, (x + 8, y + 8))
        
        # Health
        health = getattr(target, 'health', 0)
        max_health = getattr(target, 'max_health', 100)
        self._render_bar(x + 8, y + 32, 164, 16, health, max_health, COLOR_HEALTH)
    
    def _render_notifications(self, game_state):
        """Render floating notifications."""
        notifications = game_state.get('notifications', [])
        y = SCREEN_HEIGHT // 3
        
        for note in notifications[-5:]:  # Show last 5
            text = self.font.render(note['text'], True, note.get('color', COLOR_TEXT))
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, y))
            
            # Shadow
            shadow = self.font.render(note['text'], True, (0, 0, 0))
            self.screen.blit(shadow, (text_rect.x + 2, text_rect.y + 2))
            self.screen.blit(text, text_rect)
            
            y += 25

