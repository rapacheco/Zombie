import os
from random import choice, randrange, randint
from math import atan, degrees, sqrt

import pygame
from pygame.locals import *

# global constants:
WIDTH = 800
HEIGHT = 500
BLACK = (0,0,0)
WHITE = (255,255,255)
MAX_ICONS = 3

# helper functions
def load_image(file, colorkey=None, size=(50,50)):
    fullname = os.path.join("images", file)
    image = pygame.image.load(fullname)
    image = image.convert()
    if colorkey is not None:
        if colorkey is -1:
            colorkey = image.get_at((0,0))
        image.set_colorkey(colorkey, RLEACCEL)
    return pygame.transform.scale(image, size)

def load_sound(name, music=False):
    class NoneSound:
        def play(self): pass
    if not pygame.mixer:
        return NoneSound()
    if music:
        folder = "music"
    else:
        folder = "sounds"
    fullname = os.path.join(folder, name)
    sound = pygame.mixer.Sound(fullname)
    return sound

def load_font(file, size):
    if file is not None:
        fullname = os.path.join("fonts", file)
    else:
        fullname = None
    font = pygame.font.Font(fullname, size)
    return font

def load_high_score():
    fullname = os.path.join("temp", "temp.csv")
    with open(fullname, 'r') as fp:
        temp = fp.read()
        if temp == '':
            high, so_far = 0, 0
        else:
            high, so_far = int(temp), int(temp)
    return high, so_far

def erase_high_score():
    fullname = os.path.join("temp", "temp.csv")
    with open(fullname, 'w') as fp:
        fp.write('0')
    return 0

def update_high_score():
    if high > so_far:
        fullname = os.path.join("temp", "temp.csv")
        with open(fullname, 'w+') as fp:
            fp.write(str(high))

def initialize():
    zombie = Zombie(5)
    hud = Hud(zombie)
    main_char = pygame.sprite.GroupSingle((zombie))
    shooting = pygame.sprite.Group(())
    brains = pygame.sprite.Group(())
    hud.update()
    sound_track = SoundTrack()
    sound_track.play_intro()
    return zombie, hud, main_char, shooting, brains, sound_track

# defines character's classes:
class Zombie(pygame.sprite.Sprite):
    """
    Class for the zombie, the main character of the game
    """
    def __init__(self, life):
        pygame.sprite.Sprite.__init__(self)
        self.idle = [load_image("idle1.png", -1), pygame.transform.flip(load_image("idle1.png", -1), True, False),
                     load_image("idle2.png", -1), pygame.transform.flip(load_image("idle2.png", -1), True, False)]
        self.hit = [load_image("hit1.png", -1), pygame.transform.flip(load_image("hit1.png", -1), True, False),
                    load_image("hit2.png", -1), pygame.transform.flip(load_image("hit2.png", -1), True, False)]
        self.death = load_image("splat.png", -1)
        self.state = self.idle
        self.image = self.state[0]
        self.rect = pygame.Rect([WIDTH/2,HEIGHT/2],[WIDTH/12.8,HEIGHT/9.6])
        self.roar = load_sound("roar.wav")
        self.roar.set_volume(0.8)
        self.chew = load_sound("chew.wav")
        self.chew.set_volume(1.0)
        self.life = life
        self.right, self.left, self.up, self.down = 0, 0, 0, 0
        self.count = 3

    def __str__(self):
        return "Zombie with life " + str(self.life) + "."

    def get_life(self):
        return self.life

    def get_score(self):
        return self.score

    def incr_score(self, points):
        self.score += points

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

    def hurt(self, damage):
        self.state = self.hit
        self.roar.play()
        self.life -= damage

    def sound_chew(self):
        self.chew.play()

    def dying(self):
        self.image = self.death

    def walk(self):
        """
        Makes the character move
        """
        if self.left < 0:
            if self.rect.x >= 0:
                self.rect.x += self.left
        elif self.right > 0:
            if self.rect.x <= WIDTH - self.image.get_width():
                self.rect.x += self.right
        if self.up < 0:
            if self.rect.y >= 0:
                self.rect.y += self.up
        elif self.down > 0:
            if self.rect.y <= HEIGHT - self.image.get_height():
                self.rect.y += self.down

    def movement(self):
        global init, right
        # code to make character turn to the direction it is moved and begin to walk
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_d or event.key == pygame.K_RIGHT:
                self.right = 5
                if not right:
                    self.turn()
                    right = True
            elif event.key == pygame.K_a or event.key == pygame.K_LEFT:
                self.left = -5
                if right:
                    self.turn()
                    right = False
            elif event.key == pygame.K_w or event.key == pygame.K_UP:
                self.up = -5
            elif event.key == pygame.K_s or event.key == pygame.K_DOWN:
                self.down = 5

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
            if init and right:
                self.image = self.state[1]
                init = False
            elif init and not right:
                self.image = self.state[0]
                init = False
            elif not init and right:
                self.image = self.state[3]
                init = True
            elif not init and not right:
                self.image = self.state[2]
                init = True

class Shot(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.files = ["shot.wav", "shot2.flac", "shot3.flac"]
        self.sound = load_sound(choice(self.files))
        self.sound.play()
        self.damage = 1
        self.image = pygame.Surface([20,20])
        self.rect = self.image.get_rect()
        self.hor = choice([True, False])
        self.velocity = 10
        if self.hor:
            loc = randint(0, HEIGHT-1)
            if choice([True, False]):
                start_pos = [0,loc]
                self.rect.x = start_pos[0]
                self.rect.y = loc
                w = zombie.rect.x + (zombie.rect.width / 2)
                h = zombie.rect.y - start_pos[1]
                if h > 0 or h == 0:
                    h += (zombie.rect.height / 2)
                    hip = sqrt(pow(h, 2) + pow(w, 2))
                    self.speed = ((self.velocity * w) / hip, (self.velocity * h) / hip)
                else:
                    h = abs(h) - (zombie.rect.height / 2)
                    hip = sqrt(pow(h, 2) + pow(w, 2))
                    self.speed = ((self.velocity * w) / hip, -(self.velocity * h) / hip)
                self.angle = degrees(atan((h / w)))
            else:
                start_pos = [WIDTH-20,loc]
                self.rect.x = start_pos[0]
                self.rect.y = loc
                w = zombie.rect.x - start_pos[0] + (zombie.rect.width / 2)
                h = zombie.rect.y - start_pos[1]
                if h > 0 or h == 0:
                    h += (zombie.rect.height / 2)
                    hip = sqrt(pow(h, 2) + pow(w, 2))
                    self.speed = ((self.velocity * w) / hip, (self.velocity * h) / hip)
                else:
                    h = abs(h) - (zombie.rect.height / 2)
                    hip = sqrt(pow(h, 2) + pow(w, 2))
                    self.speed = ((self.velocity * w) / hip, -(self.velocity * h) / hip)
                self.angle = degrees(atan((h / w)))
            if self.angle > 30:
                pygame.draw.line(self.image, WHITE, (0, 0), (20, 20), 10)
            elif self.angle < -30:
                pygame.draw.line(self.image, WHITE, (0, 20), (20, 0), 10)
            else:
                pygame.draw.line(self.image, WHITE, (0, 10), (20, 10), 10)
            while True:
                color = (randint(0, 19), randint(0, 19))
                if self.image.get_at(color) != WHITE:
                    colorkey = self.image.get_at(color)
                    self.image.set_colorkey(colorkey, RLEACCEL)
                    break
        else:
            above = choice([True, False])
            loc = randint(0, WIDTH-1)
            if above:
                start_pos = [loc, 0]
                self.rect.y = 0
                self.rect.x = loc
                h = zombie.rect.y + (zombie.rect.height / 2)
                w = zombie.rect.x - start_pos[0]
                orig_w = w
                if w > 0 or w == 0:
                    w += (zombie.rect.width / 2)
                    hip = sqrt(pow(h, 2) + pow(w, 2))
                    self.speed = ((self.velocity * w) / hip, (self.velocity * h) / hip)
                else:
                    w = abs(w) - (zombie.rect.width / 2)
                    hip = sqrt(pow(h, 2) + pow(w, 2))
                    self.speed = (-(self.velocity * w) / hip, (self.velocity * h) / hip)
                self.angle = degrees(atan((orig_w / h)))
            else:
                start_pos = [loc, HEIGHT-20]
                self.rect.y = start_pos[1]
                self.rect.x = loc
                h = start_pos[1] - zombie.rect.y + (zombie.rect.height / 2)
                w = zombie.rect.x - start_pos[0]
                orig_w = w
                if w > 0 or w == 0:
                    w += (zombie.rect.width / 2)
                    hip = sqrt(pow(h, 2) + pow(w, 2))
                    self.speed = ((self.velocity * w) / hip, -(self.velocity * h) / hip)
                else:
                    w = abs(w) - (zombie.rect.width / 2)
                    hip = sqrt(pow(h, 2) + pow(w, 2))
                    self.speed = (-(self.velocity * w) / hip, -(self.velocity * h) / hip)
                self.angle = degrees(atan((orig_w / h)))

            if self.angle <= 30 and self.angle >= -30:
                pygame.draw.line(self.image, WHITE, (10, 0), (10, 20), 10)
            else:
                if above:
                    if self.angle > 30:
                        pygame.draw.line(self.image, WHITE, (0, 0), (20, 20), 10)
                    elif self.angle < -30:
                        pygame.draw.line(self.image, WHITE, (20, 0), (0, 20), 10)
                else:
                    if self.angle > 30:
                        pygame.draw.line(self.image, WHITE, (20, 0), (0, 20), 10)
                    elif self.angle < -30:
                        pygame.draw.line(self.image, WHITE, (0, 0), (20, 20), 10)
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
        if self.hor:
            self.rect.x += self.speed[0]
            self.rect.y += self.speed[1]
        else:
            self.rect.x += self.speed[0]
            self.rect.y += self.speed[1]

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
    def __init__(self):
        Icons.__init__(self, icons)
        self.image = self.icons.subsurface((100, 150, 50, 45))
        self.loc = (randrange(WIDTH - 50), randrange(HEIGHT - 50))
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
    def __init__(self, char):
        self.micro = load_font("creepster.ttf", HEIGHT // 20)
        self.small = load_font("creepster.ttf", HEIGHT // 10)
        self.medium = load_font("creepster.ttf", HEIGHT // 5)
        self.big = load_font("holocaust.ttf", HEIGHT // 3)
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

    def update(self):
        self.brains = self.small.render("BRAINS: " + str(self.score), True, BLACK)
        self.lives = self.small.render("LIVES: " + str(self.life_left), True, BLACK)
        self.higher = self.small.render("HIGH SCORE: " + str(high), True, BLACK)

    def draw(self, char, screen):
        if game_on:
            screen.blit(self.brains, (WIDTH // 20, HEIGHT // 30))
            screen.blit(self.higher, (WIDTH // 2 - (self.higher.get_width() // 2), HEIGHT // 30))
            screen.blit(self.lives, (WIDTH - (WIDTH // 20) - self.lives.get_width(), HEIGHT // 30))
        elif dead:
            screen.blit(self.brains, (WIDTH // 20, HEIGHT // 30))
            screen.blit(self.higher, (WIDTH // 2 - (self.higher.get_width() // 2), HEIGHT // 30))
            screen.blit(self.lives, (WIDTH - (WIDTH // 20) - self.lives.get_width(), HEIGHT // 30))
            screen.blit(self.over, (WIDTH // 2 - (self.over.get_width() // 2), HEIGHT // 2 - (self.over.get_height() // 2)))
            screen.blit(self.ask, (WIDTH // 2 - (self.ask.get_width() // 2), HEIGHT // 2 + self.ask.get_height()))
        # elif game_halt and not dead and main_screen:
        elif main_screen:
            screen.blit(self.up_title, (WIDTH // 2 - (self.up_title.get_width() // 2), self.up_title.get_height() // 6))
            screen.blit(self.down_title, (WIDTH // 2 - (self.down_title.get_width() // 2), HEIGHT // 2 - self.down_title.get_height() // 4))
            screen.blit(self.ask_title, (WIDTH // 2 - (self.ask_title.get_width() // 2), HEIGHT - self.ask_title.get_height() * 1.7))
            screen.blit(self.me, (WIDTH // 2 - (self.me.get_width() // 2), HEIGHT - self.me.get_height() * 1.1))
        elif main_menu:
            i = (4, 8, 12, 16)[state-1]
            screen.blit(self.arrow, (WIDTH // 5, HEIGHT // 20 * i))
            screen.blit(self.start, (WIDTH // 2 - (self.start.get_width() // 2), HEIGHT // 20 * 4))
            screen.blit(self.reset, (WIDTH // 2 - (self.reset.get_width() // 2), HEIGHT // 20 * 8))
            screen.blit(self.credits, (WIDTH // 2 - (self.credits.get_width() // 2), HEIGHT // 20 * 12))
            screen.blit(self.quit, (WIDTH // 2 - (self.quit.get_width() // 2), HEIGHT // 20 * 16))
        elif sure:
            screen.blit(self.sure1, (WIDTH // 2 - (self.sure1.get_width() // 2), HEIGHT // 5 * 2))
            screen.blit(self.sure2, (WIDTH // 2 - (self.sure2.get_width() // 2), HEIGHT // 5 * 3))
        elif credits:
            pass

    def decr_life(self, damage):
        self.life_left -= damage
        self.update()

    def incr_score(self, points):
        global high
        self.score += points
        if self.score > high:
            high += points
        self.update()

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

# initializes pygame and creates a frame
pygame.init()
pygame.font.init()
pygame.mixer.init()
if not pygame.font.get_init():
    print("Warning, fonts disabled")
if pygame.mixer is None:
    print("Warning, sound disabled")
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Zombie Attacked!")

high, so_far = load_high_score()

main_screen_fade = False
zombie, hud, main_char, shooting, brains, sound_track = initialize()

icons = load_image("zombie_icons.png", colorkey=BLACK, size=(400, 200))
background = load_image("background.png", size=(WIDTH, HEIGHT))
blood = load_image("blood.png", -1, size=(300, 50))

pygame.time.set_timer(USEREVENT+1, 500)
pygame.time.set_timer(USEREVENT+2, 1000)
pygame.time.set_timer(USEREVENT+3, 5000)
clock = pygame.time.Clock()

# initializes variables for the main loop
right = False
init = False
done = False
hurt = False
#
main_screen = True
main_menu = False
sure = False
credit = False
game_on = False
dead = False
#
state = 1
count = 0
playtime = 0
cycletime = 0
interval = 1.0

# main loop with the game's logic
while not done:
    # keeps track of time for animation purposes
    milliseconds = clock.tick(60)
    seconds = milliseconds / 1000.0
    playtime += seconds
    cycletime += seconds

    for event in pygame.event.get():
        # playes decides if wants to play a new game or to quit when game ends
        if event.type == pygame.KEYDOWN:
            if main_screen:
                if event.key:
                    # count, alpha = 0, 255
                    # for i in range(255):
                    #     alpha -= 1
                    #     screen.blit(background, (0, 0))
                    #     hud.up_title.set_alpha(alpha)
                    #     hud.down_title.set_alpha(alpha)
                    #     hud.ask_title.set_alpha(alpha)
                    #     hud.me.set_alpha(alpha)
                    #     screen.blit(hud.up_title, (WIDTH // 2 - (hud.up_title.get_width() // 2), hud.up_title.get_height() // 6))
                    #     screen.blit(hud.down_title, (WIDTH // 2 - (hud.down_title.get_width() // 2), HEIGHT // 2 - hud.down_title.get_height() // 4))
                    #     screen.blit(hud.ask_title, (WIDTH // 2 - (hud.ask_title.get_width() // 2), HEIGHT - hud.ask_title.get_height() * 1.7))
                    #     screen.blit(hud.me, (WIDTH // 2 - (hud.me.get_width() // 2), HEIGHT - hud.me.get_height() * 1.1))
                    #     pygame.display.flip()
                    #     pygame.time.delay(1000)
                    main_screen, main_menu = False, True

            if main_menu:
                if event.key == pygame.K_w or event.key == pygame.K_UP:
                    if state == 1:
                        state = 4
                    else:
                        state -= 1

                elif event.key == pygame.K_s or event.key == pygame.K_DOWN:
                    if state == 4:
                        state = 1
                    else:
                        state += 1

                elif event.key == pygame.K_RETURN:
                    if state == 1:
                        main_menu, game_on = False, True
                        sound_track.stop_intro()
                        sound_track.play_loop()

                    elif state == 2:
                        main_menu, sure = False, True

                    elif state == 3:
                        main_menu, credit = False, True

                    elif state == 4:
                        done = True

            if sure:
                if event.key == pygame.K_y:
                    high = erase_high_score()
                    hud.update()
                    main_menu, sure = True, False
                elif event.key == pygame.K_n:
                    main_menu, sure = True, False

            if credits:
                if event.key:
                    main_menu, credits = True, False

            if dead:
                if event.key == pygame.K_y:
                    zombie, hud, main_char, shooting, brains, sound_track = initialize()
                    sound_track.play_loop()
                    game_on, dead = True, False
                elif event.key == pygame.K_n:
                    # closes the game window
                    zombie, hud, main_char, shooting, brains, sound_track = initialize()
                    sound_track.play_intro()
                    hud.update()
                    main_menu, dead, state = True, False, 1

        elif event.type == USEREVENT+1 and game_on:
            brains.update()
        elif event.type == USEREVENT+2 and game_on:
            shot = Shot()
            shooting.add((shot))
            # pass
        elif event.type == USEREVENT+3 and game_on:
            white_brain = WhiteBrain()
            brains.add((white_brain))
        elif event.type == pygame.QUIT:
            done = True
        zombie.movement()

    # if zombie gets shot, takes damage
    for coll in pygame.sprite.groupcollide(shooting, main_char, True, False):
        dam = coll.get_damage()
        zombie.hurt(dam)
        hud.decr_life(dam)
        hurt = True

    # if zombie gets a brain, improve score
    for catch in pygame.sprite.groupcollide(brains, main_char, True, False):
        hud.incr_score(1)
        zombie.sound_chew()

    # sets maximum amount of brains in 10
    for b in brains:
        if b.count >= 11:
            brains.remove((b))

    # remove the shots as soon as they clear the screen
    for s in shooting:
        if s.rect.x < -20 or s.rect.x > WIDTH+20 or s.rect.y < -20 or s.rect.y > HEIGHT+20:
            shooting.remove((s))

    # if zombie gets hurt, spray of blood
    if hurt:
        if cycletime > interval and count < 6:
            background.blit(blood, (zombie.rect.x, zombie.rect.y, 50, 50), area=(50 * count, 0, 50, 50))
            count += 1
        elif count >= 6:
            count = 0
            hurt = False

    # if run out of lives, zombie dies and game over
    if zombie.life <= 0:
        zombie.dying()
        game_on, dead = False, True
        sound_track.fadeout_loop(2500)

    # paint the screen black and draw background
    screen.fill(BLACK)
    screen.blit(background, (0, 0))

    # allows the zombie to walk and the shooting to take place
    if game_on:
        zombie.walk()
        shooting.update()
        main_char.draw(screen)

    # code for drawing the elements in the screen
    hud.draw(zombie, screen)
    # if not game_halt:
    shooting.draw(screen)
    brains.draw(screen)
    pygame.display.flip()

update_high_score()
pygame.quit()

# Red Zombie images acquired from http://opengameart.org/content/bevouliin-free-zombie-sprite-sheets-game-character-for-game-developers
# Zombie sounds acquired from http://soundbible.com/950-Bite.html
# Shooting sounds acquired from https://www.freesound.org/people/LeMudCrab/sounds/163455/, https://www.freesound.org/people/urupin/sounds/192104/ and https://www.freesound.org/people/qubodup/sounds/219456/
# Background grass image acquired from http://opengameart.org/content/synthetic-grass-texture-pack
# Blood splatter animation sheet acquired from http://opengameart.org/content/blood-effect-sprite-sheet and http://opengameart.org/content/blood-splats
# Icons acquired from http://opengameart.org/content/zombie-ui-pack
# Fonts acquired from http://dl.1001fonts.com/zombie-holocaust.zip (by Chad Savage) and http://dl.1001fonts.com/creepster.zip (by Font Diner)
# Soundtrack acquired from http://www.music-note.jp/bgm/mp3/0801/darkshadow_loop.wav and http://www.music-note.jp/bgm/mp3/0801/darkshadow.wav

# TO DO:
# - fix delay on the shooting sound
# - main screen
# - way to restart high score
# - make an executable file
# - different kinds of shots
# - special brains and other icons
# - increasing difficulty
# - maybe levels?
