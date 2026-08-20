# -*- coding: utf-8 -*-
import os, base64

BASE = r"d:\Skill Library\Thesis Tutor v4.0"
OUT = os.path.join(BASE, "knowledge_base", "es", "specialized")
os.makedirs(OUT, exist_ok=True)

def w(name, b64):
    content = base64.b64decode(b64).decode("utf-8")
    path = os.path.join(OUT, name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"OK: {name} ({len(content)} chars)")

