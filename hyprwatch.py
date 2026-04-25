import subprocess
import time
import argparse
import sys
import os
from PIL import Image
import numpy as np

TEMP_DIR = "/tmp/hyprwatch/"
PROJECT_TITLE = "Hyprwatch - Screen Change Monitor for Hyprland"


def capture_image(monitor: str, output: str):
    result = subprocess.run(
        ["grim", "-o", monitor, output],
        capture_output=True
    )
    if result.returncode != 0:
        print(f"Error capturing screen: {result.stderr.decode()}")
        sys.exit(1)


def compare_array(prev_frame: np.ndarray, curr_frame: np.ndarray, noise: int) -> float:
    diff = np.abs(prev_frame.astype(int) - curr_frame.astype(int))
    return np.any(diff > noise, axis=-1).mean() * 100


def convert_image_to_array(image_path: str) -> np.ndarray:
    return np.array(Image.open(image_path))

def system_notify(message: str):
    subprocess.run(["notify-send", "hyprwatch", message])


def main():
    os.makedirs(TEMP_DIR, exist_ok=True)

    parser = argparse.ArgumentParser(description=PROJECT_TITLE)
    parser.add_argument("--monitor", default="DP-1", help="Monitor name (default: DP-1)")
    parser.add_argument("--interval", type=float, default=2.0, help="Seconds between checks (default: 2)")
    parser.add_argument("--threshold", type=float, default=5.0, help="Percentage change to trigger a notification (default: 5)")
    parser.add_argument("--noise", type=int, default=10, help="Pixel change threshold to ignore minor differences (default: 10)")
    args = parser.parse_args()

    prev_path = f"{TEMP_DIR}hyprwatch_1.png"
    curr_path = f"{TEMP_DIR}hyprwatch_2.png"

    print("─" * 32)
    print(PROJECT_TITLE)
    print("─" * 32)
    print(f"Monitor   : {args.monitor}")
    print(f"Interval  : {args.interval}s")
    print(f"Threshold : {args.threshold}%")
    print(f"Noise     : {args.noise}")
    print("─" * 32)
    print("Starting up — capturing baseline frame...")

    capture_image(args.monitor, prev_path)
    print("Monitoring... (Ctrl+C to stop)\n")

    try:
        while True:
            time.sleep(args.interval)
            capture_image(args.monitor, curr_path)

            prev_frame = convert_image_to_array(prev_path)
            curr_frame = convert_image_to_array(curr_path)

            diff_pct = compare_array(prev_frame, curr_frame, args.noise)
            print(f"Change: {diff_pct:.1f}%")

            if diff_pct > args.threshold:
                # system_notify(f"Detected {diff_pct:.1f}% change on {args.monitor}")
                print(f"[ALERT] Detected {diff_pct:.1f}% change on {args.monitor}")

            # The actual frame replacement happens here, after the comparison
            #os.replace(curr_path, prev_path)

    except KeyboardInterrupt:
        print("\nStopped.")
        # Cleanup temporary files
        if os.path.exists(prev_path):
            os.remove(prev_path)
        if os.path.exists(curr_path):
            os.remove(curr_path)


if __name__ == "__main__":
    main()