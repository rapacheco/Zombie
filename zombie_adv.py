import os
from random import choice, randint, randrange
from math import sqrt, atan, degrees

import pygame
from pygame.locals import *

WIDTH = 800
HEIGHT = 500
BLACK = (0,0,0)
WHITE = (255,255,255)
MAX_ICONS = 3

def main():
    game = Main()
    while not game.done:
        game.loop()

def get_size():
    return (WIDTH, HEIGHT)

def load_image(file, colorkey=None, size=(50, 50)):
    fullname = os.path.join("images", file)
    img = pygame.image.load(fullname)
    img = img.convert()
    if colorkey is not None:
        if colorkey is -1:
            colorkey = img.get_at((0,0))
        img.set_colorkey(colorkey, RLEACCEL)
    return pygame.transform.scale(img, size)

def load_sound(name, music=False):
    class NoneSound:
        def play(self): pass
    if music:
        folder = "music"
    else:
        folder = "sounds"
    fullname = os.path.join(folder, name)
    return pygame.mixer.Sound(fullname)

def load_font(file, size):
    if file is not None:
        fullname = os.path.join("fonts", file)
    else:
        fullname = None
    return pygame.font.Font(fullname, size)

class Main:
    def __init__(self):
        pygame.init()
        pygame.font.init()
        pygame.mixer.init()
        if pygame.font is None:
            print("Warning, fonts disabled")
        if pygame.mixer is None:
            print("Warning, sound disabled")
        pygame.display.set_caption("Zombie Attacked!")

        self.width, self.height = get_size()
        self.screen = pygame.display.set_mode((self.width, self.height))
        self.background = load_image("background.png", size=(self.width, self.height))
        self.icons = load_image("zombie_icons.png", colorkey=BLACK, size=(400, 200))
        self.blood = load_image("blood.png", -1, size=(300, 50))

        pygame.time.set_timer(USEREVENT+1, 500)
        pygame.time.set_timer(USEREVENT+2, 1000)
        pygame.time.set_timer(USEREVENT+3, 5000)
        self.clock = pygame.time.Clock()

        self.done = False
        self.hurt = False
        self.lock = False

        # hud states
        self.states = {
            "state": 1,
            "main_screen": True,
            "main_menu": False,
            "sure": False,
            "credit": False,
            "game_on": False,
            "dead": False}

        self.count = 0
        self.playtime = 0
        self.cycletime = 0
        self.interval = 1.0

        self.high, self.so_far = self.load_high_score()
        self.zombie, self.hud, self.sound_track = self.load_classes()
        self.all_chars, self.main_char, self.shooting, self.brains = self.groups()

        self.human = Human(3)
        self.humans = pygame.sprite.Group(())
        self.humans.add((self.human))

        self.high, self.so_far = self.load_high_score()

    def get_states(self):
        return self.states

    def load_high_score(self):
        fullname = os.path.join("temp", "temp.csv")
        with open(fullname, 'r') as fp:
            temp = fp.read()
            if temp == '':
                high, so_far = 0, 0
            else:
                high, so_far = int(temp), int(temp)
        return high, so_far

    def erase_score(self):
        fullname = os.path.join("temp", "temp.csv")
        with open(fullname, 'w') as fp:
            fp.write('0')
        return 0

    def update_high_score(self, high, so_far):
        if high > so_far:
            fullname = os.path.join("temp", "temp.csv")
            with open(fullname, 'w+') as fp:
                fp.write(str(high))

    def load_classes(self):
        zombie = Zombie(5)
        hud = Hud(zombie, self.high)
        hud.update(self.high)
        sound_track = SoundTrack()
        return zombie, hud, sound_track

    def groups(self):
        main_char = pygame.sprite.GroupSingle((self.zombie))
        all_chars = pygame.sprite.Group(())
        all_chars.add((self.zombie))
        shooting = pygame.sprite.Group(())
        brains = pygame.sprite.Group(())
        return all_chars, main_char, shooting, brains

    def loop(self):
        self.milliseconds = self.clock.tick(60)
        self.seconds = self.milliseconds / 1000.0
        self.playtime += self.seconds
        self.cycletime += self.seconds

        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:

                if self.states["main_screen"] and not self.lock:
                    if event.key:
                        self.states["main_screen"], self.states["main_menu"] = False, True
                        self.lock = True

                if self.states["main_menu"] and not self.lock:
                    if event.key == pygame.K_w or event.key == pygame.K_UP:
                        if self.states["state"] == 1:
                            self.states["state"] = 4
                        else:
                            self.states["state"] -= 1
                        self.lock = True

                    elif event.key == pygame.K_s or event.key == pygame.K_DOWN:
                        if self.states["state"] == 4:
                            self.states["state"] = 1
                        else:
                            self.states["state"] += 1
                        self.lock = True

                    elif event.key == pygame.K_RETURN:
                        if self.states["state"] == 1:
                            self.states["main_menu"], self.states["game_on"] = False, True
                            self.sound_track.stop_intro()
                            self.sound_track.play_loop()
                            self.lock = True

                        elif self.states["state"] == 2:
                            self.states["main_menu"], self.states["sure"] = False, True
                            self.lock = True

                        elif self.states["state"] == 3:
                            self.states["main_menu"], self.states["credit"] = False, True
                            self.lock = True

                        elif self.states["state"] == 4:
                            self.update_high_score(self.high, self.so_far)
                            self.done = True

                if self.states["sure"] and not self.lock:
                    if event.key == pygame.K_y:
                        self.high = self.erase_score()
                        self.hud.update(self.high)
                        self.states["main_menu"], self.states["sure"] = True, False
                        self.lock = True
                    elif event.key == pygame.K_n:
                        self.states["main_menu"], self.states["sure"] = True, False
                        self.lock = True

                if self.states["credit"] and not self.lock:
                    if event.key:
                        self.states["main_menu"], self.states["credit"] = True, False
                        self.lock = True

                if self.states["dead"] and not self.lock:
                    if event.key == pygame.K_y:
                        self.zombie, self.hud, self.sound_track = self.load_classes()
                        self.all_chars, self.main_char, self.shooting, self.brains = self.groups()

                        self.sound_track.play_loop()
                        self.states["game_on"], self.states["dead"] = True, False
                        self.lock = True
                    elif event.key == pygame.K_n:
                        self.zombie, self.hud, self.sound_track = self.load_classes()
                        self.all_chars, self.main_char, self.shooting, self.brains = self.groups()
                        self.sound_track.play_intro()
                        self.states["main_menu"], self.states["dead"], self.states["state"] = True, False, 1
                        self.lock = True

            elif event.type == pygame.KEYUP:
                if self.states["main_screen"]:
                    if event.key:
                        self.lock = False

                if self.states["main_menu"]:
                    if event.key:
                        self.lock = False

                if self.states["sure"]:
                    if event.key:
                        self.lock = False

                if self.states["credit"]:
                    if event.key:
                        self.lock = False

                if self.states["dead"]:
                    if event.key:
                        self.lock = False

            elif event.type == USEREVENT+1 and self.states["game_on"]:
                self.brains.update()
            elif event.type == USEREVENT+2 and self.states["game_on"]:
                self.human.shoot(self.zombie, self.shooting)
                # pass
            elif event.type == USEREVENT+3 and self.states["game_on"]:
                white_brain = WhiteBrain(self.icons)
                self.brains.add((white_brain))
            elif event.type == pygame.QUIT:
                self.update_high_score(self.high, self.so_far)
                self.done = True
            self.zombie.movement(event)

        # if zombie gets shot, takes damage
        for coll in pygame.sprite.groupcollide(self.shooting, self.main_char, True, False):
            damage = coll.get_damage()
            self.zombie.hurt(damage)
            self.zombie.hurted = True
            self.hud.decr_life(damage, self.high)

        # if char gets hurt, spray of blood
        for char in self.all_chars:
            if char.hurted:
                if self.cycletime > self.interval and char.anim < 6:
                    self.background.blit(self.blood, (char.rect.x, char.rect.y, 50, 50), area=(50 * char.anim, 0, 50, 50))
                    char.anim += 1
                elif char.anim >= 6:
                    char.anim = 0
                    char.hurted = False

        # if run out of lives, zombie dies and game over
        if self.zombie.life <= 0:
            self.zombie.dying()
            self.states["game_on"], self.states["dead"] = False, True
            self.sound_track.fadeout_loop(2500)

        # if zombie gets a brain, improve score
        for catch in pygame.sprite.groupcollide(self.brains, self.main_char, True, False):
            self.high = self.hud.incr_score(1, self.high)
            self.zombie.sound_chew()

        # sets maximum amount of brains in 10
        for b in self.brains:
            if b.count >= 11:
                self.brains.remove((b))

        # remove the shots as soon as they clear the screen
        for s in self.shooting:
            if s.rect.x < -20 or s.rect.x > WIDTH+20 or s.rect.y < -20 or s.rect.y > HEIGHT+20:
                self.shooting.remove((s))

        # paint the screen black and draw background
        self.screen.fill(BLACK)
        self.screen.blit(self.background, (0, 0))

        # allows the zombie to walk and the shooting to take place
        if self.states["game_on"] and not self.states["dead"]:
            self.zombie.walk()
            self.shooting.update()
            self.main_char.draw(self.screen)
            self.humans.draw(self.screen)

        self.hud.draw(self.zombie, self.screen, self.states)
        self.shooting.draw(self.screen)
        self.brains.draw(self.screen)
        pygame.display.flip()

class Character(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.WIDTH, self.HEIGHT = get_size()
        self.size = (int(self.WIDTH/16), int(self.HEIGHT/10))
        self.rect = pygame.Rect((self.WIDTH/2,self.HEIGHT/2), self.size)

        self.death = load_image("splat.png", -1, size=self.size)

        self.speed = 0
        self.life = 0
        self.anim = 0

        self.right, self.left, self.up, self.down = 0, 0, 0, 0
        self.hurted, self.init, self.r = False, False, False

    def turn(self):
        """
        Flips the character's image horizontaly
        """
        if self.image == self.state[0]:
            self.image = self.state[1]
        elif self.image == self.state[1]:
            self.image = self.state[0]
        elif self.image == self.state[2]:
            self.image = self.state[3]
        elif self.image == self.state[3]:
            self.image = self.state[2]

    def walk(self):
        """
        Makes the character move
        """
        if self.left < 0:
            if self.rect.x >= 0:
                self.rect.x += self.left
        elif self.right > 0:
            if self.rect.x <= self.WIDTH - self.image.get_width():
                self.rect.x += self.right
        if self.up < 0:
            if self.rect.y >= 0:
                self.rect.y += self.up
        elif self.down > 0:
            if self.rect.y <= self.HEIGHT - self.image.get_height():
                self.rect.y += self.down

    def hurt(self, damage):
        self.state = self.hit
        self.roar.play()
        self.life -= damage

    def dying(self):
        self.image = self.death

    def movement(self, event):
        # code to make character turn to the direction it is moved and begin to walk
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_d or event.key == pygame.K_RIGHT:
                self.right = self.speed
                if not self.r:
                    self.turn()
                    self.r = True
            elif event.key == pygame.K_a or event.key == pygame.K_LEFT:
                self.left = -self.speed
                if self.r:
                    self.turn()
                    self.r = False
            elif event.key == pygame.K_w or event.key == pygame.K_UP:
                self.up = -self.speed
            elif event.key == pygame.K_s or event.key == pygame.K_DOWN:
                self.down = self.speed

        # code for stoping the character when button is released
        elif event.type == pygame.KEYUP:
            if (event.key == pygame.K_d or event.key == pygame.K_RIGHT) and self.right > -1:
                self.right = 0
            elif (event.key == pygame.K_a or event.key == pygame.K_LEFT) and self.left < 1:
                self.left = 0
            elif (event.key == pygame.K_w or event.key == pygame.K_UP) and self.up < 1:
                self.up = 0
            elif (event.key == pygame.K_s or event.key == pygame.K_DOWN) and self.down > -1:
                self.down = 0

        # code for maintaining the character turned in the same direction, even if the image changes
        elif event.type == USEREVENT+1:
            if self.state == self.hit:
                self.count -= 1
            if self.count <= 0:
                self.state = self.idle
                self.count = 3
            if self.init and self.r:
                self.image = self.state[1]
                self.init = False
            elif self.init and not self.r:
                self.image = self.state[0]
                self.init = False
            elif not self.init and self.r:
                self.image = self.state[3]
                self.init = True
            elif not self.init and not self.r:
                self.image = self.state[2]
                self.init = True

class Zombie(Character):
    """
    Class for the zombie, the main character of the game
    """
    def __init__(self, life):
        Character.__init__(self)
        self.idle = [load_image("idle1.png", -1, size=self.size),
                     pygame.transform.flip(load_image("idle1.png", -1, size=self.size), True, False),
                     load_image("idle2.png", -1, size=self.size),
                     pygame.transform.flip(load_image("idle2.png", -1, size=self.size), True, False)]
        self.hit = [load_image("hit1.png", -1, size=self.size),
                    pygame.transform.flip(load_image("hit1.png", -1, size=self.size), True, False),
                    load_image("hit2.png", -1, size=self.size),
                    pygame.transform.flip(load_image("hit2.png", -1, size=self.size), True, False)]
        self.state = self.idle
        self.image = self.state[0]
        self.life = life
        self.speed = 5
        self.count = 3

        self.roar = load_sound("roar.wav")
        self.roar.set_volume(0.7)
        self.chew = load_sound("chew.wav")
        self.chew.set_volume(1.0)

    def __str__(self):
        return "Zombie with life " + str(self.life) + "."

    def get_life(self):
        return self.life

    def sound_chew(self):
        self.chew.play()

class Human(Character):
    """
    Class for the humans, the enemies of the zombie
    """
    def __init__(self, life):
        Character.__init__(self)
        self.idle = [load_image("idle1.png", -1, size=self.size),
                     pygame.transform.flip(load_image("idle1.png", -1, size=self.size), True, False),
                     load_image("idle2.png", -1, size=self.size),
                     pygame.transform.flip(load_image("idle2.png", -1, size=self.size), True, False)]
        self.hit = [load_image("hit1.png", -1, size=self.size),
                    pygame.transform.flip(load_image("hit1.png", -1, size=self.size), True, False),
                    load_image("hit2.png", -1, size=self.size),
                    pygame.transform.flip(load_image("hit2.png", -1, size=self.size), True, False)]
        self.rect = pygame.Rect((randint(0, self.WIDTH-self.size[0]),randint(0, self.HEIGHT-self.size[1])), self.size)
        self.state = self.idle
        self.image = self.state[0]
        self.life = life
        self.speed = 3
        self.count = 3

        self.roar = load_sound("roar.wav")
        self.roar.set_volume(0.7)
        self.chew = load_sound("chew.wav")
        self.chew.set_volume(1.0)

    def __str__(self):
        return "Human with life " + str(self.life) + "."

    def get_life(self):
        return self.life

    def shoot(self, target, group):
        shot = Shot((self.rect.x, self.rect.y), target, 10)
        group.add((shot))

class Shot(pygame.sprite.Sprite):
    def __init__(self, pos, target, vel):
        pygame.sprite.Sprite.__init__(self)
        self.files = ["shot.wav", "shot2.flac", "shot3.flac"]
        self.sound = load_sound(choice(self.files))
        self.sound.play()
        self.damage = 1
        self.image = pygame.Surface([20,20])
        self.rect = self.image.get_rect()
        self.velocity = vel
        start_pos = pos
        self.rect.x, self.rect.y = start_pos
        self.down, self.right = True, True

        h, w = 0, 0

        init_w = target.rect.x - start_pos[0]
        if init_w > 0:
            w = init_w + (target.rect.width / 2)
        else:
            if init_w < 0:
                w = abs(init_w) - (target.rect.width / 2)
            self.right = False

        init_h = target.rect.y - start_pos[1]
        if init_h > 0:
            h = init_h + (target.rect.height / 2)
        else:
            if init_h < 0:
                h = abs(init_h) - (target.rect.height / 2)
            self.down = False

        hip = sqrt(pow(h, 2) + pow(w, 2))

        if self.right and self.down:
            self.speed = ((self.velocity * w) / hip, (self.velocity * h) / hip)
        elif self.right and not self.down:
            self.speed = ((self.velocity * w) / hip, -(self.velocity * h) / hip)
        elif not self.right and self.down:
            self.speed = (-(self.velocity * w) / hip, (self.velocity * h) / hip)
        elif not self.right and not self.down:
            self.speed = (-(self.velocity * w) / hip, -(self.velocity * h) / hip)

        self.angle = degrees(atan((h / w)))

        if (init_w > WIDTH / 5 and init_h < -(HEIGHT / 5)) or (init_w < -(WIDTH / 5) and init_h > HEIGHT / 5):
            pygame.draw.line(self.image, WHITE, (0, 20), (20, 0), 10)
        elif (init_w > WIDTH / 5 and init_h > HEIGHT / 5) or (init_w < -(WIDTH / 5) and init_h < -(HEIGHT / 5)):
            pygame.draw.line(self.image, WHITE, (0, 0), (20, 20), 10)
        elif abs(init_w) > abs(init_h):
            pygame.draw.line(self.image, WHITE, (0, 10), (20, 10), 10)
        else:
            pygame.draw.line(self.image, WHITE, (10, 0), (10, 20), 10)

        while True:
            color = (randint(0, 19), randint(0, 19))
            if self.image.get_at(color) != WHITE:
                colorkey = self.image.get_at(color)
                self.image.set_colorkey(colorkey, RLEACCEL)
                break

    def __str__(self):
        return "Shot that takes one life"

    def get_damage(self):
        return self.damage

    def update(self):
        self.rect.x += self.speed[0]
        self.rect.y += self.speed[1]
        # if self.hor:
        #     self.rect.x += self.speed[0]
        #     self.rect.y += self.speed[1]
        # else:
        #     self.rect.x += self.speed[0]
        #     self.rect.y += self.speed[1]

# class Shot(pygame.sprite.Sprite):
#     def __init__(self, zombie):
#         pygame.sprite.Sprite.__init__(self)
#         self.files = ["shot.wav", "shot2.flac", "shot3.flac"]
#         self.sound = load_sound(choice(self.files))
#         self.sound.play()
#         self.damage = 1
#         self.image = pygame.Surface([20,20])
#         self.rect = self.image.get_rect()
#         self.hor = choice([True, False])
#         self.velocity = 10
#         if self.hor:
#             loc = randint(0, HEIGHT-1)
#             if choice([True, False]):
#                 start_pos = [0,loc]
#                 self.rect.x = start_pos[0]
#                 self.rect.y = loc
#                 w = zombie.rect.x + (zombie.rect.width / 2)
#                 h = zombie.rect.y - start_pos[1]
#                 if h > 0 or h == 0:
#                     h += (zombie.rect.height / 2)
#                     hip = sqrt(pow(h, 2) + pow(w, 2))
#                     self.speed = ((self.velocity * w) / hip, (self.velocity * h) / hip)
#                 else:
#                     h = abs(h) - (zombie.rect.height / 2)
#                     hip = sqrt(pow(h, 2) + pow(w, 2))
#                     self.speed = ((self.velocity * w) / hip, -(self.velocity * h) / hip)
#                 self.angle = degrees(atan((h / w)))
#             else:
#                 start_pos = [WIDTH-20,loc]
#                 self.rect.x = start_pos[0]
#                 self.rect.y = loc
#                 w = zombie.rect.x - start_pos[0] + (zombie.rect.width / 2)
#                 h = zombie.rect.y - start_pos[1]
#                 if h > 0 or h == 0:
#                     h += (zombie.rect.height / 2)
#                     hip = sqrt(pow(h, 2) + pow(w, 2))
#                     self.speed = ((self.velocity * w) / hip, (self.velocity * h) / hip)
#                 else:
#                     h = abs(h) - (zombie.rect.height / 2)
#                     hip = sqrt(pow(h, 2) + pow(w, 2))
#                     self.speed = ((self.velocity * w) / hip, -(self.velocity * h) / hip)
#                 self.angle = degrees(atan((h / w)))
#             if self.angle > 30:
#                 pygame.draw.line(self.image, WHITE, (0, 0), (20, 20), 10)
#             elif self.angle < -30:
#                 pygame.draw.line(self.image, WHITE, (0, 20), (20, 0), 10)
#             else:
#                 pygame.draw.line(self.image, WHITE, (0, 10), (20, 10), 10)
#             while True:
#                 color = (randint(0, 19), randint(0, 19))
#                 if self.image.get_at(color) != WHITE:
#                     colorkey = self.image.get_at(color)
#                     self.image.set_colorkey(colorkey, RLEACCEL)
#                     break
#         else:
#             above = choice([True, False])
#             loc = randint(0, WIDTH-1)
#             if above:
#                 start_pos = [loc, 0]
#                 self.rect.y = 0
#                 self.rect.x = loc
#                 h = zombie.rect.y + (zombie.rect.height / 2)
#                 w = zombie.rect.x - start_pos[0]
#                 orig_w = w
#                 if w > 0 or w == 0:
#                     w += (zombie.rect.width / 2)
#                     hip = sqrt(pow(h, 2) + pow(w, 2))
#                     self.speed = ((self.velocity * w) / hip, (self.velocity * h) / hip)
#                 else:
#                     w = abs(w) - (zombie.rect.width / 2)
#                     hip = sqrt(pow(h, 2) + pow(w, 2))
#                     self.speed = (-(self.velocity * w) / hip, (self.velocity * h) / hip)
#                 self.angle = degrees(atan((orig_w / h)))
#             else:
#                 start_pos = [loc, HEIGHT-20]
#                 self.rect.y = start_pos[1]
#                 self.rect.x = loc
#                 h = start_pos[1] - zombie.rect.y + (zombie.rect.height / 2)
#                 w = zombie.rect.x - start_pos[0]
#                 orig_w = w
#                 if w > 0 or w == 0:
#                     w += (zombie.rect.width / 2)
#                     hip = sqrt(pow(h, 2) + pow(w, 2))
#                     self.speed = ((self.velocity * w) / hip, -(self.velocity * h) / hip)
#                 else:
#                     w = abs(w) - (zombie.rect.width / 2)
#                     hip = sqrt(pow(h, 2) + pow(w, 2))
#                     self.speed = (-(self.velocity * w) / hip, -(self.velocity * h) / hip)
#                 self.angle = degrees(atan((orig_w / h)))
#
#             if self.angle <= 30 and self.angle >= -30:
#                 pygame.draw.line(self.image, WHITE, (10, 0), (10, 20), 10)
#             else:
#                 if above:
#                     if self.angle > 30:
#                         pygame.draw.line(self.image, WHITE, (0, 0), (20, 20), 10)
#                     elif self.angle < -30:
#                         pygame.draw.line(self.image, WHITE, (20, 0), (0, 20), 10)
#                 else:
#                     if self.angle > 30:
#                         pygame.draw.line(self.image, WHITE, (20, 0), (0, 20), 10)
#                     elif self.angle < -30:
#                         pygame.draw.line(self.image, WHITE, (0, 0), (20, 20), 10)
#             while True:
#                 color = (randint(0, 19), randint(0, 19))
#                 if self.image.get_at(color) != WHITE:
#                     colorkey = self.image.get_at(color)
#                     self.image.set_colorkey(colorkey, RLEACCEL)
#                     break
#
#     def __str__(self):
#         return "Shot that takes one life"
#
#     def get_damage(self):
#         return self.damage
#
#     def update(self):
#         if self.hor:
#             self.rect.x += self.speed[0]
#             self.rect.y += self.speed[1]
#         else:
#             self.rect.x += self.speed[0]
#             self.rect.y += self.speed[1]

class Icons(pygame.sprite.Sprite):
    """
    Class for the icons that will appear on the game
    """
    def __init__(self, icons):
        pygame.sprite.Sprite.__init__(self)
        self.icons = icons
        self.count = 0

    def update(self):
        """
        Blits all of the icons queued
        """
        self.count += 1

class WhiteBrain(Icons):
    """
    Class for the white brains that will appear on the game
    White brains give 1 point for the player
    Inherits from the Icons Class
    """
    def __init__(self, icons):
        Icons.__init__(self, icons)
        self.image = self.icons.subsurface((100, 150, 50, 45))
        self.loc = (randint(0, WIDTH - 50), randint(0, HEIGHT - 50))
        self.rect = pygame.Rect((self.loc), (50, 45))

    def update(self):
        self.count += 1
        if self.count >= 7 and self.count % 2 != 0:
            self.image.set_alpha(0)
        elif self.count >= 7 and self.count % 2 == 0:
            self.image.set_alpha(255)
        elif self.count >= 11:
            self.image.set_alpha(0)

class Hud():
    """
    Class for all the fonts blitted on the screen
    Includes the score, high score, lives, game over and title screen
    """
    def __init__(self, char, high):
        self.width, self.height = get_size()
        self.micro = load_font("creepster.ttf", self.height // 20)
        self.small = load_font("creepster.ttf", self.height // 10)
        self.medium = load_font("creepster.ttf", self.height // 5)
        self.big = load_font("holocaust.ttf", self.height // 3)
        #
        self.score, self.high_score, self.life_left = 0, high, char.get_life()
        self.over = self.medium.render("GAME OVER!!!", True, BLACK)
        self.ask = self.small.render("new game? (Y)es or (N)o", True, BLACK)
        self.up_title = self.big.render("ZOMBIE", True, BLACK)
        self.down_title = self.big.render("ATTACKED", True, BLACK)
        self.ask_title = self.small.render("Press any button", True, BLACK)
        self.me = self.micro.render("Created and developed by Rafael P Ribeiro", True, BLACK)
        #
        self.arrow = self.small.render(">", True, BLACK)
        self.start = self.small.render("Start game", True, BLACK)
        self.reset = self.small.render("Reset high Score", True, BLACK)
        self.sure1 = self.small.render("Are you sure you want to", True, BLACK)
        self.sure2 = self.small.render("reset the high score? (Y) or (N)", True, BLACK)
        self.credits = self.small.render("Credits", True, BLACK)
        self.quit = self.small.render("Quit", True, BLACK)

    def update(self, high):
        self.brains = self.small.render("BRAINS: " + str(self.score), True, BLACK)
        self.lives = self.small.render("LIVES: " + str(self.life_left), True, BLACK)
        self.higher = self.small.render("HIGH SCORE: " + str(high), True, BLACK)

    def draw(self, char, screen, states):
        if states["game_on"]:
            screen.blit(self.brains, (self.width // 20, self.height // 30))
            screen.blit(self.higher, (self.width // 2 - (self.higher.get_width() // 2), self.height // 30))
            screen.blit(self.lives, (self.width - (self.width // 20) - self.lives.get_width(), self.height // 30))
        elif states["dead"]:
            screen.blit(self.brains, (self.width // 20, self.height // 30))
            screen.blit(self.higher, (self.width // 2 - (self.higher.get_width() // 2), self.height // 30))
            screen.blit(self.lives, (self.width - (self.width // 20) - self.lives.get_width(), self.height // 30))
            screen.blit(self.over, (self.width // 2 - (self.over.get_width() // 2), self.height // 2 - (self.over.get_height() // 2)))
            screen.blit(self.ask, (self.width // 2 - (self.ask.get_width() // 2), self.height // 2 + self.ask.get_height()))
        elif states["main_screen"]:
            screen.blit(self.up_title, (self.width // 2 - (self.up_title.get_width() // 2), self.up_title.get_height() // 6))
            screen.blit(self.down_title, (self.width // 2 - (self.down_title.get_width() // 2), self.height // 2 - self.down_title.get_height() // 4))
            screen.blit(self.ask_title, (self.width // 2 - (self.ask_title.get_width() // 2), self.height - self.ask_title.get_height() * 1.7))
            screen.blit(self.me, (self.width // 2 - (self.me.get_width() // 2), self.height - self.me.get_height() * 1.1))
        elif states["main_menu"]:
            i = (4, 8, 12, 16)[states["state"]-1]
            screen.blit(self.arrow, (self.width // 5, self.height // 20 * i))
            screen.blit(self.start, (self.width // 2 - (self.start.get_width() // 2), self.height // 20 * 4))
            screen.blit(self.reset, (self.width // 2 - (self.reset.get_width() // 2), self.height // 20 * 8))
            screen.blit(self.credits, (self.width // 2 - (self.credits.get_width() // 2), self.height // 20 * 12))
            screen.blit(self.quit, (self.width // 2 - (self.quit.get_width() // 2), self.height // 20 * 16))
        elif states["sure"]:
            screen.blit(self.sure1, (self.width // 2 - (self.sure1.get_width() // 2), self.height // 5 * 2))
            screen.blit(self.sure2, (self.width // 2 - (self.sure2.get_width() // 2), self.height // 5 * 3))
        elif states["credit"]:
            screen.blit(self.me, (self.width // 2 - (self.me.get_width() // 2), self.height - self.me.get_height() * 1.1))

    def decr_life(self, damage, high):
        self.life_left -= damage
        self.update(high)

    def incr_score(self, points, high):
        self.score += points
        if self.score > high:
            high += points
        self.update(high)
        return high

class SoundTrack():
    def __init__(self):
        self.intro = load_sound("darkshadow.wav", music=True)
        self.loop = load_sound("darkshadow_loop.wav", music=True)

    def play_intro(self):
        self.intro.play(loops=-1)

    def stop_intro(self):
        self.intro.stop()

    def play_loop(self):
        self.loop.play(loops=-1)

    def stop_loop(self):
        self.loop.stop()

    def fadeout_loop(self, milisecs):
        self.loop.fadeout(milisecs)

if __name__ == "__main__":
    main()

# Red Zombie images acquired from http://opengameart.org/content/bevouliin-free-zombie-sprite-sheets-game-character-for-game-developers
# Zombie sounds acquired from http://soundbible.com/950-Bite.html
# Shooting sounds acquired from https://www.freesound.org/people/LeMudCrab/sounds/163455/, https://www.freesound.org/people/urupin/sounds/192104/ and https://www.freesound.org/people/qubodup/sounds/219456/
# Background grass image acquired from http://opengameart.org/content/synthetic-grass-texture-pack
# Blood splatter animation sheet acquired from http://opengameart.org/content/blood-effect-sprite-sheet and http://opengameart.org/content/blood-splats
# Icons acquired from http://opengameart.org/content/zombie-ui-pack
# Fonts acquired from http://dl.1001fonts.com/zombie-holocaust.zip (by Chad Savage) and http://dl.1001fonts.com/creepster.zip (by Font Diner)
# Soundtrack acquired from http://www.music-note.jp/bgm/mp3/0801/darkshadow_loop.wav and http://www.music-note.jp/bgm/mp3/0801/darkshadow.wav

# TO DO:
# - characters shooting zombie
# - fix delay on the shooting sound
# - make an executable file
# - different kinds of shots
# - special brains and other icons
# - increasing difficulty
# - maybe levels?
