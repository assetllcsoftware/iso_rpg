"""AI processor - handles enemy and ally AI decisions.

Simplified AI:
- Enemies: chase, attack, return to home
- Allies: follow leader, attack nearby enemies
"""

import esper
from typing import Optional, Tuple

from ..components import (
    Position, Velocity, Speed, MoveIntent, Path,
    Health, Mana, CombatStats, CombatTarget, AttackIntent,
    AIController, EnemyAI, AllyAI, AggroRange, LeashRange,
    PartyMember, Enemy, Ally, PlayerControlled, Selected, Downed, Dead,
    SpellBook, Casting, CastIntent, GlobalCooldown
)
from ...core.events import EventBus, Event, EventType
from ...core.constants import AIState
from ...core.formulas import distance


# Constants
ALLY_FOLLOW_DISTANCE = 2.0   # Start following if farther than this
ALLY_STOP_DISTANCE = 1.0     # Stop when this close to leader
ALLY_ENGAGE_RANGE = 6.0      # Attack enemies within this range
ENEMY_AGGRO_RANGE = 6.0      # Default enemy aggro range
ENEMY_LEASH_RANGE = 12.0     # Default leash range

# Ally autocast is 3x slower than player casting
ALLY_SPELL_COOLDOWN_MULT = 3.0
ALLY_HEAL_THRESHOLD = 0.5    # Heal allies below 50% health


class AIProcessor(esper.Processor):
    """Processes AI decisions for enemies and allies."""
    
    def __init__(self, event_bus: EventBus, pathfinder=None, dungeon=None):
        self.event_bus = event_bus
        self.pathfinder = pathfinder
        self.dungeon = dungeon
    
    def set_pathfinder(self, pathfinder):
        self.pathfinder = pathfinder
    
    def set_dungeon(self, dungeon):
        self.dungeon = dungeon
    
    def process(self, dt: float):
        """Process AI decisions each frame."""
        from ...core.perf_monitor import perf
        perf.mark("AIProcessor")
        
        self._process_enemy_ai(dt)
        self._process_ally_ai(dt)
        
        perf.measure("AIProcessor")
    
    # =========================================================================
    # ENEMY AI
    # =========================================================================
    
    def _process_enemy_ai(self, dt: float):
        """Simple enemy AI: idle -> chase -> attack -> return."""
        for ent, (pos, ai, enemy_ai) in esper.get_components(
            Position, AIController, EnemyAI
        ):
            if esper.has_component(ent, Dead):
                continue
            
            # Throttle decisions
            ai.decision_timer -= dt
            if ai.decision_timer > 0:
                continue
            ai.decision_timer = 0.2
            
            # Get ranges
            aggro = ENEMY_AGGRO_RANGE
            leash = ENEMY_LEASH_RANGE
            if esper.has_component(ent, AggroRange):
                aggro = esper.component_for_entity(ent, AggroRange).range
            if esper.has_component(ent, LeashRange):
                leash = esper.component_for_entity(ent, LeashRange).range
            
            # Find nearest player
            target, target_dist = self._find_nearest_player(pos)
            
            # Check leash
            home_dist = distance(pos.x, pos.y, ai.home_x, ai.home_y)
            if home_dist > leash:
                ai.state = AIState.RETURN
                ai.target_id = -1
            
            # State machine
            if ai.state == AIState.IDLE or ai.state == AIState.PATROL:
                if target and target_dist <= aggro:
                    ai.state = AIState.CHASE
                    ai.target_id = target
                else:
                    self._stop_moving(ent)
            
            elif ai.state == AIState.CHASE:
                if not self._is_valid_target(ai.target_id):
                    ai.state = AIState.RETURN
                    continue
                
                target_pos = esper.component_for_entity(ai.target_id, Position)
                attack_range = self._get_attack_range(ent)
                
                # Only transition to ATTACK if we have line of sight
                has_los = True
                if self.dungeon:
                    has_los = self.dungeon.has_line_of_sight(
                        pos.x, pos.y, target_pos.x, target_pos.y
                    )
                
                if target_dist <= attack_range and has_los:
                    ai.state = AIState.ATTACK
                else:
                    # Chase - pathfinder will find way around walls
                    self._move_toward_entity(ent, pos, ai.target_id)
            
            elif ai.state == AIState.ATTACK:
                if not self._is_valid_target(ai.target_id):
                    ai.state = AIState.RETURN
                    continue
                
                target_pos = esper.component_for_entity(ai.target_id, Position)
                
                # Check line of sight - can't attack through walls
                if self.dungeon and not self.dungeon.has_line_of_sight(
                    pos.x, pos.y, target_pos.x, target_pos.y
                ):
                    # Lost sight - try to chase around obstacles
                    ai.state = AIState.CHASE
                    continue
                
                attack_range = self._get_attack_range(ent)
                dist = distance(pos.x, pos.y, target_pos.x, target_pos.y)
                
                if dist > attack_range * 1.2:
                    ai.state = AIState.CHASE
                else:
                    self._set_attack_intent(ent, ai.target_id)
                    self._stop_moving(ent)
            
            elif ai.state == AIState.RETURN:
                home_dist = distance(pos.x, pos.y, ai.home_x, ai.home_y)
                if home_dist < 1.0:
                    ai.state = AIState.IDLE
                    self._stop_moving(ent)
                else:
                    self._move_toward_point(ent, pos, ai.home_x, ai.home_y)
            
            elif ai.state == AIState.FLEE:
                if ai.target_id >= 0 and esper.entity_exists(ai.target_id):
                    target_pos = esper.component_for_entity(ai.target_id, Position)
                    self._move_away_from(ent, pos, target_pos.x, target_pos.y)
    
    # =========================================================================
    # ALLY AI - Simple follow and assist
    # =========================================================================
    
    def _process_ally_ai(self, dt: float):
        """Simple ally AI: follow leader, attack enemies in range."""
        # First, find the currently selected/controlled party member (leader)
        leader_id = -1
        leader_pos = None
        
        for ent, (pctrl, sel, pos) in esper.get_components(
            PlayerControlled, Selected, Position
        ):
            leader_id = ent
            leader_pos = pos
            break
        
        # If no selected leader, find any player-controlled entity
        if leader_id < 0:
            for ent, (pctrl, pos) in esper.get_components(PlayerControlled, Position):
                if not esper.has_component(ent, Downed) and not esper.has_component(ent, Dead):
                    leader_id = ent
                    leader_pos = pos
                    break
        
        if leader_id < 0 or leader_pos is None:
            return
        
        # Process each ally
        for ent, (pos, ai, ally_ai) in esper.get_components(
            Position, AIController, AllyAI
        ):
            # Skip if this IS the leader
            if ent == leader_id:
                continue
            
            # Skip downed/dead
            if esper.has_component(ent, Downed) or esper.has_component(ent, Dead):
                self._stop_moving(ent)
                continue
            
            # Throttle decisions
            ai.decision_timer -= dt
            if ai.decision_timer > 0:
                continue
            ai.decision_timer = 0.1  # Fast updates for responsive following
            
            # Calculate distance to leader
            leader_dist = distance(pos.x, pos.y, leader_pos.x, leader_pos.y)
            
            # Check for nearby enemies
            nearest_enemy, enemy_dist = self._find_nearest_enemy(pos)
            
            # Try to autocast spells (3x slower than player)
            self._try_ally_autocast(ent, pos, ally_ai, nearest_enemy, enemy_dist, dt)
            
            # State: ENGAGE if enemy nearby
            if nearest_enemy and enemy_dist <= ALLY_ENGAGE_RANGE:
                attack_range = self._get_attack_range(ent)
                
                # Get enemy position for LOS check
                enemy_pos = esper.component_for_entity(nearest_enemy, Position)
                has_los = True
                if self.dungeon:
                    has_los = self.dungeon.has_line_of_sight(
                        pos.x, pos.y, enemy_pos.x, enemy_pos.y
                    )
                
                if enemy_dist <= attack_range and has_los:
                    # In range AND has LOS - attack!
                    self._set_attack_intent(ent, nearest_enemy)
                    self._stop_moving(ent)
                    ai.state = AIState.ENGAGE
                    ai.target_id = nearest_enemy
                elif has_los:
                    # Has LOS but out of range - move toward enemy
                    self._move_toward_entity(ent, pos, nearest_enemy)
                    ai.state = AIState.ENGAGE
                    ai.target_id = nearest_enemy
                else:
                    # No LOS - don't engage, follow leader instead
                    pass
                continue
            
            # State: FOLLOW leader
            ai.state = AIState.FOLLOW
            ai.target_id = leader_id
            
            if leader_dist > ALLY_FOLLOW_DISTANCE:
                # Follow the leader
                self._move_toward_entity(ent, pos, leader_id)
            elif leader_dist < ALLY_STOP_DISTANCE:
                # Close enough, stop
                self._stop_moving(ent)
            else:
                # In the sweet spot, slow follow
                self._move_toward_entity(ent, pos, leader_id, speed_mult=0.5)
    
    # =========================================================================
    # ALLY SPELLCASTING (3x slower than player)
    # =========================================================================
    
    def _try_ally_autocast(self, ent: int, pos: Position, ally_ai: AllyAI, 
                           nearest_enemy: Optional[int], enemy_dist: float, dt: float):
        """Try to autocast spells for ally AI at reduced speed."""
        # Skip if already casting
        if esper.has_component(ent, Casting):
            return
        
        # Skip if player already queued a spell (don't override player input!)
        if esper.has_component(ent, CastIntent):
            return
        
        # Skip if on global cooldown
        if esper.has_component(ent, GlobalCooldown):
            gcd = esper.component_for_entity(ent, GlobalCooldown)
            if not gcd.ready:
                return
        
        # Need a spellbook
        if not esper.has_component(ent, SpellBook):
            return
        
        spellbook = esper.component_for_entity(ent, SpellBook)
        if not spellbook.known_spells:
            return
        
        # Need mana
        if not esper.has_component(ent, Mana):
            return
        mana = esper.component_for_entity(ent, Mana)
        
        # Update spell cooldown timers
        for spell_id in list(ally_ai.spell_ready_timers.keys()):
            ally_ai.spell_ready_timers[spell_id] -= dt
            if ally_ai.spell_ready_timers[spell_id] <= 0:
                del ally_ai.spell_ready_timers[spell_id]
        
        # Load spell data
        from ...data.loader import data_loader
        
        # Priority 1: Heal low-health allies
        heal_spell = self._find_heal_spell(spellbook, ally_ai, mana, data_loader)
        if heal_spell:
            heal_target = self._find_ally_needing_heal(pos)
            if heal_target:
                self._cast_ally_spell(ent, heal_spell, heal_target, ally_ai, data_loader)
                return
        
        # Priority 2: Attack enemies
        if nearest_enemy and enemy_dist <= ALLY_ENGAGE_RANGE:
            attack_spell = self._find_attack_spell(spellbook, ally_ai, mana, data_loader)
            if attack_spell:
                self._cast_ally_spell(ent, attack_spell, nearest_enemy, ally_ai, data_loader)
                return
    
    def _find_heal_spell(self, spellbook, ally_ai: AllyAI, mana, data_loader) -> Optional[str]:
        """Find an available heal spell."""
        for spell_id in spellbook.known_spells:
            # Check cooldown
            if spell_id in ally_ai.spell_ready_timers:
                continue
            
            spell_data = data_loader.get_spell(spell_id)
            if not spell_data:
                continue
            
            # Is it a heal?
            if spell_data.get('effect') != 'heal' and 'heal' not in spell_id:
                continue
            
            # Have enough mana?
            mana_cost = spell_data.get('mana_cost', 0)
            if mana.current < mana_cost:
                continue
            
            return spell_id
        return None
    
    def _find_attack_spell(self, spellbook, ally_ai: AllyAI, mana, data_loader) -> Optional[str]:
        """Find an available attack spell."""
        for spell_id in spellbook.known_spells:
            # Check cooldown
            if spell_id in ally_ai.spell_ready_timers:
                continue
            
            spell_data = data_loader.get_spell(spell_id)
            if not spell_data:
                continue
            
            # Skip heals
            if spell_data.get('effect') == 'heal' or 'heal' in spell_id:
                continue
            
            # Have enough mana?
            mana_cost = spell_data.get('mana_cost', 0)
            if mana.current < mana_cost:
                continue
            
            return spell_id
        return None
    
    def _find_ally_needing_heal(self, pos: Position) -> Optional[int]:
        """Find an ally that needs healing."""
        for ent, (ally_pos, _, health) in esper.get_components(Position, PartyMember, Health):
            if esper.has_component(ent, Dead):
                continue
            
            # Check if low health
            if health.current / health.maximum < ALLY_HEAL_THRESHOLD:
                # Check distance
                dist = distance(pos.x, pos.y, ally_pos.x, ally_pos.y)
                if dist <= 8.0:  # Heal range
                    return ent
        return None
    
    def _cast_ally_spell(self, caster: int, spell_id: str, target: int, 
                         ally_ai: AllyAI, data_loader):
        """Cast a spell and set the 3x slower cooldown."""
        spell_data = data_loader.get_spell(spell_id)
        if not spell_data:
            return
        
        # Get target position
        if not esper.has_component(target, Position):
            return
        target_pos = esper.component_for_entity(target, Position)
        
        # Emit spell cast event
        self.event_bus.emit(Event(EventType.SPELL_CAST_REQUESTED, {
            "caster": caster,
            "spell_id": spell_id,
            "target_id": target,
            "target_x": target_pos.x,
            "target_y": target_pos.y
        }))
        
        # Set 3x cooldown for AI
        base_cooldown = spell_data.get('cooldown', 2.0)
        ally_ai.spell_ready_timers[spell_id] = base_cooldown * ALLY_SPELL_COOLDOWN_MULT
    
    # =========================================================================
    # HELPER METHODS
    # =========================================================================
    
    def _find_nearest_player(self, pos: Position) -> Tuple[Optional[int], float]:
        """Find nearest living party member with line of sight."""
        nearest = None
        nearest_dist = float('inf')
        
        for ent, (member_pos, _) in esper.get_components(Position, PartyMember):
            if esper.has_component(ent, Downed) or esper.has_component(ent, Dead):
                continue
            
            # Check line of sight - can't target through walls
            if self.dungeon:
                if not self.dungeon.has_line_of_sight(
                    int(pos.x), int(pos.y),
                    int(member_pos.x), int(member_pos.y)
                ):
                    continue
            
            dist = distance(pos.x, pos.y, member_pos.x, member_pos.y)
            if dist < nearest_dist:
                nearest_dist = dist
                nearest = ent
        
        return nearest, nearest_dist
    
    def _find_nearest_enemy(self, pos: Position) -> Tuple[Optional[int], float]:
        """Find nearest living enemy."""
        nearest = None
        nearest_dist = float('inf')
        
        for ent, (enemy_pos, _) in esper.get_components(Position, Enemy):
            if esper.has_component(ent, Dead):
                continue
            
            # Check line of sight if we have a dungeon
            if self.dungeon:
                if not self.dungeon.has_line_of_sight(
                    int(pos.x), int(pos.y),
                    int(enemy_pos.x), int(enemy_pos.y)
                ):
                    continue
            
            dist = distance(pos.x, pos.y, enemy_pos.x, enemy_pos.y)
            if dist < nearest_dist:
                nearest_dist = dist
                nearest = ent
        
        return nearest, nearest_dist
    
    def _is_valid_target(self, target_id: int) -> bool:
        """Check if target is valid (exists and not dead/downed)."""
        if target_id < 0:
            return False
        if not esper.entity_exists(target_id):
            return False
        if esper.has_component(target_id, Dead):
            return False
        if esper.has_component(target_id, Downed):
            return False
        return True
    
    def _get_attack_range(self, ent: int) -> float:
        """Get entity's attack range."""
        if esper.has_component(ent, CombatStats):
            return esper.component_for_entity(ent, CombatStats).attack_range
        return 1.5
    
    def _move_toward_entity(self, ent: int, pos: Position, target_id: int, speed_mult: float = 1.0):
        """Set movement intent toward another entity."""
        if not esper.entity_exists(target_id):
            return
        if not esper.has_component(target_id, Position):
            return
        
        target_pos = esper.component_for_entity(target_id, Position)
        self._move_toward_point(ent, pos, target_pos.x, target_pos.y, speed_mult)
    
    def _move_toward_point(self, ent: int, pos: Position, tx: float, ty: float, speed_mult: float = 1.0):
        """Set movement intent toward a point."""
        dx = tx - pos.x
        dy = ty - pos.y
        dist = max(0.01, distance(pos.x, pos.y, tx, ty))
        
        # Normalize
        dx /= dist
        dy /= dist
        
        # Apply speed multiplier
        dx *= speed_mult
        dy *= speed_mult
        
        if esper.has_component(ent, MoveIntent):
            intent = esper.component_for_entity(ent, MoveIntent)
            intent.dx = dx
            intent.dy = dy
        else:
            esper.add_component(ent, MoveIntent(dx=dx, dy=dy))
    
    def _move_away_from(self, ent: int, pos: Position, tx: float, ty: float):
        """Set movement intent away from a point."""
        dx = pos.x - tx
        dy = pos.y - ty
        dist = max(0.01, distance(pos.x, pos.y, tx, ty))
        
        if esper.has_component(ent, MoveIntent):
            intent = esper.component_for_entity(ent, MoveIntent)
            intent.dx = dx / dist
            intent.dy = dy / dist
    
    def _stop_moving(self, ent: int):
        """Stop entity movement."""
        if esper.has_component(ent, MoveIntent):
            intent = esper.component_for_entity(ent, MoveIntent)
            intent.dx = 0
            intent.dy = 0
    
    def _set_attack_intent(self, ent: int, target_id: int):
        """Set attack intent on target."""
        if esper.has_component(ent, AttackIntent):
            intent = esper.component_for_entity(ent, AttackIntent)
            intent.target_id = target_id
        else:
            esper.add_component(ent, AttackIntent(target_id=target_id))
