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
        # Slower projectile travel - 4 units per second
        duration = max(0.3, distance / 4.0)
        
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
        
        # For delayed damage
        self.damage = 0
        self.damage_target = None
        self.caster = None
    
    def update(self, dt):
        super().update(dt)
        
        progress = self.progress
        self.x = self.start_x + (self.target_x - self.start_x) * progress
        self.y = self.start_y + (self.target_y - self.start_y) * progress
        
        # Apply damage and spawn impact when bolt reaches target
        if not self.active and not self.impact_spawned:
            # Apply delayed damage
            if self.damage > 0 and self.damage_target and hasattr(self.damage_target, 'take_damage'):
                if self.damage_target.health > 0:
                    self.damage_target.take_damage(self.damage, self.caster)
            
            # Spawn impact visual
            if self.spawn_impact_on_finish and self.effects_manager:
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
        
        # Outer glow - bigger
        glow_size = max(5, int(35 * camera.zoom))
        glow_surf = pygame.Surface((glow_size * 2 + 4, glow_size * 2 + 4), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (*self.color, 40), (glow_size + 2, glow_size + 2), glow_size)
        pygame.draw.circle(glow_surf, (*self.color, 80), (glow_size + 2, glow_size + 2), max(3, glow_size // 2))
        screen.blit(glow_surf, (screen_x - glow_size - 2, screen_y - glow_size - 2))
        
        # Bright core - bigger
        core_size = max(4, int(12 * camera.zoom))
        pygame.draw.circle(screen, (255, 255, 255), (screen_x, screen_y), core_size)
        pygame.draw.circle(screen, self.color, (screen_x, screen_y), core_size + 3, 3)


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
        # Fireball is slower and more dramatic
        dx = target_x - start_x
        dy = target_y - start_y
        distance = math.sqrt(dx * dx + dy * dy)
        self.duration = max(0.5, distance / 3.0)  # Even slower than normal bolts
    
    def update(self, dt):
        super().update(dt)
        
        # Lots of fire particles trailing behind
        for _ in range(3):  # Multiple particles per frame
            if random.random() < 0.95:
                self.particles.append({
                    'x': self.x + random.uniform(-0.3, 0.3),
                    'y': self.y + random.uniform(-0.3, 0.3),
                    'vx': random.uniform(-3, 3),
                    'vy': random.uniform(-5, -2),
                    'life': random.uniform(0.3, 0.6),
                    'size': random.uniform(5, 12),
                })
    
    def render(self, screen, camera):
        # Draw fire particles first
        for p in self.particles:
            alpha = min(255, max(0, int(220 * (p['life'] / 0.6))))
            screen_pos = camera.world_to_screen(p['x'], p['y'])
            size = max(2, int(p['size'] * camera.zoom))
            
            # Orange to yellow gradient based on life
            r = 255
            g = int(100 + 120 * (p['life'] / 0.6))
            b = int(50 * (p['life'] / 0.6))
            
            part_surf = pygame.Surface((size * 2 + 2, size * 2 + 2), pygame.SRCALPHA)
            pygame.draw.circle(part_surf, (r, g, b, alpha), (size + 1, size + 1), size)
            screen.blit(part_surf, (screen_pos[0] - size - 1, screen_pos[1] - size - 1))
        
        # Draw main fireball - big and bright
        screen_x, screen_y = camera.world_to_screen(self.x, self.y)
        
        # Outer glow
        glow_size = max(8, int(45 * camera.zoom))
        glow_surf = pygame.Surface((glow_size * 2 + 4, glow_size * 2 + 4), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (255, 100, 30, 50), (glow_size + 2, glow_size + 2), glow_size)
        pygame.draw.circle(glow_surf, (255, 150, 50, 100), (glow_size + 2, glow_size + 2), glow_size // 2)
        screen.blit(glow_surf, (screen_x - glow_size - 2, screen_y - glow_size - 2))
        
        # Bright yellow-white core
        core_size = max(6, int(18 * camera.zoom))
        pygame.draw.circle(screen, (255, 255, 200), (screen_x, screen_y), core_size)
        pygame.draw.circle(screen, (255, 200, 100), (screen_x, screen_y), core_size + 4, 4)


class HealEffect(Effect):
    """Healing sparkles rising up with glowing cross."""
    
    def __init__(self, x, y):
        super().__init__(x, y, duration=1.0)
        self.particles = []
        self.spawn_timer = 0
        self.ring_radius = 0
    
    def update(self, dt):
        super().update(dt)
        
        # Expanding ring
        self.ring_radius = self.progress * 2.0
        
        # Spawn healing particles
        self.spawn_timer += dt
        if self.spawn_timer > 0.03 and self.progress < 0.8:
            self.spawn_timer = 0
            angle = random.uniform(0, math.pi * 2)
            dist = random.uniform(0.2, 1.0)
            self.particles.append({
                'x': self.x + math.cos(angle) * dist,
                'y': self.y + math.sin(angle) * dist,
                'vy': -random.uniform(2, 5),
                'life': random.uniform(0.5, 0.9),
                'size': random.uniform(3, 8),
                'is_cross': random.random() < 0.3,
            })
        
        # Update particles
        for p in self.particles:
            p['y'] += p['vy'] * dt
            p['life'] -= dt
        
        self.particles = [p for p in self.particles if p['life'] > 0]
    
    def render(self, screen, camera):
        screen_x, screen_y = camera.world_to_screen(self.x, self.y)
        
        # Draw expanding ring
        ring_size = max(1, int(self.ring_radius * 30 * camera.zoom))
        ring_alpha = max(0, int(150 * (1 - self.progress)))
        if ring_size > 0 and ring_alpha > 0:
            ring_surf = pygame.Surface((ring_size * 2 + 4, ring_size * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(ring_surf, (100, 255, 150, ring_alpha), 
                             (ring_size + 2, ring_size + 2), ring_size, 3)
            screen.blit(ring_surf, (screen_x - ring_size - 2, screen_y - ring_size - 2))
        
        # Draw center glow
        if self.progress < 0.5:
            glow_alpha = int(180 * (1 - self.progress * 2))
            glow_size = max(1, int(15 * camera.zoom))
            glow_surf = pygame.Surface((glow_size * 2 + 4, glow_size * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (150, 255, 180, glow_alpha), 
                             (glow_size + 2, glow_size + 2), glow_size)
            screen.blit(glow_surf, (screen_x - glow_size - 2, screen_y - glow_size - 2))
        
        for p in self.particles:
            alpha = min(255, max(0, int(255 * (p['life'] / 0.9))))
            screen_pos = camera.world_to_screen(p['x'], p['y'])
            size = max(1, int(p['size'] * camera.zoom))
            
            color = (100, 255, 150)
            
            part_surf = pygame.Surface((size * 2 + 4, size * 2 + 4), pygame.SRCALPHA)
            
            if p.get('is_cross') and size > 3:
                # Draw plus sign
                cx, cy = size + 2, size + 2
                pygame.draw.line(part_surf, (*color, alpha), (cx, cy - size//2), (cx, cy + size//2), 2)
                pygame.draw.line(part_surf, (*color, alpha), (cx - size//2, cy), (cx + size//2, cy), 2)
            else:
                pygame.draw.circle(part_surf, (*color, alpha), (size + 2, size + 2), size)
            
            screen.blit(part_surf, (screen_pos[0] - size - 2, screen_pos[1] - size - 2))


class LightningBoltEffect(Effect):
    """Jagged lightning bolt that strikes instantly."""
    
    def __init__(self, start_x, start_y, target_x, target_y):
        super().__init__(start_x, start_y, duration=0.4)
        self.start_x = start_x
        self.start_y = start_y
        self.target_x = target_x
        self.target_y = target_y
        self.bolts = []
        self._generate_bolt()
    
    def _generate_bolt(self):
        """Generate a jagged lightning path."""
        dx = self.target_x - self.start_x
        dy = self.target_y - self.start_y
        dist = max(0.1, math.sqrt(dx * dx + dy * dy))
        
        segments = max(4, int(dist * 2))
        points = [(self.start_x, self.start_y)]
        
        for i in range(1, segments):
            t = i / segments
            x = self.start_x + dx * t
            y = self.start_y + dy * t
            perp_x = -dy / dist
            perp_y = dx / dist
            offset = random.uniform(-0.4, 0.4) * (1 - abs(t - 0.5) * 2)
            x += perp_x * offset
            y += perp_y * offset
            points.append((x, y))
        
        points.append((self.target_x, self.target_y))
        self.bolts.append(points)
        
        # Branching bolts
        for i, (px, py) in enumerate(points[1:-2]):
            if random.random() < 0.3:
                branch_len = random.uniform(0.5, 1.5)
                branch_angle = math.atan2(dy, dx) + random.uniform(-1.2, 1.2)
                branch_end = (px + math.cos(branch_angle) * branch_len,
                              py + math.sin(branch_angle) * branch_len)
                self.bolts.append([(px, py), branch_end])
    
    def render(self, screen, camera):
        fade = 1.0 - self.progress
        
        # Screen flash
        if self.progress < 0.1:
            flash_alpha = int(80 * (1 - self.progress * 10))
            flash_surf = pygame.Surface((screen.get_width(), screen.get_height()), pygame.SRCALPHA)
            flash_surf.fill((200, 200, 255, flash_alpha))
            screen.blit(flash_surf, (0, 0))
        
        for bolt_points in self.bolts:
            if len(bolt_points) < 2:
                continue
            screen_points = [camera.world_to_screen(x, y) for x, y in bolt_points]
            
            # Glow
            alpha = min(255, max(0, int(100 * fade)))
            if alpha > 0:
                for i in range(len(screen_points) - 1):
                    glow_surf = pygame.Surface((screen.get_width(), screen.get_height()), pygame.SRCALPHA)
                    pygame.draw.line(glow_surf, (150, 150, 255, alpha), 
                                   screen_points[i], screen_points[i+1], 8)
                    screen.blit(glow_surf, (0, 0))
            
            # Core
            for i in range(len(screen_points) - 1):
                pygame.draw.line(screen, (255, 255, 255), screen_points[i], screen_points[i+1], 3)
                pygame.draw.line(screen, (200, 200, 255), screen_points[i], screen_points[i+1], 2)


class ChainLightningEffect(Effect):
    """Lightning that jumps between multiple targets."""
    
    def __init__(self, positions):
        if len(positions) < 2:
            positions = [(0, 0), (1, 1)]
        super().__init__(positions[0][0], positions[0][1], duration=0.6)
        self.positions = positions
        self.bolts = []
        
        for i in range(len(positions) - 1):
            self._generate_bolt(positions[i], positions[i + 1], delay=i * 0.1)
    
    def _generate_bolt(self, start, end, delay):
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        dist = max(0.1, math.sqrt(dx * dx + dy * dy))
        
        segments = max(3, int(dist * 2))
        points = [start]
        
        for i in range(1, segments):
            t = i / segments
            x = start[0] + dx * t
            y = start[1] + dy * t
            perp_x = -dy / dist
            perp_y = dx / dist
            offset = random.uniform(-0.3, 0.3) * (1 - abs(t - 0.5) * 2)
            x += perp_x * offset
            y += perp_y * offset
            points.append((x, y))
        
        points.append(end)
        self.bolts.append({'points': points, 'delay': delay})
    
    def render(self, screen, camera):
        for bolt in self.bolts:
            if self.elapsed < bolt['delay']:
                continue
            
            bolt_progress = (self.elapsed - bolt['delay']) / max(0.1, self.duration - bolt['delay'])
            fade = max(0, 1.0 - bolt_progress)
            if fade <= 0:
                continue
            
            points = bolt['points']
            screen_points = [camera.world_to_screen(x, y) for x, y in points]
            if len(screen_points) < 2:
                continue
            
            alpha = min(255, max(0, int(80 * fade)))
            for i in range(len(screen_points) - 1):
                glow_surf = pygame.Surface((screen.get_width(), screen.get_height()), pygame.SRCALPHA)
                pygame.draw.line(glow_surf, (180, 180, 255, alpha), 
                               screen_points[i], screen_points[i+1], 6)
                screen.blit(glow_surf, (0, 0))
            
            for i in range(len(screen_points) - 1):
                pygame.draw.line(screen, (255, 255, 255), screen_points[i], screen_points[i+1], 2)
            
            # Sparks at nodes
            for px, py in screen_points:
                if random.random() < 0.5 * fade:
                    pygame.draw.circle(screen, (255, 255, 255), (int(px), int(py)), random.randint(2, 4))


class IceShardEffect(Effect):
    """Crystalline ice projectile with frost trail."""
    
    def __init__(self, start_x, start_y, target_x, target_y):
        dx = target_x - start_x
        dy = target_y - start_y
        distance = math.sqrt(dx * dx + dy * dy)
        # Slower travel - 5 units per second
        duration = max(0.3, distance / 5.0)
        
        super().__init__(start_x, start_y, duration=duration)
        self.start_x = start_x
        self.start_y = start_y
        self.target_x = target_x
        self.target_y = target_y
        self.angle = math.atan2(dy, dx)
        self.frost_particles = []
        
        # For impact spawning
        self.spawn_impact_on_finish = False
        self.impact_color = (150, 200, 255)
        self.effects_manager = None
        self.impact_spawned = False
        
        # For delayed damage
        self.damage = 0
        self.damage_target = None
        self.caster = None
    
    def update(self, dt):
        super().update(dt)
        progress = self.progress
        self.x = self.start_x + (self.target_x - self.start_x) * progress
        self.y = self.start_y + (self.target_y - self.start_y) * progress
        
        # Apply damage and spawn impact when shard reaches target
        if not self.active and not self.impact_spawned:
            # Apply delayed damage
            if self.damage > 0 and self.damage_target and hasattr(self.damage_target, 'take_damage'):
                if self.damage_target.health > 0:
                    self.damage_target.take_damage(self.damage, self.caster)
            
            # Spawn impact visual
            if self.spawn_impact_on_finish and self.effects_manager:
                self.effects_manager.spawn_impact(self.target_x, self.target_y, self.impact_color, 0.8)
            
            self.impact_spawned = True
        
        if random.random() < 0.7:
            self.frost_particles.append({
                'x': self.x, 'y': self.y,
                'vx': random.uniform(-1, 1), 'vy': random.uniform(-1, 0.5),
                'life': random.uniform(0.3, 0.5), 'size': random.uniform(2, 5),
            })
        
        for p in self.frost_particles:
            p['x'] += p['vx'] * dt
            p['y'] += p['vy'] * dt
            p['life'] -= dt
        self.frost_particles = [p for p in self.frost_particles if p['life'] > 0]
    
    def render(self, screen, camera):
        # Frost particles trail
        for p in self.frost_particles:
            alpha = min(255, max(0, int(200 * (p['life'] / 0.5))))
            screen_pos = camera.world_to_screen(p['x'], p['y'])
            size = max(3, int(p['size'] * camera.zoom * 1.5))
            frost_surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            pygame.draw.circle(frost_surf, (180, 220, 255, alpha), (size, size), size)
            screen.blit(frost_surf, (screen_pos[0] - size, screen_pos[1] - size))
        
        screen_x, screen_y = camera.world_to_screen(self.x, self.y)
        size = max(8, int(20 * camera.zoom))  # Bigger crystal
        
        # Glow behind crystal
        glow_size = int(size * 1.5)
        glow_surf = pygame.Surface((glow_size * 2 + 4, glow_size * 2 + 4), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (150, 200, 255, 60), (glow_size + 2, glow_size + 2), glow_size)
        screen.blit(glow_surf, (screen_x - glow_size - 2, screen_y - glow_size - 2))
        
        # Crystal shape - larger and brighter
        points = [
            (screen_x + math.cos(self.angle) * size, screen_y + math.sin(self.angle) * size),
            (screen_x + math.cos(self.angle + 2.2) * size * 0.6, screen_y + math.sin(self.angle + 2.2) * size * 0.6),
            (screen_x + math.cos(self.angle + math.pi) * size * 0.4, screen_y + math.sin(self.angle + math.pi) * size * 0.4),
            (screen_x + math.cos(self.angle - 2.2) * size * 0.6, screen_y + math.sin(self.angle - 2.2) * size * 0.6),
        ]
        pygame.draw.polygon(screen, (200, 235, 255), points)
        pygame.draw.polygon(screen, (255, 255, 255), points, 2)


class MeteorEffect(Effect):
    """Falling meteor with fire trail and big impact."""
    
    def __init__(self, target_x, target_y):
        super().__init__(target_x, target_y, duration=1.2)
        self.target_x = target_x
        self.target_y = target_y
        self.start_offset_y = -8.0
        self.meteor_x = target_x
        self.meteor_y = target_y + self.start_offset_y
        self.fire_particles = []
        self.impacted = False
        self.impact_time = 0.6
    
    def update(self, dt):
        super().update(dt)
        if self.elapsed < self.impact_time:
            fall_progress = self.elapsed / self.impact_time
            self.meteor_y = self.target_y + self.start_offset_y * (1 - fall_progress)
            if random.random() < 0.9:
                self.fire_particles.append({
                    'x': self.meteor_x + random.uniform(-0.3, 0.3),
                    'y': self.meteor_y,
                    'vx': random.uniform(-1, 1), 'vy': random.uniform(-3, -1),
                    'life': random.uniform(0.3, 0.6), 'size': random.uniform(4, 10),
                })
        elif not self.impacted:
            self.impacted = True
        
        for p in self.fire_particles:
            p['x'] += p['vx'] * dt
            p['y'] += p['vy'] * dt
            p['life'] -= dt
        self.fire_particles = [p for p in self.fire_particles if p['life'] > 0]
    
    def render(self, screen, camera):
        for p in self.fire_particles:
            alpha = min(255, max(0, int(255 * (p['life'] / 0.6))))
            screen_pos = camera.world_to_screen(p['x'], p['y'])
            size = max(1, int(p['size'] * camera.zoom))
            fire_surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            pygame.draw.circle(fire_surf, (255, 150, 50, alpha), (size, size), size)
            screen.blit(fire_surf, (screen_pos[0] - size, screen_pos[1] - size))
        
        if self.elapsed < self.impact_time:
            screen_x, screen_y = camera.world_to_screen(self.meteor_x, self.meteor_y)
            rock_size = int(18 * camera.zoom)
            pygame.draw.circle(screen, (100, 60, 40), (screen_x, screen_y), rock_size)
            glow_surf = pygame.Surface((rock_size * 4, rock_size * 4), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (255, 100, 30, 100), (rock_size * 2, rock_size * 2), rock_size * 2)
            screen.blit(glow_surf, (screen_x - rock_size * 2, screen_y - rock_size * 2))
        else:
            impact_progress = (self.elapsed - self.impact_time) / (self.duration - self.impact_time)
            screen_x, screen_y = camera.world_to_screen(self.target_x, self.target_y)
            ring_size = max(1, int((30 + 80 * impact_progress) * camera.zoom))
            ring_alpha = max(0, int(200 * (1 - impact_progress)))
            ring_surf = pygame.Surface((ring_size * 2 + 10, ring_size * 2 + 10), pygame.SRCALPHA)
            pygame.draw.circle(ring_surf, (255, 100, 30, ring_alpha), (ring_size + 5, ring_size + 5), ring_size, 5)
            screen.blit(ring_surf, (screen_x - ring_size - 5, screen_y - ring_size - 5))


class InfernoEffect(Effect):
    """Massive fire explosion with multiple rings."""
    
    def __init__(self, x, y):
        super().__init__(x, y, duration=1.5)
        self.fire_particles = []
        self.rings = []
        self.spawn_timer = 0
    
    def update(self, dt):
        super().update(dt)
        
        # Spawn fire particles rapidly
        self.spawn_timer += dt
        if self.spawn_timer > 0.02 and self.progress < 0.7:
            self.spawn_timer = 0
            for _ in range(3):
                angle = random.uniform(0, math.pi * 2)
                speed = random.uniform(3, 8)
                self.fire_particles.append({
                    'x': self.x + random.uniform(-0.5, 0.5),
                    'y': self.y + random.uniform(-0.5, 0.5),
                    'vx': math.cos(angle) * speed,
                    'vy': math.sin(angle) * speed - 2,
                    'life': random.uniform(0.4, 0.8),
                    'size': random.uniform(6, 15),
                })
        
        # Spawn expanding rings
        if self.elapsed < 0.3 and len(self.rings) < 3:
            self.rings.append({'radius': 0, 'alpha': 255})
        
        for ring in self.rings:
            ring['radius'] += dt * 4
            ring['alpha'] = max(0, ring['alpha'] - dt * 200)
        
        for p in self.fire_particles:
            p['x'] += p['vx'] * dt
            p['y'] += p['vy'] * dt
            p['life'] -= dt
        self.fire_particles = [p for p in self.fire_particles if p['life'] > 0]
        self.rings = [r for r in self.rings if r['alpha'] > 0]
    
    def render(self, screen, camera):
        screen_x, screen_y = camera.world_to_screen(self.x, self.y)
        
        # Draw rings
        for ring in self.rings:
            ring_size = int(ring['radius'] * 30 * camera.zoom)
            alpha = int(ring['alpha'])
            if ring_size > 0:
                ring_surf = pygame.Surface((ring_size * 2 + 10, ring_size * 2 + 10), pygame.SRCALPHA)
                pygame.draw.circle(ring_surf, (255, 80, 0, alpha), (ring_size + 5, ring_size + 5), ring_size, 4)
                screen.blit(ring_surf, (screen_x - ring_size - 5, screen_y - ring_size - 5))
        
        # Draw fire particles
        for p in self.fire_particles:
            screen_pos = camera.world_to_screen(p['x'], p['y'])
            size = max(1, int(p['size'] * camera.zoom * (p['life'] / 0.8)))
            alpha = min(255, int(255 * (p['life'] / 0.8)))
            fire_surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            pygame.draw.circle(fire_surf, (255, 100 + int(100 * p['life']), 30, alpha), (size, size), size)
            screen.blit(fire_surf, (screen_pos[0] - size, screen_pos[1] - size))


class BlizzardEffect(Effect):
    """Swirling ice storm with snowflakes."""
    
    def __init__(self, x, y):
        super().__init__(x, y, duration=2.0)
        self.ice_particles = []
        self.spawn_timer = 0
        self.rotation = 0
    
    def update(self, dt):
        super().update(dt)
        self.rotation += dt * 3
        
        # Spawn ice particles
        self.spawn_timer += dt
        if self.spawn_timer > 0.03 and self.progress < 0.8:
            self.spawn_timer = 0
            angle = self.rotation + random.uniform(-0.5, 0.5)
            dist = random.uniform(0.5, 2.5)
            self.ice_particles.append({
                'angle': angle,
                'dist': dist,
                'y_offset': random.uniform(-1, 1),
                'vy': random.uniform(-1, 1),
                'life': random.uniform(0.5, 1.0),
                'size': random.randint(3, 8),
            })
        
        for p in self.ice_particles:
            p['angle'] += dt * 2
            p['y_offset'] += p['vy'] * dt
            p['life'] -= dt
        self.ice_particles = [p for p in self.ice_particles if p['life'] > 0]
    
    def render(self, screen, camera):
        screen_x, screen_y = camera.world_to_screen(self.x, self.y)
        
        # Draw center glow
        center_size = int(40 * camera.zoom * (1 - self.progress * 0.5))
        glow_surf = pygame.Surface((center_size * 2, center_size * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (150, 200, 255, 80), (center_size, center_size), center_size)
        screen.blit(glow_surf, (screen_x - center_size, screen_y - center_size))
        
        # Draw ice particles
        for p in self.ice_particles:
            px = self.x + math.cos(p['angle']) * p['dist']
            py = self.y + math.sin(p['angle']) * p['dist'] * 0.5 + p['y_offset']
            screen_pos = camera.world_to_screen(px, py)
            size = max(1, int(p['size'] * camera.zoom))
            alpha = min(255, int(255 * p['life']))
            pygame.draw.circle(screen, (180, 220, 255), screen_pos, size)
            pygame.draw.circle(screen, (255, 255, 255), screen_pos, size // 2)


class ArmageddonEffect(Effect):
    """Rain of fire meteors all around."""
    
    def __init__(self, x, y):
        super().__init__(x, y, duration=2.5)
        self.meteors = []
        self.spawn_timer = 0
        self.impacts = []
    
    def update(self, dt):
        super().update(dt)
        
        # Spawn meteors
        self.spawn_timer += dt
        if self.spawn_timer > 0.15 and self.progress < 0.7:
            self.spawn_timer = 0
            angle = random.uniform(0, math.pi * 2)
            dist = random.uniform(1, 5)
            target_x = self.x + math.cos(angle) * dist
            target_y = self.y + math.sin(angle) * dist
            self.meteors.append({
                'target_x': target_x,
                'target_y': target_y,
                'start_y': target_y - 4,
                'progress': 0,
                'size': random.uniform(6, 12),
            })
        
        for m in self.meteors:
            m['progress'] += dt * 2
            if m['progress'] >= 1.0 and 'impacted' not in m:
                m['impacted'] = True
                self.impacts.append({
                    'x': m['target_x'],
                    'y': m['target_y'],
                    'radius': 0,
                    'alpha': 255,
                })
        self.meteors = [m for m in self.meteors if m['progress'] < 1.0]
        
        for i in self.impacts:
            i['radius'] += dt * 3
            i['alpha'] = max(0, i['alpha'] - dt * 300)
        self.impacts = [i for i in self.impacts if i['alpha'] > 0]
    
    def render(self, screen, camera):
        # Draw falling meteors
        for m in self.meteors:
            current_y = m['start_y'] + (m['target_y'] - m['start_y']) * m['progress']
            screen_pos = camera.world_to_screen(m['target_x'], current_y)
            size = int(m['size'] * camera.zoom)
            # Fire trail
            for i in range(3):
                trail_y = current_y - (i + 1) * 0.3
                trail_pos = camera.world_to_screen(m['target_x'], trail_y)
                trail_size = size - i * 2
                if trail_size > 0:
                    pygame.draw.circle(screen, (255, 150 - i * 30, 30), trail_pos, trail_size)
            # Meteor
            pygame.draw.circle(screen, (100, 60, 40), screen_pos, size)
        
        # Draw impacts
        for i in self.impacts:
            screen_pos = camera.world_to_screen(i['x'], i['y'])
            radius = int(i['radius'] * 20 * camera.zoom)
            alpha = int(i['alpha'])
            if radius > 0:
                ring_surf = pygame.Surface((radius * 2 + 10, radius * 2 + 10), pygame.SRCALPHA)
                pygame.draw.circle(ring_surf, (255, 100, 30, alpha), (radius + 5, radius + 5), radius, 3)
                screen.blit(ring_surf, (screen_pos[0] - radius - 5, screen_pos[1] - radius - 5))


class SanctuaryEffect(Effect):
    """Golden dome of healing light."""
    
    def __init__(self, x, y):
        super().__init__(x, y, duration=2.0)
        self.sparkles = []
        self.dome_alpha = 0
    
    def update(self, dt):
        super().update(dt)
        
        # Dome alpha curve
        if self.progress < 0.2:
            self.dome_alpha = self.progress / 0.2
        elif self.progress > 0.8:
            self.dome_alpha = (1.0 - self.progress) / 0.2
        else:
            self.dome_alpha = 1.0
        
        # Spawn sparkles
        if random.random() < 0.3:
            angle = random.uniform(0, math.pi * 2)
            dist = random.uniform(1, 4)
            self.sparkles.append({
                'x': self.x + math.cos(angle) * dist,
                'y': self.y + math.sin(angle) * dist * 0.5,
                'vy': -random.uniform(1, 3),
                'life': random.uniform(0.5, 1.0),
                'size': random.randint(2, 5),
            })
        
        for s in self.sparkles:
            s['y'] += s['vy'] * dt
            s['life'] -= dt
        self.sparkles = [s for s in self.sparkles if s['life'] > 0]
    
    def render(self, screen, camera):
        screen_x, screen_y = camera.world_to_screen(self.x, self.y)
        
        # Draw dome
        dome_size = int(80 * camera.zoom)
        dome_height = int(60 * camera.zoom)
        alpha = int(100 * self.dome_alpha)
        dome_surf = pygame.Surface((dome_size * 2, dome_height * 2), pygame.SRCALPHA)
        pygame.draw.ellipse(dome_surf, (255, 255, 200, alpha), (0, dome_height // 2, dome_size * 2, dome_height))
        pygame.draw.ellipse(dome_surf, (255, 255, 150, alpha + 50), (0, dome_height // 2, dome_size * 2, dome_height), 3)
        screen.blit(dome_surf, (screen_x - dome_size, screen_y - dome_height))
        
        # Draw sparkles
        for s in self.sparkles:
            screen_pos = camera.world_to_screen(s['x'], s['y'])
            pygame.draw.circle(screen, (255, 255, 200), screen_pos, s['size'])


class RegenerationEffect(Effect):
    """Pulsing green healing waves."""
    
    def __init__(self, x, y):
        super().__init__(x, y, duration=1.5)
        self.waves = []
        self.wave_timer = 0
    
    def update(self, dt):
        super().update(dt)
        
        # Spawn waves
        self.wave_timer += dt
        if self.wave_timer > 0.3 and len(self.waves) < 4:
            self.wave_timer = 0
            self.waves.append({'radius': 0, 'alpha': 200})
        
        for w in self.waves:
            w['radius'] += dt * 2
            w['alpha'] = max(0, w['alpha'] - dt * 100)
        self.waves = [w for w in self.waves if w['alpha'] > 0]
    
    def render(self, screen, camera):
        screen_x, screen_y = camera.world_to_screen(self.x, self.y)
        
        for w in self.waves:
            radius = int(w['radius'] * 30 * camera.zoom)
            alpha = int(w['alpha'])
            if radius > 0:
                wave_surf = pygame.Surface((radius * 2 + 10, radius * 2 + 10), pygame.SRCALPHA)
                pygame.draw.circle(wave_surf, (100, 255, 100, alpha), (radius + 5, radius + 5), radius, 3)
                screen.blit(wave_surf, (screen_x - radius - 5, screen_y - radius - 5))
        
        # Center glow
        glow_size = int(15 * camera.zoom)
        glow_surf = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (150, 255, 150, 150), (glow_size, glow_size), glow_size)
        screen.blit(glow_surf, (screen_x - glow_size, screen_y - glow_size))


class ReviveEffect(Effect):
    """Bright upward light beam with sparkles."""
    
    def __init__(self, x, y):
        super().__init__(x, y, duration=1.2)
        self.sparkles = []
    
    def update(self, dt):
        super().update(dt)
        
        # Spawn sparkles rising up
        if random.random() < 0.5:
            self.sparkles.append({
                'x': self.x + random.uniform(-0.5, 0.5),
                'y': self.y,
                'vy': -random.uniform(3, 6),
                'life': random.uniform(0.5, 1.0),
                'size': random.randint(3, 7),
            })
        
        for s in self.sparkles:
            s['y'] += s['vy'] * dt
            s['life'] -= dt
        self.sparkles = [s for s in self.sparkles if s['life'] > 0]
    
    def render(self, screen, camera):
        screen_x, screen_y = camera.world_to_screen(self.x, self.y)
        
        # Light beam
        beam_width = int(20 * camera.zoom)
        beam_height = int(80 * camera.zoom)
        alpha = int(150 * (1 - self.progress))
        beam_surf = pygame.Surface((beam_width, beam_height), pygame.SRCALPHA)
        pygame.draw.rect(beam_surf, (255, 255, 200, alpha), (0, 0, beam_width, beam_height))
        screen.blit(beam_surf, (screen_x - beam_width // 2, screen_y - beam_height))
        
        # Sparkles
        for s in self.sparkles:
            screen_pos = camera.world_to_screen(s['x'], s['y'])
            pygame.draw.circle(screen, (255, 255, 220), screen_pos, s['size'])


class PoisonCloudEffect(Effect):
    """Toxic green cloud with skull particles."""
    
    def __init__(self, x, y):
        super().__init__(x, y, duration=2.0)
        self.puffs = []
        self.spawn_timer = 0
    
    def update(self, dt):
        super().update(dt)
        
        # Spawn cloud puffs
        self.spawn_timer += dt
        if self.spawn_timer > 0.1 and self.progress < 0.8:
            self.spawn_timer = 0
            angle = random.uniform(0, math.pi * 2)
            dist = random.uniform(0, 1.5)
            self.puffs.append({
                'x': self.x + math.cos(angle) * dist,
                'y': self.y + math.sin(angle) * dist * 0.5,
                'size': random.uniform(15, 30),
                'life': random.uniform(0.8, 1.5),
                'drift_x': random.uniform(-0.5, 0.5),
                'drift_y': random.uniform(-0.3, 0.3),
            })
        
        for p in self.puffs:
            p['x'] += p['drift_x'] * dt
            p['y'] += p['drift_y'] * dt
            p['life'] -= dt
        self.puffs = [p for p in self.puffs if p['life'] > 0]
    
    def render(self, screen, camera):
        for p in self.puffs:
            screen_pos = camera.world_to_screen(p['x'], p['y'])
            size = int(p['size'] * camera.zoom * (p['life'] / 1.5))
            alpha = min(150, int(150 * (p['life'] / 1.5)))
            if size > 0:
                puff_surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
                pygame.draw.circle(puff_surf, (100, 180, 50, alpha), (size, size), size)
                screen.blit(puff_surf, (screen_pos[0] - size, screen_pos[1] - size))


class EntangleEffect(Effect):
    """Vines rising from the ground."""
    
    def __init__(self, x, y):
        super().__init__(x, y, duration=1.5)
        self.vines = []
        for i in range(6):
            angle = i * (math.pi / 3)
            self.vines.append({
                'angle': angle,
                'progress': 0,
                'max_length': random.uniform(1.0, 1.5),
            })
    
    def update(self, dt):
        super().update(dt)
        
        for v in self.vines:
            if self.progress < 0.5:
                v['progress'] = min(1.0, v['progress'] + dt * 3)
            else:
                v['progress'] = max(0, v['progress'] - dt * 2)
    
    def render(self, screen, camera):
        screen_x, screen_y = camera.world_to_screen(self.x, self.y)
        
        for v in self.vines:
            if v['progress'] > 0:
                length = v['progress'] * v['max_length']
                segments = 5
                prev_pos = (screen_x, screen_y)
                for s in range(segments):
                    seg_progress = (s + 1) / segments
                    angle = v['angle'] + math.sin(seg_progress * math.pi * 2) * 0.3
                    dist = length * seg_progress
                    vx = self.x + math.cos(angle) * dist
                    vy = self.y + math.sin(angle) * dist * 0.5 - seg_progress * 0.5
                    curr_pos = camera.world_to_screen(vx, vy)
                    thickness = int((4 - s * 0.5) * camera.zoom)
                    pygame.draw.line(screen, (80, 160, 60), prev_pos, curr_pos, max(1, thickness))
                    prev_pos = curr_pos


class SummonEffect(Effect):
    """Magical summoning circle with rising entity."""
    
    def __init__(self, x, y, color=(120, 110, 100)):
        super().__init__(x, y, duration=1.5)
        self.color = color
        self.particles = []
        self.rotation = 0
    
    def update(self, dt):
        super().update(dt)
        self.rotation += dt * 4
        
        # Spawn particles rising
        if random.random() < 0.4 and self.progress < 0.8:
            angle = random.uniform(0, math.pi * 2)
            self.particles.append({
                'x': self.x + math.cos(angle) * 1.0,
                'y': self.y + math.sin(angle) * 0.5,
                'vy': -random.uniform(2, 4),
                'life': random.uniform(0.5, 1.0),
            })
        
        for p in self.particles:
            p['y'] += p['vy'] * dt
            p['life'] -= dt
        self.particles = [p for p in self.particles if p['life'] > 0]
    
    def render(self, screen, camera):
        screen_x, screen_y = camera.world_to_screen(self.x, self.y)
        
        # Summoning circle
        circle_size = int(50 * camera.zoom)
        for i in range(3):
            offset = i * (math.pi * 2 / 3)
            angle = self.rotation + offset
            cx = screen_x + int(math.cos(angle) * circle_size * 0.7)
            cy = screen_y + int(math.sin(angle) * circle_size * 0.35)
            pygame.draw.circle(screen, self.color, (cx, cy), int(8 * camera.zoom))
        
        # Outer ring
        pygame.draw.ellipse(screen, self.color, 
                           (screen_x - circle_size, screen_y - circle_size // 2,
                            circle_size * 2, circle_size), 2)
        
        # Rising particles
        for p in self.particles:
            screen_pos = camera.world_to_screen(p['x'], p['y'])
            pygame.draw.circle(screen, self.color, screen_pos, 4)


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
    
    def spawn_spell(self, spell_name, start_x, start_y, target_x, target_y, extra_targets=None, 
                    damage=0, damage_target=None, caster=None):
        """Spawn a spell effect with optional delayed damage."""
        if spell_name == 'fireball':
            bolt = FireballEffect(start_x, start_y, target_x, target_y)
            bolt.spawn_impact_on_finish = True
            bolt.impact_color = (255, 100, 50)
            bolt.effects_manager = self
            bolt.damage = damage
            bolt.damage_target = damage_target
            bolt.caster = caster
            self.effects.append(bolt)
        elif spell_name == 'ice_shard':
            bolt = IceShardEffect(start_x, start_y, target_x, target_y)
            bolt.spawn_impact_on_finish = True
            bolt.impact_color = (150, 200, 255)
            bolt.effects_manager = self
            bolt.damage = damage
            bolt.damage_target = damage_target
            bolt.caster = caster
            self.effects.append(bolt)
        elif spell_name == 'lightning_bolt':
            bolt = LightningBoltEffect(start_x, start_y, target_x, target_y)
            bolt.spawn_impact_on_finish = True
            bolt.impact_color = (200, 200, 255)
            bolt.effects_manager = self
            bolt.damage = damage
            bolt.damage_target = damage_target
            bolt.caster = caster
            self.effects.append(bolt)
        elif spell_name == 'chain_lightning':
            # Chain lightning needs multiple target positions
            positions = [(start_x, start_y), (target_x, target_y)]
            if extra_targets:
                positions.extend(extra_targets)
            effect = ChainLightningEffect(positions)
            effect.damage = damage
            effect.damage_target = damage_target
            effect.caster = caster
            effect.extra_targets = extra_targets or []
            self.effects.append(effect)
        elif spell_name == 'meteor':
            effect = MeteorEffect(target_x, target_y)
            effect.damage = damage
            effect.damage_target = damage_target
            effect.caster = caster
            self.effects.append(effect)
        elif spell_name == 'inferno':
            # Big fiery explosion
            effect = InfernoEffect(target_x, target_y)
            self.effects.append(effect)
        elif spell_name == 'blizzard':
            # Swirling ice storm
            effect = BlizzardEffect(target_x, target_y)
            self.effects.append(effect)
        elif spell_name == 'armageddon':
            # Rain of fire around caster
            effect = ArmageddonEffect(start_x, start_y)
            self.effects.append(effect)
        elif spell_name in ('heal', 'group_heal'):
            self.effects.append(HealEffect(target_x, target_y))
        elif spell_name == 'sanctuary':
            # Golden dome heal
            effect = SanctuaryEffect(target_x, target_y)
            self.effects.append(effect)
        elif spell_name == 'regeneration':
            # Pulsing green aura
            effect = RegenerationEffect(target_x, target_y)
            self.effects.append(effect)
        elif spell_name == 'revive':
            self.effects.append(ReviveEffect(target_x, target_y))
        elif spell_name == 'poison_cloud':
            effect = PoisonCloudEffect(target_x, target_y)
            self.effects.append(effect)
        elif spell_name == 'entangle':
            effect = EntangleEffect(target_x, target_y)
            self.effects.append(effect)
        elif spell_name == 'summon_wolf':
            effect = SummonEffect(target_x, target_y, color=(120, 110, 100))
            self.effects.append(effect)
        else:
            # Generic magic bolt
            bolt = SpellBoltEffect(start_x, start_y, target_x, target_y)
            bolt.spawn_impact_on_finish = True
            bolt.effects_manager = self
            self.effects.append(bolt)
    
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

