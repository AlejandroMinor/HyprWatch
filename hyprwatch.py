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

def capture_image(monitor: str, output: str) -> None:
    result = subprocess.run(
        ["grim", "-o", monitor, output],
        capture_output=True
    )
    if result.returncode != 0:
        log.error(f"Error capturing screen: {result.stderr.decode()}")
        sys.exit(1)


def compare_array(prev_frame: np.ndarray, curr_frame: np.ndarray, noise: int) -> float:
    diff = np.abs(prev_frame.astype(int) - curr_frame.astype(int))
    return np.any(diff > noise, axis=-1).mean() * 100


def convert_image_to_array(image_path: str) -> np.ndarray:
    return np.array(Image.open(image_path))


def run_on_change(command: str | None, diff_pct: float, monitor: str) -> None:
    if command:
        subprocess.run(shlex.split(command))
    else:
        subprocess.run(["notify-send", "hyprwatch", f"Detected {diff_pct:.1f}% change on {monitor}"])


def log_startup(args: argparse.Namespace) -> None:
    log.info(PROJECT_TITLE)
    log.debug(f"Monitor    : {args.monitor}")
    log.debug(f"Interval   : {args.interval}s")
    log.debug(f"Threshold  : {args.threshold}%")
    log.debug(f"Noise      : {args.noise}")
    log.debug(f"Max alerts : {args.max_alerts if args.max_alerts > 0 else 'unlimited'}")
    log.debug(f"Cooldown   : {args.cooldown}s")
    log.debug("Starting up — capturing baseline frame...")


def define_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=PROJECT_TITLE)
    parser.add_argument("--monitor", default=None, help="Monitor name (default: interactive picker)")
    parser.add_argument("--interval", type=float, default=2.0, help="Seconds between checks (default: 2)")
    parser.add_argument("--threshold", type=float, default=5.0, help="Percentage change to trigger a notification (default: 5)")
    parser.add_argument("--noise", type=int, default=10, help="Pixel change threshold to ignore minor differences (default: 10)")
    parser.add_argument("--on-change", default=None, dest="on_change", help="Command to run on change (default: notify-send)")
    parser.add_argument("--max-alerts", type=int, default=3, dest="max_alerts", help="Max alerts to send, 0 for unlimited (default: 3)")
    parser.add_argument("--cooldown", type=int, default=30, help="Seconds to wait after a change before resuming (default: 30)")
    parser.add_argument("--quiet", action="store_true", help="Suppress all output, only warnings and errors are shown")
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


def main() -> None:
    setup_logging()
    os.makedirs(TEMP_DIR, exist_ok=True)
    args = define_args()
    if args.quiet:
        logging.getLogger().setLevel(logging.WARNING)
    if args.monitor is None:
        args.monitor = select_monitor(get_monitors())
    log_startup(args)

    capture_image(args.monitor, PREV_PATH)
    log.info("Monitoring... (Ctrl+C to stop)\n")

    alert_count = 0

    try:
        while True:
            time.sleep(args.interval)
            capture_image(args.monitor, CURR_PATH)

            prev_frame = convert_image_to_array(PREV_PATH)
            curr_frame = convert_image_to_array(CURR_PATH)

            diff_pct = compare_array(prev_frame, curr_frame, args.noise)
            log.debug(f"Change: {diff_pct:.1f}%")

            if diff_pct > args.threshold:
                log.warning(f"Change detected — {diff_pct:.1f}% on {args.monitor}")
                run_on_change(args.on_change, diff_pct, args.monitor)
                alert_count += 1
                if args.max_alerts > 0 and alert_count >= args.max_alerts:
                    log.warning(f"Reached max alerts ({args.max_alerts}). Stopping.")
                    break
                if args.cooldown > 0:
                    log.warning(f"Next check in {args.cooldown}s...")
                    time.sleep(args.cooldown)

    except KeyboardInterrupt:
        log.debug("\nStopped.")
        if os.path.exists(PREV_PATH):
            os.remove(PREV_PATH)
        if os.path.exists(CURR_PATH):
            os.remove(CURR_PATH)


if __name__ == "__main__":
    main()
