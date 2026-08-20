#!/usr/bin/env python
"""刷新 Obsidian oa：目录分层 + 索引 + Bases + 关联 Canvas。

用法：
  python tools/oa/refresh_vault.py
  python tools/oa/refresh_vault.py --vault "D:/Obsidian/MyVault"
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.oa.config import load_config
from tools.oa.vault_layout import refresh_oa_vault


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--config", default="")
    p.add_argument("--vault", default="", help="Obsidian 库根；默认探测已保存库")
    p.add_argument("--papers-dir", default="", help="默认 Research/Patents")
    args = p.parse_args(argv)

    cfg = load_config(args.config or None)
    vault = args.vault.strip() or None
    if not vault:
        try:
            from tools.patent_reader.shared.common import resolve_obsidian_vault, runtime_config

            resolved = resolve_obsidian_vault()
            if resolved.get("vault") and not resolved.get("needs_user_input"):
                vault = str(resolved["vault"])
            papers = args.papers_dir.strip() or runtime_config().get("papers_dir") or "Research/Patents"
        except Exception:
            papers = args.papers_dir.strip() or "Research/Patents"
    else:
        papers = args.papers_dir.strip() or "Research/Patents"

    result = refresh_oa_vault(cfg=cfg, vault=vault, papers_dir=papers)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
