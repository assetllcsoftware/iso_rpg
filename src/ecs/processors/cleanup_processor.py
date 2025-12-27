"""Cleanup processor - removes entities marked for deletion."""

import esper

from ..components.tags import ToRemove, Enemy
from ..components.health import Dead


# Time to wait before removing dead enemy corpses (seconds)
CORPSE_DESPAWN_TIME = 15.0


class CleanupProcessor(esper.Processor):
    """Removes entities marked with ToRemove component.
    
    Also handles corpse cleanup after death animations.
    Should run LAST in the processor order.
    """
    
    def process(self, dt: float):
        """Remove all entities marked for removal."""
        to_delete = []
        
        # Remove entities explicitly marked for removal
        for ent, (remove,) in esper.get_components(ToRemove):
            to_delete.append(ent)
        
        # Update dead enemy timers and remove after delay
        for ent, (dead, enemy) in esper.get_components(Dead, Enemy):
            dead.timer += dt
            if dead.timer >= CORPSE_DESPAWN_TIME:
                to_delete.append(ent)
        
        for ent in to_delete:
            if esper.entity_exists(ent):
                esper.delete_entity(ent)
