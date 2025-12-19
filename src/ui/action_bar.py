"""Action bar for quick-use slots."""

import pygame
from ..engine.constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    COLOR_UI_BG, COLOR_UI_BORDER, COLOR_UI_ACCENT,
    COLOR_TEXT, COLOR_TEXT_DIM, COLOR_MANA, RARITY_COLORS
)


class ActionBar:
    """Hotbar for quick-use items and spells."""
    
    NUM_SLOTS = 8
    
    def __init__(self, screen):
        self.screen = screen
        self.slots = [None] * self.NUM_SLOTS  # Each slot: {'type': 'spell'/'item', 'id': ...}
        self.cooldowns = [0.0] * self.NUM_SLOTS
        
        # Layout
        self.slot_size = 50
        self.padding = 4
        self.bar_height = 70
        
        total_width = self.NUM_SLOTS * (self.slot_size + self.padding) + self.padding
        self.bar_x = (SCREEN_WIDTH - total_width) // 2
        self.bar_y = SCREEN_HEIGHT - self.bar_height - 10
        
        # Fonts
        pygame.font.init()
        self.font = pygame.font.Font(None, 24)
        self.font_small = pygame.font.Font(None, 18)
        
        # Dragging
        self.dragging = None
        self.drag_source = None
        
        # Setup default slots
        self._setup_defaults()
    
    def _setup_defaults(self):
        """Set up default action bar assignments."""
        # Slot 0: Health potion
        self.slots[0] = {'type': 'item', 'effect_type': 'heal', 'name': 'Health Potion'}
        # Slot 1: Mana potion  
        self.slots[1] = {'type': 'item', 'effect_type': 'mana', 'name': 'Mana Potion'}
        # Slot 2-4: Spells
        self.slots[2] = {'type': 'spell', 'id': 'fireball', 'name': 'Fireball'}
        self.slots[3] = {'type': 'spell', 'id': 'heal', 'name': 'Heal'}
        self.slots[4] = {'type': 'spell', 'id': 'ice_shard', 'name': 'Ice Shard'}
    
    def get_slot_rect(self, index):
        """Get the rectangle for a slot."""
        x = self.bar_x + self.padding + index * (self.slot_size + self.padding)
        y = self.bar_y + 10
        return pygame.Rect(x, y, self.slot_size, self.slot_size)
    
    def use_slot(self, index, character, game):
        """Use the item/spell in a slot."""
        print(f"[DEBUG] Action bar slot {index+1} pressed")
        
        if index < 0 or index >= self.NUM_SLOTS:
            print(f"[DEBUG] Invalid slot index: {index}")
            return False
        
        slot = self.slots[index]
        if not slot:
            game.add_notification(f"Slot {index+1} is empty", (150, 150, 150))
            print(f"[DEBUG] Slot {index} is empty")
            return False
        
        print(f"[DEBUG] Slot contains: {slot}")
        
        # Check cooldown
        if self.cooldowns[index] > 0:
            game.add_notification("On cooldown!", (150, 150, 150))
            return False
        
        if slot['type'] == 'item':
            return self._use_item_slot(index, slot, character, game)
        elif slot['type'] == 'spell':
            return self._use_spell_slot(index, slot, character, game)
        
        return False
    
    def _use_item_slot(self, index, slot, character, game):
        """Use an item from the action bar."""
        effect_type = slot.get('effect_type')
        
        # Find matching item in inventory
        for item in character.inventory:
            if hasattr(item, 'effect_type') and item.effect_type == effect_type:
                if item.use(character):
                    character.inventory.remove(item)
                    game.add_notification(f"Used {item.name}", (100, 255, 150))
                    self.cooldowns[index] = 0.5  # Short cooldown
                    return True
        
        game.add_notification(f"No {slot.get('name', 'item')} available!", (200, 100, 100))
        return False
    
    def _use_spell_slot(self, index, slot, character, game):
        """Cast a spell from the action bar."""
        spell_id = slot.get('id')
        
        if not hasattr(character, 'spellbook'):
            game.add_notification("Cannot cast spells!", (200, 100, 100))
            return False
        
        if spell_id not in character.spellbook.spells:
            game.add_notification("Spell not learned!", (200, 100, 100))
            return False
        
        spell = character.spellbook.spells[spell_id]
        
        # Check mana
        if character.mana < spell.mana_cost:
            game.add_notification("Not enough mana!", (100, 100, 200))
            return False
        
        # Check spell cooldown
        if character.spellbook.cooldowns.get(spell_id, 0) > 0:
            game.add_notification("Spell on cooldown!", (150, 150, 150))
            return False
        
        # Determine target
        if game.target:
            target_pos = (game.target.x, game.target.y)
        else:
            target_pos = (character.x, character.y)
        
        # Cast!
        result = game.magic.cast_spell(character, character.spellbook, spell_id, target_pos, game.world)
        
        if result:
            game.add_notification(f"Cast {result.name}!", result.color)
            game.effects.spawn_spell(spell_id, character.x, character.y, target_pos[0], target_pos[1])
            self.cooldowns[index] = result.cooldown
            return True
        
        return False
    
    def assign_spell(self, slot_index, spell_id, spell_name):
        """Assign a spell to a slot."""
        if 0 <= slot_index < self.NUM_SLOTS:
            self.slots[slot_index] = {
                'type': 'spell',
                'id': spell_id,
                'name': spell_name
            }
    
    def assign_item(self, slot_index, effect_type, item_name):
        """Assign an item type to a slot."""
        if 0 <= slot_index < self.NUM_SLOTS:
            self.slots[slot_index] = {
                'type': 'item',
                'effect_type': effect_type,
                'name': item_name
            }
    
    def clear_slot(self, slot_index):
        """Clear a slot."""
        if 0 <= slot_index < self.NUM_SLOTS:
            self.slots[slot_index] = None
    
    def update(self, dt):
        """Update cooldowns."""
        for i in range(self.NUM_SLOTS):
            if self.cooldowns[i] > 0:
                self.cooldowns[i] = max(0, self.cooldowns[i] - dt)
    
    def count_items(self, character, effect_type):
        """Count how many items of a type the character has."""
        count = 0
        for item in character.inventory:
            if hasattr(item, 'effect_type') and item.effect_type == effect_type:
                count += 1
        return count
    
    def render(self, character):
        """Render the action bar."""
        # Background
        bar_rect = pygame.Rect(
            self.bar_x, self.bar_y,
            self.NUM_SLOTS * (self.slot_size + self.padding) + self.padding,
            self.bar_height
        )
        pygame.draw.rect(self.screen, COLOR_UI_BG, bar_rect)
        pygame.draw.rect(self.screen, COLOR_UI_BORDER, bar_rect, 2)
        
        # Slots
        for i in range(self.NUM_SLOTS):
            self._render_slot(i, character)
    
    def _render_slot(self, index, character):
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
            # Slot content
            if slot['type'] == 'spell':
                self._render_spell_slot(rect, slot, character)
            elif slot['type'] == 'item':
                self._render_item_slot(rect, slot, character)
            
            # Cooldown overlay
            if self.cooldowns[index] > 0:
                self._render_cooldown(rect, self.cooldowns[index])
    
    def _render_spell_slot(self, rect, slot, character):
        """Render a spell slot."""
        from .icons import draw_spell_icon
        
        spell_id = slot.get('id')
        
        # Draw spell icon
        icon_surf = pygame.Surface((rect.width - 8, rect.height - 8), pygame.SRCALPHA)
        icon_rect = icon_surf.get_rect()
        draw_spell_icon(icon_surf, icon_rect, spell_id)
        self.screen.blit(icon_surf, (rect.x + 4, rect.y + 4))
        
        # Check if usable
        can_use = True
        if hasattr(character, 'spellbook'):
            spell = character.spellbook.spells.get(spell_id)
            if spell and character.mana < spell.mana_cost:
                can_use = False
                # Mana cost indicator
                cost_text = self.font_small.render(f"{int(spell.mana_cost)}", True, COLOR_MANA)
                self.screen.blit(cost_text, (rect.right - 18, rect.bottom - 14))
        
        if not can_use:
            # Darken overlay
            dark = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            dark.fill((0, 0, 0, 100))
            self.screen.blit(dark, rect)
    
    def _render_item_slot(self, rect, slot, character):
        """Render an item slot."""
        from .icons import draw_potion_icon
        
        effect_type = slot.get('effect_type')
        
        # Draw potion icon
        icon_surf = pygame.Surface((rect.width - 8, rect.height - 8), pygame.SRCALPHA)
        icon_rect = icon_surf.get_rect()
        draw_potion_icon(icon_surf, icon_rect, effect_type)
        self.screen.blit(icon_surf, (rect.x + 4, rect.y + 4))
        
        # Item count
        count = self.count_items(character, effect_type)
        
        # Count in corner with background
        count_bg = pygame.Surface((16, 14), pygame.SRCALPHA)
        count_bg.fill((0, 0, 0, 180))
        self.screen.blit(count_bg, (rect.right - 18, rect.bottom - 16))
        count_text = self.font_small.render(str(count), True, (255, 255, 255))
        self.screen.blit(count_text, (rect.right - 14, rect.bottom - 14))
        
        if count == 0:
            # Darken if none available
            dark = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            dark.fill((0, 0, 0, 120))
            self.screen.blit(dark, rect)
    
    def _render_cooldown(self, rect, cooldown):
        """Render cooldown overlay."""
        # Semi-transparent dark overlay
        overlay = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, rect)
        
        # Cooldown text
        cd_text = self.font.render(f"{cooldown:.1f}", True, (255, 255, 255))
        cd_rect = cd_text.get_rect(center=rect.center)
        self.screen.blit(cd_text, cd_rect)

