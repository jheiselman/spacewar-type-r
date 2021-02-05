import os
import math
import random
import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import gluBuild2DMipmaps, gluOrtho2D
from lava.media import MediaManager

mediaman = MediaManager()

class GLSprite(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.name = "GLsprite"
        self.x = 0
        self.y = 0
        self.width = 0
        self.height = 0
        self.rect = None
        self.__radius = 0.0
        self.__scale = 1.0
        
    def get_radius(self):
        return self.__radius

    def set_radius(self, radius):
        self.__radius = radius
        self.scaled_radius = radius * self.scale
        
    radius = property(get_radius, set_radius)
    
    def get_scale(self):
        return self.__scale
        
    def set_scale(self, scale):
        self.__scale = scale
        self.scaled_radius = self.radius * scale
        
    scale = property(get_scale, set_scale)
    
    def draw(self):
        width = self.width / 2
        height = self.height / 2
        
        glLoadIdentity()

        glTranslate(self.x, self.y, 0.0)
        glRotatef(self.facing, 0.0, 0.0, 1.0)
        glScalef(self.scale, self.scale, 1.0)
        
        glBindTexture(GL_TEXTURE_2D, self.texture)

        glBegin(GL_QUADS)
        glTexCoord2f(0.0, 0.0); glVertex3f(-width, -height, 0.0)
        glTexCoord2f(1.0, 0.0); glVertex3f( width, -height, 0.0)
        glTexCoord2f(1.0, 1.0); glVertex3f( width,  height, 0.0)
        glTexCoord2f(0.0, 1.0); glVertex3f(-width,  height, 0.0)
        glEnd()
        
    def load_texture(self, image_ref):
        textureSurface = image_ref
        colorkey = textureSurface.get_at((0,0))
        textureSurface.set_colorkey(colorkey)
        
        rect = textureSurface.get_rect()
        textureData = pygame.image.tostring(textureSurface, "RGBA", 1)
       
        self.texture = glGenTextures(1)
        
        glBindTexture(GL_TEXTURE_2D, self.texture)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER,
                        GL_LINEAR_MIPMAP_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        gluBuild2DMipmaps(GL_TEXTURE_2D, GL_RGBA, textureSurface.get_width(),
                          textureSurface.get_height(), GL_RGBA,
                          GL_UNSIGNED_BYTE, textureData)
                          
        return rect.width, rect.height


class GLSpriteGroup(pygame.sprite.Group):
    def __init__(self, *args):
        pygame.sprite.Group.__init__(self, *args)

    def draw(self):
        for sprite in self.iterate_sprites():
            sprite.draw()

    def iterate_sprites(self):
        for sprite in self.sprites():
            yield sprite


class Background(GLSprite):
    def __init__(self, point, image):
        (x, y) = point
        GLSprite.__init__(self)
        
        self.x = x / 2
        self.y = y / 2
        self.width = x
        self.height = y
        self.load_texture(mediaman.load_image(image))

    def draw(self):
        width = self.width / 2
        height = self.height / 2
        
        glLoadIdentity()

        glTranslate(self.x, self.y, -0.5)

        glBindTexture(GL_TEXTURE_2D, self.texture)
        glColor(1.0, 1.0, 1.0, 0.5)
        glBegin(GL_QUADS)
        glTexCoord2f(0.0, 0.0); glVertex3f(-width, -height, 0.0)
        glTexCoord2f(1.0, 0.0); glVertex3f( width, -height, 0.0)
        glTexCoord2f(1.0, 1.0); glVertex3f( width,  height, 0.0)
        glTexCoord2f(0.0, 1.0); glVertex3f(-width,  height, 0.0)
        glEnd()
        glColor(1.0, 1.0, 1.0, 1.0)
        

class SpawnPoint(object):
    def __init__(self, x, y, facing):
        self.x = x
        self.y = y
        self.facing = facing

    def spawn(self, player):
        player.x = self.x
        player.y = self.y
        player.facing = self.facing
        
        radian = math.radians(self.facing + 90)
        (vx, vy) = sincos(radian, 0.01)
        player.vx = vx
        player.vy = vy


class ParticleEmitter(object):
    def __init__(self, parent, number):
        x = 0
        while x < number:
            Particle(parent)
            x += 1


class Particle(GLSprite):
    def __init__(self, parent):
        GLSprite.__init__(self)
        self.name = "particle"

        #self.load_texture(os.path.join('images', 'explode.gif'))
        self.load_texture(mediaman.load_image('explode.gif', 'images'))
        self.width = self.height = 10
        self.radius = 5

        # Starting position
        self.facing = parent.facing * random.random() * 100
        self.x = parent.x
        self.y = parent.y

        # Velocity and TTL
        self.life = 1000 
        self.vx = random.uniform(-0.09, 0.09)
        self.vy = random.uniform(-0.09, 0.09)

        # Add to world
        parent.world.g_render.add(self)
        
    def update(self, interval):
        self.x += self.vx * interval
        self.y += self.vy * interval
        self.life -= interval
        
        if self.life <= 0:
            self.kill()

    def draw(self):
        glColor(1.0, 1.0, 1.0, 0.5)
        GLSprite.draw(self)
        glColor(1.0, 1.0, 1.0, 1.0)


class GLText(GLSprite):
    def __init__(self, string, x, y, font='Vera.ttf', size=14,
                 valign='center', halign='center'):
        GLSprite.__init__(self)
        self.name = 'Text'
        self.string = ''

        self.x = x
        self.y = y
        self.size = size
        self.facing = 0

        self.width = 0
        self.height = 0
        self.valign = valign
        self.halign = halign

        pygame.font.init()
        self.font = pygame.font.Font(os.path.join('fonts', font), size)
        self.update_string(string)

    def update_string(self, new_string):
        if new_string == "" or new_string == None or self.string == new_string:
            return
        self.string = str(new_string)
        self.text = self.font.render(self.string, 1, (255, 255, 255))
        (self.width, self.height) = self.load_texture()

        if self.halign == 'left':
            self.x += self.width / 2
        elif self.halign == 'right':
            self.x -= self.width / 2

    def load_texture(self):
        text = self.text
        rect = text.get_rect()
        width = power2(rect.width)
        height = power2(rect.height)
        self.xTexScale = rect.width / float(width)
        self.yTexScale = rect.height / float(height)

        surface = pygame.Surface((width, height), SRCALPHA, 32)
        surface.blit(text, (0, 0))
        textureData = pygame.image.tostring(surface, "RGBA", 1)
        self.texture = glGenTextures(1)

        glBindTexture(GL_TEXTURE_2D, self.texture)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width,
                     height, 0, GL_RGBA, GL_UNSIGNED_BYTE, textureData)

        return rect.width, rect.height

    def draw(self):
        width = self.width / 2
        height = self.height / 2
        xTex = self.xTexScale
        yTex = 1.0 - self.yTexScale
        
        glLoadIdentity()

        glTranslate(self.x, self.y, 0.0)
        glRotatef(self.facing, 0.0, 0.0, 1.0)
        glScalef(self.scale, self.scale, 1.0)
        
        glBindTexture(GL_TEXTURE_2D, self.texture)

        glBegin(GL_QUADS)
        glTexCoord2f(0.0, yTex); glVertex3f(-width, -height, 0.0)
        glTexCoord2f(xTex, yTex); glVertex3f( width, -height, 0.0)
        glTexCoord2f(xTex, 1.0); glVertex3f( width,  height, 0.0)
        glTexCoord2f(0.0, 1.0); glVertex3f(-width,  height, 0.0)
        glEnd()


class Console(object):
    def __init__(self):
        pass

    def write(self, text):
        print(text)


class Scene(object):
    def __init__(self, screen_size):
        self.size = screen_size
        self.blend = False
        self.g_background = GLSpriteGroup()
        self.g_hud = GLSpriteGroup()
        self.g_render = GLSpriteGroup()
        
    def run(self):
        self.clock = pygame.time.Clock()
        self.running = True
        last_tick = this_tick = pygame.time.get_ticks()
        timer = 0
        
        while self.running:
            interval = self.clock.tick()
            timer += interval
            self.tick(interval)
            if timer >= 25:
                self.static_tick(timer)
                timer = 0

    def tick(self, timer):
        self.draw_screen()

    def static_tick(self, timer):
        pass
        
    def draw_screen(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        self.g_background.draw()
        self.g_render.draw()
        self.g_hud.draw()
        pygame.display.flip()
        

def power2(x):
    """power2(x) -> nearest power of two
    
    Calculate the nearest power of two that is equal
    or greater than x
    """
    p = math.log(x) / math.log(2)
    return 2**int(math.ceil(p))        

def sincos(angle, speed):
    vx = speed*math.cos(angle)
    vy = speed*math.sin(angle)
    return (vx, vy)
