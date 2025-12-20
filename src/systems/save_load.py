"""Save and load game state."""

import json
import os
from datetime import datetime


SAVE_DIR = "saves"


def ensure_save_dir():
    """Make sure save directory exists."""
    if not os.path.exists(SAVE_DIR):
        os.makedirs(SAVE_DIR)


def serialize_character(char):
    """Convert character to saveable dict."""
    data = {
        'name': char.name,
        'char_class': getattr(char, 'char_class', 'warrior'),
        'x': char.x,
        'y': char.y,
        'level': char.level,
        'experience': char.experience,
        'health': char.health,
        'max_health': char.max_health,
        'mana': char.mana,
        'max_mana': char.max_mana,
        'strength': char.strength,
        'dexterity': char.dexterity,
        'intelligence': char.intelligence,
        'skills': char.skills,
        'skill_xp': char.skill_xp,
        'gold': char.gold,
        'is_player_controlled': char.is_player_controlled,
        'color': char.color,
        'inventory': [serialize_item(item) for item in char.inventory if item],
        'equipment': {
            slot: serialize_item(item) if item else None
            for slot, item in char.equipment.items()
        },
        'spells_known': list(char.spellbook.spells.keys()) if hasattr(char, 'spellbook') else [],
        # Downed state
        'is_downed': getattr(char, 'is_downed', False),
        'down_timer': getattr(char, 'down_timer', 0.0),
        # Formation
        'formation_offset': getattr(char, 'formation_offset', (1.5, 1.5)),
    }
    return data


def serialize_item(item):
    """Convert item to saveable dict."""
    if item is None:
        return None
    
    data = {
        'name': item.name,
        'weight': item.weight,
        'value': item.value,
        'rarity': item.rarity,
    }
    
    # Equipment specific
    if hasattr(item, 'slot'):
        data['type'] = 'equipment'
        data['slot'] = item.slot
        data['armor'] = getattr(item, 'armor', 0)
        data['damage'] = getattr(item, 'damage', 0)
        data['weapon_type'] = getattr(item, 'weapon_type', 'melee')
        data['attack_range'] = getattr(item, 'attack_range', 1.5)
        data['strength_bonus'] = getattr(item, 'strength_bonus', 0)
        data['dexterity_bonus'] = getattr(item, 'dexterity_bonus', 0)
        data['intelligence_bonus'] = getattr(item, 'intelligence_bonus', 0)
        data['health_bonus'] = getattr(item, 'health_bonus', 0)
        data['mana_bonus'] = getattr(item, 'mana_bonus', 0)
        data['level_req'] = getattr(item, 'level_req', 1)
    
    # Consumable specific
    if hasattr(item, 'effect_type'):
        data['type'] = 'consumable'
        data['effect_type'] = item.effect_type
        data['effect_value'] = item.effect_value
    
    return data


def deserialize_item(data):
    """Recreate item from saved data."""
    if data is None:
        return None
    
    from ..entities.item import Equipment, Consumable
    
    if data.get('type') == 'consumable':
        item = Consumable(
            data['name'],
            data['effect_type'],
            data['effect_value'],
            data['weight'],
            data['value']
        )
        item.rarity = data['rarity']
        return item
    
    elif data.get('type') == 'equipment':
        item = Equipment(
            data['name'],
            data['slot'],
            data['weight'],
            data['value'],
            data['rarity']
        )
        item.armor = data.get('armor', 0)
        item.damage = data.get('damage', 0)
        item.weapon_type = data.get('weapon_type', 'melee')
        item.attack_range = data.get('attack_range', 1.5)
        item.strength_bonus = data.get('strength_bonus', 0)
        item.dexterity_bonus = data.get('dexterity_bonus', 0)
        item.intelligence_bonus = data.get('intelligence_bonus', 0)
        item.health_bonus = data.get('health_bonus', 0)
        item.mana_bonus = data.get('mana_bonus', 0)
        item.level_req = data.get('level_req', 1)
        return item
    
    return None


def deserialize_character(data, is_main=False):
    """Recreate character from saved data."""
    from ..entities.character import Character
    from ..systems.magic import SpellBook
    
    char = Character(data['name'], data['x'], data['y'])
    
    # Class (v2+)
    char.char_class = data.get('char_class', 'warrior')
    
    char.level = data['level']
    char.experience = data['experience']
    char.health = data['health']
    char.max_health = data['max_health']
    char.mana = data['mana']
    char.max_mana = data['max_mana']
    char.strength = data['strength']
    char.dexterity = data['dexterity']
    char.intelligence = data['intelligence']
    char.skills = data['skills']
    char.skill_xp = data['skill_xp']
    char.gold = data['gold']
    char.is_player_controlled = data['is_player_controlled']
    char.color = tuple(data['color'])
    
    # Inventory
    char.inventory = [deserialize_item(item) for item in data['inventory']]
    char.inventory = [i for i in char.inventory if i]  # Remove None
    
    # Equipment
    for slot, item_data in data['equipment'].items():
        char.equipment[slot] = deserialize_item(item_data)
    
    # Spells - restore exactly what was saved
    char.spellbook = SpellBook()
    for spell_id in data.get('spells_known', []):
        char.spellbook.learn_spell(spell_id)
    
    # Downed state (v2+)
    char.is_downed = data.get('is_downed', False)
    char.down_timer = data.get('down_timer', 0.0)
    
    # Formation (v2+)
    offset = data.get('formation_offset', (1.5, 1.5))
    char.formation_offset = tuple(offset) if isinstance(offset, list) else offset
    
    return char


SAVE_VERSION = 2  # Increment on breaking changes

def save_game(game, slot=1):
    """Save the current game state."""
    ensure_save_dir()
    
    save_data = {
        'version': SAVE_VERSION,
        'game_version': '0.1.0',  # Game version string
        'timestamp': datetime.now().isoformat(),
        'dungeon_level': game.world.level,
        'dungeon_seed': getattr(game.world, 'dungeon_seed', None),
        'gold': game.gold,
        'party': [serialize_character(char) for char in game.party],
    }
    
    filename = os.path.join(SAVE_DIR, f"save_{slot}.json")
    
    with open(filename, 'w') as f:
        json.dump(save_data, f, indent=2)
    
    return filename


def load_game(game, slot=1):
    """Load a saved game state."""
    filename = os.path.join(SAVE_DIR, f"save_{slot}.json")
    
    if not os.path.exists(filename):
        return False
    
    with open(filename, 'r') as f:
        save_data = json.load(f)
    
    # Regenerate dungeon at saved level with same seed
    dungeon_level = save_data['dungeon_level']
    dungeon_seed = save_data.get('dungeon_seed')
    game.world.generate_dungeon(level=dungeon_level, seed=dungeon_seed)
    
    # Recreate party
    game.party = []
    main_char = None
    
    for i, char_data in enumerate(save_data['party']):
        char = deserialize_character(char_data, is_main=(i == 0))
        game.party.append(char)
        
        if char.is_player_controlled and main_char is None:
            main_char = char
    
    # Setup party relationships
    if len(game.party) > 1 and main_char:
        for char in game.party[1:]:
            char.follow_target = main_char
            char.formation_offset = (1.5, 1.5)
    
    game.world.characters = game.party
    game.selected_character = main_char or game.party[0]
    game.gold = save_data['gold']
    game.target = None
    
    # Center camera
    game.camera.follow(game.selected_character.x, game.selected_character.y, instant=True)
    
    return True


def get_save_info(slot=1):
    """Get info about a save file."""
    filename = os.path.join(SAVE_DIR, f"save_{slot}.json")
    
    if not os.path.exists(filename):
        return None
    
    with open(filename, 'r') as f:
        data = json.load(f)
    
    return {
        'version': data.get('version', 1),
        'game_version': data.get('game_version', 'unknown'),
        'timestamp': data['timestamp'],
        'dungeon_level': data['dungeon_level'],
        'dungeon_seed': data.get('dungeon_seed'),
        'party_size': len(data['party']),
        'main_char': data['party'][0]['name'] if data['party'] else 'Unknown',
        'main_level': data['party'][0]['level'] if data['party'] else 1,
    }


def delete_save(slot=1):
    """Delete a save file."""
    filename = os.path.join(SAVE_DIR, f"save_{slot}.json")
    if os.path.exists(filename):
        os.remove(filename)
        return True
    return False

