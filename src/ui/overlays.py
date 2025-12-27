"""Game overlays (pause, game over, loading, etc.)."""

import pygame
from typing import Callable, Optional

from ..core.constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    COLOR_UI_BG, COLOR_UI_BORDER, COLOR_UI_ACCENT,
    COLOR_TEXT, COLOR_TEXT_DIM, COLOR_HEALTH
)


class PauseOverlay:
    """Pause menu overlay."""
    
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.visible = False
        self.selected_option = 0
        
        pygame.font.init()
        self.font_title = pygame.font.Font(None, 64)
        self.font = pygame.font.Font(None, 36)
        
        self.options = [
            "Resume",
            "Save Game (F5)",
            "Load Game (F9)", 
            "Options",
            "Return to Town",
            "Quit to Menu"
        ]
        
        # Callbacks
        self.on_resume: Optional[Callable] = None
        self.on_save: Optional[Callable] = None
        self.on_load: Optional[Callable] = None
        self.on_options: Optional[Callable] = None
        self.on_return_town: Optional[Callable] = None
        self.on_quit: Optional[Callable] = None
    
    def toggle(self):
        """Toggle pause menu."""
        self.visible = not self.visible
    
    def show(self):
        """Show pause menu."""
        self.visible = True
        self.selected_option = 0
    
    def hide(self):
        """Hide pause menu."""
        self.visible = False
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle input events."""
        if not self.visible:
            return False
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.hide()
                return True
            elif event.key == pygame.K_UP:
                self.selected_option = (self.selected_option - 1) % len(self.options)
                return True
            elif event.key == pygame.K_DOWN:
                self.selected_option = (self.selected_option + 1) % len(self.options)
                return True
            elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                self._select_option()
                return True
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                return self._handle_click(event.pos)
        
        return False
    
    def _handle_click(self, pos) -> bool:
        """Handle mouse click."""
        center_x = SCREEN_WIDTH // 2
        start_y = SCREEN_HEIGHT // 2 - 50
        
        for i, _ in enumerate(self.options):
            y = start_y + i * 50
            rect = pygame.Rect(center_x - 150, y - 15, 300, 40)
            if rect.collidepoint(pos):
                self.selected_option = i
                self._select_option()
                return True
        return False
    
    def _select_option(self):
        """Execute selected option."""
        option = self.options[self.selected_option]
        
        if option == "Resume":
            self.hide()
            if self.on_resume:
                self.on_resume()
        elif "Save" in option:
            if self.on_save:
                self.on_save()
        elif "Load" in option:
            if self.on_load:
                self.on_load()
        elif option == "Options":
            if self.on_options:
                self.on_options()
        elif "Town" in option:
            if self.on_return_town:
                self.on_return_town()
        elif "Quit" in option:
            if self.on_quit:
                self.on_quit()
    
    def render(self):
        """Render pause overlay."""
        if not self.visible:
            return
        
        # Dark overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))
        
        # Title
        title = self.font_title.render("PAUSED", True, COLOR_UI_ACCENT)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 150))
        self.screen.blit(title, title_rect)
        
        # Options
        center_x = SCREEN_WIDTH // 2
        start_y = SCREEN_HEIGHT // 2 - 50
        
        for i, option in enumerate(self.options):
            y = start_y + i * 50
            is_selected = i == self.selected_option
            
            # Background for selected
            if is_selected:
                rect = pygame.Rect(center_x - 150, y - 10, 300, 40)
                pygame.draw.rect(self.screen, (60, 55, 80), rect)
                pygame.draw.rect(self.screen, COLOR_UI_ACCENT, rect, 2)
            
            color = COLOR_TEXT if is_selected else COLOR_TEXT_DIM
            text = self.font.render(option, True, color)
            text_rect = text.get_rect(center=(center_x, y + 8))
            self.screen.blit(text, text_rect)


class GameOverOverlay:
    """Game over screen."""
    
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.visible = False
        self.selected_option = 0
        self.death_message = "All heroes have fallen..."
        
        pygame.font.init()
        self.font_title = pygame.font.Font(None, 80)
        self.font = pygame.font.Font(None, 36)
        self.font_small = pygame.font.Font(None, 24)
        
        self.options = ["Try Again", "Return to Town", "Quit to Menu"]
        
        # Callbacks
        self.on_retry: Optional[Callable] = None
        self.on_town: Optional[Callable] = None
        self.on_quit: Optional[Callable] = None
        
        # Animation
        self.timer = 0.0
    
    def show(self, message: str = None):
        """Show game over screen."""
        self.visible = True
        self.selected_option = 0
        self.timer = 0.0
        if message:
            self.death_message = message
    
    def hide(self):
        """Hide game over screen."""
        self.visible = False
    
    def update(self, dt: float):
        """Update animation."""
        if self.visible:
            self.timer += dt
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle input events."""
        if not self.visible:
            return False
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected_option = (self.selected_option - 1) % len(self.options)
                return True
            elif event.key == pygame.K_DOWN:
                self.selected_option = (self.selected_option + 1) % len(self.options)
                return True
            elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                self._select_option()
                return True
        
        return False
    
    def _select_option(self):
        """Execute selected option."""
        option = self.options[self.selected_option]
        
        if option == "Try Again":
            if self.on_retry:
                self.on_retry()
            self.hide()
        elif "Town" in option:
            if self.on_town:
                self.on_town()
            self.hide()
        elif "Quit" in option:
            if self.on_quit:
                self.on_quit()
            self.hide()
    
    def render(self):
        """Render game over overlay."""
        if not self.visible:
            return
        
        # Red tint overlay that fades in
        alpha = min(180, int(self.timer * 100))
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((40, 0, 0, alpha))
        self.screen.blit(overlay, (0, 0))
        
        # Title with pulsing effect
        pulse = 0.9 + 0.1 * abs((self.timer % 2.0) - 1.0)
        title = self.font_title.render("GAME OVER", True, (200, 50, 50))
        
        # Scale effect
        scaled_size = (int(title.get_width() * pulse), int(title.get_height() * pulse))
        scaled_title = pygame.transform.scale(title, scaled_size)
        title_rect = scaled_title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3))
        self.screen.blit(scaled_title, title_rect)
        
        # Death message
        msg = self.font_small.render(self.death_message, True, COLOR_TEXT_DIM)
        msg_rect = msg.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3 + 60))
        self.screen.blit(msg, msg_rect)
        
        # Options (fade in after delay)
        if self.timer > 1.0:
            center_x = SCREEN_WIDTH // 2
            start_y = SCREEN_HEIGHT // 2 + 50
            
            for i, option in enumerate(self.options):
                y = start_y + i * 50
                is_selected = i == self.selected_option
                
                if is_selected:
                    rect = pygame.Rect(center_x - 120, y - 10, 240, 40)
                    pygame.draw.rect(self.screen, (80, 30, 30), rect)
                    pygame.draw.rect(self.screen, (200, 80, 80), rect, 2)
                
                color = (255, 200, 200) if is_selected else (150, 120, 120)
                text = self.font.render(option, True, color)
                text_rect = text.get_rect(center=(center_x, y + 8))
                self.screen.blit(text, text_rect)


class LoadingOverlay:
    """Loading screen overlay."""
    
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.visible = False
        self.message = "Loading..."
        self.progress = 0.0
        
        pygame.font.init()
        self.font_title = pygame.font.Font(None, 48)
        self.font = pygame.font.Font(None, 28)
    
    def show(self, message: str = "Loading..."):
        """Show loading screen."""
        self.visible = True
        self.message = message
        self.progress = 0.0
    
    def hide(self):
        """Hide loading screen."""
        self.visible = False
    
    def set_progress(self, progress: float):
        """Set loading progress (0.0 - 1.0)."""
        self.progress = max(0.0, min(1.0, progress))
    
    def render(self):
        """Render loading overlay."""
        if not self.visible:
            return
        
        # Dark background
        self.screen.fill((15, 12, 20))
        
        # Title
        title = self.font_title.render(self.message, True, COLOR_UI_ACCENT)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 30))
        self.screen.blit(title, title_rect)
        
        # Progress bar
        bar_width = 400
        bar_height = 20
        bar_x = (SCREEN_WIDTH - bar_width) // 2
        bar_y = SCREEN_HEIGHT // 2 + 20
        
        pygame.draw.rect(self.screen, (40, 35, 50), 
                        (bar_x, bar_y, bar_width, bar_height))
        pygame.draw.rect(self.screen, COLOR_UI_ACCENT,
                        (bar_x, bar_y, int(bar_width * self.progress), bar_height))
        pygame.draw.rect(self.screen, COLOR_UI_BORDER,
                        (bar_x, bar_y, bar_width, bar_height), 2)
        
        # Progress text
        pct = int(self.progress * 100)
        pct_text = self.font.render(f"{pct}%", True, COLOR_TEXT)
        pct_rect = pct_text.get_rect(center=(SCREEN_WIDTH // 2, bar_y + bar_height + 20))
        self.screen.blit(pct_text, pct_rect)

