"""Main game class - orchestrates the game loop and systems."""

import pygame
import time
import esper

from .core.constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS, FIXED_TIMESTEP, GameState
)
from .core.events import EventBus, Event, EventType

from .ecs.processors import (
    InputProcessor, MovementProcessor, CombatProcessor,
    AIProcessor, MagicProcessor, AnimationProcessor,
    ProgressionProcessor, LootProcessor, CleanupProcessor,
    SaveLoadProcessor, WorldProcessor, DroppedItemProcessor
)
from .ecs.factories import create_party, create_enemies_for_level
from .ecs.components import PartyMember

from .world import Dungeon, Pathfinder
from .rendering import Camera, Renderer
from .ui import (
    HUD, InventoryUI, SkillTreeUI, ActionBar, Minimap,
    NotificationManager, PauseOverlay, GameOverOverlay
)
from .scenes import TownScene
from .audio import AudioManager


class Game:
    """Main game class - ties everything together."""
    
    def __init__(self):
        # Initialize display
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("ML Siege")
        
        self.clock = pygame.time.Clock()
        self.running = True
        self.state = GameState.PLAYING
        
        # Fixed timestep variables
        self.accumulator = 0.0
        self.previous_time = time.time()
        
        # Core systems
        self.event_bus = EventBus()
        
        # World
        self.dungeon = Dungeon(80, 80)
        self.pathfinder = None
        
        # Rendering
        self.camera = Camera(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.renderer = Renderer(self.screen, self.camera)
        
        # UI Systems
        self.hud = HUD(self.screen)
        self.inventory_ui = InventoryUI(self.screen)
        self.skill_tree_ui = SkillTreeUI(self.screen)
        self.action_bar = ActionBar(self.screen, self.event_bus)
        self.minimap = Minimap(self.screen)
        self.notifications = NotificationManager(self.screen)
        self.pause_overlay = PauseOverlay(self.screen)
        self.game_over_overlay = GameOverOverlay(self.screen)
        
        # Scenes
        self.town_scene = TownScene(self.screen, self.event_bus)
        
        # Set up overlay callbacks
        self._setup_overlay_callbacks()
        
        # Audio - generate all sounds and music
        self.audio = AudioManager(self.event_bus)
        self.audio.initialize()
        
        # Start dungeon ambient music
        self.audio.play_music("dungeon_ambient")
        
        # Processors
        self._setup_processors()
        
        # Subscribe to events
        self._setup_event_handlers()
        
        # Current level
        self.current_level = 1
        
        # Track entities
        self.party_entities = []
        
        # FPS tracking
        self.fps = 0.0
    
    def _setup_overlay_callbacks(self):
        """Set up callbacks for overlay menus."""
        # Pause overlay
        self.pause_overlay.on_resume = lambda: setattr(self, 'state', GameState.PLAYING)
        self.pause_overlay.on_save = lambda: self.event_bus.emit(Event(EventType.GAME_SAVE_REQUESTED))
        self.pause_overlay.on_load = lambda: self.event_bus.emit(Event(EventType.GAME_LOAD_REQUESTED))
        self.pause_overlay.on_quit = lambda: setattr(self, 'running', False)
        
        # Game over overlay
        self.game_over_overlay.on_retry = self._restart_game
        self.game_over_overlay.on_quit = lambda: setattr(self, 'running', False)
    
    def _setup_processors(self):
        """Initialize and add all ECS processors in correct order."""
        from .ecs.processors import RegenProcessor
        
        # Create processors
        self.input_processor = InputProcessor(self.event_bus)
        self.ai_processor = AIProcessor(self.event_bus)
        self.movement_processor = MovementProcessor(self.event_bus, self.dungeon)
        self.combat_processor = CombatProcessor(self.event_bus)
        self.magic_processor = MagicProcessor(self.event_bus)
        self.animation_processor = AnimationProcessor()
        self.progression_processor = ProgressionProcessor(self.event_bus)
        self.loot_processor = LootProcessor(self.event_bus)
        self.cleanup_processor = CleanupProcessor()
        self.save_load_processor = SaveLoadProcessor(self.event_bus)
        self.world_processor = WorldProcessor(self.event_bus)
        self.dropped_item_processor = DroppedItemProcessor(self.event_bus)
        self.regen_processor = RegenProcessor(self.event_bus)
        
        # Add in order (priority - higher runs first)
        esper.add_processor(self.input_processor, priority=100)
        esper.add_processor(self.ai_processor, priority=90)
        esper.add_processor(self.movement_processor, priority=80)
        esper.add_processor(self.combat_processor, priority=70)
        esper.add_processor(self.magic_processor, priority=60)
        esper.add_processor(self.world_processor, priority=55)  # After magic, before animation
        esper.add_processor(self.regen_processor, priority=52)  # Before animation
        esper.add_processor(self.animation_processor, priority=50)
        esper.add_processor(self.progression_processor, priority=40)
        esper.add_processor(self.loot_processor, priority=30)
        esper.add_processor(self.dropped_item_processor, priority=25)
        esper.add_processor(self.save_load_processor, priority=20)
        esper.add_processor(self.cleanup_processor, priority=0)  # Always last
        
        # Give input processor references to other processors
        self.input_processor.camera = self.camera
        self.input_processor.save_load_processor = self.save_load_processor
        self.input_processor.world_processor = self.world_processor
    
    def _setup_event_handlers(self):
        """Subscribe to game events."""
        self.event_bus.subscribe(EventType.GAME_PAUSED, self._on_pause)
        self.event_bus.subscribe(EventType.PARTY_WIPED, self._on_party_wipe)
        self.event_bus.subscribe(EventType.CAMERA_ZOOMED, self._on_camera_zoom)
        self.event_bus.subscribe(EventType.NOTIFICATION, self._on_notification)
        self.event_bus.subscribe(EventType.MENU_OPENED, self._on_menu_opened)
        self.event_bus.subscribe(EventType.ACTION_BAR_USED, self._on_action_bar_used)
        self.event_bus.subscribe(EventType.LEVEL_UP, self._on_level_up)
        self.event_bus.subscribe(EventType.STAIRS_USED, self._on_stairs_used)
        self.event_bus.subscribe(EventType.TOWN_ENTERED, self._on_town_entered)
        self.event_bus.subscribe(EventType.TOWN_LEFT, self._on_town_left)
        self.event_bus.subscribe(EventType.GAME_LOADED, self._on_game_loaded)
    
    def _on_pause(self, event):
        """Handle pause event."""
        if self.state == GameState.PLAYING:
            self.state = GameState.PAUSED
            self.pause_overlay.show()
        elif self.state == GameState.PAUSED:
            self.state = GameState.PLAYING
            self.pause_overlay.hide()
    
    def _on_party_wipe(self, event):
        """Handle party wipe."""
        self.state = GameState.GAME_OVER
        self.game_over_overlay.show("All heroes have fallen...")
    
    def _on_camera_zoom(self, event):
        """Handle camera zoom."""
        direction = event.data.get("direction", 0)
        self.camera.adjust_zoom(direction)
    
    def _on_notification(self, event):
        """Handle notification event."""
        text = event.data.get("text", "")
        color = event.data.get("color", (255, 255, 255))
        self.notifications.add(text, color)
    
    def _on_menu_opened(self, event):
        """Handle menu open events."""
        menu = event.data.get("menu", "")
        if menu == "inventory":
            self.inventory_ui.toggle()
            self.state = GameState.INVENTORY if self.inventory_ui.visible else GameState.PLAYING
        elif menu == "skill_tree":
            self.skill_tree_ui.toggle()
            self.state = GameState.SKILL_TREE if self.skill_tree_ui.visible else GameState.PLAYING
    
    def _on_action_bar_used(self, event):
        """Handle action bar slot use."""
        slot = event.data.get("slot", 0)
        # Find selected party member
        from .ecs.components import PlayerControlled, Selected
        for ent, (_, _) in esper.get_components(PlayerControlled, Selected):
            self.action_bar.use_slot(slot, ent)
            break
    
    def _on_level_up(self, event):
        """Handle level up event."""
        skill = event.data.get("skill", "")
        new_level = event.data.get("new_level", 1)
        self.notifications.add(
            f"{skill.title()} Level {new_level}!",
            (255, 255, 100)
        )
    
    def _restart_game(self):
        """Restart the game."""
        self._setup_processors()
        self.start_new_game()
        self.state = GameState.PLAYING
    
    def _on_stairs_used(self, event):
        """Handle stairs usage - change dungeon level."""
        direction = event.data.get("direction", 1)
        
        if direction > 0:
            # Going down
            self.current_level += 1
            self._generate_new_level()
        elif direction < 0 and self.current_level > 1:
            # Going up (can't go above level 1)
            self.current_level -= 1
            self._generate_new_level()
        elif direction < 0 and self.current_level == 1:
            # Return to town from level 1
            self.event_bus.emit(Event(EventType.TOWN_ENTERED, {
                "from_level": self.current_level
            }))
    
    def _on_town_entered(self, event):
        """Handle entering town."""
        self.state = GameState.TOWN
        self.town_scene.show()
    
    def _on_town_left(self, event):
        """Handle leaving town."""
        self.state = GameState.PLAYING
        self.town_scene.hide()
        target_level = event.data.get("target_level", 1)
        
        if target_level != self.current_level:
            self.current_level = target_level
            self._generate_new_level()
    
    def _on_game_loaded(self, event):
        """Handle game loaded - regenerate dungeon with saved seed and restore state."""
        from .ecs.components import (
            Gold, Position, PlayerControlled, Selected, Health, Mana,
            Attributes, SkillLevels, SkillXP, CharacterLevel, SpellBook, Enemy
        )
        from .ecs.factories import create_enemies_for_level
        
        dungeon_level = event.data.get("dungeon_level", 1)
        dungeon_seed = event.data.get("dungeon_seed")
        party_data = event.data.get("party_data", [])
        total_gold = event.data.get("total_gold", 0)
        
        # Remove all existing enemies before regenerating dungeon
        enemies_to_remove = []
        for ent, (_,) in esper.get_components(Enemy):
            enemies_to_remove.append(ent)
        for ent in enemies_to_remove:
            esper.delete_entity(ent)
        
        # Regenerate dungeon with the saved seed
        self.current_level = dungeon_level
        size_increase = min(dungeon_level * 5, 40)
        self.dungeon = Dungeon(80 + size_increase, 80 + size_increase)
        self.dungeon.generate(
            min_rooms=8 + dungeon_level,
            max_rooms=12 + dungeon_level * 2,
            seed=dungeon_seed
        )
        
        self.pathfinder = Pathfinder(self.dungeon)
        
        # Update processors with new dungeon
        self.movement_processor.set_dungeon(self.dungeon)
        self.combat_processor.set_dungeon(self.dungeon)
        self.magic_processor.set_dungeon(self.dungeon)
        self.ai_processor.set_pathfinder(self.pathfinder)
        self.ai_processor.set_dungeon(self.dungeon)
        self.world_processor.set_dungeon(self.dungeon)
        self.loot_processor.dungeon_level = self.current_level
        self.minimap.set_dungeon(self.dungeon)
        
        # Respawn enemies at correct spawn points
        create_enemies_for_level(
            self.dungeon.spawn_points,
            self.current_level,
            {"spawning": {"enemy_table": [
                {"levels": [1, 3], "enemies": [
                    {"id": "skeleton", "weight": 50},
                    {"id": "goblin", "weight": 30},
                    {"id": "spider", "weight": 20}
                ]},
                {"levels": [4, 99], "enemies": [
                    {"id": "skeleton", "weight": 30},
                    {"id": "goblin", "weight": 25},
                    {"id": "zombie", "weight": 25},
                    {"id": "orc", "weight": 15},
                    {"id": "spider", "weight": 5}
                ]}
            ]}}
        )
        
        # Update save processor with dungeon info
        self.save_load_processor.set_dungeon_info(self.current_level, self.dungeon.seed)
        
        # Restore party data
        party_by_index = {}
        for ent, (member,) in esper.get_components(PartyMember):
            party_by_index[member.party_index] = ent
        
        for char_data in party_data:
            party_idx = char_data.get("party_index", 0)
            if party_idx not in party_by_index:
                continue
            ent = party_by_index[party_idx]
            
            # Restore position
            if "position" in char_data and esper.has_component(ent, Position):
                pos = esper.component_for_entity(ent, Position)
                pos.x = char_data["position"]["x"]
                pos.y = char_data["position"]["y"]
            
            # Restore health
            if "health" in char_data and esper.has_component(ent, Health):
                health = esper.component_for_entity(ent, Health)
                health.current = char_data["health"]["current"]
                health.maximum = char_data["health"]["maximum"]
            
            # Restore mana
            if "mana" in char_data and esper.has_component(ent, Mana):
                mana = esper.component_for_entity(ent, Mana)
                mana.current = char_data["mana"]["current"]
                mana.maximum = char_data["mana"]["maximum"]
            
            # Restore attributes
            if "attributes" in char_data and esper.has_component(ent, Attributes):
                attrs = esper.component_for_entity(ent, Attributes)
                attrs.strength = char_data["attributes"]["strength"]
                attrs.dexterity = char_data["attributes"]["dexterity"]
                attrs.intelligence = char_data["attributes"]["intelligence"]
            
            # Restore skills
            if "skills" in char_data and esper.has_component(ent, SkillLevels):
                skills = esper.component_for_entity(ent, SkillLevels)
                skills.melee = char_data["skills"]["melee"]
                skills.ranged = char_data["skills"]["ranged"]
                skills.combat_magic = char_data["skills"]["combat_magic"]
                skills.nature_magic = char_data["skills"]["nature_magic"]
            
            # Restore skill XP
            if "skill_xp" in char_data and esper.has_component(ent, SkillXP):
                xp = esper.component_for_entity(ent, SkillXP)
                xp.melee = char_data["skill_xp"]["melee"]
                xp.ranged = char_data["skill_xp"]["ranged"]
                xp.combat_magic = char_data["skill_xp"]["combat_magic"]
                xp.nature_magic = char_data["skill_xp"]["nature_magic"]
            
            # Restore level
            if "level" in char_data and esper.has_component(ent, CharacterLevel):
                level = esper.component_for_entity(ent, CharacterLevel)
                level.level = char_data["level"]
            
            # Restore spells
            if "spells" in char_data and esper.has_component(ent, SpellBook):
                spellbook = esper.component_for_entity(ent, SpellBook)
                spellbook.known_spells = set(char_data["spells"])
        
        # Restore gold
        for ent, (_, gold) in esper.get_components(PartyMember, Gold):
            gold.amount = total_gold
            break
        
        # Center camera on player
        for ent, (pos, _, _) in esper.get_components(Position, PlayerControlled, Selected):
            self.camera.center_on(pos.x, pos.y)
            break
    
    def _generate_new_level(self):
        """Generate a new dungeon level, preserving party."""
        from .ecs.components import Enemy, Position, Health, Mana
        
        # Save party state
        party_data = []
        for ent, (member,) in esper.get_components(PartyMember):
            data = {"entity": ent}
            if esper.has_component(ent, Health):
                h = esper.component_for_entity(ent, Health)
                data["health"] = (h.current, h.maximum)
            if esper.has_component(ent, Mana):
                m = esper.component_for_entity(ent, Mana)
                data["mana"] = (m.current, m.maximum)
            party_data.append(data)
        
        # Remove all enemies (but not party or dropped items)
        enemies_to_remove = []
        for ent, (_,) in esper.get_components(Enemy):
            enemies_to_remove.append(ent)
        for ent in enemies_to_remove:
            esper.delete_entity(ent)
        
        # Generate new dungeon
        size_increase = min(self.current_level * 5, 40)
        self.dungeon = Dungeon(80 + size_increase, 80 + size_increase)
        self.dungeon.generate(
            min_rooms=8 + self.current_level,
            max_rooms=12 + self.current_level * 2
        )
        
        self.pathfinder = Pathfinder(self.dungeon)
        
        # Update processors
        self.movement_processor.set_dungeon(self.dungeon)
        self.combat_processor.set_dungeon(self.dungeon)
        self.magic_processor.set_dungeon(self.dungeon)
        self.ai_processor.set_pathfinder(self.pathfinder)
        self.ai_processor.set_dungeon(self.dungeon)
        self.world_processor.set_dungeon(self.dungeon)
        self.loot_processor.dungeon_level = self.current_level
        
        # Update minimap
        self.minimap.set_dungeon(self.dungeon)
        
        # Update save processor with dungeon info
        self.save_load_processor.set_dungeon_info(self.current_level, self.dungeon.seed)
        
        # Move party to spawn
        spawn_x, spawn_y = self.dungeon.get_player_spawn()
        for data in party_data:
            ent = data["entity"]
            if esper.entity_exists(ent) and esper.has_component(ent, Position):
                pos = esper.component_for_entity(ent, Position)
                pos.x = spawn_x
                pos.y = spawn_y
                spawn_x += 1.0  # Offset party members
        
        # Create new enemies
        from .ecs.factories import create_enemies_for_level
        create_enemies_for_level(
            self.dungeon.spawn_points,
            self.current_level,
            {"spawning": {"enemy_table": [
                {"levels": [1, 3], "enemies": [
                    {"id": "skeleton", "weight": 50},
                    {"id": "goblin", "weight": 30},
                    {"id": "spider", "weight": 20}
                ]},
                {"levels": [4, 99], "enemies": [
                    {"id": "skeleton", "weight": 30},
                    {"id": "goblin", "weight": 25},
                    {"id": "zombie", "weight": 25},
                    {"id": "orc", "weight": 15},
                    {"id": "spider", "weight": 5}
                ]}
            ]}}
        )
        
        # Center camera
        self.camera.center_on(spawn_x - 1, spawn_y)
        
        self.event_bus.emit(Event(EventType.LEVEL_CHANGED, {
            "new_level": self.current_level
        }))
        
        self.notifications.add(f"Dungeon Level {self.current_level}", (255, 220, 150))
    
    def start_new_game(self):
        """Start a new game."""
        self.current_level = 1
        
        # Clear esper database (this also removes processors!)
        esper.clear_database()
        
        # Re-add processors after clearing database
        self._setup_processors()
        
        # Generate dungeon
        self.dungeon.generate(min_rooms=8, max_rooms=12)
        self.pathfinder = Pathfinder(self.dungeon)
        
        # Update processors with dungeon reference
        self.movement_processor.set_dungeon(self.dungeon)
        self.combat_processor.set_dungeon(self.dungeon)
        self.magic_processor.set_dungeon(self.dungeon)
        self.ai_processor.set_pathfinder(self.pathfinder)
        self.ai_processor.set_dungeon(self.dungeon)
        self.world_processor.set_dungeon(self.dungeon)
        self.loot_processor.dungeon_level = self.current_level
        
        # Update minimap
        self.minimap.set_dungeon(self.dungeon)
        
        # Update save processor with dungeon info
        self.save_load_processor.set_dungeon_info(self.current_level, self.dungeon.seed)
        
        # Get spawn position
        spawn_x, spawn_y = self.dungeon.get_player_spawn()
        
        # Create party
        self.party_entities = create_party(spawn_x, spawn_y)
        
        # Create enemies
        create_enemies_for_level(
            self.dungeon.spawn_points,
            self.current_level,
            {"spawning": {"enemy_table": [
                {"levels": [1, 3], "enemies": [
                    {"id": "skeleton", "weight": 70},
                    {"id": "spider", "weight": 30}
                ]},
                {"levels": [4, 99], "enemies": [
                    {"id": "skeleton", "weight": 40},
                    {"id": "zombie", "weight": 30},
                    {"id": "orc", "weight": 20},
                    {"id": "spider", "weight": 10}
                ]}
            ]}}
        )
        
        # Center camera on player
        self.camera.center_on(spawn_x, spawn_y)
        
        # Add notification
        self.notifications.add("Entering the dungeon...", (200, 180, 255))
        
        self.state = GameState.PLAYING
    
    def run(self):
        """Main game loop."""
        # Start new game immediately
        self.start_new_game()
        
        while self.running:
            current_time = time.time()
            frame_time = min(current_time - self.previous_time, 0.25)
            self.previous_time = current_time
            
            # PHASE 1: INPUT (immediate)
            self._handle_events()
            
            # PHASE 2: UPDATE (fixed timestep for game logic states)
            if self.state in (GameState.PLAYING, GameState.INVENTORY, GameState.SKILL_TREE):
                self.accumulator += frame_time
                
                while self.accumulator >= FIXED_TIMESTEP:
                    if self.state == GameState.PLAYING:
                        self._update(FIXED_TIMESTEP)
                    self.accumulator -= FIXED_TIMESTEP
                
                # Update notifications and action bar
                self.notifications.update(frame_time)
                self.action_bar.update(frame_time)
            
            # Update game over animation
            if self.state == GameState.GAME_OVER:
                self.game_over_overlay.update(frame_time)
            
            # PHASE 3: RENDER (variable)
            self._render(frame_time)
            
            # PHASE 4: PRESENT
            pygame.display.flip()
            
            # Cap frame rate
            self.clock.tick(FPS)
            self.fps = self.clock.get_fps()
    
    def _handle_events(self):
        """Handle pygame events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                continue
            
            # UI overlays get first crack at events
            if self.state == GameState.PAUSED:
                if self.pause_overlay.handle_event(event):
                    continue
            
            if self.state == GameState.GAME_OVER:
                if self.game_over_overlay.handle_event(event):
                    continue
            
            if self.state == GameState.INVENTORY:
                if self.inventory_ui.handle_event(event):
                    if not self.inventory_ui.visible:
                        self.state = GameState.PLAYING
                    continue
            
            if self.state == GameState.SKILL_TREE:
                if self.skill_tree_ui.handle_event(event):
                    if not self.skill_tree_ui.visible:
                        self.state = GameState.PLAYING
                    continue
            
            if self.state == GameState.TOWN:
                if self.town_scene.handle_event(event):
                    continue
            
            # Pass to input processor
            if self.state == GameState.PLAYING:
                self.input_processor.handle_event(event)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.state == GameState.PAUSED:
                        self.state = GameState.PLAYING
                        self.pause_overlay.hide()
                    elif self.state == GameState.GAME_OVER:
                        self.running = False
                elif event.key == pygame.K_SPACE:
                    if self.state == GameState.GAME_OVER:
                        # Restart
                        self._restart_game()
    
    def _update(self, dt: float):
        """Update game state."""
        # Process all ECS systems
        esper.process(dt)
        
        # Process events
        self.event_bus.process()
        
        # Update camera to follow player
        from .ecs.components import Position, PlayerControlled, Selected
        
        for ent, (pos, _, _) in esper.get_components(
            Position, PlayerControlled, Selected
        ):
            self.camera.follow(pos.x, pos.y)
            break
        
        self.camera.update(dt)
    
    def _render(self, dt: float):
        """Render the game."""
        # Always render world and entities (for menu backgrounds)
        self.renderer.render(self.dungeon)
        
        # Render HUD elements when not in full-screen menus
        if self.state != GameState.GAME_OVER:
            self.hud.render(self.fps)
            self.minimap.render()
            
            # Get selected entity for action bar
            from .ecs.components import PlayerControlled, Selected
            selected = -1
            for ent, (_, _) in esper.get_components(PlayerControlled, Selected):
                selected = ent
                break
            if selected >= 0:
                self.action_bar.render(selected)
        
        # Render notifications
        self.notifications.render()
        
        # Render UI overlays
        if self.state == GameState.PAUSED:
            self.pause_overlay.render()
        elif self.state == GameState.GAME_OVER:
            self.game_over_overlay.render()
        elif self.state == GameState.INVENTORY:
            self.inventory_ui.render()
        elif self.state == GameState.SKILL_TREE:
            self.skill_tree_ui.render()
        elif self.state == GameState.TOWN:
            self.town_scene.render()
