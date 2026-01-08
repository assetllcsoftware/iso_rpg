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
        # Base font sizes (will be scaled)
        self._base_font_small = 18
        self._base_font_medium = 24
        self._base_font_large = 32
        self._base_font_title = 42
        
        # Current scale factor (1.0 = default)
        self._ui_scale = 1.0
        self._rebuild_fonts()
        
        # Town portal button
        self.portal_button_rect = pygame.Rect(20, 0, 60, 60)  # Y set dynamically
    
    def _rebuild_fonts(self):
        """Rebuild fonts at current scale."""
        self.font_small = pygame.font.Font(None, int(self._base_font_small * self._ui_scale))
        self.font_medium = pygame.font.Font(None, int(self._base_font_medium * self._ui_scale))
        self.font_large = pygame.font.Font(None, int(self._base_font_large * self._ui_scale))
        self.font_title = pygame.font.Font(None, int(self._base_font_title * self._ui_scale))
    
    def set_scale(self, scale: float):
        """Set UI scale factor."""
        if abs(scale - self._ui_scale) > 0.01:  # Only rebuild if changed
            self._ui_scale = scale
            self._rebuild_fonts()
    
    def s(self, value: int) -> int:
        """Scale a value by UI scale factor."""
        return int(value * self._ui_scale)
    
    def render(self, fps: float = 0.0, camera_zoom: float = 1.0):
        """Render the HUD."""
        # Scale UI based on camera zoom - make it big and readable
        target_scale = camera_zoom / 1.0  # 75% of previous
        target_scale = max(1.5, min(3.0, target_scale))
        self.set_scale(target_scale)
        
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
        panel_height = self.s(115) + self.s(5)  # Match _render_party_portraits
        y = self.s(20) + num_members * panel_height + self.s(10)
        
        btn_size = self.s(60)
        self.portal_button_rect = pygame.Rect(self.s(20), y, btn_size, btn_size)
        
        # Check if hovered
        mouse_pos = pygame.mouse.get_pos()
        is_hovered = self.portal_button_rect.collidepoint(mouse_pos)
        
        # Background
        bg_color = (50, 80, 120) if is_hovered else (30, 50, 90)
        pygame.draw.rect(self.screen, bg_color, self.portal_button_rect, border_radius=self.s(8))
        pygame.draw.rect(self.screen, (80, 140, 200), self.portal_button_rect, 2, border_radius=self.s(8))
        
        # Portal swirl effect
        cx, cy = self.portal_button_rect.center
        import math
        import time
        t = time.time() * 2
        
        # Outer ring
        pygame.draw.circle(self.screen, (60, 120, 180), (cx, cy), self.s(22), 2)
        
        # Inner swirl
        for i in range(6):
            angle = t + i * (math.pi / 3)
            r = self.s(12) + math.sin(t * 2 + i) * self.s(4)
            px = cx + math.cos(angle) * r
            py = cy + math.sin(angle) * r
            pygame.draw.circle(self.screen, (100, 180, 255), (int(px), int(py)), self.s(3))
        
        # Center
        pygame.draw.circle(self.screen, (150, 200, 255), (cx, cy), self.s(6))
        
        # Label
        label = self.font_small.render("H", True, (200, 230, 255))
        self.screen.blit(label, (self.portal_button_rect.right - self.s(14), self.portal_button_rect.top + 2))
        
        # "Town" text below
        town_text = self.font_small.render("Town", True, COLOR_TEXT_DIM)
        self.screen.blit(town_text, (self.portal_button_rect.x + self.s(12), self.portal_button_rect.bottom + 2))
    
    def _render_party_portraits(self):
        """Render party member portraits and status."""
        y_offset = self.s(20)
        panel_height = self.s(115)  # Taller to fit XP bars
        panel_width = self.s(200)
        
        for ent, (member, health) in esper.get_components(PartyMember, Health):
            x = self.s(20)
            y = y_offset + member.party_index * (panel_height + self.s(5))
            
            # Background
            bg_color = COLOR_UI_BG if not esper.has_component(ent, Selected) else (45, 42, 55)
            pygame.draw.rect(self.screen, bg_color, (x, y, panel_width, panel_height))
            pygame.draw.rect(self.screen, COLOR_UI_BORDER, (x, y, panel_width, panel_height), 2)
            
            # Selection indicator
            if esper.has_component(ent, Selected):
                pygame.draw.rect(self.screen, COLOR_UI_ACCENT, (x, y, self.s(4), panel_height))
            
            # Name
            name = "Hero"
            if esper.has_component(ent, CharacterName):
                name = esper.component_for_entity(ent, CharacterName).name
            
            name_surf = self.font_medium.render(name, True, COLOR_TEXT)
            self.screen.blit(name_surf, (x + self.s(60), y + self.s(8)))
            
            # Level
            level = 1
            if esper.has_component(ent, CharacterLevel):
                level = esper.component_for_entity(ent, CharacterLevel).level
            
            level_surf = self.font_small.render(f"Lv.{level}", True, COLOR_TEXT_DIM)
            self.screen.blit(level_surf, (x + self.s(160), y + self.s(12)))
            
            # Portrait - use procedural icon (scale it)
            portrait_size = self.s(44)
            portrait = icon_generator.get_character_portrait(name, portrait_size)
            self.screen.blit(portrait, (x + self.s(8), y + self.s(8)))
            
            # Health bar
            bar_x = x + self.s(60)
            bar_y = y + self.s(35)
            bar_w = self.s(130)
            bar_h = self.s(14)
            
            pygame.draw.rect(self.screen, (40, 35, 45), (bar_x, bar_y, bar_w, bar_h))
            health_w = int(bar_w * health.percent)
            pygame.draw.rect(self.screen, COLOR_HEALTH, (bar_x, bar_y, health_w, bar_h))
            pygame.draw.rect(self.screen, COLOR_UI_BORDER, (bar_x, bar_y, bar_w, bar_h), 1)
            
            health_text = f"{health.current}/{health.maximum}"
            health_surf = self.font_small.render(health_text, True, COLOR_TEXT)
            self.screen.blit(health_surf, (bar_x + self.s(5), bar_y + 1))
            
            # Mana bar
            if esper.has_component(ent, Mana):
                mana = esper.component_for_entity(ent, Mana)
                bar_y = y + self.s(52)
                bar_h = self.s(10)
                
                pygame.draw.rect(self.screen, (35, 40, 50), (bar_x, bar_y, bar_w, bar_h))
                mana_w = int(bar_w * mana.percent)
                pygame.draw.rect(self.screen, COLOR_MANA, (bar_x, bar_y, mana_w, bar_h))
                pygame.draw.rect(self.screen, COLOR_UI_BORDER, (bar_x, bar_y, bar_w, bar_h), 1)
            
            # Skill XP bars (compact 2x2 grid)
            self._render_skill_xp_bars(ent, x + self.s(8), y + self.s(68))
    
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
        
        bar_w = self.s(90)
        bar_h = self.s(8)
        
        for i, (skill_name, label, color) in enumerate(skills):
            # 2x2 grid layout
            col = i % 2
            row = i // 2
            bx = x + col * self.s(95)
            by = y + row * self.s(18)
            
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
        """Render spell bars at bottom left - one row per party member (mobile thumb access)."""
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
        
        # Layout constants (scaled)
        slot_size = self.s(44)
        slot_spacing = self.s(6)
        num_slots = 5
        row_height = self.s(56)
        row_spacing = self.s(8)
        
        bar_w = num_slots * (slot_size + slot_spacing) + self.s(80)  # Extra for label
        total_height = len(party_members) * row_height + (len(party_members) - 1) * row_spacing
        
        # Left-aligned for mobile thumb access
        bar_x = self.s(20)
        bar_y = self.screen.get_height() - total_height - self.s(20)
        
        for i, (party_idx, ent, spellbook, name, is_selected) in enumerate(party_members):
            row_y = bar_y + i * (row_height + row_spacing)
            
            # Row background
            bg_color = (40, 38, 50) if is_selected else COLOR_UI_BG
            pygame.draw.rect(self.screen, bg_color, (bar_x, row_y, bar_w, row_height))
            pygame.draw.rect(self.screen, COLOR_UI_BORDER, (bar_x, row_y, bar_w, row_height), 2)
            
            # Selection indicator
            if is_selected:
                pygame.draw.rect(self.screen, COLOR_UI_ACCENT, (bar_x, row_y, self.s(4), row_height))
            
            # Character name label
            name_surf = self.font_small.render(name[:6], True, COLOR_TEXT_DIM)
            self.screen.blit(name_surf, (bar_x + self.s(8), row_y + self.s(4)))
            
            # Get key bindings for this party member
            keys = SPELL_KEYS[party_idx] if party_idx < len(SPELL_KEYS) else ["?"] * 5
            
            # Render 5 spell slots
            slots_start_x = bar_x + self.s(70)
            
            for slot_idx in range(num_slots):
                slot_x = slots_start_x + slot_idx * (slot_size + slot_spacing)
                slot_y = row_y + self.s(6)
                
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
                self.screen.blit(key_surf, (slot_x + self.s(3), slot_y + 2))
                
                # Spell icon (if has spell)
                if has_spell and spell_id:
                    # Generate and draw procedural spell icon
                    icon_size = slot_size - self.s(8)
                    spell_icon = icon_generator.get_spell_icon(spell_id, icon_size)
                    self.screen.blit(spell_icon, (slot_x + self.s(4), slot_y + self.s(4)))
                
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
        map_size = self.s(150)
        x = self.screen.get_width() - map_size - self.s(20)
        y = self.s(20)
        
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
        
        box_w = self.s(150)
        box_h = self.s(35)
        x = self.screen.get_width() - box_w - self.s(20)
        y = self.screen.get_height() - box_h - self.s(15)
        
        pygame.draw.rect(self.screen, COLOR_UI_BG, (x, y, box_w, box_h))
        pygame.draw.rect(self.screen, COLOR_UI_BORDER, (x, y, box_w, box_h), 2)
        
        # Gold icon (circle)
        pygame.draw.circle(self.screen, COLOR_GOLD, (x + self.s(20), y + box_h // 2), self.s(10))
        
        # Amount
        gold_text = f"{total_gold:,}"
        gold_surf = self.font_medium.render(gold_text, True, COLOR_GOLD)
        self.screen.blit(gold_surf, (x + self.s(40), y + self.s(8)))
    
    def _render_fps(self, fps: float):
        """Render FPS counter."""
        from ..core.constants import DEBUG_SHOW_FPS
        
        if not DEBUG_SHOW_FPS and fps == 0:
            return
        
        fps_text = f"FPS: {int(fps)}"
        fps_surf = self.font_small.render(fps_text, True, COLOR_TEXT_DIM)
        self.screen.blit(fps_surf, (self.screen.get_width() - 80, self.screen.get_height() - 25))
