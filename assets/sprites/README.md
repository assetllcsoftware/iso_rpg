# External Sprites

Drop your JPG, BMP, or PNG sprite images here. **White background is auto-removed.**

## Quick Start

1. **Drop your image** in this folder (e.g., `my_boss.jpg`)
2. **Load it** with one line:

```python
sprite_mgr.load_external_sprite("my_boss", "my_boss.jpg", "large")
```

That's it! The sprite is auto-scaled and white background removed.

## Sprite Types (Auto-Sizing)

| Type | Size | Use for |
|------|------|---------|
| `"hero"` / `"player"` | 48×48 | Main characters |
| `"character"` / `"enemy"` / `"ally"` | 32×32 | NPCs, enemies |
| `"item"` | 16×16 | Inventory items |
| `"icon"` | 24×24 | UI icons |
| `"large"` | 64×64 | Large enemies |
| `"huge"` / `"boss"` | 96×96 | Boss monsters |
| `"decoration"` / `"prop"` | 48×48 / 40×40 | Props |
| `"original"` | No scaling | Keep original size |

## Animation Spritesheets

For a **horizontal strip** of animation frames:

```python
# If you have "boss_attack.jpg" that's 256×64 (4 frames of 64×64):
frames = sprite_mgr.load_external_animation("boss_attack", "boss_attack.jpg", 4, "large")
```

The frame size is auto-detected from the image dimensions!

## Bulk Loading

Put all enemy images in `assets/sprites/enemies/` and load them all:

```python
sprite_mgr.load_all_from_folder("enemies", "enemy")
# Loads all .jpg/.bmp/.png files, names from filenames
```

## Tips

1. **Use pure white background** - RGB(255,255,255) works best
2. **Avoid anti-aliasing** - Hard edges look better after threshold
3. **Any size works** - It auto-scales to game size
4. **BMP is cleanest** - No compression artifacts
5. **JPG is fine** - Use high quality to avoid edge artifacts

## Using Loaded Sprites

```python
# Single sprites
surface = sprite_mgr.sprites["my_boss"]
# or
surface = sprite_mgr.get_item_sprite("my_boss")

# Animation frames
frames = sprite_mgr.sprites["boss_attack"]  # List
frame_0 = sprite_mgr.sprites["boss_attack_0"]
frame_1 = sprite_mgr.sprites["boss_attack_1"]
```
