"""YAML data loader for game content."""

import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path


class DataLoader:
    """Loads and caches game data from YAML files."""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self._cache: Dict[str, Dict] = {}
    
    def _load_yaml(self, filename: str) -> Dict:
        """Load a YAML file, using cache if available."""
        if filename in self._cache:
            return self._cache[filename]
        
        filepath = self.data_dir / filename
        if not filepath.exists():
            raise FileNotFoundError(f"Data file not found: {filepath}")
        
        with open(filepath, 'r') as f:
            data = yaml.safe_load(f)
        
        self._cache[filename] = data or {}
        return self._cache[filename]
    
    def get_character(self, char_id: str) -> Optional[Dict]:
        """Get character definition by ID."""
        data = self._load_yaml("characters.yaml")
        return data.get(char_id)
    
    def get_enemy(self, enemy_id: str) -> Optional[Dict]:
        """Get enemy definition by ID."""
        data = self._load_yaml("enemies.yaml")
        return data.get(enemy_id)
    
    def get_item(self, item_id: str) -> Optional[Dict]:
        """Get item definition by ID."""
        data = self._load_yaml("items.yaml")
        return data.get(item_id)
    
    def get_spell(self, spell_id: str) -> Optional[Dict]:
        """Get spell definition by ID."""
        data = self._load_yaml("spells.yaml")
        return data.get(spell_id)
    
    def get_loot_table(self, table_id: str) -> Optional[Dict]:
        """Get loot table definition by ID."""
        data = self._load_yaml("loot_tables.yaml")
        return data.get(table_id)
    
    def get_dungeon_config(self, dungeon_id: str = "temple_dungeon") -> Optional[Dict]:
        """Get dungeon configuration by ID."""
        data = self._load_yaml("dungeon.yaml")
        return data.get(dungeon_id)
    
    def get_all_enemies(self) -> Dict[str, Dict]:
        """Get all enemy definitions."""
        return self._load_yaml("enemies.yaml")
    
    def get_all_items(self) -> Dict[str, Dict]:
        """Get all item definitions."""
        return self._load_yaml("items.yaml")
    
    def get_all_spells(self) -> Dict[str, Dict]:
        """Get all spell definitions."""
        return self._load_yaml("spells.yaml")
    
    def reload(self):
        """Clear cache and reload all data."""
        self._cache.clear()


# Global instance
data_loader = DataLoader()

