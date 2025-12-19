"""Magic system with combat and nature magic."""

from ..engine.constants import SKILL_COMBAT_MAGIC, SKILL_NATURE_MAGIC


class Spell:
    """A castable spell."""
    
    def __init__(self, name, mana_cost, skill_type, level_req=0):
        self.name = name
        self.mana_cost = mana_cost
        self.skill_type = skill_type  # combat_magic or nature_magic
        self.level_req = level_req
        
        # Spell properties
        self.damage = 0
        self.heal_amount = 0
        self.range = 6.0
        self.area_radius = 0  # 0 = single target
        self.cooldown = 1.0
        self.duration = 0  # For buffs/debuffs
        
        # Visual
        self.color = (100, 100, 255)
        self.description = ""
    
    def can_cast(self, caster):
        """Check if caster can use this spell."""
        if caster.mana < self.mana_cost:
            return False
        skill_level = caster.skills.get(self.skill_type, 0)
        if skill_level < self.level_req:
            return False
        return True
    
    def get_damage(self, caster):
        """Calculate spell damage based on caster stats."""
        base = self.damage
        int_bonus = caster.intelligence / 10
        skill_bonus = caster.skills.get(self.skill_type, 0) / 5
        return int(base * (1 + int_bonus + skill_bonus))
    
    def get_heal(self, caster):
        """Calculate heal amount based on caster stats."""
        base = self.heal_amount
        int_bonus = caster.intelligence / 15
        skill_bonus = caster.skills.get(self.skill_type, 0) / 5
        return int(base * (1 + int_bonus + skill_bonus))


# Combat Magic Spells
COMBAT_SPELLS = {
    'fireball': {
        'name': 'Fireball',
        'mana_cost': 15,
        'damage': 25,
        'range': 7.0,
        'area_radius': 2.0,
        'cooldown': 2.0,
        'level_req': 0,
        'color': (255, 100, 50),
        'description': 'Hurls a ball of fire that explodes on impact.',
    },
    'lightning_bolt': {
        'name': 'Lightning Bolt',
        'mana_cost': 12,
        'damage': 20,
        'range': 8.0,
        'cooldown': 1.5,
        'level_req': 3,
        'color': (200, 200, 255),
        'description': 'Strikes target with a bolt of lightning.',
    },
    'ice_shard': {
        'name': 'Ice Shard',
        'mana_cost': 8,
        'damage': 12,
        'range': 6.0,
        'cooldown': 1.0,
        'level_req': 0,
        'color': (150, 200, 255),
        'description': 'Launches a shard of ice at the enemy.',
    },
    'meteor': {
        'name': 'Meteor',
        'mana_cost': 40,
        'damage': 60,
        'range': 6.0,
        'area_radius': 3.0,
        'cooldown': 5.0,
        'level_req': 15,
        'color': (255, 150, 100),
        'description': 'Calls down a devastating meteor from the sky.',
    },
    'chain_lightning': {
        'name': 'Chain Lightning',
        'mana_cost': 25,
        'damage': 15,
        'range': 6.0,
        'cooldown': 3.0,
        'level_req': 8,
        'color': (180, 180, 255),
        'description': 'Lightning that jumps between nearby enemies.',
    },
}

# Nature Magic Spells
NATURE_SPELLS = {
    'heal': {
        'name': 'Heal',
        'mana_cost': 10,
        'heal_amount': 30,
        'range': 6.0,
        'cooldown': 1.5,
        'level_req': 0,
        'color': (100, 255, 100),
        'description': 'Heals a single target.',
    },
    'group_heal': {
        'name': 'Group Heal',
        'mana_cost': 25,
        'heal_amount': 20,
        'range': 0,
        'area_radius': 5.0,
        'cooldown': 4.0,
        'level_req': 5,
        'color': (150, 255, 150),
        'description': 'Heals all nearby party members.',
    },
    'regeneration': {
        'name': 'Regeneration',
        'mana_cost': 15,
        'heal_amount': 5,  # Per second
        'duration': 10.0,
        'range': 6.0,
        'cooldown': 15.0,
        'level_req': 3,
        'color': (100, 200, 100),
        'description': 'Target regenerates health over time.',
    },
    'poison_cloud': {
        'name': 'Poison Cloud',
        'mana_cost': 18,
        'damage': 8,  # Per second
        'duration': 5.0,
        'range': 5.0,
        'area_radius': 2.5,
        'cooldown': 6.0,
        'level_req': 4,
        'color': (100, 180, 50),
        'description': 'Creates a cloud of poison that damages enemies.',
    },
    'summon_wolf': {
        'name': 'Summon Wolf',
        'mana_cost': 30,
        'duration': 30.0,
        'cooldown': 45.0,
        'level_req': 8,
        'color': (150, 140, 120),
        'description': 'Summons a wolf companion to fight for you.',
    },
    'entangle': {
        'name': 'Entangle',
        'mana_cost': 12,
        'duration': 4.0,
        'range': 5.0,
        'area_radius': 2.0,
        'cooldown': 8.0,
        'level_req': 2,
        'color': (80, 150, 50),
        'description': 'Roots enemies in place with vines.',
    },
}


def create_spell(spell_id):
    """Create a spell from template."""
    if spell_id in COMBAT_SPELLS:
        data = COMBAT_SPELLS[spell_id]
        skill_type = SKILL_COMBAT_MAGIC
    elif spell_id in NATURE_SPELLS:
        data = NATURE_SPELLS[spell_id]
        skill_type = SKILL_NATURE_MAGIC
    else:
        return None
    
    spell = Spell(data['name'], data['mana_cost'], skill_type, data.get('level_req', 0))
    spell.damage = data.get('damage', 0)
    spell.heal_amount = data.get('heal_amount', 0)
    spell.range = data.get('range', 6.0)
    spell.area_radius = data.get('area_radius', 0)
    spell.cooldown = data.get('cooldown', 1.0)
    spell.duration = data.get('duration', 0)
    spell.color = data.get('color', (100, 100, 255))
    spell.description = data.get('description', '')
    
    return spell


class SpellBook:
    """Collection of learned spells for a character."""
    
    def __init__(self):
        self.spells = {}  # spell_id -> Spell
        self.cooldowns = {}  # spell_id -> remaining cooldown
    
    def learn_spell(self, spell_id):
        """Learn a new spell."""
        spell = create_spell(spell_id)
        if spell:
            self.spells[spell_id] = spell
            self.cooldowns[spell_id] = 0
            return True
        return False
    
    def can_cast(self, spell_id, caster):
        """Check if spell can be cast."""
        if spell_id not in self.spells:
            return False
        if self.cooldowns.get(spell_id, 0) > 0:
            return False
        return self.spells[spell_id].can_cast(caster)
    
    def get_available_spells(self, caster):
        """Get list of spells that can be cast."""
        available = []
        for spell_id, spell in self.spells.items():
            if spell.can_cast(caster) and self.cooldowns.get(spell_id, 0) <= 0:
                available.append((spell_id, spell))
        return available
    
    def update(self, dt):
        """Update cooldowns."""
        for spell_id in self.cooldowns:
            if self.cooldowns[spell_id] > 0:
                self.cooldowns[spell_id] -= dt


class SpellEffect:
    """Active spell effect in the world."""
    
    def __init__(self, spell, caster, target_pos, targets):
        self.spell = spell
        self.caster = caster
        self.target_pos = target_pos
        self.targets = targets
        
        self.duration = spell.duration if spell.duration > 0 else 0.5
        self.elapsed = 0
        self.active = True
        
        # For damage/heal over time
        self.tick_timer = 0
        self.tick_interval = 1.0
    
    def update(self, dt):
        """Update spell effect."""
        self.elapsed += dt
        
        if self.elapsed >= self.duration:
            self.active = False
            return
        
        # Handle periodic effects
        if self.spell.duration > 0:
            self.tick_timer += dt
            if self.tick_timer >= self.tick_interval:
                self.tick_timer -= self.tick_interval
                self._apply_tick()
    
    def _apply_tick(self):
        """Apply periodic effect tick."""
        for target in self.targets:
            if not hasattr(target, 'health') or target.health <= 0:
                continue
            
            if self.spell.damage > 0:
                damage = self.spell.get_damage(self.caster) // int(self.spell.duration)
                target.take_damage(damage, self.caster)
            
            if self.spell.heal_amount > 0 and hasattr(target, 'heal'):
                heal = self.spell.get_heal(self.caster) // int(self.spell.duration)
                target.heal(heal)


class MagicSystem:
    """Manages spell casting and effects."""
    
    def __init__(self):
        self.active_effects = []
    
    def cast_spell(self, caster, spell_book, spell_id, target_pos, world):
        """Cast a spell."""
        if not spell_book.can_cast(spell_id, caster):
            return None
        
        spell = spell_book.spells[spell_id]
        
        # Consume mana
        caster.mana -= spell.mana_cost
        
        # Set cooldown
        spell_book.cooldowns[spell_id] = spell.cooldown
        
        # Gain skill XP
        caster.gain_skill_xp(spell.skill_type, 15)
        
        # Find targets
        targets = []
        if spell.area_radius > 0:
            # AoE spell
            if spell.damage > 0:
                targets = world.get_enemies_in_range(
                    target_pos[0], target_pos[1], spell.area_radius
                )
            elif spell.heal_amount > 0:
                for char in world.characters:
                    if char.distance_to(target_pos) <= spell.area_radius:
                        targets.append(char)
        else:
            # Single target
            entity = world.get_entity_at(target_pos[0], target_pos[1], radius=1.0)
            if entity:
                targets = [entity]
        
        # Apply immediate effects
        for target in targets:
            if spell.damage > 0 and hasattr(target, 'take_damage'):
                damage = spell.get_damage(caster)
                target.take_damage(damage, caster)
            
            if spell.heal_amount > 0 and hasattr(target, 'heal'):
                if spell.duration == 0:
                    heal = spell.get_heal(caster)
                    target.heal(heal)
        
        # Create spell effect for duration spells
        if spell.duration > 0:
            effect = SpellEffect(spell, caster, target_pos, targets)
            self.active_effects.append(effect)
        
        return spell
    
    def update(self, dt):
        """Update all active spell effects."""
        self.active_effects = [
            effect for effect in self.active_effects
            if effect.active
        ]
        
        for effect in self.active_effects:
            effect.update(dt)

