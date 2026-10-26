import os
import sys

APP_DIR = "/system/apps/pewpew"
os.chdir(APP_DIR)
sys.path.insert(0, APP_DIR)

import math
import random

from badgeware import State

from aliens import ALIEN_H, ALIEN_W, PENS, POINTS, RGBS, SHEET, ZAP_PEN, Fleet, draw_flash
from boss import BOSS_H, BOSS_W, RGB as BOSS_RGB, Boss
from controls import Controls
from fx import Flash, Glow, Particles, Popups, Rings, Shake, Starfield, draw_star
from pew import CHARGE_FULL, SPRITE, SPRITE_W, STAR_RADIUS, Pew

W = screen.width
H = screen.height

LOGO = image.load("assets/logo.png")
FORKLIFT = image.load("assets/forklift.png")
SMALL = font.nope
LARGE = font.ziplock
# Rows of the font bitmaps that hold capital letters (used for the gradients).
LARGE_CAPS = (5, 18)
SMALL_CAPS = (3, 11)

WHITE = color.rgb(255, 255, 255)
DIM = color.rgb(175, 185, 215)
SHADOW = color.rgb(0, 0, 0, 160)
VEIL = color.rgb(0, 0, 0, 150)
DARK_VEIL = color.rgb(4, 6, 14, 235)
BAR_BACK = color.rgb(0, 0, 0, 170)
PANEL = color.rgb(0, 0, 0, 120)
GOLD = color.rgb(255, 228, 90)
PINK = color.rgb(255, 140, 215)
NAVY = color.rgb(41, 65, 89)
RED = color.rgb(226, 59, 59)
CYAN = color.rgb(120, 220, 255)
BOSS_PEN = color.rgb(*BOSS_RGB)
MEDALS = (color.rgb(255, 215, 80), color.rgb(205, 215, 235), color.rgb(225, 150, 90))
BLACK = color.rgb(0, 0, 0)
INK = color.rgb(40, 22, 18)
AD_YELLOW = color.rgb(255, 212, 55)
AD_RAY = color.rgb(255, 188, 30)
DUST = color.rgb(150, 120, 80)

# Gradient styles for big text: (top, bottom, outline).
GOLDEN = ((255, 250, 190), (255, 140, 30), (60, 20, 10))
ROSE = ((255, 215, 245), (220, 50, 170), (50, 10, 45))
CRIMSON = ((255, 200, 180), (215, 25, 40), (45, 5, 10))
ICE = ((225, 255, 255), (50, 140, 255), (10, 20, 60))

MAX_FRAME_MS = 100
BANNER_MS = 1300
AD_MS = 3000
AD_DRIVE_MS = 600
CLEAR_MS = 2000
WARNING_MS = 2600
WAVE_BONUS = 100
PERFECT_BONUS = 500
BOSS_BONUS = 1000
BOSS_HIT = 10
COMBO_STEPS = (5, 10, 20, 30)
TITLE_IDLE_MS = 9000
DEMO_MS = 30000
SCORES_MS = 6500
ENTRY_IDLE_MS = 30000
BOARD_SIZE = 5
LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 "
DEFAULT_BOARD = [["PEW", 2500], ["OCT", 2000], ["GIT", 1500], ["HUB", 1000], ["CAT", 500]]
MENU_BUTTONS = (BUTTON_UP, BUTTON_DOWN, BUTTON_LEFT, BUTTON_RIGHT, BUTTON_SELECT, BUTTON_BACK, BUTTON_MENU)


# ---- saved data -------------------------------------------------------------

def clean_board(board):
    out = []
    if isinstance(board, list):
        for entry in board:
            if (isinstance(entry, (list, tuple)) and len(entry) == 2 and isinstance(entry[0], str)
                    and isinstance(entry[1], int) and entry[1] >= 0):
                name = "".join(ch for ch in entry[0].upper()[:3] if ch in LETTERS)
                out.append([(name + "   ")[:3], entry[1]])
    out.sort(key=lambda e: -e[1])
    return out[:BOARD_SIZE]


saved = {"highscore": 0, "tilt": False, "board": None, "name": "AAA"}
State.load("pewpew", saved)
if not isinstance(saved.get("highscore"), int):
    saved["highscore"] = 0
if not isinstance(saved.get("tilt"), bool):
    saved["tilt"] = False
if not isinstance(saved.get("name"), str) or len(saved["name"]) != 3 or any(ch not in LETTERS for ch in saved["name"]):
    saved["name"] = "AAA"
if saved.get("board") is None:
    saved["board"] = [list(e) for e in DEFAULT_BOARD]
    if saved["highscore"] > DEFAULT_BOARD[-1][1]:
        saved["board"].append(["YOU", saved["highscore"]])
saved["board"] = clean_board(saved["board"])


def best_score():
    top = saved["board"][0][1] if saved["board"] else 0
    return max(top, saved["highscore"])


def board_rank(score):
    """Where a score would land on the board (0-based), or None if it doesn't make it."""
    if score <= 0:
        return None
    for i, (_name, value) in enumerate(saved["board"]):
        if score > value:
            return i
    return len(saved["board"]) if len(saved["board"]) < BOARD_SIZE else None


screen.antialias = image.X2


# ---- text helpers -----------------------------------------------------------

def shadow_text(text, x, y, pen=WHITE, scale=1):
    screen.pen = SHADOW
    screen.text(text, x + scale, y + scale, scale)
    screen.pen = pen
    screen.text(text, x, y, scale)


def centre_text(text, y, pen=WHITE, scale=1):
    width, _ = screen.measure_text(text, scale)
    shadow_text(text, (W - width) / 2, y, pen, scale)


def mix(a, b, t):
    return (int(a[0] + (b[0] - a[0]) * t), int(a[1] + (b[1] - a[1]) * t), int(a[2] + (b[2] - a[2]) * t))


class Label:
    """Big text pre-rendered once: drop shadow, outline and a vertical gradient fill.

    `shine` is a white copy of the fill, for highlight sweeps and hit flashes.
    """

    def __init__(self, text, style, fnt=LARGE, caps=LARGE_CAPS):
        top, bottom, outline = style
        screen.font = fnt
        w, h = screen.measure_text(text)
        self.width = int(w) + 3
        self.height = int(h) + 3
        self.img = image(self.width, self.height)
        self.shine = image(self.width, self.height)
        img = self.img
        img.font = fnt
        img.pen = color.rgb(0, 0, 0, 170)
        img.text(text, 2, 3)
        img.pen = color.rgb(*outline)
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, -1), (-1, 1), (1, 1)):
            img.text(text, 1 + dx, 1 + dy)
        first, last = caps
        bands = last - first
        for i in range(bands + 2):
            y = 0 if i == 0 else first + i
            tall = first + 2 if i == 0 else (1 if i <= bands else self.height)
            img.clip = rect(0, y, self.width, tall)
            img.pen = color.rgb(255, 255, 255) if i == 1 else color.rgb(*mix(top, bottom, min(1.0, i / bands)))
            img.text(text, 1, 1)
        img.clip = rect(0, 0, self.width, self.height)
        self.shine.font = fnt
        self.shine.pen = color.rgb(255, 255, 255)
        self.shine.text(text, 1, 1)
        self.caps = caps

    def draw(self, cx, cy, scale=1.0, shine=False):
        """Draw centred on (cx, cy), where cy is the middle of the capital letters."""
        w = self.width * scale
        h = self.height * scale
        mid = (self.caps[0] + self.caps[1]) / 2 + 1
        box = rect(int(cx - w / 2), int(cy - mid * scale), int(w), int(h))
        screen.blit(self.shine if shine else self.img, box)


labels = {}


def label(text, style):
    key = (text, style)
    if key not in labels:
        if len(labels) > 24:
            labels.clear()
        labels[key] = Label(text, style)
    return labels[key]


def punch(age_ms, ms=220):
    """Scale for text that slams in: big, then settles on 1 with a little overshoot."""
    if age_ms >= ms:
        return 1.0
    t = age_ms / ms
    return 1 + 1.2 * (1 - t) * (1 - t) - 0.15 * math.sin(t * math.pi)


def ease_out_back(t):
    t = max(0.0, min(1.0, t)) - 1
    return 1 + t * t * (2.7 * t + 1.7)


def bounce(t):
    """Drop that lands at 1 and bounces twice."""
    if t >= 1:
        return 1.0
    t = max(0.0, t)
    if t < 0.6:
        return (t / 0.6) ** 2
    t -= 0.8
    return 1 - (0.04 - t * t) * 4 if t < 0.2 else 1.0


def ad_forklift_x(t):
    """The ad's forklift reverses in from the left and parks at x=6."""
    return -FORKLIFT.width + (6 + FORKLIFT.width) * ease_out_back(t / AD_DRIVE_MS)


def ink_text(text, cx, y):
    """Dark text with a light drop shadow, for the yellow ad background."""
    width, _ = screen.measure_text(text)
    screen.pen = color.rgb(255, 255, 255, 150)
    screen.text(text, cx - width / 2 + 1, y + 1)
    screen.pen = INK
    screen.text(text, cx - width / 2, y)


def hazard(y, shift):
    """A 6 px yellow-and-black hazard stripe across the screen."""
    screen.pen = AD_YELLOW
    screen.rectangle(0, y, W, 6)
    screen.pen = BLACK
    for x in range(-12, W + 12, 12):
        x0 = x + shift
        screen.triangle(vec2(x0, y), vec2(x0 + 6, y), vec2(x0, y + 6))
        screen.triangle(vec2(x0, y), vec2(x0, y + 6), vec2(x0 - 6, y + 6))


class Game:
    TITLE = 0
    PLAY = 1
    PAUSE = 2
    AD = 3
    ENTRY = 4
    SCORES = 5

    FIGHT = 0
    CLEAR = 1
    WARNING = 2

    def __init__(self):
        self.space = Starfield()
        self.particles = Particles()
        self.rings = Rings()
        self.popups = Popups()
        self.shake = Shake()
        self.flash = Flash()
        self.glow = Glow()
        self.controls = Controls(saved["tilt"])
        self.clock = 0
        self.score = 0
        self.shown_score = 0.0
        self.wave = 1
        self.pew = None
        self.fleet = None
        self.phase = Game.FIGHT
        self.phase_until = 0
        self.phase_at = 0
        self.banner_until = 0
        self.new_best = False
        self.demo = False
        self.freeze = 0
        self.ghosts = []
        self.callout = None
        self.burst_at = -9999
        self.burst_queued = False
        self.next_boom = 0
        self.clear_text = ""
        self.perfect = False
        self.combo = 0
        self.wave_damage = 0
        self.rank = None
        self.entry_name = list(saved["name"])
        self.entry_pos = 0
        self.entry_at = 0
        self.highlight = None
        self.state_at = 0
        self.title_at = 0
        self.title_landed = False
        self.comet = None
        self.go_title(badge.ticks)

    # ---- state changes -------------------------------------------------------

    def set_state(self, state, now):
        self.state = state
        self.state_at = now
        self.glow.breathe = state in (Game.TITLE, Game.SCORES) or (state == Game.PLAY and self.demo)

    def go_title(self, now):
        self.demo = False
        self.title_at = now
        self.title_landed = False
        self.space.set_wave(1, False)
        self.space.warp_target = 0.0
        self.particles.clear()
        self.rings.clear()
        self.popups.clear()
        self.set_state(Game.TITLE, now)

    def show_scores(self, now, highlight=None):
        self.demo = False
        self.highlight = highlight
        self.space.warp_target = 0.0
        self.set_state(Game.SCORES, now)

    def start(self, demo=False):
        self.demo = demo
        self.clock = 0
        self.score = 0
        self.shown_score = 0.0
        self.wave = 1
        self.combo = 0
        self.freeze = 0
        self.ghosts = []
        self.callout = None
        self.burst_at = -9999
        self.burst_queued = False
        self.pew = Pew()
        self.particles.clear()
        self.rings.clear()
        self.popups.clear()
        self.controls.calibrate()
        self.begin_wave()
        self.set_state(Game.PLAY, badge.ticks)

    def begin_wave(self):
        boss = self.wave % 3 == 0
        self.space.set_wave(self.wave, boss)
        self.space.warp_target = 0.0
        self.wave_damage = 0
        self.phase_at = self.clock
        if boss:
            self.fleet = Boss(self.wave, self.clock)
            self.phase = Game.WARNING
            self.phase_until = self.clock + WARNING_MS
            self.banner_until = self.clock
            self.glow.alarm(badge.ticks, WARNING_MS)
        else:
            self.fleet = Fleet(self.wave, self.clock)
            self.phase = Game.FIGHT
            self.banner_until = self.clock + BANNER_MS

    def wave_cleared(self):
        boss = isinstance(self.fleet, Boss)
        self.perfect = self.wave_damage == 0
        bonus = WAVE_BONUS + (PERFECT_BONUS if self.perfect else 0)
        self.score += bonus
        self.clear_text = "BOSS DOWN!" if boss else "WAVE CLEAR"
        self.phase = Game.CLEAR
        self.phase_at = self.clock
        self.phase_until = self.clock + CLEAR_MS
        self.glow.chase(badge.ticks, 600)
        # Any alien shots still flying fizzle into sparks.
        for z in self.fleet.zaps:
            self.particles.burst(z[0], z[1], ZAP_PEN, 3, 25)
        self.fleet.zaps = []
        self.popups.add(W / 2, 86, "+%d" % bonus, (255, 228, 90), 1200)

    def lose_life(self):
        x, y = self.pew.centre()
        self.pew.hit(self.clock)
        self.fleet.zaps = []
        self.particles.burst(x, y, RED, 14, 70)
        self.particles.burst(x, y, NAVY, 8, 40)
        self.rings.add(x, y, (255, 80, 80), 26, 420)
        self.shake.kick(5)
        self.flash.kick(0.7, (255, 40, 40))
        self.glow.flash(1.0)
        self.freeze = 120
        self.wave_damage += 1
        self.break_combo()
        if self.pew.lives <= 0:
            self.game_over()

    def game_over(self):
        now = badge.ticks
        self.pew.lives = 0
        if isinstance(self.fleet, Boss):
            self.fleet.attack = None
        if self.demo:
            self.show_scores(now)
            return
        self.rank = board_rank(self.score)
        self.new_best = self.score > best_score()
        if self.score > saved["highscore"]:
            saved["highscore"] = self.score
            State.save("pewpew", saved)
        self.particles.clear()
        self.glow.alarm(now, AD_MS)
        self.set_state(Game.AD, now)

    def end_ad(self, now):
        if self.rank is not None:
            self.enter_name(now)
        else:
            self.go_title(now)

    def enter_name(self, now):
        self.entry_name = list(saved["name"])
        self.entry_pos = 0
        self.entry_at = now
        self.set_state(Game.ENTRY, now)

    def save_name(self, now):
        name = "".join(self.entry_name)
        saved["name"] = name
        board = saved["board"]
        board.insert(self.rank, [name, self.score])
        del board[BOARD_SIZE:]
        State.save("pewpew", saved)
        self.show_scores(now, self.rank)

    def toggle_tilt(self):
        saved["tilt"] = not saved["tilt"]
        self.controls.tilt = saved["tilt"]
        State.save("pewpew", saved)

    # ---- scoring -------------------------------------------------------------

    def multiplier(self):
        return 1 + sum(1 for step in COMBO_STEPS if self.combo >= step)

    def add_points(self, base, x, y, rgb):
        mult = self.multiplier()
        points = base * mult
        self.score += points
        self.popups.add(x, y - 4, "+%d" % points, (255, 228, 90) if mult > 1 else rgb)

    def count_hit(self):
        before = self.multiplier()
        self.combo += 1
        after = self.multiplier()
        if after > before:
            self.call("COMBO x%d" % after, GOLDEN, 900)
            x, y = self.pew.centre()
            self.rings.add(x, y, (255, 228, 90), 22, 380)
            self.glow.flash(0.8)

    def break_combo(self):
        if self.combo >= COMBO_STEPS[0]:
            x, y = self.pew.centre()
            self.popups.add(x, y - 16, "COMBO LOST", (150, 160, 190), 600)
        self.combo = 0

    def call(self, text, style, ms):
        self.callout = (label(text, style), self.clock, ms)

    # ---- input ---------------------------------------------------------------

    def any_pressed(self):
        for button in MENU_BUTTONS:
            if badge.pressed(button):
                return True
        return False

    def update(self, dt_ms):
        now = badge.ticks
        if self.state != Game.PAUSE:
            self.space.update(dt_ms / 1000 * (2.5 if self.state == Game.PLAY else 1))
        self.flash.update(dt_ms)
        self.glow.update(now, dt_ms)
        if self.state != Game.PAUSE:
            self.shake.update(dt_ms)

        if self.state == Game.PLAY and self.freeze > 0:
            # Hit-stop: hold the frame for a beat so big hits land.
            self.freeze -= dt_ms
            if self.demo and self.any_pressed():
                self.go_title(now)
            elif badge.pressed(BUTTON_UP):
                self.burst_queued = True
            return

        if self.state != Game.PAUSE:
            self.particles.update(dt_ms)
            self.rings.update(dt_ms)
            self.popups.update(dt_ms)

        if self.state == Game.TITLE:
            if badge.pressed(BUTTON_SELECT):
                self.start()
            elif badge.pressed(BUTTON_DOWN):
                self.toggle_tilt()
                self.title_at = min(self.title_at, now - 1200)
                self.state_at = now
            elif self.any_pressed():
                self.title_at = min(self.title_at, now - 1200)
                self.state_at = now
            if self.state == Game.TITLE and now - self.state_at > TITLE_IDLE_MS:
                self.start(demo=True)
        elif self.state == Game.SCORES:
            if badge.pressed(BUTTON_SELECT):
                self.start()
            elif self.any_pressed():
                self.go_title(now)
            elif now - self.state_at > SCORES_MS:
                self.go_title(now)
        elif self.state == Game.PLAY:
            if self.demo:
                if badge.pressed(BUTTON_SELECT):
                    self.start()
                elif self.any_pressed():
                    self.go_title(now)
                elif now - self.state_at > DEMO_MS:
                    self.show_scores(now)
                else:
                    self.play(dt_ms)
            elif badge.pressed(BUTTON_MENU) or badge.pressed(BUTTON_BACK):
                self.set_state(Game.PAUSE, now)
            else:
                self.play(dt_ms)
        elif self.state == Game.PAUSE:
            if badge.pressed(BUTTON_SELECT):
                self.set_state(Game.PLAY, now)
            elif badge.pressed(BUTTON_BACK):
                self.go_title(now)
        elif self.state == Game.AD:
            # Unskippable: no button does anything until the ad has run.
            t = now - self.state_at
            if t < AD_DRIVE_MS and random.random() < 0.6:
                self.particles.burst(ad_forklift_x(t) + 10, 92, DUST, 1, 25)
            if t >= AD_MS:
                self.end_ad(now)
        elif self.state == Game.ENTRY:
            self.update_entry(now)

    def update_entry(self, now):
        name = self.entry_name
        i = self.entry_pos
        if badge.pressed(BUTTON_UP):
            name[i] = LETTERS[(LETTERS.index(name[i]) + 1) % len(LETTERS)]
            self.entry_at = now
        elif badge.pressed(BUTTON_DOWN):
            name[i] = LETTERS[(LETTERS.index(name[i]) - 1) % len(LETTERS)]
            self.entry_at = now
        elif badge.pressed(BUTTON_RIGHT):
            self.entry_pos = min(2, i + 1)
            self.entry_at = now
        elif badge.pressed(BUTTON_LEFT) or badge.pressed(BUTTON_BACK):
            self.entry_pos = max(0, i - 1)
            self.entry_at = now
        elif badge.pressed(BUTTON_SELECT):
            self.entry_at = now
            if i < 2:
                self.entry_pos += 1
            else:
                self.save_name(now)
        elif now - self.entry_at > ENTRY_IDLE_MS:
            self.save_name(now)

    def demo_axis(self):
        """Attract-mode pilot: line up under a target, sidestep anything falling close."""
        pew = self.pew
        px, py = pew.centre()
        fleet = self.fleet
        goal = px
        if isinstance(fleet, Boss):
            goal = fleet.core()[0]
            if fleet.attack == "beam" and abs(fleet.beam_x - px) < 22:
                goal = px + (30 if px < fleet.beam_x else -30)
                if goal < 14 or goal > W - 14:
                    goal = px - (goal - px)
        elif fleet.divers:
            d = fleet.divers[0]
            goal = d.x + ALIEN_W / 2
        else:
            best = None
            for c in range(5):
                for r in range(2, -1, -1):
                    if fleet.slots[r][c] == 1:
                        ax, _ay = fleet.slot_pos(r, c)
                        dist = abs(ax + ALIEN_W / 2 - px)
                        if best is None or dist < best[0]:
                            best = (dist, ax + ALIEN_W / 2)
                        break
            if best:
                goal = best[1]
        for z in fleet.zaps:
            if py - 45 < z[1] < py + 6 and abs(z[0] - px) < 13:
                goal = px + (25 if z[0] < px else -25)
                if goal < 10 or goal > W - 10:
                    goal = px - (goal - px)
        return max(-1.0, min(1.0, (goal - px) / 8))

    # ---- per-frame play ------------------------------------------------------

    def play(self, dt_ms):
        self.clock += dt_ms
        now = self.clock
        dt = dt_ms / 1000
        pew = self.pew
        fleet = self.fleet
        boss = isinstance(fleet, Boss)

        self.shown_score += (self.score - self.shown_score) * min(1.0, dt * 8)
        if self.score - self.shown_score < 1:
            self.shown_score = self.score
        self.ghosts = [g for g in self.ghosts if g[3] > now]

        if self.demo:
            axis = self.demo_axis()
            fire = True
            use_burst = pew.charged()
        else:
            axis = self.controls.axis(dt_ms)
            fire = badge.held(BUTTON_SELECT) or badge.pressed(BUTTON_SELECT)
            use_burst = badge.pressed(BUTTON_UP) or self.burst_queued
        self.burst_queued = False
        pew.move(axis, dt)
        if fire:
            pew.fire(now)
        if use_burst and pew.burst():
            self.burst_at = now
            self.call("OCTO-BURST!", ROSE, 900)
            self.glow.chase(badge.ticks)
            self.glow.flash(1.0)
            self.shake.kick(3)
            self.flash.kick(0.45, (255, 140, 215))
            x, y = pew.centre()
            self.rings.add(x, y, (255, 140, 215), 40, 450)
            self.freeze = 90
        if pew.update_stars(dt):
            self.break_combo()

        fleet.settle(dt)
        if self.phase == Game.WARNING:
            if now >= self.phase_until:
                self.phase = Game.FIGHT
                self.phase_at = now
        elif self.phase == Game.CLEAR:
            if now - self.phase_at > 700:
                self.space.warp_target = 1.0
            if now >= self.phase_until:
                self.wave += 1
                self.begin_wave()
                return
        elif now >= self.banner_until:
            fleet.update(now, dt, pew.centre()[0])

        if boss:
            self.play_boss(now)
        else:
            self.play_fleet()
        if self.state != Game.PLAY:
            return

        if not pew.blinking(now) and self.phase != Game.CLEAR:
            rammed = fleet.ram(pew.hitbox())
            if rammed:
                row, ax, ay = rammed
                self.particles.burst(ax + ALIEN_W / 2, ay + ALIEN_H / 2, PENS[row], 10)
            if rammed or fleet.zap_hits(pew.hitbox()) or (boss and fleet.beam_hits(pew.hitbox())):
                self.lose_life()
                if self.state != Game.PLAY:
                    return

        if self.phase == Game.FIGHT:
            if fleet.count == 0:
                self.wave_cleared()
            elif fleet.bottom() >= pew.y + 8:
                x, y = pew.centre()
                self.particles.burst(x, y, RED, 16, 80)
                self.shake.kick(6)
                self.flash.kick(0.8, (255, 40, 40))
                self.glow.flash(1.0)
                self.game_over()

    def play_fleet(self):
        pew = self.pew
        fleet = self.fleet
        for star in pew.stars[:]:
            hit = fleet.hit(star.x, star.y, STAR_RADIUS)
            if hit:
                row, ax, ay, dove = hit
                cx = ax + ALIEN_W / 2
                cy = ay + ALIEN_H / 2
                pew.stars.remove(star)
                pew.add_charge()
                self.count_hit()
                self.add_points(POINTS[row] * (2 if dove else 1), cx, ay, RGBS[row])
                self.ghosts.append((ax, ay, row, self.clock + 70))
                self.particles.burst(cx, cy, PENS[row], 14 if dove else 10, 70 if dove else 55)
                self.rings.add(cx, cy, RGBS[row], 18 if dove else 13, 340)
                self.shake.kick(2 if dove else 1)
                self.glow.flash(0.7 if dove else 0.5)
                self.freeze = max(self.freeze, 60 if dove else 35)
            elif fleet.block(star.x, star.y, STAR_RADIUS):
                pew.stars.remove(star)
                self.particles.burst(star.x, star.y, ZAP_PEN, 4, 30)

    def play_boss(self, now):
        pew = self.pew
        boss = self.fleet
        for star in pew.stars[:]:
            hit = boss.hit(star.x, star.y, STAR_RADIUS)
            if hit:
                x, y, killed = hit
                pew.stars.remove(star)
                pew.add_charge()
                self.count_hit()
                self.add_points(BOSS_HIT, x, y, BOSS_RGB)
                self.particles.burst(x, y, BOSS_PEN, 5, 45)
                self.glow.flash(0.4)
                if killed:
                    self.boss_killed()
                    break
            elif boss.block(star.x, star.y, STAR_RADIUS):
                pew.stars.remove(star)
                self.particles.burst(star.x, star.y, ZAP_PEN, 4, 30)

        if boss.dying and now >= self.next_boom:
            # Chain of explosions across the hull while it goes down.
            self.next_boom = now + 70
            x = boss.x + random.uniform(4, BOSS_W - 4)
            y = boss.y + random.uniform(2, BOSS_H - 6)
            pen = (BOSS_PEN, GOLD, WHITE, PINK)[random.randrange(4)]
            self.particles.burst(x, y, pen, 8, 70)
            self.rings.add(x, y, (255, 228, 160), 14, 280)
            self.flash.kick(0.25, (255, 200, 120))
            self.shake.kick(1.5)
            self.glow.flash(0.8)
        if boss.count == 0 and self.phase == Game.FIGHT:
            x, y = boss.core()
            for pen in (BOSS_PEN, GOLD, WHITE, PINK):
                self.particles.burst(x, y, pen, 10, 110)
            self.rings.add(x, y, (255, 255, 255), 60, 600)
            self.rings.add(x, y, BOSS_RGB, 40, 500)
            self.flash.kick(1.0)
            self.shake.kick(6)
            self.glow.chase(badge.ticks, 900)

    def boss_killed(self):
        boss = self.fleet
        x, y = boss.core()
        self.score += BOSS_BONUS * boss.stage
        self.popups.add(x, y - 10, "+%d" % (BOSS_BONUS * boss.stage), (255, 228, 90), 1400)
        self.flash.kick(0.9)
        self.shake.kick(6)
        self.freeze = 260
        self.next_boom = self.clock

    # ---- drawing -------------------------------------------------------------

    def draw(self):
        now = badge.ticks
        self.space.draw()

        if self.state == Game.TITLE:
            self.draw_title(now)
        elif self.state == Game.SCORES:
            self.draw_scores(now)
        elif self.state == Game.AD:
            self.draw_ad(now)
        else:
            self.draw_play(now)
        self.flash.draw()

    def draw_play(self, now):
        ox, oy = self.shake.offset()
        clock = self.clock
        if self.phase != Game.CLEAR or self.fleet.zaps:
            self.fleet.draw(clock, ox, oy)
        for x, y, row, _until in self.ghosts:
            draw_flash(row, x + ox, y + oy)
        self.draw_burst_fx(clock, ox, oy)
        self.pew.draw(clock, ox, oy)
        self.particles.draw(ox, oy)
        self.rings.draw(ox, oy)
        self.popups.draw(ox, oy)
        if self.state == Game.ENTRY:
            screen.pen = DARK_VEIL
            screen.rectangle(0, 0, W, H)
            self.particles.draw(0, 0)
        else:
            self.draw_hud(now)
            self.draw_banners(now)

        if self.state == Game.PAUSE:
            self.draw_veil()
            label("PAUSED", ICE).draw(W / 2, 44)
            screen.font = SMALL
            centre_text("SELECT resume", 66, DIM)
            centre_text("BACK title", 78, DIM)
        elif self.state == Game.ENTRY:
            self.draw_entry(now)
        elif self.demo:
            self.draw_demo_overlay(now)

    def draw_burst_fx(self, clock, ox, oy):
        age = clock - self.burst_at
        if age > 380:
            return
        x, y = self.pew.centre()
        t = age / 380
        screen.pen = color.rgb(255, 140, 215, int(230 * (1 - t)))
        inner = 8 + 50 * t
        outer = 20 + 120 * t
        for i in range(16):
            a = i * math.pi / 8 + t
            ca = math.cos(a)
            sa = math.sin(a)
            screen.line(int(x + ox + ca * inner), int(y + oy + sa * inner),
                        int(x + ox + ca * outer), int(y + oy + sa * outer))

    def draw_veil(self):
        screen.pen = VEIL
        screen.rectangle(0, 0, W, H)

    def draw_hud(self, now):
        screen.pen = BAR_BACK
        screen.rectangle(0, 0, W, 10)
        screen.font = SMALL
        score_text = "%05d" % int(self.shown_score)
        shadow_text(score_text, 2, 0)
        mult = self.multiplier()

        # One centre slot: the burst prompt blinks over the combo, which replaces HI.
        pew = self.pew
        if pew.charged() and not self.demo and (now // 250) % 2:
            centre_text("UP: BURST!", 0, PINK)
        elif mult > 1:
            centre_text("COMBO x%d" % mult, 0, GOLD if (now // 120) % 2 else PINK)
        elif self.demo:
            centre_text("DEMO", 0, DIM)
        elif not pew.charged():
            centre_text("HI %d" % max(best_score(), self.score), 0, DIM)

        for i in range(pew.lives):
            screen.blit(SPRITE, rect(W - 11 - i * 11, 1, 10, 9))

        fleet = self.fleet
        if isinstance(fleet, Boss) and self.phase == Game.FIGHT and fleet.hp > 0:
            screen.pen = BAR_BACK
            screen.rectangle(29, 11, 102, 5)
            screen.pen = color.rgb(255, 255, 255, 60)
            screen.shape(shape.rectangle(29, 11, 102, 5).stroke(1))
            fill = int(100 * fleet.hp / fleet.max_hp)
            flashing = fleet.t < fleet.flash_until
            screen.pen = WHITE if flashing else (RED if fleet.enraged() else BOSS_PEN)
            screen.rectangle(30, 12, fill, 3)
            screen.pen = color.rgb(255, 255, 255, 90)
            screen.rectangle(30, 12, fill, 1)

        # Octo-burst charge, with a shimmer running along it when full.
        screen.pen = BAR_BACK
        screen.rectangle(0, H - 3, W, 3)
        filled = int(W * pew.charge / CHARGE_FULL)
        screen.pen = PINK if pew.charged() else DIM
        screen.rectangle(0, H - 2, filled, 2)
        if pew.charged():
            screen.pen = WHITE
            screen.rectangle(int((now / 3) % (W + 20)) - 20, H - 2, 12, 2)

    def draw_banners(self, now):
        clock = self.clock
        if self.phase == Game.FIGHT and clock < self.banner_until:
            age = clock - (self.banner_until - BANNER_MS)
            label("WAVE %d" % self.wave, GOLDEN).draw(W / 2, 66, punch(age))
        elif self.phase == Game.WARNING:
            self.draw_warning(clock)
        elif self.phase == Game.CLEAR:
            age = clock - self.phase_at
            label(self.clear_text, ICE).draw(W / 2, 44, punch(age))
            if self.perfect and age > 350:
                label("PERFECT!", GOLDEN).draw(W / 2, 62, punch(age - 350), (now // 120) % 4 == 0)

        if self.callout:
            lbl, at, ms = self.callout
            age = clock - at
            if age > ms:
                self.callout = None
            elif self.phase == Game.FIGHT and clock >= self.banner_until:
                lbl.draw(W / 2, 36, punch(age, 180), age < 60)

    def draw_warning(self, clock):
        age = clock - self.phase_at
        on = (age // 200) % 3 != 2
        # Hazard stripes sliding across the top and bottom of the screen.
        screen.pen = color.rgb(200, 20, 30, 170 if on else 90)
        screen.rectangle(0, 30, W, 8)
        screen.rectangle(0, 68, W, 8)
        screen.pen = color.rgb(0, 0, 0, 160)
        shift = int(age / 25) % 12
        for x in range(-12, W + 12, 12):
            screen.triangle(vec2(x + shift, 30), vec2(x + shift + 6, 30), vec2(x + shift - 2, 38))
            screen.triangle(vec2(x - shift + 12, 68), vec2(x - shift + 18, 68), vec2(x - shift + 10, 76))
        if on:
            label("WARNING", CRIMSON).draw(W / 2, 53, punch(age % 400, 120) if age < 400 else 1.0)
        screen.font = SMALL
        name = self.fleet.name
        typed = name[:int(max(0, age - 600) / 60)]
        if typed:
            width, _ = screen.measure_text(name)
            shadow_text(typed, (W - width) / 2, 80, PINK if typed == name or (age // 80) % 2 else WHITE)

    def draw_demo_overlay(self, now):
        if (now // 600) % 2:
            screen.pen = BAR_BACK
            screen.rectangle(0, 68, W, 12)
            screen.font = SMALL
            centre_text("PRESS SELECT TO PLAY", 68, GOLD)

    def draw_title(self, now):
        t = now - self.title_at
        cx, cy = 35, 40

        # A trio of aliens orbiting the logo; the ones behind are drawn first.
        orbit = []
        for i in range(3):
            a = now / 900 + i * 2.094
            orbit.append((math.sin(a), cx + math.cos(a) * 30 - ALIEN_W / 2, cy + math.sin(a) * 8 + 22, i))
        appear = min(1.0, t / 900)
        for depth, x, y, row in orbit:
            if depth < 0 and t > 300:
                screen.blit(SHEET.sprite((now // 200) % 2, row), vec2(int(x), int(y)))

        size = 64 * ease_out_back(t / 500)
        if size > 1:
            bob = math.sin(now / 400) * 2
            screen.blit(LOGO, rect(int(cx - size / 2), int(cy - size / 2 + bob), int(size), int(size)))

        for depth, x, y, row in orbit:
            if depth >= 0 and t > 300:
                screen.blit(SHEET.sprite((now // 200) % 2, row), vec2(int(x), int(y)))

        self.draw_comet(now)

        # "PEW / PEW!" at double size; the letters drop in one by one.
        landed = True
        lines = (("PEW", 22), ("PEW!", 52))
        index = 0
        for word, y in lines:
            lbl = label(word, GOLDEN)
            drop = bounce((t - 250 - index * 110) / 420)
            landed = landed and drop >= 1
            if drop > 0:
                ty = y - (1 - drop) * 90
                lbl.draw(114, ty, 2)
                # Shine sweep every few seconds once everything is in place.
                sweep = (t - 1800) % 3200
                if t > 1800 and sweep < 700:
                    bx = int(60 + sweep / 700 * 110)
                    screen.clip = rect(bx, 0, 7, H)
                    screen.alpha = 170
                    lbl.draw(114, ty, 2, True)
                    screen.alpha = 255
                    screen.clip = rect(0, 0, W, H)
            index += 1
        if landed and not self.title_landed:
            self.title_landed = True
            self.flash.kick(0.5)
            self.shake.kick(2)
            self.glow.flash(1.0)
            for i in range(12):
                self.particles.burst(random.uniform(70, 158), 66, GOLD, 1, 50)

        self.particles.draw(0, 0)
        if t < 1100:
            return
        screen.font = SMALL
        pulse = 0.5 + 0.5 * math.sin(now / 160)
        centre_text("PRESS SELECT", 77, color.rgb(255, int(200 + 55 * pulse), int(90 + 140 * pulse)))
        top = saved["board"][0] if saved["board"] else ["---", 0]
        if top[1] >= best_score():
            centre_text("HI %d  %s" % (best_score(), top[0]), 88, DIM)
        else:
            centre_text("HI %d" % best_score(), 88, DIM)
        centre_text("DOWN: TILT %s" % ("ON" if saved["tilt"] else "OFF"), 99, DIM)

    def draw_comet(self, now):
        if self.comet is None or now > self.comet[4]:
            if random.random() < 0.01:
                x = random.uniform(40, W + 20)
                self.comet = (x, -4.0, -random.uniform(70, 110), random.uniform(50, 80), now + 1500, now)
            return
        x0, y0, vx, vy, _end, born = self.comet
        age = (now - born) / 1000
        x = x0 + vx * age
        y = y0 + vy * age
        for i in range(6):
            k = i * 0.015
            screen.pen = color.rgb(255, 255, 255, 200 - i * 33)
            screen.rectangle(int(x - vx * k), int(y - vy * k), 1 if i else 2, 1 if i else 2)

    def draw_scores(self, now):
        t = now - self.state_at
        label("HALL OF FAME", GOLDEN).draw(W / 2, 14, punch(t))
        screen.pen = PANEL
        screen.rectangle(8, 27, W - 16, 15 * len(saved["board"]) + 2)
        screen.font = SMALL
        for i, (name, value) in enumerate(saved["board"]):
            slide = ease_out_back((t - 200 - i * 90) / 350)
            if slide <= 0:
                continue
            y = 30 + i * 15
            x = int(W * (1 - slide))
            pen = MEDALS[i] if i < 3 else DIM
            if i == self.highlight:
                screen.pen = color.rgb(255, 140, 215, 110 + int(60 * math.sin(now / 120)))
                screen.rectangle(x + 9, y - 1, W - 18, 13)
                pen = GOLD if (now // 200) % 2 else WHITE
                screen.pen = pen
                screen.triangle(vec2(x + 4, y + 2), vec2(x + 4, y + 8), vec2(x + 8, y + 5))
            shadow_text("%d" % (i + 1), x + 16, y, pen)
            shadow_text(name, x + 36, y, pen)
            score = "%d" % value
            width, _ = screen.measure_text(score)
            shadow_text(score, x + W - 16 - width, y, pen)
        if t > 1200 and (now // 500) % 2:
            centre_text("PRESS SELECT", 105, GOLD)

    def draw_ad(self, now):
        t = now - self.state_at

        # Infomercial sunburst behind the forklift.
        screen.pen = AD_YELLOW
        screen.rectangle(0, 0, W, H)
        screen.pen = AD_RAY
        cx, cy = 35, 64
        spin = now / 1500
        for i in range(12):
            a = spin + i * math.pi / 6
            screen.triangle(vec2(cx, cy), vec2(cx + math.cos(a) * 220, cy + math.sin(a) * 220),
                            vec2(cx + math.cos(a + 0.26) * 220, cy + math.sin(a + 0.26) * 220))

        rumble = int(math.sin(t / 40)) if t < AD_DRIVE_MS else 0
        screen.blit(FORKLIFT, vec2(int(ad_forklift_x(t)), 36 + rumble))
        self.particles.draw(0, 0)

        right = 112
        screen.font = SMALL
        if t > 200:
            ink_text("GET YOURSELF", right, 18)
        if t > 400:
            label("FORKLIFT", CRIMSON).draw(right, 38, punch(t - 400))
        if t > 650:
            label("CERTIFIED!", CRIMSON).draw(right, 56, punch(t - 650), (now // 150) % 6 == 0)
        if t > 1000:
            screen.font = SMALL
            ink_text("SPONSORED BY", right, 70)
            pew = label("PEW", ROSE)
            left = right - (17 + pew.width) / 2
            screen.blit(SPRITE, rect(int(left), 80, 14, 12))
            pew.draw(left + 17 + pew.width / 2, 86)

        shift = int(now / 40) % 12
        hazard(11, shift)
        hazard(100, -shift)

        # Top bar: AD tag, GAME OVER, final score. Bottom bar: the bad news, countdown, progress.
        screen.pen = BLACK
        screen.rectangle(0, 0, W, 11)
        screen.rectangle(0, 106, W, 14)
        screen.pen = AD_YELLOW
        screen.shape(shape.rounded_rectangle(1, 0, 17, 11, 2))
        screen.font = SMALL
        screen.pen = BLACK
        screen.text("AD", 4, -1)
        centre_text("GAME OVER", -1, WHITE)
        score = "%d" % self.score
        width, _ = screen.measure_text(score)
        shadow_text(score, W - 2 - width, -1, GOLD)
        shadow_text("CAN'T SKIP THIS AD", 2, 106, DIM)
        left_ms = max(0, AD_MS - t)
        countdown = "0:%02d" % ((left_ms + 999) // 1000)
        width, _ = screen.measure_text(countdown)
        shadow_text(countdown, W - 2 - width, 106, WHITE)
        screen.pen = AD_YELLOW
        screen.rectangle(0, H - 2, int(W * min(1.0, t / AD_MS)), 2)

    def draw_entry(self, now):
        label("NEW HIGH SCORE!" if self.new_best else "TOP %d!" % BOARD_SIZE, GOLDEN).draw(W / 2, 16)
        screen.font = SMALL
        centre_text("RANK %d    %d" % (self.rank + 1, self.score), 29, WHITE)
        for i, ch in enumerate(self.entry_name):
            x = 44 + i * 26
            active = i == self.entry_pos
            pen = GOLD if active else WHITE
            if active:
                screen.pen = color.rgb(255, 228, 90, 70)
                screen.rectangle(x - 4, 48, 24, 28)
                screen.pen = GOLD
                screen.shape(shape.rectangle(x - 4, 48, 24, 28).stroke(1))
                bob = int(math.sin(now / 120))
                screen.pen = GOLD
                screen.triangle(vec2(x + 8, 42 + bob), vec2(x + 4, 46 + bob), vec2(x + 12, 46 + bob))
                screen.triangle(vec2(x + 8, 82 - bob), vec2(x + 4, 78 - bob), vec2(x + 12, 78 - bob))
            shadow_text(ch, x, 46, pen, 2)
            screen.pen = pen
            screen.rectangle(x - 1, 73, 18, 1)
        centre_text("UP/DOWN: LETTER", 90, DIM)
        centre_text("SELECT: NEXT", 101, DIM)


game = Game()


def update():
    dt_ms = min(badge.ticks_delta, MAX_FRAME_MS)
    game.update(dt_ms)
    game.draw()


def on_exit():
    game.glow.off()


run(update)
