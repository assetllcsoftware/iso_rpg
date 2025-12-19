"""Sound effects system using pygame's built-in synth."""

import pygame
import math
import random

# Initialize mixer
pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)


class SoundGenerator:
    """Generate simple sound effects programmatically."""
    
    @staticmethod
    def generate_tone(frequency, duration, volume=0.3, wave='square'):
        """Generate a simple tone."""
        sample_rate = 22050
        n_samples = int(sample_rate * duration)
        
        # Create buffer
        buf = bytearray()
        for i in range(n_samples):
            t = i / sample_rate
            
            if wave == 'sine':
                value = math.sin(2 * math.pi * frequency * t)
            elif wave == 'square':
                value = 1 if math.sin(2 * math.pi * frequency * t) > 0 else -1
            elif wave == 'saw':
                value = 2 * (t * frequency - math.floor(t * frequency + 0.5))
            else:
                value = math.sin(2 * math.pi * frequency * t)
            
            # Apply envelope (fade out)
            envelope = 1 - (i / n_samples) ** 0.5
            value *= envelope * volume
            
            # Convert to 16-bit signed
            sample = int(max(-32767, min(32767, value * 32767)))
            # Stereo - same value for both channels
            buf.extend(sample.to_bytes(2, 'little', signed=True))
            buf.extend(sample.to_bytes(2, 'little', signed=True))
        
        # Create sound
        sound = pygame.mixer.Sound(buffer=bytes(buf))
        return sound
    
    @staticmethod
    def generate_noise(duration, volume=0.2):
        """Generate white noise burst."""
        sample_rate = 22050
        n_samples = int(sample_rate * duration)
        
        buf = bytearray()
        for i in range(n_samples):
            # White noise
            value = random.uniform(-1, 1)
            
            # Envelope
            envelope = 1 - (i / n_samples)
            value *= envelope * volume
            
            sample = int(max(-32767, min(32767, value * 32767)))
            buf.extend(sample.to_bytes(2, 'little', signed=True))
            buf.extend(sample.to_bytes(2, 'little', signed=True))
        
        sound = pygame.mixer.Sound(buffer=bytes(buf))
        return sound


class MusicGenerator:
    """Generate procedural background music with melodies."""
    
    def __init__(self):
        self.sample_rate = 22050
        self.playing = False
        self.music_channel = None
        
        # Musical scales (frequency ratios)
        # Minor scale for dark dungeon feel
        self.minor_scale = [1, 1.122, 1.189, 1.335, 1.498, 1.587, 1.782, 2]
        # Pentatonic for melodies
        self.pentatonic = [1, 1.122, 1.335, 1.498, 1.782, 2]
        
    def _note_freq(self, base, scale_degree, octave=0):
        """Get frequency for a scale degree."""
        idx = scale_degree % len(self.minor_scale)
        octave_mult = 2 ** (octave + scale_degree // len(self.minor_scale))
        return base * self.minor_scale[idx] * octave_mult
    
    def _synth_note(self, t, freq, wave='triangle'):
        """Synthesize a single note."""
        if wave == 'sine':
            return math.sin(2 * math.pi * freq * t)
        elif wave == 'triangle':
            phase = (t * freq) % 1
            return 4 * abs(phase - 0.5) - 1
        elif wave == 'square':
            return 1 if math.sin(2 * math.pi * freq * t) > 0 else -1
        elif wave == 'saw':
            return 2 * ((t * freq) % 1) - 1
        return math.sin(2 * math.pi * freq * t)
        
    def generate_dungeon_ambience(self, duration=32):
        """Generate dark melodic dungeon music."""
        n_samples = int(self.sample_rate * duration)
        buf = bytearray()
        
        base_freq = 110  # A2
        bpm = 70
        beat_duration = 60 / bpm
        
        # Chord progression (i - VI - III - VII in minor)
        chord_prog = [
            [0, 2, 4],      # Am
            [5, 0, 2],      # F
            [2, 4, 6],      # C
            [6, 1, 3],      # G
        ]
        
        # Melody pattern (scale degrees, -1 = rest)
        melody = [0, 2, 4, 2, 0, -1, 4, 5, 4, 2, 0, -1, 2, 4, 5, 7,
                  5, 4, 2, 0, -1, 2, 0, -1, 4, 2, 0, 2, 4, 5, 4, 2]
        
        # Arpeggio pattern
        arp_pattern = [0, 1, 2, 1]
        
        for i in range(n_samples):
            t = i / self.sample_rate
            
            # Current beat and bar
            beat = t / beat_duration
            bar = int(beat / 4) % 4
            beat_in_bar = beat % 4
            sixteenth = int((beat * 4) % 16)
            
            current_chord = chord_prog[bar]
            
            # === BASS (root note, octave down) ===
            bass_freq = self._note_freq(base_freq / 2, current_chord[0])
            bass = self._synth_note(t, bass_freq, 'triangle') * 0.25
            # Pulsing envelope
            bass *= 0.6 + 0.4 * (1 - (beat_in_bar % 1))
            
            # === PAD (chord tones) ===
            pad = 0
            for j, degree in enumerate(current_chord):
                freq = self._note_freq(base_freq, degree)
                pad += self._synth_note(t, freq, 'sine') * 0.12
                # Add slight detune for richness
                pad += self._synth_note(t, freq * 1.003, 'sine') * 0.06
            # Slow swell
            pad *= 0.7 + 0.3 * math.sin(t * 0.5)
            
            # === ARPEGGIO ===
            arp_idx = arp_pattern[sixteenth % 4]
            arp_degree = current_chord[arp_idx % len(current_chord)]
            arp_freq = self._note_freq(base_freq * 2, arp_degree)
            arp = self._synth_note(t, arp_freq, 'triangle') * 0.15
            # Quick decay envelope
            arp_phase = (beat * 4) % 1
            arp *= max(0, 1 - arp_phase * 2)
            
            # === MELODY (every half beat) ===
            melody_idx = int(beat * 2) % len(melody)
            melody_note = melody[melody_idx]
            melody_val = 0
            if melody_note >= 0:
                mel_freq = self._note_freq(base_freq * 2, melody_note)
                melody_val = self._synth_note(t, mel_freq, 'sine') * 0.2
                # Decay
                mel_phase = (beat * 2) % 1
                melody_val *= max(0, 1 - mel_phase * 1.5)
            
            # === ATMOSPHERE ===
            # Subtle high shimmer
            shimmer = self._synth_note(t, base_freq * 8, 'sine') * 0.03
            shimmer *= 0.5 + 0.5 * math.sin(t * 2)
            
            # Combine all layers
            value = bass + pad + arp + melody_val + shimmer
            
            # Master envelope - fade in/out
            fade_samples = self.sample_rate * 2
            if i < fade_samples:
                value *= i / fade_samples
            elif i > n_samples - fade_samples:
                value *= (n_samples - i) / fade_samples
            
            # Soft limiting
            value = math.tanh(value * 1.2) * 0.8
            
            sample = int(value * 32767)
            buf.extend(sample.to_bytes(2, 'little', signed=True))
            buf.extend(sample.to_bytes(2, 'little', signed=True))
        
        return pygame.mixer.Sound(buffer=bytes(buf))
    
    def generate_combat_music(self, duration=24):
        """Generate intense combat music."""
        n_samples = int(self.sample_rate * duration)
        buf = bytearray()
        
        base_freq = 110  # A2
        bpm = 140  # Fast tempo
        beat_duration = 60 / bpm
        
        # More aggressive chord progression
        chord_prog = [
            [0, 2, 4],      # Am
            [0, 2, 4],      # Am
            [5, 0, 2],      # F
            [6, 1, 3],      # G
        ]
        
        for i in range(n_samples):
            t = i / self.sample_rate
            
            beat = t / beat_duration
            bar = int(beat / 4) % 4
            beat_in_bar = beat % 4
            eighth = int((beat * 2) % 8)
            
            current_chord = chord_prog[bar]
            
            # === DRIVING BASS ===
            bass_freq = self._note_freq(base_freq / 2, current_chord[0])
            bass = self._synth_note(t, bass_freq, 'saw') * 0.3
            # Pump on every eighth note
            bass *= 0.4 + 0.6 * (1 - (beat * 2 % 1) ** 0.5)
            
            # === POWER CHORDS ===
            power = 0
            root = self._note_freq(base_freq, current_chord[0])
            fifth = root * 1.5
            power += self._synth_note(t, root, 'square') * 0.15
            power += self._synth_note(t, fifth, 'square') * 0.12
            # Hit on beats 1 and 3
            if beat_in_bar % 2 < 0.5:
                power *= 1.5
            
            # === RHYTHMIC STABS ===
            stab = 0
            if eighth in [0, 3, 4, 6]:
                for degree in current_chord:
                    freq = self._note_freq(base_freq * 2, degree)
                    stab += self._synth_note(t, freq, 'square') * 0.08
                stab *= max(0, 1 - (beat * 2 % 1) * 3)
            
            # === KICK DRUM (noise burst) ===
            kick = 0
            kick_phase = beat % 1
            if kick_phase < 0.1:
                kick_freq = 60 * (1 - kick_phase * 5)
                kick = self._synth_note(t, kick_freq, 'sine') * 0.4
                kick *= 1 - kick_phase * 10
            
            # === SNARE (noise) on 2 and 4 ===
            snare = 0
            if int(beat_in_bar) in [1, 3]:
                snare_phase = beat_in_bar % 1
                if snare_phase < 0.15:
                    snare = (random.random() * 2 - 1) * 0.25
                    snare *= 1 - snare_phase * 6
            
            # Combine
            value = bass + power + stab + kick + snare
            
            # Fade
            fade_samples = self.sample_rate
            if i < fade_samples:
                value *= i / fade_samples
            elif i > n_samples - fade_samples:
                value *= (n_samples - i) / fade_samples
            
            value = math.tanh(value * 1.3) * 0.85
            
            sample = int(value * 32767)
            buf.extend(sample.to_bytes(2, 'little', signed=True))
            buf.extend(sample.to_bytes(2, 'little', signed=True))
        
        return pygame.mixer.Sound(buffer=bytes(buf))


class AudioManager:
    """Manages game sound effects."""
    
    def __init__(self):
        self.enabled = True
        self.volume = 0.5
        self.music_volume = 0.6  # Louder music
        self.sounds = {}
        self._generate_sounds()
        
        # Music
        self.music_gen = MusicGenerator()
        self.current_music = None
        self.music_channel = None
        self._generate_music()
    
    def _generate_sounds(self):
        """Pre-generate all sound effects."""
        gen = SoundGenerator()
        
        # Combat sounds
        self.sounds['sword_hit'] = self._create_sword_sound()
        self.sounds['arrow_shoot'] = self._create_arrow_sound()
        self.sounds['spell_cast'] = self._create_spell_sound()
        self.sounds['fireball'] = self._create_fireball_sound()
        self.sounds['heal'] = self._create_heal_sound()
        
        # UI sounds
        self.sounds['pickup'] = self._create_pickup_sound()
        self.sounds['equip'] = self._create_equip_sound()
        self.sounds['levelup'] = self._create_levelup_sound()
        self.sounds['error'] = self._create_error_sound()
        
        # Other
        self.sounds['hit_taken'] = self._create_hit_taken_sound()
        self.sounds['death'] = self._create_death_sound()
        self.sounds['stairs'] = self._create_stairs_sound()
    
    def _create_sword_sound(self):
        """Sword slash sound."""
        gen = SoundGenerator()
        # Quick descending tone + noise
        sounds = []
        sounds.append(gen.generate_tone(800, 0.05, 0.2, 'saw'))
        sounds.append(gen.generate_tone(400, 0.08, 0.15, 'saw'))
        sounds.append(gen.generate_noise(0.1, 0.15))
        return sounds[0]  # Simplified
    
    def _create_arrow_sound(self):
        """Arrow whoosh sound."""
        gen = SoundGenerator()
        return gen.generate_tone(1200, 0.1, 0.15, 'sine')
    
    def _create_spell_sound(self):
        """Generic spell cast sound."""
        gen = SoundGenerator()
        return gen.generate_tone(600, 0.15, 0.2, 'sine')
    
    def _create_fireball_sound(self):
        """Fireball cast sound."""
        gen = SoundGenerator()
        return gen.generate_noise(0.2, 0.25)
    
    def _create_heal_sound(self):
        """Healing sound - ascending tones."""
        gen = SoundGenerator()
        return gen.generate_tone(800, 0.2, 0.2, 'sine')
    
    def _create_pickup_sound(self):
        """Item pickup sound."""
        gen = SoundGenerator()
        return gen.generate_tone(1000, 0.08, 0.2, 'square')
    
    def _create_equip_sound(self):
        """Equipment sound."""
        gen = SoundGenerator()
        return gen.generate_tone(500, 0.1, 0.15, 'square')
    
    def _create_levelup_sound(self):
        """Level up fanfare."""
        gen = SoundGenerator()
        return gen.generate_tone(1200, 0.3, 0.25, 'square')
    
    def _create_error_sound(self):
        """Error/failure sound."""
        gen = SoundGenerator()
        return gen.generate_tone(200, 0.15, 0.2, 'square')
    
    def _create_hit_taken_sound(self):
        """Taking damage sound."""
        gen = SoundGenerator()
        return gen.generate_noise(0.1, 0.2)
    
    def _create_death_sound(self):
        """Death sound."""
        gen = SoundGenerator()
        return gen.generate_tone(150, 0.4, 0.3, 'saw')
    
    def _create_stairs_sound(self):
        """Descending stairs sound."""
        gen = SoundGenerator()
        return gen.generate_tone(400, 0.2, 0.2, 'sine')
    
    def play(self, sound_name):
        """Play a sound effect."""
        if not self.enabled:
            return
        
        sound = self.sounds.get(sound_name)
        if sound:
            sound.set_volume(self.volume)
            sound.play()
    
    def set_volume(self, volume):
        """Set master volume (0.0 - 1.0)."""
        self.volume = max(0.0, min(1.0, volume))
    
    def toggle(self):
        """Toggle sound on/off."""
        self.enabled = not self.enabled
        if not self.enabled:
            self.stop_music()
        return self.enabled
    
    def _generate_music(self):
        """Pre-generate music tracks."""
        print("[Audio] Generating background music...")
        self.dungeon_music = self.music_gen.generate_dungeon_ambience(30)
        self.combat_music = self.music_gen.generate_combat_music(20)
        print("[Audio] Music ready!")
    
    def play_music(self, track='dungeon'):
        """Start playing background music."""
        if not self.enabled:
            return
        
        if track == 'dungeon':
            music = self.dungeon_music
        elif track == 'combat':
            music = self.combat_music
        else:
            music = self.dungeon_music
        
        music.set_volume(self.music_volume)
        self.music_channel = music.play(loops=-1)  # Loop forever
        self.current_music = track
    
    def stop_music(self):
        """Stop background music."""
        if self.music_channel:
            self.music_channel.stop()
            self.music_channel = None
            self.current_music = None
    
    def set_music_volume(self, volume):
        """Set music volume (0.0 - 1.0)."""
        self.music_volume = max(0.0, min(1.0, volume))
        if self.music_channel:
            # Update currently playing
            pass  # pygame doesn't easily support this
    
    def toggle_music(self):
        """Toggle music on/off."""
        if self.current_music:
            self.stop_music()
        else:
            self.play_music('dungeon')


# Global audio manager
audio = AudioManager()

