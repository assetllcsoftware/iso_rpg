"""Inventory and character sheet UI."""

import pygame
from ..engine.constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, ALL_SLOTS,
    COLOR_UI_BG, COLOR_UI_BORDER, COLOR_UI_ACCENT,
    COLOR_HEALTH, COLOR_MANA, COLOR_XP, COLOR_TEXT, COLOR_TEXT_DIM,
    RARITY_COLORS, SKILL_MELEE, SKILL_RANGED, SKILL_COMBAT_MAGIC, SKILL_NATURE_MAGIC
)


class InventoryUI:
    """Full-screen inventory and character sheet."""
    
    def __init__(self, screen):
        self.screen = screen
        self.visible = False
        self.selected_item = None
        self.dragging_item = None
        self.drag_source = None  # 'inventory' or slot name
        self.hover_item = None
        
        # Party switching
        self.party = None
        self.party_index = 0
        self.viewing_character = None
        
        # Fonts
        pygame.font.init()
        self.font = pygame.font.Font(None, 24)
        self.font_large = pygame.font.Font(None, 32)
        self.font_small = pygame.font.Font(None, 18)
        self.font_title = pygame.font.Font(None, 40)
        
        # Layout
        self.panel_width = 320
        self.panel_height = 500
        self.slot_size = 48
        self.padding = 12
        
        # Panel positions
        self.left_panel = pygame.Rect(
            50, (SCREEN_HEIGHT - self.panel_height) // 2,
            self.panel_width, self.panel_height
        )
        self.right_panel = pygame.Rect(
            SCREEN_WIDTH - self.panel_width - 50,
            (SCREEN_HEIGHT - self.panel_height) // 2,
            self.panel_width, self.panel_height
        )
        
        # Equipment slot positions (on character silhouette)
        self.equip_slots = self._setup_equip_slots()
        
        # Inventory grid
        self.inv_cols = 5
        self.inv_rows = 6
        self.inv_slots = []
        self._setup_inv_slots()
    
    def _setup_equip_slots(self):
        """Setup equipment slot positions."""
        cx = self.left_panel.x + self.panel_width // 2
        cy = self.left_panel.y + 180
        
        slots = {
            'head': pygame.Rect(cx - 24, cy - 80, self.slot_size, self.slot_size),
            'amulet': pygame.Rect(cx + 35, cy - 50, self.slot_size, self.slot_size),
            'chest': pygame.Rect(cx - 24, cy - 20, self.slot_size, self.slot_size),
            'main_hand': pygame.Rect(cx - 85, cy - 10, self.slot_size, self.slot_size),
            'off_hand': pygame.Rect(cx + 35, cy - 10, self.slot_size, self.slot_size),
            'hands': pygame.Rect(cx - 85, cy + 45, self.slot_size, self.slot_size),
            'ring_1': pygame.Rect(cx - 85, cy + 100, self.slot_size, self.slot_size),
            'ring_2': pygame.Rect(cx + 35, cy + 100, self.slot_size, self.slot_size),
            'legs': pygame.Rect(cx - 24, cy + 45, self.slot_size, self.slot_size),
            'feet': pygame.Rect(cx - 24, cy + 100, self.slot_size, self.slot_size),
        }
        return slots
    
    def _setup_inv_slots(self):
        """Setup inventory grid slots."""
        start_x = self.right_panel.x + self.padding
        start_y = self.right_panel.y + 100
        
        self.inv_slots = []
        for row in range(self.inv_rows):
            for col in range(self.inv_cols):
                x = start_x + col * (self.slot_size + 4)
                y = start_y + row * (self.slot_size + 4)
                self.inv_slots.append(pygame.Rect(x, y, self.slot_size, self.slot_size))
    
    def toggle(self):
        """Toggle inventory visibility."""
        self.visible = not self.visible
        self.selected_item = None
        self.dragging_item = None
    
    def handle_event(self, event, character, action_bar=None):
        """Handle input events."""
        if not self.visible:
            return False
        
        # Use viewing_character if set, otherwise the passed character
        char = self.viewing_character or character
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_TAB and self.party:
                # Cycle through party members
                self.party_index = (self.party_index + 1) % len(self.party)
                self.viewing_character = self.party[self.party_index]
                return True
            elif event.key == pygame.K_ESCAPE:
                self.visible = False
                return True
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                # Check party tab clicks first
                if self.party and self._handle_party_tab_click(event.pos):
                    return True
                return self._handle_click(event.pos, char)
            elif event.button == 3 and action_bar:
                # Right-click to assign to action bar
                return self._handle_right_click(event.pos, char, action_bar)
        
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and self.dragging_item:
                return self._handle_drop(event.pos, char)
        
        elif event.type == pygame.MOUSEMOTION:
            self._update_hover(event.pos, char)
            if self.dragging_item:
                return True
        
        return False
    
    def _handle_party_tab_click(self, pos):
        """Check if clicking on party member tabs."""
        if not self.party:
            return False
        
        tab_y = 20
        for i, member in enumerate(self.party):
            tab_rect = pygame.Rect(60 + i * 110, tab_y, 100, 30)
            if tab_rect.collidepoint(pos):
                self.party_index = i
                self.viewing_character = member
                return True
        return False
    
    def set_party(self, party, current_index=0):
        """Set the party reference for switching between members."""
        self.party = party
        self.party_index = current_index
        if party and len(party) > current_index:
            self.viewing_character = party[current_index]
    
    def _handle_right_click(self, pos, character, action_bar):
        """Handle right-click to assign item to action bar."""
        # Check inventory slots
        for i, rect in enumerate(self.inv_slots):
            if rect.collidepoint(pos) and i < len(character.inventory):
                item = character.inventory[i]
                if item and hasattr(item, 'effect_type'):
                    # Find first empty slot or last slot
                    for slot_idx in range(action_bar.NUM_SLOTS):
                        if action_bar.slots[slot_idx] is None:
                            action_bar.assign_item(slot_idx, item.effect_type, item.name)
                            return True
                    # No empty slot, use slot 7 (last)
                    action_bar.assign_item(7, item.effect_type, item.name)
                    return True
        return False
    
    def _handle_click(self, pos, character):
        """Handle click on inventory."""
        # Check equipment slots
        for slot_name, rect in self.equip_slots.items():
            if rect.collidepoint(pos):
                item = character.equipment.get(slot_name)
                if item:
                    self.dragging_item = item
                    self.drag_source = slot_name
                return True
        
        # Check inventory slots
        for i, rect in enumerate(self.inv_slots):
            if rect.collidepoint(pos):
                if i < len(character.inventory):
                    self.dragging_item = character.inventory[i]
                    self.drag_source = ('inventory', i)
                return True
        
        return False
    
    def _handle_drop(self, pos, character):
        """Handle dropping an item."""
        if not self.dragging_item:
            return False
        
        item = self.dragging_item
        source = self.drag_source
        
        # Check if dropping on equipment slot
        for slot_name, rect in self.equip_slots.items():
            if rect.collidepoint(pos):
                if hasattr(item, 'slot') and item.slot == slot_name:
                    # Valid equip
                    self._do_equip(character, item, slot_name, source)
                    break
        
        # Check if dropping on inventory
        for i, rect in enumerate(self.inv_slots):
            if rect.collidepoint(pos):
                self._do_inventory_swap(character, item, i, source)
                break
        
        self.dragging_item = None
        self.drag_source = None
        return True
    
    def _do_equip(self, character, item, slot_name, source):
        """Equip an item."""
        # Remove from source
        if isinstance(source, tuple) and source[0] == 'inventory':
            character.inventory.remove(item)
        elif source in self.equip_slots:
            character.equipment[source] = None
        
        # Swap with existing
        old_item = character.equipment.get(slot_name)
        if old_item:
            character.inventory.append(old_item)
        
        character.equipment[slot_name] = item
    
    def _do_inventory_swap(self, character, item, target_idx, source):
        """Move item to inventory slot."""
        # Remove from source
        if isinstance(source, tuple) and source[0] == 'inventory':
            source_idx = source[1]
            character.inventory[source_idx] = None
        elif source in self.equip_slots:
            character.equipment[source] = None
        
        # Add to inventory
        while len(character.inventory) <= target_idx:
            character.inventory.append(None)
        
        # Swap if something there
        existing = character.inventory[target_idx] if target_idx < len(character.inventory) else None
        character.inventory[target_idx] = item
        
        if existing and isinstance(source, tuple):
            character.inventory[source[1]] = existing
        elif existing and source in self.equip_slots:
            if hasattr(existing, 'slot') and existing.slot == source:
                character.equipment[source] = existing
            else:
                character.inventory.append(existing)
        
        # Clean up None entries at end
        while character.inventory and character.inventory[-1] is None:
            character.inventory.pop()
    
    def _update_hover(self, pos, character):
        """Update hovered item for tooltip."""
        self.hover_item = None
        
        for slot_name, rect in self.equip_slots.items():
            if rect.collidepoint(pos):
                self.hover_item = character.equipment.get(slot_name)
                return
        
        for i, rect in enumerate(self.inv_slots):
            if rect.collidepoint(pos) and i < len(character.inventory):
                self.hover_item = character.inventory[i]
                return
    
    def render(self, character):
        """Render inventory UI."""
        if not self.visible:
            return
        
        # Use viewing_character if set
        char = self.viewing_character or character
        
        # Darken background
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        
        # Party tabs at top
        if self.party and len(self.party) > 1:
            self._render_party_tabs()
        
        # Left panel - Character sheet
        self._render_character_panel(char)
        
        # Right panel - Inventory
        self._render_inventory_panel(char)
        
        # Tooltip
        if self.hover_item and not self.dragging_item:
            self._render_tooltip(self.hover_item, pygame.mouse.get_pos())
        
        # Dragging item
        if self.dragging_item:
            self._render_dragged_item(self.dragging_item, pygame.mouse.get_pos())
    
    def _render_party_tabs(self):
        """Render party member tabs at the top."""
        tab_y = 20
        
        for i, member in enumerate(self.party):
            tab_rect = pygame.Rect(60 + i * 110, tab_y, 100, 30)
            
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
        
        # TAB hint
        hint = self.font_small.render("TAB to switch", True, COLOR_TEXT_DIM)
        self.screen.blit(hint, (60 + len(self.party) * 110 + 15, tab_y + 8))
    
    def _render_character_panel(self, char):
        """Render character stats and equipment."""
        panel = self.left_panel
        
        # Background
        pygame.draw.rect(self.screen, COLOR_UI_BG, panel)
        pygame.draw.rect(self.screen, COLOR_UI_BORDER, panel, 2)
        
        # Title
        title = self.font_title.render(char.name, True, COLOR_UI_ACCENT)
        self.screen.blit(title, (panel.x + self.padding, panel.y + self.padding))
        
        # Class and level
        class_text = self.font.render(
            f"Level {char.level} {char.character_class}", True, COLOR_TEXT
        )
        self.screen.blit(class_text, (panel.x + self.padding, panel.y + 50))
        
        # Equipment slots
        for slot_name, rect in self.equip_slots.items():
            self._render_slot(rect, char.equipment.get(slot_name), slot_name)
        
        # Stats section
        stats_y = panel.y + 320
        self._render_stats(char, panel.x + self.padding, stats_y)
        
        # Skills section
        skills_y = stats_y + 80
        self._render_skills(char, panel.x + self.padding, skills_y)
    
    def _render_inventory_panel(self, char):
        """Render inventory grid."""
        panel = self.right_panel
        
        # Background
        pygame.draw.rect(self.screen, COLOR_UI_BG, panel)
        pygame.draw.rect(self.screen, COLOR_UI_BORDER, panel, 2)
        
        # Title
        title = self.font_title.render("Inventory", True, COLOR_UI_ACCENT)
        self.screen.blit(title, (panel.x + self.padding, panel.y + self.padding))
        
        # Weight
        weight_text = self.font_small.render(
            f"Weight: {char.current_weight:.1f} / {char.max_weight}", True, COLOR_TEXT_DIM
        )
        self.screen.blit(weight_text, (panel.x + self.padding, panel.y + 50))
        
        # Gold
        gold_text = self.font.render(f"Gold: {char.gold}", True, (220, 180, 60))
        self.screen.blit(gold_text, (panel.x + self.padding, panel.y + 70))
        
        # Inventory slots
        for i, rect in enumerate(self.inv_slots):
            item = char.inventory[i] if i < len(char.inventory) else None
            self._render_slot(rect, item)
    
    def _render_slot(self, rect, item, slot_name=None):
        """Render an inventory/equipment slot."""
        from .icons import get_item_icon_surface
        
        # Background
        pygame.draw.rect(self.screen, (35, 30, 45), rect)
        pygame.draw.rect(self.screen, COLOR_UI_BORDER, rect, 1)
        
        if item:
            # Item background with rarity color
            rarity_color = RARITY_COLORS.get(item.rarity, (100, 100, 100))
            inner = rect.inflate(-4, -4)
            pygame.draw.rect(self.screen, (*rarity_color, 100), inner)
            
            # Draw item icon
            icon_size = min(rect.width - 8, rect.height - 8)
            icon_surf = get_item_icon_surface(item, icon_size)
            icon_rect = icon_surf.get_rect(center=rect.center)
            self.screen.blit(icon_surf, icon_rect)
            
            # Rarity border
            pygame.draw.rect(self.screen, rarity_color, inner, 2)
        elif slot_name:
            # Empty slot label
            label = slot_name.replace('_', '\n').split('\n')[0][:4]
            label_text = self.font_small.render(label, True, COLOR_TEXT_DIM)
            label_rect = label_text.get_rect(center=rect.center)
            self.screen.blit(label_text, label_rect)
    
    def _render_stats(self, char, x, y):
        """Render character stats."""
        stats = [
            ("STR", char.strength, (200, 100, 100)),
            ("DEX", char.dexterity, (100, 200, 100)),
            ("INT", char.intelligence, (100, 100, 200)),
        ]
        
        for i, (name, value, color) in enumerate(stats):
            stat_x = x + i * 90
            
            # Label
            label = self.font_small.render(name, True, color)
            self.screen.blit(label, (stat_x, y))
            
            # Value
            val_text = self.font_large.render(str(value), True, COLOR_TEXT)
            self.screen.blit(val_text, (stat_x, y + 15))
        
        # Secondary stats
        y += 50
        secondary = [
            f"HP: {int(char.health)}/{char.max_health}",
            f"MP: {int(char.mana)}/{char.max_mana}",
            f"Armor: {char.armor}",
            f"Damage: {char.damage}",
        ]
        
        for i, text in enumerate(secondary):
            col = i % 2
            row = i // 2
            stat_text = self.font_small.render(text, True, COLOR_TEXT_DIM)
            self.screen.blit(stat_text, (x + col * 130, y + row * 18))
    
    def _render_skills(self, char, x, y):
        """Render skill levels and XP bars."""
        skills = [
            (SKILL_MELEE, "Melee", (200, 100, 100)),
            (SKILL_RANGED, "Ranged", (100, 200, 100)),
            (SKILL_COMBAT_MAGIC, "Combat Magic", (200, 100, 200)),
            (SKILL_NATURE_MAGIC, "Nature Magic", (100, 200, 150)),
        ]
        
        for i, (skill_id, name, color) in enumerate(skills):
            skill_y = y + i * 22
            level = char.skills.get(skill_id, 0)
            xp = char.skill_xp.get(skill_id, 0)
            xp_needed = (level + 1) * 100
            
            # Skill name and level
            text = self.font_small.render(f"{name}: {level}", True, color)
            self.screen.blit(text, (x, skill_y))
            
            # XP bar
            bar_x = x + 120
            bar_width = 80
            bar_height = 8
            
            pygame.draw.rect(self.screen, (30, 25, 35), 
                           (bar_x, skill_y + 4, bar_width, bar_height))
            
            fill_width = int(bar_width * (xp / xp_needed))
            pygame.draw.rect(self.screen, color,
                           (bar_x, skill_y + 4, fill_width, bar_height))
    
    def _render_tooltip(self, item, pos):
        """Render item tooltip."""
        lines = [item.name]
        
        if hasattr(item, 'damage') and item.damage > 0:
            lines.append(f"Damage: {item.damage}")
        if hasattr(item, 'armor') and item.armor > 0:
            lines.append(f"Armor: {item.armor}")
        if hasattr(item, 'effect_type'):
            lines.append(f"Effect: {item.effect_type} +{item.effect_value}")
        
        # Bonus stats
        bonuses = []
        if hasattr(item, 'strength_bonus') and item.strength_bonus:
            bonuses.append(f"+{item.strength_bonus} STR")
        if hasattr(item, 'dexterity_bonus') and item.dexterity_bonus:
            bonuses.append(f"+{item.dexterity_bonus} DEX")
        if hasattr(item, 'intelligence_bonus') and item.intelligence_bonus:
            bonuses.append(f"+{item.intelligence_bonus} INT")
        if bonuses:
            lines.append(" ".join(bonuses))
        
        lines.append(f"Weight: {item.weight}")
        lines.append(f"Value: {item.value} gold")
        
        # Calculate size
        width = max(self.font_small.size(line)[0] for line in lines) + 20
        height = len(lines) * 18 + 10
        
        # Position
        x = min(pos[0] + 15, SCREEN_WIDTH - width - 10)
        y = min(pos[1] + 15, SCREEN_HEIGHT - height - 10)
        
        # Background
        tooltip_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(self.screen, (20, 18, 25), tooltip_rect)
        pygame.draw.rect(self.screen, RARITY_COLORS.get(item.rarity, COLOR_UI_BORDER), 
                        tooltip_rect, 1)
        
        # Text
        for i, line in enumerate(lines):
            color = RARITY_COLORS.get(item.rarity, COLOR_TEXT) if i == 0 else COLOR_TEXT_DIM
            text = self.font_small.render(line, True, color)
            self.screen.blit(text, (x + 10, y + 5 + i * 18))
    
    def _render_dragged_item(self, item, pos):
        """Render item being dragged."""
        rect = pygame.Rect(pos[0] - 24, pos[1] - 24, self.slot_size, self.slot_size)
        rarity_color = RARITY_COLORS.get(item.rarity, (100, 100, 100))
        
        # Semi-transparent background
        surf = pygame.Surface((self.slot_size, self.slot_size), pygame.SRCALPHA)
        pygame.draw.rect(surf, (*rarity_color, 200), surf.get_rect())
        self.screen.blit(surf, rect)
        
        # Item letter
        icon_text = self.font.render(item.name[0].upper(), True, (255, 255, 255))
        icon_rect = icon_text.get_rect(center=rect.center)
        self.screen.blit(icon_text, icon_rect)

