# Processor Flow & Responsibilities

## Overview

Processors run in a specific order each frame. Understanding which processor handles what prevents bugs like projectiles getting blocked by collision checks meant for characters.

---

## Processor Execution Order

```
1. InputProcessor      - Read player input, set intents
2. AIProcessor         - AI decisions, set intents  
3. MovementProcessor   - Apply velocities, handle collision
4. CombatProcessor     - Resolve melee attacks
5. MagicProcessor      - Spells, projectiles, effects
6. EffectsProcessor    - Status effects (burn, slow, etc.)
7. ProgressionProcessor - XP, leveling
8. AnimationProcessor  - Update sprite animations
9. PositionValidator   - LAST: Fix any invalid positions
```

---

## Entity Type Responsibilities

### Characters (Hero, Lyra, Enemies)
| Aspect | Responsible Processor |
|--------|----------------------|
| Movement input | InputProcessor / AIProcessor |
| Position updates | MovementProcessor |
| Ground collision | MovementProcessor._can_move_to() |
| Wall sliding | MovementProcessor |
| Position validation | PositionValidator |

### Projectiles (Fireballs, Ice Shards, etc.)
| Aspect | Responsible Processor |
|--------|----------------------|
| Creation | MagicProcessor._create_projectile() |
| Velocity/homing | MagicProcessor._update_projectiles() |
| Position updates | MovementProcessor (NO collision!) |
| Wall collision | MagicProcessor._update_projectiles() |
| Hit detection | MagicProcessor._update_projectiles() |
| Cleanup | MagicProcessor (adds ToRemove) |

**IMPORTANT**: Projectiles must SKIP:
- Ground collision in MovementProcessor (they fly!)
- Position validation in PositionValidator (they can be anywhere!)

### Visual Effects (Hit sparks, spell impacts)
| Aspect | Responsible Processor |
|--------|----------------------|
| Creation | Various (on hit, on cast, etc.) |
| Timer/cleanup | MagicProcessor or AnimationProcessor |
| Position validation | SKIP - effects can be anywhere |

### Area Effects (Fire patches, poison clouds)
| Aspect | Responsible Processor |
|--------|----------------------|
| Creation | MagicProcessor |
| Tick damage | MagicProcessor._update_area_effects() |
| Position validation | SKIP - effects can be anywhere |

---

## Component Ownership Rules

### Position Component
- **Modified by**: MovementProcessor (primary), MagicProcessor (leap abilities), PositionValidator (fixes only)
- **Read by**: Everyone

### Velocity Component  
- **Modified by**: InputProcessor/AIProcessor (set direction), MagicProcessor (projectile homing)
- **Applied by**: MovementProcessor ONLY
- **Special case**: Projectiles apply velocity directly without collision checks

### Health Component
- **Modified by**: CombatProcessor, MagicProcessor
- **Read by**: AIProcessor, HUD, etc.

---

## Skip Lists (What NOT to process)

### MovementProcessor._apply_velocities()
Skip collision checks for:
- `Projectile` - flies through air, handles own wall collision
- `Dead` / `Downed` - don't move

### PositionValidator.process()
Skip entirely for:
- `Projectile` - flying, handles own collision
- `VisualEffect` - can be anywhere
- `AreaEffect` - can be anywhere
- `Dead` - death animations may clip walls

---

## Common Bugs & How to Avoid

### Bug: Projectiles don't move
**Cause**: MovementProcessor blocking them with ground collision
**Fix**: Skip collision for entities with `Projectile` component

### Bug: Projectiles get reset to weird positions
**Cause**: PositionValidator treating them as stuck entities
**Fix**: Skip entities with `Projectile` component in validator

### Bug: Characters attack through walls
**Cause**: Missing LOS check before attack
**Fix**: Always check `dungeon.has_line_of_sight()` before dealing damage

### Bug: Spells cast at wrong target
**Cause**: AI sends spell_id but processor uses slot number
**Fix**: Check for `spell_id` in event data before falling back to slot

### Bug: Entity ends up in wall
**Cause**: Some code moved entity without checking collision
**Fix**: Only MovementProcessor should modify Position (except for teleports which must validate)

---

## Adding New Entity Types

When adding a new flying/floating entity type:

1. **MovementProcessor**: Add to skip list in `_apply_velocities()` if it shouldn't collide with ground
2. **PositionValidator**: Add to skip list in `process()` if it can exist in non-walkable tiles
3. **Handle own collision**: The entity's managing processor must handle wall/boundary collision

Example for a new "Boomerang" entity:
```python
# In MovementProcessor._apply_velocities():
if esper.has_component(ent, Boomerang):
    pos.x += vel.dx * dt
    pos.y += vel.dy * dt
    continue  # Skip ground collision

# In PositionValidator.process():
if esper.has_component(ent, Boomerang):
    continue  # Skip validation

# In WeaponProcessor (or wherever boomerang logic lives):
# Handle wall collision, return path, hit detection, etc.
```

---

## Debugging Tips

### Projectile Issues
Add debug prints to track lifecycle:
```python
print(f"[PROJECTILE] Created entity {ent} at ({x}, {y})")
print(f"[PROJECTILE UPDATE] Processing {count} projectiles")
print(f"[PROJECTILE HIT] {spell} hit {target}")
print(f"[PROJECTILE WALL] {spell} hit wall at ({x}, {y})")
```

### Position Issues
Check which processor is modifying positions unexpectedly:
```python
# Add to Position component temporarily:
def __setattr__(self, name, value):
    if name in ('x', 'y'):
        import traceback
        traceback.print_stack(limit=5)
    super().__setattr__(name, value)
```

---

## Golden Rules

1. **One processor owns each action** - Don't have multiple processors trying to move the same entity
2. **Check component types** - Always check if entity is a projectile/effect before applying character logic
3. **Skip lists are critical** - When adding new entity types, update ALL relevant skip lists
4. **LOS before damage** - Never deal damage without checking line of sight first
5. **Validate teleports** - Any instant position change must check `is_walkable()`

