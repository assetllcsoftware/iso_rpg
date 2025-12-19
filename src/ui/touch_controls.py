"""Touch and mouse input handling for mobile."""

import pygame
import time
from ..engine.constants import SCREEN_WIDTH, SCREEN_HEIGHT


class TouchControls:
    """Handle touch/mouse input for mobile gameplay."""
    
    def __init__(self):
        self.touch_start = None
        self.touch_start_time = 0
        self.last_tap_time = 0
        self.last_tap_pos = None
        
        # Thresholds
        self.tap_threshold = 0.3  # Max time for a tap
        self.double_tap_threshold = 0.4  # Max time between taps
        self.drag_threshold = 10  # Min pixels for drag
        self.hold_threshold = 0.5  # Time for hold
        
        # Current state
        self.is_dragging = False
        self.is_holding = False
        self.drag_start = None
        
        # Virtual joystick (optional)
        self.joystick_active = False
        self.joystick_pos = None
        self.joystick_center = None
        self.joystick_radius = 60
    
    def handle_event(self, event):
        """Process input event and return action."""
        if event.type == pygame.MOUSEBUTTONDOWN:
            return self._handle_touch_start(event.pos, event.button)
        
        elif event.type == pygame.MOUSEBUTTONUP:
            return self._handle_touch_end(event.pos, event.button)
        
        elif event.type == pygame.MOUSEMOTION:
            return self._handle_touch_move(event.pos, event.buttons)
        
        elif event.type == pygame.MOUSEWHEEL:
            return {'action': 'zoom', 'delta': event.y * 0.1}
        
        return None
    
    def _handle_touch_start(self, pos, button):
        """Handle touch/click start."""
        current_time = time.time()
        
        self.touch_start = pos
        self.touch_start_time = current_time
        self.is_dragging = False
        self.is_holding = False
        
        # Check for double tap
        if (self.last_tap_pos and 
            current_time - self.last_tap_time < self.double_tap_threshold):
            dist = ((pos[0] - self.last_tap_pos[0])**2 + 
                   (pos[1] - self.last_tap_pos[1])**2) ** 0.5
            if dist < 30:
                self.last_tap_time = 0
                self.last_tap_pos = None
                return {'action': 'double_tap', 'pos': pos, 'button': button}
        
        # Right click for camera drag
        if button == 3:
            return {'action': 'camera_drag_start', 'pos': pos}
        
        return None
    
    def _handle_touch_end(self, pos, button):
        """Handle touch/click end."""
        if not self.touch_start:
            return None
        
        current_time = time.time()
        elapsed = current_time - self.touch_start_time
        
        # Calculate distance moved
        dist = ((pos[0] - self.touch_start[0])**2 + 
               (pos[1] - self.touch_start[1])**2) ** 0.5
        
        result = None
        
        if button == 3:
            result = {'action': 'camera_drag_end', 'pos': pos}
        elif self.is_dragging:
            result = {'action': 'drag_end', 'pos': pos, 'start': self.touch_start}
        elif self.is_holding:
            result = {'action': 'hold_end', 'pos': pos}
        elif elapsed < self.tap_threshold and dist < self.drag_threshold:
            # It's a tap
            self.last_tap_time = current_time
            self.last_tap_pos = pos
            result = {'action': 'tap', 'pos': pos, 'button': button}
        
        self.touch_start = None
        self.is_dragging = False
        self.is_holding = False
        
        return result
    
    def _handle_touch_move(self, pos, buttons):
        """Handle touch/mouse movement."""
        if not self.touch_start:
            return None
        
        current_time = time.time()
        elapsed = current_time - self.touch_start_time
        
        dist = ((pos[0] - self.touch_start[0])**2 + 
               (pos[1] - self.touch_start[1])**2) ** 0.5
        
        # Right button drag = camera drag
        if buttons[2]:  # Right button
            return {'action': 'camera_drag_move', 'pos': pos}
        
        # Check for drag start
        if dist > self.drag_threshold and not self.is_dragging:
            self.is_dragging = True
            self.drag_start = self.touch_start
            return {'action': 'drag_start', 'pos': pos, 'start': self.touch_start}
        
        # Continue drag
        if self.is_dragging:
            return {'action': 'drag_move', 'pos': pos, 'start': self.touch_start}
        
        # Check for hold
        if elapsed > self.hold_threshold and not self.is_holding:
            self.is_holding = True
            return {'action': 'hold', 'pos': pos}
        
        return None
    
    def update(self, dt):
        """Update touch state (for hold detection during no-move)."""
        if self.touch_start and not self.is_dragging and not self.is_holding:
            elapsed = time.time() - self.touch_start_time
            if elapsed > self.hold_threshold:
                self.is_holding = True
                return {'action': 'hold', 'pos': self.touch_start}
        return None
    
    def get_ui_element_at(self, pos, ui_regions):
        """Check if position is over a UI element."""
        for name, rect in ui_regions.items():
            if rect.collidepoint(pos):
                return name
        return None

