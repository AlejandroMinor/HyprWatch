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
| `--interval` | `2.0` | Seconds between captures |
| `--threshold` | `5.0` | % change required to notify |
| `--noise` | `10` | Per-pixel noise tolerance |

## Example

```bash
python hyprwatch.py --monitor DP-1 --interval 3 --threshold 10
```

## How to find your monitor name

On Hyprland:
```bash
hyprctl monitors
```

On other Wayland compositors, `hyprctl` won't be available — use the equivalent tool for your compositor (e.g. `wlr-randr`, `swaymsg -t get_outputs`, etc.).
