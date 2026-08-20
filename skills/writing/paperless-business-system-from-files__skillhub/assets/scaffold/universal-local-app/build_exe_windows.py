from __future__ import annotations
import subprocess, sys
raise SystemExit(subprocess.call([sys.executable,'-m','PyInstaller','--clean','app.spec']))
