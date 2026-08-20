# -*- coding: utf-8 -*-
import sys, base64, os
OUT = r"d:\Skill Library\Thesis Tutor v4.0\knowledge_base\es\specialized"
os.makedirs(OUT, exist_ok=True)
for line in sys.stdin:
    line = line.strip()
    if not line or line == "END":
        continue
    parts = line.split("|", 1)
    if len(parts) == 2:
        fname = parts[0].strip()
        b64 = parts[1].strip()
        content = base64.b64decode(b64).decode("utf-8")
        path = os.path.join(OUT, fname)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"OK: {fname} ({len(content)} chars)")
