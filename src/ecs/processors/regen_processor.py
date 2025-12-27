"""Regeneration processor - handles health and mana regen."""

import esper

from ..components import Health, Mana, Regeneration, Downed, Dead, PartyMember
from ...core.events import EventBus, Event, EventType


class RegenProcessor(esper.Processor):
    """Processes health and mana regeneration.
    
    - Mana regenerates constantly (default 2/sec)
    - Health regenerates only out of combat (default 0)
    - Downed/dead entities don't regenerate
    """
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.combat_cooldown: float = 0.0  # Time since last combat action
    
    def process(self, dt: float):
        """Process regeneration each frame."""
        # Check if any party member is in combat
        in_combat = self._check_combat_status()
        
        for ent, regen in esper.get_component(Regeneration):
            # Skip dead/downed
            if esper.has_component(ent, Dead) or esper.has_component(ent, Downed):
                continue
            
            # Mana regeneration (always, but slower in combat)
            if esper.has_component(ent, Mana):
                mana = esper.component_for_entity(ent, Mana)
                if mana.current < mana.maximum:
                    regen_rate = regen.mana_per_second
                    if in_combat:
                        regen_rate *= 0.5  # Half regen in combat
                    
                    mana.current = min(
                        mana.maximum,
                        mana.current + regen_rate * dt
                    )
            
            # Health regeneration (only out of combat)
            if not in_combat and esper.has_component(ent, Health):
                health = esper.component_for_entity(ent, Health)
                if health.current < health.maximum and regen.health_per_second > 0:
                    health.current = min(
                        health.maximum,
                        health.current + regen.health_per_second * dt
                    )
    
    def _check_combat_status(self) -> bool:
        """Check if party is in combat (enemies nearby with aggro)."""
        from ..components import AIController, Enemy, Position
        from ...core.constants import AIState
        
        # Check if any enemy is in CHASE or ATTACK state
        for ent, (ai, _) in esper.get_components(AIController, Enemy):
            if esper.has_component(ent, Dead):
                continue
            if ai.state in (AIState.CHASE, AIState.ATTACK, AIState.ENGAGE):
                return True
        
        return False

