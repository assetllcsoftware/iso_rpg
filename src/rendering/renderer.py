"""Main renderer - draws everything to screen."""

import os
import json
import pygame
import esper
import math
from typing import List, Tuple, Optional

from .camera import Camera
from .sprites import SpriteManager
from .pixel_sprites import HERO_SIZE, CHAR_SIZE
from ..core.constants import (
    TILE_WIDTH, TILE_HEIGHT, WALL_HEIGHT, TileType,
    COLOR_BG, COLOR_HEALTH, COLOR_MANA, COLOR_TEXT,
    SCREEN_WIDTH, SCREEN_HEIGHT
)
from ..ecs.components import (
    Position, Sprite, Animation, AnimationState, Facing, Direction,
    Health, Mana, HealthBar, DamageNumber, RenderOffset,
    PartyMember, Enemy, Selected, Projectile, AreaEffect,
    DroppedItem, GoldDrop, Dead, Downed
)
from ..ecs.components.rendering import VisualEffect
from ..core.constants import RARITY_COLORS
from ..world.dungeon import Dungeon


class Renderer:
    """Main rendering system."""
    
    # Tile colors - Indian Temple / Desert Theme
    TILE_COLORS = {
        TileType.VOID: (20, 15, 10),           # Dark desert night
        TileType.FLOOR: (210, 180, 140),       # Sandstone floor
        TileType.WALL: (180, 100, 70),         # Terracotta walls
        TileType.DOOR: (139, 90, 43),          # Wooden doors with gold
        TileType.STAIRS_DOWN: (200, 160, 80),  # Golden temple stairs
        TileType.STAIRS_UP: (160, 180, 200),   # Bluish stairs (to sky)
        TileType.WATER: (60, 140, 140),        # Teal temple pool
        TileType.PIT: (40, 30, 20),            # Dark pit
    }
    
    def __init__(self, screen: pygame.Surface, camera: Camera):
        self.screen = screen
        self.camera = camera
        self.sprites = SpriteManager()
        self.sprites.load_all()
        
        # Pre-render tile surfaces
        self._tile_surfaces = {}
        self._generate_tile_surfaces()
        
        # Pre-render decoration surfaces (for performance)
        self._palm_cache = {}
        self._rock_cache = {}
        self._ruin_cache = {}
        self._water_cache = {}
        self._plant_cache = {}
        # Room prop caches
        self._barrel_cache = {}
        self._urn_cache = {}
        self._chest_cache = {}
        self._crate_cache = {}
        self._pot_cache = {}
        # External sprite caches
        self._external_palms = []
        self._external_rocks = []
        self._external_ruins = []
        self._external_water = []
        self._external_plants = []
        self._external_walls = []
        # Specific wall sprites for room borders (transformed to fit isometric grid)
        self._wall1 = None  # Top-right walls (transformed)
        self._wall3 = None  # Top-left walls (transformed)
        # Room props
        self._external_barrels = []
        self._external_crates = []
        self._external_chests = []
        self._external_urns = []
        # Floor
        self._external_rugs = []
        self._load_external_decorations()
        self._generate_decoration_surfaces()
        
        # Font
        pygame.font.init()
        self.font_small = pygame.font.Font(None, 20)
        self.font_medium = pygame.font.Font(None, 28)
        self.font_large = pygame.font.Font(None, 36)
        self.font_damage = pygame.font.Font(None, 48)  # Big damage numbers
    
    def _generate_tile_surfaces(self):
        """Pre-render isometric tile surfaces."""
        for tile_type, color in self.TILE_COLORS.items():
            # Floor tile (diamond)
            floor_surf = pygame.Surface((TILE_WIDTH, TILE_HEIGHT), pygame.SRCALPHA)
            points = [
                (TILE_WIDTH // 2, 0),
                (TILE_WIDTH, TILE_HEIGHT // 2),
                (TILE_WIDTH // 2, TILE_HEIGHT),
                (0, TILE_HEIGHT // 2),
            ]
            pygame.draw.polygon(floor_surf, color, points)
            pygame.draw.polygon(floor_surf, tuple(min(255, c + 20) for c in color), points, 1)
            
            self._tile_surfaces[tile_type] = floor_surf
            
            # Wall tile (with height)
            if tile_type == TileType.WALL:
                wall_surf = pygame.Surface((TILE_WIDTH, TILE_HEIGHT + WALL_HEIGHT), pygame.SRCALPHA)
                
                # Top face
                top_color = tuple(min(255, c + 30) for c in color)
                top_points = [
                    (TILE_WIDTH // 2, 0),
                    (TILE_WIDTH, TILE_HEIGHT // 2),
                    (TILE_WIDTH // 2, TILE_HEIGHT),
                    (0, TILE_HEIGHT // 2),
                ]
                pygame.draw.polygon(wall_surf, top_color, top_points)
                
                # Left face
                left_color = tuple(max(0, c - 20) for c in color)
                left_points = [
                    (0, TILE_HEIGHT // 2),
                    (TILE_WIDTH // 2, TILE_HEIGHT),
                    (TILE_WIDTH // 2, TILE_HEIGHT + WALL_HEIGHT),
                    (0, TILE_HEIGHT // 2 + WALL_HEIGHT),
                ]
                pygame.draw.polygon(wall_surf, left_color, left_points)
                
                # Right face
                right_color = color
                right_points = [
                    (TILE_WIDTH, TILE_HEIGHT // 2),
                    (TILE_WIDTH // 2, TILE_HEIGHT),
                    (TILE_WIDTH // 2, TILE_HEIGHT + WALL_HEIGHT),
                    (TILE_WIDTH, TILE_HEIGHT // 2 + WALL_HEIGHT),
                ]
                pygame.draw.polygon(wall_surf, right_color, right_points)
                
                self._tile_surfaces[(tile_type, 'wall')] = wall_surf
    
    def render(self, dungeon: Optional[Dungeon]):
        """Render the entire game scene."""
        # Clear screen
        self.screen.fill(COLOR_BG)
        
        # Render dungeon tiles
        if dungeon:
            self._render_dungeon(dungeon)
            
            # Render floor decorations (rugs, patterns) - on top of tiles
            self._render_floor_decor(dungeon)
            
            # Render room top walls (wall1, wall3 sprites)
            self._render_room_walls(dungeon)
            
            # Render void decorations (palm trees, rocks) behind entities
            self._render_decorations(dungeon)
            
            # Render room props (barrels, urns) - these need Y-sorting with entities
            self._render_room_props(dungeon)
        
        # Render area effects (below entities)
        self._render_area_effects()
        
        # Render dropped items (below entities)
        self._render_dropped_items()
        
        # Collect and sort entities by Y position (painter's algorithm)
        entities = self._collect_renderable_entities()
        entities.sort(key=lambda e: e[1])  # Sort by y position
        
        # Render entities
        for ent_data in entities:
            self._render_entity(ent_data)
        
        # Render projectiles (above entities)
        self._render_projectiles()
        
        # Render visual effects
        self._render_visual_effects()
        
        # Render damage numbers (on top)
        self._render_damage_numbers()
    
    def _render_dungeon(self, dungeon: Dungeon):
        """Render dungeon tiles."""
        bounds = self.camera.get_visible_bounds()
        min_x = max(0, int(bounds[0]) - 2)
        min_y = max(0, int(bounds[1]) - 2)
        max_x = min(dungeon.width, int(bounds[2]) + 2)
        max_y = min(dungeon.height, int(bounds[3]) + 2)
        
        # Render actual tiles
        for y in range(min_y, max_y):
            for x in range(min_x, max_x):
                tile = dungeon.get_tile(x, y)
                
                if tile == TileType.VOID:
                    continue
                
                screen_x, screen_y = self.camera.world_to_screen(x, y)
                
                # Adjust for tile size
                screen_x -= int(TILE_WIDTH / 2 * self.camera.zoom)
                screen_y -= int(TILE_HEIGHT / 2 * self.camera.zoom)
                
                if tile == TileType.WALL:
                    # Use wall surface
                    surf = self._tile_surfaces.get((tile, 'wall'))
                    if surf:
                        scaled = pygame.transform.scale(
                            surf,
                            (int(TILE_WIDTH * self.camera.zoom),
                             int((TILE_HEIGHT + WALL_HEIGHT) * self.camera.zoom))
                        )
                        self.screen.blit(scaled, (screen_x, screen_y - int(WALL_HEIGHT * self.camera.zoom)))
                else:
                    surf = self._tile_surfaces.get(tile)
                    if surf:
                        scaled = pygame.transform.scale(
                            surf,
                            (int(TILE_WIDTH * self.camera.zoom),
                             int(TILE_HEIGHT * self.camera.zoom))
                        )
                        self.screen.blit(scaled, (screen_x, screen_y))
    
    def _render_room_walls(self, dungeon: Dungeon):
        """Render wall sprites along the isometric room edges, with gaps for corridors."""
        if not hasattr(self, '_wall1') or not hasattr(self, '_wall3'):
            return
        if self._wall1 is None or self._wall3 is None:
            return
        
        bounds = self.camera.get_visible_bounds()
        
        for room in dungeon.rooms:
            # Check if room is visible
            if not (bounds[0] - 5 <= room.x + room.width <= bounds[2] + 5 and
                    bounds[1] - 5 <= room.y + room.height <= bounds[3] + 5):
                continue
            
            # TOP-LEFT EDGE: runs along x = room.x (left side of room)
            # Wall3 goes on the left edge, aligned with isometric left-down diagonal
            for y in range(room.y, room.y + room.height):
                if not (bounds[1] - 2 <= y <= bounds[3] + 2):
                    continue
                
                x = room.x
                
                # Skip wall if there's a corridor entering/exiting here
                # Check: is the tile to the LEFT of this edge walkable? (corridor going out)
                has_corridor = False
                if x > 0 and dungeon.is_walkable(x - 1, y):
                    has_corridor = True
                
                if has_corridor:
                    continue
                
                # Get screen position at the LEFT edge of the tile (x - 0.5)
                screen_x, screen_y = self.camera.world_to_screen(x - 0.5, y + 0.5)
                
                surf = self._wall3
                scaled_w = int(surf.get_width() * self.camera.zoom * 0.5)
                scaled_h = int(surf.get_height() * self.camera.zoom * 0.5)
                
                if scaled_w < 5:
                    continue
                
                scaled = pygame.transform.smoothscale(surf, (scaled_w, scaled_h))
                
                draw_x = screen_x - scaled_w // 2
                draw_y = screen_y - scaled_h
                
                self.screen.blit(scaled, (draw_x, draw_y))
            
            # TOP-RIGHT EDGE: runs along y = room.y (top side of room)
            # Wall1 goes on the top edge, aligned with isometric right-down diagonal
            for x in range(room.x, room.x + room.width):
                if not (bounds[0] - 2 <= x <= bounds[2] + 2):
                    continue
                
                y = room.y
                
                # Skip wall if there's a corridor entering/exiting here
                # Check: is the tile ABOVE this edge walkable? (corridor going out)
                has_corridor = False
                if y > 0 and dungeon.is_walkable(x, y - 1):
                    has_corridor = True
                
                if has_corridor:
                    continue
                
                # Get screen position at the TOP edge of the tile (y - 0.5)
                screen_x, screen_y = self.camera.world_to_screen(x + 0.5, y - 0.5)
                
                surf = self._wall1
                scaled_w = int(surf.get_width() * self.camera.zoom * 0.5)
                scaled_h = int(surf.get_height() * self.camera.zoom * 0.5)
                
                if scaled_w < 5:
                    continue
                
                scaled = pygame.transform.smoothscale(surf, (scaled_w, scaled_h))
                
                draw_x = screen_x - scaled_w // 2
                draw_y = screen_y - scaled_h
                
                self.screen.blit(scaled, (draw_x, draw_y))
    
    def _generate_decoration_surfaces(self):
        """Pre-render all decoration surfaces for performance."""
        # Palm trees
        for variant in range(3):
            for size_idx, size in enumerate([0.9, 1.0, 1.1]):
                key = (variant, size_idx)
                self._palm_cache[key] = self._create_palm_surface(size, variant)
        
        # Rocks
        for variant in range(5):
            for size_idx, size in enumerate([0.6, 1.0, 1.4]):
                key = (variant, size_idx)
                self._rock_cache[key] = self._create_rock_surface(size, variant)
        
        # Terracotta ruins
        for variant in range(4):
            self._ruin_cache[variant] = self._create_ruin_surface(1.0, variant)
        
        # Water pools
        for variant in range(3):
            for size_idx, size in enumerate([1.0, 1.5, 2.0]):
                key = (variant, size_idx)
                self._water_cache[key] = self._create_water_surface(size, variant)
        
        # Small plants
        for variant in range(3):
            self._plant_cache[variant] = self._create_plant_surface(1.0, variant)
        
        # Room props
        for variant in range(3):
            self._barrel_cache[variant] = self._create_barrel_surface(variant)
            self._urn_cache[variant] = self._create_urn_surface(variant)
            self._crate_cache[variant] = self._create_crate_surface(variant)
            self._pot_cache[variant] = self._create_pot_surface(variant)
        for variant in range(2):
            self._chest_cache[variant] = self._create_chest_surface(variant)
    
    def _create_palm_surface(self, size: float, variant: int) -> pygame.Surface:
        """Create a pre-rendered palm tree surface."""
        # Canvas size
        width = int(300 * size)
        height = int(400 * size)
        
        surf = pygame.Surface((width, height), pygame.SRCALPHA)
        center_x = width // 2
        base_y = height - 20
        
        trunk_height = int(220 * size)
        trunk_width = int(35 * size)
        crown_y = base_y - trunk_height
        
        # === TRUNK with diamond/scale pattern (like reference) ===
        trunk_dark = (75, 50, 30)
        trunk_mid = (100, 70, 45)
        trunk_light = (130, 95, 60)
        
        # Draw trunk base shape
        num_rows = 18
        row_height = trunk_height // num_rows
        
        for row in range(num_rows):
            t = row / num_rows
            y_pos = base_y - int(trunk_height * t)
            
            # Trunk tapers
            row_width = trunk_width * (1 - t * 0.35)
            
            # Diamond scale pattern
            num_scales = 4 + int(t * 2)
            scale_width = row_width * 2 / num_scales
            
            for s in range(num_scales):
                offset = (scale_width / 2) if (row % 2 == 1) else 0
                sx = center_x - row_width + s * scale_width + offset
                
                # Diamond shape
                points = [
                    (sx + scale_width / 2, y_pos - row_height),
                    (sx + scale_width, y_pos - row_height / 2),
                    (sx + scale_width / 2, y_pos),
                    (sx, y_pos - row_height / 2),
                ]
                
                # Alternate colors for 3D effect
                if (row + s) % 2 == 0:
                    color = trunk_mid
                else:
                    color = trunk_dark
                
                pygame.draw.polygon(surf, color, [(int(p[0]), int(p[1])) for p in points])
                
                # Highlight edge
                pygame.draw.line(surf, trunk_light,
                               (int(points[0][0]), int(points[0][1])),
                               (int(points[1][0]), int(points[1][1])), 1)
        
        # === DEAD/BROWN FRONDS hanging down (like reference) ===
        dead_color = (160, 130, 80)
        dead_dark = (120, 95, 55)
        
        for i in range(4):
            angle = math.pi / 2 + (i - 1.5) * 0.4 + variant * 0.2
            length = int(80 * size)
            
            # Drooping dead frond
            pts = []
            for j in range(8):
                t = j / 7
                px = center_x + math.cos(angle) * length * t * 0.3
                py = crown_y + length * t  # Hangs straight down
                pts.append((int(px), int(py)))
            
            pygame.draw.lines(surf, dead_dark, False, pts, max(2, int(4 * size)))
            
            # Ragged edges
            for j in range(1, 7):
                if pts[j][1] < height:
                    for side in [-1, 1]:
                        ex = pts[j][0] + side * int(15 * size * (1 - j/8))
                        ey = pts[j][1] + int(8 * size)
                        pygame.draw.line(surf, dead_color, pts[j], (ex, ey), max(1, int(2 * size)))
        
        # === LUSH GREEN FRONDS ===
        frond_length = int(130 * size)
        num_fronds = 8 + variant
        
        # Colors like reference - rich greens with yellow-green highlights
        green_dark = (45, 100, 40)
        green_mid = (65, 140, 55)
        green_light = (95, 175, 70)
        green_tip = (120, 190, 85)
        
        # Sort by angle for proper layering
        frond_data = []
        for i in range(num_fronds):
            angle = (i / num_fronds) * 2 * math.pi - math.pi / 2 + variant * 0.3
            frond_data.append(angle)
        frond_data.sort(key=lambda a: math.sin(a))
        
        for angle in frond_data:
            # Determine color based on position
            if math.sin(angle) < -0.3:
                base_color = green_dark
                tip_color = green_mid
            elif math.sin(angle) > 0.3:
                base_color = green_light
                tip_color = green_tip
            else:
                base_color = green_mid
                tip_color = green_light
            
            # Elegant droop curve
            droop = 0.6
            
            # Draw frond with many leaflets (feathery look)
            stem_pts = []
            for j in range(12):
                t = j / 11
                # Curved drooping path
                px = center_x + math.cos(angle) * frond_length * t
                py = crown_y + math.sin(angle) * frond_length * 0.4 * t + frond_length * droop * t * t
                stem_pts.append((int(px), int(py)))
            
            # Main stem
            pygame.draw.lines(surf, base_color, False, stem_pts, max(2, int(4 * size)))
            
            # Feathery leaflets along stem
            for j in range(1, 11):
                t = j / 11
                if j >= len(stem_pts):
                    continue
                    
                sx, sy = stem_pts[j]
                leaflet_len = int(45 * size * (1 - t * 0.5))
                
                # Gradient color
                color = (
                    int(base_color[0] + (tip_color[0] - base_color[0]) * t),
                    int(base_color[1] + (tip_color[1] - base_color[1]) * t),
                    int(base_color[2] + (tip_color[2] - base_color[2]) * t),
                )
                
                # Leaflets on both sides
                for side in [-1, 1]:
                    leaf_angle = angle + side * (math.pi / 2.2)
                    
                    # Each leaflet has sub-leaflets for feathery effect
                    for sub in range(5):
                        sub_t = sub / 4
                        sub_angle = leaf_angle + side * sub_t * 0.3
                        sub_len = leaflet_len * (1 - sub_t * 0.3)
                        
                        lx = sx + math.cos(sub_angle) * sub_len
                        ly = sy + math.sin(sub_angle) * sub_len * 0.5 + sub_len * 0.2
                        
                        pygame.draw.line(surf, color, (sx, sy), (int(lx), int(ly)),
                                       max(1, int(2 * size * (1 - sub_t * 0.5))))
        
        # === COCONUTS ===
        if variant > 0:
            for i in range(2 + variant):
                angle = i * 0.8 - 0.8 + variant * 0.3
                cx = int(center_x + math.cos(angle) * 15 * size)
                cy = int(crown_y + 15 * size + math.sin(angle) * 8 * size)
                
                coconut_r = int(10 * size)
                pygame.draw.circle(surf, (60, 45, 25), (cx, cy), coconut_r)
                pygame.draw.circle(surf, (85, 65, 40), (cx - 2, cy - 2), coconut_r - 2)
                pygame.draw.circle(surf, (110, 85, 55), (cx - 3, cy - 3), coconut_r // 3)
        
        # === CROWN CENTER ===
        pygame.draw.circle(surf, (80, 60, 35), (center_x, int(crown_y + 5)), int(12 * size))
        
        return surf
    
    def _render_decorations(self, dungeon: Dungeon):
        """Render decorative elements."""
        bounds = self.camera.get_visible_bounds()
        
        # Sort decorations by y for proper layering
        visible_decs = []
        for dec in dungeon.decorations:
            if (bounds[0] - 6 <= dec.x <= bounds[2] + 6 and
                bounds[1] - 8 <= dec.y <= bounds[3] + 4):
                visible_decs.append(dec)
        
        # Render back-to-front (water first, then rocks, then plants/ruins, then palms)
        type_order = {'water': 0, 'rock': 1, 'plant': 2, 'ruin': 3, 'palm_tree': 4}
        visible_decs.sort(key=lambda d: (type_order.get(d.type, 2), d.y))
        
        for dec in visible_decs:
            if dec.type == 'palm_tree':
                self._draw_palm_tree(dec.x, dec.y, dec.size, dec.variant)
            elif dec.type == 'rock':
                self._draw_rock(dec.x, dec.y, dec.size, dec.variant)
            elif dec.type == 'ruin':
                self._draw_ruin(dec.x, dec.y, dec.size, dec.variant)
            elif dec.type == 'water':
                self._draw_water(dec.x, dec.y, dec.size, dec.variant)
            elif dec.type == 'plant':
                self._draw_plant(dec.x, dec.y, dec.size, dec.variant)
    
    def _detect_wall_angle(self, surf: pygame.Surface, threshold: int = 200) -> float:
        """
        Detect the dominant angle of a wall sprite by analyzing edge pixels.
        Returns angle in degrees from horizontal.
        """
        width, height = surf.get_size()
        
        # Collect edge pixels (non-transparent, non-white)
        edge_points = []
        
        for y in range(height):
            for x in range(width):
                color = surf.get_at((x, y))
                # Skip transparent and white pixels
                if color[3] < 128:  # Transparent
                    continue
                if color[0] >= threshold and color[1] >= threshold and color[2] >= threshold:
                    continue  # White
                
                # Check if this is an edge pixel (has transparent neighbor)
                is_edge = False
                for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < width and 0 <= ny < height:
                        nc = surf.get_at((nx, ny))
                        if nc[3] < 128:
                            is_edge = True
                            break
                    else:
                        is_edge = True
                        break
                
                if is_edge:
                    edge_points.append((x, y))
        
        if len(edge_points) < 10:
            return 0.0
        
        # Use simple linear regression to find dominant angle
        # Calculate covariance and variance
        n = len(edge_points)
        sum_x = sum(p[0] for p in edge_points)
        sum_y = sum(p[1] for p in edge_points)
        sum_xy = sum(p[0] * p[1] for p in edge_points)
        sum_xx = sum(p[0] * p[0] for p in edge_points)
        
        mean_x = sum_x / n
        mean_y = sum_y / n
        
        # Covariance and variance
        cov_xy = (sum_xy / n) - (mean_x * mean_y)
        var_x = (sum_xx / n) - (mean_x * mean_x)
        
        if abs(var_x) < 0.001:
            return 90.0  # Vertical line
        
        slope = cov_xy / var_x
        angle = math.degrees(math.atan(slope))
        
        return angle
    
    def _align_wall_to_isometric(self, surf: pygame.Surface, target_angle: float) -> pygame.Surface:
        """
        Transform a wall sprite to align with isometric grid edges.
        
        Args:
            surf: The wall sprite
            target_angle: Target angle in degrees (26.57 for right edge, -26.57 for left edge)
        
        Returns:
            Transformed surface
        """
        # Detect current angle of the wall in the sprite
        detected_angle = self._detect_wall_angle(surf)
        
        # Calculate rotation needed
        rotation = target_angle - detected_angle
        
        # Normalize rotation to reasonable range
        while rotation > 180:
            rotation -= 360
        while rotation < -180:
            rotation += 360
        
        print(f"Wall transform: detected={detected_angle:.1f}°, target={target_angle:.1f}°, rotation={rotation:.1f}°")
        
        # Apply rotation
        if abs(rotation) > 1:  # Only rotate if significant
            rotated = pygame.transform.rotate(surf, -rotation)  # Negative because pygame rotates counter-clockwise
            return rotated
        
        return surf
    
    def _load_external_decorations(self):
        """Load external decoration sprites from assets/sprites/"""
        # Go up from src/rendering/ to project root, then into assets/sprites
        sprites_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "assets", "sprites")
        mapping_file = os.path.join(sprites_dir, "sprite_mapping.json")
        
        if not os.path.exists(mapping_file):
            return
        
        try:
            with open(mapping_file) as f:
                mapping = json.load(f)
        except:
            return
        
        # Mapping from name keywords to cache lists
        categories = {
            'palm': self._external_palms,
            'rock': self._external_rocks,
            'ruin': self._external_ruins,
            'pool': self._external_water,
            'plant': self._external_plants,
            'wall': self._external_walls,  # Treat walls as ruins
            'barrel': self._external_barrels,
            'crate': self._external_crates,
            'chest': self._external_chests,
            'urn': self._external_urns,
            'rug': self._external_rugs,
        }
        
        loaded = 0
        for name, info in mapping.items():
            filepath = os.path.join(sprites_dir, info["file"])
            if not os.path.exists(filepath):
                continue
            
            try:
                surf = pygame.image.load(filepath).convert_alpha()
                
                # Specifically capture wall1 and wall3 for room borders
                name_lower = name.lower()
                if name_lower == 'wall1':
                    # Transform to align with top-right isometric edge (26.57° from horizontal)
                    self._wall1 = self._align_wall_to_isometric(surf, target_angle=26.57)
                elif name_lower == 'wall3':
                    # Transform to align with top-left isometric edge (-26.57° from horizontal)
                    self._wall3 = self._align_wall_to_isometric(surf, target_angle=-26.57)
                
                # Find matching category
                for keyword, cache_list in categories.items():
                    if keyword in name_lower:
                        cache_list.append(surf)
                        loaded += 1
                        break
                        
            except Exception as e:
                print(f"Error loading {filepath}: {e}")
        
        if loaded > 0:
            print(f"Loaded {loaded} external sprites: "
                  f"{len(self._external_palms)} palms, "
                  f"{len(self._external_rocks)} rocks, "
                  f"{len(self._external_ruins) + len(self._external_walls)} ruins, "
                  f"{len(self._external_water)} pools, "
                  f"{len(self._external_plants)} plants, "
                  f"{len(self._external_barrels)} barrels, "
                  f"{len(self._external_crates)} crates, "
                  f"{len(self._external_chests)} chests, "
                  f"{len(self._external_urns)} urns, "
                  f"{len(self._external_rugs)} rugs")
    
    def _draw_palm_tree(self, x: float, y: float, size: float, variant: int):
        """Draw a palm tree using external or cached surface."""
        screen_x, screen_y = self.camera.world_to_screen(x, y)
        
        # Use external palm if available
        if self._external_palms:
            surf = self._external_palms[variant % len(self._external_palms)]
            # Scale based on size parameter and zoom
            base_scale = size * 1.5  # Make them bigger
            scaled_width = int(surf.get_width() * self.camera.zoom * base_scale)
            scaled_height = int(surf.get_height() * self.camera.zoom * base_scale)
        else:
            # Fallback to procedural
            size_idx = min(2, max(0, int((size - 0.85) / 0.1)))
            key = (variant, size_idx)
            
            if key not in self._palm_cache:
                return
            
            surf = self._palm_cache[key]
            scaled_width = int(surf.get_width() * self.camera.zoom)
            scaled_height = int(surf.get_height() * self.camera.zoom)
        
        if scaled_width < 10 or scaled_height < 10:
            return
        
        scaled = pygame.transform.smoothscale(surf, (scaled_width, scaled_height))
        draw_x = screen_x - scaled_width // 2
        draw_y = screen_y - scaled_height + int(20 * self.camera.zoom)
        
        self.screen.blit(scaled, (draw_x, draw_y))
    
    def _create_rock_surface(self, size: float, variant: int) -> pygame.Surface:
        """Create a desert rock/boulder surface."""
        width = int(80 * size)
        height = int(60 * size)
        surf = pygame.Surface((width, height), pygame.SRCALPHA)
        
        cx, cy = width // 2, height // 2
        
        # Rock colors - warm desert tones
        colors = [
            [(140, 110, 80), (110, 85, 60), (90, 70, 50)],    # Sandstone
            [(120, 100, 90), (95, 80, 70), (75, 60, 50)],     # Gray-brown
            [(160, 130, 100), (130, 105, 80), (100, 80, 60)], # Light tan
            [(100, 80, 70), (80, 65, 55), (60, 50, 40)],      # Dark brown
            [(150, 120, 90), (120, 95, 70), (90, 70, 55)],    # Golden
        ]
        base, mid, dark = colors[variant % len(colors)]
        
        # Main rock shape (irregular polygon)
        num_points = 6 + variant
        points = []
        for i in range(num_points):
            angle = (i / num_points) * 2 * math.pi
            r = (0.35 + 0.15 * math.sin(angle * 3 + variant)) * min(width, height)
            px = cx + math.cos(angle) * r
            py = cy + math.sin(angle) * r * 0.7  # Flatten vertically
            points.append((int(px), int(py)))
        
        pygame.draw.polygon(surf, mid, points)
        
        # Shading - darker bottom right
        shadow_points = points[len(points)//3:len(points)*2//3]
        if len(shadow_points) >= 3:
            shadow_points.append((cx, cy))
            pygame.draw.polygon(surf, dark, shadow_points)
        
        # Highlight - lighter top left
        highlight_points = points[:len(points)//3] + [(cx, cy)]
        if len(highlight_points) >= 3:
            pygame.draw.polygon(surf, base, highlight_points)
        
        # Outline
        pygame.draw.polygon(surf, dark, points, 2)
        
        # Cracks/texture
        for i in range(2 + variant % 3):
            crack_start = points[i % len(points)]
            crack_end = (cx + (crack_start[0] - cx) * 0.3, 
                        cy + (crack_start[1] - cy) * 0.3)
            pygame.draw.line(surf, dark, crack_start, (int(crack_end[0]), int(crack_end[1])), 1)
        
        return surf
    
    def _draw_rock(self, x: float, y: float, size: float, variant: int):
        """Draw a rock using external or cached surface."""
        screen_x, screen_y = self.camera.world_to_screen(x, y)
        
        # Use external rock if available
        if self._external_rocks:
            surf = self._external_rocks[variant % len(self._external_rocks)]
            base_scale = size * 1.2
        else:
            size_idx = min(2, max(0, int((size - 0.5) / 0.4)))
            key = (variant, size_idx)
            if key not in self._rock_cache:
                return
            surf = self._rock_cache[key]
            base_scale = 1.0
        
        scaled_width = int(surf.get_width() * self.camera.zoom * base_scale)
        scaled_height = int(surf.get_height() * self.camera.zoom * base_scale)
        
        if scaled_width < 5:
            return
        
        scaled = pygame.transform.smoothscale(surf, (scaled_width, scaled_height))
        self.screen.blit(scaled, (screen_x - scaled_width // 2, screen_y - scaled_height // 2))
    
    def _create_ruin_surface(self, size: float, variant: int) -> pygame.Surface:
        """Create a terracotta ruin/pillar surface."""
        width = int(100 * size)
        height = int(140 * size)
        surf = pygame.Surface((width, height), pygame.SRCALPHA)
        
        cx = width // 2
        base_y = height - 10
        
        # Terracotta colors
        terra_dark = (140, 75, 50)
        terra_mid = (175, 95, 65)
        terra_light = (200, 120, 85)
        
        if variant == 0:
            # Broken pillar
            pillar_w = int(35 * size)
            pillar_h = int(90 * size)
            
            # Base
            pygame.draw.rect(surf, terra_mid, 
                           (cx - pillar_w//2 - 5, base_y - 15, pillar_w + 10, 15))
            
            # Pillar shaft
            pygame.draw.rect(surf, terra_mid,
                           (cx - pillar_w//2, base_y - pillar_h, pillar_w, pillar_h - 15))
            pygame.draw.rect(surf, terra_light,
                           (cx - pillar_w//2, base_y - pillar_h, pillar_w // 3, pillar_h - 15))
            pygame.draw.rect(surf, terra_dark,
                           (cx + pillar_w//6, base_y - pillar_h, pillar_w // 3, pillar_h - 15))
            
            # Broken top (jagged)
            for i in range(5):
                jag_x = cx - pillar_w//2 + i * pillar_w // 4
                jag_h = int(10 * size) + (i * 7) % 20
                pygame.draw.polygon(surf, terra_mid, [
                    (jag_x, base_y - pillar_h),
                    (jag_x + pillar_w//5, base_y - pillar_h - jag_h),
                    (jag_x + pillar_w//4, base_y - pillar_h)
                ])
        
        elif variant == 1:
            # Wall fragment
            wall_w = int(70 * size)
            wall_h = int(50 * size)
            
            pygame.draw.rect(surf, terra_mid,
                           (cx - wall_w//2, base_y - wall_h, wall_w, wall_h))
            pygame.draw.rect(surf, terra_light,
                           (cx - wall_w//2, base_y - wall_h, wall_w, 8))
            pygame.draw.rect(surf, terra_dark,
                           (cx - wall_w//2, base_y - 8, wall_w, 8))
            
            # Decorative carved line
            pygame.draw.line(surf, terra_dark,
                           (cx - wall_w//2 + 5, base_y - wall_h//2),
                           (cx + wall_w//2 - 5, base_y - wall_h//2), 3)
        
        elif variant == 2:
            # Archway fragment
            arch_w = int(60 * size)
            arch_h = int(80 * size)
            
            # Left pillar
            pygame.draw.rect(surf, terra_mid,
                           (cx - arch_w//2, base_y - arch_h, 15, arch_h))
            pygame.draw.rect(surf, terra_light,
                           (cx - arch_w//2, base_y - arch_h, 5, arch_h))
            
            # Right pillar (partial)
            pygame.draw.rect(surf, terra_mid,
                           (cx + arch_w//2 - 15, base_y - arch_h + 20, 15, arch_h - 20))
            
            # Arch top (partial)
            pygame.draw.arc(surf, terra_mid,
                          (cx - arch_w//2, base_y - arch_h - 10, arch_w, 40),
                          0, math.pi, int(8 * size))
        
        else:
            # Fallen blocks
            for i in range(3):
                bx = cx - 30 + i * 25 + (i * 7) % 10
                by = base_y - 10 - i * 8
                bw = 20 + (i * 5) % 15
                bh = 15 + (i * 3) % 10
                
                pygame.draw.rect(surf, terra_mid if i % 2 else terra_dark,
                               (bx, by, bw, bh))
                pygame.draw.rect(surf, terra_light,
                               (bx, by, bw, 3))
        
        return surf
    
    def _draw_ruin(self, x: float, y: float, size: float, variant: int):
        """Draw a ruin using external or cached surface."""
        screen_x, screen_y = self.camera.world_to_screen(x, y)
        
        # Use only ruins (walls are now used for room borders)
        if self._external_ruins:
            surf = self._external_ruins[variant % len(self._external_ruins)]
            base_scale = size * 1.3
        else:
            if variant not in self._ruin_cache:
                return
            surf = self._ruin_cache[variant]
            base_scale = size
        
        scaled_width = int(surf.get_width() * self.camera.zoom * base_scale)
        scaled_height = int(surf.get_height() * self.camera.zoom * base_scale)
        
        if scaled_width < 10:
            return
        
        scaled = pygame.transform.smoothscale(surf, (scaled_width, scaled_height))
        self.screen.blit(scaled, (screen_x - scaled_width // 2, 
                                  screen_y - scaled_height + int(10 * self.camera.zoom)))
    
    def _create_water_surface(self, size: float, variant: int) -> pygame.Surface:
        """Create an oasis water pool surface."""
        width = int(120 * size)
        height = int(80 * size)
        surf = pygame.Surface((width, height), pygame.SRCALPHA)
        
        cx, cy = width // 2, height // 2
        
        # Water colors - teal/turquoise like temple pools
        water_deep = (30, 90, 100)
        water_mid = (50, 130, 140)
        water_light = (80, 170, 180)
        water_shine = (150, 220, 230)
        
        # Sandy edge
        edge_color = (190, 160, 120)
        
        # Outer sandy edge (ellipse)
        pygame.draw.ellipse(surf, edge_color, (0, 0, width, height))
        
        # Main water pool
        pool_margin = int(12 * size)
        pygame.draw.ellipse(surf, water_deep, 
                          (pool_margin, pool_margin, 
                           width - pool_margin*2, height - pool_margin*2))
        
        # Lighter center
        inner_margin = int(25 * size)
        pygame.draw.ellipse(surf, water_mid,
                          (inner_margin, inner_margin,
                           width - inner_margin*2, height - inner_margin*2))
        
        # Highlight/reflection
        shine_x = cx - int(15 * size)
        shine_y = cy - int(10 * size)
        pygame.draw.ellipse(surf, water_light,
                          (shine_x, shine_y, int(30 * size), int(15 * size)))
        
        # Small shine spot
        pygame.draw.ellipse(surf, water_shine,
                          (shine_x + 5, shine_y + 3, int(10 * size), int(6 * size)))
        
        # Ripple lines
        for i in range(2 + variant):
            ripple_r = int((20 + i * 15) * size)
            pygame.draw.ellipse(surf, water_light,
                              (cx - ripple_r, cy - ripple_r//2, ripple_r*2, ripple_r),
                              1)
        
        return surf
    
    def _draw_water(self, x: float, y: float, size: float, variant: int):
        """Draw a water pool using external or cached surface."""
        screen_x, screen_y = self.camera.world_to_screen(x, y)
        
        if self._external_water:
            surf = self._external_water[variant % len(self._external_water)]
            base_scale = size * 1.5
        else:
            size_idx = min(2, max(0, int((size - 0.8) / 0.5)))
            key = (variant, size_idx)
            if key not in self._water_cache:
                return
            surf = self._water_cache[key]
            base_scale = 1.0
        
        scaled_width = int(surf.get_width() * self.camera.zoom * base_scale)
        scaled_height = int(surf.get_height() * self.camera.zoom * base_scale)
        
        if scaled_width < 10:
            return
        
        scaled = pygame.transform.smoothscale(surf, (scaled_width, scaled_height))
        self.screen.blit(scaled, (screen_x - scaled_width // 2, screen_y - scaled_height // 2))
    
    def _create_plant_surface(self, size: float, variant: int) -> pygame.Surface:
        """Create a small desert plant/grass tuft."""
        width = int(40 * size)
        height = int(35 * size)
        surf = pygame.Surface((width, height), pygame.SRCALPHA)
        
        cx = width // 2
        base_y = height - 5
        
        if variant == 0:
            # Grass tuft
            grass_colors = [(80, 130, 60), (100, 150, 70), (70, 110, 50)]
            for i in range(7):
                gx = cx + (i - 3) * 4
                gh = int(15 + (i * 5) % 12)
                curve = (i - 3) * 2
                color = grass_colors[i % 3]
                
                pts = [(gx, base_y), (gx + curve, base_y - gh), (gx + 2, base_y)]
                pygame.draw.polygon(surf, color, pts)
        
        elif variant == 1:
            # Small bush
            bush_color = (60, 100, 50)
            bush_light = (80, 130, 65)
            
            pygame.draw.ellipse(surf, bush_color, (cx - 15, base_y - 20, 30, 22))
            pygame.draw.ellipse(surf, bush_light, (cx - 10, base_y - 18, 15, 12))
        
        else:
            # Desert flower
            stem_color = (70, 110, 55)
            flower_color = (220, 180, 80)  # Yellow/orange
            
            pygame.draw.line(surf, stem_color, (cx, base_y), (cx, base_y - 20), 2)
            pygame.draw.circle(surf, flower_color, (cx, base_y - 22), 6)
            pygame.draw.circle(surf, (240, 200, 100), (cx - 1, base_y - 23), 3)
        
        return surf
    
    def _draw_plant(self, x: float, y: float, size: float, variant: int):
        """Draw a plant using external or cached surface."""
        screen_x, screen_y = self.camera.world_to_screen(x, y)
        
        if self._external_plants:
            surf = self._external_plants[variant % len(self._external_plants)]
            base_scale = size * 1.2
        else:
            if variant not in self._plant_cache:
                return
            surf = self._plant_cache[variant]
            base_scale = size
        
        scaled_width = int(surf.get_width() * self.camera.zoom * base_scale)
        scaled_height = int(surf.get_height() * self.camera.zoom * base_scale)
        
        if scaled_width < 5:
            return
        
        scaled = pygame.transform.smoothscale(surf, (scaled_width, scaled_height))
        self.screen.blit(scaled, (screen_x - scaled_width // 2, 
                                  screen_y - scaled_height + int(5 * self.camera.zoom)))
    
    # ==================== ROOM PROPS ====================
    
    def _create_barrel_surface(self, variant: int) -> pygame.Surface:
        """Create a wooden barrel surface."""
        width, height = 40, 50
        surf = pygame.Surface((width, height), pygame.SRCALPHA)
        
        # Colors - worn wood tones
        colors = [
            ((120, 80, 50), (90, 60, 40), (70, 45, 30)),   # Oak brown
            ((100, 70, 45), (75, 55, 35), (55, 40, 25)),   # Dark wood
            ((140, 95, 60), (110, 75, 50), (85, 55, 35)),  # Light wood
        ]
        wood, wood_dark, wood_shadow = colors[variant % len(colors)]
        band_color = (60, 55, 50)  # Iron bands
        
        cx, cy = width // 2, height // 2
        
        # Main barrel body (oval)
        pygame.draw.ellipse(surf, wood, (4, 8, 32, 38))
        pygame.draw.ellipse(surf, wood_dark, (4, 8, 32, 38), 2)
        
        # Side shading
        pygame.draw.ellipse(surf, wood_shadow, (4, 12, 10, 30))
        
        # Top ellipse
        pygame.draw.ellipse(surf, wood_dark, (6, 4, 28, 12))
        pygame.draw.ellipse(surf, wood, (8, 5, 24, 9))
        
        # Metal bands
        pygame.draw.ellipse(surf, band_color, (5, 14, 30, 6), 2)
        pygame.draw.ellipse(surf, band_color, (5, 32, 30, 6), 2)
        
        # Wood grain lines
        for i in range(3):
            lx = 12 + i * 8
            pygame.draw.line(surf, wood_dark, (lx, 12), (lx, 40), 1)
        
        return surf
    
    def _create_urn_surface(self, variant: int) -> pygame.Surface:
        """Create a decorative terracotta urn."""
        width, height = 35, 50
        surf = pygame.Surface((width, height), pygame.SRCALPHA)
        
        # Terracotta colors
        colors = [
            ((180, 100, 70), (150, 80, 55), (120, 60, 40)),
            ((160, 90, 65), (130, 70, 50), (100, 55, 35)),
            ((200, 115, 80), (170, 95, 65), (140, 75, 50)),
        ]
        terra, terra_mid, terra_dark = colors[variant % len(colors)]
        
        cx = width // 2
        
        # Base
        pygame.draw.ellipse(surf, terra_dark, (10, 42, 15, 6))
        
        # Body - bulbous bottom
        pygame.draw.ellipse(surf, terra, (5, 22, 25, 24))
        pygame.draw.ellipse(surf, terra_mid, (5, 22, 10, 20))  # Shading
        
        # Neck
        pygame.draw.rect(surf, terra, (12, 10, 11, 15))
        pygame.draw.rect(surf, terra_mid, (12, 10, 4, 15))
        
        # Rim
        pygame.draw.ellipse(surf, terra, (10, 6, 15, 8))
        pygame.draw.ellipse(surf, terra_dark, (10, 6, 15, 8), 1)
        
        # Decorative pattern (horizontal lines)
        pygame.draw.line(surf, terra_dark, (8, 28), (27, 28), 1)
        pygame.draw.line(surf, terra_dark, (6, 34), (29, 34), 1)
        
        # Maybe a crack
        if variant == 1:
            pygame.draw.line(surf, terra_dark, (18, 15), (22, 30), 1)
        
        return surf
    
    def _create_crate_surface(self, variant: int) -> pygame.Surface:
        """Create a wooden crate."""
        size = 36
        surf = pygame.Surface((size, size + 5), pygame.SRCALPHA)
        
        colors = [
            ((130, 90, 55), (100, 70, 45)),
            ((110, 75, 50), (85, 60, 40)),
            ((145, 100, 60), (115, 80, 50)),
        ]
        wood, wood_dark = colors[variant % len(colors)]
        
        # Top face (diamond for isometric)
        top_points = [(size//2, 0), (size-2, 12), (size//2, 24), (2, 12)]
        pygame.draw.polygon(surf, wood, top_points)
        pygame.draw.polygon(surf, wood_dark, top_points, 2)
        
        # Front-left face
        fl_points = [(2, 12), (size//2, 24), (size//2, size+2), (2, size-10)]
        pygame.draw.polygon(surf, wood_dark, fl_points)
        pygame.draw.polygon(surf, (70, 50, 30), fl_points, 1)
        
        # Front-right face
        fr_points = [(size//2, 24), (size-2, 12), (size-2, size-10), (size//2, size+2)]
        pygame.draw.polygon(surf, wood, fr_points)
        pygame.draw.polygon(surf, (70, 50, 30), fr_points, 1)
        
        # Cross boards on top
        pygame.draw.line(surf, wood_dark, top_points[0], top_points[2], 2)
        pygame.draw.line(surf, wood_dark, top_points[1], top_points[3], 2)
        
        return surf
    
    def _create_pot_surface(self, variant: int) -> pygame.Surface:
        """Create a clay pot."""
        width, height = 28, 30
        surf = pygame.Surface((width, height), pygame.SRCALPHA)
        
        colors = [
            ((165, 95, 65), (135, 75, 50)),
            ((145, 85, 60), (115, 65, 45)),
            ((180, 105, 75), (150, 85, 60)),
        ]
        clay, clay_dark = colors[variant % len(colors)]
        
        # Main pot body
        pygame.draw.ellipse(surf, clay, (4, 8, 20, 20))
        pygame.draw.ellipse(surf, clay_dark, (4, 10, 8, 16))  # Shadow
        
        # Rim
        pygame.draw.ellipse(surf, clay, (6, 4, 16, 8))
        pygame.draw.ellipse(surf, clay_dark, (6, 4, 16, 8), 1)
        
        # Interior shadow
        pygame.draw.ellipse(surf, clay_dark, (8, 5, 12, 5))
        
        return surf
    
    def _create_chest_surface(self, variant: int) -> pygame.Surface:
        """Create a treasure chest."""
        width, height = 45, 40
        surf = pygame.Surface((width, height), pygame.SRCALPHA)
        
        # Chest colors
        wood = (100, 65, 40)
        wood_light = (130, 85, 55)
        wood_dark = (70, 45, 28)
        metal = (180, 150, 60) if variant == 0 else (120, 110, 100)
        metal_dark = (140, 115, 45) if variant == 0 else (85, 80, 75)
        
        # Base/bottom
        pygame.draw.rect(surf, wood, (4, 20, 37, 18))
        pygame.draw.rect(surf, wood_dark, (4, 20, 37, 18), 2)
        
        # Curved lid
        pygame.draw.ellipse(surf, wood_light, (4, 8, 37, 24))
        pygame.draw.rect(surf, (0, 0, 0, 0), (0, 20, 45, 20))  # Cut bottom
        pygame.draw.ellipse(surf, wood, (4, 8, 37, 24))
        pygame.draw.arc(surf, wood_dark, (4, 8, 37, 24), 0, 3.14, 2)
        
        # Metal straps
        pygame.draw.rect(surf, metal, (10, 10, 4, 28))
        pygame.draw.rect(surf, metal, (31, 10, 4, 28))
        pygame.draw.rect(surf, metal_dark, (10, 10, 4, 28), 1)
        pygame.draw.rect(surf, metal_dark, (31, 10, 4, 28), 1)
        
        # Lock/clasp
        pygame.draw.rect(surf, metal, (19, 18, 7, 8))
        pygame.draw.rect(surf, metal_dark, (19, 18, 7, 8), 1)
        pygame.draw.circle(surf, metal_dark, (22, 24), 2)
        
        return surf
    
    def _render_floor_decor(self, dungeon: Dungeon):
        """Render floor decorations (rugs, patterns, etc.)."""
        bounds = self.camera.get_visible_bounds()
        
        for decor in dungeon.floor_decor:
            # Check visibility
            if not (bounds[0] - 5 <= decor.x <= bounds[2] + 5 and
                    bounds[1] - 5 <= decor.y <= bounds[3] + 5):
                continue
            
            self._draw_floor_decor(decor)
    
    def _draw_floor_decor(self, decor):
        """Draw a single floor decoration."""
        screen_x, screen_y = self.camera.world_to_screen(decor.x, decor.y)
        tile_w = int(TILE_WIDTH * self.camera.zoom)
        tile_h = int(TILE_HEIGHT * self.camera.zoom)
        
        if decor.type == 'rug':
            self._draw_rug(screen_x, screen_y, decor.width, decor.height, decor.variant)
        elif decor.type == 'mosaic':
            self._draw_mosaic(screen_x, screen_y, decor.width, decor.variant)
        elif decor.type == 'accent':
            self._draw_accent_tile(screen_x, screen_y, decor.variant)
        elif decor.type == 'border':
            self._draw_border_tiles(screen_x, screen_y, decor.width, decor.height, decor.variant)
        elif decor.type == 'crack':
            self._draw_floor_crack(screen_x, screen_y, decor.variant)
        elif decor.type == 'stain':
            self._draw_floor_stain(screen_x, screen_y, decor.variant)
    
    def _draw_rug(self, sx: int, sy: int, w: int, h: int, variant: int):
        """Draw an ornate rug using external or procedural."""
        tile_w = int(TILE_WIDTH * self.camera.zoom)
        tile_h = int(TILE_HEIGHT * self.camera.zoom)
        
        rug_w = w * tile_w
        rug_h = h * tile_h // 2
        
        # Use external rug if available
        if self._external_rugs:
            surf = self._external_rugs[variant % len(self._external_rugs)]
            scaled = pygame.transform.smoothscale(surf, (rug_w, rug_h))
            self.screen.blit(scaled, (sx - rug_w // 2, sy - rug_h // 2))
            return
        
        # Procedural fallback
        colors = [
            ((150, 50, 50), (180, 80, 40), (60, 40, 80)),
            ((50, 80, 130), (70, 110, 160), (180, 150, 60)),
            ((80, 120, 60), (110, 150, 80), (150, 80, 50)),
            ((130, 60, 100), (160, 90, 130), (200, 170, 80)),
        ]
        main, accent, border = colors[variant % len(colors)]
        
        rug_surf = pygame.Surface((rug_w, rug_h), pygame.SRCALPHA)
        pygame.draw.rect(rug_surf, main, (0, 0, rug_w, rug_h))
        pygame.draw.rect(rug_surf, border, (0, 0, rug_w, rug_h), max(2, int(3 * self.camera.zoom)))
        
        inner_margin = max(4, int(8 * self.camera.zoom))
        pygame.draw.rect(rug_surf, accent, 
                        (inner_margin, inner_margin, 
                         rug_w - inner_margin*2, rug_h - inner_margin*2), 
                        max(1, int(2 * self.camera.zoom)))
        
        cx, cy = rug_w // 2, rug_h // 2
        d_size = min(rug_w, rug_h) // 3
        diamond = [(cx, cy - d_size), (cx + d_size, cy), 
                   (cx, cy + d_size), (cx - d_size, cy)]
        pygame.draw.polygon(rug_surf, accent, diamond)
        pygame.draw.polygon(rug_surf, border, diamond, 1)
        
        self.screen.blit(rug_surf, (sx - rug_w // 2, sy - rug_h // 2))
    
    def _draw_mosaic(self, sx: int, sy: int, size: int, variant: int):
        """Draw a floor mosaic pattern."""
        tile_w = int(TILE_WIDTH * self.camera.zoom)
        tile_h = int(TILE_HEIGHT * self.camera.zoom)
        
        mos_size = size * tile_w
        
        # Mosaic colors
        colors = [
            ((180, 160, 140), (140, 100, 70), (100, 80, 60)),
            ((160, 150, 130), (120, 90, 60), (80, 60, 45)),
            ((170, 155, 135), (130, 95, 65), (90, 70, 50)),
        ]
        light, mid, dark = colors[variant % len(colors)]
        
        surf = pygame.Surface((mos_size, mos_size // 2), pygame.SRCALPHA)
        
        # Circular mosaic
        cx, cy = mos_size // 2, mos_size // 4
        pygame.draw.ellipse(surf, mid, (4, 4, mos_size - 8, mos_size // 2 - 8))
        pygame.draw.ellipse(surf, dark, (4, 4, mos_size - 8, mos_size // 2 - 8), 2)
        
        # Inner rings
        for i in range(3, 0, -1):
            r = (mos_size // 2 - 10) * i // 4
            color = light if i % 2 else mid
            pygame.draw.ellipse(surf, color, (cx - r, cy - r//2, r*2, r), 0)
            pygame.draw.ellipse(surf, dark, (cx - r, cy - r//2, r*2, r), 1)
        
        self.screen.blit(surf, (sx - mos_size // 2, sy - mos_size // 4))
    
    def _draw_accent_tile(self, sx: int, sy: int, variant: int):
        """Draw a single decorative floor tile."""
        tile_w = int(TILE_WIDTH * self.camera.zoom)
        tile_h = int(TILE_HEIGHT * self.camera.zoom)
        
        colors = [
            (170, 140, 110), (150, 120, 95), (185, 155, 125),
            (160, 130, 100), (175, 145, 115)
        ]
        color = colors[variant % len(colors)]
        
        # Diamond tile
        half_w, half_h = tile_w // 3, tile_h // 3
        points = [(sx, sy - half_h), (sx + half_w, sy), 
                  (sx, sy + half_h), (sx - half_w, sy)]
        pygame.draw.polygon(self.screen, color, points)
        pygame.draw.polygon(self.screen, (color[0] - 30, color[1] - 25, color[2] - 20), points, 1)
    
    def _draw_border_tiles(self, sx: int, sy: int, w: int, h: int, variant: int):
        """Draw a tile border around a room."""
        tile_w = int(TILE_WIDTH * self.camera.zoom)
        tile_h = int(TILE_HEIGHT * self.camera.zoom)
        
        border_color = (150, 120, 90)
        
        # Just draw corner accents to avoid clutter
        corner_size = int(8 * self.camera.zoom)
        corners = [
            (sx, sy),
            (sx + w * tile_w, sy),
            (sx + w * tile_w, sy + h * tile_h // 2),
            (sx, sy + h * tile_h // 2)
        ]
        
        for cx, cy in corners:
            pygame.draw.rect(self.screen, border_color, 
                           (cx - corner_size//2, cy - corner_size//2, 
                            corner_size, corner_size))
    
    def _draw_floor_crack(self, sx: int, sy: int, variant: int):
        """Draw a crack in the floor."""
        color = (80, 65, 50)
        
        # Random crack pattern
        if variant == 0:
            points = [(sx, sy), (sx + 5, sy + 8), (sx + 3, sy + 15), (sx + 10, sy + 20)]
        elif variant == 1:
            points = [(sx - 8, sy), (sx, sy + 5), (sx + 8, sy + 3), (sx + 12, sy + 10)]
        else:
            points = [(sx, sy - 5), (sx + 3, sy + 5), (sx - 2, sy + 12)]
        
        scaled_points = [(int(p[0] * self.camera.zoom), int(p[1] * self.camera.zoom)) 
                        for p in points]
        
        if len(scaled_points) >= 2:
            pygame.draw.lines(self.screen, color, False, scaled_points, 
                            max(1, int(2 * self.camera.zoom)))
    
    def _draw_floor_stain(self, sx: int, sy: int, variant: int):
        """Draw a stain on the floor."""
        colors = [(100, 85, 70, 100), (90, 75, 60, 80), (110, 95, 80, 90)]
        color = colors[variant % len(colors)]
        
        size = int((10 + variant * 5) * self.camera.zoom)
        
        stain_surf = pygame.Surface((size * 2, size), pygame.SRCALPHA)
        pygame.draw.ellipse(stain_surf, color, (0, 0, size * 2, size))
        
        self.screen.blit(stain_surf, (sx - size, sy - size // 2))
    
    def _render_room_props(self, dungeon: Dungeon):
        """Render room props (barrels, urns, chests, etc.)."""
        bounds = self.camera.get_visible_bounds()
        
        # Collect visible props
        visible_props = []
        for prop in dungeon.room_props:
            if (bounds[0] - 2 <= prop.x <= bounds[2] + 2 and
                bounds[1] - 2 <= prop.y <= bounds[3] + 2):
                visible_props.append(prop)
        
        # Sort by Y for proper layering
        visible_props.sort(key=lambda p: p.y)
        
        for prop in visible_props:
            self._draw_room_prop(prop)
    
    def _draw_room_prop(self, prop):
        """Draw a single room prop."""
        screen_x, screen_y = self.camera.world_to_screen(prop.x, prop.y)
        
        surf = None
        
        # Check for external sprites first
        if prop.type == 'barrel' and self._external_barrels:
            surf = self._external_barrels[prop.variant % len(self._external_barrels)]
        elif prop.type == 'crate' and self._external_crates:
            surf = self._external_crates[prop.variant % len(self._external_crates)]
        elif prop.type == 'chest' and self._external_chests:
            surf = self._external_chests[prop.variant % len(self._external_chests)]
        elif prop.type == 'urn' and self._external_urns:
            surf = self._external_urns[prop.variant % len(self._external_urns)]
        else:
            # Use procedural cache
            cache = None
            if prop.type == 'barrel':
                cache = self._barrel_cache
            elif prop.type == 'urn':
                cache = self._urn_cache
            elif prop.type == 'crate':
                cache = self._crate_cache
            elif prop.type == 'pot':
                cache = self._pot_cache
            elif prop.type == 'chest':
                cache = self._chest_cache
            
            if cache is not None and prop.variant in cache:
                surf = cache[prop.variant]
        
        if surf is None:
            return
        scaled_w = int(surf.get_width() * self.camera.zoom)
        scaled_h = int(surf.get_height() * self.camera.zoom)
        
        if scaled_w < 5:
            return
        
        scaled = pygame.transform.smoothscale(surf, (scaled_w, scaled_h))
        
        # Draw prop (no shadow)
        self.screen.blit(scaled, (screen_x - scaled_w // 2, screen_y - scaled_h + int(5 * self.camera.zoom)))
    
    def _collect_renderable_entities(self) -> List[Tuple]:
        """Collect all entities that should be rendered."""
        entities = []
        
        for ent, (pos, sprite) in esper.get_components(Position, Sprite):
            # Skip dropped items and gold - they're rendered separately
            if esper.has_component(ent, DroppedItem) or esper.has_component(ent, GoldDrop):
                continue
            
            entities.append((
                ent,
                pos.y + pos.x * 0.001,  # Sort key (y position, with x tiebreaker)
                pos,
                sprite
            ))
        
        return entities
    
    def _render_entity(self, ent_data: Tuple):
        """Render a single entity."""
        ent, _, pos, sprite = ent_data
        
        # Get screen position (ground position)
        ground_x, ground_y = self.camera.world_to_screen(pos.x, pos.y)
        screen_x, screen_y = ground_x, ground_y
        
        # Track if entity is airborne for shadow
        air_height = 0
        
        # Apply render offset (e.g., for leap attacks)
        if esper.has_component(ent, RenderOffset):
            offset = esper.component_for_entity(ent, RenderOffset)
            screen_x += int(offset.x * self.camera.zoom)
            screen_y += int(offset.y * self.camera.zoom)
            air_height = -offset.y  # Positive = in the air
        
        # Get animation state
        anim_state = AnimationState.IDLE
        frame = 0
        if esper.has_component(ent, Animation):
            anim = esper.component_for_entity(ent, Animation)
            anim_state = anim.state
            frame = anim.frame
        
        # Get facing
        direction = Direction.DOWN
        if esper.has_component(ent, Facing):
            direction = esper.component_for_entity(ent, Facing).direction
        
        # Get sprite frame
        surf = self.sprites.get_character_frame(
            sprite.sprite_set, anim_state, direction, frame
        )
        
        # Get actual sprite size
        actual_w = surf.get_width()
        actual_h = surf.get_height()
        
        # Scale
        scaled_w = int(actual_w * self.camera.zoom)
        scaled_h = int(actual_h * self.camera.zoom)
        scaled = pygame.transform.scale(surf, (scaled_w, scaled_h))
        
        # Rotate if dead (fall over effect)
        is_dead = esper.has_component(ent, Dead)
        is_downed = esper.has_component(ent, Downed)
        if is_dead or is_downed:
            # Rotate 90 degrees to show fallen
            scaled = pygame.transform.rotate(scaled, 90)
            # Fade out dead enemies
            if is_dead:
                scaled.set_alpha(150)
        
        # Center on position (use rotated dimensions)
        draw_x = screen_x - scaled.get_width() // 2
        draw_y = screen_y - scaled.get_height() // 2 if (is_dead or is_downed) else screen_y - scaled_h
        
        # Draw shadow on ground if airborne (during leap)
        # Baseline offset is 16 (entities have y=-16), so leap height = air_height - 16
        leap_height = air_height - 16 if air_height > 16 else 0
        if leap_height > 20:  # Only show shadow when actually leaping
            shadow_alpha = min(150, int(50 + leap_height * 0.5))
            shadow_w = int(scaled_w * 0.7)
            shadow_h = int(8 * self.camera.zoom)
            shadow_x = ground_x - shadow_w // 2
            shadow_y = ground_y - shadow_h // 2
            
            shadow_surf = pygame.Surface((shadow_w, shadow_h), pygame.SRCALPHA)
            pygame.draw.ellipse(shadow_surf, (0, 0, 0, shadow_alpha), (0, 0, shadow_w, shadow_h))
            self.screen.blit(shadow_surf, (shadow_x, shadow_y))
        
        # Draw selection indicator (but not for dead entities)
        if esper.has_component(ent, Selected) and not is_dead:
            indicator_y = draw_y + scaled.get_height()
            pygame.draw.ellipse(
                self.screen,
                (100, 180, 100, 150),
                (draw_x, indicator_y - 4, scaled.get_width(), 8)
            )
        
        # Draw sprite
        self.screen.blit(scaled, (draw_x, draw_y))
        
        # Draw health bar (but not for dead entities)
        if esper.has_component(ent, HealthBar) and esper.has_component(ent, Health) and not is_dead:
            health_bar = esper.component_for_entity(ent, HealthBar)
            health = esper.component_for_entity(ent, Health)
            
            if health_bar.show and health.percent < 1.0:
                bar_w = int(32 * self.camera.zoom)
                bar_h = int(4 * self.camera.zoom)
                bar_x = screen_x - bar_w // 2
                bar_y = draw_y - int(8 * self.camera.zoom)
                
                # Background
                pygame.draw.rect(self.screen, (30, 30, 30), (bar_x, bar_y, bar_w, bar_h))
                
                # Health fill
                fill_w = int(bar_w * health.percent)
                color = COLOR_HEALTH if esper.has_component(ent, Enemy) else (60, 160, 60)
                pygame.draw.rect(self.screen, color, (bar_x, bar_y, fill_w, bar_h))
                
                # Border
                pygame.draw.rect(self.screen, (60, 60, 60), (bar_x, bar_y, bar_w, bar_h), 1)
    
    def _render_projectiles(self):
        """Render spell projectiles."""
        for ent, (pos, proj) in esper.get_components(Position, Projectile):
            screen_x, screen_y = self.camera.world_to_screen(pos.x, pos.y)
            
            # Choose color based on damage type
            damage_type = proj.damage_type if proj.damage_type else "fire"
            color = self._get_damage_type_color(damage_type)
            
            # Draw projectile as a glowing orb - ensure minimum size
            size = max(4, int(12 * self.camera.zoom))
            
            try:
                # Glow effect
                glow_surf = pygame.Surface((size * 3, size * 3), pygame.SRCALPHA)
                for i in range(3, 0, -1):
                    alpha = min(255, 50 * i)
                    glow_color = (color[0], color[1], color[2], alpha)
                    radius = max(1, size * i // 2)
                    pygame.draw.circle(glow_surf, glow_color, (int(size * 1.5), int(size * 1.5)), radius)
                
                self.screen.blit(glow_surf, (int(screen_x - size * 1.5), int(screen_y - size * 1.5)))
                
                # Core
                pygame.draw.circle(self.screen, color, (int(screen_x), int(screen_y)), max(1, size // 2))
                pygame.draw.circle(self.screen, (255, 255, 255), (int(screen_x), int(screen_y)), max(1, size // 4))
            except (ValueError, pygame.error):
                pass  # Skip invalid projectiles
    
    def _render_area_effects(self):
        """Render area of effect markers."""
        for ent, (pos, effect) in esper.get_components(Position, AreaEffect):
            screen_x, screen_y = self.camera.world_to_screen(pos.x, pos.y)
            
            # Get color based on damage type
            damage_type = effect.damage_type if effect.damage_type else "fire"
            color = self._get_damage_type_color(damage_type)
            
            # Draw AOE circle - ensure minimum radius
            radius = max(4, int(effect.radius * TILE_WIDTH * self.camera.zoom * 0.5))
            
            # Pulsing effect based on timer - clamp alpha
            pulse = abs((effect.duration % 1.0) - 0.5) * 2
            alpha = max(0, min(255, int(80 + pulse * 50)))
            
            try:
                # Create surface for transparency
                aoe_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
                fill_color = (color[0], color[1], color[2], max(0, alpha // 2))
                border_color = (color[0], color[1], color[2], alpha)
                pygame.draw.circle(aoe_surf, fill_color, (radius, radius), radius)
                pygame.draw.circle(aoe_surf, border_color, (radius, radius), radius, 2)
                self.screen.blit(aoe_surf, (int(screen_x - radius), int(screen_y - radius)))
            except (ValueError, pygame.error):
                pass  # Skip invalid effects
    
    def _render_visual_effects(self):
        """Render visual effects (explosions, etc.)."""
        for ent, (pos, effect) in esper.get_components(Position, VisualEffect):
            screen_x, screen_y = self.camera.world_to_screen(pos.x, pos.y)
            
            effect_type = effect.effect_type if effect.effect_type else ""
            
            # Get base color from effect type
            if 'fire' in effect_type:
                color = (255, 120, 40)
            elif 'ice' in effect_type:
                color = (100, 180, 255)
            elif 'lightning' in effect_type:
                color = (255, 255, 100)
            elif 'poison' in effect_type:
                color = (100, 200, 80)
            elif 'heal' in effect_type:
                color = (100, 255, 150)
            else:
                color = (200, 200, 200)
            
            # Fade based on timer - clamp alpha to valid range
            alpha = max(0, min(255, int(255 * min(1.0, max(0.0, effect.timer)))))
            
            # Draw effect - ensure minimum size
            size = max(4, int(20 * self.camera.zoom))
            
            try:
                effect_surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
                pygame.draw.circle(effect_surf, (color[0], color[1], color[2], alpha), (size, size), size)
                pygame.draw.circle(effect_surf, (color[0], color[1], color[2], max(0, alpha // 2)), (size, size), size + 4, 2)
                self.screen.blit(effect_surf, (int(screen_x - size), int(screen_y - size)))
            except (ValueError, pygame.error):
                pass  # Skip invalid effects
    
    def _get_damage_type_color(self, damage_type: str) -> tuple:
        """Get color for a damage type."""
        colors = {
            'fire': (255, 120, 40),
            'ice': (100, 180, 255),
            'lightning': (255, 255, 100),
            'poison': (100, 200, 80),
            'holy': (255, 255, 200),
            'physical': (200, 200, 200),
        }
        return colors.get(damage_type, (200, 200, 200))
    
    def _render_damage_numbers(self):
        """Render floating damage numbers."""
        for ent, (pos, dmg) in esper.get_components(Position, DamageNumber):
            screen_x, screen_y = self.camera.world_to_screen(pos.x, pos.y)
            
            # Choose color based on damage type
            if dmg.is_heal:
                color = (100, 255, 100)  # Bright green for heals
            elif dmg.is_player_damage:
                color = (255, 50, 50)    # Red for damage to party members
            elif dmg.is_crit:
                color = (255, 255, 50)   # Yellow for crits
            else:
                color = (50, 255, 50)    # Green for damage to enemies
            
            # Fade out over timer
            alpha = int(255 * min(1.0, dmg.timer / 0.8))
            
            text = str(dmg.value)
            if dmg.is_crit:
                text += "!"
            
            # Use big font for damage numbers
            text_surf = self.font_damage.render(text, True, color)
            
            # Add black outline for visibility
            outline_color = (0, 0, 0)
            outline_surf = self.font_damage.render(text, True, outline_color)
            
            # Draw outline (offset in 4 directions)
            for ox, oy in [(-2, 0), (2, 0), (0, -2), (0, 2), (-1, -1), (1, -1), (-1, 1), (1, 1)]:
                outline_surf.set_alpha(alpha)
                self.screen.blit(
                    outline_surf,
                    (screen_x - text_surf.get_width() // 2 + ox, screen_y + oy)
                )
            
            # Draw main text
            text_surf.set_alpha(alpha)
            self.screen.blit(
                text_surf,
                (screen_x - text_surf.get_width() // 2, screen_y)
            )
    
    def _render_dropped_items(self):
        """Render dropped items with glow effect."""
        import math
        
        for ent, (pos, dropped) in esper.get_components(Position, DroppedItem):
            screen_x, screen_y = self.camera.world_to_screen(pos.x, pos.y)
            
            # Get rarity color
            rarity = dropped.rarity
            rarity_color = RARITY_COLORS.get(rarity, (200, 200, 200))
            
            # Pulsing glow effect
            glow_intensity = 0.5 + 0.5 * math.sin(dropped.glow_timer * 3.0)
            glow_size = int(20 + 8 * glow_intensity)
            
            # Draw glow
            glow_surf = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
            glow_alpha = int(80 * glow_intensity)
            for i in range(3, 0, -1):
                radius = int(glow_size * i / 3)
                alpha = glow_alpha // i
                pygame.draw.circle(
                    glow_surf,
                    (rarity_color[0], rarity_color[1], rarity_color[2], alpha),
                    (glow_size, glow_size),
                    radius
                )
            
            self.screen.blit(
                glow_surf,
                (screen_x - glow_size, screen_y - glow_size)
            )
            
            # Draw item icon (small square with rarity border)
            item_size = 16
            item_rect = pygame.Rect(
                screen_x - item_size // 2,
                screen_y - item_size // 2,
                item_size, item_size
            )
            
            pygame.draw.rect(self.screen, (40, 35, 50), item_rect)
            pygame.draw.rect(self.screen, rarity_color, item_rect, 2)
            
            # Item initial if has item data
            if dropped.item and hasattr(dropped.item, 'name'):
                initial = dropped.item.name[0].upper()
                initial_surf = self.font_small.render(initial, True, (255, 255, 255))
                self.screen.blit(
                    initial_surf,
                    (screen_x - initial_surf.get_width() // 2,
                     screen_y - initial_surf.get_height() // 2)
                )
        
        # Render gold drops
        for ent, (pos, gold) in esper.get_components(Position, GoldDrop):
            screen_x, screen_y = self.camera.world_to_screen(pos.x, pos.y)
            
            # Gold coin glow
            gold_color = (220, 180, 60)
            
            # Draw gold coin
            pygame.draw.circle(self.screen, gold_color, (int(screen_x), int(screen_y)), 8)
            pygame.draw.circle(self.screen, (180, 140, 40), (int(screen_x), int(screen_y)), 8, 2)
            
            # Amount text
            if gold.amount > 1:
                text = str(gold.amount)
                text_surf = self.font_small.render(text, True, gold_color)
                self.screen.blit(
                    text_surf,
                    (screen_x - text_surf.get_width() // 2, screen_y + 10)
                )
