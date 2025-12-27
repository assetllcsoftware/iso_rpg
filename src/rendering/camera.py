"""Camera for viewport management."""

from ..core.constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, TILE_WIDTH, TILE_HEIGHT,
    CAMERA_ZOOM_DEFAULT, CAMERA_ZOOM_MIN, CAMERA_ZOOM_MAX,
    CAMERA_SMOOTH_SPEED
)


class Camera:
    """Isometric camera with smooth following and zoom."""
    
    def __init__(self, screen_width: int = SCREEN_WIDTH, screen_height: int = SCREEN_HEIGHT):
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # Camera position (in world coordinates)
        self.x = 0.0
        self.y = 0.0
        
        # Target position (for smooth following)
        self.target_x = 0.0
        self.target_y = 0.0
        
        # Zoom
        self.zoom = CAMERA_ZOOM_DEFAULT
        
        # Smoothing
        self.smooth_speed = CAMERA_SMOOTH_SPEED
    
    def update(self, dt: float):
        """Update camera position (smooth follow)."""
        # Lerp toward target
        self.x += (self.target_x - self.x) * self.smooth_speed * dt
        self.y += (self.target_y - self.y) * self.smooth_speed * dt
    
    def follow(self, world_x: float, world_y: float):
        """Set target to follow (usually player position)."""
        self.target_x = world_x
        self.target_y = world_y
    
    def center_on(self, world_x: float, world_y: float):
        """Immediately center on position."""
        self.x = world_x
        self.y = world_y
        self.target_x = world_x
        self.target_y = world_y
    
    def adjust_zoom(self, delta: float):
        """Adjust zoom level."""
        self.zoom = max(CAMERA_ZOOM_MIN, min(CAMERA_ZOOM_MAX, self.zoom + delta * 0.1))
    
    def world_to_screen(self, world_x: float, world_y: float) -> tuple:
        """Convert world coordinates to screen coordinates (isometric)."""
        # Isometric projection
        iso_x = (world_x - world_y) * (TILE_WIDTH / 2)
        iso_y = (world_x + world_y) * (TILE_HEIGHT / 2)
        
        # Apply zoom
        iso_x *= self.zoom
        iso_y *= self.zoom
        
        # Apply camera offset (center on camera position)
        cam_iso_x = (self.x - self.y) * (TILE_WIDTH / 2) * self.zoom
        cam_iso_y = (self.x + self.y) * (TILE_HEIGHT / 2) * self.zoom
        
        screen_x = iso_x - cam_iso_x + self.screen_width / 2
        screen_y = iso_y - cam_iso_y + self.screen_height / 2
        
        return (int(screen_x), int(screen_y))
    
    def screen_to_world(self, screen_x: int, screen_y: int) -> tuple:
        """Convert screen coordinates to world coordinates."""
        # Reverse the camera offset
        cam_iso_x = (self.x - self.y) * (TILE_WIDTH / 2) * self.zoom
        cam_iso_y = (self.x + self.y) * (TILE_HEIGHT / 2) * self.zoom
        
        iso_x = (screen_x - self.screen_width / 2 + cam_iso_x) / self.zoom
        iso_y = (screen_y - self.screen_height / 2 + cam_iso_y) / self.zoom
        
        # Reverse isometric projection
        world_x = (iso_x / (TILE_WIDTH / 2) + iso_y / (TILE_HEIGHT / 2)) / 2
        world_y = (iso_y / (TILE_HEIGHT / 2) - iso_x / (TILE_WIDTH / 2)) / 2
        
        return (world_x, world_y)
    
    def get_visible_bounds(self) -> tuple:
        """Get visible world bounds (min_x, min_y, max_x, max_y)."""
        # Screen corners in world coords
        margin = 5  # Extra tiles around edges
        
        # Approximate - just use camera center and screen size
        half_tiles_x = (self.screen_width / (TILE_WIDTH * self.zoom)) + margin
        half_tiles_y = (self.screen_height / (TILE_HEIGHT * self.zoom)) + margin
        
        return (
            self.x - half_tiles_x,
            self.y - half_tiles_y,
            self.x + half_tiles_x,
            self.y + half_tiles_y
        )

