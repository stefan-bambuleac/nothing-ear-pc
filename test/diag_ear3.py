#!/usr/bin/env python3
"""
diag_ear3.py — find why UI still shows Ear (2), fix what it can.

Checks + auto-fixes:
  1. control.js  dee8c0 name + image refs        -> re-patch if stale
  2. two.js      image refs                       -> re-patch if stale
  3. res/assets  ear_three_white_*.png present    -> report
  4. sqlite DB   rows, model values, trigger      -> remap + recreate trigger
  5. html titles ear (2) -> ear (3)               -> re-patch if stale
  6. electron cache                                -> purge (close app first!)

Run from ear-pc root, app CLOSED:
    py -3.11 diag_ear3.py
Then start app, rescan. Still Ear 2 -> paste full output.
"""
import os
import re
import shutil
import sqlite3
import sys

DB = "devicesndpreferences.db"
KNOWN = ('31d53d', '624011', '1016dd', 'dee8c0', 'acc520')
ASSETS = os.path.join("res", "assets")
NEED = ["ear_three_white_left.png", "ear_three_white_right.png",
        "ear_three_white_case.png", "ear_three_white_duo.png"]
IMG_EDITS = {
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
fixed = []


def wr(path, txt):
    if not os.path.exists(path + ".bak"):
        shutil.copy2(path, path + ".bak")
    open(path, "w", encoding="utf-8").write(txt)


def check_control_js():
    p = os.path.join("res", "js", "control.js")
    if not os.path.exists(p):
        print(f"[1] {p} MISSING — wrong directory?")
        return
    t = open(p, encoding="utf-8").read()
    m = re.search(r'"dee8c0":\s*\{\s*name:\s*"([^"]+)"', t)
    name = m.group(1) if m else "<pattern not found>"
    three = t.count("ear_three_white")
    print(f"[1] control.js: dee8c0 name = {name!r}, ear_three refs = {three}/4")
    changed = False
    if name != "Nothing Ear (3)":
        t = re.sub(r'("dee8c0":\s*\{\s*name:\s*")[^"]+', r"\1Nothing Ear (3)", t)
        changed = True
    if three < 4:
        for old, new in IMG_EDITS[p]:
            t = t.replace(old, new)
        changed = True
    if changed:
        wr(p, t)
        fixed.append("control.js re-patched")


def check_two_js():
    p = os.path.join("res", "js", "two.js")
    if not os.path.exists(p):
        print(f"[2] {p} MISSING")
        return
    t = open(p, encoding="utf-8").read()
    three = t.count("ear_three_white")
    print(f"[2] two.js: ear_three refs = {three}/2")
    if three < 2:
        for old, new in IMG_EDITS[p]:
            t = t.replace(old, new)
        wr(p, t)
        fixed.append("two.js re-patched")


def check_assets():
    missing = [f for f in NEED if not os.path.exists(os.path.join(ASSETS, f))]
    if missing:
        print(f"[3] assets MISSING: {missing} — images will 404/blank")
    else:
        sizes = {f: os.path.getsize(os.path.join(ASSETS, f)) for f in NEED}
        print(f"[3] assets OK: {sizes}")


def check_db():
    if not os.path.exists(DB):
        print(f"[4] {DB} MISSING — never scanned from this dir, or app runs "
              f"from different cwd. run_ear3.bat must cd here.")
        return
    con = sqlite3.connect(DB)
    cur = con.cursor()
    rows = cur.execute("SELECT id, mac, name, model FROM devices").fetchall()
    trig = cur.execute("SELECT name FROM sqlite_master WHERE type='trigger' "
                       "AND name='ear3_model_fix'").fetchone()
    print(f"[4] DB rows: {rows}")
    print(f"    trigger ear3_model_fix: {'PRESENT' if trig else 'MISSING'}")
    n = cur.execute("UPDATE devices SET model='dee8c0' WHERE model NOT IN "
                    "(?,?,?,?,?)", KNOWN).rowcount
    if n:
        fixed.append(f"DB: {n} row(s) remapped -> dee8c0")
    if not trig:
        cur.execute(
            "CREATE TRIGGER ear3_model_fix AFTER INSERT ON devices FOR EACH ROW "
            "WHEN NEW.model NOT IN ('31d53d','624011','1016dd','dee8c0','acc520') "
            "BEGIN UPDATE devices SET model='dee8c0' WHERE id = NEW.id; END")
        fixed.append("DB: trigger recreated")
    con.commit()
    con.close()


def check_titles():
    for p in (os.path.join("res", "MainControl", "MainControl_two.html"),
              os.path.join("res", "tray", "two.html")):
        if not os.path.exists(p):
            print(f"[5] {p} MISSING")
            continue
        t = open(p, encoding="utf-8").read()
        ok = ">ear (3)</div>" in t
        print(f"[5] {p}: title = {'ear (3)' if ok else 'ear (2) STALE'}")
        if not ok and ">ear (2)</div>" in t:
            wr(p, t.replace(">ear (2)</div>", ">ear (3)</div>"))
            fixed.append(f"{p} title re-patched")


def purge_electron_cache():
    appdata = os.environ.get("APPDATA", "")
    purged = []
    for base in ("electron", "ear-pc", "ear (PC)"):
        for sub in ("Cache", "Code Cache", "GPUCache"):
            d = os.path.join(appdata, base, sub)
            if os.path.isdir(d):
                try:
                    shutil.rmtree(d)
                    purged.append(d)
                except OSError as e:
                    print(f"[6] cache LOCKED (app running?): {d} — {e}")
    print(f"[6] electron cache purged: {purged if purged else 'none found'}")


def main():
    if not os.path.exists("main.pyc"):
        sys.exit("main.pyc not found — run from ear-pc root")
    check_control_js()
    check_two_js()
    check_assets()
    check_db()
    check_titles()
    purge_electron_cache()
    print()
    if fixed:
        print("FIXED:", *fixed, sep="\n  ")
    else:
        print("All patches were already in place — cause was cache "
              "(purged above) or app was running old files in memory.")
    print("\nStart app: run_ear3.bat  ->  scan  ->  click device.")


if __name__ == "__main__":
    main()
