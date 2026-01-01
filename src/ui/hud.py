"""HUD (Heads-Up Display) rendering."""

import pygame
import esper
from typing import Optional, List, Tuple

from ..core.constants import (
    COLOR_UI_BG, COLOR_UI_BORDER, COLOR_UI_ACCENT,
    COLOR_HEALTH, COLOR_MANA, COLOR_XP, COLOR_GOLD,
    COLOR_TEXT, COLOR_TEXT_DIM
)
from ..core.events import EventBus, Event, EventType
from ..core.formulas import xp_for_skill_level
from ..ecs.components import (
    Health, Mana, Gold, CharacterName, CharacterLevel,
    SkillLevels, SkillXP, SpellBook, Equipment, Inventory,
    PartyMember, PlayerControlled, Selected
)
from .icons import icon_generator


# Spell key bindings per party member
SPELL_KEYS = [
    ["Q", "W", "E", "R", "T"],  # Hero (party_index 0)
    ["A", "S", "D", "F", "G"],  # Lyra (party_index 1)
    ["Z", "X", "C", "V", "B"],  # Third member (party_index 2)
]


class HUD:
    """In-game HUD rendering."""
    
    def __init__(self, screen: pygame.Surface, event_bus: EventBus = None):
        self.screen = screen
        self.event_bus = event_bus
        
        pygame.font.init()
        self.font_small = pygame.font.Font(None, 18)
        self.font_medium = pygame.font.Font(None, 24)
        self.font_large = pygame.font.Font(None, 32)
        self.font_title = pygame.font.Font(None, 42)
        
        # Town portal button
        self.portal_button_rect = pygame.Rect(20, 0, 60, 60)  # Y set dynamically
    
    def render(self, fps: float = 0.0):
        """Render the HUD."""
        # Party portraits (top left)
        self._render_party_portraits()
        
        # Town portal button (below portraits)
        self._render_town_portal_button()
        
        # Spell bars (bottom center) - one row per party member
        self._render_spell_bars()
        
        # Minimap (top right) - placeholder
        self._render_minimap_placeholder()
        
        # Gold (bottom right)
        self._render_gold()
        
        # FPS counter (debug)
        self._render_fps(fps)
    
    def handle_click(self, pos: Tuple[int, int]) -> bool:
        """Handle mouse click. Returns True if handled."""
        if self.portal_button_rect.collidepoint(pos):
            if self.event_bus:
                self.event_bus.emit(Event(EventType.NOTIFICATION, {
                    "text": "Town Portal!",
                    "color": (100, 200, 255)
                }))
                self.event_bus.emit(Event(EventType.TOWN_ENTERED, {"from_level": 1}))
            return True
        return False
    
    def _render_town_portal_button(self):
        """Render the town portal button."""
        # Position below party portraits (after up to 3 members)
        num_members = sum(1 for _ in esper.get_components(PartyMember, Health))
        panel_height = 115 + 5  # Match _render_party_portraits
        y = 20 + num_members * panel_height + 10
        
        self.portal_button_rect = pygame.Rect(20, y, 60, 60)
        
        # Check if hovered
        mouse_pos = pygame.mouse.get_pos()
        is_hovered = self.portal_button_rect.collidepoint(mouse_pos)
        
        # Background
        bg_color = (50, 80, 120) if is_hovered else (30, 50, 90)
        pygame.draw.rect(self.screen, bg_color, self.portal_button_rect, border_radius=8)
        pygame.draw.rect(self.screen, (80, 140, 200), self.portal_button_rect, 2, border_radius=8)
        
        # Portal swirl effect
        cx, cy = self.portal_button_rect.center
        import math
        import time
        t = time.time() * 2
        
        # Outer ring
        pygame.draw.circle(self.screen, (60, 120, 180), (cx, cy), 22, 2)
        
        # Inner swirl
        for i in range(6):
            angle = t + i * (math.pi / 3)
            r = 12 + math.sin(t * 2 + i) * 4
            px = cx + math.cos(angle) * r
            py = cy + math.sin(angle) * r
            pygame.draw.circle(self.screen, (100, 180, 255), (int(px), int(py)), 3)
        
        # Center
        pygame.draw.circle(self.screen, (150, 200, 255), (cx, cy), 6)
        
        # Label
        label = self.font_small.render("H", True, (200, 230, 255))
        self.screen.blit(label, (self.portal_button_rect.right - 14, self.portal_button_rect.top + 2))
        
        # "Town" text below
        town_text = self.font_small.render("Town", True, COLOR_TEXT_DIM)
        self.screen.blit(town_text, (self.portal_button_rect.x + 12, self.portal_button_rect.bottom + 2))
    
    def _render_party_portraits(self):
        """Render party member portraits and status."""
        y_offset = 20
        panel_height = 115  # Taller to fit XP bars
        
        for ent, (member, health) in esper.get_components(PartyMember, Health):
            x = 20
            y = y_offset + member.party_index * (panel_height + 5)
            
            # Background
            bg_color = COLOR_UI_BG if not esper.has_component(ent, Selected) else (45, 42, 55)
            pygame.draw.rect(self.screen, bg_color, (x, y, 200, panel_height))
            pygame.draw.rect(self.screen, COLOR_UI_BORDER, (x, y, 200, panel_height), 2)
            
            # Selection indicator
            if esper.has_component(ent, Selected):
                pygame.draw.rect(self.screen, COLOR_UI_ACCENT, (x, y, 4, panel_height))
            
            # Name
            name = "Hero"
            if esper.has_component(ent, CharacterName):
                name = esper.component_for_entity(ent, CharacterName).name
            
            name_surf = self.font_medium.render(name, True, COLOR_TEXT)
            self.screen.blit(name_surf, (x + 60, y + 8))
            
            # Level
            level = 1
            if esper.has_component(ent, CharacterLevel):
                level = esper.component_for_entity(ent, CharacterLevel).level
            
            level_surf = self.font_small.render(f"Lv.{level}", True, COLOR_TEXT_DIM)
            self.screen.blit(level_surf, (x + 160, y + 12))
            
            # Portrait - use procedural icon
            portrait = icon_generator.get_character_portrait(name, 44)
            self.screen.blit(portrait, (x + 8, y + 8))
            
            # Health bar
            bar_x = x + 60
            bar_y = y + 35
            bar_w = 130
            bar_h = 14
            
            pygame.draw.rect(self.screen, (40, 35, 45), (bar_x, bar_y, bar_w, bar_h))
            health_w = int(bar_w * health.percent)
            pygame.draw.rect(self.screen, COLOR_HEALTH, (bar_x, bar_y, health_w, bar_h))
            pygame.draw.rect(self.screen, COLOR_UI_BORDER, (bar_x, bar_y, bar_w, bar_h), 1)
            
            health_text = f"{health.current}/{health.maximum}"
            health_surf = self.font_small.render(health_text, True, COLOR_TEXT)
            self.screen.blit(health_surf, (bar_x + 5, bar_y + 1))
            
            # Mana bar
            if esper.has_component(ent, Mana):
                mana = esper.component_for_entity(ent, Mana)
                bar_y = y + 52
                bar_h = 10
                
                pygame.draw.rect(self.screen, (35, 40, 50), (bar_x, bar_y, bar_w, bar_h))
                mana_w = int(bar_w * mana.percent)
                pygame.draw.rect(self.screen, COLOR_MANA, (bar_x, bar_y, mana_w, bar_h))
                pygame.draw.rect(self.screen, COLOR_UI_BORDER, (bar_x, bar_y, bar_w, bar_h), 1)
            
            # Skill XP bars (compact 2x2 grid)
            self._render_skill_xp_bars(ent, x + 8, y + 68)
    
    def _render_skill_xp_bars(self, ent: int, x: int, y: int):
        """Render compact skill XP bars for a character."""
        # Get skill levels and XP
        skill_levels = None
        skill_xp = None
        if esper.has_component(ent, SkillLevels):
            skill_levels = esper.component_for_entity(ent, SkillLevels)
        if esper.has_component(ent, SkillXP):
            skill_xp = esper.component_for_entity(ent, SkillXP)
        
        if not skill_levels or not skill_xp:
            return
        
        # Skill colors and names (compact labels)
        skills = [
            ("melee", "M", (200, 80, 80)),     # Red
            ("ranged", "R", (80, 180, 80)),    # Green  
            ("combat_magic", "C", (100, 100, 220)),  # Blue
            ("nature_magic", "N", (80, 200, 180)),   # Teal
        ]
        
        bar_w = 90
        bar_h = 8
        
        for i, (skill_name, label, color) in enumerate(skills):
            # 2x2 grid layout
            col = i % 2
            row = i // 2
            bx = x + col * 95
            by = y + row * 18
            
            level = skill_levels.get(skill_name)
            xp = skill_xp.get(skill_name)
            xp_needed = xp_for_skill_level(level)
            progress = min(1.0, xp / xp_needed) if xp_needed > 0 else 0
            
            # Background
            pygame.draw.rect(self.screen, (30, 30, 35), (bx, by, bar_w, bar_h))
            
            # Progress fill
            fill_w = int(bar_w * progress)
            pygame.draw.rect(self.screen, color, (bx, by, fill_w, bar_h))
            
            # Border
            pygame.draw.rect(self.screen, (60, 60, 70), (bx, by, bar_w, bar_h), 1)
            
            # Label and level
            label_text = f"{label}:{level}"
            label_surf = self.font_small.render(label_text, True, COLOR_TEXT)
            self.screen.blit(label_surf, (bx + 2, by - 1))
    
    def _render_spell_bars(self):
        """Render spell bars at bottom center - one row per party member."""
        # Collect party members sorted by index
        party_members: List[Tuple[int, int, Optional[object]]] = []  # (party_index, entity, spellbook)
        
        for ent, (member,) in esper.get_components(PartyMember):
            spellbook = None
            if esper.has_component(ent, SpellBook):
                spellbook = esper.component_for_entity(ent, SpellBook)
            
            name = "???"
            if esper.has_component(ent, CharacterName):
                name = esper.component_for_entity(ent, CharacterName).name
            
            is_selected = esper.has_component(ent, Selected)
            party_members.append((member.party_index, ent, spellbook, name, is_selected))
        
        # Sort by party index
        party_members.sort(key=lambda x: x[0])
        
        # Layout constants
        slot_size = 44
        slot_spacing = 6
        num_slots = 5
        row_height = 56
        row_spacing = 8
        
        bar_w = num_slots * (slot_size + slot_spacing) + 80  # Extra for label
        total_height = len(party_members) * row_height + (len(party_members) - 1) * row_spacing
        
        bar_x = (self.screen.get_width() - bar_w) // 2
        bar_y = self.screen.get_height() - total_height - 20
        
        for i, (party_idx, ent, spellbook, name, is_selected) in enumerate(party_members):
            row_y = bar_y + i * (row_height + row_spacing)
            
            # Row background
            bg_color = (40, 38, 50) if is_selected else COLOR_UI_BG
            pygame.draw.rect(self.screen, bg_color, (bar_x, row_y, bar_w, row_height))
            pygame.draw.rect(self.screen, COLOR_UI_BORDER, (bar_x, row_y, bar_w, row_height), 2)
            
            # Selection indicator
            if is_selected:
                pygame.draw.rect(self.screen, COLOR_UI_ACCENT, (bar_x, row_y, 4, row_height))
            
            # Character name label
            name_surf = self.font_small.render(name[:6], True, COLOR_TEXT_DIM)
            self.screen.blit(name_surf, (bar_x + 8, row_y + 4))
            
            # Get key bindings for this party member
            keys = SPELL_KEYS[party_idx] if party_idx < len(SPELL_KEYS) else ["?"] * 5
            
            # Render 5 spell slots
            slots_start_x = bar_x + 70
            
            for slot_idx in range(num_slots):
                slot_x = slots_start_x + slot_idx * (slot_size + slot_spacing)
                slot_y = row_y + 6
                
                # Slot background
                has_spell = False
                spell_id = None
                cooldown = 0.0
                
                if spellbook:
                    spells = list(spellbook.known_spells)
                    if slot_idx < len(spells):
                        has_spell = True
                        spell_id = spells[slot_idx]
                        cooldown = spellbook.cooldowns.get(spell_id, 0.0)
                
                slot_color = (55, 50, 65) if has_spell else (40, 35, 45)
                pygame.draw.rect(self.screen, slot_color, (slot_x, slot_y, slot_size, slot_size))
                pygame.draw.rect(self.screen, COLOR_UI_BORDER, (slot_x, slot_y, slot_size, slot_size), 1)
                
                # Hotkey label (top-left corner)
                key_label = keys[slot_idx] if slot_idx < len(keys) else "?"
                key_color = COLOR_UI_ACCENT if is_selected else COLOR_TEXT_DIM
                key_surf = self.font_small.render(key_label, True, key_color)
                self.screen.blit(key_surf, (slot_x + 3, slot_y + 2))
                
                # Spell icon (if has spell)
                if has_spell and spell_id:
                    # Generate and draw procedural spell icon
                    icon_size = slot_size - 8
                    spell_icon = icon_generator.get_spell_icon(spell_id, icon_size)
                    self.screen.blit(spell_icon, (slot_x + 4, slot_y + 4))
                
                # Cooldown overlay
                if cooldown > 0:
                    # Dark overlay
                    dark_surf = pygame.Surface((slot_size, slot_size))
                    dark_surf.fill((20, 20, 20))
                    dark_surf.set_alpha(180)
                    self.screen.blit(dark_surf, (slot_x, slot_y))
                    
                    # Cooldown text
                    cd_text = f"{cooldown:.1f}"
                    cd_surf = self.font_medium.render(cd_text, True, COLOR_TEXT)
                    self.screen.blit(
                        cd_surf,
                        (slot_x + slot_size // 2 - cd_surf.get_width() // 2,
                         slot_y + slot_size // 2 - cd_surf.get_height() // 2)
                    )
    
    def _render_minimap_placeholder(self):
        """Render minimap placeholder."""
        map_size = 150
        x = self.screen.get_width() - map_size - 20
        y = 20
        
        pygame.draw.rect(self.screen, COLOR_UI_BG, (x, y, map_size, map_size))
        pygame.draw.rect(self.screen, COLOR_UI_BORDER, (x, y, map_size, map_size), 2)
        
        # "MINIMAP" text
        text_surf = self.font_small.render("MINIMAP", True, COLOR_TEXT_DIM)
        self.screen.blit(
            text_surf,
            (x + map_size // 2 - text_surf.get_width() // 2,
             y + map_size // 2 - text_surf.get_height() // 2)
        )
    
    def _render_gold(self):
        """Render gold amount."""
        # Find player's gold (from party leader)
        total_gold = 0
        for ent, (member, gold) in esper.get_components(PartyMember, Gold):
            if member.party_index == 0:
                total_gold = gold.amount
                break
        
        x = self.screen.get_width() - 170
        y = self.screen.get_height() - 50
        
        pygame.draw.rect(self.screen, COLOR_UI_BG, (x, y, 150, 35))
        pygame.draw.rect(self.screen, COLOR_UI_BORDER, (x, y, 150, 35), 2)
        
        # Gold icon (circle)
        pygame.draw.circle(self.screen, COLOR_GOLD, (x + 20, y + 17), 10)
        
        # Amount
        gold_text = f"{total_gold:,}"
        gold_surf = self.font_medium.render(gold_text, True, COLOR_GOLD)
        self.screen.blit(gold_surf, (x + 40, y + 8))
    
    def _render_fps(self, fps: float):
        """Render FPS counter."""
        from ..core.constants import DEBUG_SHOW_FPS
        
        if not DEBUG_SHOW_FPS and fps == 0:
            return
        
        fps_text = f"FPS: {int(fps)}"
        fps_surf = self.font_small.render(fps_text, True, COLOR_TEXT_DIM)
        self.screen.blit(fps_surf, (self.screen.get_width() - 80, self.screen.get_height() - 25))
