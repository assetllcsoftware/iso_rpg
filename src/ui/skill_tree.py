"""Skill tree viewer UI."""

import pygame
from ..engine.constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    COLOR_UI_BG, COLOR_UI_BORDER, COLOR_UI_ACCENT,
    COLOR_TEXT, COLOR_TEXT_DIM, COLOR_XP,
    SKILL_MELEE, SKILL_RANGED, SKILL_COMBAT_MAGIC, SKILL_NATURE_MAGIC
)


# Skill unlock data
SKILL_UNLOCKS = {
    SKILL_MELEE: [
        (1, "Basic Attacks", "Use melee weapons"),
        (5, "Power Strike", "150% damage, 3s cooldown"),
        (10, "Whirlwind", "AoE attack around self"),
        (15, "Berserker Rage", "+50% attack speed 10s"),
        (20, "Execute", "Instant kill <15% HP"),
        (25, "Blade Master", "+20% crit chance"),
    ],
    SKILL_RANGED: [
        (1, "Basic Shots", "Use ranged weapons"),
        (5, "Quick Shot", "Fire 2 arrows rapidly"),
        (10, "Piercing Arrow", "Hits all in line"),
        (15, "Multishot", "Fire 3 arrows spread"),
        (20, "Rain of Arrows", "AoE damage"),
        (25, "Sharpshooter", "+30% crit damage"),
    ],
    SKILL_COMBAT_MAGIC: [
        (1, "Fireball", "Explosive fire damage"),
        (3, "Lightning Bolt", "Instant electric hit"),
        (5, "Ice Shard", "Fast ice projectile"),
        (8, "Chain Lightning", "Jumps to 3 enemies"),
        (12, "Meteor", "Massive AoE damage"),
        (20, "Armageddon", "Ultimate destruction"),
    ],
    SKILL_NATURE_MAGIC: [
        (1, "Heal", "Single target heal"),
        (3, "Regeneration", "Heal over time"),
        (5, "Group Heal", "Heal all party"),
        (8, "Summon Wolf", "Wolf companion"),
        (12, "Poison Cloud", "Damage over time AoE"),
        (20, "Resurrection", "Revive fallen ally"),
    ],
}

SKILL_COLORS = {
    SKILL_MELEE: (200, 100, 100),
    SKILL_RANGED: (100, 200, 100),
    SKILL_COMBAT_MAGIC: (200, 100, 200),
    SKILL_NATURE_MAGIC: (100, 200, 150),
}

SKILL_NAMES = {
    SKILL_MELEE: "Melee",
    SKILL_RANGED: "Ranged", 
    SKILL_COMBAT_MAGIC: "Combat Magic",
    SKILL_NATURE_MAGIC: "Nature Magic",
}


class SkillTreeUI:
    """Skill tree viewer."""
    
    def __init__(self, screen):
        self.screen = screen
        self.visible = False
        self.selected_skill = SKILL_MELEE
        
        # Party switching
        self.party = None
        self.party_index = 0
        self.viewing_character = None
        
        # Fonts
        pygame.font.init()
        self.font = pygame.font.Font(None, 24)
        self.font_large = pygame.font.Font(None, 32)
        self.font_small = pygame.font.Font(None, 18)
        self.font_title = pygame.font.Font(None, 48)
        
        # Layout
        self.panel_width = 900
        self.panel_height = 550
        self.panel_x = (SCREEN_WIDTH - self.panel_width) // 2
        self.panel_y = (SCREEN_HEIGHT - self.panel_height) // 2
    
    def toggle(self):
        """Toggle visibility."""
        self.visible = not self.visible
    
    def set_party(self, party, current_index=0):
        """Set the party reference for switching between members."""
        self.party = party
        self.party_index = current_index
        if party and len(party) > current_index:
            self.viewing_character = party[current_index]
    
    def handle_event(self, event):
        """Handle input events."""
        if not self.visible:
            return False
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_TAB and self.party:
                # Cycle through party members
                self.party_index = (self.party_index + 1) % len(self.party)
                self.viewing_character = self.party[self.party_index]
                return True
            elif event.key == pygame.K_1:
                self.selected_skill = SKILL_MELEE
                return True
            elif event.key == pygame.K_2:
                self.selected_skill = SKILL_RANGED
                return True
            elif event.key == pygame.K_3:
                self.selected_skill = SKILL_COMBAT_MAGIC
                return True
            elif event.key == pygame.K_4:
                self.selected_skill = SKILL_NATURE_MAGIC
                return True
            elif event.key in (pygame.K_ESCAPE, pygame.K_k):
                self.visible = False
                return True
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.party:
                # Check party tab clicks
                if self._handle_party_tab_click(event.pos):
                    return True
        
        return False
    
    def _handle_party_tab_click(self, pos):
        """Check if clicking on party member tabs."""
        if not self.party:
            return False
        
        tab_y = self.panel_y - 40
        for i, member in enumerate(self.party):
            tab_rect = pygame.Rect(self.panel_x + 20 + i * 110, tab_y, 100, 30)
            if tab_rect.collidepoint(pos):
                self.party_index = i
                self.viewing_character = member
                return True
        return False
    
    def render(self, character):
        """Render the skill tree."""
        if not self.visible:
            return
        
        # Use viewing_character if set
        char = self.viewing_character or character
        
        # Darken background
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))
        
        # Party tabs above main panel
        if self.party and len(self.party) > 1:
            self._render_party_tabs()
        
        # Main panel
        panel_rect = pygame.Rect(self.panel_x, self.panel_y, 
                                  self.panel_width, self.panel_height)
        pygame.draw.rect(self.screen, COLOR_UI_BG, panel_rect)
        pygame.draw.rect(self.screen, COLOR_UI_BORDER, panel_rect, 3)
        
        # Title
        title = self.font_title.render("SKILLS", True, COLOR_UI_ACCENT)
        title_rect = title.get_rect(centerx=SCREEN_WIDTH // 2, y=self.panel_y + 15)
        self.screen.blit(title, title_rect)
        
        # Character name
        char_text = self.font.render(f"{char.name} - Level {char.level}", 
                                      True, COLOR_TEXT)
        self.screen.blit(char_text, (self.panel_x + 20, self.panel_y + 20))
        
        # Skill tabs
        self._render_tabs(char)
        
        # Selected skill tree
        self._render_skill_tree(char)
        
        # Instructions
        tab_hint = " | TAB to switch characters" if (self.party and len(self.party) > 1) else ""
        hint = self.font_small.render(f"Press 1-4 to switch skills, K or ESC to close{tab_hint}", 
                                       True, COLOR_TEXT_DIM)
        hint_rect = hint.get_rect(centerx=SCREEN_WIDTH // 2, 
                                   y=self.panel_y + self.panel_height - 25)
        self.screen.blit(hint, hint_rect)
    
    def _render_party_tabs(self):
        """Render party member tabs above the main panel."""
        tab_y = self.panel_y - 40
        
        for i, member in enumerate(self.party):
            tab_rect = pygame.Rect(self.panel_x + 20 + i * 110, tab_y, 100, 30)
            
            # Highlight selected
            if i == self.party_index:
                pygame.draw.rect(self.screen, (80, 70, 100), tab_rect)
                pygame.draw.rect(self.screen, COLOR_UI_ACCENT, tab_rect, 2)
            else:
                pygame.draw.rect(self.screen, (50, 45, 60), tab_rect)
                pygame.draw.rect(self.screen, (80, 75, 95), tab_rect, 1)
            
            # Name
            name = self.font.render(member.name[:12], True, COLOR_TEXT)
            self.screen.blit(name, (tab_rect.x + 8, tab_rect.y + 6))
    
    def _render_tabs(self, character):
        """Render skill category tabs."""
        tab_y = self.panel_y + 60
        tab_width = 200
        tab_height = 50
        
        skills = [SKILL_MELEE, SKILL_RANGED, SKILL_COMBAT_MAGIC, SKILL_NATURE_MAGIC]
        
        for i, skill_id in enumerate(skills):
            tab_x = self.panel_x + 20 + i * (tab_width + 10)
            tab_rect = pygame.Rect(tab_x, tab_y, tab_width, tab_height)
            
            color = SKILL_COLORS[skill_id]
            is_selected = skill_id == self.selected_skill
            
            # Tab background
            if is_selected:
                pygame.draw.rect(self.screen, color, tab_rect)
            else:
                pygame.draw.rect(self.screen, (40, 35, 50), tab_rect)
            pygame.draw.rect(self.screen, color, tab_rect, 2)
            
            # Skill name and level
            skill_level = character.skills.get(skill_id, 0)
            name = SKILL_NAMES[skill_id]
            
            text_color = (255, 255, 255) if is_selected else color
            name_text = self.font.render(f"{name}", True, text_color)
            level_text = self.font_small.render(f"Level {skill_level}", True, text_color)
            
            self.screen.blit(name_text, (tab_x + 10, tab_y + 8))
            self.screen.blit(level_text, (tab_x + 10, tab_y + 28))
            
            # XP bar
            xp = character.skill_xp.get(skill_id, 0)
            xp_needed = (skill_level + 1) * 100
            xp_pct = xp / xp_needed if xp_needed > 0 else 0
            
            bar_x = tab_x + 100
            bar_y = tab_y + 30
            bar_w = 90
            bar_h = 10
            
            pygame.draw.rect(self.screen, (30, 25, 35), (bar_x, bar_y, bar_w, bar_h))
            pygame.draw.rect(self.screen, color, (bar_x, bar_y, int(bar_w * xp_pct), bar_h))
    
    def _render_skill_tree(self, character):
        """Render the selected skill's unlock tree."""
        tree_y = self.panel_y + 130
        tree_x = self.panel_x + 40
        
        skill_id = self.selected_skill
        skill_level = character.skills.get(skill_id, 0)
        color = SKILL_COLORS[skill_id]
        unlocks = SKILL_UNLOCKS[skill_id]
        
        # Title
        title = self.font_large.render(f"{SKILL_NAMES[skill_id]} Abilities", True, color)
        self.screen.blit(title, (tree_x, tree_y))
        
        # Draw unlock nodes
        node_y = tree_y + 50
        node_spacing = 60
        
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
                # Lock icon (simple X)
                pygame.draw.line(self.screen, (100, 100, 100), 
                               (node_x - 5, node_y + 10), (node_x + 5, node_y + 20), 2)
                pygame.draw.line(self.screen, (100, 100, 100),
                               (node_x + 5, node_y + 10), (node_x - 5, node_y + 20), 2)
            
            # Ability info
            text_x = node_x + 30
            
            # Level requirement
            level_color = (100, 255, 100) if unlocked else (255, 100, 100)
            level_text = self.font_small.render(f"Lv.{req_level}", True, level_color)
            self.screen.blit(level_text, (text_x, node_y))
            
            # Ability name
            name_color = COLOR_TEXT if unlocked else COLOR_TEXT_DIM
            name_text = self.font.render(ability_name, True, name_color)
            self.screen.blit(name_text, (text_x + 50, node_y))
            
            # Description
            desc_color = COLOR_TEXT_DIM
            desc_text = self.font_small.render(description, True, desc_color)
            self.screen.blit(desc_text, (text_x + 50, node_y + 22))
            
            # Connecting line to next
            if req_level < unlocks[-1][0]:
                line_color = color if unlocked else (50, 45, 60)
                pygame.draw.line(self.screen, line_color,
                               (node_x, node_y + 30), (node_x, node_y + node_spacing - 15), 2)
            
            node_y += node_spacing

