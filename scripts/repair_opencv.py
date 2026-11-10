"""Repair overlapping cv2 wheel installations without touching model checkpoints."""

import argparse, subprocess, sys
from pathlib import Path

PACKAGES = [
    "opencv-python",
    "opencv-contrib-python",
    "opencv-python-headless",
    "opencv-contrib-python-headless",
]


def repair(uv, python):
    subprocess.run([uv, "pip", "uninstall", "--python", python, *PACKAGES], check=True)
    subprocess.run(
        [
            uv,
            "pip",
            "install",
            "--python",
            python,
            "--no-deps",
            "--reinstall",
            "opencv-contrib-python==4.12.0.88",
        ],
        check=True,
    )
    subprocess.run(
        [python, str(Path(__file__).with_name("check_dependencies.py"))], check=True
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--uv", required=True)
    p.add_argument("--python", default=sys.executable)
    a = p.parse_args()
    repair(a.uv, a.python)
