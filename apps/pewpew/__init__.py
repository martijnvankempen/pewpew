# pewpew - the GitHub logo, as ASCII art, flies across the badge screen
# from left to right. MonaOS / badgeware app for the GitHub Universe badge.

from badgeware import screen, PixelFont, brushes, io, run

# GitHub mark (Octocat) rasterised from the official octicon at three sizes.
# Largest first; init() picks the biggest one that fits the screen.
LOGOS = [
    [
        "          ############",
        "       ##################",
        "    ########################",
        "   #####  ############   ####",
        "  #####                  #####",
        " ######                  ######",
        "######                    ######",
        "######                    ######",
        "######                    ######",
        "#######                   ######",
        " #######                #######",
        "  ###  ######      ###########",
        "   ###  ####        #########",
        "    ####            ########",
        "       #####        #####",
        "          ##        ##",
    ],
    [
        "      ##########",
        "   ################",
        "  ###  ########  ###",
        " ####            ####",
        "####              ####",
        "####              ####",
        "####              ####",
        " #####          #####",
        "  ##  ##      ######",
        "   #####      #####",
        "      ##      ##",
    ],
    [
        "   ########",
        " ## ###### ##",
        "###        ###",
        "###        ###",
        "###        ###",
        " ## #    ####",
        "   ##    ##",
    ],
]

FONT_PATH = "/system/assets/fonts/teatime.ppf"
SPEED = 40  # pixels per second
MAX_STEP_MS = 100  # cap per-frame movement after a stall (e.g. app start)

BACKGROUND = brushes.color(13, 17, 23)
FOREGROUND = brushes.color(57, 211, 83)

# Filled in by init()
runs = []  # (x_offset, y_offset, "###") for each run of '#' in the logo
logo_w = 0
logo_y = 0
x = 0.0


def find_runs(logo, cw, lh):
    """Split each line into runs of '#', positioned in pixels.

    Drawing runs at explicit offsets means we never depend on how wide the
    font draws a space.
    """
    out = []
    for row, line in enumerate(logo):
        col = 0
        n = len(line)
        while col < n:
            if line[col] == "#":
                start = col
                while col < n and line[col] == "#":
                    col += 1
                out.append((int(start * cw), row * lh, line[start:col]))
            else:
                col += 1
    return out


def init():
    global runs, logo_w, logo_y, x
    font = PixelFont.load(FONT_PATH)
    screen.font = font

    # Measure the real glyph size so the fit works for any font and screen.
    cw = screen.measure_text("##########")[0] / 10
    lh = font.height

    logo = LOGOS[-1]
    for candidate in LOGOS:
        cols = max(len(line) for line in candidate)
        if cols * cw <= screen.width and len(candidate) * lh <= screen.height:
            logo = candidate
            break

    logo_w = int(max(len(line) for line in logo) * cw)
    logo_y = max((screen.height - len(logo) * lh) // 2, 0)
    runs = find_runs(logo, cw, lh)
    x = -logo_w


def update():
    global x

    x += SPEED * min(io.ticks_delta, MAX_STEP_MS) / 1000
    if x >= screen.width:
        x = -logo_w

    screen.brush = BACKGROUND
    screen.clear()

    screen.brush = FOREGROUND
    ix = int(x)
    for dx, dy, text in runs:
        screen.text(text, ix + dx, logo_y + dy)


if __name__ == "__main__":
    run(update)
