#!/usr/bin/env python3
"""
Dungeon Siege Mobile Prototype
A Pygame-based action RPG inspired by Dungeon Siege 1

Controls:
- Left Click: Move / Select
- Right Drag: Pan camera
- Double Click: Attack / Interact
- Scroll: Zoom
- TAB: Cycle party members
- SPACE/ESC: Pause
- 1: Use health potion
- 2: Use mana potion
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.engine import Game


def main():
    """Entry point."""
    print("=" * 50)
    print("Dungeon Siege Mobile Prototype")
    print("=" * 50)
    print("\nControls:")
    print("  Left Click  - Move / Select")
    print("  Right Drag  - Pan camera")
    print("  Double Click- Attack enemy")
    print("  Scroll      - Zoom in/out")
    print("  TAB         - Cycle party members")
    print("  SPACE/ESC   - Pause game")
    print("  1/2         - Use health/mana potion")
    print("\n" + "=" * 50)
    
    game = Game()
    game.run()


if __name__ == "__main__":
    main()

