"""Fix Unicode characters in Python files that break Windows cp1252 encoding"""
import os
import re

REPLACEMENTS = {
    "\u2713": "[OK]",      # ✓
    "\u2714": "[OK]",      # ✔
    "\u2718": "[FAIL]",    # ✘
    "\u26a0": "[WARN]",    # ⚠
    "\u2550": "=",         # ═
    "\u2551": "|",         # ║
    "\u2554": "+",         # ╔
    "\u2557": "+",         # ╗
    "\u255a": "+",         # ╚
    "\u255d": "+",         # ╝
    "\u203c": "!!",        # ‼
    "\u2019": "'",         # '
    "\u2018": "'",         # '
    "\u201c": '"',         # "
    "\u201d": '"',         # "
    "\u2014": "--",        # —
    "\u2013": "-",         # –
    "\u00e9": "e",         # é
    "\u20b9": "Rs.",       # ₹ (in Python strings only)
}

fixed = []
for root, dirs, files in os.walk("backend"):
    dirs[:] = [d for d in dirs if d not in ("__pycache__", ".git")]
    for fname in files:
        if not fname.endswith(".py"):
            continue
        fpath = os.path.join(root, fname)
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception:
            continue
        
        new_content = content
        for uni, ascii_rep in REPLACEMENTS.items():
            new_content = new_content.replace(uni, ascii_rep)
        
        if new_content != content:
            with open(fpath, "w", encoding="utf-8") as f:
                f.write(new_content)
            fixed.append(fpath)
            print(f"Fixed: {fpath}")

if not fixed:
    print("No Unicode issues found in backend Python files.")
else:
    print(f"\nFixed {len(fixed)} files.")
