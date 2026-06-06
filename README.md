# hyprwatch

Screen change monitor built for Hyprland on Arch Linux.
Detects when something changes on your screen and sends a desktop notification — ideal for waiting on long-running processes.

## System dependencies

```bash
sudo pacman -S python-pillow python-numpy grim libnotify fzf slurp
```

## Usage

Run without `--monitor` to get an interactive picker:
```bash
python hyprwatch.py
```

Or pass a monitor name directly to skip the picker:
```bash
python hyprwatch.py --monitor DP-1
```

To watch a specific area, use `--area` without a value to draw the selection interactively (coordinates are absolute):
```bash
python hyprwatch.py --area
```

Or pass the geometry directly:
```bash
python hyprwatch.py --area "100,200 800x600"
```


## Options

| Argument | Default | Description |
|---|---|---|
| `--monitor` | *(interactive picker)* | Monitor name — omit to select from a list |
| `--area` | *(none)* | Area to capture as `x,y wxh` — omit value to draw interactively with slurp. Takes priority over `--monitor` |
| `--interval` | `5.0` | Seconds between checks |
| `--threshold` | `2.0` | Percentage change to trigger an alert |
| `--noise` | `5` | Per-pixel difference to ignore (reduces false positives) |
| `--on-change` | *(notify-send)* | Command to run when a change is detected |
| `--max-alerts` | `1` | Max alerts before stopping, `0` for unlimited |
| `--cooldown` | `30` | Seconds to wait after an alert before resuming |
| `--on-stable` | *(notify-send)* | Enable stable mode — optionally pass a command, omit for notify-send |
| `--stable-interval` | `5.0` | Seconds without change required to consider stable |
| `--stable-threshold` | `0.05` | Max % change to consider stable — tolerates cursor blink, use `0.0` for pixel-perfect |
| `--stable-noise` | `0` | Per-pixel difference to ignore in stable mode — `0` means pixel-perfect |
| `--quiet` | `false` | Suppress all output, only warnings and errors are shown |

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

Alert when the screen has been stable for 5 seconds (e.g. waiting for AI output to finish):
```bash
python hyprwatch.py --monitor DP-1 --on-stable "notify-send hyprwatch 'Done, check your screen'"
```

Override stable sensitivity for a very subtle indicator:
```bash
python hyprwatch.py --monitor DP-1 --on-stable "notify-send hyprwatch done" --stable-interval 3 --stable-threshold 0.1 --stable-noise 2
```


## How to find your monitor name

If you run `hyprwatch.py` without `--monitor`, an interactive fzf menu will show all available monitors with their model names — just select one and press Enter.

To list monitors manually:
```bash
hyprctl monitors
```

---

> Looking for the older version with generic Wayland compositor support? Check out the `v1.0-wayland-generic` tag.
