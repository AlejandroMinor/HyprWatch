import subprocess
import shlex
import time
import argparse
import logging
import json
import sys
import os
from PIL import Image
import numpy as np
from logger import setup_logging

TEMP_DIR = "/tmp/hyprwatch/"
PREV_PATH = f"{TEMP_DIR}hyprwatch_1.png"
CURR_PATH = f"{TEMP_DIR}hyprwatch_2.png"
PROJECT_TITLE = "Hyprwatch - Screen Change Monitor for Hyprland"

log = logging.getLogger(__name__)

def capture_image(monitor: str | None, area: str | None, output: str) -> None:
    cmd = ["grim"]
    if area:
        cmd += ["-g", area]
    elif monitor:
        cmd += ["-o", monitor]
    cmd.append(output)
    result = subprocess.run(cmd, capture_output=True)
    if result.returncode != 0:
        log.error(f"Error capturing screen: {result.stderr.decode()}")
        sys.exit(1)


def compare_array(prev_frame: np.ndarray, curr_frame: np.ndarray, noise: int) -> float:
    diff = np.abs(prev_frame.astype(int) - curr_frame.astype(int))
    return np.any(diff > noise, axis=-1).mean() * 100


def convert_image_to_array(image_path: str) -> np.ndarray:
    return np.array(Image.open(image_path))


def run_action(command: str | None, message: str) -> None:
    if command:
        subprocess.run(shlex.split(command))
    else:
        subprocess.run(["notify-send", "hyprwatch", message])


def select_area() -> str:
    result = subprocess.run(["slurp"], capture_output=True)
    if result.returncode != 0 or not result.stdout:
        print("No area selected.")
        sys.exit(0)
    return result.stdout.decode().strip()


def log_startup(args: argparse.Namespace) -> None:
    log.info(PROJECT_TITLE)
    log.debug(f"Monitor    : {args.monitor}")
    if args.area:
        log.debug(f"Area       : {args.area}")
    log.debug(f"Interval   : {args.interval}s")
    log.debug(f"Max alerts : {args.max_alerts if args.max_alerts > 0 else 'unlimited'}")
    log.debug(f"Cooldown   : {args.cooldown}s")
    if args.on_stable:
        log.debug(f"Interval   : {args.stable_interval}s (stable)")
        log.debug(f"Threshold  : {args.stable_threshold}% (stable)")
        log.debug(f"Noise      : {args.stable_noise} (stable)")
        log.debug("Starting up — stable mode...")
    else:
        log.debug(f"Threshold  : {args.threshold}%")
        log.debug(f"Noise      : {args.noise}")
        log.debug("Starting up — capturing baseline frame...")


def define_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=PROJECT_TITLE)
    parser.add_argument("--monitor", default=None, help="Monitor name (default: interactive picker)")
    parser.add_argument("--area", nargs="?", const="", default=None, dest="area", help="Area to capture as 'x,y wxh' — omit value to pick interactively with slurp")
    parser.add_argument("--interval", type=float, default=5.0, help="Seconds between checks (default: 5)")
    parser.add_argument("--threshold", type=float, default=2.0, help="Percentage change to trigger a notification (default: 2)")
    parser.add_argument("--noise", type=int, default=5, help="Pixel change threshold to ignore minor differences (default: 5)")
    parser.add_argument("--on-change", default=None, dest="on_change", help="Command to run on change (default: notify-send)")
    parser.add_argument("--max-alerts", type=int, default=1, dest="max_alerts", help="Max alerts to send, 0 for unlimited (default: 1)")
    parser.add_argument("--cooldown", type=int, default=30, help="Seconds to wait after a change before resuming (default: 30)")
    parser.add_argument("--quiet", action="store_true", help="Suppress all output, only warnings and errors are shown")
    parser.add_argument("--on-stable", nargs="?", const="", default=None, dest="on_stable", help="Enable stable mode — optionally pass a command to run (default: notify-send)")
    parser.add_argument("--stable-interval", type=float, default=5.0, dest="stable_interval", help="Seconds without change required to consider stable (default: 5)")
    parser.add_argument("--stable-threshold", type=float, default=0.05, dest="stable_threshold", help="Max %% change to consider stable (default: 0.05 — tolerates cursor blink)")
    parser.add_argument("--stable-noise", type=int, default=0, dest="stable_noise", help="Per-pixel difference to ignore in stable mode (default: 0 — pixel-perfect)")
    return parser.parse_args()

def get_monitors() -> list[dict]:
    result = subprocess.run(["hyprctl", "monitors", "-j"], capture_output=True)
    if result.returncode != 0:
        log.error(f"Error getting monitors: {result.stderr.decode()}")
        sys.exit(1)
    return json.loads(result.stdout.decode())

def select_monitor(monitors: list[dict]) -> str:
    lines = [f"{m['name']} ({m['model']})" for m in monitors]
    fzf = subprocess.run(
        ["fzf", "--prompt=  Select monitor to watch: ", "--layout=reverse", "--border=none", "--no-info",
         "--header=No monitor specified via --monitor, select one to continue...", "--header-first"],
        input="\n".join(lines).encode(),
        capture_output=True,
    )
    if fzf.returncode != 0 or not fzf.stdout:
        print("No monitor selected.")
        sys.exit(0)
    return fzf.stdout.decode().split()[0]

def max_alerts_reached(alert_count: int, max_alerts: int) -> bool:
    if max_alerts > 0 and alert_count >= max_alerts:
        log.warning(f"Reached max alerts ({max_alerts}).")
        return True
    return False


def wait_cooldown(cooldown: int) -> None:
    if cooldown > 0:
        log.warning(f"Next check in {cooldown}s...")
        time.sleep(cooldown)


def cleanup_temp_files() -> None:
    if os.path.exists(PREV_PATH):
        os.remove(PREV_PATH)
    if os.path.exists(CURR_PATH):
        os.remove(CURR_PATH)


def change_loop(monitor: str | None, area: str | None, max_alerts: int, cooldown: int,
                interval: float, noise: int, threshold: float, on_change: str | None) -> None:
    target = area if area else monitor
    alert_count = 0
    log.debug(f"Starting in {interval}s...")
    time.sleep(interval)
    capture_image(monitor, area, PREV_PATH)
    try:
        while True:
            time.sleep(interval)
            capture_image(monitor, area, CURR_PATH)

            prev_frame = convert_image_to_array(PREV_PATH)
            curr_frame = convert_image_to_array(CURR_PATH)

            diff_pct = compare_array(prev_frame, curr_frame, noise)
            log.debug(f"Change: {diff_pct:.1f}%")

            if diff_pct > threshold:
                log.warning(f"Change detected — {diff_pct:.1f}% on {target}")
                run_action(on_change, f"Detected {diff_pct:.1f}% change on {target}")
                alert_count += 1
                if max_alerts_reached(alert_count, max_alerts):
                    break
                wait_cooldown(cooldown)

    except KeyboardInterrupt:
        log.debug("\nStopped.")
    finally:
        cleanup_temp_files()


def stable_loop(monitor: str | None, area: str | None, max_alerts: int, cooldown: int,
                stable_interval: float, stable_noise: int, stable_threshold: float, on_stable: str | None) -> None:
    target = area if area else monitor
    alert_count = 0
    log.debug(f"Starting in {stable_interval}s...")
    time.sleep(stable_interval)
    try:
        while True:
            capture_image(monitor, area, PREV_PATH)
            log.debug(f"Capturing baseline, next check in {stable_interval}s...")
            time.sleep(stable_interval)
            capture_image(monitor, area, CURR_PATH)

            prev_frame = convert_image_to_array(PREV_PATH)
            curr_frame = convert_image_to_array(CURR_PATH)

            diff_pct = compare_array(prev_frame, curr_frame, stable_noise)
            log.debug(f"Change: {diff_pct:.1f}%")

            if diff_pct <= stable_threshold:
                log.warning(f"Stable detected — no change in {stable_interval}s on {target}")
                run_action(on_stable, f"Screen stable on {target}")
                alert_count += 1
                if max_alerts_reached(alert_count, max_alerts):
                    break
                wait_cooldown(cooldown)

    except KeyboardInterrupt:
        log.debug("\nStopped.")
    finally:
        cleanup_temp_files()


def main() -> None:
    setup_logging()
    os.makedirs(TEMP_DIR, exist_ok=True)
    args = define_args()
    if args.quiet:
        logging.getLogger().setLevel(logging.WARNING)
    if args.area is not None:
        if args.area == "":
            args.area = select_area()
    elif args.monitor is None:
        args.monitor = select_monitor(get_monitors())
    log_startup(args)
    log.info("Monitoring... (Ctrl+C to stop)\n")

    if args.on_stable is not None:
        stable_loop(args.monitor, args.area, args.max_alerts, args.cooldown, args.stable_interval, args.stable_noise, args.stable_threshold, args.on_stable or None)
    else:
        change_loop(args.monitor, args.area, args.max_alerts, args.cooldown, args.interval, args.noise, args.threshold, args.on_change)


if __name__ == "__main__":
    main()
