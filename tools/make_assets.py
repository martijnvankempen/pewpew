#!/usr/bin/env python3
"""Generate the Pew Pew! badge app images from pew.png. Needs Pillow."""

from pathlib import Path

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
    sheet = Image.new("RGBA", (11 * 2, 8 * len(ALIENS)), (0, 0, 0, 0))
    sp = sheet.load()
    for row, (body, *frames) in enumerate(ALIENS):
        for col, frame in enumerate(frames):
            for y, line in enumerate(frame):
                for x, ch in enumerate(line):
                    color = {"#": body, "o": EYE, "x": PUPIL}.get(ch)
                    if color:
                        sp[col * 11 + x, row * 8 + y] = color + (255,)
    return sheet


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


if __name__ == "__main__":
    main()
