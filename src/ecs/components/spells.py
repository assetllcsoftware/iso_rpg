"""Spell and magic components."""

from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional


@dataclass
class SpellBook:
    """Known spells and cooldowns."""
    known_spells: List[str] = field(default_factory=list)  # Ordered list of spell IDs
    cooldowns: Dict[str, float] = field(default_factory=dict)  # spell_id -> remaining
    
    def knows(self, spell_id: str) -> bool:
        return spell_id in self.known_spells
    
    def learn(self, spell_id: str):
        if spell_id not in self.known_spells:
            self.known_spells.append(spell_id)
        if spell_id not in self.cooldowns:
            self.cooldowns[spell_id] = 0.0
    
    def can_cast(self, spell_id: str) -> bool:
        """Check if spell is known and off cooldown."""
        if spell_id not in self.known_spells:
            return False
        return self.cooldowns.get(spell_id, 0.0) <= 0
    
    def start_cooldown(self, spell_id: str, duration: float):
        self.cooldowns[spell_id] = duration
    
    def update_cooldowns(self, dt: float):
        for spell_id in self.cooldowns:
            self.cooldowns[spell_id] = max(0.0, self.cooldowns[spell_id] - dt)


@dataclass
class CastIntent:
    """Intent to cast a spell (set by input/AI)."""
    spell_id: str = ""
    target_id: int = -1  # Entity target
    target_x: float = 0.0  # Ground target
    target_y: float = 0.0


@dataclass
class Casting:
    """Currently casting a spell."""
    spell_id: str = ""
    target_id: int = -1
    target_x: float = 0.0
    target_y: float = 0.0
    cast_time: float = 0.0  # Time until spell fires


@dataclass
class GlobalCooldown:
    """Global cooldown - prevents spamming abilities too fast."""
    remaining: float = 0.0  # Time until next ability can be used
    
    @property
    def ready(self) -> bool:
        return self.remaining <= 0


@dataclass
class Projectile:
    """A spell projectile in flight."""
    spell_id: str = ""
    caster_id: int = -1
    target_id: int = -1
    target_x: float = 0.0
    target_y: float = 0.0
    speed: float = 12.0
    damage: int = 0
    damage_type: str = "fire"


@dataclass
class AreaEffect:
    """An area effect on the ground."""
    spell_id: str = ""
    caster_id: int = -1
    radius: float = 3.0
    duration: float = 0.0
    tick_interval: float = 0.5
    next_tick: float = 0.0
    damage_per_tick: int = 0
    damage_type: str = "fire"


@dataclass
class StatusEffect:
    """A status effect on an entity."""
    effect_type: str = ""  # slow, burn, poison, frozen, regen
    duration: float = 0.0
    source_id: int = -1
    
    # Effect-specific values
    slow_amount: float = 0.0  # 0.3 = 30% slower
    damage_per_second: float = 0.0
    heal_per_second: float = 0.0


@dataclass 
class StatusEffects:
    """Collection of active status effects."""
    effects: List[StatusEffect] = field(default_factory=list)
    
    def add(self, effect: StatusEffect):
        # Replace existing effect of same type from same source
        self.effects = [e for e in self.effects 
                       if not (e.effect_type == effect.effect_type and 
                              e.source_id == effect.source_id)]
        self.effects.append(effect)
    
    def remove_expired(self):
        self.effects = [e for e in self.effects if e.duration > 0]
    
    def get_slow_multiplier(self) -> float:
        """Get combined slow effect (multiplicative)."""
        mult = 1.0
        for e in self.effects:
            if e.effect_type == "stun":
                return 0.0  # Stopped completely
            if e.effect_type == "slow":
                mult *= (1.0 - e.slow_amount)
        return mult


@dataclass
class ActiveAbility:
    """An ongoing multi-hit or channeled ability."""
    spell_id: str = ""
    hits_remaining: int = 0
    hit_interval: float = 0.5
    next_hit_timer: float = 0.0
    radius: float = 2.5
    damage_per_hit: int = 0
    total_duration: float = 0.0  # For animation tracking


@dataclass
class LeapingAbility:
    """Tracks an in-progress leap attack."""
    spell_id: str = ""
    target_id: int = -1
    start_x: float = 0.0
    start_y: float = 0.0
    target_x: float = 0.0
    target_y: float = 0.0
    duration: float = 0.8  # Time to complete leap
    elapsed: float = 0.0
    damage: int = 0
    aoe_radius: float = 0.0
    aoe_damage: int = 0
    stun_duration: float = 0.0
    aoe_stun_duration: float = 0.0  # Stun duration for AOE targets
    has_landed: bool = False


@dataclass
class DelayedSpellEffect:
    """Delay effect application (e.g. for heavy animations)."""
    spell_id: str = ""
    caster_id: int = -1
    target_id: int = -1  # Primary target
    target_x: float = 0.0  # Ground target
    target_y: float = 0.0
    timer: float = 0.0  # Time until effect applies
    base_damage: int = 0
    spell_data: dict = field(default_factory=dict)


