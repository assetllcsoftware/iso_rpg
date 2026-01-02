"""Pure calculation functions for game mechanics.

ALL game math goes here. No side effects, just calculations.
These functions receive values and return results - they don't modify state.
"""

import math
import random
from typing import Dict, Tuple


# =============================================================================
# COMBAT FORMULAS
# =============================================================================

def calculate_physical_damage(
    weapon_damage: int,
    attacker_strength: int,
    target_armor: int,
    attacker_dexterity: int = 0
) -> Tuple[int, bool]:
    """Calculate physical damage with armor mitigation.
    
    Args:
        weapon_damage: Base damage from weapon
        attacker_strength: Attacker's STR stat
        target_armor: Target's total armor
        attacker_dexterity: Attacker's DEX for crit chance
    
    Returns:
        Tuple of (final_damage, is_critical)
    """
    # Step 1: Strength bonus (+5% per point)
    strength_multiplier = 1 + (attacker_strength * 0.05)
    damage = weapon_damage * strength_multiplier
    
    # Step 2: Armor reduction (diminishing returns)
    # Formula: damage * (100 / (100 + armor))
    armor_multiplier = 100 / (100 + target_armor)
    damage = damage * armor_multiplier
    
    # Step 3: Critical hit check
    crit_chance = 0.05  # 5% base
    crit_chance += attacker_dexterity * 0.005  # +0.5% per DEX
    
    is_critical = random.random() < crit_chance
    if is_critical:
        damage = damage * 1.5  # 150% damage
    
    # Minimum 1 damage
    return max(1, int(damage)), is_critical


def calculate_elemental_damage(
    base_damage: int,
    target_resistance: float
) -> int:
    """Calculate elemental damage with resistance.
    
    Elemental damage bypasses armor but can be resisted.
    
    Args:
        base_damage: Raw elemental damage
        target_resistance: Target's resistance (-1.0 to 1.0)
            - 0.5 = 50% less damage taken
            - -0.5 = 50% MORE damage taken (weakness)
    
    Returns:
        Final damage as integer
    """
    # Clamp resistance
    resistance = max(-1.0, min(1.0, target_resistance))
    damage = base_damage * (1 - resistance)
    return max(1, int(damage))


def calculate_spell_damage(
    base_damage: int,
    caster_intelligence: int,
    caster_skill_level: int
) -> int:
    """Calculate spell damage based on INT and skill level.
    
    Args:
        base_damage: Spell's base damage
        caster_intelligence: Caster's INT stat
        caster_skill_level: Caster's level in the spell's school
    
    Returns:
        Final spell damage
    """
    # Intelligence adds +3% per point
    int_multiplier = 1 + (caster_intelligence * 0.03)
    
    # Skill level adds +5% per level (after level 1)
    skill_multiplier = 1 + ((caster_skill_level - 1) * 0.05)
    
    damage = base_damage * int_multiplier * skill_multiplier
    return int(damage)


def calculate_heal_amount(
    base_heal: int,
    caster_intelligence: int,
    nature_magic_level: int
) -> int:
    """Calculate healing amount.
    
    Same scaling as spell damage but for healing.
    """
    int_multiplier = 1 + (caster_intelligence * 0.03)
    skill_multiplier = 1 + ((nature_magic_level - 1) * 0.05)
    
    heal = base_heal * int_multiplier * skill_multiplier
    return int(heal)


def armor_damage_reduction(armor: int) -> float:
    """Get damage multiplier from armor.
    
    Returns:
        Multiplier (0.0 to 1.0) - multiply incoming damage by this
    """
    return 100 / (100 + armor)


def effective_hp(base_hp: int, armor: int) -> int:
    """Calculate effective HP with armor.
    
    How much damage can this entity actually take?
    """
    reduction = armor_damage_reduction(armor)
    return int(base_hp / reduction)


# =============================================================================
# PROGRESSION FORMULAS
# =============================================================================

def xp_for_skill_level(current_level: int) -> int:
    """XP required to reach next skill level.
    
    Formula: 100 * level^1.5
    """
    return int(100 * (current_level ** 1.5))


def calculate_character_level(skills: Dict[str, int]) -> int:
    """Calculate character level from skill levels.
    
    Formula: max(1, sum(skill_levels) // 2)
    """
    total = sum(skills.values())
    return max(1, total // 2)


# XP values for actions
XP_MELEE_HIT = 10
XP_RANGED_HIT = 10
XP_SPELL_HIT = 15
XP_HEAL_CAST = 12
XP_BUFF_CAST = 8
XP_KILL_BONUS = 25


def xp_from_kill(enemy_xp_value: int) -> int:
    """XP gained from killing an enemy."""
    return enemy_xp_value + XP_KILL_BONUS


# Skill level-up stat bonuses
SKILL_STAT_BONUSES = {
    "melee": {"strength": 1, "max_health": 5},
    "ranged": {"dexterity": 1, "max_health": 3},
    "combat_magic": {"intelligence": 1, "max_mana": 5},
    "nature_magic": {"intelligence": 1, "max_mana": 3, "max_health": 2},
}


# =============================================================================
# ITEM SCALING
# =============================================================================

def scale_item_stat(base_value: int, item_level: int, stat_type: str = "damage") -> int:
    """Scale item stats by level.
    
    Args:
        base_value: Base stat value
        item_level: Item's level
        stat_type: "damage" (12%/lvl), "armor" (10%/lvl), or other (8%/lvl)
    
    Returns:
        Scaled stat value
    """
    if stat_type == "damage":
        multiplier = 1 + (item_level - 1) * 0.12
    elif stat_type == "armor":
        multiplier = 1 + (item_level - 1) * 0.10
    else:
        multiplier = 1 + (item_level - 1) * 0.08
    
    return int(base_value * multiplier)


# Rarity stat multipliers
RARITY_MULTIPLIERS = {
    "common": 1.0,
    "uncommon": 1.15,
    "rare": 1.35,
    "epic": 1.60,
    "legendary": 2.0,
}


def apply_rarity_multiplier(base_value: int, rarity: str) -> int:
    """Apply rarity multiplier to a stat."""
    mult = RARITY_MULTIPLIERS.get(rarity, 1.0)
    return int(base_value * mult)


# Item base values for gold calculation
ITEM_BASE_VALUES = {
    "weapon": 25,
    "armor": 20,
    "consumable": 15,
    "accessory": 50,
}

# Rarity value multipliers (different from stat multipliers)
RARITY_VALUE_MULTIPLIERS = {
    "common": 1.0,
    "uncommon": 1.5,
    "rare": 3.0,
    "epic": 6.0,
    "legendary": 15.0,
}


def calculate_item_value(
    item_type: str,
    item_level: int,
    rarity: str,
    stat_bonuses: Dict[str, int] = None
) -> int:
    """Calculate gold value of an item.
    
    Args:
        item_type: "weapon", "armor", "consumable", "accessory"
        item_level: Item's level
        rarity: Item's rarity tier
        stat_bonuses: Dict of bonus stats (optional)
    
    Returns:
        Gold value
    """
    base = ITEM_BASE_VALUES.get(item_type, 10)
    
    # Level scaling (+20% per level)
    level_mult = 1 + (item_level - 1) * 0.20
    
    # Rarity scaling
    rarity_mult = RARITY_VALUE_MULTIPLIERS.get(rarity, 1.0)
    
    # Stat bonus value
    stat_bonus = 0
    if stat_bonuses:
        stat_bonus = (
            stat_bonuses.get("strength", 0) * 10 +
            stat_bonuses.get("dexterity", 0) * 10 +
            stat_bonuses.get("intelligence", 0) * 10 +
            stat_bonuses.get("health", 0) * 2 +
            stat_bonuses.get("mana", 0) * 3 +
            stat_bonuses.get("damage", 0) * 2 +
            stat_bonuses.get("armor", 0) * 3
        )
    
    value = (base * level_mult * rarity_mult) + stat_bonus
    return max(1, int(value))


# =============================================================================
# ENEMY SCALING
# =============================================================================

def calculate_enemy_stats(base_stats: Dict, level: int) -> Dict:
    """Scale enemy stats by dungeon level.
    
    Args:
        base_stats: Base enemy stats dict
        level: Dungeon level
    
    Returns:
        Scaled stats dict
    """
    return {
        "health": base_stats["health"] + level * base_stats.get("health_per_level", 10),
        "damage": base_stats["damage"] + level * base_stats.get("damage_per_level", 2),
        "armor": base_stats["armor"] + level * base_stats.get("armor_per_level", 1),
        "xp_value": base_stats["xp_value"] + level * 3,
        "gold_min": base_stats.get("gold_min", 3) + level,
        "gold_max": base_stats.get("gold_max", 8) + level * 2,
    }


def enemy_count_for_level(level: int, dungeon_size: int = 80) -> int:
    """Calculate number of enemies for a dungeon level."""
    base_enemies = 15
    enemies_per_level = 8
    
    count = base_enemies + level * enemies_per_level
    
    # Scale with dungeon size
    size_factor = dungeon_size / 80
    return int(count * size_factor)


# =============================================================================
# LOOT FORMULAS
# =============================================================================

def enemy_drop_chance(level: int) -> float:
    """Chance that an enemy drops any loot.
    
    Returns: 0.0 to 1.0 probability
    """
    return min(0.50, 0.15 + level * 0.01)


def rarity_chances(level: int) -> Dict[str, float]:
    """Get rarity probabilities for a dungeon level."""
    return {
        "common": max(0.30, 0.70 - level * 0.02),
        "uncommon": min(0.35, 0.20 + level * 0.01),
        "rare": min(0.20, 0.08 + level * 0.007),
        "epic": min(0.15, 0.02 + level * 0.003),
        "legendary": min(0.02, level * 0.0005),
    }


def roll_gold_drop(gold_min: int, gold_max: int, enemy_level: int) -> int:
    """Calculate gold dropped by enemy."""
    base = random.randint(gold_min, gold_max)
    return base + enemy_level


# =============================================================================
# REGENERATION
# =============================================================================

def health_regen_per_second(in_combat: bool, vitality_bonus: float = 0) -> float:
    """Health regeneration rate.
    
    Out of combat: 0.5 HP/s base
    In combat: 0 (no natural regen)
    """
    if in_combat:
        return 0.0
    return 0.5 + vitality_bonus


def mana_regen_per_second(intelligence: int, in_combat: bool) -> float:
    """Mana regeneration rate.
    
    Base: 2.0 MP/s
    In combat: 50% reduced
    Intelligence bonus: +0.1 per INT
    """
    base_regen = 2.0
    int_bonus = intelligence * 0.1
    total = base_regen + int_bonus
    
    if in_combat:
        total *= 0.5
    
    return total


# =============================================================================
# DUNGEON GENERATION
# =============================================================================

def dungeon_size(level: int) -> int:
    """Calculate dungeon dimensions for a level."""
    return min(150, 60 + level * 10)


def room_count(level: int) -> int:
    """Number of rooms to generate."""
    return min(20, 8 + level)


# =============================================================================
# ECONOMY
# =============================================================================

def merchant_buy_price(item_value: int) -> int:
    """Price player pays to buy from merchant."""
    from .constants import MERCHANT_SELL_RATE
    return int(item_value * MERCHANT_SELL_RATE)


def merchant_sell_price(item_value: int) -> int:
    """Price merchant pays for player's item."""
    from .constants import MERCHANT_BUY_RATE
    return max(1, int(item_value * MERCHANT_BUY_RATE))


def death_gold_penalty(current_gold: int) -> int:
    """Gold lost on party wipe."""
    from .constants import DEATH_GOLD_PENALTY
    return int(current_gold * DEATH_GOLD_PENALTY)


# =============================================================================
# DISTANCE / UTILITY
# =============================================================================

def distance(x1: float, y1: float, x2: float, y2: float) -> float:
    """Euclidean distance between two points."""
    dx = x2 - x1
    dy = y2 - y1
    return math.sqrt(dx * dx + dy * dy)


def in_range(x1: float, y1: float, x2: float, y2: float, range_limit: float) -> bool:
    """Check if two points are within range of each other."""
    return distance(x1, y1, x2, y2) <= range_limit


def ai_spell_delay(spell_cooldown: float) -> float:
    """Time AI waits before auto-casting (gives player time to trigger)."""
    return spell_cooldown * 3.0
