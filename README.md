# Volume Booster

A tiny system-tray app that pushes your Linux audio **above 100%** — for YouTube
videos and other sources that are so quiet you can hardly hear them even with the
player and desktop volume maxed out.

It works by asking PipeWire/PulseAudio to apply digital gain on your default
sink. No audio is re-routed or re-encoded; it simply raises the output level.

![license](https://img.shields.io/badge/license-MIT-blue.svg)

## Why? Can't I just turn everything up?

YouTube's own volume slider and your desktop volume both top out at 100%. When a
recording itself is mastered very quietly, "100%" everywhere still leaves you at
a whisper. Volume Booster adds headroom **above** that ceiling.

## Features

- **Left-click** the tray icon → a floating **0–200% slider** with − / + fine
  buttons and a "Reset to 100%" button.
- **Right-click** → quick presets **100 / 125 / 150 / 175 / 200%**, Reset, Quit.
- The icon turns **orange with a live % badge** whenever you're boosted
  (white at normal level, gray when muted).
- Live-syncs with media keys and your desktop's volume widget, so it never fights
  them.

## How much can it boost? (practical limits)

There is **no meaningful software ceiling** — PipeWire stores volume as a 32-bit
value whose maximum is roughly **6.5 million percent** (~96 dB of gain). That is
not a recommendation. The *useful* limit is set by **digital clipping**, because
at 100% the DAC is already outputting full scale (0 dBFS); anything above 100% is
pure software gain.

| Boost | Gain    | When it's useful                          |
| ----- | ------- | ----------------------------------------- |
| 100%  | 0 dB    | normal listening                          |
| 125%  | +1.9 dB | gentle lift                               |
| 150%  | +3.5 dB | quiet videos — comfortable sweet spot     |
| 200%  | +6.0 dB | very quiet dialogue/podcasts (default cap)|
| 300%  | +9.5 dB | extremely quiet sources, mild clipping    |
| 400%+ | +12 dB+ | mostly clipping; risky for your ears/speakers |

> **Practical answer:** for most "can barely hear it" content, **150–200%** is the
> sweet spot. The default ceiling is **200%** (raise it by editing `MAX_PCT` in
> `volume_booster.py`). Be careful above ~300% — a sudden loud transient at high
> boost can distort or hurt your hearing.

## Requirements

- Linux with **PipeWire** or **PulseAudio** (basically any modern distro).
- **Python 3** and **PyQt6**.
- `pactl` (from `pulseaudio-utils` / `pipewire-pulse`).

## Install

### Debian / Ubuntu (.deb)

Download `volume-booster_1.0.0_all.deb` from the
[releases](https://github.com/VanguardArts/volume-booster/releases) page and:

```bash
sudo apt install ./volume-booster_1.0.0_all.deb
```

Or build it yourself:

```bash
scripts/build-deb.sh
sudo apt install ./build/volume-booster_1.0.0_all.deb
```

### Portable install (any distro, no root)

```bash
./install.sh            # installs to ~/.local
```
Override the location with `PREFIX=/usr/local ./install.sh` (use `sudo`).

### Arch Linux

```bash
cd arch && makepkg -si
```
(An [AUR](https://aur.archlinux.org) package can be added on request.)

### From source (development)

```bash
python3 volume_booster.py
```

## Usage

```bash
volume-booster          # start (also appears in your app menu)
```
To run it automatically at login, add a copy of
`packaging/volume-booster.desktop` to `~/.config/autostart/`.

## Uninstall

```bash
./uninstall.sh                      # if installed via install.sh
sudo apt remove volume-booster      # if installed via .deb
```

## Development

```bash
make install    # portable install
make deb        # build the .deb
```
The whole app is one file (`volume_booster.py`) with no runtime dependencies
beyond Python + PyQt6 + pactl.

## License

MIT — see [LICENSE](LICENSE).
