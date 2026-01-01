# Comprehensive Code Review - January 2026

## Summary

- **17 files over 300 lines** (rule violation)
- **5 critical architecture issues** 
- **12 medium code quality issues**
- **8 minor issues**

---

## CRITICAL: File Size Violations (Max 300 Lines Rule)

| File | Lines | Action |
|------|-------|--------|
| `pixel_sprites.py` | 4231 | Split by sprite type (hero, enemies, effects, props) |
| `renderer.py` | 1852 | Split by concern (tiles, entities, UI, effects) |
| `magic_processor.py` | 1486 | Split by spell type (projectile, melee, aoe) |
| `game.py` | 792 | Split into game_loop, game_state, game_events, game_setup |
| `dungeon.py` | 694 | Split generation vs runtime methods |
| `shop.py` | 506 | OK but could share code with inventory |
| `ai_processor.py` | 540 | Split enemy vs ally AI |
| `input_processor.py` | 415 | OK |
| `combat_processor.py` | 381 | OK |

---

## CRITICAL: Architecture Issues

### 1. Constants Inconsistency
**File:** `src/core/constants.py` + `src/core/formulas.py`

**Problems:**
```python
# constants.py says:
DEATH_GOLD_PENALTY = 0.50      # Lose 50% gold

# formulas.py says:
def death_gold_penalty(current_gold: int) -> int:
    return int(current_gold * 0.10)  # Actually 10%!
```

```python
# RARITY_COLORS has duplicates:
RARITY_COLORS = {
    0: (180, 180, 180),   # Int keys
    Rarity.COMMON: (180, 180, 180),  # AND Enum keys
}
```

**Fix:** Use constants in formulas, remove duplicate keys.

---

### 2. Components Have Methods (Violates ECS)
**Files:** `equipment.py`, `spells.py`

**Problems:**
```python
# equipment.py - Inventory has methods!
@dataclass
class Inventory:
    def add(self, item_id, quantity):  # NO!
    def remove(self, item_id, quantity):  # NO!

# spells.py - StatusEffects has methods!
@dataclass
class StatusEffects:
    def get_slow_multiplier(self):  # Should be in processor!
```

Components should be pure data. Move `add()`, `remove()`, `get_slow_multiplier()` to processors.

---

### 3. Event Bus Inconsistency
**File:** `src/core/events.py`

**Problems:**
```python
# Global instance at bottom of file
event_bus = EventBus()  # Some code imports this

# But also passed via DI
class MagicProcessor:
    def __init__(self, event_bus: EventBus):  # Some code uses this
```

Some systems use global, some use injection. Pick one.

---

### 4. AI Doesn't Use Pathfinding
**Files:** `ai_processor.py`, `movement_processor.py`

**Problems:**
```python
# AI just moves in straight lines:
def _move_toward_point(self, ent, pos, tx, ty):
    dx = tx - pos.x
    dy = ty - pos.y
    # NO PATHFINDING - will walk into walls!
```

Pathfinder exists (`src/world/pathfinding.py`) but AI doesn't use it. Entities get stuck on walls.

---

### 5. Town Uses Different Systems
**File:** `src/scenes/town.py`

**Current Status:** Fixed - town now uses same renderer/camera as dungeon.

**Remaining Issues:**
- NPCs don't have Speed component (can't be pushed)
- Shop is separate from inventory (not reusing code)
- No transition animation

---

## MEDIUM: Code Quality Issues

### 6. Magic Numbers in Code
```python
# ai_processor.py
if dist < 10.0:  # Magic number - what is 10?
    enemies_nearby = True

# animation_processor.py
if abs(vel.dx) > 0.1 or abs(vel.dy) > 0.1:  # Magic 0.1
```

Move to constants.py with meaningful names.

---

### 7. Type Hints Missing
```python
# Many functions like:
def _find_nearest_enemy(self, pos):  # Returns what? Tuple? Optional?
    # ...
    return nearest, nearest_dist  # Should be -> Tuple[Optional[int], float]
```

---

### 8. Perf Monitor Creates File on Import
**File:** `src/core/perf_monitor.py`

```python
def __init__(self, enabled: bool = False):
    self.log_file = open("perf_log.txt", "w")  # Opens even if disabled!
```

Only open file when enabled=True.

---

### 9. Shop Doesn't Reuse Inventory UI
**Files:** `shop.py` vs `inventory.py`

Shop recreates all the item rendering code instead of reusing InventoryUI.

---

### 10. Duplicate Item Lookup Logic
```python
# shop.py
item_data = data_loader.get_item(inv_item.item_id)
base_value = item_data.get('value', 10)
sell_price = max(1, int(base_value * 0.5))

# formulas.py already has:
def merchant_sell_price(item_value: int) -> int:
    return max(1, item_value // 2)
```

Shop should use formulas.py functions.

---

### 11. Hardcoded Shop Markup
```python
# shop.py
buy_price = int(base_value * 1.5)  # Hardcoded 150%

# But constants.py has:
MERCHANT_SELL_RATE = 1.0  # Should be using this
```

---

### 12. SCREEN_WIDTH/HEIGHT Used Inconsistently
```python
# Some UI uses:
from ..core.constants import SCREEN_WIDTH, SCREEN_HEIGHT

# But actual screen size may differ (fullscreen):
screen_w, screen_h = screen.get_size()  # This is correct
```

Always use `screen.get_size()`, never constants.

---

### 13. Dead Code: Unused Imports
Several files import things they don't use. Run `autoflake` or similar.

---

### 14. No Docstrings on Public Methods
Many processors have methods without docstrings explaining what they do.

---

### 15. Inconsistent Coordinate Systems
- Some code uses `(x, y)` tuples
- Some uses separate `x`, `y` parameters  
- Some uses `Position` components

Pick one and be consistent.

---

### 16. Animation Frame Counts Hardcoded
```python
# animation_processor.py
FRAME_COUNTS = {
    AnimationState.SPIN: 12,  # Hardcoded here
}

# But pixel_sprites.py generates different frame counts!
```

Should be driven by actual sprite data.

---

### 17. No Input Validation on Save/Load
Save files are trusted completely. Malformed saves could crash the game.

---

## MINOR: Small Fixes

### 18. SpellBook imports Set but uses List
```python
from typing import Dict, List, Set, Optional  # Set imported but not used
known_spells: List[str]  # Now a list, not set
```

---

### 19. Unused `max_size` Check
```python
# equipment.py
max_size: int = 30

# But is_full uses len(items) >= max_size
# Some add() calls don't check is_full first
```

---

### 20. Town NPCs Use Enemy Sprites
```python
{'name': 'Blacksmith', 'sprite': 'orc'},  # Orc for blacksmith?
```

Should have dedicated NPC sprites.

---

### 21. No Sound for Town Interactions
Buying/selling items has no audio feedback.

---

### 22. Camera Zoom Not Saved
Zoom level resets on scene change.

---

### 23. Gold Display in Multiple Places
Gold is rendered in both HUD and TownScene. Should be one source.

---

### 24. Portal Hotkey 'H' Not Documented
`InputProcessor` has `pygame.K_h` for town portal but no UI hint.

---

### 25. Inventory Weight Not Displayed
`Inventory.max_weight` exists but isn't shown in UI.

---

## Action Plan

### Phase 1: Critical (Do First)
- [ ] Fix constants.py / formulas.py mismatch
- [ ] Remove methods from components
- [ ] Make AI use pathfinder
- [ ] Split pixel_sprites.py (4231 → 4 files of ~1000)
- [ ] Split renderer.py (1852 → 4 files)
- [ ] Split game.py (792 → 4 files)

### Phase 2: Medium (This Week)
- [ ] Remove magic numbers
- [ ] Add type hints to return values
- [ ] Shop reuse inventory rendering
- [ ] Use formulas.py for all price calculations
- [ ] Fix perf monitor file creation

### Phase 3: Minor (When Convenient)
- [ ] Clean unused imports
- [ ] Add docstrings
- [ ] NPC sprites
- [ ] Sound effects for shop
- [ ] Save camera zoom

---

## File Split Proposals

### `pixel_sprites.py` → 4 files:
1. `sprites_hero.py` - Hero animations
2. `sprites_enemies.py` - Enemy animations  
3. `sprites_effects.py` - Spell effects, damage numbers
4. `sprites_props.py` - Barrels, chests, decorations

### `renderer.py` → 4 files:
1. `render_tiles.py` - Dungeon/town tiles
2. `render_entities.py` - Characters, enemies
3. `render_effects.py` - Particles, spell effects
4. `render_ui.py` - Health bars, damage numbers

### `game.py` → 4 files:
1. `game.py` - Main loop only
2. `game_state.py` - State machine, transitions
3. `game_events.py` - Event handlers
4. `game_setup.py` - Initialization, processor setup

---

## Tests Needed

Currently NO test files exist. Need:
- [ ] `tests/test_formulas.py` - Damage/healing calculations
- [ ] `tests/test_los.py` - Line of sight algorithm
- [ ] `tests/test_pathfinding.py` - A* correctness
- [ ] `tests/test_save_load.py` - Save/load round-trip

---

## Performance Notes

From perf_log.txt analysis:
- Music transition: 2+ seconds (FIXED - preload now)
- Magic processor: ~5ms average (OK)
- Renderer: ~8ms average (OK but could optimize)
- AI processor: ~2ms average (OK)

Main bottleneck was music loading, now fixed.
