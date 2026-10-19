# pewpew

The GitHub logo (Octocat mark, as ASCII art) flies across the screen from left
to right on the GitHub Universe hackable badge (2025 badge: Badger/Tufty 2350,
MonaOS + `badgeware`, 160x120 logical screen).

## Badge app: `apps/pewpew/`

- `__init__.py` - the app (`init()` / `update()`, standard MonaOS lifecycle).
- `icon.png` - 24x24 launcher icon.

The app measures the font's real glyph size at startup and picks the largest
of three logo sizes that fits `screen.width` x `screen.height`, then centres
it vertically. Movement is time-based (`io.ticks_delta`), so speed is the same
regardless of frame rate. Press HOME to return to the launcher.

### Install

1. Double-tap RESET on the badge; the `BADGER` disk mounts.
2. Copy `apps/pewpew` to `BADGER/apps/pewpew` (the disk root is `/system`).
3. Eject the disk cleanly, tap RESET, and pick **pewpew** in the launcher.

If pewpew doesn't appear in the launcher, check that
`BADGER/apps/pewpew/__init__.py` exists, then reset.

### Try it without a badge

Use the community simulator from
[anxkhn/github-universe-2025](https://github.com/anxkhn/github-universe-2025)
(`badge25/simulator/badge_simulator.py`, needs `pygame`):

```sh
python3 badge_simulator.py -C <dir containing apps/ and assets/> apps/pewpew
```

Note that the simulator substitutes a pygame font for the badge's `.ppf`
pixel fonts, so the logo size you see there may differ from the hardware.

## Terminal preview: `pewpew.py`

The same animation for a desktop terminal (`python3 pewpew.py`, Ctrl+C to
quit). Handy for previewing; not needed for the badge.
