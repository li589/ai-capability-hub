# -*- coding: utf-8 -*-
import os, sys

BASE = r"d:\Skill Library\Thesis Tutor v4.0"
OUT = os.path.join(BASE, "knowledge_base", "es", "specialized")
os.makedirs(OUT, exist_ok=True)

def w(name, content):
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
        f.write(content)
    print(f"OK: {name}", file=sys.stderr)

translations = {}
