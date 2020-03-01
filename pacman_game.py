import time
import sys
import pygame as pg
from pygame.locals import *
from pygame.sprite import Sprite
from vector import Vector


# -------------------------------------------------------------------------------------
class Node(Sprite):

    def __init__(self, game):
        super().__init__()
        self.game = game
        self.screen = self.game.surface

        self.image = pg.image.load('images/pebble.png')
        self.rect = self.image.get_rect()

        self.rect.left = self.rect.width
        self.rect.top = self.rect.height
        self.x = float(self.rect.x)

    def width(self): return self.rect.width

    def height(self): return self.rect.height

    def check_edges(self):
        r = self.rect
        s_r = self.screen.get_rect()
        return r.right >= s_r.right or r.left <= 0

    def draw(self): self.screen.blit(self.image, self.rect)

    def update(self):
        self.draw()


# -------------------------------------------------------------------------------------
class Grid:

    def __init__(self, game):
        self.dir = 0
        self.nodes = pg.sprite.Group()
        self.screen = game.surface
        self.game = game

        # Static Nodes
        self.create_node(n=9, row=18)
        self.create_node(n=13, row=18)
        self.create_node(n=17, row=18)

    def create_node(self, n, row):
        node = Node(game=self.game)
        rect = node.rect
        width, height = rect.size
        node.x = width + 2 * n * width
        rect.x = node.x
        rect.y = rect.height + 2 * height * row
        self.nodes.add(node)

    def check_ship_hit(self):
        if pg.sprite.spritecollideany(self.game.player, self.nodes):
            self.nodes.remove()
            # print('Ship HIT!') if self.game.player.velocity.x != 0 or self.game.player.velocity.y != 0:
            # self.game.player.velocity.x, self.game.player.velocity.y = 0, 0
        return

    def update(self):
        self.check_ship_hit()
        self.nodes.update()


def game_over():
    print("GAME OVER.")
    quit()


# -------------------------------------------------------------------------------------
class Player:
    SPEED = 6

    def __init__(self, rect, velocity=Vector()):
        self.pacAnimation = ['images/pac0.png', 'images/pac1.png', 'images/pac2.png']
        self.currentFrame, self.currentAngle, self.animationDirection = 0, 0, 0
        self.rect = rect
        self.velocity = velocity
        self.player = pg.Rect(300, 100, 50, 50)
        self.image = pg.transform.rotozoom(pg.image.load(self.pacAnimation[self.currentFrame]),
                                           self.currentAngle, 0.06)

    def __repr__(self):
        return "Player(rect={},velocity={})".format(self.rect, self.velocity)

    def change_frame(self):
        if self.velocity == Vector():
            return
        if self.animationDirection == 0:
            if self.currentFrame == 0:
                self.currentFrame = 1
            elif self.currentFrame == 1:
                self.currentFrame = 2
            else:
                self.animationDirection = 1
        else:
            if self.currentFrame == 2:
                self.currentFrame = 1
            elif self.currentFrame == 1:
                self.currentFrame = 0
            else:
                self.animationDirection = 0

    def limit_to_screen(self, game):
        self.rect.top = max(0, min(game.WINDOW_HEIGHT - self.rect.height - 55, self.rect.top))
        self.rect.left = max(0, min(game.WINDOW_WIDTH - self.rect.width + 35, self.rect.left))

    def move_ip(self, game):
        if self.velocity == Vector():
            return
        self.rect.move_ip(self.velocity.x, self.velocity.y)
        self.limit_to_screen(game)

    def move(self, game):
        if self.velocity == Vector():
            return
        tempX = self.velocity.x
        tempY = self.velocity.y
        self.rect.left += self.velocity.x
        self.rect.top += self.velocity.y
        if tempX != 0 or tempY != 0:
            self.change_frame()
        if self.velocity.x > 0:
            self.currentAngle = 0
        elif self.velocity.x < 0:
            self.currentAngle = 180
        elif self.velocity.y > 0:
            self.currentAngle = -90
        else:
            self.currentAngle = 90

        self.limit_to_screen(game)

    def check_collisions(self, game):
        pass

    def draw(self, game):
        self.image = pg.transform.rotozoom(pg.image.load(self.pacAnimation[self.currentFrame]),
                                           self.currentAngle, 0.06)
        game.surface.blit(self.image, self.rect)

    def update(self, game):
        self.check_collisions(game=game)
        self.move(game=game)
        # self.change_frame()
        self.draw(game=game)


# -------------------------------------------------------------------------------------
class Audio:  # sound(s) and background music
    def __init__(self, sounds, playing):
        self.sounds = {}
        for sound in sounds:
            for k, v in sound.items():
                self.sounds[k] = pg.mixer.Sound(v)

        self.playing = playing

    def play_sound(self, sound):
        if self.playing and sound in self.sounds.keys():
            self.sounds[sound].play()

    def toggle(self):
        self.playing = not self.playing
        pg.mixer.music.play(-1, 0.0) if self.playing else pg.mixer.music.stop()

    def game_over(self, game):
        pg.playing = False
        pg.mixer.music.stop()
        self.play_sound(game.GAME_OVER_SOUND)


# -------------------------------------------------------------------------------------
class Game:
    def __init__(self, title):
        pg.init()
        logo = pg.image.load('images/pac2.png')
        pg.display.set_icon(logo)
        self.WINDOW_WIDTH, self.WINDOW_HEIGHT = 550, 700
        self.font = pg.font.SysFont(None, 48)
        self.player = Player(pg.Rect(259, 363, 50, 50), Vector())

        # Audio
        self.intro_src = 'sounds/start-music.mp3'
        # self.background_src = 'sounds/ghost-normal-move.ogg'
        self.PICKUP_SOUND, self.GAME_OVER_SOUND = 0, 1
        sounds = [{self.PICKUP_SOUND: 'sounds/pickup.wav',
                   self.GAME_OVER_SOUND: 'sounds/game_over.wav'}]
        self.audio = Audio(sounds=sounds, playing=True)

        self.finished = False
        self.BLACK = (0, 0, 0)
        self.BACKGROUND_COLOR = self.BLACK
        self.WALL_COLOR = (255, 0, 0)
        self.FPS = 60

        pg.display.set_caption(title)
        self.surface = pg.display.set_mode((self.WINDOW_WIDTH, self.WINDOW_HEIGHT), 0, 32)
        self.grid = Grid(self)
        self.bImage = pg.image.load('images/pacGrid.png')
        self.mainClock = pg.time.Clock()

    @staticmethod
    def wait_for_key_press():
        key_pressed = False
        while not key_pressed:
            for e in pg.event.get():
                if e.type == QUIT or e.type == KEYDOWN and e.key == K_ESCAPE:
                    Game.terminate()
                elif e.type == KEYDOWN:
                    key_pressed = True

    def process_event_loop(self, event):
        # speed = Player.SPEED
        e_type = event.type
        movement = {K_a: Vector(-1, 0), K_d: Vector(1, 0), K_w: Vector(0, -1), K_s: Vector(0, 1)}
        translate = {K_LEFT: K_a, K_RIGHT: K_d, K_UP: K_w, K_DOWN: K_s}
        left_right_up_down = (K_LEFT, K_a, K_RIGHT, K_d, K_UP, K_w, K_DOWN, K_s)
        x_z = (K_x, K_z)

        if e_type == KEYDOWN or e_type == KEYUP:
            k = event.key
            if k == K_m and e_type == KEYUP:
                pg.mixer.music.stop()
            elif k in x_z:
                if e_type == KEYDOWN:
                    pass
                elif e_type == KEYUP:
                    pass
            elif k in left_right_up_down:
                if k in translate.keys():
                    k = translate[k]
                self.player.velocity = Player.SPEED * movement[k]
            elif k == K_x:
                pass
        elif e_type == QUIT or (e_type == KEYUP and event.key == K_ESCAPE):
            self.finished = True
        elif e_type == MOUSEBUTTONUP:
            pass

    def update(self):
        self.surface.fill(self.BACKGROUND_COLOR)
        self.surface.blit(self.bImage, (0, 46))
        self.grid.update()

        # 2 Red Rectangles
        # pg.draw.rect(self.surface, self.WALL_COLOR, (0, 46, 29, 260))
        # pg.draw.rect(self.surface, self.WALL_COLOR, (0, 335, 29, 319))

        self.player.update(game=self)
        pg.display.update()

    def menu(self):
        self.surface.fill(self.BACKGROUND_COLOR)

        # Wait for Keypress To Move To Next State
        key_pressed = False
        while not key_pressed:
            for e in pg.event.get():
                if e.type == QUIT or e.type == KEYDOWN and e.key == K_ESCAPE:
                    Game.terminate()
                elif e.type == KEYDOWN and e.key == K_SPACE:
                    key_pressed = True
        self.play()

    def play(self):
        pg.mixer.music.load(self.intro_src)
        pg.mixer.music.play(1, 0.0)
        while not self.finished:
            for event in pg.event.get():
                self.process_event_loop(event)

            self.update()
            # can't move until intro music stops
            while pg.mixer.music.get_busy():
                time.sleep(1)
            time.sleep(0.02)
            self.mainClock.tick(self.FPS)
        Game.terminate()

    @staticmethod
    def terminate():
        pg.quit()
        sys.exit()


# -------------------------------------------------------------------------------------
def main():
    game = Game(title='Pac-Man')
    game.menu()


# -------------------------------------------------------------------------------------
if __name__ == '__main__':
    main()
