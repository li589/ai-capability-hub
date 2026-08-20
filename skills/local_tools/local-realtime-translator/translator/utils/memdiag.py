"""Lightweight memory diagnostics for locating the pipeline's RAM footprint.

Toggle on with the env var ``RT_MEMDIAG=1``. When off, every call here is a
cheap no-op so it can be left wired into the hot paths without cost.

Two things are tracked:
  * Process RSS (resident set size) — the actual physical RAM the Python
    process holds. On an Intel iGPU (UMA) this also reflects OpenVINO's
    "GPU" allocations, since integrated graphics share system memory.
  * A labelled timeline: ``stamp("after X")`` prints RSS now and the delta
    since the previous stamp, so you can see exactly which load step or which
    runtime event adds memory — and whether RSS keeps climbing (a leak) or
    plateaus (just a large static footprint).
"""

from __future__ import annotations

import os
import sys
import threading
import time

_ENABLED = os.environ.get("RT_MEMDIAG", "") not in ("", "0", "false", "False")
_LOCK = threading.Lock()
_LAST_RSS = None
_PEAK_RSS = 0
_START_TS = None

try:
    import psutil  # noqa: F401
    _HAVE_PSUTIL = True
except Exception:
    _HAVE_PSUTIL = False


def enabled() -> bool:
    return _ENABLED


def _rss_bytes() -> int:
    if _HAVE_PSUTIL:
        import psutil
        return psutil.Process().memory_info().rss
    return 0


def _sys_mem():
    if _HAVE_PSUTIL:
        import psutil
        vm = psutil.virtual_memory()
        return vm.used, vm.total
    return 0, 0


def _fmt_gb(n: int) -> str:
    return f"{n / (1024 ** 3):6.2f}GB"


def stamp(label: str) -> None:
    """Print current RSS and the delta since the previous stamp."""
    if not _ENABLED:
        return
    global _LAST_RSS, _PEAK_RSS, _START_TS
    with _LOCK:
        rss = _rss_bytes()
        _PEAK_RSS = max(_PEAK_RSS, rss)
        if _START_TS is None:
            _START_TS = time.time()
        elapsed = time.time() - _START_TS
        delta = 0 if _LAST_RSS is None else rss - _LAST_RSS
        _LAST_RSS = rss
        used, total = _sys_mem()
        sign = "+" if delta >= 0 else "-"
        msg = (
            f"[MEMDIAG t={elapsed:6.1f}s] RSS={_fmt_gb(rss)} "
            f"(d={sign}{_fmt_gb(abs(delta)).strip()})  "
            f"peak={_fmt_gb(_PEAK_RSS)}  "
            f"sys_used={_fmt_gb(used)}/{_fmt_gb(total)}  | {label}"
        )
        print(msg, file=sys.stderr, flush=True)


def sample(label: str = "tick") -> None:
    """Alias for periodic runtime sampling (same as stamp)."""
    stamp(label)
