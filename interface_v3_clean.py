#!/usr/bin/env python3
"""
interface_v3_clean.py — restore clean v3-style interface.

Removes v8 sledgehammer (function overrides, console line, ?v8/?v=5
cache-busters, [v8]/[v5] markers, whoami.txt). Keeps proper map-based
lookup with dee8c0/acc520 -> Nothing Ear (3) + ear_three images.
DB trigger guarantees model=dee8c0, so map lookup is safe.

Run from ear-pc folder:
    py -3.11 interface_v3_clean.py
Restart via ear-pc.exe.
"""
import os
import re
import sys

if not os.path.exists("main.pyc"):
    sys.exit("run from ear-pc folder (next to main.pyc)")

CJ = os.path.join("res", "js", "control.js")
t = open(CJ, encoding="utf-8").read()

# drop console beacon
t = re.sub(r'^console\.log\("EAR3 BUILD v\d+".*\n\n?', "", t)

# drop injected override returns, keep original bodies underneath
t = re.sub(
    r'function getImageForModel\(modelID\) \{\n'
    r'    return "\.\./assets/ear_three_white_right\.png\?v\d+";\n\n',
    "function getImageForModel(modelID) {\n", t)
t = re.sub(
    r'function getModelInfo\(modelID\) \{\n'
    r'    return \{ name: "Nothing Ear \(3\)",[\s\S]*?isANC: true \};\n\n',
    "function getModelInfo(modelID) {\n", t)
open(CJ, "w", encoding="utf-8").write(t)
print("control.js: overrides removed, map restored")

changed = 0
for dirpath, _, files in os.walk("res"):
    for fn in files:
        if not fn.endswith((".html", ".js")):
            continue
        p = os.path.join(dirpath, fn)
        try:
            s = open(p, encoding="utf-8").read()
        except (UnicodeDecodeError, OSError):
            continue
        n = s
        # strip every cache-buster variant
        n = re.sub(r"\?v=?\d+\b", "", n)
        # strip scanner markers
        n = re.sub(r"Select your device \[v\d+\]", "Select your device", n)
        # re-assert Ear (3) map values (idempotent)
        n = n.replace("Nothing Ear (2)", "Nothing Ear (3)")
        n = n.replace(">ear (2)<", ">ear (3)<")
        for c in ("white", "black"):
            for part in ("left", "right", "case", "duo"):
                n = n.replace(f"../assets/ear_two_{c}_{part}.png",
                              f"../assets/ear_three_white_{part}.png")
        if n != s:
            open(p, "w", encoding="utf-8").write(n)
            changed += 1
            print(f"cleaned: {p}")

w = os.path.join("res", "whoami.txt")
if os.path.exists(w):
    os.remove(w)
    print("removed: res/whoami.txt")

print(f"done, {changed} files touched. Restart via ear-pc.exe.")
