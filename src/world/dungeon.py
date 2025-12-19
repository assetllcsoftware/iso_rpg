"""Procedural dungeon generation."""

import random
import numpy as np
from ..engine.constants import TILE_EMPTY, TILE_FLOOR, TILE_WALL, TILE_DOOR, TILE_STAIRS_DOWN


class Room:
    """A rectangular room in the dungeon."""
    
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.connected = False
    
    @property
    def center(self):
        return (self.x + self.width // 2, self.y + self.height // 2)
    
    @property
    def x2(self):
        return self.x + self.width
    
    @property
    def y2(self):
        return self.y + self.height
    
    def intersects(self, other, margin=1):
        """Check if this room intersects another (with margin)."""
        return (self.x - margin < other.x2 and 
                self.x2 + margin > other.x and
                self.y - margin < other.y2 and 
                self.y2 + margin > other.y)


class DungeonGenerator:
    """Generates procedural dungeons."""
    
    def __init__(self, width=50, height=50, seed=None):
        self.width = width
        self.height = height
        self.seed = seed
        
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)
        
        self.tiles = np.zeros((height, width), dtype=np.int8)
        self.rooms = []
        self.corridors = []
    
    def generate(self, num_rooms=10, min_room_size=5, max_room_size=12):
        """Generate a dungeon with rooms and corridors."""
        self.tiles.fill(TILE_EMPTY)
        self.rooms = []
        self.corridors = []
        
        # Generate rooms
        attempts = 0
        max_attempts = num_rooms * 20
        
        while len(self.rooms) < num_rooms and attempts < max_attempts:
            attempts += 1
            
            w = random.randint(min_room_size, max_room_size)
            h = random.randint(min_room_size, max_room_size)
            x = random.randint(1, self.width - w - 2)
            y = random.randint(1, self.height - h - 2)
            
            new_room = Room(x, y, w, h)
            
            # Check for intersections
            valid = True
            for room in self.rooms:
                if new_room.intersects(room, margin=2):
                    valid = False
                    break
            
            if valid:
                self.rooms.append(new_room)
                self._carve_room(new_room)
        
        # Connect rooms
        self._connect_rooms()
        
        # Add walls around floor tiles
        self._add_walls()
        
        return self.tiles
    
    def _carve_room(self, room):
        """Carve out a room."""
        for y in range(room.y, room.y2):
            for x in range(room.x, room.x2):
                self.tiles[y, x] = TILE_FLOOR
    
    def _connect_rooms(self):
        """Connect all rooms with corridors."""
        if len(self.rooms) < 2:
            return
        
        # Connect each room to the next
        for i in range(len(self.rooms) - 1):
            room1 = self.rooms[i]
            room2 = self.rooms[i + 1]
            self._create_corridor(room1.center, room2.center)
        
        # Add some extra connections for loops
        extra_connections = len(self.rooms) // 3
        for _ in range(extra_connections):
            room1 = random.choice(self.rooms)
            room2 = random.choice(self.rooms)
            if room1 != room2:
                self._create_corridor(room1.center, room2.center)
    
    def _create_corridor(self, start, end):
        """Create an L-shaped corridor between two points."""
        x1, y1 = start
        x2, y2 = end
        
        # Randomly choose horizontal-first or vertical-first
        if random.random() < 0.5:
            self._carve_h_corridor(x1, x2, y1)
            self._carve_v_corridor(y1, y2, x2)
        else:
            self._carve_v_corridor(y1, y2, x1)
            self._carve_h_corridor(x1, x2, y2)
    
    def _carve_h_corridor(self, x1, x2, y):
        """Carve a horizontal corridor."""
        for x in range(min(x1, x2), max(x1, x2) + 1):
            if 0 <= x < self.width and 0 <= y < self.height:
                self.tiles[y, x] = TILE_FLOOR
                # Make corridors 2 tiles wide
                if y + 1 < self.height:
                    self.tiles[y + 1, x] = TILE_FLOOR
    
    def _carve_v_corridor(self, y1, y2, x):
        """Carve a vertical corridor."""
        for y in range(min(y1, y2), max(y1, y2) + 1):
            if 0 <= x < self.width and 0 <= y < self.height:
                self.tiles[y, x] = TILE_FLOOR
                # Make corridors 2 tiles wide
                if x + 1 < self.width:
                    self.tiles[y, x + 1] = TILE_FLOOR
    
    def _add_walls(self):
        """Add walls around floor tiles."""
        wall_tiles = []
        
        for y in range(self.height):
            for x in range(self.width):
                if self.tiles[y, x] == TILE_EMPTY:
                    # Check if adjacent to floor
                    for dy in [-1, 0, 1]:
                        for dx in [-1, 0, 1]:
                            ny, nx = y + dy, x + dx
                            if 0 <= ny < self.height and 0 <= nx < self.width:
                                if self.tiles[ny, nx] == TILE_FLOOR:
                                    wall_tiles.append((y, x))
                                    break
                        else:
                            continue
                        break
        
        for y, x in wall_tiles:
            self.tiles[y, x] = TILE_WALL
    
    def get_spawn_points(self, num_points=1):
        """Get valid spawn points in rooms."""
        points = []
        
        for room in self.rooms:
            cx, cy = room.center
            points.append((cx, cy))
        
        return points[:num_points] if points else [(self.width // 2, self.height // 2)]
    
    def get_enemy_spawn_points(self, num_points=10):
        """Get spawn points for enemies, spread across rooms."""
        points = []
        
        for room in self.rooms[1:]:  # Skip first room (player spawn)
            # Add a few spawn points per room
            for _ in range(random.randint(1, 3)):
                x = random.randint(room.x + 1, room.x2 - 2)
                y = random.randint(room.y + 1, room.y2 - 2)
                points.append((x, y))
        
        random.shuffle(points)
        return points[:num_points]
    
    def place_stairs(self):
        """Place stairs in the last room."""
        if len(self.rooms) < 2:
            # Fallback - place in center of map
            cx, cy = self.width // 2, self.height // 2
            self.tiles[cy, cx] = TILE_STAIRS_DOWN
            return (cx, cy)
        
        # Put stairs in the room farthest from spawn
        last_room = self.rooms[-1]
        stairs_x, stairs_y = last_room.center
        
        # Make sure it's a valid floor tile
        self.tiles[stairs_y, stairs_x] = TILE_STAIRS_DOWN
        
        print(f"[DEBUG] Stairs placed at ({stairs_x}, {stairs_y})")
        
        return (stairs_x, stairs_y)

