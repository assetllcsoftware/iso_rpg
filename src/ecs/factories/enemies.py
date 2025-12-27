"""Enemy entity factories."""

import esper
from typing import Optional

from ..components import (
    Position, Velocity, Facing, Speed, CollisionRadius, Direction,
    Health, Mana,
    CombatStats, AttackCooldown, CombatTarget, Weapon, Resistances,
    AIController, EnemyAI, AggroRange, LeashRange,
    Sprite, Animation, AnimationState, RenderOffset, HealthBar,
    Enemy,
    StatusEffects
)
from ...data.loader import data_loader
from ...core.constants import AIState
from ...core.formulas import calculate_enemy_stats


def create_enemy(
    enemy_id: str,
    x: float,
    y: float,
    level: int = 1
) -> int:
    """Create an enemy entity from data definition.
    
    Args:
        enemy_id: Enemy ID from enemies.yaml (e.g., "skeleton", "spider")
        x, y: Starting position
        level: Dungeon level for scaling
    
    Returns:
        Entity ID
    """
    data = data_loader.get_enemy(enemy_id)
    if not data:
        raise ValueError(f"Unknown enemy: {enemy_id}")
    
    base_stats = data.get("base_stats", {})
    behavior = data.get("behavior", {})
    scaling = data.get("scaling", {})
    
    # Scale stats by level
    scaled = calculate_enemy_stats({
        "health": base_stats.get("health", 50),
        "damage": base_stats.get("damage", 10),
        "armor": base_stats.get("armor", 0),
        "xp_value": data.get("xp_value", 15),
        "gold_min": data.get("gold_range", [3, 8])[0],
        "gold_max": data.get("gold_range", [3, 8])[1],
        "health_per_level": scaling.get("health_per_level", 10),
        "damage_per_level": scaling.get("damage_per_level", 2),
        "armor_per_level": scaling.get("armor_per_level", 1),
    }, level)
    
    # Create entity
    entity = esper.create_entity(
        # Transform
        Position(x=x, y=y),
        Velocity(),
        Facing(direction=Direction.DOWN),
        Speed(value=base_stats.get("speed", 3.5)),
        CollisionRadius(radius=0.4),
        
        # Health
        Health(current=scaled["health"], maximum=scaled["health"]),
        
        # Combat
        CombatStats(
            damage=scaled["damage"],
            armor=scaled["armor"],
            attack_speed=base_stats.get("attack_speed", 1.0),
            attack_range=base_stats.get("attack_range", 1.5)
        ),
        AttackCooldown(),
        CombatTarget(),
        
        # AI
        AIController(
            state=AIState.IDLE,
            home_x=x,
            home_y=y
        ),
        EnemyAI(enemy_type=enemy_id),
        AggroRange(range=behavior.get("aggro_range", 6.0)),
        LeashRange(range=behavior.get("leash_range", 15.0)),
        
        # Rendering
        Sprite(sprite_set=data.get("sprite_set", enemy_id)),
        Animation(state=AnimationState.IDLE),
        RenderOffset(y=-16),
        HealthBar(),
        
        # Tags
        Enemy(),
        
        # Status effects
        StatusEffects(),
    )
    
    # Add resistances if any
    resistances = data.get("resistances", {})
    if resistances:
        esper.add_component(entity, Resistances(
            fire=resistances.get("fire", 0.0),
            ice=resistances.get("ice", 0.0),
            lightning=resistances.get("lightning", 0.0),
            poison=resistances.get("poison", 0.0),
            holy=resistances.get("holy", 0.0),
        ))
    
    # Add mana if enemy has abilities
    abilities = data.get("abilities", [])
    if abilities:
        esper.add_component(entity, Mana(current=100, maximum=100))
    
    return entity


def create_enemies_for_level(
    spawn_points: list,
    dungeon_level: int,
    dungeon_config: dict
) -> list:
    """Create enemies for a dungeon level.
    
    Args:
        spawn_points: List of (x, y) spawn positions
        dungeon_level: Current dungeon level
        dungeon_config: Dungeon configuration with enemy tables
    
    Returns:
        List of enemy entity IDs
    """
    import random
    
    entities = []
    
    # Get enemy table for this level
    spawning = dungeon_config.get("spawning", {})
    enemy_table = spawning.get("enemy_table", [])
    
    # Find applicable table entry
    applicable_enemies = []
    for entry in enemy_table:
        levels = entry.get("levels", [1, 99])
        if levels[0] <= dungeon_level <= levels[1]:
            applicable_enemies = entry.get("enemies", [])
            break
    
    if not applicable_enemies:
        # Default to skeleton
        applicable_enemies = [{"id": "skeleton", "weight": 100}]
    
    # Build weighted list
    weighted = []
    for enemy in applicable_enemies:
        enemy_id = enemy.get("id", "skeleton")
        weight = enemy.get("weight", 50)
        weighted.extend([enemy_id] * weight)
    
    # Spawn enemies
    for x, y in spawn_points:
        if weighted:
            enemy_id = random.choice(weighted)
            entity = create_enemy(enemy_id, x, y, dungeon_level)
            entities.append(entity)
    
    return entities

