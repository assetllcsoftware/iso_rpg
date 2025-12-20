"""Main game class."""

import pygame
from .constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS, COLOR_BG, COLOR_TEXT_DIM,
    SKILL_MELEE, SKILL_RANGED, SKILL_COMBAT_MAGIC, SKILL_NATURE_MAGIC
)
from .camera import Camera
from .renderer import IsometricRenderer
from ..world.world import World
from ..entities.character import Character
from ..ui.hud import HUD
from ..ui.touch_controls import TouchControls
from ..ui.inventory import InventoryUI
from ..ui.action_bar import ActionBar
from ..ui.skill_tree import SkillTreeUI
from ..ui.town import TownScene, PortalButton
from ..ui.spell_buttons import SpellButtons
from ..ui.save_menu import SaveLoadMenu
from ..systems.audio import audio
from ..systems.magic import MagicSystem, SpellBook, Spell
from ..systems.effects import EffectsManager
from ..systems.save_load import save_game, load_game
from ..entities.item import create_weapon, create_armor, create_potion


class Game:
    """Main game manager."""
    
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Dungeon Siege Mobile")
        
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True
        self.paused = False
        self.game_over = False
        self.game_over_timer = 0
        
        # Core systems
        self.camera = Camera()
        self.renderer = IsometricRenderer(self.screen)
        self.hud = HUD(self.screen)
        self.touch = TouchControls()
        self.magic = MagicSystem()
        self.inventory_ui = InventoryUI(self.screen)
        self.effects = EffectsManager()
        self.action_bar = ActionBar(self.screen)
        self.skill_tree = SkillTreeUI(self.screen)
        self.town_scene = TownScene(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.in_town = False
        self.spell_buttons = SpellButtons(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.save_menu = SaveLoadMenu(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.portal_button = PortalButton(SCREEN_WIDTH - 70, SCREEN_HEIGHT - 130)
        self.audio = audio
        
        # Keyboard movement state
        self.keys_held = {
            'up': False,
            'down': False,
            'left': False,
            'right': False
        }
        
        # Game state
        self.world = None
        self.party = []
        self.selected_character = None
        self.target = None
        self.gold = 0
        
        # Notifications
        self.notifications = []
        self.notification_timer = 0
        
        # Combat state
        self.in_combat = False
        
        # Initialize game
        self._new_game()
    
    def _new_game(self):
        """Start a new game."""
        # Reset state
        self.party = []
        self.target = None
        self.gold = 0
        self.notifications = []
        self.game_over = False
        self.game_over_timer = 0
        self.paused = False
        
        # Create world
        self.world = World(60, 60)
        spawn_points = self.world.generate_dungeon(level=1)
        
        # Create party
        spawn = spawn_points[0] if spawn_points else (30, 30)
        
        # Main character
        hero = Character("Hero", spawn[0], spawn[1])
        hero.is_player_controlled = True
        hero.color = (140, 180, 220)
        # Hero starts with 2 spells
        hero.spellbook = SpellBook()
        hero.spellbook.learn_spell('fireball')    # Q
        hero.spellbook.learn_spell('heal')        # W
        
        # Starting equipment
        sword = create_weapon('short_sword', level=1)
        if sword:
            hero.equipment['main_hand'] = sword
        
        # Starting potions
        for _ in range(3):
            potion = create_potion('health', level=1)
            if potion:
                hero.inventory.append(potion)
        for _ in range(2):
            potion = create_potion('mana', level=1)
            if potion:
                hero.inventory.append(potion)
        
        # Some starter equipment to sell/use
        extra_sword = create_weapon('short_sword', level=1)
        if extra_sword:
            hero.inventory.append(extra_sword)
        bow = create_weapon('bow', level=1)
        if bow:
            hero.inventory.append(bow)
        helm = create_armor('leather_helm', level=1)
        if helm:
            hero.inventory.append(helm)
        boots = create_armor('leather_boots', level=1)
        if boots:
            hero.inventory.append(boots)
        
        self.party.append(hero)
        
        # Companion - Elven Mage class
        companion = Character("Lyra", spawn[0] + 1, spawn[1] + 1)
        companion.char_class = 'mage'
        companion.color = (140, 180, 220)  # Blue-ish for mage
        companion.follow_target = hero
        companion.formation_offset = (1.5, 1.5)
        
        # Mage stats: high int/mana, low strength
        companion.strength = 6
        companion.dexterity = 10
        companion.intelligence = 16
        companion.max_mana = 80
        companion.mana = 80
        companion.max_health = 120
        companion.health = 120
        
        # Mage starts at level 0 like everyone - learns spells through use
        # (skills start at 0 by default)
        companion.skills[SKILL_RANGED] = 1
        
        # Lyra starts with 1 spell
        companion.spellbook = SpellBook()
        companion.spellbook.learn_spell('ice_shard')     # A
        
        # Companion equipment - staff
        staff = create_weapon('staff', level=1)
        if staff:
            companion.equipment['main_hand'] = staff
        
        # Companion potions - more mana
        for _ in range(1):
            potion = create_potion('health', level=1)
            if potion:
                companion.inventory.append(potion)
        for _ in range(3):
            potion = create_potion('mana', level=1)
            if potion:
                companion.inventory.append(potion)
        
        # Lyra's spare gear
        extra_staff = create_weapon('staff', level=1)
        if extra_staff:
            companion.inventory.append(extra_staff)
        robe = create_armor('leather_chest', level=1)
        if robe:
            companion.inventory.append(robe)
        
        self.party.append(companion)
        
        # Add party to world
        self.world.characters = self.party
        
        # Select main character
        self.selected_character = hero
        
        # Center camera
        self.camera.follow(hero.x, hero.y, instant=True)
        
        self.add_notification("Welcome to the dungeon!", (180, 140, 90))
        
        # Start background music
        self.audio.play_music('dungeon')
    
    def add_notification(self, text, color=(225, 215, 200)):
        """Add a floating notification."""
        self.notifications.append({
            'text': text,
            'color': color,
            'time': 3.0
        })
    
    def run(self):
        """Main game loop."""
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            
            self._handle_events()
            
            if not self.paused and not self.game_over:
                self._update(dt)
            elif self.game_over:
                self.game_over_timer += dt
            
            self._render()
            
            pygame.display.flip()
        
        pygame.quit()
    
    def _handle_events(self):
        """Process input events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            # Town scene has highest priority when active
            if self.in_town and self.selected_character:
                result = self.town_scene.handle_event(event, self.selected_character)
                if result == 'exit':
                    self._exit_town()
                continue
            
            elif event.type == pygame.KEYDOWN:
                # Save menu gets highest priority
                if self.save_menu.visible:
                    if self.save_menu.handle_event(event, self):
                        continue
                
                # Skill tree gets priority for key events when visible
                if self.skill_tree.visible:
                    if self.skill_tree.handle_event(event):
                        continue
                
                # Track arrow key presses (NOT WASD - those are for spells)
                if event.key == pygame.K_UP:
                    self.keys_held['up'] = True
                elif event.key == pygame.K_DOWN:
                    self.keys_held['down'] = True
                elif event.key == pygame.K_LEFT:
                    self.keys_held['left'] = True
                elif event.key == pygame.K_RIGHT:
                    self.keys_held['right'] = True
                
                self._handle_key(event.key)
            
            elif event.type == pygame.KEYUP:
                # Track arrow key releases
                if event.key == pygame.K_UP:
                    self.keys_held['up'] = False
                elif event.key == pygame.K_DOWN:
                    self.keys_held['down'] = False
                elif event.key == pygame.K_LEFT:
                    self.keys_held['left'] = False
                elif event.key == pygame.K_RIGHT:
                    self.keys_held['right'] = False
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                
                # Check spell button clicks
                spell_click = self.spell_buttons.handle_click(mx, my)
                if spell_click:
                    party_idx, spell_idx = spell_click
                    self._cast_party_spell(party_idx, spell_idx)
                    continue
                
                # Check portal button click
                if self.portal_button.handle_click(mx, my):
                    self._enter_town()
                    continue
                
                # Inventory UI gets first crack at events
                if self.inventory_ui.visible and self.selected_character:
                    if self.inventory_ui.handle_event(event, self.selected_character, self.action_bar):
                        continue
                
                # Don't process mouse/touch when skill tree is open
                if self.skill_tree.visible:
                    continue
                
                action = self.touch.handle_event(event)
                if action:
                    self._handle_touch_action(action)
            
            else:
                # Save menu gets highest priority for mouse events
                if self.save_menu.visible:
                    if self.save_menu.handle_event(event, self):
                        continue
                
                # Inventory UI gets first crack at events
                if self.inventory_ui.visible and self.selected_character:
                    if self.inventory_ui.handle_event(event, self.selected_character, self.action_bar):
                        continue
                
                # Don't process mouse/touch when skill tree is open
                if self.skill_tree.visible:
                    continue
                
                action = self.touch.handle_event(event)
                if action:
                    self._handle_touch_action(action)
        
        # Check for held touch
        action = self.touch.update(dt=1/60)
        if action:
            self._handle_touch_action(action)
        
        # Handle keyboard movement
        self._handle_keyboard_movement()
    
    def _handle_keyboard_movement(self):
        """Handle arrow key movement."""
        if self.paused or self.game_over:
            return
        if self.inventory_ui.visible or self.skill_tree.visible:
            return
        if not self.selected_character:
            return
        
        # Calculate movement direction
        dx, dy = 0, 0
        if self.keys_held['up']:
            dy -= 1
        if self.keys_held['down']:
            dy += 1
        if self.keys_held['left']:
            dx -= 1
        if self.keys_held['right']:
            dx += 1
        
        if dx != 0 or dy != 0:
            # Normalize diagonal movement
            if dx != 0 and dy != 0:
                dx *= 0.707  # 1/sqrt(2)
                dy *= 0.707
            
            char = self.selected_character
            speed = char.speed * (1/60)  # Per frame
            
            new_x = char.x + dx * speed
            new_y = char.y + dy * speed
            
            # Check if walkable
            if self.world.is_walkable(new_x, new_y):
                char.x = new_x
                char.y = new_y
                char.target_pos = None  # Cancel click-to-move
    
    def _attack_nearest_enemy(self):
        """Attack the nearest enemy in range."""
        if not self.selected_character:
            return
        
        char = self.selected_character
        attack_range = 2.0  # Melee range
        
        # Check if we have a ranged weapon
        weapon = char.equipment.get('main_hand')
        if weapon and weapon.weapon_type == 'ranged':
            attack_range = 6.0
        elif weapon and weapon.weapon_type == 'magic':
            attack_range = 5.0
        
        # Find nearest enemy
        nearest = None
        nearest_dist = float('inf')
        
        for enemy in self.world.enemies:
            if enemy.health <= 0:
                continue
            dist = ((enemy.x - char.x)**2 + (enemy.y - char.y)**2)**0.5
            if dist < nearest_dist and dist <= attack_range:
                nearest_dist = dist
                nearest = enemy
        
        if nearest:
            char.target = nearest
            self.add_notification(f"Attacking {nearest.name}", (200, 100, 100))
        else:
            self.add_notification("No enemy in range", (150, 150, 150))
    
    def _handle_key(self, key):
        """Handle keyboard input."""
        # Restart on game over
        if self.game_over:
            if key in (pygame.K_r, pygame.K_SPACE, pygame.K_RETURN):
                self._new_game()
            return
        
        if key == pygame.K_ESCAPE:
            self.paused = not self.paused
        elif key == pygame.K_SPACE:
            # Space = attack nearest enemy (not pause)
            if not self.inventory_ui.visible and not self.skill_tree.visible:
                self._attack_nearest_enemy()
            else:
                # Close menus with space
                self.inventory_ui.visible = False
                self.skill_tree.visible = False
        elif key == pygame.K_TAB:
            # Cycle selected character
            if self.party:
                idx = self.party.index(self.selected_character)
                self.selected_character = self.party[(idx + 1) % len(self.party)]
        elif key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, 
                     pygame.K_5, pygame.K_6, pygame.K_7, pygame.K_8):
            # Number keys 1-8 use action bar slots
            slot_index = key - pygame.K_1  # Convert to 0-7
            if self.selected_character:
                self.action_bar.use_slot(slot_index, self.selected_character, self)
        # Spell keys per character row
        # QWER = party[0] (main), ASDF = party[1] (ally 1), ZXCV = party[2] (ally 2)
        elif key in (pygame.K_q, pygame.K_w, pygame.K_e, pygame.K_r):
            self._cast_party_spell(0, [pygame.K_q, pygame.K_w, pygame.K_e, pygame.K_r].index(key))
        elif key in (pygame.K_a, pygame.K_s, pygame.K_d, pygame.K_f):
            self._cast_party_spell(1, [pygame.K_a, pygame.K_s, pygame.K_d, pygame.K_f].index(key))
        elif key in (pygame.K_z, pygame.K_x, pygame.K_c, pygame.K_v):
            self._cast_party_spell(2, [pygame.K_z, pygame.K_x, pygame.K_c, pygame.K_v].index(key))
        elif key == pygame.K_i:
            self.inventory_ui.set_party(self.party, 0)
            self.inventory_ui.toggle()
        elif key == pygame.K_c:
            self.inventory_ui.set_party(self.party, 0)
            self.inventory_ui.toggle()  # Character sheet
        elif key == pygame.K_k:
            self.skill_tree.set_party(self.party, 0)
            self.skill_tree.toggle()  # Skill tree
        elif key in (pygame.K_g, pygame.K_f):
            self._pickup_nearby_items()
        elif key in (pygame.K_RETURN, pygame.K_PERIOD, pygame.K_GREATER):
            self._try_descend_stairs()
        elif key == pygame.K_F5:
            self.save_menu.show('save')
        elif key == pygame.K_F9:
            self.save_menu.show('load')
        elif key == pygame.K_m:
            self.audio.toggle_music()
            status = "on" if self.audio.current_music else "off"
            self.add_notification(f"Music {status}", (150, 150, 200))
    
    def _handle_touch_action(self, action):
        """Handle touch/mouse actions."""
        # Restart on game over with click
        if self.game_over:
            if action['action'] in ('tap', 'double_tap'):
                self._new_game()
            return
        
        # Don't process world clicks when inventory is open
        if self.inventory_ui.visible:
            return
        
        if action['action'] == 'tap':
            self._handle_tap(action['pos'], action.get('button', 1))
        
        elif action['action'] == 'double_tap':
            self._handle_double_tap(action['pos'])
        
        elif action['action'] == 'camera_drag_start':
            self.camera.start_drag(action['pos'])
        
        elif action['action'] == 'camera_drag_move':
            self.camera.update_drag(action['pos'])
        
        elif action['action'] == 'camera_drag_end':
            self.camera.end_drag()
        
        elif action['action'] == 'zoom':
            self.camera.zoom_at(pygame.mouse.get_pos(), action['delta'])
    
    def _handle_tap(self, pos, button):
        """Handle tap/click."""
        world_pos = self.camera.screen_to_world(*pos)
        
        # PRIORITY 1: Check for items first (before entities) 
        item_pickup = self._get_item_at(world_pos[0], world_pos[1])
        if item_pickup:
            self._pickup_item(item_pickup)
            return
        
        # PRIORITY 2: Check if there are items near the character
        if self.selected_character:
            char = self.selected_character
            item_near_char = self._get_item_at(char.x, char.y, radius=3.0)
            if item_near_char:
                self._pickup_item(item_near_char)
                return
        
        # PRIORITY 3: Check if tapping on entity
        entity = self.world.get_entity_at(world_pos[0], world_pos[1])
        
        if entity:
            if entity in self.party:
                # Select party member
                self.selected_character = entity
            else:
                # Target enemy
                self.target = entity
        else:
            # Move to location
            if self.selected_character:
                path = self.world.find_path(
                    (self.selected_character.x, self.selected_character.y),
                    world_pos
                )
                if path:
                    self.selected_character.set_path(path)
    
    def _handle_double_tap(self, pos):
        """Handle double tap - attack or interact."""
        world_pos = self.camera.screen_to_world(*pos)
        entity = self.world.get_entity_at(world_pos[0], world_pos[1])
        
        if entity and entity not in self.party:
            # Attack!
            self.target = entity
            self._command_attack(entity)
    
    def _command_attack(self, target):
        """Command selected character to attack target."""
        if not self.selected_character:
            return
        
        char = self.selected_character
        char.target = target
        char.in_combat = True
        
        # Move into range
        dist = char.distance_to(target)
        if dist > char.attack_range:
            path = self.world.find_path(
                (char.x, char.y),
                (target.x, target.y)
            )
            if path:
                char.set_path(path)
    
    def _use_potion(self, potion_type):
        """Use a potion from inventory."""
        if not self.selected_character:
            return
        
        char = self.selected_character
        for item in char.inventory:
            if hasattr(item, 'effect_type') and item.effect_type == potion_type:
                if item.use(char):
                    char.inventory.remove(item)
                    self.add_notification(f"Used {item.name}")
                    return
    
    def _cast_party_spell(self, party_index, spell_index):
        """Cast a spell for a specific party member by index."""
        if party_index >= len(self.party):
            return
        
        char = self.party[party_index]
        if not hasattr(char, 'spellbook'):
            return
        
        spells = list(char.spellbook.spells.keys())
        if spell_index >= len(spells):
            return
        
        spell_id = spells[spell_index]
        self._cast_spell_for_char(char, spell_id)
    
    def _cast_spell(self, spell_id):
        """Cast a spell at target or self (for selected character)."""
        if not self.selected_character:
            return
        self._cast_spell_for_char(self.selected_character, spell_id)
    
    def _cast_spell_for_char(self, char, spell_id):
        """Cast a spell for a specific character."""
        if not hasattr(char, 'spellbook'):
            return
        
        if spell_id not in char.spellbook.spells:
            self.add_notification("Spell not learned!", (180, 80, 80))
            return
        
        spell = char.spellbook.spells[spell_id]
        
        # Reset AI timer for this spell (so AI waits 3x cooldown before auto-casting)
        if hasattr(char, 'ai_spell_timers'):
            char.ai_spell_timers[spell_id] = 0
        
        # Determine target position
        actual_target = self.target
        
        # For offensive spells, auto-target nearest enemy if no target selected
        if spell.damage > 0 and not actual_target:
            nearest_enemy = None
            nearest_dist = float('inf')
            for enemy in self.world.enemies:
                if enemy.health > 0:
                    dist = ((char.x - enemy.x) ** 2 + (char.y - enemy.y) ** 2) ** 0.5
                    if dist < nearest_dist and dist <= spell.range:
                        nearest_dist = dist
                        nearest_enemy = enemy
            if nearest_enemy:
                actual_target = nearest_enemy
        
        if actual_target and actual_target != char:
            target_pos = (actual_target.x, actual_target.y)
            
            # Check range for offensive spells
            if spell.damage > 0 and spell.range > 0:
                dist = ((char.x - actual_target.x) ** 2 + (char.y - actual_target.y) ** 2) ** 0.5
                if dist > spell.range:
                    self.add_notification("Target out of range!", (180, 80, 80))
                    return
        else:
            # Self-cast (heals, buffs)
            target_pos = (char.x, char.y)
        
        # For chain lightning, find additional targets
        extra_targets = None
        if spell_id == 'chain_lightning' and self.target:
            extra_targets = []
            # Find up to 3 more enemies near the primary target
            for enemy in self.world.enemies:
                if enemy != self.target and enemy.health > 0:
                    dist = ((enemy.x - self.target.x) ** 2 + (enemy.y - self.target.y) ** 2) ** 0.5
                    if dist <= 4.0:  # Chain jump range
                        extra_targets.append((enemy.x, enemy.y))
                        if len(extra_targets) >= 3:
                            break
        
        spell = self.magic.cast_spell(
            char, char.spellbook, spell_id, target_pos, self.world
        )
        
        if spell:
            self.add_notification(f"{char.name}: {spell.name}!", spell.color)
            
            # Calculate damage for projectile effects
            damage = spell.get_damage(char) if spell.damage > 0 else 0
            
            # Spawn spell visual effect with delayed damage
            self.effects.spawn_spell(
                spell_id, char.x, char.y, target_pos[0], target_pos[1], 
                extra_targets=extra_targets,
                damage=damage,
                damage_target=actual_target,
                caster=char
            )
            
            # Chain lightning damages extra targets
            if spell_id == 'chain_lightning' and extra_targets:
                chain_damage = spell.get_damage(char)
                for ex, ey in extra_targets:
                    for enemy in self.world.enemies:
                        if enemy.health > 0 and abs(enemy.x - ex) < 1.0 and abs(enemy.y - ey) < 1.0:
                            enemy.take_damage(chain_damage, char)
                            break
            
            if 'heal' in spell_id:
                self.audio.play('heal')
            elif 'fire' in spell_id:
                self.audio.play('fireball')
            else:
                self.audio.play('spell_cast')
        else:
            # Check why it failed
            if spell_id not in char.spellbook.spells:
                self.add_notification("Spell not learned!", (180, 80, 80))
            elif char.mana < char.spellbook.spells.get(spell_id, Spell("", 999, "")).mana_cost:
                self.add_notification("Not enough mana!", (80, 80, 180))
    
    def _get_item_at(self, x, y, radius=2.0):
        """Get dropped item at world position. Larger radius = easier clicking."""
        # Sort by distance and return closest
        items_with_dist = []
        for item_data in self.world.items_on_ground:
            dist = ((item_data['x'] - x) ** 2 + (item_data['y'] - y) ** 2) ** 0.5
            if dist <= radius:
                items_with_dist.append((dist, item_data))
        
        if items_with_dist:
            items_with_dist.sort(key=lambda x: x[0])
            return items_with_dist[0][1]
        return None
    
    def _pickup_item(self, item_data):
        """Pick up an item from the ground."""
        if not self.selected_character:
            print("[DEBUG] _pickup_item: No selected character")
            return
        
        char = self.selected_character
        dist = char.distance_to((item_data['x'], item_data['y']))
        print(f"[DEBUG] _pickup_item: {item_data['item'].name} dist={dist:.1f}")
        
        if dist > 3.0:  # Increased range
            # Too far, move to it
            path = self.world.find_path(
                (char.x, char.y),
                (item_data['x'], item_data['y'])
            )
            if path:
                char.set_path(path)
            self.add_notification("Moving to item...", COLOR_TEXT_DIM)
            print(f"[DEBUG] _pickup_item: Too far, moving")
            return
        
        item = item_data['item']
        
        # Check weight
        if char.current_weight + item.weight > char.max_weight:
            self.add_notification("Inventory full!", (200, 100, 100))
            print(f"[DEBUG] _pickup_item: Inventory full")
            return
        
        # Add to inventory
        char.inventory.append(item)
        self.world.items_on_ground.remove(item_data)
        self.audio.play('pickup')
        print(f"[DEBUG] _pickup_item: SUCCESS picked up {item.name}")
        
        # Notification with rarity color
        from ..engine.constants import RARITY_COLORS
        color = RARITY_COLORS.get(item.rarity, (200, 200, 200))
        self.add_notification(f"Picked up {item.name}", color)
    
    def _pickup_nearby_items(self):
        """Pick up all items near the selected character."""
        if not self.selected_character:
            return
        
        char = self.selected_character
        pickup_range = 5.0  # Very generous range
        
        # Debug: show total items on ground
        total_items = len(self.world.items_on_ground)
        print(f"[DEBUG] G pressed: {total_items} items on ground, char at ({char.x:.1f}, {char.y:.1f})")
        
        # Build list first to avoid modification during iteration
        items_to_pickup = []
        for item_data in list(self.world.items_on_ground):
            dist = char.distance_to((item_data['x'], item_data['y']))
            print(f"[DEBUG]   - {item_data['item'].name} at ({item_data['x']:.1f}, {item_data['y']:.1f}) dist={dist:.1f}")
            if dist <= pickup_range:
                items_to_pickup.append(item_data)
        
        if not items_to_pickup:
            self.add_notification(f"No items in range ({total_items} on map)", (150, 150, 150))
            return
        
        picked_count = 0
        for item_data in items_to_pickup:
            if item_data not in self.world.items_on_ground:
                continue  # Already picked up by auto-pickup
            item = item_data['item']
            if char.current_weight + item.weight <= char.max_weight:
                char.inventory.append(item)
                self.world.items_on_ground.remove(item_data)
                picked_count += 1
                print(f"[DEBUG] G pickup SUCCESS: {item.name}")
                from ..engine.constants import RARITY_COLORS
                color = RARITY_COLORS.get(item.rarity, (200, 200, 200))
                self.add_notification(f"Picked up {item.name}", color)
            else:
                print(f"[DEBUG] G pickup FAILED: {item.name} - too heavy")
        
        if picked_count > 0:
            self.audio.play('pickup')
        else:
            self.add_notification("Couldn't pick up items (weight?)", (200, 150, 100))
    
    def _auto_pickup(self):
        """Auto-pickup ALL items when walking over them."""
        if not self.selected_character:
            return
        
        char = self.selected_character
        auto_range = 1.5  # Pickup range
        
        items_to_pickup = []
        for item_data in list(self.world.items_on_ground):
            dist = char.distance_to((item_data['x'], item_data['y']))
            if dist <= auto_range:
                item = item_data['item']
                if char.current_weight + item.weight <= char.max_weight:
                    items_to_pickup.append(item_data)
        
        for item_data in items_to_pickup:
            item = item_data['item']
            char.inventory.append(item)
            self.world.items_on_ground.remove(item_data)
            from ..engine.constants import RARITY_COLORS
            color = RARITY_COLORS.get(item.rarity, (200, 200, 200))
            self.add_notification(f"Picked up {item.name}", color)
            self.audio.play('pickup')
    
    def _try_descend_stairs(self):
        """Try to go down stairs."""
        if not self.selected_character:
            return
        
        if self.world.is_on_stairs(self.selected_character):
            self._descend_to_next_level()
        else:
            self.add_notification("No stairs here!", (150, 150, 150))
    
    def _descend_to_next_level(self):
        """Go to the next dungeon level."""
        next_level = self.world.level + 1
        
        self.add_notification(f"Descending to level {next_level}...", (100, 200, 100))
        
        # Generate new level
        spawn_points = self.world.generate_dungeon(level=next_level)
        spawn = spawn_points[0] if spawn_points else (30, 30)
        
        # Move party to spawn
        for i, char in enumerate(self.party):
            char.x = spawn[0] + (i % 2) * 1.5
            char.y = spawn[1] + (i // 2) * 1.5
            char.path = []
            char.target = None
        
        # Update world reference
        self.world.characters = self.party
        
        # Reset target
        self.target = None
        
        # Camera to new position
        self.camera.follow(self.selected_character.x, self.selected_character.y, instant=True)
        
        self.add_notification(f"Welcome to level {next_level}!", (180, 140, 90))
        self.audio.play('stairs')
    
    def _quick_save(self):
        """Quick save the game."""
        try:
            filename = save_game(self, slot=1)
            self.add_notification("Game saved! (F9 to load)", (100, 200, 100))
            self.audio.play('equip')
        except Exception as e:
            self.add_notification(f"Save failed: {e}", (200, 100, 100))
            self.audio.play('error')
    
    def _quick_load(self):
        """Quick load the game."""
        try:
            if load_game(self, slot=1):
                self.add_notification("Game loaded!", (100, 200, 100))
            else:
                self.add_notification("No save file found!", (200, 150, 100))
        except Exception as e:
            self.add_notification(f"Load failed: {e}", (200, 100, 100))
    
    def _enter_town(self):
        """Enter town from dungeon."""
        if self.selected_character:
            # Store dungeon position for return
            self._dungeon_pos = (self.selected_character.x, self.selected_character.y)
            self.in_town = True
            self.town_scene.enter(self.selected_character, self.party)
            self.add_notification("Entered Town", (100, 180, 255))
    
    def _exit_town(self):
        """Exit town back to dungeon."""
        if self.selected_character and hasattr(self, '_dungeon_pos'):
            self.selected_character.x, self.selected_character.y = self._dungeon_pos
        self.in_town = False
        self.town_scene.exit()
        self.add_notification("Returned to Dungeon", (180, 140, 100))
    
    def _update(self, dt):
        """Update game state."""
        # Update town if active
        if self.in_town:
            self.town_scene.update(dt, self.selected_character)
            return
        
        # Update world
        self.world.update(dt)
        
        # Auto-pickup gold and potions
        self._auto_pickup()
        
        # Process combat events for attack animations
        for event in self.world.combat_events:
            attacker = event['attacker']
            target = event['target']
            if event['type'] == 'spell':
                # Use proper spell effect based on spell_id
                spell_id = event.get('spell_id', 'magic_bolt')
                damage = event.get('damage', 0)
                delayed = event.get('delayed_damage', False)
                
                # Spawn spell effect - damage applied on projectile impact
                self.effects.spawn_spell(
                    spell_id,
                    attacker.x, attacker.y,
                    target.x, target.y,
                    damage=damage if delayed else 0,
                    damage_target=target if delayed else None,
                    caster=attacker
                )
            elif event['type'] == 'ranged':
                self.effects.spawn_ranged_attack(
                    attacker.x, attacker.y,
                    target.x, target.y
                )
            else:
                self.effects.spawn_melee_attack(
                    attacker.x, attacker.y,
                    target.x, target.y
                )
        
        # Update magic
        self.magic.update(dt)
        for char in self.party:
            if hasattr(char, 'spellbook'):
                char.spellbook.update(dt)
        
        # Update combat
        self._update_combat(dt)
        
        # Update visual effects
        self.effects.update(dt)
        
        # Update action bar cooldowns
        self.action_bar.update(dt)
        
        # Update portal button animation
        self.portal_button.update(dt)
        
        # Update camera to follow selected character
        if self.selected_character:
            self.camera.follow(self.selected_character.x, self.selected_character.y)
        
        self.camera.update(dt)
        
        # Update notifications
        self.notifications = [
            {**n, 'time': n['time'] - dt}
            for n in self.notifications
            if n['time'] > 0
        ]
        
        # Check for target death
        if self.target and getattr(self.target, 'health', 0) <= 0:
            self.add_notification(f"Defeated {self.target.name}!", (180, 140, 90))
            self.target = None
        
        # Check for party wipe (game over)
        alive_count = sum(1 for char in self.party if char.health > 0)
        if alive_count == 0:
            self.game_over = True
            self.game_over_timer = 0
        
        # Check for level ups
        self._check_level_ups()
        
        # Check if on stairs - show prompt
        if self.selected_character and self.world.is_on_stairs(self.selected_character):
            if not hasattr(self, '_stairs_prompt_shown') or not self._stairs_prompt_shown:
                self.add_notification("Press ENTER to descend stairs", (100, 200, 100))
                self._stairs_prompt_shown = True
        else:
            self._stairs_prompt_shown = False
    
    def _check_level_ups(self):
        """Check for and display level up notifications."""
        for char in self.party:
            if hasattr(char, 'pending_level_ups'):
                for level_up in char.pending_level_ups:
                    if level_up['skill'] == 'CHARACTER':
                        self.add_notification(
                            f"⬆ {char.name} is now level {level_up['new_level']}!",
                            (255, 215, 0)  # Gold
                        )
                        self.audio.play('levelup')
                    else:
                        self.add_notification(
                            f"⬆ {char.name}: {level_up['skill']} → {level_up['new_level']}",
                            (100, 200, 255)  # Light blue
                        )
                        self.audio.play('levelup')
                char.pending_level_ups = []
    
    def _update_combat(self, dt):
        """Update combat state."""
        for char in self.party:
            if char.target and char.target.health <= 0:
                char.target = None
                char.in_combat = False
                continue
            
            # Skip weapon attacks for mages - they only cast spells via AI
            if getattr(char, 'char_class', '') == 'mage':
                continue
            
            if char.target:
                dist = char.distance_to(char.target)
                if dist <= char.attack_range:
                    if char.can_attack():
                        damage = char.attack(char.target)
                        actual_damage = char.target.take_damage(damage, char)
                        
                        # Spawn attack animation and sound
                        weapon = char.equipment.get('main_hand')
                        if weapon:
                            if weapon.weapon_type == 'ranged':
                                self.effects.spawn_ranged_attack(
                                    char.x, char.y, 
                                    char.target.x, char.target.y
                                )
                                self.audio.play('arrow_shoot')
                            elif weapon.weapon_type == 'magic':
                                self.effects.spawn_spell(
                                    'magic_bolt', char.x, char.y,
                                    char.target.x, char.target.y
                                )
                                self.audio.play('spell_cast')
                            else:
                                self.effects.spawn_melee_attack(
                                    char.x, char.y,
                                    char.target.x, char.target.y
                                )
                                self.audio.play('sword_hit')
                        else:
                            # Unarmed melee
                            self.effects.spawn_melee_attack(
                                char.x, char.y,
                                char.target.x, char.target.y
                            )
                            self.audio.play('sword_hit')
                        
                        # Damage number
                        if actual_damage > 0:
                            self.add_notification(f"-{actual_damage}", (255, 100, 100))
                    
                    # Stop moving when in range
                    char.path = []
    
    def _render(self):
        """Render everything."""
        # Render town if active
        if self.in_town and self.selected_character:
            self.town_scene.render(self.screen, self.camera, self.selected_character)
            pygame.display.flip()
            return
        
        # Render world
        self.renderer.render_world(self.world, self.camera)
        
        # Render entities (sorted by Y for proper depth)
        all_entities = self.party + self.world.enemies
        all_entities.sort(key=lambda e: e.y)
        
        for entity in all_entities:
            if hasattr(entity, 'health') and entity.health <= 0:
                continue
            self.renderer.render_entity(entity, self.camera)
        
        # Render selection
        if self.selected_character:
            self.renderer.render_selection(self.selected_character, self.camera)
        
        # Render target indicator
        if self.target and self.target.health > 0:
            self.renderer.render_selection(self.target, self.camera)
        
        # Render path
        if self.selected_character and self.selected_character.path:
            self.renderer.render_path(
                [(self.selected_character.x, self.selected_character.y)] + 
                self.selected_character.path,
                self.camera
            )
        
        # Render dropped items
        self._render_dropped_items()
        
        # Render visual effects
        self.effects.render(self.screen, self.camera)
        
        # Render action bar
        if self.selected_character:
            self.action_bar.render(self.selected_character)
        
        # Render spell buttons (left side for mobile)
        self.spell_buttons.render(self.screen, self.party)
        
        # Render HUD
        game_state = {
            'party': self.party,
            'world': self.world,
            'target': self.target,
            'gold': self.gold,
            'notifications': self.notifications,
        }
        self.hud.render(game_state)
        
        # Inventory UI
        if self.inventory_ui.visible and self.selected_character:
            self.inventory_ui.render(self.selected_character)
        
        # Skill tree UI
        if self.skill_tree.visible and self.selected_character:
            self.skill_tree.render(self.selected_character)
        
        # Save/Load menu (renders on top of everything)
        self.save_menu.render(self.screen)
        
        # Portal button (only visible in dungeon, not in menus)
        if not self.in_town and not self.inventory_ui.visible and not self.skill_tree.visible:
            self.portal_button.render(self.screen)
        
        # Pause overlay
        if self.paused:
            self._render_pause_overlay()
        
        # Game over overlay
        if self.game_over:
            self._render_game_over()
    
    def _render_dropped_items(self):
        """Render items on the ground."""
        from ..engine.constants import RARITY_COLORS
        import math
        
        for item_data in self.world.items_on_ground:
            item = item_data['item']
            x, y = item_data['x'], item_data['y']
            
            screen_x, screen_y = self.camera.world_to_screen(x, y)
            
            # Skip if off screen
            if screen_x < -50 or screen_x > SCREEN_WIDTH + 50:
                continue
            if screen_y < -50 or screen_y > SCREEN_HEIGHT + 50:
                continue
            
            # Pulsing glow effect
            time = pygame.time.get_ticks() / 1000
            pulse = abs(math.sin(time * 2 + item.id)) * 0.5 + 0.5
            
            # Get rarity color
            rarity_color = RARITY_COLORS.get(item.rarity, (150, 150, 150))
            glow_color = tuple(int(c * pulse) for c in rarity_color)
            
            # Draw glow
            glow_size = int(12 * self.camera.zoom)
            glow_surf = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (*glow_color, 100), 
                             (glow_size, glow_size), glow_size)
            self.screen.blit(glow_surf, 
                           (screen_x - glow_size, screen_y - glow_size))
            
            # Draw item
            item_size = int(8 * self.camera.zoom)
            pygame.draw.circle(self.screen, rarity_color, 
                             (screen_x, screen_y), item_size)
            pygame.draw.circle(self.screen, (255, 255, 255), 
                             (screen_x, screen_y), item_size, 1)
    
    def _render_pause_overlay(self):
        """Render pause screen overlay."""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))
        self.screen.blit(overlay, (0, 0))
        
        font = pygame.font.Font(None, 72)
        text = font.render("PAUSED", True, (225, 215, 200))
        rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        self.screen.blit(text, rect)
        
        font_small = pygame.font.Font(None, 32)
        hint = font_small.render("Press SPACE or ESC to continue", True, (180, 170, 160))
        hint_rect = hint.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))
        self.screen.blit(hint, hint_rect)
    
    def _render_game_over(self):
        """Render game over screen."""
        # Dark red overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        
        # Fade in effect
        alpha = min(180, int(self.game_over_timer * 120))
        overlay.fill((40, 10, 10, alpha))
        self.screen.blit(overlay, (0, 0))
        
        if self.game_over_timer > 0.5:
            # Title
            font_large = pygame.font.Font(None, 96)
            title = font_large.render("YOU DIED", True, (180, 50, 50))
            title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 40))
            
            # Shadow
            shadow = font_large.render("YOU DIED", True, (60, 20, 20))
            self.screen.blit(shadow, (title_rect.x + 4, title_rect.y + 4))
            self.screen.blit(title, title_rect)
        
        if self.game_over_timer > 1.5:
            # Stats
            font = pygame.font.Font(None, 36)
            
            # Show final stats
            total_kills = sum(1 for _ in [])  # Could track this
            stats_text = f"Gold collected: {self.gold}"
            stats = font.render(stats_text, True, (200, 180, 160))
            stats_rect = stats.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30))
            self.screen.blit(stats, stats_rect)
        
        if self.game_over_timer > 2.0:
            # Restart prompt
            font_small = pygame.font.Font(None, 32)
            
            # Pulsing effect
            pulse = abs(((self.game_over_timer * 2) % 2) - 1)
            color_val = int(140 + pulse * 80)
            
            hint = font_small.render("Press R or Click to restart", True, (color_val, color_val - 20, color_val - 40))
            hint_rect = hint.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 80))
            self.screen.blit(hint, hint_rect)

