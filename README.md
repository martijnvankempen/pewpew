# pewpew

**Pew Pew!** is a small alien shooter for the GitHub Universe 2026 badge
(Tufty 2350 derivative, 160x120 logical screen). Pew, the cat-octopus from
`pew.png`, fires spinning stars from alternating finger-guns at an alien
fleet that marches, wobbles and swoops down at you.

## How to play

Shoot all 15 aliens to clear a wave, then survive the next, faster one. The
game ends when you have lost all three lives or the fleet reaches Pew.

### Controls

| Badge button | Simulator key | Title screen | Playing | Paused | Game over |
| --- | --- | --- | --- | --- | --- |
| LEFT / RIGHT | Arrow keys, or A / D | | Move Pew | | |
| SELECT | Space or Enter, or J | Start | Fire (hold for auto-fire) | Resume | Play again |
| UP | Arrow Up, or W | | Octo-burst (when charged) | | |
| DOWN | Arrow Down, or S | Tilt-to-steer on/off | | | |
| BACK | K | | Pause | Quit to title | Back to title |
| MENU | U | | Pause | | |
| HOME | Esc | Back to the badge menu | Back to the badge menu | Back to the badge menu | Back to the badge menu |

The badge's touch pad and physical buttons do the same thing, and the
controls follow the screen when you hold the badge upside down. On the game
over screen, SELECT and BACK work after a short pause (0.8 s) so you don't
skip it by accident.

### Shooting

- Pew fires from the left and right finger-guns in turn. Hold SELECT for
  auto-fire, about four shots a second.
- Up to four stars can be on screen at once.
- Stars also destroy alien shots they touch.

### Octo-burst

- Every alien you hit adds one charge. Ten hits fill the bar along the bottom
  edge of the screen; it turns pink and "UP: BURST!" flashes at the top.
- Press UP to fire seven stars at once in a wide fan. Burst stars don't count
  towards the four-star limit.
- The charge carries over between waves, and resets when you use it.

### Scoring

| Alien | Row | In formation | Diving |
| --- | --- | --- | --- |
| Pink, one big eye | Top | 30 | 60 |
| Cyan, horned | Middle | 20 | 40 |
| Green jelly | Bottom | 10 | 20 |

Clearing a wave is worth 100 points. Your best score is shown on the title
screen and in the top bar.

### The alien fleet

- The fleet (three rows of five) marches side to side and drops a little
  each time it reaches the edge of the screen.
- It gets faster as you shoot it down: the last alien moves more than three
  times as fast as the full fleet.
- It is not a steady march: the aliens bob up and down, the fleet keeps
  speeding up and slowing down, and now and then it turns back without
  reaching the edge.
- The lowest alien in a random column fires; about one shot in three is aimed
  at where Pew is.

### Divers

- Every few seconds an alien shivers in place for a moment and then breaks
  formation to swoop down at Pew on a curvy, random path.
- Most divers fire an aimed shot on the way down.
- A diver that flies into Pew costs you a life (and dies too).
- A diver that misses flies off the bottom, comes back in from the top and
  returns to its place in the fleet.
- Shooting a diver is worth double points.

### Lives

- You start with three lives, shown as small Pews at the top right.
- Getting hit removes any alien shots on screen, and Pew blinks for 1.5 s
  while nothing can hurt it.

### Waves

Each wave starts with a "WAVE n" banner. The fleet holds still for about a
second while you can already move and shoot. Every new wave:

- marches faster (15% more per wave) and starts slightly lower;
- fires more often and can have more shots on screen (up to four);
- sends divers more often, and more of them at once (up to three).

### Tilt-to-steer

Turn it on with DOWN on the title screen. When a game starts, the way you
are holding the badge becomes "level". Lean it left or right to move:
around 15 degrees is full speed, and tiny wobbles are ignored. The buttons
keep working while tilt is on.

### Screen and lights

- Top bar: your score on the left, the best score in the middle (or the
  Octo-burst prompt), lives on the right.
- Bottom edge: the Octo-burst charge bar.
- The screen shakes on hits, and the badge's case LEDs flash when you hit
  something or get hit. They run around the badge during an Octo-burst and
  when you clear a wave.

### Saved on the badge

The best score and the tilt setting are kept between games and after a
reset. The best score is only saved at game over: quitting to the title
from the pause screen, or pressing HOME, doesn't save it.

## Layout

| Path | What |
| --- | --- |
| `badge/apps/pewpew/__init__.py` | App setup, screens (title, play, pause, game over), HUD, saved data |
| `badge/apps/pewpew/pew.py` | Pew: movement, alternating shots, Octo-burst, lives |
| `badge/apps/pewpew/aliens.py` | The fleet: march, pace changes, divers, zaps, hit tests |
| `badge/apps/pewpew/fx.py` | Starfield, particles, screen shake, case LEDs |
| `badge/apps/pewpew/controls.py` | Buttons plus optional tilt-to-steer |
| `badge/apps/pewpew/assets/`, `icon.png` | Generated images |
| `tools/make_assets.py` | Builds the images from `pew.png` (needs Pillow) |
| `tools/simulate.mjs` | Runs the app in the badge simulator in a browser (needs Node and a badger/home clone) |

The app uses the 2026 runtime globals (`badge`, `screen`, `image`, ...), not
the 2025 `badgeware` API.

## Regenerate the images

```sh
python3 -m venv ~/.venvs/pewpew && ~/.venvs/pewpew/bin/pip install pillow
~/.venvs/pewpew/bin/python tools/make_assets.py
```

The script prints the finger-tip positions in the player sprite; keep
`MUZZLES` in `pew.py` in sync if the sprite changes.

## Check and run

The checks and deployment tools live in
[badger/home](https://github.com/badger/home). With a clone at
`~/src/badger-home`:

```sh
scripts=~/src/badger-home/.github/skills/hyb26-skill/scripts
python3 $scripts/validate_app.py badge/apps/pewpew --target emulator
python3 ~/src/badger-home/.github/scripts/validate_app_readmes.py badge/apps
```

To try it without a badge, start the simulator and open the printed URL
(the keys are in the controls table above):

```sh
node tools/simulate.mjs --home ~/src/badger-home
```

It serves the Badge Simulator page from the badger/home clone, runs
`badge/apps/pewpew` in it and accepts scripted presses, screenshots and code
(`/ctl/press`, `/ctl/screenshot`, `/ctl/exec`; see the top of the script).
The simulator always reports a level badge, so tilt-to-steer and the case
LEDs need real hardware.

## Install on a badge

Connect the badge over USB, then preview and copy the app:

```sh
python3 $scripts/deploy_app.py badge/apps/pewpew
python3 $scripts/deploy_app.py badge/apps/pewpew --write
```

Or put the badge in USB Disk Mode (double-tap RESET) and copy
`badge/apps/pewpew` to `BADGER/apps/pewpew`. Stock menus need the menu icon
patch (`patch_menu_icons.py`) to show `icon.png`.
