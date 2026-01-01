"""Town scene - uses SAME systems as dungeon, just no combat."""

import pygame
import esper
from typing import Optional, List

from ..core.constants import COLOR_TEXT, COLOR_TEXT_DIM, COLOR_GOLD
from ..core.events import EventBus, Event, EventType
from ..core.formulas import distance
from ..ecs.components import (
    PartyMember, Health, Mana, Gold, Position, Facing, Direction,
    Sprite, Animation, AnimationState, RenderOffset, Enemy, CharacterName
)
from ..world.town_map import TownMap
from ..ui.shop import ShopUI


# NPC definitions
TOWN_NPCS = [
    {'name': 'Blacksmith', 'type': 'blacksmith', 'x': 10, 'y': 14, 'sprite': 'orc'},
    {'name': 'Alchemist', 'type': 'alchemist', 'x': 29, 'y': 14, 'sprite': 'mage'},
    {'name': 'Innkeeper', 'type': 'inn', 'x': 11, 'y': 26, 'sprite': 'hero'},
]


class TownScene:
    """Town - same movement as dungeon, NPCs to talk to with SPACE."""
    
    def __init__(self, screen: pygame.Surface, event_bus: EventBus):
        self.screen = screen
        self.event_bus = event_bus
        self.active = False
        self.dungeon_level = 1
        
        pygame.font.init()
        self.font = pygame.font.Font(None, 32)
        self.font_small = pygame.font.Font(None, 24)
        
        # Town map (same interface as Dungeon)
        self.town_map = TownMap(40, 35)
        
        # Shop UI
        self.shop_ui = ShopUI(screen, event_bus)
        
        # Saved positions
        self.saved_party_positions = {}
        self.saved_enemy_positions = {}
        
        # NPCs
        self.npc_entities: List[tuple] = []
        self.nearby_npc = None
        self.nearby_npc_type = None
    
    def show(self, dungeon_level: int = 1):
        """Enter town."""
        self.active = True
        self.dungeon_level = dungeon_level
        self.shop_ui.hide()
        
        # Save dungeon state
        self._save_positions()
        
        # Move party to town
        self._place_party()
        
        # Create NPCs
        self._create_npcs()
        
        # Heal
        for ent, (_, health) in esper.get_components(PartyMember, Health):
            health.current = health.maximum
            if esper.has_component(ent, Mana):
                mana = esper.component_for_entity(ent, Mana)
                mana.current = mana.maximum
        
        self.event_bus.emit(Event(EventType.NOTIFICATION, {
            "text": "Welcome to Town! Party healed.",
            "color": (100, 255, 150)
        }))
    
    def hide(self):
        """Leave town."""
        self.active = False
        self.shop_ui.hide()
        self._remove_npcs()
        self._restore_positions()
    
    def _save_positions(self):
        """Save party/enemy positions, hide enemies."""
        self.saved_party_positions = {}
        self.saved_enemy_positions = {}
        
        for ent, (_, pos) in esper.get_components(PartyMember, Position):
            self.saved_party_positions[ent] = (pos.x, pos.y)
        
        for ent, (_, pos) in esper.get_components(Enemy, Position):
            self.saved_enemy_positions[ent] = (pos.x, pos.y)
            pos.x, pos.y = -1000, -1000
    
    def _restore_positions(self):
        """Restore positions."""
        for ent, (x, y) in self.saved_party_positions.items():
            if esper.entity_exists(ent) and esper.has_component(ent, Position):
                pos = esper.component_for_entity(ent, Position)
                pos.x, pos.y = x, y
        
        for ent, (x, y) in self.saved_enemy_positions.items():
            if esper.entity_exists(ent) and esper.has_component(ent, Position):
                pos = esper.component_for_entity(ent, Position)
                pos.x, pos.y = x, y
    
    def _place_party(self):
        """Place party at town spawn."""
        sx, sy = self.town_map.spawn_point
        for ent, (member, pos) in esper.get_components(PartyMember, Position):
            pos.x = sx + (member.party_index % 3 - 1) * 1.2
            pos.y = sy + (member.party_index // 3) * 1.2
    
    def _create_npcs(self):
        """Create NPC entities."""
        self.npc_entities = []
        for npc in TOWN_NPCS:
            ent = esper.create_entity(
                Position(x=float(npc['x']), y=float(npc['y'])),
                Sprite(sprite_set=npc['sprite']),
                Animation(state=AnimationState.IDLE, frame=0, timer=0),
                Facing(direction=Direction.DOWN),
                RenderOffset(y=-16),
                CharacterName(name=npc['name']),
            )
            self.npc_entities.append((ent, npc['type'], npc['name']))
    
    def _remove_npcs(self):
        """Remove NPCs."""
        for ent, _, _ in self.npc_entities:
            if esper.entity_exists(ent):
                esper.delete_entity(ent)
        self.npc_entities = []
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle town-specific input (SPACE to talk, ESC to leave)."""
        if not self.active:
            return False
        
        if self.shop_ui.visible:
            return self.shop_ui.handle_event(event)
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._leave_town()
                return True
            elif event.key == pygame.K_SPACE:
                if self.nearby_npc_type:
                    self._interact(self.nearby_npc_type)
                return True
        
        # Let other input (movement) pass through to InputProcessor
        return False
    
    def _interact(self, npc_type: str):
        """Interact with NPC."""
        if npc_type == 'blacksmith':
            self.shop_ui.show('blacksmith', self.dungeon_level)
        elif npc_type == 'alchemist':
            self.shop_ui.show('alchemist', self.dungeon_level)
        elif npc_type == 'inn':
            for ent, (_, health) in esper.get_components(PartyMember, Health):
                health.current = health.maximum
                if esper.has_component(ent, Mana):
                    mana = esper.component_for_entity(ent, Mana)
                    mana.current = mana.maximum
            self.event_bus.emit(Event(EventType.NOTIFICATION, {
                "text": "Party rested!",
                "color": (100, 255, 150)
            }))
        elif npc_type == 'portal':
            self._leave_town()
    
    def _leave_town(self):
        """Leave town."""
        self.event_bus.emit(Event(EventType.TOWN_LEFT, {"target_level": self.dungeon_level}))
    
    def update(self, dt: float):
        """Check for nearby NPCs."""
        if not self.active:
            return
        
        # Find leader
        leader_pos = None
        for ent, (member, pos) in esper.get_components(PartyMember, Position):
            if member.party_index == 0:
                leader_pos = pos
                break
        
        self.nearby_npc = None
        self.nearby_npc_type = None
        
        if leader_pos:
            # Check NPCs
            for ent, npc_type, npc_name in self.npc_entities:
                if esper.entity_exists(ent) and esper.has_component(ent, Position):
                    npc_pos = esper.component_for_entity(ent, Position)
                    if distance(leader_pos.x, leader_pos.y, npc_pos.x, npc_pos.y) < 2.5:
                        self.nearby_npc = npc_name
                        self.nearby_npc_type = npc_type
                        break
            
            # Check portal
            building = self.town_map.get_building_at(leader_pos.x, leader_pos.y)
            if building and building.building_type == 'portal':
                self.nearby_npc = "Portal"
                self.nearby_npc_type = "portal"
    
    def render(self, renderer, camera):
        """Render town using game's renderer/camera."""
        if not self.active:
            return
        
        # Render map and entities (same as dungeon)
        renderer.render(self.town_map)
        
        # NPC labels
        for ent, _, npc_name in self.npc_entities:
            if esper.entity_exists(ent) and esper.has_component(ent, Position):
                pos = esper.component_for_entity(ent, Position)
                sx, sy = camera.world_to_screen(pos.x, pos.y - 1.5)
                text = self.font_small.render(npc_name, True, COLOR_TEXT)
                pygame.draw.rect(self.screen, (30, 30, 40),
                               (sx - text.get_width()//2 - 4, sy - 2, 
                                text.get_width() + 8, text.get_height() + 4),
                               border_radius=3)
                self.screen.blit(text, (sx - text.get_width()//2, sy))
        
        # Gold
        gold = 0
        for ent, (member, g) in esper.get_components(PartyMember, Gold):
            if member.party_index == 0:
                gold = g.amount
                break
        gold_text = self.font.render(f"Gold: {gold}", True, COLOR_GOLD)
        pygame.draw.rect(self.screen, (30, 30, 40), (10, 10, gold_text.get_width() + 20, 35), border_radius=5)
        self.screen.blit(gold_text, (20, 17))
        
        # Prompt
        screen_w, screen_h = self.screen.get_size()
        if self.nearby_npc:
            text = f"SPACE: {'Leave' if self.nearby_npc_type == 'portal' else 'Talk to ' + self.nearby_npc}"
            prompt = self.font.render(text, True, COLOR_TEXT)
            bx = screen_w//2 - prompt.get_width()//2 - 15
            pygame.draw.rect(self.screen, (40, 60, 80), (bx, screen_h - 80, prompt.get_width() + 30, 40), border_radius=8)
            self.screen.blit(prompt, (bx + 15, screen_h - 72))
        
        # Controls hint
        hint = self.font_small.render("Right-click: Move | SPACE: Talk | ESC: Leave", True, COLOR_TEXT_DIM)
        self.screen.blit(hint, (screen_w//2 - hint.get_width()//2, screen_h - 30))
        
        # Shop
        self.shop_ui.render()
