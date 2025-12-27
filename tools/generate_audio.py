#!/usr/bin/env python3
"""Pre-generate all game audio files for faster loading."""

import os
import sys
import wave
import struct

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame
import numpy as np

# Initialize pygame mixer
pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

from src.audio.sound_generator import SoundGenerator
from src.audio.music_generator import MusicGenerator


def save_sound_as_wav(sound: pygame.mixer.Sound, filepath: str):
    """Save a pygame Sound to a WAV file."""
    # Get raw samples from sound
    samples = pygame.sndarray.array(sound)
    
    with wave.open(filepath, 'w') as wav:
        wav.setnchannels(2)  # Stereo
        wav.setsampwidth(2)  # 16-bit
        wav.setframerate(44100)
        wav.writeframes(samples.tobytes())


def main():
    sounds_dir = "assets/audio/sounds"
    music_dir = "assets/audio/music"
    
    os.makedirs(sounds_dir, exist_ok=True)
    os.makedirs(music_dir, exist_ok=True)
    
    sound_gen = SoundGenerator()
    music_gen = MusicGenerator()
    
    # =========================================================================
    # GENERATE SOUND EFFECTS
    # =========================================================================
    
    sounds = {
        # Hero abilities
        "whirlwind": sound_gen.whirlwind,
        "leap_strike": sound_gen.leap_strike,
        "crushing_blow": sound_gen.crushing_blow,
        "shield_bash": sound_gen.shield_bash,
        "battle_cry": sound_gen.battle_cry,
        
        # Mage spells
        "fireball": sound_gen.fireball,
        "ice_shard": sound_gen.ice_shard,
        "lightning_bolt": sound_gen.lightning_bolt,
        "chain_lightning": sound_gen.chain_lightning,
        "inferno": sound_gen.inferno,
        "blizzard": sound_gen.blizzard,
        "meteor": sound_gen.meteor,
        "armageddon": sound_gen.armageddon,
        "heal": sound_gen.heal,
        "poison_cloud": sound_gen.poison_cloud,
        "entangle": sound_gen.entangle,
        "revive": sound_gen.revive,
        "group_heal": sound_gen.group_heal,
        "regeneration": sound_gen.regeneration,
        "summon_wolf": sound_gen.summon_wolf,
        "sanctuary": sound_gen.sanctuary,
        
        # Combat sounds
        "hit_melee": sound_gen.hit_melee,
        "hit_crit": sound_gen.hit_crit,
        "hit_spell": sound_gen.hit_spell,
        "block": sound_gen.block,
        "sword_swing": sound_gen.sword_swing,
        "bow_shot": sound_gen.bow_shot,
        "arrow_hit": sound_gen.arrow_hit,
        "death": sound_gen.death,
        
        # Enemy sounds
        "skeleton_rattle": sound_gen.skeleton_rattle,
        "goblin_grunt": sound_gen.goblin_grunt,
        "spider_hiss": sound_gen.spider_hiss,
        "zombie_groan": sound_gen.zombie_groan,
        "orc_roar": sound_gen.orc_roar,
        "demon_growl": sound_gen.demon_growl,
        
        # UI sounds
        "pickup_item": sound_gen.pickup_item,
        "pickup_gold": sound_gen.pickup_gold,
        "level_up": sound_gen.level_up,
        "menu_click": sound_gen.menu_click,
        "menu_open": sound_gen.menu_open,
        "equip_item": sound_gen.equip_item,
        "potion_drink": sound_gen.potion_drink,
        "chest_open": sound_gen.chest_open,
        "error": sound_gen.error,
        "footstep": sound_gen.footstep,
    }
    
    print(f"Generating {len(sounds)} sound effects...")
    for name, generator in sounds.items():
        filepath = os.path.join(sounds_dir, f"{name}.wav")
        print(f"  {name}...", end=" ", flush=True)
        try:
            sound = generator()
            save_sound_as_wav(sound, filepath)
            print("OK")
        except Exception as e:
            print(f"ERROR: {e}")
    
    # =========================================================================
    # GENERATE MUSIC
    # =========================================================================
    
    music_tracks = {
        "dungeon_ambient": (music_gen.dungeon_ambient, 60.0),
        "combat_music": (music_gen.combat_music, 30.0),
        "menu_music": (music_gen.menu_music, 45.0),
    }
    
    print(f"\nGenerating {len(music_tracks)} music tracks...")
    for name, (generator, duration) in music_tracks.items():
        filepath = os.path.join(music_dir, f"{name}.wav")
        print(f"  {name} ({duration}s)...", end=" ", flush=True)
        try:
            samples = generator(duration)
            music_gen.save_as_wav(samples, filepath)
            print("OK")
        except Exception as e:
            print(f"ERROR: {e}")
    
    print("\nDone! Audio files saved to assets/audio/")
    print(f"  Sounds: {sounds_dir}/")
    print(f"  Music:  {music_dir}/")


if __name__ == "__main__":
    main()

