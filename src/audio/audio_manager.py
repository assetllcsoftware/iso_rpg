"""Audio manager - sound effects and music."""

import pygame
import os
import tempfile
from typing import Dict, Optional

from ..core.events import EventBus, Event, EventType
from .sound_generator import SoundGenerator
from .music_generator import MusicGenerator


class AudioManager:
    """Manages game audio - music and sound effects."""
    
    def __init__(self, event_bus: EventBus, assets_path: str = "assets/audio"):
        self.event_bus = event_bus
        self.assets_path = assets_path
        
        # Volume settings
        self.sfx_volume = 0.7
        self.music_volume = 0.4
        self.master_volume = 1.0
        
        # Mute states
        self.sfx_muted = False
        self.music_muted = False
        
        # Loaded sounds
        self.sounds: Dict[str, pygame.mixer.Sound] = {}
        
        # Music state
        self.current_music: Optional[str] = None
        self.music_files: Dict[str, str] = {}  # name -> temp file path
        
        # Generators
        self.sound_gen = SoundGenerator()
        self.music_gen = MusicGenerator()
        
        # Subscribe to events
        self._subscribe_events()
    
    def _subscribe_events(self):
        """Subscribe to game events for audio triggers."""
        # Combat events
        self.event_bus.subscribe(EventType.DAMAGE_DEALT, self._on_damage)
        self.event_bus.subscribe(EventType.ENTITY_DIED, self._on_death)
        
        # Magic events
        self.event_bus.subscribe(EventType.SPELL_CAST, self._on_spell_cast)
        
        # Pickup events
        self.event_bus.subscribe(EventType.ITEM_PICKED_UP, self._on_item_pickup)
        self.event_bus.subscribe(EventType.GOLD_CHANGED, self._on_gold_pickup)
        
        # Progression events
        self.event_bus.subscribe(EventType.LEVEL_UP, self._on_level_up)
        
        # Combat state (for music transitions)
        self.event_bus.subscribe(EventType.COMBAT_STARTED, self._on_combat_started)
        self.event_bus.subscribe(EventType.COMBAT_ENDED, self._on_combat_ended)
    
    def initialize(self):
        """Initialize audio system - load from files or generate."""
        # Ensure mixer is initialized
        if not pygame.mixer.get_init():
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        
        # Try to load pre-generated sounds, otherwise generate
        if not self._load_sounds_from_files():
            print("Pre-generated sounds not found, generating...")
            self._generate_sounds()
        
        # Try to load pre-generated music, otherwise generate
        if not self._load_music_from_files():
            print("Pre-generated music not found, generating...")
            self._generate_music()
    
    def _load_sounds_from_files(self) -> bool:
        """Try to load pre-generated sound effects from files."""
        sounds_dir = os.path.join(self.assets_path, "sounds")
        
        if not os.path.exists(sounds_dir):
            return False
        
        # List of all sound names we need
        sound_names = [
            # Hero abilities
            "whirlwind", "leap_strike", "crushing_blow", "shield_bash", "battle_cry",
            # Mage spells
            "fireball", "ice_shard", "lightning_bolt", "chain_lightning",
            "inferno", "blizzard", "meteor", "armageddon",
            "heal", "poison_cloud", "entangle", "revive",
            "group_heal", "regeneration", "summon_wolf", "sanctuary",
            # Combat sounds
            "hit_melee", "hit_crit", "hit_spell", "block",
            "sword_swing", "bow_shot", "arrow_hit", "death",
            # Enemy sounds
            "skeleton_rattle", "goblin_grunt", "spider_hiss",
            "zombie_groan", "orc_roar", "demon_growl",
            # UI sounds
            "pickup_item", "pickup_gold", "level_up",
            "menu_click", "menu_open", "equip_item",
            "potion_drink", "chest_open", "error", "footstep",
        ]
        
        # Check if all files exist
        for name in sound_names:
            filepath = os.path.join(sounds_dir, f"{name}.wav")
            if not os.path.exists(filepath):
                print(f"Missing sound file: {filepath}")
                return False
        
        # Load all sounds
        print("Loading pre-generated sound effects...")
        for name in sound_names:
            filepath = os.path.join(sounds_dir, f"{name}.wav")
            try:
                self.sounds[name] = pygame.mixer.Sound(filepath)
            except Exception as e:
                print(f"Error loading {name}: {e}")
                return False
        
        # Add aliases
        self.sounds["spell_fire"] = self.sounds["fireball"]
        self.sounds["spell_ice"] = self.sounds["ice_shard"]
        self.sounds["spell_lightning"] = self.sounds["lightning_bolt"]
        self.sounds["spell_heal"] = self.sounds["heal"]
        self.sounds["hit_ranged"] = self.sounds["arrow_hit"]
        
        print(f"Loaded {len(self.sounds)} sound effects from files")
        return True
    
    def _load_music_from_files(self) -> bool:
        """Try to load pre-generated music from files."""
        music_dir = os.path.join(self.assets_path, "music")
        
        if not os.path.exists(music_dir):
            return False
        
        music_names = ["dungeon_ambient", "combat_music", "menu_music"]
        
        # Check if all files exist
        for name in music_names:
            filepath = os.path.join(music_dir, f"{name}.wav")
            if not os.path.exists(filepath):
                print(f"Missing music file: {filepath}")
                return False
        
        # Store paths for music files
        print("Loading pre-generated music...")
        for name in music_names:
            filepath = os.path.join(music_dir, f"{name}.wav")
            self.music_files[name] = filepath
        
        print(f"Loaded {len(self.music_files)} music tracks from files")
        return True
    
    def _generate_sounds(self):
        """Generate all game sound effects."""
        print("Generating sound effects...")
        
        # Hero abilities
        self.sounds["whirlwind"] = self.sound_gen.whirlwind()
        self.sounds["leap_strike"] = self.sound_gen.leap_strike()
        self.sounds["crushing_blow"] = self.sound_gen.crushing_blow()
        self.sounds["shield_bash"] = self.sound_gen.shield_bash()
        self.sounds["battle_cry"] = self.sound_gen.battle_cry()
        
        # Mage spells
        self.sounds["fireball"] = self.sound_gen.fireball()
        self.sounds["ice_shard"] = self.sound_gen.ice_shard()
        self.sounds["lightning_bolt"] = self.sound_gen.lightning_bolt()
        self.sounds["chain_lightning"] = self.sound_gen.chain_lightning()
        self.sounds["inferno"] = self.sound_gen.inferno()
        self.sounds["blizzard"] = self.sound_gen.blizzard()
        self.sounds["meteor"] = self.sound_gen.meteor()
        self.sounds["armageddon"] = self.sound_gen.armageddon()
        self.sounds["heal"] = self.sound_gen.heal()
        self.sounds["poison_cloud"] = self.sound_gen.poison_cloud()
        self.sounds["entangle"] = self.sound_gen.entangle()
        self.sounds["revive"] = self.sound_gen.revive()
        self.sounds["group_heal"] = self.sound_gen.group_heal()
        self.sounds["regeneration"] = self.sound_gen.regeneration()
        self.sounds["summon_wolf"] = self.sound_gen.summon_wolf()
        self.sounds["sanctuary"] = self.sound_gen.sanctuary()
        
        # Combat sounds
        self.sounds["hit_melee"] = self.sound_gen.hit_melee()
        self.sounds["hit_crit"] = self.sound_gen.hit_crit()
        self.sounds["hit_spell"] = self.sound_gen.hit_spell()
        self.sounds["block"] = self.sound_gen.block()
        self.sounds["sword_swing"] = self.sound_gen.sword_swing()
        self.sounds["bow_shot"] = self.sound_gen.bow_shot()
        self.sounds["arrow_hit"] = self.sound_gen.arrow_hit()
        self.sounds["death"] = self.sound_gen.death()
        
        # Enemy sounds
        self.sounds["skeleton_rattle"] = self.sound_gen.skeleton_rattle()
        self.sounds["goblin_grunt"] = self.sound_gen.goblin_grunt()
        self.sounds["spider_hiss"] = self.sound_gen.spider_hiss()
        self.sounds["zombie_groan"] = self.sound_gen.zombie_groan()
        self.sounds["orc_roar"] = self.sound_gen.orc_roar()
        self.sounds["demon_growl"] = self.sound_gen.demon_growl()
        
        # UI sounds
        self.sounds["pickup_item"] = self.sound_gen.pickup_item()
        self.sounds["pickup_gold"] = self.sound_gen.pickup_gold()
        self.sounds["level_up"] = self.sound_gen.level_up()
        self.sounds["menu_click"] = self.sound_gen.menu_click()
        self.sounds["menu_open"] = self.sound_gen.menu_open()
        self.sounds["equip_item"] = self.sound_gen.equip_item()
        self.sounds["potion_drink"] = self.sound_gen.potion_drink()
        self.sounds["chest_open"] = self.sound_gen.chest_open()
        self.sounds["error"] = self.sound_gen.error()
        self.sounds["footstep"] = self.sound_gen.footstep()
        
        # Aliases for compatibility
        self.sounds["spell_fire"] = self.sounds["fireball"]
        self.sounds["spell_ice"] = self.sounds["ice_shard"]
        self.sounds["spell_lightning"] = self.sounds["lightning_bolt"]
        self.sounds["spell_heal"] = self.sounds["heal"]
        self.sounds["hit_ranged"] = self.sounds["arrow_hit"]
        
        print(f"Generated {len(self.sounds)} sound effects")
    
    def _generate_music(self):
        """Generate background music tracks."""
        print("Generating music...")
        
        # Create temp directory for music files
        temp_dir = tempfile.gettempdir()
        
        # Dungeon ambient (60 seconds, loops)
        dungeon_samples = self.music_gen.dungeon_ambient(60.0)
        dungeon_path = os.path.join(temp_dir, "ml_siege_dungeon.wav")
        self.music_gen.save_as_wav(dungeon_samples, dungeon_path)
        self.music_files["dungeon_ambient"] = dungeon_path
        
        # Combat music (30 seconds, loops)
        combat_samples = self.music_gen.combat_music(30.0)
        combat_path = os.path.join(temp_dir, "ml_siege_combat.wav")
        self.music_gen.save_as_wav(combat_samples, combat_path)
        self.music_files["combat_music"] = combat_path
        
        # Menu music (45 seconds, loops)
        menu_samples = self.music_gen.menu_music(45.0)
        menu_path = os.path.join(temp_dir, "ml_siege_menu.wav")
        self.music_gen.save_as_wav(menu_samples, menu_path)
        self.music_files["menu_music"] = menu_path
        
        print(f"Generated {len(self.music_files)} music tracks")
    
    def play_sound(self, sound_name: str, volume_mult: float = 1.0):
        """Play a sound effect."""
        if self.sfx_muted:
            return
        
        if sound_name not in self.sounds:
            return
        
        sound = self.sounds[sound_name]
        if sound:
            final_volume = self.sfx_volume * self.master_volume * volume_mult
            sound.set_volume(final_volume)
            sound.play()
    
    def play_music(self, music_name: str, loop: bool = True, fade_ms: int = 1000):
        """Play background music with optional crossfade."""
        if self.music_muted:
            return
        
        if music_name not in self.music_files:
            print(f"Music not found: {music_name}")
            return
        
        if self.current_music == music_name:
            return  # Already playing
        
        # Fade out current music
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.fadeout(fade_ms)
        
        # Load and play new music
        try:
            pygame.mixer.music.load(self.music_files[music_name])
            pygame.mixer.music.set_volume(self.music_volume * self.master_volume)
            loops = -1 if loop else 0
            pygame.mixer.music.play(loops, fade_ms=fade_ms)
            self.current_music = music_name
        except Exception as e:
            print(f"Error playing music: {e}")
    
    def stop_music(self, fade_ms: int = 500):
        """Stop background music with fadeout."""
        pygame.mixer.music.fadeout(fade_ms)
        self.current_music = None
    
    def pause_music(self):
        """Pause background music."""
        pygame.mixer.music.pause()
    
    def resume_music(self):
        """Resume paused music."""
        pygame.mixer.music.unpause()
    
    def set_sfx_volume(self, volume: float):
        """Set sound effects volume (0.0 to 1.0)."""
        self.sfx_volume = max(0.0, min(1.0, volume))
    
    def set_music_volume(self, volume: float):
        """Set music volume (0.0 to 1.0)."""
        self.music_volume = max(0.0, min(1.0, volume))
        pygame.mixer.music.set_volume(self.music_volume * self.master_volume)
    
    def set_master_volume(self, volume: float):
        """Set master volume (0.0 to 1.0)."""
        self.master_volume = max(0.0, min(1.0, volume))
        pygame.mixer.music.set_volume(self.music_volume * self.master_volume)
    
    def toggle_sfx_mute(self):
        """Toggle sound effects mute."""
        self.sfx_muted = not self.sfx_muted
    
    def toggle_music_mute(self):
        """Toggle music mute."""
        self.music_muted = not self.music_muted
        if self.music_muted:
            self.pause_music()
        else:
            self.resume_music()
    
    # =========================================================================
    # EVENT HANDLERS
    # =========================================================================
    
    def _on_damage(self, event: Event):
        """Handle damage event - play hit sounds."""
        damage_type = event.data.get("damage_type", "physical")
        is_crit = event.data.get("is_crit", False)
        weapon_type = event.data.get("weapon_type", "melee")
        
        if is_crit:
            self.play_sound("hit_crit")
        elif damage_type == "physical":
            if weapon_type == "ranged":
                self.play_sound("arrow_hit")
            else:
                self.play_sound("hit_melee")
        else:
            self.play_sound("hit_spell")
    
    def _on_death(self, event: Event):
        """Handle death event."""
        entity_type = event.data.get("entity_type", "enemy")
        enemy_type = event.data.get("enemy_type", "")
        
        # Play death sound
        self.play_sound("death")
        
        # Play enemy-specific sound
        if "skeleton" in enemy_type:
            self.play_sound("skeleton_rattle")
        elif "goblin" in enemy_type:
            self.play_sound("goblin_grunt")
        elif "spider" in enemy_type:
            self.play_sound("spider_hiss")
        elif "zombie" in enemy_type:
            self.play_sound("zombie_groan")
        elif "orc" in enemy_type:
            self.play_sound("orc_roar")
        elif "demon" in enemy_type:
            self.play_sound("demon_growl")
    
    def _on_spell_cast(self, event: Event):
        """Handle spell cast event - play spell sounds."""
        spell_id = event.data.get("spell_id", "")
        
        # Try exact match first
        if spell_id in self.sounds:
            self.play_sound(spell_id)
            return
        
        # Fallback to category sounds
        if "fire" in spell_id or spell_id in ["fireball", "inferno", "meteor", "armageddon"]:
            self.play_sound("fireball")
        elif "ice" in spell_id or "frost" in spell_id or "blizzard" in spell_id:
            self.play_sound("ice_shard")
        elif "lightning" in spell_id:
            self.play_sound("lightning_bolt")
        elif "heal" in spell_id or "regen" in spell_id:
            self.play_sound("heal")
        elif "poison" in spell_id:
            self.play_sound("poison_cloud")
        elif "whirlwind" in spell_id or "spin" in spell_id:
            self.play_sound("whirlwind")
        elif "leap" in spell_id or "jump" in spell_id:
            self.play_sound("leap_strike")
        elif "crush" in spell_id or "heavy" in spell_id:
            self.play_sound("crushing_blow")
        elif "bash" in spell_id or "shield" in spell_id:
            self.play_sound("shield_bash")
        elif "cry" in spell_id or "shout" in spell_id:
            self.play_sound("battle_cry")
        elif "summon" in spell_id:
            self.play_sound("summon_wolf")
        elif "entangle" in spell_id or "root" in spell_id:
            self.play_sound("entangle")
        elif "revive" in spell_id:
            self.play_sound("revive")
        elif "sanctuary" in spell_id:
            self.play_sound("sanctuary")
    
    def _on_item_pickup(self, event: Event):
        """Handle item pickup."""
        item_type = event.data.get("item_type", "")
        
        if "potion" in item_type:
            self.play_sound("potion_drink")
        else:
            self.play_sound("pickup_item")
    
    def _on_gold_pickup(self, event: Event):
        """Handle gold pickup."""
        amount = event.data.get("amount", 0)
        if amount > 0:
            self.play_sound("pickup_gold")
    
    def _on_level_up(self, event: Event):
        """Handle level up."""
        self.play_sound("level_up")
    
    def _on_combat_started(self, event: Event):
        """Switch to combat music."""
        self.play_music("combat_music", fade_ms=500)
    
    def _on_combat_ended(self, event: Event):
        """Switch back to ambient music."""
        self.play_music("dungeon_ambient", fade_ms=2000)
    
    # =========================================================================
    # DIRECT SOUND TRIGGERS (for non-event based sounds)
    # =========================================================================
    
    def play_footstep(self):
        """Play footstep sound (called from movement)."""
        self.play_sound("footstep", 0.3)
    
    def play_menu_click(self):
        """Play menu click sound."""
        self.play_sound("menu_click")
    
    def play_menu_open(self):
        """Play menu open sound."""
        self.play_sound("menu_open")
    
    def play_equip(self):
        """Play equipment change sound."""
        self.play_sound("equip_item")
    
    def play_chest_open(self):
        """Play chest opening sound."""
        self.play_sound("chest_open")
    
    def play_error(self):
        """Play error/can't do that sound."""
        self.play_sound("error")
    
    def play_block(self):
        """Play shield block sound."""
        self.play_sound("block")
    
    def play_sword_swing(self):
        """Play basic attack swing sound."""
        self.play_sound("sword_swing")
    
    def play_bow_shot(self):
        """Play bow shooting sound."""
        self.play_sound("bow_shot")
    
    def play_enemy_sound(self, enemy_type: str):
        """Play enemy-specific sound."""
        if "skeleton" in enemy_type:
            self.play_sound("skeleton_rattle")
        elif "goblin" in enemy_type:
            self.play_sound("goblin_grunt")
        elif "spider" in enemy_type:
            self.play_sound("spider_hiss")
        elif "zombie" in enemy_type:
            self.play_sound("zombie_groan")
        elif "orc" in enemy_type:
            self.play_sound("orc_roar")
        elif "demon" in enemy_type:
            self.play_sound("demon_growl")
