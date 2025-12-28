"""Animation processor - updates animation states and frames."""

import esper

from ..components import (
    Position, Velocity, Animation, AnimationState, Facing, Direction,
    Downed, Dead, InCombat, Casting, AttackIntent, ActiveAbility, LeapingAbility
)
from ..components.rendering import DamageNumber, VisualEffect
from ..components.tags import ToRemove


class AnimationProcessor(esper.Processor):
    """Updates animation states and frame counters."""
    
    # Frame counts per animation
    FRAME_COUNTS = {
        AnimationState.IDLE: 4,
        AnimationState.WALK: 8,
        AnimationState.ATTACK: 6,
        AnimationState.CAST: 6,
        AnimationState.DEATH: 1,  # Single defeated frame
        AnimationState.DOWNED: 1,
        # Hero special abilities
        AnimationState.SPIN: 24,  # 3 full rotations (8 frames each)
        AnimationState.LEAP: 10,  # Epic jump arc with impact
        AnimationState.HEAVY: 10, # Wind-up and slam
        AnimationState.BASH: 8,   # Shield bash lunge and strike
        # Mage channeling  
        AnimationState.CHANNEL: 4,  # Looping channel
    }
    
    def process(self, dt: float):
        """Update animations each frame."""
        from ...core.perf_monitor import perf
        perf.mark("AnimationProcessor")
        
        self._update_animation_states(dt)
        self._update_damage_numbers(dt)
        self._update_visual_effects(dt)
        
        perf.measure("AnimationProcessor")
    
    def _update_animation_states(self, dt: float):
        """Update animation states based on entity state."""
        for ent, (anim,) in esper.get_components(Animation):
            # Determine target state
            target_state = self._get_target_state(ent)
            
            # Check if we should transition
            should_transition = False
            
            if anim.state != target_state:
                # Some animations should complete before transitioning
                if anim.state in (AnimationState.ATTACK, AnimationState.CAST, 
                                  AnimationState.SPIN, AnimationState.LEAP, 
                                  AnimationState.HEAVY, AnimationState.BASH,
                                  AnimationState.CHANNEL):
                    # For SPIN, check if ActiveAbility is still going
                    if anim.state == AnimationState.SPIN and esper.has_component(ent, ActiveAbility):
                        # Keep spinning while ability is active - loop the animation
                        pass  # Don't transition
                    # For LEAP, check if LeapingAbility is still going
                    elif anim.state == AnimationState.LEAP and esper.has_component(ent, LeapingAbility):
                        # Keep leap animation while in the air
                        pass  # Don't transition
                    else:
                        # Check if animation finished
                        frames = self.FRAME_COUNTS.get(anim.state, 4)
                        if anim.frame >= frames - 1:
                            should_transition = True
                elif anim.state == AnimationState.DEATH:
                    # Death stays forever
                    pass
                else:
                    should_transition = True
            
            if should_transition:
                anim.state = target_state
                anim.frame = 0
                anim.timer = 0.0
            
            # Update frame timer
            anim.timer += dt
            
            if anim.timer >= anim.frame_duration:
                anim.timer -= anim.frame_duration
                
                frames = self.FRAME_COUNTS.get(anim.state, 4)
                
                if anim.state in (AnimationState.DEATH, AnimationState.DOWNED):
                    # Don't loop
                    anim.frame = min(anim.frame + 1, frames - 1)
                else:
                    anim.frame = (anim.frame + 1) % frames
    
    def _get_target_state(self, ent: int) -> AnimationState:
        """Determine what animation state an entity should be in."""
        # Dead entities stay in death animation
        if esper.has_component(ent, Dead):
            return AnimationState.DEATH
        
        # Downed allies
        if esper.has_component(ent, Downed):
            return AnimationState.DOWNED
        
        # Check if casting
        if esper.has_component(ent, Casting):
            return AnimationState.CAST
        
        # Check if attacking (has attack intent)
        if esper.has_component(ent, AttackIntent):
            return AnimationState.ATTACK
        
        # Check if moving
        if esper.has_component(ent, Velocity):
            vel = esper.component_for_entity(ent, Velocity)
            if abs(vel.dx) > 0.1 or abs(vel.dy) > 0.1:
                return AnimationState.WALK
        
        return AnimationState.IDLE
    
    def _update_damage_numbers(self, dt: float):
        """Update floating damage numbers."""
        for ent, (pos, dmg) in esper.get_components(Position, DamageNumber):
            dmg.timer -= dt
            
            # Move up
            pos.y -= dmg.rise_speed * dt * 0.01
            
            if dmg.timer <= 0:
                esper.add_component(ent, ToRemove())
    
    def _update_visual_effects(self, dt: float):
        """Update visual effects."""
        for ent, (effect,) in esper.get_components(VisualEffect):
            effect.timer -= dt
            
            if effect.timer <= 0:
                esper.add_component(ent, ToRemove())
