# pewpew

**Pew Pew!** is a small alien shooter for the GitHub Universe 2026 badge
(Tufty 2350 derivative, 160x120 logical screen). Pew, the cat-octopus from
`pew.png`, fires spinning stars from alternating finger-guns at an alien
fleet that marches, wobbles and swoops down at you.

To play it on your own badge, see
[Install on your badge](#install-on-your-badge).

## What it looks like

These are captures from the badge simulator (`tools/simulate.mjs`). The
badge's 160x120 screen is shown at 2x in the animation and 3x in the stills.

<p align="center">
  <img src="docs/screenshots/gameplay.gif" alt="Animated gameplay: Pew fires stars at the alien fleet, dodges divers and sets off an Octo-burst" width="480">
  <img src="docs/screenshots/badge.png" alt="Pew Pew! running on the GitHub Universe 2026 badge in the simulator, purple touch card on top" height="360">
</p>

| | | |
| :---: | :---: | :---: |
| ![Title screen with the PEW PEW! logo and a PRESS TO PLAY arrow](docs/screenshots/title.png) | ![HOW TO PLAY card: the badge with arrows to each control](docs/screenshots/how-to-play.png) | ![Wave 1: Pew under the alien fleet](docs/screenshots/gameplay.png) |
| **Title**: the arrow points at the real SELECT button | **How to play**: arrows to every control | **Wave 1**: the fleet bobs and changes pace |
| ![Two aliens diving at Pew](docs/screenshots/divers.png) | ![Octo-burst: a fan of pink stars](docs/screenshots/octo-burst.png) | ![WAVE CLEAR and PERFECT!](docs/screenshots/wave-clear.png) |
| **Divers** swoop down at Pew | **Octo-burst**: seven stars at once | **Wave clear**, with a PERFECT bonus |
| ![Boss WARNING: MERGE CONFLICT](docs/screenshots/boss-warning.png) | ![Boss fight with a health bar](docs/screenshots/boss.png) | ![DO BETTER! while Pew fires stars that burst into fireworks](docs/screenshots/do-better.png) |
| **Boss warning** every third wave | **Boss fight** with its health bar | **Game over**: DO BETTER! for 8 seconds |
| ![The forklift sponsor ad](docs/screenshots/ad.png) | ![Name entry for a top-5 score](docs/screenshots/name-entry.png) | ![Hall of Fame](docs/screenshots/hall-of-fame.png) |
| **Then** the 6-second sponsor ad | **Name entry** for a top-5 score | **Hall of Fame** |

## Install on your badge

The game is one folder, `badge/apps/pewpew`. Copy it into the badge's `apps`
folder and it shows up in the badge menu. No firmware update, Wi-Fi or extra
hardware is needed.

You need:

- a GitHub Universe 2026 badge;
- a USB-C cable that carries data (with a charge-only cable the badge's drive
  never appears);
- this repository: `git clone https://github.com/martijnvankempen/pewpew.git`,
  or **Code > Download ZIP** on GitHub and unzip it.

### Copy it by hand

1. Connect the badge to your computer.
2. Put the badge in USB Disk Mode: quickly double-tap its RESET button, or open
   the **Mass Storage** app from the badge menu. After a few seconds a drive
   called **BADGER** appears.
3. Open BADGER. It has an `apps` folder (on some badges `system/apps`).
4. Copy the `badge/apps/pewpew` folder from this repository into that `apps`
   folder. Copy the folder itself, so you end up with
   `BADGER/apps/pewpew/__init__.py`.
5. Eject BADGER like a USB stick and wait for the drive to disappear. The
   badge restarts into the menu; press RESET if it doesn't. On Windows, "An
   error occurred while ejecting 'BADGER'" is harmless: the badge restarts as
   soon as it gets the request, after the files are written.
6. In the menu, move to the **Pewpew** tile with the buttons and press SELECT.
   It comes after the badge's own apps.

### Or use the badger/home scripts

[badger/home](https://github.com/badger/home) has scripts that switch the
badge to USB Disk Mode, copy the app and eject the drive for you. They need
Python 3 and `mpremote`. Run them from the root of this repository.

macOS or Linux:

```sh
git clone --depth 1 https://github.com/badger/home ~/src/badger-home
python3 -m pip install mpremote
scripts=~/src/badger-home/.github/skills/hyb26-skill/scripts

python3 $scripts/badge_serial.py disk-mode            # reboots into USB Disk Mode
python3 $scripts/deploy_app.py badge/apps/pewpew      # lists what it would copy
python3 $scripts/deploy_app.py badge/apps/pewpew --write
python3 $scripts/badge_serial.py eject
```

Windows (PowerShell, not WSL: WSL doesn't see the badge's USB port or the
BADGER drive):

```powershell
git clone --depth 1 https://github.com/badger/home $HOME\src\badger-home
python -m pip install mpremote
$scripts = "$HOME\src\badger-home\.github\skills\hyb26-skill\scripts"

python $scripts\badge_serial.py disk-mode
python $scripts\deploy_app.py badge\apps\pewpew
python $scripts\deploy_app.py badge\apps\pewpew --write
python $scripts\badge_serial.py eject
```

- `deploy_app.py` finds BADGER by itself; if it doesn't, add `--mount` with
  the drive, for example `--mount E:\` or `--mount /Volumes/BADGER`.
- If `disk-mode` fails on your badge's firmware, double-tap RESET instead.
- If pip refuses to install `mpremote` ("externally managed"), use
  `pipx install mpremote`.

### Update to a new version

Get the new version (`git pull`, or download the ZIP again) and copy it
again. By hand, delete `BADGER/apps/pewpew` first. With the script, add
`--replace`; it keeps the old version in `BADGER/.badge-app-backups`:

```sh
python3 $scripts/deploy_app.py badge/apps/pewpew --write --replace
```

The Hall of Fame, best score and settings live outside the app folder, in
`/state/pewpew.json`, so updates keep them.

### Pew on the menu tile

The menu on badges from the event shows a default icon for apps that don't
come with the badge. To show Pew's face (`icon.png`) on the tile instead,
patch the menu once per badge, in USB Disk Mode:

```sh
python3 $scripts/badge_serial.py info               # "menu icon.png support: yes/no"
python3 $scripts/patch_menu_icons.py                # preview
python3 $scripts/patch_menu_icons.py --write
python3 $scripts/badge_serial.py eject
```

The patch keeps the original menu in `BADGER/.badge-app-backups`. The game
works the same without it.

### Remove it

In USB Disk Mode, delete `BADGER/apps/pewpew` and eject. The scores stay in
`/state/pewpew.json`, which isn't on the BADGER drive. To clear them, for
example to start a fresh Hall of Fame on an event day, run this with the
port from `badge_serial.py port` (such as `COM5` or `/dev/ttyACM0`) and press
RESET afterwards:

```sh
mpremote connect PORT exec "import os; os.remove('/state/pewpew.json')"
```

### If something goes wrong

| Problem | What to do |
| --- | --- |
| No BADGER drive | Use a data cable. Double-tap RESET faster, or open the Mass Storage app. |
| A drive called RP2350 appears | That's the firmware bootloader, not the badge's storage. Don't copy anything there; press RESET once and try again. |
| Pewpew isn't in the menu | Check that `BADGER/apps/pewpew/__init__.py` exists (not `apps/pewpew/pewpew/...` or `apps/badge/...`), then press RESET. |
| The tile has a default icon | See [Pew on the menu tile](#pew-on-the-menu-tile). |
| The badge doesn't restart after ejecting | Press RESET. |
| The game stops with an error | Run `mpremote connect PORT resume repl`, start the game from the menu and read the error; Ctrl-] exits. |

## How to play

Shoot all 15 aliens to clear a wave, then survive the next, faster one.
Every third wave is a boss fight. The game ends when you have lost all three
lives or the fleet reaches Pew.

### The badge's controls

Hold the badge as it hangs on the lanyard: the purple touch card on top and
the screen below it.

- **Touch pad** (purple card): a d-pad on the right; on the left a big round
  SELECT pad and a smaller round BACK pad; in the middle two small pills,
  MENU and HOME.
- **Buttons**: LEFT, RIGHT and SELECT under the screen; UP and DOWN on the
  right edge.

| Control | Simulator key | Title screen | How to play | Playing | Paused | Name entry |
| --- | --- | --- | --- | --- | --- | --- |
| Touch d-pad | W / A / S / D | DOWN: tilt-to-steer on/off | | Fly around, up and down too | | Change / move letter |
| LEFT / RIGHT buttons | Arrow Left / Right | | | Move left / right | | Previous / next letter |
| SELECT (button or big touch pad) | Space or Enter, or J | Start | Play now | Fire (hold for auto-fire) | Resume | Next letter; on the last one, save |
| UP / DOWN buttons (right edge) | Arrow Up / Down | DOWN: tilt-to-steer on/off | | Octo-burst (when charged) | | Change letter |
| BACK (small touch pad) | K | | Back to title | Pause | Quit to title | Previous letter |
| MENU (touch pill) | U | | | Pause | | |
| HOME (touch pill) | Esc | Back to the badge menu | Back to the badge menu | Back to the badge menu | Back to the badge menu | Back to the badge menu |

The controls follow the screen when you hold the badge upside down. No button
does anything during DO BETTER! or the ad.

You don't need to know the button names: whenever the game wants SELECT
("PRESS TO PLAY", "RESUME", "NEXT"), a bouncing arrow at the bottom edge of
the screen points straight down at the SELECT button under it. When the
Octo-burst is ready, and on the name entry, arrows at the right edge point at
the two side buttons. Held upside down, the arrows point up and left instead.

### How to play card

Pressing SELECT on the title shows a HOW TO PLAY card before the game starts:
a drawing of the badge in the middle with labelled arrows pointing at each
control (FIRE, MOVE, PAUSE, BURST), colour-coded like the controls themselves
(cyan moves, gold fires, pink is the Octo-burst, lilac pauses). One arrow at a
time turns white and its control gets a blinking frame. It stays up until you press SELECT, so read it at
your own pace; BACK goes back to the title instead.

### Attract mode

Leave the title screen alone for 9 seconds and the badge plays itself: an
autopilot flies Pew through the waves for up to 30 seconds, then the Hall of
Fame and the HOW TO PLAY card are shown and it goes back to the title. The
case LEDs breathe slowly meanwhile. SELECT starts a real game from the demo,
the Hall of Fame or the card; any other button goes to the title.

### Moving

- The LEFT and RIGHT buttons move Pew sideways along the bottom.
- The touch d-pad moves Pew in eight directions: besides left and right it
  can lift Pew about a quarter of the screen up to dodge shots and divers,
  but never into the alien fleet. Diagonals are as fast as straight moves.
- Tilt-to-steer (below) adds to the sideways movement.

### Shooting

- Pew fires from the left and right finger-guns in turn. Hold SELECT (the
  button or the big touch pad) for auto-fire, about four shots a second.
- Up to four stars can be on screen at once.
- Stars also destroy alien shots they touch.

### Octo-burst

- Every alien you hit adds one charge. Ten hits fill the bar along the bottom
  edge of the screen; it turns pink, "BURST!" flashes at the top and arrows
  point at the two buttons on the right edge.
- Press either button on the right edge (UP or DOWN) to fire seven stars at
  once in a wide fan. Up on the touch pad moves Pew instead. Burst stars
  don't count towards the four-star limit.
- The charge carries over between waves, and resets when you use it.

### Scoring

| Alien | Row | In formation | Diving |
| --- | --- | --- | --- |
| Pink, one big eye | Top | 30 | 60 |
| Cyan, horned | Middle | 20 | 40 |
| Green jelly | Bottom | 10 | 20 |

Clearing a wave is worth 100 points, plus 500 for a PERFECT wave (no lives
lost). Every star that hits the boss is worth 10, and destroying it is worth
1000 per boss you have beaten so far (1000, 2000, ...). Your best score is shown on the title screen
and in the top bar.

### Combo

Every hit in a row raises the combo. At 5, 10, 20 and 30 hits all points are
multiplied by 2, 3, 4 and 5; the multiplier shows next to your score. An
aimed star that flies off the top without hitting anything, or losing a
life, resets the combo (Octo-burst stars that miss don't count).

### Hall of Fame

The five best scores are kept on the badge with three-letter initials. It
starts with made-up scores to beat, arcade style. When your score makes
the table, the name entry follows DO BETTER! and the ad, and it remembers the
last initials you used. The Hall of Fame is saved straight away and shown with your
new row highlighted.

### DO BETTER!

<p align="center">
  <img src="docs/screenshots/do-better.gif" alt="Animated: DO BETTER! over Pew, who sways side to side firing stars that burst into fireworks, with Octo-burst fans" width="320">
</p>

When you lose, "DO BETTER!" slams onto the screen for 8 seconds with your
final score, and no button can skip it. Pew isn't fazed: it pops up from the
bottom and sways side to side, firing from alternating finger-guns. Every
star bursts into a little firework of sparks and a ring, and every couple
of seconds an Octo-burst fan goes off with a pink shockwave while the case
LEDs chase. Then the ad starts.

### The ad

After DO BETTER!, a 6-second sponsor ad plays and no button can skip it. A red
forklift reverses in on a spinning sunburst with "GET YOURSELF FORKLIFT
CERTIFIED!", a five-star rating and "SPONSORED BY CoE". The top bar shows
GAME OVER and your
final score; the bottom bar counts down and fills up, and the case LEDs pulse
like a forklift's warning beacon. After the ad you go to the name entry if
your score made the Hall of Fame, otherwise back to the title screen. The
self-playing demo never shows DO BETTER! or the ad.

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

### Boss waves

- Waves 3, 6, 9, ... are boss fights. A red WARNING with hazard stripes
  and the boss's name comes first, and the case LEDs flash red.
- The mothership glides from side to side and has a health bar under the top
  bar. It gets tougher with every boss.
- It takes turns between a fan of shots, a volley of aimed shots and a laser:
  a thin flickering line warns you where the beam will hit, then a wide beam
  fires straight down. Below half health it attacks more often and fires
  bigger volleys.
- Destroying it sets off a chain of explosions before the next wave.

### Lives

- You start with three lives, shown as small Pews at the top right.
- Getting hit removes any alien shots on screen, and Pew blinks inside a
  shield bubble for 1.5 s while nothing can hurt it.

### Waves

Each wave starts with a "WAVE n" banner while the aliens fly in to their
places. The fleet holds still for about a second while you can already move
and shoot. After a wave is cleared the stars stretch into a hyperspace jump,
and the background changes colour. Every new wave:

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

The Hall of Fame, your last initials, the best score and the tilt setting are
kept between games and after a reset. Scores are only saved when you lose:
quitting to the title from the pause screen, or pressing HOME, doesn't save
them.

## Layout

| Path | What |
| --- | --- |
| `badge/apps/pewpew/__init__.py` | App setup, screens (title, how to play, attract demo, play, pause, DO BETTER!, game-over ad, name entry, Hall of Fame), waves and bosses, combo, HUD, saved data |
| `badge/apps/pewpew/pew.py` | Pew: movement, alternating shots, Octo-burst, lives |
| `badge/apps/pewpew/aliens.py` | The fleet: fly-in, march, pace changes, divers, zaps, hit tests |
| `badge/apps/pewpew/boss.py` | The boss: entry, movement, fan/aimed/laser attacks, damage, death |
| `badge/apps/pewpew/fx.py` | Nebula, planet and warping starfield, particles, shockwave rings, score popups, screen flash and shake, case LEDs |
| `badge/apps/pewpew/controls.py` | Steering from the buttons, the touch pad (8 directions) and optional tilt |
| `badge/apps/pewpew/assets/`, `icon.png` | Generated images |
| `tools/make_assets.py` | Builds the images from `pew.png`, and the ad's forklift from `forklift.jpg` (needs Pillow) |
| `tools/simulate.mjs` | Runs the app in the badge simulator in a browser (needs Node and a badger/home clone) |
| `docs/screenshots/` | The README's screenshots and animation, captured in the simulator |

The app uses the 2026 runtime globals (`badge`, `screen`, `image`, ...), not
the 2025 `badgeware` API.

## Regenerate the images

```sh
python3 -m venv ~/.venvs/pewpew && ~/.venvs/pewpew/bin/pip install pillow
~/.venvs/pewpew/bin/python tools/make_assets.py
```

The script prints the finger-tip positions in the player sprite; keep
`MUZZLES` in `pew.py` in sync if the sprite changes.

The forklift photo `forklift.jpg` isn't in git. Put it in the repository root
to rebuild `assets/forklift.png`: the script removes the background, paints
over the brand lettering and the side sticker (`BRAND_BOXES`) and turns the
orange paint red. Without the photo it keeps the committed `forklift.png`.

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
LEDs need real hardware. To put it on a real badge, see
[Install on your badge](#install-on-your-badge).
