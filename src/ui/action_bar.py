"""Action bar for quick-use slots (1-8 keys)."""

import pygame
import esper
from typing import Optional, Dict, List

from ..core.constants import (
    COLOR_UI_BG, COLOR_UI_BORDER, COLOR_UI_ACCENT,
    COLOR_TEXT, COLOR_TEXT_DIM, COLOR_MANA, COLOR_HEALTH, RARITY_COLORS
)
from ..ecs.components import (
    Health, Mana, SpellBook, PartyMember, Selected, Inventory as InventoryComp,
    Downed, Dead
)
from ..core.events import EventBus, Event, EventType


class ActionBar:
    """Hotbar for quick-use items and spells (keys 1-8)."""
    
    NUM_SLOTS = 8
    
    def __init__(self, screen: pygame.Surface, event_bus: EventBus):
        self.screen = screen
        self.event_bus = event_bus
        
        # Slot contents: {'type': 'spell'/'item', 'id': ..., 'name': ...}
        self.slots: List[Optional[Dict]] = [None] * self.NUM_SLOTS
        self.cooldowns: List[float] = [0.0] * self.NUM_SLOTS
        
        # Base layout sizes
        self._base_slot_size = 50
        self._base_padding = 4
        self._base_bar_height = 60
        
        # UI scaling
        self._ui_scale = 1.0
        self._rebuild_layout()
        
        # Fonts
        pygame.font.init()
        self._base_font = 24
        self._base_font_small = 18
        self._rebuild_fonts()
        
        # Setup defaults
        self._setup_defaults()
    
    def _rebuild_layout(self):
        """Rebuild layout at current scale."""
        self.slot_size = int(self._base_slot_size * self._ui_scale)
        self.padding = int(self._base_padding * self._ui_scale)
        self.bar_height = int(self._base_bar_height * self._ui_scale)
        
        total_width = self.NUM_SLOTS * (self.slot_size + self.padding) + self.padding
        self.bar_x = self.screen.get_width() - total_width - int(20 * self._ui_scale)
        self.bar_y = self.screen.get_height() - self.bar_height - int(100 * self._ui_scale)
    
    def _rebuild_fonts(self):
        """Rebuild fonts at current scale."""
        self.font = pygame.font.Font(None, int(self._base_font * self._ui_scale))
        self.font_small = pygame.font.Font(None, int(self._base_font_small * self._ui_scale))
    
    def set_scale(self, scale: float):
        """Set UI scale factor."""
        if abs(scale - self._ui_scale) > 0.01:
            self._ui_scale = scale
            self._rebuild_layout()
            self._rebuild_fonts()
    
    def s(self, value: int) -> int:
        """Scale a value by UI scale factor."""
        return int(value * self._ui_scale)
    
    def _setup_defaults(self):
        """Set up default action bar assignments."""
        self.slots[0] = {'type': 'item', 'effect_type': 'heal', 'name': 'Health Potion'}
        self.slots[1] = {'type': 'item', 'effect_type': 'restore_mana', 'name': 'Mana Potion'}
    
    def get_slot_rect(self, index: int) -> pygame.Rect:
        """Get rectangle for a slot."""
        x = self.bar_x + self.padding + index * (self.slot_size + self.padding)
        y = self.bar_y + 5
        return pygame.Rect(x, y, self.slot_size, self.slot_size)
    
    def use_slot(self, index: int, entity: int) -> bool:
        """Use the item/spell in a slot."""
        if index < 0 or index >= self.NUM_SLOTS:
            return False
        
        slot = self.slots[index]
        if not slot:
            self.event_bus.emit(Event(EventType.NOTIFICATION, {
                "text": f"Slot {index + 1} is empty",
                "color": (150, 150, 150)
            }))
            return False
        
        # Check cooldown
        if self.cooldowns[index] > 0:
            self.event_bus.emit(Event(EventType.NOTIFICATION, {
                "text": "On cooldown!",
                "color": (150, 150, 150)
            }))
            return False
        
        if slot['type'] == 'item':
            return self._use_item_slot(index, slot, entity)
        elif slot['type'] == 'spell':
            return self._use_spell_slot(index, slot, entity)
        
        return False
    
    def _use_item_slot(self, index: int, slot: Dict, entity: int) -> bool:
        """Use an item from the action bar. Searches ALL party inventories (shared potions)."""
        from ..data.loader import data_loader
        
        effect_type = slot.get('effect_type')
        
        # Search ALL party members' inventories for matching consumables
        # Party shares potions!
        matching_items = []
        for party_ent, (member,) in esper.get_components(PartyMember):
            if not esper.has_component(party_ent, InventoryComp):
                continue
            inv = esper.component_for_entity(party_ent, InventoryComp)
            
            for i, item in enumerate(inv.items):
                item_data = data_loader.get_item(item.item_id)
                if not item_data:
                    continue
                
                item_effect_type = item_data.get('effect_type')
                if item_effect_type == effect_type:
                    effect_value = item_data.get('effect_value', 50)
                    # Store: (effect_value, inv_index, item, item_data, inventory_owner_ent, inventory)
                    matching_items.append((effect_value, i, item, item_data, party_ent, inv))
        
        if not matching_items:
            self.event_bus.emit(Event(EventType.NOTIFICATION, {
                "text": f"No potions available",
                "color": (200, 150, 150)
            }))
            return False
        
        # Sort by effect_value ascending (use smallest first)
        matching_items.sort(key=lambda x: x[0])
        
        # Use the smallest potion
        effect_value, i, item, item_data, inv_owner, inv = matching_items[0]
        item_name = item_data.get('name', 'Potion')
        
        # Get character name for notification
        from ..ecs.components import CharacterName
        char_name = "???"
        if esper.has_component(entity, CharacterName):
            char_name = esper.component_for_entity(entity, CharacterName).name
        
        if effect_type == 'heal':
            # Can't use health potion on downed/dead
            if esper.has_component(entity, Downed) or esper.has_component(entity, Dead):
                self.event_bus.emit(Event(EventType.NOTIFICATION, {
                    "text": f"{char_name} is downed!",
                    "color": (200, 150, 150)
                }))
                return False
            
            if esper.has_component(entity, Health):
                health = esper.component_for_entity(entity, Health)
                health.current = min(health.maximum, health.current + effect_value)
                
                self.event_bus.emit(Event(EventType.NOTIFICATION, {
                    "text": f"{char_name}: +{effect_value} HP",
                    "color": (100, 255, 150)
                }))
        
        elif effect_type == 'restore_mana':
            # Mana potions go to party member with lowest mana % who uses magic
            from ..ecs.components import CharacterClass
            
            best_target = None
            best_mana_pct = 1.0
            
            for ent, (_, mana_comp) in esper.get_components(PartyMember, Mana):
                # Skip downed/dead - can't give them mana
                if esper.has_component(ent, Downed) or esper.has_component(ent, Dead):
                    continue
                # Skip if full mana
                if mana_comp.current >= mana_comp.maximum:
                    continue
                # Prefer mages (they actually need mana)
                is_mage = False
                if esper.has_component(ent, CharacterClass):
                    cc = esper.component_for_entity(ent, CharacterClass)
                    is_mage = cc.class_name in ('mage', 'cleric')
                
                mana_pct = mana_comp.current / max(1, mana_comp.maximum)
                # Mages get priority (subtract 0.5 from their percentage)
                effective_pct = mana_pct - (0.5 if is_mage else 0)
                
                if effective_pct < best_mana_pct:
                    best_mana_pct = effective_pct
                    best_target = ent
            
            if best_target and esper.has_component(best_target, Mana):
                mana = esper.component_for_entity(best_target, Mana)
                mana.current = min(mana.maximum, mana.current + effect_value)
                
                # Get target name
                target_name = "Ally"
                if esper.has_component(best_target, CharacterName):
                    target_name = esper.component_for_entity(best_target, CharacterName).name
                
                self.event_bus.emit(Event(EventType.NOTIFICATION, {
                    "text": f"{target_name}: +{effect_value} MP",
                    "color": (100, 150, 255)
                }))
            else:
                self.event_bus.emit(Event(EventType.NOTIFICATION, {
                    "text": "No one needs mana",
                    "color": (150, 150, 150)
                }))
                return False
        
        # Reduce quantity or remove item
        item.quantity -= 1
        if item.quantity <= 0:
            inv.items.pop(i)
        
        self.cooldowns[index] = 0.5
        return True
    
    def _use_spell_slot(self, index: int, slot: Dict, entity: int) -> bool:
        """Use a spell from the action bar."""
        self.event_bus.emit(Event(EventType.NOTIFICATION, {
            "text": f"Spell slots not implemented",
            "color": (200, 100, 100)
        }))
        return False
    
    def _use_spell_slot(self, index: int, slot: Dict, entity: int) -> bool:
        """Cast a spell from the action bar."""
        spell_id = slot.get('id')
        
        if not esper.has_component(entity, SpellBook):
            return False
        
        spellbook = esper.component_for_entity(entity, SpellBook)
        
        if spell_id not in spellbook.known_spells:
            self.event_bus.emit(Event(EventType.NOTIFICATION, {
                "text": "Spell not learned!",
                "color": (200, 100, 100)
            }))
            return False
        
        # Request spell cast through event
        self.event_bus.emit(Event(EventType.SPELL_CAST_REQUESTED, {
            "caster": entity,
            "spell_id": spell_id,
            "target_id": -1,  # Will auto-target
            "target_x": 0,
            "target_y": 0
        }))
        
        return True
    
    def assign_spell(self, slot_index: int, spell_id: str, spell_name: str):
        """Assign a spell to a slot."""
        if 0 <= slot_index < self.NUM_SLOTS:
            self.slots[slot_index] = {
                'type': 'spell',
                'id': spell_id,
                'name': spell_name
            }
    
    def assign_item(self, slot_index: int, effect_type: str, item_name: str):
        """Assign an item type to a slot."""
        if 0 <= slot_index < self.NUM_SLOTS:
            self.slots[slot_index] = {
                'type': 'item',
                'effect_type': effect_type,
                'name': item_name
            }
    
    def clear_slot(self, slot_index: int):
        """Clear a slot."""
        if 0 <= slot_index < self.NUM_SLOTS:
            self.slots[slot_index] = None
    
    def update(self, dt: float):
        """Update cooldowns."""
        for i in range(self.NUM_SLOTS):
            if self.cooldowns[i] > 0:
                self.cooldowns[i] = max(0, self.cooldowns[i] - dt)
    
    def count_items(self, entity: int, effect_type: str) -> int:
        """Count items of a type in inventory."""
        from ..data.loader import data_loader
        
        if not esper.has_component(entity, InventoryComp):
            return 0
        
        inv = esper.component_for_entity(entity, InventoryComp)
        count = 0
        for item in inv.items:
            item_data = data_loader.get_item(item.item_id)
            if item_data and item_data.get('effect_type') == effect_type:
                count += item.quantity
        return count
    
    def render(self, entity: int, camera_zoom: float = 1.0):
        """Render the action bar."""
        # Scale UI based on camera zoom - make it big and readable
        target_scale = camera_zoom / 1.0  # 75% of previous
        target_scale = max(1.5, min(3.0, target_scale))
        self.set_scale(target_scale)
        
        # Background
        total_width = self.NUM_SLOTS * (self.slot_size + self.padding) + self.padding
        bar_rect = pygame.Rect(self.bar_x, self.bar_y, total_width, self.bar_height)
        pygame.draw.rect(self.screen, COLOR_UI_BG, bar_rect)
        pygame.draw.rect(self.screen, COLOR_UI_BORDER, bar_rect, 2)
        
        # Label
        label = self.font_small.render("Action Bar", True, COLOR_TEXT_DIM)
        self.screen.blit(label, (self.bar_x + self.s(5), self.bar_y - self.s(15)))
        
        # Slots
        for i in range(self.NUM_SLOTS):
            self._render_slot(i, entity)
    
    def _render_slot(self, index: int, entity: int):
        """Render a single slot."""
        rect = self.get_slot_rect(index)
        slot = self.slots[index]
        
        # Background
        pygame.draw.rect(self.screen, (35, 30, 45), rect)
        pygame.draw.rect(self.screen, COLOR_UI_BORDER, rect, 1)
        
        # Slot number
        num_text = self.font_small.render(str(index + 1), True, COLOR_TEXT_DIM)
        self.screen.blit(num_text, (rect.x + 2, rect.y + 2))
        
        if slot:
            if slot['type'] == 'spell':
                self._render_spell_slot(rect, slot, entity)
            elif slot['type'] == 'item':
                self._render_item_slot(rect, slot, entity)
            
            # Cooldown overlay
            if self.cooldowns[index] > 0:
                self._render_cooldown(rect, self.cooldowns[index])
    
    def _render_spell_slot(self, rect: pygame.Rect, slot: Dict, entity: int):
        """Render a spell slot."""
        spell_id = slot.get('id', '')
        
        # Color based on spell type
        if 'fire' in spell_id:
            color = (255, 120, 50)
        elif 'ice' in spell_id or 'frost' in spell_id:
            color = (100, 180, 255)
        elif 'heal' in spell_id:
            color = (100, 255, 150)
        elif 'lightning' in spell_id:
            color = (255, 255, 100)
        else:
            color = (180, 150, 220)
        
        # Draw icon circle
        inner = rect.inflate(-8, -8)
        pygame.draw.circle(self.screen, color, inner.center, inner.width // 2 - 2)
        
        # Abbreviation
        abbrev = spell_id[:3].upper() if spell_id else "???"
        abbrev_surf = self.font_small.render(abbrev, True, (255, 255, 255))
        abbrev_rect = abbrev_surf.get_rect(center=rect.center)
        self.screen.blit(abbrev_surf, abbrev_rect)
    
    def _render_item_slot(self, rect: pygame.Rect, slot: Dict, entity: int):
        """Render an item slot."""
        effect_type = slot.get('effect_type', '')
        
        # Potion color
        if effect_type == 'heal':
            color = COLOR_HEALTH
        elif effect_type in ('mana', 'restore_mana'):
            color = COLOR_MANA
        else:
            color = (150, 150, 150)
        
        # Draw potion shape
        inner = rect.inflate(-10, -10)
        
        # Bottle
        bottle_rect = pygame.Rect(inner.x + inner.width // 4, inner.y + inner.height // 3,
                                  inner.width // 2, inner.height * 2 // 3)
        pygame.draw.rect(self.screen, color, bottle_rect, border_radius=3)
        
        # Neck
        neck_rect = pygame.Rect(inner.centerx - 4, inner.y + 2, 8, inner.height // 4)
        pygame.draw.rect(self.screen, (100, 90, 110), neck_rect)
        
        # Count
        count = self.count_items(entity, effect_type)
        count_surf = self.font_small.render(str(count), True, (255, 255, 255))
        self.screen.blit(count_surf, (rect.right - 14, rect.bottom - 14))
        
        if count == 0:
            # Darken if none
            dark = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            dark.fill((0, 0, 0, 120))
            self.screen.blit(dark, rect)
    
    def _render_cooldown(self, rect: pygame.Rect, cooldown: float):
        """Render cooldown overlay."""
        overlay = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, rect)
        
        cd_text = self.font.render(f"{cooldown:.1f}", True, (255, 255, 255))
        cd_rect = cd_text.get_rect(center=rect.center)
        self.screen.blit(cd_text, cd_rect)

