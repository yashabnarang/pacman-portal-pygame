import pygame as pg
import sys
import random
import time
from pygame.locals import *
from vector import Vector


class Food:
    WIDTH = 20
    HEIGHT = 20

    def __init__(self, game):
        self.left = random.randint(0, game.WINDOW_WIDTH - Food.WIDTH)
        self.top = random.randint(0, game.WINDOW_HEIGHT - Food.HEIGHT)
        self.width, self.height = Food.WIDTH, Food.WIDTH
        self.rect = pg.Rect(self.left, self.top, self.width, self.height)

    def __repr__(self):
        return "Food(rect={})".format(self.rect)

    def draw(self, game):
        pg.draw.rect(game.surface, game.GREEN, self.rect)


class Foods:
    append_attempts = 0
    initial_foods = 40

    def __init__(self, game):
        self.food_list = []
        self.food_interval = 20
        for i in range(Foods.initial_foods):
            self.append(Food(game=game))

    def append(self, food):
        self.food_list.append(food)

    def append_food_sometimes(self, game):
        Foods.append_attempts += 1
        if Foods.append_attempts % self.food_interval == 0:
            self.append(Food(game=game))

    def check_collisions(self, player):
        for food in self.food_list:
            if food.rect.colliderect(player.rect):
                self.food_list.remove(food)

    def update(self, game):
        self.append_food_sometimes(game=game)
        self.draw(game)

    def draw(self, game):
        for food in self.food_list:
            food.draw(game)


class Player:
    def __init__(self, rect, velocity):
        self.rect = rect
        self.velocity = velocity
        self.player = pg.Rect(300, 100, 50, 50)

    def __repr__(self):
        return "Player(rect={},velocity={})".format(self.rect, self.velocity)

    def limit_to_screen(self, game):
        self.rect.top = max(0, min(game.WINDOW_HEIGHT - self.rect.height, self.rect.top))
        self.rect.left = max(0, min(game.WINDOW_WIDTH - self.rect.width, self.rect.left))

    def move(self, game):
        self.rect.left += self.velocity.x
        self.rect.top += self.velocity.y
        self.limit_to_screen(game)

    def move_to_random(self, game):
        self.rect.top = random.randint(0, game.WINDOW_HEIGHT - self.rect.height)
        self.rect.left = random.randint(0, game.WINDOW_WIDTH - self.rect.width)

    def check_collisions(self, game):
        game.foods.check_collisions(self)

    def draw(self, game):
        pg.draw.rect(game.surface, game.BLACK, self.rect)

    def update(self, game):
        self.check_collisions(game=game)
        self.move(game=game)
        self.draw(game=game)


class Game:
    def __init__(self, title):
        self.player_speed = 12
        self.WINDOW_WIDTH = self.WINDOW_HEIGHT = 400
        self.player = Player(pg.Rect(300, 100, 50, 50),
                             self.player_speed * Vector(1.0, 1.0))
        self.foods = Foods(self)

        self.finished = False
        self.title = title
        self.mainClock = pg.time.Clock()
        self.surface = pg.display.set_mode((self.WINDOW_WIDTH, self.WINDOW_HEIGHT), 0, 32)
        pg.display.set_caption(self.title)

        self.WHITE = (255, 255, 255)
        self.GREEN = (0, 255, 0)
        self.BLACK = (0, 0, 0)

    def process_event_loop(self, event):
        speed = self.player_speed
        e_type = event.type
        movement = {K_a: Vector(-1, 0), K_d: Vector(1, 0), K_w: Vector(0, -1), K_s: Vector(0, 1)}
        translate = {K_LEFT: K_a, K_RIGHT: K_d, K_UP: K_w, K_DOWN: K_s}
        left_right_up_down = (K_LEFT, K_a, K_RIGHT, K_d, K_UP, K_w, K_DOWN, K_s)

        if e_type == KEYDOWN or e_type == KEYUP:
            k = event.key
            if k in left_right_up_down:
                if k in translate.keys():
                    k = translate[k]
                self.player.velocity = speed * movement[k]
                # self.player.velocity = speed * movement[k] if e_type == KEYDOWN else Vector()
            elif k == K_x:
                self.player.move_to_random(game=self)
        elif e_type == QUIT or (e_type == KEYUP and event.key == K_ESCAPE):
            self.finished = True
        elif e_type == MOUSEBUTTONUP:
            self.foods.append(Food(event.pos))

    def update(self):
        self.surface.fill(self.WHITE)
        self.foods.update(game=self)
        self.player.update(game=self)
        pg.display.update()

    def play(self):
        while not self.finished:
            for event in pg.event.get():
                self.process_event_loop(event)

            self.update()
            time.sleep(0.02)
            self.mainClock.tick(40)

        pg.quit()   # when self.finished
        sys.exit()


def main():
    game = Game(title='Collision Detection')
    game.play()


if __name__ == '__main__':
    main()
