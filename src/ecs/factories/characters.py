"""Character entity factories."""

import esper
from typing import Optional

from ..components import (
    Position, Velocity, Facing, Speed, CollisionRadius, Direction,
    Health, Mana, Regeneration,
    CombatStats, AttackCooldown, Weapon,
    Attributes, SkillLevels, SkillXP, CharacterLevel, CharacterClass, CharacterName,
    Equipment, Inventory, Gold,
    SpellBook,
    AIController, AllyAI, AggroRange,
    Sprite, Animation, AnimationState, RenderOffset, HealthBar,
    PlayerControlled, Selected, PartyMember, Ally,
    StatusEffects
)
from ...data.loader import data_loader
from ...core.constants import AIState


def create_character(
    char_id: str,
    x: float,
    y: float,
    party_index: int = 0
) -> int:
    """Create a character entity from data definition.
    
    Args:
        char_id: Character ID from characters.yaml (e.g., "hero", "lyra")
        x, y: Starting position
        party_index: 0 for leader, 1+ for allies
    
    Returns:
        Entity ID
    """
    data = data_loader.get_character(char_id)
    if not data:
        raise ValueError(f"Unknown character: {char_id}")
    
    stats = data.get("base_stats", {})
    skills = data.get("starting_skills", {})
    
    # Create entity with all components
    entity = esper.create_entity(
        # Transform
        Position(x=x, y=y),
        Velocity(),
        Facing(direction=Direction.DOWN),
        Speed(value=stats.get("speed", 5.0)),
        CollisionRadius(radius=0.4),
        
        # Health & Mana
        Health(current=stats.get("health", 100), maximum=stats.get("health", 100)),
        Mana(current=stats.get("mana", 100), maximum=stats.get("mana", 100)),
        Regeneration(),
        
        # Combat
        CombatStats(
            damage=stats.get("damage", 10),
            armor=stats.get("armor", 0),
            attack_speed=stats.get("attack_speed", 1.0),
            attack_range=stats.get("attack_range", 1.5)
        ),
        AttackCooldown(),
        
        # Stats
        Attributes(
            strength=stats.get("strength", 10),
            dexterity=stats.get("dexterity", 10),
            intelligence=stats.get("intelligence", 10)
        ),
        SkillLevels(
            melee=skills.get("melee", 0),
            ranged=skills.get("ranged", 0),
            combat_magic=skills.get("combat_magic", 0),
            nature_magic=skills.get("nature_magic", 0)
        ),
        SkillXP(),
        CharacterLevel(level=1),
        CharacterClass(class_name=data.get("class", "warrior")),
        CharacterName(name=data.get("name", "Unknown")),
        
        # Equipment & Inventory
        Equipment(),
        Inventory(),
        Gold(amount=data.get("starting_gold", 0)),
        
        # Spells
        SpellBook(),
        
        # Rendering
        Sprite(sprite_set=data.get("sprite_set", "hero")),
        Animation(state=AnimationState.IDLE),
        RenderOffset(y=-16),
        HealthBar(),
        
        # Party
        PartyMember(party_index=party_index),
        
        # Status effects
        StatusEffects(),
    )
    
    # All party members can be player-controlled (when selected)
    esper.add_component(entity, PlayerControlled())
    
    # Only first party member starts selected
    if party_index == 0:
        esper.add_component(entity, Selected())
    
    # Non-leader party members also get AI for when they're not selected
    if party_index > 0:
        offset = data.get("formation_offset", [1.5, 0.5])
        esper.add_component(entity, Ally())
        esper.add_component(entity, AllyAI(
            leader_id=-1,  # Set later
            formation_offset=tuple(offset)
        ))
        esper.add_component(entity, AIController(state=AIState.FOLLOW))
    
    # Add starting equipment
    equipment_comp = esper.component_for_entity(entity, Equipment)
    for slot, item_id in data.get("starting_equipment", {}).items():
        if item_id:
            equipment_comp.equip(slot, item_id)
    
    # Add starting inventory
    inventory_comp = esper.component_for_entity(entity, Inventory)
    for item_entry in data.get("starting_inventory", []):
        if isinstance(item_entry, dict):
            inventory_comp.add(item_entry["item"], item_entry.get("quantity", 1))
    
    # Add starting spells
    spellbook = esper.component_for_entity(entity, SpellBook)
    for spell_id in data.get("starting_spells", []):
        spellbook.learn(spell_id)
    
    # Set weapon from equipment
    main_hand = equipment_comp.get("main_hand")
    if main_hand:
        item_data = data_loader.get_item(main_hand)
        if item_data:
            esper.add_component(entity, Weapon(
                item_id=main_hand,
                damage=item_data.get("damage", 10),
                attack_range=item_data.get("attack_range", 1.5),
                attack_speed=item_data.get("attack_speed", 1.0),
                weapon_type=item_data.get("weapon_type", "melee"),
                fire_damage=item_data.get("fire_damage", 0),
                ice_damage=item_data.get("ice_damage", 0),
            ))
    
    return entity


def create_party(x: float, y: float) -> list:
    """Create the starting party (Hero + Lyra).
    
    Returns:
        List of entity IDs [hero_id, lyra_id]
    """
    hero = create_character("hero", x, y, party_index=0)
    lyra = create_character("lyra", x + 1.5, y + 0.5, party_index=1)
    
    # Set Lyra to follow Hero
    ally_ai = esper.component_for_entity(lyra, AllyAI)
    ally_ai.leader_id = hero
    
    return [hero, lyra]

