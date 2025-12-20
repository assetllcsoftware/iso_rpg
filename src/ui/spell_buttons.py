"""Mobile-friendly spell buttons with cooldown display."""

import pygame
import math
from .spell_icons import draw_spell_icon


class SpellButtons:
    """Spell buttons for each party member on left side of screen."""
    
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # Button layout
        self.button_size = 50
        self.padding = 8
        self.left_margin = 15
        
        # Each row is a party member (max 3)
        # Row 0: QWER (main char)
        # Row 1: ASDF (ally 1)
        # Row 2: ZXCV (ally 2)
        self.key_rows = [
            [pygame.K_q, pygame.K_w, pygame.K_e, pygame.K_r],
            [pygame.K_a, pygame.K_s, pygame.K_d, pygame.K_f],
            [pygame.K_z, pygame.K_x, pygame.K_c, pygame.K_v],
        ]
        self.key_labels = [
            ['Q', 'W', 'E', 'R'],
            ['A', 'S', 'D', 'F'],
            ['Z', 'X', 'C', 'V'],
        ]
        
        # Colors per row
        self.row_colors = [
            (80, 120, 180),   # Blue for main
            (120, 80, 160),   # Purple for ally 1
            (80, 160, 120),   # Green for ally 2
        ]
        
        self.font = pygame.font.Font(None, 20)
        self.font_small = pygame.font.Font(None, 16)
        
        # Party reference
        self.party = None
    
    def set_party(self, party):
        """Set party reference."""
        self.party = party
    
    def _get_button_rect(self, row, col):
        """Get rect for a spell button."""
        x = self.left_margin + col * (self.button_size + self.padding)
        # Start from middle of screen, offset by row
        base_y = self.screen_height // 2 - 60
        y = base_y + row * (self.button_size + self.padding + 10)
        return pygame.Rect(x, y, self.button_size, self.button_size)
    
    def handle_click(self, mx, my):
        """Check if a spell button was clicked. Returns (party_index, spell_index) or None."""
        if not self.party:
            return None
        
        for row in range(min(len(self.party), 3)):
            char = self.party[row]
            if not hasattr(char, 'spellbook'):
                continue
            
            spells = list(char.spellbook.spells.keys())
            for col in range(min(len(spells), 4)):
                rect = self._get_button_rect(row, col)
                if rect.collidepoint(mx, my):
                    return (row, col)
        
        return None
    
    def render(self, screen, party):
        """Render spell buttons for all party members."""
        if not party:
            return
        
        self.party = party
        
        for row in range(min(len(party), 3)):
            char = party[row]
            if not hasattr(char, 'spellbook'):
                continue
            
            spells = list(char.spellbook.spells.items())
            row_color = self.row_colors[row]
            
            # Character name label
            name_text = self.font_small.render(char.name[:8], True, row_color)
            name_x = self.left_margin
            name_y = self._get_button_rect(row, 0).y - 15
            screen.blit(name_text, (name_x, name_y))
            
            for col in range(min(len(spells), 4)):
                spell_id, spell = spells[col]
                rect = self._get_button_rect(row, col)
                
                # Get cooldown
                cooldown = char.spellbook.cooldowns.get(spell_id, 0)
                max_cooldown = spell.cooldown
                
                # Check if can cast (mana + cooldown only - spells are only shown if learned)
                cooldown = char.spellbook.cooldowns.get(spell_id, 0)
                has_mana = char.mana >= spell.mana_cost
                can_cast = has_mana and cooldown <= 0
                
                # Background color based on state
                if can_cast:
                    bg_color = row_color
                else:
                    bg_color = tuple(c // 2 for c in row_color)
                
                pygame.draw.rect(screen, bg_color, rect, border_radius=6)
                pygame.draw.rect(screen, (40, 40, 50), rect, 2, border_radius=6)
                
                # Draw spell icon
                spell_color = spell.color
                draw_spell_icon(screen, spell_id, rect, spell_color)
                
                # Cooldown spinner overlay
                if cooldown > 0:
                    self._draw_cooldown_spinner(screen, rect, cooldown, max_cooldown)
                
                # Key label
                key_label = self.key_labels[row][col]
                key_text = self.font.render(key_label, True, (255, 255, 255))
                screen.blit(key_text, (rect.right - 18, rect.bottom - 18))
                
                # Mana cost
                mana_text = self.font_small.render(str(spell.mana_cost), True, (150, 180, 255))
                screen.blit(mana_text, (rect.x + 5, rect.bottom - 14))
    
    def _draw_cooldown_spinner(self, screen, rect, cooldown, max_cooldown):
        """Draw spinning cooldown overlay."""
        if max_cooldown <= 0:
            return
        
        # Calculate progress (1.0 = full cooldown, 0.0 = ready)
        progress = min(1.0, cooldown / max_cooldown)
        
        # Dark overlay
        overlay = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, rect.topleft)
        
        # Spinning arc
        center = rect.center
        radius = rect.width // 2 - 4
        
        # Draw arc from top, clockwise based on remaining cooldown
        start_angle = math.pi / 2  # Top
        end_angle = start_angle - (2 * math.pi * progress)
        
        if progress > 0.01:
            # Draw the "remaining" arc
            points = [center]
            num_segments = max(3, int(20 * progress))
            for i in range(num_segments + 1):
                angle = start_angle - (2 * math.pi * progress * i / num_segments)
                x = center[0] + radius * math.cos(angle)
                y = center[1] - radius * math.sin(angle)
                points.append((x, y))
            
            if len(points) >= 3:
                pygame.draw.polygon(screen, (100, 100, 120, 180), points)
        
        # Cooldown number
        cd_text = self.font.render(f"{cooldown:.1f}", True, (255, 255, 255))
        text_rect = cd_text.get_rect(center=center)
        screen.blit(cd_text, text_rect)

