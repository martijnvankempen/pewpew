import math
import random

from aliens import Fleet, ZAP_SPEED

W = screen.width
H = screen.height

SHEET = image.load("assets/boss.png").spritesheet(3, 1)
BOSS_W = 40
BOSS_H = 28
HOME_Y = 19
CORE = (20, 17)
HITBOX = (3, 1, 34, 22)

RGB = (150, 80, 255)
NAMES = ("MERGE CONFLICT", "THE 404 HYDRA", "LEGACY MONOLITH", "INFINITE LOOP")

ENTER_SPEED = 22
TELEGRAPH = 0.75
BEAM_TIME = 0.5
BEAM_W = 8
DEATH_S = 1.8

BEAM_WARN = color.rgb(255, 60, 60, 150)
BEAM_GLOW = color.rgb(255, 60, 160, 90)
BEAM_EDGE = color.rgb(255, 90, 200, 220)
BEAM_CORE = color.rgb(255, 240, 250)


class Boss(Fleet):
    """A mothership that soaks up hits and cycles through spread, aimed and beam attacks.

    It shares the zap list, zap drawing and zap hit tests with the alien fleet.
    """

    def __init__(self, wave, now):
        self.wave = wave
        self.stage = wave // 3
        self.name = NAMES[(self.stage - 1) % len(NAMES)]
        self.hp = self.max_hp = 30 + 12 * self.stage
        self.count = 1
        self.x = (W - BOSS_W) / 2
        self.y = -BOSS_H - 4.0
        self.t = 0.0
        self.entry = 1.0
        self.zaps = []
        self.divers = []
        self.flash_until = 0.0
        self.attack = None
        self.attack_t = 0.0
        self.next_attack = 1.2
        self.volley = []
        self.dying = 0.0
        self.beam_x = 0.0

    # ---- state ---------------------------------------------------------------

    def settle(self, dt):
        pass

    def entering(self):
        return self.y < HOME_Y

    def enraged(self):
        return self.hp * 2 <= self.max_hp

    def core(self):
        return self.x + CORE[0], self.y + CORE[1]

    def bottom(self):
        return 0

    def beam_live(self):
        return self.attack == "beam" and self.attack_t >= TELEGRAPH

    # ---- per-frame -----------------------------------------------------------

    def update(self, now, dt, target_x):
        self.t += dt
        if self.dying:
            self.dying = max(0.0, self.dying - dt)
            self.x += random.uniform(-1, 1)
            self.y += 6 * dt
            if not self.dying:
                self.count = 0
            return

        if self.entering():
            self.y = min(HOME_Y, self.y + ENTER_SPEED * dt)
        elif self.attack != "beam":
            # Glide side to side; a little faster once it is angry.
            swing = (W - BOSS_W) / 2 - 4
            pace = 0.9 if self.enraged() else 0.6
            goal = (W - BOSS_W) / 2 + math.sin(self.t * pace) * swing
            self.x += (goal - self.x) * min(1.0, dt * 2.5)
            self.y = HOME_Y + math.sin(self.t * 1.7) * 3

        self.run_attack(dt, target_x)

        for z in self.zaps:
            z[0] += z[2] * dt
            z[1] += z[3] * dt
        self.zaps = [z for z in self.zaps if z[1] < H and -4 < z[0] < W]

    def run_attack(self, dt, target_x):
        if self.entering():
            return
        cx, cy = self.core()
        if self.attack is None:
            self.next_attack -= dt
            if self.next_attack <= 0:
                options = ("fan", "aimed", "beam")
                self.attack = options[random.randrange(len(options))]
                self.attack_t = 0.0
                if self.attack == "aimed":
                    self.volley = [0.0, 0.18, 0.36] + ([0.54, 0.72] if self.enraged() else [])
                elif self.attack == "beam":
                    self.beam_x = cx
            return

        self.attack_t += dt
        if self.attack == "fan":
            shots = 7 if self.enraged() else 5
            spread = 0.9
            for i in range(shots):
                angle = -spread / 2 + spread * i / (shots - 1)
                speed = ZAP_SPEED * 1.1
                self.zaps.append([cx - 1.5, cy, math.sin(angle) * speed, math.cos(angle) * speed])
            self.finish()
        elif self.attack == "aimed":
            while self.volley and self.attack_t >= self.volley[0]:
                self.volley.pop(0)
                self.shoot(cx, cy, target_x, True)
            if not self.volley:
                self.finish()
        elif self.attack == "beam":
            self.beam_x = cx
            if self.attack_t >= TELEGRAPH + BEAM_TIME:
                self.finish()

    def finish(self):
        self.attack = None
        gap = 1.0 if self.enraged() else 1.5
        self.next_attack = gap * random.uniform(0.8, 1.2) - min(0.4, 0.1 * (self.stage - 1))

    # ---- collisions ----------------------------------------------------------

    def hit(self, x, y, radius):
        """One point of damage per star; returns (x, y, killed) or None."""
        if self.dying or self.y < -BOSS_H / 2:
            return None
        bx, by, bw, bh = HITBOX
        left = self.x + bx
        top = self.y + by
        if left - radius <= x <= left + bw + radius and top - radius <= y <= top + bh + radius:
            self.hp -= 1
            self.flash_until = self.t + 0.06
            if self.hp <= 0:
                self.hp = 0
                self.dying = DEATH_S
                self.attack = None
                self.zaps = []
                return x, y, True
            return x, y, False
        return None

    def ram(self, box):
        return None

    def beam_hits(self, box):
        if not self.beam_live():
            return False
        bx, _by, bw, _bh = box
        return bx <= self.beam_x + BEAM_W / 2 and self.beam_x - BEAM_W / 2 <= bx + bw

    # ---- drawing -------------------------------------------------------------

    def draw(self, now, ox, oy):
        x = int(self.x + ox)
        y = int(self.y + oy)
        if self.attack == "beam" and not self.dying:
            self.draw_beam(now, ox, oy)

        if self.t < self.flash_until or (self.dying and (now // 60) % 2):
            frame = 2
        else:
            frame = (now // 200) % 2
        screen.blit(SHEET.sprite(frame, 0), vec2(x, y))
        self.draw_zaps(now, ox, oy)

    def draw_beam(self, now, ox, oy):
        cx = self.beam_x + ox
        top = self.y + CORE[1] + oy
        if self.attack_t < TELEGRAPH:
            # Thin flickering warning line, getting more urgent.
            if (now // (110 if self.attack_t < TELEGRAPH / 2 else 50)) % 2:
                screen.pen = BEAM_WARN
                screen.rectangle(int(cx), int(top), 1, H)
            screen.pen = BEAM_CORE
            screen.circle(vec2(cx, top), 1 + self.attack_t * 4)
            return
        wobble = (now // 40) % 2
        half = BEAM_W // 2 + wobble
        screen.pen = BEAM_GLOW
        screen.rectangle(int(cx - half - 3), int(top), half * 2 + 6, H)
        screen.pen = BEAM_EDGE
        screen.rectangle(int(cx - half), int(top), half * 2, H)
        screen.pen = BEAM_CORE
        screen.rectangle(int(cx - 1 - wobble), int(top), 2 + wobble * 2, H)
        screen.circle(vec2(cx, top), 4 + wobble)
