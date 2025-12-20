# Game Balance

## Current Formulas

### Skill XP (linear)
```
xp_needed = (skill_level + 1) * 100
```
| Level | XP Needed |
|-------|-----------|
| 0→1   | 100       |
| 5→6   | 600       |
| 10→11 | 1100      |

### XP Gains
- Melee/Ranged attack: 10 XP
- Spell cast: 15 XP

### Enemy Scaling
```
level_mult = 1 + (level - 1) * 0.15
```
+15% stats per dungeon floor

### Enemy Spawn Count
```
count = 5 + level * 2
```

### Base Stats
- Player: 100 HP, 50 Mana
- Ally (Lyra): 70 HP, 80 Mana
- Goblin: 30 HP
- Skeleton: 40 HP

---

## Planned Changes

### 1. Logarithmic Skill Leveling
Fast early levels, slower later. Get 3 spells quickly, then grind for more.

```
xp_needed = 50 * (skill_level + 1) ^ 1.5
```
| Level | XP Needed |
|-------|-----------|
| 0→1   | 50        |
| 1→2   | 140       |
| 2→3   | 260       |
| 5→6   | 700       |
| 10→11 | 1800      |

### 2. More Health (Longer Fights)
Increase all HP pools so battles aren't instant.

- Player: 100 → 150 HP
- Ally: 70 → 120 HP  
- Goblin: 30 → 50 HP
- Skeleton: 40 → 70 HP
- All enemies: roughly +60% HP

### 3. Earlier AOE Access
- Move Fireball (AOE) to level 0 requirement (already done)
- Add Chain Lightning at Combat Magic level 3 (currently 8)
- Add Poison Cloud at Nature Magic level 2 (currently 4)

