# Dungeon Siege Refactoring Plan

**Source:** `/home/bryce/projects/dungeon_siege` (read-only reference)  
**Target:** `/home/bryce/projects/ml_siege` (clean rewrite)  
**Date:** December 2024

---

## Executive Summary

The original `dungeon_siege` codebase has a working game but suffers from architectural issues that make it fragile and hard to extend. This rewrite will use **Esper ECS** as the foundation, following the tenets already documented in `dungeon_siege/docs/rewrite/00_TENETS.md`.

---

## Current Problems in dungeon_siege

### 1. God Objects

| File | Lines | Problem |
|------|-------|---------|
| `game.py` | 1,342 | Does input, combat, UI coordination, state management, rendering orchestration, item pickup, spell casting, notifications, level transitions... everything |
| `pixel_sprites.py` | 3,515 | All sprite generation in one massive file |
| `effects.py` | 1,352 | All visual effects in one place |
| `character.py` | 597 | AI, combat, stats, equipment, skills, spells, regeneration all mixed together |
| `town.py` | 962 | Entire town scene including merchants, UI, and logic |

### 2. Hidden Dependencies (`_world_ref` Anti-pattern)

```python
# Found throughout character.py, entity.py, enemy.py
char._world_ref = self  # Magic assignment in world.py
if hasattr(self, '_world_ref') and self._world_ref:  # Defensive checks everywhere
    self._world_ref.find_path(...)
```

This makes testing impossible and creates hidden coupling.

### 3. Multiple Update Paths for Same Logic

Damage is applied in at least 4 places:
- `game.py:_update_combat()` - player attacks
- `character.py:_update_ai()` - AI ally attacks
- `enemy.py:_update_attack()` - enemy attacks  
- `effects.py` - spell projectile impacts

### 4. Data Duplication

- `game.target` AND `character.target` - which is authoritative?
- Combat state tracked in both `Game` and individual entities
- Spell cooldowns managed in multiple places

### 5. Implicit State Machines

AI state exists (`AI_IDLE`, `AI_ATTACK`, etc.) but the logic handling it is scattered across 200+ lines of conditionals in `character.py` and `enemy.py`.

### 6. No Event System

Systems call each other directly. When an enemy dies:

```python
# Currently in game.py - tightly coupled
self.add_notification(f"Defeated {self.target.name}!")  # UI
self.target = None                                        # State
enemy.drop_loot()                                         # Loot
char.experience += enemy.xp_value                        # Progression
self.audio.play('kill')                                  # Audio
```

---

## Proposed Architecture with Esper

### Why Esper Makes Sense

1. **Lightweight** - Pure Python, no dependencies, ~500 lines
2. **Pygame-friendly** - Designed for games, works well with Pygame's loop
3. **Forces good patterns** - Components are data, Processors are logic
4. **Matches the tenets** - Single source of truth, explicit dependencies, one update path

### Core Concept

```python
import esper

# Components are pure data (dataclasses)
@dataclass
class Position:
    x: float
    y: float

@dataclass  
class Health:
    current: int
    maximum: int

@dataclass
class CombatTarget:
    target_entity: int  # Entity ID

# Processors contain logic
class MovementProcessor(esper.Processor):
    def process(self, dt):
        for ent, (pos, vel) in self.world.get_components(Position, Velocity):
            pos.x += vel.dx * dt
            pos.y += vel.dy * dt

class CombatProcessor(esper.Processor):
    def process(self, dt):
        for ent, (target, stats) in self.world.get_components(CombatTarget, CombatStats):
            # ALL combat logic lives here - nowhere else
            ...
```

---

## Proposed Component Structure

### Core Components

```
components/
├── transform.py       # Position, Velocity, Facing
├── health.py          # Health, Mana, Regeneration
├── combat.py          # CombatStats, CombatTarget, AttackCooldown
├── stats.py           # Attributes (STR/DEX/INT), Skills, Level
├── equipment.py       # EquipmentSlots, Inventory, Weight
├── ai.py              # AIState, PatrolPath, FollowTarget, AggroRange
├── sprite.py          # SpriteID, AnimationState, Facing
├── player.py          # PlayerControlled, Selected (tags)
└── enemy.py           # EnemyType, LootTable, XPValue
```

### Core Processors (Systems)

```
processors/
├── input.py           # InputProcessor - reads input, sets movement intent
├── ai.py              # AIProcessor - enemy and ally AI decisions
├── movement.py        # MovementProcessor - pathfinding, collision
├── combat.py          # CombatProcessor - ALL damage calculation
├── magic.py           # MagicProcessor - spell casting, cooldowns
├── progression.py     # ProgressionProcessor - XP, level ups
├── loot.py            # LootProcessor - item drops
├── animation.py       # AnimationProcessor - sprite state updates
├── camera.py          # CameraProcessor - follow, zoom
└── effects.py         # EffectsProcessor - visual effects lifecycle
```

---

## New Directory Structure

```
ml_siege/
├── main.py                    # Entry point only
├── game.py                    # Slim game loop (~150 lines)
├── requirements.txt
├── README.md
│
├── src/
│   ├── __init__.py
│   │
│   ├── ecs/
│   │   ├── __init__.py
│   │   │
│   │   ├── components/            # Pure data
│   │   │   ├── __init__.py
│   │   │   ├── transform.py       # Position, Velocity, Facing
│   │   │   ├── health.py          # Health, Mana
│   │   │   ├── combat.py          # CombatStats, CombatTarget, AttackCooldown
│   │   │   ├── stats.py           # Attributes, Skills, Level
│   │   │   ├── equipment.py       # EquipmentSlots, Inventory
│   │   │   ├── ai.py              # AIState, PatrolPath, FollowTarget
│   │   │   ├── rendering.py       # Sprite, Animation
│   │   │   ├── tags.py            # PlayerControlled, Selected, Enemy
│   │   │   └── spell.py           # SpellBook, SpellCooldowns
│   │   │
│   │   ├── processors/            # Logic (Esper Processors)
│   │   │   ├── __init__.py
│   │   │   ├── input.py           # InputProcessor
│   │   │   ├── ai.py              # AIProcessor
│   │   │   ├── movement.py        # MovementProcessor
│   │   │   ├── combat.py          # CombatProcessor
│   │   │   ├── magic.py           # MagicProcessor
│   │   │   ├── progression.py     # ProgressionProcessor
│   │   │   ├── animation.py       # AnimationProcessor
│   │   │   └── effects.py         # EffectsProcessor
│   │   │
│   │   └── factories/             # Entity creation
│   │       ├── __init__.py
│   │       ├── character.py       # create_hero(), create_companion()
│   │       ├── enemy.py           # create_goblin(), create_orc(), etc.
│   │       └── item.py            # create_weapon(), create_armor()
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── events.py              # Event bus
│   │   ├── constants.py           # All magic numbers and enums
│   │   └── formulas.py            # Pure calculation functions
│   │
│   ├── world/
│   │   ├── __init__.py
│   │   ├── dungeon_gen.py         # Procedural generation
│   │   ├── pathfinding.py         # A* implementation
│   │   └── tiles.py               # Tile types and properties
│   │
│   ├── rendering/
│   │   ├── __init__.py
│   │   ├── renderer.py            # Isometric projection
│   │   ├── camera.py              # Camera system
│   │   └── sprites/
│   │       ├── __init__.py
│   │       ├── character_sprites.py
│   │       ├── enemy_sprites.py
│   │       ├── effect_sprites.py
│   │       ├── tile_sprites.py
│   │       └── ui_sprites.py
│   │
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── hud.py
│   │   ├── inventory.py
│   │   ├── skill_tree.py
│   │   ├── merchant.py
│   │   └── widgets/
│   │       ├── __init__.py
│   │       ├── button.py
│   │       ├── panel.py
│   │       └── tooltip.py
│   │
│   ├── audio/
│   │   ├── __init__.py
│   │   └── audio.py
│   │
│   └── scenes/
│       ├── __init__.py
│       ├── game_scene.py          # Main dungeon gameplay
│       └── town_scene.py          # Town/merchant scene
│
├── data/
│   ├── enemies.yaml
│   ├── items.yaml
│   ├── spells.yaml
│   └── loot_tables.yaml
│
├── saves/
│
└── docs/
    ├── REFACTORING_PLAN.md        # This file
    └── ARCHITECTURE.md            # Technical architecture details
```

---

## Migration Strategy

### Phase 1: Foundation

**Goal:** Set up project structure and core ECS.

1. Create directory structure
2. Add `esper` and `pygame` to requirements.txt
3. Create basic game loop with Esper world
4. Implement Position, Velocity components
5. Implement MovementProcessor
6. Get a single entity moving on screen

### Phase 2: Core Components

**Goal:** Define all data as components.

1. **Transform** - Position, Velocity, Facing
2. **Health** - Health, Mana, MaxHealth, MaxMana
3. **CombatStats** - Damage, Armor, AttackSpeed, AttackRange
4. **Attributes** - Strength, Dexterity, Intelligence
5. **Skills** - Melee, Ranged, CombatMagic, NatureMagic (with XP)
6. **AIState** - State enum, target entity ID, patrol points
7. **Tags** - PlayerControlled, Enemy, Selected (marker components)

### Phase 3: Core Processors

**Order matters - start with most isolated:**

1. **MovementProcessor** - Apply velocity, handle pathfinding
2. **AnimationProcessor** - Update sprite states based on movement/combat
3. **InputProcessor** - Read input, set player entity's movement intent
4. **AIProcessor** - Enemy and ally decision making
5. **CombatProcessor** - ALL damage calculation in one place
6. **MagicProcessor** - Spell casting, cooldowns, effects
7. **ProgressionProcessor** - XP gain, level ups, skill advancement

### Phase 4: Event Bus

**Goal:** Decouple systems completely.

Events to implement:
- `ENTITY_DIED` → triggers loot, XP, notification, audio
- `DAMAGE_DEALT` → triggers hit effects, damage numbers
- `LEVEL_UP` → triggers notification, stat recalc
- `SKILL_UP` → triggers notification, spell learning
- `ITEM_PICKED_UP` → triggers notification, audio
- `SPELL_CAST` → triggers effects, audio
- `DUNGEON_LEVEL_CHANGED` → triggers world regeneration

### Phase 5: World & Rendering

1. Port dungeon generation (can mostly copy from original)
2. Port A* pathfinding (can mostly copy from original)
3. Implement isometric renderer
4. Implement camera system
5. Port sprite generation (split into multiple files!)

### Phase 6: UI

1. HUD (health bars, mana, portraits)
2. Inventory system
3. Equipment slots
4. Skill tree
5. Merchant/trading

### Phase 7: Content & Polish

1. Port all enemy types
2. Port all item definitions
3. Port all spell definitions
4. Save/load system
5. Audio system
6. Town scene

---

## Key Refactoring Rules

### Rule 1: Components Are Dumb Data

```python
# ✅ Good
@dataclass
class Health:
    current: int
    maximum: int

# ❌ Bad - no methods, no logic
@dataclass
class Health:
    current: int
    maximum: int
    
    def take_damage(self, amount):  # NO! This goes in a Processor
        self.current -= amount
```

### Rule 2: One Processor Per Concern

```python
# CombatProcessor is the ONLY place damage is applied
class CombatProcessor(esper.Processor):
    def process(self, dt):
        # Handle ALL combat: player attacks, enemy attacks, spell damage
        ...
```

### Rule 3: Processors Don't Know About Each Other

```python
# ❌ Bad
class CombatProcessor:
    def process(self, dt):
        self.loot_processor.drop_loot(enemy)  # Direct call

# ✅ Good  
class CombatProcessor:
    def process(self, dt):
        if target_health.current <= 0:
            self.event_bus.emit("ENTITY_DIED", entity=target)
```

### Rule 4: Query Don't Store

```python
# ❌ Bad - storing entity reference
self.target = enemy

# ✅ Good - store entity ID, query when needed
@dataclass
class CombatTarget:
    target_id: int  # Entity ID, not object reference

# In processor:
target_pos = self.world.component_for_entity(combat.target_id, Position)
```

### Rule 5: Files Are Small

- **Max 300 lines per file**
- If a file exceeds this, split it
- File name = single responsibility

### Rule 6: Constants Are Centralized

```python
# constants.py
AGGRO_RANGE = 6.0
MELEE_ATTACK_RANGE = 1.5
RANGED_ATTACK_RANGE = 7.0

class WeaponType(Enum):
    MELEE = "melee"
    RANGED = "ranged"
    MAGIC = "magic"

class AIState(Enum):
    IDLE = "idle"
    FOLLOW = "follow"
    CHASE = "chase"
    ATTACK = "attack"
    FLEE = "flee"
    RETURN = "return"
```

### Rule 7: Pure Calculation Functions

```python
# formulas.py
def calculate_damage(base_damage: int, strength: int, target_armor: int) -> int:
    """Pure calculation, no side effects."""
    modifier = 1 + strength * 0.05
    mitigation = 100 / (100 + target_armor)
    return int(base_damage * modifier * mitigation)

def calculate_xp_for_level(level: int) -> int:
    """XP required to reach the next level."""
    return int(100 * (level ** 1.5))
```

---

## Esper Quick Reference

### Creating the World

```python
import esper

world = esper.World()
```

### Creating Entities

```python
# Create entity and add components
player = world.create_entity(
    Position(x=10.0, y=10.0),
    Velocity(dx=0.0, dy=0.0),
    Health(current=100, maximum=100),
    PlayerControlled()  # Tag component
)
```

### Querying Entities

```python
# Get all entities with Position AND Velocity
for ent, (pos, vel) in world.get_components(Position, Velocity):
    pos.x += vel.dx * dt

# Get single component for known entity
pos = world.component_for_entity(player_id, Position)

# Check if entity has component
if world.has_component(ent, PlayerControlled):
    ...

# Get all entities with a specific component
for ent, (health,) in world.get_component(Health):
    if health.current <= 0:
        world.delete_entity(ent)
```

### Creating Processors

```python
class MovementProcessor(esper.Processor):
    def __init__(self, game_map):
        self.game_map = game_map  # Inject dependencies
    
    def process(self, dt):
        for ent, (pos, vel) in self.world.get_components(Position, Velocity):
            new_x = pos.x + vel.dx * dt
            new_y = pos.y + vel.dy * dt
            
            if self.game_map.is_walkable(new_x, new_y):
                pos.x = new_x
                pos.y = new_y
```

### Adding Processors to World

```python
# Processors run in the order they're added
world.add_processor(InputProcessor())
world.add_processor(AIProcessor())
world.add_processor(MovementProcessor(game_map))
world.add_processor(CombatProcessor(event_bus))
world.add_processor(AnimationProcessor())

# In game loop
world.process(dt)  # Calls all processors in order
```

### Removing Entities

```python
world.delete_entity(entity_id)

# Or mark for deletion (safer during iteration)
world.delete_entity(entity_id, immediate=False)
world._clear_dead_entities()  # Call after processing
```

---

## Event Bus Design

```python
from enum import Enum, auto
from typing import Callable, Dict, List, Any
from dataclasses import dataclass

class EventType(Enum):
    ENTITY_DIED = auto()
    DAMAGE_DEALT = auto()
    LEVEL_UP = auto()
    SKILL_UP = auto()
    SPELL_CAST = auto()
    ITEM_PICKED_UP = auto()
    ITEM_EQUIPPED = auto()
    DUNGEON_LEVEL_CHANGED = auto()

@dataclass
class Event:
    type: EventType
    data: Dict[str, Any]

class EventBus:
    def __init__(self):
        self._subscribers: Dict[EventType, List[Callable]] = {}
        self._queue: List[Event] = []
    
    def subscribe(self, event_type: EventType, callback: Callable):
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)
    
    def emit(self, event_type: EventType, **data):
        self._queue.append(Event(type=event_type, data=data))
    
    def process(self):
        while self._queue:
            event = self._queue.pop(0)
            for callback in self._subscribers.get(event.type, []):
                callback(event.data)
```

---

## Testing Strategy

### Unit Tests for Processors

```python
def test_combat_processor_applies_damage():
    world = esper.World()
    
    attacker = world.create_entity(
        Position(0, 0),
        CombatStats(damage=10, attack_speed=1.0)
    )
    target = world.create_entity(
        Position(1, 0),
        Health(current=100, maximum=100)
    )
    
    # Give attacker a target
    world.add_component(attacker, CombatTarget(target_id=target))
    
    processor = CombatProcessor()
    world.add_processor(processor)
    
    world.process(dt=1.0)
    
    health = world.component_for_entity(target, Health)
    assert health.current == 90  # 100 - 10 damage
```

### Integration Tests

```python
def test_enemy_death_drops_loot():
    world, event_bus = create_test_world()
    
    enemy = create_enemy(world, "goblin", x=10, y=10)
    enemy_health = world.component_for_entity(enemy, Health)
    enemy_health.current = 0
    
    # Process should emit ENTITY_DIED
    world.process(dt=0.016)
    event_bus.process()
    
    # Check loot was created
    loot_entities = list(world.get_component(LootDrop))
    assert len(loot_entities) > 0
```

---

## Reference: Original dungeon_siege Docs (27 Docs Reviewed)

The original codebase has extensive documentation in `dungeon_siege/docs/rewrite/`. All 27 docs were reviewed and improvements incorporated:

### Docs That Informed Architecture
| Doc | Key Takeaway | Action Taken |
|-----|--------------|--------------|
| `00_TENETS.md` | 10 non-negotiable principles | All tenets align with Esper ECS approach |
| `03_ARCHITECTURE.md` | System Ownership Map | Excellent reference - WHERE to make changes |
| `04_STATE_MACHINES.md` | All state enums and transitions | Added GameState, CharacterState, expanded AIState |
| `22_EVENTS.md` | Complete event catalog with payloads | Updated `events.py` with full event list |
| `21_CONSTANTS.md` | Comprehensive constant definitions | Updated `constants.py` with all enums |
| `24_GAME_LOOP.md` | Fixed timestep loop structure | Confirms our approach |

### Docs That Are Content Reference (Copy Values)
| Doc | Use Case |
|-----|----------|
| `01_PRD.md` | Feature checklist (party of 2, 4 skills, 10 slots) |
| `02_GDD.md` | Damage types, enemy behaviors, spell unlocks |
| `05_DATA_MODELS.md` | YAML schemas for characters, enemies, items, spells |
| `07_FORMULAS.md` | All game math (damage, XP, scaling) |
| `08_CONTENT.md` | Exact values for all entities |
| `23_LEVEL_DATA.md` | Enemy/level scaling tables |

### Docs That Are Implementation Reference (Porting)
| Doc | Use Case |
|-----|----------|
| `06_SYSTEMS.md` | System implementations (maps to our processors) |
| `09_UI_SPEC.md` | UI layouts and flows |
| `10_RENDERING.md` | Isometric projection math |
| `11_AUDIO.md` | Procedural audio approach |
| `12_SPRITES.md` | Procedural sprite generation |
| `13_INPUT.md` | Input handling patterns |
| `14_DUNGEON_GEN.md` | Room/corridor generation algorithm |
| `15_PATHFINDING.md` | A* implementation |
| `16_SAVE_SYSTEM.md` | Serialization format |
| `17_SEQUENCES.md` | Flow diagrams for key interactions |

### Key Differences: Our Plan vs Sister Folder Plan

| Aspect | Sister Folder | Our Plan | Verdict |
|--------|--------------|----------|---------|
| **ECS** | Hand-rolled implementation | **Esper library** | Esper wins - battle-tested, less code |
| **Architecture** | Custom World/Components | Esper's built-in | Same patterns, less boilerplate |
| **File Structure** | Similar | Similar | Aligned |
| **Event Bus** | Custom implementation | Custom (same pattern) | Same |

### Improvements Incorporated From Review

1. **Added to `constants.py`:**
   - `GameState` enum (MAIN_MENU, LOADING, PLAYING, etc.)
   - `CharacterState` enum (IDLE, MOVING, ATTACKING, CASTING, DOWNED, etc.)
   - `DamageType` enum (PHYSICAL, FIRE, ICE, LIGHTNING, POISON, HOLY)
   - `SpellSchool`, `SpellType`, `SpellTarget` enums
   - Cooldown tier system (exponential: 1, 3, 9, 27, 81, 243)
   - AI constants (FORMATION_OFFSETS, ENGAGE_RANGE, etc.)
   - Debug flags

2. **Added to `events.py`:**
   - Full event catalog (45+ events)
   - Payload documentation in docstrings
   - New categories: Status Effects, Movement, Game Flow, Trading

3. **System Ownership Map (from `03_ARCHITECTURE.md`):**
   
   | If you need to change... | Look in... | NOT in... |
   |--------------------------|------------|-----------|
   | Damage calculation | `processors/combat.py` | game.py, entities |
   | Spell effects | `processors/magic.py` | game.py, effects |
   | Enemy AI behavior | `processors/ai.py` | entities |
   | Character movement | `processors/movement.py` | entities, game.py |
   | XP/leveling formulas | `core/formulas.py` | entities |
   | UI layout | `ui/*.py` | game.py, renderer |
   | Sound effects | `audio.py` via events | game.py inline |

---

## Questions to Resolve

1. **Save/Load** - How will ECS entities serialize? 
   - Option A: Custom serialization walking all entities
   - Option B: Snapshot entire world state to JSON
   
2. **UI Binding** - How will UI observe component changes?
   - Option A: Events for everything
   - Option B: UI queries components each frame
   
3. **Sprite System** - Should sprites be components or separate?
   - Recommendation: `SpriteID` component points to sprite, actual sprite data in rendering layer

---

## Estimated Effort

| Phase | Effort | Description |
|-------|--------|-------------|
| 1. Foundation | 2-3 days | Project setup, basic ECS working |
| 2. Core Components | 2-3 days | All component dataclasses |
| 3. Core Processors | 5-7 days | Movement, AI, Combat, Magic |
| 4. Event Bus | 1-2 days | Event system implementation |
| 5. World & Rendering | 4-5 days | Dungeon gen, pathfinding, isometric |
| 6. UI | 4-5 days | HUD, inventory, skill tree |
| 7. Content & Polish | 3-5 days | Enemies, items, spells, audio |
| **Total** | **~4 weeks** | |

---

## Next Steps

1. Create initial project structure
2. Set up requirements.txt with esper and pygame
3. Implement basic game loop
4. Create first components (Position, Velocity)
5. Create first processor (MovementProcessor)
6. Get something moving on screen!

