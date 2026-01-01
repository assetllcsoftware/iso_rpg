"""Minimap rendering."""

import pygame
import esper
from typing import Optional, Tuple

from ..core.constants import (
    COLOR_UI_BG, COLOR_UI_BORDER,
    TILE_WIDTH, TILE_HEIGHT
)
from ..ecs.components import Position, PartyMember, Enemy, Selected


class Minimap:
    """Renders a minimap showing dungeon layout and entities."""
    
    def __init__(self, screen: pygame.Surface, size: int = 150):
        self.screen = screen
        self.size = size
        self.surface = pygame.Surface((size, size))
        self.x = self.screen.get_width() - size - 20
        self.y = 20
        
        # Colors
        self.color_wall = (40, 35, 45)
        self.color_floor = (60, 55, 70)
        self.color_player = (100, 200, 255)
        self.color_ally = (100, 255, 150)
        self.color_enemy = (255, 100, 100)
        self.color_stairs = (255, 200, 100)
        self.color_fog = (20, 18, 25)
        
        # Cached dungeon data
        self.dungeon_surface: Optional[pygame.Surface] = None
        self.dungeon_scale = 1.0
        self.dungeon_offset = (0, 0)
        
        # Visibility tracking (explored tiles)
        self.explored = set()
    
    def set_dungeon(self, dungeon):
        """Pre-render dungeon to minimap surface."""
        if not dungeon:
            self.dungeon_surface = None
            return
        
        # Calculate scale to fit dungeon in minimap
        self.dungeon_scale = min(
            (self.size - 10) / dungeon.width,
            (self.size - 10) / dungeon.height
        )
        
        # Create surface
        map_width = int(dungeon.width * self.dungeon_scale)
        map_height = int(dungeon.height * self.dungeon_scale)
        
        self.dungeon_surface = pygame.Surface((map_width, map_height))
        self.dungeon_surface.fill(self.color_fog)
        
        # Draw tiles
        for y in range(dungeon.height):
            for x in range(dungeon.width):
                tile_x = int(x * self.dungeon_scale)
                tile_y = int(y * self.dungeon_scale)
                tile_size = max(1, int(self.dungeon_scale))
                
                if dungeon.is_walkable(x, y):
                    color = self.color_floor
                else:
                    color = self.color_wall
                
                pygame.draw.rect(
                    self.dungeon_surface, color,
                    (tile_x, tile_y, tile_size, tile_size)
                )
        
        # Draw stairs
        if dungeon.stairs_down:
            sx, sy = dungeon.stairs_down
            stair_x = int(sx * self.dungeon_scale)
            stair_y = int(sy * self.dungeon_scale)
            pygame.draw.rect(
                self.dungeon_surface, self.color_stairs,
                (stair_x, stair_y, max(2, int(self.dungeon_scale * 2)),
                 max(2, int(self.dungeon_scale * 2)))
            )
        
        # Center offset
        self.dungeon_offset = (
            (self.size - map_width) // 2,
            (self.size - map_height) // 2
        )
    
    def update_explored(self, x: int, y: int, radius: int = 5):
        """Mark tiles as explored around position."""
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                if dx * dx + dy * dy <= radius * radius:
                    self.explored.add((x + dx, y + dy))
    
    def render(self, center_entity: int = -1):
        """Render the minimap."""
        # Background
        pygame.draw.rect(self.screen, COLOR_UI_BG, 
                        (self.x, self.y, self.size, self.size))
        pygame.draw.rect(self.screen, COLOR_UI_BORDER,
                        (self.x, self.y, self.size, self.size), 2)
        
        if not self.dungeon_surface:
            return
        
        # Blit dungeon
        self.screen.blit(
            self.dungeon_surface,
            (self.x + self.dungeon_offset[0], self.y + self.dungeon_offset[1])
        )
        
        # Draw entities
        self._render_entities()
    
    def _render_entities(self):
        """Render entity markers on minimap."""
        # Draw enemies first (red dots)
        for ent, (pos, _) in esper.get_components(Position, Enemy):
            self._draw_entity_marker(pos.x, pos.y, self.color_enemy, 2)
        
        # Draw party members
        for ent, (pos, member) in esper.get_components(Position, PartyMember):
            is_selected = esper.has_component(ent, Selected)
            color = self.color_player if is_selected else self.color_ally
            size = 4 if is_selected else 3
            self._draw_entity_marker(pos.x, pos.y, color, size)
            
            # Update fog of war around party members
            self.update_explored(int(pos.x), int(pos.y))
    
    def _draw_entity_marker(self, world_x: float, world_y: float, 
                           color: Tuple[int, int, int], size: int):
        """Draw an entity marker on the minimap."""
        map_x = self.x + self.dungeon_offset[0] + int(world_x * self.dungeon_scale)
        map_y = self.y + self.dungeon_offset[1] + int(world_y * self.dungeon_scale)
        
        pygame.draw.circle(self.screen, color, (map_x, map_y), size)
    
    def get_clicked_position(self, mouse_pos: Tuple[int, int]) -> Optional[Tuple[int, int]]:
        """Convert minimap click to world position."""
        mx, my = mouse_pos
        
        if not (self.x <= mx <= self.x + self.size and 
                self.y <= my <= self.y + self.size):
            return None
        
        if not self.dungeon_surface:
            return None
        
        # Convert to world coords
        local_x = mx - self.x - self.dungeon_offset[0]
        local_y = my - self.y - self.dungeon_offset[1]
        
        world_x = int(local_x / self.dungeon_scale)
        world_y = int(local_y / self.dungeon_scale)
        
        return (world_x, world_y)

