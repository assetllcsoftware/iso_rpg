"""Town map - uses same tile system as dungeon."""

from typing import List, Tuple, Optional
from dataclasses import dataclass, field

from ..core.constants import TileType


@dataclass
class TownBuilding:
    """A building in town that can be interacted with."""
    x: int
    y: int
    width: int
    height: int
    name: str
    building_type: str  # 'blacksmith', 'alchemist', 'inn', 'portal'
    
    @property
    def center(self) -> Tuple[int, int]:
        return (self.x + self.width // 2, self.y + self.height // 2)
    
    @property
    def door(self) -> Tuple[int, int]:
        """Position in front of the building (where player stands to interact)."""
        return (self.x + self.width // 2, self.y + self.height)


class TownMap:
    """Town map using same interface as Dungeon for rendering."""
    
    def __init__(self, width: int = 40, height: int = 30):
        self.width = width
        self.height = height
        self.tiles = [[TileType.VOID for _ in range(width)] for _ in range(height)]
        self.buildings: List[TownBuilding] = []
        self.spawn_point: Tuple[int, int] = (width // 2, height // 2)
        
        # Empty lists to match Dungeon interface
        self.rooms = []
        self.decorations = []
        self.room_props = []
        self.floor_decor = []
        
        self._generate()
    
    def _generate(self):
        """Generate the town layout."""
        # Create grassy floor area
        for y in range(3, self.height - 3):
            for x in range(3, self.width - 3):
                self.tiles[y][x] = TileType.FLOOR
        
        # Stone path in the middle
        path_y = self.height // 2
        for x in range(3, self.width - 3):
            for dy in range(-1, 2):
                if 0 <= path_y + dy < self.height:
                    self.tiles[path_y + dy][x] = TileType.FLOOR
        
        # Vertical path
        path_x = self.width // 2
        for y in range(3, self.height - 3):
            for dx in range(-1, 2):
                if 0 <= path_x + dx < self.width:
                    self.tiles[y][path_x + dx] = TileType.FLOOR
        
        # Place buildings
        self._place_buildings()
        
        # Spawn point in center
        self.spawn_point = (self.width // 2, self.height // 2 + 2)
        
        # Add some water features
        self._add_fountain(self.width // 2, self.height // 2 - 4)
    
    def _place_buildings(self):
        """Place the town buildings."""
        cx, cy = self.width // 2, self.height // 2
        
        # Blacksmith - top left
        self._create_building(cx - 12, cy - 8, 5, 4, "Blacksmith", "blacksmith")
        
        # Alchemist - top right
        self._create_building(cx + 7, cy - 8, 5, 4, "Alchemist", "alchemist")
        
        # Inn - bottom left
        self._create_building(cx - 12, cy + 4, 6, 4, "Inn", "inn")
        
        # Portal - bottom right (smaller)
        self._create_building(cx + 8, cy + 5, 3, 3, "Portal", "portal")
    
    def _create_building(self, x: int, y: int, w: int, h: int, name: str, btype: str):
        """Create a building with walls."""
        building = TownBuilding(x, y, w, h, name, btype)
        self.buildings.append(building)
        
        if btype == 'portal':
            # Portal is just a special floor tile
            for by in range(y, y + h):
                for bx in range(x, x + w):
                    if 0 <= bx < self.width and 0 <= by < self.height:
                        self.tiles[by][bx] = TileType.STAIRS_UP
        else:
            # Draw building footprint as walls
            for by in range(y, y + h):
                for bx in range(x, x + w):
                    if 0 <= bx < self.width and 0 <= by < self.height:
                        self.tiles[by][bx] = TileType.WALL
            
            # Door tile (walkable, in front of building)
            door_x, door_y = x + w // 2, y + h
            if 0 <= door_x < self.width and 0 <= door_y < self.height:
                self.tiles[door_y][door_x] = TileType.DOOR
    
    def _add_fountain(self, x: int, y: int):
        """Add a small fountain."""
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                fx, fy = x + dx, y + dy
                if 0 <= fx < self.width and 0 <= fy < self.height:
                    self.tiles[fy][fx] = TileType.WATER
    
    def get_tile(self, x: int, y: int) -> TileType:
        """Get tile type at position."""
        if not (0 <= x < self.width and 0 <= y < self.height):
            return TileType.VOID
        return self.tiles[y][x]
    
    def is_walkable(self, x: int, y: int) -> bool:
        """Check if a tile is walkable."""
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            return False
        tile = self.tiles[int(y)][int(x)]
        return tile in (TileType.FLOOR, TileType.DOOR, TileType.STAIRS_UP, TileType.STAIRS_DOWN)
    
    def get_building_at(self, x: float, y: float) -> Optional[TownBuilding]:
        """Get building at position (checks door area or inside for portal)."""
        ix, iy = int(x), int(y)
        
        for building in self.buildings:
            if building.building_type == 'portal':
                # Portal - check if standing on it
                if (building.x <= ix < building.x + building.width and
                    building.y <= iy < building.y + building.height):
                    return building
            else:
                # Other buildings - check if at door position
                door_x, door_y = building.door
                if abs(ix - door_x) <= 1 and abs(iy - door_y) <= 1:
                    return building
        
        return None
    
    def has_line_of_sight(self, x1: float, y1: float, x2: float, y2: float) -> bool:
        """Always return True in town (no combat)."""
        return True
    
    def get_player_spawn(self) -> Tuple[float, float]:
        """Return the spawn point for players entering town."""
        return (float(self.spawn_point[0]), float(self.spawn_point[1]))

