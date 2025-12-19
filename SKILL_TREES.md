# Skill & Spell Advancement Trees

## Combat Skills (Usage-Based)

Skills level up automatically as you use them. Every 100 XP = 1 level.

### ⚔️ Melee (Skill)
**Levels with:** Using melee weapons (swords, axes, maces)
**Stat bonuses per level:** +1 STR, +5 Max HP

| Level | Unlock |
|-------|--------|
| 1 | Basic attacks |
| 5 | **Power Strike** - 150% damage, 3s cooldown |
| 10 | **Whirlwind** - AoE attack around self |
| 15 | **Berserker Rage** - +50% attack speed for 10s |
| 20 | **Execute** - Instant kill enemies below 15% HP |
| 25 | **Blade Master** - +20% crit chance permanently |

### 🏹 Ranged (Skill)
**Levels with:** Using bows, crossbows
**Stat bonuses per level:** +1 DEX, +3 Max HP

| Level | Unlock |
|-------|--------|
| 1 | Basic shots |
| 5 | **Quick Shot** - Fire 2 arrows rapidly |
| 10 | **Piercing Arrow** - Hits all enemies in line |
| 15 | **Multishot** - Fire 3 arrows in spread |
| 20 | **Rain of Arrows** - AoE damage on area |
| 25 | **Sharpshooter** - +30% crit damage permanently |

### 🔥 Combat Magic (Skill)
**Levels with:** Casting offensive spells
**Stat bonuses per level:** +1 INT, +5 Max MP

| Level | Unlock |
|-------|--------|
| 1 | **Fireball** (starting spell) |
| 3 | **Lightning Bolt** |
| 5 | **Ice Shard** |
| 8 | **Chain Lightning** |
| 12 | **Meteor** |
| 15 | **Inferno** - Large fire AoE |
| 20 | **Thunderstorm** - Lightning strikes area |
| 25 | **Armageddon** - Ultimate destruction spell |

### 🌿 Nature Magic (Skill)
**Levels with:** Casting healing/support spells
**Stat bonuses per level:** +1 INT, +3 Max MP, +2 Max HP

| Level | Unlock |
|-------|--------|
| 1 | **Heal** (starting spell) |
| 3 | **Regeneration** - Heal over time |
| 5 | **Group Heal** |
| 8 | **Summon Wolf** |
| 10 | **Entangle** - Root enemies |
| 12 | **Poison Cloud** |
| 15 | **Summon Bear** |
| 20 | **Nature's Blessing** - Full party buff |
| 25 | **Resurrection** - Revive fallen ally |

---

## Spell Details

### Combat Magic Spells

| Spell | Mana | Damage | Range | Cooldown | Description |
|-------|------|--------|-------|----------|-------------|
| Fireball | 15 | 25 (+INT) | 7 | 2s | Explodes on impact, 2 tile radius |
| Ice Shard | 8 | 12 (+INT) | 6 | 1s | Fast projectile, slows target |
| Lightning Bolt | 12 | 20 (+INT) | 8 | 1.5s | Instant hit, high accuracy |
| Chain Lightning | 25 | 15 (+INT) | 6 | 3s | Jumps to 3 nearby enemies |
| Meteor | 40 | 60 (+INT) | 6 | 5s | Massive AoE, 3 tile radius |
| Inferno | 35 | 40 (+INT) | 5 | 4s | Leaves burning ground |
| Thunderstorm | 50 | 30 (+INT) | 0 | 8s | Hits all enemies on screen |
| Armageddon | 80 | 100 (+INT) | 10 | 20s | Ultimate destruction |

### Nature Magic Spells

| Spell | Mana | Effect | Range | Cooldown | Description |
|-------|------|--------|-------|----------|-------------|
| Heal | 10 | 30 (+INT) HP | 6 | 1.5s | Single target heal |
| Regeneration | 15 | 5 HP/sec | 6 | 15s | 10 second duration |
| Group Heal | 25 | 20 (+INT) HP | 0 | 4s | Heals all party in 5 tiles |
| Summon Wolf | 30 | Companion | 0 | 45s | Wolf fights for 30s |
| Entangle | 12 | Root 4s | 5 | 8s | Roots enemies in 2 tile radius |
| Poison Cloud | 18 | 8 dmg/sec | 5 | 6s | 5s duration, 2.5 tile radius |
| Summon Bear | 50 | Companion | 0 | 60s | Stronger than wolf, 45s |
| Nature's Blessing | 40 | Buff | 0 | 30s | +20% all stats for party |
| Resurrection | 60 | Revive | 6 | 120s | Bring back fallen ally |

---

## Melee Abilities

| Ability | Mana/Stamina | Damage | Cooldown | Req Level |
|---------|--------------|--------|----------|-----------|
| Power Strike | 0 | 150% | 3s | Melee 5 |
| Whirlwind | 0 | 80% x enemies | 6s | Melee 10 |
| Berserker Rage | 0 | Buff | 30s | Melee 15 |
| Execute | 0 | Instant kill | 10s | Melee 20 |

## Ranged Abilities

| Ability | Mana/Stamina | Damage | Cooldown | Req Level |
|---------|--------------|--------|----------|-----------|
| Quick Shot | 0 | 80% x2 | 2s | Ranged 5 |
| Piercing Arrow | 0 | 100% pierce | 5s | Ranged 10 |
| Multishot | 0 | 60% x3 | 4s | Ranged 15 |
| Rain of Arrows | 0 | 50% AoE | 10s | Ranged 20 |

---

## Ally AI Modes

Allies level up the same way as the player through usage:

| Mode | Behavior |
|------|----------|
| **Follow** | Stay near player, attack nearby enemies |
| **Aggressive** | Seek and attack all enemies |
| **Defensive** | Only attack if player is attacked |
| **Passive** | Never attack, just follow |

---

## Future: Passive Talents

Each skill could have a talent tree with passive bonuses:

### Melee Talents
- Thick Skin: +5% damage reduction per point
- Battle Hardened: +10 HP per point
- Weapon Mastery: +5% damage per point

### Ranged Talents  
- Eagle Eye: +5% crit chance per point
- Quick Hands: +5% attack speed per point
- Steady Aim: +10% accuracy per point

### Combat Magic Talents
- Spell Power: +5% spell damage per point
- Mana Flow: +10 MP per point
- Quick Cast: -5% cooldowns per point

### Nature Magic Talents
- Healing Touch: +10% healing per point
- Nature's Gift: +5 MP regen per point
- Summon Mastery: +20% summon duration per point

