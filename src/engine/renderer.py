"""Isometric rendering system."""

import pygame
import math
from .constants import (
    TILE_WIDTH, TILE_HEIGHT, SCREEN_WIDTH, SCREEN_HEIGHT,
    TILE_FLOOR, TILE_WALL, TILE_DOOR, TILE_WATER, TILE_LAVA, TILE_STAIRS_DOWN,
    COLOR_BG, COLOR_UI_ACCENT
)


class IsometricRenderer:
    """Handles all isometric rendering."""
    
    def __init__(self, screen):
        self.screen = screen
        self.tile_surfaces = {}
        self._create_tile_surfaces()
    
    def _create_tile_surfaces(self):
        """Pre-render tile surfaces."""
        # Floor tile - dark stone
        self.tile_surfaces[TILE_FLOOR] = self._create_diamond_tile(
            (45, 40, 55), (35, 30, 45), (55, 50, 65)
        )
        
        # Wall tile - raised block
        self.tile_surfaces[TILE_WALL] = self._create_wall_tile(
            (70, 60, 85), (50, 45, 65), (90, 80, 105)
        )
        
        # Door tile
        self.tile_surfaces[TILE_DOOR] = self._create_diamond_tile(
            (100, 70, 50), (80, 55, 40), (120, 85, 60)
        )
        
        # Water tile - animated would be nice
        self.tile_surfaces[TILE_WATER] = self._create_diamond_tile(
            (40, 70, 120), (30, 55, 100), (50, 85, 140)
        )
        
        # Lava tile
        self.tile_surfaces[TILE_LAVA] = self._create_diamond_tile(
            (180, 80, 30), (140, 50, 20), (220, 120, 40)
        )
        
        # Stairs down
        self.tile_surfaces[TILE_STAIRS_DOWN] = self._create_stairs_tile()
    
    def _create_diamond_tile(self, top_color, left_color, right_color):
        """Create a diamond-shaped floor tile."""
        surface = pygame.Surface((TILE_WIDTH, TILE_HEIGHT), pygame.SRCALPHA)
        
        # Diamond points
        points = [
            (TILE_WIDTH // 2, 0),           # Top
            (TILE_WIDTH, TILE_HEIGHT // 2),  # Right
            (TILE_WIDTH // 2, TILE_HEIGHT),  # Bottom
            (0, TILE_HEIGHT // 2),           # Left
        ]
        
        pygame.draw.polygon(surface, top_color, points)
        pygame.draw.polygon(surface, (20, 18, 25), points, 1)
        
        return surface
    
    def _create_wall_tile(self, top_color, left_color, right_color):
        """Create a 3D wall block."""
        wall_height = TILE_HEIGHT * 2
        surface = pygame.Surface((TILE_WIDTH, TILE_HEIGHT + wall_height), pygame.SRCALPHA)
        
        # Top face
        top_points = [
            (TILE_WIDTH // 2, 0),
            (TILE_WIDTH, TILE_HEIGHT // 2),
            (TILE_WIDTH // 2, TILE_HEIGHT),
            (0, TILE_HEIGHT // 2),
        ]
        
        # Left face
        left_points = [
            (0, TILE_HEIGHT // 2),
            (TILE_WIDTH // 2, TILE_HEIGHT),
            (TILE_WIDTH // 2, TILE_HEIGHT + wall_height),
            (0, TILE_HEIGHT // 2 + wall_height),
        ]
        
        # Right face
        right_points = [
            (TILE_WIDTH, TILE_HEIGHT // 2),
            (TILE_WIDTH // 2, TILE_HEIGHT),
            (TILE_WIDTH // 2, TILE_HEIGHT + wall_height),
            (TILE_WIDTH, TILE_HEIGHT // 2 + wall_height),
        ]
        
        pygame.draw.polygon(surface, left_color, left_points)
        pygame.draw.polygon(surface, right_color, right_points)
        pygame.draw.polygon(surface, top_color, top_points)
        
        # Outlines
        pygame.draw.polygon(surface, (20, 18, 25), top_points, 1)
        pygame.draw.polygon(surface, (20, 18, 25), left_points, 1)
        pygame.draw.polygon(surface, (20, 18, 25), right_points, 1)
        
        return surface
    
    def _create_stairs_tile(self):
        """Create stairs going down tile."""
        surface = pygame.Surface((TILE_WIDTH, TILE_HEIGHT + 16), pygame.SRCALPHA)
        
        # Base floor
        points = [
            (TILE_WIDTH // 2, 0),
            (TILE_WIDTH, TILE_HEIGHT // 2),
            (TILE_WIDTH // 2, TILE_HEIGHT),
            (0, TILE_HEIGHT // 2),
        ]
        pygame.draw.polygon(surface, (35, 30, 45), points)
        
        # Draw stair steps going "down"
        step_colors = [(60, 50, 70), (50, 40, 60), (40, 30, 50), (30, 25, 40)]
        for i, color in enumerate(step_colors):
            offset_y = i * 3 + 4
            step_points = [
                (TILE_WIDTH // 2, offset_y),
                (TILE_WIDTH - 8 - i * 4, TILE_HEIGHT // 2 + offset_y // 2),
                (TILE_WIDTH // 2, TILE_HEIGHT - 4 + offset_y // 2),
                (8 + i * 4, TILE_HEIGHT // 2 + offset_y // 2),
            ]
            pygame.draw.polygon(surface, color, step_points)
        
        # Highlight/glow effect for visibility
        pygame.draw.polygon(surface, (100, 180, 100), points, 2)
        
        return surface
    
    def render_world(self, world, camera):
        """Render the world tiles in isometric order."""
        self.screen.fill(COLOR_BG)
        
        if world is None:
            return
        
        tiles = world.tiles
        height, width = tiles.shape
        
        # Calculate visible range
        # Render in correct isometric order (back to front)
        for layer in range(width + height):
            for x in range(max(0, layer - height + 1), min(layer + 1, width)):
                y = layer - x
                if 0 <= y < height:
                    tile_type = tiles[y, x]
                    if tile_type == 0:
                        continue
                    
                    screen_x, screen_y = camera.world_to_screen(x, y)
                    
                    # Skip if off screen
                    if screen_x < -TILE_WIDTH * 2 or screen_x > SCREEN_WIDTH + TILE_WIDTH:
                        continue
                    if screen_y < -TILE_HEIGHT * 4 or screen_y > SCREEN_HEIGHT + TILE_HEIGHT:
                        continue
                    
                    surface = self.tile_surfaces.get(tile_type)
                    if surface:
                        # Adjust position for tile anchor
                        draw_x = screen_x - TILE_WIDTH // 2
                        draw_y = screen_y - TILE_HEIGHT // 2
                        
                        # Walls need offset for their height
                        if tile_type == TILE_WALL:
                            draw_y -= TILE_HEIGHT * 2
                        
                        # Apply zoom
                        if camera.zoom != 1.0:
                            scaled = pygame.transform.scale(
                                surface,
                                (int(surface.get_width() * camera.zoom),
                                 int(surface.get_height() * camera.zoom))
                            )
                            draw_x = screen_x - scaled.get_width() // 2
                            draw_y = screen_y - scaled.get_height() // 2
                            if tile_type == TILE_WALL:
                                draw_y -= int(TILE_HEIGHT * 2 * camera.zoom)
                            self.screen.blit(scaled, (draw_x, draw_y))
                        else:
                            self.screen.blit(surface, (draw_x, draw_y))
    
    def render_entity(self, entity, camera):
        """Render an entity at its world position."""
        screen_x, screen_y = camera.world_to_screen(entity.x, entity.y)
        
        # Get entity sprite or create placeholder
        size = int(24 * camera.zoom)
        
        # Check if entity is downed
        is_downed = getattr(entity, 'is_downed', False)
        
        # Draw shadow
        shadow_rect = pygame.Rect(
            screen_x - size // 2,
            screen_y - size // 4,
            size,
            size // 2
        )
        shadow_surf = pygame.Surface((size, size // 2), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_surf, (0, 0, 0, 80), shadow_surf.get_rect())
        self.screen.blit(shadow_surf, shadow_rect)
        
        # Draw entity body
        entity_color = entity.color if hasattr(entity, 'color') else (200, 150, 100)
        
        if is_downed:
            # Downed: draw lying down (horizontal ellipse)
            body_rect = pygame.Rect(
                screen_x - size // 2,
                screen_y - size // 4,
                size,
                size // 3
            )
            # Fade the color to show they're downed
            faded_color = tuple(c // 2 for c in entity_color)
            pygame.draw.ellipse(self.screen, faded_color, body_rect)
            pygame.draw.ellipse(self.screen, (30, 25, 40), body_rect, 2)
            
            # Pulsing "revive me" indicator
            time = pygame.time.get_ticks() / 1000
            pulse = abs(math.sin(time * 2)) * 0.5 + 0.5
            indicator_color = (255, int(255 * pulse), 0)
            pygame.draw.circle(self.screen, indicator_color, 
                             (screen_x, screen_y - size // 2), 6)
            pygame.draw.circle(self.screen, (30, 25, 40), 
                             (screen_x, screen_y - size // 2), 6, 1)
        else:
            # Normal: draw standing (vertical ellipse)
            body_rect = pygame.Rect(
                screen_x - size // 3,
                screen_y - size,
                size * 2 // 3,
                size
            )
            pygame.draw.ellipse(self.screen, entity_color, body_rect)
            pygame.draw.ellipse(self.screen, (30, 25, 40), body_rect, 2)
        
        # Health bar above entity (only if not downed)
        if hasattr(entity, 'health') and hasattr(entity, 'max_health') and not is_downed:
            bar_width = size
            bar_height = 4
            bar_x = screen_x - bar_width // 2
            bar_y = screen_y - size - 10
            
            # Background
            pygame.draw.rect(self.screen, (30, 25, 40),
                           (bar_x, bar_y, bar_width, bar_height))
            
            # Health fill
            health_pct = entity.health / entity.max_health
            health_color = (160, 45, 55) if health_pct < 0.3 else (90, 160, 90)
            pygame.draw.rect(self.screen, health_color,
                           (bar_x, bar_y, int(bar_width * health_pct), bar_height))
    
    def render_selection(self, entity, camera):
        """Render selection indicator around entity."""
        screen_x, screen_y = camera.world_to_screen(entity.x, entity.y)
        size = int(32 * camera.zoom)
        
        # Pulsing selection circle
        time = pygame.time.get_ticks() / 1000
        pulse = abs(math.sin(time * 3)) * 0.3 + 0.7
        
        color = tuple(int(c * pulse) for c in COLOR_UI_ACCENT)
        pygame.draw.circle(self.screen, color, (screen_x, screen_y), size // 2 + 4, 2)
    
    def render_path(self, path, camera):
        """Render a movement path."""
        if len(path) < 2:
            return
        
        points = [camera.world_to_screen(p[0], p[1]) for p in path]
        pygame.draw.lines(self.screen, (100, 180, 100, 128), False, points, 2)
        
        # Draw end marker
        end = points[-1]
        pygame.draw.circle(self.screen, (100, 180, 100), end, 6, 2)

