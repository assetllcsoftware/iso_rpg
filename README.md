# Dungeon Siege Mobile Prototype

A Pygame-based mobile prototype inspired by Dungeon Siege 1, designed for landscape orientation.

## Features

- **Isometric View**: Classic isometric dungeon crawler perspective
- **Party System**: Control multiple characters with AI companions
- **Usage-Based Leveling**: Skills improve as you use them (melee, ranged, magic)
- **Real-Time Combat**: Pause-and-play tactical combat
- **Inventory System**: Weight-based inventory with equipment slots
- **Procedural Dungeons**: Randomized dungeon layouts with loot

## Controls (Touch/Mouse)

- **Tap/Click**: Move to location, select target, interact
- **Drag**: Pan camera, drag items in inventory
- **Double-tap**: Attack/interact with target
- **Hold**: Open context menu

## Running the Game

```bash
pip install -r requirements.txt
python main.py
```

## Target Resolution

Landscape mobile: 1280x720 (16:9)

## Project Structure

```
dungeon_siege/
├── main.py           # Entry point
├── src/
│   ├── engine/       # Core game loop, rendering
│   ├── entities/     # Characters, enemies, items
│   ├── systems/      # Combat, inventory, magic
│   ├── world/        # Dungeon generation, tiles
│   └── ui/           # HUD, menus, touch controls
└── assets/           # Sprites, sounds, fonts
```

