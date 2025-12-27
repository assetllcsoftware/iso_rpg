"""Inventory and character sheet UI."""

import pygame
import esper
from typing import Optional, List, Dict, Tuple

from ..core.constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    COLOR_UI_BG, COLOR_UI_BORDER, COLOR_UI_ACCENT,
    COLOR_HEALTH, COLOR_MANA, COLOR_XP, COLOR_TEXT, COLOR_TEXT_DIM, COLOR_GOLD,
    RARITY_COLORS, RARITY_NAMES
)
from ..ecs.components import (
    Health, Mana, Attributes, SkillLevels, SkillXP, CharacterLevel,
    CharacterName, Equipment, Inventory as InventoryComp, PartyMember
)


class InventoryUI:
    """Full-screen inventory and character sheet."""
    
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.visible = False
        self.selected_entity: int = -1
        self.selected_item_idx: int = -1
        self.hover_item_idx: int = -1
        self.hover_equip_slot: Optional[str] = None
        self.dragging_item = None
        self.drag_source = None
        
        # Party tab for switching characters
        self.party_entities: List[int] = []
        self.party_index: int = 0
        
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
        
        # Equipment slot positions
        self.equip_slots = self._setup_equip_slots()
        
        # Inventory grid
        self.inv_cols = 5
        self.inv_rows = 6
        self.inv_slots: List[pygame.Rect] = []
        self._setup_inv_slots()
    
    def _setup_equip_slots(self) -> Dict[str, pygame.Rect]:
        """Setup equipment slot positions on character silhouette."""
        cx = self.left_panel.x + self.panel_width // 2
        cy = self.left_panel.y + 180
        
        return {
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
        if self.visible:
            self._refresh_party()
    
    def show(self, entity: int):
        """Show inventory for specific entity."""
        self.visible = True
        self.selected_entity = entity
        self._refresh_party()
    
    def hide(self):
        """Hide inventory."""
        self.visible = False
        self.dragging_item = None
    
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
        """Handle input events. Returns True if handled."""
        if not self.visible:
            return False
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE or event.key == pygame.K_i:
                self.hide()
                return True
            elif event.key == pygame.K_TAB:
                self._cycle_party_member()
                return True
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                return self._handle_click(event.pos)
        
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and self.dragging_item:
                return self._handle_drop(event.pos)
        
        elif event.type == pygame.MOUSEMOTION:
            self._update_hover(event.pos)
            return self.dragging_item is not None
        
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
            tab_rect = pygame.Rect(60 + i * 110, 20, 100, 30)
            if tab_rect.collidepoint(pos):
                self.selected_entity = ent
                return True
        
        # Check inventory slots - start drag
        for i, rect in enumerate(self.inv_slots):
            if rect.collidepoint(pos):
                if esper.has_component(self.selected_entity, InventoryComp):
                    inv = esper.component_for_entity(self.selected_entity, InventoryComp)
                    if i < len(inv.items):
                        self.dragging_item = inv.items[i]
                        self.drag_source = ('inventory', i)
                return True
        
        # Check equipment slots
        for slot_name, rect in self.equip_slots.items():
            if rect.collidepoint(pos):
                if esper.has_component(self.selected_entity, Equipment):
                    equip = esper.component_for_entity(self.selected_entity, Equipment)
                    item = equip.get(slot_name)
                    if item:
                        self.dragging_item = item
                        self.drag_source = ('equipment', slot_name)
                return True
        
        return False
    
    def _handle_drop(self, pos: Tuple[int, int]) -> bool:
        """Handle item drop."""
        from ..data.loader import data_loader
        
        if not self.dragging_item or not self.drag_source:
            return False
        
        ent = self.selected_entity
        if ent < 0:
            self.dragging_item = None
            self.drag_source = None
            return False
        
        source_type, source_idx = self.drag_source
        
        # Get inventory and equipment
        inv = None
        equip = None
        if esper.has_component(ent, InventoryComp):
            inv = esper.component_for_entity(ent, InventoryComp)
        if esper.has_component(ent, Equipment):
            equip = esper.component_for_entity(ent, Equipment)
        
        # Check where we're dropping
        target_inv_slot = -1
        target_equip_slot = None
        
        for i, rect in enumerate(self.inv_slots):
            if rect.collidepoint(pos):
                target_inv_slot = i
                break
        
        for slot_name, rect in self.equip_slots.items():
            if rect.collidepoint(pos):
                target_equip_slot = slot_name
                break
        
        # Get item id for slot checking
        if hasattr(self.dragging_item, 'item_id'):
            item_id = self.dragging_item.item_id
        else:
            item_id = self.dragging_item
        
        item_data = data_loader.get_item(item_id) or {}
        item_slot = item_data.get('slot', '')
        
        # Handle different drop scenarios
        if source_type == 'inventory' and target_equip_slot and equip and inv:
            # Equipping from inventory
            # Check if item can go in this slot
            if self._can_equip_in_slot(item_slot, target_equip_slot):
                # Remove from inventory
                if source_idx < len(inv.items):
                    inv.items.pop(source_idx)
                
                # Unequip any existing item
                old_item = equip.unequip(target_equip_slot)
                if old_item:
                    inv.add(old_item)
                
                # Equip the new item
                equip.equip(target_equip_slot, item_id)
        
        elif source_type == 'equipment' and target_inv_slot >= 0 and equip and inv:
            # Unequipping to inventory
            old_slot = source_idx  # This is actually the slot name
            unequipped = equip.unequip(old_slot)
            if unequipped:
                inv.add(unequipped)
        
        elif source_type == 'inventory' and target_inv_slot >= 0 and inv:
            # Moving within inventory
            if source_idx != target_inv_slot and source_idx < len(inv.items):
                item = inv.items.pop(source_idx)
                # Insert at target position
                if target_inv_slot >= len(inv.items):
                    inv.items.append(item)
                else:
                    inv.items.insert(target_inv_slot, item)
        
        elif source_type == 'equipment' and target_equip_slot and equip:
            # Swapping equipment slots
            old_slot = source_idx
            if old_slot != target_equip_slot:
                item1 = equip.unequip(old_slot)
                item2 = equip.unequip(target_equip_slot)
                
                if item1 and self._can_equip_in_slot(item_data.get('slot', ''), target_equip_slot):
                    equip.equip(target_equip_slot, item1)
                elif item1:
                    equip.equip(old_slot, item1)  # Put back
                
                if item2:
                    old_item_data = data_loader.get_item(item2) or {}
                    if self._can_equip_in_slot(old_item_data.get('slot', ''), old_slot):
                        equip.equip(old_slot, item2)
                    elif inv:
                        inv.add(item2)
        
        self.dragging_item = None
        self.drag_source = None
        return True
    
    def _can_equip_in_slot(self, item_slot: str, equip_slot: str) -> bool:
        """Check if item can be equipped in the given slot."""
        if not item_slot:
            return False
        
        # Direct match
        if item_slot == equip_slot:
            return True
        
        # Ring can go in ring_1 or ring_2
        if item_slot == 'ring' and equip_slot in ('ring_1', 'ring_2'):
            return True
        
        # Weapon can go in main_hand
        if item_slot in ('weapon', 'sword', 'axe', 'staff', 'bow', 'dagger', 'mace') and equip_slot == 'main_hand':
            return True
        
        # Shield/offhand can go in off_hand
        if item_slot in ('shield', 'offhand', 'off_hand') and equip_slot == 'off_hand':
            return True
        
        # Armor types
        if item_slot in ('helmet', 'helm', 'head') and equip_slot == 'head':
            return True
        if item_slot in ('chest', 'armor', 'robe', 'chestplate') and equip_slot == 'chest':
            return True
        if item_slot in ('gloves', 'hands', 'gauntlets') and equip_slot == 'hands':
            return True
        if item_slot in ('boots', 'feet', 'shoes') and equip_slot == 'feet':
            return True
        if item_slot in ('legs', 'pants', 'leggings') and equip_slot == 'legs':
            return True
        if item_slot in ('amulet', 'necklace', 'neck') and equip_slot == 'amulet':
            return True
        
        return False
    
    def _update_hover(self, pos: Tuple[int, int]):
        """Update hover state."""
        self.hover_item_idx = -1
        self.hover_equip_slot = None
        
        # Check inventory slots
        for i, rect in enumerate(self.inv_slots):
            if rect.collidepoint(pos):
                self.hover_item_idx = i
                return
        
        # Check equipment slots
        for slot_name, rect in self.equip_slots.items():
            if rect.collidepoint(pos):
                self.hover_equip_slot = slot_name
                return
    
    def render(self):
        """Render inventory UI."""
        if not self.visible:
            return
        
        # Darken background
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        
        # Party tabs
        self._render_party_tabs()
        
        # Left panel - Character sheet
        self._render_character_panel()
        
        # Right panel - Inventory
        self._render_inventory_panel()
        
        # Tooltip (for inventory or equipment)
        if not self.dragging_item:
            if self.hover_item_idx >= 0:
                self._render_tooltip()
            elif self.hover_equip_slot:
                self._render_equip_tooltip()
        
        # Dragging item
        if self.dragging_item:
            self._render_dragged_item()
    
    def _render_party_tabs(self):
        """Render party member tabs."""
        for i, ent in enumerate(self.party_entities):
            tab_rect = pygame.Rect(60 + i * 110, 20, 100, 30)
            
            is_selected = ent == self.selected_entity
            if is_selected:
                pygame.draw.rect(self.screen, (80, 70, 100), tab_rect)
                pygame.draw.rect(self.screen, COLOR_UI_ACCENT, tab_rect, 2)
            else:
                pygame.draw.rect(self.screen, (50, 45, 60), tab_rect)
                pygame.draw.rect(self.screen, (80, 75, 95), tab_rect, 1)
            
            # Name
            name = "???"
            if esper.has_component(ent, CharacterName):
                name = esper.component_for_entity(ent, CharacterName).name
            
            name_surf = self.font.render(name[:12], True, COLOR_TEXT)
            self.screen.blit(name_surf, (tab_rect.x + 8, tab_rect.y + 6))
    
    def _render_character_panel(self):
        """Render character stats and equipment."""
        panel = self.left_panel
        ent = self.selected_entity
        
        if ent < 0 or not esper.entity_exists(ent):
            return
        
        # Background
        pygame.draw.rect(self.screen, COLOR_UI_BG, panel)
        pygame.draw.rect(self.screen, COLOR_UI_BORDER, panel, 2)
        
        # Title
        name = "Character"
        if esper.has_component(ent, CharacterName):
            name = esper.component_for_entity(ent, CharacterName).name
        
        title = self.font_title.render(name, True, COLOR_UI_ACCENT)
        self.screen.blit(title, (panel.x + self.padding, panel.y + self.padding))
        
        # Level
        level = 1
        if esper.has_component(ent, CharacterLevel):
            level = esper.component_for_entity(ent, CharacterLevel).level
        
        level_text = self.font.render(f"Level {level}", True, COLOR_TEXT)
        self.screen.blit(level_text, (panel.x + self.padding, panel.y + 50))
        
        # Equipment slots
        for slot_name, rect in self.equip_slots.items():
            item = None
            if esper.has_component(ent, Equipment):
                equip = esper.component_for_entity(ent, Equipment)
                item = equip.get(slot_name)
            
            self._render_slot(rect, item, slot_name)
        
        # Stats
        self._render_stats(panel.x + self.padding, panel.y + 320)
    
    def _render_inventory_panel(self):
        """Render inventory grid."""
        panel = self.right_panel
        ent = self.selected_entity
        
        # Background
        pygame.draw.rect(self.screen, COLOR_UI_BG, panel)
        pygame.draw.rect(self.screen, COLOR_UI_BORDER, panel, 2)
        
        # Title
        title = self.font_title.render("Inventory", True, COLOR_UI_ACCENT)
        self.screen.blit(title, (panel.x + self.padding, panel.y + self.padding))
        
        # Get inventory
        items = []
        if ent >= 0 and esper.has_component(ent, InventoryComp):
            inv = esper.component_for_entity(ent, InventoryComp)
            items = inv.items
        
        # Slots
        for i, rect in enumerate(self.inv_slots):
            item = items[i] if i < len(items) else None
            self._render_slot(rect, item)
    
    def _render_slot(self, rect: pygame.Rect, item, slot_name: str = None):
        """Render an inventory/equipment slot."""
        from ..data.loader import data_loader
        from .icons import icon_generator
        
        # Background
        pygame.draw.rect(self.screen, (35, 30, 45), rect)
        pygame.draw.rect(self.screen, COLOR_UI_BORDER, rect, 1)
        
        if item:
            # Get item data - could be InventoryItem or equipment string
            if hasattr(item, 'item_id'):
                item_id = item.item_id
            else:
                item_id = item
            
            # Look up item data for name and rarity
            item_data = data_loader.get_item(item_id) or {}
            name = item_data.get('name', item_id)
            item_type = item_data.get('type', item_id)
            weapon_type = item_data.get('weapon_type', '')
            slot = item_data.get('slot', '')
            rarity = item_data.get('rarity', 0)
            
            # Build icon type string - prefer specific info for icon lookup
            # Use item_id or name as it has the specific item type (e.g., "short_sword" vs "weapon")
            icon_type = item_id if item_id else name
            
            # Rarity color
            rarity_color = RARITY_COLORS.get(rarity, (180, 180, 180))
            
            inner = rect.inflate(-4, -4)
            pygame.draw.rect(self.screen, (*rarity_color[:3], 100), inner)
            pygame.draw.rect(self.screen, rarity_color, inner, 2)
            
            # Item icon (use item_id for specific icon matching)
            icon_size = min(rect.width, rect.height) - 8
            icon = icon_generator.get_item_icon(icon_type, rarity, icon_size)
            icon_rect = icon.get_rect(center=rect.center)
            self.screen.blit(icon, icon_rect)
            
            # Show short item name below equipment slots
            if slot_name:
                short_name = name[:8] + "..." if len(name) > 8 else name
                name_text = self.font_small.render(short_name, True, rarity_color)
                name_rect = name_text.get_rect(centerx=rect.centerx, top=rect.bottom + 2)
                self.screen.blit(name_text, name_rect)
        elif slot_name:
            # Empty slot label
            label = slot_name.replace('_', '\n').split('\n')[0][:4]
            label_text = self.font_small.render(label, True, COLOR_TEXT_DIM)
            label_rect = label_text.get_rect(center=rect.center)
            self.screen.blit(label_text, label_rect)
    
    def _render_stats(self, x: int, y: int):
        """Render character stats."""
        ent = self.selected_entity
        if ent < 0:
            return
        
        # Attributes
        if esper.has_component(ent, Attributes):
            attrs = esper.component_for_entity(ent, Attributes)
            
            stats = [
                ("STR", attrs.strength, (200, 100, 100)),
                ("DEX", attrs.dexterity, (100, 200, 100)),
                ("INT", attrs.intelligence, (100, 100, 200)),
            ]
            
            for i, (name, value, color) in enumerate(stats):
                stat_x = x + i * 90
                
                label = self.font_small.render(name, True, color)
                self.screen.blit(label, (stat_x, y))
                
                val_text = self.font_large.render(str(value), True, COLOR_TEXT)
                self.screen.blit(val_text, (stat_x, y + 15))
        
        # Health/Mana
        y += 50
        if esper.has_component(ent, Health):
            health = esper.component_for_entity(ent, Health)
            hp_text = self.font_small.render(f"HP: {health.current}/{health.maximum}", True, COLOR_HEALTH)
            self.screen.blit(hp_text, (x, y))
        
        if esper.has_component(ent, Mana):
            mana = esper.component_for_entity(ent, Mana)
            mp_text = self.font_small.render(f"MP: {mana.current}/{mana.maximum}", True, COLOR_MANA)
            self.screen.blit(mp_text, (x + 100, y))
    
    def _render_tooltip(self):
        """Render item tooltip."""
        from ..data.loader import data_loader
        
        ent = self.selected_entity
        if ent < 0 or not esper.has_component(ent, InventoryComp):
            return
        
        inv = esper.component_for_entity(ent, InventoryComp)
        if self.hover_item_idx >= len(inv.items):
            return
        
        item = inv.items[self.hover_item_idx]
        if not item:
            return
        
        # Look up item data
        item_id = item.item_id if hasattr(item, 'item_id') else str(item)
        item_data = data_loader.get_item(item_id) or {}
        
        # Get rarity info
        rarity = item_data.get('rarity', 0)
        rarity_name = RARITY_NAMES.get(rarity, "Common")
        rarity_color = RARITY_COLORS.get(rarity, (180, 180, 180))
        
        # Build tooltip lines with colors
        name = item_data.get('name', item_id)
        lines = []
        line_colors = []
        
        # Item name in rarity color
        lines.append(name)
        line_colors.append(rarity_color)
        
        # Show quantity if > 1
        quantity = getattr(item, 'quantity', 1)
        if quantity > 1:
            lines[0] += f" x{quantity}"
        
        # Rarity text
        lines.append(f"[{rarity_name}]")
        line_colors.append(rarity_color)
        
        # Description
        desc = item_data.get('description', '')
        if desc:
            lines.append(desc)
            line_colors.append(COLOR_TEXT_DIM)
        
        # Type
        item_type = item_data.get('type', '')
        if item_type:
            lines.append(f"Type: {item_type.capitalize()}")
            line_colors.append(COLOR_TEXT_DIM)
        
        # Stats with highlighting
        if item_data.get('damage', 0) > 0:
            lines.append(f"Damage: {item_data['damage']}")
            line_colors.append((255, 180, 100))
        if item_data.get('fire_damage', 0) > 0:
            lines.append(f"  +{item_data['fire_damage']} Fire")
            line_colors.append((255, 120, 50))
        if item_data.get('ice_damage', 0) > 0:
            lines.append(f"  +{item_data['ice_damage']} Ice")
            line_colors.append((100, 180, 255))
        if item_data.get('lightning_damage', 0) > 0:
            lines.append(f"  +{item_data['lightning_damage']} Lightning")
            line_colors.append((255, 255, 100))
        if item_data.get('poison_damage', 0) > 0:
            lines.append(f"  +{item_data['poison_damage']} Poison")
            line_colors.append((100, 255, 100))
        if item_data.get('armor', 0) > 0:
            lines.append(f"Armor: {item_data['armor']}")
            line_colors.append((150, 200, 255))
        if item_data.get('block_chance', 0) > 0:
            lines.append(f"Block: {int(item_data['block_chance'] * 100)}%")
            line_colors.append((200, 200, 200))
        if item_data.get('crit_bonus', 0) > 0:
            lines.append(f"Crit: +{int(item_data['crit_bonus'] * 100)}%")
            line_colors.append((255, 220, 100))
        if item_data.get('lifesteal', 0) > 0:
            lines.append(f"Lifesteal: {int(item_data['lifesteal'] * 100)}%")
            line_colors.append((200, 50, 50))
        if item_data.get('mana_bonus', 0) > 0:
            lines.append(f"Mana: +{item_data['mana_bonus']}")
            line_colors.append((100, 150, 255))
        if item_data.get('health_bonus', 0) > 0:
            lines.append(f"Health: +{item_data['health_bonus']}")
            line_colors.append((255, 100, 100))
        if item_data.get('strength_bonus', 0) > 0:
            lines.append(f"Strength: +{item_data['strength_bonus']}")
            line_colors.append((255, 150, 100))
        if item_data.get('dexterity_bonus', 0) > 0:
            lines.append(f"Dexterity: +{item_data['dexterity_bonus']}")
            line_colors.append((100, 255, 150))
        if item_data.get('intelligence_bonus', 0) > 0:
            lines.append(f"Intelligence: +{item_data['intelligence_bonus']}")
            line_colors.append((100, 150, 255))
        if item_data.get('all_stats', 0) > 0:
            lines.append(f"All Stats: +{item_data['all_stats']}")
            line_colors.append((255, 215, 0))
        
        # Effect for consumables
        if item_data.get('effect_value', 0) > 0:
            effect_type = item_data.get('effect_type', 'heal')
            lines.append(f"Effect: {effect_type.replace('_', ' ').title()} {item_data['effect_value']}")
            line_colors.append((100, 255, 100))
        
        lines.append(f"Value: {item_data.get('value', 0)} gold")
        line_colors.append(COLOR_GOLD if item_data.get('value', 0) > 100 else COLOR_TEXT_DIM)
        
        # Render tooltip
        mouse_pos = pygame.mouse.get_pos()
        width = max(self.font_small.size(line)[0] for line in lines) + 20
        height = len(lines) * 18 + 10
        
        x = min(mouse_pos[0] + 15, SCREEN_WIDTH - width - 10)
        y = min(mouse_pos[1] + 15, SCREEN_HEIGHT - height - 10)
        
        tooltip_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(self.screen, (20, 18, 25), tooltip_rect)
        pygame.draw.rect(self.screen, rarity_color, tooltip_rect, 1)
        
        for i, line in enumerate(lines):
            color = line_colors[i] if i < len(line_colors) else COLOR_TEXT_DIM
            text = self.font_small.render(line, True, color)
            self.screen.blit(text, (x + 10, y + 5 + i * 18))
    
    def _render_equip_tooltip(self):
        """Render tooltip for equipped item."""
        from ..data.loader import data_loader
        
        ent = self.selected_entity
        if ent < 0 or not esper.has_component(ent, Equipment):
            return
        
        equip = esper.component_for_entity(ent, Equipment)
        item = equip.get(self.hover_equip_slot)
        
        if not item:
            # Show empty slot info
            slot_name = self.hover_equip_slot.replace('_', ' ').title()
            mouse_pos = pygame.mouse.get_pos()
            text = self.font_small.render(f"Empty {slot_name} slot", True, COLOR_TEXT_DIM)
            width = text.get_width() + 20
            height = 24
            
            x = min(mouse_pos[0] + 15, SCREEN_WIDTH - width - 10)
            y = min(mouse_pos[1] + 15, SCREEN_HEIGHT - height - 10)
            
            pygame.draw.rect(self.screen, (20, 18, 25), (x, y, width, height))
            pygame.draw.rect(self.screen, COLOR_UI_BORDER, (x, y, width, height), 1)
            self.screen.blit(text, (x + 10, y + 4))
            return
        
        # Look up item data
        item_id = item if isinstance(item, str) else (item.item_id if hasattr(item, 'item_id') else str(item))
        item_data = data_loader.get_item(item_id) or {}
        
        # Get rarity info
        rarity = item_data.get('rarity', 0)
        rarity_name = RARITY_NAMES.get(rarity, "Common")
        rarity_color = RARITY_COLORS.get(rarity, (180, 180, 180))
        
        # Build tooltip lines
        name = item_data.get('name', item_id)
        lines = [name, f"[{rarity_name}]"]
        line_colors = [rarity_color, rarity_color]
        
        # Slot
        slot_name = self.hover_equip_slot.replace('_', ' ').title()
        lines.append(f"Slot: {slot_name}")
        line_colors.append(COLOR_TEXT_DIM)
        
        # Stats
        if item_data.get('damage', 0) > 0:
            lines.append(f"Damage: {item_data['damage']}")
            line_colors.append((255, 180, 100))
        if item_data.get('armor', 0) > 0:
            lines.append(f"Armor: {item_data['armor']}")
            line_colors.append((150, 200, 255))
        if item_data.get('block_chance', 0) > 0:
            lines.append(f"Block: {int(item_data['block_chance'] * 100)}%")
            line_colors.append((200, 200, 200))
        
        # Render tooltip
        mouse_pos = pygame.mouse.get_pos()
        width = max(self.font_small.size(line)[0] for line in lines) + 20
        height = len(lines) * 18 + 10
        
        x = min(mouse_pos[0] + 15, SCREEN_WIDTH - width - 10)
        y = min(mouse_pos[1] + 15, SCREEN_HEIGHT - height - 10)
        
        tooltip_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(self.screen, (20, 18, 25), tooltip_rect)
        pygame.draw.rect(self.screen, rarity_color, tooltip_rect, 1)
        
        for i, line in enumerate(lines):
            color = line_colors[i] if i < len(line_colors) else COLOR_TEXT_DIM
            text = self.font_small.render(line, True, color)
            self.screen.blit(text, (x + 10, y + 5 + i * 18))
    
    def _render_dragged_item(self):
        """Render item being dragged."""
        from ..data.loader import data_loader
        
        if not self.dragging_item:
            return
        
        mouse_pos = pygame.mouse.get_pos()
        rect = pygame.Rect(mouse_pos[0] - 24, mouse_pos[1] - 24, 
                          self.slot_size, self.slot_size)
        
        # Get item data
        item_id = self.dragging_item.item_id if hasattr(self.dragging_item, 'item_id') else str(self.dragging_item)
        item_data = data_loader.get_item(item_id) or {}
        
        rarity = item_data.get('rarity', 0)
        rarity_color = RARITY_COLORS.get(rarity, (100, 100, 100))
        
        surf = pygame.Surface((self.slot_size, self.slot_size), pygame.SRCALPHA)
        pygame.draw.rect(surf, (*rarity_color, 200), surf.get_rect())
        self.screen.blit(surf, rect)
        
        name = item_data.get('name', item_id)
        initial = self.font.render(name[0].upper() if name else '?', True, (255, 255, 255))
        initial_rect = initial.get_rect(center=rect.center)
        self.screen.blit(initial, initial_rect)

