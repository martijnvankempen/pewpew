import math
import random

W = screen.width
H = screen.height

STAR_SHAPE = shape.star(0, 0, 5, 0.5, 1)

FAR = color.rgb(55, 65, 95)
MID = color.rgb(115, 125, 165)
NEAR = color.rgb(225, 225, 255)

MAX_PARTICLES = 64
MAX_RINGS = 8
MAX_POPUPS = 6

NEBULA = image.load("assets/nebula.png")
PLANET = image.load("assets/planet.png")
# Per-wave colour wash over the nebula, (r, g, b, alpha); the last one is for boss waves.
TINTS = ((0, 0, 0, 0), (60, 0, 90, 40), (0, 70, 90, 40), (90, 30, 0, 36), (0, 40, 120, 40))
BOSS_TINT = (140, 0, 30, 55)


def draw_star(x, y, radius, angle, pen):
    screen.pen = pen
    STAR_SHAPE.transform = mat3().translate(x, y).rotate(angle).scale(radius)
    screen.shape(STAR_SHAPE)


class Starfield:
    """Three layers of stars over a slowly scrolling nebula and a drifting planet.

    `warp` (0..1) stretches the stars into hyperspace streaks between waves.
    """

    def __init__(self, count=40):
        self.dots = []
        for i in range(count):
            speed = (6, 12, 22)[i % 3]
            self.dots.append([random.uniform(0, W), random.uniform(0, H), speed])
        self.scroll = 0.0
        self.planet_x = W - 40.0
        self.planet_y = 18.0
        self.warp = 0.0
        self.warp_target = 0.0
        self.tint = TINTS[0]

    def set_wave(self, wave, boss):
        self.tint = BOSS_TINT if boss else TINTS[(wave - 1) % len(TINTS)]

    def update(self, dt):
        self.warp += (self.warp_target - self.warp) * min(1.0, dt * 4)
        boost = 1 + self.warp * 14
        for dot in self.dots:
            dot[1] += dot[2] * dt * boost
            if dot[1] >= H:
                dot[1] -= H
                dot[0] = random.uniform(0, W)
        self.scroll = (self.scroll + dt * (2 + self.warp * 30)) % H
        self.planet_y += dt * (1.2 + self.warp * 40)
        if self.planet_y > H + 30:
            self.planet_y = -40.0
            self.planet_x = random.uniform(10, W - 36)

    def draw(self):
        top = int(self.scroll)
        screen.blit(NEBULA, vec2(0, top))
        screen.blit(NEBULA, vec2(0, top - H))
        if self.tint[3]:
            screen.pen = color.rgb(*self.tint)
            screen.rectangle(0, 0, W, H)
        screen.alpha = 150
        screen.blit(PLANET, vec2(int(self.planet_x), int(self.planet_y)))
        screen.alpha = 255

        streak = self.warp * 18
        for x, y, speed in self.dots:
            screen.pen = FAR if speed < 10 else MID if speed < 20 else NEAR
            if streak > 1:
                length = int(1 + streak * speed / 22)
                screen.rectangle(int(x), int(y) - length, 1, length + 1)
            else:
                screen.rectangle(int(x), int(y), 1, 1)


class Particles:
    def __init__(self):
        self.items = []

    def burst(self, x, y, pen, count=8, speed=55):
        for i in range(count):
            angle = random.uniform(0, math.pi * 2)
            v = random.uniform(0.35, 1.0) * speed
            # [x, y, vx, vy, life_ms, pen, is_star]
            self.items.append([x, y, math.cos(angle) * v, math.sin(angle) * v,
                               random.randint(250, 550), pen, i < 2])
        if len(self.items) > MAX_PARTICLES:
            del self.items[:len(self.items) - MAX_PARTICLES]

    def clear(self):
        self.items = []

    def update(self, dt_ms):
        dt = dt_ms / 1000
        alive = []
        for p in self.items:
            p[0] += p[2] * dt
            p[1] += p[3] * dt
            p[4] -= dt_ms
            if p[4] > 0:
                alive.append(p)
        self.items = alive

    def draw(self, ox, oy):
        for x, y, _vx, _vy, life, pen, is_star in self.items:
            if is_star:
                draw_star(x + ox, y + oy, 2, life, pen)
                continue
            screen.pen = pen
            size = 2 if life > 220 else 1
            screen.rectangle(int(x + ox), int(y + oy), size, size)


class Rings:
    """Expanding shockwave rings that fade as they grow."""

    def __init__(self):
        self.items = []

    def add(self, x, y, rgb, size=14, ms=320):
        # [x, y, (r, g, b), max radius, life_ms, total_ms]
        self.items.append([x, y, rgb, size, ms, ms])
        if len(self.items) > MAX_RINGS:
            del self.items[0]

    def clear(self):
        self.items = []

    def update(self, dt_ms):
        for ring in self.items:
            ring[4] -= dt_ms
        self.items = [ring for ring in self.items if ring[4] > 0]

    def draw(self, ox, oy):
        for x, y, rgb, size, life, total in self.items:
            t = 1 - life / total
            radius = 2 + (size - 2) * (1 - (1 - t) * (1 - t))
            screen.pen = color.rgb(rgb[0], rgb[1], rgb[2], int(255 * (1 - t)))
            screen.shape(shape.circle(x + ox, y + oy, radius).stroke(2 if t < 0.5 else 1))


class Popups:
    """Floating score numbers and short callouts that rise and fade."""

    def __init__(self):
        self.items = []

    def add(self, x, y, text, rgb, ms=700):
        # [x, y, text, (r, g, b), life_ms, total_ms]
        self.items.append([x, y, text, rgb, ms, ms])
        if len(self.items) > MAX_POPUPS:
            del self.items[0]

    def clear(self):
        self.items = []

    def update(self, dt_ms):
        dt = dt_ms / 1000
        for p in self.items:
            p[1] -= 14 * dt
            p[4] -= dt_ms
        self.items = [p for p in self.items if p[4] > 0]

    def draw(self, ox, oy):
        screen.font = font.nope
        for x, y, text, rgb, life, total in self.items:
            alpha = 255 if life > total / 2 else int(510 * life / total)
            width, _ = screen.measure_text(text)
            tx = max(1, min(W - width - 1, x - width / 2)) + ox
            screen.pen = color.rgb(0, 0, 0, alpha * 2 // 3)
            screen.text(text, tx + 1, y + oy + 1)
            screen.pen = color.rgb(rgb[0], rgb[1], rgb[2], alpha)
            screen.text(text, tx, y + oy)


class Flash:
    """A full-screen colour flash that fades out."""

    def __init__(self):
        self.rgb = (255, 255, 255)
        self.level = 0.0

    def kick(self, level, rgb=(255, 255, 255)):
        if level >= self.level:
            self.rgb = rgb
            self.level = level

    def update(self, dt_ms):
        self.level *= 0.8 ** (dt_ms / 16.6)
        if self.level < 0.02:
            self.level = 0.0

    def draw(self):
        if self.level:
            screen.pen = color.rgb(self.rgb[0], self.rgb[1], self.rgb[2], int(220 * min(1.0, self.level)))
            screen.rectangle(0, 0, W, H)


class Shake:
    def __init__(self):
        self.amount = 0.0

    def kick(self, amount):
        self.amount = min(6.0, self.amount + amount)

    def update(self, dt_ms):
        self.amount *= 0.85 ** (dt_ms / 16.6)

    def offset(self):
        if self.amount < 0.5:
            return 0, 0
        a = self.amount
        return int(random.uniform(-a, a)), int(random.uniform(-a, a))


class Glow:
    """Case LED feedback: flashes that fade, a short chase, a red alarm pulse and an idle breath."""

    def __init__(self):
        self.level = 0.0
        self.chase_until = 0
        self.alarm_until = 0
        self.breathe = False
        self.sent = None

    def alarm(self, now, ms):
        self.alarm_until = now + ms

    def flash(self, level):
        self.level = max(self.level, level)

    def chase(self, now, ms=700):
        self.chase_until = now + ms

    def update(self, now, dt_ms):
        self.level *= 0.9 ** (dt_ms / 16.6)
        if now < self.chase_until:
            step = (now // 70) % 4
            lights = tuple(1.0 if i == step else 0.15 for i in range(4))
        elif now < self.alarm_until:
            lights = (1.0 if (now // 150) % 2 else 0.1,)
        else:
            level = self.level
            if self.breathe:
                level = max(level, 0.08 + 0.3 * (0.5 + 0.5 * math.sin(now / 700)))
            lights = (round(min(1.0, level) * 20) / 20,)
        if lights != self.sent:
            badge.caselights(*lights)
            self.sent = lights

    def off(self):
        badge.caselights(0)
        self.sent = None
