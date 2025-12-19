"""World management and pathfinding."""

import heapq
import numpy as np
from .dungeon import DungeonGenerator
from ..engine.constants import TILE_FLOOR, TILE_DOOR, TILE_STAIRS_DOWN
from ..entities.enemy import Enemy


class World:
    """Manages the game world, entities, and pathfinding."""
    
    def __init__(self, width=50, height=50):
        self.width = width
        self.height = height
        self.tiles = None
        self.dungeon_gen = None
        
        # Entities
        self.characters = []
        self.enemies = []
        self.items_on_ground = []
        
        # Current level
        self.level = 1
        
        # Stairs position
        self.stairs_pos = None
        
        # Combat events for visual effects
        self.combat_events = []
    
    def generate_dungeon(self, level=1, seed=None):
        """Generate a new dungeon level."""
        self.level = level
        
        # Generate a seed if not provided, so we can save/reload consistently
        if seed is None:
            import random
            seed = random.randint(0, 2**31 - 1)
        self.dungeon_seed = seed
        
        self.dungeon_gen = DungeonGenerator(self.width, self.height, seed)
        
        # More rooms for higher levels
        num_rooms = 8 + level
        self.tiles = self.dungeon_gen.generate(num_rooms=num_rooms)
        
        # Place stairs to next level
        self.stairs_pos = self.dungeon_gen.place_stairs()
        
        # Spawn enemies
        self.enemies = []
        enemy_spawns = self.dungeon_gen.get_enemy_spawn_points(5 + level * 2)
        
        enemy_types = ['goblin', 'skeleton', 'spider']
        if level >= 3:
            enemy_types.append('orc')
        if level >= 5:
            enemy_types.append('dark_mage')
        if level >= 7:
            enemy_types.append('troll')
        
        for x, y in enemy_spawns:
            enemy_type = np.random.choice(enemy_types)
            enemy_level = max(1, level + np.random.randint(-1, 2))
            enemy = Enemy(enemy_type, x, y, enemy_level)
            
            # Set patrol points within room
            room = self._find_room_at(x, y)
            if room:
                enemy.patrol_points = [
                    (room.x + 1, room.y + 1),
                    (room.x2 - 2, room.y + 1),
                    (room.x2 - 2, room.y2 - 2),
                    (room.x + 1, room.y2 - 2),
                ]
            
            self.enemies.append(enemy)
        
        return self.dungeon_gen.get_spawn_points(1)
    
    def _find_room_at(self, x, y):
        """Find the room containing a point."""
        if not self.dungeon_gen:
            return None
        for room in self.dungeon_gen.rooms:
            if room.x <= x < room.x2 and room.y <= y < room.y2:
                return room
        return None
    
    def is_walkable(self, x, y):
        """Check if a tile is walkable."""
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            return False
        tile = self.tiles[int(y), int(x)]
        return tile in (TILE_FLOOR, TILE_DOOR, TILE_STAIRS_DOWN)
    
    def is_on_stairs(self, entity):
        """Check if an entity is standing on stairs."""
        if not self.stairs_pos:
            return False
        # Use tile position for more reliable detection
        entity_tile_x = int(entity.x)
        entity_tile_y = int(entity.y)
        stairs_x, stairs_y = self.stairs_pos
        
        # Check if on same tile or adjacent
        dist = abs(entity_tile_x - stairs_x) + abs(entity_tile_y - stairs_y)
        return dist <= 1
    
    def find_path(self, start, end):
        """A* pathfinding from start to end."""
        start = (int(start[0]), int(start[1]))
        end = (int(end[0]), int(end[1]))
        
        if not self.is_walkable(end[0], end[1]):
            # Find nearest walkable tile
            end = self._find_nearest_walkable(end)
            if not end:
                return []
        
        # A* algorithm
        open_set = []
        heapq.heappush(open_set, (0, start))
        
        came_from = {}
        g_score = {start: 0}
        f_score = {start: self._heuristic(start, end)}
        
        while open_set:
            current = heapq.heappop(open_set)[1]
            
            if current == end:
                return self._reconstruct_path(came_from, current)
            
            for neighbor in self._get_neighbors(current):
                tentative_g = g_score[current] + self._move_cost(current, neighbor)
                
                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score[neighbor] = tentative_g + self._heuristic(neighbor, end)
                    
                    if neighbor not in [item[1] for item in open_set]:
                        heapq.heappush(open_set, (f_score[neighbor], neighbor))
        
        return []
    
    def _heuristic(self, a, b):
        """Manhattan distance heuristic."""
        return abs(a[0] - b[0]) + abs(a[1] - b[1])
    
    def _move_cost(self, a, b):
        """Cost to move between adjacent tiles."""
        # Diagonal movement costs more
        if a[0] != b[0] and a[1] != b[1]:
            return 1.414
        return 1.0
    
    def _get_neighbors(self, pos):
        """Get walkable neighboring tiles."""
        neighbors = []
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1),
                       (-1, -1), (-1, 1), (1, -1), (1, 1)]:
            nx, ny = pos[0] + dx, pos[1] + dy
            if self.is_walkable(nx, ny):
                # For diagonal movement, ensure we can actually go diagonally
                if dx != 0 and dy != 0:
                    if not self.is_walkable(pos[0] + dx, pos[1]):
                        continue
                    if not self.is_walkable(pos[0], pos[1] + dy):
                        continue
                neighbors.append((nx, ny))
        return neighbors
    
    def _reconstruct_path(self, came_from, current):
        """Reconstruct path from A* result."""
        path = [current]
        while current in came_from:
            current = came_from[current]
            path.append(current)
        path.reverse()
        
        # Convert to float centers
        return [(p[0] + 0.5, p[1] + 0.5) for p in path]
    
    def _find_nearest_walkable(self, pos):
        """Find the nearest walkable tile to a position."""
        x, y = int(pos[0]), int(pos[1])
        
        for radius in range(1, 10):
            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):
                    if abs(dx) == radius or abs(dy) == radius:
                        nx, ny = x + dx, y + dy
                        if self.is_walkable(nx, ny):
                            return (nx, ny)
        return None
    
    def get_entity_at(self, x, y, radius=0.5):
        """Get entity at a world position."""
        for char in self.characters:
            if char.distance_to((x, y)) <= radius:
                return char
        
        for enemy in self.enemies:
            if enemy.health > 0 and enemy.distance_to((x, y)) <= radius:
                return enemy
        
        return None
    
    def get_enemies_in_range(self, x, y, radius):
        """Get all enemies within a radius."""
        return [e for e in self.enemies 
                if e.health > 0 and e.distance_to((x, y)) <= radius]
    
    def update(self, dt):
        """Update all entities in the world."""
        # Clear combat events
        self.combat_events = []
        
        # Update enemies
        alive_enemies = []
        for enemy in self.enemies:
            if enemy.health > 0:
                enemy.update(dt, self.characters, self.combat_events)
                alive_enemies.append(enemy)
            else:
                # Drop loot
                loot = enemy.drop_loot()
                if loot['items']:
                    for item in loot['items']:
                        self.items_on_ground.append({
                            'item': item,
                            'x': enemy.x,
                            'y': enemy.y
                        })
                        print(f"[DEBUG] Dropped: {item.name} at ({enemy.x:.1f}, {enemy.y:.1f})")
                # Give XP to characters in combat
                for char in self.characters:
                    if char.in_combat:
                        char.experience += enemy.xp_value
        
        self.enemies = alive_enemies
        
        # Update characters
        for char in self.characters:
            char._world_ref = self  # Give characters access to world for AI
            char.update(dt)
        
        # Apply entity separation (prevent stacking/blocking)
        all_entities = self.characters + self.enemies
        for entity in all_entities:
            if hasattr(entity, 'health') and entity.health <= 0:
                continue
            entity.apply_separation(all_entities, dt)
            
            # Also push away from walls
            self._push_from_walls(entity, dt)
    
    def _push_from_walls(self, entity, dt):
        """Push entity away from nearby walls."""
        check_radius = entity.radius + 0.3
        
        push_x = 0.0
        push_y = 0.0
        
        # Check tiles around entity
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                
                tile_x = int(entity.x + dx * check_radius)
                tile_y = int(entity.y + dy * check_radius)
                
                if not self.is_walkable(tile_x, tile_y):
                    # Calculate push away from this wall tile
                    wall_center_x = tile_x + 0.5
                    wall_center_y = tile_y + 0.5
                    
                    dist_x = entity.x - wall_center_x
                    dist_y = entity.y - wall_center_y
                    dist = (dist_x ** 2 + dist_y ** 2) ** 0.5
                    
                    if dist < check_radius and dist > 0.01:
                        push_strength = (check_radius - dist) * 3.0
                        push_x += (dist_x / dist) * push_strength
                        push_y += (dist_y / dist) * push_strength
        
        if abs(push_x) > 0.01 or abs(push_y) > 0.01:
            entity.x += push_x * dt
            entity.y += push_y * dt

