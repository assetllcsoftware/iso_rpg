"""Sprite loading and management using pixel art generator."""

import os
import pygame
from typing import Dict, Optional, Tuple, List

from .pixel_sprites import PixelSpriteGenerator, HERO_SIZE, CHAR_SIZE
from ..ecs.components.rendering import AnimationState
from ..ecs.components.transform import Direction


def load_sprite_with_white_bg(
    filepath: str,
    threshold: int = 250,
    target_size: Optional[Tuple[int, int]] = None
) -> pygame.Surface:
    """
    Load a JPG/BMP/PNG image and convert white background to transparent.
    Automatically scales to target size.
    
    Args:
        filepath: Path to the image file
        threshold: Pixels with R,G,B all >= threshold are treated as white (default 250)
        target_size: (width, height) to scale to. If None, keeps original size.
        
    Returns:
        pygame.Surface with alpha channel (white pixels made transparent)
    """
    # Load the image
    image = pygame.image.load(filepath)
    
    # Convert to a format we can manipulate (before scaling for quality)
    image = image.convert_alpha()
    
    # Get original size
    orig_w, orig_h = image.get_size()
    
    # Process at original size first (better quality), then scale
    # Create new surface with alpha
    result = pygame.Surface((orig_w, orig_h), pygame.SRCALPHA)
    
    # Use PixelArray for faster processing
    try:
        px_array = pygame.PixelArray(image)
        for y in range(orig_h):
            for x in range(orig_w):
                color = image.unmap_rgb(px_array[x, y])
                r, g, b = color[0], color[1], color[2]
                a = color[3] if len(color) > 3 else 255
                
                # Check if pixel is "white" (all channels above threshold)
                if r >= threshold and g >= threshold and b >= threshold:
                    result.set_at((x, y), (r, g, b, 0))
                else:
                    result.set_at((x, y), (r, g, b, a))
        del px_array
    except Exception:
        # Fallback to slower method
        for y in range(orig_h):
            for x in range(orig_w):
                r, g, b, a = image.get_at((x, y))
                if r >= threshold and g >= threshold and b >= threshold:
                    result.set_at((x, y), (r, g, b, 0))
                else:
                    result.set_at((x, y), (r, g, b, 255))
    
    # Scale to target size if specified
    if target_size and target_size != (orig_w, orig_h):
        result = pygame.transform.smoothscale(result, target_size)
    
    return result


def load_spritesheet_with_white_bg(
    filepath: str,
    frame_width: int,
    frame_height: int,
    num_frames: int,
    threshold: int = 250,
    scale: Optional[Tuple[int, int]] = None
) -> List[pygame.Surface]:
    """
    Load a spritesheet (horizontal strip) and split into frames.
    
    Args:
        filepath: Path to the spritesheet image
        frame_width: Width of each frame in the original image
        frame_height: Height of each frame in the original image
        num_frames: Number of frames to extract
        threshold: White threshold for transparency
        scale: Optional (width, height) to scale each frame to
        
    Returns:
        List of pygame.Surface frames with transparency
    """
    # Load the full sheet
    sheet = pygame.image.load(filepath).convert_alpha()
    
    frames = []
    for i in range(num_frames):
        # Extract frame at original size
        frame = pygame.Surface((frame_width, frame_height), pygame.SRCALPHA)
        frame.blit(sheet, (0, 0), (i * frame_width, 0, frame_width, frame_height))
        
        # Process transparency at original size (better quality)
        result = pygame.Surface((frame_width, frame_height), pygame.SRCALPHA)
        
        for y in range(frame_height):
            for x in range(frame_width):
                r, g, b, a = frame.get_at((x, y))
                if r >= threshold and g >= threshold and b >= threshold:
                    result.set_at((x, y), (r, g, b, 0))
                else:
                    result.set_at((x, y), (r, g, b, a if a < 255 else 255))
        
        # Scale AFTER transparency processing for better edges
        if scale and scale != (frame_width, frame_height):
            result = pygame.transform.smoothscale(result, scale)
        
        frames.append(result)
    
    return frames


# Faster version using pygame's colorkey (simpler, less flexible)
def load_sprite_colorkey(
    filepath: str,
    colorkey: Tuple[int, int, int] = (255, 255, 255),
    scale: Optional[Tuple[int, int]] = None
) -> pygame.Surface:
    """
    Load an image using pygame's built-in colorkey transparency.
    Faster than per-pixel threshold but requires exact color match.
    
    Args:
        filepath: Path to the image file
        colorkey: The exact RGB color to make transparent (default white)
        scale: Optional (width, height) to scale the sprite to
        
    Returns:
        pygame.Surface with colorkey transparency set
    """
    image = pygame.image.load(filepath).convert()
    
    # Set the colorkey BEFORE scaling for better quality
    image.set_colorkey(colorkey)
    
    if scale:
        # Convert to alpha surface, scale, then back
        alpha_surf = image.convert_alpha()
        alpha_surf = pygame.transform.smoothscale(alpha_surf, scale)
        return alpha_surf
    
    return image.convert_alpha()


class SpriteManager:
    """Loads and manages all game sprites using the pixel art generator."""
    
    # Path to external sprite assets
    ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "assets", "sprites")
    
    def __init__(self):
        self.generator = PixelSpriteGenerator()
        self.sprites: Dict[str, Dict] = {}
        self.loaded = False
        
        # Placeholder surfaces for missing sprites
        self._placeholders: Dict[Tuple[int, int], pygame.Surface] = {}
        
        # External sprite cache
        self._external_sprites: Dict[str, pygame.Surface] = {}
    
    def load_all(self):
        """Load all sprite assets using the pixel generator."""
        if self.loaded:
            return
        
        # Generate hero sprites
        self._generate_hero_sprites()
        
        # Generate mage/ally sprites
        self._generate_mage_sprites()
        
        # Generate enemy sprites
        self._generate_enemy_sprites()
        
        # Generate item sprites
        self._generate_item_sprites()
        
        # Generate effect sprites
        self._generate_effect_sprites()
        
        # Load any external sprites that were processed
        self.load_processed_sprites()
        
        self.loaded = True
    
    def _generate_hero_sprites(self):
        """Generate hero character sprites."""
        self.sprites["hero"] = {}
        
        # Idle animation (4 frames)
        idle_frames = {
            Direction.DOWN: [self.generator.hero_idle(i) for i in range(4)],
            Direction.LEFT: [self.generator.hero_idle(i) for i in range(4)],
            Direction.RIGHT: [pygame.transform.flip(self.generator.hero_idle(i), True, False) for i in range(4)],
            Direction.UP: [self.generator.hero_idle(i) for i in range(4)],
        }
        self.sprites["hero"][AnimationState.IDLE] = idle_frames
        
        # Walk animation (8 frames)
        walk_frames = {
            Direction.DOWN: [self.generator.hero_walk(i, 0) for i in range(8)],
            Direction.LEFT: [self.generator.hero_walk(i, 1) for i in range(8)],
            Direction.RIGHT: [self.generator.hero_walk(i, 2) for i in range(8)],
            Direction.UP: [self.generator.hero_walk(i, 3) for i in range(8)],
        }
        self.sprites["hero"][AnimationState.WALK] = walk_frames
        
        # Attack animation (4 frames)
        attack_frames = {
            Direction.DOWN: [self.generator.hero_attack(i) for i in range(4)],
            Direction.LEFT: [self.generator.hero_attack(i) for i in range(4)],
            Direction.RIGHT: [pygame.transform.flip(self.generator.hero_attack(i), True, False) for i in range(4)],
            Direction.UP: [self.generator.hero_attack(i) for i in range(4)],
        }
        self.sprites["hero"][AnimationState.ATTACK] = attack_frames
        
        # Cast animation
        cast_frames = {
            Direction.DOWN: [self.generator.hero_cast(i) for i in range(6)],
            Direction.LEFT: [self.generator.hero_cast(i) for i in range(6)],
            Direction.RIGHT: [pygame.transform.flip(self.generator.hero_cast(i), True, False) for i in range(6)],
            Direction.UP: [self.generator.hero_cast(i) for i in range(6)],
        }
        self.sprites["hero"][AnimationState.CAST] = cast_frames
        
        # Death animation
        death_frames = {
            Direction.DOWN: [self.generator.hero_death(i) for i in range(4)],
            Direction.LEFT: [self.generator.hero_death(i) for i in range(4)],
            Direction.RIGHT: [pygame.transform.flip(self.generator.hero_death(i), True, False) for i in range(4)],
            Direction.UP: [self.generator.hero_death(i) for i in range(4)],
        }
        self.sprites["hero"][AnimationState.DEATH] = death_frames
        self.sprites["hero"][AnimationState.DOWNED] = death_frames
        
        # Spin attack animation (24 frames = 3 full rotations)
        spin_frames = {
            Direction.DOWN: [self.generator.hero_spin(i) for i in range(24)],
            Direction.LEFT: [self.generator.hero_spin(i) for i in range(24)],
            Direction.RIGHT: [self.generator.hero_spin(i) for i in range(24)],  # Same for all directions (spinning)
            Direction.UP: [self.generator.hero_spin(i) for i in range(24)],
        }
        self.sprites["hero"][AnimationState.SPIN] = spin_frames
        
        # Leap strike animation (10 frames - epic jump with massive impact)
        leap_frames = {
            Direction.DOWN: [self.generator.hero_leap(i) for i in range(10)],
            Direction.LEFT: [self.generator.hero_leap(i) for i in range(10)],
            Direction.RIGHT: [pygame.transform.flip(self.generator.hero_leap(i), True, False) for i in range(10)],
            Direction.UP: [self.generator.hero_leap(i) for i in range(10)],
        }
        self.sprites["hero"][AnimationState.LEAP] = leap_frames
        
        # Heavy strike animation (10 frames)
        heavy_frames = {
            Direction.DOWN: [self.generator.hero_heavy(i) for i in range(10)],
            Direction.LEFT: [self.generator.hero_heavy(i) for i in range(10)],
            Direction.RIGHT: [pygame.transform.flip(self.generator.hero_heavy(i), True, False) for i in range(10)],
            Direction.UP: [self.generator.hero_heavy(i) for i in range(10)],
        }
        self.sprites["hero"][AnimationState.HEAVY] = heavy_frames
        
        # Bash animation (8 frames) - shield bash lunge
        bash_frames = {
            Direction.DOWN: [self.generator.hero_bash(i) for i in range(8)],
            Direction.LEFT: [self.generator.hero_bash(i) for i in range(8)],
            Direction.RIGHT: [pygame.transform.flip(self.generator.hero_bash(i), True, False) for i in range(8)],
            Direction.UP: [self.generator.hero_bash(i) for i in range(8)],
        }
        self.sprites["hero"][AnimationState.BASH] = bash_frames
    
    def _generate_mage_sprites(self):
        """Generate mage/Lyra character sprites."""
        self.sprites["lyra"] = {}
        
        # Idle animation
        idle_frames = {
            Direction.DOWN: [self.generator.mage_idle(i) for i in range(4)],
            Direction.LEFT: [self.generator.mage_idle(i) for i in range(4)],
            Direction.RIGHT: [pygame.transform.flip(self.generator.mage_idle(i), True, False) for i in range(4)],
            Direction.UP: [self.generator.mage_idle(i) for i in range(4)],
        }
        self.sprites["lyra"][AnimationState.IDLE] = idle_frames
        
        # Walk animation
        walk_frames = {
            Direction.DOWN: [self.generator.mage_walk(i, 0) for i in range(8)],
            Direction.LEFT: [self.generator.mage_walk(i, 1) for i in range(8)],
            Direction.RIGHT: [self.generator.mage_walk(i, 2) for i in range(8)],
            Direction.UP: [self.generator.mage_walk(i, 3) for i in range(8)],
        }
        self.sprites["lyra"][AnimationState.WALK] = walk_frames
        
        # Cast animation
        cast_frames = {
            Direction.DOWN: [self.generator.mage_cast(i) for i in range(6)],
            Direction.LEFT: [self.generator.mage_cast(i) for i in range(6)],
            Direction.RIGHT: [pygame.transform.flip(self.generator.mage_cast(i), True, False) for i in range(6)],
            Direction.UP: [self.generator.mage_cast(i) for i in range(6)],
        }
        self.sprites["lyra"][AnimationState.CAST] = cast_frames
        self.sprites["lyra"][AnimationState.ATTACK] = cast_frames
        
        # Death animation
        death_frames = {
            Direction.DOWN: [self.generator.mage_death(i) for i in range(4)],
            Direction.LEFT: [self.generator.mage_death(i) for i in range(4)],
            Direction.RIGHT: [pygame.transform.flip(self.generator.mage_death(i), True, False) for i in range(4)],
            Direction.UP: [self.generator.mage_death(i) for i in range(4)],
        }
        self.sprites["lyra"][AnimationState.DEATH] = death_frames
        self.sprites["lyra"][AnimationState.DOWNED] = death_frames
    
    def _generate_enemy_sprites(self):
        """Generate enemy sprites, using external if available."""
        # Try loading external skeleton sprites first
        skeleton_external = self._load_external_character_sprites("skeleton1")
        if skeleton_external:
            self.sprites["skeleton"] = skeleton_external
            print("Using external skeleton sprites")
        else:
            # Fallback to procedural
            self.sprites["skeleton"] = self._generate_simple_enemy(
                self.generator.skeleton_idle,
                self.generator.skeleton_attack,
            )
        
        # Try loading external goblin sprites
        goblin_external = self._load_external_character_sprites("goblin1")
        if goblin_external:
            self.sprites["goblin"] = goblin_external
            print("Using external goblin sprites")
        
        # Spider - has walk
        self.sprites["spider"] = self._generate_enemy_with_walk(
            self.generator.spider_idle,
            self.generator.spider_walk,
            self.generator.spider_attack,
            self.generator.spider_death,
        )
        
        # Zombie - has walk
        self.sprites["zombie"] = self._generate_enemy_with_walk(
            self.generator.zombie_idle,
            self.generator.zombie_walk,
            self.generator.zombie_attack,
            self.generator.zombie_death,
        )
        
        # Orc - has walk
        self.sprites["orc"] = self._generate_enemy_with_walk(
            self.generator.orc_idle,
            self.generator.orc_walk,
            self.generator.orc_attack,
            self.generator.orc_death,
        )
        
        # Demon - has walk
        self.sprites["demon"] = self._generate_enemy_with_walk(
            self.generator.demon_idle,
            self.generator.demon_walk,
            self.generator.demon_attack,
            self.generator.demon_death,
        )
    
    def _load_external_character_sprites(self, base_name: str) -> Optional[Dict]:
        """
        Load external character sprites with facing/away and idle/attack variants.
        
        Expected files:
            {base_name}_twords.png      - facing camera, idle
            {base_name}_twords_attack.png - facing camera, attack
            {base_name}_away.png        - facing away, idle  
            {base_name}_away_attack.png - facing away, attack
            {base_name}_defeated.png    - death/downed state
        
        Returns:
            Dict with AnimationState -> Direction -> frames, or None if not found
        """
        enemy_dir = os.path.join(self.ASSETS_DIR, "enemy")
        
        # Check if files exist
        files = {
            'twords': os.path.join(enemy_dir, f"{base_name}_twords.png"),
            'twords_attack': os.path.join(enemy_dir, f"{base_name}_twords_attack.png"),
            'away': os.path.join(enemy_dir, f"{base_name}_away.png"),
            'away_attack': os.path.join(enemy_dir, f"{base_name}_away_attack.png"),
            'defeated': os.path.join(enemy_dir, f"{base_name}_defeated.png"),
        }
        
        # Check at least the basic ones exist
        if not os.path.exists(files['twords']) or not os.path.exists(files['away']):
            return None
        
        try:
            # Load sprites
            sprites = {}
            for key, path in files.items():
                if os.path.exists(path):
                    sprites[key] = pygame.image.load(path).convert_alpha()
            
            # Build the sprite set
            # Facing camera (twords) = DOWN direction
            # Facing away = UP direction
            # LEFT/RIGHT = flipped versions
            
            sprite_set = {}
            
            # IDLE: twords for DOWN, away for UP
            twords_idle = sprites.get('twords')
            away_idle = sprites.get('away')
            
            if twords_idle and away_idle:
                idle_frames = {
                    Direction.DOWN: [twords_idle],  # Facing camera
                    Direction.UP: [away_idle],      # Facing away
                    Direction.LEFT: [twords_idle],  # Use facing camera
                    Direction.RIGHT: [pygame.transform.flip(twords_idle, True, False)],
                }
                sprite_set[AnimationState.IDLE] = idle_frames
                sprite_set[AnimationState.WALK] = idle_frames  # Use idle for walk too
            
            # ATTACK: twords_attack for DOWN, away_attack for UP
            twords_attack = sprites.get('twords_attack', twords_idle)
            away_attack = sprites.get('away_attack', away_idle)
            
            if twords_attack and away_attack:
                attack_frames = {
                    Direction.DOWN: [twords_attack],
                    Direction.UP: [away_attack],
                    Direction.LEFT: [twords_attack],
                    Direction.RIGHT: [pygame.transform.flip(twords_attack, True, False)],
                }
                sprite_set[AnimationState.ATTACK] = attack_frames
                sprite_set[AnimationState.CAST] = attack_frames
            
            # DEATH: use defeated sprite if available, else fall back to idle
            defeated_sprite = sprites.get('defeated')
            if defeated_sprite:
                death_frames = {
                    Direction.DOWN: [defeated_sprite],
                    Direction.UP: [defeated_sprite],
                    Direction.LEFT: [defeated_sprite],
                    Direction.RIGHT: [pygame.transform.flip(defeated_sprite, True, False)],
                }
                sprite_set[AnimationState.DEATH] = death_frames
                sprite_set[AnimationState.DOWNED] = death_frames
            else:
                sprite_set[AnimationState.DEATH] = sprite_set.get(AnimationState.IDLE, {})
                sprite_set[AnimationState.DOWNED] = sprite_set.get(AnimationState.IDLE, {})
            
            return sprite_set
            
        except Exception as e:
            print(f"Error loading external character sprites for {base_name}: {e}")
            return None
    
    def _generate_simple_enemy(self, idle_fn, attack_fn):
        """Generate sprites for enemy with just idle and attack (like skeleton)."""
        sprite_set = {}
        
        # Idle
        idle_frames = self._make_directional_frames(idle_fn, 4)
        sprite_set[AnimationState.IDLE] = idle_frames
        sprite_set[AnimationState.WALK] = idle_frames  # Use idle for walk
        
        # Attack
        attack_frames = self._make_directional_frames(attack_fn, 4)
        sprite_set[AnimationState.ATTACK] = attack_frames
        sprite_set[AnimationState.CAST] = attack_frames
        
        # Death - use idle for now
        sprite_set[AnimationState.DEATH] = idle_frames
        sprite_set[AnimationState.DOWNED] = idle_frames
        
        return sprite_set
    
    def _generate_enemy_with_walk(self, idle_fn, walk_fn, attack_fn, death_fn):
        """Generate sprites for enemy with walk animation."""
        sprite_set = {}
        
        # Idle
        idle_frames = self._make_directional_frames(idle_fn, 4)
        sprite_set[AnimationState.IDLE] = idle_frames
        
        # Walk (no direction param, use flip for sides)
        walk_frames = self._make_directional_frames(walk_fn, 4)
        sprite_set[AnimationState.WALK] = walk_frames
        
        # Attack
        attack_frames = self._make_directional_frames(attack_fn, 4)
        sprite_set[AnimationState.ATTACK] = attack_frames
        sprite_set[AnimationState.CAST] = attack_frames
        
        # Death
        death_frames = self._make_directional_frames(death_fn, 4)
        sprite_set[AnimationState.DEATH] = death_frames
        sprite_set[AnimationState.DOWNED] = death_frames
        
        return sprite_set
    
    def _make_directional_frames(self, fn, num_frames):
        """Make frames for all 4 directions from a function that only takes frame number."""
        frames = [fn(i) for i in range(num_frames)]
        flipped = [pygame.transform.flip(f, True, False) for f in frames]
        
        return {
            Direction.DOWN: frames,
            Direction.LEFT: frames,
            Direction.RIGHT: flipped,
            Direction.UP: frames,
        }
    
    def _generate_item_sprites(self):
        """Generate item sprites."""
        # Weapons
        self.sprites["iron_sword"] = self.generator.sword_iron()
        self.sprites["steel_sword"] = self.generator.sword_basic()
        self.sprites["fire_sword"] = self.generator.sword_flame()
        
        # Potions
        self.sprites["health_potion"] = self.generator.potion_health()
        self.sprites["mana_potion"] = self.generator.potion_mana()
        
        # Gold
        self.sprites["gold"] = self.generator.gold_coins()
        
        # Default
        self.sprites["item_default"] = self.generator.gold_coins()
    
    def _generate_effect_sprites(self):
        """Generate spell effect sprites."""
        # Projectiles
        self.sprites["projectile_fire"] = self.generator.fireball_projectile(0)
        self.sprites["projectile_ice"] = self.generator.ice_shard_projectile(0)
        self.sprites["projectile_lightning"] = self.generator.lightning_bolt_effect(0)
        
        # AOE effects
        self.sprites["aoe_fire"] = self.generator.explosion_effect(0)
        self.sprites["aoe_ice"] = self.generator.ice_explosion_effect(0)
    
    def get_character_frame(
        self,
        sprite_set: str,
        anim_state: AnimationState,
        direction: Direction,
        frame: int
    ) -> pygame.Surface:
        """Get a specific character animation frame."""
        if sprite_set not in self.sprites:
            return self._get_placeholder(HERO_SIZE, HERO_SIZE)
        
        sprite_data = self.sprites[sprite_set]
        if not isinstance(sprite_data, dict):
            return sprite_data if isinstance(sprite_data, pygame.Surface) else self._get_placeholder(HERO_SIZE, HERO_SIZE)
        
        original_state = anim_state
        if anim_state not in sprite_data:
            anim_state = AnimationState.IDLE
        
        frames_by_dir = sprite_data.get(anim_state, {})
        frames = frames_by_dir.get(direction, frames_by_dir.get(Direction.DOWN, []))
        
        if not frames:
            return self._get_placeholder(HERO_SIZE, HERO_SIZE)
        
        # For death/downed states that fell back to IDLE, always use frame 0 to prevent flickering
        if original_state in (AnimationState.DEATH, AnimationState.DOWNED) and anim_state == AnimationState.IDLE:
            return frames[0]
        
        return frames[frame % len(frames)]
    
    def get_item_sprite(self, sprite_name: str) -> pygame.Surface:
        """Get an item sprite."""
        if sprite_name in self.sprites:
            sprite = self.sprites[sprite_name]
            if isinstance(sprite, pygame.Surface):
                return sprite
        
        return self._get_placeholder(16, 16)
    
    def get_effect_sprite(self, effect_name: str) -> pygame.Surface:
        """Get an effect sprite."""
        if effect_name in self.sprites:
            sprite = self.sprites[effect_name]
            if isinstance(sprite, pygame.Surface):
                return sprite
        
        return self._get_placeholder(24, 24)
    
    def _get_placeholder(self, width: int, height: int) -> pygame.Surface:
        """Get or create a placeholder surface."""
        key = (width, height)
        if key not in self._placeholders:
            surf = pygame.Surface((width, height), pygame.SRCALPHA)
            pygame.draw.rect(surf, (255, 0, 255), (0, 0, width, height))
            pygame.draw.line(surf, (0, 0, 0), (0, 0), (width, height))
            pygame.draw.line(surf, (0, 0, 0), (width, 0), (0, height))
            self._placeholders[key] = surf
        
        return self._placeholders[key]
    
    def load_external_sprite(
        self, 
        name: str, 
        filename: str,
        sprite_type: str = "character",
        threshold: int = 250,
        use_colorkey: bool = False
    ) -> pygame.Surface:
        """
        Load an external sprite image (JPG/BMP/PNG) with white background removal.
        Automatically scales based on sprite_type.
        
        Args:
            name: Name to register the sprite under
            filename: Filename (looked up in assets/sprites/)
            sprite_type: Type determines auto-scaling:
                - "hero" / "player" -> 48x48 (HERO_SIZE)
                - "character" / "enemy" / "ally" -> 32x32 (CHAR_SIZE)
                - "item" -> 16x16
                - "icon" -> 24x24
                - "large" -> 64x64
                - "huge" -> 96x96
                - "decoration" -> 48x48
                - "original" -> no scaling
            threshold: White threshold for transparency (default 250)
            use_colorkey: Use faster colorkey method (requires exact white)
            
        Returns:
            The loaded pygame.Surface
            
        Example:
            # Just drop "boss.jpg" in assets/sprites/ and call:
            sprite_mgr.load_external_sprite("boss", "boss.jpg", "large")
        """
        # Determine target size based on type
        size_map = {
            "hero": (HERO_SIZE, HERO_SIZE),
            "player": (HERO_SIZE, HERO_SIZE),
            "character": (CHAR_SIZE, CHAR_SIZE),
            "enemy": (CHAR_SIZE, CHAR_SIZE),
            "ally": (CHAR_SIZE, CHAR_SIZE),
            "item": (16, 16),
            "icon": (24, 24),
            "large": (64, 64),
            "huge": (96, 96),
            "boss": (96, 96),
            "decoration": (48, 48),
            "prop": (40, 40),
            "original": None,
        }
        target_size = size_map.get(sprite_type.lower(), (CHAR_SIZE, CHAR_SIZE))
        
        filepath = os.path.join(self.ASSETS_DIR, filename)
        
        if not os.path.exists(filepath):
            print(f"Warning: Sprite file not found: {filepath}")
            sz = target_size or (32, 32)
            return self._get_placeholder(sz[0], sz[1])
        
        try:
            if use_colorkey:
                sprite = load_sprite_colorkey(filepath, scale=target_size)
            else:
                sprite = load_sprite_with_white_bg(filepath, threshold=threshold, target_size=target_size)
            
            self.sprites[name] = sprite
            self._external_sprites[name] = sprite
            print(f"Loaded external sprite: {name} ({sprite.get_width()}x{sprite.get_height()})")
            return sprite
        except Exception as e:
            print(f"Error loading sprite {filename}: {e}")
            sz = target_size or (32, 32)
            return self._get_placeholder(sz[0], sz[1])
    
    def load_external_animation(
        self,
        name: str,
        filename: str,
        num_frames: int,
        sprite_type: str = "character",
        threshold: int = 250
    ) -> List[pygame.Surface]:
        """
        Load an external spritesheet (horizontal strip) for animations.
        Auto-detects frame size from image dimensions.
        
        Args:
            name: Base name to register frames under
            filename: Filename (looked up in assets/sprites/)
            num_frames: Number of frames in the strip
            sprite_type: Type for auto-scaling (see load_external_sprite)
            threshold: White threshold for transparency
            
        Returns:
            List of pygame.Surfaces
            
        Example:
            # Put "boss_attack.jpg" (a horizontal strip) in assets/sprites/
            # If it's 256x64 with 4 frames, just call:
            frames = sprite_mgr.load_external_animation("boss_attack", "boss_attack.jpg", 4, "large")
        """
        # Determine target size
        size_map = {
            "hero": (HERO_SIZE, HERO_SIZE),
            "player": (HERO_SIZE, HERO_SIZE),
            "character": (CHAR_SIZE, CHAR_SIZE),
            "enemy": (CHAR_SIZE, CHAR_SIZE),
            "ally": (CHAR_SIZE, CHAR_SIZE),
            "item": (16, 16),
            "large": (64, 64),
            "huge": (96, 96),
            "boss": (96, 96),
            "original": None,
        }
        target_size = size_map.get(sprite_type.lower(), (CHAR_SIZE, CHAR_SIZE))
        
        filepath = os.path.join(self.ASSETS_DIR, filename)
        
        if not os.path.exists(filepath):
            print(f"Warning: Spritesheet not found: {filepath}")
            sz = target_size or (32, 32)
            return [self._get_placeholder(sz[0], sz[1])] * num_frames
        
        try:
            # Load to get dimensions
            sheet = pygame.image.load(filepath)
            sheet_w, sheet_h = sheet.get_size()
            
            # Auto-detect frame size (assume horizontal strip)
            frame_width = sheet_w // num_frames
            frame_height = sheet_h
            
            print(f"Loading spritesheet: {filename} ({sheet_w}x{sheet_h}) -> {num_frames} frames of {frame_width}x{frame_height}")
            
            frames = load_spritesheet_with_white_bg(
                filepath, frame_width, frame_height, num_frames,
                threshold=threshold, scale=target_size
            )
            
            # Register each frame
            for i, frame in enumerate(frames):
                self.sprites[f"{name}_{i}"] = frame
            
            # Also register the list
            self.sprites[name] = frames
            
            sz = target_size or (frame_width, frame_height)
            print(f"Loaded animation: {name} ({num_frames} frames at {sz[0]}x{sz[1]})")
            return frames
        except Exception as e:
            print(f"Error loading spritesheet {filename}: {e}")
            import traceback
            traceback.print_exc()
            sz = target_size or (32, 32)
            return [self._get_placeholder(sz[0], sz[1])] * num_frames
    
    def load_all_from_folder(self, subfolder: str = "", sprite_type: str = "character") -> int:
        """
        Load ALL images from a folder automatically.
        Names are derived from filenames (without extension).
        
        Args:
            subfolder: Subfolder within assets/sprites/ (e.g., "enemies")
            sprite_type: Type for auto-scaling
            
        Returns:
            Number of sprites loaded
            
        Example:
            # Put enemy1.jpg, enemy2.bmp, boss.png in assets/sprites/enemies/
            sprite_mgr.load_all_from_folder("enemies", "enemy")
            # Now use sprite_mgr.sprites["enemy1"], sprite_mgr.sprites["boss"], etc.
        """
        folder = os.path.join(self.ASSETS_DIR, subfolder) if subfolder else self.ASSETS_DIR
        
        if not os.path.exists(folder):
            print(f"Warning: Folder not found: {folder}")
            return 0
        
        count = 0
        extensions = ('.jpg', '.jpeg', '.bmp', '.png', '.gif')
        
        for filename in os.listdir(folder):
            if filename.lower().endswith(extensions):
                # Get name without extension
                name = os.path.splitext(filename)[0]
                
                # Load it
                full_path = os.path.join(subfolder, filename) if subfolder else filename
                self.load_external_sprite(name, full_path, sprite_type)
                count += 1
        
        print(f"Loaded {count} sprites from {folder}")
        return count
    
    def load_processed_sprites(self) -> int:
        """
        Load all sprites that were processed by tools/process_sprites.py.
        Uses the sprite_mapping.json file to know what's available.
        
        Returns:
            Number of sprites loaded
        """
        import json
        
        mapping_file = os.path.join(self.ASSETS_DIR, "sprite_mapping.json")
        
        if not os.path.exists(mapping_file):
            return 0
        
        try:
            with open(mapping_file) as f:
                mapping = json.load(f)
        except Exception as e:
            print(f"Error reading sprite mapping: {e}")
            return 0
        
        count = 0
        for name, info in mapping.items():
            filepath = os.path.join(self.ASSETS_DIR, info["file"])
            
            if not os.path.exists(filepath):
                continue
            
            try:
                # These are already processed PNGs with transparency
                sprite = pygame.image.load(filepath).convert_alpha()
                self.sprites[name] = sprite
                self._external_sprites[name] = sprite
                count += 1
            except Exception as e:
                print(f"Error loading {name}: {e}")
        
        if count > 0:
            print(f"Loaded {count} processed sprites from mapping")
        
        return count
