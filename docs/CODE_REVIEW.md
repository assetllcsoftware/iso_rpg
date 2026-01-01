# Code Review - January 2026

## What Actually Matters vs What's Pedantic

### ACTUALLY BREAKS THE GAME (Fix These)

| Issue | Impact | Effort |
|-------|--------|--------|
| **TOWN IS BROKEN** - can't move, can't exit, processors don't run | Game literally unplayable in town | HIGH |
| AI walks in straight lines, gets stuck on walls | Enemies freeze, combat breaks | Medium |
| Constants vs formulas mismatch (50% vs 10% gold penalty) | Wrong game balance | Easy |
| Shop hardcodes prices instead of using formulas | Inconsistent economy | Easy |

### MAKES CODE HARDER TO MAINTAIN (Fix Eventually)

| Issue | Impact | Effort |
|-------|--------|--------|
| `pixel_sprites.py` is 4231 lines | Can't find anything | High |
| `renderer.py` is 1852 lines | Hard to modify rendering | High |
| No tests exist | Can't refactor safely | Medium |
| Magic numbers everywhere | Hard to tune gameplay | Easy |

### PEDANTIC STUFF I SHOULD IGNORE

| "Issue" | Why It's Fine |
|---------|---------------|
| Components have methods like `Inventory.add()` | Convenience methods are OK - they just manipulate data |
| Event bus global + DI | Both patterns work, consistency isn't worth refactoring |
| Some files over 300 lines | Arbitrary rule - `dungeon.py` at 694 lines is ONE cohesive class |
| Missing type hints | Nice to have, not blocking anything |
| Unused imports | Run a linter once, done |

---

## Realistic Action Plan

### Week 1: Fix What's Actually Broken

**1. Make AI use pathfinding** (HIGH PRIORITY)
```python
# Current (broken):
def _move_toward_point(self, ent, pos, tx, ty):
    dx = tx - pos.x  # Walks into walls!

# Should be:
def _move_toward_point(self, ent, pos, tx, ty):
    path = self.pathfinder.find_path(pos.x, pos.y, tx, ty)
    if path:
        # Follow path instead of straight line
```

**2. Fix constants/formulas mismatch**
```python
# formulas.py - USE THE CONSTANT
def death_gold_penalty(current_gold: int) -> int:
    from .constants import DEATH_GOLD_PENALTY
    return int(current_gold * DEATH_GOLD_PENALTY)
```

**3. Shop uses formulas.py**
```python
# Instead of hardcoded:
buy_price = int(base_value * 1.5)

# Use:
from ..core.formulas import merchant_buy_price
buy_price = merchant_buy_price(base_value)
```

### Week 2: Split The Big Files (Only the worst ones)

**Split `pixel_sprites.py` (4231 lines) → 3 files:**
```
rendering/
├── sprites/
│   ├── __init__.py      # Re-exports everything
│   ├── characters.py    # Hero, mage, enemies (~1500 lines)
│   ├── effects.py       # Spells, particles (~1000 lines)
│   └── world.py         # Tiles, props, decorations (~1700 lines)
```

**Split `renderer.py` (1852 lines) → 2 files:**
```
rendering/
├── renderer.py          # Main render loop, camera (~600 lines)
└── render_world.py      # Tile rendering, decorations (~1200 lines)
```

**DON'T split `game.py`** - It's 792 lines but it's the main loop. Splitting it creates circular imports and makes debugging harder. Leave it.

### Week 3: Add Critical Tests

```
tests/
├── test_formulas.py     # Damage calculations - EASY, pure functions
├── test_pathfinding.py  # A* correctness - CRITICAL for AI fix
└── test_los.py          # Line of sight - CRITICAL, caused many bugs
```

### Backlog (Do When Bored)

- [ ] Remove RARITY_COLORS duplicate keys
- [ ] Add docstrings to processor methods
- [ ] NPC sprites instead of using enemy sprites
- [ ] Shop sound effects
- [ ] Type hints on public functions

---

## What I Was Wrong About

### ❌ "Components shouldn't have methods"

This is ECS purism. `Inventory.add()` is fine:
```python
@dataclass
class Inventory:
    items: List[InventoryItem]
    
    def add(self, item_id, quantity):  # This is FINE
        # It's just a helper that manipulates the data
        # Not "logic" - just list manipulation
```

Moving this to a processor would mean:
```python
# Now you need this everywhere:
InventoryProcessor.add_item(entity, item_id, quantity)

# Instead of:
inventory.add(item_id, quantity)
```

That's worse, not better.

### ❌ "Event bus should be one or the other"

Using DI in processors (testable) AND having a global (convenient for one-off handlers) is fine. Real projects do this.

### ❌ "Split game.py into 4 files"

This would create:
- Circular imports between game_state.py and game_events.py
- Harder debugging (stack traces across 4 files)
- No real benefit

792 lines for a main game loop is acceptable.

---

## Actual Architecture Problems

### 1. No Separation Between "What To Do" and "How To Do It"

Currently:
```python
# AI decides AND moves in the same processor
class AIProcessor:
    def _move_toward_point(self, ...):  # AI shouldn't do movement!
```

Should be:
```python
# AI just sets intent
class AIProcessor:
    def process(self):
        intent = MoveIntent(target_x, target_y)
        esper.add_component(ent, intent)

# Movement processor handles HOW
class MovementProcessor:
    def process(self):
        # Uses pathfinder to actually move
```

This is partially done but not consistently.

### 2. Dungeon vs TownMap Duplication

`TownMap` duplicates methods from `Dungeon`:
- `get_tile()`
- `is_walkable()`
- `has_line_of_sight()`

Should have a base `GameMap` class or protocol.

### 3. UI Doesn't Use Events Consistently

Some UI updates by polling:
```python
# Every frame, poll for gold
gold = self._get_player_gold()
```

Some UI updates by events:
```python
# React to gold change event
event_bus.subscribe(GOLD_CHANGED, self._on_gold_changed)
```

Pick one pattern.

---

## Summary

**Do This Week:**
1. Make AI use pathfinder (fixes stuck enemies)
2. Fix gold penalty constant mismatch
3. Shop uses formulas.py

**Do Next Week:**
1. Split pixel_sprites.py into 3 files
2. Split renderer.py into 2 files
3. Add tests for formulas, pathfinding, LOS

**Don't Bother:**
- Moving methods out of components
- Splitting game.py
- Enforcing 300-line rule everywhere
- Perfect type hints
