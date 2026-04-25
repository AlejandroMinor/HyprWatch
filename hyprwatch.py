import subprocess
import shlex
import time
import argparse
import sys
import os
from PIL import Image
import numpy as np

TEMP_DIR = "/tmp/hyprwatch/"
PREV_PATH = f"{TEMP_DIR}hyprwatch_1.png"
CURR_PATH = f"{TEMP_DIR}hyprwatch_2.png"
PROJECT_TITLE = "Hyprwatch - Screen Change Monitor for Hyprland"

RESET  = "\033[0m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
RED    = "\033[31m"
GREEN  = "\033[32m"
YELLOW = "\033[33m"
CYAN   = "\033[36m"


def capture_image(monitor: str, output: str):
    result = subprocess.run(
        ["grim", "-o", monitor, output],
        capture_output=True
    )
    if result.returncode != 0:
        print(f"{RED}Error capturing screen: {result.stderr.decode()}{RESET}")
        sys.exit(1)


def compare_array(prev_frame: np.ndarray, curr_frame: np.ndarray, noise: int) -> float:
    diff = np.abs(prev_frame.astype(int) - curr_frame.astype(int))
    return np.any(diff > noise, axis=-1).mean() * 100


def convert_image_to_array(image_path: str) -> np.ndarray:
    return np.array(Image.open(image_path))


def run_on_change(command: str | None, diff_pct: float, monitor: str):
    if command:
        subprocess.run(shlex.split(command))
    else:
        subprocess.run(["notify-send", "hyprwatch", f"Detected {diff_pct:.1f}% change on {monitor}"])


def print_startup(args):
    print(f"{CYAN}{'─' * 32}{RESET}")
    print(f"{BOLD}{PROJECT_TITLE}{RESET}")
    print(f"{CYAN}{'─' * 32}{RESET}")
    print(f"{DIM}Monitor    :{RESET} {args.monitor}")
    print(f"{DIM}Interval   :{RESET} {args.interval}s")
    print(f"{DIM}Threshold  :{RESET} {args.threshold}%")
    print(f"{DIM}Noise      :{RESET} {args.noise}")
    print(f"{DIM}Max alerts :{RESET} {args.max_alerts if args.max_alerts > 0 else 'unlimited'}")
    print(f"{DIM}Cooldown   :{RESET} {args.cooldown}s")
    print(f"{CYAN}{'─' * 32}{RESET}")
    print(f"{DIM}Starting up — capturing baseline frame...{RESET}")

def define_args():
    parser = argparse.ArgumentParser(description=PROJECT_TITLE)
    parser.add_argument("--monitor", default="DP-1", help="Monitor name (default: DP-1)")
    parser.add_argument("--interval", type=float, default=2.0, help="Seconds between checks (default: 2)")
    parser.add_argument("--threshold", type=float, default=5.0, help="Percentage change to trigger a notification (default: 5)")
    parser.add_argument("--noise", type=int, default=10, help="Pixel change threshold to ignore minor differences (default: 10)")
    parser.add_argument("--on-change", default=None, dest="on_change", help="Command to run on change (default: notify-send)")
    parser.add_argument("--max-alerts", type=int, default=3, dest="max_alerts", help="Max alerts to send, 0 for unlimited (default: 3)")
    parser.add_argument("--cooldown", type=int, default=30, help="Seconds to wait after a change before resuming (default: 30)")
    return parser.parse_args()

def main():
    os.makedirs(TEMP_DIR, exist_ok=True)
    args = define_args()
    print_startup(args)

    capture_image(args.monitor, PREV_PATH)
    print(f"{GREEN}Monitoring...{RESET} {DIM}(Ctrl+C to stop){RESET}\n")

    alert_count = 0

    try:
        while True:
            time.sleep(args.interval)
            capture_image(args.monitor, CURR_PATH)

            prev_frame = convert_image_to_array(PREV_PATH)
            curr_frame = convert_image_to_array(CURR_PATH)

            diff_pct = compare_array(prev_frame, curr_frame, args.noise)
            print(f"{DIM}Change: {diff_pct:.1f}%{RESET}")

            if diff_pct > args.threshold:
                print(f"{RED}{BOLD}[ALERT]{RESET} Change detected — {diff_pct:.1f}% on {args.monitor}")
                run_on_change(args.on_change, diff_pct, args.monitor)
                alert_count += 1
                if args.max_alerts > 0 and alert_count >= args.max_alerts:
                    print(f"{YELLOW}Reached max alerts ({args.max_alerts}). Stopping.{RESET}")
                    break
                if args.cooldown > 0:
                    print(f"{DIM}Next check in {args.cooldown}s...{RESET}")
                    time.sleep(args.cooldown)


    except KeyboardInterrupt:
        print(f"\n{DIM}Stopped.{RESET}")
        if os.path.exists(PREV_PATH):
            os.remove(PREV_PATH)
        if os.path.exists(CURR_PATH):
            os.remove(CURR_PATH)


if __name__ == "__main__":
    main()
