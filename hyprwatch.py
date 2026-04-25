import subprocess
import time
import argparse
import sys
import os
from PIL import Image
import numpy as np

TEMP_DIR = "/tmp/hyprwatch/"


def capture_image(monitor: str, output: str):
    result = subprocess.run(
        ["grim", "-o", monitor, output],
        capture_output=True
    )
    if result.returncode != 0:
        print(f"Error capturing screen: {result.stderr.decode()}")
        sys.exit(1)


def compare_array(array1: str, array2: str, noise: int) -> float:
    diff = np.abs(array1.astype(int) - array2.astype(int))
    return np.any(diff > noise, axis=-1).mean() * 100


def convert_image_to_array(image_path: str) -> np.ndarray:
    return np.array(Image.open(image_path))

def system_notify(message: str):
    subprocess.run(["notify-send", "hyprwatch", message])


def main():
    os.makedirs(TEMP_DIR, exist_ok=True)

    parser = argparse.ArgumentParser(description="hyprwatch - Screen change monitor for Hyprland")
    parser.add_argument("--monitor", default="DP-1", help="Monitor name (default: DP-1)")
    parser.add_argument("--interval", type=float, default=2.0, help="Seconds between checks (default: 2)")
    parser.add_argument("--threshold", type=float, default=5.0, help="%% percentage change to trigger notification (default: 5)")
    parser.add_argument("--noise", type=int, default=10, help="Pixel change threshold to ignore minor differences (default: 10)")
    args = parser.parse_args()

    frame1 = f"{TEMP_DIR}hyprwatch_1.png"
    frame2 = f"{TEMP_DIR}hyprwatch_2.png"

    print(f"Monitor : {args.monitor}")
    print(f"Interval : {args.interval}s")
    print(f"Threshold : {args.threshold}%")
    print(f"Noise : {args.noise}")
    print("Creating initial capture...")

    capture_image(args.monitor, frame1)
    print("Starting up — capturing baseline frame...")

    try:
        while True:
            time.sleep(args.interval)
            capture_image(args.monitor, frame2)

            array1 = convert_image_to_array(frame1)
            array2 = convert_image_to_array(frame2)

            change = compare_array(array1, array2, args.noise)
            print(f"Change detected: {change:.1f}%")

            if change > args.threshold:
                # notify(f"Detected {change:.1f}% change on {args.monitor}")
                print(f"[ALERT] Detected {change:.1f}% change on {args.monitor}")

            # The actual frame replacement happens here, after the comparison
            #os.replace(frame2, frame1)

    except KeyboardInterrupt:
        print("\nDetenido.")
        # Cleanup temporary files
        if os.path.exists(frame1):
            os.remove(frame1)
        if os.path.exists(frame2):
            os.remove(frame2)


if __name__ == "__main__":
    main()