"""Progression processor - handles XP gain and leveling."""

import esper

from ..components import (
    SkillLevels, SkillXP, CharacterLevel, Attributes,
    Health, Mana, PartyMember
)
from ...core.events import EventBus, Event, EventType
from ...core.formulas import (
    xp_for_skill_level, calculate_character_level, SKILL_STAT_BONUSES
)


class ProgressionProcessor(esper.Processor):
    """Processes XP gain and skill level-ups."""
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
    
    def process(self, dt: float):
        """Check for level-ups each frame."""
        for ent, (skills, xp) in esper.get_components(SkillLevels, SkillXP):
            self._check_skill_levelups(ent, skills, xp)
    
    def _check_skill_levelups(self, ent: int, skills: SkillLevels, xp: SkillXP):
        """Check and process skill level-ups."""
        skill_names = ["melee", "ranged", "combat_magic", "nature_magic"]
        
        for skill_name in skill_names:
            current_level = skills.get(skill_name)
            current_xp = xp.get(skill_name)
            required_xp = xp_for_skill_level(current_level)
            
            while current_xp >= required_xp and current_level < 99:
                # Level up!
                current_xp -= required_xp
                current_level += 1
                
                # Update components
                setattr(skills, skill_name, current_level)
                setattr(xp, skill_name, current_xp)
                
                # Apply stat bonuses
                self._apply_levelup_bonuses(ent, skill_name)
                
                # Emit event
                self.event_bus.emit(Event(EventType.LEVEL_UP, {
                    "entity": ent,
                    "skill": skill_name,
                    "new_level": current_level
                }))
                
                # Recalculate character level
                if esper.has_component(ent, CharacterLevel):
                    char_level = esper.component_for_entity(ent, CharacterLevel)
                    all_skills = {
                        "melee": skills.melee,
                        "ranged": skills.ranged,
                        "combat_magic": skills.combat_magic,
                        "nature_magic": skills.nature_magic
                    }
                    char_level.level = calculate_character_level(all_skills)
                
                # Next level check
                required_xp = xp_for_skill_level(current_level)
    
    def _apply_levelup_bonuses(self, ent: int, skill_name: str):
        """Apply stat bonuses from leveling a skill."""
        bonuses = SKILL_STAT_BONUSES.get(skill_name, {})
        
        if "strength" in bonuses or "dexterity" in bonuses or "intelligence" in bonuses:
            if esper.has_component(ent, Attributes):
                attrs = esper.component_for_entity(ent, Attributes)
                attrs.strength += bonuses.get("strength", 0)
                attrs.dexterity += bonuses.get("dexterity", 0)
                attrs.intelligence += bonuses.get("intelligence", 0)
        
        if "max_health" in bonuses:
            if esper.has_component(ent, Health):
                health = esper.component_for_entity(ent, Health)
                health.maximum += bonuses["max_health"]
                health.current += bonuses["max_health"]  # Also heal
        
        if "max_mana" in bonuses:
            if esper.has_component(ent, Mana):
                mana = esper.component_for_entity(ent, Mana)
                mana.maximum += bonuses["max_mana"]
                mana.current += bonuses["max_mana"]  # Also restore
