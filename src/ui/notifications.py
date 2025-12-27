"""Floating notification system."""

import pygame
from typing import List, Tuple, Optional
from dataclasses import dataclass

from ..core.constants import SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_TEXT


@dataclass
class Notification:
    """A single notification message."""
    text: str
    color: Tuple[int, int, int]
    time_remaining: float
    y_offset: float = 0.0


class NotificationManager:
    """Manages floating notifications."""
    
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.notifications: List[Notification] = []
        self.max_notifications = 5
        self.notification_duration = 3.0
        
        pygame.font.init()
        self.font = pygame.font.Font(None, 28)
        self.font_shadow = pygame.font.Font(None, 28)
    
    def add(self, text: str, color: Tuple[int, int, int] = COLOR_TEXT):
        """Add a new notification."""
        notification = Notification(
            text=text,
            color=color,
            time_remaining=self.notification_duration
        )
        
        self.notifications.append(notification)
        
        # Limit number of notifications
        while len(self.notifications) > self.max_notifications:
            self.notifications.pop(0)
    
    def update(self, dt: float):
        """Update notification timers."""
        for notification in self.notifications[:]:
            notification.time_remaining -= dt
            notification.y_offset += dt * 20  # Float upward
            
            if notification.time_remaining <= 0:
                self.notifications.remove(notification)
    
    def render(self):
        """Render all active notifications."""
        if not self.notifications:
            return
        
        base_y = SCREEN_HEIGHT // 3
        
        for i, notification in enumerate(self.notifications[-self.max_notifications:]):
            y = base_y + i * 30 - int(notification.y_offset)
            
            # Fade out near end
            alpha = min(255, int(255 * (notification.time_remaining / 0.5)))
            if notification.time_remaining > 0.5:
                alpha = 255
            
            # Shadow
            shadow_surf = self.font_shadow.render(notification.text, True, (0, 0, 0))
            shadow_surf.set_alpha(alpha)
            shadow_rect = shadow_surf.get_rect(center=(SCREEN_WIDTH // 2 + 2, y + 2))
            self.screen.blit(shadow_surf, shadow_rect)
            
            # Text
            text_surf = self.font.render(notification.text, True, notification.color)
            text_surf.set_alpha(alpha)
            text_rect = text_surf.get_rect(center=(SCREEN_WIDTH // 2, y))
            self.screen.blit(text_surf, text_rect)
    
    def clear(self):
        """Clear all notifications."""
        self.notifications.clear()

