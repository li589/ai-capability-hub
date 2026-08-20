from __future__ import annotations

import os
import sys

def resolve_state_dir(app_name: str = "tcop-sre-agents") -> str:
    explicit = os.environ.get("TCOP_SRE_STATE_DIR", "").strip()
    if explicit:
        return os.path.expanduser(explicit)

    xdg_state = os.environ.get("XDG_STATE_HOME", "").strip()
    if xdg_state:
        return os.path.join(os.path.expanduser(xdg_state), app_name)

    if sys.platform == "win32":
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
    else:
        base = os.path.join(os.path.expanduser("~"), ".local", "state")
    return os.path.join(base, app_name)
