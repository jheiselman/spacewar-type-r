import os
import math
import pygame
from lava.primitives import *
from lava.media import MediaManager

mediaman = MediaManager()

class Star(GLSprite):
    def __init__(self, world, startx, starty):
        GLSprite.__init__(self)
        self.gravityEffect = world.g_collision
        self.can_die = False
        self.to_hit = 32000

        self.load_texture(mediaman.load_image('sun.png', 'images'))
        self.width = self.height = 50
        self.radius = 19
        
        self.x = startx
        self.y = starty
        self.vx = 0.0
        self.vy = 0.0
        self.facing = 0.0

    def update(self, interval):
        # Divide by 4 to fake a larger mass
        self.x += (self.vx / 4) * interval
        self.y += (self.vy / 4) * interval

    def gravitate(self, interval):
        for sprite in self.gravityEffect.iterate_sprites():
            rad = self.radius * self.scale
            # Get vector: from self to sprite
            vector = (sprite.x - self.x, sprite.y - self.y)
            # Find radian angle of vector, reverse direction
            angle = math.atan2(vector[1], vector[0]) - math.pi
            # Get distance, adjust for self's radius
            distance = math.sqrt(vector[0] ** 2 + vector[1] ** 2) - rad
            if distance > 0:
                r = distance / 200 + 1
                # Gravity calculation
                force = 0.15 / 1000 / (r ** 2) * interval
            else:
                force = 0.0
            (gx, gy) = sincos(angle, force)
            sprite.vx += gx
            sprite.vy += gy

    
class Ship(GLSprite):
    def __init__(self, world, name = "Unknown", image = 'ship.png'):
        GLSprite.__init__(self)
        self.can_die = True
        self.world = world
        self.name = name
        
        self.load_texture(mediaman.load_image(image, 'images'))
        self.width = self.height = 40
        self.radius = 18

        # Starting position and orientation
        self.facing = 0.0
        self.x = 0.0
        self.y = 0.0
        self.vx = 0.0
        self.vy = 0.0

        # Movement attributes
        self.accel = 0.15 / 1000.0
        self.maxspeed = 0.3
        self.turn_rate = 0.2
        self.turn = 0

        # Ship attributes
        self.life = 3
        self.gun_ready = True
        self.fire_rate = 400
        self.last_fired = 0
        self.score = 0

    def update(self, interval):
        self.x += self.vx * interval
        self.y += self.vy * interval
        self.facing += self.turn * interval
        self.facing %= 360
        
        if not self.gun_ready:
            ticks = pygame.time.get_ticks()
            if ticks - self.last_fired > self.fire_rate:
               self.gun_ready = True

    def fire(self):
        if not self.gun_ready:
            return None
            
        if not self.alive():
            return None
            
        self.last_fired = pygame.time.get_ticks()
        self.gun_ready = False

        Torpedo(self)
        
    def thrust(self, interval):
        radian = math.radians(self.facing + 90)
        (vx, vy) = sincos(radian, self.accel)
        self.vx += vx * interval
        self.vy += vy * interval

        current_speed = math.sqrt(self.vx ** 2 + self.vy ** 2)

        if current_speed > self.maxspeed:
            multiple =  self.maxspeed / current_speed
            self.vx *= multiple
            self.vy *= multiple
    
    def reverse_thrust(self, interval):
        radian = math.radians(self.facing + 90)
        (vx, vy) = sincos(radian, (self.accel / 2))
        self.vx -= vx * interval
        self.vy -= vy * interval
        
        current_speed = math.sqrt(self.vx ** 2 + self.vy ** 2)
        
        if current_speed > self.maxspeed:
            multiple = self.maxspeed / current_speed
            self.vx *= multiple
            self.vy *= multiple

    def rotate(self, multiplier):
        self.turn = self.turn_rate * multiplier

    def take_damage(self, attacker):
        self.life -= attacker.to_hit
        
        ParticleEmitter(self, 3)
        
        if self.life <= 0:
            self.kill()
            
    def kill(self):
        if self.alive():
            ParticleEmitter(self, 10)
            GLSprite.kill(self)        


class Torpedo(GLSprite):
    def __init__(self, parent):
        GLSprite.__init__(self)
        self.parent = parent
        self.name = "torpedo"
        self.can_die = True
        self.to_hit = 1
        
        self.load_texture(mediaman.load_image('torpedo.png', 'images'))
        
        self.width = self.height = 6
        self.radius = 4

        # Starting position
        self.facing = parent.facing
        angle = math.radians(self.facing + 90)
        distance = parent.radius * parent.scale + self.radius * self.scale
        (sx, sy) = sincos(angle, distance + 1)
        self.x = parent.x + sx
        self.y = parent.y + sy

        # Velocity and TTL
        speed = 0.3
        self.life = 1500
        (tx, ty) = sincos(angle, speed)
        self.vx = parent.vx + tx
        self.vy = parent.vy + ty

        # Add to world
        parent.world.g_render.add(self)
        parent.world.g_collision.add(self)
        
    def update(self, interval):
        self.x += self.vx * interval
        self.y += self.vy * interval
        self.life -= interval
        
        if self.life <= 0:
            self.kill()
