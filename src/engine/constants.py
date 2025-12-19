"""Game constants and configuration."""

# Display settings (landscape mobile)
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60

# Isometric tile dimensions
TILE_WIDTH = 64
TILE_HEIGHT = 32

# Colors - Dark fantasy palette
COLOR_BG = (15, 12, 20)
COLOR_UI_BG = (25, 22, 35)
COLOR_UI_BORDER = (65, 55, 80)
COLOR_UI_ACCENT = (180, 140, 90)
COLOR_HEALTH = (160, 45, 55)
COLOR_MANA = (55, 90, 160)
COLOR_XP = (90, 160, 90)
COLOR_GOLD = (220, 180, 60)
COLOR_TEXT = (225, 215, 200)
COLOR_TEXT_DIM = (140, 130, 120)

# Tile types
TILE_EMPTY = 0
TILE_FLOOR = 1
TILE_WALL = 2
TILE_DOOR = 3
TILE_STAIRS_DOWN = 4
TILE_WATER = 5
TILE_LAVA = 6

# Entity layers
LAYER_FLOOR = 0
LAYER_ITEMS = 1
LAYER_ENTITIES = 2
LAYER_EFFECTS = 3
LAYER_UI = 4

# Character classes (based on skill usage like DS1)
SKILL_MELEE = 'melee'
SKILL_RANGED = 'ranged'
SKILL_COMBAT_MAGIC = 'combat_magic'
SKILL_NATURE_MAGIC = 'nature_magic'

# Item rarity
RARITY_COMMON = 0
RARITY_UNCOMMON = 1
RARITY_RARE = 2
RARITY_LEGENDARY = 3
RARITY_SET = 4

RARITY_COLORS = {
    RARITY_COMMON: (200, 200, 200),
    RARITY_UNCOMMON: (100, 180, 100),
    RARITY_RARE: (100, 140, 220),
    RARITY_LEGENDARY: (180, 100, 220),
    RARITY_SET: (220, 180, 60),
}

# Equipment slots
SLOT_HEAD = 'head'
SLOT_CHEST = 'chest'
SLOT_HANDS = 'hands'
SLOT_LEGS = 'legs'
SLOT_FEET = 'feet'
SLOT_MAIN_HAND = 'main_hand'
SLOT_OFF_HAND = 'off_hand'
SLOT_RING_1 = 'ring_1'
SLOT_RING_2 = 'ring_2'
SLOT_AMULET = 'amulet'

ALL_SLOTS = [
    SLOT_HEAD, SLOT_CHEST, SLOT_HANDS, SLOT_LEGS, SLOT_FEET,
    SLOT_MAIN_HAND, SLOT_OFF_HAND, SLOT_RING_1, SLOT_RING_2, SLOT_AMULET
]

# Combat
ATTACK_RANGE_MELEE = 1.5
ATTACK_RANGE_RANGED = 8.0
ATTACK_RANGE_MAGIC = 6.0

# AI States
AI_IDLE = 'idle'
AI_FOLLOW = 'follow'
AI_ATTACK = 'attack'
AI_FLEE = 'flee'
AI_PATROL = 'patrol'

