#!/usr/bin/env python3
"""pewpew - fly the GitHub logo across your terminal, left to right.

Pure Python 3 standard library, no dependencies. The logo size is picked to
fit the current terminal and the animation adapts live when the window is
resized. Press Ctrl+C to quit.
"""

import argparse
import shutil
import sys
import time

# GitHub mark (Octocat) rasterised from the official octicon at three sizes.
# Two characters per "pixel" horizontally to compensate for tall terminal cells.
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
    ["GitHub"],
]

CSI = "\x1b["
HIDE_CURSOR = CSI + "?25l"
SHOW_CURSOR = CSI + "?25h"
CLEAR = CSI + "2J"
HOME = CSI + "H"
ALT_SCREEN_ON = CSI + "?1049h"
ALT_SCREEN_OFF = CSI + "?1049l"


def screen_size():
    """Return (columns, rows) of the terminal, with a sane fallback."""
    size = shutil.get_terminal_size(fallback=(80, 24))
    return max(size.columns, 1), max(size.lines, 1)


def pick_logo(cols, rows):
    """Return the largest logo that fits inside the screen."""
    for logo in LOGOS:
        width = max(len(line) for line in logo)
        if len(logo) <= rows and width <= cols:
            return logo
    return LOGOS[-1]


def render_frame(logo, x, cols, rows):
    """Build a full-screen frame with the logo's left edge at column x.

    The logo is vertically centred and clipped at the screen edges, so x may
    be negative (entering from the left) or beyond cols (leaving on the right).
    """
    width = max(len(line) for line in logo)
    top = max((rows - len(logo)) // 2, 0)
    lines = []
    for r in range(rows):
        i = r - top
        if 0 <= i < len(logo):
            src = logo[i].ljust(width)
            row = [" "] * cols
            for j, ch in enumerate(src):
                c = x + j
                if 0 <= c < cols:
                    row[c] = ch
            lines.append("".join(row))
        else:
            lines.append(" " * cols)
    return "\n".join(lines)


def run(fps, speed, loops, color):
    out = sys.stdout
    delay = 1.0 / fps
    out.write(ALT_SCREEN_ON + HIDE_CURSOR + CLEAR)
    if color:
        out.write(CSI + "1m")
    try:
        done = 0
        while loops == 0 or done < loops:
            cols, rows = screen_size()
            logo = pick_logo(cols, rows)
            width = max(len(line) for line in logo)
            x = -width
            while x < cols:
                new_cols, new_rows = screen_size()
                if (new_cols, new_rows) != (cols, rows):
                    cols, rows = new_cols, new_rows
                    logo = pick_logo(cols, rows)
                    width = max(len(line) for line in logo)
                    out.write(CLEAR)
                out.write(HOME + render_frame(logo, x, cols, rows))
                out.flush()
                time.sleep(delay)
                x += speed
            done += 1
    except KeyboardInterrupt:
        pass
    finally:
        out.write(CSI + "0m" + SHOW_CURSOR + ALT_SCREEN_OFF)
        out.flush()


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Fly the GitHub logo across the terminal from left to right."
    )
    parser.add_argument("--fps", type=float, default=30, help="frames per second (default: 30)")
    parser.add_argument("--speed", type=int, default=1, help="columns moved per frame (default: 1)")
    parser.add_argument("--loops", type=int, default=0, help="number of fly-bys, 0 = forever (default: 0)")
    parser.add_argument("--no-bold", action="store_true", help="disable bold text")
    args = parser.parse_args(argv)
    if args.fps <= 0 or args.speed < 1 or args.loops < 0:
        parser.error("--fps must be > 0, --speed >= 1 and --loops >= 0")
    run(args.fps, args.speed, args.loops, not args.no_bold)


if __name__ == "__main__":
    main()
