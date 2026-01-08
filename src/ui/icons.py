"""Procedural icon generation for spells and items."""

import pygame
import math
from typing import Dict, Tuple, Optional


class IconGenerator:
    """Generates procedural icons for spells and items."""
    
    # Spell school colors
    SPELL_COLORS = {
        'fire': [(255, 100, 30), (255, 200, 50), (255, 50, 0)],
        'ice': [(100, 180, 255), (200, 230, 255), (50, 100, 200)],
        'lightning': [(255, 255, 100), (255, 255, 200), (200, 200, 50)],
        'poison': [(100, 200, 80), (150, 255, 100), (50, 150, 30)],
        'nature': [(80, 200, 80), (120, 255, 120), (40, 150, 40)],
        'holy': [(255, 255, 200), (255, 255, 255), (255, 230, 150)],
        'dark': [(80, 50, 100), (120, 80, 150), (50, 30, 60)],
        'physical': [(180, 180, 180), (220, 220, 220), (140, 140, 140)],
        # Melee warrior abilities
        'spin': [(255, 120, 50), (255, 180, 100), (200, 80, 30)],  # Orange/red spin
        'leap': [(100, 200, 255), (150, 230, 255), (60, 150, 200)],  # Sky blue leap
        'crush': [(200, 100, 50), (255, 150, 80), (150, 60, 30)],  # Brown/orange slam
        'shield': [(150, 150, 200), (200, 200, 255), (100, 100, 150)],  # Silver/blue shield
        'warcry': [(255, 200, 50), (255, 255, 100), (200, 150, 30)],  # Gold warcry
    }
    
    # Item type shapes
    ITEM_SHAPES = {
        'sword': 'blade',
        'axe': 'axe_head',
        'staff': 'staff',
        'bow': 'bow',
        'shield': 'shield',
        'helmet': 'helmet',
        'armor': 'chestplate',
        'potion': 'bottle',
        'ring': 'ring',
        'amulet': 'amulet',
    }
    
    def __init__(self, cache_size: int = 100):
        self.cache: Dict[str, pygame.Surface] = {}
        self.cache_size = cache_size
    
    def get_spell_icon(self, spell_id: str, size: int = 40) -> pygame.Surface:
        """Get or generate a spell icon."""
        cache_key = f"spell_{spell_id}_{size}"
        
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        icon = self._generate_spell_icon(spell_id, size)
        self._cache_icon(cache_key, icon)
        return icon
    
    def get_item_icon(self, item_type: str, rarity: int = 0, size: int = 40) -> pygame.Surface:
        """Get or generate an item icon."""
        cache_key = f"item_{item_type}_{rarity}_{size}"
        
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        icon = self._generate_item_icon(item_type, rarity, size)
        self._cache_icon(cache_key, icon)
        return icon
    
    def get_character_portrait(self, character_name: str, size: int = 44) -> pygame.Surface:
        """Get or generate a character portrait icon."""
        cache_key = f"portrait_{character_name}_{size}"
        
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        icon = self._generate_character_portrait(character_name, size)
        self._cache_icon(cache_key, icon)
        return icon
    
    def _generate_character_portrait(self, name: str, size: int) -> pygame.Surface:
        """Generate a character portrait."""
        surface = pygame.Surface((size, size), pygame.SRCALPHA)
        
        name_lower = name.lower()
        
        if 'hero' in name_lower or 'warrior' in name_lower:
            # Hero portrait - warm colors, warrior style
            # Background
            pygame.draw.rect(surface, (60, 45, 35), (0, 0, size, size))
            
            # Face shape (tan skin)
            cx, cy = size // 2, size // 2
            pygame.draw.ellipse(surface, (200, 160, 120), (size//4, size//6, size//2, size*2//3))
            
            # Hair (dark)
            pygame.draw.ellipse(surface, (50, 35, 25), (size//4, size//8, size//2, size//3))
            
            # Eyes
            eye_y = cy - size//10
            pygame.draw.circle(surface, (40, 30, 20), (cx - size//8, eye_y), size//12)
            pygame.draw.circle(surface, (40, 30, 20), (cx + size//8, eye_y), size//12)
            pygame.draw.circle(surface, (255, 255, 255), (cx - size//8, eye_y), size//16)
            pygame.draw.circle(surface, (255, 255, 255), (cx + size//8, eye_y), size//16)
            
            # Helmet/headband (gold)
            pygame.draw.rect(surface, (200, 160, 50), (size//6, size//5, size*2//3, size//8))
            pygame.draw.rect(surface, (150, 120, 40), (size//6, size//5, size*2//3, size//8), 1)
            
            # Border
            pygame.draw.rect(surface, (180, 140, 60), (0, 0, size, size), 2)
            
        elif 'lyra' in name_lower or 'mage' in name_lower:
            # Lyra portrait - cool colors, mystic style
            # Background
            pygame.draw.rect(surface, (40, 35, 60), (0, 0, size, size))
            
            # Face shape (lighter skin)
            cx, cy = size // 2, size // 2
            pygame.draw.ellipse(surface, (220, 180, 150), (size//4, size//6, size//2, size*2//3))
            
            # Hair (golden blonde)
            pygame.draw.ellipse(surface, (220, 180, 100), (size//5, size//8, size*3//5, size//2))
            pygame.draw.ellipse(surface, (200, 160, 80), (size//4, size//10, size//2, size//3))
            
            # Eyes (blue-ish)
            eye_y = cy - size//10
            pygame.draw.circle(surface, (60, 100, 150), (cx - size//8, eye_y), size//10)
            pygame.draw.circle(surface, (60, 100, 150), (cx + size//8, eye_y), size//10)
            pygame.draw.circle(surface, (150, 200, 255), (cx - size//8, eye_y), size//16)
            pygame.draw.circle(surface, (150, 200, 255), (cx + size//8, eye_y), size//16)
            
            # Headpiece (blue gem)
            pygame.draw.circle(surface, (100, 150, 220), (cx, size//5), size//8)
            pygame.draw.circle(surface, (150, 200, 255), (cx - 1, size//5 - 1), size//12)
            
            # Border
            pygame.draw.rect(surface, (100, 80, 160), (0, 0, size, size), 2)
            
        else:
            # Generic portrait
            pygame.draw.rect(surface, (50, 50, 50), (0, 0, size, size))
            pygame.draw.ellipse(surface, (150, 130, 110), (size//4, size//5, size//2, size*3//5))
            pygame.draw.rect(surface, (80, 80, 80), (0, 0, size, size), 2)
        
        return surface
    
    def _cache_icon(self, key: str, icon: pygame.Surface):
        """Add icon to cache, evicting old entries if necessary."""
        if len(self.cache) >= self.cache_size:
            # Remove oldest entry (first in dict)
            oldest = next(iter(self.cache))
            del self.cache[oldest]
        self.cache[key] = icon
    
    def _generate_spell_icon(self, spell_id: str, size: int) -> pygame.Surface:
        """Generate a spell icon based on spell type."""
        surface = pygame.Surface((size, size), pygame.SRCALPHA)
        center = size // 2
        
        # Determine spell type from id
        spell_type = self._determine_spell_type(spell_id)
        colors = self.SPELL_COLORS.get(spell_type, self.SPELL_COLORS['physical'])
        
        # Background circle
        pygame.draw.circle(surface, (30, 25, 40), (center, center), size // 2 - 2)
        
        # Draw spell effect based on type
        if spell_type == 'fire':
            self._draw_fire_effect(surface, center, size, colors)
        elif spell_type == 'ice':
            self._draw_ice_effect(surface, center, size, colors)
        elif spell_type == 'lightning':
            self._draw_lightning_effect(surface, center, size, colors)
        elif spell_type == 'poison':
            self._draw_poison_effect(surface, center, size, colors)
        elif spell_type == 'nature':
            self._draw_heal_effect(surface, center, size, colors)
        elif spell_type == 'spin':
            self._draw_spin_effect(surface, center, size, colors)
        elif spell_type == 'leap':
            self._draw_leap_effect(surface, center, size, colors)
        elif spell_type == 'crush':
            self._draw_crush_effect(surface, center, size, colors)
        elif spell_type == 'shield':
            self._draw_shield_effect(surface, center, size, colors)
        elif spell_type == 'warcry':
            self._draw_warcry_effect(surface, center, size, colors)
        else:
            self._draw_generic_effect(surface, center, size, colors)
        
        # Border
        pygame.draw.circle(surface, colors[2], (center, center), size // 2 - 1, 2)
        
        return surface
    
    def _determine_spell_type(self, spell_id: str) -> str:
        """Determine spell type from spell ID."""
        spell_id = spell_id.lower()
        
        if any(w in spell_id for w in ['fire', 'flame', 'inferno', 'meteor', 'burn']):
            return 'fire'
        elif any(w in spell_id for w in ['ice', 'frost', 'blizzard', 'cold', 'freeze', 'shard']):
            return 'ice'
        elif any(w in spell_id for w in ['lightning', 'thunder', 'shock', 'bolt', 'chain']):
            return 'lightning'
        elif any(w in spell_id for w in ['poison', 'venom', 'toxic', 'acid']):
            return 'poison'
        elif any(w in spell_id for w in ['heal', 'life', 'revive', 'regen', 'nature']):
            return 'nature'
        elif any(w in spell_id for w in ['holy', 'light', 'divine', 'smite']):
            return 'holy'
        elif any(w in spell_id for w in ['dark', 'shadow', 'death', 'curse']):
            return 'dark'
        elif any(w in spell_id for w in ['whirl', 'spin', 'wind']):
            return 'spin'
        elif any(w in spell_id for w in ['leap', 'jump', 'strike']):
            return 'leap'
        elif any(w in spell_id for w in ['crush', 'heavy', 'smash', 'slam']):
            return 'crush'
        elif any(w in spell_id for w in ['bash', 'shield', 'block']):
            return 'shield'
        elif any(w in spell_id for w in ['cry', 'shout', 'roar', 'battle']):
            return 'warcry'
        else:
            return 'physical'
    
    def _draw_fire_effect(self, surface, center, size, colors):
        """Draw fire spell effect."""
        # Flame shape
        flame_points = []
        for i in range(5):
            angle = math.pi / 2 + i * math.pi * 2 / 5
            inner_angle = angle + math.pi / 5
            
            outer_r = size // 3
            inner_r = size // 5
            
            flame_points.append((
                center + int(math.cos(angle) * outer_r),
                center - int(math.sin(angle) * outer_r)
            ))
            flame_points.append((
                center + int(math.cos(inner_angle) * inner_r),
                center - int(math.sin(inner_angle) * inner_r)
            ))
        
        pygame.draw.polygon(surface, colors[0], flame_points)
        
        # Inner glow
        pygame.draw.circle(surface, colors[1], (center, center), size // 6)
    
    def _draw_ice_effect(self, surface, center, size, colors):
        """Draw ice spell effect."""
        # Crystal/snowflake shape
        for i in range(6):
            angle = i * math.pi / 3
            end_x = center + int(math.cos(angle) * size // 3)
            end_y = center + int(math.sin(angle) * size // 3)
            pygame.draw.line(surface, colors[0], (center, center), (end_x, end_y), 3)
            
            # Crystal branches
            for offset in [-math.pi/6, math.pi/6]:
                branch_angle = angle + offset
                mid_x = center + int(math.cos(angle) * size // 5)
                mid_y = center + int(math.sin(angle) * size // 5)
                branch_end_x = mid_x + int(math.cos(branch_angle) * size // 8)
                branch_end_y = mid_y + int(math.sin(branch_angle) * size // 8)
                pygame.draw.line(surface, colors[1], (mid_x, mid_y), (branch_end_x, branch_end_y), 2)
        
        # Center
        pygame.draw.circle(surface, colors[1], (center, center), size // 8)
    
    def _draw_lightning_effect(self, surface, center, size, colors):
        """Draw lightning spell effect."""
        # Zigzag bolt
        points = [
            (center - 3, center - size // 3),
            (center + 5, center - size // 8),
            (center - 2, center),
            (center + 8, center + size // 8),
            (center, center + size // 3),
            (center - 4, center),
            (center + 2, center - size // 8),
            (center - 3, center - size // 3),
        ]
        pygame.draw.polygon(surface, colors[0], points)
        
        # Glow
        inner_points = [
            (center, center - size // 4),
            (center + 3, center),
            (center, center + size // 4),
            (center - 3, center),
        ]
        pygame.draw.polygon(surface, colors[1], inner_points)
    
    def _draw_poison_effect(self, surface, center, size, colors):
        """Draw poison spell effect."""
        # Skull-like shape (simplified)
        pygame.draw.circle(surface, colors[0], (center, center - 2), size // 4)
        pygame.draw.circle(surface, colors[1], (center, center + size // 6), size // 5)
        
        # Droplets
        for i in range(3):
            x = center - size // 5 + i * size // 5
            pygame.draw.circle(surface, colors[0], (x, center + size // 4), 3)
    
    def _draw_heal_effect(self, surface, center, size, colors):
        """Draw heal/nature spell effect."""
        # Cross/plus shape
        bar_width = size // 5
        bar_length = size // 3
        
        # Horizontal
        pygame.draw.rect(surface, colors[0],
                        (center - bar_length, center - bar_width // 2,
                         bar_length * 2, bar_width), border_radius=2)
        # Vertical
        pygame.draw.rect(surface, colors[0],
                        (center - bar_width // 2, center - bar_length,
                         bar_width, bar_length * 2), border_radius=2)
        
        # Glow
        pygame.draw.circle(surface, colors[1], (center, center), size // 6)
    
    def _draw_generic_effect(self, surface, center, size, colors):
        """Draw generic spell effect."""
        # Simple star
        pygame.draw.circle(surface, colors[0], (center, center), size // 4)
        for i in range(8):
            angle = i * math.pi / 4
            end_x = center + int(math.cos(angle) * size // 3)
            end_y = center + int(math.sin(angle) * size // 3)
            pygame.draw.line(surface, colors[1], (center, center), (end_x, end_y), 2)
    
    def _draw_spin_effect(self, surface, center, size, colors):
        """Draw whirlwind/spin effect - circular motion lines."""
        # Circular swirl pattern
        for i in range(3):
            angle_start = i * math.pi * 2 / 3
            for j in range(8):
                angle = angle_start + j * 0.15
                r = size // 4 + j * (size // 16)
                x = center + int(math.cos(angle) * r)
                y = center + int(math.sin(angle) * r)
                pygame.draw.circle(surface, colors[0] if j < 4 else colors[1], (x, y), 2)
        # Center blade
        pygame.draw.polygon(surface, colors[1], [
            (center, center - size // 4),
            (center - size // 8, center),
            (center, center + size // 6),
            (center + size // 8, center),
        ])
    
    def _draw_leap_effect(self, surface, center, size, colors):
        """Draw leap strike effect - upward arrow with motion lines."""
        # Upward arrow
        pygame.draw.polygon(surface, colors[0], [
            (center, center - size // 3),
            (center - size // 4, center),
            (center - size // 8, center),
            (center - size // 8, center + size // 4),
            (center + size // 8, center + size // 4),
            (center + size // 8, center),
            (center + size // 4, center),
        ])
        # Motion lines
        for i in range(3):
            y = center + size // 6 + i * 4
            pygame.draw.line(surface, colors[1], (center - size // 6, y), (center + size // 6, y), 1)
    
    def _draw_crush_effect(self, surface, center, size, colors):
        """Draw crushing blow effect - hammer/fist coming down."""
        # Fist/hammer shape
        pygame.draw.rect(surface, colors[0], (center - size // 6, center - size // 4, size // 3, size // 3))
        pygame.draw.rect(surface, colors[1], (center - size // 8, center - size // 5, size // 4, size // 4))
        # Impact lines below
        for i in range(5):
            offset = (i - 2) * size // 8
            pygame.draw.line(surface, colors[2], 
                           (center + offset, center + size // 6),
                           (center + offset * 1.5, center + size // 3), 2)
        # Ground crack
        pygame.draw.line(surface, colors[2], (center - size // 3, center + size // 4), 
                        (center + size // 3, center + size // 4), 2)
    
    def _draw_shield_effect(self, surface, center, size, colors):
        """Draw shield bash effect - shield with impact."""
        # Shield shape
        pygame.draw.polygon(surface, colors[0], [
            (center, center - size // 3),
            (center - size // 3, center - size // 6),
            (center - size // 3, center + size // 6),
            (center, center + size // 3),
            (center + size // 3, center + size // 6),
            (center + size // 3, center - size // 6),
        ])
        # Shield highlight
        pygame.draw.polygon(surface, colors[1], [
            (center, center - size // 4),
            (center - size // 5, center - size // 8),
            (center - size // 5, center + size // 8),
            (center, center + size // 4),
        ])
        # Impact star on right
        for angle in [0, math.pi/4, -math.pi/4]:
            end_x = center + size // 3 + int(math.cos(angle) * size // 6)
            end_y = center + int(math.sin(angle) * size // 6)
            pygame.draw.line(surface, colors[2], (center + size // 3, center), (end_x, end_y), 2)
    
    def _draw_warcry_effect(self, surface, center, size, colors):
        """Draw battle cry effect - sound waves emanating outward."""
        # Mouth/head center
        pygame.draw.circle(surface, colors[0], (center - size // 6, center), size // 6)
        # Sound wave arcs
        for i in range(3):
            r = size // 4 + i * size // 8
            pygame.draw.arc(surface, colors[1], 
                          (center - size // 8 - r, center - r, r * 2, r * 2),
                          -math.pi/3, math.pi/3, 2)
    
    def _generate_item_icon(self, item_type: str, rarity: int, size: int) -> pygame.Surface:
        """Generate an item icon."""
        surface = pygame.Surface((size, size), pygame.SRCALPHA)
        center = size // 2
        
        # Rarity colors
        rarity_colors = [
            (180, 180, 180),  # Common
            (100, 200, 100),  # Uncommon
            (100, 150, 255),  # Rare
            (200, 100, 255),  # Epic
            (255, 200, 50),   # Legendary
        ]
        color = rarity_colors[min(rarity, len(rarity_colors) - 1)]
        
        # Background
        pygame.draw.rect(surface, (30, 25, 40), (2, 2, size - 4, size - 4), border_radius=4)
        
        # Draw item based on type
        item_lower = item_type.lower()
        
        # Weapons - specific types first
        if 'crossbow' in item_lower:
            self._draw_crossbow_icon(surface, center, size, color)
        elif 'bow' in item_lower or 'sling' in item_lower:
            self._draw_bow_icon(surface, center, size, color)
        elif 'dagger' in item_lower:
            self._draw_dagger_icon(surface, center, size, color)
        elif 'scimitar' in item_lower or 'falchion' in item_lower:
            self._draw_scimitar_icon(surface, center, size, color)
        elif 'claymore' in item_lower or 'greatsword' in item_lower:
            self._draw_greatsword_icon(surface, center, size, color)
        elif 'sword' in item_lower or 'blade' in item_lower:
            self._draw_sword_icon(surface, center, size, color)
        elif 'hatchet' in item_lower:
            self._draw_hatchet_icon(surface, center, size, color)
        elif 'axe' in item_lower or 'cleaver' in item_lower:
            self._draw_axe_icon(surface, center, size, color)
        elif 'club' in item_lower:
            self._draw_club_icon(surface, center, size, color)
        elif 'maul' in item_lower or 'hammer' in item_lower:
            self._draw_mace_icon(surface, center, size, color)
        elif 'mace' in item_lower or 'morning_star' in item_lower:
            self._draw_mace_icon(surface, center, size, color)
        elif 'javelin' in item_lower or 'spear' in item_lower:
            self._draw_javelin_icon(surface, center, size, color)
        elif 'throwing' in item_lower:
            self._draw_throwing_icon(surface, center, size, color)
        elif 'staff' in item_lower or 'rod' in item_lower:
            self._draw_staff_icon(surface, center, size, color)
        elif 'wand' in item_lower or 'orb' in item_lower:
            self._draw_wand_icon(surface, center, size, color)
        elif 'conduit' in item_lower:
            self._draw_orb_icon(surface, center, size, color)
        
        # Armor
        elif 'helm' in item_lower or 'visage' in item_lower:
            self._draw_helm_icon(surface, center, size, color)
        elif 'hood' in item_lower or 'coif' in item_lower:
            self._draw_hood_icon(surface, center, size, color)
        elif 'hat' in item_lower or 'cap' in item_lower:
            self._draw_wizardhat_icon(surface, center, size, color)
        elif 'crown' in item_lower or 'circlet' in item_lower:
            self._draw_crown_icon(surface, center, size, color)
        elif 'robe' in item_lower or 'garb' in item_lower:
            self._draw_robe_icon(surface, center, size, color)
        elif 'armor' in item_lower or 'chest' in item_lower or 'plate' in item_lower:
            self._draw_armor_icon(surface, center, size, color)
        elif 'mail' in item_lower or 'chain' in item_lower:
            self._draw_chainmail_icon(surface, center, size, color)
        elif 'leather' in item_lower or 'vest' in item_lower or 'shirt' in item_lower:
            self._draw_leather_icon(surface, center, size, color)
        elif 'shield' in item_lower or 'buckler' in item_lower or 'aegis' in item_lower:
            self._draw_shield_icon(surface, center, size, color)
        elif 'boot' in item_lower or 'shoe' in item_lower:
            self._draw_boots_icon(surface, center, size, color)
        elif 'glove' in item_lower or 'gauntlet' in item_lower:
            self._draw_gloves_icon(surface, center, size, color)
        elif 'legging' in item_lower or 'pant' in item_lower:
            self._draw_leggings_icon(surface, center, size, color)
        
        # Accessories
        elif 'ring' in item_lower:
            self._draw_ring_icon(surface, center, size, color)
        elif 'amulet' in item_lower or 'heart' in item_lower:
            self._draw_amulet_icon(surface, center, size, color)
        
        # Consumables
        elif 'potion' in item_lower or 'elixir' in item_lower:
            self._draw_potion_icon(surface, center, size, color)
        
        # Materials
        elif 'bone' in item_lower:
            self._draw_bone_icon(surface, center, size, color)
        elif 'silk' in item_lower:
            self._draw_silk_icon(surface, center, size, color)
        elif 'gland' in item_lower or 'venom' in item_lower:
            self._draw_gland_icon(surface, center, size, color)
        elif 'flesh' in item_lower:
            self._draw_flesh_icon(surface, center, size, color)
        elif 'heart' in item_lower:
            self._draw_demon_heart_icon(surface, center, size, color)
        elif 'scale' in item_lower:
            self._draw_scale_icon(surface, center, size, color)
        elif 'dust' in item_lower:
            self._draw_dust_icon(surface, center, size, color)
        elif 'essence' in item_lower or 'void' in item_lower:
            self._draw_essence_icon(surface, center, size, color)
        
        else:
            self._draw_generic_item(surface, center, size, color)
        
        # Rarity border
        pygame.draw.rect(surface, color, (0, 0, size, size), 2, border_radius=4)
        
        return surface
    
    def _draw_sword_icon(self, surface, center, size, color):
        """Draw sword item icon - SVG style with gradients and detail."""
        # Shadow under blade
        shadow_points = [
            (center + 2, center - size // 3 + 2),
            (center + size // 8 + 2, center + size // 6 + 2),
            (center + 2, center + size // 5 + 2),
            (center - size // 8 + 2, center + size // 6 + 2),
        ]
        pygame.draw.polygon(surface, (20, 20, 20, 80), shadow_points)
        
        # Main blade
        blade_points = [
            (center, center - size // 3),
            (center + size // 8, center + size // 6),
            (center, center + size // 5),
            (center - size // 8, center + size // 6),
        ]
        pygame.draw.polygon(surface, color, blade_points)
        
        # Blade highlight (left edge)
        highlight = tuple(min(c + 60, 255) for c in color[:3])
        pygame.draw.line(surface, highlight,
                        (center - size // 10, center + size // 8),
                        (center - 1, center - size // 3 + 4), 2)
        
        # Blade edge line
        dark = tuple(max(c - 40, 0) for c in color[:3])
        pygame.draw.line(surface, dark,
                        (center, center - size // 3),
                        (center, center + size // 5), 1)
        
        # Guard with 3D effect
        guard_y = center + size // 6
        pygame.draw.line(surface, (80, 70, 60),
                        (center - size // 4, guard_y + 2),
                        (center + size // 4, guard_y + 2), 4)
        pygame.draw.line(surface, (180, 160, 100),
                        (center - size // 4, guard_y),
                        (center + size // 4, guard_y), 4)
        pygame.draw.line(surface, (220, 200, 140),
                        (center - size // 4, guard_y - 1),
                        (center + size // 4, guard_y - 1), 1)
        
        # Handle with wrap detail
        handle_x = center - 3
        handle_y = guard_y + 3
        handle_h = size // 4
        pygame.draw.rect(surface, (60, 40, 30), (handle_x, handle_y, 7, handle_h))
        # Leather wraps
        for i in range(3):
            wrap_y = handle_y + 3 + i * (handle_h // 4)
            pygame.draw.line(surface, (90, 60, 40), (handle_x, wrap_y), (handle_x + 6, wrap_y), 2)
        
        # Pommel
        pygame.draw.circle(surface, (160, 140, 80), (center, guard_y + handle_h + 5), 4)
        pygame.draw.circle(surface, (200, 180, 120), (center - 1, guard_y + handle_h + 4), 2)
    
    def _draw_potion_icon(self, surface, center, size, color):
        """Draw potion item icon - SVG style with shine."""
        bottle_width = size // 3
        bottle_height = size // 2
        
        # Shadow
        pygame.draw.ellipse(surface, (20, 20, 20, 60),
                           (center - bottle_width // 2 + 2,
                            center - bottle_height // 4 + 2,
                            bottle_width, bottle_height))
        
        # Bottle body (darker base)
        dark_color = tuple(max(c - 50, 0) for c in color[:3])
        pygame.draw.ellipse(surface, dark_color,
                           (center - bottle_width // 2,
                            center - bottle_height // 4,
                            bottle_width, bottle_height))
        
        # Liquid fill (main color)
        pygame.draw.ellipse(surface, color,
                           (center - bottle_width // 2 + 2,
                            center - bottle_height // 4 + bottle_height // 4,
                            bottle_width - 4, bottle_height // 2))
        
        # Glass neck
        neck_width = bottle_width // 2
        neck_x = center - neck_width // 2
        neck_y = center - bottle_height // 2
        neck_h = bottle_height // 3
        pygame.draw.rect(surface, (180, 200, 220), (neck_x, neck_y, neck_width, neck_h))
        pygame.draw.rect(surface, (220, 240, 255), (neck_x + 1, neck_y, 2, neck_h))  # Highlight
        
        # Cork with grain
        cork_y = neck_y - 6
        pygame.draw.rect(surface, (160, 110, 60), (neck_x - 2, cork_y, neck_width + 4, 8), border_radius=2)
        pygame.draw.line(surface, (130, 90, 50), (neck_x, cork_y + 2), (neck_x + neck_width, cork_y + 2), 1)
        pygame.draw.line(surface, (130, 90, 50), (neck_x, cork_y + 5), (neck_x + neck_width, cork_y + 5), 1)
        
        # Shine on bottle
        shine_color = tuple(min(c + 100, 255) for c in color[:3])
        pygame.draw.ellipse(surface, (*shine_color, 150),
                           (center - bottle_width // 4, center, bottle_width // 4, bottle_height // 4))
        
        # Bubbles
        pygame.draw.circle(surface, (255, 255, 255, 180), (center - 3, center + size // 8), 2)
        pygame.draw.circle(surface, (255, 255, 255, 150), (center + 2, center + size // 10), 1)
    
    def _draw_armor_icon(self, surface, center, size, color):
        """Draw armor item icon - SVG style with 3D shading."""
        # Shadow
        shadow_points = [
            (center + 2, center - size // 4 + 2),
            (center + size // 4 + 2, center - size // 6 + 2),
            (center + size // 3 + 2, center + 2),
            (center + size // 5 + 2, center + size // 3 + 2),
            (center + 2, center + size // 4 + 2),
            (center - size // 5 + 2, center + size // 3 + 2),
            (center - size // 3 + 2, center + 2),
            (center - size // 4 + 2, center - size // 6 + 2),
        ]
        pygame.draw.polygon(surface, (20, 20, 20, 80), shadow_points)
        
        # Main armor body
        points = [
            (center, center - size // 4),
            (center + size // 4, center - size // 6),
            (center + size // 3, center),
            (center + size // 5, center + size // 3),
            (center, center + size // 4),
            (center - size // 5, center + size // 3),
            (center - size // 3, center),
            (center - size // 4, center - size // 6),
        ]
        pygame.draw.polygon(surface, color, points)
        
        # Darker right side for depth
        dark = tuple(max(c - 40, 0) for c in color[:3])
        right_points = [
            (center, center - size // 4),
            (center + size // 4, center - size // 6),
            (center + size // 3, center),
            (center + size // 5, center + size // 3),
            (center, center + size // 4),
        ]
        pygame.draw.polygon(surface, dark, right_points)
        
        # Highlight on left chest
        highlight = tuple(min(c + 50, 255) for c in color[:3])
        pygame.draw.polygon(surface, highlight, [
            (center - size // 6, center - size // 6),
            (center - size // 4, center),
            (center - size // 5, center + size // 6),
            (center - size // 10, center),
        ])
        
        # Collar
        pygame.draw.arc(surface, (200, 180, 150),
                       (center - size // 5, center - size // 3,
                        size * 2 // 5, size // 4), 0, math.pi, 3)
        
        # Center line detail
        pygame.draw.line(surface, (100, 90, 80),
                        (center, center - size // 5),
                        (center, center + size // 5), 2)
        
        # Rivets
        for i in range(-1, 2):
            rivet_y = center + i * (size // 6)
            pygame.draw.circle(surface, (180, 160, 120), (center - size // 4, rivet_y), 2)
            pygame.draw.circle(surface, (180, 160, 120), (center + size // 4, rivet_y), 2)
    
    def _draw_ring_icon(self, surface, center, size, color):
        """Draw ring item icon - SVG style with gem and shine."""
        # Shadow
        pygame.draw.circle(surface, (20, 20, 20, 80), (center + 2, center + 2), size // 3, 4)
        
        # Main ring band
        pygame.draw.circle(surface, color, (center, center), size // 3, 5)
        
        # Inner highlight
        highlight = tuple(min(c + 50, 255) for c in color[:3])
        pygame.draw.arc(surface, highlight,
                       (center - size // 3, center - size // 3, size * 2 // 3, size * 2 // 3),
                       math.pi * 0.8, math.pi * 1.3, 2)
        
        # Gem setting
        gem_y = center - size // 4
        pygame.draw.circle(surface, (40, 35, 50), (center, gem_y), size // 6 + 2)
        
        # Gem with facets
        gem_color = tuple(min(c + 80, 255) for c in color[:3])
        pygame.draw.circle(surface, gem_color, (center, gem_y), size // 6)
        
        # Gem highlight
        pygame.draw.circle(surface, (255, 255, 255), (center - 2, gem_y - 2), size // 10)
        
        # Gem facet lines
        dark = tuple(max(c - 40, 0) for c in color[:3])
        pygame.draw.line(surface, dark, (center - size // 8, gem_y), (center + size // 8, gem_y), 1)
        pygame.draw.line(surface, dark, (center, gem_y - size // 8), (center, gem_y + size // 8), 1)
    
    def _draw_staff_icon(self, surface, center, size, color):
        """Draw staff/wand icon - SVG style with glow."""
        # Shaft shadow
        pygame.draw.rect(surface, (40, 30, 20),
                        (center, center - size // 3 + 2, 5, size * 2 // 3))
        
        # Wooden shaft with gradient
        pygame.draw.rect(surface, (80, 55, 35),
                        (center - 2, center - size // 3, 5, size * 2 // 3))
        pygame.draw.line(surface, (120, 90, 60),
                        (center - 1, center - size // 3),
                        (center - 1, center + size // 3), 2)
        
        # Shaft rings
        for i in range(4):
            ring_y = center - size // 4 + i * (size // 6)
            pygame.draw.line(surface, (60, 40, 25),
                            (center - 3, ring_y),
                            (center + 3, ring_y), 2)
        
        # Crystal glow
        glow_surf = pygame.Surface((size // 2, size // 2), pygame.SRCALPHA)
        for r in range(size // 4, 0, -2):
            alpha = 30 - r * 2
            pygame.draw.circle(glow_surf, (*color[:3], max(alpha, 0)),
                             (size // 4, size // 4), r)
        surface.blit(glow_surf, (center - size // 4, center - size // 2 - size // 6))
        
        # Crystal
        crystal_points = [
            (center, center - size // 3 - size // 5),
            (center - size // 7, center - size // 3 + 2),
            (center + size // 7, center - size // 3 + 2),
        ]
        pygame.draw.polygon(surface, color, crystal_points)
        
        # Crystal facets
        dark = tuple(max(c - 40, 0) for c in color[:3])
        pygame.draw.polygon(surface, dark, [
            (center, center - size // 3 - size // 5),
            (center, center - size // 3 + 2),
            (center + size // 7, center - size // 3 + 2),
        ])
        
        # Crystal shine
        pygame.draw.line(surface, (255, 255, 255),
                        (center - size // 12, center - size // 3 - size // 8),
                        (center - size // 14, center - size // 3), 2)
    
    def _draw_bow_icon(self, surface, center, size, color):
        """Draw bow icon - SVG style with wood grain."""
        # Shadow
        pygame.draw.arc(surface, (20, 20, 20, 80),
                       (center - size // 3 + 2, center - size // 3 + 2, size // 2, size * 2 // 3),
                       -math.pi / 2, math.pi / 2, 4)
        
        # Bow limb (wood)
        dark_wood = tuple(max(c - 30, 0) for c in color[:3])
        pygame.draw.arc(surface, dark_wood,
                       (center - size // 3, center - size // 3, size // 2 + 2, size * 2 // 3),
                       -math.pi / 2, math.pi / 2, 5)
        pygame.draw.arc(surface, color,
                       (center - size // 3, center - size // 3, size // 2, size * 2 // 3),
                       -math.pi / 2, math.pi / 2, 4)
        
        # Wood grain highlight
        highlight = tuple(min(c + 40, 255) for c in color[:3])
        pygame.draw.arc(surface, highlight,
                       (center - size // 3 - 1, center - size // 3 + 2, size // 2, size * 2 // 3 - 4),
                       -math.pi / 3, math.pi / 3, 1)
        
        # String
        pygame.draw.line(surface, (220, 200, 160),
                        (center - size // 10, center - size // 3 + 4),
                        (center - size // 10, center + size // 3 - 4), 2)
        pygame.draw.line(surface, (180, 160, 120),
                        (center - size // 10 + 1, center - size // 3 + 4),
                        (center - size // 10 + 1, center + size // 3 - 4), 1)
        
        # Arrow shaft
        pygame.draw.line(surface, (120, 90, 50),
                        (center - size // 3, center),
                        (center + size // 4, center), 3)
        pygame.draw.line(surface, (160, 120, 70),
                        (center - size // 3, center - 1),
                        (center + size // 4, center - 1), 1)
        
        # Arrow head (steel)
        pygame.draw.polygon(surface, (200, 200, 210), [
            (center + size // 4 + 6, center),
            (center + size // 4 - 2, center - 5),
            (center + size // 4 - 2, center + 5),
        ])
        pygame.draw.polygon(surface, (160, 160, 170), [
            (center + size // 4 + 6, center),
            (center + size // 4 - 2, center + 5),
            (center + size // 4 + 2, center),
        ])
        
        # Arrow fletching
        pygame.draw.polygon(surface, (200, 50, 50), [
            (center - size // 3 - 2, center - 4),
            (center - size // 3 + 6, center),
            (center - size // 3 - 2, center),
        ])
        pygame.draw.polygon(surface, (200, 50, 50), [
            (center - size // 3 - 2, center + 4),
            (center - size // 3 + 6, center),
            (center - size // 3 - 2, center),
        ])
    
    def _draw_axe_icon(self, surface, center, size, color):
        """Draw axe icon - SVG style with metal edge."""
        # Handle shadow
        pygame.draw.rect(surface, (40, 30, 20),
                        (center, center - size // 6 + 2, 6, size // 2))
        
        # Wooden handle with grain
        pygame.draw.rect(surface, (80, 55, 35),
                        (center - 2, center - size // 6, 6, size // 2))
        pygame.draw.line(surface, (110, 80, 50),
                        (center - 1, center - size // 6),
                        (center - 1, center + size // 3), 2)
        
        # Handle wraps
        for i in range(3):
            wrap_y = center + size // 10 + i * (size // 8)
            pygame.draw.line(surface, (60, 45, 30),
                            (center - 3, wrap_y), (center + 4, wrap_y), 2)
        
        # Axe head shadow
        pygame.draw.polygon(surface, (20, 20, 20, 80), [
            (center + 4, center - size // 6 + 2),
            (center + size // 3 + 2, center - size // 3 + 2),
            (center + size // 3 + 2, center + size // 6 + 2),
            (center + 4, center + size // 5 + 2),
        ])
        
        # Axe head body
        dark = tuple(max(c - 40, 0) for c in color[:3])
        pygame.draw.polygon(surface, color, [
            (center + 2, center - size // 6),
            (center + size // 3, center - size // 3),
            (center + size // 3, center + size // 6),
            (center + 2, center + size // 5),
        ])
        
        # Darker back edge
        pygame.draw.polygon(surface, dark, [
            (center + 2, center - size // 6),
            (center + size // 6, center - size // 4),
            (center + size // 6, center + size // 8),
            (center + 2, center + size // 5),
        ])
        
        # Cutting edge highlight
        highlight = tuple(min(c + 60, 255) for c in color[:3])
        pygame.draw.line(surface, highlight,
                        (center + size // 3, center - size // 3 + 2),
                        (center + size // 3, center + size // 6 - 2), 2)
        
        # Edge bevel
        pygame.draw.line(surface, (240, 240, 250),
                        (center + size // 3 - 3, center - size // 4),
                        (center + size // 3 - 3, center + size // 8), 1)
    
    def _draw_mace_icon(self, surface, center, size, color):
        """Draw mace/hammer icon - SVG style with metal head."""
        # Handle shadow
        pygame.draw.rect(surface, (40, 30, 20),
                        (center, center - size // 10 + 2, 6, size // 2))
        
        # Wooden handle
        pygame.draw.rect(surface, (80, 55, 35),
                        (center - 2, center - size // 10, 6, size // 2))
        pygame.draw.line(surface, (110, 80, 50),
                        (center - 1, center - size // 10),
                        (center - 1, center + size // 3), 2)
        
        # Handle grip
        for i in range(4):
            wrap_y = center + size // 8 + i * (size // 10)
            pygame.draw.line(surface, (60, 45, 30),
                            (center - 3, wrap_y), (center + 4, wrap_y), 2)
        
        # Mace head shadow
        pygame.draw.rect(surface, (20, 20, 20, 80),
                        (center - size // 5 + 2, center - size // 3 + 2, size * 2 // 5, size // 3),
                        border_radius=4)
        
        # Mace head body
        pygame.draw.rect(surface, color,
                        (center - size // 5, center - size // 3, size * 2 // 5, size // 3),
                        border_radius=4)
        
        # 3D shading on head
        dark = tuple(max(c - 40, 0) for c in color[:3])
        pygame.draw.rect(surface, dark,
                        (center, center - size // 3, size // 5, size // 3),
                        border_radius=2)
        
        # Highlight
        highlight = tuple(min(c + 50, 255) for c in color[:3])
        pygame.draw.rect(surface, highlight,
                        (center - size // 5 + 3, center - size // 3 + 3, size // 6, size // 6),
                        border_radius=2)
        
        # Spikes/flanges
        spike_color = tuple(min(c + 30, 255) for c in color[:3])
        for i in range(-1, 2):
            spike_x = center + i * (size // 5)
            pygame.draw.polygon(surface, spike_color, [
                (spike_x, center - size // 3 - 4),
                (spike_x - 4, center - size // 3),
                (spike_x + 4, center - size // 3),
            ])
    
    def _draw_helm_icon(self, surface, center, size, color):
        """Draw helmet icon - SVG style with visor and details."""
        # Shadow
        pygame.draw.ellipse(surface, (20, 20, 20, 80),
                           (center - size // 3 + 2, center - size // 3 + 2, size * 2 // 3, size // 2 + 4))
        
        # Main dome
        pygame.draw.ellipse(surface, color,
                           (center - size // 3, center - size // 3, size * 2 // 3, size // 2 + 4))
        
        # 3D shading on right side
        dark = tuple(max(c - 40, 0) for c in color[:3])
        pygame.draw.arc(surface, dark,
                       (center - size // 3, center - size // 3, size * 2 // 3, size // 2 + 4),
                       -math.pi / 2, math.pi / 4, size // 4)
        
        # Highlight on left
        highlight = tuple(min(c + 50, 255) for c in color[:3])
        pygame.draw.arc(surface, highlight,
                       (center - size // 3 + 4, center - size // 3 + 4, size // 3, size // 3),
                       math.pi / 2, math.pi, 3)
        
        # Face opening / visor
        pygame.draw.ellipse(surface, (30, 25, 40),
                           (center - size // 5, center - size // 8, size * 2 // 5, size // 3))
        
        # Visor slits
        for i in range(3):
            slit_y = center - size // 12 + i * (size // 10)
            pygame.draw.line(surface, (50, 45, 60),
                            (center - size // 6 + 2, slit_y),
                            (center + size // 6 - 2, slit_y), 2)
        
        # Nose guard
        pygame.draw.line(surface, color,
                        (center, center - size // 8),
                        (center, center + size // 6), 3)
        
        # Brim with beveled edge
        pygame.draw.rect(surface, dark,
                        (center - size // 3, center + size // 8, size * 2 // 3, size // 8))
        pygame.draw.line(surface, highlight,
                        (center - size // 3, center + size // 8),
                        (center + size // 3, center + size // 8), 2)
        
        # Crest/plume holder
        pygame.draw.circle(surface, highlight, (center, center - size // 3 + 2), size // 10)
    
    def _draw_boots_icon(self, surface, center, size, color):
        """Draw boots icon - SVG style with leather details."""
        # Shadow
        pygame.draw.ellipse(surface, (20, 20, 20, 80),
                           (center - size // 5 + 2, center + size // 8 + 2, size // 2 + 2, size // 4))
        
        # Boot sole
        pygame.draw.ellipse(surface, (50, 40, 35),
                           (center - size // 5, center + size // 6, size // 2 + 4, size // 5))
        
        # Boot foot
        pygame.draw.ellipse(surface, color,
                           (center - size // 5, center + size // 10, size // 2, size // 4))
        
        # Boot shaft shadow
        dark = tuple(max(c - 40, 0) for c in color[:3])
        pygame.draw.rect(surface, dark,
                        (center - size // 8 + 2, center - size // 3 + 2, size // 4 + 2, size // 2))
        
        # Boot shaft
        pygame.draw.rect(surface, color,
                        (center - size // 8, center - size // 3, size // 4, size // 2))
        
        # Shaft highlight
        highlight = tuple(min(c + 40, 255) for c in color[:3])
        pygame.draw.line(surface, highlight,
                        (center - size // 10, center - size // 3 + 4),
                        (center - size // 10, center + size // 8), 2)
        
        # Boot top fold
        pygame.draw.arc(surface, dark,
                       (center - size // 6, center - size // 3 - 4, size // 3, size // 6),
                       0, math.pi, 3)
        pygame.draw.arc(surface, highlight,
                       (center - size // 6, center - size // 3 - 2, size // 3, size // 6),
                       0, math.pi, 1)
        
        # Laces
        for i in range(3):
            lace_y = center - size // 6 + i * (size // 8)
            pygame.draw.line(surface, (180, 160, 120),
                            (center - size // 12, lace_y),
                            (center + size // 12, lace_y), 1)
        
        # Buckle
        pygame.draw.rect(surface, (200, 180, 100),
                        (center - size // 10, center + size // 20, size // 5, size // 12))
    
    def _draw_gloves_icon(self, surface, center, size, color):
        """Draw gloves icon - SVG style with armor plates."""
        dark = tuple(max(c - 40, 0) for c in color[:3])
        highlight = tuple(min(c + 50, 255) for c in color[:3])
        
        # Shadow
        pygame.draw.rect(surface, (20, 20, 20, 80),
                        (center - size // 4 + 2, center - size // 6 + 2, size // 3 + 2, size // 2),
                        border_radius=4)
        
        # Palm/main glove body
        pygame.draw.rect(surface, color,
                        (center - size // 4, center - size // 6, size // 3, size // 2),
                        border_radius=4)
        
        # Palm shading
        pygame.draw.rect(surface, dark,
                        (center - size // 10, center - size // 8, size // 5, size // 3),
                        border_radius=2)
        
        # Fingers with joints
        for i in range(4):
            fx = center - size // 5 + i * (size // 7)
            # Finger shadow
            pygame.draw.rect(surface, dark,
                            (fx + 1, center - size // 3 + 1, size // 9, size // 4),
                            border_radius=2)
            # Finger
            pygame.draw.rect(surface, color,
                            (fx, center - size // 3, size // 9, size // 4),
                            border_radius=2)
            # Finger joint
            pygame.draw.line(surface, dark,
                            (fx, center - size // 5),
                            (fx + size // 10, center - size // 5), 1)
            # Fingertip highlight
            pygame.draw.rect(surface, highlight,
                            (fx + 1, center - size // 3 + 1, size // 12, size // 12),
                            border_radius=1)
        
        # Thumb
        pygame.draw.rect(surface, dark,
                        (center - size // 3 + 1, center - size // 10 + 1, size // 7, size // 4),
                        border_radius=3)
        pygame.draw.rect(surface, color,
                        (center - size // 3, center - size // 10, size // 7, size // 4),
                        border_radius=3)
        
        # Wrist guard/cuff
        pygame.draw.rect(surface, highlight,
                        (center - size // 4, center + size // 5, size // 3, size // 8),
                        border_radius=2)
        pygame.draw.line(surface, dark,
                        (center - size // 4, center + size // 4),
                        (center + size // 12, center + size // 4), 2)
        
        # Knuckle plates
        for i in range(3):
            kx = center - size // 6 + i * (size // 7)
            pygame.draw.rect(surface, highlight,
                            (kx, center - size // 8, size // 8, size // 10),
                            border_radius=1)
    
    def _draw_shield_icon(self, surface, center, size, color):
        """Draw shield icon - SVG style with beveled edges."""
        # Shadow
        shadow_points = [
            (center + 2, center - size // 3 + 2),
            (center + size // 3 + 2, center - size // 6 + 2),
            (center + size // 4 + 2, center + size // 4 + 2),
            (center + 2, center + size // 3 + 2),
            (center - size // 4 + 2, center + size // 4 + 2),
            (center - size // 3 + 2, center - size // 6 + 2),
        ]
        pygame.draw.polygon(surface, (20, 20, 20, 80), shadow_points)
        
        # Main shield body
        points = [
            (center, center - size // 3),
            (center + size // 3, center - size // 6),
            (center + size // 4, center + size // 4),
            (center, center + size // 3),
            (center - size // 4, center + size // 4),
            (center - size // 3, center - size // 6),
        ]
        pygame.draw.polygon(surface, color, points)
        
        # Darker right half
        dark = tuple(max(c - 30, 0) for c in color[:3])
        right_half = [
            (center, center - size // 3),
            (center + size // 3, center - size // 6),
            (center + size // 4, center + size // 4),
            (center, center + size // 3),
        ]
        pygame.draw.polygon(surface, dark, right_half)
        
        # Rim/edge highlight
        highlight = tuple(min(c + 60, 255) for c in color[:3])
        pygame.draw.lines(surface, highlight, False, [
            (center - size // 3, center - size // 6),
            (center, center - size // 3),
            (center + size // 3, center - size // 6),
        ], 2)
        
        # Inner beveled edge
        inner_points = [
            (center, center - size // 4),
            (center + size // 5, center - size // 8),
            (center + size // 6, center + size // 6),
            (center, center + size // 5),
            (center - size // 6, center + size // 6),
            (center - size // 5, center - size // 8),
        ]
        pygame.draw.polygon(surface, dark, inner_points, 2)
        
        # Central emblem
        emblem_color = tuple(min(c + 80, 255) for c in color[:3])
        pygame.draw.circle(surface, emblem_color, (center, center), size // 6)
        pygame.draw.circle(surface, (255, 255, 255), (center - 2, center - 2), size // 10)
        
        # Cross on emblem
        pygame.draw.line(surface, dark, (center - size // 10, center), (center + size // 10, center), 2)
        pygame.draw.line(surface, dark, (center, center - size // 10), (center, center + size // 10), 2)
    
    def _draw_amulet_icon(self, surface, center, size, color):
        """Draw amulet icon - SVG style with chain links and gem."""
        dark = tuple(max(c - 40, 0) for c in color[:3])
        highlight = tuple(min(c + 60, 255) for c in color[:3])
        
        # Chain links
        chain_color = (200, 180, 100)
        chain_dark = (160, 140, 70)
        for i in range(5):
            angle = math.pi * 0.2 + i * (math.pi * 0.15)
            cx = center + int(math.cos(angle) * size // 3)
            cy = center - size // 4 + int(math.sin(angle) * size // 6)
            pygame.draw.ellipse(surface, chain_dark, (cx - 4, cy - 3, 8, 6))
            pygame.draw.ellipse(surface, chain_color, (cx - 3, cy - 2, 6, 4))
        
        # Mirror for other side
        for i in range(5):
            angle = math.pi - (math.pi * 0.2 + i * (math.pi * 0.15))
            cx = center + int(math.cos(angle) * size // 3)
            cy = center - size // 4 + int(math.sin(angle) * size // 6)
            pygame.draw.ellipse(surface, chain_dark, (cx - 4, cy - 3, 8, 6))
            pygame.draw.ellipse(surface, chain_color, (cx - 3, cy - 2, 6, 4))
        
        # Pendant shadow
        pygame.draw.polygon(surface, (20, 20, 20, 80), [
            (center + 2, center - size // 10 + 2),
            (center - size // 5 + 2, center + size // 7 + 2),
            (center + 2, center + size // 3 + 2),
            (center + size // 5 + 2, center + size // 7 + 2),
        ])
        
        # Pendant body
        pygame.draw.polygon(surface, color, [
            (center, center - size // 10),
            (center - size // 5, center + size // 7),
            (center, center + size // 3),
            (center + size // 5, center + size // 7),
        ])
        
        # Pendant facets
        pygame.draw.polygon(surface, dark, [
            (center, center - size // 10),
            (center, center + size // 3),
            (center + size // 5, center + size // 7),
        ])
        
        # Pendant edge highlight
        pygame.draw.line(surface, highlight,
                        (center - size // 5 + 2, center + size // 7),
                        (center - 1, center - size // 10 + 2), 2)
        
        # Central gem
        gem_y = center + size // 10
        pygame.draw.circle(surface, (60, 50, 80), (center, gem_y), size // 7)
        pygame.draw.circle(surface, highlight, (center, gem_y), size // 8)
        pygame.draw.circle(surface, (255, 255, 255), (center - 2, gem_y - 2), size // 12)
        
        # Gem facet
        pygame.draw.line(surface, dark,
                        (center - size // 10, gem_y),
                        (center + size // 10, gem_y), 1)
    
    def _draw_generic_item(self, surface, center, size, color):
        """Draw generic item icon - SVG style mysterious item."""
        dark = tuple(max(c - 40, 0) for c in color[:3])
        highlight = tuple(min(c + 60, 255) for c in color[:3])
        
        # Shadow
        pygame.draw.rect(surface, (20, 20, 20, 80),
                        (center - size // 4 + 2, center - size // 4 + 2,
                         size // 2, size // 2), border_radius=6)
        
        # Main box/container
        pygame.draw.rect(surface, color,
                        (center - size // 4, center - size // 4,
                         size // 2, size // 2), border_radius=6)
        
        # 3D shading
        pygame.draw.rect(surface, dark,
                        (center, center - size // 4,
                         size // 4, size // 2), border_radius=3)
        
        # Highlight edge
        pygame.draw.line(surface, highlight,
                        (center - size // 4 + 3, center - size // 4 + 3),
                        (center - size // 4 + 3, center + size // 5), 2)
        pygame.draw.line(surface, highlight,
                        (center - size // 4 + 3, center - size // 4 + 3),
                        (center + size // 8, center - size // 4 + 3), 2)
        
        # Mystery symbol (question mark or rune)
        pygame.draw.arc(surface, (255, 255, 255),
                       (center - size // 8, center - size // 5, size // 4, size // 5),
                       0, math.pi * 1.5, 2)
        pygame.draw.line(surface, (255, 255, 255),
                        (center, center - size // 20),
                        (center, center + size // 10), 2)
        pygame.draw.circle(surface, (255, 255, 255), (center, center + size // 6), 2)
        
        # Glow effect
        glow_surf = pygame.Surface((size // 2, size // 2), pygame.SRCALPHA)
        for r in range(size // 4, 0, -3):
            alpha = 20 - r
            pygame.draw.circle(glow_surf, (*color[:3], max(alpha, 0)),
                             (size // 4, size // 4), r)
        surface.blit(glow_surf, (center - size // 4, center - size // 4))
    
    # =========================================================================
    # NEW WEAPON ICONS
    # =========================================================================
    
    def _draw_dagger_icon(self, surface, center, size, color):
        """Draw a sleek dagger icon."""
        dark = tuple(max(c - 40, 0) for c in color[:3])
        highlight = tuple(min(c + 60, 255) for c in color[:3])
        
        # Blade shadow
        pygame.draw.polygon(surface, (20, 20, 20, 80), [
            (center + 2, center - size // 3 + 2),
            (center + size // 12 + 2, center + size // 10 + 2),
            (center + 2, center + size // 8 + 2),
            (center - size // 12 + 2, center + size // 10 + 2),
        ])
        
        # Thin blade
        pygame.draw.polygon(surface, color, [
            (center, center - size // 3),
            (center + size // 12, center + size // 10),
            (center, center + size // 8),
            (center - size // 12, center + size // 10),
        ])
        
        # Blade edge
        pygame.draw.line(surface, highlight,
                        (center - size // 14, center + size // 12),
                        (center, center - size // 3 + 2), 1)
        pygame.draw.line(surface, dark,
                        (center, center - size // 3),
                        (center, center + size // 8), 1)
        
        # Small guard
        guard_y = center + size // 10
        pygame.draw.line(surface, (160, 140, 80),
                        (center - size // 6, guard_y),
                        (center + size // 6, guard_y), 3)
        
        # Wrapped handle
        for i in range(4):
            wrap_y = guard_y + 4 + i * 4
            pygame.draw.line(surface, (70, 50, 35),
                            (center - 3, wrap_y),
                            (center + 3, wrap_y), 2)
        
        # Small pommel
        pygame.draw.circle(surface, (140, 120, 60), (center, guard_y + 20), 3)
    
    def _draw_scimitar_icon(self, surface, center, size, color):
        """Draw curved scimitar blade."""
        dark = tuple(max(c - 40, 0) for c in color[:3])
        highlight = tuple(min(c + 60, 255) for c in color[:3])
        
        # Curved blade using arc approximation
        blade_points = [
            (center - size // 6, center - size // 3),
            (center + size // 8, center - size // 4),
            (center + size // 5, center),
            (center + size // 8, center + size // 8),
            (center - size // 12, center + size // 12),
            (center - size // 5, center - size // 6),
        ]
        pygame.draw.polygon(surface, color, blade_points)
        
        # Blade highlight curve
        pygame.draw.lines(surface, highlight, False, [
            (center - size // 5, center - size // 6),
            (center - size // 6, center - size // 3),
            (center + size // 8, center - size // 4),
        ], 2)
        
        # Edge
        pygame.draw.lines(surface, (240, 240, 250), False, [
            (center + size // 8, center - size // 4),
            (center + size // 5, center),
            (center + size // 8, center + size // 8),
        ], 1)
        
        # Guard
        guard_y = center + size // 10
        pygame.draw.ellipse(surface, (180, 160, 100),
                           (center - size // 5, guard_y - 2, size * 2 // 5, size // 10))
        
        # Handle
        pygame.draw.rect(surface, (80, 55, 35),
                        (center - 3, guard_y + 4, 6, size // 4))
        pygame.draw.circle(surface, (200, 180, 100), (center, guard_y + size // 4 + 6), 4)
    
    def _draw_greatsword_icon(self, surface, center, size, color):
        """Draw a massive two-handed sword."""
        dark = tuple(max(c - 40, 0) for c in color[:3])
        highlight = tuple(min(c + 60, 255) for c in color[:3])
        
        # Wide blade
        pygame.draw.polygon(surface, color, [
            (center, center - size // 2 + 4),
            (center + size // 5, center - size // 6),
            (center + size // 5, center + size // 10),
            (center, center + size // 6),
            (center - size // 5, center + size // 10),
            (center - size // 5, center - size // 6),
        ])
        
        # Fuller (blood groove)
        pygame.draw.line(surface, dark,
                        (center, center - size // 3),
                        (center, center + size // 12), 3)
        
        # Blade highlights
        pygame.draw.line(surface, highlight,
                        (center - size // 6, center - size // 8),
                        (center - 2, center - size // 2 + 6), 2)
        
        # Large crossguard
        guard_y = center + size // 8
        pygame.draw.rect(surface, (180, 160, 100),
                        (center - size // 3, guard_y - 3, size * 2 // 3, 8))
        pygame.draw.line(surface, (220, 200, 140),
                        (center - size // 3, guard_y - 3),
                        (center + size // 3, guard_y - 3), 2)
        
        # Long handle
        pygame.draw.rect(surface, (70, 50, 35),
                        (center - 4, guard_y + 5, 8, size // 3))
        
        # Pommel
        pygame.draw.circle(surface, (160, 140, 80), (center, guard_y + size // 3 + 8), 5)
    
    def _draw_club_icon(self, surface, center, size, color):
        """Draw a primitive wooden club."""
        # Main shaft - thicker at top
        pygame.draw.polygon(surface, (100, 70, 45), [
            (center - size // 6, center - size // 3),
            (center + size // 6, center - size // 3),
            (center + size // 10, center + size // 3),
            (center - size // 10, center + size // 3),
        ])
        
        # Wood grain lines
        for i in range(4):
            y = center - size // 4 + i * (size // 6)
            pygame.draw.line(surface, (80, 55, 35),
                            (center - size // 8, y),
                            (center + size // 8, y + 5), 1)
        
        # Knots
        pygame.draw.circle(surface, (70, 45, 30), (center - size // 10, center - size // 6), 3)
        pygame.draw.circle(surface, (70, 45, 30), (center + size // 12, center + size // 10), 2)
        
        # Highlight edge
        pygame.draw.line(surface, (130, 95, 60),
                        (center - size // 7, center - size // 3 + 2),
                        (center - size // 11, center + size // 3 - 2), 2)
    
    def _draw_hatchet_icon(self, surface, center, size, color):
        """Draw a small hatchet."""
        dark = tuple(max(c - 40, 0) for c in color[:3])
        highlight = tuple(min(c + 60, 255) for c in color[:3])
        
        # Handle
        pygame.draw.rect(surface, (90, 65, 40),
                        (center - 3, center - size // 10, 6, size // 2 + 4))
        pygame.draw.line(surface, (120, 90, 55),
                        (center - 2, center - size // 10),
                        (center - 2, center + size // 3), 2)
        
        # Small axe head
        pygame.draw.polygon(surface, color, [
            (center + 2, center - size // 6),
            (center + size // 4, center - size // 4),
            (center + size // 4, center + size // 12),
            (center + 2, center + size // 8),
        ])
        
        # Edge highlight
        pygame.draw.line(surface, (240, 240, 250),
                        (center + size // 4 - 1, center - size // 5),
                        (center + size // 4 - 1, center + size // 14), 1)
        
        # Head bevel
        pygame.draw.polygon(surface, dark, [
            (center + 2, center - size // 6),
            (center + size // 8, center - size // 8),
            (center + size // 8, center + size // 16),
            (center + 2, center + size // 8),
        ])
    
    def _draw_crossbow_icon(self, surface, center, size, color):
        """Draw a crossbow."""
        dark = tuple(max(c - 40, 0) for c in color[:3])
        
        # Stock/body
        pygame.draw.rect(surface, (90, 65, 40),
                        (center - size // 10, center - size // 10, size // 3, size // 5))
        pygame.draw.rect(surface, (70, 50, 35),
                        (center - size // 10, center + size // 20, size // 3, size // 3))
        
        # Bow limbs
        pygame.draw.arc(surface, color,
                       (center - size // 3, center - size // 3, size // 3, size // 2),
                       -math.pi / 4, math.pi / 4, 4)
        pygame.draw.arc(surface, color,
                       (center, center - size // 3, size // 3, size // 2),
                       math.pi * 3 / 4, math.pi * 5 / 4, 4)
        
        # String
        pygame.draw.line(surface, (200, 180, 140),
                        (center - size // 4, center - size // 8),
                        (center + size // 4, center - size // 8), 2)
        
        # Bolt
        pygame.draw.line(surface, (100, 75, 50),
                        (center - size // 10, center),
                        (center + size // 4, center), 2)
        pygame.draw.polygon(surface, (180, 180, 190), [
            (center + size // 4 + 4, center),
            (center + size // 4 - 2, center - 3),
            (center + size // 4 - 2, center + 3),
        ])
        
        # Trigger
        pygame.draw.rect(surface, (60, 45, 30),
                        (center, center + size // 6, size // 12, size // 6))
    
    def _draw_javelin_icon(self, surface, center, size, color):
        """Draw a throwing javelin/spear."""
        highlight = tuple(min(c + 60, 255) for c in color[:3])
        
        # Long shaft
        pygame.draw.line(surface, (100, 75, 50),
                        (center, center - size // 3),
                        (center, center + size // 3), 4)
        pygame.draw.line(surface, (130, 100, 65),
                        (center - 1, center - size // 3),
                        (center - 1, center + size // 3), 1)
        
        # Spear head
        pygame.draw.polygon(surface, color, [
            (center, center - size // 2 + 4),
            (center - size // 10, center - size // 4),
            (center + size // 10, center - size // 4),
        ])
        pygame.draw.line(surface, highlight,
                        (center - size // 12, center - size // 3),
                        (center - 1, center - size // 2 + 6), 1)
        
        # Binding
        for i in range(2):
            y = center - size // 4 - 2 + i * 4
            pygame.draw.line(surface, (140, 100, 60),
                            (center - 3, y), (center + 3, y), 2)
    
    def _draw_throwing_icon(self, surface, center, size, color):
        """Draw throwing weapons (daggers/knives)."""
        # Draw 3 small throwing knives
        for i, offset in enumerate([-size // 5, 0, size // 5]):
            angle = -0.2 + i * 0.2
            # Small blade
            bx = center + offset
            by = center - size // 6
            pygame.draw.polygon(surface, color, [
                (bx, by - size // 6),
                (bx + size // 16, by + size // 12),
                (bx - size // 16, by + size // 12),
            ])
            # Handle
            pygame.draw.rect(surface, (80, 55, 35),
                            (bx - 2, by + size // 12, 4, size // 6))
    
    def _draw_wand_icon(self, surface, center, size, color):
        """Draw a magic wand."""
        highlight = tuple(min(c + 80, 255) for c in color[:3])
        
        # Thin shaft
        pygame.draw.line(surface, (60, 45, 35),
                        (center + size // 5, center + size // 3),
                        (center - size // 6, center - size // 4), 4)
        pygame.draw.line(surface, (90, 70, 50),
                        (center + size // 5 - 1, center + size // 3 - 1),
                        (center - size // 6 - 1, center - size // 4 - 1), 2)
        
        # Glowing tip
        tip_x = center - size // 6
        tip_y = center - size // 4
        
        # Glow
        glow_surf = pygame.Surface((size // 2, size // 2), pygame.SRCALPHA)
        for r in range(size // 5, 0, -2):
            alpha = 40 - r * 3
            pygame.draw.circle(glow_surf, (*color[:3], max(alpha, 0)),
                             (size // 4, size // 4), r)
        surface.blit(glow_surf, (tip_x - size // 4, tip_y - size // 4))
        
        # Crystal tip
        pygame.draw.circle(surface, color, (tip_x, tip_y), size // 10)
        pygame.draw.circle(surface, highlight, (tip_x - 1, tip_y - 1), size // 16)
        
        # Handle decoration
        pygame.draw.circle(surface, (120, 100, 60),
                          (center + size // 6, center + size // 4), 4)
    
    def _draw_orb_icon(self, surface, center, size, color):
        """Draw a magical orb."""
        dark = tuple(max(c - 40, 0) for c in color[:3])
        highlight = tuple(min(c + 80, 255) for c in color[:3])
        
        # Outer glow
        glow_surf = pygame.Surface((size, size), pygame.SRCALPHA)
        for r in range(size // 2, size // 4, -2):
            alpha = 30 - (r - size // 4)
            pygame.draw.circle(glow_surf, (*color[:3], max(alpha, 0)),
                             (size // 2, size // 2), r)
        surface.blit(glow_surf, (0, 0))
        
        # Main orb
        pygame.draw.circle(surface, dark, (center, center), size // 3)
        pygame.draw.circle(surface, color, (center, center), size // 3 - 2)
        
        # Inner glow/pattern
        pygame.draw.circle(surface, highlight, (center - 4, center - 4), size // 8)
        
        # Swirling energy
        for i in range(3):
            angle = i * math.pi * 2 / 3
            x = center + int(math.cos(angle) * size // 6)
            y = center + int(math.sin(angle) * size // 6)
            pygame.draw.circle(surface, highlight, (x, y), 2)
    
    # =========================================================================
    # NEW ARMOR ICONS
    # =========================================================================
    
    def _draw_hood_icon(self, surface, center, size, color):
        """Draw a cloth hood/coif."""
        dark = tuple(max(c - 40, 0) for c in color[:3])
        
        # Hood shape
        pygame.draw.ellipse(surface, color,
                           (center - size // 3, center - size // 3, size * 2 // 3, size // 2))
        
        # Face opening (darker)
        pygame.draw.ellipse(surface, (30, 25, 35),
                           (center - size // 5, center - size // 6, size * 2 // 5, size // 3))
        
        # Hood folds
        pygame.draw.arc(surface, dark,
                       (center - size // 4, center - size // 4, size // 2, size // 3),
                       0, math.pi, 2)
        
        # Draping sides
        pygame.draw.polygon(surface, dark, [
            (center - size // 3, center + size // 10),
            (center - size // 4, center + size // 3),
            (center - size // 6, center + size // 10),
        ])
        pygame.draw.polygon(surface, dark, [
            (center + size // 3, center + size // 10),
            (center + size // 4, center + size // 3),
            (center + size // 6, center + size // 10),
        ])
    
    def _draw_wizardhat_icon(self, surface, center, size, color):
        """Draw a pointed wizard hat."""
        dark = tuple(max(c - 40, 0) for c in color[:3])
        highlight = tuple(min(c + 50, 255) for c in color[:3])
        
        # Wide brim
        pygame.draw.ellipse(surface, dark,
                           (center - size // 3, center + size // 10, size * 2 // 3, size // 5))
        
        # Cone
        pygame.draw.polygon(surface, color, [
            (center, center - size // 2 + 4),
            (center - size // 4, center + size // 6),
            (center + size // 4, center + size // 6),
        ])
        
        # Cone shading
        pygame.draw.polygon(surface, dark, [
            (center, center - size // 2 + 4),
            (center, center + size // 8),
            (center + size // 4, center + size // 6),
        ])
        
        # Star decoration
        star_y = center - size // 8
        pygame.draw.polygon(surface, (255, 220, 100), [
            (center, star_y - 5),
            (center + 3, star_y),
            (center, star_y + 5),
            (center - 3, star_y),
        ])
    
    def _draw_crown_icon(self, surface, center, size, color):
        """Draw a royal crown/circlet."""
        dark = tuple(max(c - 40, 0) for c in color[:3])
        highlight = tuple(min(c + 60, 255) for c in color[:3])
        
        # Base band
        pygame.draw.rect(surface, color,
                        (center - size // 3, center, size * 2 // 3, size // 5))
        pygame.draw.rect(surface, dark,
                        (center - size // 3, center + size // 10, size * 2 // 3, size // 10))
        
        # Points
        for i, offset in enumerate([-size // 4, 0, size // 4]):
            h = size // 3 if i == 1 else size // 4
            pygame.draw.polygon(surface, color, [
                (center + offset - size // 10, center),
                (center + offset, center - h),
                (center + offset + size // 10, center),
            ])
            # Gem on each point
            pygame.draw.circle(surface, highlight,
                             (center + offset, center - h + 4), 3)
        
        # Band decoration
        pygame.draw.line(surface, highlight,
                        (center - size // 3 + 2, center + 2),
                        (center + size // 3 - 2, center + 2), 1)
    
    def _draw_robe_icon(self, surface, center, size, color):
        """Draw mage robes."""
        dark = tuple(max(c - 40, 0) for c in color[:3])
        highlight = tuple(min(c + 50, 255) for c in color[:3])
        
        # Main robe shape
        pygame.draw.polygon(surface, color, [
            (center, center - size // 4),
            (center - size // 4, center - size // 6),
            (center - size // 3, center + size // 3),
            (center + size // 3, center + size // 3),
            (center + size // 4, center - size // 6),
        ])
        
        # Collar
        pygame.draw.arc(surface, highlight,
                       (center - size // 6, center - size // 4, size // 3, size // 6),
                       0, math.pi, 2)
        
        # Center seam
        pygame.draw.line(surface, dark,
                        (center, center - size // 6),
                        (center, center + size // 4), 2)
        
        # Sleeve hints
        pygame.draw.line(surface, dark,
                        (center - size // 5, center - size // 10),
                        (center - size // 3 + 4, center + size // 8), 2)
        pygame.draw.line(surface, dark,
                        (center + size // 5, center - size // 10),
                        (center + size // 3 - 4, center + size // 8), 2)
        
        # Mystical symbol
        pygame.draw.circle(surface, highlight, (center, center + size // 10), size // 10, 1)
    
    def _draw_chainmail_icon(self, surface, center, size, color):
        """Draw chainmail armor."""
        dark = tuple(max(c - 30, 0) for c in color[:3])
        
        # Torso shape
        pygame.draw.polygon(surface, color, [
            (center, center - size // 4),
            (center - size // 4, center - size // 6),
            (center - size // 3, center + size // 4),
            (center + size // 3, center + size // 4),
            (center + size // 4, center - size // 6),
        ])
        
        # Chain pattern (circles)
        for row in range(5):
            for col in range(5):
                x = center - size // 4 + col * (size // 8)
                y = center - size // 8 + row * (size // 10)
                if row % 2 == 1:
                    x += size // 16
                pygame.draw.circle(surface, dark, (x, y), 3, 1)
        
        # Collar
        pygame.draw.arc(surface, (180, 170, 160),
                       (center - size // 5, center - size // 4, size * 2 // 5, size // 6),
                       0, math.pi, 2)
    
    def _draw_leather_icon(self, surface, center, size, color):
        """Draw leather armor/vest."""
        dark = tuple(max(c - 40, 0) for c in color[:3])
        highlight = tuple(min(c + 40, 255) for c in color[:3])
        
        # Vest shape
        pygame.draw.polygon(surface, color, [
            (center, center - size // 4),
            (center - size // 4, center - size // 6),
            (center - size // 4, center + size // 4),
            (center + size // 4, center + size // 4),
            (center + size // 4, center - size // 6),
        ])
        
        # Darker sides
        pygame.draw.polygon(surface, dark, [
            (center, center - size // 4),
            (center + size // 4, center - size // 6),
            (center + size // 4, center + size // 4),
            (center, center + size // 5),
        ])
        
        # Stitching
        pygame.draw.line(surface, (60, 45, 35),
                        (center, center - size // 5),
                        (center, center + size // 5), 1)
        
        # Buttons/laces
        for i in range(3):
            y = center - size // 10 + i * (size // 8)
            pygame.draw.circle(surface, (100, 80, 50), (center, y), 2)
    
    def _draw_leggings_icon(self, surface, center, size, color):
        """Draw pants/leggings."""
        dark = tuple(max(c - 40, 0) for c in color[:3])
        
        # Waistband
        pygame.draw.rect(surface, color,
                        (center - size // 4, center - size // 3, size // 2, size // 8))
        
        # Left leg
        pygame.draw.polygon(surface, color, [
            (center - size // 4, center - size // 4),
            (center - size // 8, center - size // 4),
            (center - size // 10, center + size // 3),
            (center - size // 4, center + size // 3),
        ])
        
        # Right leg (darker)
        pygame.draw.polygon(surface, dark, [
            (center + size // 8, center - size // 4),
            (center + size // 4, center - size // 4),
            (center + size // 4, center + size // 3),
            (center + size // 10, center + size // 3),
        ])
        
        # Belt buckle
        pygame.draw.rect(surface, (180, 160, 100),
                        (center - size // 12, center - size // 3 - 2, size // 6, size // 10))
    
    # =========================================================================
    # MATERIAL ICONS
    # =========================================================================
    
    def _draw_bone_icon(self, surface, center, size, color):
        """Draw a bone."""
        # Shaft
        pygame.draw.rect(surface, (240, 235, 220),
                        (center - size // 12, center - size // 4, size // 6, size // 2))
        
        # Top knob
        pygame.draw.circle(surface, (240, 235, 220), (center, center - size // 4), size // 8)
        pygame.draw.circle(surface, (220, 215, 200), (center - 2, center - size // 4 - 2), size // 14)
        
        # Bottom knob
        pygame.draw.circle(surface, (240, 235, 220), (center, center + size // 4), size // 8)
        
        # Cracks
        pygame.draw.line(surface, (200, 195, 180),
                        (center - 2, center - size // 10),
                        (center + 3, center + size // 10), 1)
    
    def _draw_silk_icon(self, surface, center, size, color):
        """Draw spider silk."""
        # Silk strands
        for i in range(5):
            angle = math.pi / 6 + i * (math.pi / 8)
            x1 = center + int(math.cos(angle) * size // 5)
            y1 = center + int(math.sin(angle) * size // 5)
            x2 = center + int(math.cos(angle + math.pi) * size // 3)
            y2 = center + int(math.sin(angle + math.pi) * size // 3)
            pygame.draw.line(surface, (240, 240, 245), (x1, y1), (x2, y2), 1)
        
        # Central bundle
        pygame.draw.ellipse(surface, (250, 250, 255),
                           (center - size // 6, center - size // 8, size // 3, size // 4))
        pygame.draw.ellipse(surface, (230, 230, 240),
                           (center - size // 8, center - size // 12, size // 4, size // 6))
    
    def _draw_gland_icon(self, surface, center, size, color):
        """Draw poison gland."""
        # Gland body
        pygame.draw.ellipse(surface, (100, 180, 80),
                           (center - size // 4, center - size // 5, size // 2, size * 2 // 5))
        
        # Vein pattern
        pygame.draw.arc(surface, (60, 140, 50),
                       (center - size // 5, center - size // 6, size // 3, size // 4),
                       0, math.pi, 1)
        
        # Dripping
        pygame.draw.circle(surface, (80, 200, 60), (center, center + size // 5), 4)
        pygame.draw.circle(surface, (80, 200, 60), (center, center + size // 3), 2)
    
    def _draw_flesh_icon(self, surface, center, size, color):
        """Draw rotting flesh."""
        # Chunk shape
        pygame.draw.ellipse(surface, (120, 80, 70),
                           (center - size // 3, center - size // 4, size * 2 // 3, size // 2))
        
        # Gross details
        pygame.draw.ellipse(surface, (80, 60, 50),
                           (center - size // 6, center - size // 8, size // 4, size // 5))
        pygame.draw.ellipse(surface, (100, 70, 60),
                           (center + size // 10, center + size // 20, size // 6, size // 8))
        
        # Maggot/decay spots
        for _ in range(3):
            x = center + (hash(str(center)) % 10 - 5)
            y = center + (hash(str(center + 1)) % 10 - 5)
            pygame.draw.circle(surface, (60, 45, 35), (x, y), 2)
    
    def _draw_demon_heart_icon(self, surface, center, size, color):
        """Draw a demon heart."""
        # Glow
        glow_surf = pygame.Surface((size, size), pygame.SRCALPHA)
        for r in range(size // 3, 0, -3):
            alpha = 40 - r * 2
            pygame.draw.circle(glow_surf, (255, 50, 30, max(alpha, 0)),
                             (size // 2, size // 2), r)
        surface.blit(glow_surf, (0, 0))
        
        # Heart shape using overlapping circles
        pygame.draw.circle(surface, (180, 30, 40), (center - size // 8, center - size // 10), size // 5)
        pygame.draw.circle(surface, (180, 30, 40), (center + size // 8, center - size // 10), size // 5)
        pygame.draw.polygon(surface, (180, 30, 40), [
            (center - size // 4, center - size // 12),
            (center, center + size // 4),
            (center + size // 4, center - size // 12),
        ])
        
        # Veins
        pygame.draw.line(surface, (100, 20, 25),
                        (center, center - size // 8),
                        (center - size // 8, center + size // 10), 1)
        pygame.draw.line(surface, (100, 20, 25),
                        (center, center - size // 8),
                        (center + size // 10, center + size // 12), 1)
    
    def _draw_scale_icon(self, surface, center, size, color):
        """Draw a dragon scale."""
        # Scale shape
        pygame.draw.polygon(surface, (80, 150, 80), [
            (center, center - size // 3),
            (center - size // 4, center),
            (center - size // 5, center + size // 4),
            (center + size // 5, center + size // 4),
            (center + size // 4, center),
        ])
        
        # Ridges
        for i in range(3):
            y = center - size // 6 + i * (size // 8)
            pygame.draw.arc(surface, (60, 120, 60),
                           (center - size // 5, y, size * 2 // 5, size // 8),
                           0, math.pi, 2)
        
        # Shimmer
        pygame.draw.line(surface, (150, 220, 150),
                        (center - size // 8, center - size // 5),
                        (center - size // 10, center - size // 10), 2)
    
    def _draw_dust_icon(self, surface, center, size, color):
        """Draw arcane dust."""
        # Sparkles
        for i in range(8):
            angle = i * math.pi / 4
            r = size // 4 + (i % 3) * 4
            x = center + int(math.cos(angle) * r)
            y = center + int(math.sin(angle) * r)
            pygame.draw.circle(surface, (200, 180, 255), (x, y), 2)
            pygame.draw.circle(surface, (255, 255, 255), (x, y), 1)
        
        # Central glow
        glow_surf = pygame.Surface((size // 2, size // 2), pygame.SRCALPHA)
        for r in range(size // 4, 0, -2):
            alpha = 50 - r * 3
            pygame.draw.circle(glow_surf, (180, 150, 255, max(alpha, 0)),
                             (size // 4, size // 4), r)
        surface.blit(glow_surf, (center - size // 4, center - size // 4))
        
        pygame.draw.circle(surface, (220, 200, 255), (center, center), size // 8)
    
    def _draw_essence_icon(self, surface, center, size, color):
        """Draw void essence."""
        # Dark core
        pygame.draw.circle(surface, (20, 10, 30), (center, center), size // 4)
        
        # Void swirl
        for i in range(3):
            angle = i * math.pi * 2 / 3
            arc_center_x = center + int(math.cos(angle) * size // 6)
            arc_center_y = center + int(math.sin(angle) * size // 6)
            pygame.draw.arc(surface, (80, 40, 120),
                           (arc_center_x - size // 6, arc_center_y - size // 6, size // 3, size // 3),
                           angle, angle + math.pi, 2)
        
        # Energy tendrils
        for i in range(5):
            angle = i * math.pi * 2 / 5
            x = center + int(math.cos(angle) * size // 3)
            y = center + int(math.sin(angle) * size // 3)
            pygame.draw.line(surface, (100, 60, 150), (center, center), (x, y), 1)
        
        # Central void
        pygame.draw.circle(surface, (40, 20, 60), (center, center), size // 6)
        pygame.draw.circle(surface, (60, 30, 90), (center - 2, center - 2), size // 12)


# Global icon generator instance
icon_generator = IconGenerator()

