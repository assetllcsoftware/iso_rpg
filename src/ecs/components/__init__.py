"""ECS Components - Pure data classes."""

# Transform
from .transform import (
    Position, Velocity, Facing, Speed, CollisionRadius,
    Path, MoveIntent, TargetPosition, Direction, Knockback
)

# Health & Mana
from .health import Health, Mana, Regeneration, Downed, Dead

# Combat
from .combat import (
    CombatStats, CombatTarget, AttackCooldown, AttackIntent,
    Weapon, Resistances, InCombat
)

# Stats & Progression
from .stats import (
    Attributes, SkillLevels, SkillXP, CharacterLevel,
    CharacterClass, CharacterName
)

# Equipment & Inventory
from .equipment import Equipment, Inventory, InventoryItem, Gold

# Spells & Magic
from .spells import (
    SpellBook, CastIntent, Casting, Projectile,
    AreaEffect, StatusEffect, StatusEffects, ActiveAbility, LeapingAbility,
    GlobalCooldown, DelayedSpellEffect
)

# AI
from .ai import (
    AIController, AggroRange, LeashRange, AllyAI, EnemyAI,
    PatrolPath, Summon
)

# Rendering
from .rendering import (
    Sprite, Animation, AnimationState, RenderOffset,
    HealthBar, DamageNumber, VisualEffect
)

# Tags
from .tags import (
    PlayerControlled, Selected, PartyMember, Enemy, Ally,
    Loot, Interactable, ToRemove
)

# Items
from .items import ItemDrop, DroppedItem, GoldDrop, PickupRadius

__all__ = [
    # Transform
    'Position', 'Velocity', 'Facing', 'Speed', 'CollisionRadius',
    'Path', 'MoveIntent', 'TargetPosition', 'Direction', 'Knockback',
    # Health
    'Health', 'Mana', 'Regeneration', 'Downed', 'Dead',
    # Combat
    'CombatStats', 'CombatTarget', 'AttackCooldown', 'AttackIntent',
    'Weapon', 'Resistances', 'InCombat',
    # Stats
    'Attributes', 'SkillLevels', 'SkillXP', 'CharacterLevel',
    'CharacterClass', 'CharacterName',
    # Equipment
    'Equipment', 'Inventory', 'InventoryItem', 'Gold',
    # Spells
    'SpellBook', 'CastIntent', 'Casting', 'Projectile',
    'AreaEffect', 'StatusEffect', 'StatusEffects', 'ActiveAbility', 'LeapingAbility',
    'GlobalCooldown', 'DelayedSpellEffect',
    # AI
    'AIController', 'AggroRange', 'LeashRange', 'AllyAI', 'EnemyAI',
    'PatrolPath', 'Summon',
    # Rendering
    'Sprite', 'Animation', 'AnimationState', 'RenderOffset',
    'HealthBar', 'DamageNumber', 'VisualEffect',
    # Tags
    'PlayerControlled', 'Selected', 'PartyMember', 'Enemy', 'Ally',
    'Loot', 'Interactable', 'ToRemove',
    # Items
    'ItemDrop', 'DroppedItem', 'GoldDrop', 'PickupRadius',
]
