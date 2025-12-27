# Raw Sprites - Drop Zone

**Just dump your images here and run the processor!**

## Quick Start

1. Drop your JPG/BMP/PNG images here
2. Run: `pipenv run python tools/process_sprites.py`
3. Done! They'll be processed and ready to use.

## Naming Convention (Optional)

The processor is smart about names:

| Filename | Detected As |
|----------|-------------|
| `hero_idle_1.jpg` | Hero, idle animation, frame 1 |
| `skeleton_walk.bmp` | Skeleton enemy, walk animation |
| `boss_attack_1.png` | Boss, attack animation, frame 1 |
| `cool_monster.jpg` | Enemy named "cool_monster" |
| `my_potion.png` | Item named "my_potion" |

### Known Type Keywords
- **Hero**: `hero`, `player`, `warrior`
- **Ally**: `lyra`, `mage`, `ally`
- **Enemy**: `skeleton`, `spider`, `zombie`, `orc`, `demon`, `goblin`, `slime`
- **Boss**: `boss`, `dragon`
- **Item**: `potion`, `sword`, `staff`, `armor`, `shield`
- **Prop**: `barrel`, `chest`, `crate`, `urn`

### Animation Keywords
`idle`, `walk`, `attack`, `cast`, `death`, `hit`, `run`

## Processor Options

```bash
# Interactive mode (asks about each image)
pipenv run python tools/process_sprites.py

# Auto mode (uses detected types)
pipenv run python tools/process_sprites.py --auto

# Force all as specific type
pipenv run python tools/process_sprites.py --type enemy
pipenv run python tools/process_sprites.py --type boss

# Adjust white threshold (default 250)
pipenv run python tools/process_sprites.py --threshold 240
```

## What Happens

1. White background removed (threshold: RGB >= 250)
2. Resized to game size based on type
3. Saved as PNG in `assets/sprites/{type}/`
4. Mapping saved to `assets/sprites/sprite_mapping.json`

## Auto-Load in Game

After processing, sprites auto-load:

```python
# In SpriteManager.load_all():
sprite_mgr.load_processed_sprites()

# Then use:
surface = sprite_mgr.sprites["skeleton_walk"]
```

