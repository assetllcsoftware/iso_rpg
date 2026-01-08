"""Save and load game state."""

import os
import json
import esper
from typing import Dict, Any, Optional
from dataclasses import asdict

from ..components import (
    Position, Health, Mana, Attributes, SkillLevels, SkillXP, CharacterLevel,
    CharacterName, CharacterClass, PartyMember, Equipment, SpellBook, Gold,
    Inventory as InventoryComp
)
from ...core.events import EventBus, Event, EventType


SAVE_DIR = "saves"
SAVE_FILE = "game.json"


class SaveLoadProcessor(esper.Processor):
    """Handles saving and loading game state."""
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.pending_save = False
        self.pending_load = False
        
        # Dungeon info (set by game)
        self._dungeon_level = 1
        self._dungeon_seed = None
        
        # Subscribe to events
        self.event_bus.subscribe(EventType.GAME_SAVE_REQUESTED, self._on_save_requested)
        self.event_bus.subscribe(EventType.GAME_LOAD_REQUESTED, self._on_load_requested)
        
        # Ensure save directory exists
        os.makedirs(SAVE_DIR, exist_ok=True)
    
    def _on_save_requested(self, event: Event):
        """Handle save request."""
        self.pending_save = True
    
    def _on_load_requested(self, event: Event):
        """Handle load request."""
        self.pending_load = True
    
    def process(self, dt: float):
        """Process pending save/load."""
        if self.pending_save:
            self._do_save()
            self.pending_save = False
        
        if self.pending_load:
            self._do_load()
            self.pending_load = False
    
    def _do_save(self):
        """Perform save operation."""
        try:
            save_data = self._gather_save_data()
            
            save_path = os.path.join(SAVE_DIR, SAVE_FILE)
            with open(save_path, 'w') as f:
                json.dump(save_data, f, indent=2)
            
            self.event_bus.emit(Event(EventType.GAME_SAVED, {
                "path": save_path
            }))
            
            self.event_bus.emit(Event(EventType.NOTIFICATION, {
                "text": "Game Saved!",
                "color": (100, 255, 150)
            }))
        except Exception as e:
            self.event_bus.emit(Event(EventType.NOTIFICATION, {
                "text": f"Save failed: {str(e)}",
                "color": (255, 100, 100)
            }))
    
    def _do_load(self):
        """Perform load operation."""
        save_path = os.path.join(SAVE_DIR, SAVE_FILE)
        
        if not os.path.exists(save_path):
            self.event_bus.emit(Event(EventType.NOTIFICATION, {
                "text": "No save file found!",
                "color": (255, 200, 100)
            }))
            return
        
        try:
            with open(save_path, 'r') as f:
                save_data = json.load(f)
            
            # Get dungeon info BEFORE restoring (we need to regenerate first)
            dungeon_level = save_data.get("dungeon_level", 1)
            dungeon_seed = save_data.get("dungeon_seed")
            
            # Emit event to regenerate dungeon with same seed
            total_gold = save_data.get("total_gold", 0)
            print(f"[LOAD DEBUG] Read from save file: total_gold={total_gold}")
            self.event_bus.emit(Event(EventType.GAME_LOADED, {
                "path": save_path,
                "dungeon_level": dungeon_level,
                "dungeon_seed": dungeon_seed,
                "total_gold": total_gold,
                "party_data": save_data.get("party", [])
            }))
            
            self.event_bus.emit(Event(EventType.NOTIFICATION, {
                "text": "Game Loaded!",
                "color": (100, 255, 150)
            }))
        except Exception as e:
            self.event_bus.emit(Event(EventType.NOTIFICATION, {
                "text": f"Load failed: {str(e)}",
                "color": (255, 100, 100)
            }))
    
    def _gather_save_data(self) -> Dict[str, Any]:
        """Gather all saveable data."""
        data = {
            "version": 1,
            "party": [],
            "dungeon_level": self._dungeon_level,
            "dungeon_seed": self._dungeon_seed,
            "total_gold": 0,
        }
        
        # Save party members
        for ent, (member,) in esper.get_components(PartyMember):
            char_data = self._save_character(ent)
            data["party"].append(char_data)
            
            # Track total gold (only from party leader - index 0)
            if member.party_index == 0 and esper.has_component(ent, Gold):
                gold = esper.component_for_entity(ent, Gold)
                data["total_gold"] = gold.amount
                print(f"[SAVE DEBUG] Saving gold amount: {gold.amount}")
        
        return data
    
    def set_dungeon_info(self, level: int, seed: int):
        """Set dungeon info for saving. Called by game when level changes."""
        self._dungeon_level = level
        self._dungeon_seed = seed
    
    def _save_character(self, ent: int) -> Dict[str, Any]:
        """Save a character entity."""
        char = {}
        
        if esper.has_component(ent, CharacterName):
            char["name"] = esper.component_for_entity(ent, CharacterName).name
        
        if esper.has_component(ent, CharacterClass):
            char["class"] = esper.component_for_entity(ent, CharacterClass).class_name
        
        if esper.has_component(ent, CharacterLevel):
            char["level"] = esper.component_for_entity(ent, CharacterLevel).level
        
        if esper.has_component(ent, Position):
            pos = esper.component_for_entity(ent, Position)
            char["position"] = {"x": pos.x, "y": pos.y}
        
        if esper.has_component(ent, Health):
            health = esper.component_for_entity(ent, Health)
            char["health"] = {"current": health.current, "maximum": health.maximum}
        
        if esper.has_component(ent, Mana):
            mana = esper.component_for_entity(ent, Mana)
            char["mana"] = {"current": mana.current, "maximum": mana.maximum}
        
        if esper.has_component(ent, Attributes):
            attrs = esper.component_for_entity(ent, Attributes)
            char["attributes"] = {
                "strength": attrs.strength,
                "dexterity": attrs.dexterity,
                "intelligence": attrs.intelligence
            }
        
        if esper.has_component(ent, SkillLevels):
            skills = esper.component_for_entity(ent, SkillLevels)
            char["skills"] = {
                "melee": skills.melee,
                "ranged": skills.ranged,
                "combat_magic": skills.combat_magic,
                "nature_magic": skills.nature_magic
            }
        
        if esper.has_component(ent, SkillXP):
            xp = esper.component_for_entity(ent, SkillXP)
            char["skill_xp"] = {
                "melee": xp.melee,
                "ranged": xp.ranged,
                "combat_magic": xp.combat_magic,
                "nature_magic": xp.nature_magic
            }
        
        if esper.has_component(ent, SpellBook):
            spellbook = esper.component_for_entity(ent, SpellBook)
            char["spells"] = list(spellbook.known_spells)
        
        if esper.has_component(ent, PartyMember):
            member = esper.component_for_entity(ent, PartyMember)
            char["party_index"] = member.party_index
        
        # Save inventory
        if esper.has_component(ent, InventoryComp):
            inv = esper.component_for_entity(ent, InventoryComp)
            char["inventory"] = []
            for item in inv.items:
                item_data = {
                    "item_id": item.item_id if hasattr(item, 'item_id') else str(item),
                    "quantity": getattr(item, 'quantity', 1)
                }
                char["inventory"].append(item_data)
        
        # Save equipment
        if esper.has_component(ent, Equipment):
            equip = esper.component_for_entity(ent, Equipment)
            char["equipment"] = {}
            for slot in ['head', 'chest', 'hands', 'legs', 'feet', 'main_hand', 'off_hand', 'amulet', 'ring_1', 'ring_2']:
                item = equip.get(slot)
                if item:
                    char["equipment"][slot] = item if isinstance(item, str) else (item.item_id if hasattr(item, 'item_id') else str(item))
        
        return char
    
    def _restore_save_data(self, data: Dict[str, Any]):
        """Restore saved data to current entities."""
        party_by_index = {}
        
        # Index current party members
        for ent, (member,) in esper.get_components(PartyMember):
            party_by_index[member.party_index] = ent
        
        # Restore each saved character
        for char_data in data.get("party", []):
            party_idx = char_data.get("party_index", 0)
            
            if party_idx in party_by_index:
                ent = party_by_index[party_idx]
                self._restore_character(ent, char_data)
    
    def _restore_character(self, ent: int, data: Dict[str, Any]):
        """Restore character data to entity."""
        if "position" in data and esper.has_component(ent, Position):
            pos = esper.component_for_entity(ent, Position)
            pos.x = data["position"]["x"]
            pos.y = data["position"]["y"]
        
        if "health" in data and esper.has_component(ent, Health):
            health = esper.component_for_entity(ent, Health)
            health.current = data["health"]["current"]
            health.maximum = data["health"]["maximum"]
        
        if "mana" in data and esper.has_component(ent, Mana):
            mana = esper.component_for_entity(ent, Mana)
            mana.current = data["mana"]["current"]
            mana.maximum = data["mana"]["maximum"]
        
        if "attributes" in data and esper.has_component(ent, Attributes):
            attrs = esper.component_for_entity(ent, Attributes)
            attrs.strength = data["attributes"]["strength"]
            attrs.dexterity = data["attributes"]["dexterity"]
            attrs.intelligence = data["attributes"]["intelligence"]
        
        if "skills" in data and esper.has_component(ent, SkillLevels):
            skills = esper.component_for_entity(ent, SkillLevels)
            skills.melee = data["skills"]["melee"]
            skills.ranged = data["skills"]["ranged"]
            skills.combat_magic = data["skills"]["combat_magic"]
            skills.nature_magic = data["skills"]["nature_magic"]
        
        if "skill_xp" in data and esper.has_component(ent, SkillXP):
            xp = esper.component_for_entity(ent, SkillXP)
            xp.melee = data["skill_xp"]["melee"]
            xp.ranged = data["skill_xp"]["ranged"]
            xp.combat_magic = data["skill_xp"]["combat_magic"]
            xp.nature_magic = data["skill_xp"]["nature_magic"]
        
        if "level" in data and esper.has_component(ent, CharacterLevel):
            level = esper.component_for_entity(ent, CharacterLevel)
            level.level = data["level"]
        
        if "spells" in data and esper.has_component(ent, SpellBook):
            spellbook = esper.component_for_entity(ent, SpellBook)
            spellbook.known_spells = list(data["spells"])  # Keep as list to preserve order
        
        # Restore inventory
        if "inventory" in data and esper.has_component(ent, InventoryComp):
            from ..components.equipment import InventoryItem
            inv = esper.component_for_entity(ent, InventoryComp)
            inv.items = []
            for item_data in data["inventory"]:
                item = InventoryItem(
                    item_id=item_data["item_id"],
                    quantity=item_data.get("quantity", 1)
                )
                inv.items.append(item)
        
        # Restore equipment
        if "equipment" in data and esper.has_component(ent, Equipment):
            equip = esper.component_for_entity(ent, Equipment)
            for slot, item_id in data["equipment"].items():
                if item_id:
                    equip.equip(slot, item_id)
    
    def has_save_file(self) -> bool:
        """Check if a save file exists."""
        return os.path.exists(os.path.join(SAVE_DIR, SAVE_FILE))
    
    def quick_save(self):
        """Immediate save (F5 key)."""
        self.pending_save = True
    
    def quick_load(self):
        """Immediate load (F9 key)."""
        self.pending_load = True

