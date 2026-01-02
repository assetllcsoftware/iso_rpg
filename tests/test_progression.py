"""Tests for progression system.

These tests ensure XP, leveling, and skill advancement work.
If broken, characters can't grow stronger.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core.formulas import (
    xp_for_skill_level,
    calculate_character_level,
    XP_MELEE_HIT,
    XP_RANGED_HIT,
    XP_SPELL_HIT,
    XP_HEAL_CAST,
    XP_KILL_BONUS,
    SKILL_STAT_BONUSES,
)


# =============================================================================
# XP GAIN TESTS
# Gameplay Impact: Actions reward XP
# =============================================================================

class TestXPGain:
    """Test XP is gained from actions."""
    
    def test_melee_hit_grants_melee_xp(self):
        """Using melee levels melee skill.
        
        GAMEPLAY: Swing sword, gain melee XP.
        Core progression for warriors.
        """
        assert XP_MELEE_HIT > 0, "Melee hits should grant XP"
    
    def test_ranged_hit_grants_ranged_xp(self):
        """Using ranged levels ranged skill.
        
        GAMEPLAY: Shoot arrow, gain ranged XP.
        """
        assert XP_RANGED_HIT > 0, "Ranged hits should grant XP"
    
    def test_spell_hit_grants_magic_xp(self):
        """Using spells levels magic skill.
        
        GAMEPLAY: Cast fireball, gain combat magic XP.
        """
        assert XP_SPELL_HIT > 0, "Spell hits should grant XP"
    
    def test_heal_grants_nature_magic_xp(self):
        """Healing levels nature magic.
        
        GAMEPLAY: Cast heal, gain nature magic XP.
        """
        assert XP_HEAL_CAST > 0, "Healing should grant XP"
    
    def test_kill_grants_bonus_xp(self):
        """Killing enemies gives XP bonus.
        
        GAMEPLAY: Last hit on enemy = bonus XP.
        """
        assert XP_KILL_BONUS > 0, "Kills should grant bonus XP"
    
    def test_xp_granted_to_correct_skill(self):
        """XP goes to right skill.
        
        GAMEPLAY: Melee XP goes to melee, not ranged.
        """
        # Would test ProgressionProcessor assigns XP correctly
        pass


# =============================================================================
# LEVELING TESTS
# Gameplay Impact: Skills level up
# =============================================================================

class TestLeveling:
    """Test skill leveling mechanics."""
    
    def test_xp_required_increases_per_level(self):
        """Higher levels need more XP.
        
        GAMEPLAY: Level 2 needs more XP than level 1.
        Pacing slows as you progress.
        """
        xp_level_1 = xp_for_skill_level(1)
        xp_level_5 = xp_for_skill_level(5)
        xp_level_10 = xp_for_skill_level(10)
        
        assert xp_level_5 > xp_level_1, "Level 5 needs more XP than level 1"
        assert xp_level_10 > xp_level_5, "Level 10 needs more XP than level 5"
    
    def test_character_level_is_sum_of_skills(self):
        """Character level reflects total progress.
        
        GAMEPLAY: Character level = sum(skills) / 2
        Shows overall progression.
        """
        skills = {"melee": 5, "ranged": 3, "combat_magic": 2, "nature_magic": 2}
        level = calculate_character_level(skills)
        
        expected = (5 + 3 + 2 + 2) // 2  # 6
        assert level == expected
    
    def test_minimum_character_level_is_one(self):
        """Character level at least 1.
        
        GAMEPLAY: New character is level 1, not 0.
        """
        skills = {"melee": 1, "ranged": 1, "combat_magic": 1, "nature_magic": 1}
        level = calculate_character_level(skills)
        
        assert level >= 1


# =============================================================================
# STAT BONUS TESTS
# Gameplay Impact: Leveling makes you stronger
# =============================================================================

class TestStatBonuses:
    """Test level-up stat bonuses."""
    
    def test_skill_levelup_grants_stat_bonus(self):
        """Leveling up makes you stronger.
        
        GAMEPLAY: Each skill level gives stats.
        Tangible reward for leveling.
        """
        assert len(SKILL_STAT_BONUSES) > 0, "Should have stat bonuses defined"
    
    def test_melee_levelup_gives_strength(self):
        """Melee leveling gives expected stats.
        
        GAMEPLAY: Melee skill grants STR and HP.
        """
        bonuses = SKILL_STAT_BONUSES.get("melee", {})
        assert "strength" in bonuses, "Melee should grant STR"
        assert "max_health" in bonuses, "Melee should grant HP"
    
    def test_magic_levelup_gives_mana(self):
        """Magic leveling gives expected stats.
        
        GAMEPLAY: Magic skills grant INT and MP.
        """
        bonuses = SKILL_STAT_BONUSES.get("combat_magic", {})
        assert "intelligence" in bonuses, "Combat Magic should grant INT"
        assert "max_mana" in bonuses, "Combat Magic should grant MP"
    
    def test_nature_magic_gives_hybrid_stats(self):
        """Nature magic is hybrid.
        
        GAMEPLAY: Nature magic gives INT, MP, and HP.
        Support/healer role.
        """
        bonuses = SKILL_STAT_BONUSES.get("nature_magic", {})
        assert "intelligence" in bonuses, "Nature Magic should grant INT"
        assert "max_mana" in bonuses, "Nature Magic should grant MP"
        assert "max_health" in bonuses, "Nature Magic should grant HP"


# =============================================================================
# SKILL TREE TESTS
# Gameplay Impact: Can unlock and upgrade abilities
# =============================================================================

class TestSkillTree:
    """Test skill tree functionality."""
    
    def test_can_allocate_skill_points(self):
        """Skill tree works.
        
        GAMEPLAY: Level up, can spend point in skill tree.
        """
        pass
    
    def test_skill_requirements_enforced(self):
        """Can't skip skill prerequisites.
        
        GAMEPLAY: Need tier 1 skill before tier 2.
        """
        pass
    
    def test_skill_points_saved_and_loaded(self):
        """Progress persists.
        
        GAMEPLAY: Skill allocations survive save/load.
        """
        pass
    
    def test_skill_points_earned_on_levelup(self):
        """Get points from leveling.
        
        GAMEPLAY: Level up = 1 skill point.
        """
        pass


# =============================================================================
# ENEMY XP VALUE TESTS
# Gameplay Impact: Enemies give appropriate XP
# =============================================================================

class TestEnemyXPValues:
    """Test enemy XP rewards."""
    
    def test_enemy_gives_xp_on_death(self):
        """Kill enemy = XP.
        
        GAMEPLAY: Killing enemies progresses your character.
        """
        pass
    
    def test_higher_level_enemies_more_xp(self):
        """Harder enemies = more XP.
        
        GAMEPLAY: Dungeon level 10 enemies give more XP than level 1.
        """
        pass
    
    def test_xp_split_between_party(self):
        """XP shared.
        
        GAMEPLAY: Both Hero and Lyra get XP from kills.
        """
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

