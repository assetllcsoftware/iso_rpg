"""World management and pathfinding."""

import heapq
import numpy as np
from .dungeon import DungeonGenerator
from ..engine.constants import TILE_FLOOR, TILE_DOOR, TILE_STAIRS_DOWN, TILE_STAIRS_UP
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
        
        # Stairs positions
        self.stairs_down_pos = None
        self.stairs_up_pos = None
        self.stairs_pos = None  # Legacy, points to stairs_down
        
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
        self.stairs_down_pos = self.dungeon_gen.place_stairs()
        self.stairs_pos = self.stairs_down_pos  # Legacy compatibility
        
        # Place stairs up on level 2+ (to go back to previous level)
        if level > 1:
            spawn = self.dungeon_gen.get_spawn_points(1)
            if spawn:
                self.stairs_up_pos = self.dungeon_gen.place_stairs_up(spawn[0][0], spawn[0][1])
        else:
            self.stairs_up_pos = None
        
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
        return tile in (TILE_FLOOR, TILE_DOOR, TILE_STAIRS_DOWN, TILE_STAIRS_UP)
    
    def is_on_stairs(self, entity):
        """Check if an entity is standing on stairs down."""
        if not self.stairs_down_pos:
            return False
        entity_tile_x = int(entity.x)
        entity_tile_y = int(entity.y)
        stairs_x, stairs_y = self.stairs_down_pos
        dist = abs(entity_tile_x - stairs_x) + abs(entity_tile_y - stairs_y)
        return dist <= 1
    
    def is_on_stairs_up(self, entity):
        """Check if an entity is standing on stairs up."""
        if not self.stairs_up_pos:
            return False
        entity_tile_x = int(entity.x)
        entity_tile_y = int(entity.y)
        stairs_x, stairs_y = self.stairs_up_pos
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
    
    def get_entity_at(self, x, y, radius=0.5, enemies_only=False):
        """Get entity at a world position. Check enemies first for combat targeting."""
        # Check enemies first - most common use is targeting enemies
        for enemy in self.enemies:
            if enemy.health > 0 and enemy.distance_to((x, y)) <= radius:
                return enemy
        
        # Only check allies if not enemies_only
        if not enemies_only:
            for char in self.characters:
                if char.distance_to((x, y)) <= radius:
                    return char
        
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
            enemy._world_ref = self  # Give enemies access to world for collision
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
        
        # Auto-revive downed allies when out of combat
        self._check_auto_revive()
        
        # Apply entity separation (prevent stacking/blocking)
        all_entities = self.characters + self.enemies
        for entity in all_entities:
            if hasattr(entity, 'health') and entity.health <= 0:
                continue
            if getattr(entity, 'is_downed', False):
                continue  # Don't push downed characters
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
            new_x = entity.x + push_x * dt
            new_y = entity.y + push_y * dt
            # Only apply if new position is walkable
            if self.is_walkable(int(new_x), int(new_y)):
                entity.x = new_x
                entity.y = new_y
    
    def _check_auto_revive(self):
        """Auto-revive downed allies when no enemies are nearby."""
        # Find downed characters
        downed = [c for c in self.characters if getattr(c, 'is_downed', False)]
        if not downed:
            return
        
        # Find alive characters
        alive = [c for c in self.characters if not getattr(c, 'is_downed', False) and c.health > 0]
        if not alive:
            return
        
        # Check if any enemy is within aggro range of any alive character
        aggro_range = 6.0
        enemies_nearby = False
        for char in alive:
            for enemy in self.enemies:
                if enemy.health <= 0:
                    continue
                dist = ((char.x - enemy.x) ** 2 + (char.y - enemy.y) ** 2) ** 0.5
                if dist < aggro_range:
                    enemies_nearby = True
                    break
            if enemies_nearby:
                break
        
        # If no enemies nearby, revive downed allies
        if not enemies_nearby:
            for downed_char in downed:
                # Check if an alive character is close enough to revive
                for helper in alive:
                    dist = ((helper.x - downed_char.x) ** 2 + (helper.y - downed_char.y) ** 2) ** 0.5
                    if dist < 3.0:
                        downed_char.revive(50)  # Revive at 50% health
                        break

