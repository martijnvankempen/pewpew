#!/usr/bin/env python3
"""Generate the Pew Pew! badge app images from pew.png. Needs Pillow."""

from pathlib import Path

import math
import random

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "pew.png"
APP = ROOT / "badge" / "apps" / "pewpew"
ASSETS = APP / "assets"

NAVY = (41, 65, 89)
OUTLINE = (226, 59, 59)
EYE = (255, 255, 255)

PLAYER_SIZE = (26, 22)
LOGO_SIZE = 64
ICON_SIZE = 48

# Original alien designs, 11x8, two animation frames each.
# '#' body, 'o' eye white, 'x' pupil, '.' transparent.
ALIENS = [
    (
        (255, 92, 205),
        [
            "....###....",
            "..#######..",
            ".###ooo###.",
            ".##ooxoo##.",
            ".###ooo###.",
            "..#######..",
            ".#.#...#.#.",
            "#...#.#...#",
        ],
        [
            "....###....",
            "..#######..",
            ".###ooo###.",
            ".##oxooo##.",
            ".###ooo###.",
            "..#######..",
            "..#.#.#.#..",
            ".#..#.#..#.",
        ],
    ),
    (
        (80, 220, 255),
        [
            ".#.......#.",
            ".##.....##.",
            "..#######..",
            ".##o###o##.",
            ".#########.",
            ".#.#.#.#.#.",
            "..#######..",
            ".##.....##.",
        ],
        [
            ".#.......#.",
            "..#.....#..",
            "..#######..",
            ".##o###o##.",
            ".#########.",
            ".##.#.#.##.",
            "..#######..",
            "...##.##...",
        ],
    ),
    (
        (160, 255, 90),
        [
            "...#####...",
            ".#########.",
            "###o###o###",
            "###########",
            "#.##.#.##.#",
            "#.#..#..#.#",
            "..#..#..#..",
            ".#...#...#.",
        ],
        [
            "...#####...",
            ".#########.",
            "###o###o###",
            "###########",
            "#.##.#.##.#",
            ".#.#.#.#.#.",
            ".#..#.#..#.",
            "..#.....#..",
        ],
    ),
]
PUPIL = (20, 20, 30)


def is_red(p):
    return p[0] > 150 and p[1] < 110 and p[2] < 110


def is_white(p):
    return p[0] > 200 and p[1] > 200 and p[2] > 200


def is_navy(p):
    return abs(p[0] - NAVY[0]) + abs(p[1] - NAVY[1]) + abs(p[2] - NAVY[2]) < 60


def bbox(pixels, size, keep):
    w, h = size
    xs, ys = [], []
    for y in range(h):
        for x in range(w):
            if keep(pixels[x, y]):
                xs.append(x)
                ys.append(y)
    return min(xs), min(ys), max(xs) + 1, max(ys) + 1


def paletted(rgba):
    """Pixel art with hard alpha -> indexed PNG, index 0 transparent."""
    colors = [(0, 0, 0)]
    out = Image.new("P", rgba.size, 0)
    src, dst = rgba.load(), out.load()
    for y in range(rgba.height):
        for x in range(rgba.width):
            r, g, b, a = src[x, y]
            if a < 128:
                continue
            if (r, g, b) not in colors:
                colors.append((r, g, b))
            dst[x, y] = colors.index((r, g, b))
    out.putpalette([c for rgb in colors for c in rgb])
    out.info["transparency"] = 0
    return out


def save(img, path, **kwargs):
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, optimize=True, **kwargs)
    print(f"wrote {path.relative_to(ROOT)} {img.size[0]}x{img.size[1]} {img.mode}")


def make_logo(src, cx, cy, ring_r, size):
    box = (round(cx - ring_r), round(cy - ring_r), round(cx + ring_r), round(cy + ring_r))
    crop = src.crop(box).convert("RGBA")
    mask = Image.new("L", crop.size, 0)
    ImageDraw.Draw(mask).ellipse((0, 0, crop.width - 1, crop.height - 1), fill=255)
    crop.putalpha(mask)
    return crop.resize((size, size), Image.LANCZOS)


def make_player(src, cx, cy, r):
    px = src.load()
    inside = (r - 4) ** 2
    body = Image.new("L", src.size, 0)
    eyes = Image.new("L", src.size, 0)
    bp, ep = body.load(), eyes.load()
    for y in range(round(cy - r), round(cy + r)):
        for x in range(round(cx - r), round(cx + r)):
            if (x - cx) ** 2 + (y - cy) ** 2 >= inside:
                continue
            if is_navy(px[x, y]):
                bp[x, y] = 255
            elif is_white(px[x, y]):
                ep[x, y] = 255
    box = body.getbbox()
    body = body.crop(box).resize(PLAYER_SIZE, Image.BOX)
    eyes = eyes.crop(box).resize(PLAYER_SIZE, Image.BOX)

    w, h = PLAYER_SIZE
    sprite = Image.new("RGBA", (w + 2, h + 2), (0, 0, 0, 0))
    sp, bp, ep = sprite.load(), body.load(), eyes.load()
    for y in range(h):
        for x in range(w):
            if ep[x, y] > 60:
                sp[x + 1, y + 1] = EYE + (255,)
            elif bp[x, y] > 110:
                sp[x + 1, y + 1] = NAVY + (255,)

    filled = {(x, y) for y in range(h + 2) for x in range(w + 2) if sp[x, y][3]}
    for y in range(h + 2):
        for x in range(w + 2):
            if (x, y) in filled:
                continue
            if any((x + dx, y + dy) in filled for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                sp[x, y] = OUTLINE + (255,)

    # Fingertips: highest body pixel in the outer quarters (the ears sit further in).
    def tip(columns):
        best = None
        for x in columns:
            for y in range(h + 2):
                if (x, y) in filled:
                    if best is None or y < best[1]:
                        best = (x, y)
                    break
        return best

    quarter = (w + 2) // 4
    print("muzzles", tip(range(0, quarter)), tip(range(w + 2 - quarter, w + 2)))
    return sprite


def make_aliens():
    """Two animation frames per alien, plus a white silhouette for the hit flash."""
    sheet = Image.new("RGBA", (11 * 3, 8 * len(ALIENS)), (0, 0, 0, 0))
    sp = sheet.load()
    for row, (body, *frames) in enumerate(ALIENS):
        for col, frame in enumerate(frames + [frames[0]]):
            for y, line in enumerate(frame):
                for x, ch in enumerate(line):
                    color = {"#": body, "o": EYE, "x": PUPIL}.get(ch)
                    if color:
                        sp[col * 11 + x, row * 8 + y] = (EYE if col == 2 else color) + (255,)
    return sheet


BOSS_SIZE = (40, 28)
BOSS_BODY = (150, 80, 255)
BOSS_SHADE = (95, 45, 185)
BOSS_LIGHT = (205, 165, 255)
BOSS_RIM = (60, 30, 120)
BOSS_LAMP = (255, 228, 90)
BOSS_LINE = (22, 10, 44)


def make_boss_frame(frame, flash=False):
    """The mothership: a three-eyed dome on a lit rim, with six wavy tentacles."""
    w, h = BOSS_SIZE
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = img.load()

    def put(x, y, c):
        if 0 <= x < w and 0 <= y < h:
            px[x, y] = c + (255,)

    for y in range(h):
        for x in range(w):
            # Tentacles under the rim.
            if 16 <= y <= 26:
                for i, base in enumerate((7, 12, 17, 22, 27, 32)):
                    sway = math.sin(y * 0.7 + i * 1.3 + frame * math.pi) * 1.6 * (y - 15) / 10
                    width = 1.6 if y < 23 else 0.9
                    if abs(x + 0.5 - (base + sway)) < width:
                        put(x, y, BOSS_SHADE if y < 22 else BOSS_RIM)
            # Dome.
            dx, dy = (x + 0.5 - 20) / 17.5, (y + 0.5 - 12) / 11
            if dx * dx + dy * dy <= 1 and y <= 14:
                shade = BOSS_SHADE if dy > 0.35 or dx > 0.55 else BOSS_BODY
                hx, hy = (x + 0.5 - 12) / 5, (y + 0.5 - 5) / 2
                put(x, y, BOSS_LIGHT if hx * hx + hy * hy <= 1 else shade)
            # Rim with running lights.
            if 14 <= y <= 17 and 2 <= x <= 37:
                lamp = y in (15, 16) and x % 4 == (0 if frame == 0 else 2) and 4 <= x <= 35
                put(x, y, BOSS_LAMP if lamp else BOSS_RIM)

    def eye(cx, cy, r, look):
        for y in range(h):
            for x in range(w):
                d = (x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2
                if d <= r * r:
                    put(x, y, EYE)
                if (x + 0.5 - cx - look) ** 2 + (y + 0.5 - cy - 0.5) ** 2 <= (r * 0.5) ** 2:
                    put(x, y, PUPIL)

    look = -1 if frame == 0 else 1
    eye(20, 8.5, 4.2, look)
    eye(10.5, 10, 2.4, look * 0.6)
    eye(29.5, 10, 2.4, look * 0.6)

    filled = {(x, y) for y in range(h) for x in range(w) if px[x, y][3]}
    for y in range(h):
        for x in range(w):
            if (x, y) not in filled and any((x + dx, y + dy) in filled
                                            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                put(x, y, BOSS_LINE)
    if flash:
        for x, y in filled:
            put(x, y, EYE)
    return img


def make_boss():
    w, h = BOSS_SIZE
    sheet = Image.new("RGBA", (w * 3, h), (0, 0, 0, 0))
    sheet.paste(make_boss_frame(0), (0, 0))
    sheet.paste(make_boss_frame(1), (w, 0))
    sheet.paste(make_boss_frame(0, flash=True), (w * 2, 0))
    return sheet


def periodic_noise(w, h, cells_x, cells_y, rng):
    """Smooth value noise that tiles in both directions."""
    grid = [[rng.random() for _ in range(cells_x)] for _ in range(cells_y)]
    out = []
    for y in range(h):
        fy = y / h * cells_y
        y0 = int(fy)
        ty = fy - y0
        ty = ty * ty * (3 - 2 * ty)
        row = []
        for x in range(w):
            fx = x / w * cells_x
            x0 = int(fx)
            tx = fx - x0
            tx = tx * tx * (3 - 2 * tx)
            a = grid[y0 % cells_y][x0 % cells_x]
            b = grid[y0 % cells_y][(x0 + 1) % cells_x]
            c = grid[(y0 + 1) % cells_y][x0 % cells_x]
            d = grid[(y0 + 1) % cells_y][(x0 + 1) % cells_x]
            row.append((a + (b - a) * tx) * (1 - ty) + (c + (d - c) * tx) * ty)
        out.append(row)
    return out


def fractal(w, h, rng):
    layers = [(periodic_noise(w, h, 4 * k, 3 * k, rng), 1 / k) for k in (1, 2, 4, 8)]
    total = sum(weight for _, weight in layers)
    return [[sum(n[y][x] * weight for n, weight in layers) / total for x in range(w)] for y in range(h)]


def make_nebula(w=160, h=120):
    """Dark, vertically tiling space clouds that sit behind everything."""
    rng = random.Random(2026)
    purple = fractal(w, h, rng)
    teal = fractal(w, h, rng)
    base = (7, 10, 18)
    img = Image.new("RGB", (w, h))
    px = img.load()
    for y in range(h):
        for x in range(w):
            p = max(0.0, (purple[y][x] - 0.45) / 0.3)
            t = max(0.0, (teal[y][x] - 0.5) / 0.3)
            core = max(0.0, p - 0.75) * 2
            r = base[0] + 58 * min(p, 1) + 60 * min(core, 1)
            g = base[1] + 14 * min(p, 1) + 40 * min(t, 1)
            b = base[2] + 70 * min(p, 1) + 52 * min(t, 1) + 40 * min(core, 1)
            px[x, y] = (min(255, int(r)), min(255, int(g)), min(255, int(b)))
    return img.quantize(64, dither=Image.Dither.NONE)


def make_planet(size=26):
    """A ringed planet lit from the top left, supersampled for soft edges."""
    k = 4
    big = Image.new("RGBA", (size * k, size * k), (0, 0, 0, 0))
    px = big.load()
    c = size * k / 2
    r = 8 * k
    ring_pen = (255, 140, 215)

    def ring(x, y):
        rx, ry = (x - c) * math.cos(0.35) + (y - c) * math.sin(0.35), -(x - c) * math.sin(0.35) + (y - c) * math.cos(0.35)
        d = (rx / (12.5 * k)) ** 2 + (ry / (3.2 * k)) ** 2
        return 0.72 <= d <= 1.0, ry

    for y in range(size * k):
        for x in range(size * k):
            on_ring, ry = ring(x, y)
            dx, dy = x - c, y - c
            inside = dx * dx + dy * dy <= r * r
            if inside and not (on_ring and ry > 0):
                light = max(0.0, 1 - math.hypot(dx + 0.45 * r, dy + 0.45 * r) / (1.9 * r))
                band = 0.12 * math.sin(dy / k * 1.4)
                px[x, y] = (int(30 + 120 * light), int(70 + 150 * light + 30 * band), int(110 + 130 * light + 30 * band), 255)
            elif on_ring:
                fade = 0.55 if ry < 0 and inside else 1.0
                px[x, y] = tuple(int(v * fade) for v in ring_pen) + (230,)
    return big.resize((size, size), Image.LANCZOS)


def main():
    src = Image.open(SOURCE).convert("RGB")
    px = src.load()
    red = bbox(px, src.size, is_red)
    white = bbox(px, src.size, is_white)
    cx, cy = (red[0] + red[2]) / 2, (red[1] + red[3]) / 2
    r = (red[2] - red[0]) / 2
    ring_r = (white[2] - white[0]) / 2

    save(make_logo(src, cx, cy, ring_r, LOGO_SIZE), ASSETS / "logo.png")
    save(make_logo(src, cx, cy, ring_r, ICON_SIZE), APP / "icon.png")
    save(paletted(make_player(src, cx, cy, r)), ASSETS / "pew.png")
    save(paletted(make_aliens()), ASSETS / "aliens.png")
    save(paletted(make_boss()), ASSETS / "boss.png")
    save(make_nebula(), ASSETS / "nebula.png")
    save(make_planet(), ASSETS / "planet.png")


if __name__ == "__main__":
    main()
