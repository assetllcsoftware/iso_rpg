"""ECS Processors - all game logic lives here."""

from .input_processor import InputProcessor
from .movement_processor import MovementProcessor
from .combat_processor import CombatProcessor
from .ai_processor import AIProcessor
from .magic_processor import MagicProcessor
from .animation_processor import AnimationProcessor
from .progression_processor import ProgressionProcessor
from .loot_processor import LootProcessor
from .cleanup_processor import CleanupProcessor
from .save_load_processor import SaveLoadProcessor
from .world_processor import WorldProcessor, DroppedItemProcessor
from .regen_processor import RegenProcessor
from .position_validator import PositionValidator

__all__ = [
    'InputProcessor',
    'MovementProcessor',
    'CombatProcessor',
    'AIProcessor',
    'MagicProcessor',
    'AnimationProcessor',
    'ProgressionProcessor',
    'LootProcessor',
    'CleanupProcessor',
    'SaveLoadProcessor',
    'WorldProcessor',
    'DroppedItemProcessor',
    'RegenProcessor',
    'PositionValidator',
]
