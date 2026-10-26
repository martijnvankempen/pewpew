import math
import random

W = screen.width
H = screen.height

STAR_SHAPE = shape.star(0, 0, 5, 0.5, 1)

FAR = color.rgb(55, 65, 95)
MID = color.rgb(115, 125, 165)
NEAR = color.rgb(225, 225, 255)

MAX_PARTICLES = 48


def draw_star(x, y, radius, angle, pen):
    screen.pen = pen
    STAR_SHAPE.transform = mat3().translate(x, y).rotate(angle).scale(radius)
    screen.shape(STAR_SHAPE)


class Starfield:
    def __init__(self, count=40):
        self.dots = []
        for i in range(count):
            speed = (6, 12, 22)[i % 3]
            self.dots.append([random.uniform(0, W), random.uniform(0, H), speed])

    def update(self, dt):
        for dot in self.dots:
            dot[1] += dot[2] * dt
            if dot[1] >= H:
                dot[1] -= H
                dot[0] = random.uniform(0, W)

    def draw(self):
        for x, y, speed in self.dots:
            screen.pen = FAR if speed < 10 else MID if speed < 20 else NEAR
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
    """Case LED feedback: flashes that fade, plus a short chase for the Octo-burst."""

    def __init__(self):
        self.level = 0.0
        self.chase_until = 0
        self.sent = None

    def flash(self, level):
        self.level = max(self.level, level)

    def chase(self, now, ms=700):
        self.chase_until = now + ms

    def update(self, now, dt_ms):
        self.level *= 0.9 ** (dt_ms / 16.6)
        if now < self.chase_until:
            step = (now // 70) % 4
            lights = tuple(1.0 if i == step else 0.15 for i in range(4))
        else:
            lights = (round(min(1.0, self.level) * 20) / 20,)
        if lights != self.sent:
            badge.caselights(*lights)
            self.sent = lights

    def off(self):
        badge.caselights(0)
        self.sent = None
