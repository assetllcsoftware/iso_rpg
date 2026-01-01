"""Dungeon generation and tile map."""

import random
from typing import List, Tuple, Optional, Set
from dataclasses import dataclass, field

from ..core.constants import TileType


@dataclass
class Room:
    """A room in the dungeon."""
    x: int
    y: int
    width: int
    height: int
    
    @property
    def center(self) -> Tuple[int, int]:
        return (self.x + self.width // 2, self.y + self.height // 2)
    
    @property
    def inner(self) -> Tuple[int, int, int, int]:
        """Inner area (excluding walls)."""
        return (self.x + 1, self.y + 1, self.width - 2, self.height - 2)
    
    def intersects(self, other: 'Room', margin: int = 1) -> bool:
        """Check if rooms overlap (with margin)."""
        return (
            self.x - margin <= other.x + other.width and
            self.x + self.width + margin >= other.x and
            self.y - margin <= other.y + other.height and
            self.y + self.height + margin >= other.y
        )


@dataclass
class Decoration:
    """A decorative element in the dungeon (void spaces)."""
    x: int
    y: int
    type: str  # 'palm_tree', 'rock', 'ruin', 'water', 'plant'
    size: float = 1.0
    variant: int = 0


@dataclass
class RoomProp:
    """A prop inside a room (barrel, urn, chest, etc.)."""
    x: float
    y: float
    type: str  # 'barrel', 'urn', 'chest', 'crate', 'pot'
    variant: int = 0
    breakable: bool = True
    has_loot: bool = False  # Only ~10% have anything


@dataclass
class FloorDecor:
    """Decorative floor pattern/tile."""
    x: int
    y: int
    type: str  # 'rug', 'mosaic', 'pattern', 'crack', 'stain'
    width: int = 1
    height: int = 1
    variant: int = 0


class Dungeon:
    """Procedurally generated dungeon with rooms and corridors."""
    
    def __init__(self, width: int = 80, height: int = 80):
        self.width = width
        self.height = height
        self.tiles = [[TileType.VOID for _ in range(width)] for _ in range(height)]
        self.rooms: List[Room] = []
        self.spawn_points: List[Tuple[int, int]] = []
        self.decorations: List[Decoration] = []  # Void space decorations
        self.room_props: List[RoomProp] = []     # Barrels, urns, chests
        self.floor_decor: List[FloorDecor] = []  # Floor patterns
        self.stairs_down: Optional[Tuple[int, int]] = None
        self.stairs_up: Optional[Tuple[int, int]] = None
        self.seed: Optional[int] = None
    
    def generate(
        self,
        min_rooms: int = 8,
        max_rooms: int = 15,
        min_room_size: int = 5,
        max_room_size: int = 12,
        seed: Optional[int] = None
    ):
        """Generate a new dungeon layout.
        
        Args:
            seed: Optional random seed for reproducible generation
        """
        # Set seed for reproducibility
        if seed is None:
            seed = random.randint(0, 2**31 - 1)
        self.seed = seed
        random.seed(seed)
        
        self.rooms.clear()
        self.spawn_points.clear()
        
        # Fill with void
        self.tiles = [[TileType.VOID for _ in range(self.width)] 
                      for _ in range(self.height)]
        
        target_rooms = random.randint(min_rooms, max_rooms)
        attempts = 0
        max_attempts = target_rooms * 50
        
        while len(self.rooms) < target_rooms and attempts < max_attempts:
            attempts += 1
            
            # Random room dimensions
            w = random.randint(min_room_size, max_room_size)
            h = random.randint(min_room_size, max_room_size)
            x = random.randint(1, self.width - w - 2)
            y = random.randint(1, self.height - h - 2)
            
            new_room = Room(x, y, w, h)
            
            # Check for overlap
            overlaps = False
            for room in self.rooms:
                if new_room.intersects(room, margin=2):
                    overlaps = True
                    break
            
            if not overlaps:
                self._carve_room(new_room)
                
                # Connect to previous room
                if self.rooms:
                    self._connect_rooms(self.rooms[-1], new_room)
                
                self.rooms.append(new_room)
        
        # Place stairs
        if len(self.rooms) >= 2:
            start_room = self.rooms[0]
            end_room = self.rooms[-1]
            
            self.stairs_up = start_room.center
            self.stairs_down = end_room.center
            
            self.tiles[self.stairs_up[1]][self.stairs_up[0]] = TileType.STAIRS_UP
            self.tiles[self.stairs_down[1]][self.stairs_down[0]] = TileType.STAIRS_DOWN
        
        # Generate spawn points (for enemies)
        self._generate_spawn_points()
        
        # Generate room decorations (barrels, urns, floor patterns)
        self._generate_room_props()
        self._generate_floor_decor()
        
        # Generate void decorations (palm trees, rocks, etc.)
        self._generate_decorations()
    
    def _carve_room(self, room: Room):
        """Carve out a room."""
        for y in range(room.y, room.y + room.height):
            for x in range(room.x, room.x + room.width):
                if 0 <= x < self.width and 0 <= y < self.height:
                    self.tiles[y][x] = TileType.FLOOR
    
    def _connect_rooms(self, room1: Room, room2: Room):
        """Connect two rooms with a corridor."""
        x1, y1 = room1.center
        x2, y2 = room2.center
        
        # Randomly decide to go horizontal or vertical first
        if random.random() < 0.5:
            self._carve_h_tunnel(x1, x2, y1)
            self._carve_v_tunnel(y1, y2, x2)
        else:
            self._carve_v_tunnel(y1, y2, x1)
            self._carve_h_tunnel(x1, x2, y2)
    
    def _carve_h_tunnel(self, x1: int, x2: int, y: int):
        """Carve horizontal tunnel."""
        for x in range(min(x1, x2), max(x1, x2) + 1):
            if 0 <= x < self.width and 0 <= y < self.height:
                self.tiles[y][x] = TileType.FLOOR
    
    def _carve_v_tunnel(self, y1: int, y2: int, x: int):
        """Carve vertical tunnel."""
        for y in range(min(y1, y2), max(y1, y2) + 1):
            if 0 <= x < self.width and 0 <= y < self.height:
                self.tiles[y][x] = TileType.FLOOR
    
    def _generate_spawn_points(self):
        """Generate enemy spawn points in rooms."""
        self.spawn_points.clear()
        
        # Skip first room (player spawn)
        for room in self.rooms[1:]:
            # Place spawn points inside rooms (1-2 per room for early game balance)
            inner = room.inner
            num_spawns = random.randint(1, 2)
            
            for _ in range(num_spawns):
                x = random.randint(inner[0], inner[0] + inner[2])
                y = random.randint(inner[1], inner[1] + inner[3])
                
                if self.is_walkable(x, y):
                    self.spawn_points.append((x, y))
    
    def _generate_room_props(self):
        """Generate barrels, urns, chests, crates inside rooms."""
        self.room_props.clear()
        
        prop_types = ['barrel', 'urn', 'crate', 'pot', 'chest']
        prop_weights = [30, 25, 20, 20, 5]  # Chests are rare
        
        for room in self.rooms:
            inner = room.inner
            room_area = inner[2] * inner[3]
            
            # Bigger rooms get more props
            if room_area < 20:
                num_props = random.randint(0, 2)
            elif room_area < 40:
                num_props = random.randint(1, 4)
            else:
                num_props = random.randint(2, 6)
            
            # Track used positions to avoid overlap
            used_positions: Set[Tuple[int, int]] = set()
            
            for _ in range(num_props):
                # Try to place against walls or in corners (more natural)
                attempts = 0
                while attempts < 10:
                    # Prefer edges (70%) vs random interior (30%)
                    if random.random() < 0.7:
                        # Edge placement
                        edge = random.choice(['top', 'bottom', 'left', 'right'])
                        if edge == 'top':
                            x = random.randint(inner[0], inner[0] + inner[2])
                            y = inner[1]
                        elif edge == 'bottom':
                            x = random.randint(inner[0], inner[0] + inner[2])
                            y = inner[1] + inner[3]
                        elif edge == 'left':
                            x = inner[0]
                            y = random.randint(inner[1], inner[1] + inner[3])
                        else:
                            x = inner[0] + inner[2]
                            y = random.randint(inner[1], inner[1] + inner[3])
                    else:
                        x = random.randint(inner[0], inner[0] + inner[2])
                        y = random.randint(inner[1], inner[1] + inner[3])
                    
                    # Check not blocking important tiles
                    tile = self.get_tile(x, y)
                    if tile not in (TileType.FLOOR,):
                        attempts += 1
                        continue
                    
                    # Check not too close to stairs or spawn
                    too_close = False
                    if self.stairs_up and abs(x - self.stairs_up[0]) < 2 and abs(y - self.stairs_up[1]) < 2:
                        too_close = True
                    if self.stairs_down and abs(x - self.stairs_down[0]) < 2 and abs(y - self.stairs_down[1]) < 2:
                        too_close = True
                    for sx, sy in self.spawn_points:
                        if abs(x - sx) < 2 and abs(y - sy) < 2:
                            too_close = True
                            break
                    
                    if too_close or (x, y) in used_positions:
                        attempts += 1
                        continue
                    
                    # Check spacing from other props
                    prop_close = any(
                        abs(p.x - x) < 1.5 and abs(p.y - y) < 1.5
                        for p in self.room_props
                    )
                    if prop_close:
                        attempts += 1
                        continue
                    
                    # Place the prop
                    prop_type = random.choices(prop_types, weights=prop_weights)[0]
                    has_loot = random.random() < 0.1  # 10% chance of loot
                    
                    # Small position offset for natural feel
                    px = x + random.uniform(-0.2, 0.2)
                    py = y + random.uniform(-0.2, 0.2)
                    
                    self.room_props.append(RoomProp(
                        x=px, y=py,
                        type=prop_type,
                        variant=random.randint(0, 2),
                        breakable=(prop_type != 'chest'),
                        has_loot=has_loot
                    ))
                    used_positions.add((x, y))
                    break
                    
                    attempts += 1
    
    def _generate_floor_decor(self):
        """Generate decorative floor patterns in larger rooms."""
        self.floor_decor.clear()
        
        for room in self.rooms:
            inner = room.inner
            room_area = inner[2] * inner[3]
            
            # Small rooms get simple accents, bigger rooms get full decor
            if room_area < 16:
                # 40% chance of just a few accent tiles
                if random.random() < 0.4:
                    num = random.randint(1, 2)
                    for _ in range(num):
                        ax = random.randint(inner[0] + 1, inner[0] + inner[2] - 1)
                        ay = random.randint(inner[1] + 1, inner[1] + inner[3] - 1)
                        self.floor_decor.append(FloorDecor(ax, ay, 'accent', 1, 1, random.randint(0, 4)))
                continue
            
            # 80% chance of floor decoration for medium/large rooms
            if random.random() > 0.8:
                continue
            
            decor_type = random.choice(['rug', 'mosaic', 'pattern', 'tiles'])
            cx, cy = room.center
            
            if decor_type == 'rug':
                # Central rug
                rug_w = min(inner[2] - 2, random.randint(3, 5))
                rug_h = min(inner[3] - 2, random.randint(2, 4))
                self.floor_decor.append(FloorDecor(
                    x=cx - rug_w // 2,
                    y=cy - rug_h // 2,
                    type='rug',
                    width=rug_w,
                    height=rug_h,
                    variant=random.randint(0, 3)
                ))
            
            elif decor_type == 'mosaic':
                # Center mosaic pattern
                size = min(inner[2] - 2, inner[3] - 2, random.randint(2, 4))
                self.floor_decor.append(FloorDecor(
                    x=cx - size // 2,
                    y=cy - size // 2,
                    type='mosaic',
                    width=size,
                    height=size,
                    variant=random.randint(0, 2)
                ))
            
            elif decor_type == 'pattern':
                # Scattered tile accents
                num_accents = random.randint(2, 5)
                for _ in range(num_accents):
                    ax = random.randint(inner[0] + 1, inner[0] + inner[2] - 1)
                    ay = random.randint(inner[1] + 1, inner[1] + inner[3] - 1)
                    self.floor_decor.append(FloorDecor(
                        x=ax, y=ay,
                        type='accent',
                        width=1, height=1,
                        variant=random.randint(0, 4)
                    ))
            
            else:  # tiles
                # Checkered or bordered tiles
                self.floor_decor.append(FloorDecor(
                    x=inner[0],
                    y=inner[1],
                    type='border',
                    width=inner[2],
                    height=inner[3],
                    variant=random.randint(0, 2)
                ))
            
            # Add some cracks/stains for wear (most rooms have some)
            if random.random() < 0.7:
                num_wear = random.randint(1, 4)
                for _ in range(num_wear):
                    wx = random.randint(inner[0], inner[0] + inner[2])
                    wy = random.randint(inner[1], inner[1] + inner[3])
                    self.floor_decor.append(FloorDecor(
                        x=wx, y=wy,
                        type=random.choice(['crack', 'stain']),
                        width=1, height=1,
                        variant=random.randint(0, 2)
                    ))
        
        # Add some accent tiles to corridors too
        for y in range(2, self.height - 2):
            for x in range(2, self.width - 2):
                if self.tiles[y][x] == TileType.FLOOR:
                    # Check if in a corridor (narrow passage)
                    in_room = any(
                        room.x <= x < room.x + room.width and
                        room.y <= y < room.y + room.height
                        for room in self.rooms
                    )
                    if not in_room and random.random() < 0.03:
                        self.floor_decor.append(FloorDecor(
                            x=x, y=y,
                            type='accent',
                            width=1, height=1,
                            variant=random.randint(0, 4)
                        ))
    
    def _generate_decorations(self):
        """Generate decorative elements in void spaces around the dungeon."""
        self.decorations.clear()
        
        # Categorize void tiles by distance from walkable areas
        near_tiles = []      # 2-4 tiles from floor (palms, ruins)
        mid_tiles = []       # 5-8 tiles from floor (rocks, water)
        far_tiles = []       # 9+ tiles (background rocks)
        
        for y in range(2, self.height - 2):
            for x in range(2, self.width - 2):
                if self.tiles[y][x] != TileType.VOID:
                    continue
                
                # Find minimum distance to walkable
                min_dist = 999
                for dy in range(-12, 13):
                    for dx in range(-12, 13):
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < self.width and 0 <= ny < self.height:
                            if self.tiles[ny][nx] in (TileType.FLOOR, TileType.DOOR,
                                                      TileType.STAIRS_UP, TileType.STAIRS_DOWN):
                                dist = abs(dx) + abs(dy)
                                min_dist = min(min_dist, dist)
                
                if 2 <= min_dist <= 4:
                    near_tiles.append((x, y))
                elif 5 <= min_dist <= 8:
                    mid_tiles.append((x, y))
                elif 9 <= min_dist <= 15:
                    far_tiles.append((x, y))
        
        # === PALM TREES (near walkable areas) ===
        random.shuffle(near_tiles)
        palm_count = 0
        max_palms = 12
        
        for x, y in near_tiles:
            if palm_count >= max_palms:
                break
            if random.random() > 0.04:
                continue
            
            # Check spacing
            too_close = any(
                dec.type == 'palm_tree' and abs(dec.x - x) < 6 and abs(dec.y - y) < 6
                for dec in self.decorations
            )
            if not too_close:
                self.decorations.append(Decoration(x, y, 'palm_tree', 
                                                   random.uniform(0.9, 1.15), 
                                                   random.randint(0, 2)))
                palm_count += 1
        
        # === TERRACOTTA RUINS (near walkable) ===
        ruin_count = 0
        max_ruins = 8
        
        for x, y in near_tiles:
            if ruin_count >= max_ruins:
                break
            if random.random() > 0.03:
                continue
            
            too_close = any(
                abs(dec.x - x) < 4 and abs(dec.y - y) < 4
                for dec in self.decorations
            )
            if not too_close:
                self.decorations.append(Decoration(x, y, 'ruin',
                                                   random.uniform(0.8, 1.2),
                                                   random.randint(0, 3)))
                ruin_count += 1
        
        # === WATER POOLS / OASES (mid distance) ===
        water_count = 0
        max_water = 4
        
        random.shuffle(mid_tiles)
        for x, y in mid_tiles:
            if water_count >= max_water:
                break
            if random.random() > 0.02:
                continue
            
            too_close = any(
                abs(dec.x - x) < 8 and abs(dec.y - y) < 8
                for dec in self.decorations if dec.type == 'water'
            )
            if not too_close:
                self.decorations.append(Decoration(x, y, 'water',
                                                   random.uniform(1.0, 2.0),
                                                   random.randint(0, 2)))
                water_count += 1
        
        # === ROCKS (mid and far) ===
        rock_tiles = mid_tiles + far_tiles
        random.shuffle(rock_tiles)
        rock_count = 0
        max_rocks = 25
        
        for x, y in rock_tiles:
            if rock_count >= max_rocks:
                break
            if random.random() > 0.02:
                continue
            
            too_close = any(
                dec.type == 'rock' and abs(dec.x - x) < 3 and abs(dec.y - y) < 3
                for dec in self.decorations
            )
            if not too_close:
                self.decorations.append(Decoration(x, y, 'rock',
                                                   random.uniform(0.5, 1.5),
                                                   random.randint(0, 4)))
                rock_count += 1
        
        # === SMALL PLANTS / GRASS TUFTS ===
        plant_count = 0
        max_plants = 30
        
        for x, y in near_tiles + mid_tiles:
            if plant_count >= max_plants:
                break
            if random.random() > 0.05:
                continue
            
            self.decorations.append(Decoration(x, y, 'plant',
                                               random.uniform(0.6, 1.0),
                                               random.randint(0, 2)))
            plant_count += 1
    
    def is_walkable(self, x: int, y: int) -> bool:
        """Check if a tile is walkable."""
        if not (0 <= x < self.width and 0 <= y < self.height):
            return False
        
        tile = self.tiles[y][x]
        return tile in (TileType.FLOOR, TileType.DOOR, 
                       TileType.STAIRS_DOWN, TileType.STAIRS_UP)
    
    def get_tile(self, x: int, y: int) -> TileType:
        """Get tile type at position."""
        if not (0 <= x < self.width and 0 <= y < self.height):
            return TileType.VOID
        return self.tiles[y][x]
    
    def get_player_spawn(self) -> Tuple[float, float]:
        """Get the player spawn position (center of first room)."""
        if self.rooms:
            center = self.rooms[0].center
            return (float(center[0]), float(center[1]))
        return (self.width / 2, self.height / 2)
    
    def get_random_floor_pos(self) -> Optional[Tuple[float, float]]:
        """Get a random walkable position."""
        attempts = 0
        while attempts < 100:
            x = random.randint(0, self.width - 1)
            y = random.randint(0, self.height - 1)
            if self.is_walkable(x, y):
                return (float(x) + 0.5, float(y) + 0.5)
            attempts += 1
        return None
    
    def has_line_of_sight(self, x1: float, y1: float, x2: float, y2: float) -> bool:
        """Check if there's a clear line of sight between two points.
        
        Uses DDA (Digital Differential Analyzer) algorithm to check
        EVERY single tile the line passes through. This is bulletproof.
        """
        # Convert to tile coordinates
        ix1, iy1 = int(x1), int(y1)
        ix2, iy2 = int(x2), int(y2)
        
        # Same tile = always visible
        if ix1 == ix2 and iy1 == iy2:
            return True
        
        # Use DDA algorithm - guaranteed to hit every tile
        dx = abs(ix2 - ix1)
        dy = abs(iy2 - iy1)
        
        x = ix1
        y = iy1
        
        # Direction of step
        x_inc = 1 if ix2 > ix1 else -1
        y_inc = 1 if iy2 > iy1 else -1
        
        # Previous position for diagonal check
        prev_x, prev_y = x, y
        
        if dx >= dy:
            # X-dominant line (or equal)
            error = dx / 2
            while x != ix2:
                prev_x, prev_y = x, y
                x += x_inc
                error -= dy
                if error < 0:
                    y += y_inc
                    error += dx
                    # Diagonal move - check corner cutting
                    # Must be able to pass through BOTH adjacent tiles
                    if not self.is_walkable(x, prev_y) or not self.is_walkable(prev_x, y):
                        return False
                
                # Check current tile (skip destination - target stands there)
                if x != ix2 or y != iy2:
                    if not self.is_walkable(x, y):
                        return False
            # After X loop, check if Y still needs to reach destination
            while y != iy2:
                prev_x, prev_y = x, y
                y += y_inc
                if x != ix2 or y != iy2:
                    if not self.is_walkable(x, y):
                        return False
        else:
            # Y-dominant line
            error = dy / 2
            while y != iy2:
                prev_x, prev_y = x, y
                y += y_inc
                error -= dx
                if error < 0:
                    x += x_inc
                    error += dy
                    # Diagonal move - check corner cutting
                    if not self.is_walkable(x, prev_y) or not self.is_walkable(prev_x, y):
                        return False
                
                # Check current tile (skip destination - target stands there)
                if x != ix2 or y != iy2:
                    if not self.is_walkable(x, y):
                        return False
            # After Y loop, check if X still needs to reach destination
            while x != ix2:
                prev_x, prev_y = x, y
                x += x_inc
                if x != ix2 or y != iy2:
                    if not self.is_walkable(x, y):
                        return False
        
        return True
    
    def is_in_bounds(self, x: int, y: int) -> bool:
        """Check if position is within dungeon bounds."""
        return 0 <= x < self.width and 0 <= y < self.height
    
    def clamp_position(self, x: float, y: float) -> Tuple[float, float]:
        """Clamp a position to valid walkable area.
        
        Tries to find the nearest walkable tile if the position is not walkable.
        """
        # First check if it's already walkable
        if self.is_walkable(int(x), int(y)):
            return x, y
        
        # Otherwise, find nearest walkable tile
        best_x, best_y = x, y
        best_dist = float('inf')
        
        # Search in expanding radius for a walkable tile
        for radius in range(1, 10):
            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):
                    check_x = int(x) + dx
                    check_y = int(y) + dy
                    if self.is_walkable(check_x, check_y):
                        dist = (dx * dx + dy * dy) ** 0.5
                        if dist < best_dist:
                            best_dist = dist
                            best_x = check_x + 0.5
                            best_y = check_y + 0.5
            if best_dist < float('inf'):
                break
        
        return best_x, best_y

