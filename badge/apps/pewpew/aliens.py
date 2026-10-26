import math
import random

W = screen.width
H = screen.height

SHEET = image.load("assets/aliens.png").spritesheet(3, 3)
FLASH_FRAME = 2
ALIEN_W = 11
ALIEN_H = 8
COLS = 5
ROWS = 3
STEP_X = 20
STEP_Y = 13
FLEET_W = (COLS - 1) * STEP_X + ALIEN_W
TOP = 16
MARGIN = 2
BOB = 2.5

POINTS = (30, 20, 10)
RGBS = ((255, 92, 205), (80, 220, 255), (160, 255, 90))
PENS = tuple(color.rgb(*rgb) for rgb in RGBS)
ZAP_PEN = color.rgb(255, 120, 60)
ZAP_CORE = color.rgb(255, 235, 150)

BASE_SPEED = 10
DROP = 4
ZAP_SPEED = 45
ZAP_W = 3
ZAP_H = 7
AIMED_CHANCE = 0.3

WINDUP = 0.35
DIVE_SPEED = 30
DIVE_ACCEL = 50
RETURN_SPEED = 40
ENTRY_S = 1.2

EMPTY = 0
HOME = 1
DIVING = 2


class Diver:
    """An alien that has left its slot to swoop at Pew, then flies back in from the top."""

    def __init__(self, r, c, x, y, target_x):
        self.r = r
        self.c = c
        self.x = self.x0 = x
        self.y = self.y0 = y
        self.target_x = target_x - ALIEN_W / 2 + random.uniform(-15, 15)
        self.vy = DIVE_SPEED
        self.swing = random.uniform(12, 28) * (1 if random.random() < 0.5 else -1)
        self.loops = random.uniform(1.0, 2.5)
        self.wait = WINDUP
        self.returning = False
        self.fired = False


class Fleet:
    def __init__(self, wave, now):
        self.wave = wave
        self.slots = [[HOME] * COLS for _ in range(ROWS)]
        self.count = ROWS * COLS
        self.x = (W - FLEET_W) / 2
        self.y = TOP + min(wave - 1, 4) * 3
        self.dir = 1
        self.travel = 0.0
        self.t = 0.0
        self.pace = 1.0
        self.pace_target = 1.0
        self.next_pace = now + 1500
        self.zaps = []
        self.divers = []
        self.next_zap = now + 1200
        self.next_dive = now + 1500 + self.dive_gap()
        self.entry = 0.0

    def settle(self, dt):
        """Advance the fly-in and the idle bob; runs even while the fleet holds still."""
        if self.entry < ENTRY_S:
            self.entry = min(ENTRY_S, self.entry + dt)
            self.t += dt

    def speed(self):
        killed = 1 - self.count / (ROWS * COLS)
        return BASE_SPEED * self.pace * (1 + 0.15 * (self.wave - 1)) * (1 + 2.5 * killed)

    def dive_gap(self):
        return random.randint(1800, 4200) - min(1200, 200 * (self.wave - 1))

    def slot_pos(self, r, c):
        bob = math.sin(self.t * 3 + c * 0.9 + r * 1.7) * BOB
        x = self.x + c * STEP_X
        y = self.y + r * STEP_Y + bob
        if self.entry < ENTRY_S:
            # Fly in from above on a curve, the back row first, one column after another.
            k = max(0.0, min(1.0, self.entry / ENTRY_S * 1.9 - (ROWS - 1 - r) * 0.2 - c * 0.1))
            left = 1 - k
            ease = left * left * left
            x += math.sin(left * 4) * 50 * (1 if c % 2 else -1) * left
            y -= ease * 120
        return x, y

    def occupied_columns(self):
        return [c for c in range(COLS) if any(self.slots[r][c] for r in range(ROWS))]

    def bottom(self):
        for r in range(ROWS - 1, -1, -1):
            if any(self.slots[r]):
                return self.y + r * STEP_Y + ALIEN_H
        return 0

    def update(self, now, dt, target_x):
        self.t += dt

        # Random changes of pace, and the odd feint the other way.
        if now >= self.next_pace:
            self.pace_target = random.uniform(0.6, 1.5)
            if random.random() < 0.25:
                self.dir = -self.dir
            self.next_pace = now + random.randint(800, 2000)
        self.pace += (self.pace_target - self.pace) * min(1.0, dt * 3)

        step = self.speed() * dt
        self.x += self.dir * step
        self.travel += step

        cols = self.occupied_columns()
        left = self.x + cols[0] * STEP_X
        right = self.x + cols[-1] * STEP_X + ALIEN_W
        if self.dir > 0 and right >= W - MARGIN:
            self.x -= right - (W - MARGIN)
            self.dir = -1
            self.y += DROP
        elif self.dir < 0 and left <= MARGIN:
            self.x += MARGIN - left
            self.dir = 1
            self.y += DROP

        if now >= self.next_zap:
            if len(self.zaps) < min(1 + self.wave, 4):
                self.fire_from_formation(target_x)
            self.next_zap = now + random.randint(600, 1400) - min(400, 60 * (self.wave - 1))

        if now >= self.next_dive:
            if len(self.divers) < min(1 + self.wave // 2, 3):
                self.launch(target_x)
            self.next_dive = now + self.dive_gap()

        self.update_divers(dt, target_x)

        for z in self.zaps:
            z[0] += z[2] * dt
            z[1] += z[3] * dt
        self.zaps = [z for z in self.zaps if z[1] < H and -ZAP_W < z[0] < W]

    def shoot(self, x, y, target_x, aimed):
        speed = ZAP_SPEED * random.uniform(0.9, 1.3)
        vx = 0.0
        if aimed:
            flight = max(0.3, (H - 16 - y) / speed)
            vx = max(-35.0, min(35.0, (target_x - x) / flight))
        self.zaps.append([x - ZAP_W / 2, y, vx, speed])

    def fire_from_formation(self, target_x):
        cols = [c for c in range(COLS) if any(self.slots[r][c] == HOME for r in range(ROWS))]
        if not cols:
            return
        c = cols[random.randrange(len(cols))]
        for r in range(ROWS - 1, -1, -1):
            if self.slots[r][c] == HOME:
                x, y = self.slot_pos(r, c)
                self.shoot(x + ALIEN_W / 2, y + ALIEN_H, target_x, random.random() < AIMED_CHANCE)
                return

    def launch(self, target_x):
        homes = [(r, c) for r in range(ROWS) for c in range(COLS) if self.slots[r][c] == HOME]
        if not homes:
            return
        r, c = homes[random.randrange(len(homes))]
        x, y = self.slot_pos(r, c)
        self.slots[r][c] = DIVING
        self.divers.append(Diver(r, c, x, y, target_x))

    def update_divers(self, dt, target_x):
        for d in self.divers[:]:
            if d.wait > 0:
                # Wind-up: shiver in the slot so the player gets a moment of warning.
                d.wait -= dt
                d.x0, d.y0 = self.slot_pos(d.r, d.c)
                d.x = d.x0 + random.uniform(-1, 1)
                d.y = d.y0
            elif not d.returning:
                d.vy += DIVE_ACCEL * dt
                d.y += d.vy * dt
                p = max(0.0, (d.y - d.y0) / (H - d.y0))
                d.x = d.x0 + (d.target_x - d.x0) * min(1.0, p * 1.4) + math.sin(p * math.pi * d.loops) * d.swing
                d.x = max(0.0, min(W - ALIEN_W, d.x))
                if not d.fired and p > 0.3:
                    d.fired = True
                    if random.random() < 0.7 and len(self.zaps) < 5:
                        self.shoot(d.x + ALIEN_W / 2, d.y + ALIEN_H, target_x, True)
                if d.y > H + 4:
                    d.returning = True
                    d.y = -ALIEN_H - 2
            else:
                sx, sy = self.slot_pos(d.r, d.c)
                d.y += RETURN_SPEED * dt
                d.x += (sx - d.x) * min(1.0, dt * 3)
                if d.y >= sy:
                    self.slots[d.r][d.c] = HOME
                    self.divers.remove(d)

    def kill_diver(self, d):
        self.divers.remove(d)
        self.slots[d.r][d.c] = EMPTY
        self.count -= 1

    def hit(self, x, y, radius):
        """Kill the alien under a star at (x, y); returns (row, ax, ay, was_diving) or None."""
        for r in range(ROWS):
            for c in range(COLS):
                if self.slots[r][c] != HOME:
                    continue
                ax, ay = self.slot_pos(r, c)
                if ax - radius <= x <= ax + ALIEN_W + radius and ay - radius <= y <= ay + ALIEN_H + radius:
                    self.slots[r][c] = EMPTY
                    self.count -= 1
                    return r, ax, ay, False
        for d in self.divers:
            if d.x - radius <= x <= d.x + ALIEN_W + radius and d.y - radius <= y <= d.y + ALIEN_H + radius:
                self.kill_diver(d)
                return d.r, d.x, d.y, True
        return None

    def ram(self, box):
        """A diver that flies into Pew dies too; returns (row, x, y) or None."""
        bx, by, bw, bh = box
        for d in self.divers:
            if bx <= d.x + ALIEN_W and d.x <= bx + bw and by <= d.y + ALIEN_H and d.y <= by + bh:
                self.kill_diver(d)
                return d.r, d.x, d.y
        return None

    def block(self, x, y, radius):
        """Stars cancel zaps they touch."""
        for z in self.zaps:
            if abs(z[0] + ZAP_W / 2 - x) <= radius + 1 and z[1] - radius <= y <= z[1] + ZAP_H + radius:
                self.zaps.remove(z)
                return True
        return False

    def zap_hits(self, box):
        bx, by, bw, bh = box
        for z in self.zaps:
            if bx <= z[0] + ZAP_W and z[0] <= bx + bw and by <= z[1] + ZAP_H and z[1] <= by + bh:
                self.zaps.remove(z)
                return True
        return False

    def draw(self, now, ox, oy):
        frame = int(self.travel / 4 + self.entry * 6) % 2
        for r in range(ROWS):
            sprite = SHEET.sprite(frame, r)
            for c in range(COLS):
                if self.slots[r][c] == HOME:
                    ax, ay = self.slot_pos(r, c)
                    screen.blit(sprite, vec2(int(ax + ox), int(ay + oy)))

        flap = (now // 120) % 2
        for d in self.divers:
            screen.blit(SHEET.sprite(flap, d.r), vec2(int(d.x + ox), int(d.y + oy)))

        self.draw_zaps(now, ox, oy)

    def draw_zaps(self, now, ox, oy):
        wiggle = (now // 90) % 2
        for z in self.zaps:
            x = int(z[0] + ox)
            y = int(z[1] + oy)
            screen.pen = ZAP_PEN
            screen.rectangle(x + wiggle, y, 2, 3)
            screen.rectangle(x + 1 - wiggle, y + 3, 2, 2)
            screen.rectangle(x + wiggle, y + 5, 2, 2)
            screen.pen = ZAP_CORE
            screen.rectangle(x + wiggle, y + 6, 2, 1)


def draw_flash(row, x, y):
    screen.blit(SHEET.sprite(FLASH_FRAME, row), vec2(int(x), int(y)))
