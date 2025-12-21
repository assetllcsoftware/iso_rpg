"""Isometric rendering system."""

import pygame
import math
from .constants import (
    TILE_WIDTH, TILE_HEIGHT, SCREEN_WIDTH, SCREEN_HEIGHT,
    TILE_FLOOR, TILE_WALL, TILE_DOOR, TILE_WATER, TILE_LAVA, TILE_STAIRS_DOWN, TILE_STAIRS_UP,
    COLOR_BG, COLOR_UI_ACCENT
)

# Import sprite system
try:
    from src.sprites import (
        get_hero_sprites, get_mage_sprites, 
        get_skeleton_sprites, get_spider_sprites, get_zombie_sprites,
        get_orc_sprites, get_demon_sprites,
        get_spell_sprites, get_spell_effect_sprites,
        get_item_sprites, get_weapon_sprites, get_armor_sprites,
        get_environment_tiles, CHAR_SIZE
    )
    SPRITES_AVAILABLE = True
except ImportError:
    SPRITES_AVAILABLE = False


class IsometricRenderer:
    """Handles all isometric rendering."""
    
    def __init__(self, screen):
        self.screen = screen
        self.tile_surfaces = {}
        self._create_tile_surfaces()
        
        # Load pixel art sprites
        self.sprites_loaded = False
        self.character_sprites = {}
        self.enemy_sprites = {}
        self.spell_sprites = {}
        self.item_sprites = {}
        self.environment_tiles = {}
        self._load_sprites()
    
    def _load_sprites(self):
        """Load all pixel art sprites."""
        if not SPRITES_AVAILABLE:
            print("[Renderer] Sprite system not available, using placeholders")
            return
        
        try:
            # Character sprites
            self.character_sprites['hero'] = get_hero_sprites()
            self.character_sprites['mage'] = get_mage_sprites()
            
            # Enemy sprites
            self.enemy_sprites['skeleton'] = get_skeleton_sprites()
            self.enemy_sprites['spider'] = get_spider_sprites()
            self.enemy_sprites['zombie'] = get_zombie_sprites()
            self.enemy_sprites['orc'] = get_orc_sprites()
            self.enemy_sprites['demon'] = get_demon_sprites()
            
            # Spell effects
            self.spell_sprites = get_spell_sprites()
            self.spell_effect_sprites = get_spell_effect_sprites()
            
            # Items
            self.item_sprites = get_item_sprites()
            self.weapon_sprites = get_weapon_sprites()
            self.armor_sprites = get_armor_sprites()
            
            # Environment
            self.environment_tiles = get_environment_tiles()
            self.sprites_loaded = True
            
            # Apply Indian temple theme to tiles
            self._update_tiles_with_sprites()
            
            print("[Renderer] Loaded pixel art sprites (Indian temple theme)!")
        except Exception as e:
            print(f"[Renderer] Failed to load sprites: {e}")
            import traceback
            traceback.print_exc()
            self.sprites_loaded = False
    
    def _create_tile_surfaces(self):
        """Pre-render tile surfaces - will be replaced with Indian temple sprites if available."""
        # Fallback tiles (used if sprites not loaded)
        # Floor tile - sandstone base
        self.tile_surfaces[TILE_FLOOR] = self._create_diamond_tile(
            (210, 180, 140), (170, 140, 100), (235, 210, 175)
        )
        
        # Wall tile - terracotta
        self.tile_surfaces[TILE_WALL] = self._create_wall_tile(
            (180, 100, 70), (140, 70, 50), (200, 120, 90)
        )
        
        # Door tile - wood with gold trim
        self.tile_surfaces[TILE_DOOR] = self._create_diamond_tile(
            (139, 90, 43), (100, 60, 30), (170, 120, 60)
        )
        
        # Water tile - teal temple pool
        self.tile_surfaces[TILE_WATER] = self._create_diamond_tile(
            (60, 140, 140), (40, 100, 100), (80, 160, 160)
        )
        
        # Lava tile - orange/saffron
        self.tile_surfaces[TILE_LAVA] = self._create_diamond_tile(
            (220, 130, 40), (180, 100, 30), (255, 160, 50)
        )
        
        # Stairs down - golden temple stairs
        self.tile_surfaces[TILE_STAIRS_DOWN] = self._create_stairs_tile()
        
        # Stairs up - bluish to distinguish from down
        self.tile_surfaces[TILE_STAIRS_UP] = self._create_stairs_up_tile()
    
    def _update_tiles_with_sprites(self):
        """Update tile surfaces with pixel art sprites if available."""
        if not self.sprites_loaded or not self.environment_tiles:
            return
        
        # Replace tiles with Indian temple versions
        if 'floor' in self.environment_tiles:
            floor_sprite = self.environment_tiles['floor']
            self.tile_surfaces[TILE_FLOOR] = self._sprite_to_isometric(floor_sprite)
        
        if 'wall' in self.environment_tiles:
            wall_sprite = self.environment_tiles['wall']
            self.tile_surfaces[TILE_WALL] = self._sprite_to_isometric_wall(wall_sprite)
        
        if 'door' in self.environment_tiles:
            door_sprite = self.environment_tiles['door']
            self.tile_surfaces[TILE_DOOR] = self._sprite_to_isometric(door_sprite)
        
        if 'water' in self.environment_tiles:
            water_sheet = self.environment_tiles['water']
            if hasattr(water_sheet, 'get_frame'):
                self.tile_surfaces[TILE_WATER] = self._sprite_to_isometric(water_sheet.get_frame())
        
        # Keep procedural stairs for better visibility (they have glow effects)
        # The pixel art stairs are too flat when converted to isometric
        # self.tile_surfaces[TILE_STAIRS_DOWN] stays as procedural
        # self.tile_surfaces[TILE_STAIRS_UP] stays as procedural
        
        print("[Renderer] Applied Indian temple tile theme!")
    
    def _sprite_to_isometric(self, sprite):
        """Convert a square sprite to isometric diamond shape using proper projection."""
        sprite_size = sprite.get_width()
        
        # Create isometric surface (diamond shape)
        iso_surf = pygame.Surface((TILE_WIDTH, TILE_HEIGHT), pygame.SRCALPHA)
        
        # For each pixel in the isometric output, find the corresponding source pixel
        # Isometric projection: 
        #   iso_x = (src_x - src_y) * (TILE_WIDTH / 2 / sprite_size) + TILE_WIDTH/2
        #   iso_y = (src_x + src_y) * (TILE_HEIGHT / 2 / sprite_size)
        # Inverse:
        #   src_x = (iso_x - TILE_WIDTH/2) / (TILE_WIDTH/sprite_size) + (iso_y) / (TILE_HEIGHT/sprite_size)  
        #   src_y = (iso_y) / (TILE_HEIGHT/sprite_size) - (iso_x - TILE_WIDTH/2) / (TILE_WIDTH/sprite_size)
        
        half_w = TILE_WIDTH / 2
        half_h = TILE_HEIGHT / 2
        
        for iso_y in range(TILE_HEIGHT):
            for iso_x in range(TILE_WIDTH):
                # Convert isometric coords to source sprite coords
                # Normalized coordinates relative to center
                nx = (iso_x - half_w) / half_w  # -1 to 1
                ny = (iso_y - half_h) / half_h  # -1 to 1 (but tile height is half width)
                
                # Inverse isometric projection
                src_x = (nx + ny * 2) / 2  # -1 to 1 in source space
                src_y = (ny * 2 - nx) / 2  # -1 to 1 in source space
                
                # Convert to pixel coordinates
                px = int((src_x + 1) / 2 * (sprite_size - 1))
                py = int((src_y + 1) / 2 * (sprite_size - 1))
                
                # Check if within source sprite bounds
                if 0 <= px < sprite_size and 0 <= py < sprite_size:
                    try:
                        color = sprite.get_at((px, py))
                        if color[3] > 0:  # Not transparent
                            iso_surf.set_at((iso_x, iso_y), color)
                    except:
                        pass
        
        return iso_surf
    
    def _sprite_to_isometric_wall(self, sprite):
        """Convert a square sprite to isometric wall with height."""
        wall_height = TILE_HEIGHT * 2
        surface = pygame.Surface((TILE_WIDTH, TILE_HEIGHT + wall_height), pygame.SRCALPHA)
        
        # Draw top face (isometric diamond from sprite)
        top_face = self._sprite_to_isometric(sprite)
        surface.blit(top_face, (0, 0))
        
        # Sample colors from sprite for the wall sides
        sprite_size = sprite.get_width()
        try:
            # Get colors from left and right sides of sprite
            left_color = sprite.get_at((sprite_size // 4, sprite_size // 2))
            right_color = sprite.get_at((3 * sprite_size // 4, sprite_size // 2))
            # Darken for sides
            left_color = tuple(max(0, c - 40) for c in left_color[:3])
            right_color = tuple(max(0, c - 20) for c in right_color[:3])
        except:
            left_color = (140, 70, 50)
            right_color = (160, 90, 70)
        
        # Left face (darker)
        left_points = [
            (0, TILE_HEIGHT // 2),
            (TILE_WIDTH // 2, TILE_HEIGHT),
            (TILE_WIDTH // 2, TILE_HEIGHT + wall_height),
            (0, TILE_HEIGHT // 2 + wall_height),
        ]
        pygame.draw.polygon(surface, left_color, left_points)
        pygame.draw.polygon(surface, (30, 20, 15), left_points, 1)
        
        # Right face (lighter)
        right_points = [
            (TILE_WIDTH, TILE_HEIGHT // 2),
            (TILE_WIDTH // 2, TILE_HEIGHT),
            (TILE_WIDTH // 2, TILE_HEIGHT + wall_height),
            (TILE_WIDTH, TILE_HEIGHT // 2 + wall_height),
        ]
        pygame.draw.polygon(surface, right_color, right_points)
        pygame.draw.polygon(surface, (30, 20, 15), right_points, 1)
        
        # Add some texture lines to the wall faces
        for i in range(1, 4):
            y_offset = i * wall_height // 4
            # Left face horizontal line (darker)
            line_color_l = (max(0, left_color[0] - 20), max(0, left_color[1] - 20), max(0, left_color[2] - 20))
            pygame.draw.line(surface, line_color_l,
                           (2, TILE_HEIGHT // 2 + y_offset),
                           (TILE_WIDTH // 2 - 2, TILE_HEIGHT + y_offset), 1)
            # Right face horizontal line (lighter)
            line_color_r = (min(255, right_color[0] + 10), min(255, right_color[1] + 10), min(255, right_color[2] + 10))
            pygame.draw.line(surface, line_color_r,
                           (TILE_WIDTH // 2 + 2, TILE_HEIGHT + y_offset),
                           (TILE_WIDTH - 2, TILE_HEIGHT // 2 + y_offset), 1)
        
        return surface
    
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
        """Create stairs going down tile - bright green for visibility."""
        surface = pygame.Surface((TILE_WIDTH, TILE_HEIGHT + 16), pygame.SRCALPHA)
        
        # Base floor - brighter
        points = [
            (TILE_WIDTH // 2, 0),
            (TILE_WIDTH, TILE_HEIGHT // 2),
            (TILE_WIDTH // 2, TILE_HEIGHT),
            (0, TILE_HEIGHT // 2),
        ]
        pygame.draw.polygon(surface, (50, 70, 50), points)
        
        # Draw stair steps going "down" - greenish
        step_colors = [(70, 100, 70), (60, 90, 60), (50, 80, 50), (40, 70, 40)]
        for i, color in enumerate(step_colors):
            offset_y = i * 3 + 4
            step_points = [
                (TILE_WIDTH // 2, offset_y),
                (TILE_WIDTH - 8 - i * 4, TILE_HEIGHT // 2 + offset_y // 2),
                (TILE_WIDTH // 2, TILE_HEIGHT - 4 + offset_y // 2),
                (8 + i * 4, TILE_HEIGHT // 2 + offset_y // 2),
            ]
            pygame.draw.polygon(surface, color, step_points)
        
        # Bright green glow for visibility
        pygame.draw.polygon(surface, (100, 255, 100), points, 3)
        
        # Arrow pointing down
        arrow_points = [
            (TILE_WIDTH // 2, TILE_HEIGHT - 2),
            (TILE_WIDTH // 2 - 6, TILE_HEIGHT - 10),
            (TILE_WIDTH // 2 + 6, TILE_HEIGHT - 10),
        ]
        pygame.draw.polygon(surface, (150, 255, 150), arrow_points)
        
        return surface
    
    def _create_stairs_up_tile(self):
        """Create stairs going up tile - bright blue for visibility."""
        surface = pygame.Surface((TILE_WIDTH, TILE_HEIGHT + 16), pygame.SRCALPHA)
        
        # Base floor - brighter blue
        points = [
            (TILE_WIDTH // 2, 0),
            (TILE_WIDTH, TILE_HEIGHT // 2),
            (TILE_WIDTH // 2, TILE_HEIGHT),
            (0, TILE_HEIGHT // 2),
        ]
        pygame.draw.polygon(surface, (50, 50, 80), points)
        
        # Draw stair steps going "up" - bluish
        step_colors = [(60, 80, 120), (70, 90, 130), (80, 100, 140), (90, 110, 150)]
        for i, color in enumerate(step_colors):
            offset_y = (3 - i) * 3 + 4
            step_points = [
                (TILE_WIDTH // 2, offset_y),
                (TILE_WIDTH - 8 - (3 - i) * 4, TILE_HEIGHT // 2 + offset_y // 2),
                (TILE_WIDTH // 2, TILE_HEIGHT - 4 + offset_y // 2),
                (8 + (3 - i) * 4, TILE_HEIGHT // 2 + offset_y // 2),
            ]
            pygame.draw.polygon(surface, color, step_points)
        
        # Bright blue glow for visibility
        pygame.draw.polygon(surface, (100, 150, 255), points, 3)
        
        # Arrow pointing up
        arrow_points = [
            (TILE_WIDTH // 2, 4),
            (TILE_WIDTH // 2 - 6, 12),
            (TILE_WIDTH // 2 + 6, 12),
        ]
        pygame.draw.polygon(surface, (150, 200, 255), arrow_points)
        
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
                        # Scale the tile
                        scaled_w = round(surface.get_width() * camera.zoom)
                        scaled_h = round(surface.get_height() * camera.zoom)
                        
                        if camera.zoom != 1.0:
                            scaled = pygame.transform.scale(surface, (scaled_w, scaled_h))
                        else:
                            scaled = surface
                        
                        # Position: center horizontally, anchor bottom at tile position
                        # For floors: bottom of diamond aligns with screen_y
                        # For walls: bottom of wall base aligns with screen_y
                        draw_x = round(screen_x - scaled_w / 2)
                        
                        if tile_type == TILE_WALL:
                            # Wall is taller - the bottom diamond should align with floor position
                            # Wall surface is TILE_HEIGHT * 3 tall (base TILE_HEIGHT + 2*TILE_HEIGHT wall)
                            # We want the bottom of the wall (at TILE_HEIGHT from bottom) to align
                            draw_y = round(screen_y - scaled_h + round(TILE_HEIGHT * camera.zoom / 2))
                        else:
                            # Floor tiles: center the diamond vertically
                            draw_y = round(screen_y - scaled_h / 2)
                        
                        self.screen.blit(scaled, (draw_x, draw_y))
    
    def render_entity(self, entity, camera, dt=0.016):
        """Render an entity at its world position."""
        screen_x, screen_y = camera.world_to_screen(entity.x, entity.y)
        
        # Sprite size scales with zoom
        base_size = 32
        size = int(base_size * camera.zoom)
        
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
        
        # Try to use pixel art sprites
        sprite_drawn = False
        if self.sprites_loaded:
            sprite_drawn = self._draw_entity_sprite(entity, screen_x, screen_y, size, dt, is_downed)
        
        # Fallback to placeholder if no sprite
        if not sprite_drawn:
            self._draw_entity_placeholder(entity, screen_x, screen_y, size, is_downed)
        
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
    
    def _draw_entity_sprite(self, entity, screen_x, screen_y, size, dt, is_downed):
        """Draw entity using pixel art sprites. Returns True if sprite was drawn."""
        sprites = None
        anim_name = 'idle'
        
        # Determine which sprite set to use
        if hasattr(entity, 'is_player_controlled'):
            # It's a character (hero or ally)
            if getattr(entity, 'is_player_controlled', False):
                sprites = self.character_sprites.get('hero')
            else:
                char_class = getattr(entity, 'char_class', 'mage')
                sprites = self.character_sprites.get(char_class, self.character_sprites.get('mage'))
        else:
            # It's an enemy
            enemy_type = getattr(entity, 'enemy_type', 'skeleton')
            sprites = self.enemy_sprites.get(enemy_type, self.enemy_sprites.get('skeleton'))
        
        if not sprites:
            return False
        
        # Determine animation state
        if is_downed:
            anim_name = 'death'
        elif getattr(entity, 'is_moving', False):
            anim_name = 'walk'
        elif getattr(entity, 'attack_cooldown', 0) > 0.3:
            if hasattr(entity, 'spellbook'):
                anim_name = 'cast'
            else:
                anim_name = 'attack'
        
        # Get the animation
        anim = sprites.get(anim_name, sprites.get('idle'))
        if not anim:
            return False
        
        # Update animation
        anim.update(dt)
        
        # Get current frame
        frame = anim.get_frame()
        if not frame:
            return False
        
        # Scale sprite
        if size != 32:
            frame = pygame.transform.scale(frame, (size, size))
        
        # Draw sprite centered
        sprite_rect = frame.get_rect(center=(screen_x, screen_y - size // 2))
        self.screen.blit(frame, sprite_rect)
        
        return True
    
    def _draw_entity_placeholder(self, entity, screen_x, screen_y, size, is_downed):
        """Draw placeholder ellipse for entity."""
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

