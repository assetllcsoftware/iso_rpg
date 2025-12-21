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
        
        # Special flags
        self.heals_party = False  # Heals party members instead of targeting
        self.revives = False  # Can revive downed allies
        
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


# Combat Magic Spells - Exponential cooldowns: ~1s -> ~3s -> ~10s -> ~30s
COMBAT_SPELLS = {
    # TIER 1: Starter spells - ~1s cooldown, spammable
    'ice_shard': {
        'name': 'Ice Shard',
        'mana_cost': 0,  # FREE - cooldown only spam spell
        'damage': 10,
        'range': 6.0,
        'cooldown': 1.0,
        'level_req': 0,
        'color': (150, 200, 255),
        'description': 'Fast ice projectile. No mana cost!',
    },
    'fireball': {
        'name': 'Fireball',
        'mana_cost': 5,
        'damage': 15,
        'range': 7.0,
        'area_radius': 1.5,
        'cooldown': 1.5,
        'level_req': 0,
        'color': (255, 100, 50),
        'description': 'Explosive fire damage. Good starter spell.',
    },
    
    # TIER 2: Early unlocks - ~3s cooldown, medium power
    'lightning_bolt': {
        'name': 'Lightning Bolt',
        'mana_cost': 8,
        'damage': 35,
        'range': 8.0,
        'cooldown': 3.0,
        'level_req': 2,
        'color': (200, 200, 255),
        'description': 'Instant lightning strike. Good damage.',
    },
    'chain_lightning': {
        'name': 'Chain Lightning',
        'mana_cost': 15,
        'damage': 25,
        'range': 6.0,
        'cooldown': 4.0,
        'level_req': 3,
        'color': (180, 180, 255),
        'chain_targets': 3,
        'description': 'Jumps to 3 nearby enemies. Great for groups.',
    },
    
    # TIER 3: Mid-game - ~10s cooldown, high power
    'inferno': {
        'name': 'Inferno',
        'mana_cost': 25,
        'damage': 80,
        'range': 6.0,
        'area_radius': 3.0,
        'cooldown': 10.0,
        'level_req': 5,
        'color': (255, 80, 30),
        'description': 'Massive fire explosion. Devastating AoE.',
    },
    'blizzard': {
        'name': 'Blizzard',
        'mana_cost': 30,
        'damage': 60,
        'range': 7.0,
        'area_radius': 4.0,
        'cooldown': 12.0,
        'level_req': 6,
        'color': (180, 220, 255),
        'description': 'Frozen storm damages all in area.',
    },
    
    # TIER 4: Late-game - ~30s cooldown, massive power
    'meteor': {
        'name': 'Meteor',
        'mana_cost': 50,
        'damage': 200,
        'range': 6.0,
        'area_radius': 4.0,
        'cooldown': 30.0,
        'level_req': 10,
        'color': (255, 150, 100),
        'description': 'Devastating meteor from the sky. Ultimate destruction.',
    },
    'armageddon': {
        'name': 'Armageddon',
        'mana_cost': 80,
        'damage': 150,
        'range': 0,  # Centered on caster
        'area_radius': 8.0,
        'cooldown': 45.0,
        'level_req': 15,
        'color': (255, 50, 50),
        'description': 'Rain of fire around you. Destroys everything nearby.',
    },
}

# Nature Magic Spells - Exponential cooldowns: ~1s -> ~3s -> ~10s -> ~30s
NATURE_SPELLS = {
    # TIER 1: Starter spells - ~1s cooldown
    'heal': {
        'name': 'Heal',
        'mana_cost': 5,
        'heal_amount': 25,
        'range': 0,
        'area_radius': 3.0,
        'cooldown': 1.5,
        'level_req': 0,
        'color': (100, 255, 100),
        'description': 'Quick heal for you and nearby allies.',
        'heals_party': True,
    },
    
    # TIER 2: Early unlocks - ~3s cooldown
    'poison_cloud': {
        'name': 'Poison Cloud',
        'mana_cost': 12,
        'damage': 15,  # Per second
        'duration': 4.0,
        'range': 5.0,
        'area_radius': 2.5,
        'cooldown': 4.0,
        'level_req': 2,
        'color': (100, 180, 50),
        'description': 'Poison cloud deals damage over time.',
    },
    'entangle': {
        'name': 'Entangle',
        'mana_cost': 10,
        'duration': 3.0,
        'range': 5.0,
        'area_radius': 2.0,
        'cooldown': 3.0,
        'level_req': 2,
        'color': (80, 150, 50),
        'description': 'Roots enemies in place.',
    },
    'revive': {
        'name': 'Revive',
        'mana_cost': 20,
        'heal_amount': 50,  # % of max health
        'range': 3.0,
        'cooldown': 5.0,
        'level_req': 3,
        'color': (255, 255, 150),
        'description': 'Revives a downed ally.',
        'revives': True,
    },
    
    # TIER 3: Mid-game - ~10s cooldown
    'group_heal': {
        'name': 'Group Heal',
        'mana_cost': 25,
        'heal_amount': 60,
        'range': 0,
        'area_radius': 6.0,
        'cooldown': 10.0,
        'level_req': 5,
        'color': (150, 255, 150),
        'description': 'Powerful heal for entire party.',
        'heals_party': True,
    },
    'regeneration': {
        'name': 'Regeneration',
        'mana_cost': 20,
        'heal_amount': 10,  # Per second
        'duration': 15.0,
        'range': 0,
        'area_radius': 5.0,
        'cooldown': 12.0,
        'level_req': 6,
        'color': (100, 200, 100),
        'description': 'Party regenerates health over time.',
        'heals_party': True,
    },
    
    # TIER 4: Late-game - ~30s cooldown
    'summon_wolf': {
        'name': 'Summon Wolf',
        'mana_cost': 40,
        'duration': 60.0,
        'cooldown': 30.0,
        'level_req': 8,
        'color': (150, 140, 120),
        'description': 'Summons a powerful wolf ally.',
    },
    'sanctuary': {
        'name': 'Sanctuary',
        'mana_cost': 60,
        'heal_amount': 100,
        'range': 0,
        'area_radius': 8.0,
        'cooldown': 45.0,
        'level_req': 12,
        'color': (255, 255, 200),
        'description': 'Massive heal and cleanse for entire party.',
        'heals_party': True,
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
    spell.heals_party = data.get('heals_party', False)
    spell.revives = data.get('revives', False)
    
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
        
        # Handle revive spell
        if spell.revives:
            # Find downed ally near target
            for char in world.characters:
                if hasattr(char, 'is_downed') and char.is_downed:
                    if char.distance_to(target_pos) <= spell.range:
                        char.revive(spell.heal_amount)
                        return spell
            return spell  # No downed ally found, spell still consumed
        
        # Find targets
        targets = []
        if spell.heals_party:
            # Party heal - heal caster and all nearby allies
            targets = [caster]  # Always include caster
            for char in world.characters:
                if char != caster and not getattr(char, 'is_downed', False):
                    if char.distance_to(caster) <= spell.area_radius:
                        targets.append(char)
        elif spell.area_radius > 0:
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
            # Single target - for damage spells, only target enemies
            enemies_only = spell.damage > 0
            entity = world.get_entity_at(target_pos[0], target_pos[1], radius=1.0, enemies_only=enemies_only)
            if entity:
                targets = [entity]
        
        # Only TRUE projectiles delay damage (fireball, ice_shard travel to target)
        # Lightning/meteor are instant or have special handling
        is_projectile = spell_id in ('fireball', 'ice_shard')
        
        # Apply immediate effects (non-projectile spells)
        for target in targets:
            if spell.damage > 0 and hasattr(target, 'take_damage') and not is_projectile:
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

