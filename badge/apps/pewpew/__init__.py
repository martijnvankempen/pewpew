import os
import sys

APP_DIR = "/system/apps/pewpew"
os.chdir(APP_DIR)
sys.path.insert(0, APP_DIR)

import math

from badgeware import State

from aliens import ALIEN_H, ALIEN_W, PENS, POINTS, ZAP_PEN, Fleet
from controls import Controls
from fx import Glow, Particles, Shake, Starfield
from pew import CHARGE_FULL, SPRITE, STAR_RADIUS, Pew

W = screen.width
H = screen.height

LOGO = image.load("assets/logo.png")
SMALL = font.nope
LARGE = font.ziplock

SPACE = color.rgb(7, 10, 18)
WHITE = color.rgb(255, 255, 255)
DIM = color.rgb(150, 160, 190)
SHADOW = color.rgb(0, 0, 0, 160)
VEIL = color.rgb(0, 0, 0, 150)
GOLD = color.rgb(255, 228, 90)
PINK = color.rgb(255, 140, 215)
NAVY = color.rgb(41, 65, 89)
RED = color.rgb(226, 59, 59)

MAX_FRAME_MS = 100
BANNER_MS = 1300
OVER_HOLD_MS = 800
WAVE_BONUS = 100

saved = {"highscore": 0, "tilt": False}
State.load("pewpew", saved)
if not isinstance(saved.get("highscore"), int):
    saved["highscore"] = 0
if not isinstance(saved.get("tilt"), bool):
    saved["tilt"] = False

screen.antialias = image.X2


def shadow_text(text, x, y, pen=WHITE):
    screen.pen = SHADOW
    screen.text(text, x + 1, y + 1)
    screen.pen = pen
    screen.text(text, x, y)


def centre_text(text, y, pen=WHITE):
    width, _ = screen.measure_text(text)
    shadow_text(text, (W - width) / 2, y, pen)


class Game:
    TITLE = 0
    PLAY = 1
    PAUSE = 2
    OVER = 3

    def __init__(self):
        self.state = Game.TITLE
        self.space = Starfield()
        self.particles = Particles()
        self.shake = Shake()
        self.glow = Glow()
        self.controls = Controls(saved["tilt"])
        self.clock = 0
        self.score = 0
        self.wave = 1
        self.pew = None
        self.fleet = None
        self.banner_until = 0
        self.over_at = 0
        self.new_best = False

    # ---- state changes -------------------------------------------------------

    def start(self):
        self.clock = 0
        self.score = 0
        self.wave = 1
        self.pew = Pew()
        self.fleet = Fleet(1, self.clock)
        self.banner_until = BANNER_MS
        self.particles.clear()
        self.controls.calibrate()
        self.state = Game.PLAY

    def next_wave(self):
        self.score += WAVE_BONUS
        self.wave += 1
        self.fleet = Fleet(self.wave, self.clock)
        self.banner_until = self.clock + BANNER_MS
        self.glow.chase(badge.ticks, 400)

    def lose_life(self):
        x, y = self.pew.centre()
        self.pew.hit(self.clock)
        self.fleet.zaps = []
        self.particles.burst(x, y, RED, 14, 70)
        self.particles.burst(x, y, NAVY, 8, 40)
        self.shake.kick(5)
        self.glow.flash(1.0)
        if self.pew.lives <= 0:
            self.game_over()

    def game_over(self):
        self.pew.lives = 0
        self.state = Game.OVER
        self.over_at = badge.ticks
        self.new_best = self.score > saved["highscore"]
        if self.new_best:
            saved["highscore"] = self.score
            State.save("pewpew", saved)

    def toggle_tilt(self):
        saved["tilt"] = not saved["tilt"]
        self.controls.tilt = saved["tilt"]
        State.save("pewpew", saved)

    # ---- per-frame logic -----------------------------------------------------

    def update(self, dt_ms):
        now = badge.ticks
        if self.state != Game.PAUSE:
            self.space.update(dt_ms / 1000 * (2.5 if self.state == Game.PLAY else 1))
            self.particles.update(dt_ms)
            self.shake.update(dt_ms)
        self.glow.update(now, dt_ms)

        if self.state == Game.TITLE:
            if badge.pressed(BUTTON_SELECT):
                self.start()
            elif badge.pressed(BUTTON_DOWN):
                self.toggle_tilt()
        elif self.state == Game.PLAY:
            if badge.pressed(BUTTON_MENU) or badge.pressed(BUTTON_BACK):
                self.state = Game.PAUSE
            else:
                self.play(dt_ms)
        elif self.state == Game.PAUSE:
            if badge.pressed(BUTTON_SELECT):
                self.state = Game.PLAY
            elif badge.pressed(BUTTON_BACK):
                self.state = Game.TITLE
        elif now - self.over_at > OVER_HOLD_MS:
            if badge.pressed(BUTTON_SELECT):
                self.start()
            elif badge.pressed(BUTTON_BACK):
                self.state = Game.TITLE

    def play(self, dt_ms):
        self.clock += dt_ms
        now = self.clock
        dt = dt_ms / 1000
        pew = self.pew
        fleet = self.fleet

        pew.move(self.controls.axis(dt_ms), dt)
        if badge.held(BUTTON_SELECT) or badge.pressed(BUTTON_SELECT):
            pew.fire(now)
        if badge.pressed(BUTTON_UP) and pew.burst():
            self.glow.chase(badge.ticks)
            self.glow.flash(1.0)
            self.shake.kick(3)
        pew.update_stars(dt)

        if now >= self.banner_until:
            fleet.update(now, dt, pew.centre()[0])

        for star in pew.stars[:]:
            hit = fleet.hit(star.x, star.y, STAR_RADIUS)
            if hit:
                row, ax, ay, dove = hit
                pew.stars.remove(star)
                pew.add_charge()
                self.score += POINTS[row] * (2 if dove else 1)
                self.particles.burst(ax + ALIEN_W / 2, ay + ALIEN_H / 2, PENS[row], 12 if dove else 8)
                self.shake.kick(2 if dove else 1)
                self.glow.flash(0.7 if dove else 0.5)
            elif fleet.block(star.x, star.y, STAR_RADIUS):
                pew.stars.remove(star)
                self.particles.burst(star.x, star.y, ZAP_PEN, 4, 30)

        if not pew.blinking(now):
            rammed = fleet.ram(pew.hitbox())
            if rammed:
                row, ax, ay = rammed
                self.particles.burst(ax + ALIEN_W / 2, ay + ALIEN_H / 2, PENS[row], 10)
            if rammed or fleet.zap_hits(pew.hitbox()):
                self.lose_life()
                if self.state != Game.PLAY:
                    return

        if fleet.count == 0:
            self.next_wave()
        elif fleet.bottom() >= pew.y + 8:
            x, y = pew.centre()
            self.particles.burst(x, y, RED, 16, 80)
            self.shake.kick(6)
            self.glow.flash(1.0)
            self.game_over()

    # ---- drawing -------------------------------------------------------------

    def draw(self):
        now = badge.ticks
        screen.pen = SPACE
        screen.clear()
        self.space.draw()

        if self.state == Game.TITLE:
            self.draw_title(now)
            return

        ox, oy = self.shake.offset()
        self.fleet.draw(self.clock, ox, oy)
        self.pew.draw(self.clock, ox, oy)
        self.particles.draw(ox, oy)
        self.draw_hud(now)

        if self.state == Game.PLAY and self.clock < self.banner_until:
            screen.font = LARGE
            centre_text("WAVE %d" % self.wave, 52, GOLD)
        elif self.state == Game.PAUSE:
            self.draw_veil()
            screen.font = LARGE
            centre_text("PAUSED", 36)
            screen.font = SMALL
            centre_text("SELECT resume", 66, DIM)
            centre_text("BACK title", 78, DIM)
        elif self.state == Game.OVER:
            self.draw_over(now)

    def draw_veil(self):
        screen.pen = VEIL
        screen.rectangle(0, 0, W, H)

    def draw_hud(self, now):
        screen.font = SMALL
        shadow_text("%d" % self.score, 2, 1)

        pew = self.pew
        if pew.charged():
            if (now // 250) % 2:
                centre_text("UP: BURST!", 1, PINK)
        else:
            centre_text("HI %d" % saved["highscore"], 1, DIM)

        for i in range(pew.lives):
            screen.blit(SPRITE, rect(W - 11 - i * 11, 1, 10, 9))

        screen.pen = PINK if pew.charged() else DIM
        screen.rectangle(0, H - 1, int(W * pew.charge / CHARGE_FULL), 1)

    def draw_title(self, now):
        bob = int(math.sin(now / 400) * 2)
        screen.blit(LOGO, vec2((W - LOGO.width) // 2, 2 + bob))

        screen.font = LARGE
        centre_text("PEW PEW!", 63, GOLD)

        screen.font = SMALL
        centre_text("BEST %d" % saved["highscore"], 80, DIM)
        if (now // 500) % 2:
            centre_text("SELECT to start", 91)
        centre_text("DOWN tilt: %s" % ("ON" if saved["tilt"] else "OFF"), 102, DIM)

    def draw_over(self, now):
        self.draw_veil()
        screen.font = LARGE
        centre_text("GAME OVER", 26, RED)
        screen.font = SMALL
        centre_text("SCORE %d" % self.score, 54)
        centre_text("NEW BEST!" if self.new_best else "BEST %d" % saved["highscore"], 66,
                    GOLD if self.new_best else DIM)
        if now - self.over_at > OVER_HOLD_MS:
            if (now // 500) % 2:
                centre_text("SELECT play again", 88)
            centre_text("BACK title", 100, DIM)


game = Game()


def update():
    dt_ms = min(badge.ticks_delta, MAX_FRAME_MS)
    game.update(dt_ms)
    game.draw()


def on_exit():
    game.glow.off()


run(update)
