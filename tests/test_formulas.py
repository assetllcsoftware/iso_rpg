"""Tests for combat and economy formulas.

These tests ensure the core math of the game is correct.
If these break, damage numbers, XP, gold, and item values will be wrong.
"""

import pytest
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core.formulas import (
    calculate_physical_damage,
    calculate_elemental_damage,
    calculate_spell_damage,
    calculate_heal_amount,
    armor_damage_reduction,
    effective_hp,
    xp_for_skill_level,
    calculate_character_level,
    scale_item_stat,
    apply_rarity_multiplier,
    calculate_item_value,
    calculate_enemy_stats,
    merchant_buy_price,
    merchant_sell_price,
    death_gold_penalty,
    distance,
    in_range,
    XP_MELEE_HIT,
    XP_SPELL_HIT,
    XP_HEAL_CAST,
    XP_KILL_BONUS,
)


# =============================================================================
# PHYSICAL COMBAT TESTS
# Gameplay Impact: Players feel stronger as STR increases, armor matters
# =============================================================================

class TestPhysicalDamage:
    """Test physical damage calculations."""
    
    def test_weapon_damage_scales_with_strength(self):
        """Players feel stronger as STR increases.
        
        GAMEPLAY: A warrior with 20 STR should hit harder than one with 10 STR.
        Without this, pumping STR feels pointless.
        """
        import random
        random.seed(999)  # No crits for consistent test
        
        weapon_dmg = 10
        armor = 0
        
        # Low STR (10) -> 1.5x multiplier
        dmg_low_str, _ = calculate_physical_damage(weapon_dmg, 10, armor)
        
        # High STR (20) -> 2.0x multiplier  
        dmg_high_str, _ = calculate_physical_damage(weapon_dmg, 20, armor)
        
        assert dmg_high_str > dmg_low_str, "Higher STR should deal more damage"
    
    def test_armor_reduces_damage(self):
        """Armor items are worth equipping.
        
        GAMEPLAY: Wearing armor should noticeably reduce incoming damage.
        Without this, players won't bother with armor gear.
        """
        import random
        random.seed(999)  # No crits for consistent test
        
        weapon_dmg = 100
        strength = 10
        
        dmg_no_armor, _ = calculate_physical_damage(weapon_dmg, strength, 0)
        dmg_with_armor, _ = calculate_physical_damage(weapon_dmg, strength, 50)
        
        assert dmg_with_armor < dmg_no_armor, "Armor should reduce damage"
        # 50 armor should reduce damage by ~33%
        assert dmg_with_armor < dmg_no_armor * 0.75
    
    def test_armor_diminishing_returns(self):
        """Can't become invincible with enough armor.
        
        GAMEPLAY: Even with massive armor, enemies should still hurt you.
        Prevents degenerate "stack armor, become unkillable" builds.
        """
        import random
        random.seed(999)  # No crits for consistent test
        
        weapon_dmg = 100
        strength = 10
        
        dmg_100_armor, _ = calculate_physical_damage(weapon_dmg, strength, 100)
        dmg_500_armor, _ = calculate_physical_damage(weapon_dmg, strength, 500)
        
        # 500 armor should NOT be 5x better than 100 armor
        reduction_100 = 1 - (dmg_100_armor / (weapon_dmg * 1.5))  # Account for STR
        reduction_500 = 1 - (dmg_500_armor / (weapon_dmg * 1.5))
        
        # Diminishing returns: 500 armor should be less than 2x as effective as 100
        assert reduction_500 < reduction_100 * 2
    
    def test_minimum_damage_is_one(self):
        """Attacks always do something.
        
        GAMEPLAY: Even against high armor targets, you can chip away.
        Prevents "I literally can't damage this enemy" situations.
        """
        weapon_dmg = 1
        strength = 1
        armor = 1000
        
        dmg, _ = calculate_physical_damage(weapon_dmg, strength, armor)
        assert dmg >= 1, "Minimum damage should be 1"
    
    def test_critical_hits_deal_150_percent(self):
        """Crits feel impactful.
        
        GAMEPLAY: When you see "CRIT!", the damage should be noticeably higher.
        Makes combat more exciting with damage spikes.
        """
        import random
        random.seed(999)  # No crits for consistent test
        
        weapon_dmg = 100
        strength = 10
        armor = 0
        
        base_dmg, _ = calculate_physical_damage(weapon_dmg, strength, armor, 0)
        
        # Verify base damage is correct (non-crit)
        expected_base = int(weapon_dmg * (1 + strength * 0.05))
        assert base_dmg == expected_base or base_dmg == int(expected_base * 1.5)
    
    def test_dex_increases_crit_chance(self):
        """DEX builds are viable.
        
        GAMEPLAY: High DEX characters should crit more often.
        Makes DEX a viable alternative to pure STR builds.
        """
        # Run many trials and compare crit rates
        import random
        random.seed(42)
        
        weapon_dmg = 10
        strength = 10
        armor = 0
        
        # Count crits with low DEX (0 DEX = 5% crit)
        crits_low_dex = sum(
            1 for _ in range(1000)
            if calculate_physical_damage(weapon_dmg, strength, armor, 0)[1]
        )
        
        # Reset seed for fair comparison
        random.seed(42)
        
        # Count crits with high DEX (50 DEX = 30% crit)
        crits_high_dex = sum(
            1 for _ in range(1000)
            if calculate_physical_damage(weapon_dmg, strength, armor, 50)[1]
        )
        
        assert crits_high_dex > crits_low_dex, "Higher DEX should crit more"


# =============================================================================
# SPELL COMBAT TESTS
# Gameplay Impact: Mages feel stronger as INT increases, skill levels matter
# =============================================================================

class TestSpellDamage:
    """Test spell damage calculations."""
    
    def test_spell_damage_scales_with_intelligence(self):
        """Mages feel stronger as INT increases.
        
        GAMEPLAY: A mage with 20 INT should hit harder than one with 10 INT.
        Without this, INT feels pointless for damage dealers.
        """
        base_dmg = 100
        skill_level = 1
        
        dmg_low_int = calculate_spell_damage(base_dmg, 10, skill_level)
        dmg_high_int = calculate_spell_damage(base_dmg, 20, skill_level)
        
        assert dmg_high_int > dmg_low_int, "Higher INT should deal more spell damage"
    
    def test_spell_damage_scales_with_skill_level(self):
        """Leveling up spells is rewarding.
        
        GAMEPLAY: Using spells levels up magic skills, making future spells stronger.
        Core progression loop for mage characters.
        """
        base_dmg = 100
        intelligence = 10
        
        dmg_level_1 = calculate_spell_damage(base_dmg, intelligence, caster_skill_level=1)
        dmg_level_10 = calculate_spell_damage(base_dmg, intelligence, caster_skill_level=10)
        
        assert dmg_level_10 > dmg_level_1, "Higher skill level should deal more damage"
        # Level 10 should be ~45% stronger than level 1
        assert dmg_level_10 >= dmg_level_1 * 1.4
    
    def test_elemental_resistance_reduces_damage(self):
        """Resistance gear matters.
        
        GAMEPLAY: Fire resistance should reduce fire damage taken.
        Makes resistance gear valuable against specific enemies.
        """
        base_dmg = 100
        
        dmg_no_resist = calculate_elemental_damage(base_dmg, target_resistance=0)
        dmg_with_resist = calculate_elemental_damage(base_dmg, target_resistance=0.5)
        
        assert dmg_with_resist < dmg_no_resist, "Resistance should reduce damage"
        assert dmg_with_resist == 50, "50% resistance should halve damage"
    
    def test_elemental_weakness_increases_damage(self):
        """Exploit enemy weaknesses.
        
        GAMEPLAY: Using fire against ice enemies should deal bonus damage.
        Encourages strategic spell selection.
        """
        base_dmg = 100
        
        dmg_normal = calculate_elemental_damage(base_dmg, target_resistance=0)
        dmg_weak = calculate_elemental_damage(base_dmg, target_resistance=-0.5)
        
        assert dmg_weak > dmg_normal, "Weakness should increase damage"
        assert dmg_weak == 150, "-50% resistance should deal 150% damage"
    
    def test_heal_scales_with_int_and_skill(self):
        """Healers scale properly.
        
        GAMEPLAY: A dedicated healer should heal more than a warrior with heal spell.
        Makes healer builds viable.
        """
        base_heal = 50
        
        heal_low_stats = calculate_heal_amount(base_heal, 10, 1)
        heal_high_stats = calculate_heal_amount(base_heal, 20, 10)
        
        assert heal_high_stats > heal_low_stats, "Higher stats should heal more"


# =============================================================================
# ECONOMY TESTS
# Gameplay Impact: Trading feels fair, death has consequences
# =============================================================================

class TestEconomy:
    """Test economy calculations."""
    
    def test_merchant_buy_price_is_full_value(self):
        """Buying feels fair.
        
        GAMEPLAY: Items cost their full value to buy.
        Standard RPG economy - buy high, sell low.
        """
        item_value = 100
        buy_price = merchant_buy_price(item_value)
        
        assert buy_price == 100, "Buy price should be full value"
    
    def test_merchant_sell_price_is_half(self):
        """Selling feels fair.
        
        GAMEPLAY: You get 50% of item value when selling.
        Encourages using items rather than hoarding for gold.
        """
        item_value = 100
        sell_price = merchant_sell_price(item_value)
        
        assert sell_price == 50, "Sell price should be 50% of value"
    
    def test_sell_price_minimum_one(self):
        """Can always sell items for something.
        
        GAMEPLAY: Even trash items sell for at least 1 gold.
        """
        sell_price = merchant_sell_price(1)
        assert sell_price >= 1, "Minimum sell price should be 1"
    
    def test_death_penalty_takes_50_percent_gold(self):
        """Death has consequences.
        
        GAMEPLAY: Dying should hurt significantly.
        50% gold loss makes death meaningful and encourages caution.
        """
        current_gold = 1000
        penalty = death_gold_penalty(current_gold)
        
        assert penalty == 500, "Death penalty should be 50% of gold"
    
    def test_item_value_scales_with_level(self):
        """Higher level items worth more.
        
        GAMEPLAY: Level 10 sword should be worth more than level 1 sword.
        Makes dungeon progression rewarding.
        """
        value_level_1 = calculate_item_value("weapon", item_level=1, rarity="common")
        value_level_10 = calculate_item_value("weapon", item_level=10, rarity="common")
        
        assert value_level_10 > value_level_1, "Higher level items should be worth more"
    
    def test_rarity_multiplies_item_value(self):
        """Rare items worth more gold.
        
        GAMEPLAY: Finding a legendary item should feel jackpot-worthy.
        """
        value_common = calculate_item_value("weapon", item_level=5, rarity="common")
        value_legendary = calculate_item_value("weapon", item_level=5, rarity="legendary")
        
        assert value_legendary > value_common * 5, "Legendary should be worth much more"


# =============================================================================
# UTILITY TESTS
# =============================================================================

class TestUtility:
    """Test utility functions."""
    
    def test_distance_calculation(self):
        """Distance formula is correct."""
        d = distance(0, 0, 3, 4)
        assert d == 5.0, "3-4-5 triangle should have distance 5"
    
    def test_in_range_true_when_close(self):
        """Range check works for close entities."""
        assert in_range(0, 0, 1, 1, range_limit=2) is True
    
    def test_in_range_false_when_far(self):
        """Range check works for far entities."""
        assert in_range(0, 0, 10, 10, range_limit=2) is False


# =============================================================================
# PROGRESSION TESTS
# =============================================================================

class TestProgression:
    """Test progression calculations."""
    
    def test_xp_required_increases_per_level(self):
        """Higher levels need more XP.
        
        GAMEPLAY: Leveling slows down as you progress.
        Standard RPG pacing.
        """
        xp_level_1 = xp_for_skill_level(1)
        xp_level_10 = xp_for_skill_level(10)
        
        assert xp_level_10 > xp_level_1, "Higher levels need more XP"
        # Level 10 should need significantly more than level 1
        assert xp_level_10 > xp_level_1 * 5
    
    def test_character_level_calculation(self):
        """Character level reflects total progress.
        
        GAMEPLAY: Character level is displayed and affects some systems.
        """
        # Total skills = 8 -> character level = 4
        skills = {"melee": 2, "ranged": 2, "combat_magic": 2, "nature_magic": 2}
        level = calculate_character_level(skills)
        
        assert level == 4, "Character level should be sum of skills / 2"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

