# pewpew

A tiny terminal animation: the GitHub logo (Octocat mark, in ASCII art) flies
across your screen from left to right.

- Pure Python 3 standard library, no dependencies.
- Adapts to the terminal size: picks the largest logo that fits (16, 11 or 7
  rows, falling back to the text `GitHub` on tiny screens), centres it
  vertically, and reacts live to window resizes.
- Restores your terminal (cursor, screen contents) on exit / Ctrl+C.

## Usage

```sh
python3 pewpew.py                  # loop forever, Ctrl+C to quit
python3 pewpew.py --loops 1        # single fly-by
python3 pewpew.py --fps 60 --speed 2
python3 pewpew.py --help
```

## Hackable badge

The goal is to eventually run this on a GitHub Universe hackable badge (the
2025 badge, Badger 2350, is an RP2350 board running MicroPython with a
320x240 display). The frame logic (`pick_logo` / `render_frame`) is
deliberately free of terminal-specific code so it can be reused there with a
different output backend.
