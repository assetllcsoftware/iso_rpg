#!/usr/bin/env python3
"""
Sprite Processor - Drop images in assets/raw/ and run this script.

It will:
1. Scan assets/raw/ for all images
2. Remove white backgrounds
3. Resize to game sprite sizes
4. Save processed sprites to assets/sprites/
5. Generate a mapping file

Naming Convention (optional but helpful):
    hero_idle_1.jpg      -> hero idle animation frame 1
    skeleton_walk.bmp    -> skeleton walk sprite
    boss_attack_1.png    -> boss attack animation frame 1
    random_enemy.jpg     -> enemy sprite named "random_enemy"
    
Or just name them anything - the script will ask what type each one is.

Usage:
    pipenv run python tools/process_sprites.py
    pipenv run python tools/process_sprites.py --auto   # Auto-detect types from names
    pipenv run python tools/process_sprites.py --type enemy  # Process all as enemy type
"""

import os
import sys
import json
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Initialize pygame for image processing
import pygame
pygame.init()

# Create a tiny hidden display (needed for some pygame operations)
try:
    pygame.display.set_mode((1, 1), pygame.HIDDEN)
except:
    # Fallback for systems without HIDDEN support
    os.environ['SDL_VIDEODRIVER'] = 'dummy'
    pygame.display.set_mode((1, 1))

# Paths
RAW_DIR = project_root / "assets" / "raw"
SPRITES_DIR = project_root / "assets" / "sprites"
MAPPING_FILE = SPRITES_DIR / "sprite_mapping.json"

# Size presets
SIZES = {
    "hero": (48, 48),
    "player": (48, 48),
    "ally": (48, 48),
    "lyra": (48, 48),
    "mage": (48, 48),
    "enemy": (32, 32),
    "character": (32, 32),
    "skeleton": (32, 32),
    "spider": (32, 32),
    "zombie": (32, 32),
    "orc": (32, 32),
    "demon": (32, 32),
    "item": (16, 16),
    "potion": (16, 16),
    "weapon": (16, 16),
    "armor": (16, 16),
    "icon": (24, 24),
    "large": (64, 64),
    "boss": (96, 96),
    "huge": (96, 96),
    "decoration": (48, 48),
    "prop": (40, 40),
    "barrel": (40, 50),
    "chest": (45, 40),
    "tile": (32, 32),
}

# Known character/enemy names for auto-detection
KNOWN_TYPES = {
    "hero": "hero",
    "player": "hero",
    "warrior": "hero",
    "lyra": "ally",
    "mage": "ally",
    "ally": "ally",
    "skeleton": "enemy",
    "spider": "enemy",
    "zombie": "enemy",
    "orc": "enemy",
    "demon": "enemy",
    "goblin": "enemy",
    "slime": "enemy",
    "boss": "boss",
    "dragon": "boss",
    "potion": "item",
    "sword": "item",
    "staff": "item",
    "armor": "item",
    "shield": "item",
    "barrel": "prop",
    "chest": "prop",
    "crate": "prop",
    "urn": "prop",
}

# Animation states
ANIM_STATES = ["idle", "walk", "attack", "cast", "death", "hit", "run"]


def remove_white_background(surface: pygame.Surface, threshold: int = 250) -> pygame.Surface:
    """Remove white background from pygame surface."""
    width, height = surface.get_size()
    result = pygame.Surface((width, height), pygame.SRCALPHA)
    
    # Convert to format with alpha if needed
    if surface.get_alpha() is None and not surface.get_flags() & pygame.SRCALPHA:
        surface = surface.convert_alpha()
    
    for y in range(height):
        for x in range(width):
            try:
                color = surface.get_at((x, y))
                r, g, b = color[0], color[1], color[2]
                a = color[3] if len(color) > 3 else 255
                
                # Check if pixel is "white" (all channels above threshold)
                if r >= threshold and g >= threshold and b >= threshold:
                    result.set_at((x, y), (r, g, b, 0))  # Transparent
                else:
                    result.set_at((x, y), (r, g, b, a))
            except:
                pass
    
    return result


def process_image(src_path: Path, dest_path: Path, size: tuple, threshold: int = 250):
    """Process a single image: remove white bg, resize, save as PNG."""
    # Load image
    surface = pygame.image.load(str(src_path))
    
    # Remove white background at original size (better quality)
    surface = remove_white_background(surface, threshold)
    
    # Resize with smooth scaling
    surface = pygame.transform.smoothscale(surface, size)
    
    # Save as PNG
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    pygame.image.save(surface, str(dest_path))
    
    return True


def detect_type_from_name(filename: str) -> tuple:
    """
    Try to detect sprite type and animation state from filename.
    Returns (base_name, sprite_type, anim_state, frame_num)
    """
    name = Path(filename).stem.lower()
    parts = name.replace("-", "_").split("_")
    
    base_name = parts[0]
    sprite_type = None
    anim_state = None
    frame_num = None
    
    # Check if first part is a known type
    if base_name in KNOWN_TYPES:
        sprite_type = KNOWN_TYPES[base_name]
    
    # Look for animation state and frame number
    for part in parts[1:]:
        if part in ANIM_STATES:
            anim_state = part
        elif part.isdigit():
            frame_num = int(part)
        elif part in KNOWN_TYPES:
            sprite_type = KNOWN_TYPES[part]
    
    # Build clean base name (everything before animation state)
    clean_parts = []
    for part in parts:
        if part in ANIM_STATES or part.isdigit():
            break
        clean_parts.append(part)
    base_name = "_".join(clean_parts) if clean_parts else parts[0]
    
    return base_name, sprite_type, anim_state, frame_num


def get_size_for_type(sprite_type: str) -> tuple:
    """Get pixel size for a sprite type."""
    return SIZES.get(sprite_type, SIZES.get("enemy", (32, 32)))


def interactive_process(threshold: int = 250):
    """Interactive mode - asks about each image."""
    raw_files = list(RAW_DIR.glob("*"))
    raw_files = [f for f in raw_files if f.suffix.lower() in [".jpg", ".jpeg", ".png", ".bmp", ".gif"]]
    
    if not raw_files:
        print(f"\nNo images found in {RAW_DIR}")
        print("Drop your images there and run again!")
        return
    
    print(f"\nFound {len(raw_files)} images in {RAW_DIR}\n")
    
    mapping = load_existing_mapping()
    
    for src_path in raw_files:
        base_name, detected_type, anim_state, frame_num = detect_type_from_name(src_path.name)
        
        print(f"\n{'='*50}")
        print(f"File: {src_path.name}")
        print(f"  Detected: name='{base_name}', type='{detected_type}', anim='{anim_state}', frame={frame_num}")
        
        # Ask for type if not detected
        if detected_type is None:
            print(f"\nWhat type is this? Options:")
            print("  hero, ally, enemy, boss, item, prop, decoration, large, huge")
            print("  (or press Enter for 'enemy')")
            type_input = input("> ").strip().lower()
            detected_type = type_input if type_input else "enemy"
        else:
            print(f"  Using type: {detected_type}")
        
        # Get size
        size = get_size_for_type(detected_type)
        
        # Build destination filename
        if anim_state and frame_num is not None:
            dest_name = f"{base_name}_{anim_state}_{frame_num}.png"
        elif anim_state:
            dest_name = f"{base_name}_{anim_state}.png"
        else:
            dest_name = f"{base_name}.png"
        
        dest_path = SPRITES_DIR / detected_type / dest_name
        
        print(f"  -> Saving to: {dest_path.relative_to(project_root)}")
        print(f"     Size: {size[0]}x{size[1]}")
        
        # Process
        try:
            process_image(src_path, dest_path, size, threshold)
            print(f"  ✓ Done!")
            
            # Add to mapping
            sprite_key = dest_name.replace(".png", "")
            mapping[sprite_key] = {
                "file": str(dest_path.relative_to(SPRITES_DIR)),
                "type": detected_type,
                "size": list(size),
                "original": src_path.name,
            }
            if anim_state:
                mapping[sprite_key]["anim"] = anim_state
            if frame_num is not None:
                mapping[sprite_key]["frame"] = frame_num
                
        except Exception as e:
            print(f"  ✗ Error: {e}")
            import traceback
            traceback.print_exc()
    
    # Save mapping
    save_mapping(mapping)
    
    print(f"\n{'='*50}")
    print("Done! Processed sprites are in assets/sprites/")
    print("\nTo use in game, sprites auto-load on startup!")


def auto_process(default_type: str = None, threshold: int = 250):
    """Auto mode - processes all images using detected or default type."""
    raw_files = list(RAW_DIR.glob("*"))
    raw_files = [f for f in raw_files if f.suffix.lower() in [".jpg", ".jpeg", ".png", ".bmp", ".gif"]]
    
    if not raw_files:
        print(f"No images found in {RAW_DIR}")
        return
    
    print(f"Processing {len(raw_files)} images...")
    
    mapping = load_existing_mapping()
    
    for src_path in raw_files:
        base_name, detected_type, anim_state, frame_num = detect_type_from_name(src_path.name)
        
        # Use default type if provided, otherwise use detected or "enemy"
        sprite_type = default_type or detected_type or "enemy"
        size = get_size_for_type(sprite_type)
        
        # Build destination
        if anim_state and frame_num is not None:
            dest_name = f"{base_name}_{anim_state}_{frame_num}.png"
        elif anim_state:
            dest_name = f"{base_name}_{anim_state}.png"
        else:
            dest_name = f"{base_name}.png"
        
        dest_path = SPRITES_DIR / sprite_type / dest_name
        
        try:
            process_image(src_path, dest_path, size, threshold)
            print(f"  ✓ {src_path.name} -> {dest_path.relative_to(project_root)} ({size[0]}x{size[1]})")
            
            sprite_key = dest_name.replace(".png", "")
            mapping[sprite_key] = {
                "file": str(dest_path.relative_to(SPRITES_DIR)),
                "type": sprite_type,
                "size": list(size),
            }
        except Exception as e:
            print(f"  ✗ {src_path.name}: {e}")
    
    save_mapping(mapping)
    print(f"\nDone!")


def load_existing_mapping() -> dict:
    """Load existing mapping file if it exists."""
    if MAPPING_FILE.exists():
        try:
            with open(MAPPING_FILE) as f:
                return json.load(f)
        except:
            pass
    return {}


def save_mapping(mapping: dict):
    """Save mapping to file."""
    if mapping:
        SPRITES_DIR.mkdir(parents=True, exist_ok=True)
        with open(MAPPING_FILE, "w") as f:
            json.dump(mapping, f, indent=2)
        print(f"\nMapping saved to: {MAPPING_FILE.relative_to(project_root)}")


def main():
    parser = argparse.ArgumentParser(description="Process raw sprites for the game")
    parser.add_argument("--auto", action="store_true", help="Auto-process without prompts")
    parser.add_argument("--type", type=str, help="Force all sprites to this type (hero, enemy, boss, item, etc)")
    parser.add_argument("--threshold", type=int, default=250, help="White threshold (0-255, default 250)")
    args = parser.parse_args()
    
    # Ensure directories exist
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    SPRITES_DIR.mkdir(parents=True, exist_ok=True)
    
    print("="*50)
    print("  Sprite Processor")
    print("="*50)
    
    if args.auto or args.type:
        auto_process(args.type, args.threshold)
    else:
        interactive_process(args.threshold)
    
    pygame.quit()


if __name__ == "__main__":
    main()
