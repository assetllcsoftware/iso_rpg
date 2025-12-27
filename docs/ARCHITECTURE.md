# Architecture

## Overview

ML Siege uses an Entity Component System (ECS) architecture powered by [Esper](https://github.com/benmoran56/esper).

```
┌─────────────────────────────────────────────────────────────────────┐
│                           GAME LOOP                                  │
│                                                                     │
│   Input ──► Process Events ──► Update Systems ──► Render ──► Present│
│                                     │                               │
│                              ┌──────┴──────┐                        │
│                              ▼             ▼                        │
│                     ┌─────────────┐  ┌──────────┐                   │
│                     │   ESPER     │  │  EVENT   │                   │
│                     │   WORLD     │  │   BUS    │                   │
│                     └──────┬──────┘  └──────────┘                   │
│                            │                                         │
│         ┌──────────────────┼──────────────────┐                     │
│         ▼                  ▼                  ▼                     │
│   ┌───────────┐     ┌───────────┐      ┌───────────┐               │
│   │ ENTITIES  │     │COMPONENTS │      │PROCESSORS │               │
│   │  (IDs)    │     │  (Data)   │      │  (Logic)  │               │
│   └───────────┘     └───────────┘      └───────────┘               │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## ECS Concepts

### Entities

Entities are just integer IDs. They have no data or behavior themselves.

```python
player_id = world.create_entity()  # Returns an int like 1
enemy_id = world.create_entity()   # Returns 2
```

### Components

Components are pure data containers (dataclasses). No methods, no logic.

```python
@dataclass
class Position:
    x: float
    y: float

@dataclass
class Health:
    current: int
    maximum: int
```

### Processors

Processors contain all the logic. They query for entities with specific components and operate on them.

```python
class MovementProcessor(esper.Processor):
    def process(self, dt):
        for ent, (pos, vel) in self.world.get_components(Position, Velocity):
            pos.x += vel.dx * dt
            pos.y += vel.dy * dt
```

## System Order

Processors run in a fixed order every frame:

1. **InputProcessor** - Read input, set movement intent
2. **AIProcessor** - Enemy/ally AI decisions
3. **MovementProcessor** - Apply movement, collision detection
4. **CombatProcessor** - Process attacks, apply damage
5. **MagicProcessor** - Spell casting, cooldowns
6. **ProgressionProcessor** - XP, level ups
7. **EffectsProcessor** - Visual effects lifecycle
8. **AnimationProcessor** - Update sprite states

## Event Bus

Systems communicate through events, not direct calls.

```python
# CombatProcessor emits when entity dies
if health.current <= 0:
    event_bus.emit(EventType.ENTITY_DIED, entity_id=ent, killer_id=attacker)

# Other systems subscribe
class AudioSystem:
    def __init__(self, event_bus):
        event_bus.subscribe(EventType.ENTITY_DIED, self.on_entity_died)
    
    def on_entity_died(self, data):
        self.play_sound("death")

class LootSystem:
    def __init__(self, event_bus):
        event_bus.subscribe(EventType.ENTITY_DIED, self.on_entity_died)
    
    def on_entity_died(self, data):
        self.drop_loot(data["entity_id"])
```

## Data Flow

```
User Input
    │
    ▼
┌─────────────────┐
│ InputProcessor  │ ──► Sets Velocity, CombatIntent components
└─────────────────┘
    │
    ▼
┌─────────────────┐
│  AIProcessor    │ ──► Sets Velocity, CombatTarget for AI entities
└─────────────────┘
    │
    ▼
┌─────────────────┐
│MovementProcessor│ ──► Updates Position based on Velocity
└─────────────────┘
    │
    ▼
┌─────────────────┐
│ CombatProcessor │ ──► Applies damage, emits DAMAGE_DEALT, ENTITY_DIED
└─────────────────┘
    │
    ▼
┌─────────────────┐
│  Event Bus      │ ──► Routes events to subscribers
└─────────────────┘
    │
    ▼
┌─────────────────┐
│    Renderer     │ ──► Reads Position, Sprite components, draws to screen
└─────────────────┘
```

## Component Reference

### Transform
- `Position(x, y)` - World coordinates
- `Velocity(dx, dy)` - Movement per second
- `Facing` - Direction enum (DOWN, LEFT, RIGHT, UP)

### Combat
- `Health(current, maximum)`
- `Mana(current, maximum)`
- `CombatStats(damage, armor, attack_speed, attack_range)`
- `CombatTarget(target_id)` - Entity ID of current target
- `AttackCooldown(remaining)` - Time until can attack again

### Stats
- `Attributes(strength, dexterity, intelligence)`
- `Skills(melee, ranged, combat_magic, nature_magic)` - Each with level and XP
- `Level(current, experience)`

### AI
- `AIState(state)` - IDLE, FOLLOW, CHASE, ATTACK, FLEE, RETURN
- `PatrolPath(points, current_index)`
- `FollowTarget(leader_id, offset)`
- `AggroRange(range)`
- `LeashRange(range, home_position)`

### Tags (Marker Components)
- `PlayerControlled()` - This entity responds to player input
- `Enemy()` - This entity is hostile
- `Selected()` - Currently selected by player
- `Ally()` - This entity is on the player's team

### Rendering
- `Sprite(sprite_id, animation, frame)`
- `AnimationState(current, timer)`

## System Ownership Map

**Use this table to find WHERE to make changes:**

| If you need to change... | Look in... | NOT in... |
|--------------------------|------------|-----------|
| Damage calculation | `processors/combat.py` | game.py, entities |
| Spell effects | `processors/magic.py` | game.py, effects |
| Enemy AI behavior | `processors/ai.py` | entities |
| Ally AI behavior | `processors/ai.py` | entities |
| Character movement | `processors/movement.py` | entities, game.py |
| XP/leveling formulas | `core/formulas.py` | entities inline |
| Item stats/effects | `data/items.yaml` | item.py inline |
| Level generation | `world/dungeon_gen.py` | world.py |
| UI layout | `ui/*.py` | game.py, renderer |
| Rendering | `rendering/*.py` | game.py |
| Input handling | `processors/input.py` | game.py (events only) |
| Sound effects | `audio/` via events | game.py inline calls |
| Save/Load | TBD | game.py |
| Pathfinding | `world/pathfinding.py` | entity.py inline |
| Combat targeting | `processors/combat.py` | game.py, character.py |
| Animation timing | `processors/animation.py` | renderer inline |

### Data Ownership

| Data | Owner Component | Written By | Read By |
|------|-----------------|------------|---------|
| Position | `Position` | MovementProcessor | Renderer, AIProcessor |
| Health | `Health` | CombatProcessor | Renderer, AIProcessor |
| Target | `CombatTarget` | AIProcessor, InputProcessor | CombatProcessor |
| AI State | `AIState` | AIProcessor | AIProcessor, AnimationProcessor |
| Cooldowns | `AttackCooldown` | CombatProcessor | CombatProcessor |
| Spell CDs | `SpellCooldowns` | MagicProcessor | MagicProcessor, UI |

## File Size Rules

- **Max 300 lines per file**
- One responsibility per file
- If it's getting big, split it

## Naming Conventions

- Components: PascalCase nouns (`Position`, `Health`, `CombatStats`)
- Processors: PascalCase with "Processor" suffix (`MovementProcessor`)
- Events: SCREAMING_SNAKE_CASE (`ENTITY_DIED`, `DAMAGE_DEALT`)
- Constants: SCREAMING_SNAKE_CASE (`TILE_WIDTH`, `AGGRO_RANGE`)
- Functions: snake_case (`calculate_damage`, `create_enemy`)

