#!/usr/bin/env python
import sys
import math
import random
from actors import *
from lava.config import ConfigManager
from lava.physics import radial_collide
from lava.levels import LevelManager

# Wrap foreign imports in try/except clauses
try:
    import pygame
except ImportError:
    sys.exit("Pygame was not found")
else:
    from pygame.locals import *

try:
    from OpenGL.GL import *
except ImportError:
    sys.exit("PyOpenGL was not found")

try:
    import psyco
except ImportError:
    print("psyco not found")
else:
    print("enabling psyco")
    from psyco.classes import *
    psyco.full()
# End of the imports


class Game(Scene):
    def __init__(self, config, grid, level_file):
        Scene.__init__(self, grid)
        self.lm = LevelManager("levels")
        self.config = config
        self.keys = config.keys
        self.blend = True
        self.console = Console()
        self.spawn_points = list()
        self.grid = grid

        self.g_background = GLSpriteGroup()
        self.g_spawns = GLSpriteGroup()
        self.g_stars = GLSpriteGroup()
        self.g_ships = GLSpriteGroup()
        self.g_collision = GLSpriteGroup()
        self.g_render = GLSpriteGroup()
        self.g_hud = GLSpriteGroup()
        self.load_level(level_file)
        
        pygame.time.set_timer(USEREVENT, 1000)

    def tick(self, interval):
        """ Functions called every frame """
        self.g_render.update(interval)
        [self.check_bounds(sprite) for sprite in self.g_collision]
        self.draw_screen()
        
    def static_tick(self, interval):
        """ Functions called at a rate near 40 fps """
        [self.handle_events(event) for event in pygame.event.get()]
        self.handle_keydown(interval)
        [sprite.gravitate(interval) for sprite in self.g_stars]
        [self.world_collision(sprite) for sprite in self.g_ships]
        [self.world_collision(sprite) for sprite in self.g_stars]

    def world_collision(self, sprite1):
        """ Run radial_collide() for sprite1 against all g_collision sprites """
        [self.detect_collision(sprite1, sprite2) for sprite2 in self.g_collision]

    def detect_collision(self, sprite1, sprite2):
        if sprite1 is sprite2:
            return
            
        simple_description1 = (sprite1.x, sprite1.y, sprite1.scaled_radius)
        simple_description2 = (sprite2.x, sprite2.y, sprite2.scaled_radius)
        
        if radial_collide(simple_description1, simple_description2):
            self.collide(sprite1, sprite2)

    def collide(self, entity1, entity2):
        """ Perform different actions depending on what is colliding """
        if isinstance(entity1, Ship) and isinstance(entity2, Ship):
            entity1.score -= 1
            entity2.score -= 1
            self.console.write("%s and %s got a little too close" % (entity1.name, entity2.name))
            entity1.kill()
            entity2.kill()

        elif isinstance(entity1, Ship) and isinstance(entity2, Torpedo):
            entity1.take_damage(entity2)
            attacker = entity2.parent
            entity2.kill()
            del entity2
            self.console.write("%s was attacked by %s" % (entity1.name, attacker.name))
             
            if not entity1.alive():
                if entity1 is attacker:
                    self.console.write("%s ends it all." % entity1.name)
                    entity1.score -= 1
                    if entity1.score <= -10:
                        self.console.write("%s WON!" % attacker.name)
                        self.load_level(self.level.next_level)
                else:
                    self.console.write("%s was shot down by %s" % (entity1.name, attacker.name))
                    attacker.score += 1
                    if attacker.score >= 10 or entity1.score <= -10:
                        self.console.write("%s WON!" % attacker.name)
                        self.load_level(self.level.next_level)

        elif isinstance(entity1, Star) and not isinstance(entity2, Star):
            entity2.kill()
            if isinstance(entity2, Ship):
                self.console.write("%s did a backflip into the lava" % (entity2.name))
                entity2.score -= 1
                if entity2.score <= -10:
                    self.console.write("%s is done" % entity2.name)
                    self.load_level(self.level.next_level)

        self.score1.update_string(self.ship1.score)
        self.score2.update_string(self.ship2.score)

    def handle_events(self, event):
        if not self.running:
            return
        if event.type == QUIT or (event.type == KEYDOWN and
                                  event.key == K_ESCAPE):
            self.running = False
            pygame.quit()
        if event.type == USEREVENT:
            self.print_fps()
        elif event.type == KEYDOWN:
            keys = self.keys
            if event.key == keys['restart']:
                self.console.write("Restarting World")
                self.load_level()
            elif event.key == keys['kill_ship1']:
                self.ship1.kill()
                self.ship1.score -= 1
            elif event.key == keys['kill_ship2']:
                self.ship2.kill()
                self.ship2.score -= 1
            elif event.key == keys['scale_ship1']:
                if self.ship1.scale == 1.0:
                    self.ship1.scale = 2.0
                else:
                    self.ship1.scale = 1.0
            elif event.key == keys['scale_ship2']:
                if self.ship2.scale == 1.0:
                    self.ship2.scale = 2.0
                else:
                    self.ship2.scale = 1.0
            elif event.key == keys['toggle_blend']:
                if self.blend:
                    self.blend = False
                    glDisable(GL_BLEND)
                    self.console.write("Turning blending off")
                else:
                    self.blend = True
                    glEnable(GL_BLEND)
                    self.console.write("Turning blending on")
                    
    def handle_keydown(self, interval):
        if not self.running:
            return

        ship1 = self.ship1
        ship2 = self.ship2
        keys = self.keys
        
        pressed = pygame.key.get_pressed()
        if pressed[keys['forward_ship1']]:
            ship1.thrust(interval)
        elif pressed[keys['reverse_ship1']]:
            ship1.reverse_thrust(interval)
        if pressed[keys['right_ship1']]:
            ship1.rotate(-1)
        elif pressed[keys['left_ship1']]:
            ship1.rotate(1)
        else:
            ship1.rotate(0)
        if pressed[keys['fire_ship1']]:
            if ship1.alive():
                ship1.fire()
            else:
                self.respawn(ship1)
            
        if pressed[keys['forward_ship2']]:
            ship2.thrust(interval)
        elif pressed[keys['reverse_ship2']]:
            ship2.reverse_thrust(interval)
        if pressed[keys['right_ship2']]:
            ship2.rotate(-1)
        elif pressed[keys['left_ship2']]:
            ship2.rotate(1)
        else:
            ship2.rotate(0)
        if pressed[keys['fire_ship2']]:
            if ship2.alive():
                ship2.fire()
            else:
                self.respawn(ship2)

    def check_bounds(self, sprite):
        if sprite.x > self.size[0]:
            sprite.x -= self.size[0]
        elif sprite.x < 0:
            sprite.x += self.size[0]
        if sprite.y > self.size[1]:
            sprite.y -= self.size[1]
        elif sprite.y < 0:
            sprite.y += self.size[1]

    def respawn(self, player):
        x = random.randrange(0, len(self.spawn_points))
        self.spawn_points[x].spawn(player)

        player.life = 3
        self.g_ships.add(player)
        self.g_render.add(player)
        self.g_collision.add(player)

    def load_level(self, level_file):
        if level_file:
            width = self.grid[0]
            height = self.grid[1]
        
            self.g_background.empty()
            self.g_spawns.empty()
            self.g_stars.empty()
            self.g_ships.empty()
            self.g_collision.empty()
            self.g_render.empty()
            self.g_hud.empty()

            self.level = self.lm.load(level_file)
            print("Working with level file %s" % self.level.file)

            # load background specified in level file
            self.bkg = Background((width, height), self.level.background)

            # load the static sprites from the level def
            for static_entity_name in self.level.static_entities:
                entity_data = self.level.static_entities[static_entity_name]

                # specific routines for different classes
                if entity_data['class'] == "Star":
                    if entity_data['pos_x'] == "center":
                        x = width / 2
                    else:
                        x = entity_data['pos_x']

                    if entity_data['pos_y'] == "center":
                        y = height / 2
                    else:
                        y = entity_data['pos_y']

                    entity = Star(self, x, y)
                    entity.vx = entity_data['vel_x']
                    entity.vy = entity_data['vel_y']
                    self.g_stars.add(entity)

                self.g_collision.add(entity)
                self.g_render.add(entity)

            # load spawn points from level def
            for spawn_point_name in self.level.spawn_points:
                spawn_point = self.level.spawn_points[spawn_point_name]
                self.spawn_points.append(SpawnPoint(spawn_point['pos_x'], spawn_point['pos_y'], spawn_point['facing']))

            # load up ships
            # TODO: Make this controlled from the level info and config info
            self.ship1 = Ship(self, name = self.config.player1_name)
            self.ship2 = Ship(self, name = self.config.player2_name, image = 'ship2.png')

            player1 = GLText(self.ship1.name, 20, height - 20, halign='left')
            player2 = GLText(self.ship2.name, width - 20, height - 20, halign='right')
            self.score1 = GLText(self.ship1.score, player1.x, height - 55, size=50)
            self.score2 = GLText(self.ship2.score, player2.x, height - 55, size=50)

            self.g_background.add(self.bkg)
            self.g_ships.add(self.ship1, self.ship2)
            self.g_collision.add(self.ship1, self.ship2)
            self.g_render.add(self.ship1, self.ship2)
            self.g_hud.add(player1, player2, self.score1, self.score2)

            self.spawn_points[0].spawn(self.ship1)
            self.spawn_points[3].spawn(self.ship2)
        else:
            self.running = False

    def print_fps(self):
        self.console.write("FPS: %2d" % self.clock.get_fps())


def init():
    glEnable(GL_TEXTURE_2D)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glShadeModel(GL_SMOOTH)
    glClearColor(0.0, 0.0, 0.0, 0.0)
    glClearDepth(1.0)
    glEnable(GL_DEPTH_TEST)
    glDepthFunc(GL_LEQUAL)

def resize(size):
    (width, height) = size
    if height == 0:
        height = 1

    aspect_ratio = "%.2f" % (float(width) / height)
    if aspect_ratio == "1.33":
        grid = (800, 600)
    elif aspect_ratio == "1.60":
        grid = (800, 500)
    else:
        raise SystemExit
    glViewport(0, 0, width, height)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluOrtho2D(0.0, float(grid[0]), 0.0, float(grid[1]))
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    
    return grid

def main(level = 'level1'):
    pygame.init()
    config = ConfigManager(filename = 'spacewar.cfg')
    screen = pygame.display.set_mode(config.resolution, OPENGL | DOUBLEBUF)
    pygame.display.set_caption('Spacewar Type-R')
    grid = resize(config.resolution)
    init()
    game = Game(config, grid, level)
    game.run()

if __name__ == '__main__':
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        main()
