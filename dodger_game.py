import pygame as pg
import sys
import random
import time
from pygame.locals import *
from vector import Vector


# -------------------------------------------------------------------------------------
class Baddie:
    MIN_SIZE, MAX_SIZE = 10, 40
    MIN_SPEED, MAX_SPEED = 1, 8
    REVERSE_CHEATING = False
    SLOW_CHEATING = False
    VALUE = 1

    def __init__(self, game, position=None):
        g, randint = game, random.randint                 # aliases
        g_w, g_h = game.WINDOW_WIDTH, game.WINDOW_HEIGHT

        self.velocity = Vector(0, randint(Baddie.MIN_SPEED, Baddie.MAX_SPEED))
        width = height = randint(Baddie.MIN_SIZE, Baddie.MAX_SIZE)
        if position is None:
            left, top = randint(0, g_w - width), randint(0, g_h - height)
        else:
            left, top = position.x, position.y
        self.value = Baddie.VALUE
        self.rect = pg.Rect(left, top, width, height)
        self.image = pg.image.load(game.baddie_image_src)

    def __repr__(self):
        return "Baddie(rect={})".format(self.rect)

    def move(self):
        v = Vector(self.velocity.x, self.velocity.y)
        if Baddie.REVERSE_CHEATING:
            v.y = -5
        elif Baddie.SLOW_CHEATING:
            v.y = 1
        self.rect.left += v.x
        self.rect.top += v.y

    def draw(self, game):
        game.surface.blit(self.image, self.rect)


# -------------------------------------------------------------------------------------
class Baddies:
    append_attempts = 80
    initial = 1

    def __init__(self, game):
        self.list = []
        self.interval = 20
        for i in range(Baddies.initial):
            self.append(Baddie(game=game))

    def append(self, baddie):
        self.list.append(baddie)

    def append_baddie_sometimes(self, game):
        if Baddie.REVERSE_CHEATING or Baddie.SLOW_CHEATING:
            return
        Baddies.append_attempts += 1
        if Baddies.append_attempts % self.append_attempts == 0:
            self.append(Baddie(game=game))

    def move(self, game):    # remove baddies who fall off the screen
        for baddie in self.list:
            baddie.move()
            if baddie.rect.top >= game.WINDOW_HEIGHT:
                self.list.remove(baddie)

    def update(self, game):
        self.append_baddie_sometimes(game=game)
        self.move(game)
        self.draw(game)

    def draw(self, game):
        for baddie in self.list:
            baddie.draw(game)


# -------------------------------------------------------------------------------------
class Player:
    SPEED = 6

    def __init__(self, rect, velocity=Vector(), image_src='player.png'):
        self.rect = rect
        self.velocity = velocity
        self.player = pg.Rect(300, 100, 50, 50)
        self.image = pg.image.load(image_src)
        self.stretched_image = pg.transform.scale(self.image, (rect.width, rect.height))

    def __repr__(self):
        return "Player(rect={},velocity={})".format(self.rect, self.velocity)

    def limit_to_screen(self, game):
        self.rect.top = max(0, min(game.WINDOW_HEIGHT - self.rect.height, self.rect.top))
        self.rect.left = max(0, min(game.WINDOW_WIDTH - self.rect.width, self.rect.left))

    def move_ip(self, game):
        if self.velocity == Vector():
            return
        self.rect.move_ip(self.velocity.x, self.velocity.y)
        self.limit_to_screen(game)

    def move(self, game):
        if self.velocity == Vector():
            return
        self.rect.left += self.velocity.x
        self.rect.top += self.velocity.y
        self.limit_to_screen(game)

    def move_to_random(self, game):
        self.rect.top = random.randint(0, game.WINDOW_HEIGHT - self.rect.height)
        self.rect.left = random.randint(0, game.WINDOW_WIDTH - self.rect.width)

    def check_collisions(self, game):
        g = game
        for baddie in g.baddies.list:
            if baddie.rect.colliderect(self.rect):
                g.baddies.list.remove(baddie)
                g.score.increment(baddie.value)
                g.audio.play_sound(g.PICKUP_SOUND)

    def draw(self, game):
        game.surface.blit(self.stretched_image, self.rect)

    def update(self, game):
        self.check_collisions(game=game)
        self.move(game=game)
        self.draw(game=game)


# -------------------------------------------------------------------------------------
class Audio:   # sound(s) and background music
    def __init__(self, sounds, background_src, playing):
        self.sounds = {}
        for sound in sounds:
            for k, v in sound.items():
                self.sounds[k] = pg.mixer.Sound(v)
        self.background_src = background_src

        self.playing = playing
        pg.mixer.music.load(self.background_src)
        if self.playing:
            pg.mixer.music.play(-1, 0.0)

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
class Score:
    def __init__(self, font, game):
        self.font = font
        self.game = game
        self.score = 0
        self.top_score = 0

    def increment(self, amount):
        self.score += amount

    def draw(self):
        self.draw_text("Score: {}".format(self.score), 10, 0)
        self.draw_text("Top Score: {}".format(self.top_score), 10, 40)

    def draw_text(self, text, x, y):
        text_obj = self.font.render(text, 1, self.game.TEXT_COLOR)
        text_rect = text_obj.get_rect()
        text_rect.topleft = (x, y)
        self.game.surface.blit(text_obj, text_rect)

    def update(self):
        if self.score > self.top_score:
            self.top_score = self.score
        self.draw()

    def reset(self):
        self.score = 0


# -------------------------------------------------------------------------------------
class Game:
    def __init__(self, title):
        pg.init()
        self.WINDOW_WIDTH = self.WINDOW_HEIGHT = 600
        self.font = pg.font.SysFont(None, 48)
        self.player_img_src = 'player.png'
        self.baddie_image_src = 'baddie.png'
        self.background_src = 'background.mid'
        self.PICKUP_SOUND, self.GAME_OVER_SOUND = 0, 1
        sounds = [{self.PICKUP_SOUND: 'pickup.wav',
                   self.GAME_OVER_SOUND: 'game_over.wav'}]
        self.player = Player(pg.Rect(300, 100, 50, 50), Vector(), image_src=self.player_img_src)
        self.baddie = Baddie(game=self)
        self.baddie_interval = 10

        self.baddies = Baddies(game=self)
        self.audio = Audio(sounds=sounds, background_src=self.background_src, playing=True)
        self.score = Score(font=self.font, game=self)

        self.finished = False
        self.TEXT_COLOR = (0, 0, 0)
        self.SEPIA = (240, 200, 170)
        self.BACKGROUND_COLOR = self.SEPIA
        self.FPS = 60

        pg.display.set_caption(title)
        self.surface = pg.display.set_mode((self.WINDOW_WIDTH, self.WINDOW_HEIGHT), 0, 32)
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
        speed = Player.SPEED
        e_type = event.type
        movement = {K_a: Vector(-1, 0), K_d: Vector(1, 0), K_w: Vector(0, -1), K_s: Vector(0, 1)}
        translate = {K_LEFT: K_a, K_RIGHT: K_d, K_UP: K_w, K_DOWN: K_s}
        left_right_up_down = (K_LEFT, K_a, K_RIGHT, K_d, K_UP, K_w, K_DOWN, K_s)
        x_z = (K_x, K_z)

        if self.score.score > 40:
            self.game_over()

        if e_type == KEYDOWN or e_type == KEYUP:
            k = event.key
            if k == K_m and e_type == KEYUP:
                self.audio.toggle()
            elif k in x_z:
                if e_type == KEYDOWN:
                    Baddie.REVERSE_CHEATING = k == K_z
                    Baddie.SLOW_CHEATING = k == K_x
                elif e_type == KEYUP:
                    self.score.reset()
                    Baddie.REVERSE_CHEATING = Baddie.SLOW_CHEATING = False
                    print("Cheating is now false")
            elif k in left_right_up_down:
                if k in translate.keys():
                    k = translate[k]
                self.player.velocity = Player.SPEED * movement[k]
                # self.player.velocity = Player.SPEED * movement[k] if e_type == KEYDOWN else Vector()
            elif k == K_x:
                self.player.move_to_random(game=self)
        elif e_type == QUIT or (e_type == KEYUP and event.key == K_ESCAPE):
            self.finished = True
        elif e_type == MOUSEBUTTONUP:
            self.baddies.append(Baddie(game=self, position=event))

    def update(self):
        self.surface.fill(self.BACKGROUND_COLOR)
        self.score.update()
        self.baddies.update(game=self)
        self.player.update(game=self)
        pg.display.update()

    def play(self):
        while not self.finished:
            for event in pg.event.get():
                self.process_event_loop(event)

            self.update()
            time.sleep(0.02)
            self.mainClock.tick(self.FPS)
        Game.terminate()

    def game_over(self):
        self.audio.game_over(game=self)
        width, height = self.WINDOW_WIDTH, self.WINDOW_HEIGHT
        self.score.draw_text(text='GAME OVER', x=width/3, y=height/3)
        self.score.draw_text(text='Press a key to play again.', x=width/3 - 80,
                             y=height/3 + 50)
        pg.display.update()
        self.wait_for_key_press()

    @staticmethod
    def terminate():
        pg.quit()
        sys.exit()


# -------------------------------------------------------------------------------------
def main():
    game = Game(title='Dodger game')
    game.play()


# -------------------------------------------------------------------------------------
if __name__ == '__main__':
    main()
