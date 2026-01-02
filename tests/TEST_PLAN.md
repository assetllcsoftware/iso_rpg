# Test Plan - ML Siege

Each test documents what gameplay feature it protects. When a test breaks, you know exactly what player experience is at risk.

---

## 1. COMBAT FORMULAS (test_formulas.py)

### Physical Combat
| # | Test Name | Gameplay Impact |
|---|-----------|-----------------|
| 1 | `test_weapon_damage_scales_with_strength` | Players feel stronger as STR increases |
| 2 | `test_armor_reduces_damage` | Armor items are worth equipping |
| 3 | `test_armor_diminishing_returns` | Can't become invincible with enough armor |
| 4 | `test_minimum_damage_is_one` | Attacks always do something |
| 5 | `test_critical_hits_deal_150_percent` | Crits feel impactful |
| 6 | `test_dex_increases_crit_chance` | DEX builds are viable |

### Spell Combat
| # | Test Name | Gameplay Impact |
|---|-----------|-----------------|
| 7 | `test_spell_damage_scales_with_intelligence` | Mages feel stronger as INT increases |
| 8 | `test_spell_damage_scales_with_skill_level` | Leveling up spells is rewarding |
| 9 | `test_elemental_resistance_reduces_damage` | Resistance gear matters |
| 10 | `test_elemental_weakness_increases_damage` | Exploit enemy weaknesses |
| 11 | `test_heal_scales_with_int_and_skill` | Healers scale properly |

### Economy
| # | Test Name | Gameplay Impact |
|---|-----------|-----------------|
| 12 | `test_merchant_buy_price_is_full_value` | Buying feels fair |
| 13 | `test_merchant_sell_price_is_half` | Selling feels fair |
| 14 | `test_death_penalty_takes_50_percent_gold` | Death has consequences |
| 15 | `test_item_value_scales_with_level` | Higher level items worth more |
| 16 | `test_rarity_multiplies_item_value` | Rare items worth more gold |

---

## 2. PROGRESSION (test_progression.py)

### XP and Leveling
| # | Test Name | Gameplay Impact |
|---|-----------|-----------------|
| 17 | `test_melee_hit_grants_melee_xp` | Using melee levels melee skill |
| 18 | `test_spell_hit_grants_magic_xp` | Using spells levels magic skill |
| 19 | `test_heal_grants_nature_magic_xp` | Healing levels nature magic |
| 20 | `test_kill_grants_bonus_xp` | Killing enemies gives XP bonus |
| 21 | `test_xp_required_increases_per_level` | Higher levels need more XP |
| 22 | `test_character_level_is_sum_of_skills` | Character level reflects total progress |
| 23 | `test_skill_levelup_grants_stat_bonus` | Leveling up makes you stronger |
| 24 | `test_melee_levelup_gives_strength` | Melee leveling gives expected stats |
| 25 | `test_magic_levelup_gives_mana` | Magic leveling gives expected stats |

### Skill Tree
| # | Test Name | Gameplay Impact |
|---|-----------|-----------------|
| 26 | `test_can_allocate_skill_points` | Skill tree works |
| 27 | `test_skill_requirements_enforced` | Can't skip skill prerequisites |
| 28 | `test_skill_points_saved_and_loaded` | Progress persists |

---

## 3. MOVEMENT & COLLISION (test_movement.py)

### Basic Movement
| # | Test Name | Gameplay Impact |
|---|-----------|-----------------|
| 29 | `test_entity_moves_toward_target` | Clicking to move works |
| 30 | `test_entity_stops_at_walls` | Can't walk through walls |
| 31 | `test_entity_slides_along_walls` | Movement feels smooth near walls |
| 32 | `test_movement_respects_speed_stat` | Slow enemies are slow, fast are fast |
| 33 | `test_downed_entities_dont_move` | Downed characters stay put |

### Projectiles
| # | Test Name | Gameplay Impact |
|---|-----------|-----------------|
| 34 | `test_projectiles_fly_freely` | Spells actually move |
| 35 | `test_projectiles_stop_at_walls` | Spells don't go through walls |
| 36 | `test_projectiles_hit_targets` | Spells deal damage |
| 37 | `test_projectiles_track_moving_targets` | Homing spells work |
| 38 | `test_projectiles_timeout_after_5_seconds` | Stray projectiles cleanup |

### Pathfinding
| # | Test Name | Gameplay Impact |
|---|-----------|-----------------|
| 39 | `test_pathfinding_finds_route_around_wall` | AI can navigate |
| 40 | `test_pathfinding_returns_none_if_blocked` | AI doesn't freeze on impossible paths |
| 41 | `test_pathfinding_prefers_shorter_routes` | AI takes reasonable paths |

---

## 4. LINE OF SIGHT (test_los.py)

### Basic LOS
| # | Test Name | Gameplay Impact |
|---|-----------|-----------------|
| 42 | `test_los_clear_in_open_room` | Can see enemies in same room |
| 43 | `test_los_blocked_by_wall` | Can't see through walls |
| 44 | `test_los_blocked_by_corner` | Can't shoot around corners |
| 45 | `test_los_through_doorway` | Can see through open doors |
| 46 | `test_los_diagonal_wall_blocks` | Diagonal walls block properly |

### Combat LOS
| # | Test Name | Gameplay Impact |
|---|-----------|-----------------|
| 47 | `test_melee_attack_requires_los` | Can't melee through walls |
| 48 | `test_spell_cast_requires_los` | Can't cast through walls |
| 49 | `test_ai_attack_requires_los` | Enemies can't cheat with LOS |
| 50 | `test_ally_spell_requires_los` | Lyra can't cast through walls |

---

## 5. COMBAT SYSTEM (test_combat.py)

### Attacks
| # | Test Name | Gameplay Impact |
|---|-----------|-----------------|
| 51 | `test_melee_attack_deals_damage` | Basic attacks work |
| 52 | `test_ranged_attack_deals_damage` | Ranged attacks work |
| 53 | `test_attack_respects_cooldown` | Can't attack spam |
| 54 | `test_attack_uses_weapon_range` | Weapon range matters |
| 55 | `test_no_friendly_fire_melee` | Can't hurt allies with melee |
| 56 | `test_no_friendly_fire_spells` | Can't hurt allies with spells |

### Death & Downed
| # | Test Name | Gameplay Impact |
|---|-----------|-----------------|
| 57 | `test_entity_dies_at_zero_health` | Enemies can be killed |
| 58 | `test_party_member_downs_not_dies` | Party members get downed, not killed |
| 59 | `test_downed_ally_can_be_revived` | Revive mechanic works |
| 60 | `test_all_party_downed_triggers_wipe` | Party wipe triggers properly |
| 61 | `test_party_wipe_loses_gold` | Death has consequences |
| 62 | `test_party_wipe_respawns_at_entrance` | Can continue after wipe |

### Status Effects
| # | Test Name | Gameplay Impact |
|---|-----------|-----------------|
| 63 | `test_stun_prevents_actions` | Stun CC works |
| 64 | `test_slow_reduces_speed` | Slow CC works |
| 65 | `test_burn_deals_damage_over_time` | DoT effects work |
| 66 | `test_poison_stacks` | Poison can stack |
| 67 | `test_status_effects_expire` | Effects don't last forever |

---

## 6. SPELLS & ABILITIES (test_spells.py)

### Melee Abilities
| # | Test Name | Gameplay Impact |
|---|-----------|-----------------|
| 68 | `test_whirlwind_hits_multiple_enemies` | Whirlwind is AoE |
| 69 | `test_whirlwind_hits_6_times` | Whirlwind multi-hit works |
| 70 | `test_leap_strike_moves_player` | Leap Strike has mobility |
| 71 | `test_leap_strike_stuns_target` | Leap Strike CC works |
| 72 | `test_leap_strike_blocked_by_walls` | Can't leap through walls |
| 73 | `test_crushing_blow_reduces_armor` | Crushing Blow debuff works |
| 74 | `test_shield_bash_knocks_back` | Shield Bash knockback works |

### Projectile Spells
| # | Test Name | Gameplay Impact |
|---|-----------|-----------------|
| 75 | `test_fireball_creates_projectile` | Fireball fires |
| 76 | `test_fireball_deals_fire_damage` | Fireball damage type is fire |
| 77 | `test_ice_shard_slows_target` | Ice Shard CC works |
| 78 | `test_heal_restores_health` | Heal spell heals |
| 79 | `test_heal_targets_allies_only` | Can't heal enemies |

### Cooldowns
| # | Test Name | Gameplay Impact |
|---|-----------|-----------------|
| 80 | `test_spell_goes_on_cooldown_after_cast` | Can't spam spells |
| 81 | `test_cooldown_decrements_over_time` | Cooldowns recover |
| 82 | `test_global_cooldown_prevents_spam` | GCD works |
| 83 | `test_mana_consumed_on_cast` | Spells cost mana |
| 84 | `test_insufficient_mana_prevents_cast` | Can't cast without mana |

---

## 7. AI BEHAVIOR (test_ai.py)

### Enemy AI
| # | Test Name | Gameplay Impact |
|---|-----------|-----------------|
| 85 | `test_enemy_aggros_when_player_in_range` | Enemies notice you |
| 86 | `test_enemy_chases_player` | Enemies pursue you |
| 87 | `test_enemy_attacks_when_in_range` | Enemies fight back |
| 88 | `test_enemy_respects_leash_range` | Enemies don't chase forever |
| 89 | `test_enemy_returns_to_spawn_when_leashed` | Enemies reset properly |

### Ally AI
| # | Test Name | Gameplay Impact |
|---|-----------|-----------------|
| 90 | `test_ally_follows_leader` | Lyra follows you |
| 91 | `test_ally_attacks_nearby_enemies` | Lyra helps in combat |
| 92 | `test_ally_heals_wounded_allies` | Lyra heals when needed |
| 93 | `test_ally_respects_los_for_spells` | Lyra doesn't cast through walls |
| 94 | `test_ally_ai_disabled_when_selected` | Can control Lyra directly |

---

## 8. INVENTORY & EQUIPMENT (test_inventory.py)

### Basic Inventory
| # | Test Name | Gameplay Impact |
|---|-----------|-----------------|
| 95 | `test_can_add_item_to_inventory` | Picking up items works |
| 96 | `test_can_remove_item_from_inventory` | Dropping/selling works |
| 97 | `test_inventory_has_max_capacity` | Inventory has limits |
| 98 | `test_stackable_items_stack` | Potions stack properly |

### Equipment
| # | Test Name | Gameplay Impact |
|---|-----------|-----------------|
| 99 | `test_equipping_weapon_changes_damage` | Weapons affect damage |
| 100 | `test_equipping_armor_changes_armor_stat` | Armor items work |
| 101 | `test_unequip_returns_item_to_inventory` | Unequip works |
| 102 | `test_equipment_slot_restrictions` | Can't wear sword as helmet |

### Consumables
| # | Test Name | Gameplay Impact |
|---|-----------|-----------------|
| 103 | `test_health_potion_restores_health` | Health potions work |
| 104 | `test_mana_potion_restores_mana` | Mana potions work |
| 105 | `test_consumable_removed_after_use` | Using potion consumes it |

---

## 9. SAVE/LOAD SYSTEM (test_save_load.py)

### Character Data
| # | Test Name | Gameplay Impact |
|---|-----------|-----------------|
| 106 | `test_save_preserves_player_position` | Position persists |
| 107 | `test_save_preserves_health_mana` | HP/MP persists |
| 108 | `test_save_preserves_skill_levels` | Skill progress persists |
| 109 | `test_save_preserves_skill_xp` | XP progress persists |
| 110 | `test_save_preserves_gold` | Gold persists |
| 111 | `test_save_preserves_inventory` | Items persist |
| 112 | `test_save_preserves_equipment` | Equipped items persist |
| 113 | `test_save_preserves_spell_order` | Spell bar order persists |

### World State
| # | Test Name | Gameplay Impact |
|---|-----------|-----------------|
| 114 | `test_save_preserves_dungeon_level` | Current level persists |
| 115 | `test_save_preserves_dungeon_seed` | Same dungeon on reload |
| 116 | `test_save_preserves_enemy_positions` | Enemy state persists |
| 117 | `test_save_preserves_explored_map` | Fog of war persists |

### Load Validation
| # | Test Name | Gameplay Impact |
|---|-----------|-----------------|
| 118 | `test_load_restores_player_position` | Can continue from save |
| 119 | `test_load_restores_party_composition` | Both characters load |
| 120 | `test_load_handles_missing_save_file` | Graceful handling |
| 121 | `test_load_handles_corrupted_save` | Don't crash on bad data |

---

## 10. DUNGEON GENERATION (test_dungeon.py)

### Basic Generation
| # | Test Name | Gameplay Impact |
|---|-----------|-----------------|
| 122 | `test_dungeon_has_spawn_point` | Player can spawn |
| 123 | `test_dungeon_has_exit_stairs` | Can progress to next level |
| 124 | `test_spawn_and_exit_are_connected` | Can reach the exit |
| 125 | `test_rooms_are_connected` | No isolated rooms |
| 126 | `test_dungeon_size_increases_with_level` | Higher levels are bigger |

### Props & Enemies
| # | Test Name | Gameplay Impact |
|---|-----------|-----------------|
| 127 | `test_enemies_spawn_in_rooms` | Enemies exist |
| 128 | `test_enemy_count_scales_with_level` | Higher levels have more enemies |
| 129 | `test_props_spawn_in_rooms` | Barrels, crates exist |
| 130 | `test_loot_chests_spawn` | Can find loot |

---

## 11. TOWN & SHOP (test_town.py)

### Town Navigation
| # | Test Name | Gameplay Impact |
|---|-----------|-----------------|
| 131 | `test_can_enter_town` | Town portal works |
| 132 | `test_can_leave_town` | Can return to dungeon |
| 133 | `test_party_position_saved_on_enter` | Return to same spot |
| 134 | `test_enemies_hidden_in_town` | No combat in town |
| 135 | `test_movement_works_in_town` | Can walk around town |

### Shopping
| # | Test Name | Gameplay Impact |
|---|-----------|-----------------|
| 136 | `test_shop_shows_level_appropriate_items` | Shop scales with progress |
| 137 | `test_can_buy_item_with_enough_gold` | Buying works |
| 138 | `test_cannot_buy_without_gold` | Need gold to buy |
| 139 | `test_buying_removes_gold` | Gold deducted |
| 140 | `test_buying_adds_to_inventory` | Item received |
| 141 | `test_can_sell_inventory_item` | Selling works |
| 142 | `test_selling_adds_gold` | Get paid for selling |
| 143 | `test_selling_removes_from_inventory` | Item removed |

---

## 12. UI & INPUT (test_ui.py)

### Character Control
| # | Test Name | Gameplay Impact |
|---|-----------|-----------------|
| 144 | `test_arrow_keys_move_selected_character` | Keyboard movement works |
| 145 | `test_right_click_moves_to_position` | Mouse movement works |
| 146 | `test_tab_cycles_character_selection` | Can switch characters |
| 147 | `test_f1_f2_select_specific_character` | Direct character select works |
| 148 | `test_selected_character_responds_to_input` | Only selected char moves |

### Spell Casting
| # | Test Name | Gameplay Impact |
|---|-----------|-----------------|
| 149 | `test_qwer_casts_hero_spells` | Hero spell keys work |
| 150 | `test_asdf_casts_lyra_spells` | Lyra spell keys work |
| 151 | `test_clicking_enemy_targets_spell` | Can target spells |

### Menus
| # | Test Name | Gameplay Impact |
|---|-----------|-----------------|
| 152 | `test_i_opens_inventory` | Inventory hotkey works |
| 153 | `test_escape_closes_menu` | Can close menus |
| 154 | `test_h_opens_town_portal` | Town portal hotkey works |

---

## Summary

**Total Tests: 154**

### By Category:
- Combat Formulas: 16 tests
- Progression: 12 tests  
- Movement & Collision: 13 tests
- Line of Sight: 9 tests
- Combat System: 17 tests
- Spells & Abilities: 17 tests
- AI Behavior: 10 tests
- Inventory & Equipment: 11 tests
- Save/Load: 16 tests
- Dungeon Generation: 9 tests
- Town & Shop: 13 tests
- UI & Input: 11 tests

### Priority Order:
1. **Save/Load** - Players lose progress if broken
2. **Combat Formulas** - Core gameplay feel
3. **Combat System** - Game is unplayable if broken
4. **Movement** - Can't play if can't move
5. **Spells** - Major feature
6. **AI** - Enemies and allies need to work
7. **Inventory** - Loot is core loop
8. **Line of Sight** - Exploits if broken
9. **Progression** - Long-term engagement
10. **Dungeon Gen** - Variety and replayability
11. **Town/Shop** - Important but not core
12. **UI/Input** - Usually stable

