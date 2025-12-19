"""Items, equipment, and loot generation."""

import random
from ..engine.constants import (
    RARITY_COMMON, RARITY_UNCOMMON, RARITY_RARE, RARITY_LEGENDARY,
    RARITY_COLORS, SLOT_MAIN_HAND, SLOT_OFF_HAND, SLOT_HEAD, 
    SLOT_CHEST, SLOT_HANDS, SLOT_LEGS, SLOT_FEET,
    ATTACK_RANGE_MELEE, ATTACK_RANGE_RANGED, ATTACK_RANGE_MAGIC
)


class Item:
    """Base item class."""
    
    _next_id = 0
    
    def __init__(self, name, weight=1.0, value=0, rarity=RARITY_COMMON):
        self.id = Item._next_id
        Item._next_id += 1
        
        self.name = name
        self.weight = weight
        self.value = value
        self.rarity = rarity
        self.stackable = False
        self.stack_count = 1
        self.max_stack = 1
    
    @property
    def color(self):
        return RARITY_COLORS.get(self.rarity, (200, 200, 200))
    
    def __repr__(self):
        return f"<Item: {self.name}>"


class Equipment(Item):
    """Equippable item with stats."""
    
    def __init__(self, name, slot, weight=2.0, value=10, rarity=RARITY_COMMON):
        super().__init__(name, weight, value, rarity)
        self.slot = slot
        
        # Combat stats
        self.armor = 0
        self.damage = 0
        self.attack_range = ATTACK_RANGE_MELEE
        self.weapon_type = 'melee'  # melee, ranged, magic
        
        # Bonus stats
        self.strength_bonus = 0
        self.dexterity_bonus = 0
        self.intelligence_bonus = 0
        self.health_bonus = 0
        self.mana_bonus = 0
        
        # Requirements
        self.level_req = 1
        self.strength_req = 0
        self.dexterity_req = 0
        self.intelligence_req = 0


class Consumable(Item):
    """Usable item like potions."""
    
    def __init__(self, name, effect_type, effect_value, weight=0.5, value=5):
        super().__init__(name, weight, value, RARITY_COMMON)
        self.effect_type = effect_type  # 'heal', 'mana', 'buff'
        self.effect_value = effect_value
        self.stackable = True
        self.max_stack = 20
    
    def use(self, character):
        """Apply consumable effect."""
        if self.effect_type == 'heal':
            character.heal(self.effect_value)
            return True
        elif self.effect_type == 'mana':
            character.restore_mana(self.effect_value)
            return True
        return False


# Item templates
WEAPON_TEMPLATES = {
    # Melee
    'short_sword': {'slot': SLOT_MAIN_HAND, 'damage': 8, 'type': 'melee', 'weight': 3},
    'longsword': {'slot': SLOT_MAIN_HAND, 'damage': 12, 'type': 'melee', 'weight': 5},
    'battle_axe': {'slot': SLOT_MAIN_HAND, 'damage': 15, 'type': 'melee', 'weight': 7},
    'mace': {'slot': SLOT_MAIN_HAND, 'damage': 10, 'type': 'melee', 'weight': 6},
    'dagger': {'slot': SLOT_MAIN_HAND, 'damage': 5, 'type': 'melee', 'weight': 1},
    
    # Ranged
    'short_bow': {'slot': SLOT_MAIN_HAND, 'damage': 7, 'type': 'ranged', 'weight': 2, 'range': ATTACK_RANGE_RANGED},
    'longbow': {'slot': SLOT_MAIN_HAND, 'damage': 11, 'type': 'ranged', 'weight': 3, 'range': ATTACK_RANGE_RANGED},
    'crossbow': {'slot': SLOT_MAIN_HAND, 'damage': 14, 'type': 'ranged', 'weight': 5, 'range': ATTACK_RANGE_RANGED},
    
    # Magic
    'staff': {'slot': SLOT_MAIN_HAND, 'damage': 6, 'type': 'magic', 'weight': 4, 'range': ATTACK_RANGE_MAGIC},
    'wand': {'slot': SLOT_MAIN_HAND, 'damage': 8, 'type': 'magic', 'weight': 1, 'range': ATTACK_RANGE_MAGIC},
    'orb': {'slot': SLOT_OFF_HAND, 'damage': 4, 'type': 'magic', 'weight': 2, 'range': ATTACK_RANGE_MAGIC},
}

ARMOR_TEMPLATES = {
    # Head
    'leather_cap': {'slot': SLOT_HEAD, 'armor': 2, 'weight': 1},
    'chain_coif': {'slot': SLOT_HEAD, 'armor': 4, 'weight': 2},
    'plate_helm': {'slot': SLOT_HEAD, 'armor': 6, 'weight': 4},
    
    # Chest
    'leather_armor': {'slot': SLOT_CHEST, 'armor': 5, 'weight': 5},
    'chain_mail': {'slot': SLOT_CHEST, 'armor': 10, 'weight': 12},
    'plate_armor': {'slot': SLOT_CHEST, 'armor': 15, 'weight': 20},
    
    # Hands
    'leather_gloves': {'slot': SLOT_HANDS, 'armor': 1, 'weight': 0.5},
    'chain_gloves': {'slot': SLOT_HANDS, 'armor': 2, 'weight': 1},
    'plate_gauntlets': {'slot': SLOT_HANDS, 'armor': 3, 'weight': 2},
    
    # Legs
    'leather_pants': {'slot': SLOT_LEGS, 'armor': 3, 'weight': 2},
    'chain_leggings': {'slot': SLOT_LEGS, 'armor': 6, 'weight': 6},
    'plate_greaves': {'slot': SLOT_LEGS, 'armor': 9, 'weight': 10},
    
    # Feet
    'leather_boots': {'slot': SLOT_FEET, 'armor': 1, 'weight': 1},
    'chain_boots': {'slot': SLOT_FEET, 'armor': 2, 'weight': 2},
    'plate_boots': {'slot': SLOT_FEET, 'armor': 3, 'weight': 3},
    
    # Off-hand
    'buckler': {'slot': SLOT_OFF_HAND, 'armor': 3, 'weight': 3},
    'kite_shield': {'slot': SLOT_OFF_HAND, 'armor': 6, 'weight': 6},
    'tower_shield': {'slot': SLOT_OFF_HAND, 'armor': 10, 'weight': 12},
}

PREFIXES = {
    RARITY_UNCOMMON: ['Sturdy', 'Sharp', 'Reinforced', 'Fine'],
    RARITY_RARE: ['Masterwork', 'Enchanted', 'Blessed', 'Runic'],
    RARITY_LEGENDARY: ['Legendary', 'Ancient', 'Divine', 'Mythic'],
}

SUFFIXES = {
    RARITY_UNCOMMON: ['of Might', 'of Speed', 'of Wisdom', 'of Fortitude'],
    RARITY_RARE: ['of Power', 'of the Hawk', 'of the Sage', 'of Giants'],
    RARITY_LEGENDARY: ['of Destruction', 'of the Gods', 'of Eternity', 'of Doom'],
}


def create_weapon(template_name, rarity=RARITY_COMMON, level=1):
    """Create a weapon from template."""
    template = WEAPON_TEMPLATES.get(template_name)
    if not template:
        return None
    
    name = template_name.replace('_', ' ').title()
    
    # Add prefix/suffix for higher rarity
    if rarity >= RARITY_UNCOMMON:
        if random.random() < 0.5:
            prefix = random.choice(PREFIXES.get(rarity, PREFIXES[RARITY_UNCOMMON]))
            name = f"{prefix} {name}"
        else:
            suffix = random.choice(SUFFIXES.get(rarity, SUFFIXES[RARITY_UNCOMMON]))
            name = f"{name} {suffix}"
    
    weapon = Equipment(name, template['slot'], template['weight'], rarity=rarity)
    
    # Base damage scaled by level and rarity
    rarity_mult = 1.0 + rarity * 0.25
    level_mult = 1.0 + (level - 1) * 0.1
    weapon.damage = int(template['damage'] * rarity_mult * level_mult)
    weapon.weapon_type = template['type']
    weapon.attack_range = template.get('range', ATTACK_RANGE_MELEE)
    weapon.level_req = level
    
    # Add bonus stats based on rarity
    if rarity >= RARITY_UNCOMMON:
        stat_points = rarity * 2 * level
        for _ in range(stat_points):
            stat = random.choice(['strength', 'dexterity', 'intelligence'])
            if stat == 'strength':
                weapon.strength_bonus += 1
            elif stat == 'dexterity':
                weapon.dexterity_bonus += 1
            else:
                weapon.intelligence_bonus += 1
    
    weapon.value = int(weapon.damage * 5 * rarity_mult)
    
    return weapon


def create_armor(template_name, rarity=RARITY_COMMON, level=1):
    """Create armor from template."""
    template = ARMOR_TEMPLATES.get(template_name)
    if not template:
        return None
    
    name = template_name.replace('_', ' ').title()
    
    if rarity >= RARITY_UNCOMMON:
        if random.random() < 0.5:
            prefix = random.choice(PREFIXES.get(rarity, PREFIXES[RARITY_UNCOMMON]))
            name = f"{prefix} {name}"
        else:
            suffix = random.choice(SUFFIXES.get(rarity, SUFFIXES[RARITY_UNCOMMON]))
            name = f"{name} {suffix}"
    
    armor = Equipment(name, template['slot'], template['weight'], rarity=rarity)
    
    rarity_mult = 1.0 + rarity * 0.25
    level_mult = 1.0 + (level - 1) * 0.1
    armor.armor = int(template['armor'] * rarity_mult * level_mult)
    armor.level_req = level
    
    # Add bonus stats
    if rarity >= RARITY_UNCOMMON:
        stat_points = rarity * level
        for _ in range(stat_points):
            bonus = random.choice(['health', 'mana', 'strength', 'dexterity', 'intelligence'])
            if bonus == 'health':
                armor.health_bonus += 5
            elif bonus == 'mana':
                armor.mana_bonus += 3
            elif bonus == 'strength':
                armor.strength_bonus += 1
            elif bonus == 'dexterity':
                armor.dexterity_bonus += 1
            else:
                armor.intelligence_bonus += 1
    
    armor.value = int(armor.armor * 8 * rarity_mult)
    
    return armor


def create_potion(potion_type, level=1):
    """Create a potion."""
    if potion_type == 'health':
        value = 20 + level * 10
        return Consumable(f"Health Potion", 'heal', value, value=value // 2)
    elif potion_type == 'mana':
        value = 15 + level * 8
        return Consumable(f"Mana Potion", 'mana', value, value=value // 2)
    return None


def generate_loot(level, enemy_type=None):
    """Generate random loot based on level."""
    loot = []
    
    # Gold
    gold = random.randint(level * 5, level * 20)
    
    # Chance for items
    if random.random() < 0.4:  # 40% chance for potion
        potion_type = random.choice(['health', 'mana'])
        potion = create_potion(potion_type, level)
        if potion:
            loot.append(potion)
    
    # Chance for equipment
    if random.random() < 0.25:  # 25% chance
        # Determine rarity
        roll = random.random()
        if roll < 0.02:
            rarity = RARITY_LEGENDARY
        elif roll < 0.10:
            rarity = RARITY_RARE
        elif roll < 0.35:
            rarity = RARITY_UNCOMMON
        else:
            rarity = RARITY_COMMON
        
        # Weapon or armor
        if random.random() < 0.4:
            template = random.choice(list(WEAPON_TEMPLATES.keys()))
            item = create_weapon(template, rarity, level)
        else:
            template = random.choice(list(ARMOR_TEMPLATES.keys()))
            item = create_armor(template, rarity, level)
        
        if item:
            loot.append(item)
    
    return {'gold': gold, 'items': loot}

