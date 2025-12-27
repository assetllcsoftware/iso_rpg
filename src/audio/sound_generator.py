"""Procedural sound generator - creates game sounds programmatically."""

import pygame
import numpy as np
import math
from typing import Tuple


def generate_sound(samples: np.ndarray, sample_rate: int = 44100) -> pygame.mixer.Sound:
    """Convert numpy array to pygame Sound."""
    # Ensure samples are in correct format (16-bit signed)
    samples = np.clip(samples * 32767, -32768, 32767).astype(np.int16)
    # Make stereo
    stereo = np.column_stack((samples, samples))
    return pygame.mixer.Sound(buffer=stereo.tobytes())


def sine_wave(freq: float, duration: float, sample_rate: int = 44100) -> np.ndarray:
    """Generate a sine wave."""
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    return np.sin(2 * np.pi * freq * t)


def square_wave(freq: float, duration: float, sample_rate: int = 44100) -> np.ndarray:
    """Generate a square wave."""
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    return np.sign(np.sin(2 * np.pi * freq * t))


def sawtooth_wave(freq: float, duration: float, sample_rate: int = 44100) -> np.ndarray:
    """Generate a sawtooth wave."""
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    return 2 * (t * freq - np.floor(0.5 + t * freq))


def noise(duration: float, sample_rate: int = 44100) -> np.ndarray:
    """Generate white noise."""
    return np.random.uniform(-1, 1, int(sample_rate * duration))


def envelope(samples: np.ndarray, attack: float = 0.01, decay: float = 0.1, 
             sustain: float = 0.7, release: float = 0.2, sample_rate: int = 44100) -> np.ndarray:
    """Apply ADSR envelope to samples."""
    total_samples = len(samples)
    attack_samples = int(attack * sample_rate)
    decay_samples = int(decay * sample_rate)
    release_samples = int(release * sample_rate)
    sustain_samples = total_samples - attack_samples - decay_samples - release_samples
    
    if sustain_samples < 0:
        # Adjust for very short sounds
        sustain_samples = 0
        scale = total_samples / (attack_samples + decay_samples + release_samples)
        attack_samples = int(attack_samples * scale)
        decay_samples = int(decay_samples * scale)
        release_samples = total_samples - attack_samples - decay_samples
    
    env = np.concatenate([
        np.linspace(0, 1, attack_samples),
        np.linspace(1, sustain, decay_samples),
        np.full(sustain_samples, sustain),
        np.linspace(sustain, 0, release_samples)
    ])
    
    # Pad or trim to match samples length
    if len(env) < total_samples:
        env = np.pad(env, (0, total_samples - len(env)))
    else:
        env = env[:total_samples]
    
    return samples * env


def lowpass_filter(samples: np.ndarray, cutoff: float = 0.1) -> np.ndarray:
    """Simple lowpass filter."""
    alpha = cutoff
    filtered = np.zeros_like(samples)
    filtered[0] = samples[0]
    for i in range(1, len(samples)):
        filtered[i] = alpha * samples[i] + (1 - alpha) * filtered[i-1]
    return filtered


def highpass_filter(samples: np.ndarray, cutoff: float = 0.9) -> np.ndarray:
    """Simple highpass filter."""
    return samples - lowpass_filter(samples, 1 - cutoff)


def pitch_sweep(start_freq: float, end_freq: float, duration: float, 
                wave_type: str = 'sine', sample_rate: int = 44100) -> np.ndarray:
    """Generate a pitch sweep."""
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    freq = np.linspace(start_freq, end_freq, len(t))
    phase = 2 * np.pi * np.cumsum(freq) / sample_rate
    
    if wave_type == 'sine':
        return np.sin(phase)
    elif wave_type == 'square':
        return np.sign(np.sin(phase))
    elif wave_type == 'sawtooth':
        return 2 * (phase / (2 * np.pi) - np.floor(0.5 + phase / (2 * np.pi)))
    return np.sin(phase)


class SoundGenerator:
    """Generates all game sound effects procedurally."""
    
    def __init__(self, sample_rate: int = 44100):
        self.sample_rate = sample_rate
    
    # =========================================================================
    # HERO ABILITIES
    # =========================================================================
    
    def whirlwind(self) -> pygame.mixer.Sound:
        """Spinning blade whoosh - 3 rotation swooshes."""
        duration = 1.5
        samples = np.zeros(int(self.sample_rate * duration))
        
        # 3 swoosh cycles
        for i in range(6):
            t = i * 0.25
            # Whoosh is filtered noise with pitch variation
            whoosh_len = 0.2
            whoosh_samples = int(self.sample_rate * whoosh_len)
            start_idx = int(t * self.sample_rate)
            if start_idx + whoosh_samples > len(samples):
                break
            
            whoosh = noise(whoosh_len, self.sample_rate)
            whoosh = lowpass_filter(whoosh, 0.15)
            # Add some tone
            whoosh += sine_wave(200 + i * 20, whoosh_len, self.sample_rate) * 0.3
            whoosh = envelope(whoosh, 0.02, 0.05, 0.5, 0.08)
            samples[start_idx:start_idx + len(whoosh)] += whoosh * 0.5
        
        # Add blade ring undertone
        blade = sine_wave(800, duration, self.sample_rate) * 0.1
        blade += sine_wave(1200, duration, self.sample_rate) * 0.05
        blade = envelope(blade, 0.1, 0.2, 0.3, 0.5)
        samples += blade
        
        return generate_sound(samples * 0.6, self.sample_rate)
    
    def leap_strike(self) -> pygame.mixer.Sound:
        """Jump + heavy ground impact."""
        duration = 0.8
        samples = np.zeros(int(self.sample_rate * duration))
        
        # Jump whoosh (rising)
        jump = pitch_sweep(100, 400, 0.3, 'sine', self.sample_rate)
        jump += noise(0.3, self.sample_rate) * 0.3
        jump = lowpass_filter(jump, 0.2)
        jump = envelope(jump, 0.05, 0.1, 0.4, 0.1)
        samples[:len(jump)] = jump * 0.5
        
        # Impact (at 0.5s)
        impact_start = int(0.5 * self.sample_rate)
        impact = pitch_sweep(200, 40, 0.3, 'sine', self.sample_rate)
        impact += noise(0.3, self.sample_rate) * 0.5
        impact = lowpass_filter(impact, 0.1)
        impact = envelope(impact, 0.01, 0.05, 0.2, 0.2)
        samples[impact_start:impact_start + len(impact)] += impact * 0.8
        
        # Shockwave rumble
        rumble = sine_wave(50, 0.3, self.sample_rate)  # Shorter to fit
        rumble = envelope(rumble, 0.01, 0.1, 0.3, 0.3)
        end_idx = min(impact_start + len(rumble), len(samples))
        samples[impact_start:end_idx] += rumble[:end_idx - impact_start] * 0.4
        
        return generate_sound(samples * 0.7, self.sample_rate)
    
    def crushing_blow(self) -> pygame.mixer.Sound:
        """Heavy slam + ground crack."""
        duration = 0.6
        samples = np.zeros(int(self.sample_rate * duration))
        
        # Wind up whoosh
        windup = pitch_sweep(300, 100, 0.2, 'sine', self.sample_rate)
        windup = envelope(windup, 0.05, 0.1, 0.5, 0.05)
        samples[:len(windup)] = windup * 0.3
        
        # Heavy impact
        impact_start = int(0.25 * self.sample_rate)
        impact = pitch_sweep(150, 30, 0.35, 'sine', self.sample_rate)
        impact += noise(0.35, self.sample_rate) * 0.6
        impact = lowpass_filter(impact, 0.08)
        impact = envelope(impact, 0.005, 0.05, 0.3, 0.3)
        samples[impact_start:impact_start + len(impact)] += impact * 0.9
        
        # Crack sounds (short high transients)
        for i in range(3):
            crack_start = impact_start + int((0.02 + i * 0.03) * self.sample_rate)
            crack = noise(0.02, self.sample_rate)
            crack = highpass_filter(crack, 0.7)
            crack = envelope(crack, 0.001, 0.01, 0.1, 0.01)
            if crack_start + len(crack) < len(samples):
                samples[crack_start:crack_start + len(crack)] += crack * 0.4
        
        return generate_sound(samples * 0.8, self.sample_rate)
    
    def shield_bash(self) -> pygame.mixer.Sound:
        """Metal clang + impact."""
        duration = 0.4
        samples = np.zeros(int(self.sample_rate * duration))
        
        # Metal clang (multiple harmonics)
        clang = np.zeros(int(self.sample_rate * 0.3))
        for freq in [800, 1200, 1600, 2400]:
            clang += sine_wave(freq, 0.3, self.sample_rate) * (1.0 / freq * 400)
        clang = envelope(clang, 0.001, 0.02, 0.3, 0.2)
        samples[:len(clang)] = clang * 0.5
        
        # Body impact thud
        thud = pitch_sweep(200, 60, 0.15, 'sine', self.sample_rate)
        thud += noise(0.15, self.sample_rate) * 0.3
        thud = lowpass_filter(thud, 0.1)
        thud = envelope(thud, 0.005, 0.02, 0.3, 0.1)
        samples[:len(thud)] += thud * 0.6
        
        return generate_sound(samples * 0.7, self.sample_rate)
    
    def battle_cry(self) -> pygame.mixer.Sound:
        """Warrior shout."""
        duration = 0.8
        samples = np.zeros(int(self.sample_rate * duration))
        
        # Base vocal tone
        voice = sine_wave(150, duration, self.sample_rate)
        voice += sine_wave(300, duration, self.sample_rate) * 0.5
        voice += sine_wave(450, duration, self.sample_rate) * 0.25
        
        # Add formants (vowel sounds)
        voice += sine_wave(800, duration, self.sample_rate) * 0.2
        voice += sine_wave(1200, duration, self.sample_rate) * 0.1
        
        # Modulate for vibrato
        t = np.linspace(0, duration, int(self.sample_rate * duration), False)
        vibrato = 1 + 0.1 * np.sin(2 * np.pi * 6 * t)
        voice *= vibrato
        
        voice = envelope(voice, 0.05, 0.1, 0.7, 0.3)
        samples[:len(voice)] = voice
        
        return generate_sound(samples * 0.5, self.sample_rate)
    
    # =========================================================================
    # MAGE SPELLS
    # =========================================================================
    
    def fireball(self) -> pygame.mixer.Sound:
        """Fire launch + woosh."""
        duration = 0.5
        samples = np.zeros(int(self.sample_rate * duration))
        
        # Fire launch
        launch = noise(0.15, self.sample_rate)
        launch = lowpass_filter(launch, 0.15)
        launch += pitch_sweep(200, 400, 0.15, 'sine', self.sample_rate) * 0.3
        launch = envelope(launch, 0.01, 0.05, 0.5, 0.05)
        samples[:len(launch)] = launch * 0.6
        
        # Fire woosh trail
        trail = noise(0.4, self.sample_rate)
        trail = lowpass_filter(trail, 0.1)
        trail = envelope(trail, 0.05, 0.1, 0.4, 0.2)
        samples[int(0.1 * self.sample_rate):int(0.1 * self.sample_rate) + len(trail)] += trail * 0.4
        
        return generate_sound(samples * 0.6, self.sample_rate)
    
    def ice_shard(self) -> pygame.mixer.Sound:
        """Crystalline shatter."""
        duration = 0.4
        samples = np.zeros(int(self.sample_rate * duration))
        
        # High crystalline tones
        crystal = np.zeros(int(self.sample_rate * 0.3))
        for freq in [2000, 2500, 3000, 3500]:
            crystal += sine_wave(freq, 0.3, self.sample_rate) * 0.2
        crystal = envelope(crystal, 0.005, 0.05, 0.4, 0.2)
        samples[:len(crystal)] = crystal
        
        # Ice crack
        crack = noise(0.1, self.sample_rate)
        crack = highpass_filter(crack, 0.6)
        crack = envelope(crack, 0.001, 0.02, 0.2, 0.05)
        samples[:len(crack)] += crack * 0.5
        
        return generate_sound(samples * 0.5, self.sample_rate)
    
    def lightning_bolt(self) -> pygame.mixer.Sound:
        """Electric zap."""
        duration = 0.3
        samples = np.zeros(int(self.sample_rate * duration))
        
        # Electric crackle
        zap = noise(duration, self.sample_rate)
        # Modulate with random on/off
        t = np.linspace(0, duration, int(self.sample_rate * duration), False)
        modulation = (np.sin(2 * np.pi * 50 * t) > 0).astype(float)
        modulation *= (np.sin(2 * np.pi * 120 * t) > 0.3).astype(float)
        zap *= modulation
        zap = highpass_filter(zap, 0.5)
        zap = envelope(zap, 0.001, 0.02, 0.5, 0.1)
        samples[:len(zap)] = zap * 0.7
        
        # Bass thump
        thump = sine_wave(80, 0.1, self.sample_rate)
        thump = envelope(thump, 0.001, 0.02, 0.3, 0.05)
        samples[:len(thump)] += thump * 0.4
        
        return generate_sound(samples * 0.6, self.sample_rate)
    
    def chain_lightning(self) -> pygame.mixer.Sound:
        """Multiple electric arcs."""
        duration = 0.6
        samples = np.zeros(int(self.sample_rate * duration))
        
        # Multiple zaps
        for i in range(4):
            zap_start = int(i * 0.12 * self.sample_rate)
            zap = noise(0.15, self.sample_rate)
            t = np.linspace(0, 0.15, int(self.sample_rate * 0.15), False)
            mod = (np.sin(2 * np.pi * (60 + i * 20) * t) > 0).astype(float)
            zap *= mod
            zap = highpass_filter(zap, 0.5)
            zap = envelope(zap, 0.001, 0.02, 0.4, 0.08)
            if zap_start + len(zap) < len(samples):
                samples[zap_start:zap_start + len(zap)] += zap * (0.7 - i * 0.1)
        
        return generate_sound(samples * 0.6, self.sample_rate)
    
    def inferno(self) -> pygame.mixer.Sound:
        """Roaring flames."""
        duration = 1.0
        samples = np.zeros(int(self.sample_rate * duration))
        
        # Fire roar (filtered noise with modulation)
        fire = noise(duration, self.sample_rate)
        fire = lowpass_filter(fire, 0.1)
        
        # Modulate for flickering
        t = np.linspace(0, duration, len(fire), False)
        mod = 0.7 + 0.3 * np.sin(2 * np.pi * 8 * t) * np.sin(2 * np.pi * 3 * t)
        fire *= mod
        
        fire = envelope(fire, 0.1, 0.2, 0.6, 0.3)
        samples[:len(fire)] = fire * 0.7
        
        # Add bass rumble
        rumble = sine_wave(60, duration, self.sample_rate)
        rumble = envelope(rumble, 0.1, 0.2, 0.5, 0.3)
        samples += rumble * 0.3
        
        return generate_sound(samples * 0.6, self.sample_rate)
    
    def blizzard(self) -> pygame.mixer.Sound:
        """Howling wind + ice."""
        duration = 1.2
        samples = np.zeros(int(self.sample_rate * duration))
        
        # Wind howl
        wind = noise(duration, self.sample_rate)
        wind = lowpass_filter(wind, 0.05)
        
        # Modulate for gusting
        t = np.linspace(0, duration, len(wind), False)
        gust = 0.5 + 0.5 * np.sin(2 * np.pi * 2 * t)
        wind *= gust
        wind = envelope(wind, 0.2, 0.2, 0.6, 0.3)
        samples[:len(wind)] = wind * 0.5
        
        # Ice crystals (periodic high pings)
        for i in range(8):
            ping_start = int((0.1 + i * 0.12) * self.sample_rate)
            ping = sine_wave(2500 + i * 200, 0.08, self.sample_rate)
            ping = envelope(ping, 0.001, 0.02, 0.3, 0.05)
            if ping_start + len(ping) < len(samples):
                samples[ping_start:ping_start + len(ping)] += ping * 0.15
        
        return generate_sound(samples * 0.5, self.sample_rate)
    
    def meteor(self) -> pygame.mixer.Sound:
        """Rumble + massive explosion."""
        duration = 1.5
        samples = np.zeros(int(self.sample_rate * duration))
        
        # Incoming rumble (rising pitch)
        rumble = pitch_sweep(50, 200, 0.8, 'sine', self.sample_rate)
        rumble += noise(0.8, self.sample_rate) * 0.3
        rumble = lowpass_filter(rumble, 0.1)
        rumble = envelope(rumble, 0.1, 0.2, 0.6, 0.1)
        samples[:len(rumble)] = rumble * 0.5
        
        # Massive explosion
        exp_start = int(0.8 * self.sample_rate)
        explosion = noise(0.7, self.sample_rate)
        explosion = lowpass_filter(explosion, 0.08)
        explosion += pitch_sweep(100, 20, 0.7, 'sine', self.sample_rate) * 0.5
        explosion = envelope(explosion, 0.005, 0.1, 0.4, 0.4)
        samples[exp_start:exp_start + len(explosion)] += explosion * 0.9
        
        return generate_sound(samples * 0.7, self.sample_rate)
    
    def armageddon(self) -> pygame.mixer.Sound:
        """Apocalyptic rumble with multiple impacts."""
        duration = 2.0
        samples = np.zeros(int(self.sample_rate * duration))
        
        # Continuous deep rumble
        rumble = sine_wave(40, duration, self.sample_rate)
        rumble += sine_wave(60, duration, self.sample_rate) * 0.5
        rumble += noise(duration, self.sample_rate) * 0.2
        rumble = lowpass_filter(rumble, 0.05)
        rumble = envelope(rumble, 0.2, 0.3, 0.7, 0.4)
        samples[:len(rumble)] = rumble * 0.4
        
        # Multiple impacts
        for i in range(6):
            imp_start = int((0.2 + i * 0.25) * self.sample_rate)
            impact = noise(0.3, self.sample_rate)
            impact = lowpass_filter(impact, 0.1)
            impact = envelope(impact, 0.005, 0.05, 0.3, 0.2)
            if imp_start + len(impact) < len(samples):
                samples[imp_start:imp_start + len(impact)] += impact * (0.6 + 0.1 * i)
        
        return generate_sound(samples * 0.6, self.sample_rate)
    
    def heal(self) -> pygame.mixer.Sound:
        """Gentle healing chime."""
        duration = 0.6
        samples = np.zeros(int(self.sample_rate * duration))
        
        # Ascending chimes
        for i, freq in enumerate([523, 659, 784, 1047]):  # C5, E5, G5, C6
            chime_start = int(i * 0.1 * self.sample_rate)
            chime = sine_wave(freq, 0.4, self.sample_rate)
            chime += sine_wave(freq * 2, 0.4, self.sample_rate) * 0.3
            chime = envelope(chime, 0.01, 0.05, 0.4, 0.3)
            if chime_start + len(chime) < len(samples):
                samples[chime_start:chime_start + len(chime)] += chime * 0.3
        
        return generate_sound(samples * 0.5, self.sample_rate)
    
    def poison_cloud(self) -> pygame.mixer.Sound:
        """Hissing gas."""
        duration = 0.6
        samples = np.zeros(int(self.sample_rate * duration))
        
        # Hissing noise
        hiss = noise(duration, self.sample_rate)
        hiss = highpass_filter(hiss, 0.6)
        hiss = lowpass_filter(hiss, 0.3)
        
        # Bubble modulation
        t = np.linspace(0, duration, len(hiss), False)
        bubbles = 0.7 + 0.3 * np.sin(2 * np.pi * 15 * t)
        hiss *= bubbles
        hiss = envelope(hiss, 0.1, 0.1, 0.6, 0.2)
        samples[:len(hiss)] = hiss
        
        return generate_sound(samples * 0.4, self.sample_rate)
    
    def entangle(self) -> pygame.mixer.Sound:
        """Vine/root growth."""
        duration = 0.5
        samples = np.zeros(int(self.sample_rate * duration))
        
        # Creaking/growing sounds
        for i in range(4):
            creak_start = int(i * 0.1 * self.sample_rate)
            creak = pitch_sweep(100 + i * 50, 200 + i * 30, 0.15, 'sawtooth', self.sample_rate)
            creak = lowpass_filter(creak, 0.15)
            creak = envelope(creak, 0.02, 0.05, 0.4, 0.08)
            if creak_start + len(creak) < len(samples):
                samples[creak_start:creak_start + len(creak)] += creak * 0.4
        
        return generate_sound(samples * 0.5, self.sample_rate)
    
    def revive(self) -> pygame.mixer.Sound:
        """Resurrection chime - ascending magical tones."""
        duration = 1.0
        samples = np.zeros(int(self.sample_rate * duration))
        
        # Mystical ascending scale
        freqs = [262, 330, 392, 523, 659, 784]  # C4 to G5
        for i, freq in enumerate(freqs):
            tone_start = int(i * 0.12 * self.sample_rate)
            tone = sine_wave(freq, 0.5, self.sample_rate)
            tone += sine_wave(freq * 2, 0.5, self.sample_rate) * 0.4
            tone += sine_wave(freq * 3, 0.5, self.sample_rate) * 0.2
            tone = envelope(tone, 0.02, 0.1, 0.5, 0.3)
            if tone_start + len(tone) < len(samples):
                samples[tone_start:tone_start + len(tone)] += tone * 0.25
        
        return generate_sound(samples * 0.5, self.sample_rate)
    
    def group_heal(self) -> pygame.mixer.Sound:
        """Larger heal effect."""
        duration = 0.8
        samples = np.zeros(int(self.sample_rate * duration))
        
        # Multiple chime layers
        for j in range(2):
            for i, freq in enumerate([523, 659, 784, 1047]):
                chime_start = int((j * 0.2 + i * 0.08) * self.sample_rate)
                chime = sine_wave(freq, 0.5, self.sample_rate)
                chime += sine_wave(freq * 2, 0.5, self.sample_rate) * 0.3
                chime = envelope(chime, 0.01, 0.05, 0.4, 0.35)
                if chime_start + len(chime) < len(samples):
                    samples[chime_start:chime_start + len(chime)] += chime * 0.2
        
        return generate_sound(samples * 0.5, self.sample_rate)
    
    def regeneration(self) -> pygame.mixer.Sound:
        """Soft glowing sound."""
        duration = 0.5
        samples = np.zeros(int(self.sample_rate * duration))
        
        # Soft pulsing tone
        tone = sine_wave(440, duration, self.sample_rate)
        tone += sine_wave(880, duration, self.sample_rate) * 0.3
        
        # Pulse modulation
        t = np.linspace(0, duration, len(tone), False)
        pulse = 0.5 + 0.5 * np.sin(2 * np.pi * 4 * t)
        tone *= pulse
        tone = envelope(tone, 0.1, 0.1, 0.6, 0.2)
        samples[:len(tone)] = tone
        
        return generate_sound(samples * 0.3, self.sample_rate)
    
    def summon_wolf(self) -> pygame.mixer.Sound:
        """Wolf howl."""
        duration = 1.0
        samples = np.zeros(int(self.sample_rate * duration))
        
        # Howl with pitch variation
        t = np.linspace(0, duration, int(self.sample_rate * duration), False)
        # Pitch curve: rise then fall
        pitch_curve = 200 + 150 * np.sin(np.pi * t / duration)
        
        phase = 2 * np.pi * np.cumsum(pitch_curve) / self.sample_rate
        howl = np.sin(phase)
        howl += np.sin(phase * 2) * 0.3
        howl += np.sin(phase * 3) * 0.15
        
        # Add slight vibrato
        vibrato = 1 + 0.05 * np.sin(2 * np.pi * 8 * t)
        howl *= vibrato
        
        howl = envelope(howl, 0.1, 0.2, 0.5, 0.3)
        samples[:len(howl)] = howl
        
        return generate_sound(samples * 0.5, self.sample_rate)
    
    def sanctuary(self) -> pygame.mixer.Sound:
        """Divine bell/chime."""
        duration = 1.2
        samples = np.zeros(int(self.sample_rate * duration))
        
        # Bell harmonics
        bell = np.zeros(int(self.sample_rate * duration))
        for i, (freq, amp) in enumerate([(440, 1.0), (880, 0.6), (1320, 0.3), 
                                          (1760, 0.2), (2200, 0.1)]):
            partial = sine_wave(freq, duration, self.sample_rate) * amp
            bell += partial
        
        bell = envelope(bell, 0.01, 0.1, 0.4, 0.7)
        samples[:len(bell)] = bell * 0.4
        
        return generate_sound(samples * 0.5, self.sample_rate)
    
    # =========================================================================
    # COMBAT SOUNDS
    # =========================================================================
    
    def hit_melee(self) -> pygame.mixer.Sound:
        """Sword/weapon impact."""
        duration = 0.15
        samples = np.zeros(int(self.sample_rate * duration))
        
        # Impact thud
        impact = noise(duration, self.sample_rate)
        impact = lowpass_filter(impact, 0.15)
        impact += pitch_sweep(400, 100, duration, 'sine', self.sample_rate) * 0.3
        impact = envelope(impact, 0.001, 0.02, 0.3, 0.1)
        samples[:len(impact)] = impact
        
        return generate_sound(samples * 0.7, self.sample_rate)
    
    def hit_crit(self) -> pygame.mixer.Sound:
        """Critical hit - louder, more impact."""
        duration = 0.25
        samples = np.zeros(int(self.sample_rate * duration))
        
        # Heavy impact
        impact = noise(duration, self.sample_rate)
        impact = lowpass_filter(impact, 0.12)
        impact += pitch_sweep(500, 80, duration, 'sine', self.sample_rate) * 0.5
        impact = envelope(impact, 0.001, 0.03, 0.4, 0.15)
        samples[:len(impact)] = impact * 0.9
        
        # Add ring
        ring = sine_wave(1000, 0.15, self.sample_rate)
        ring = envelope(ring, 0.001, 0.02, 0.2, 0.1)
        samples[:len(ring)] += ring * 0.3
        
        return generate_sound(samples * 0.8, self.sample_rate)
    
    def hit_spell(self) -> pygame.mixer.Sound:
        """Magic impact."""
        duration = 0.2
        samples = np.zeros(int(self.sample_rate * duration))
        
        # Magical burst
        burst = noise(duration, self.sample_rate)
        burst = lowpass_filter(burst, 0.2)
        burst += sine_wave(600, duration, self.sample_rate) * 0.3
        burst = envelope(burst, 0.001, 0.03, 0.3, 0.1)
        samples[:len(burst)] = burst
        
        return generate_sound(samples * 0.6, self.sample_rate)
    
    def block(self) -> pygame.mixer.Sound:
        """Shield block."""
        duration = 0.2
        samples = np.zeros(int(self.sample_rate * duration))
        
        # Metal clang
        clang = np.zeros(int(self.sample_rate * duration))
        for freq in [600, 900, 1200]:
            clang += sine_wave(freq, duration, self.sample_rate) * 0.3
        clang = envelope(clang, 0.001, 0.02, 0.3, 0.15)
        samples[:len(clang)] = clang
        
        return generate_sound(samples * 0.6, self.sample_rate)
    
    def sword_swing(self) -> pygame.mixer.Sound:
        """Basic attack whoosh."""
        duration = 0.15
        samples = np.zeros(int(self.sample_rate * duration))
        
        # Whoosh
        whoosh = noise(duration, self.sample_rate)
        whoosh = lowpass_filter(whoosh, 0.2)
        whoosh = envelope(whoosh, 0.01, 0.03, 0.4, 0.06)
        samples[:len(whoosh)] = whoosh
        
        return generate_sound(samples * 0.4, self.sample_rate)
    
    def bow_shot(self) -> pygame.mixer.Sound:
        """Arrow release."""
        duration = 0.2
        samples = np.zeros(int(self.sample_rate * duration))
        
        # String twang
        twang = pitch_sweep(400, 200, 0.1, 'sine', self.sample_rate)
        twang = envelope(twang, 0.001, 0.02, 0.3, 0.07)
        samples[:len(twang)] = twang * 0.5
        
        # Arrow whoosh
        whoosh = noise(0.15, self.sample_rate)
        whoosh = lowpass_filter(whoosh, 0.25)
        whoosh = envelope(whoosh, 0.02, 0.03, 0.4, 0.1)
        samples[int(0.05 * self.sample_rate):int(0.05 * self.sample_rate) + len(whoosh)] += whoosh * 0.4
        
        return generate_sound(samples * 0.5, self.sample_rate)
    
    def arrow_hit(self) -> pygame.mixer.Sound:
        """Arrow impact."""
        duration = 0.1
        samples = np.zeros(int(self.sample_rate * duration))
        
        # Thud
        impact = noise(duration, self.sample_rate)
        impact = lowpass_filter(impact, 0.2)
        impact = envelope(impact, 0.001, 0.02, 0.3, 0.05)
        samples[:len(impact)] = impact
        
        return generate_sound(samples * 0.5, self.sample_rate)
    
    def death(self) -> pygame.mixer.Sound:
        """Death sound."""
        duration = 0.5
        samples = np.zeros(int(self.sample_rate * duration))
        
        # Falling tone
        fall = pitch_sweep(300, 80, duration, 'sine', self.sample_rate)
        fall = envelope(fall, 0.01, 0.1, 0.5, 0.3)
        samples[:len(fall)] = fall * 0.5
        
        # Impact
        impact = noise(0.2, self.sample_rate)
        impact = lowpass_filter(impact, 0.1)
        impact = envelope(impact, 0.01, 0.05, 0.3, 0.1)
        samples[int(0.3 * self.sample_rate):int(0.3 * self.sample_rate) + len(impact)] += impact * 0.4
        
        return generate_sound(samples * 0.6, self.sample_rate)
    
    # =========================================================================
    # ENEMY SOUNDS
    # =========================================================================
    
    def skeleton_rattle(self) -> pygame.mixer.Sound:
        """Bone rattling."""
        duration = 0.3
        samples = np.zeros(int(self.sample_rate * duration))
        
        # Multiple clicks/rattles
        for i in range(5):
            click_start = int((i * 0.05 + np.random.uniform(0, 0.02)) * self.sample_rate)
            click = noise(0.02, self.sample_rate)
            click = highpass_filter(click, 0.7)
            click = envelope(click, 0.001, 0.005, 0.3, 0.01)
            if click_start + len(click) < len(samples):
                samples[click_start:click_start + len(click)] += click * 0.5
        
        return generate_sound(samples * 0.5, self.sample_rate)
    
    def goblin_grunt(self) -> pygame.mixer.Sound:
        """Goblin attack grunt."""
        duration = 0.25
        samples = np.zeros(int(self.sample_rate * duration))
        
        # Harsh vocal
        grunt = sawtooth_wave(120, duration, self.sample_rate)
        grunt += sawtooth_wave(180, duration, self.sample_rate) * 0.5
        grunt = lowpass_filter(grunt, 0.15)
        grunt = envelope(grunt, 0.02, 0.05, 0.5, 0.1)
        samples[:len(grunt)] = grunt
        
        return generate_sound(samples * 0.4, self.sample_rate)
    
    def spider_hiss(self) -> pygame.mixer.Sound:
        """Spider hissing."""
        duration = 0.3
        samples = np.zeros(int(self.sample_rate * duration))
        
        # Hiss
        hiss = noise(duration, self.sample_rate)
        hiss = highpass_filter(hiss, 0.5)
        hiss = lowpass_filter(hiss, 0.4)
        hiss = envelope(hiss, 0.02, 0.05, 0.6, 0.1)
        samples[:len(hiss)] = hiss
        
        return generate_sound(samples * 0.4, self.sample_rate)
    
    def zombie_groan(self) -> pygame.mixer.Sound:
        """Undead moan."""
        duration = 0.6
        samples = np.zeros(int(self.sample_rate * duration))
        
        # Low moan
        moan = sine_wave(80, duration, self.sample_rate)
        moan += sine_wave(120, duration, self.sample_rate) * 0.5
        moan += noise(duration, self.sample_rate) * 0.2
        moan = lowpass_filter(moan, 0.1)
        
        # Wavering
        t = np.linspace(0, duration, len(moan), False)
        waver = 1 + 0.2 * np.sin(2 * np.pi * 3 * t)
        moan *= waver
        
        moan = envelope(moan, 0.1, 0.1, 0.5, 0.2)
        samples[:len(moan)] = moan
        
        return generate_sound(samples * 0.4, self.sample_rate)
    
    def orc_roar(self) -> pygame.mixer.Sound:
        """Orc attack roar."""
        duration = 0.4
        samples = np.zeros(int(self.sample_rate * duration))
        
        # Deep roar
        roar = sawtooth_wave(100, duration, self.sample_rate)
        roar += sawtooth_wave(150, duration, self.sample_rate) * 0.6
        roar += noise(duration, self.sample_rate) * 0.3
        roar = lowpass_filter(roar, 0.12)
        roar = envelope(roar, 0.03, 0.1, 0.5, 0.2)
        samples[:len(roar)] = roar
        
        return generate_sound(samples * 0.5, self.sample_rate)
    
    def demon_growl(self) -> pygame.mixer.Sound:
        """Demon growling."""
        duration = 0.5
        samples = np.zeros(int(self.sample_rate * duration))
        
        # Deep demonic growl
        growl = sawtooth_wave(60, duration, self.sample_rate)
        growl += sawtooth_wave(90, duration, self.sample_rate) * 0.5
        growl += noise(duration, self.sample_rate) * 0.4
        growl = lowpass_filter(growl, 0.08)
        
        # Modulation for menace
        t = np.linspace(0, duration, len(growl), False)
        mod = 0.7 + 0.3 * np.sin(2 * np.pi * 5 * t)
        growl *= mod
        
        growl = envelope(growl, 0.05, 0.1, 0.6, 0.2)
        samples[:len(growl)] = growl
        
        return generate_sound(samples * 0.5, self.sample_rate)
    
    # =========================================================================
    # UI / PICKUP SOUNDS
    # =========================================================================
    
    def pickup_item(self) -> pygame.mixer.Sound:
        """Item pickup sound."""
        duration = 0.2
        samples = np.zeros(int(self.sample_rate * duration))
        
        # Short ascending tones
        for i, freq in enumerate([400, 600, 800]):
            tone_start = int(i * 0.04 * self.sample_rate)
            tone = sine_wave(freq, 0.1, self.sample_rate)
            tone = envelope(tone, 0.005, 0.02, 0.4, 0.05)
            if tone_start + len(tone) < len(samples):
                samples[tone_start:tone_start + len(tone)] += tone * 0.4
        
        return generate_sound(samples * 0.5, self.sample_rate)
    
    def pickup_gold(self) -> pygame.mixer.Sound:
        """Coin jingle."""
        duration = 0.3
        samples = np.zeros(int(self.sample_rate * duration))
        
        # Multiple coin clinks
        for i in range(4):
            clink_start = int((i * 0.05 + np.random.uniform(0, 0.02)) * self.sample_rate)
            freq = 2000 + np.random.uniform(-200, 200)
            clink = sine_wave(freq, 0.08, self.sample_rate)
            clink += sine_wave(freq * 1.5, 0.08, self.sample_rate) * 0.3
            clink = envelope(clink, 0.001, 0.01, 0.3, 0.05)
            if clink_start + len(clink) < len(samples):
                samples[clink_start:clink_start + len(clink)] += clink * 0.3
        
        return generate_sound(samples * 0.5, self.sample_rate)
    
    def level_up(self) -> pygame.mixer.Sound:
        """Level up fanfare."""
        duration = 1.0
        samples = np.zeros(int(self.sample_rate * duration))
        
        # Ascending fanfare
        notes = [(523, 0.15), (659, 0.15), (784, 0.15), (1047, 0.4)]
        t = 0
        for freq, dur in notes:
            start = int(t * self.sample_rate)
            note = sine_wave(freq, dur, self.sample_rate)
            note += sine_wave(freq * 2, dur, self.sample_rate) * 0.4
            note += sine_wave(freq * 3, dur, self.sample_rate) * 0.2
            note = envelope(note, 0.01, 0.05, 0.6, 0.3)
            if start + len(note) < len(samples):
                samples[start:start + len(note)] += note * 0.4
            t += dur * 0.8
        
        return generate_sound(samples * 0.6, self.sample_rate)
    
    def menu_click(self) -> pygame.mixer.Sound:
        """Button click."""
        duration = 0.05
        samples = sine_wave(800, duration, self.sample_rate)
        samples = envelope(samples, 0.001, 0.01, 0.5, 0.02)
        return generate_sound(samples * 0.3, self.sample_rate)
    
    def menu_open(self) -> pygame.mixer.Sound:
        """Menu open whoosh."""
        duration = 0.15
        samples = pitch_sweep(200, 600, duration, 'sine', self.sample_rate)
        samples = envelope(samples, 0.01, 0.03, 0.5, 0.05)
        return generate_sound(samples * 0.3, self.sample_rate)
    
    def equip_item(self) -> pygame.mixer.Sound:
        """Gear equip sound."""
        duration = 0.2
        samples = np.zeros(int(self.sample_rate * duration))
        
        # Metal clink
        clink = sine_wave(1200, 0.1, self.sample_rate)
        clink += sine_wave(1800, 0.1, self.sample_rate) * 0.4
        clink = envelope(clink, 0.001, 0.02, 0.4, 0.06)
        samples[:len(clink)] = clink
        
        return generate_sound(samples * 0.4, self.sample_rate)
    
    def potion_drink(self) -> pygame.mixer.Sound:
        """Gulp/drink sound."""
        duration = 0.3
        samples = np.zeros(int(self.sample_rate * duration))
        
        # Gulping sounds
        for i in range(3):
            gulp_start = int(i * 0.08 * self.sample_rate)
            gulp = pitch_sweep(200, 100, 0.08, 'sine', self.sample_rate)
            gulp = lowpass_filter(gulp, 0.2)
            gulp = envelope(gulp, 0.01, 0.02, 0.5, 0.03)
            if gulp_start + len(gulp) < len(samples):
                samples[gulp_start:gulp_start + len(gulp)] += gulp * 0.5
        
        return generate_sound(samples * 0.5, self.sample_rate)
    
    def chest_open(self) -> pygame.mixer.Sound:
        """Treasure chest opening."""
        duration = 0.4
        samples = np.zeros(int(self.sample_rate * duration))
        
        # Creak
        creak = pitch_sweep(150, 300, 0.2, 'sawtooth', self.sample_rate)
        creak = lowpass_filter(creak, 0.15)
        creak = envelope(creak, 0.02, 0.05, 0.5, 0.1)
        samples[:len(creak)] = creak * 0.4
        
        # Sparkle
        for i in range(3):
            spark_start = int((0.2 + i * 0.05) * self.sample_rate)
            spark = sine_wave(1500 + i * 200, 0.1, self.sample_rate)
            spark = envelope(spark, 0.001, 0.02, 0.3, 0.05)
            if spark_start + len(spark) < len(samples):
                samples[spark_start:spark_start + len(spark)] += spark * 0.3
        
        return generate_sound(samples * 0.5, self.sample_rate)
    
    def error(self) -> pygame.mixer.Sound:
        """Error/can't do that sound."""
        duration = 0.15
        samples = np.zeros(int(self.sample_rate * duration))
        
        # Descending buzz
        buzz = square_wave(200, duration, self.sample_rate) * 0.3
        buzz += square_wave(150, duration, self.sample_rate) * 0.2
        buzz = lowpass_filter(buzz, 0.2)
        buzz = envelope(buzz, 0.01, 0.02, 0.5, 0.05)
        samples[:len(buzz)] = buzz
        
        return generate_sound(samples * 0.4, self.sample_rate)
    
    def footstep(self) -> pygame.mixer.Sound:
        """Footstep on stone."""
        duration = 0.1
        samples = noise(duration, self.sample_rate)
        samples = lowpass_filter(samples, 0.15)
        samples = envelope(samples, 0.005, 0.02, 0.3, 0.05)
        return generate_sound(samples * 0.2, self.sample_rate)

