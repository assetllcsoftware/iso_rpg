"""Skill tree viewer UI."""

import pygame
import esper
import math
from typing import List, Tuple, Dict

from ..core.constants import (
    COLOR_UI_BG, COLOR_UI_BORDER, COLOR_UI_ACCENT,
    COLOR_TEXT, COLOR_TEXT_DIM, COLOR_XP
)
from ..ecs.components import (
    SkillLevels, SkillXP, CharacterLevel, CharacterName, PartyMember
)
from ..core.formulas import xp_for_skill_level


# Skill colors
SKILL_COLORS = {
    'melee': (200, 100, 100),
    'ranged': (100, 200, 100),
    'combat_magic': (200, 100, 200),
    'nature_magic': (100, 200, 150),
}

SKILL_NAMES = {
    'melee': "Melee",
    'ranged': "Ranged",
    'combat_magic': "Combat Magic",
    'nature_magic': "Nature Magic",
}

# Skill unlock data
SKILL_UNLOCKS = {
    'melee': [
        (0, "Basic Attacks", "Use melee weapons"),
        (3, "Power Strike", "150% damage, 3s CD"),
        (6, "Whirlwind", "AoE attack, 10s CD"),
        (10, "Berserker Rage", "+50% speed, 30s CD"),
        (15, "Execute", "Instant kill <15% HP"),
    ],
    'ranged': [
        (0, "Basic Shots", "Use ranged weapons"),
        (3, "Quick Shot", "Fire 2 arrows, 3s CD"),
        (6, "Piercing Arrow", "Hits all, 10s CD"),
        (10, "Multishot", "Fire 3 arrows, 10s CD"),
        (15, "Rain of Arrows", "AoE damage, 30s CD"),
    ],
    'combat_magic': [
        (0, "Ice Shard", "Fast, FREE, 1s CD"),
        (0, "Fireball", "AoE fire, 1.5s CD"),
        (2, "Lightning Bolt", "35 dmg, 3s CD"),
        (3, "Chain Lightning", "Hits 3, 4s CD"),
        (5, "Inferno", "80 AoE dmg, 10s CD"),
        (6, "Blizzard", "60 AoE dmg, 12s CD"),
        (10, "Meteor", "200 dmg!, 30s CD"),
        (15, "Armageddon", "Everything dies, 45s CD"),
    ],
    'nature_magic': [
        (0, "Heal", "Quick heal, 1.5s CD"),
        (2, "Poison Cloud", "DoT, 4s CD"),
        (2, "Entangle", "Root enemies, 3s CD"),
        (3, "Revive", "Revive ally, 5s CD"),
        (5, "Group Heal", "Big heal, 10s CD"),
        (6, "Regeneration", "HoT aura, 12s CD"),
        (8, "Summon Wolf", "Wolf ally, 30s CD"),
        (12, "Sanctuary", "Mega heal, 45s CD"),
    ],
}


class SkillTreeUI:
    """Skill tree viewer."""
    
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.visible = False
        self.selected_skill = 'melee'
        
        # Party tab
        self.party_entities: List[int] = []
        self.selected_entity: int = -1
        
        # Fonts
        pygame.font.init()
        self.font = pygame.font.Font(None, 24)
        self.font_large = pygame.font.Font(None, 32)
        self.font_small = pygame.font.Font(None, 18)
        self.font_title = pygame.font.Font(None, 48)
        
        # Layout (calculated dynamically in render)
        self.panel_width = 900
        self.panel_height = 550
        self.panel_x = 0
        self.panel_y = 0
    
    def toggle(self):
        """Toggle visibility."""
        self.visible = not self.visible
        if self.visible:
            self._refresh_party()
    
    def show(self, entity: int):
        """Show skill tree for entity."""
        self.visible = True
        self.selected_entity = entity
        self._refresh_party()
    
    def hide(self):
        """Hide skill tree."""
        self.visible = False
    
    def _refresh_party(self):
        """Refresh party entity list."""
        self.party_entities = []
        for ent, (member,) in esper.get_components(PartyMember):
            self.party_entities.append((member.party_index, ent))
        self.party_entities.sort(key=lambda x: x[0])
        self.party_entities = [e for _, e in self.party_entities]
        
        if self.selected_entity < 0 and self.party_entities:
            self.selected_entity = self.party_entities[0]
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle input events."""
        if not self.visible:
            return False
        
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_k):
                self.hide()
                return True
            elif event.key == pygame.K_TAB:
                self._cycle_party_member()
                return True
            elif event.key == pygame.K_1:
                self.selected_skill = 'melee'
                return True
            elif event.key == pygame.K_2:
                self.selected_skill = 'ranged'
                return True
            elif event.key == pygame.K_3:
                self.selected_skill = 'combat_magic'
                return True
            elif event.key == pygame.K_4:
                self.selected_skill = 'nature_magic'
                return True
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                return self._handle_click(event.pos)
        
        return False
    
    def _cycle_party_member(self):
        """Cycle through party members."""
        if not self.party_entities:
            return
        try:
            idx = self.party_entities.index(self.selected_entity)
            self.selected_entity = self.party_entities[(idx + 1) % len(self.party_entities)]
        except ValueError:
            self.selected_entity = self.party_entities[0]
    
    def _handle_click(self, pos: Tuple[int, int]) -> bool:
        """Handle mouse click."""
        # Check party tabs
        for i, ent in enumerate(self.party_entities):
            tab_rect = pygame.Rect(self.panel_x + 20 + i * 110, self.panel_y - 40, 100, 30)
            if tab_rect.collidepoint(pos):
                self.selected_entity = ent
                return True
        return False
    
    def render(self):
        """Render the skill tree."""
        if not self.visible:
            return
        
        ent = self.selected_entity
        if ent < 0:
            return
        
        # Update panel positions based on actual screen size
        screen_w = self.screen.get_width()
        screen_h = self.screen.get_height()
        self.panel_x = (screen_w - self.panel_width) // 2
        self.panel_y = (screen_h - self.panel_height) // 2
        
        # Darken background
        overlay = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))
        
        # Party tabs
        self._render_party_tabs()
        
        # Main panel
        panel_rect = pygame.Rect(self.panel_x, self.panel_y, 
                                 self.panel_width, self.panel_height)
        pygame.draw.rect(self.screen, COLOR_UI_BG, panel_rect)
        pygame.draw.rect(self.screen, COLOR_UI_BORDER, panel_rect, 3)
        
        # Title
        title = self.font_title.render("SKILLS", True, COLOR_UI_ACCENT)
        title_rect = title.get_rect(centerx=self.screen.get_width() // 2, y=self.panel_y + 15)
        self.screen.blit(title, title_rect)
        
        # Character name
        name = "???"
        level = 1
        if esper.has_component(ent, CharacterName):
            name = esper.component_for_entity(ent, CharacterName).name
        if esper.has_component(ent, CharacterLevel):
            level = esper.component_for_entity(ent, CharacterLevel).level
        
        char_text = self.font.render(f"{name} - Level {level}", True, COLOR_TEXT)
        self.screen.blit(char_text, (self.panel_x + 20, self.panel_y + 20))
        
        # Skill tabs
        self._render_skill_tabs()
        
        # Selected skill tree
        self._render_skill_tree()
        
        # Instructions
        hint = self.font_small.render(
            "Press 1-4 to switch skills, K or ESC to close, TAB to switch characters",
            True, COLOR_TEXT_DIM
        )
        hint_rect = hint.get_rect(centerx=self.screen.get_width() // 2, 
                                  y=self.panel_y + self.panel_height - 25)
        self.screen.blit(hint, hint_rect)
    
    def _render_party_tabs(self):
        """Render party member tabs."""
        for i, ent in enumerate(self.party_entities):
            tab_rect = pygame.Rect(self.panel_x + 20 + i * 110, self.panel_y - 40, 100, 30)
            
            is_selected = ent == self.selected_entity
            if is_selected:
                pygame.draw.rect(self.screen, (80, 70, 100), tab_rect)
                pygame.draw.rect(self.screen, COLOR_UI_ACCENT, tab_rect, 2)
            else:
                pygame.draw.rect(self.screen, (50, 45, 60), tab_rect)
                pygame.draw.rect(self.screen, (80, 75, 95), tab_rect, 1)
            
            name = "???"
            if esper.has_component(ent, CharacterName):
                name = esper.component_for_entity(ent, CharacterName).name
            
            name_surf = self.font.render(name[:12], True, COLOR_TEXT)
            self.screen.blit(name_surf, (tab_rect.x + 8, tab_rect.y + 6))
    
    def _render_skill_tabs(self):
        """Render skill category tabs."""
        ent = self.selected_entity
        tab_y = self.panel_y + 60
        tab_width = 200
        tab_height = 50
        
        skills = ['melee', 'ranged', 'combat_magic', 'nature_magic']
        
        for i, skill_id in enumerate(skills):
            tab_x = self.panel_x + 20 + i * (tab_width + 10)
            tab_rect = pygame.Rect(tab_x, tab_y, tab_width, tab_height)
            
            color = SKILL_COLORS[skill_id]
            is_selected = skill_id == self.selected_skill
            
            if is_selected:
                pygame.draw.rect(self.screen, color, tab_rect)
            else:
                pygame.draw.rect(self.screen, (40, 35, 50), tab_rect)
            pygame.draw.rect(self.screen, color, tab_rect, 2)
            
            # Skill name and level
            skill_level = 0
            if esper.has_component(ent, SkillLevels):
                skills_comp = esper.component_for_entity(ent, SkillLevels)
                skill_level = skills_comp.get(skill_id)
            
            name = SKILL_NAMES[skill_id]
            text_color = (255, 255, 255) if is_selected else color
            
            name_text = self.font.render(name, True, text_color)
            level_text = self.font_small.render(f"Level {skill_level}", True, text_color)
            
            self.screen.blit(name_text, (tab_x + 10, tab_y + 8))
            self.screen.blit(level_text, (tab_x + 10, tab_y + 28))
            
            # XP bar
            if esper.has_component(ent, SkillXP):
                skill_xp = esper.component_for_entity(ent, SkillXP)
                xp = skill_xp.get(skill_id)
                xp_needed = xp_for_skill_level(skill_level)
                xp_pct = xp / xp_needed if xp_needed > 0 else 0
                
                bar_x = tab_x + 100
                bar_y = tab_y + 30
                bar_w = 90
                bar_h = 10
                
                pygame.draw.rect(self.screen, (30, 25, 35), (bar_x, bar_y, bar_w, bar_h))
                pygame.draw.rect(self.screen, color, (bar_x, bar_y, int(bar_w * xp_pct), bar_h))
    
    def _render_skill_tree(self):
        """Render selected skill's unlock tree."""
        ent = self.selected_entity
        tree_y = self.panel_y + 130
        tree_x = self.panel_x + 40
        
        skill_id = self.selected_skill
        skill_level = 0
        if esper.has_component(ent, SkillLevels):
            skills_comp = esper.component_for_entity(ent, SkillLevels)
            skill_level = skills_comp.get(skill_id)
        
        color = SKILL_COLORS[skill_id]
        unlocks = SKILL_UNLOCKS[skill_id]
        
        # Title
        title = self.font_large.render(f"{SKILL_NAMES[skill_id]} Abilities", True, color)
        self.screen.blit(title, (tree_x, tree_y))
        
        # Draw unlock nodes
        node_y = tree_y + 50
        node_spacing = 50
        
        for req_level, ability_name, description in unlocks:
            unlocked = skill_level >= req_level
            
            # Node circle
            node_x = tree_x + 30
            node_color = color if unlocked else (60, 55, 70)
            pygame.draw.circle(self.screen, node_color, (node_x, node_y + 15), 15)
            
            if unlocked:
                # Checkmark
                pygame.draw.circle(self.screen, (255, 255, 255), (node_x, node_y + 15), 8)
            else:
                # Lock X
                pygame.draw.line(self.screen, (100, 100, 100),
                               (node_x - 5, node_y + 10), (node_x + 5, node_y + 20), 2)
                pygame.draw.line(self.screen, (100, 100, 100),
                               (node_x + 5, node_y + 10), (node_x - 5, node_y + 20), 2)
            
            # Level requirement
            text_x = node_x + 30
            level_color = (100, 255, 100) if unlocked else (255, 100, 100)
            level_text = self.font_small.render(f"Lv.{req_level}", True, level_color)
            self.screen.blit(level_text, (text_x, node_y))
            
            # Ability name
            name_color = COLOR_TEXT if unlocked else COLOR_TEXT_DIM
            name_text = self.font.render(ability_name, True, name_color)
            self.screen.blit(name_text, (text_x + 50, node_y))
            
            # Description
            desc_text = self.font_small.render(description, True, COLOR_TEXT_DIM)
            self.screen.blit(desc_text, (text_x + 50, node_y + 22))
            
            # Connection line
            if req_level < unlocks[-1][0]:
                line_color = color if unlocked else (50, 45, 60)
                pygame.draw.line(self.screen, line_color,
                               (node_x, node_y + 30), (node_x, node_y + node_spacing - 5), 2)
            
            node_y += node_spacing

