"""Item and spell icons."""

import pygame
import math


def draw_potion_icon(surface, rect, potion_type):
    """Draw a potion bottle icon."""
    cx, cy = rect.centerx, rect.centery
    w, h = rect.width, rect.height
    
    # Colors based on type
    colors = {
        'heal': ((200, 50, 50), (255, 100, 100)),
        'mana': ((50, 50, 200), (100, 100, 255)),
    }
    dark, light = colors.get(potion_type, ((150, 150, 150), (200, 200, 200)))
    
    # Bottle shape
    bottle_w = w * 0.5
    bottle_h = h * 0.6
    
    # Neck
    neck_w = bottle_w * 0.4
    neck_h = h * 0.2
    neck_rect = pygame.Rect(cx - neck_w//2, cy - bottle_h//2 - neck_h//2, neck_w, neck_h)
    pygame.draw.rect(surface, (80, 70, 90), neck_rect)
    
    # Cork
    cork_rect = pygame.Rect(cx - neck_w//2 - 1, cy - bottle_h//2 - neck_h - 2, neck_w + 2, 6)
    pygame.draw.rect(surface, (139, 90, 43), cork_rect)
    
    # Body
    body_rect = pygame.Rect(cx - bottle_w//2, cy - bottle_h//3, bottle_w, bottle_h * 0.7)
    pygame.draw.rect(surface, dark, body_rect, border_radius=4)
    
    # Liquid shine
    shine_rect = pygame.Rect(body_rect.x + 3, body_rect.y + 3, 4, body_rect.height - 6)
    pygame.draw.rect(surface, light, shine_rect)


def draw_sword_icon(surface, rect, rarity_color):
    """Draw a sword icon."""
    cx, cy = rect.centerx, rect.centery
    w, h = rect.width, rect.height
    
    # Blade
    blade_points = [
        (cx, cy - h * 0.4),  # Tip
        (cx + w * 0.12, cy + h * 0.15),  # Right edge
        (cx - w * 0.12, cy + h * 0.15),  # Left edge
    ]
    pygame.draw.polygon(surface, (180, 180, 190), blade_points)
    pygame.draw.polygon(surface, (220, 220, 230), blade_points, 1)
    
    # Guard
    guard_rect = pygame.Rect(cx - w * 0.25, cy + h * 0.1, w * 0.5, h * 0.08)
    pygame.draw.rect(surface, rarity_color, guard_rect)
    
    # Handle
    handle_rect = pygame.Rect(cx - w * 0.08, cy + h * 0.15, w * 0.16, h * 0.25)
    pygame.draw.rect(surface, (80, 50, 30), handle_rect)
    
    # Pommel
    pygame.draw.circle(surface, rarity_color, (cx, int(cy + h * 0.4)), int(w * 0.1))


def draw_bow_icon(surface, rect, rarity_color):
    """Draw a bow icon."""
    cx, cy = rect.centerx, rect.centery
    w, h = rect.width, rect.height
    
    # Bow arc
    arc_rect = pygame.Rect(cx - w * 0.35, cy - h * 0.4, w * 0.5, h * 0.8)
    pygame.draw.arc(surface, (120, 80, 50), arc_rect, -math.pi/2, math.pi/2, 3)
    
    # String
    pygame.draw.line(surface, (200, 200, 200), 
                    (cx + w * 0.1, cy - h * 0.35),
                    (cx + w * 0.1, cy + h * 0.35), 1)
    
    # Arrow
    arrow_y = cy
    pygame.draw.line(surface, (150, 120, 80),
                    (cx - w * 0.1, arrow_y),
                    (cx + w * 0.35, arrow_y), 2)
    # Arrowhead
    pygame.draw.polygon(surface, (180, 180, 180), [
        (cx + w * 0.35, arrow_y),
        (cx + w * 0.25, arrow_y - 4),
        (cx + w * 0.25, arrow_y + 4),
    ])


def draw_staff_icon(surface, rect, rarity_color):
    """Draw a magic staff icon."""
    cx, cy = rect.centerx, rect.centery
    w, h = rect.width, rect.height
    
    # Staff shaft
    pygame.draw.line(surface, (100, 70, 50),
                    (cx, cy - h * 0.35),
                    (cx, cy + h * 0.4), 4)
    
    # Crystal/orb on top
    pygame.draw.circle(surface, rarity_color, (cx, int(cy - h * 0.35)), int(w * 0.18))
    pygame.draw.circle(surface, (255, 255, 255), (cx - 2, int(cy - h * 0.35) - 2), 3)


def draw_armor_icon(surface, rect, slot, rarity_color):
    """Draw armor piece icon based on slot."""
    cx, cy = rect.centerx, rect.centery
    w, h = rect.width, rect.height
    
    if slot == 'head':
        # Helmet
        pygame.draw.arc(surface, rarity_color, 
                       pygame.Rect(cx - w*0.3, cy - h*0.3, w*0.6, h*0.5),
                       0, math.pi, 4)
        pygame.draw.rect(surface, rarity_color,
                        (cx - w*0.3, cy, w*0.6, h*0.2))
    
    elif slot == 'chest':
        # Chestplate
        points = [
            (cx, cy - h * 0.3),
            (cx + w * 0.35, cy - h * 0.15),
            (cx + w * 0.3, cy + h * 0.3),
            (cx, cy + h * 0.35),
            (cx - w * 0.3, cy + h * 0.3),
            (cx - w * 0.35, cy - h * 0.15),
        ]
        pygame.draw.polygon(surface, rarity_color, points)
        pygame.draw.polygon(surface, (255, 255, 255), points, 1)
    
    elif slot == 'feet':
        # Boots
        pygame.draw.ellipse(surface, rarity_color,
                           (cx - w*0.35, cy, w*0.3, h*0.25))
        pygame.draw.ellipse(surface, rarity_color,
                           (cx + w*0.05, cy, w*0.3, h*0.25))
    
    elif slot == 'off_hand':
        # Shield
        points = [
            (cx, cy - h * 0.35),
            (cx + w * 0.3, cy - h * 0.2),
            (cx + w * 0.3, cy + h * 0.15),
            (cx, cy + h * 0.35),
            (cx - w * 0.3, cy + h * 0.15),
            (cx - w * 0.3, cy - h * 0.2),
        ]
        pygame.draw.polygon(surface, rarity_color, points)
        pygame.draw.polygon(surface, (50, 50, 50), points, 2)
    
    else:
        # Generic armor piece
        pygame.draw.rect(surface, rarity_color,
                        (cx - w*0.3, cy - h*0.25, w*0.6, h*0.5),
                        border_radius=3)


def draw_spell_icon(surface, rect, spell_id):
    """Draw a spell icon."""
    cx, cy = rect.centerx, rect.centery
    w, h = rect.width, rect.height
    
    spell_visuals = {
        'fireball': {'color': (255, 100, 50), 'symbol': '🔥'},
        'heal': {'color': (100, 255, 150), 'symbol': '+'},
        'ice_shard': {'color': (150, 200, 255), 'symbol': '❄'},
        'lightning_bolt': {'color': (200, 200, 255), 'symbol': '⚡'},
        'meteor': {'color': (255, 150, 50), 'symbol': '☄'},
        'poison_cloud': {'color': (100, 180, 50), 'symbol': '☠'},
    }
    
    visual = spell_visuals.get(spell_id, {'color': (150, 150, 200), 'symbol': '✦'})
    color = visual['color']
    
    # Glowing circle background
    pygame.draw.circle(surface, color, (cx, cy), int(w * 0.35))
    pygame.draw.circle(surface, (255, 255, 255), (cx, cy), int(w * 0.35), 2)
    
    # Inner glow
    pygame.draw.circle(surface, (255, 255, 255), (cx, cy), int(w * 0.15))


def get_item_icon_surface(item, size=48):
    """Generate an icon surface for an item."""
    surface = pygame.Surface((size, size), pygame.SRCALPHA)
    rect = surface.get_rect()
    
    from ..engine.constants import RARITY_COLORS
    rarity_color = RARITY_COLORS.get(item.rarity, (150, 150, 150))
    
    # Determine item type and draw appropriate icon
    if hasattr(item, 'effect_type'):
        # It's a consumable
        draw_potion_icon(surface, rect, item.effect_type)
    
    elif hasattr(item, 'weapon_type'):
        # It's a weapon
        if item.weapon_type == 'ranged':
            draw_bow_icon(surface, rect, rarity_color)
        elif item.weapon_type == 'magic':
            draw_staff_icon(surface, rect, rarity_color)
        else:
            draw_sword_icon(surface, rect, rarity_color)
    
    elif hasattr(item, 'armor') and item.armor > 0:
        # It's armor
        slot = getattr(item, 'slot', 'chest')
        draw_armor_icon(surface, rect, slot, rarity_color)
    
    else:
        # Generic item
        pygame.draw.rect(surface, rarity_color, rect.inflate(-8, -8), border_radius=4)
    
    return surface

