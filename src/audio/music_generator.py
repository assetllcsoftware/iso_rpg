"""Procedural music generator - creates ambient dungeon music."""

import pygame
import numpy as np
import math
from typing import List, Tuple


def generate_music_buffer(samples: np.ndarray, sample_rate: int = 44100) -> bytes:
    """Convert numpy array to bytes for pygame music."""
    # Ensure samples are in correct format (16-bit signed)
    samples = np.clip(samples * 32767 * 0.5, -32768, 32767).astype(np.int16)
    # Make stereo
    stereo = np.column_stack((samples, samples))
    return stereo.tobytes()


class MusicGenerator:
    """Generates ambient background music procedurally."""
    
    def __init__(self, sample_rate: int = 44100):
        self.sample_rate = sample_rate
    
    def _sine(self, freq: float, duration: float) -> np.ndarray:
        """Generate sine wave."""
        t = np.linspace(0, duration, int(self.sample_rate * duration), False)
        return np.sin(2 * np.pi * freq * t)
    
    def _envelope(self, samples: np.ndarray, attack: float = 0.1, 
                  decay: float = 0.2, sustain: float = 0.6, 
                  release: float = 0.3) -> np.ndarray:
        """Apply ADSR envelope."""
        total = len(samples)
        a = int(attack * total)
        d = int(decay * total)
        r = int(release * total)
        s = total - a - d - r
        
        if s < 0:
            s = 0
            scale = total / (a + d + r)
            a = int(a * scale)
            d = int(d * scale)
            r = total - a - d
        
        env = np.concatenate([
            np.linspace(0, 1, a),
            np.linspace(1, sustain, d),
            np.full(s, sustain),
            np.linspace(sustain, 0, r)
        ])
        
        if len(env) < total:
            env = np.pad(env, (0, total - len(env)))
        else:
            env = env[:total]
        
        return samples * env
    
    def _lowpass(self, samples: np.ndarray, cutoff: float = 0.1) -> np.ndarray:
        """Simple lowpass filter."""
        filtered = np.zeros_like(samples)
        filtered[0] = samples[0]
        for i in range(1, len(samples)):
            filtered[i] = cutoff * samples[i] + (1 - cutoff) * filtered[i-1]
        return filtered
    
    def _pad_sound(self, freq: float, duration: float, 
                   harmonics: List[Tuple[float, float]] = None) -> np.ndarray:
        """Create a soft pad sound."""
        if harmonics is None:
            harmonics = [(1, 1.0), (2, 0.5), (3, 0.25), (4, 0.125)]
        
        samples = np.zeros(int(self.sample_rate * duration))
        for mult, amp in harmonics:
            samples += self._sine(freq * mult, duration) * amp
        
        samples = self._lowpass(samples, 0.05)
        samples = self._envelope(samples, 0.3, 0.2, 0.5, 0.3)
        return samples * 0.3
    
    def _arp_note(self, freq: float, duration: float) -> np.ndarray:
        """Create an arpeggiated note."""
        samples = self._sine(freq, duration)
        samples += self._sine(freq * 2, duration) * 0.3
        samples = self._envelope(samples, 0.01, 0.1, 0.3, 0.2)
        return samples * 0.15
    
    def _bass_note(self, freq: float, duration: float) -> np.ndarray:
        """Create a bass note."""
        samples = self._sine(freq, duration)
        samples += self._sine(freq * 2, duration) * 0.3
        samples = self._lowpass(samples, 0.08)
        samples = self._envelope(samples, 0.05, 0.1, 0.7, 0.2)
        return samples * 0.4
    
    def dungeon_ambient(self, duration: float = 60.0) -> np.ndarray:
        """Generate ambient dungeon exploration music.
        
        Dark, mysterious, with sparse melodic elements.
        """
        total_samples = int(self.sample_rate * duration)
        samples = np.zeros(total_samples)
        
        # Key: D minor
        # D2=73.4, A2=110, D3=146.8, F3=174.6, A3=220, D4=293.7
        
        # Drone pad (very slow, dark)
        drone_freqs = [73.4, 110]  # D2, A2 - perfect fifth drone
        for freq in drone_freqs:
            # Long evolving drone
            drone = np.zeros(total_samples)
            t = np.linspace(0, duration, total_samples, False)
            
            # Slow amplitude modulation
            mod = 0.3 + 0.2 * np.sin(2 * np.pi * 0.05 * t)
            mod *= 0.3 + 0.2 * np.sin(2 * np.pi * 0.03 * t + 1)
            
            drone = np.sin(2 * np.pi * freq * t) * mod
            drone += np.sin(2 * np.pi * freq * 2 * t) * mod * 0.3
            drone = self._lowpass(drone, 0.03)
            samples += drone * 0.25
        
        # Sparse melodic notes (pentatonic: D, F, G, A, C)
        melody_freqs = [293.7, 349.2, 392.0, 440.0, 523.3]  # D4, F4, G4, A4, C5
        note_times = []
        current_time = 2.0
        while current_time < duration - 4:
            note_times.append(current_time)
            current_time += np.random.uniform(3.0, 8.0)
        
        for t in note_times:
            freq = np.random.choice(melody_freqs)
            note_dur = np.random.uniform(1.5, 3.0)
            note = self._pad_sound(freq, note_dur)
            
            start_idx = int(t * self.sample_rate)
            end_idx = min(start_idx + len(note), total_samples)
            samples[start_idx:end_idx] += note[:end_idx - start_idx] * 0.4
        
        # Occasional low bass notes
        bass_times = []
        current_time = 5.0
        while current_time < duration - 3:
            bass_times.append(current_time)
            current_time += np.random.uniform(8.0, 15.0)
        
        bass_freqs = [73.4, 98.0, 110.0]  # D2, G2, A2
        for t in bass_times:
            freq = np.random.choice(bass_freqs)
            note = self._bass_note(freq, 2.0)
            
            start_idx = int(t * self.sample_rate)
            end_idx = min(start_idx + len(note), total_samples)
            samples[start_idx:end_idx] += note[:end_idx - start_idx]
        
        # Subtle texture (filtered noise like wind)
        texture = np.random.uniform(-1, 1, total_samples)
        texture = self._lowpass(texture, 0.01)
        t = np.linspace(0, duration, total_samples, False)
        texture_mod = 0.3 + 0.3 * np.sin(2 * np.pi * 0.02 * t)
        samples += texture * texture_mod * 0.05
        
        return samples
    
    def combat_music(self, duration: float = 30.0) -> np.ndarray:
        """Generate intense combat music.
        
        Driving rhythm, tension, urgency.
        """
        total_samples = int(self.sample_rate * duration)
        samples = np.zeros(total_samples)
        
        # BPM = 140, so beat = 60/140 = 0.428s
        beat_dur = 60.0 / 140.0
        
        # Driving bass pattern (D minor)
        bass_pattern = [73.4, 0, 73.4, 0, 98.0, 0, 73.4, 0]  # D2, rest, D2, rest, G2, rest, D2, rest
        
        current_beat = 0
        while current_beat * beat_dur < duration - 0.5:
            for i, freq in enumerate(bass_pattern):
                t = (current_beat + i * 0.5) * beat_dur
                if t >= duration - 0.3:
                    break
                
                if freq > 0:
                    note = self._bass_note(freq, beat_dur * 0.4)
                    start_idx = int(t * self.sample_rate)
                    end_idx = min(start_idx + len(note), total_samples)
                    samples[start_idx:end_idx] += note[:end_idx - start_idx] * 0.5
            
            current_beat += 4
        
        # Driving hi-hat rhythm
        hat_pattern = [1, 0, 1, 0, 1, 0, 1, 0]
        current_beat = 0
        while current_beat * beat_dur < duration - 0.5:
            for i, hit in enumerate(hat_pattern):
                if hit:
                    t = (current_beat + i * 0.5) * beat_dur
                    if t >= duration - 0.1:
                        break
                    
                    # Hi-hat is filtered noise
                    hat = np.random.uniform(-1, 1, int(self.sample_rate * 0.05))
                    hat = self._envelope(hat, 0.001, 0.01, 0.2, 0.03)
                    # Highpass
                    hat = hat - self._lowpass(hat, 0.3)
                    
                    start_idx = int(t * self.sample_rate)
                    end_idx = min(start_idx + len(hat), total_samples)
                    samples[start_idx:end_idx] += hat[:end_idx - start_idx] * 0.15
            
            current_beat += 4
        
        # Tension strings (sustained, dissonant)
        tension_dur = 4.0
        tension_times = np.arange(0, duration - tension_dur, tension_dur)
        tension_chords = [
            [146.8, 174.6, 220.0],  # Dm
            [130.8, 164.8, 196.0],  # Cm
            [146.8, 174.6, 233.1],  # Dm (sus4)
            [123.5, 155.6, 185.0],  # Bb
        ]
        
        for i, t in enumerate(tension_times):
            chord = tension_chords[i % len(tension_chords)]
            chord_samples = np.zeros(int(self.sample_rate * tension_dur))
            
            for freq in chord:
                note = self._pad_sound(freq, tension_dur)
                chord_samples[:len(note)] += note
            
            start_idx = int(t * self.sample_rate)
            end_idx = min(start_idx + len(chord_samples), total_samples)
            samples[start_idx:end_idx] += chord_samples[:end_idx - start_idx] * 0.3
        
        return samples
    
    def menu_music(self, duration: float = 45.0) -> np.ndarray:
        """Generate menu/title screen music.
        
        Heroic, adventurous, but calm.
        """
        total_samples = int(self.sample_rate * duration)
        samples = np.zeros(total_samples)
        
        # Key: C major / A minor for heroic feel
        # Slow arpeggios
        arp_patterns = [
            [261.6, 329.6, 392.0, 523.3],  # C major
            [220.0, 261.6, 329.6, 440.0],  # Am
            [246.9, 311.1, 370.0, 493.9],  # B dim (brief tension)
            [261.6, 329.6, 392.0, 523.3],  # C major
        ]
        
        beat_dur = 60.0 / 80.0  # 80 BPM, relaxed
        
        current_beat = 0
        pattern_idx = 0
        while current_beat * beat_dur < duration - 2:
            pattern = arp_patterns[pattern_idx % len(arp_patterns)]
            
            for i, freq in enumerate(pattern):
                t = (current_beat + i * 0.5) * beat_dur
                if t >= duration - 1:
                    break
                
                note = self._arp_note(freq, beat_dur * 0.8)
                start_idx = int(t * self.sample_rate)
                end_idx = min(start_idx + len(note), total_samples)
                samples[start_idx:end_idx] += note[:end_idx - start_idx] * 0.5
            
            current_beat += 2
            pattern_idx += 1
        
        # Sustained pad underneath
        pad_freqs = [130.8, 196.0]  # C3, G3
        t = np.linspace(0, duration, total_samples, False)
        
        for freq in pad_freqs:
            mod = 0.4 + 0.2 * np.sin(2 * np.pi * 0.1 * t)
            pad = np.sin(2 * np.pi * freq * t) * mod
            pad += np.sin(2 * np.pi * freq * 2 * t) * mod * 0.3
            pad = self._lowpass(pad, 0.04)
            samples += pad * 0.15
        
        # Gentle bass
        bass_times = np.arange(0, duration - 2, 4.0)
        bass_freqs = [65.4, 55.0, 61.7, 65.4]  # C2, A1, B1, C2
        
        for i, t in enumerate(bass_times):
            freq = bass_freqs[i % len(bass_freqs)]
            note = self._bass_note(freq, 2.0)
            
            start_idx = int(t * self.sample_rate)
            end_idx = min(start_idx + len(note), total_samples)
            samples[start_idx:end_idx] += note[:end_idx - start_idx] * 0.3
        
        return samples
    
    def save_as_wav(self, samples: np.ndarray, filename: str):
        """Save samples to a WAV file."""
        import wave
        import struct
        
        # Normalize and convert to 16-bit
        samples = np.clip(samples, -1, 1)
        samples = (samples * 32767 * 0.7).astype(np.int16)
        
        # Make stereo
        stereo = np.column_stack((samples, samples)).flatten()
        
        with wave.open(filename, 'w') as wav:
            wav.setnchannels(2)
            wav.setsampwidth(2)
            wav.setframerate(self.sample_rate)
            wav.writeframes(stereo.tobytes())

