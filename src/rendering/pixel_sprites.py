"""
Pixel Art Sprite Generator
Generates all game sprites procedurally using pygame drawing.
Each sprite is 32x32 pixels for characters, 16x16 for items.
"""

import pygame
import math

# Sprite sizes
CHAR_SIZE = 32  # Standard characters are 32x32
HERO_SIZE = 48  # Hero and mage are 48x48 (larger, more detailed)
ITEM_SIZE = 16  # Items are 16x16
TILE_SIZE = 32  # Tiles are 32x32

# Color palettes
PALETTE = {
    # Skin tones (Indian)
    'skin_light': (200, 160, 120),
    'skin_mid': (170, 130, 95),
    'skin_shadow': (140, 100, 70),
    
    # Hero colors - Indian Warrior Theme
    'hero_gold': (255, 200, 60),
    'hero_gold_light': (255, 230, 120),
    'hero_gold_dark': (200, 150, 30),
    'hero_red': (180, 50, 40),
    'hero_red_light': (220, 80, 60),
    'hero_red_dark': (120, 30, 25),
    'hero_saffron': (230, 140, 50),
    'hero_white': (250, 245, 235),
    'hero_armor': (80, 90, 110),  # Silver/steel parts
    'hero_armor_light': (140, 150, 170),
    'hero_armor_dark': (50, 55, 70),
    'hero_cape': (180, 50, 50),
    'hero_cape_dark': (120, 30, 30),
    
    # Mage colors - Indian Mystic Theme
    'mage_robe': (60, 50, 120),  # Deep blue/purple
    'mage_robe_light': (90, 80, 160),
    'mage_robe_dark': (35, 30, 80),
    'mage_trim': (200, 170, 80),  # Gold trim
    'mage_gold': (230, 190, 90),
    'mage_gold_light': (255, 220, 130),
    'mage_gold_dark': (180, 140, 60),
    'mage_blue_gem': (100, 180, 255),
    'mage_blue_glow': (150, 210, 255),
    'mage_blue_dark': (60, 120, 200),
    'mage_hair': (220, 180, 100),  # Golden blonde
    'mage_hair_dark': (180, 140, 70),
    'peacock_green': (40, 140, 100),
    'peacock_blue': (50, 100, 180),
    
    # Enemy - Skeleton
    'bone': (240, 235, 220),
    'bone_shadow': (180, 170, 150),
    'bone_dark': (120, 110, 100),
    
    # Enemy - Zombie  
    'zombie_skin': (120, 140, 100),
    'zombie_dark': (80, 100, 60),
    'zombie_wound': (100, 50, 50),
    
    # Enemy - Spider
    'spider_body': (40, 35, 30),
    'spider_light': (70, 60, 50),
    'spider_eyes': (200, 50, 50),
    
    # Enemy - Orc
    'orc_skin': (100, 140, 80),
    'orc_dark': (70, 100, 50),
    'orc_armor': (80, 70, 60),
    
    # Enemy - Demon
    'demon_skin': (160, 50, 50),
    'demon_dark': (100, 30, 30),
    'demon_horns': (60, 40, 40),
    
    # Weapons
    'steel': (180, 185, 190),
    'steel_light': (220, 225, 230),
    'steel_dark': (120, 125, 130),
    'wood': (139, 90, 43),
    'wood_dark': (100, 60, 30),
    'gold': (255, 215, 0),
    'gold_dark': (200, 160, 0),
    
    # Magic
    'fire': (255, 100, 30),
    'fire_light': (255, 200, 100),
    'fire_dark': (180, 50, 20),
    'ice': (150, 200, 255),
    'ice_light': (200, 230, 255),
    'ice_dark': (100, 150, 200),
    'lightning': (200, 200, 255),
    'heal': (100, 255, 100),
    'poison': (100, 180, 50),
    
    # Environment - Indian Temple Theme
    'sandstone': (210, 180, 140),
    'sandstone_light': (235, 210, 175),
    'sandstone_dark': (170, 140, 100),
    'terracotta': (180, 100, 70),
    'terracotta_dark': (140, 70, 50),
    'temple_gold': (200, 165, 80),
    'temple_gold_light': (230, 200, 120),
    'temple_teal': (60, 140, 140),
    'temple_teal_dark': (40, 100, 100),
    'temple_red': (160, 50, 50),
    'temple_saffron': (220, 130, 40),
    'lotus_pink': (230, 150, 170),
    'lotus_white': (250, 245, 240),
    'marble': (240, 235, 230),
    'marble_vein': (200, 195, 190),
}


class SpriteSheet:
    """Container for animated sprite frames."""
    
    def __init__(self, frames, frame_duration=0.15):
        self.frames = frames  # List of pygame surfaces
        self.frame_duration = frame_duration
        self.current_frame = 0
        self.elapsed = 0
    
    def update(self, dt):
        self.elapsed += dt
        if self.elapsed >= self.frame_duration:
            self.elapsed = 0
            self.current_frame = (self.current_frame + 1) % len(self.frames)
    
    def get_frame(self):
        return self.frames[self.current_frame]
    
    def reset(self):
        self.current_frame = 0
        self.elapsed = 0


class DirectionalSpriteSheet:
    """Container for directional animated sprites (4 directions)."""
    
    def __init__(self, direction_frames, frame_duration=0.15):
        """
        direction_frames: dict with keys 0,1,2,3 (down,left,right,up)
                         each value is a list of frames
        """
        self.direction_frames = direction_frames
        self.frame_duration = frame_duration
        self.current_frame = 0
        self.current_direction = 0
        self.elapsed = 0
    
    def update(self, dt):
        self.elapsed += dt
        if self.elapsed >= self.frame_duration:
            self.elapsed = 0
            frames = self.direction_frames.get(self.current_direction, [])
            if frames:
                self.current_frame = (self.current_frame + 1) % len(frames)
    
    def set_direction(self, direction):
        """Set facing direction (0=down, 1=left, 2=right, 3=up)."""
        if direction != self.current_direction:
            self.current_direction = direction
            # Keep frame count but don't reset animation
    
    def get_frame(self, direction=None):
        """Get current frame for specified or current direction."""
        if direction is not None:
            self.set_direction(direction)
        frames = self.direction_frames.get(self.current_direction, [])
        if not frames:
            return None
        return frames[self.current_frame % len(frames)]
    
    def reset(self):
        self.current_frame = 0
        self.elapsed = 0


class PixelSpriteGenerator:
    """Generates all game sprites programmatically."""
    
    def __init__(self):
        self.cache = {}
    
    def _create_surface(self, size=CHAR_SIZE):
        """Create a transparent surface."""
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        return surf
    
    def _draw_pixel(self, surf, x, y, color):
        """Draw a single pixel."""
        if 0 <= x < surf.get_width() and 0 <= y < surf.get_height():
            surf.set_at((x, y), color)
    
    def _draw_rect(self, surf, x, y, w, h, color):
        """Draw a filled rectangle."""
        pygame.draw.rect(surf, color, (x, y, w, h))
    
    def _draw_outline_rect(self, surf, x, y, w, h, color):
        """Draw rectangle outline."""
        pygame.draw.rect(surf, color, (x, y, w, h), 1)
    
    # ==================== HERO SPRITES ====================
    
    def hero_idle(self, frame=0):
        """Hero idle animation - Indian warrior with crown, shield, and flaming sword."""
        surf = self._create_surface(HERO_SIZE)
        
        # Animation offset (subtle breathing)
        y_off = 1 if frame % 2 == 0 else 0
        flame_flicker = 2 if frame % 3 == 0 else (1 if frame % 3 == 1 else 0)
        
        # === CAPE (behind everything) ===
        # Flowing red cape
        self._draw_rect(surf, 10, 24 + y_off, 6, 18, PALETTE['hero_red'])
        self._draw_rect(surf, 11, 26 + y_off, 5, 16, PALETTE['hero_red_dark'])
        self._draw_rect(surf, 32, 24 + y_off, 6, 18, PALETTE['hero_red'])
        self._draw_rect(surf, 33, 26 + y_off, 4, 16, PALETTE['hero_red_dark'])
        # Cape flowing part
        self._draw_rect(surf, 6, 30 + y_off, 4, 12, PALETTE['hero_red'])
        self._draw_rect(surf, 38, 30 + y_off, 4, 12, PALETTE['hero_red'])
        
        # === LEGS ===
        # White dhoti/pants
        self._draw_rect(surf, 17, 34 + y_off, 6, 10, PALETTE['hero_white'])
        self._draw_rect(surf, 25, 34 + y_off, 6, 10, PALETTE['hero_white'])
        # Gold shin guards
        self._draw_rect(surf, 17, 38 + y_off, 6, 6, PALETTE['hero_gold_dark'])
        self._draw_rect(surf, 18, 39 + y_off, 4, 4, PALETTE['hero_gold'])
        self._draw_rect(surf, 25, 38 + y_off, 6, 6, PALETTE['hero_gold_dark'])
        self._draw_rect(surf, 26, 39 + y_off, 4, 4, PALETTE['hero_gold'])
        # Feet
        self._draw_rect(surf, 16, 44 + y_off, 7, 3, PALETTE['hero_armor_dark'])
        self._draw_rect(surf, 25, 44 + y_off, 7, 3, PALETTE['hero_armor_dark'])
        
        # === BODY/TORSO ===
        # Chest armor - silver/gold with red sash
        self._draw_rect(surf, 15, 22 + y_off, 18, 12, PALETTE['hero_armor'])
        self._draw_rect(surf, 16, 23 + y_off, 16, 10, PALETTE['hero_armor_light'])
        # Gold trim on chest
        self._draw_rect(surf, 15, 22 + y_off, 18, 2, PALETTE['hero_gold'])
        self._draw_rect(surf, 22, 24 + y_off, 4, 8, PALETTE['hero_gold'])  # Center gold stripe
        # Red sash across torso
        self._draw_rect(surf, 14, 28 + y_off, 20, 4, PALETTE['hero_red'])
        self._draw_rect(surf, 15, 29 + y_off, 18, 2, PALETTE['hero_saffron'])
        # Gold belt
        self._draw_rect(surf, 15, 32 + y_off, 18, 3, PALETTE['hero_gold'])
        self._draw_rect(surf, 16, 33 + y_off, 16, 1, PALETTE['hero_gold_light'])
        # Belt jewel
        self._draw_rect(surf, 22, 32 + y_off, 4, 3, PALETTE['hero_red'])
        
        # === SHOULDER ARMOR ===
        # Left shoulder
        self._draw_rect(surf, 10, 20 + y_off, 7, 6, PALETTE['hero_gold_dark'])
        self._draw_rect(surf, 11, 21 + y_off, 5, 4, PALETTE['hero_gold'])
        # Right shoulder
        self._draw_rect(surf, 31, 20 + y_off, 7, 6, PALETTE['hero_gold_dark'])
        self._draw_rect(surf, 32, 21 + y_off, 5, 4, PALETTE['hero_gold'])
        
        # === ARMS ===
        # Left arm (holding shield)
        self._draw_rect(surf, 8, 26 + y_off, 5, 10, PALETTE['hero_armor'])
        self._draw_rect(surf, 9, 27 + y_off, 3, 8, PALETTE['skin_mid'])
        # Right arm (holding sword)
        self._draw_rect(surf, 35, 26 + y_off, 5, 10, PALETTE['hero_armor'])
        self._draw_rect(surf, 36, 27 + y_off, 3, 8, PALETTE['skin_mid'])
        # Hands
        self._draw_rect(surf, 7, 35 + y_off, 5, 4, PALETTE['skin_light'])
        self._draw_rect(surf, 36, 35 + y_off, 5, 4, PALETTE['skin_light'])
        
        # === SHIELD (left side) ===
        # Shield base - dark with gold trim
        self._draw_rect(surf, 2, 24 + y_off, 12, 16, PALETTE['hero_armor_dark'])
        self._draw_rect(surf, 3, 25 + y_off, 10, 14, PALETTE['hero_armor'])
        # Gold shield rim
        self._draw_outline_rect(surf, 2, 24 + y_off, 12, 16, PALETTE['hero_gold'])
        self._draw_outline_rect(surf, 3, 25 + y_off, 10, 14, PALETTE['hero_gold_dark'])
        # Sun emblem on shield
        self._draw_rect(surf, 6, 29 + y_off, 4, 4, PALETTE['hero_gold'])
        self._draw_rect(surf, 7, 30 + y_off, 2, 2, PALETTE['hero_saffron'])
        # Sun rays
        self._draw_pixel(surf, 8, 27 + y_off, PALETTE['hero_gold'])
        self._draw_pixel(surf, 8, 35 + y_off, PALETTE['hero_gold'])
        self._draw_pixel(surf, 4, 31 + y_off, PALETTE['hero_gold'])
        self._draw_pixel(surf, 12, 31 + y_off, PALETTE['hero_gold'])
        
        # === HEAD ===
        # Face
        self._draw_rect(surf, 18, 10 + y_off, 12, 12, PALETTE['skin_light'])
        self._draw_rect(surf, 19, 11 + y_off, 10, 10, PALETTE['skin_mid'])
        # Eyes
        self._draw_rect(surf, 20, 14 + y_off, 3, 2, (40, 30, 20))
        self._draw_rect(surf, 25, 14 + y_off, 3, 2, (40, 30, 20))
        self._draw_pixel(surf, 21, 14 + y_off, (255, 255, 255))
        self._draw_pixel(surf, 26, 14 + y_off, (255, 255, 255))
        # Nose
        self._draw_rect(surf, 23, 16 + y_off, 2, 3, PALETTE['skin_shadow'])
        # Mouth
        self._draw_rect(surf, 22, 19 + y_off, 4, 1, PALETTE['skin_shadow'])
        
        # === CROWN/HEADDRESS ===
        # Main crown base - gold
        self._draw_rect(surf, 16, 6 + y_off, 16, 6, PALETTE['hero_gold'])
        self._draw_rect(surf, 17, 7 + y_off, 14, 4, PALETTE['hero_gold_light'])
        # Crown points
        self._draw_rect(surf, 18, 3 + y_off, 3, 4, PALETTE['hero_gold'])
        self._draw_rect(surf, 22, 1 + y_off, 4, 6, PALETTE['hero_gold'])  # Center tallest
        self._draw_rect(surf, 27, 3 + y_off, 3, 4, PALETTE['hero_gold'])
        # Sun disk behind head
        self._draw_rect(surf, 14, 4 + y_off, 3, 10, PALETTE['hero_gold_dark'])
        self._draw_rect(surf, 31, 4 + y_off, 3, 10, PALETTE['hero_gold_dark'])
        # Red jewel in crown
        self._draw_rect(surf, 23, 2 + y_off, 2, 2, PALETTE['hero_red'])
        self._draw_rect(surf, 23, 8 + y_off, 2, 2, PALETTE['hero_red'])
        # Red plume/hair
        self._draw_rect(surf, 30, 2 + y_off, 4, 3, PALETTE['hero_red'])
        self._draw_rect(surf, 32, 1 + y_off, 5, 4, PALETTE['hero_red_light'])
        self._draw_rect(surf, 35, 0 + y_off, 6, 3, PALETTE['hero_red'])
        self._draw_rect(surf, 38, 2 + y_off, 5, 4, PALETTE['hero_red_dark'])
        
        # === FLAMING SWORD (right side) ===
        # Blade - gold/steel
        self._draw_rect(surf, 40, 8 + y_off + flame_flicker, 3, 22, PALETTE['hero_gold'])
        self._draw_rect(surf, 41, 10 + y_off + flame_flicker, 1, 18, PALETTE['hero_gold_light'])
        # Hilt
        self._draw_rect(surf, 38, 30 + y_off, 7, 3, PALETTE['hero_gold_dark'])
        self._draw_rect(surf, 40, 33 + y_off, 3, 5, PALETTE['wood'])
        # Flames on blade
        self._draw_rect(surf, 38 + flame_flicker, 5 + y_off, 3, 5, PALETTE['fire'])
        self._draw_rect(surf, 42 - flame_flicker, 4 + y_off, 2, 4, PALETTE['fire'])
        self._draw_rect(surf, 39, 7 + y_off + flame_flicker, 2, 3, PALETTE['fire_light'])
        self._draw_rect(surf, 43, 6 + y_off + flame_flicker, 2, 3, PALETTE['fire_light'])
        # More flame particles
        self._draw_pixel(surf, 37 + flame_flicker, 3 + y_off, PALETTE['fire_light'])
        self._draw_pixel(surf, 44 - flame_flicker, 2 + y_off, PALETTE['fire'])
        self._draw_pixel(surf, 40, 3 + y_off + flame_flicker, PALETTE['fire'])
        
        # === JEWELRY/DETAILS ===
        # Necklace
        self._draw_rect(surf, 19, 22 + y_off, 10, 1, PALETTE['hero_gold'])
        # Rudraksha beads on necklace
        self._draw_pixel(surf, 21, 22 + y_off, (100, 70, 50))
        self._draw_pixel(surf, 24, 22 + y_off, (100, 70, 50))
        self._draw_pixel(surf, 27, 22 + y_off, (100, 70, 50))
        # Earrings
        self._draw_rect(surf, 17, 14 + y_off, 2, 3, PALETTE['hero_gold'])
        self._draw_rect(surf, 29, 14 + y_off, 2, 3, PALETTE['hero_gold'])
        
        return surf
    
    def hero_walk(self, frame=0, direction=0):
        """Hero walk animation - Indian warrior. direction: 0=down, 1=left, 2=right, 3=up"""
        surf = self._create_surface(HERO_SIZE)
        
        # Leg animation
        leg_offsets = [(0, 0), (3, -1), (0, 0), (-3, -1)]
        l_off, r_off = leg_offsets[frame % 4], leg_offsets[(frame + 2) % 4]
        y_off = 1 if frame % 2 == 0 else 0
        flame_flicker = frame % 3
        cape_flow = frame % 4
        arm_swing = [0, 3, 0, -3][frame % 4]
        
        if direction == 0:  # DOWN - facing camera
            self._draw_hero_walk_down(surf, y_off, l_off, r_off, cape_flow, arm_swing, flame_flicker)
        elif direction == 1:  # LEFT - facing left
            self._draw_hero_walk_left(surf, y_off, l_off, r_off, cape_flow, arm_swing, flame_flicker)
        elif direction == 2:  # RIGHT - facing right
            self._draw_hero_walk_right(surf, y_off, l_off, r_off, cape_flow, arm_swing, flame_flicker)
        else:  # UP - facing away
            self._draw_hero_walk_up(surf, y_off, l_off, r_off, cape_flow, arm_swing, flame_flicker)
        
        return surf
    
    def _draw_hero_walk_down(self, surf, y_off, l_off, r_off, cape_flow, arm_swing, flame_flicker):
        """Hero walking towards camera (down)."""
        # Cape behind
        self._draw_rect(surf, 8 - cape_flow, 24 + y_off, 6, 16 + cape_flow, PALETTE['hero_red'])
        self._draw_rect(surf, 34 + cape_flow // 2, 24 + y_off, 6, 16 + cape_flow, PALETTE['hero_red'])
        
        # Legs
        self._draw_rect(surf, 17 + l_off[0], 34 + y_off + l_off[1], 6, 10, PALETTE['hero_white'])
        self._draw_rect(surf, 25 + r_off[0], 34 + y_off + r_off[1], 6, 10, PALETTE['hero_white'])
        self._draw_rect(surf, 17 + l_off[0], 38 + y_off + l_off[1], 6, 6, PALETTE['hero_gold'])
        self._draw_rect(surf, 25 + r_off[0], 38 + y_off + r_off[1], 6, 6, PALETTE['hero_gold'])
        self._draw_rect(surf, 16 + l_off[0], 44 + y_off, 7, 3, PALETTE['hero_armor_dark'])
        self._draw_rect(surf, 25 + r_off[0], 44 + y_off, 7, 3, PALETTE['hero_armor_dark'])
        
        # Body
        self._draw_rect(surf, 15, 22 + y_off, 18, 12, PALETTE['hero_armor'])
        self._draw_rect(surf, 16, 23 + y_off, 16, 10, PALETTE['hero_armor_light'])
        self._draw_rect(surf, 15, 22 + y_off, 18, 2, PALETTE['hero_gold'])
        self._draw_rect(surf, 22, 24 + y_off, 4, 8, PALETTE['hero_gold'])
        self._draw_rect(surf, 14, 28 + y_off, 20, 4, PALETTE['hero_red'])
        self._draw_rect(surf, 15, 32 + y_off, 18, 3, PALETTE['hero_gold'])
        
        # Shoulders & Arms
        self._draw_rect(surf, 10, 20 + y_off, 7, 6, PALETTE['hero_gold'])
        self._draw_rect(surf, 31, 20 + y_off, 7, 6, PALETTE['hero_gold'])
        self._draw_rect(surf, 8, 26 + y_off - arm_swing, 5, 10, PALETTE['hero_armor'])
        self._draw_rect(surf, 35, 26 + y_off + arm_swing, 5, 10, PALETTE['hero_armor'])
        self._draw_rect(surf, 7, 35 + y_off - arm_swing, 5, 4, PALETTE['skin_light'])
        self._draw_rect(surf, 36, 35 + y_off + arm_swing, 5, 4, PALETTE['skin_light'])
        
        # Shield (left)
        self._draw_rect(surf, 2, 24 + y_off - arm_swing, 12, 16, PALETTE['hero_armor_dark'])
        self._draw_rect(surf, 3, 25 + y_off - arm_swing, 10, 14, PALETTE['hero_armor'])
        self._draw_outline_rect(surf, 2, 24 + y_off - arm_swing, 12, 16, PALETTE['hero_gold'])
        self._draw_rect(surf, 6, 29 + y_off - arm_swing, 4, 4, PALETTE['hero_gold'])
        
        # Head with face
        self._draw_rect(surf, 18, 10 + y_off, 12, 12, PALETTE['skin_light'])
        self._draw_rect(surf, 19, 11 + y_off, 10, 10, PALETTE['skin_mid'])
        self._draw_rect(surf, 20, 14 + y_off, 3, 2, (40, 30, 20))  # Eyes
        self._draw_rect(surf, 25, 14 + y_off, 3, 2, (40, 30, 20))
        
        # Crown
        self._draw_rect(surf, 16, 6 + y_off, 16, 6, PALETTE['hero_gold'])
        self._draw_rect(surf, 22, 1 + y_off, 4, 6, PALETTE['hero_gold'])
        self._draw_rect(surf, 23, 2 + y_off, 2, 2, PALETTE['hero_red'])
        self._draw_rect(surf, 30 + cape_flow // 2, 2 + y_off, 8, 4, PALETTE['hero_red'])
        
        # Flaming Sword (right)
        self._draw_rect(surf, 40, 8 + y_off + arm_swing + flame_flicker, 3, 22, PALETTE['hero_gold'])
        self._draw_rect(surf, 38, 30 + y_off + arm_swing, 7, 3, PALETTE['hero_gold_dark'])
        self._draw_rect(surf, 38 + flame_flicker, 4 + y_off + arm_swing, 3, 5, PALETTE['fire'])
        self._draw_rect(surf, 42 - flame_flicker, 3 + y_off + arm_swing, 2, 4, PALETTE['fire_light'])
    
    def _draw_hero_walk_left(self, surf, y_off, l_off, r_off, cape_flow, arm_swing, flame_flicker):
        """Hero walking left - side view with shield forward."""
        # Cape flowing right (behind)
        self._draw_rect(surf, 30 + cape_flow, 22 + y_off, 10 + cape_flow, 20, PALETTE['hero_red'])
        self._draw_rect(surf, 32 + cape_flow, 24 + y_off, 8 + cape_flow, 16, PALETTE['hero_red_dark'])
        
        # Legs (side view - one in front of other)
        self._draw_rect(surf, 20 + r_off[0], 34 + y_off + r_off[1], 8, 10, PALETTE['hero_white'])  # Back leg
        self._draw_rect(surf, 20 + r_off[0], 38 + y_off + r_off[1], 8, 6, PALETTE['hero_gold'])
        self._draw_rect(surf, 18 + l_off[0], 34 + y_off + l_off[1], 8, 10, PALETTE['hero_white'])  # Front leg
        self._draw_rect(surf, 18 + l_off[0], 38 + y_off + l_off[1], 8, 6, PALETTE['hero_gold'])
        self._draw_rect(surf, 17 + l_off[0], 44 + y_off, 10, 3, PALETTE['hero_armor_dark'])
        
        # Body (side view - narrower)
        self._draw_rect(surf, 18, 22 + y_off, 12, 12, PALETTE['hero_armor'])
        self._draw_rect(surf, 19, 23 + y_off, 10, 10, PALETTE['hero_armor_light'])
        self._draw_rect(surf, 18, 22 + y_off, 12, 2, PALETTE['hero_gold'])
        self._draw_rect(surf, 17, 28 + y_off, 14, 4, PALETTE['hero_red'])
        self._draw_rect(surf, 18, 32 + y_off, 12, 3, PALETTE['hero_gold'])
        
        # Shoulder
        self._draw_rect(surf, 16, 20 + y_off, 10, 5, PALETTE['hero_gold'])
        
        # Arm with shield (front - prominent)
        self._draw_rect(surf, 8, 24 + y_off, 12, 18, PALETTE['hero_armor_dark'])  # Shield
        self._draw_rect(surf, 9, 25 + y_off, 10, 16, PALETTE['hero_armor'])
        self._draw_outline_rect(surf, 8, 24 + y_off, 12, 18, PALETTE['hero_gold'])
        self._draw_rect(surf, 12, 30 + y_off, 4, 4, PALETTE['hero_gold'])  # Sun emblem
        self._draw_rect(surf, 13, 31 + y_off, 2, 2, PALETTE['hero_saffron'])
        
        # Head (side profile)
        self._draw_rect(surf, 18, 10 + y_off, 10, 12, PALETTE['skin_light'])
        self._draw_rect(surf, 19, 11 + y_off, 8, 10, PALETTE['skin_mid'])
        self._draw_rect(surf, 18, 14 + y_off, 2, 2, (40, 30, 20))  # Eye
        self._draw_rect(surf, 16, 16 + y_off, 3, 2, PALETTE['skin_shadow'])  # Nose
        
        # Crown (side)
        self._draw_rect(surf, 17, 6 + y_off, 12, 6, PALETTE['hero_gold'])
        self._draw_rect(surf, 21, 1 + y_off, 4, 6, PALETTE['hero_gold'])
        self._draw_rect(surf, 22, 2 + y_off, 2, 2, PALETTE['hero_red'])
        
        # Sword (behind/right - less visible)
        self._draw_rect(surf, 28, 12 + y_off + arm_swing, 3, 20, PALETTE['hero_gold'])
        self._draw_rect(surf, 27 + flame_flicker, 8 + y_off + arm_swing, 2, 4, PALETTE['fire'])
    
    def _draw_hero_walk_right(self, surf, y_off, l_off, r_off, cape_flow, arm_swing, flame_flicker):
        """Hero walking right - side view with sword forward."""
        # Cape flowing left (behind)
        self._draw_rect(surf, 4 - cape_flow, 22 + y_off, 10 + cape_flow, 20, PALETTE['hero_red'])
        self._draw_rect(surf, 6 - cape_flow, 24 + y_off, 8 + cape_flow, 16, PALETTE['hero_red_dark'])
        
        # Legs (side view)
        self._draw_rect(surf, 20 + l_off[0], 34 + y_off + l_off[1], 8, 10, PALETTE['hero_white'])
        self._draw_rect(surf, 20 + l_off[0], 38 + y_off + l_off[1], 8, 6, PALETTE['hero_gold'])
        self._draw_rect(surf, 22 + r_off[0], 34 + y_off + r_off[1], 8, 10, PALETTE['hero_white'])
        self._draw_rect(surf, 22 + r_off[0], 38 + y_off + r_off[1], 8, 6, PALETTE['hero_gold'])
        self._draw_rect(surf, 21 + r_off[0], 44 + y_off, 10, 3, PALETTE['hero_armor_dark'])
        
        # Body (side view)
        self._draw_rect(surf, 18, 22 + y_off, 12, 12, PALETTE['hero_armor'])
        self._draw_rect(surf, 19, 23 + y_off, 10, 10, PALETTE['hero_armor_light'])
        self._draw_rect(surf, 18, 22 + y_off, 12, 2, PALETTE['hero_gold'])
        self._draw_rect(surf, 17, 28 + y_off, 14, 4, PALETTE['hero_red'])
        self._draw_rect(surf, 18, 32 + y_off, 12, 3, PALETTE['hero_gold'])
        
        # Shoulder
        self._draw_rect(surf, 22, 20 + y_off, 10, 5, PALETTE['hero_gold'])
        
        # Shield (behind/left - less visible)
        self._draw_rect(surf, 12, 26 + y_off, 8, 12, PALETTE['hero_armor_dark'])
        self._draw_outline_rect(surf, 12, 26 + y_off, 8, 12, PALETTE['hero_gold'])
        
        # Head (side profile - facing right)
        self._draw_rect(surf, 20, 10 + y_off, 10, 12, PALETTE['skin_light'])
        self._draw_rect(surf, 21, 11 + y_off, 8, 10, PALETTE['skin_mid'])
        self._draw_rect(surf, 28, 14 + y_off, 2, 2, (40, 30, 20))  # Eye
        self._draw_rect(surf, 29, 16 + y_off, 3, 2, PALETTE['skin_shadow'])  # Nose
        
        # Crown (side)
        self._draw_rect(surf, 19, 6 + y_off, 12, 6, PALETTE['hero_gold'])
        self._draw_rect(surf, 23, 1 + y_off, 4, 6, PALETTE['hero_gold'])
        self._draw_rect(surf, 24, 2 + y_off, 2, 2, PALETTE['hero_red'])
        self._draw_rect(surf, 28, 4 + y_off, 6, 3, PALETTE['hero_red'])  # Plume
        
        # Flaming Sword (front - prominent)
        self._draw_rect(surf, 34, 8 + y_off + arm_swing + flame_flicker, 4, 26, PALETTE['hero_gold'])
        self._draw_rect(surf, 35, 10 + y_off + arm_swing + flame_flicker, 2, 22, PALETTE['hero_gold_light'])
        self._draw_rect(surf, 32, 32 + y_off + arm_swing, 8, 3, PALETTE['hero_gold_dark'])
        self._draw_rect(surf, 32 + flame_flicker, 4 + y_off + arm_swing, 4, 6, PALETTE['fire'])
        self._draw_rect(surf, 36 - flame_flicker, 2 + y_off + arm_swing, 3, 5, PALETTE['fire_light'])
        self._draw_rect(surf, 34, 0 + y_off + arm_swing + flame_flicker, 2, 4, PALETTE['fire'])
    
    def _draw_hero_walk_up(self, surf, y_off, l_off, r_off, cape_flow, arm_swing, flame_flicker):
        """Hero walking away from camera (up) - back view."""
        # Cape prominent (front in this view)
        self._draw_rect(surf, 12, 18 + y_off, 24, 26 + cape_flow, PALETTE['hero_red'])
        self._draw_rect(surf, 14, 20 + y_off, 20, 22 + cape_flow, PALETTE['hero_red_dark'])
        # Cape gold trim
        self._draw_rect(surf, 12, 18 + y_off, 2, 26 + cape_flow, PALETTE['hero_gold'])
        self._draw_rect(surf, 34, 18 + y_off, 2, 26 + cape_flow, PALETTE['hero_gold'])
        
        # Legs (back view)
        self._draw_rect(surf, 17 + l_off[0], 34 + y_off + l_off[1], 6, 10, PALETTE['hero_white'])
        self._draw_rect(surf, 25 + r_off[0], 34 + y_off + r_off[1], 6, 10, PALETTE['hero_white'])
        self._draw_rect(surf, 17 + l_off[0], 38 + y_off + l_off[1], 6, 6, PALETTE['hero_gold'])
        self._draw_rect(surf, 25 + r_off[0], 38 + y_off + r_off[1], 6, 6, PALETTE['hero_gold'])
        self._draw_rect(surf, 16 + l_off[0], 44 + y_off, 7, 3, PALETTE['hero_armor_dark'])
        self._draw_rect(surf, 25 + r_off[0], 44 + y_off, 7, 3, PALETTE['hero_armor_dark'])
        
        # Body (back)
        self._draw_rect(surf, 15, 22 + y_off, 18, 12, PALETTE['hero_armor'])
        self._draw_rect(surf, 16, 23 + y_off, 16, 10, PALETTE['hero_armor_dark'])
        self._draw_rect(surf, 15, 32 + y_off, 18, 3, PALETTE['hero_gold'])
        
        # Shoulders
        self._draw_rect(surf, 10, 20 + y_off, 7, 6, PALETTE['hero_gold'])
        self._draw_rect(surf, 31, 20 + y_off, 7, 6, PALETTE['hero_gold'])
        
        # Arms
        self._draw_rect(surf, 8, 26 + y_off - arm_swing, 5, 10, PALETTE['hero_armor'])
        self._draw_rect(surf, 35, 26 + y_off + arm_swing, 5, 10, PALETTE['hero_armor'])
        
        # Shield (back of left arm)
        self._draw_rect(surf, 4, 24 + y_off - arm_swing, 10, 14, PALETTE['hero_armor_dark'])
        self._draw_outline_rect(surf, 4, 24 + y_off - arm_swing, 10, 14, PALETTE['hero_gold'])
        
        # Head (back of head)
        self._draw_rect(surf, 18, 10 + y_off, 12, 12, PALETTE['skin_shadow'])
        
        # Crown (back)
        self._draw_rect(surf, 16, 6 + y_off, 16, 6, PALETTE['hero_gold'])
        self._draw_rect(surf, 17, 7 + y_off, 14, 4, PALETTE['hero_gold_dark'])
        self._draw_rect(surf, 22, 1 + y_off, 4, 6, PALETTE['hero_gold'])
        # Plume prominent from back
        self._draw_rect(surf, 28, 0 + y_off, 10, 6, PALETTE['hero_red'])
        self._draw_rect(surf, 30, 2 + y_off, 8, 4, PALETTE['hero_red_light'])
        
        # Sword (back of right arm)
        self._draw_rect(surf, 38, 10 + y_off + arm_swing, 3, 20, PALETTE['hero_gold'])
        self._draw_rect(surf, 37 + flame_flicker, 6 + y_off + arm_swing, 2, 4, PALETTE['fire'])
    
    def hero_attack(self, frame=0):
        """Hero flaming sword attack animation - Indian warrior."""
        surf = self._create_surface(HERO_SIZE)
        
        # Attack phases: wind up, swing, follow through
        phases = [
            {'sword_angle': -60, 'lean': 0},
            {'sword_angle': -20, 'lean': 2},
            {'sword_angle': 45, 'lean': 4},
            {'sword_angle': 90, 'lean': 3},
        ]
        phase = phases[min(frame, len(phases) - 1)]
        lean = phase['lean']
        
        # === CAPE (flowing back during attack) ===
        self._draw_rect(surf, 6 - frame, 24, 8, 18 + frame, PALETTE['hero_red'])
        self._draw_rect(surf, 4 - frame, 28, 6, 14 + frame, PALETTE['hero_red_dark'])
        
        # === LEGS ===
        self._draw_rect(surf, 17, 34, 6, 10, PALETTE['hero_white'])
        self._draw_rect(surf, 25 + lean, 34, 6, 10, PALETTE['hero_white'])
        self._draw_rect(surf, 17, 38, 6, 6, PALETTE['hero_gold'])
        self._draw_rect(surf, 25 + lean, 38, 6, 6, PALETTE['hero_gold'])
        self._draw_rect(surf, 16, 44, 7, 3, PALETTE['hero_armor_dark'])
        self._draw_rect(surf, 25 + lean, 44, 7, 3, PALETTE['hero_armor_dark'])
        
        # === BODY (leaning forward) ===
        self._draw_rect(surf, 15 + lean // 2, 22, 18, 12, PALETTE['hero_armor'])
        self._draw_rect(surf, 16 + lean // 2, 23, 16, 10, PALETTE['hero_armor_light'])
        self._draw_rect(surf, 15 + lean // 2, 22, 18, 2, PALETTE['hero_gold'])
        self._draw_rect(surf, 14 + lean // 2, 28, 20, 4, PALETTE['hero_red'])
        self._draw_rect(surf, 15 + lean // 2, 32, 18, 3, PALETTE['hero_gold'])
        
        # === SHOULDERS ===
        self._draw_rect(surf, 10 + lean // 2, 20, 7, 6, PALETTE['hero_gold'])
        self._draw_rect(surf, 31 + lean, 20, 7, 6, PALETTE['hero_gold'])
        
        # === SHIELD ARM (pulled back) ===
        self._draw_rect(surf, 6, 26, 5, 10, PALETTE['hero_armor'])
        self._draw_rect(surf, 2, 24 - frame, 12, 16, PALETTE['hero_armor_dark'])
        self._draw_outline_rect(surf, 2, 24 - frame, 12, 16, PALETTE['hero_gold'])
        self._draw_rect(surf, 6, 29 - frame, 4, 4, PALETTE['hero_gold'])
        
        # === HEAD ===
        self._draw_rect(surf, 18 + lean // 2, 10, 12, 12, PALETTE['skin_light'])
        self._draw_rect(surf, 19 + lean // 2, 11, 10, 10, PALETTE['skin_mid'])
        self._draw_rect(surf, 20 + lean // 2, 14, 3, 2, (40, 30, 20))
        self._draw_rect(surf, 25 + lean // 2, 14, 3, 2, (40, 30, 20))
        
        # === CROWN ===
        self._draw_rect(surf, 16 + lean // 2, 6, 16, 6, PALETTE['hero_gold'])
        self._draw_rect(surf, 22 + lean // 2, 1, 4, 6, PALETTE['hero_gold'])
        self._draw_rect(surf, 23 + lean // 2, 2, 2, 2, PALETTE['hero_red'])
        self._draw_rect(surf, 30 + lean, 2, 8, 4, PALETTE['hero_red'])
        
        # === FLAMING SWORD (swinging) ===
        angle = math.radians(phase['sword_angle'])
        sword_len = 22
        sx = 34 + lean
        sy = 24
        ex = int(sx + math.cos(angle) * sword_len)
        ey = int(sy + math.sin(angle) * sword_len)
        
        # Sword blade
        pygame.draw.line(surf, PALETTE['hero_gold'], (sx, sy), (ex, ey), 4)
        pygame.draw.line(surf, PALETTE['hero_gold_light'], (sx, sy), (ex, ey), 2)
        
        # Fire trail
        for i in range(6):
            fx = int(sx + math.cos(angle) * (sword_len - i * 3))
            fy = int(sy + math.sin(angle) * (sword_len - i * 3))
            fire_offset = (frame + i) % 3 - 1
            self._draw_rect(surf, fx - 2 + fire_offset, fy - 3, 4, 4, PALETTE['fire'])
            self._draw_rect(surf, fx - 1, fy - 2 + fire_offset, 2, 2, PALETTE['fire_light'])
        
        # Slash effect on frame 2-3
        if frame >= 2:
            for i in range(8):
                px = sx + int(math.cos(angle + 0.4) * (sword_len + i * 3))
                py = sy + int(math.sin(angle + 0.4) * (sword_len + i * 3))
                self._draw_rect(surf, px, py, 2, 2, (255, 200, 100))
        
        return surf
    
    def hero_cast(self, frame=0):
        """Hero spell casting animation - Indian warrior channeling magic."""
        surf = self._create_surface(HERO_SIZE)
        
        # Casting pose - arms raised
        arm_raise = min(frame * 3, 10)
        magic_grow = min(frame * 2, 8)
        
        # === CAPE ===
        self._draw_rect(surf, 10, 24, 6, 18, PALETTE['hero_red'])
        self._draw_rect(surf, 32, 24, 6, 18, PALETTE['hero_red'])
        
        # === LEGS ===
        self._draw_rect(surf, 17, 34, 6, 10, PALETTE['hero_white'])
        self._draw_rect(surf, 25, 34, 6, 10, PALETTE['hero_white'])
        self._draw_rect(surf, 17, 38, 6, 6, PALETTE['hero_gold'])
        self._draw_rect(surf, 25, 38, 6, 6, PALETTE['hero_gold'])
        self._draw_rect(surf, 16, 44, 7, 3, PALETTE['hero_armor_dark'])
        self._draw_rect(surf, 25, 44, 7, 3, PALETTE['hero_armor_dark'])
        
        # === BODY ===
        self._draw_rect(surf, 15, 22, 18, 12, PALETTE['hero_armor'])
        self._draw_rect(surf, 16, 23, 16, 10, PALETTE['hero_armor_light'])
        self._draw_rect(surf, 15, 22, 18, 2, PALETTE['hero_gold'])
        self._draw_rect(surf, 14, 28, 20, 4, PALETTE['hero_red'])
        self._draw_rect(surf, 15, 32, 18, 3, PALETTE['hero_gold'])
        
        # === SHOULDERS ===
        self._draw_rect(surf, 10, 20, 7, 6, PALETTE['hero_gold'])
        self._draw_rect(surf, 31, 20, 7, 6, PALETTE['hero_gold'])
        
        # === ARMS (raised for casting) ===
        self._draw_rect(surf, 8, 18 - arm_raise, 5, 12, PALETTE['hero_armor'])
        self._draw_rect(surf, 35, 18 - arm_raise, 5, 12, PALETTE['hero_armor'])
        # Hands
        self._draw_rect(surf, 7, 16 - arm_raise, 6, 5, PALETTE['skin_light'])
        self._draw_rect(surf, 35, 16 - arm_raise, 6, 5, PALETTE['skin_light'])
        
        # === MAGIC EFFECT between hands ===
        if frame >= 1:
            cx, cy = 24, 14 - arm_raise
            # Outer glow
            pygame.draw.circle(surf, (255, 200, 100, 150), (cx, cy), magic_grow + 6)
            pygame.draw.circle(surf, PALETTE['fire'], (cx, cy), magic_grow + 3)
            pygame.draw.circle(surf, PALETTE['fire_light'], (cx, cy), magic_grow)
            # Sparkles
            for i in range(4):
                angle = (frame * 0.5 + i * 1.57)
                px = int(cx + math.cos(angle) * (magic_grow + 4))
                py = int(cy + math.sin(angle) * (magic_grow + 4))
                self._draw_rect(surf, px - 1, py - 1, 3, 3, (255, 255, 200))
        
        # === HEAD ===
        self._draw_rect(surf, 18, 10, 12, 12, PALETTE['skin_light'])
        self._draw_rect(surf, 19, 11, 10, 10, PALETTE['skin_mid'])
        self._draw_rect(surf, 20, 14, 3, 2, (40, 30, 20))
        self._draw_rect(surf, 25, 14, 3, 2, (40, 30, 20))
        
        # === CROWN (glowing during cast) ===
        self._draw_rect(surf, 16, 6, 16, 6, PALETTE['hero_gold_light'])
        self._draw_rect(surf, 22, 1, 4, 6, PALETTE['hero_gold_light'])
        self._draw_rect(surf, 23, 2, 2, 2, PALETTE['hero_red'])
        self._draw_rect(surf, 30, 2, 8, 4, PALETTE['hero_red'])
        
        return surf
    
    def hero_death(self, frame=0):
        """Hero death/falling animation - Indian warrior falls."""
        surf = self._create_surface(HERO_SIZE)
        
        # Fall angle increases with frame
        fall_angle = min(frame * 22, 90)
        
        # At full death, draw horizontal
        if fall_angle >= 90:
            # Lying down - cape spread, crown fallen
            self._draw_rect(surf, 2, 28, 38, 6, PALETTE['hero_red'])  # Cape spread
            self._draw_rect(surf, 6, 26, 30, 8, PALETTE['hero_armor'])  # Body
            self._draw_rect(surf, 8, 27, 26, 6, PALETTE['hero_armor_light'])
            self._draw_rect(surf, 10, 28, 22, 4, PALETTE['hero_gold'])  # Gold trim
            self._draw_rect(surf, 2, 28, 8, 6, PALETTE['skin_light'])  # Head
            self._draw_rect(surf, 36, 30, 8, 4, PALETTE['hero_armor_dark'])  # Feet
            # Fallen crown
            self._draw_rect(surf, 0, 24, 8, 4, PALETTE['hero_gold'])
            self._draw_rect(surf, 2, 22, 4, 3, PALETTE['hero_gold'])
            self._draw_rect(surf, 3, 23, 2, 2, PALETTE['hero_red'])
            # Dropped sword
            self._draw_rect(surf, 38, 24, 8, 3, PALETTE['hero_gold'])
            self._draw_rect(surf, 36, 22, 4, 3, PALETTE['fire'])
        else:
            # Falling - Indian warrior tilting
            tilt = fall_angle / 90
            y_shift = int(tilt * 14)
            x_shift = int(tilt * 8)
            
            # Cape
            self._draw_rect(surf, 8 - x_shift, 24 + y_shift, 6, 16, PALETTE['hero_red'])
            # Legs
            self._draw_rect(surf, 17 - x_shift // 2, 34 + y_shift, 6, 10, PALETTE['hero_white'])
            self._draw_rect(surf, 25 - x_shift // 2, 34 + y_shift, 6, 10, PALETTE['hero_white'])
            # Body
            self._draw_rect(surf, 15 - x_shift, 22 + y_shift, 18, 12, PALETTE['hero_armor'])
            self._draw_rect(surf, 14 - x_shift, 28 + y_shift, 20, 4, PALETTE['hero_red'])
            self._draw_rect(surf, 15 - x_shift, 22 + y_shift, 18, 2, PALETTE['hero_gold'])
            # Head
            self._draw_rect(surf, 18 - x_shift * 1.5, 10 + y_shift, 12, 12, PALETTE['skin_light'])
            # Crown (falling off)
            crown_fall = int(tilt * 6)
            self._draw_rect(surf, 16 - x_shift * 2 - crown_fall, 6 + y_shift - crown_fall, 12, 5, PALETTE['hero_gold'])
            self._draw_rect(surf, 20 - x_shift * 2 - crown_fall, 3 + y_shift - crown_fall, 4, 4, PALETTE['hero_gold'])
        
        return surf
    
    # ==================== HERO SPECIAL ABILITY SPRITES ====================
    
    def hero_spin(self, frame=0):
        """Hero whirlwind spin attack - 24 frames for 3 full rotations."""
        surf = self._create_surface(HERO_SIZE)
        
        # 3 full rotations over 24 frames (8 frames per rotation)
        # Speed increases slightly each rotation
        rotation = frame // 8  # Which rotation we're on (0, 1, 2)
        frame_in_rotation = frame % 8
        
        # Angle accelerates slightly each rotation
        base_angle = frame_in_rotation * 45 + rotation * 360
        angle = base_angle + rotation * 10  # Extra angle per rotation for acceleration feel
        rad = math.radians(angle)
        
        # Intensity increases with each rotation
        intensity = 1 + rotation * 0.3  # 1.0, 1.3, 1.6
        
        # More motion blur trails on later rotations
        blur_count = 3 + rotation * 2  # 3, 5, 7 trails
        for blur_offset in range(blur_count):
            blur_rad = rad - math.radians(blur_offset * (12 - rotation * 2))
            blur_alpha = max(30, 100 - blur_offset * 15)
            self._draw_spin_frame(surf, blur_rad, blur_alpha)
        
        # Main figure at current rotation
        self._draw_spin_frame(surf, rad, 255)
        
        # Expanding slash ring effect
        slash_radius = 16 + rotation * 4  # Grows each rotation
        slash_count = 8 + rotation * 4  # More slashes each rotation
        for i in range(slash_count):
            slash_angle = rad + math.radians(i * (360 / slash_count))
            sx = 24 + int(math.cos(slash_angle) * slash_radius)
            sy = 28 + int(math.sin(slash_angle) * slash_radius)
            
            # Slash sparkle - more intense colors on later rotations
            if rotation == 0:
                color = PALETTE['hero_gold'] if (frame + i) % 2 == 0 else PALETTE['steel_light']
            elif rotation == 1:
                color = PALETTE['fire'] if (frame + i) % 2 == 0 else PALETTE['hero_gold_light']
            else:
                color = PALETTE['fire_light'] if (frame + i) % 2 == 0 else PALETTE['fire']
            
            size = 2 + rotation
            self._draw_rect(surf, sx - size//2, sy - size//2, size, size, color)
        
        # Sword arc trail
        sword_trail_count = 4 + rotation * 2
        for i in range(sword_trail_count):
            trail_rad = rad - math.radians(i * 20)
            trail_dist = 18 + rotation * 2
            tx = 24 + int(math.cos(trail_rad) * trail_dist)
            ty = 28 + int(math.sin(trail_rad) * trail_dist)
            trail_alpha = 200 - i * 30
            if trail_alpha > 0:
                color = PALETTE['fire'] if i % 2 == 0 else PALETTE['fire_light']
                self._draw_rect(surf, tx - 2, ty - 2, 4, 4, color)
        
        # Ground dust tornado effect
        dust_count = 6 + rotation * 3
        for i in range(dust_count):
            dust_angle = rad * 2 + math.radians(i * (360 / dust_count))  # Spins faster than body
            dust_dist = 12 + (i % 3) * 4 + rotation * 2
            dx = 24 + int(math.cos(dust_angle) * dust_dist)
            dy = 38 + int(math.sin(dust_angle) * 3)
            dust_size = 1 + (frame + i) % 3
            self._draw_rect(surf, dx, dy, dust_size, dust_size, PALETTE['sandstone'])
        
        # Wind effect lines on final rotation
        if rotation == 2:
            for i in range(6):
                wind_angle = rad + math.radians(i * 60 + 30)
                wind_start = 20
                wind_end = 24
                wx1 = 24 + int(math.cos(wind_angle) * wind_start)
                wy1 = 28 + int(math.sin(wind_angle) * wind_start)
                wx2 = 24 + int(math.cos(wind_angle) * wind_end)
                wy2 = 28 + int(math.sin(wind_angle) * wind_end)
                pygame.draw.line(surf, (200, 200, 220), (wx1, wy1), (wx2, wy2), 1)
        
        return surf
    
    def _draw_spin_frame(self, surf, rad, alpha):
        """Helper to draw hero at specific rotation angle."""
        cx, cy = 24, 28  # Center point
        
        # Calculate offsets based on angle
        facing_away = abs(math.cos(rad)) < 0.5  # Back visible when rotated 90/270
        side_view = abs(math.sin(rad)) > 0.7  # Side view at 90/270
        
        # Body position shifts based on rotation
        body_x = cx + int(math.sin(rad) * 4)
        body_y = cy
        
        # === CAPE (trails behind rotation) ===
        cape_angle = rad + math.pi  # Cape opposite to facing
        cape_x = cx + int(math.cos(cape_angle) * 12)
        cape_y = cy + int(math.sin(cape_angle) * 3)
        self._draw_rect(surf, cape_x - 4, cape_y - 2, 8, 16, PALETTE['hero_red'])
        self._draw_rect(surf, cape_x - 3, cape_y, 6, 14, PALETTE['hero_red_dark'])
        
        # === BODY ===
        self._draw_rect(surf, body_x - 8, body_y - 8, 16, 12, PALETTE['hero_armor'])
        self._draw_rect(surf, body_x - 7, body_y - 7, 14, 10, PALETTE['hero_armor_light'])
        self._draw_rect(surf, body_x - 8, body_y - 8, 16, 2, PALETTE['hero_gold'])
        self._draw_rect(surf, body_x - 9, body_y + 2, 18, 3, PALETTE['hero_red'])
        self._draw_rect(surf, body_x - 8, body_y + 5, 16, 2, PALETTE['hero_gold'])
        
        # === LEGS ===
        leg_spread = 3 if side_view else 0
        self._draw_rect(surf, body_x - 5 - leg_spread, body_y + 6, 5, 10, PALETTE['hero_white'])
        self._draw_rect(surf, body_x + leg_spread, body_y + 6, 5, 10, PALETTE['hero_white'])
        self._draw_rect(surf, body_x - 5 - leg_spread, body_y + 12, 5, 4, PALETTE['hero_gold'])
        self._draw_rect(surf, body_x + leg_spread, body_y + 12, 5, 4, PALETTE['hero_gold'])
        
        # === HEAD ===
        head_x = body_x + int(math.sin(rad) * 2)
        self._draw_rect(surf, head_x - 5, body_y - 18, 10, 10, PALETTE['skin_light'])
        self._draw_rect(surf, head_x - 4, body_y - 17, 8, 8, PALETTE['skin_mid'])
        
        # === CROWN ===
        self._draw_rect(surf, head_x - 6, body_y - 24, 12, 5, PALETTE['hero_gold'])
        self._draw_rect(surf, head_x - 2, body_y - 28, 4, 5, PALETTE['hero_gold'])
        self._draw_rect(surf, head_x - 1, body_y - 27, 2, 2, PALETTE['hero_red'])
        
        # === SWORD (extended outward during spin) ===
        sword_angle = rad - math.pi / 4  # Sword leads the rotation
        sword_len = 22
        sword_x = cx + int(math.cos(sword_angle) * 10)
        sword_y = cy + int(math.sin(sword_angle) * 6)
        sword_end_x = sword_x + int(math.cos(sword_angle) * sword_len)
        sword_end_y = sword_y + int(math.sin(sword_angle) * sword_len)
        
        pygame.draw.line(surf, PALETTE['hero_gold'], (sword_x, sword_y), (sword_end_x, sword_end_y), 4)
        pygame.draw.line(surf, PALETTE['hero_gold_light'], (sword_x, sword_y), (sword_end_x, sword_end_y), 2)
        
        # Fire trail on sword
        for i in range(4):
            fx = sword_x + int(math.cos(sword_angle) * (sword_len - i * 5))
            fy = sword_y + int(math.sin(sword_angle) * (sword_len - i * 5))
            fire_color = PALETTE['fire'] if i % 2 == 0 else PALETTE['fire_light']
            self._draw_rect(surf, fx - 2, fy - 2, 4, 4, fire_color)
    
    def hero_leap(self, frame=0):
        """Hero leap strike - 10 frames: charge, crouch, LAUNCH, soar, apex, dive, IMPACT, shockwave, crater, recover."""
        surf = self._create_surface(HERO_SIZE)
        
        # Extended animation phases
        # 0: charging energy, 1: deep crouch, 2: explosive launch, 3: soaring up, 4: apex hover
        # 5: diving down, 6: IMPACT, 7: shockwave expand, 8: crater, 9: heroic stand
        
        heights = [-2, -6, 4, 14, 20, 12, -4, -2, 0, 0]
        tilts = [0, 6, 12, 8, 4, -8, -12, 4, 2, 0]
        
        height = heights[min(frame, len(heights) - 1)]
        tilt = tilts[min(frame, len(tilts) - 1)]
        
        cx, cy = 24, 28 - height
        
        # === CHARGE ENERGY (frame 0) ===
        if frame == 0:
            # Ground energy circle
            for i in range(12):
                angle = i * math.pi / 6 + frame * 0.5
                radius = 14
                px = 24 + int(math.cos(angle) * radius)
                py = 40 + int(math.sin(angle) * 3)
                self._draw_rect(surf, px - 1, py - 1, 3, 2, PALETTE['fire'])
            # Rising energy particles
            for i in range(6):
                py = 44 - i * 4
                px = 24 + ((i * 7) % 11) - 5
                self._draw_rect(surf, px, py, 2, 2, PALETTE['fire_light'])
        
        # === JUMP SHADOW (shrinks as hero rises, grows on descent) ===
        if frame >= 2:
            if frame <= 5:
                shadow_size = max(3, 10 - height // 3)
            else:
                shadow_size = min(20, 6 + (frame - 6) * 5)
            shadow_alpha = max(30, 150 - height * 5)
            self._draw_rect(surf, 24 - shadow_size, 42, shadow_size * 2, 3, (40, 35, 30))
        
        # === WIND TRAIL (frames 2-5) ===
        if 2 <= frame <= 5:
            trail_count = 4
            for i in range(trail_count):
                trail_y = cy + 10 + i * 6
                trail_width = 8 - i * 2
                trail_alpha = 150 - i * 40
                # Motion blur streaks
                self._draw_rect(surf, cx - trail_width, trail_y, trail_width * 2, 2, (200, 220, 255))
        
        # === CAPE (dramatic billowing) ===
        if frame <= 1:
            # Gathered for jump
            self._draw_rect(surf, cx - 10, cy + 4, 8, 12, PALETTE['hero_red'])
        elif frame <= 4:
            # Streaming behind during ascent
            cape_len = 16 + frame * 2
            for i in range(4):
                cape_x = cx - 12 - i * 2
                cape_y = cy + 2 + i * 3
                cape_w = 6 - i
                self._draw_rect(surf, cape_x, cape_y, cape_w, cape_len - i * 3, PALETTE['hero_red'] if i % 2 == 0 else PALETTE['hero_red_dark'])
        elif frame <= 6:
            # Whipping forward during dive
            self._draw_rect(surf, cx - 6, cy - 8, 6, 20, PALETTE['hero_red'])
            self._draw_rect(surf, cx - 4, cy - 12, 4, 8, PALETTE['hero_red_dark'])
        else:
            # Settling
            self._draw_rect(surf, cx - 12, cy + 2, 8, 14, PALETTE['hero_red'])
        
        # === LEGS ===
        if frame <= 1:  # Crouching
            self._draw_rect(surf, cx - 6, cy + 8, 5, 8, PALETTE['hero_white'])
            self._draw_rect(surf, cx + 1, cy + 8, 5, 8, PALETTE['hero_white'])
        elif frame <= 4:  # Legs back, tucked
            self._draw_rect(surf, cx - 8, cy + 6, 5, 6, PALETTE['hero_white'])
            self._draw_rect(surf, cx - 4, cy + 10, 5, 6, PALETTE['hero_white'])
        elif frame <= 6:  # Legs forward for impact
            self._draw_rect(surf, cx - 4, cy + 4, 5, 8, PALETTE['hero_white'])
            self._draw_rect(surf, cx + 2, cy + 8, 5, 6, PALETTE['hero_white'])
        else:  # Wide stance landing
            spread = min(4, (frame - 6) * 2)
            self._draw_rect(surf, cx - 8 - spread, cy + 6, 6, 12, PALETTE['hero_white'])
            self._draw_rect(surf, cx + 2 + spread, cy + 6, 6, 12, PALETTE['hero_white'])
        
        # Gold shin guards
        self._draw_rect(surf, cx - 7, cy + 14, 5, 4, PALETTE['hero_gold'])
        self._draw_rect(surf, cx + 2, cy + 14, 5, 4, PALETTE['hero_gold'])
        
        # === BODY ===
        body_x = cx + tilt // 3
        body_rotate = tilt // 2
        self._draw_rect(surf, body_x - 8, cy - 6 - abs(body_rotate), 16, 12, PALETTE['hero_armor'])
        self._draw_rect(surf, body_x - 7, cy - 5 - abs(body_rotate), 14, 10, PALETTE['hero_armor_light'])
        self._draw_rect(surf, body_x - 8, cy - 6 - abs(body_rotate), 16, 2, PALETTE['hero_gold'])
        self._draw_rect(surf, body_x - 9, cy + 4 - abs(body_rotate), 18, 3, PALETTE['hero_red'])
        
        # === SHOULDERS ===
        self._draw_rect(surf, body_x - 12, cy - 8, 6, 5, PALETTE['hero_gold'])
        self._draw_rect(surf, body_x + 6, cy - 8, 6, 5, PALETTE['hero_gold'])
        
        # === HEAD ===
        head_x = body_x + tilt // 4
        head_y = cy - 16 - abs(body_rotate)
        self._draw_rect(surf, head_x - 5, head_y, 10, 10, PALETTE['skin_light'])
        self._draw_rect(surf, head_x - 4, head_y + 1, 8, 8, PALETTE['skin_mid'])
        # Fierce eyes during dive
        if 4 <= frame <= 6:
            self._draw_rect(surf, head_x - 3, head_y + 4, 3, 2, (255, 200, 50))  # Glowing eyes
            self._draw_rect(surf, head_x + 1, head_y + 4, 3, 2, (255, 200, 50))
        else:
            self._draw_rect(surf, head_x - 3, head_y + 4, 2, 2, (40, 30, 20))
            self._draw_rect(surf, head_x + 1, head_y + 4, 2, 2, (40, 30, 20))
        
        # === CROWN ===
        self._draw_rect(surf, head_x - 6, head_y - 6, 12, 5, PALETTE['hero_gold'])
        self._draw_rect(surf, head_x - 2, head_y - 10, 4, 5, PALETTE['hero_gold'])
        self._draw_rect(surf, head_x - 1, head_y - 9, 2, 2, PALETTE['hero_red'])
        
        # === SWORD - THE STAR OF THE SHOW ===
        if frame <= 1:
            # Gathering power - sword glowing at side
            sword_x, sword_y = cx + 10, cy - 4
            self._draw_rect(surf, sword_x, sword_y, 3, 16, PALETTE['hero_gold'])
            # Energy gathering around sword
            for i in range(6):
                angle = i * math.pi / 3 + frame * 2
                px = sword_x + 1 + int(math.cos(angle) * 6)
                py = sword_y + 8 + int(math.sin(angle) * 6)
                self._draw_rect(surf, px, py, 2, 2, PALETTE['fire_light'])
        elif frame <= 4:
            # Sword raised high, blazing with fire
            sword_len = 24
            sword_x = cx + 6 + tilt // 2
            sword_y = cy - 20 - height // 2
            # Main blade
            self._draw_rect(surf, sword_x, sword_y, 4, sword_len, PALETTE['hero_gold'])
            self._draw_rect(surf, sword_x + 1, sword_y + 2, 2, sword_len - 4, PALETTE['hero_gold_light'])
            # MASSIVE FLAMES
            for i in range(8):
                flame_x = sword_x - 3 + (i % 3) * 3
                flame_y = sword_y - 6 - i
                flame_size = 4 + (i % 3) * 2
                color = PALETTE['fire'] if i % 2 == 0 else PALETTE['fire_light']
                self._draw_rect(surf, flame_x, flame_y, flame_size, flame_size, color)
        elif frame <= 6:
            # DIVING STRIKE - sword pointing down, trailing fire
            sword_angle = math.radians(-70 - (frame - 4) * 20)
            sword_len = 28
            base_x = cx + 4 + tilt // 2
            base_y = cy - 6
            end_x = base_x + int(math.cos(sword_angle) * sword_len)
            end_y = base_y + int(math.sin(sword_angle) * sword_len)
            
            # Sword blade with glow
            pygame.draw.line(surf, PALETTE['hero_gold_dark'], (base_x, base_y), (end_x, end_y), 6)
            pygame.draw.line(surf, PALETTE['hero_gold'], (base_x, base_y), (end_x, end_y), 4)
            pygame.draw.line(surf, (255, 255, 200), (base_x, base_y), (end_x, end_y), 2)
            
            # Fire trail behind the dive
            for i in range(10):
                trail_x = base_x + int(math.cos(sword_angle) * (sword_len - i * 2))
                trail_y = base_y + int(math.sin(sword_angle) * (sword_len - i * 2))
                trail_size = 5 - i // 2
                if trail_size > 0:
                    color = PALETTE['fire'] if i % 2 == 0 else PALETTE['fire_light']
                    self._draw_rect(surf, trail_x - trail_size//2, trail_y - trail_size//2, trail_size, trail_size, color)
        else:
            # Sword planted in ground
            self._draw_rect(surf, cx + 2 + tilt // 4, cy + 2, 4, 18, PALETTE['hero_gold'])
            self._draw_rect(surf, cx + 3 + tilt // 4, cy + 4, 2, 14, PALETTE['hero_gold_light'])
        
        # === IMPACT EFFECTS (frames 6-8) ===
        if frame == 6:
            # Initial impact - bright flash
            pygame.draw.circle(surf, (255, 255, 200), (cx + 4, 40), 12)
            pygame.draw.circle(surf, (255, 200, 100), (cx + 4, 40), 8)
            # Ground crack lines
            for i in range(8):
                angle = i * math.pi / 4
                end_x = cx + 4 + int(math.cos(angle) * 16)
                end_y = 40 + int(math.sin(angle) * 6)
                pygame.draw.line(surf, (80, 60, 40), (cx + 4, 40), (end_x, end_y), 2)
        
        if frame == 7:
            # Shockwave ring expanding
            for ring in range(3):
                ring_radius = 12 + ring * 6
                for i in range(16):
                    angle = i * math.pi / 8 + ring * 0.3
                    px = cx + int(math.cos(angle) * ring_radius)
                    py = 40 + int(math.sin(angle) * ring_radius // 3)
                    color = PALETTE['fire_light'] if ring == 0 else (PALETTE['fire'] if ring == 1 else PALETTE['hero_gold'])
                    self._draw_rect(surf, px - 2, py - 1, 4, 3, color)
            # Flying debris
            for i in range(10):
                debris_angle = i * math.pi / 5 + 0.3
                debris_dist = 10 + i * 2
                dx = cx + int(math.cos(debris_angle) * debris_dist)
                dy = 36 - i + int(math.sin(debris_angle) * 4)
                self._draw_rect(surf, dx, dy, 3, 3, PALETTE['sandstone'])
        
        if frame == 8:
            # Settling dust and crater
            # Crater
            for i in range(6):
                crater_x = cx - 10 + i * 4
                self._draw_rect(surf, crater_x, 40, 3, 2, (60, 50, 40))
            # Dust clouds
            for i in range(8):
                dust_x = cx - 16 + i * 5
                dust_y = 36 + (i % 3) * 2
                dust_size = 4 + (i % 2) * 2
                self._draw_rect(surf, dust_x, dust_y, dust_size, dust_size - 1, PALETTE['sandstone'])
        
        return surf
    
    def hero_heavy(self, frame=0):
        """Hero heavy/crushing blow - 10 frames: MASSIVE overhead slam that shatters the ground."""
        surf = self._create_surface(HERO_SIZE)
        
        cx, cy = 24, 28
        
        # Animation phases - MORE EXAGGERATED
        # 0-1: Crouch and gather power
        # 2-4: MASSIVE wind-up, sword WAY overhead
        # 5: Apex - frozen moment, everything glowing
        # 6-7: DEVASTATING downswing
        # 8-9: Impact + ground destruction
        
        if frame <= 1:  # Crouch and gather
            crouch = frame * 3
            sword_angle_deg = -30 + frame * 20  # Sword starts low, raises
            charge_intensity = frame
            body_lean = 0
        elif frame <= 4:  # Wind-up - sword goes WAY back
            crouch = 3 - (frame - 2)
            sword_angle_deg = -10 + (frame - 2) * 50  # Goes from -10 to 140 (behind head!)
            charge_intensity = 2 + frame
            body_lean = (frame - 2) * 3
        elif frame == 5:  # Apex - frozen tension
            crouch = 0
            sword_angle_deg = 160  # Sword pointing back behind
            charge_intensity = 6
            body_lean = 8
        elif frame <= 7:  # SLAM DOWN
            crouch = (frame - 6) * 2
            progress = (frame - 5) / 2
            sword_angle_deg = 160 - progress * 250  # Swings from 160 to -90 (straight down!)
            charge_intensity = 0
            body_lean = 8 - (frame - 5) * 6
        else:  # Impact and recovery
            crouch = 4 - (frame - 8) * 2
            sword_angle_deg = -90 + (frame - 8) * 30
            charge_intensity = 0
            body_lean = -2 + (frame - 8)
        
        sword_angle = math.radians(sword_angle_deg)
        
        # === GROUND CRACK EFFECTS (frames 7-9) ===
        if frame >= 7:
            crack_intensity = frame - 6
            # Central impact point
            impact_x = cx + 8
            impact_y = cy + 14
            
            # Radiating cracks
            for i in range(8):
                crack_angle = math.radians(i * 45 + 22.5)
                crack_len = 6 + crack_intensity * 4 + (i % 2) * 3
                for j in range(crack_len // 2):
                    px = impact_x + int(math.cos(crack_angle) * j * 2)
                    py = impact_y + int(math.sin(crack_angle) * j * 0.5)
                    crack_color = (50, 40, 30) if j % 2 == 0 else (70, 55, 40)
                    self._draw_rect(surf, px, py, 2, 2, crack_color)
            
            # Flying debris chunks
            for i in range(10):
                debris_angle = math.radians(i * 36 + frame * 20)
                debris_dist = 8 + crack_intensity * 5
                debris_height = crack_intensity * 3 - i % 4
                dx = impact_x + int(math.cos(debris_angle) * debris_dist)
                dy = impact_y - debris_height + int(math.sin(debris_angle) * 2)
                debris_size = 2 + (i % 3)
                self._draw_rect(surf, dx, dy, debris_size, debris_size, PALETTE['sandstone'])
            
            # Dust clouds
            for i in range(6):
                dust_x = impact_x - 12 + i * 5
                dust_y = impact_y - 2 + (i % 2) * 3
                dust_size = 4 + crack_intensity + (i % 2) * 2
                self._draw_rect(surf, dust_x, dust_y, dust_size, dust_size - 1, (180, 160, 130))
        
        # === CAPE (billows dramatically) ===
        cape_billow = abs(sword_angle_deg) // 20 if frame <= 5 else (8 - (frame - 5) * 2)
        for i in range(4):
            cape_x = cx - 14 - body_lean - i * 2
            cape_y = cy + crouch - 4 + i * 2
            cape_h = 14 - i * 2 + cape_billow
            cape_color = PALETTE['hero_red'] if i % 2 == 0 else PALETTE['hero_red_dark']
            self._draw_rect(surf, cape_x, cape_y, 6 - i, cape_h, cape_color)
        
        # === LEGS (power stance) ===
        stance = 2 + abs(body_lean) // 2
        leg_y = cy + crouch + 4
        self._draw_rect(surf, cx - 8 - stance, leg_y, 6, 12, PALETTE['hero_white'])
        self._draw_rect(surf, cx + 2 + stance, leg_y, 6, 12, PALETTE['hero_white'])
        self._draw_rect(surf, cx - 8 - stance, leg_y + 8, 6, 4, PALETTE['hero_gold'])
        self._draw_rect(surf, cx + 2 + stance, leg_y + 8, 6, 4, PALETTE['hero_gold'])
        self._draw_rect(surf, cx - 9 - stance, leg_y + 12, 7, 3, PALETTE['hero_armor_dark'])
        self._draw_rect(surf, cx + 2 + stance, leg_y + 12, 7, 3, PALETTE['hero_armor_dark'])
        
        # === BODY (leans with swing) ===
        body_x = cx + body_lean // 2
        body_y = cy + crouch - 8
        self._draw_rect(surf, body_x - 8, body_y, 16, 14, PALETTE['hero_armor'])
        self._draw_rect(surf, body_x - 7, body_y + 1, 14, 12, PALETTE['hero_armor_light'])
        self._draw_rect(surf, body_x - 8, body_y, 16, 2, PALETTE['hero_gold'])
        self._draw_rect(surf, body_x - 9, body_y + 10, 18, 3, PALETTE['hero_red'])
        
        # === SHOULDERS (raised during wind-up) ===
        shoulder_raise = min(4, charge_intensity)
        self._draw_rect(surf, body_x - 12, body_y - 2 - shoulder_raise, 7, 6, PALETTE['hero_gold'])
        self._draw_rect(surf, body_x + 5, body_y - 2 - shoulder_raise, 7, 6, PALETTE['hero_gold'])
        
        # === HEAD (looks up during wind-up, down during swing) ===
        head_tilt = body_lean // 3
        head_x = body_x + head_tilt
        head_y = body_y - 12 - shoulder_raise
        self._draw_rect(surf, head_x - 5, head_y, 10, 10, PALETTE['skin_light'])
        self._draw_rect(surf, head_x - 4, head_y + 1, 8, 8, PALETTE['skin_mid'])
        # Fierce eyes
        if charge_intensity > 3 or frame >= 6:
            eye_color = (255, 200, 50)  # Glowing during power
        else:
            eye_color = (40, 30, 20)
        self._draw_rect(surf, head_x - 3, head_y + 4, 2, 2, eye_color)
        self._draw_rect(surf, head_x + 1, head_y + 4, 2, 2, eye_color)
        
        # === CROWN ===
        self._draw_rect(surf, head_x - 6, head_y - 6, 12, 5, PALETTE['hero_gold'])
        self._draw_rect(surf, head_x - 2, head_y - 10, 4, 5, PALETTE['hero_gold'])
        self._draw_rect(surf, head_x - 1, head_y - 9, 2, 2, PALETTE['hero_red'])
        
        # === ARMS (stretched overhead) ===
        arm_x = body_x + 2
        arm_y = body_y - 4 - shoulder_raise
        arm_angle = sword_angle - math.radians(30)
        arm_len = 12
        arm_end_x = arm_x + int(math.cos(arm_angle) * arm_len)
        arm_end_y = arm_y + int(math.sin(arm_angle) * arm_len)
        pygame.draw.line(surf, PALETTE['skin_mid'], (arm_x, arm_y), (arm_end_x, arm_end_y), 5)
        
        # === SWORD (MASSIVE and dramatic) ===
        sword_len = 30  # Bigger sword!
        sword_base_x = arm_end_x
        sword_base_y = arm_end_y
        sword_end_x = sword_base_x + int(math.cos(sword_angle) * sword_len)
        sword_end_y = sword_base_y + int(math.sin(sword_angle) * sword_len)
        
        # Power glow during charge
        if charge_intensity > 0:
            glow_radius = 4 + charge_intensity * 3
            for r in range(glow_radius, 0, -2):
                glow_color = (255, min(255, 180 + charge_intensity * 15), 50)
                pygame.draw.circle(surf, glow_color, (sword_end_x, sword_end_y), r)
            # Energy particles spiraling around sword
            for i in range(6):
                particle_angle = sword_angle + math.radians(i * 60 + frame * 30)
                particle_dist = 6 + charge_intensity
                px = sword_end_x + int(math.cos(particle_angle) * particle_dist)
                py = sword_end_y + int(math.sin(particle_angle) * particle_dist)
                self._draw_rect(surf, px - 1, py - 1, 3, 3, PALETTE['fire_light'])
        
        # Sword blade - thick and powerful
        pygame.draw.line(surf, PALETTE['hero_gold_dark'], (sword_base_x, sword_base_y), (sword_end_x, sword_end_y), 8)
        pygame.draw.line(surf, PALETTE['hero_gold'], (sword_base_x, sword_base_y), (sword_end_x, sword_end_y), 5)
        pygame.draw.line(surf, PALETTE['hero_gold_light'], (sword_base_x, sword_base_y), (sword_end_x, sword_end_y), 2)
        
        # Fire trail on sword
        for i in range(7):
            fx = sword_base_x + int(math.cos(sword_angle) * (sword_len - i * 4))
            fy = sword_base_y + int(math.sin(sword_angle) * (sword_len - i * 4))
            fire_size = 5 - i // 2
            fire_off = (frame + i) % 3 - 1
            if fire_size > 0:
                self._draw_rect(surf, fx - fire_size//2 + fire_off, fy - fire_size//2, fire_size, fire_size, PALETTE['fire'])
                self._draw_rect(surf, fx - 1, fy - 1 + fire_off, 3, 3, PALETTE['fire_light'])
        
        # === IMPACT FLASH (frame 7) ===
        if frame == 7:
            # Bright impact flash
            pygame.draw.circle(surf, (255, 255, 200), (cx + 8, cy + 14), 14)
            pygame.draw.circle(surf, (255, 230, 150), (cx + 8, cy + 14), 10)
            pygame.draw.circle(surf, (255, 200, 100), (cx + 8, cy + 14), 6)
        
        # === SHOCKWAVE RINGS (frames 8-9) ===
        if frame >= 8:
            ring_progress = frame - 7
            for ring in range(2):
                ring_radius = 10 + ring_progress * 8 + ring * 6
                for i in range(12):
                    ring_angle = math.radians(i * 30 + ring * 15)
                    rx = cx + 8 + int(math.cos(ring_angle) * ring_radius)
                    ry = cy + 14 + int(math.sin(ring_angle) * ring_radius // 3)
                    ring_color = PALETTE['fire_light'] if ring == 0 else PALETTE['hero_gold']
                    self._draw_rect(surf, rx - 2, ry - 1, 4, 3, ring_color)
        
        return surf
    
    def hero_bash(self, frame=0):
        """Hero shield bash - 8 frames: ready, lunge, extend, IMPACT, push, retract, recover x2."""
        surf = self._create_surface(HERO_SIZE)
        
        cx, cy = 24, 30
        
        # Animation phases - dramatic lunge forward with shield
        if frame == 0:  # Ready stance
            lunge_offset = 0
            shield_angle = 0
            body_lean = 0
            impact_flash = False
        elif frame == 1:  # Wind up (pull back)
            lunge_offset = -4
            shield_angle = -20
            body_lean = -3
            impact_flash = False
        elif frame == 2:  # Lunge forward
            lunge_offset = 8
            shield_angle = 15
            body_lean = 4
            impact_flash = False
        elif frame == 3:  # Full extension - IMPACT!
            lunge_offset = 16
            shield_angle = 25
            body_lean = 8
            impact_flash = True
        elif frame == 4:  # Push through
            lunge_offset = 14
            shield_angle = 20
            body_lean = 6
            impact_flash = True
        elif frame == 5:  # Retract
            lunge_offset = 8
            shield_angle = 10
            body_lean = 3
            impact_flash = False
        elif frame == 6:  # Recover
            lunge_offset = 3
            shield_angle = 5
            body_lean = 1
            impact_flash = False
        else:  # Frame 7 - back to ready
            lunge_offset = 0
            shield_angle = 0
            body_lean = 0
            impact_flash = False
        
        body_x = cx + body_lean
        
        # === CAPE (trails behind during lunge) ===
        cape_trail = max(0, -lunge_offset // 2)
        self._draw_rect(surf, body_x - 10 - cape_trail, cy - 8, 10, 20, PALETTE['hero_cape_dark'])
        self._draw_rect(surf, body_x - 8 - cape_trail, cy - 6, 6, 22, PALETTE['hero_cape'])
        
        # === LEGS (lunge stride) ===
        # Back leg
        self._draw_rect(surf, body_x - 4, cy + 10, 6, 14, PALETTE['hero_armor'])
        self._draw_rect(surf, body_x - 5, cy + 22, 8, 6, PALETTE['hero_armor_dark'])
        # Front leg (extended forward during lunge)
        front_leg_x = body_x + 2 + lunge_offset // 2
        self._draw_rect(surf, front_leg_x, cy + 8, 6, 14, PALETTE['hero_armor'])
        self._draw_rect(surf, front_leg_x - 1, cy + 20, 8, 6, PALETTE['hero_armor_dark'])
        
        # === BODY (leaning forward) ===
        # Torso
        self._draw_rect(surf, body_x - 6, cy - 10, 14, 22, PALETTE['hero_armor'])
        self._draw_rect(surf, body_x - 4, cy - 8, 10, 18, PALETTE['hero_armor_light'])
        # Gold trim
        self._draw_rect(surf, body_x - 6, cy - 10, 2, 22, PALETTE['hero_gold'])
        self._draw_rect(surf, body_x + 6, cy - 10, 2, 22, PALETTE['hero_gold'])
        
        # === SHOULDER PAULDRONS ===
        self._draw_rect(surf, body_x - 10, cy - 12, 8, 8, PALETTE['hero_armor_dark'])
        self._draw_rect(surf, body_x + 4, cy - 12, 8, 8, PALETTE['hero_armor_dark'])
        self._draw_rect(surf, body_x - 8, cy - 10, 6, 6, PALETTE['hero_armor'])
        self._draw_rect(surf, body_x + 6, cy - 10, 6, 6, PALETTE['hero_armor'])
        
        # === HEAD ===
        # Helmet
        self._draw_rect(surf, body_x - 5, cy - 22, 12, 12, PALETTE['hero_armor'])
        self._draw_rect(surf, body_x - 3, cy - 20, 8, 8, PALETTE['skin_mid'])
        # Visor
        self._draw_rect(surf, body_x - 3, cy - 18, 8, 3, PALETTE['hero_armor_dark'])
        # Crown/crest
        self._draw_rect(surf, body_x - 1, cy - 26, 4, 6, PALETTE['hero_gold'])
        self._draw_rect(surf, body_x, cy - 28, 2, 4, PALETTE['hero_gold_light'])
        
        # === SHIELD ARM (main action) ===
        shield_x = body_x + 8 + lunge_offset
        shield_y = cy - 2
        
        # Arm holding shield
        arm_angle = math.radians(shield_angle)
        self._draw_rect(surf, body_x + 6, cy - 4, 8 + lunge_offset // 2, 6, PALETTE['hero_armor'])
        
        # === THE SHIELD (big, prominent) ===
        shield_w, shield_h = 14, 20
        
        # Shield glow on impact
        if impact_flash:
            for r in range(12, 0, -3):
                glow_alpha = 180 - r * 12
                pygame.draw.circle(surf, (255, 255, 200), (shield_x + shield_w//2, shield_y + shield_h//2), r)
        
        # Shield base (kite shield shape)
        pygame.draw.polygon(surf, PALETTE['hero_armor_dark'], [
            (shield_x, shield_y),
            (shield_x + shield_w, shield_y),
            (shield_x + shield_w, shield_y + shield_h - 6),
            (shield_x + shield_w//2, shield_y + shield_h),
            (shield_x, shield_y + shield_h - 6),
        ])
        # Shield face
        pygame.draw.polygon(surf, PALETTE['hero_armor'], [
            (shield_x + 2, shield_y + 2),
            (shield_x + shield_w - 2, shield_y + 2),
            (shield_x + shield_w - 2, shield_y + shield_h - 8),
            (shield_x + shield_w//2, shield_y + shield_h - 2),
            (shield_x + 2, shield_y + shield_h - 8),
        ])
        # Shield emblem (lion/crest)
        self._draw_rect(surf, shield_x + 4, shield_y + 5, 6, 8, PALETTE['hero_gold'])
        self._draw_rect(surf, shield_x + 5, shield_y + 6, 4, 4, PALETTE['hero_gold_light'])
        # Shield rim
        pygame.draw.polygon(surf, PALETTE['hero_gold'], [
            (shield_x, shield_y),
            (shield_x + shield_w, shield_y),
            (shield_x + shield_w, shield_y + 2),
            (shield_x, shield_y + 2),
        ], 0)
        
        # === IMPACT EFFECTS (frames 3-4) ===
        if impact_flash:
            # Shockwave lines
            impact_x = shield_x + shield_w + 4
            for i in range(8):
                line_angle = math.radians(-60 + i * 15)
                line_len = 12 + (frame % 2) * 4
                end_x = impact_x + int(math.cos(line_angle) * line_len)
                end_y = shield_y + shield_h//2 + int(math.sin(line_angle) * line_len)
                pygame.draw.line(surf, (255, 255, 200), (impact_x, shield_y + shield_h//2), (end_x, end_y), 3)
            
            # Sparks
            for i in range(6):
                spark_x = impact_x + 4 + (i * 3) + (frame % 2) * 2
                spark_y = shield_y + shield_h//2 - 8 + i * 3 + (frame % 3) - 1
                self._draw_rect(surf, spark_x, spark_y, 3, 3, PALETTE['fire_light'])
            
            # Ground dust from force
            for i in range(5):
                dust_x = body_x - 8 + i * 8
                self._draw_rect(surf, dust_x, cy + 24, 4, 3, PALETTE['sandstone'])
        
        # === SWORD (on back during bash) ===
        sword_x = body_x - 8 - cape_trail
        pygame.draw.line(surf, PALETTE['hero_gold_dark'], (sword_x, cy - 6), (sword_x - 6, cy + 12), 4)
        pygame.draw.line(surf, PALETTE['hero_gold'], (sword_x, cy - 6), (sword_x - 6, cy + 12), 2)
        
        return surf
    
    # ==================== MAGE SPRITES ====================
    
    def mage_idle(self, frame=0):
        """Mage/Lyra idle animation - Indian mystic with peacock headdress and crystal staff."""
        surf = self._create_surface(HERO_SIZE)
        
        y_off = 1 if frame % 2 == 0 else 0
        magic_pulse = frame % 3
        
        # === CAPE/ROBE (flowing behind) ===
        # Main flowing robe - deep blue with gold trim
        self._draw_rect(surf, 6, 26 + y_off, 8, 18, PALETTE['mage_robe'])
        self._draw_rect(surf, 34, 26 + y_off, 8, 18, PALETTE['mage_robe'])
        # Gold trim on cape edges
        self._draw_rect(surf, 6, 26 + y_off, 2, 18, PALETTE['mage_gold'])
        self._draw_rect(surf, 40, 26 + y_off, 2, 18, PALETTE['mage_gold'])
        # Cape decorations - gold emblems
        self._draw_rect(surf, 8, 32 + y_off, 4, 4, PALETTE['mage_gold_dark'])
        self._draw_rect(surf, 36, 32 + y_off, 4, 4, PALETTE['mage_gold_dark'])
        self._draw_rect(surf, 9, 33 + y_off, 2, 2, PALETTE['mage_blue_gem'])
        self._draw_rect(surf, 37, 33 + y_off, 2, 2, PALETTE['mage_blue_gem'])
        
        # === LEGS ===
        # White pants
        self._draw_rect(surf, 17, 36 + y_off, 6, 8, PALETTE['hero_white'])
        self._draw_rect(surf, 25, 36 + y_off, 6, 8, PALETTE['hero_white'])
        # Gold boots
        self._draw_rect(surf, 16, 42 + y_off, 7, 5, PALETTE['mage_gold_dark'])
        self._draw_rect(surf, 17, 43 + y_off, 5, 3, PALETTE['mage_gold'])
        self._draw_rect(surf, 25, 42 + y_off, 7, 5, PALETTE['mage_gold_dark'])
        self._draw_rect(surf, 26, 43 + y_off, 5, 3, PALETTE['mage_gold'])
        
        # === ROBE BODY ===
        # Main robe - deep blue
        self._draw_rect(surf, 14, 24 + y_off, 20, 14, PALETTE['mage_robe'])
        self._draw_rect(surf, 15, 25 + y_off, 18, 12, PALETTE['mage_robe_light'])
        # Gold trim down center
        self._draw_rect(surf, 22, 24 + y_off, 4, 14, PALETTE['mage_gold'])
        self._draw_rect(surf, 23, 25 + y_off, 2, 12, PALETTE['mage_gold_light'])
        # Gold trim at waist/belt
        self._draw_rect(surf, 14, 32 + y_off, 20, 3, PALETTE['mage_gold'])
        self._draw_rect(surf, 15, 33 + y_off, 18, 1, PALETTE['mage_gold_light'])
        # Blue gem on belt
        self._draw_rect(surf, 22, 32 + y_off, 4, 3, PALETTE['mage_blue_gem'])
        self._draw_rect(surf, 23, 33 + y_off, 2, 1, PALETTE['mage_blue_glow'])
        # Blue gems on robe
        self._draw_rect(surf, 17, 27 + y_off, 3, 3, PALETTE['mage_blue_gem'])
        self._draw_rect(surf, 28, 27 + y_off, 3, 3, PALETTE['mage_blue_gem'])
        
        # === SHOULDERS ===
        self._draw_rect(surf, 10, 22 + y_off, 8, 5, PALETTE['mage_robe'])
        self._draw_rect(surf, 30, 22 + y_off, 8, 5, PALETTE['mage_robe'])
        # Gold shoulder trim
        self._draw_rect(surf, 10, 22 + y_off, 8, 2, PALETTE['mage_gold'])
        self._draw_rect(surf, 30, 22 + y_off, 8, 2, PALETTE['mage_gold'])
        
        # === ARMS ===
        # Left arm (holding book)
        self._draw_rect(surf, 8, 26 + y_off, 5, 10, PALETTE['mage_robe'])
        self._draw_rect(surf, 9, 27 + y_off, 3, 8, PALETTE['hero_white'])  # White sleeve
        # Gold bracelet
        self._draw_rect(surf, 8, 34 + y_off, 5, 2, PALETTE['mage_gold'])
        # Hand
        self._draw_rect(surf, 7, 36 + y_off, 6, 4, PALETTE['skin_light'])
        
        # Right arm (holding staff)
        self._draw_rect(surf, 35, 26 + y_off, 5, 10, PALETTE['mage_robe'])
        self._draw_rect(surf, 36, 27 + y_off, 3, 8, PALETTE['hero_white'])
        # Gold bracelet
        self._draw_rect(surf, 35, 34 + y_off, 5, 2, PALETTE['mage_gold'])
        # Hand
        self._draw_rect(surf, 36, 36 + y_off, 5, 4, PALETTE['skin_light'])
        
        # === SPELLBOOK (left hand) ===
        self._draw_rect(surf, 2, 32 + y_off, 10, 8, (100, 70, 50))  # Brown cover
        self._draw_rect(surf, 3, 33 + y_off, 8, 6, (80, 55, 40))  # Darker center
        # Gold corner decorations
        self._draw_rect(surf, 2, 32 + y_off, 2, 2, PALETTE['mage_gold'])
        self._draw_rect(surf, 10, 32 + y_off, 2, 2, PALETTE['mage_gold'])
        self._draw_rect(surf, 2, 38 + y_off, 2, 2, PALETTE['mage_gold'])
        self._draw_rect(surf, 10, 38 + y_off, 2, 2, PALETTE['mage_gold'])
        # Magic glow from book
        self._draw_rect(surf, 4, 34 + y_off + magic_pulse, 4, 3, PALETTE['mage_blue_glow'])
        
        # === CRYSTAL STAFF (right side) ===
        # Staff shaft - ornate gold
        self._draw_rect(surf, 40, 10 + y_off, 3, 32, PALETTE['wood_dark'])
        self._draw_rect(surf, 41, 12 + y_off, 1, 28, PALETTE['wood'])
        # Gold decorations on staff
        self._draw_rect(surf, 39, 20 + y_off, 5, 3, PALETTE['mage_gold'])
        self._draw_rect(surf, 39, 30 + y_off, 5, 3, PALETTE['mage_gold'])
        # Crystal top - large blue gem
        self._draw_rect(surf, 38, 4 + y_off, 7, 8, PALETTE['mage_blue_gem'])
        self._draw_rect(surf, 39, 5 + y_off, 5, 6, PALETTE['mage_blue_glow'])
        self._draw_rect(surf, 40, 6 + y_off + magic_pulse, 3, 4, (200, 230, 255))
        # Gold prongs holding crystal
        self._draw_rect(surf, 38, 10 + y_off, 2, 4, PALETTE['mage_gold'])
        self._draw_rect(surf, 43, 10 + y_off, 2, 4, PALETTE['mage_gold'])
        # Magic swirl around crystal
        if magic_pulse == 0:
            self._draw_pixel(surf, 36, 6 + y_off, PALETTE['mage_blue_glow'])
            self._draw_pixel(surf, 46, 8 + y_off, PALETTE['mage_blue_glow'])
        elif magic_pulse == 1:
            self._draw_pixel(surf, 37, 4 + y_off, PALETTE['mage_blue_glow'])
            self._draw_pixel(surf, 45, 10 + y_off, PALETTE['mage_blue_glow'])
        
        # === HEAD ===
        # Face
        self._draw_rect(surf, 18, 12 + y_off, 12, 10, PALETTE['skin_light'])
        self._draw_rect(surf, 19, 13 + y_off, 10, 8, PALETTE['skin_mid'])
        # Eyes - bright blue/teal
        self._draw_rect(surf, 20, 15 + y_off, 3, 3, (255, 255, 255))
        self._draw_rect(surf, 25, 15 + y_off, 3, 3, (255, 255, 255))
        self._draw_rect(surf, 21, 16 + y_off, 2, 2, (50, 150, 180))
        self._draw_rect(surf, 26, 16 + y_off, 2, 2, (50, 150, 180))
        # Nose
        self._draw_rect(surf, 23, 17 + y_off, 2, 2, PALETTE['skin_shadow'])
        # Smile
        self._draw_rect(surf, 22, 19 + y_off, 4, 1, PALETTE['skin_shadow'])
        
        # === GOLDEN HAIR ===
        self._draw_rect(surf, 17, 10 + y_off, 14, 5, PALETTE['mage_hair'])
        self._draw_rect(surf, 18, 11 + y_off, 12, 3, PALETTE['mage_hair_dark'])
        # Side hair flowing
        self._draw_rect(surf, 15, 14 + y_off, 4, 10, PALETTE['mage_hair'])
        self._draw_rect(surf, 29, 14 + y_off, 4, 10, PALETTE['mage_hair'])
        
        # === HEADDRESS ===
        # Main headdress - deep blue with gold
        self._draw_rect(surf, 16, 6 + y_off, 16, 6, PALETTE['mage_robe'])
        self._draw_rect(surf, 17, 7 + y_off, 14, 4, PALETTE['mage_robe_light'])
        # Gold crown band
        self._draw_rect(surf, 16, 10 + y_off, 16, 3, PALETTE['mage_gold'])
        self._draw_rect(surf, 17, 11 + y_off, 14, 1, PALETTE['mage_gold_light'])
        # Central blue gem
        self._draw_rect(surf, 22, 7 + y_off, 4, 4, PALETTE['mage_blue_gem'])
        self._draw_rect(surf, 23, 8 + y_off, 2, 2, PALETTE['mage_blue_glow'])
        # Side gems
        self._draw_rect(surf, 17, 8 + y_off, 3, 3, PALETTE['mage_gold'])
        self._draw_rect(surf, 28, 8 + y_off, 3, 3, PALETTE['mage_gold'])
        self._draw_rect(surf, 18, 9 + y_off, 1, 1, PALETTE['mage_blue_gem'])
        self._draw_rect(surf, 29, 9 + y_off, 1, 1, PALETTE['mage_blue_gem'])
        
        # === PEACOCK FEATHERS ===
        # Feather stems
        self._draw_rect(surf, 30, 2 + y_off, 2, 8, (80, 60, 50))
        self._draw_rect(surf, 33, 1 + y_off, 2, 7, (80, 60, 50))
        self._draw_rect(surf, 36, 3 + y_off, 2, 6, (80, 60, 50))
        # Feather eyes (peacock pattern)
        self._draw_rect(surf, 29, 0 + y_off, 4, 4, PALETTE['peacock_blue'])
        self._draw_rect(surf, 30, 1 + y_off, 2, 2, PALETTE['peacock_green'])
        self._draw_rect(surf, 32, 0 + y_off, 4, 4, PALETTE['peacock_green'])
        self._draw_rect(surf, 33, 1 + y_off, 2, 2, PALETTE['peacock_blue'])
        self._draw_rect(surf, 35, 1 + y_off, 4, 4, PALETTE['peacock_blue'])
        self._draw_rect(surf, 36, 2 + y_off, 2, 2, PALETTE['mage_gold'])
        
        # === JEWELRY ===
        # Necklace with pendant
        self._draw_rect(surf, 19, 22 + y_off, 10, 1, PALETTE['mage_gold'])
        self._draw_rect(surf, 22, 23 + y_off, 4, 3, PALETTE['mage_gold'])
        self._draw_rect(surf, 23, 24 + y_off, 2, 2, PALETTE['mage_blue_gem'])
        # Earrings
        self._draw_rect(surf, 16, 15 + y_off, 2, 3, PALETTE['mage_gold'])
        self._draw_rect(surf, 30, 15 + y_off, 2, 3, PALETTE['mage_gold'])
        
        return surf
    
    def mage_cast(self, frame=0):
        """Mage casting animation - Indian mystic channeling blue magic."""
        surf = self._create_surface(HERO_SIZE)
        
        cast_raise = min(frame * 3, 10)
        magic_grow = min(frame * 3, 12)
        
        # === CAPE (billowing) ===
        self._draw_rect(surf, 4 - frame, 26, 10, 18 + frame, PALETTE['mage_robe'])
        self._draw_rect(surf, 34 + frame, 26, 10, 18 + frame, PALETTE['mage_robe'])
        self._draw_rect(surf, 4 - frame, 26, 2, 18 + frame, PALETTE['mage_gold'])
        self._draw_rect(surf, 42 + frame, 26, 2, 18 + frame, PALETTE['mage_gold'])
        
        # === LEGS ===
        self._draw_rect(surf, 17, 36, 6, 8, PALETTE['hero_white'])
        self._draw_rect(surf, 25, 36, 6, 8, PALETTE['hero_white'])
        self._draw_rect(surf, 16, 42, 7, 5, PALETTE['mage_gold'])
        self._draw_rect(surf, 25, 42, 7, 5, PALETTE['mage_gold'])
        
        # === ROBE BODY ===
        self._draw_rect(surf, 14, 24, 20, 14, PALETTE['mage_robe'])
        self._draw_rect(surf, 15, 25, 18, 12, PALETTE['mage_robe_light'])
        self._draw_rect(surf, 22, 24, 4, 14, PALETTE['mage_gold'])
        self._draw_rect(surf, 14, 32, 20, 3, PALETTE['mage_gold'])
        self._draw_rect(surf, 22, 32, 4, 3, PALETTE['mage_blue_gem'])
        
        # === ARMS (raised for casting) ===
        self._draw_rect(surf, 6, 20 - cast_raise, 6, 14, PALETTE['mage_robe'])
        self._draw_rect(surf, 36, 20 - cast_raise, 6, 14, PALETTE['mage_robe'])
        self._draw_rect(surf, 7, 22 - cast_raise, 4, 10, PALETTE['hero_white'])
        self._draw_rect(surf, 37, 22 - cast_raise, 4, 10, PALETTE['hero_white'])
        # Gold bracelets
        self._draw_rect(surf, 6, 30 - cast_raise, 6, 2, PALETTE['mage_gold'])
        self._draw_rect(surf, 36, 30 - cast_raise, 6, 2, PALETTE['mage_gold'])
        # Hands
        self._draw_rect(surf, 5, 32 - cast_raise, 6, 4, PALETTE['skin_light'])
        self._draw_rect(surf, 37, 32 - cast_raise, 6, 4, PALETTE['skin_light'])
        
        # === STAFF (raised high) ===
        self._draw_rect(surf, 40, 4 - cast_raise // 2, 3, 34, PALETTE['wood_dark'])
        self._draw_rect(surf, 41, 6 - cast_raise // 2, 1, 30, PALETTE['wood'])
        self._draw_rect(surf, 39, 16 - cast_raise // 2, 5, 3, PALETTE['mage_gold'])
        # Crystal (glowing intensely)
        self._draw_rect(surf, 38, 0 - cast_raise // 2, 7, 8, PALETTE['mage_blue_glow'])
        self._draw_rect(surf, 39, 1 - cast_raise // 2, 5, 6, (200, 230, 255))
        self._draw_rect(surf, 40, 2 - cast_raise // 2, 3, 4, (255, 255, 255))
        
        # === MAGIC ORB (growing between hands) ===
        cx, cy = 24, 20 - cast_raise
        # Outer glow
        if magic_grow > 3:
            pygame.draw.circle(surf, PALETTE['mage_blue_dark'], (cx, cy), magic_grow + 4)
        pygame.draw.circle(surf, PALETTE['mage_blue_gem'], (cx, cy), magic_grow + 2)
        pygame.draw.circle(surf, PALETTE['mage_blue_glow'], (cx, cy), magic_grow)
        pygame.draw.circle(surf, (200, 230, 255), (cx, cy), max(1, magic_grow - 3))
        
        # Magic sparkles
        if frame >= 2:
            for i in range(6):
                angle = (i * 60 + frame * 45) * math.pi / 180
                px = cx + int(math.cos(angle) * (magic_grow + 6))
                py = cy + int(math.sin(angle) * (magic_grow + 6))
                self._draw_rect(surf, px - 1, py - 1, 3, 3, (255, 255, 255))
        
        # Magic swirls
        if frame >= 1:
            for i in range(3):
                angle = (i * 120 + frame * 60) * math.pi / 180
                dist = magic_grow + 3 + i * 2
                px = cx + int(math.cos(angle) * dist)
                py = cy + int(math.sin(angle) * dist)
                self._draw_rect(surf, px, py, 2, 2, PALETTE['mage_blue_glow'])
        
        # === HEAD ===
        self._draw_rect(surf, 18, 12, 12, 10, PALETTE['skin_light'])
        self._draw_rect(surf, 19, 13, 10, 8, PALETTE['skin_mid'])
        # Eyes (glowing with magic)
        self._draw_rect(surf, 20, 15, 3, 3, PALETTE['mage_blue_glow'])
        self._draw_rect(surf, 25, 15, 3, 3, PALETTE['mage_blue_glow'])
        
        # === HAIR ===
        self._draw_rect(surf, 17, 10, 14, 5, PALETTE['mage_hair'])
        self._draw_rect(surf, 15, 14, 4, 10, PALETTE['mage_hair'])
        self._draw_rect(surf, 29, 14, 4, 10, PALETTE['mage_hair'])
        
        # === HEADDRESS (glowing) ===
        self._draw_rect(surf, 16, 6, 16, 6, PALETTE['mage_robe_light'])
        self._draw_rect(surf, 16, 10, 16, 3, PALETTE['mage_gold_light'])
        self._draw_rect(surf, 22, 7, 4, 4, PALETTE['mage_blue_glow'])  # Gem glowing
        
        # === PEACOCK FEATHERS ===
        self._draw_rect(surf, 30, 2, 2, 8, (80, 60, 50))
        self._draw_rect(surf, 33, 1, 2, 7, (80, 60, 50))
        self._draw_rect(surf, 29, 0, 4, 4, PALETTE['peacock_blue'])
        self._draw_rect(surf, 32, 0, 4, 4, PALETTE['peacock_green'])
        
        return surf
    
    def mage_walk(self, frame=0, direction=0):
        """Mage walk animation - Indian mystic. direction: 0=down, 1=left, 2=right, 3=up"""
        surf = self._create_surface(HERO_SIZE)
        
        leg_offsets = [(0, 0), (3, -1), (0, 0), (-3, -1)]
        l_off, r_off = leg_offsets[frame % 4], leg_offsets[(frame + 2) % 4]
        y_off = 1 if frame % 2 == 0 else 0
        cape_flow = frame % 4
        arm_swing = [0, 3, 0, -3][frame % 4]
        bounce = 1 if frame % 2 == 0 else 0
        
        if direction == 0:  # DOWN
            self._draw_mage_walk_down(surf, y_off, l_off, r_off, cape_flow, arm_swing, bounce)
        elif direction == 1:  # LEFT
            self._draw_mage_walk_left(surf, y_off, l_off, r_off, cape_flow, arm_swing, bounce)
        elif direction == 2:  # RIGHT
            self._draw_mage_walk_right(surf, y_off, l_off, r_off, cape_flow, arm_swing, bounce)
        else:  # UP
            self._draw_mage_walk_up(surf, y_off, l_off, r_off, cape_flow, arm_swing, bounce)
        
        return surf
    
    def _draw_mage_walk_down(self, surf, y_off, l_off, r_off, cape_flow, arm_swing, bounce):
        """Mage walking towards camera (down)."""
        # Cape
        self._draw_rect(surf, 4 - cape_flow, 26 + y_off, 8, 18 + cape_flow, PALETTE['mage_robe'])
        self._draw_rect(surf, 36 + cape_flow // 2, 26 + y_off, 8, 18 + cape_flow, PALETTE['mage_robe'])
        self._draw_rect(surf, 4 - cape_flow, 26 + y_off, 2, 18 + cape_flow, PALETTE['mage_gold'])
        self._draw_rect(surf, 42 + cape_flow // 2, 26 + y_off, 2, 18 + cape_flow, PALETTE['mage_gold'])
        
        # Legs
        self._draw_rect(surf, 17 + l_off[0], 36 + y_off + l_off[1], 6, 8, PALETTE['hero_white'])
        self._draw_rect(surf, 25 + r_off[0], 36 + y_off + r_off[1], 6, 8, PALETTE['hero_white'])
        self._draw_rect(surf, 16 + l_off[0], 42 + y_off, 7, 5, PALETTE['mage_gold'])
        self._draw_rect(surf, 25 + r_off[0], 42 + y_off, 7, 5, PALETTE['mage_gold'])
        
        # Robe
        self._draw_rect(surf, 14, 24 + y_off, 20, 14, PALETTE['mage_robe'])
        self._draw_rect(surf, 15, 25 + y_off, 18, 12, PALETTE['mage_robe_light'])
        self._draw_rect(surf, 22, 24 + y_off, 4, 14, PALETTE['mage_gold'])
        self._draw_rect(surf, 14, 32 + y_off, 20, 3, PALETTE['mage_gold'])
        self._draw_rect(surf, 22, 32 + y_off, 4, 3, PALETTE['mage_blue_gem'])
        
        # Shoulders & Arms
        self._draw_rect(surf, 10, 22 + y_off, 8, 5, PALETTE['mage_robe'])
        self._draw_rect(surf, 30, 22 + y_off, 8, 5, PALETTE['mage_robe'])
        self._draw_rect(surf, 10, 22 + y_off, 8, 2, PALETTE['mage_gold'])
        self._draw_rect(surf, 30, 22 + y_off, 8, 2, PALETTE['mage_gold'])
        self._draw_rect(surf, 8, 26 + y_off - arm_swing, 5, 10, PALETTE['mage_robe'])
        self._draw_rect(surf, 35, 26 + y_off + arm_swing, 5, 10, PALETTE['mage_robe'])
        self._draw_rect(surf, 7, 36 + y_off - arm_swing, 6, 4, PALETTE['skin_light'])
        self._draw_rect(surf, 36, 36 + y_off + arm_swing, 5, 4, PALETTE['skin_light'])
        
        # Book (left)
        self._draw_rect(surf, 2, 32 + y_off - arm_swing, 10, 8, (100, 70, 50))
        self._draw_rect(surf, 2, 32 + y_off - arm_swing, 2, 2, PALETTE['mage_gold'])
        self._draw_rect(surf, 10, 32 + y_off - arm_swing, 2, 2, PALETTE['mage_gold'])
        
        # Staff (right)
        self._draw_rect(surf, 40, 10 + y_off + arm_swing, 3, 32, PALETTE['wood_dark'])
        self._draw_rect(surf, 39, 20 + y_off + arm_swing, 5, 3, PALETTE['mage_gold'])
        self._draw_rect(surf, 38, 4 + y_off + arm_swing, 7, 8, PALETTE['mage_blue_gem'])
        self._draw_rect(surf, 39, 5 + y_off + arm_swing, 5, 6, PALETTE['mage_blue_glow'])
        
        # Head with face
        self._draw_rect(surf, 18, 12 + y_off, 12, 10, PALETTE['skin_light'])
        self._draw_rect(surf, 19, 13 + y_off, 10, 8, PALETTE['skin_mid'])
        self._draw_rect(surf, 20, 15 + y_off, 3, 3, (255, 255, 255))
        self._draw_rect(surf, 25, 15 + y_off, 3, 3, (255, 255, 255))
        self._draw_rect(surf, 21, 16 + y_off, 2, 2, (50, 150, 180))
        self._draw_rect(surf, 26, 16 + y_off, 2, 2, (50, 150, 180))
        
        # Hair
        self._draw_rect(surf, 17, 10 + y_off, 14, 5, PALETTE['mage_hair'])
        self._draw_rect(surf, 15, 14 + y_off, 4, 10, PALETTE['mage_hair'])
        self._draw_rect(surf, 29, 14 + y_off, 4, 10, PALETTE['mage_hair'])
        
        # Headdress
        self._draw_rect(surf, 16, 6 + y_off, 16, 6, PALETTE['mage_robe'])
        self._draw_rect(surf, 16, 10 + y_off, 16, 3, PALETTE['mage_gold'])
        self._draw_rect(surf, 22, 7 + y_off, 4, 4, PALETTE['mage_blue_gem'])
        
        # Peacock feathers
        self._draw_rect(surf, 30, 2 + y_off - bounce, 2, 8, (80, 60, 50))
        self._draw_rect(surf, 33, 1 + y_off - bounce, 2, 7, (80, 60, 50))
        self._draw_rect(surf, 29, 0 + y_off - bounce, 4, 4, PALETTE['peacock_blue'])
        self._draw_rect(surf, 32, 0 + y_off - bounce, 4, 4, PALETTE['peacock_green'])
    
    def _draw_mage_walk_left(self, surf, y_off, l_off, r_off, cape_flow, arm_swing, bounce):
        """Mage walking left - book forward, staff behind."""
        # Cape flowing right
        self._draw_rect(surf, 30 + cape_flow, 22 + y_off, 12 + cape_flow, 22, PALETTE['mage_robe'])
        self._draw_rect(surf, 32 + cape_flow, 24 + y_off, 10 + cape_flow, 18, PALETTE['mage_robe_dark'])
        self._draw_rect(surf, 40 + cape_flow, 22 + y_off, 2, 22, PALETTE['mage_gold'])
        
        # Legs (side)
        self._draw_rect(surf, 20 + r_off[0], 36 + y_off + r_off[1], 8, 8, PALETTE['hero_white'])
        self._draw_rect(surf, 18 + l_off[0], 36 + y_off + l_off[1], 8, 8, PALETTE['hero_white'])
        self._draw_rect(surf, 18, 42 + y_off, 10, 5, PALETTE['mage_gold'])
        
        # Robe (side)
        self._draw_rect(surf, 18, 24 + y_off, 12, 14, PALETTE['mage_robe'])
        self._draw_rect(surf, 19, 25 + y_off, 10, 12, PALETTE['mage_robe_light'])
        self._draw_rect(surf, 17, 32 + y_off, 14, 3, PALETTE['mage_gold'])
        
        # Shoulder
        self._draw_rect(surf, 16, 22 + y_off, 10, 4, PALETTE['mage_robe'])
        self._draw_rect(surf, 16, 22 + y_off, 10, 2, PALETTE['mage_gold'])
        
        # Staff arm (behind)
        self._draw_rect(surf, 26, 24 + y_off + arm_swing, 4, 14, PALETTE['mage_robe'])
        self._draw_rect(surf, 28, 10 + y_off + arm_swing, 3, 30, PALETTE['wood_dark'])
        self._draw_rect(surf, 26, 4 + y_off + arm_swing, 7, 8, PALETTE['mage_blue_gem'])
        self._draw_rect(surf, 27, 5 + y_off + arm_swing, 5, 6, PALETTE['mage_blue_glow'])
        
        # Book arm (front - prominent)
        self._draw_rect(surf, 10, 26 + y_off - arm_swing, 6, 12, PALETTE['mage_robe'])
        self._draw_rect(surf, 4, 30 + y_off - arm_swing, 12, 10, (100, 70, 50))  # Book
        self._draw_rect(surf, 5, 31 + y_off - arm_swing, 10, 8, (80, 55, 40))
        self._draw_rect(surf, 4, 30 + y_off - arm_swing, 2, 2, PALETTE['mage_gold'])
        self._draw_rect(surf, 14, 30 + y_off - arm_swing, 2, 2, PALETTE['mage_gold'])
        self._draw_rect(surf, 7, 33 + y_off - arm_swing, 4, 3, PALETTE['mage_blue_glow'])  # Magic glow
        
        # Head (side)
        self._draw_rect(surf, 18, 12 + y_off, 10, 10, PALETTE['skin_light'])
        self._draw_rect(surf, 16, 15 + y_off, 3, 2, (50, 150, 180))  # Eye
        self._draw_rect(surf, 14, 17 + y_off, 3, 2, PALETTE['skin_shadow'])  # Nose
        
        # Hair (side)
        self._draw_rect(surf, 17, 10 + y_off, 12, 5, PALETTE['mage_hair'])
        self._draw_rect(surf, 26, 12 + y_off, 4, 12, PALETTE['mage_hair'])
        
        # Headdress (side)
        self._draw_rect(surf, 16, 6 + y_off, 14, 6, PALETTE['mage_robe'])
        self._draw_rect(surf, 16, 10 + y_off, 14, 3, PALETTE['mage_gold'])
        self._draw_rect(surf, 20, 7 + y_off, 4, 4, PALETTE['mage_blue_gem'])
        
        # Peacock feathers
        self._draw_rect(surf, 28, 2 + y_off - bounce, 2, 6, (80, 60, 50))
        self._draw_rect(surf, 27, 0 + y_off - bounce, 4, 4, PALETTE['peacock_blue'])
        self._draw_rect(surf, 30, 1 + y_off - bounce, 3, 3, PALETTE['peacock_green'])
    
    def _draw_mage_walk_right(self, surf, y_off, l_off, r_off, cape_flow, arm_swing, bounce):
        """Mage walking right - staff forward, book behind."""
        # Cape flowing left
        self._draw_rect(surf, 4 - cape_flow, 22 + y_off, 12 + cape_flow, 22, PALETTE['mage_robe'])
        self._draw_rect(surf, 6 - cape_flow, 24 + y_off, 10 + cape_flow, 18, PALETTE['mage_robe_dark'])
        self._draw_rect(surf, 4 - cape_flow, 22 + y_off, 2, 22, PALETTE['mage_gold'])
        
        # Legs (side)
        self._draw_rect(surf, 20 + l_off[0], 36 + y_off + l_off[1], 8, 8, PALETTE['hero_white'])
        self._draw_rect(surf, 22 + r_off[0], 36 + y_off + r_off[1], 8, 8, PALETTE['hero_white'])
        self._draw_rect(surf, 20, 42 + y_off, 10, 5, PALETTE['mage_gold'])
        
        # Robe (side)
        self._draw_rect(surf, 18, 24 + y_off, 12, 14, PALETTE['mage_robe'])
        self._draw_rect(surf, 19, 25 + y_off, 10, 12, PALETTE['mage_robe_light'])
        self._draw_rect(surf, 17, 32 + y_off, 14, 3, PALETTE['mage_gold'])
        
        # Shoulder
        self._draw_rect(surf, 22, 22 + y_off, 10, 4, PALETTE['mage_robe'])
        self._draw_rect(surf, 22, 22 + y_off, 10, 2, PALETTE['mage_gold'])
        
        # Book arm (behind)
        self._draw_rect(surf, 14, 26 + y_off - arm_swing, 5, 12, PALETTE['mage_robe'])
        self._draw_rect(surf, 12, 32 + y_off - arm_swing, 8, 6, (100, 70, 50))
        
        # Staff arm (front - prominent)
        self._draw_rect(surf, 32, 24 + y_off + arm_swing, 6, 14, PALETTE['mage_robe'])
        self._draw_rect(surf, 36, 6 + y_off + arm_swing, 4, 36, PALETTE['wood_dark'])
        self._draw_rect(surf, 37, 8 + y_off + arm_swing, 2, 32, PALETTE['wood'])
        self._draw_rect(surf, 34, 18 + y_off + arm_swing, 6, 3, PALETTE['mage_gold'])
        self._draw_rect(surf, 33, 0 + y_off + arm_swing, 9, 10, PALETTE['mage_blue_gem'])
        self._draw_rect(surf, 34, 1 + y_off + arm_swing, 7, 8, PALETTE['mage_blue_glow'])
        self._draw_rect(surf, 35, 2 + y_off + arm_swing, 5, 6, (200, 230, 255))
        
        # Head (side - facing right)
        self._draw_rect(surf, 20, 12 + y_off, 10, 10, PALETTE['skin_light'])
        self._draw_rect(surf, 28, 15 + y_off, 3, 2, (50, 150, 180))  # Eye
        self._draw_rect(surf, 30, 17 + y_off, 3, 2, PALETTE['skin_shadow'])  # Nose
        
        # Hair
        self._draw_rect(surf, 19, 10 + y_off, 12, 5, PALETTE['mage_hair'])
        self._draw_rect(surf, 18, 12 + y_off, 4, 12, PALETTE['mage_hair'])
        
        # Headdress
        self._draw_rect(surf, 18, 6 + y_off, 14, 6, PALETTE['mage_robe'])
        self._draw_rect(surf, 18, 10 + y_off, 14, 3, PALETTE['mage_gold'])
        self._draw_rect(surf, 24, 7 + y_off, 4, 4, PALETTE['mage_blue_gem'])
        
        # Peacock feathers (prominent this side)
        self._draw_rect(surf, 30, 2 + y_off - bounce, 2, 8, (80, 60, 50))
        self._draw_rect(surf, 33, 1 + y_off - bounce, 2, 7, (80, 60, 50))
        self._draw_rect(surf, 36, 3 + y_off - bounce, 2, 6, (80, 60, 50))
        self._draw_rect(surf, 29, 0 + y_off - bounce, 4, 4, PALETTE['peacock_blue'])
        self._draw_rect(surf, 32, 0 + y_off - bounce, 4, 4, PALETTE['peacock_green'])
        self._draw_rect(surf, 35, 1 + y_off - bounce, 4, 4, PALETTE['peacock_blue'])
    
    def _draw_mage_walk_up(self, surf, y_off, l_off, r_off, cape_flow, arm_swing, bounce):
        """Mage walking away (up) - back view, cape prominent."""
        # Cape (front in back view - prominent)
        self._draw_rect(surf, 10, 18 + y_off, 28, 28 + cape_flow, PALETTE['mage_robe'])
        self._draw_rect(surf, 12, 20 + y_off, 24, 24 + cape_flow, PALETTE['mage_robe_dark'])
        self._draw_rect(surf, 10, 18 + y_off, 2, 28 + cape_flow, PALETTE['mage_gold'])
        self._draw_rect(surf, 36, 18 + y_off, 2, 28 + cape_flow, PALETTE['mage_gold'])
        # Gold embroidery on cape
        self._draw_rect(surf, 20, 28 + y_off, 8, 6, PALETTE['mage_gold_dark'])
        self._draw_rect(surf, 21, 29 + y_off, 6, 4, PALETTE['mage_blue_gem'])
        
        # Legs (back)
        self._draw_rect(surf, 17 + l_off[0], 36 + y_off + l_off[1], 6, 8, PALETTE['hero_white'])
        self._draw_rect(surf, 25 + r_off[0], 36 + y_off + r_off[1], 6, 8, PALETTE['hero_white'])
        self._draw_rect(surf, 16 + l_off[0], 42 + y_off, 7, 5, PALETTE['mage_gold'])
        self._draw_rect(surf, 25 + r_off[0], 42 + y_off, 7, 5, PALETTE['mage_gold'])
        
        # Robe (back)
        self._draw_rect(surf, 14, 24 + y_off, 20, 14, PALETTE['mage_robe'])
        self._draw_rect(surf, 15, 25 + y_off, 18, 12, PALETTE['mage_robe_dark'])
        self._draw_rect(surf, 14, 32 + y_off, 20, 3, PALETTE['mage_gold'])
        
        # Shoulders
        self._draw_rect(surf, 10, 22 + y_off, 8, 5, PALETTE['mage_robe'])
        self._draw_rect(surf, 30, 22 + y_off, 8, 5, PALETTE['mage_robe'])
        self._draw_rect(surf, 10, 22 + y_off, 8, 2, PALETTE['mage_gold'])
        self._draw_rect(surf, 30, 22 + y_off, 8, 2, PALETTE['mage_gold'])
        
        # Arms
        self._draw_rect(surf, 8, 26 + y_off - arm_swing, 5, 10, PALETTE['mage_robe'])
        self._draw_rect(surf, 35, 26 + y_off + arm_swing, 5, 10, PALETTE['mage_robe'])
        
        # Book (back of left arm)
        self._draw_rect(surf, 4, 30 + y_off - arm_swing, 8, 6, (100, 70, 50))
        
        # Staff (back of right arm)
        self._draw_rect(surf, 38, 12 + y_off + arm_swing, 3, 28, PALETTE['wood_dark'])
        self._draw_rect(surf, 36, 6 + y_off + arm_swing, 7, 8, PALETTE['mage_blue_gem'])
        
        # Head (back of head)
        self._draw_rect(surf, 18, 12 + y_off, 12, 10, PALETTE['skin_shadow'])
        
        # Hair (back - more visible)
        self._draw_rect(surf, 16, 10 + y_off, 16, 6, PALETTE['mage_hair'])
        self._draw_rect(surf, 14, 14 + y_off, 5, 12, PALETTE['mage_hair'])
        self._draw_rect(surf, 29, 14 + y_off, 5, 12, PALETTE['mage_hair'])
        self._draw_rect(surf, 17, 12 + y_off, 14, 4, PALETTE['mage_hair_dark'])
        
        # Headdress (back)
        self._draw_rect(surf, 16, 6 + y_off, 16, 6, PALETTE['mage_robe'])
        self._draw_rect(surf, 17, 7 + y_off, 14, 4, PALETTE['mage_robe_dark'])
        self._draw_rect(surf, 16, 10 + y_off, 16, 3, PALETTE['mage_gold'])
        
        # Peacock feathers (very prominent from back)
        self._draw_rect(surf, 28, 0 + y_off - bounce, 2, 10, (80, 60, 50))
        self._draw_rect(surf, 32, 0 + y_off - bounce, 2, 9, (80, 60, 50))
        self._draw_rect(surf, 36, 1 + y_off - bounce, 2, 8, (80, 60, 50))
        self._draw_rect(surf, 26, 0 + y_off - bounce, 5, 5, PALETTE['peacock_blue'])
        self._draw_rect(surf, 27, 1 + y_off - bounce, 3, 3, PALETTE['peacock_green'])
        self._draw_rect(surf, 30, 0 + y_off - bounce, 5, 5, PALETTE['peacock_green'])
        self._draw_rect(surf, 31, 1 + y_off - bounce, 3, 3, PALETTE['peacock_blue'])
        self._draw_rect(surf, 34, 0 + y_off - bounce, 5, 5, PALETTE['peacock_blue'])
        self._draw_rect(surf, 35, 1 + y_off - bounce, 3, 3, PALETTE['mage_gold'])
    
    def mage_attack(self, frame=0):
        """Mage staff attack animation."""
        surf = self._create_surface(HERO_SIZE)
        
        # Attack phases - staff swing
        phases = [
            {'staff_angle': -30, 'lean': 0},
            {'staff_angle': 0, 'lean': 2},
            {'staff_angle': 45, 'lean': 3},
            {'staff_angle': 60, 'lean': 2},
        ]
        phase = phases[min(frame, len(phases) - 1)]
        lean = phase['lean']
        
        # === CAPE ===
        self._draw_rect(surf, 6 - frame, 26, 8, 18 + frame, PALETTE['mage_robe'])
        self._draw_rect(surf, 6 - frame, 26, 2, 18 + frame, PALETTE['mage_gold'])
        
        # === LEGS ===
        self._draw_rect(surf, 17, 36, 6, 8, PALETTE['hero_white'])
        self._draw_rect(surf, 25 + lean, 36, 6, 8, PALETTE['hero_white'])
        self._draw_rect(surf, 16, 42, 7, 5, PALETTE['mage_gold'])
        self._draw_rect(surf, 25 + lean, 42, 7, 5, PALETTE['mage_gold'])
        
        # === ROBE BODY ===
        self._draw_rect(surf, 14 + lean // 2, 24, 20, 14, PALETTE['mage_robe'])
        self._draw_rect(surf, 15 + lean // 2, 25, 18, 12, PALETTE['mage_robe_light'])
        self._draw_rect(surf, 22 + lean // 2, 24, 4, 14, PALETTE['mage_gold'])
        self._draw_rect(surf, 14 + lean // 2, 32, 20, 3, PALETTE['mage_gold'])
        
        # === STAFF SWING ===
        angle = math.radians(phase['staff_angle'])
        staff_len = 30
        sx = 34 + lean
        sy = 26
        ex = int(sx + math.cos(angle) * staff_len)
        ey = int(sy + math.sin(angle) * staff_len)
        
        # Staff shaft
        pygame.draw.line(surf, PALETTE['wood_dark'], (sx, sy), (ex, ey), 4)
        pygame.draw.line(surf, PALETTE['wood'], (sx, sy), (ex, ey), 2)
        
        # Crystal at end
        crystal_x = int(sx + math.cos(angle) * (staff_len - 4))
        crystal_y = int(sy + math.sin(angle) * (staff_len - 4))
        pygame.draw.circle(surf, PALETTE['mage_blue_gem'], (crystal_x, crystal_y), 6)
        pygame.draw.circle(surf, PALETTE['mage_blue_glow'], (crystal_x, crystal_y), 4)
        pygame.draw.circle(surf, (255, 255, 255), (crystal_x, crystal_y), 2)
        
        # Magic trail on swing
        if frame >= 2:
            for i in range(5):
                trail_angle = angle + 0.3 + i * 0.1
                tx = int(sx + math.cos(trail_angle) * (staff_len - 6 + i * 2))
                ty = int(sy + math.sin(trail_angle) * (staff_len - 6 + i * 2))
                self._draw_rect(surf, tx - 1, ty - 1, 3, 3, PALETTE['mage_blue_glow'])
        
        # === HEAD ===
        self._draw_rect(surf, 18 + lean // 2, 12, 12, 10, PALETTE['skin_light'])
        self._draw_rect(surf, 19 + lean // 2, 13, 10, 8, PALETTE['skin_mid'])
        self._draw_rect(surf, 20 + lean // 2, 15, 3, 3, (255, 255, 255))
        self._draw_rect(surf, 25 + lean // 2, 15, 3, 3, (255, 255, 255))
        
        # === HAIR ===
        self._draw_rect(surf, 17 + lean // 2, 10, 14, 5, PALETTE['mage_hair'])
        self._draw_rect(surf, 15 + lean // 2, 14, 4, 10, PALETTE['mage_hair'])
        
        # === HEADDRESS ===
        self._draw_rect(surf, 16 + lean // 2, 6, 16, 6, PALETTE['mage_robe'])
        self._draw_rect(surf, 16 + lean // 2, 10, 16, 3, PALETTE['mage_gold'])
        self._draw_rect(surf, 22 + lean // 2, 7, 4, 4, PALETTE['mage_blue_gem'])
        
        # === PEACOCK FEATHERS ===
        self._draw_rect(surf, 30 + lean, 2, 2, 8, (80, 60, 50))
        self._draw_rect(surf, 29 + lean, 0, 4, 4, PALETTE['peacock_blue'])
        self._draw_rect(surf, 32 + lean, 0, 4, 4, PALETTE['peacock_green'])
        
        return surf
    
    def mage_death(self, frame=0):
        """Mage death animation."""
        surf = self._create_surface(HERO_SIZE)
        
        fall_angle = min(frame * 22, 90)
        
        if fall_angle >= 90:
            # Lying down
            self._draw_rect(surf, 2, 28, 40, 8, PALETTE['mage_robe'])  # Robe spread
            self._draw_rect(surf, 4, 30, 36, 4, PALETTE['mage_robe_light'])
            self._draw_rect(surf, 2, 28, 40, 2, PALETTE['mage_gold'])  # Gold trim
            self._draw_rect(surf, 2, 28, 8, 6, PALETTE['skin_light'])  # Head
            self._draw_rect(surf, 2, 26, 6, 4, PALETTE['mage_hair'])  # Hair
            self._draw_rect(surf, 40, 30, 8, 4, PALETTE['mage_gold'])  # Feet
            # Fallen staff
            self._draw_rect(surf, 36, 22, 10, 3, PALETTE['wood_dark'])
            self._draw_rect(surf, 44, 20, 4, 4, PALETTE['mage_blue_gem'])
            # Fallen headdress
            self._draw_rect(surf, 0, 24, 8, 4, PALETTE['mage_robe'])
            self._draw_rect(surf, 2, 22, 4, 3, PALETTE['peacock_blue'])
        else:
            # Falling
            tilt = fall_angle / 90
            y_shift = int(tilt * 14)
            x_shift = int(tilt * 8)
            
            # Cape
            self._draw_rect(surf, 6 - x_shift, 26 + y_shift, 8, 16, PALETTE['mage_robe'])
            # Robe
            self._draw_rect(surf, 14 - x_shift, 24 + y_shift, 20, 14, PALETTE['mage_robe'])
            self._draw_rect(surf, 14 - x_shift, 32 + y_shift, 20, 3, PALETTE['mage_gold'])
            # Legs
            self._draw_rect(surf, 17 - x_shift // 2, 36 + y_shift, 6, 8, PALETTE['hero_white'])
            self._draw_rect(surf, 25 - x_shift // 2, 36 + y_shift, 6, 8, PALETTE['hero_white'])
            # Head
            self._draw_rect(surf, 18 - x_shift * 1.5, 12 + y_shift, 12, 10, PALETTE['skin_light'])
            # Hair
            self._draw_rect(surf, 17 - x_shift * 1.5, 10 + y_shift, 14, 5, PALETTE['mage_hair'])
            # Headdress falling
            hs = int(tilt * 6)
            self._draw_rect(surf, 16 - x_shift * 2 - hs, 6 + y_shift - hs, 12, 5, PALETTE['mage_robe'])
            self._draw_rect(surf, 20 - x_shift * 2 - hs, 4 + y_shift - hs, 4, 4, PALETTE['peacock_blue'])
        
        return surf
    
    # ==================== SKELETON SPRITES ====================
    
    def skeleton_idle(self, frame=0):
        """Skeleton enemy idle."""
        surf = self._create_surface()
        
        y_off = 1 if frame % 2 == 0 else 0
        
        # Feet bones
        self._draw_rect(surf, 11, 28 + y_off, 3, 3, PALETTE['bone'])
        self._draw_rect(surf, 18, 28 + y_off, 3, 3, PALETTE['bone'])
        
        # Leg bones
        self._draw_rect(surf, 12, 22 + y_off, 2, 6, PALETTE['bone'])
        self._draw_rect(surf, 18, 22 + y_off, 2, 6, PALETTE['bone'])
        
        # Pelvis
        self._draw_rect(surf, 11, 20 + y_off, 10, 3, PALETTE['bone_shadow'])
        
        # Ribcage
        self._draw_rect(surf, 11, 12 + y_off, 10, 8, PALETTE['bone'])
        # Rib gaps
        for i in range(3):
            self._draw_rect(surf, 13, 13 + i * 2 + y_off, 6, 1, PALETTE['bone_dark'])
        
        # Arm bones
        self._draw_rect(surf, 8, 14 + y_off, 2, 8, PALETTE['bone'])
        self._draw_rect(surf, 22, 14 + y_off, 2, 8, PALETTE['bone'])
        
        # Skull
        self._draw_rect(surf, 11, 4 + y_off, 10, 8, PALETTE['bone'])
        self._draw_rect(surf, 12, 5 + y_off, 8, 6, PALETTE['bone_shadow'])
        
        # Eye sockets (dark)
        self._draw_rect(surf, 12, 6 + y_off, 3, 3, PALETTE['bone_dark'])
        self._draw_rect(surf, 17, 6 + y_off, 3, 3, PALETTE['bone_dark'])
        
        # Red eye glow
        self._draw_pixel(surf, 13, 7 + y_off, (255, 50, 50))
        self._draw_pixel(surf, 18, 7 + y_off, (255, 50, 50))
        
        # Jaw
        self._draw_rect(surf, 12, 10 + y_off, 8, 2, PALETTE['bone_shadow'])
        
        # Sword
        self._draw_rect(surf, 24, 12 + y_off, 2, 12, PALETTE['steel_dark'])
        
        return surf
    
    def skeleton_attack(self, frame=0):
        """Skeleton attack animation."""
        surf = self._create_surface()
        
        # Swing phases
        swing = [-30, 0, 45, 90][min(frame, 3)]
        
        # Body (same as idle mostly)
        self._draw_rect(surf, 11, 28, 3, 3, PALETTE['bone'])
        self._draw_rect(surf, 18, 28, 3, 3, PALETTE['bone'])
        self._draw_rect(surf, 12, 22, 2, 6, PALETTE['bone'])
        self._draw_rect(surf, 18, 22, 2, 6, PALETTE['bone'])
        self._draw_rect(surf, 11, 12, 10, 8, PALETTE['bone'])
        self._draw_rect(surf, 11, 4, 10, 8, PALETTE['bone'])
        
        # Eyes glow brighter during attack
        self._draw_pixel(surf, 13, 7, (255, 100, 100))
        self._draw_pixel(surf, 18, 7, (255, 100, 100))
        
        # Sword swing
        angle = math.radians(swing)
        sx, sy = 22, 16
        ex = int(sx + math.cos(angle) * 14)
        ey = int(sy + math.sin(angle) * 14)
        pygame.draw.line(surf, PALETTE['steel'], (sx, sy), (ex, ey), 3)
        
        return surf
    
    # ==================== SPIDER SPRITES ====================
    
    def spider_idle(self, frame=0):
        """Spider enemy idle."""
        surf = self._create_surface()
        
        # Leg animation
        leg_move = 1 if frame % 2 == 0 else -1
        
        # Body (abdomen)
        pygame.draw.ellipse(surf, PALETTE['spider_body'], (10, 16, 12, 10))
        pygame.draw.ellipse(surf, PALETTE['spider_light'], (12, 18, 8, 6))
        
        # Head
        pygame.draw.ellipse(surf, PALETTE['spider_body'], (12, 10, 8, 8))
        
        # Eyes (8 of them, 2 big)
        self._draw_pixel(surf, 14, 12, PALETTE['spider_eyes'])
        self._draw_pixel(surf, 17, 12, PALETTE['spider_eyes'])
        self._draw_pixel(surf, 13, 14, (100, 30, 30))
        self._draw_pixel(surf, 18, 14, (100, 30, 30))
        
        # Legs (8 total, 4 per side)
        for i in range(4):
            # Left legs
            lx = 10 - i * 2 + (leg_move if i % 2 == 0 else -leg_move)
            ly = 16 + i * 2
            pygame.draw.line(surf, PALETTE['spider_body'], (12, 18), (lx, ly), 2)
            pygame.draw.line(surf, PALETTE['spider_body'], (lx, ly), (lx - 2, ly + 4), 2)
            
            # Right legs
            rx = 22 + i * 2 + (leg_move if i % 2 == 1 else -leg_move)
            pygame.draw.line(surf, PALETTE['spider_body'], (20, 18), (rx, ly), 2)
            pygame.draw.line(surf, PALETTE['spider_body'], (rx, ly), (rx + 2, ly + 4), 2)
        
        # Fangs
        self._draw_rect(surf, 14, 17, 1, 3, PALETTE['bone'])
        self._draw_rect(surf, 17, 17, 1, 3, PALETTE['bone'])
        
        return surf
    
    def spider_walk(self, frame=0):
        """Spider walking animation."""
        surf = self._create_surface()
        
        # More pronounced leg movement for walking
        leg_phase = [0, 2, 0, -2][frame % 4]
        
        # Body bob
        y_off = 1 if frame % 2 == 0 else 0
        
        # Body (abdomen)
        pygame.draw.ellipse(surf, PALETTE['spider_body'], (10, 16 + y_off, 12, 10))
        pygame.draw.ellipse(surf, PALETTE['spider_light'], (12, 18 + y_off, 8, 6))
        
        # Head
        pygame.draw.ellipse(surf, PALETTE['spider_body'], (12, 10 + y_off, 8, 8))
        
        # Eyes
        self._draw_pixel(surf, 14, 12 + y_off, PALETTE['spider_eyes'])
        self._draw_pixel(surf, 17, 12 + y_off, PALETTE['spider_eyes'])
        
        # Animated legs
        for i in range(4):
            leg_offset = leg_phase if i % 2 == 0 else -leg_phase
            # Left legs
            lx = 10 - i * 2 + leg_offset
            ly = 16 + i * 2 + y_off
            pygame.draw.line(surf, PALETTE['spider_body'], (12, 18 + y_off), (lx, ly), 2)
            pygame.draw.line(surf, PALETTE['spider_body'], (lx, ly), (lx - 2, ly + 4), 2)
            
            # Right legs
            rx = 22 + i * 2 - leg_offset
            pygame.draw.line(surf, PALETTE['spider_body'], (20, 18 + y_off), (rx, ly), 2)
            pygame.draw.line(surf, PALETTE['spider_body'], (rx, ly), (rx + 2, ly + 4), 2)
        
        # Fangs
        self._draw_rect(surf, 14, 17 + y_off, 1, 3, PALETTE['bone'])
        self._draw_rect(surf, 17, 17 + y_off, 1, 3, PALETTE['bone'])
        
        return surf
    
    def spider_attack(self, frame=0):
        """Spider attack animation - lunging bite."""
        surf = self._create_surface()
        
        # Lunge forward
        lunge = [0, 3, 4, 2][min(frame, 3)]
        
        # Body
        pygame.draw.ellipse(surf, PALETTE['spider_body'], (10 + lunge, 16, 12, 10))
        pygame.draw.ellipse(surf, PALETTE['spider_light'], (12 + lunge, 18, 8, 6))
        
        # Head (lunging)
        pygame.draw.ellipse(surf, PALETTE['spider_body'], (12 + lunge * 2, 10, 8, 8))
        
        # Eyes (angry red)
        self._draw_pixel(surf, 14 + lunge * 2, 12, (255, 50, 50))
        self._draw_pixel(surf, 17 + lunge * 2, 12, (255, 50, 50))
        
        # Fangs (extended during attack)
        fang_ext = 2 if frame >= 2 else 0
        self._draw_rect(surf, 14 + lunge * 2, 17, 1, 3 + fang_ext, PALETTE['bone'])
        self._draw_rect(surf, 17 + lunge * 2, 17, 1, 3 + fang_ext, PALETTE['bone'])
        
        # Legs spread for attack
        for i in range(4):
            lx = 8 - i * 2
            ly = 18 + i * 2
            pygame.draw.line(surf, PALETTE['spider_body'], (12, 20), (lx, ly), 2)
            pygame.draw.line(surf, PALETTE['spider_body'], (lx, ly), (lx - 2, ly + 4), 2)
            
            rx = 24 + i * 2
            pygame.draw.line(surf, PALETTE['spider_body'], (22, 20), (rx, ly), 2)
            pygame.draw.line(surf, PALETTE['spider_body'], (rx, ly), (rx + 2, ly + 4), 2)
        
        return surf
    
    def spider_death(self, frame=0):
        """Spider death animation - curling up."""
        surf = self._create_surface()
        
        curl = min(frame * 2, 6)
        
        if frame >= 4:
            # Fully curled/dead
            pygame.draw.ellipse(surf, PALETTE['spider_body'], (10, 20, 12, 8))
            # Legs curled under
            for i in range(4):
                pygame.draw.line(surf, PALETTE['spider_body'], 
                               (11 + i * 2, 22), (11 + i * 2, 26), 2)
        else:
            # Curling
            pygame.draw.ellipse(surf, PALETTE['spider_body'], (10, 16 + curl, 12, 10 - curl))
            pygame.draw.ellipse(surf, PALETTE['spider_body'], (12, 10 + curl, 8, 8))
            
            # Legs folding in
            for i in range(4):
                lx = 10 - (4 - curl) - i
                ly = 18 + curl + i
                pygame.draw.line(surf, PALETTE['spider_body'], (12, 20 + curl), (lx, ly), 2)
                
                rx = 22 + (4 - curl) + i
                pygame.draw.line(surf, PALETTE['spider_body'], (20, 20 + curl), (rx, ly), 2)
        
        return surf
    
    # ==================== ZOMBIE SPRITES ====================
    
    def zombie_idle(self, frame=0):
        """Zombie enemy idle - shambling stance."""
        surf = self._create_surface()
        
        # Slow sway
        sway = 1 if frame % 4 < 2 else -1
        y_off = 1 if frame % 2 == 0 else 0
        
        # Feet (shambling stance)
        self._draw_rect(surf, 9, 28 + y_off, 4, 3, PALETTE['zombie_dark'])
        self._draw_rect(surf, 19, 28 + y_off, 4, 3, PALETTE['zombie_dark'])
        
        # Legs (uneven)
        self._draw_rect(surf, 10, 22 + y_off, 3, 6, PALETTE['zombie_skin'])
        self._draw_rect(surf, 19, 23 + y_off, 3, 5, PALETTE['zombie_skin'])
        
        # Tattered body
        self._draw_rect(surf, 10, 14 + y_off, 12, 8, PALETTE['zombie_skin'])
        # Wounds
        self._draw_pixel(surf, 12, 16 + y_off, PALETTE['zombie_wound'])
        self._draw_pixel(surf, 18, 18 + y_off, PALETTE['zombie_wound'])
        self._draw_pixel(surf, 15, 19 + y_off, PALETTE['zombie_wound'])
        
        # Arms hanging (one raised slightly)
        self._draw_rect(surf, 7, 15 + y_off + sway, 3, 9, PALETTE['zombie_skin'])
        self._draw_rect(surf, 22, 16 + y_off - sway, 3, 10, PALETTE['zombie_skin'])
        
        # Hands/claws
        self._draw_rect(surf, 6, 23 + y_off + sway, 4, 3, PALETTE['zombie_dark'])
        self._draw_rect(surf, 22, 25 + y_off - sway, 4, 3, PALETTE['zombie_dark'])
        
        # Head (tilted)
        self._draw_rect(surf, 11 + sway, 5 + y_off, 10, 9, PALETTE['zombie_skin'])
        self._draw_rect(surf, 12 + sway, 6 + y_off, 8, 7, PALETTE['zombie_dark'])
        
        # Empty eyes
        self._draw_pixel(surf, 13 + sway, 8 + y_off, (200, 200, 100))
        self._draw_pixel(surf, 18 + sway, 8 + y_off, (200, 200, 100))
        
        # Exposed jaw
        self._draw_rect(surf, 13 + sway, 11 + y_off, 6, 2, PALETTE['bone'])
        
        return surf
    
    def zombie_walk(self, frame=0):
        """Zombie shambling walk."""
        surf = self._create_surface()
        
        # Shamble offsets
        leg_offsets = [(0, 0), (3, -1), (0, 0), (-3, -1)]
        l_off = leg_offsets[frame % 4]
        r_off = leg_offsets[(frame + 2) % 4]
        
        sway = [1, 2, 1, 0][frame % 4]
        
        # Feet
        self._draw_rect(surf, 9 + l_off[0], 28, 4, 3, PALETTE['zombie_dark'])
        self._draw_rect(surf, 19 + r_off[0], 28, 4, 3, PALETTE['zombie_dark'])
        
        # Legs
        self._draw_rect(surf, 10 + l_off[0], 22 + l_off[1], 3, 6, PALETTE['zombie_skin'])
        self._draw_rect(surf, 19 + r_off[0], 22 + r_off[1], 3, 6, PALETTE['zombie_skin'])
        
        # Body
        self._draw_rect(surf, 10, 14, 12, 8, PALETTE['zombie_skin'])
        self._draw_pixel(surf, 12, 16, PALETTE['zombie_wound'])
        self._draw_pixel(surf, 18, 18, PALETTE['zombie_wound'])
        
        # Arms reaching forward
        arm_reach = frame % 4
        self._draw_rect(surf, 6 + arm_reach, 14, 4, 8, PALETTE['zombie_skin'])
        self._draw_rect(surf, 22 - arm_reach, 15, 4, 8, PALETTE['zombie_skin'])
        
        # Head
        self._draw_rect(surf, 11 + sway, 5, 10, 9, PALETTE['zombie_skin'])
        self._draw_pixel(surf, 13 + sway, 8, (200, 200, 100))
        self._draw_pixel(surf, 18 + sway, 8, (200, 200, 100))
        self._draw_rect(surf, 13 + sway, 11, 6, 2, PALETTE['bone'])
        
        return surf
    
    def zombie_attack(self, frame=0):
        """Zombie clawing attack."""
        surf = self._create_surface()
        
        # Attack phases
        reach = [0, 4, 6, 3][min(frame, 3)]
        
        # Body leaning forward
        lean = reach // 2
        
        # Feet
        self._draw_rect(surf, 9, 28, 4, 3, PALETTE['zombie_dark'])
        self._draw_rect(surf, 19, 28, 4, 3, PALETTE['zombie_dark'])
        
        # Legs
        self._draw_rect(surf, 10, 22, 3, 6, PALETTE['zombie_skin'])
        self._draw_rect(surf, 19, 22, 3, 6, PALETTE['zombie_skin'])
        
        # Body
        self._draw_rect(surf, 10 + lean, 14, 12, 8, PALETTE['zombie_skin'])
        
        # Arms reaching to attack
        self._draw_rect(surf, 6 + reach, 12, 4, 8, PALETTE['zombie_skin'])
        self._draw_rect(surf, 22 + reach, 11, 4, 8, PALETTE['zombie_skin'])
        
        # Claws extended
        if frame >= 1:
            for i in range(3):
                self._draw_rect(surf, 8 + reach + i * 2, 10 + i, 1, 3, PALETTE['zombie_dark'])
                self._draw_rect(surf, 24 + reach + i * 2, 9 + i, 1, 3, PALETTE['zombie_dark'])
        
        # Head lunging
        self._draw_rect(surf, 11 + lean * 2, 5, 10, 9, PALETTE['zombie_skin'])
        # Open mouth
        self._draw_rect(surf, 13 + lean * 2, 10, 6, 4, PALETTE['zombie_wound'])
        self._draw_rect(surf, 14 + lean * 2, 10, 4, 1, PALETTE['bone'])
        self._draw_rect(surf, 14 + lean * 2, 13, 4, 1, PALETTE['bone'])
        
        return surf
    
    def zombie_death(self, frame=0):
        """Zombie death - falling apart."""
        surf = self._create_surface()
        
        fall = min(frame * 20, 80)
        
        if frame >= 4:
            # Collapsed
            self._draw_rect(surf, 4, 26, 24, 5, PALETTE['zombie_skin'])
            self._draw_rect(surf, 2, 27, 6, 4, PALETTE['zombie_skin'])  # Head
            # Gore
            self._draw_pixel(surf, 8, 27, PALETTE['zombie_wound'])
            self._draw_pixel(surf, 15, 28, PALETTE['zombie_wound'])
            self._draw_pixel(surf, 22, 27, PALETTE['zombie_wound'])
        else:
            tilt = fall / 90
            y_shift = int(tilt * 12)
            
            # Falling body
            self._draw_rect(surf, 10, 14 + y_shift, 12, 8, PALETTE['zombie_skin'])
            self._draw_rect(surf, 11 - int(tilt * 5), 5 + y_shift, 10, 9, PALETTE['zombie_skin'])
            
            # Feet staying in place
            self._draw_rect(surf, 9, 28, 4, 3, PALETTE['zombie_dark'])
            self._draw_rect(surf, 19, 28, 4, 3, PALETTE['zombie_dark'])
        
        return surf
    
    # ==================== ORC SPRITES ====================
    
    def orc_idle(self, frame=0):
        """Orc enemy idle - warrior stance."""
        surf = self._create_surface()
        
        y_off = 1 if frame % 2 == 0 else 0
        
        # Feet
        self._draw_rect(surf, 9, 27 + y_off, 5, 4, PALETTE['orc_dark'])
        self._draw_rect(surf, 18, 27 + y_off, 5, 4, PALETTE['orc_dark'])
        
        # Legs (muscular)
        self._draw_rect(surf, 10, 20 + y_off, 4, 7, PALETTE['orc_skin'])
        self._draw_rect(surf, 18, 20 + y_off, 4, 7, PALETTE['orc_skin'])
        
        # Loincloth/armor
        self._draw_rect(surf, 9, 18 + y_off, 14, 4, PALETTE['orc_armor'])
        
        # Muscular torso
        self._draw_rect(surf, 8, 10 + y_off, 16, 8, PALETTE['orc_skin'])
        self._draw_rect(surf, 10, 11 + y_off, 12, 6, PALETTE['orc_dark'])
        
        # Shoulder armor
        self._draw_rect(surf, 5, 10 + y_off, 4, 5, PALETTE['orc_armor'])
        self._draw_rect(surf, 23, 10 + y_off, 4, 5, PALETTE['orc_armor'])
        
        # Arms
        self._draw_rect(surf, 5, 14 + y_off, 4, 8, PALETTE['orc_skin'])
        self._draw_rect(surf, 23, 14 + y_off, 4, 8, PALETTE['orc_skin'])
        
        # Head (brutish)
        self._draw_rect(surf, 10, 2 + y_off, 12, 9, PALETTE['orc_skin'])
        
        # Lower jaw/underbite
        self._draw_rect(surf, 11, 8 + y_off, 10, 3, PALETTE['orc_dark'])
        
        # Tusks
        self._draw_rect(surf, 12, 8 + y_off, 2, 4, PALETTE['bone'])
        self._draw_rect(surf, 18, 8 + y_off, 2, 4, PALETTE['bone'])
        
        # Angry eyes
        self._draw_pixel(surf, 12, 5 + y_off, (255, 100, 50))
        self._draw_pixel(surf, 19, 5 + y_off, (255, 100, 50))
        
        # Battle axe (held at side)
        self._draw_rect(surf, 26, 8 + y_off, 2, 16, PALETTE['wood'])
        # Axe head
        pygame.draw.polygon(surf, PALETTE['steel'], [
            (28, 10 + y_off), (31, 14 + y_off), (28, 18 + y_off)
        ])
        
        return surf
    
    def orc_walk(self, frame=0):
        """Orc heavy walk."""
        surf = self._create_surface()
        
        # Heavy footsteps
        leg_offsets = [(0, 0), (2, -2), (0, 0), (-2, -2)]
        l_off = leg_offsets[frame % 4]
        r_off = leg_offsets[(frame + 2) % 4]
        
        y_off = 1 if frame % 2 == 0 else 0
        
        # Feet
        self._draw_rect(surf, 9 + l_off[0], 27 + y_off, 5, 4, PALETTE['orc_dark'])
        self._draw_rect(surf, 18 + r_off[0], 27 + y_off, 5, 4, PALETTE['orc_dark'])
        
        # Legs
        self._draw_rect(surf, 10 + l_off[0], 20 + y_off + l_off[1], 4, 7, PALETTE['orc_skin'])
        self._draw_rect(surf, 18 + r_off[0], 20 + y_off + r_off[1], 4, 7, PALETTE['orc_skin'])
        
        # Body (same as idle)
        self._draw_rect(surf, 9, 18 + y_off, 14, 4, PALETTE['orc_armor'])
        self._draw_rect(surf, 8, 10 + y_off, 16, 8, PALETTE['orc_skin'])
        
        # Arms swinging
        arm_swing = [0, 2, 0, -2][frame % 4]
        self._draw_rect(surf, 5, 14 + y_off - arm_swing, 4, 8, PALETTE['orc_skin'])
        self._draw_rect(surf, 23, 14 + y_off + arm_swing, 4, 8, PALETTE['orc_skin'])
        
        # Shoulder armor
        self._draw_rect(surf, 5, 10 + y_off, 4, 5, PALETTE['orc_armor'])
        self._draw_rect(surf, 23, 10 + y_off, 4, 5, PALETTE['orc_armor'])
        
        # Head
        self._draw_rect(surf, 10, 2 + y_off, 12, 9, PALETTE['orc_skin'])
        self._draw_rect(surf, 12, 8 + y_off, 2, 4, PALETTE['bone'])
        self._draw_rect(surf, 18, 8 + y_off, 2, 4, PALETTE['bone'])
        self._draw_pixel(surf, 12, 5 + y_off, (255, 100, 50))
        self._draw_pixel(surf, 19, 5 + y_off, (255, 100, 50))
        
        # Axe moving with arm
        self._draw_rect(surf, 26, 8 + y_off + arm_swing, 2, 16, PALETTE['wood'])
        pygame.draw.polygon(surf, PALETTE['steel'], [
            (28, 10 + y_off + arm_swing), (31, 14 + y_off + arm_swing), (28, 18 + y_off + arm_swing)
        ])
        
        return surf
    
    def orc_attack(self, frame=0):
        """Orc axe attack."""
        surf = self._create_surface()
        
        # Attack phases: wind up, swing, impact
        phases = [
            {'axe_angle': -60, 'lean': 0},
            {'axe_angle': -30, 'lean': 1},
            {'axe_angle': 45, 'lean': 2},
            {'axe_angle': 90, 'lean': 2},
        ]
        phase = phases[min(frame, 3)]
        
        lean = phase['lean']
        
        # Feet
        self._draw_rect(surf, 9, 27, 5, 4, PALETTE['orc_dark'])
        self._draw_rect(surf, 18 + lean, 27, 5, 4, PALETTE['orc_dark'])
        
        # Legs
        self._draw_rect(surf, 10, 20, 4, 7, PALETTE['orc_skin'])
        self._draw_rect(surf, 18 + lean, 20, 4, 7, PALETTE['orc_skin'])
        
        # Body
        self._draw_rect(surf, 8 + lean // 2, 10, 16, 8, PALETTE['orc_skin'])
        
        # Head
        self._draw_rect(surf, 10 + lean, 2, 12, 9, PALETTE['orc_skin'])
        self._draw_rect(surf, 12 + lean, 8, 2, 4, PALETTE['bone'])
        self._draw_rect(surf, 18 + lean, 8, 2, 4, PALETTE['bone'])
        # War cry eyes
        self._draw_pixel(surf, 12 + lean, 5, (255, 50, 50))
        self._draw_pixel(surf, 19 + lean, 5, (255, 50, 50))
        
        # Axe swing arc
        angle = math.radians(phase['axe_angle'])
        axe_len = 18
        ax_start_x = 20 + lean
        ax_start_y = 14
        ax_end_x = int(ax_start_x + math.cos(angle) * axe_len)
        ax_end_y = int(ax_start_y + math.sin(angle) * axe_len)
        
        pygame.draw.line(surf, PALETTE['wood'], (ax_start_x, ax_start_y), (ax_end_x, ax_end_y), 3)
        
        # Axe head at end
        head_angle = angle + math.pi / 2
        hx1 = ax_end_x + int(math.cos(head_angle) * 4)
        hy1 = ax_end_y + int(math.sin(head_angle) * 4)
        hx2 = ax_end_x - int(math.cos(head_angle) * 4)
        hy2 = ax_end_y - int(math.sin(head_angle) * 4)
        pygame.draw.polygon(surf, PALETTE['steel'], [
            (ax_end_x + 2, ax_end_y), (hx1, hy1), (hx2, hy2)
        ])
        
        # Slash effect on impact
        if frame >= 2:
            for i in range(4):
                sx = ax_end_x + int(math.cos(angle + 0.5) * (4 + i * 3))
                sy = ax_end_y + int(math.sin(angle + 0.5) * (4 + i * 3))
                self._draw_pixel(surf, sx, sy, (255, 255, 200))
        
        return surf
    
    def orc_death(self, frame=0):
        """Orc death - falling."""
        surf = self._create_surface()
        
        fall = min(frame * 25, 90)
        
        if frame >= 4:
            # Fallen
            self._draw_rect(surf, 2, 24, 28, 7, PALETTE['orc_skin'])
            self._draw_rect(surf, 0, 25, 8, 5, PALETTE['orc_skin'])  # Head
            # Axe dropped
            self._draw_rect(surf, 24, 28, 8, 2, PALETTE['wood'])
        else:
            tilt = fall / 90
            y_shift = int(tilt * 10)
            
            self._draw_rect(surf, 10 - int(tilt * 4), 20 + y_shift, 4, 7, PALETTE['orc_skin'])
            self._draw_rect(surf, 18, 20 + y_shift, 4, 7, PALETTE['orc_skin'])
            self._draw_rect(surf, 8 - int(tilt * 6), 10 + y_shift, 16, 8, PALETTE['orc_skin'])
            self._draw_rect(surf, 10 - int(tilt * 8), 2 + y_shift, 12, 9, PALETTE['orc_skin'])
        
        return surf
    
    # ==================== DEMON SPRITES ====================
    
    def demon_idle(self, frame=0):
        """Demon boss idle - menacing hover."""
        surf = self._create_surface()
        
        # Hover animation
        hover = [0, -1, -2, -1][frame % 4]
        
        # Wings (spread behind)
        wing_flap = frame % 4
        # Left wing
        pygame.draw.polygon(surf, PALETTE['demon_dark'], [
            (8, 12 + hover), (0, 4 + hover - wing_flap), (4, 18 + hover)
        ])
        # Right wing
        pygame.draw.polygon(surf, PALETTE['demon_dark'], [
            (24, 12 + hover), (31, 4 + hover - wing_flap), (28, 18 + hover)
        ])
        
        # Body
        self._draw_rect(surf, 10, 14 + hover, 12, 10, PALETTE['demon_skin'])
        self._draw_rect(surf, 11, 15 + hover, 10, 8, PALETTE['demon_dark'])
        
        # Cloven feet (hovering)
        self._draw_rect(surf, 11, 26 + hover, 3, 4, PALETTE['demon_dark'])
        self._draw_rect(surf, 18, 26 + hover, 3, 4, PALETTE['demon_dark'])
        
        # Arms
        self._draw_rect(surf, 6, 15 + hover, 4, 7, PALETTE['demon_skin'])
        self._draw_rect(surf, 22, 15 + hover, 4, 7, PALETTE['demon_skin'])
        
        # Clawed hands
        for i in range(3):
            self._draw_pixel(surf, 5 + i, 22 + hover, (40, 20, 20))
            self._draw_pixel(surf, 23 + i, 22 + hover, (40, 20, 20))
        
        # Head
        self._draw_rect(surf, 11, 4 + hover, 10, 10, PALETTE['demon_skin'])
        
        # Horns
        pygame.draw.polygon(surf, PALETTE['demon_horns'], [
            (10, 6 + hover), (8, 0 + hover), (12, 4 + hover)
        ])
        pygame.draw.polygon(surf, PALETTE['demon_horns'], [
            (22, 6 + hover), (24, 0 + hover), (20, 4 + hover)
        ])
        
        # Glowing eyes
        self._draw_pixel(surf, 13, 8 + hover, (255, 200, 0))
        self._draw_pixel(surf, 18, 8 + hover, (255, 200, 0))
        
        # Fanged mouth
        self._draw_rect(surf, 14, 11 + hover, 4, 2, (40, 20, 20))
        self._draw_pixel(surf, 14, 13 + hover, PALETTE['bone'])
        self._draw_pixel(surf, 17, 13 + hover, PALETTE['bone'])
        
        # Fire aura
        if frame % 2 == 0:
            for i in range(3):
                fx = 8 + i * 6
                fy = 28 + hover
                pygame.draw.polygon(surf, PALETTE['fire'], [
                    (fx, fy), (fx - 2, fy + 4), (fx + 2, fy + 4)
                ])
        
        return surf
    
    def demon_walk(self, frame=0):
        """Demon hovering movement."""
        surf = self._create_surface()
        
        # Forward/back motion
        move = [0, 1, 2, 1][frame % 4]
        hover = [0, -1, -2, -1][frame % 4]
        
        # Wings (more active)
        wing_flap = [0, 2, 4, 2][frame % 4]
        pygame.draw.polygon(surf, PALETTE['demon_dark'], [
            (8 + move, 12 + hover), (-2 + move, 2 + hover - wing_flap), (4 + move, 18 + hover)
        ])
        pygame.draw.polygon(surf, PALETTE['demon_dark'], [
            (24 + move, 12 + hover), (34 + move, 2 + hover - wing_flap), (28 + move, 18 + hover)
        ])
        
        # Body
        self._draw_rect(surf, 10 + move, 14 + hover, 12, 10, PALETTE['demon_skin'])
        
        # Feet trailing
        self._draw_rect(surf, 11 + move - 1, 26 + hover, 3, 4, PALETTE['demon_dark'])
        self._draw_rect(surf, 18 + move - 1, 26 + hover, 3, 4, PALETTE['demon_dark'])
        
        # Head
        self._draw_rect(surf, 11 + move, 4 + hover, 10, 10, PALETTE['demon_skin'])
        
        # Horns
        pygame.draw.polygon(surf, PALETTE['demon_horns'], [
            (10 + move, 6 + hover), (8 + move, 0 + hover), (12 + move, 4 + hover)
        ])
        pygame.draw.polygon(surf, PALETTE['demon_horns'], [
            (22 + move, 6 + hover), (24 + move, 0 + hover), (20 + move, 4 + hover)
        ])
        
        # Eyes
        self._draw_pixel(surf, 13 + move, 8 + hover, (255, 200, 0))
        self._draw_pixel(surf, 18 + move, 8 + hover, (255, 200, 0))
        
        return surf
    
    def demon_attack(self, frame=0):
        """Demon fire attack."""
        surf = self._create_surface()
        
        # Attack phases
        charge = [0, 1, 2, 3][min(frame, 3)]
        
        # Wings spread wide
        pygame.draw.polygon(surf, PALETTE['demon_dark'], [
            (8, 12), (-4, 0 - charge), (4, 20)
        ])
        pygame.draw.polygon(surf, PALETTE['demon_dark'], [
            (24, 12), (36, 0 - charge), (28, 20)
        ])
        
        # Body
        self._draw_rect(surf, 10, 14, 12, 10, PALETTE['demon_skin'])
        
        # Arms thrust forward
        arm_reach = charge * 2
        self._draw_rect(surf, 4 + arm_reach, 14, 4, 7, PALETTE['demon_skin'])
        self._draw_rect(surf, 24 + arm_reach, 14, 4, 7, PALETTE['demon_skin'])
        
        # Claws extended
        for i in range(3):
            self._draw_rect(surf, 6 + arm_reach + i * 2, 12 + i, 1, 4, PALETTE['demon_horns'])
            self._draw_rect(surf, 26 + arm_reach + i * 2, 12 + i, 1, 4, PALETTE['demon_horns'])
        
        # Head
        self._draw_rect(surf, 11, 4, 10, 10, PALETTE['demon_skin'])
        
        # Horns
        pygame.draw.polygon(surf, PALETTE['demon_horns'], [
            (10, 6), (6, -2), (12, 4)
        ])
        pygame.draw.polygon(surf, PALETTE['demon_horns'], [
            (22, 6), (26, -2), (20, 4)
        ])
        
        # Eyes blazing
        pygame.draw.circle(surf, (255, 255, 100), (13, 8), 2)
        pygame.draw.circle(surf, (255, 255, 100), (18, 8), 2)
        
        # Fire breath on later frames
        if frame >= 2:
            for i in range(5):
                fx = 20 + arm_reach + i * 3
                fy = 14 + (i % 3) - 1
                color = PALETTE['fire'] if i % 2 == 0 else PALETTE['fire_light']
                pygame.draw.circle(surf, color, (fx, fy), 3 - i // 2)
        
        return surf
    
    def demon_death(self, frame=0):
        """Demon death - dramatic fall."""
        surf = self._create_surface()
        
        fall = min(frame * 20, 80)
        
        if frame >= 4:
            # Collapsed
            self._draw_rect(surf, 4, 24, 24, 8, PALETTE['demon_skin'])
            # Wings crumpled
            pygame.draw.polygon(surf, PALETTE['demon_dark'], [
                (2, 26), (0, 20), (8, 28)
            ])
            pygame.draw.polygon(surf, PALETTE['demon_dark'], [
                (28, 26), (31, 20), (24, 28)
            ])
            # Horns
            self._draw_rect(surf, 2, 24, 4, 2, PALETTE['demon_horns'])
        else:
            tilt = fall / 90
            y_shift = int(tilt * 12)
            
            # Falling with wings folding
            wing_fold = frame * 2
            pygame.draw.polygon(surf, PALETTE['demon_dark'], [
                (8, 12 + y_shift), (4 - wing_fold, 8 + y_shift), (6, 20 + y_shift)
            ])
            pygame.draw.polygon(surf, PALETTE['demon_dark'], [
                (24, 12 + y_shift), (28 + wing_fold, 8 + y_shift), (26, 20 + y_shift)
            ])
            
            # Body
            self._draw_rect(surf, 10 - int(tilt * 4), 14 + y_shift, 12, 10, PALETTE['demon_skin'])
            self._draw_rect(surf, 11 - int(tilt * 6), 4 + y_shift, 10, 10, PALETTE['demon_skin'])
        
        return surf
    
    # ==================== SPELL EFFECT SPRITES ====================
    
    def fireball_projectile(self, frame=0):
        """Fireball projectile sprite."""
        surf = self._create_surface()
        
        cx, cy = 16, 16
        
        # Outer glow
        pygame.draw.circle(surf, (*PALETTE['fire_dark'], 100), (cx, cy), 10)
        pygame.draw.circle(surf, (*PALETTE['fire'], 150), (cx, cy), 7)
        pygame.draw.circle(surf, PALETTE['fire_light'], (cx, cy), 4)
        pygame.draw.circle(surf, (255, 255, 200), (cx, cy), 2)
        
        # Trailing flames
        for i in range(5):
            tx = cx - 4 - i * 2 + (frame % 3 - 1)
            ty = cy + (i % 3 - 1) * 2
            size = 3 - i // 2
            if size > 0:
                pygame.draw.circle(surf, PALETTE['fire'], (tx, ty), size)
        
        return surf
    
    def ice_shard_projectile(self, frame=0):
        """Ice shard projectile sprite."""
        surf = self._create_surface()
        
        cx, cy = 16, 16
        
        # Crystal shape pointing right
        points = [
            (cx + 10, cy),      # Tip
            (cx, cy - 5),       # Top
            (cx - 6, cy),       # Back
            (cx, cy + 5),       # Bottom
        ]
        pygame.draw.polygon(surf, PALETTE['ice'], points)
        pygame.draw.polygon(surf, PALETTE['ice_light'], points, 2)
        
        # Inner highlight
        pygame.draw.line(surf, (255, 255, 255), (cx - 2, cy - 2), (cx + 6, cy), 1)
        
        # Frost trail
        for i in range(4):
            tx = cx - 8 - i * 3
            ty = cy + (frame + i) % 3 - 1
            self._draw_pixel(surf, tx, ty, PALETTE['ice_light'])
        
        return surf
    
    def lightning_bolt_effect(self, frame=0):
        """Lightning bolt effect sprite."""
        surf = self._create_surface()
        
        # Jagged lightning
        points = [(4, 0)]
        x, y = 4, 0
        while y < 32:
            x += (frame % 3 - 1) * 3 + (hash(y + frame) % 5 - 2)
            x = max(4, min(28, x))
            y += 4
            points.append((x, y))
        
        if len(points) >= 2:
            pygame.draw.lines(surf, PALETTE['lightning'], False, points, 3)
            pygame.draw.lines(surf, (255, 255, 255), False, points, 1)
        
        return surf
    
    # ==================== ITEM SPRITES ====================
    
    def potion_health(self):
        """Red health potion."""
        surf = self._create_surface(ITEM_SIZE)
        
        # Bottle
        pygame.draw.ellipse(surf, (200, 50, 50), (3, 6, 10, 9))
        pygame.draw.ellipse(surf, (255, 100, 100), (5, 8, 6, 5))
        
        # Neck
        self._draw_rect(surf, 6, 3, 4, 4, (150, 40, 40))
        
        # Cork
        self._draw_rect(surf, 6, 1, 4, 3, PALETTE['wood'])
        
        return surf
    
    def potion_mana(self):
        """Blue mana potion."""
        surf = self._create_surface(ITEM_SIZE)
        
        # Bottle
        pygame.draw.ellipse(surf, (50, 50, 200), (3, 6, 10, 9))
        pygame.draw.ellipse(surf, (100, 100, 255), (5, 8, 6, 5))
        
        # Neck
        self._draw_rect(surf, 6, 3, 4, 4, (40, 40, 150))
        
        # Cork
        self._draw_rect(surf, 6, 1, 4, 3, PALETTE['wood'])
        
        return surf
    
    def sword_basic(self):
        """Basic sword icon."""
        surf = self._create_surface(ITEM_SIZE)
        
        # Blade
        pygame.draw.polygon(surf, PALETTE['steel'], [
            (8, 1), (10, 1), (10, 10), (9, 12), (8, 10)
        ])
        pygame.draw.line(surf, PALETTE['steel_light'], (9, 2), (9, 9), 1)
        
        # Guard
        self._draw_rect(surf, 5, 10, 6, 2, PALETTE['gold'])
        
        # Handle
        self._draw_rect(surf, 7, 11, 2, 4, PALETTE['wood'])
        
        return surf
    
    def gold_coins(self):
        """Gold coins icon."""
        surf = self._create_surface(ITEM_SIZE)
        
        # Stack of coins
        pygame.draw.ellipse(surf, PALETTE['gold_dark'], (2, 10, 12, 5))
        pygame.draw.ellipse(surf, PALETTE['gold'], (2, 8, 12, 5))
        pygame.draw.ellipse(surf, PALETTE['gold_dark'], (3, 6, 10, 5))
        pygame.draw.ellipse(surf, PALETTE['gold'], (3, 4, 10, 5))
        
        return surf
    
    # ==================== SPELL EFFECT SPRITES ====================
    
    def explosion_effect(self, frame=0):
        """Fire explosion effect."""
        surf = self._create_surface()
        cx, cy = 16, 16
        
        # Expansion based on frame
        size = 4 + frame * 4
        
        # Outer ring
        if size > 4:
            pygame.draw.circle(surf, (*PALETTE['fire_dark'], 150), (cx, cy), size + 4)
        
        # Main explosion
        pygame.draw.circle(surf, PALETTE['fire'], (cx, cy), size)
        pygame.draw.circle(surf, PALETTE['fire_light'], (cx, cy), max(2, size - 4))
        pygame.draw.circle(surf, (255, 255, 200), (cx, cy), max(1, size - 8))
        
        # Debris/sparks
        for i in range(8):
            angle = (i * 45 + frame * 15) * math.pi / 180
            dist = size + 2 + frame
            px = cx + int(math.cos(angle) * dist)
            py = cy + int(math.sin(angle) * dist)
            if 0 <= px < 32 and 0 <= py < 32:
                self._draw_pixel(surf, px, py, PALETTE['fire_light'])
        
        return surf
    
    def heal_aura_effect(self, frame=0):
        """Healing aura effect."""
        surf = self._create_surface()
        cx, cy = 16, 16
        
        # Pulsing ring
        pulse = abs((frame % 4) - 2) * 2
        
        # Outer glow
        pygame.draw.circle(surf, (*PALETTE['heal'], 80), (cx, cy), 12 + pulse)
        
        # Inner healing
        pygame.draw.circle(surf, (*PALETTE['heal'], 150), (cx, cy), 8 + pulse // 2)
        pygame.draw.circle(surf, (200, 255, 200), (cx, cy), 4)
        
        # Rising particles
        for i in range(4):
            py = 24 - frame * 3 - i * 4
            px = 12 + i * 4
            if 0 <= py < 32:
                pygame.draw.circle(surf, PALETTE['heal'], (px, py), 2)
        
        # Cross symbol
        self._draw_rect(surf, 14, 12, 4, 8, (255, 255, 255))
        self._draw_rect(surf, 12, 14, 8, 4, (255, 255, 255))
        
        return surf
    
    def buff_effect(self, frame=0):
        """Generic buff/powerup effect."""
        surf = self._create_surface()
        cx, cy = 16, 16
        
        # Rotating sparkles
        for i in range(6):
            angle = (i * 60 + frame * 30) * math.pi / 180
            dist = 8 + (frame % 2) * 2
            px = cx + int(math.cos(angle) * dist)
            py = cy + int(math.sin(angle) * dist)
            
            color = PALETTE['temple_gold'] if i % 2 == 0 else PALETTE['temple_gold_light']
            pygame.draw.circle(surf, color, (px, py), 3 - i % 2)
        
        # Center glow
        pygame.draw.circle(surf, (*PALETTE['temple_gold'], 100), (cx, cy), 6)
        pygame.draw.circle(surf, PALETTE['temple_gold_light'], (cx, cy), 3)
        
        # Upward arrows
        for i in range(3):
            ax = 10 + i * 6
            ay = 20 - frame * 2
            if 0 <= ay < 32:
                pygame.draw.polygon(surf, (255, 255, 200), [
                    (ax, ay - 4), (ax - 2, ay), (ax + 2, ay)
                ])
        
        return surf
    
    def ice_explosion_effect(self, frame=0):
        """Ice spell impact effect."""
        surf = self._create_surface()
        cx, cy = 16, 16
        
        # Frost burst
        size = 6 + frame * 3
        
        # Crystal shards radiating out
        for i in range(8):
            angle = (i * 45 + 22.5) * math.pi / 180
            dist = size
            px = cx + int(math.cos(angle) * dist)
            py = cy + int(math.sin(angle) * dist)
            
            # Ice shard
            pygame.draw.line(surf, PALETTE['ice'], (cx, cy), (px, py), 2)
            self._draw_pixel(surf, px, py, PALETTE['ice_light'])
        
        # Center frost
        pygame.draw.circle(surf, (*PALETTE['ice'], 150), (cx, cy), size // 2)
        pygame.draw.circle(surf, PALETTE['ice_light'], (cx, cy), size // 4)
        
        # Snowflake particles
        for i in range(6):
            angle = (i * 60 + frame * 20) * math.pi / 180
            dist = size + 4
            px = cx + int(math.cos(angle) * dist)
            py = cy + int(math.sin(angle) * dist)
            if 0 <= px < 32 and 0 <= py < 32:
                self._draw_pixel(surf, px, py, (255, 255, 255))
        
        return surf
    
    def poison_cloud_effect(self, frame=0):
        """Poison cloud effect."""
        surf = self._create_surface()
        cx, cy = 16, 16
        
        # Swirling cloud
        for i in range(5):
            angle = (i * 72 + frame * 25) * math.pi / 180
            dist = 6 + (i % 3) * 2
            px = cx + int(math.cos(angle) * dist)
            py = cy + int(math.sin(angle) * dist)
            
            size = 5 + (frame + i) % 3
            alpha = 150 - i * 20
            pygame.draw.circle(surf, (*PALETTE['poison'], alpha), (px, py), size)
        
        # Bubbles
        for i in range(3):
            bx = 10 + i * 6
            by = 20 - (frame * 2 + i * 3) % 16
            pygame.draw.circle(surf, PALETTE['poison'], (bx, by), 2)
            self._draw_pixel(surf, bx - 1, by - 1, (150, 220, 100))
        
        return surf
    
    # ==================== WEAPON SPRITES ====================
    
    def sword_iron(self):
        """Iron sword icon."""
        surf = self._create_surface(ITEM_SIZE)
        
        # Blade
        pygame.draw.polygon(surf, PALETTE['steel'], [
            (7, 0), (9, 0), (9, 9), (8, 11), (7, 9)
        ])
        pygame.draw.line(surf, PALETTE['steel_light'], (8, 1), (8, 8), 1)
        
        # Guard
        self._draw_rect(surf, 5, 9, 6, 2, PALETTE['steel_dark'])
        
        # Handle
        self._draw_rect(surf, 7, 10, 2, 4, PALETTE['wood'])
        
        # Pommel
        pygame.draw.circle(surf, PALETTE['steel'], (8, 14), 2)
        
        return surf
    
    def sword_flame(self):
        """Flaming sword icon."""
        surf = self._create_surface(ITEM_SIZE)
        
        # Blade with fire
        pygame.draw.polygon(surf, PALETTE['fire'], [
            (7, 0), (9, 0), (9, 9), (8, 11), (7, 9)
        ])
        pygame.draw.line(surf, PALETTE['fire_light'], (8, 1), (8, 8), 1)
        
        # Flames
        for i in range(3):
            fx = 6 + i * 2
            fy = 2 + i
            pygame.draw.polygon(surf, PALETTE['fire_light'], [
                (fx, fy), (fx - 1, fy + 3), (fx + 1, fy + 3)
            ])
        
        # Guard
        self._draw_rect(surf, 5, 9, 6, 2, PALETTE['gold'])
        
        # Handle
        self._draw_rect(surf, 7, 10, 2, 4, PALETTE['wood_dark'])
        
        return surf
    
    def bow_basic(self):
        """Basic bow icon."""
        surf = self._create_surface(ITEM_SIZE)
        
        # Bow curve
        pygame.draw.arc(surf, PALETTE['wood'], (2, 1, 10, 14), -0.5, 3.6, 2)
        
        # String
        pygame.draw.line(surf, (200, 200, 200), (4, 2), (4, 13), 1)
        
        # Arrow
        pygame.draw.line(surf, PALETTE['wood_dark'], (8, 3), (8, 12), 1)
        # Arrow head
        pygame.draw.polygon(surf, PALETTE['steel'], [
            (8, 1), (6, 4), (10, 4)
        ])
        # Fletching
        self._draw_pixel(surf, 7, 11, (200, 50, 50))
        self._draw_pixel(surf, 9, 11, (200, 50, 50))
        
        return surf
    
    def bow_elven(self):
        """Elven bow icon."""
        surf = self._create_surface(ITEM_SIZE)
        
        # Elegant curved bow
        pygame.draw.arc(surf, PALETTE['temple_gold'], (1, 0, 12, 16), -0.3, 3.4, 2)
        
        # Decorative tips
        self._draw_pixel(surf, 3, 1, PALETTE['temple_gold_light'])
        self._draw_pixel(surf, 3, 14, PALETTE['temple_gold_light'])
        
        # String
        pygame.draw.line(surf, (220, 220, 255), (4, 1), (4, 14), 1)
        
        return surf
    
    def staff_basic(self):
        """Basic magic staff icon."""
        surf = self._create_surface(ITEM_SIZE)
        
        # Staff shaft
        self._draw_rect(surf, 7, 4, 2, 12, PALETTE['wood'])
        self._draw_rect(surf, 8, 5, 1, 10, PALETTE['wood_dark'])
        
        # Orb on top
        pygame.draw.circle(surf, PALETTE['ice'], (8, 3), 3)
        pygame.draw.circle(surf, PALETTE['ice_light'], (7, 2), 1)
        
        return surf
    
    def staff_fire(self):
        """Fire staff icon."""
        surf = self._create_surface(ITEM_SIZE)
        
        # Staff shaft
        self._draw_rect(surf, 7, 4, 2, 12, PALETTE['wood_dark'])
        
        # Fire orb
        pygame.draw.circle(surf, PALETTE['fire'], (8, 3), 3)
        pygame.draw.circle(surf, PALETTE['fire_light'], (8, 2), 2)
        
        # Flame effect
        pygame.draw.polygon(surf, PALETTE['fire_light'], [
            (8, 0), (6, 3), (10, 3)
        ])
        
        return surf
    
    def axe_basic(self):
        """Basic axe icon."""
        surf = self._create_surface(ITEM_SIZE)
        
        # Handle
        self._draw_rect(surf, 7, 4, 2, 11, PALETTE['wood'])
        
        # Axe head
        pygame.draw.polygon(surf, PALETTE['steel'], [
            (5, 2), (3, 5), (3, 7), (5, 10), (9, 6)
        ])
        pygame.draw.line(surf, PALETTE['steel_light'], (4, 4), (4, 8), 1)
        
        return surf
    
    def axe_battle(self):
        """Battle axe icon (double-headed)."""
        surf = self._create_surface(ITEM_SIZE)
        
        # Handle
        self._draw_rect(surf, 7, 3, 2, 12, PALETTE['wood'])
        
        # Left head
        pygame.draw.polygon(surf, PALETTE['steel'], [
            (5, 1), (2, 4), (2, 6), (5, 9), (7, 5)
        ])
        # Right head
        pygame.draw.polygon(surf, PALETTE['steel'], [
            (11, 1), (14, 4), (14, 6), (11, 9), (9, 5)
        ])
        
        # Highlights
        pygame.draw.line(surf, PALETTE['steel_light'], (3, 4), (3, 6), 1)
        pygame.draw.line(surf, PALETTE['steel_light'], (13, 4), (13, 6), 1)
        
        return surf
    
    # ==================== ARMOR SPRITES ====================
    
    def helmet_iron(self):
        """Iron helmet icon."""
        surf = self._create_surface(ITEM_SIZE)
        
        # Helmet dome
        pygame.draw.ellipse(surf, PALETTE['steel'], (2, 2, 12, 10))
        pygame.draw.ellipse(surf, PALETTE['steel_light'], (4, 3, 8, 6))
        
        # Face opening
        self._draw_rect(surf, 5, 8, 6, 4, PALETTE['steel_dark'])
        
        # Nose guard
        self._draw_rect(surf, 7, 6, 2, 6, PALETTE['steel'])
        
        return surf
    
    def helmet_knight(self):
        """Knight helmet with visor."""
        surf = self._create_surface(ITEM_SIZE)
        
        # Full helmet
        pygame.draw.ellipse(surf, PALETTE['steel'], (2, 1, 12, 12))
        
        # Visor slots
        for i in range(3):
            self._draw_rect(surf, 4, 5 + i * 2, 8, 1, PALETTE['steel_dark'])
        
        # Plume on top
        self._draw_rect(surf, 7, 0, 2, 3, PALETTE['hero_cape'])
        
        return surf
    
    def helmet_horned(self):
        """Horned viking helmet."""
        surf = self._create_surface(ITEM_SIZE)
        
        # Helmet dome
        pygame.draw.ellipse(surf, PALETTE['steel'], (3, 4, 10, 10))
        
        # Horns
        pygame.draw.polygon(surf, PALETTE['bone'], [
            (2, 5), (0, 0), (5, 5)
        ])
        pygame.draw.polygon(surf, PALETTE['bone'], [
            (14, 5), (16, 0), (11, 5)
        ])
        
        # Face opening
        self._draw_rect(surf, 5, 8, 6, 4, PALETTE['steel_dark'])
        
        return surf
    
    def chest_leather(self):
        """Leather chest armor."""
        surf = self._create_surface(ITEM_SIZE)
        
        # Main body
        self._draw_rect(surf, 2, 3, 12, 10, PALETTE['wood'])
        self._draw_rect(surf, 3, 4, 10, 8, PALETTE['wood_dark'])
        
        # Straps
        self._draw_rect(surf, 4, 2, 2, 3, PALETTE['wood'])
        self._draw_rect(surf, 10, 2, 2, 3, PALETTE['wood'])
        
        # Belt
        self._draw_rect(surf, 2, 11, 12, 2, PALETTE['wood_dark'])
        pygame.draw.circle(surf, PALETTE['gold'], (8, 12), 2)
        
        return surf
    
    def chest_plate(self):
        """Plate chest armor."""
        surf = self._create_surface(ITEM_SIZE)
        
        # Main plate
        self._draw_rect(surf, 2, 2, 12, 11, PALETTE['steel'])
        self._draw_rect(surf, 3, 3, 10, 9, PALETTE['steel_light'])
        
        # Shoulder plates
        self._draw_rect(surf, 0, 3, 4, 4, PALETTE['steel'])
        self._draw_rect(surf, 12, 3, 4, 4, PALETTE['steel'])
        
        # Center ridge
        self._draw_rect(surf, 7, 4, 2, 8, PALETTE['steel_dark'])
        
        # Gold trim
        self._draw_rect(surf, 2, 2, 12, 1, PALETTE['gold'])
        
        return surf
    
    def shield_wooden(self):
        """Wooden shield."""
        surf = self._create_surface(ITEM_SIZE)
        
        # Shield shape
        pygame.draw.ellipse(surf, PALETTE['wood'], (2, 1, 12, 14))
        pygame.draw.ellipse(surf, PALETTE['wood_dark'], (4, 3, 8, 10))
        
        # Metal boss in center
        pygame.draw.circle(surf, PALETTE['steel'], (8, 8), 3)
        pygame.draw.circle(surf, PALETTE['steel_light'], (7, 7), 1)
        
        # Rim
        pygame.draw.ellipse(surf, PALETTE['steel'], (2, 1, 12, 14), 1)
        
        return surf
    
    def shield_tower(self):
        """Tower shield."""
        surf = self._create_surface(ITEM_SIZE)
        
        # Tall rectangular shield
        self._draw_rect(surf, 2, 1, 12, 14, PALETTE['steel'])
        self._draw_rect(surf, 3, 2, 10, 12, PALETTE['hero_armor'])
        
        # Heraldic cross
        self._draw_rect(surf, 7, 3, 2, 10, PALETTE['hero_cape'])
        self._draw_rect(surf, 4, 6, 8, 2, PALETTE['hero_cape'])
        
        # Corner rivets
        for x in [3, 12]:
            for y in [2, 13]:
                self._draw_pixel(surf, x, y, PALETTE['steel_light'])
        
        return surf
    
    # ==================== MORE ITEMS ====================
    
    def scroll(self):
        """Spell scroll icon."""
        surf = self._create_surface(ITEM_SIZE)
        
        # Rolled scroll
        pygame.draw.ellipse(surf, (240, 230, 210), (2, 3, 12, 4))
        self._draw_rect(surf, 2, 5, 12, 8, (240, 230, 210))
        pygame.draw.ellipse(surf, (240, 230, 210), (2, 11, 12, 4))
        
        # Rolled ends
        pygame.draw.ellipse(surf, (220, 210, 190), (2, 2, 12, 3))
        pygame.draw.ellipse(surf, (220, 210, 190), (2, 12, 12, 3))
        
        # Seal/ribbon
        pygame.draw.circle(surf, PALETTE['hero_cape'], (8, 8), 3)
        
        return surf
    
    def ring(self):
        """Magic ring icon."""
        surf = self._create_surface(ITEM_SIZE)
        
        # Ring band
        pygame.draw.circle(surf, PALETTE['gold'], (8, 8), 5, 2)
        
        # Gem on top
        pygame.draw.circle(surf, PALETTE['ice'], (8, 4), 3)
        pygame.draw.circle(surf, PALETTE['ice_light'], (7, 3), 1)
        
        return surf
    
    def amulet(self):
        """Amulet/necklace icon."""
        surf = self._create_surface(ITEM_SIZE)
        
        # Chain
        pygame.draw.arc(surf, PALETTE['gold'], (2, 0, 12, 8), 0, 3.14, 1)
        
        # Pendant base
        pygame.draw.polygon(surf, PALETTE['gold'], [
            (8, 6), (4, 10), (8, 14), (12, 10)
        ])
        
        # Gem
        pygame.draw.circle(surf, PALETTE['temple_red'], (8, 10), 3)
        self._draw_pixel(surf, 7, 9, (255, 150, 150))
        
        return surf
    
    def orb(self):
        """Magic orb icon."""
        surf = self._create_surface(ITEM_SIZE)
        
        # Orb
        pygame.draw.circle(surf, PALETTE['mage_robe'], (8, 8), 6)
        pygame.draw.circle(surf, PALETTE['mage_robe_light'], (8, 8), 5)
        
        # Inner swirl
        pygame.draw.arc(surf, (200, 180, 255), (4, 4, 8, 8), 0, 2, 2)
        
        # Highlight
        pygame.draw.circle(surf, (255, 255, 255), (6, 5), 2)
        
        return surf
    
    # ==================== UI SPRITES ====================
    
    def health_bar_frame(self, width=100, height=12):
        """Health bar frame with decorative border."""
        surf = pygame.Surface((width, height), pygame.SRCALPHA)
        
        # Outer border
        pygame.draw.rect(surf, PALETTE['temple_gold'], (0, 0, width, height), 2)
        
        # Inner bevel
        pygame.draw.rect(surf, PALETTE['temple_gold_light'], (1, 1, width - 2, 1))
        pygame.draw.rect(surf, (40, 30, 20), (1, height - 2, width - 2, 1))
        
        # Corner decorations
        self._draw_pixel(surf, 2, 2, PALETTE['lotus_pink'])
        self._draw_pixel(surf, width - 3, 2, PALETTE['lotus_pink'])
        
        return surf
    
    def health_bar_fill(self, width=96, height=8, pct=1.0):
        """Health bar fill with gradient."""
        surf = pygame.Surface((int(width * pct), height), pygame.SRCALPHA)
        
        if pct <= 0:
            return surf
        
        fill_width = int(width * pct)
        
        # Color based on health percentage
        if pct > 0.6:
            color1, color2 = (100, 200, 80), (60, 160, 50)
        elif pct > 0.3:
            color1, color2 = (220, 180, 40), (180, 140, 20)
        else:
            color1, color2 = (200, 60, 60), (150, 40, 40)
        
        # Gradient fill
        for x in range(fill_width):
            t = x / max(1, fill_width)
            r = int(color1[0] * (1 - t) + color2[0] * t)
            g = int(color1[1] * (1 - t) + color2[1] * t)
            b = int(color1[2] * (1 - t) + color2[2] * t)
            pygame.draw.line(surf, (r, g, b), (x, 0), (x, height - 1))
        
        # Highlight on top
        pygame.draw.line(surf, (255, 255, 255, 100), (0, 0), (fill_width - 1, 0))
        
        return surf
    
    def mana_bar_frame(self, width=100, height=10):
        """Mana bar frame with arcane styling."""
        surf = pygame.Surface((width, height), pygame.SRCALPHA)
        
        # Outer border - blue tint
        pygame.draw.rect(surf, PALETTE['temple_teal'], (0, 0, width, height), 2)
        
        # Inner bevel
        pygame.draw.rect(surf, (100, 150, 180), (1, 1, width - 2, 1))
        pygame.draw.rect(surf, (20, 40, 60), (1, height - 2, width - 2, 1))
        
        return surf
    
    def mana_bar_fill(self, width=96, height=6, pct=1.0):
        """Mana bar fill with magical glow."""
        surf = pygame.Surface((int(width * pct), height), pygame.SRCALPHA)
        
        if pct <= 0:
            return surf
        
        fill_width = int(width * pct)
        
        # Blue gradient
        color1, color2 = (80, 140, 220), (40, 80, 180)
        
        for x in range(fill_width):
            t = x / max(1, fill_width)
            r = int(color1[0] * (1 - t) + color2[0] * t)
            g = int(color1[1] * (1 - t) + color2[1] * t)
            b = int(color1[2] * (1 - t) + color2[2] * t)
            pygame.draw.line(surf, (r, g, b), (x, 0), (x, height - 1))
        
        # Magical sparkle
        pygame.draw.line(surf, (200, 220, 255), (0, 0), (fill_width - 1, 0))
        
        return surf
    
    def action_bar_slot(self, size=48, active=False, cooldown_pct=0):
        """Action bar slot frame."""
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        
        # Background
        bg_color = (50, 45, 60) if not active else (70, 65, 90)
        pygame.draw.rect(surf, bg_color, (0, 0, size, size))
        
        # Border
        border_color = PALETTE['temple_gold'] if active else (80, 75, 90)
        pygame.draw.rect(surf, border_color, (0, 0, size, size), 2)
        
        # Inner bevel
        pygame.draw.line(surf, (90, 85, 100), (2, 2), (size - 3, 2))
        pygame.draw.line(surf, (90, 85, 100), (2, 2), (2, size - 3))
        pygame.draw.line(surf, (30, 25, 40), (2, size - 3), (size - 3, size - 3))
        pygame.draw.line(surf, (30, 25, 40), (size - 3, 2), (size - 3, size - 3))
        
        # Cooldown overlay
        if cooldown_pct > 0:
            cooldown_height = int((size - 4) * cooldown_pct)
            cooldown_surf = pygame.Surface((size - 4, cooldown_height), pygame.SRCALPHA)
            cooldown_surf.fill((0, 0, 0, 150))
            surf.blit(cooldown_surf, (2, 2))
        
        # Corner decorations
        self._draw_pixel(surf, 3, 3, PALETTE['temple_teal'])
        self._draw_pixel(surf, size - 4, 3, PALETTE['temple_teal'])
        self._draw_pixel(surf, 3, size - 4, PALETTE['temple_teal'])
        self._draw_pixel(surf, size - 4, size - 4, PALETTE['temple_teal'])
        
        return surf
    
    def minimap_frame(self, size=120):
        """Minimap frame with decorative border."""
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        
        # Background
        pygame.draw.rect(surf, (20, 18, 25), (0, 0, size, size))
        
        # Ornate border
        pygame.draw.rect(surf, PALETTE['temple_gold'], (0, 0, size, size), 3)
        pygame.draw.rect(surf, PALETTE['sandstone_dark'], (2, 2, size - 4, size - 4), 1)
        
        # Corner flourishes
        for corner in [(4, 4), (size - 12, 4), (4, size - 12), (size - 12, size - 12)]:
            x, y = corner
            pygame.draw.polygon(surf, PALETTE['temple_gold_light'], [
                (x + 4, y), (x + 8, y + 4), (x + 4, y + 8), (x, y + 4)
            ])
        
        return surf
    
    def portrait_frame(self, size=64):
        """Character portrait frame."""
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        
        # Background
        pygame.draw.rect(surf, (30, 28, 35), (0, 0, size, size))
        
        # Ornate gold border
        pygame.draw.rect(surf, PALETTE['temple_gold'], (0, 0, size, size), 3)
        pygame.draw.rect(surf, PALETTE['temple_gold_light'], (2, 2, size - 4, size - 4), 1)
        
        # Inner shadow
        pygame.draw.rect(surf, (20, 18, 25), (4, 4, size - 8, size - 8), 1)
        
        # Corner lotus decorations
        for corner in [(2, 2), (size - 10, 2), (2, size - 10), (size - 10, size - 10)]:
            x, y = corner
            self._draw_pixel(surf, x + 3, y + 3, PALETTE['lotus_pink'])
            self._draw_pixel(surf, x + 4, y + 3, PALETTE['lotus_pink'])
            self._draw_pixel(surf, x + 3, y + 4, PALETTE['lotus_pink'])
            self._draw_pixel(surf, x + 4, y + 4, PALETTE['temple_saffron'])
        
        return surf
    
    def button_frame(self, width=80, height=24, pressed=False):
        """UI button frame."""
        surf = pygame.Surface((width, height), pygame.SRCALPHA)
        
        if pressed:
            # Pressed state
            pygame.draw.rect(surf, PALETTE['sandstone_dark'], (0, 0, width, height))
            pygame.draw.rect(surf, (40, 35, 30), (0, 0, width, height), 2)
            # Inverted bevel
            pygame.draw.line(surf, (30, 25, 20), (2, 2), (width - 3, 2))
            pygame.draw.line(surf, (100, 95, 80), (2, height - 3), (width - 3, height - 3))
        else:
            # Normal state
            pygame.draw.rect(surf, PALETTE['sandstone'], (0, 0, width, height))
            pygame.draw.rect(surf, PALETTE['temple_gold'], (0, 0, width, height), 2)
            # Normal bevel
            pygame.draw.line(surf, PALETTE['sandstone_light'], (2, 2), (width - 3, 2))
            pygame.draw.line(surf, PALETTE['sandstone_dark'], (2, height - 3), (width - 3, height - 3))
        
        return surf
    
    def tooltip_frame(self, width=150, height=80):
        """Tooltip background frame."""
        surf = pygame.Surface((width, height), pygame.SRCALPHA)
        
        # Semi-transparent background
        pygame.draw.rect(surf, (20, 18, 30, 230), (0, 0, width, height))
        
        # Border
        pygame.draw.rect(surf, PALETTE['temple_teal'], (0, 0, width, height), 1)
        pygame.draw.rect(surf, PALETTE['temple_gold'], (1, 1, width - 2, height - 2), 1)
        
        return surf
    
    # ==================== INDIAN TEMPLE ENVIRONMENT ====================
    
    def temple_floor(self, variant=0):
        """Indian temple floor tile with intricate patterns."""
        surf = self._create_surface(TILE_SIZE)
        
        # Base sandstone
        surf.fill(PALETTE['sandstone'])
        
        # Add slight texture variation
        for i in range(8):
            for j in range(8):
                if (i + j + variant) % 3 == 0:
                    self._draw_rect(surf, i*4, j*4, 4, 4, PALETTE['sandstone_light'])
                elif (i + j + variant) % 5 == 0:
                    self._draw_rect(surf, i*4, j*4, 4, 4, PALETTE['sandstone_dark'])
        
        # Decorative border pattern
        border_color = PALETTE['temple_teal']
        # Top and bottom borders
        self._draw_rect(surf, 0, 0, 32, 2, border_color)
        self._draw_rect(surf, 0, 30, 32, 2, border_color)
        # Left and right borders  
        self._draw_rect(surf, 0, 0, 2, 32, border_color)
        self._draw_rect(surf, 30, 0, 2, 32, border_color)
        
        # Corner lotus motifs
        if variant % 2 == 0:
            self._draw_lotus_corner(surf, 2, 2)
            self._draw_lotus_corner(surf, 26, 2)
            self._draw_lotus_corner(surf, 2, 26)
            self._draw_lotus_corner(surf, 26, 26)
        
        return surf
    
    def _draw_lotus_corner(self, surf, x, y):
        """Draw small lotus motif at corner."""
        # Simple 4-petal lotus
        c = PALETTE['lotus_pink']
        self._draw_pixel(surf, x, y, c)
        self._draw_pixel(surf, x+1, y, c)
        self._draw_pixel(surf, x, y+1, c)
        self._draw_pixel(surf, x+1, y+1, PALETTE['temple_gold'])
    
    def temple_floor_ornate(self):
        """Ornate temple floor with mandala pattern."""
        surf = self._create_surface(TILE_SIZE)
        
        # Base marble
        surf.fill(PALETTE['marble'])
        
        # Marble veins
        for i in range(3):
            start_x = (i * 11) % 32
            for y in range(32):
                x = start_x + (y % 5) - 2
                if 0 <= x < 32:
                    self._draw_pixel(surf, x, y, PALETTE['marble_vein'])
        
        # Central mandala circle
        cx, cy = 16, 16
        pygame.draw.circle(surf, PALETTE['temple_gold'], (cx, cy), 10, 2)
        pygame.draw.circle(surf, PALETTE['temple_teal'], (cx, cy), 7, 1)
        pygame.draw.circle(surf, PALETTE['temple_red'], (cx, cy), 4, 1)
        pygame.draw.circle(surf, PALETTE['temple_saffron'], (cx, cy), 2)
        
        # Radiating petals
        for angle in range(0, 360, 45):
            rad = math.radians(angle)
            px = cx + int(math.cos(rad) * 12)
            py = cy + int(math.sin(rad) * 12)
            self._draw_pixel(surf, px, py, PALETTE['temple_gold'])
            self._draw_pixel(surf, px+1, py, PALETTE['temple_gold_light'])
        
        return surf
    
    def temple_wall(self):
        """Indian temple wall with carved patterns."""
        surf = self._create_surface(TILE_SIZE)
        
        # Base terracotta/sandstone
        surf.fill(PALETTE['terracotta'])
        
        # Stone block pattern
        for row in range(4):
            y = row * 8
            offset = (row % 2) * 8
            for col in range(5):
                x = offset + col * 16 - 8
                if 0 <= x < 32:
                    # Block outline
                    pygame.draw.rect(surf, PALETTE['terracotta_dark'], (x, y, 15, 7), 1)
        
        # Carved elephant motif in center
        self._draw_elephant(surf, 8, 8)
        
        return surf
    
    def _draw_elephant(self, surf, x, y):
        """Draw small elephant carving."""
        c = PALETTE['sandstone_dark']
        # Body
        self._draw_rect(surf, x+4, y+6, 8, 6, c)
        # Head
        self._draw_rect(surf, x+10, y+4, 5, 5, c)
        # Trunk
        self._draw_rect(surf, x+14, y+6, 2, 6, c)
        # Legs
        self._draw_rect(surf, x+5, y+11, 2, 4, c)
        self._draw_rect(surf, x+9, y+11, 2, 4, c)
        # Ear
        self._draw_pixel(surf, x+11, y+3, c)
        # Tusk
        self._draw_pixel(surf, x+13, y+8, PALETTE['bone'])
    
    def temple_pillar(self):
        """Ornate temple pillar."""
        surf = self._create_surface(TILE_SIZE)
        surf.fill((0, 0, 0, 0))  # Transparent
        
        # Pillar base (wider)
        self._draw_rect(surf, 8, 26, 16, 6, PALETTE['sandstone_dark'])
        self._draw_rect(surf, 10, 28, 12, 4, PALETTE['sandstone'])
        
        # Main pillar shaft
        self._draw_rect(surf, 11, 6, 10, 20, PALETTE['sandstone'])
        self._draw_rect(surf, 12, 8, 8, 16, PALETTE['sandstone_light'])
        
        # Decorative bands
        for band_y in [8, 14, 20]:
            self._draw_rect(surf, 10, band_y, 12, 2, PALETTE['temple_gold'])
            self._draw_rect(surf, 11, band_y, 10, 1, PALETTE['temple_gold_light'])
        
        # Capital (top decoration)
        self._draw_rect(surf, 8, 2, 16, 4, PALETTE['sandstone'])
        # Lotus capital
        self._draw_rect(surf, 10, 0, 12, 3, PALETTE['lotus_pink'])
        self._draw_rect(surf, 12, 1, 8, 2, PALETTE['lotus_white'])
        
        return surf
    
    def temple_stairs(self):
        """Temple stairs with decorative edges."""
        surf = self._create_surface(TILE_SIZE)
        
        # Stair steps
        for i in range(4):
            step_y = 24 - i * 6
            step_width = 32 - i * 4
            step_x = i * 2
            
            # Step top
            self._draw_rect(surf, step_x, step_y, step_width, 4, PALETTE['sandstone_light'])
            # Step front
            self._draw_rect(surf, step_x, step_y + 4, step_width, 2, PALETTE['sandstone_dark'])
        
        # Gold trim on edges
        self._draw_rect(surf, 0, 24, 2, 8, PALETTE['temple_gold'])
        self._draw_rect(surf, 30, 24, 2, 8, PALETTE['temple_gold'])
        
        # Arrow indicator
        pygame.draw.polygon(surf, PALETTE['temple_saffron'], [
            (16, 2), (12, 8), (20, 8)
        ])
        
        return surf
    
    def temple_door(self):
        """Ornate temple door."""
        surf = self._create_surface(TILE_SIZE)
        
        # Door frame
        self._draw_rect(surf, 4, 0, 24, 32, PALETTE['wood_dark'])
        
        # Door panels
        self._draw_rect(surf, 6, 2, 9, 28, PALETTE['wood'])
        self._draw_rect(surf, 17, 2, 9, 28, PALETTE['wood'])
        
        # Decorative carvings on each panel
        # Left panel - sun
        pygame.draw.circle(surf, PALETTE['temple_gold'], (10, 10), 4)
        for angle in range(0, 360, 45):
            rad = math.radians(angle)
            px = 10 + int(math.cos(rad) * 6)
            py = 10 + int(math.sin(rad) * 6)
            self._draw_pixel(surf, px, py, PALETTE['temple_gold'])
        
        # Right panel - moon
        pygame.draw.circle(surf, PALETTE['lotus_white'], (22, 10), 4)
        pygame.draw.circle(surf, PALETTE['wood'], (24, 9), 3)  # Crescent effect
        
        # Door handles
        pygame.draw.circle(surf, PALETTE['temple_gold'], (8, 18), 2)
        pygame.draw.circle(surf, PALETTE['temple_gold'], (24, 18), 2)
        
        # Bottom lotus border
        for x in range(6, 26, 4):
            self._draw_pixel(surf, x, 28, PALETTE['lotus_pink'])
            self._draw_pixel(surf, x+1, 28, PALETTE['lotus_pink'])
        
        return surf
    
    def temple_altar(self):
        """Sacred altar with offerings."""
        surf = self._create_surface(TILE_SIZE)
        surf.fill((0, 0, 0, 0))
        
        # Altar base
        self._draw_rect(surf, 4, 22, 24, 10, PALETTE['sandstone_dark'])
        self._draw_rect(surf, 6, 20, 20, 8, PALETTE['sandstone'])
        
        # Altar top surface
        self._draw_rect(surf, 6, 18, 20, 3, PALETTE['marble'])
        
        # Flame/diya (oil lamp)
        cx = 16
        # Lamp base
        pygame.draw.ellipse(surf, PALETTE['temple_gold'], (12, 14, 8, 4))
        # Flame
        pygame.draw.polygon(surf, PALETTE['fire_light'], [
            (16, 6), (13, 14), (19, 14)
        ])
        pygame.draw.polygon(surf, PALETTE['fire'], [
            (16, 8), (14, 13), (18, 13)
        ])
        
        # Flowers/offerings on sides
        self._draw_pixel(surf, 8, 17, PALETTE['lotus_pink'])
        self._draw_pixel(surf, 9, 17, PALETTE['lotus_white'])
        self._draw_pixel(surf, 22, 17, PALETTE['temple_saffron'])
        self._draw_pixel(surf, 23, 17, PALETTE['lotus_pink'])
        
        return surf
    
    def temple_statue(self):
        """Temple deity statue."""
        surf = self._create_surface(TILE_SIZE)
        surf.fill((0, 0, 0, 0))
        
        # Pedestal
        self._draw_rect(surf, 8, 26, 16, 6, PALETTE['sandstone_dark'])
        self._draw_rect(surf, 10, 28, 12, 4, PALETTE['sandstone'])
        
        # Statue body (seated figure)
        self._draw_rect(surf, 11, 16, 10, 10, PALETTE['temple_gold'])
        
        # Head with crown
        self._draw_rect(surf, 12, 8, 8, 8, PALETTE['temple_gold'])
        # Crown
        self._draw_rect(surf, 11, 4, 10, 5, PALETTE['temple_gold_light'])
        pygame.draw.polygon(surf, PALETTE['temple_gold_light'], [
            (16, 0), (11, 6), (21, 6)
        ])
        
        # Face details
        self._draw_pixel(surf, 14, 11, PALETTE['temple_teal'])  # Eye
        self._draw_pixel(surf, 18, 11, PALETTE['temple_teal'])  # Eye
        
        # Multiple arms (4 arms like many Hindu deities)
        self._draw_rect(surf, 7, 14, 4, 2, PALETTE['temple_gold'])
        self._draw_rect(surf, 21, 14, 4, 2, PALETTE['temple_gold'])
        self._draw_rect(surf, 5, 18, 4, 2, PALETTE['temple_gold'])
        self._draw_rect(surf, 23, 18, 4, 2, PALETTE['temple_gold'])
        
        # Aura/glow
        pygame.draw.circle(surf, (*PALETTE['temple_saffron'], 50), (16, 12), 14)
        
        return surf
    
    def water_pool(self, frame=0):
        """Sacred temple pool/water feature."""
        surf = self._create_surface(TILE_SIZE)
        
        # Pool base
        surf.fill(PALETTE['temple_teal_dark'])
        
        # Water ripples (animated)
        for i in range(3):
            radius = 6 + i * 4 + (frame % 4)
            alpha = 150 - i * 40
            ripple_color = (*PALETTE['temple_teal'], alpha)
            pygame.draw.circle(surf, ripple_color, (16, 16), radius, 1)
        
        # Lotus flowers floating
        lotus_positions = [(8, 10), (22, 14), (12, 24)]
        for i, (lx, ly) in enumerate(lotus_positions):
            offset = (frame + i) % 4 - 2
            # Petals
            for angle in range(0, 360, 60):
                rad = math.radians(angle)
                px = lx + int(math.cos(rad) * 3)
                py = ly + offset + int(math.sin(rad) * 2)
                self._draw_pixel(surf, px, py, PALETTE['lotus_pink'])
            # Center
            self._draw_pixel(surf, lx, ly + offset, PALETTE['temple_saffron'])
        
        # Stone border
        self._draw_rect(surf, 0, 0, 32, 2, PALETTE['sandstone_dark'])
        self._draw_rect(surf, 0, 30, 32, 2, PALETTE['sandstone_dark'])
        self._draw_rect(surf, 0, 0, 2, 32, PALETTE['sandstone_dark'])
        self._draw_rect(surf, 30, 0, 2, 32, PALETTE['sandstone_dark'])
        
        return surf


# Global sprite generator instance
sprite_gen = PixelSpriteGenerator()


def get_hero_sprites():
    """Get all hero animation sprite sheets."""
    gen = sprite_gen
    # Create directional walk animations
    walk_frames = {
        0: [gen.hero_walk(i, direction=0) for i in range(4)],  # Down
        1: [gen.hero_walk(i, direction=1) for i in range(4)],  # Left
        2: [gen.hero_walk(i, direction=2) for i in range(4)],  # Right
        3: [gen.hero_walk(i, direction=3) for i in range(4)],  # Up
    }
    return {
        'idle': SpriteSheet([gen.hero_idle(i) for i in range(4)], 0.3),
        'walk': DirectionalSpriteSheet(walk_frames, 0.12),
        'attack': SpriteSheet([gen.hero_attack(i) for i in range(4)], 0.1),
        'cast': SpriteSheet([gen.hero_cast(i) for i in range(4)], 0.15),
        'death': SpriteSheet([gen.hero_death(i) for i in range(5)], 0.2),
    }


def get_mage_sprites():
    """Get all mage animation sprite sheets."""
    gen = sprite_gen
    # Create directional walk animations for mage
    walk_frames = {
        0: [gen.mage_walk(i, direction=0) for i in range(4)],  # Down
        1: [gen.mage_walk(i, direction=1) for i in range(4)],  # Left
        2: [gen.mage_walk(i, direction=2) for i in range(4)],  # Right
        3: [gen.mage_walk(i, direction=3) for i in range(4)],  # Up
    }
    return {
        'idle': SpriteSheet([gen.mage_idle(i) for i in range(4)], 0.3),
        'walk': DirectionalSpriteSheet(walk_frames, 0.12),
        'cast': SpriteSheet([gen.mage_cast(i) for i in range(4)], 0.15),
    }


def get_skeleton_sprites():
    """Get all skeleton animation sprite sheets."""
    gen = sprite_gen
    return {
        'idle': SpriteSheet([gen.skeleton_idle(i) for i in range(4)], 0.3),
        'attack': SpriteSheet([gen.skeleton_attack(i) for i in range(4)], 0.1),
    }


def get_spider_sprites():
    """Get all spider animation sprite sheets."""
    gen = sprite_gen
    return {
        'idle': SpriteSheet([gen.spider_idle(i) for i in range(4)], 0.15),
        'walk': SpriteSheet([gen.spider_walk(i) for i in range(4)], 0.12),
        'attack': SpriteSheet([gen.spider_attack(i) for i in range(4)], 0.1),
        'death': SpriteSheet([gen.spider_death(i) for i in range(5)], 0.2),
    }


def get_zombie_sprites():
    """Get all zombie animation sprite sheets."""
    gen = sprite_gen
    return {
        'idle': SpriteSheet([gen.zombie_idle(i) for i in range(4)], 0.35),
        'walk': SpriteSheet([gen.zombie_walk(i) for i in range(4)], 0.2),
        'attack': SpriteSheet([gen.zombie_attack(i) for i in range(4)], 0.12),
        'death': SpriteSheet([gen.zombie_death(i) for i in range(5)], 0.25),
    }


def get_orc_sprites():
    """Get all orc animation sprite sheets."""
    gen = sprite_gen
    return {
        'idle': SpriteSheet([gen.orc_idle(i) for i in range(4)], 0.3),
        'walk': SpriteSheet([gen.orc_walk(i) for i in range(4)], 0.15),
        'attack': SpriteSheet([gen.orc_attack(i) for i in range(4)], 0.1),
        'death': SpriteSheet([gen.orc_death(i) for i in range(5)], 0.2),
    }


def get_demon_sprites():
    """Get all demon/boss animation sprite sheets."""
    gen = sprite_gen
    return {
        'idle': SpriteSheet([gen.demon_idle(i) for i in range(4)], 0.2),
        'walk': SpriteSheet([gen.demon_walk(i) for i in range(4)], 0.15),
        'attack': SpriteSheet([gen.demon_attack(i) for i in range(4)], 0.12),
        'death': SpriteSheet([gen.demon_death(i) for i in range(5)], 0.25),
    }


def get_spell_sprites():
    """Get spell effect sprites."""
    gen = sprite_gen
    return {
        'fireball': SpriteSheet([gen.fireball_projectile(i) for i in range(4)], 0.1),
        'ice_shard': SpriteSheet([gen.ice_shard_projectile(i) for i in range(4)], 0.1),
        'lightning': SpriteSheet([gen.lightning_bolt_effect(i) for i in range(4)], 0.05),
    }


def get_spell_effect_sprites():
    """Get spell impact/effect sprites."""
    gen = sprite_gen
    return {
        'explosion': SpriteSheet([gen.explosion_effect(i) for i in range(6)], 0.08),
        'heal_aura': SpriteSheet([gen.heal_aura_effect(i) for i in range(4)], 0.15),
        'buff': SpriteSheet([gen.buff_effect(i) for i in range(4)], 0.12),
        'ice_explosion': SpriteSheet([gen.ice_explosion_effect(i) for i in range(5)], 0.1),
        'poison_cloud': SpriteSheet([gen.poison_cloud_effect(i) for i in range(4)], 0.2),
    }


def get_weapon_sprites():
    """Get weapon icon sprites."""
    gen = sprite_gen
    return {
        'sword_basic': gen.sword_basic(),
        'sword_iron': gen.sword_iron(),
        'sword_flame': gen.sword_flame(),
        'bow_basic': gen.bow_basic(),
        'bow_elven': gen.bow_elven(),
        'staff_basic': gen.staff_basic(),
        'staff_fire': gen.staff_fire(),
        'axe_basic': gen.axe_basic(),
        'axe_battle': gen.axe_battle(),
    }


def get_armor_sprites():
    """Get armor icon sprites."""
    gen = sprite_gen
    return {
        'helmet_iron': gen.helmet_iron(),
        'helmet_knight': gen.helmet_knight(),
        'helmet_horned': gen.helmet_horned(),
        'chest_leather': gen.chest_leather(),
        'chest_plate': gen.chest_plate(),
        'shield_wooden': gen.shield_wooden(),
        'shield_tower': gen.shield_tower(),
    }


def get_item_sprites():
    """Get item icons."""
    gen = sprite_gen
    return {
        'health_potion': gen.potion_health(),
        'mana_potion': gen.potion_mana(),
        'sword': gen.sword_basic(),
        'gold': gen.gold_coins(),
        'scroll': gen.scroll(),
        'ring': gen.ring(),
        'amulet': gen.amulet(),
        'orb': gen.orb(),
    }


def get_ui_sprites():
    """Get UI element sprites."""
    gen = sprite_gen
    return {
        'health_bar_frame': gen.health_bar_frame(),
        'mana_bar_frame': gen.mana_bar_frame(),
        'action_slot': gen.action_bar_slot(),
        'action_slot_active': gen.action_bar_slot(active=True),
        'minimap_frame': gen.minimap_frame(),
        'portrait_frame': gen.portrait_frame(),
        'button': gen.button_frame(),
        'button_pressed': gen.button_frame(pressed=True),
        'tooltip_frame': gen.tooltip_frame(),
    }


def get_environment_tiles():
    """Get Indian temple environment tiles."""
    gen = sprite_gen
    return {
        # Floor variations
        'floor': gen.temple_floor(0),
        'floor_v1': gen.temple_floor(1),
        'floor_v2': gen.temple_floor(2),
        'floor_ornate': gen.temple_floor_ornate(),
        
        # Walls
        'wall': gen.temple_wall(),
        
        # Special tiles
        'stairs': gen.temple_stairs(),
        'door': gen.temple_door(),
        'pillar': gen.temple_pillar(),
        'altar': gen.temple_altar(),
        'statue': gen.temple_statue(),
        
        # Water (animated)
        'water': SpriteSheet([gen.water_pool(i) for i in range(4)], 0.3),
    }

