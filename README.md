# hyprwatch

Screen change monitor built for Hyprland on Arch Linux.
Detects when something changes on your screen and sends a desktop notification — ideal for waiting on long-running processes.

> **Note:** hyprwatch is designed for Arch Linux + Hyprland. Using it on other distros is possible, but you'll need to handle dependencies and monitor names differently — see the relevant sections below.

## System dependencies

### Arch Linux (recommended)
```bash
sudo pacman -S python-pillow python-numpy grim libnotify
```

### Other distros
You'll need to install the equivalent packages using your distro's package manager or pip. `grim` and `libnotify` are Wayland tools — availability may vary.
```bash
pip install Pillow numpy
# install grim and libnotify according to your distro
```

## Usage

```bash
python hyprwatch.py --monitor DP-1
```

## Options

| Argument | Default | Description |
|---|---|---|
| `--monitor` | `DP-1` | Monitor name |
| `--interval` | `2.0` | Seconds between checks |
| `--threshold` | `5.0` | Percentage change to trigger an alert |
| `--noise` | `10` | Per-pixel difference to ignore (reduces false positives) |
| `--on-change` | *(notify-send)* | Command to run when a change is detected |
| `--max-alerts` | `3` | Max alerts before stopping, `0` for unlimited |
| `--cooldown` | `30` | Seconds to wait after an alert before resuming |

## Examples

Basic usage:
```bash
python hyprwatch.py --monitor DP-1
```

Run a custom command on change:
```bash
python hyprwatch.py --monitor DP-1 --on-change "paplay /usr/share/sounds/bell.wav"
```

Send up to 5 alerts with a 60s cooldown between them:
```bash
python hyprwatch.py --monitor DP-1 --max-alerts 5 --cooldown 60
```

## How to find your monitor name

On Hyprland:
```bash
hyprctl monitors
```

On other Wayland compositors, `hyprctl` won't be available — use the equivalent tool for your compositor (e.g. `wlr-randr`, `swaymsg -t get_outputs`, etc.).
