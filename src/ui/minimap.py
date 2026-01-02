"""Minimap rendering with fog of war."""

import pygame
import esper
from typing import Optional, Tuple, Set

from ..core.constants import (
    COLOR_UI_BG, COLOR_UI_BORDER,
    TILE_WIDTH, TILE_HEIGHT
)
from ..ecs.components import Position, PartyMember, Enemy, Selected, Dead


class Minimap:
    """Renders a minimap showing dungeon layout with fog of war."""
    
    def __init__(self, screen: pygame.Surface, size: int = 150):
        self.screen = screen
        self.size = size
        self.x = self.screen.get_width() - size - 20
        self.y = 20
        
        # Colors
        self.color_wall = (50, 45, 55)
        self.color_floor = (70, 65, 80)
        self.color_player = (100, 200, 255)
        self.color_ally = (100, 255, 150)
        self.color_enemy = (255, 100, 100)
        self.color_stairs_down = (255, 200, 100)  # Gold/orange - descend
        self.color_stairs_up = (100, 200, 255)    # Blue - ascend
        self.color_fog = (25, 22, 30)
        self.color_unexplored = (15, 12, 18)
        
        # Dungeon reference
        self.dungeon = None
        self.dungeon_scale = 1.0
        self.dungeon_offset = (0, 0)
        
        # Fog of war - explored tiles
        self.explored: Set[Tuple[int, int]] = set()
        self.explore_radius = 6  # How far the player can see
    
    def set_dungeon(self, dungeon):
        """Set dungeon reference and reset fog of war."""
        self.dungeon = dungeon
        self.explored.clear()
        
        if not dungeon:
            return
        
        # Calculate scale to fit dungeon in minimap
        self.dungeon_scale = min(
            (self.size - 10) / dungeon.width,
            (self.size - 10) / dungeon.height
        )
        
        # Center offset
        map_width = int(dungeon.width * self.dungeon_scale)
        map_height = int(dungeon.height * self.dungeon_scale)
        self.dungeon_offset = (
            (self.size - map_width) // 2,
            (self.size - map_height) // 2
        )
    
    def update_explored(self, x: int, y: int):
        """Mark tiles as explored around position."""
        for dy in range(-self.explore_radius, self.explore_radius + 1):
            for dx in range(-self.explore_radius, self.explore_radius + 1):
                if dx * dx + dy * dy <= self.explore_radius * self.explore_radius:
                    self.explored.add((x + dx, y + dy))
    
    def is_explored(self, x: int, y: int) -> bool:
        """Check if a tile has been explored."""
        return (x, y) in self.explored
    
    def render(self, center_entity: int = -1):
        """Render the minimap with fog of war."""
        # Background
        pygame.draw.rect(self.screen, COLOR_UI_BG, 
                        (self.x, self.y, self.size, self.size))
        pygame.draw.rect(self.screen, COLOR_UI_BORDER,
                        (self.x, self.y, self.size, self.size), 2)
        
        if not self.dungeon:
            return
        
        # Update explored tiles around party members
        for ent, (pos, _) in esper.get_components(Position, PartyMember):
            if not esper.has_component(ent, Dead):
                self.update_explored(int(pos.x), int(pos.y))
        
        # Draw dungeon tiles (only explored ones)
        tile_size = max(1, int(self.dungeon_scale))
        
        for y in range(self.dungeon.height):
            for x in range(self.dungeon.width):
                tile_x = self.x + self.dungeon_offset[0] + int(x * self.dungeon_scale)
                tile_y = self.y + self.dungeon_offset[1] + int(y * self.dungeon_scale)
                
                if self.is_explored(x, y):
                    # Show explored tile
                    if self.dungeon.is_walkable(x, y):
                        color = self.color_floor
                    else:
                        color = self.color_wall
                else:
                    # Unexplored - show as dark
                    color = self.color_unexplored
                
                pygame.draw.rect(
                    self.screen, color,
                    (tile_x, tile_y, tile_size, tile_size)
                )
        
        # Draw stairs (only if explored)
        # Stairs down (gold) - to descend deeper
        if self.dungeon.stairs_down:
            sx, sy = self.dungeon.stairs_down
            if self.is_explored(sx, sy):
                stair_x = self.x + self.dungeon_offset[0] + int(sx * self.dungeon_scale)
                stair_y = self.y + self.dungeon_offset[1] + int(sy * self.dungeon_scale)
                pygame.draw.rect(
                    self.screen, self.color_stairs_down,
                    (stair_x, stair_y, max(2, tile_size * 2), max(2, tile_size * 2))
                )
        
        # Stairs up (blue) - to go back up
        if self.dungeon.stairs_up:
            sx, sy = self.dungeon.stairs_up
            if self.is_explored(sx, sy):
                stair_x = self.x + self.dungeon_offset[0] + int(sx * self.dungeon_scale)
                stair_y = self.y + self.dungeon_offset[1] + int(sy * self.dungeon_scale)
                pygame.draw.rect(
                    self.screen, self.color_stairs_up,
                    (stair_x, stair_y, max(2, tile_size * 2), max(2, tile_size * 2))
                )
        
        # Draw entities
        self._render_entities()
    
    def _render_entities(self):
        """Render entity markers on minimap (only in explored areas)."""
        # Draw enemies (only if in explored area)
        for ent, (pos, _) in esper.get_components(Position, Enemy):
            if esper.has_component(ent, Dead):
                continue
            if self.is_explored(int(pos.x), int(pos.y)):
                self._draw_entity_marker(pos.x, pos.y, self.color_enemy, 2)
        
        # Draw party members (always visible)
        for ent, (pos, member) in esper.get_components(Position, PartyMember):
            is_selected = esper.has_component(ent, Selected)
            color = self.color_player if is_selected else self.color_ally
            size = 4 if is_selected else 3
            self._draw_entity_marker(pos.x, pos.y, color, size)
    
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

