"""Event bus for decoupled system communication.

Systems emit events, other systems subscribe to react.
This keeps systems isolated from each other.
"""

from enum import Enum, auto
from typing import Callable, Dict, List, Any
from dataclasses import dataclass, field


class EventType(Enum):
    """All event types in the game.
    
    See docs for payload schemas:
    - DAMAGE_DEALT: source, target, amount, damage_type, is_critical, overkill
    - ENTITY_DIED: entity, killer, death_type
    - SPELL_CAST: caster, spell, target, mana_cost
    - etc.
    """
    
    # =========================================================================
    # COMBAT
    # =========================================================================
    DAMAGE_DEALT = auto()       # source, target, amount, damage_type, is_critical
    ENTITY_DIED = auto()        # entity, killer, death_type
    ENTITY_DOWNED = auto()      # entity (party member downed, can be revived)
    ENTITY_REVIVED = auto()     # entity, reviver, health_percent
    ATTACK_STARTED = auto()     # attacker, target, weapon
    COMBAT_STARTED = auto()     # party, enemies (entered combat)
    COMBAT_ENDED = auto()       # duration, enemies_killed
    
    # =========================================================================
    # MAGIC
    # =========================================================================
    SPELL_CAST = auto()         # caster, spell, target, mana_cost
    SPELL_CAST_REQUESTED = auto() # caster, slot, target_id, target_x, target_y
    SPELL_HIT = auto()          # caster, spell, target, damage, effects
    PROJECTILE_CREATED = auto() # projectile, source, target
    PROJECTILE_HIT = auto()     # projectile, hit_entity, position
    HEALTH_RESTORED = auto()    # healer, target, amount
    
    # =========================================================================
    # PROGRESSION
    # =========================================================================
    SKILL_XP_GAINED = auto()    # character, skill, amount, source
    SKILL_LEVEL_UP = auto()     # character, skill, new_level, stat_bonuses
    CHARACTER_LEVEL_UP = auto() # character, new_level, old_level
    LEVEL_UP = auto()           # entity, skill, new_level (alias for processors)
    SPELL_UNLOCKED = auto()     # character, spell, skill, skill_level
    
    # =========================================================================
    # ITEMS
    # =========================================================================
    ITEM_PICKED_UP = auto()     # character, item, source
    ITEM_DROPPED = auto()       # character, item, position
    ITEM_EQUIPPED = auto()      # character, item, slot, previous_item
    ITEM_UNEQUIPPED = auto()    # character, item, slot
    ITEM_USED = auto()          # character, item, effect_type, effect_value
    ITEM_TRANSFERRED = auto()   # item, from_character, to_character
    GOLD_CHANGED = auto()       # character, amount, new_total, reason
    
    # =========================================================================
    # WORLD
    # =========================================================================
    LEVEL_CHANGED = auto()      # new_level, old_level, direction
    DUNGEON_GENERATED = auto()  # level, width, height, room_count, enemy_count
    STAIRS_USED = auto()        # position, direction
    TOWN_ENTERED = auto()       # from_level
    TOWN_LEFT = auto()          # target_level
    
    # =========================================================================
    # TRADING
    # =========================================================================
    TRADE_STARTED = auto()      # merchant, character
    TRADE_COMPLETED = auto()    # merchant, items_bought, items_sold, gold_spent
    ITEM_BOUGHT = auto()        # character, item, price
    ITEM_SOLD = auto()          # character, item, price
    
    # =========================================================================
    # UI
    # =========================================================================
    NOTIFICATION = auto()       # message, type
    MENU_OPENED = auto()        # menu_type
    MENU_CLOSED = auto()        # menu_type
    INVENTORY_OPENED = auto()   # character
    INVENTORY_CLOSED = auto()
    CHARACTER_SELECTED = auto() # character, previous
    CAMERA_ZOOMED = auto()      # direction
    
    # =========================================================================
    # STATUS EFFECTS
    # =========================================================================
    STATUS_APPLIED = auto()     # entity, effect_type, duration, source
    STATUS_EXPIRED = auto()     # entity, effect_type
    STATUS_TICK = auto()        # entity, effect_type, damage
    
    # =========================================================================
    # MOVEMENT
    # =========================================================================
    PATH_CALCULATED = auto()    # entity, start, end, path_length
    ENTITY_STUCK = auto()       # entity, position, target
    ENTITY_TELEPORTED = auto()  # entity, from_position, to_position, reason
    
    # =========================================================================
    # GAME FLOW
    # =========================================================================
    GAME_STARTED = auto()       # new_game, loaded_save
    GAME_PAUSED = auto()
    GAME_RESUMED = auto()
    GAME_SAVE_REQUESTED = auto() # slot (F5 quick save)
    GAME_LOAD_REQUESTED = auto() # slot (F9 quick load)
    GAME_SAVED = auto()         # slot, timestamp, playtime
    GAME_LOADED = auto()        # slot, level
    AUTOSAVE_TRIGGERED = auto()
    PARTY_WIPED = auto()        # level, gold_lost
    PARTY_RESPAWNED = auto()    # position, gold_before, gold_after
    GAME_OVER = auto()          # reason
    
    # =========================================================================
    # ACTION BAR
    # =========================================================================
    ACTION_BAR_USED = auto()    # slot


@dataclass
class Event:
    """An event with type and data payload."""
    type: EventType
    data: Dict[str, Any] = field(default_factory=dict)


class EventBus:
    """Central event dispatcher.
    
    Usage:
        bus = EventBus()
        
        # Subscribe to events
        bus.subscribe(EventType.ENTITY_DIED, my_handler)
        
        # Emit events (queued for processing)
        bus.emit(EventType.ENTITY_DIED, entity_id=42, killer_id=1)
        
        # Process all queued events (call once per frame)
        bus.process()
    """
    
    def __init__(self):
        self._subscribers: Dict[EventType, List[Callable]] = {}
        self._queue: List[Event] = []
    
    def subscribe(self, event_type: EventType, callback: Callable[[Dict[str, Any]], None]):
        """Subscribe to an event type.
        
        Args:
            event_type: The type of event to listen for
            callback: Function to call when event is processed.
                      Receives the event data dict as argument.
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)
    
    def unsubscribe(self, event_type: EventType, callback: Callable):
        """Unsubscribe from an event type."""
        if event_type in self._subscribers:
            self._subscribers[event_type].remove(callback)
    
    def emit(self, event_or_type, **data):
        """Emit an event (queued for processing).
        
        Args:
            event_or_type: Either an Event object or EventType
            **data: Event payload as keyword arguments (only if event_or_type is EventType)
        """
        if isinstance(event_or_type, Event):
            self._queue.append(event_or_type)
        else:
            self._queue.append(Event(type=event_or_type, data=data))
    
    def process(self):
        """Process all queued events.
        
        Call this once per frame after all systems have updated.
        """
        from .perf_monitor import perf
        
        while self._queue:
            event = self._queue.pop(0)
            if event.type in self._subscribers:
                for callback in self._subscribers[event.type]:
                    # Time each handler
                    handler_name = f"Event:{event.type.name}:{callback.__name__}"
                    perf.mark(handler_name)
                    callback(event)
                    perf.measure(handler_name)
    
    def clear(self):
        """Clear all queued events without processing."""
        self._queue.clear()
    
    def clear_subscribers(self, event_type: EventType = None):
        """Clear all subscribers for an event type, or all subscribers if type is None."""
        if event_type is None:
            self._subscribers.clear()
        elif event_type in self._subscribers:
            self._subscribers[event_type].clear()


# Global event bus instance
# Systems can import this directly
event_bus = EventBus()

