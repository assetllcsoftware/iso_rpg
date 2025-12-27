"""Game constants and configuration.

ALL magic numbers go here. No literal numbers in game code.
"""

from enum import Enum, auto

# =============================================================================
# DISPLAY
# =============================================================================

SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
FPS = 60
FIXED_TIMESTEP = 1.0 / 60.0

# Isometric tile dimensions
TILE_WIDTH = 64
TILE_HEIGHT = 32
WALL_HEIGHT = 32

# Camera
CAMERA_ZOOM_DEFAULT = 1.5
CAMERA_ZOOM_MIN = 0.75
CAMERA_ZOOM_MAX = 3.0
CAMERA_SMOOTH_SPEED = 5.0

# =============================================================================
# COLORS - Dark fantasy palette
# =============================================================================

# Indian Temple / Desert Theme
COLOR_BG = (210, 180, 140)           # Same as floor tiles - sandstone
COLOR_UI_BG = (45, 35, 25)           # Sandstone UI
COLOR_UI_BORDER = (120, 90, 50)      # Gold/brass border
COLOR_UI_ACCENT = (220, 160, 60)     # Saffron/gold accent
COLOR_HEALTH = (180, 50, 40)         # Deep red (vermillion)
COLOR_MANA = (40, 120, 160)          # Temple pool blue
COLOR_XP = (90, 160, 90)
COLOR_GOLD = (220, 180, 60)
COLOR_TEXT = (225, 215, 200)
COLOR_TEXT_DIM = (140, 130, 120)
COLOR_TEXT_GOOD = (60, 180, 60)
COLOR_TEXT_BAD = (180, 60, 60)

# =============================================================================
# TILES
# =============================================================================

class TileType(Enum):
    VOID = 0
    FLOOR = 1
    WALL = 2
    DOOR = 3
    STAIRS_DOWN = 4
    STAIRS_UP = 5
    WATER = 6
    PIT = 7

# =============================================================================
# GAME STATES
# =============================================================================

class GameState(Enum):
    """Top-level game states."""
    MAIN_MENU = auto()
    LOADING = auto()
    PLAYING = auto()
    PAUSED = auto()
    INVENTORY = auto()
    SKILL_TREE = auto()
    TRADING = auto()
    TOWN = auto()
    GAME_OVER = auto()

# =============================================================================
# CHARACTER STATES
# =============================================================================

class CharacterState(Enum):
    """Individual character states."""
    IDLE = auto()
    MOVING = auto()
    ATTACKING = auto()
    CASTING = auto()
    DOWNED = auto()
    DEAD = auto()
    REVIVING = auto()

# =============================================================================
# AI STATES
# =============================================================================

class AIState(Enum):
    """AI behavior states."""
    IDLE = auto()
    FOLLOW = auto()
    CHASE = auto()
    ATTACK = auto()
    FLEE = auto()
    RETURN = auto()
    PATROL = auto()
    ENGAGE = auto()  # Ally engaging enemy

# =============================================================================
# COMBAT
# =============================================================================

ATTACK_RANGE_MELEE = 1.5
ATTACK_RANGE_RANGED = 7.0
ATTACK_RANGE_MAGIC = 8.0
ATTACK_SPEED_DEFAULT = 1.0

CRIT_CHANCE_BASE = 0.05
CRIT_MULTIPLIER = 1.5

AGGRO_RANGE_DEFAULT = 6.0
LEASH_RANGE_DEFAULT = 15.0

# =============================================================================
# DAMAGE TYPES
# =============================================================================

class DamageType(Enum):
    """Types of damage."""
    PHYSICAL = "physical"
    FIRE = "fire"
    ICE = "ice"
    LIGHTNING = "lightning"
    POISON = "poison"
    HOLY = "holy"

# =============================================================================
# SKILLS
# =============================================================================

class SkillType(Enum):
    MELEE = "melee"
    RANGED = "ranged"
    COMBAT_MAGIC = "combat_magic"
    NATURE_MAGIC = "nature_magic"

# =============================================================================
# ITEMS
# =============================================================================

class Rarity(Enum):
    COMMON = 0       # Gray - Basic starting gear
    UNCOMMON = 1     # Green - Better than common
    RARE = 2         # Blue - Solid mid-tier
    EPIC = 3         # Purple - High power
    LEGENDARY = 4    # Orange - End-game tier
    MYTHIC = 5       # Red - Extremely powerful
    UNIQUE = 6       # Gold - One of a kind
    CELESTIAL = 7    # Cyan - Divine artifacts

# Rarity colors - vibrant and distinct
RARITY_COLORS = {
    0: (180, 180, 180),   # Common - Gray
    1: (80, 220, 80),     # Uncommon - Green
    2: (70, 130, 255),    # Rare - Blue
    3: (180, 70, 255),    # Epic - Purple
    4: (255, 140, 40),    # Legendary - Orange
    5: (255, 60, 60),     # Mythic - Red
    6: (255, 215, 0),     # Unique - Gold
    7: (0, 255, 255),     # Celestial - Cyan
    Rarity.COMMON: (180, 180, 180),
    Rarity.UNCOMMON: (80, 220, 80),
    Rarity.RARE: (70, 130, 255),
    Rarity.EPIC: (180, 70, 255),
    Rarity.LEGENDARY: (255, 140, 40),
    Rarity.MYTHIC: (255, 60, 60),
    Rarity.UNIQUE: (255, 215, 0),
    Rarity.CELESTIAL: (0, 255, 255),
}

# Rarity name strings for display
RARITY_NAMES = {
    0: "Common",
    1: "Uncommon",
    2: "Rare",
    3: "Epic",
    4: "Legendary",
    5: "Mythic",
    6: "Unique",
    7: "Celestial",
}

class EquipmentSlot(Enum):
    HEAD = "head"
    CHEST = "chest"
    HANDS = "hands"
    LEGS = "legs"
    FEET = "feet"
    MAIN_HAND = "main_hand"
    OFF_HAND = "off_hand"
    RING_1 = "ring_1"
    RING_2 = "ring_2"
    AMULET = "amulet"

class WeaponType(Enum):
    MELEE = "melee"
    RANGED = "ranged"
    MAGIC = "magic"

# =============================================================================
# MOVEMENT
# =============================================================================

BASE_MOVE_SPEED = 5.0  # Tiles per second
DIAGONAL_MOVE_COST = 1.414  # sqrt(2)

# =============================================================================
# SPELLS
# =============================================================================

class SpellSchool(Enum):
    """Magic schools."""
    COMBAT_MAGIC = "combat_magic"
    NATURE_MAGIC = "nature_magic"

class SpellType(Enum):
    """Spell delivery types."""
    PROJECTILE = "projectile"
    INSTANT = "instant"
    CHAIN = "chain"
    AOE = "aoe"
    BUFF = "buff"
    SUMMON = "summon"

class SpellTarget(Enum):
    """Valid spell targets."""
    ENEMY = "enemy"
    ALLY = "ally"
    SELF = "self"
    GROUND = "ground"
    DOWNED_ALLY = "downed_ally"

# Cooldown tiers (exponential scaling: each tier is 3x previous)
COOLDOWN_TIERS = {
    1: 1.0,    # Basic spells (Fireball, Ice Shard)
    2: 3.0,    # Improved spells (Lightning Bolt)
    3: 9.0,    # Advanced spells (Chain Lightning)
    4: 27.0,   # Powerful spells (Inferno, Blizzard)
    5: 81.0,   # Ultimate spells (Meteor)
    6: 243.0,  # Legendary spells (Armageddon)
}

# AI waits this multiplier * cooldown before auto-casting
AI_SPELL_DELAY_MULTIPLIER = 3.0

# =============================================================================
# ENTITY
# =============================================================================

DEFAULT_COLLISION_RADIUS = 0.4  # Tiles
SEPARATION_FORCE = 5.0
STUCK_TIME_THRESHOLD = 2.0
STUCK_DISTANCE_THRESHOLD = 0.5

# =============================================================================
# ALLY AI
# =============================================================================

FOLLOW_DISTANCE = 2.0
ENGAGE_RANGE = 8.0
TELEPORT_DISTANCE = 8.0

# Formation offsets (relative to leader)
FORMATION_OFFSETS = {
    0: (0.0, 0.0),      # Leader
    1: (1.5, 0.5),      # First ally
    2: (-1.5, 0.5),     # Second ally
    3: (0.0, 1.5),      # Third ally
}

# =============================================================================
# REGENERATION
# =============================================================================

HEALTH_REGEN_RATE = 0.5        # Per second (out of combat)
MANA_REGEN_RATE = 2.0          # Per second
MANA_REGEN_COMBAT_MULT = 0.5   # 50% regen in combat

# =============================================================================
# ECONOMY
# =============================================================================

DEATH_GOLD_PENALTY = 0.10      # Lose 10% gold on party wipe
MERCHANT_BUY_RATE = 0.5        # Merchant pays 50% of item value
MERCHANT_SELL_RATE = 1.0       # Merchant sells at 100% value

# =============================================================================
# DUNGEON GENERATION
# =============================================================================

DUNGEON_BASE_SIZE = 60
DUNGEON_SIZE_PER_LEVEL = 10
DUNGEON_MAX_SIZE = 150

ROOM_MIN_SIZE = 5
ROOM_MAX_SIZE = 12
ROOM_BASE_COUNT = 8
ROOM_MAX_COUNT = 20

ENEMY_BASE_COUNT = 15
ENEMY_COUNT_PER_LEVEL = 8

# =============================================================================
# DEBUG FLAGS
# =============================================================================

DEBUG_SHOW_FPS = False
DEBUG_SHOW_COLLISION = False
DEBUG_SHOW_PATHS = False
DEBUG_SHOW_AI_STATE = False
DEBUG_INVINCIBLE = False
DEBUG_INSTANT_KILL = False
DEBUG_UNLOCK_ALL_SPELLS = False
DEBUG_INFINITE_MANA = False

