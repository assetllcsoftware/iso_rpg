"""Save/Load menu UI."""

import pygame
import os
from datetime import datetime
from ..systems.save_load import SAVE_DIR, get_save_info, save_game, load_game, ensure_save_dir


class SaveLoadMenu:
    """Menu for saving and loading games."""
    
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.visible = False
        self.mode = 'load'  # 'save' or 'load'
        
        self.font_title = pygame.font.Font(None, 48)
        self.font = pygame.font.Font(None, 28)
        self.font_small = pygame.font.Font(None, 22)
        
        # Panel dimensions
        self.panel_width = 500
        self.panel_height = 400
        self.panel_x = (screen_width - self.panel_width) // 2
        self.panel_y = (screen_height - self.panel_height) // 2
        
        # Save slots
        self.max_saves = 20
        self.saves = []
        self.selected_slot = 0
        self.scroll_offset = 0
        self.visible_slots = 8
        
        # Colors
        self.bg_color = (25, 22, 35)
        self.border_color = (80, 70, 100)
        self.highlight_color = (60, 55, 80)
        self.selected_color = (100, 80, 140)
        self.text_color = (220, 215, 230)
        self.dim_color = (140, 135, 150)
    
    def show(self, mode='load'):
        """Show the menu."""
        self.visible = True
        self.mode = mode
        self.refresh_saves()
        self.selected_slot = 0
        self.scroll_offset = 0
    
    def hide(self):
        """Hide the menu."""
        self.visible = False
    
    def toggle(self, mode='load'):
        """Toggle visibility."""
        if self.visible:
            self.hide()
        else:
            self.show(mode)
    
    def refresh_saves(self):
        """Scan for all save files."""
        ensure_save_dir()
        self.saves = []
        
        # Look for all save files
        if os.path.exists(SAVE_DIR):
            for filename in os.listdir(SAVE_DIR):
                if filename.startswith('save_') and filename.endswith('.json'):
                    try:
                        slot = int(filename.replace('save_', '').replace('.json', ''))
                        info = get_save_info(slot)
                        if info:
                            info['slot'] = slot
                            self.saves.append(info)
                    except (ValueError, Exception):
                        pass
        
        # Sort by timestamp (newest first)
        self.saves.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    
    def get_next_slot(self):
        """Get the next available save slot number."""
        used_slots = {s['slot'] for s in self.saves}
        for i in range(1, self.max_saves + 1):
            if i not in used_slots:
                return i
        # If all slots used, overwrite oldest
        if self.saves:
            oldest = min(self.saves, key=lambda x: x.get('timestamp', ''))
            return oldest['slot']
        return 1
    
    def handle_event(self, event, game):
        """Handle input events. Returns True if event was consumed."""
        if not self.visible:
            return False
        
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_F9, pygame.K_F5):
                self.hide()
                return True
            elif event.key == pygame.K_UP:
                self.selected_slot = max(0, self.selected_slot - 1)
                # Scroll if needed
                if self.selected_slot < self.scroll_offset:
                    self.scroll_offset = self.selected_slot
                return True
            elif event.key == pygame.K_DOWN:
                max_slot = len(self.saves) if self.mode == 'load' else len(self.saves)
                self.selected_slot = min(max_slot, self.selected_slot + 1)
                # Scroll if needed
                if self.selected_slot >= self.scroll_offset + self.visible_slots:
                    self.scroll_offset = self.selected_slot - self.visible_slots + 1
                return True
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                return self._do_action(game)
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            
            # Check if clicked outside panel
            panel_rect = pygame.Rect(self.panel_x, self.panel_y, 
                                     self.panel_width, self.panel_height)
            if not panel_rect.collidepoint(mx, my):
                self.hide()
                return True
            
            # Check save slot clicks
            slot_start_y = self.panel_y + 70
            slot_height = 38
            
            for i in range(self.visible_slots):
                slot_idx = i + self.scroll_offset
                slot_y = slot_start_y + i * slot_height
                slot_rect = pygame.Rect(self.panel_x + 15, slot_y, 
                                        self.panel_width - 30, slot_height - 4)
                
                if slot_rect.collidepoint(mx, my):
                    self.selected_slot = slot_idx
                    if event.button == 1:  # Left click - select
                        pass  # Just select
                    return True
            
            # Check action button
            btn_rect = pygame.Rect(self.panel_x + self.panel_width - 120,
                                   self.panel_y + self.panel_height - 50,
                                   100, 35)
            if btn_rect.collidepoint(mx, my):
                return self._do_action(game)
        
        elif event.type == pygame.MOUSEWHEEL:
            self.scroll_offset = max(0, min(len(self.saves) - self.visible_slots,
                                           self.scroll_offset - event.y))
            return True
        
        return True  # Consume all events when menu is open
    
    def _do_action(self, game):
        """Perform save or load action."""
        if self.mode == 'save':
            # Save to new slot
            slot = self.get_next_slot()
            save_game(game, slot)
            game.add_notification(f"Game saved to slot {slot}!", (100, 255, 100))
            self.hide()
            return True
        else:
            # Load selected save
            if self.selected_slot < len(self.saves):
                save_info = self.saves[self.selected_slot]
                if load_game(game, save_info['slot']):
                    game.add_notification(f"Loaded save from {save_info['slot']}!", (100, 200, 255))
                    self.hide()
                    return True
                else:
                    game.add_notification("Failed to load save!", (255, 100, 100))
        return True
    
    def render(self, screen):
        """Render the save/load menu."""
        if not self.visible:
            return
        
        # Darken background
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))
        
        # Main panel
        panel_rect = pygame.Rect(self.panel_x, self.panel_y, 
                                 self.panel_width, self.panel_height)
        pygame.draw.rect(screen, self.bg_color, panel_rect, border_radius=8)
        pygame.draw.rect(screen, self.border_color, panel_rect, 3, border_radius=8)
        
        # Title
        title_text = "LOAD GAME" if self.mode == 'load' else "SAVE GAME"
        title = self.font_title.render(title_text, True, self.text_color)
        title_rect = title.get_rect(centerx=self.panel_x + self.panel_width // 2,
                                    y=self.panel_y + 15)
        screen.blit(title, title_rect)
        
        # Save slots
        slot_start_y = self.panel_y + 70
        slot_height = 38
        
        if not self.saves and self.mode == 'load':
            # No saves message
            no_saves = self.font.render("No saves found", True, self.dim_color)
            screen.blit(no_saves, (self.panel_x + 20, slot_start_y))
        else:
            for i in range(self.visible_slots):
                slot_idx = i + self.scroll_offset
                
                if slot_idx >= len(self.saves):
                    break
                
                save_info = self.saves[slot_idx]
                slot_y = slot_start_y + i * slot_height
                
                # Slot background
                slot_rect = pygame.Rect(self.panel_x + 15, slot_y, 
                                        self.panel_width - 30, slot_height - 4)
                
                if slot_idx == self.selected_slot:
                    pygame.draw.rect(screen, self.selected_color, slot_rect, border_radius=4)
                else:
                    pygame.draw.rect(screen, self.highlight_color, slot_rect, border_radius=4)
                
                # Slot info
                # Parse timestamp
                try:
                    ts = datetime.fromisoformat(save_info['timestamp'])
                    time_str = ts.strftime("%m/%d %H:%M")
                except:
                    time_str = "Unknown"
                
                # Main text
                main_text = f"Slot {save_info['slot']}: {save_info['main_char']} Lv{save_info['main_level']}"
                main_surf = self.font.render(main_text, True, self.text_color)
                screen.blit(main_surf, (slot_rect.x + 10, slot_rect.y + 4))
                
                # Sub text
                sub_text = f"Floor {save_info['dungeon_level']} | {time_str}"
                sub_surf = self.font_small.render(sub_text, True, self.dim_color)
                screen.blit(sub_surf, (slot_rect.x + 10, slot_rect.y + 22))
                
                # Version badge
                version = save_info.get('game_version', 'v?')
                ver_surf = self.font_small.render(version, True, self.dim_color)
                screen.blit(ver_surf, (slot_rect.right - ver_surf.get_width() - 10, slot_rect.y + 10))
        
        # Scroll indicators
        if self.scroll_offset > 0:
            up_text = self.font_small.render("▲ More", True, self.dim_color)
            screen.blit(up_text, (self.panel_x + self.panel_width // 2 - 25, slot_start_y - 18))
        
        if self.scroll_offset + self.visible_slots < len(self.saves):
            down_text = self.font_small.render("▼ More", True, self.dim_color)
            screen.blit(down_text, (self.panel_x + self.panel_width // 2 - 25, 
                                    slot_start_y + self.visible_slots * slot_height))
        
        # Action button
        btn_rect = pygame.Rect(self.panel_x + self.panel_width - 120,
                               self.panel_y + self.panel_height - 50,
                               100, 35)
        
        btn_text = "Load" if self.mode == 'load' else "Save New"
        btn_color = (80, 120, 80) if self.mode == 'load' else (80, 80, 120)
        
        can_act = (self.mode == 'save') or (self.mode == 'load' and self.saves)
        if not can_act:
            btn_color = (60, 60, 60)
        
        pygame.draw.rect(screen, btn_color, btn_rect, border_radius=4)
        pygame.draw.rect(screen, self.border_color, btn_rect, 2, border_radius=4)
        
        btn_surf = self.font.render(btn_text, True, self.text_color if can_act else self.dim_color)
        btn_text_rect = btn_surf.get_rect(center=btn_rect.center)
        screen.blit(btn_surf, btn_text_rect)
        
        # Cancel button
        cancel_rect = pygame.Rect(self.panel_x + 20,
                                  self.panel_y + self.panel_height - 50,
                                  80, 35)
        pygame.draw.rect(screen, (80, 60, 60), cancel_rect, border_radius=4)
        pygame.draw.rect(screen, self.border_color, cancel_rect, 2, border_radius=4)
        
        cancel_surf = self.font.render("Cancel", True, self.text_color)
        cancel_text_rect = cancel_surf.get_rect(center=cancel_rect.center)
        screen.blit(cancel_surf, cancel_text_rect)
        
        # Instructions
        if self.mode == 'load':
            hint = "↑↓ Select | Enter to Load | ESC to Cancel"
        else:
            hint = "Press Enter or click Save New to create a save"
        hint_surf = self.font_small.render(hint, True, self.dim_color)
        hint_rect = hint_surf.get_rect(centerx=self.panel_x + self.panel_width // 2,
                                       y=self.panel_y + self.panel_height - 20)
        screen.blit(hint_surf, hint_rect)

