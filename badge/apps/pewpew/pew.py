import math

from fx import draw_star

W = screen.width
H = screen.height

SPRITE = image.load("assets/pew.png")
SPRITE_W = 28
SPRITE_H = 24
# Fingertip positions inside the sprite, printed by tools/make_assets.py.
MUZZLES = ((2, 4), (25, 4))
HITBOX = (5, 7, 18, 15)

SPEED = 80
FIRE_MS = 220
MAX_STARS = 4
STAR_SPEED = 120
STAR_RADIUS = 4.5
BURST_SHOTS = 7
BURST_SPREAD = 0.9
CHARGE_FULL = 10
INVULNERABLE_MS = 1500
LIVES = 3

STAR_PEN = color.rgb(255, 228, 90)
BURST_PEN = color.rgb(255, 140, 215)
STAR_HALO = color.rgb(255, 228, 90, 70)
BURST_HALO = color.rgb(255, 140, 215, 70)
MUZZLE_PEN = color.rgb(255, 255, 210)
STAR_TRAIL = (color.rgb(255, 228, 90, 110), color.rgb(255, 228, 90, 50))
BURST_TRAIL = (color.rgb(255, 140, 215, 110), color.rgb(255, 140, 215, 50))
SHIELD_RGB = (120, 220, 255)


class Star:
    def __init__(self, x, y, vx, vy, burst):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.burst = burst


class Pew:
    def __init__(self):
        self.x = (W - SPRITE_W) / 2
        self.y = H - SPRITE_H - 2
        self.lives = LIVES
        self.charge = 0
        self.hand = 0
        self.next_fire = 0
        self.flash_hand = 0
        self.flash_until = 0
        self.hit_until = 0
        self.stars = []

    def move(self, axis, dt):
        self.x = max(0, min(W - SPRITE_W, self.x + axis * SPEED * dt))

    def fire(self, now):
        if now < self.next_fire:
            return False
        if sum(1 for s in self.stars if not s.burst) >= MAX_STARS:
            return False
        mx, my = MUZZLES[self.hand]
        self.stars.append(Star(self.x + mx, self.y + my, 0, -STAR_SPEED, False))
        self.flash_hand = self.hand
        self.flash_until = now + 80
        self.hand ^= 1
        self.next_fire = now + FIRE_MS
        return True

    def charged(self):
        return self.charge >= CHARGE_FULL

    def add_charge(self):
        self.charge = min(CHARGE_FULL, self.charge + 1)

    def burst(self):
        if not self.charged():
            return False
        self.charge = 0
        cx = self.x + SPRITE_W / 2
        for i in range(BURST_SHOTS):
            angle = -BURST_SPREAD + 2 * BURST_SPREAD * i / (BURST_SHOTS - 1)
            self.stars.append(Star(cx, self.y + 4, math.sin(angle) * STAR_SPEED,
                                   -math.cos(angle) * STAR_SPEED, True))
        return True

    def update_stars(self, dt):
        """Move the stars; returns how many aimed (non-burst) stars flew off without a hit."""
        for s in self.stars:
            s.x += s.vx * dt
            s.y += s.vy * dt
        kept = [s for s in self.stars if -6 < s.y and -6 < s.x < W + 6]
        missed = sum(1 for s in self.stars if not s.burst) - sum(1 for s in kept if not s.burst)
        self.stars = kept
        return missed

    def blinking(self, now):
        return now < self.hit_until

    def hit(self, now):
        self.lives -= 1
        self.hit_until = now + INVULNERABLE_MS

    def hitbox(self):
        return (self.x + HITBOX[0], self.y + HITBOX[1], HITBOX[2], HITBOX[3])

    def centre(self):
        return self.x + SPRITE_W / 2, self.y + SPRITE_H / 2

    def draw(self, now, ox, oy):
        for s in self.stars:
            x = s.x + ox
            y = s.y + oy
            trail = BURST_TRAIL if s.burst else STAR_TRAIL
            screen.pen = trail[1]
            screen.circle(vec2(x - s.vx * 0.06, y - s.vy * 0.06), 1.5)
            screen.pen = trail[0]
            screen.circle(vec2(x - s.vx * 0.03, y - s.vy * 0.03), 2.5)
            screen.pen = BURST_HALO if s.burst else STAR_HALO
            screen.circle(vec2(x, y), STAR_RADIUS + 1)
            draw_star(x, y, STAR_RADIUS, now * 0.6 + s.x * 7, BURST_PEN if s.burst else STAR_PEN)

        if self.lives <= 0:
            return
        x = int(self.x + ox)
        y = int(self.y + oy + math.sin(now / 250))
        if self.blinking(now):
            # Shield bubble while Pew can't be hurt.
            left = (self.hit_until - now) / INVULNERABLE_MS
            pulse = 0.5 + 0.5 * math.sin(now / 60)
            screen.pen = color.rgb(SHIELD_RGB[0], SHIELD_RGB[1], SHIELD_RGB[2], int(40 + 120 * left * pulse))
            screen.shape(shape.circle(x + SPRITE_W / 2, y + SPRITE_H / 2 + 1, 15).stroke(1))
            if (now // 100) % 2:
                return
        if now < self.flash_until:
            # Squash a little with the recoil of each shot.
            screen.blit(SPRITE, rect(x - 1, y + 1, SPRITE_W + 2, SPRITE_H - 1))
        else:
            screen.blit(SPRITE, vec2(x, y))
        if now < self.flash_until:
            mx, my = MUZZLES[self.flash_hand]
            screen.pen = MUZZLE_PEN
            screen.circle(vec2(x + mx, y + my), 3)
