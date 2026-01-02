"""Pytest configuration and shared fixtures.

These fixtures provide common test setup for all test files.
"""

import pytest
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


@pytest.fixture
def mock_dungeon():
    """Create a simple mock dungeon for testing."""
    from src.core.constants import TileType
    
    class MockDungeon:
        def __init__(self, width=20, height=20):
            self.width = width
            self.height = height
            # All floor by default
            self.tiles = [[TileType.FLOOR for _ in range(width)] for _ in range(height)]
            self.spawn_point = (5, 5)
            self.exit_point = (15, 15)
        
        def get_tile(self, x, y):
            if 0 <= x < self.width and 0 <= y < self.height:
                return self.tiles[y][x]
            return TileType.WALL
        
        def is_walkable(self, x, y):
            return self.get_tile(x, y) == TileType.FLOOR
        
        def set_wall(self, x, y):
            if 0 <= x < self.width and 0 <= y < self.height:
                self.tiles[y][x] = TileType.WALL
        
        def has_line_of_sight(self, x1, y1, x2, y2):
            """Simple LOS check for testing."""
            # Bresenham's line algorithm
            dx = abs(x2 - x1)
            dy = abs(y2 - y1)
            sx = 1 if x1 < x2 else -1
            sy = 1 if y1 < y2 else -1
            err = dx - dy
            
            x, y = x1, y1
            while True:
                if not self.is_walkable(x, y):
                    return False
                if x == x2 and y == y2:
                    return True
                e2 = 2 * err
                if e2 > -dy:
                    err -= dy
                    x += sx
                if e2 < dx:
                    err += dx
                    y += sy
        
        def get_player_spawn(self):
            return self.spawn_point
    
    return MockDungeon()


@pytest.fixture
def mock_entity_with_health():
    """Create a mock entity with health component."""
    return {
        'health': {'current': 100, 'maximum': 100},
        'position': {'x': 5.0, 'y': 5.0},
    }


@pytest.fixture
def mock_character_data():
    """Create mock character save data."""
    return {
        'party_index': 0,
        'position': {'x': 10.0, 'y': 10.0},
        'health': {'current': 80, 'maximum': 100},
        'mana': {'current': 50, 'maximum': 100},
        'gold': 500,
        'skills': {
            'melee': 5,
            'ranged': 3,
            'combat_magic': 2,
            'nature_magic': 4,
        },
        'skill_xp': {
            'melee': 150,
            'ranged': 80,
            'combat_magic': 30,
            'nature_magic': 200,
        },
        'spells': ['whirlwind', 'leap_strike', 'crushing_blow', 'shield_bash'],
        'inventory': [
            {'item_id': 'health_potion', 'quantity': 5},
            {'item_id': 'short_sword', 'quantity': 1},
        ],
        'equipment': {
            'main_hand': 'iron_sword',
            'chest': 'leather_armor',
        }
    }


@pytest.fixture
def mock_item_data():
    """Create mock item data."""
    return {
        'id': 'test_sword',
        'name': 'Test Sword',
        'type': 'weapon',
        'slot': 'main_hand',
        'damage': 10,
        'value': 100,
        'rarity': 'common',
    }


@pytest.fixture
def mock_spell_data():
    """Create mock spell data."""
    return {
        'id': 'test_spell',
        'name': 'Test Spell',
        'school': 'combat_magic',
        'type': 'projectile',
        'damage': 50,
        'mana_cost': 20,
        'cooldown': 5.0,
        'range': 10.0,
    }

