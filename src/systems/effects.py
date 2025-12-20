"""Visual effects and combat animations."""

import pygame
import math
import random


class Effect:
    """Base class for visual effects."""
    
    def __init__(self, x, y, duration=0.5):
        self.x = x
        self.y = y
        self.duration = duration
        self.elapsed = 0
        self.active = True
    
    @property
    def progress(self):
        """Get animation progress 0-1."""
        return min(1.0, self.elapsed / self.duration)
    
    def update(self, dt):
        """Update effect state."""
        self.elapsed += dt
        if self.elapsed >= self.duration:
            self.active = False
    
    def render(self, screen, camera):
        """Render the effect."""
        pass


class SlashEffect(Effect):
    """Melee sword/axe slash arc."""
    
    def __init__(self, x, y, target_x, target_y, color=(220, 220, 220)):
        super().__init__(x, y, duration=0.25)
        self.target_x = target_x
        self.target_y = target_y
        self.color = color
        
        # Calculate angle to target
        dx = target_x - x
        dy = target_y - y
        self.angle = math.atan2(dy, dx)
        self.arc_width = math.pi * 0.6  # 108 degree arc
    
    def render(self, screen, camera):
        screen_x, screen_y = camera.world_to_screen(self.x, self.y)
        
        # Arc parameters
        radius = max(10, int(40 * camera.zoom))
        
        # Animate the arc sweep
        progress = self.progress
        
        # Arc sweeps from start to end
        sweep_progress = min(1.0, progress * 2)  # Faster sweep
        fade = 1.0 - max(0, (progress - 0.5) * 2)  # Fade out in second half
        
        if fade <= 0:
            return
        
        # Draw multiple arc lines for thickness
        start_angle = self.angle - self.arc_width / 2
        current_arc = self.arc_width * sweep_progress
        
        # Create arc surface with alpha
        arc_surf = pygame.Surface((radius * 2 + 20, radius * 2 + 20), pygame.SRCALPHA)
        center = (radius + 10, radius + 10)
        
        # Draw the slash arc
        num_segments = 12
        for i in range(int(num_segments * sweep_progress)):
            t = i / num_segments
            angle1 = start_angle + current_arc * t
            angle2 = start_angle + current_arc * (t + 1/num_segments)
            
            # Trail effect - older parts more transparent
            alpha = min(255, max(0, int(255 * fade * (0.3 + 0.7 * t))))
            color_with_alpha = (*self.color, alpha)
            
            # Inner and outer arc points
            for r in range(radius - 8, radius + 8, 4):
                x1 = center[0] + int(math.cos(angle1) * r)
                y1 = center[1] + int(math.sin(angle1) * r)
                x2 = center[0] + int(math.cos(angle2) * r)
                y2 = center[1] + int(math.sin(angle2) * r)
                
                pygame.draw.line(arc_surf, color_with_alpha, (x1, y1), (x2, y2), 3)
        
        # Draw bright tip
        tip_angle = start_angle + current_arc
        tip_x = center[0] + int(math.cos(tip_angle) * radius)
        tip_y = center[1] + int(math.sin(tip_angle) * radius)
        tip_alpha = min(255, max(0, int(255 * fade)))
        pygame.draw.circle(arc_surf, (*self.color, tip_alpha), (tip_x, tip_y), 6)
        
        screen.blit(arc_surf, (screen_x - radius - 10, screen_y - radius - 10))


class ArrowEffect(Effect):
    """Projectile arrow for ranged attacks."""
    
    def __init__(self, start_x, start_y, target_x, target_y, color=(180, 140, 80)):
        # Calculate flight time based on distance
        dx = target_x - start_x
        dy = target_y - start_y
        distance = math.sqrt(dx * dx + dy * dy)
        duration = max(0.15, min(0.4, distance / 15))
        
        super().__init__(start_x, start_y, duration=duration)
        self.start_x = start_x
        self.start_y = start_y
        self.target_x = target_x
        self.target_y = target_y
        self.color = color
        
        # Calculate angle
        self.angle = math.atan2(dy, dx)
        
        # Trail positions
        self.trail = []
    
    def update(self, dt):
        super().update(dt)
        
        # Update current position
        progress = self.progress
        self.x = self.start_x + (self.target_x - self.start_x) * progress
        self.y = self.start_y + (self.target_y - self.start_y) * progress
        
        # Add to trail
        self.trail.append((self.x, self.y, progress))
        if len(self.trail) > 8:
            self.trail.pop(0)
    
    def render(self, screen, camera):
        # Draw trail
        for i, (tx, ty, t) in enumerate(self.trail):
            alpha = int(150 * (i / len(self.trail)))
            trail_screen = camera.world_to_screen(tx, ty)
            
            trail_surf = pygame.Surface((10, 10), pygame.SRCALPHA)
            pygame.draw.circle(trail_surf, (*self.color, alpha), (5, 5), 2)
            screen.blit(trail_surf, (trail_screen[0] - 5, trail_screen[1] - 5))
        
        # Draw arrow
        screen_x, screen_y = camera.world_to_screen(self.x, self.y)
        
        # Arrow body
        length = int(16 * camera.zoom)
        back_x = screen_x - int(math.cos(self.angle) * length)
        back_y = screen_y - int(math.sin(self.angle) * length)
        
        pygame.draw.line(screen, self.color, (back_x, back_y), (screen_x, screen_y), 3)
        
        # Arrow head
        head_size = int(6 * camera.zoom)
        head_angle1 = self.angle + math.pi * 0.8
        head_angle2 = self.angle - math.pi * 0.8
        
        head_points = [
            (screen_x, screen_y),
            (screen_x + int(math.cos(head_angle1) * head_size),
             screen_y + int(math.sin(head_angle1) * head_size)),
            (screen_x + int(math.cos(head_angle2) * head_size),
             screen_y + int(math.sin(head_angle2) * head_size)),
        ]
        pygame.draw.polygon(screen, self.color, head_points)


class SpellBoltEffect(Effect):
    """Magic projectile with particles."""
    
    def __init__(self, start_x, start_y, target_x, target_y, color=(100, 150, 255)):
        dx = target_x - start_x
        dy = target_y - start_y
        distance = math.sqrt(dx * dx + dy * dy)
        duration = max(0.2, min(0.5, distance / 8))  # Slower travel
        
        super().__init__(start_x, start_y, duration=duration)
        self.start_x = start_x
        self.start_y = start_y
        self.target_x = target_x
        self.target_y = target_y
        self.color = color
        
        self.particles = []
        self.angle = math.atan2(dy, dx)
        
        # For delayed impact
        self.spawn_impact_on_finish = False
        self.impact_color = color
        self.effects_manager = None
        self.impact_spawned = False
    
    def update(self, dt):
        super().update(dt)
        
        progress = self.progress
        self.x = self.start_x + (self.target_x - self.start_x) * progress
        self.y = self.start_y + (self.target_y - self.start_y) * progress
        
        # Spawn impact when bolt reaches target
        if not self.active and self.spawn_impact_on_finish and not self.impact_spawned:
            if self.effects_manager:
                self.effects_manager.spawn_impact(self.target_x, self.target_y, self.impact_color, 0.8)
            self.impact_spawned = True
        
        # Spawn particles
        if random.random() < 0.8:
            offset_angle = self.angle + random.uniform(-0.5, 0.5)
            speed = random.uniform(1, 3)
            self.particles.append({
                'x': self.x,
                'y': self.y,
                'vx': math.cos(offset_angle + math.pi) * speed,
                'vy': math.sin(offset_angle + math.pi) * speed,
                'life': 0.3,
                'size': random.uniform(2, 5),
            })
        
        # Update particles
        for p in self.particles:
            p['x'] += p['vx'] * dt
            p['y'] += p['vy'] * dt
            p['life'] -= dt
        
        self.particles = [p for p in self.particles if p['life'] > 0]
    
    def render(self, screen, camera):
        # Draw particles
        for p in self.particles:
            alpha = min(255, max(0, int(200 * (p['life'] / 0.3))))
            screen_pos = camera.world_to_screen(p['x'], p['y'])
            size = max(1, int(p['size'] * camera.zoom))
            
            part_surf = pygame.Surface((size * 2 + 2, size * 2 + 2), pygame.SRCALPHA)
            pygame.draw.circle(part_surf, (*self.color, alpha), (size + 1, size + 1), size)
            screen.blit(part_surf, (screen_pos[0] - size - 1, screen_pos[1] - size - 1))
        
        # Draw main bolt
        screen_x, screen_y = camera.world_to_screen(self.x, self.y)
        
        # Glow
        glow_size = max(1, int(20 * camera.zoom))
        glow_surf = pygame.Surface((glow_size * 2 + 2, glow_size * 2 + 2), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (*self.color, 60), (glow_size + 1, glow_size + 1), glow_size)
        pygame.draw.circle(glow_surf, (*self.color, 120), (glow_size + 1, glow_size + 1), max(1, glow_size // 2))
        screen.blit(glow_surf, (screen_x - glow_size - 1, screen_y - glow_size - 1))
        
        # Core
        core_size = max(1, int(6 * camera.zoom))
        pygame.draw.circle(screen, (255, 255, 255), (screen_x, screen_y), core_size)
        pygame.draw.circle(screen, self.color, (screen_x, screen_y), core_size + 2, 2)


class ImpactEffect(Effect):
    """Explosion/impact effect on hit."""
    
    def __init__(self, x, y, color=(255, 200, 100), size=1.0):
        super().__init__(x, y, duration=0.3)
        self.color = color
        self.size = size
        self.particles = []
        
        # Create burst particles
        num_particles = int(8 * size)
        for i in range(num_particles):
            angle = (i / num_particles) * math.pi * 2
            speed = random.uniform(3, 8) * size
            self.particles.append({
                'x': x,
                'y': y,
                'vx': math.cos(angle) * speed,
                'vy': math.sin(angle) * speed,
                'size': random.uniform(2, 4) * size,
            })
    
    def update(self, dt):
        super().update(dt)
        
        for p in self.particles:
            p['x'] += p['vx'] * dt
            p['y'] += p['vy'] * dt
            p['vx'] *= 0.9  # Friction
            p['vy'] *= 0.9
    
    def render(self, screen, camera):
        fade = 1.0 - self.progress
        
        # Draw expanding ring
        screen_x, screen_y = camera.world_to_screen(self.x, self.y)
        ring_radius = max(1, int((20 + 40 * self.progress) * self.size * camera.zoom))
        ring_alpha = min(255, max(0, int(200 * fade)))
        
        ring_surf = pygame.Surface((ring_radius * 2 + 6, ring_radius * 2 + 6), pygame.SRCALPHA)
        pygame.draw.circle(ring_surf, (*self.color, ring_alpha), 
                          (ring_radius + 3, ring_radius + 3), ring_radius, 3)
        screen.blit(ring_surf, (screen_x - ring_radius - 3, screen_y - ring_radius - 3))
        
        # Draw particles
        for p in self.particles:
            alpha = min(255, max(0, int(255 * fade)))
            p_screen = camera.world_to_screen(p['x'], p['y'])
            size = max(1, int(p['size'] * camera.zoom * fade))
            
            if size > 0:
                part_surf = pygame.Surface((size * 2 + 2, size * 2 + 2), pygame.SRCALPHA)
                pygame.draw.circle(part_surf, (*self.color, alpha), (size + 1, size + 1), size)
                screen.blit(part_surf, (p_screen[0] - size - 1, p_screen[1] - size - 1))


class FireballEffect(SpellBoltEffect):
    """Fireball with fire trail."""
    
    def __init__(self, start_x, start_y, target_x, target_y):
        super().__init__(start_x, start_y, target_x, target_y, color=(255, 120, 40))
    
    def update(self, dt):
        super().update(dt)
        
        # Extra fire particles
        if random.random() < 0.9:
            self.particles.append({
                'x': self.x + random.uniform(-0.2, 0.2),
                'y': self.y + random.uniform(-0.2, 0.2),
                'vx': random.uniform(-2, 2),
                'vy': random.uniform(-4, -1),
                'life': random.uniform(0.2, 0.4),
                'size': random.uniform(3, 7),
            })


class HealEffect(Effect):
    """Healing sparkles rising up."""
    
    def __init__(self, x, y):
        super().__init__(x, y, duration=0.8)
        self.particles = []
        self.spawn_timer = 0
    
    def update(self, dt):
        super().update(dt)
        
        # Spawn healing particles
        self.spawn_timer += dt
        if self.spawn_timer > 0.05 and self.progress < 0.7:
            self.spawn_timer = 0
            angle = random.uniform(0, math.pi * 2)
            dist = random.uniform(0.2, 0.8)
            self.particles.append({
                'x': self.x + math.cos(angle) * dist,
                'y': self.y + math.sin(angle) * dist,
                'vy': -random.uniform(2, 4),
                'life': random.uniform(0.4, 0.7),
                'size': random.uniform(3, 6),
            })
        
        # Update particles
        for p in self.particles:
            p['y'] += p['vy'] * dt
            p['life'] -= dt
        
        self.particles = [p for p in self.particles if p['life'] > 0]
    
    def render(self, screen, camera):
        for p in self.particles:
            alpha = min(255, max(0, int(255 * (p['life'] / 0.7))))
            screen_pos = camera.world_to_screen(p['x'], p['y'])
            size = max(1, int(p['size'] * camera.zoom))
            
            # Green healing color
            color = (100, 255, 150)
            
            part_surf = pygame.Surface((size * 2 + 2, size * 2 + 2), pygame.SRCALPHA)
            pygame.draw.circle(part_surf, (*color, alpha), (size + 1, size + 1), size)
            screen.blit(part_surf, (screen_pos[0] - size - 1, screen_pos[1] - size - 1))
            
            # Plus sign on some particles
            if size > 4:
                pygame.draw.line(part_surf, (255, 255, 255, alpha), 
                               (size + 1, size + 1 - size//2), (size + 1, size + 1 + size//2), 2)
                pygame.draw.line(part_surf, (255, 255, 255, alpha),
                               (size + 1 - size//2, size + 1), (size + 1 + size//2, size + 1), 2)


class EffectsManager:
    """Manages all active visual effects."""
    
    def __init__(self):
        self.effects = []
    
    def add(self, effect):
        """Add a new effect."""
        self.effects.append(effect)
    
    def spawn_melee_attack(self, attacker_x, attacker_y, target_x, target_y):
        """Spawn a melee slash effect."""
        self.effects.append(SlashEffect(attacker_x, attacker_y, target_x, target_y))
        # Impact on target
        self.effects.append(ImpactEffect(target_x, target_y, (255, 200, 150), size=0.6))
    
    def spawn_ranged_attack(self, start_x, start_y, target_x, target_y):
        """Spawn an arrow projectile."""
        self.effects.append(ArrowEffect(start_x, start_y, target_x, target_y))
    
    def spawn_spell(self, spell_name, start_x, start_y, target_x, target_y):
        """Spawn a spell effect."""
        if spell_name == 'fireball':
            self.effects.append(FireballEffect(start_x, start_y, target_x, target_y))
            # Delayed impact
            self.effects.append(ImpactEffect(target_x, target_y, (255, 100, 50), size=1.2))
        elif spell_name == 'ice_shard':
            self.effects.append(SpellBoltEffect(start_x, start_y, target_x, target_y, 
                                               color=(150, 200, 255)))
            self.effects.append(ImpactEffect(target_x, target_y, (150, 200, 255), size=0.8))
        elif spell_name == 'lightning_bolt':
            self.effects.append(SpellBoltEffect(start_x, start_y, target_x, target_y,
                                               color=(200, 200, 255)))
        elif spell_name == 'heal':
            self.effects.append(HealEffect(target_x, target_y))
        else:
            # Generic magic bolt
            self.effects.append(SpellBoltEffect(start_x, start_y, target_x, target_y))
    
    def spawn_impact(self, x, y, color=(255, 200, 100), size=1.0):
        """Spawn an impact effect."""
        self.effects.append(ImpactEffect(x, y, color, size))
    
    def spawn_spell_attack(self, start_x, start_y, target_x, target_y, color=(255, 100, 50)):
        """Spawn a spell attack effect (for ally spellcasting)."""
        bolt = SpellBoltEffect(start_x, start_y, target_x, target_y, color=color)
        bolt.spawn_impact_on_finish = True
        bolt.impact_color = color
        bolt.effects_manager = self
        self.effects.append(bolt)
    
    def update(self, dt):
        """Update all effects."""
        for effect in self.effects:
            effect.update(dt)
        
        # Remove finished effects
        self.effects = [e for e in self.effects if e.active]
    
    def render(self, screen, camera):
        """Render all effects."""
        for effect in self.effects:
            effect.render(screen, camera)

