"""Spell-specific icons drawn procedurally."""

import pygame
import math


def draw_spell_icon(surface, spell_id, rect, color):
    """Draw a recognizable icon for a spell."""
    cx, cy = rect.centerx, rect.centery
    size = min(rect.width, rect.height) - 8
    half = size // 2
    
    if spell_id == 'fireball':
        _draw_fireball(surface, cx, cy, half, color)
    elif spell_id == 'ice_shard':
        _draw_ice_shard(surface, cx, cy, half, color)
    elif spell_id == 'lightning_bolt':
        _draw_lightning(surface, cx, cy, half, color)
    elif spell_id == 'chain_lightning':
        _draw_chain_lightning(surface, cx, cy, half, color)
    elif spell_id == 'heal':
        _draw_heal(surface, cx, cy, half, color)
    elif spell_id == 'group_heal':
        _draw_group_heal(surface, cx, cy, half, color)
    elif spell_id == 'revive':
        _draw_revive(surface, cx, cy, half, color)
    elif spell_id == 'meteor':
        _draw_meteor(surface, cx, cy, half, color)
    elif spell_id == 'poison_cloud':
        _draw_poison(surface, cx, cy, half, color)
    elif spell_id == 'entangle':
        _draw_entangle(surface, cx, cy, half, color)
    elif spell_id == 'inferno':
        _draw_inferno(surface, cx, cy, half, color)
    elif spell_id == 'blizzard':
        _draw_blizzard(surface, cx, cy, half, color)
    elif spell_id == 'armageddon':
        _draw_armageddon(surface, cx, cy, half, color)
    elif spell_id == 'sanctuary':
        _draw_sanctuary(surface, cx, cy, half, color)
    elif spell_id == 'regeneration':
        _draw_regeneration(surface, cx, cy, half, color)
    elif spell_id == 'summon_wolf':
        _draw_summon_wolf(surface, cx, cy, half, color)
    else:
        # Generic magic orb
        _draw_magic_orb(surface, cx, cy, half, color)


def _draw_fireball(surface, cx, cy, half, color):
    """Flame icon - orange/red fire."""
    # Main flame
    flame_color = (255, 120, 30)
    points = [
        (cx, cy - half),           # Top
        (cx + half//2, cy - half//3),
        (cx + half//3, cy + half//2),
        (cx, cy + half//3),
        (cx - half//3, cy + half//2),
        (cx - half//2, cy - half//3),
    ]
    pygame.draw.polygon(surface, flame_color, points)
    
    # Inner flame
    inner_color = (255, 220, 100)
    inner_points = [
        (cx, cy - half//2),
        (cx + half//4, cy),
        (cx, cy + half//4),
        (cx - half//4, cy),
    ]
    pygame.draw.polygon(surface, inner_color, inner_points)


def _draw_ice_shard(surface, cx, cy, half, color):
    """Crystal/shard icon - blue icicle."""
    ice_color = (150, 220, 255)
    # Main shard pointing up
    points = [
        (cx, cy - half),           # Top point
        (cx + half//3, cy + half//4),
        (cx, cy + half//2),
        (cx - half//3, cy + half//4),
    ]
    pygame.draw.polygon(surface, ice_color, points)
    pygame.draw.polygon(surface, (200, 240, 255), points, 1)
    
    # Smaller side shards
    left_shard = [
        (cx - half//2, cy - half//3),
        (cx - half//4, cy),
        (cx - half//3, cy + half//4),
    ]
    pygame.draw.polygon(surface, ice_color, left_shard)
    
    right_shard = [
        (cx + half//2, cy - half//3),
        (cx + half//4, cy),
        (cx + half//3, cy + half//4),
    ]
    pygame.draw.polygon(surface, ice_color, right_shard)


def _draw_lightning(surface, cx, cy, half, color):
    """Lightning bolt icon - jagged yellow bolt."""
    bolt_color = (255, 255, 100)
    points = [
        (cx + half//4, cy - half),    # Top
        (cx - half//6, cy - half//4),
        (cx + half//4, cy - half//6),
        (cx - half//4, cy + half//2),
        (cx, cy + half//4),
        (cx + half//6, cy),
        (cx - half//4, cy - half//3),
        (cx + half//6, cy - half//2),
    ]
    pygame.draw.polygon(surface, bolt_color, points)
    pygame.draw.polygon(surface, (255, 255, 200), points, 1)


def _draw_chain_lightning(surface, cx, cy, half, color):
    """Multiple lightning bolts branching."""
    bolt_color = (180, 180, 255)
    # Main bolt
    pygame.draw.line(surface, bolt_color, (cx, cy - half), (cx - half//4, cy - half//3), 2)
    pygame.draw.line(surface, bolt_color, (cx - half//4, cy - half//3), (cx + half//4, cy), 2)
    pygame.draw.line(surface, bolt_color, (cx + half//4, cy), (cx - half//4, cy + half//2), 2)
    
    # Branch 1
    pygame.draw.line(surface, (200, 200, 255), (cx - half//4, cy - half//3), (cx - half//2, cy), 2)
    pygame.draw.line(surface, (200, 200, 255), (cx - half//2, cy), (cx - half//3, cy + half//3), 2)
    
    # Branch 2
    pygame.draw.line(surface, (200, 200, 255), (cx + half//4, cy), (cx + half//2, cy + half//4), 2)
    
    # Spark dots
    pygame.draw.circle(surface, (255, 255, 255), (cx - half//3, cy + half//3), 2)
    pygame.draw.circle(surface, (255, 255, 255), (cx + half//2, cy + half//4), 2)
    pygame.draw.circle(surface, (255, 255, 255), (cx - half//4, cy + half//2), 2)


def _draw_heal(surface, cx, cy, half, color):
    """Plus/cross icon - green healing."""
    heal_color = (100, 255, 100)
    bar_width = half // 2
    
    # Vertical bar
    pygame.draw.rect(surface, heal_color, 
                     (cx - bar_width//2, cy - half, bar_width, half * 2))
    # Horizontal bar
    pygame.draw.rect(surface, heal_color,
                     (cx - half, cy - bar_width//2, half * 2, bar_width))
    
    # Glow effect
    pygame.draw.rect(surface, (150, 255, 150),
                     (cx - bar_width//2, cy - half, bar_width, half * 2), 1)


def _draw_group_heal(surface, cx, cy, half, color):
    """Multiple plus signs - group heal."""
    heal_color = (100, 255, 100)
    
    # Central cross
    bar = half // 3
    pygame.draw.rect(surface, heal_color, (cx - bar//2, cy - half//2, bar, half))
    pygame.draw.rect(surface, heal_color, (cx - half//2, cy - bar//2, half, bar))
    
    # Surrounding smaller crosses
    for ox, oy in [(-half//2, -half//2), (half//2, -half//2), 
                   (-half//2, half//2), (half//2, half//2)]:
        small = bar // 2
        pygame.draw.rect(surface, (150, 255, 150), 
                        (cx + ox - small//2, cy + oy - small, small, small*2))
        pygame.draw.rect(surface, (150, 255, 150),
                        (cx + ox - small, cy + oy - small//2, small*2, small))


def _draw_revive(surface, cx, cy, half, color):
    """Upward arrow with sparkles - resurrection."""
    rev_color = (200, 255, 255)
    
    # Upward arrow
    arrow_points = [
        (cx, cy - half),           # Top
        (cx + half//2, cy),
        (cx + half//4, cy),
        (cx + half//4, cy + half//2),
        (cx - half//4, cy + half//2),
        (cx - half//4, cy),
        (cx - half//2, cy),
    ]
    pygame.draw.polygon(surface, rev_color, arrow_points)
    
    # Sparkles
    pygame.draw.circle(surface, (255, 255, 255), (cx - half//2, cy - half//3), 2)
    pygame.draw.circle(surface, (255, 255, 255), (cx + half//2, cy - half//3), 2)
    pygame.draw.circle(surface, (255, 255, 200), (cx, cy - half + 3), 2)


def _draw_meteor(surface, cx, cy, half, color):
    """Falling rock with fire trail."""
    # Rock
    rock_color = (120, 80, 60)
    pygame.draw.circle(surface, rock_color, (cx, cy + half//4), half//2)
    pygame.draw.circle(surface, (80, 50, 40), (cx, cy + half//4), half//2, 1)
    
    # Fire trail
    trail_color = (255, 150, 50)
    trail_points = [
        (cx - half//3, cy),
        (cx, cy - half),
        (cx + half//3, cy),
        (cx, cy + half//4),
    ]
    pygame.draw.polygon(surface, trail_color, trail_points)


def _draw_poison(surface, cx, cy, half, color):
    """Skull or toxic cloud."""
    poison_color = (120, 200, 80)
    
    # Cloud puffs
    pygame.draw.circle(surface, poison_color, (cx, cy), half//2)
    pygame.draw.circle(surface, poison_color, (cx - half//3, cy + half//4), half//3)
    pygame.draw.circle(surface, poison_color, (cx + half//3, cy + half//4), half//3)
    pygame.draw.circle(surface, poison_color, (cx, cy - half//3), half//3)
    
    # Skull hint (eyes)
    pygame.draw.circle(surface, (60, 60, 60), (cx - half//6, cy - half//8), 3)
    pygame.draw.circle(surface, (60, 60, 60), (cx + half//6, cy - half//8), 3)


def _draw_entangle(surface, cx, cy, half, color):
    """Vines/roots."""
    vine_color = (80, 160, 60)
    
    # Curving vines
    for angle_offset in [0, 120, 240]:
        angle = math.radians(angle_offset)
        for t in range(5):
            t_norm = t / 5
            x = cx + math.cos(angle + t_norm * 2) * half * t_norm
            y = cy + math.sin(angle + t_norm * 2) * half * t_norm - half//3
            pygame.draw.circle(surface, vine_color, (int(x), int(y)), 3 - t//2)


def _draw_magic_orb(surface, cx, cy, half, color):
    """Generic magic orb."""
    pygame.draw.circle(surface, color, (cx, cy), half//2)
    pygame.draw.circle(surface, (255, 255, 255, 100), (cx - half//6, cy - half//6), half//6)


def _draw_inferno(surface, cx, cy, half, color):
    """Large explosive fire - bigger fireball with explosion lines."""
    # Multiple fire layers
    pygame.draw.circle(surface, (255, 50, 0), (cx, cy), half * 2 // 3)
    pygame.draw.circle(surface, (255, 150, 0), (cx, cy), half // 2)
    pygame.draw.circle(surface, (255, 255, 100), (cx, cy), half // 4)
    
    # Explosion rays
    for angle in range(0, 360, 45):
        rad = math.radians(angle)
        ex = cx + int(math.cos(rad) * half)
        ey = cy + int(math.sin(rad) * half)
        pygame.draw.line(surface, (255, 100, 0), (cx, cy), (ex, ey), 2)


def _draw_blizzard(surface, cx, cy, half, color):
    """Swirling ice storm."""
    # Central swirl
    ice_color = (180, 220, 255)
    for i in range(3):
        angle = i * 120
        for t in range(4):
            rad = math.radians(angle + t * 30)
            dist = half * (t + 1) // 4
            x = cx + int(math.cos(rad) * dist)
            y = cy + int(math.sin(rad) * dist)
            pygame.draw.circle(surface, ice_color, (x, y), 3 - t // 2)
    
    # Snowflakes
    pygame.draw.circle(surface, (255, 255, 255), (cx, cy), 3)
    pygame.draw.circle(surface, (200, 240, 255), (cx - half//2, cy - half//3), 2)
    pygame.draw.circle(surface, (200, 240, 255), (cx + half//2, cy + half//4), 2)


def _draw_armageddon(surface, cx, cy, half, color):
    """Rain of fire - multiple meteors."""
    # Multiple small meteors
    meteor_positions = [
        (cx - half//3, cy - half//3),
        (cx + half//3, cy - half//4),
        (cx, cy + half//4),
    ]
    
    for mx, my in meteor_positions:
        # Fire trail
        pygame.draw.polygon(surface, (255, 100, 0), [
            (mx, my - half//3),
            (mx - half//6, my),
            (mx + half//6, my),
        ])
        # Rock
        pygame.draw.circle(surface, (100, 60, 40), (mx, my), half//4)
    
    # Central explosion
    pygame.draw.circle(surface, (255, 200, 0), (cx, cy), half//3)


def _draw_sanctuary(surface, cx, cy, half, color):
    """Holy dome of protection."""
    # Dome outline
    pygame.draw.arc(surface, (255, 255, 200), 
                   (cx - half, cy - half//2, half * 2, half * 2),
                   math.pi, 2 * math.pi, 3)
    
    # Ground line
    pygame.draw.line(surface, (255, 255, 200), 
                    (cx - half, cy + half//2), (cx + half, cy + half//2), 2)
    
    # Holy cross inside
    pygame.draw.line(surface, (255, 255, 150), (cx, cy - half//3), (cx, cy + half//3), 2)
    pygame.draw.line(surface, (255, 255, 150), (cx - half//3, cy), (cx + half//3, cy), 2)
    
    # Sparkles
    for angle in [45, 135, 225, 315]:
        rad = math.radians(angle)
        sx = cx + int(math.cos(rad) * half * 2 // 3)
        sy = cy - half//4 + int(math.sin(rad) * half // 3)
        pygame.draw.circle(surface, (255, 255, 255), (sx, sy), 2)


def _draw_regeneration(surface, cx, cy, half, color):
    """Healing over time - pulsing hearts/waves."""
    heal_color = (100, 220, 100)
    
    # Pulsing waves outward
    for i, radius in enumerate([half//4, half//2, half * 3 // 4]):
        alpha = 255 - i * 60
        pygame.draw.circle(surface, heal_color, (cx, cy), radius, 2)
    
    # Plus in center
    bar = half // 4
    pygame.draw.rect(surface, (150, 255, 150), (cx - bar//2, cy - bar, bar, bar * 2))
    pygame.draw.rect(surface, (150, 255, 150), (cx - bar, cy - bar//2, bar * 2, bar))


def _draw_summon_wolf(surface, cx, cy, half, color):
    """Wolf head icon."""
    wolf_color = (120, 110, 100)
    
    # Head
    pygame.draw.ellipse(surface, wolf_color, 
                       (cx - half//2, cy - half//3, half, half * 2 // 3))
    
    # Ears
    ear_points_l = [(cx - half//3, cy - half//3), (cx - half//2, cy - half), (cx - half//6, cy - half//3)]
    ear_points_r = [(cx + half//3, cy - half//3), (cx + half//2, cy - half), (cx + half//6, cy - half//3)]
    pygame.draw.polygon(surface, wolf_color, ear_points_l)
    pygame.draw.polygon(surface, wolf_color, ear_points_r)
    
    # Eyes
    pygame.draw.circle(surface, (200, 200, 100), (cx - half//4, cy - half//6), 3)
    pygame.draw.circle(surface, (200, 200, 100), (cx + half//4, cy - half//6), 3)
    
    # Snout
    pygame.draw.ellipse(surface, (100, 90, 80), 
                       (cx - half//4, cy, half//2, half//3))

