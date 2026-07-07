#!/usr/bin/env python3
"""
patch_ear3_images.py — swap Ear (2) product photos for Ear (3) in the UI.

App ships no Ear (3) renders. You supply 4 transparent PNGs, script rewires
all references on the dee8c0 route (main window, tray, device list, gesture
page).

STEP 1 — put these 4 files into res/assets/ (exact names):
    ear_three_white_left.png     single left bud
    ear_three_white_right.png    single right bud
    ear_three_white_case.png     open case
    ear_three_white_duo.png      both buds

  Source: nothing.tech Ear (3) product page / press images. Transparent
  background PNG. Size free — CSS scales. Black-variant renders fine too,
  keep the file names above (only the white slot is routed).

STEP 2 — run from ear-pc root:
    py -3.11 patch_ear3_images.py

Idempotent. .bak backups on first run. Rerun after replacing images = no-op
(paths already rewired; images load by name).
"""
import os
import shutil
import sys

ASSETS = os.path.join("res", "assets")
NEED = [
    "ear_three_white_left.png",
    "ear_three_white_right.png",
    "ear_three_white_case.png",
    "ear_three_white_duo.png",
]

# file -> list of (old, new) replacements
EDITS = {
    os.path.join("res", "js", "control.js"): [
        ('../assets/ear_two_white_left.png',  '../assets/ear_three_white_left.png'),
        ('../assets/ear_two_white_case.png',  '../assets/ear_three_white_case.png'),
        ('../assets/ear_two_white_right.png', '../assets/ear_three_white_right.png'),
        ('../assets/ear_two_white_duo.png',   '../assets/ear_three_white_duo.png'),
    ],
    os.path.join("res", "js", "two.js"): [
        ('../assets/ear_two_white_left.png',  '../assets/ear_three_white_left.png'),
        ('../assets/ear_two_white_right.png', '../assets/ear_three_white_right.png'),
    ],
}


def backup(path):
    bak = path + ".bak"
    if not os.path.exists(bak):
        shutil.copy2(path, bak)
        print(f"  backup: {bak}")


def main():
    if not os.path.exists("main.pyc"):
        sys.exit("main.pyc not found — run from ear-pc root directory")

    missing = [f for f in NEED if not os.path.exists(os.path.join(ASSETS, f))]
    if missing:
        print("Missing image files in res/assets/:")
        for f in missing:
            print(f"  {f}")
        print("\nGet Ear (3) renders (transparent PNG) from nothing.tech "
              "product page or press kit, save with names above, rerun.")
        sys.exit(1)

    for path, pairs in EDITS.items():
        if not os.path.exists(path):
            print(f"WARN: {path} not found, skipped")
            continue
        txt = open(path, encoding="utf-8").read()
        new = txt
        for old, repl in pairs:
            new = new.replace(old, repl)
        if new != txt:
            backup(path)
            open(path, "w", encoding="utf-8").write(new)
            print(f"patched: {path}")
        else:
            print(f"already patched: {path}")

    print("\nDone. Restart app (run_ear3.bat) — Ear (3) images live.")


if __name__ == "__main__":
    main()
