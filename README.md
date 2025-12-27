# ML Siege

A clean rewrite of Dungeon Siege using Esper ECS.

## About

This is a ground-up rewrite of the `dungeon_siege` prototype, focusing on:

- **Maintainability** - Clean ECS architecture with Esper
- **Extensibility** - Easy to add new features without breaking existing ones
- **Testability** - Pure functions and isolated systems

## Architecture

- **Esper ECS** - Entity Component System for game logic
- **Pygame** - Rendering and input
- **Event Bus** - Decoupled system communication

See [docs/REFACTORING_PLAN.md](docs/REFACTORING_PLAN.md) for the full plan.

## Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Run
python main.py
```

## Project Structure

```
ml_siege/
├── main.py                 # Entry point
├── game.py                 # Game loop
├── src/
│   ├── ecs/
│   │   ├── components/     # Pure data (Position, Health, etc.)
│   │   ├── processors/     # Logic (MovementProcessor, CombatProcessor, etc.)
│   │   └── factories/      # Entity creation helpers
│   ├── core/
│   │   ├── events.py       # Event bus
│   │   ├── constants.py    # All magic numbers
│   │   └── formulas.py     # Pure calculation functions
│   ├── world/              # Dungeon generation, pathfinding
│   ├── rendering/          # Isometric renderer, camera, sprites
│   ├── ui/                 # HUD, inventory, menus
│   └── audio/              # Sound system
├── data/                   # YAML data files (enemies, items, spells)
└── docs/                   # Documentation
```

## Controls

- **Arrow Keys** - Move
- **Left Click** - Move to / Select
- **Double Click** - Attack
- **Right Drag** - Pan camera
- **Scroll** - Zoom
- **TAB** - Cycle party members
- **SPACE** - Attack nearest
- **Q/W/E/R** - Cast spells (party member 1)
- **A/S/D/F** - Cast spells (party member 2)
- **I** - Inventory
- **K** - Skill tree
- **ESC** - Pause

## Reference

Original game: `../dungeon_siege/`  
Original docs: `../dungeon_siege/docs/rewrite/`

