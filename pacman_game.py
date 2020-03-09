import time
import sys
import pygame as pg
import random
from button import Button
from pygame.locals import *
from settings import Settings
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
        # for row in range(14, 121, 3):
        # for col in range(6, 50*2, 3):
        # self.create_node(n=col, row=row)

    def create_node(self, n, row):
        node = Node(game=self.game)
        rect = node.rect
        width, height = rect.size
        node.x = width + 2 * n * (width / 4)
        rect.x = node.x
        rect.y = rect.height + 2 * (height / 4) * row
        self.nodes.add(node)

    def check_hit(self):
        for i in range(len(self.game.bricks)):
            pg.sprite.spritecollide(self.game.bricks[i], self.nodes, True)
        if pg.sprite.spritecollide(self.game.player, self.nodes, True):
            self.game.audio.play_sound(0)
            self.game.score += 10
        if len(self.nodes) == 0:
            self.game.level += 1
            self.reset_grid()

    def reset_grid(self):
        for row in range(14, 121, 3):
            for col in range(6, 50 * 2, 3):
                self.create_node(n=col, row=row)

    def update(self):
        self.check_hit()
        self.nodes.update()


def game_over():
    print("GAME OVER.")
    quit()


# -------------------------------------------------------------------------------------
class Walls:

    def __init__(self, game):
        super().__init__()
        self.game = game
        self.screen = self.game.surface

        self.wall_list = pg.sprite.Group()

    def create_wall(self, left, top, width, height):
        wall = Node(game=self.game)
        wall.rect = (left, top, width, height)
        self.wall_list.add(wall)

    # def check_ship_hit(self):
    # pg.sprite.spritecollide(self.game.player, self.walls, True)

    # def update(self):
    # self.check_ship_hit()
    # self.nodes.update()


class Brick(Sprite):

    def __init__(self, game, width, height):
        Sprite.__init__(self)
        self.game = game
        self.image = self.game.surface([width, height])
        self.image.fill(color)
        self.rect = self.image.get_rect()


# -------------------------------------------------------------------------------------
class Player:
    SPEED = 6

    def __init__(self, rect, velocity=Vector()):
        self.pacAnimation = ['images/pac0.png', 'images/pac1.png', 'images/pac2.png']
        self.currentFrame, self.currentAngle, self.animationDirection = 0, 0, 0
        self.rect = rect
        self.velocity = velocity
        self.player = pg.Rect(300, 100, 25, 25)
        self.lives = 3
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
        self.rect.top = max(73, min(game.WINDOW_HEIGHT - self.rect.height - 80, self.rect.top))
        if 0 <= self.rect.left > game.WINDOW_HEIGHT:
            self.rect.left = max(-28, min(game.WINDOW_WIDTH - self.rect.width + 48, self.rect.left))
        elif self.rect.left < -30:
            self.rect.left = game.WINDOW_WIDTH
        elif self.rect.left > game.WINDOW_WIDTH:
            self.rect.left = -30

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

        if not self.check_collisions(game):
            self.rect.left += self.velocity.x
            self.rect.top += self.velocity.y
        if self.check_collisions(game):
            self.rect.left -= self.velocity.x
            self.rect.top -= self.velocity.y

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

    def check_ghosts(self, game):
        if self.rect.colliderect(game.blinky.rect) or self.rect.colliderect(game.pinky.rect) or \
                self.rect.colliderect(game.inky.rect) or self.rect.colliderect(game.clyde.rect):
            self.rect.left, self.rect.top = 259, 363
            game.blinky.rect.left, game.blinky.rect.top = 259, 250
            game.pinky.rect.left, game.pinky.rect.top = 259, 180
            game.inky.rect.left, game.inky.rect.top = 259, 150
            game.clyde.rect.left, game.clyde.rect.top = 259, 210
            self.lives -= 1

    def check_collisions(self, game):
        for j in range(len(game.walls)):
            if self.rect.colliderect(game.walls[j]):
                return True
        return False

    def draw(self, game):
        self.image = pg.transform.rotozoom(pg.image.load(self.pacAnimation[self.currentFrame]),
                                           self.currentAngle, 0.06)
        game.surface.blit(self.image, self.rect)

    def update(self, game):
        self.check_ghosts(game=game)
        self.check_collisions(game=game)
        self.move(game=game)
        self.draw(game=game)


# -------------------------------------------------------------------------------------
class Enemy:
    SPEED = 6

    def __init__(self, rect, velocity=Vector()):
        self.enemyAnimation = ['images/blinky0.png', 'images/blinky1.png', 'images/blinky2.png', 'images/blinky3.png',
                               'images/blinky4.png', 'images/blinky5.png', 'images/blinky6.png', 'images/blinky7.png']
        self.currentFrame, self.animationDirection = 0, 0
        self.startF, self.endF = 0, 1  # len(self.enemyAnimation) - 1
        self.rect = rect
        self.velocity = velocity
        self.enemy = pg.Rect(300, 100, 50, 50)
        self.image = pg.transform.rotozoom(pg.image.load(self.enemyAnimation[self.currentFrame]), 0, 0.06)

    def __repr__(self):
        return "Enemy(rect={},velocity={})".format(self.rect, self.velocity)

    def change_frame(self):
        if self.velocity == Vector():
            return
        if self.startF <= self.currentFrame < self.endF:
            self.currentFrame += 1
        else:
            self.currentFrame = self.startF

    def limit_to_screen(self, game):
        self.rect.top = max(73, min(game.WINDOW_HEIGHT - self.rect.height - 55, self.rect.top))
        if game.m == 0:
            self.rect.left = max(-28, min(game.WINDOW_WIDTH - self.rect.width + 48, self.rect.left))
        else:
            self.rect.left = max(-300, min(game.WINDOW_WIDTH - self.rect.width + 48, self.rect.left))

    def move_ip(self, game):
        if self.velocity == Vector():
            return
        self.rect.move_ip(self.velocity.x, self.velocity.y)
        self.limit_to_screen(game)

    def move(self, game):
        if self.velocity == Vector():
            return

        if game.m == 1:
            self.rect.left += self.velocity.x
            self.rect.top += self.velocity.y
            tempX = self.velocity.x
            tempY = self.velocity.y
            if tempX != 0 or tempY != 0:
                self.change_frame()
        else:
            self.change_frame()
            if not self.check_collisions(game):
                self.rect.left += self.velocity.x
                self.rect.top += self.velocity.y
            if self.check_collisions(game):
                self.rect.left -= self.velocity.x
                self.rect.top -= self.velocity.y
            if self.velocity.x > 0:
                self.startF, self.endF = 2, 3
            elif self.velocity.x < 0:
                self.startF, self.endF = 0, 1
            elif self.velocity.y > 0:
                self.startF, self.endF = 4, 5
            else:
                self.startF, self.endF = 6, 7

        self.limit_to_screen(game)

    def check_collisions(self, game):
        for j in range(len(game.walls)):
            if self.rect.colliderect(game.walls[j]):
                return True
        return False

    def draw(self, game):
        self.image = pg.transform.rotozoom(pg.image.load(self.enemyAnimation[self.currentFrame]), 0, 0.06)
        game.surface.blit(self.image, self.rect)

    def update(self, game):
        self.check_collisions(game=game)
        self.move(game=game)
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
        self.play_sound(game.GAME_OVER)


# -------------------------------------------------------------------------------------
class Game:
    def __init__(self, title):
        pg.init()
        logo = pg.image.load('images/pac2.png')
        pg.display.set_icon(logo)
        self.WINDOW_WIDTH, self.WINDOW_HEIGHT = 550, 700
        self.bitFont = pg.font.Font('fonts/8-Bit Madness.ttf', 28)

        self.m = 0
        self.mAnimate = Enemy(pg.Rect(self.WINDOW_WIDTH, 363, 50, 50), Vector())
        self.mAnimate.enemyAnimation = ['images/menu0.png', 'images/menu1.png', 'images/menu2.png', 'images/menu3.png',
                                        'images/menu4.png', 'images/menu5.png', 'images/menu6.png']

        self.player = Player(pg.Rect(259, 363, 25, 25), Vector())
        self.blinky = Enemy(pg.Rect(259, 250, 25, 25), Vector())
        self.pinky = Enemy(pg.Rect(259, 305, 25, 25), Vector())
        self.inky = Enemy(pg.Rect(230, 305, 25, 25), Vector())
        self.clyde = Enemy(pg.Rect(285, 305, 25, 25), Vector())

        self.bCount, self.iCount, self.pCount, self.cCount = 0, 0, 0, 0
        self.btemp, self.itemp, self.ptemp, self.ctemp = 1, -1, 1, -1

        self.pinky.enemyAnimation = ['images/pinky0.png', 'images/pinky1.png', 'images/pinky2.png', 'images/pinky3.png',
                                     'images/pinky4.png', 'images/pinky5.png', 'images/pinky6.png', 'images/pinky7.png']
        self.inky.enemyAnimation = ['images/inky0.png', 'images/inky1.png', 'images/inky2.png', 'images/inky3.png',
                                    'images/inky4.png', 'images/inky5.png', 'images/inky6.png', 'images/inky7.png']
        self.clyde.enemyAnimation = ['images/clyde0.png', 'images/clyde1.png', 'images/clyde2.png', 'images/clyde3.png',
                                     'images/clyde4.png', 'images/clyde5.png', 'images/clyde6.png', 'images/clyde7.png']

        # Audio
        self.intro_src = 'sounds/start-music.mp3'
        # self.background_src = 'sounds/ghost-normal-move.ogg'
        self.EAT_SOUND, self.GHOST, self.GAME_OVER = 0, 1, 2
        sounds = [{self.EAT_SOUND: 'sounds/eat.ogg',
                   self.GHOST: 'sounds/ghost-normal-move.ogg',
                   self.GAME_OVER: 'sounds/game_over.wav'}]
        self.audio = Audio(sounds=sounds, playing=True)

        # Static Bricks (Player/Node)
        b1 = Player(pg.Rect(0, 40, 29, 260))
        b2 = Player(pg.Rect(0, 341, 29, 319))
        b3 = Player(pg.Rect(self.WINDOW_WIDTH - 29, 40, 29, 260))
        b4 = Player(pg.Rect(self.WINDOW_WIDTH - 29, 341, 29, 319))
        b5 = Player(pg.Rect(58, 100, 60, 40))
        b6 = Player(pg.Rect(140, 100, 100, 40))
        b7 = Player(pg.Rect(self.WINDOW_WIDTH - 240, 100, 100, 40))
        b8 = Player(pg.Rect(self.WINDOW_WIDTH - 118, 100, 60, 40))
        b9 = Player(pg.Rect(58, 155, 60, 40))
        b10 = Player(pg.Rect(self.WINDOW_WIDTH - 118, 155, 60, 40))
        b11 = Player(pg.Rect(58, self.WINDOW_HEIGHT - 140, 180, 40))
        b12 = Player(pg.Rect(self.WINDOW_WIDTH - 240, self.WINDOW_HEIGHT - 140, 190, 40))
        b13 = Player(pg.Rect(140, 155, 40, 160))
        b14 = Player(pg.Rect(self.WINDOW_WIDTH - 180, 155, 40, 160))
        b15 = Player(pg.Rect(self.WINDOW_WIDTH / 2 - 12, 80, 30, 60))
        b16 = Player(pg.Rect(self.WINDOW_WIDTH / 2 - 70, 155, 140, 40))
        b17 = Player(pg.Rect(0, 222, 120, 85))
        b18 = Player(pg.Rect(150, 220, 90, 30))
        b19 = Player(pg.Rect(270, 200, 20, 50))
        b20 = Player(pg.Rect(310, 220, 90, 30))
        b21 = Player(pg.Rect(430, 222, 120, 85))
        b22 = Player(pg.Rect(200, 280, 150, 85))
        b23 = Player(pg.Rect(0, 330, 120, 85))
        b24 = Player(pg.Rect(150, 330, 30, 85))
        b25 = Player(pg.Rect(370, 330, 40, 85))
        b26 = Player(pg.Rect(430, 330, 120, 85))
        b27 = Player(pg.Rect(210, 390, 140, 30))
        b28 = Player(pg.Rect(60, 440, 60, 40))
        b29 = Player(pg.Rect(430, 440, 70, 40))
        b30 = Player(pg.Rect(150, 440, 90, 40))
        b31 = Player(pg.Rect(315, 445, 90, 40))
        b32 = Player(pg.Rect(260, 430, 30, 50))
        b33 = Player(pg.Rect(90, 470, 30, 70))
        b34 = Player(pg.Rect(430, 470, 40, 70))
        b35 = Player(pg.Rect(30, 500, 30, 40))
        b36 = Player(pg.Rect(490, 500, 30, 40))
        b37 = Player(pg.Rect(140, 500, 40, 50))
        b38 = Player(pg.Rect(370, 500, 40, 50))
        b39 = Player(pg.Rect(210, 500, 140, 40))
        b40 = Player(pg.Rect(260, 530, 30, 70))
        self.bricks = [b1, b2, b3, b4, b5, b6, b7, b8, b9, b10, b11, b12, b13, b14, b15, b16, b17, b18, b19, b20, b21,
                       b22, b23, b24, b25, b26, b27, b28, b29, b30, b31, b32, b33, b34, b35, b36, b37, b38, b39, b40]

        # Static Walls (Player/Wall)
        w1 = Player(pg.Rect(-30, 40, 50, 260))
        w2 = Player(pg.Rect(-30, 341, 50, 319))
        w3 = Player(pg.Rect(self.WINDOW_WIDTH - 29, 40, 60, 260))
        w4 = Player(pg.Rect(self.WINDOW_WIDTH - 29, 341, 60, 319))
        w5 = Player(pg.Rect(58, 100, 50, 25))
        w6 = Player(pg.Rect(140, 100, 80, 25))
        w7 = Player(pg.Rect(self.WINDOW_WIDTH - 230, 100, 80, 25))
        w8 = Player(pg.Rect(self.WINDOW_WIDTH - 110, 100, 40, 25))
        w9 = Player(pg.Rect(60, 165, 50, 20))
        w10 = Player(pg.Rect(self.WINDOW_WIDTH - 110, 165, 40, 20))
        w11 = Player(pg.Rect(60, self.WINDOW_HEIGHT - 130, 165, 25))
        w12 = Player(pg.Rect(self.WINDOW_WIDTH - 230, self.WINDOW_HEIGHT - 140, 165, 25))
        w13 = Player(pg.Rect(145, 165, 25, 130))
        w14 = Player(pg.Rect(self.WINDOW_WIDTH - 170, 165, 20, 130))
        w15 = Player(pg.Rect(self.WINDOW_WIDTH / 2 - 12, 80, 20, 40))
        w16 = Player(pg.Rect(self.WINDOW_WIDTH / 2 - 70, 165, 130, 20))
        w17 = Player(pg.Rect(0, 222, 105, 80))
        w18 = Player(pg.Rect(150, 220, 70, 20))
        w19 = Player(pg.Rect(270, 200, 10, 40))
        w20 = Player(pg.Rect(320, 220, 60, 20))
        w21 = Player(pg.Rect(430, 222, 120, 76))
        w22 = Player(pg.Rect(200, 280, 140, 75))
        w23 = Player(pg.Rect(0, 341, 105, 75))
        w24 = Player(pg.Rect(150, 335, 20, 75))
        w25 = Player(pg.Rect(380, 335, 20, 75))
        w26 = Player(pg.Rect(440, 341, 120, 70))
        w27 = Player(pg.Rect(210, 390, 130, 25))
        w28 = Player(pg.Rect(60, 450, 50, 25))
        w29 = Player(pg.Rect(435, 450, 50, 25))
        w30 = Player(pg.Rect(150, 450, 70, 25))
        w31 = Player(pg.Rect(315, 450, 70, 25))
        w32 = Player(pg.Rect(260, 430, 20, 40))
        w33 = Player(pg.Rect(90, 470, 20, 60))
        w34 = Player(pg.Rect(435, 470, 20, 60))
        w35 = Player(pg.Rect(30, 510, 20, 25))
        w36 = Player(pg.Rect(495, 510, 20, 25))
        w37 = Player(pg.Rect(150, 510, 15, 50))
        w38 = Player(pg.Rect(380, 510, 15, 50))
        w39 = Player(pg.Rect(210, 510, 130, 20))
        w40 = Player(pg.Rect(260, 530, 20, 50))
        self.walls = [w1, w2, w3, w4, w5, w6, w7, w8, w9, w10, w11, w12, w13, w14, w15, w16, w17, w18, w19, w20, w21,
                      w22, w23, w24, w25, w26, w27, w28, w29, w30, w31, w32, w33, w34, w35, w36, w37, w38, w39, w40]

        self.score, self.level = 0, 0
        self.finished = False
        self.BLACK = (0, 0, 0)
        self.WHITE = (255, 255, 255)
        self.BACKGROUND_COLOR = self.BLACK
        self.WALL_COLOR = (255, 0, 0)
        self.FPS = 60

        pg.display.set_caption(title)
        self.surface = pg.display.set_mode((self.WINDOW_WIDTH, self.WINDOW_HEIGHT), 0, 32)
        self.grid = Grid(self)

        self.bImage = pg.image.load('images/pacGrid.png')
        self.mImage = pg.image.load('images/menu.png')
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
                self.blinky.velocity = -Player.SPEED * movement[k]
                self.pinky.velocity = Enemy.SPEED * movement[k]
                self.inky.velocity = Enemy.SPEED * movement[k]
            elif k == K_x:
                # shoot blue portal
                pass
            elif k == K_c:
                # shoot orange portal
                pass
        elif e_type == QUIT or (e_type == KEYUP and event.key == K_ESCAPE):
            self.finished = True
        elif e_type == MOUSEBUTTONUP:
            pass

    def update(self):
        self.surface.fill(self.BACKGROUND_COLOR)
        self.surface.blit(self.bImage, (0, 46))

        text = self.bitFont.render(f'Score: {self.score}', True, self.WHITE, self.BLACK)
        textRect = text.get_rect()
        textRect.center = (70, 25)
        self.surface.blit(text, textRect)

        text2 = self.bitFont.render(f'Level: {self.level}', True, self.WHITE, self.BLACK)
        textRect2 = text2.get_rect()
        textRect2.center = (500, 25)
        self.surface.blit(text2, textRect2)

        text3 = self.bitFont.render(f'Lives: {self.player.lives}', True, self.WHITE, self.BLACK)
        textRect3 = text3.get_rect()
        textRect3.center = (70, 675)
        self.surface.blit(text3, textRect3)

        # Test Rect
        # pg.draw.rect(self.surface, self.WALL_COLOR, (210, 390, 140, 30))

        self.grid.update()

        self.player.update(game=self)
        if self.player.lives == 0:
            print('Game Over!')
            self.audio.game_over(self)
            self.player.lives = 3
            self.score, self.level = 0, 1
            self.grid.reset_grid()
            # reset location of pacman and ghosts
            self.player.rect.left, self.player.rect.top = 259, 363
            self.blinky.rect.left, self.blinky.rect.top = 259, 250
            self.pinky.rect.left, self.pinky.rect.top = 259, 180
            self.inky.rect.left, self.inky.rect.top = 259, 150
            self.clyde.rect.left, self.clyde.rect.top = 259, 210
            self.menu()

        '''
        self.bCount += 1
        if self.bCount >= 100:
            self.btemp *= -1
            self.bCount = 0
        self.blinky.velocity = Player.SPEED * Vector(-1 * self.btemp, 0)
        '''
        self.blinky.update(game=self)
        '''
        self.iCount += 1
        if self.iCount >= 100:
            self.itemp *= -1
            self.iCount = 0
        self.inky.velocity = Player.SPEED * Vector(-1 * self.itemp, 0)
        '''
        self.inky.update(game=self)
        '''
        self.pCount += 1
        if self.pCount >= 100:
            self.ptemp *= -1
            self.pCount = 0
        self.pinky.velocity = Player.SPEED * Vector(-1 * self.ptemp, 0)
        '''
        self.pinky.update(game=self)

        # Randomized Clyde Movement
        # if current second are divisible by 3 or 7, actually move, else dont
        # self.cCount = random number between 1-4
        # if 1 move=left, 2=up, 3=right, 4=down
        if self.mainClock.get_time() % random.randint(1, 40) == 0:
            self.cCount = random.randint(1, 4)
            if self.cCount == 1:
                self.clyde.velocity = Enemy.SPEED * Vector(1, 0)
            elif self.cCount == 2:
                self.clyde.velocity = Enemy.SPEED * Vector(0, 1)
            elif self.cCount == 3:
                self.clyde.velocity = Enemy.SPEED * Vector(-1, 0)
            else:  # 4
                self.clyde.velocity = Enemy.SPEED * Vector(0, -1)
        self.clyde.update(game=self)
        pg.display.update()

    def menu(self):
        self.m = 1  # menu is on
        self.surface.blit(self.mImage, (0, 0))
        self.mAnimate.update(game=self)
        sett = Settings()
        # Make the Play button.
        play_button = Button(sett, self.surface, "Play")
        play_button.rect.top += 200
        play_button.prep_msg("Play")
        # Make the HighScore button.
        hScore_button = Button(sett, self.surface, "Highscores")
        hScore_button.rect.top += 250
        hScore_button.prep_msg("Highscores")
        # mouse_x, mouse_y = pg.mouse.get_pos()
        # button_clicked = play_button.rect.collidepoint(mouse_x, mouse_y)

        pg.display.update()
        play_button.draw_button()
        hScore_button.draw_button()

        self.bitFont = pg.font.Font('fonts/8-Bit Madness.ttf', 28)
        blinkC, pinkC, inkyC, clydeC = (249, 0, 0), (249, 141, 224), (5, 249, 249), (249, 138, 13)
        text = self.bitFont.render('Pac-man', True, (249, 241, 0), (0, 0, 0))
        text0 = self.bitFont.render('Blinky', True, blinkC, (0, 0, 0))
        text1 = self.bitFont.render('Pinky', True, pinkC, (0, 0, 0))
        text2 = self.bitFont.render('Inky', True, inkyC, (0, 0, 0))
        text3 = self.bitFont.render('Clyde', True, clydeC, (0, 0, 0))
        text4 = self.bitFont.render('How High Can You Score?', True, (249, 241, 0), (0, 0, 0))
        textRect, textRect0, textRect1, textRect2, textRect3, textRect4 \
            = text.get_rect(), text0.get_rect(), text1.get_rect(), text2.get_rect(), text3.get_rect(), text4.get_rect()
        textRect.center, textRect0.center, textRect1.center, textRect2.center, textRect3.center, textRect4.center \
            = (75 + 40, 450), (185 + 40, 450), (275 + 40, 450), (350 + 40, 450), (425 + 40, 450), (275 + 10, 450)

        # Wait for Keypress To Move To Next State
        key_pressed = False
        count = 0
        temp = -1
        while not key_pressed:
            if count == 150:
                temp *= -1
                count = 0
            count += 1
            self.mAnimate.velocity = Enemy.SPEED * Vector(1 * temp, 0)
            self.surface.blit(self.mImage, (0, 0))
            if self.mAnimate.velocity == Enemy.SPEED * Vector(-1, 0):
                self.mAnimate.rect.left = self.mAnimate.rect.left
                self.mAnimate.startF, self.mAnimate.endF = 0, 2
                self.surface.blit(text, textRect)
                self.surface.blit(text0, textRect0)
                self.surface.blit(text1, textRect1)
                self.surface.blit(text2, textRect2)
                self.surface.blit(text3, textRect3)
            else:
                self.mAnimate.startF, self.mAnimate.endF = 3, len(self.mAnimate.enemyAnimation) - 1
                self.surface.blit(text4, textRect4)

            self.mAnimate.update(game=self)
            play_button.draw_button()
            hScore_button.draw_button()
            pg.display.update()
            for e in pg.event.get():
                if e.type == QUIT or e.type == KEYDOWN and e.key == K_ESCAPE:
                    Game.terminate()
                elif e.type == pg.MOUSEBUTTONDOWN:
                    mouse_x, mouse_y = pg.mouse.get_pos()
                    button_clicked = play_button.rect.collidepoint(mouse_x, mouse_y)
                    if button_clicked:
                        # Reset the game settings.
                        key_pressed = True
                        # Hide the mouse cursor.
                        pg.mouse.set_visible(False)
            time.sleep(0.02)
        self.m = 0  # menu is off
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
                time.sleep(0.02)
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
