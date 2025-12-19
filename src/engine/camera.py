"""Isometric camera system."""

import pygame
from .constants import SCREEN_WIDTH, SCREEN_HEIGHT, TILE_WIDTH, TILE_HEIGHT


class Camera:
    """Isometric camera with smooth scrolling and zoom."""
    
    def __init__(self):
        self.x = 0.0
        self.y = 0.0
        self.target_x = 0.0
        self.target_y = 0.0
        self.zoom = 1.0
        self.min_zoom = 0.5
        self.max_zoom = 2.0
        self.smooth_speed = 8.0
        self.dragging = False
        self.drag_start = None
        self.drag_camera_start = None
    
    def world_to_screen(self, world_x, world_y):
        """Convert world coordinates to isometric screen coordinates."""
        # Isometric transformation
        iso_x = (world_x - world_y) * (TILE_WIDTH // 2)
        iso_y = (world_x + world_y) * (TILE_HEIGHT // 2)
        
        # Apply camera offset and zoom
        screen_x = (iso_x - self.x) * self.zoom + SCREEN_WIDTH // 2
        screen_y = (iso_y - self.y) * self.zoom + SCREEN_HEIGHT // 2
        
        return int(screen_x), int(screen_y)
    
    def screen_to_world(self, screen_x, screen_y):
        """Convert screen coordinates to world coordinates."""
        # Reverse camera offset and zoom
        iso_x = (screen_x - SCREEN_WIDTH // 2) / self.zoom + self.x
        iso_y = (screen_y - SCREEN_HEIGHT // 2) / self.zoom + self.y
        
        # Reverse isometric transformation
        world_x = (iso_x / (TILE_WIDTH // 2) + iso_y / (TILE_HEIGHT // 2)) / 2
        world_y = (iso_y / (TILE_HEIGHT // 2) - iso_x / (TILE_WIDTH // 2)) / 2
        
        return world_x, world_y
    
    def follow(self, world_x, world_y, instant=False):
        """Set camera to follow a world position."""
        iso_x = (world_x - world_y) * (TILE_WIDTH // 2)
        iso_y = (world_x + world_y) * (TILE_HEIGHT // 2)
        
        self.target_x = iso_x
        self.target_y = iso_y
        
        if instant:
            self.x = self.target_x
            self.y = self.target_y
    
    def update(self, dt):
        """Smooth camera movement."""
        if not self.dragging:
            lerp = min(1.0, self.smooth_speed * dt)
            self.x += (self.target_x - self.x) * lerp
            self.y += (self.target_y - self.y) * lerp
    
    def start_drag(self, screen_pos):
        """Start camera drag."""
        self.dragging = True
        self.drag_start = screen_pos
        self.drag_camera_start = (self.x, self.y)
    
    def update_drag(self, screen_pos):
        """Update camera position during drag."""
        if self.dragging and self.drag_start:
            dx = (self.drag_start[0] - screen_pos[0]) / self.zoom
            dy = (self.drag_start[1] - screen_pos[1]) / self.zoom
            self.x = self.drag_camera_start[0] + dx
            self.y = self.drag_camera_start[1] + dy
            self.target_x = self.x
            self.target_y = self.y
    
    def end_drag(self):
        """End camera drag."""
        self.dragging = False
        self.drag_start = None
    
    def set_zoom(self, zoom):
        """Set zoom level with clamping."""
        self.zoom = max(self.min_zoom, min(self.max_zoom, zoom))
    
    def zoom_at(self, screen_pos, zoom_delta):
        """Zoom towards a screen position."""
        old_world = self.screen_to_world(*screen_pos)
        self.set_zoom(self.zoom + zoom_delta)
        new_world = self.screen_to_world(*screen_pos)
        
        # Adjust camera to keep the point under cursor
        dx = (old_world[0] - new_world[0])
        dy = (old_world[1] - new_world[1])
        iso_dx = (dx - dy) * (TILE_WIDTH // 2)
        iso_dy = (dx + dy) * (TILE_HEIGHT // 2)
        self.x += iso_dx
        self.y += iso_dy
        self.target_x = self.x
        self.target_y = self.y

