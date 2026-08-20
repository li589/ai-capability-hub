#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
装前查（zhuangqiancha.com）命令行查询 · WorkBuddy / SkillHub Skill 后端。

- 纯客户端，经 Cloudflare Worker 读公开分片，零 API Key。
- 仅 Python 3 标准库；默认纯文本，不生成图片。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request

DEFAULT_ROOT = "https://s.zhuangqiancha.com/"
DATA_ROOT = os.environ.get("ZQC_DATA_URL", DEFAULT_ROOT).rstrip("/") + "/"
SITE_URL = os.environ.get("ZQC_SITE_URL", "https://www.zhuangqiancha.com").rstrip("/")
CACHE_DIR = os.path.join(tempfile.gettempdir(), "zqc_cache")
CACHE_TTL = 3600

GRADE_LABEL = {
    "red": "高风险",
    "orange": "谨慎",
    "yellow": "观察",
    "green": "未见风险",
    "unknown": "待评估",
}
GRADE_RANK = {"red": 0, "orange": 1, "yellow": 2, "green": 3, "unknown": 4}
SEV_RANK = {"P0": 0, "P1": 1, "P2": 2, None: 9}
BASIS_CN = {"code": "代码实锤", "doc": "文档自述", "doc_combo": "文档高危组合"}

# 与官网详情页「隐私去向」卡一致：真实数据外传类规则
EXFIL_RULES = {
    "R4_sensitive_file_exfil",
    "R5_external_exfil",
    "R8_suspicious_egress",
    "R9_env_credential_send",
}
PRIVACY_CAPS = {"privacy_upload", "cred_access"}
CLASS_CN = {
    "suspicious": "可疑",
    "official_api": "官方",
    "cdn": "CDN",
    "unknown": "未分类",
}

_SKILLHUB_RE = re.compile(
    r"https?://(?:www\.)?skillhub\.cn/skills/([^/\s?#]+)/([^/\s?#]+)",
    re.I,
)
_GITHUB_RE = re.compile(
    r"https?://(?:www\.)?github\.com/([^/\s?#]+)/([^/\s?#]+)",
    re.I,
)


def fnv1a(s: str) -> int:
    h = 0x811C9DC5
    for b in s.encode("utf-8"):
        h ^= b
        h = (h * 0x01000193) & 0xFFFFFFFF
    return h


def shard_of(slug: str) -> int:
    return fnv1a(slug) % 256


def _cache_path(url: str) -> str:
    os.makedirs(CACHE_DIR, exist_ok=True)
    key = hashlib.md5(url.encode("utf-8")).hexdigest()
    return os.path.join(CACHE_DIR, key + ".json")


def fetch_json(url: str, ttl: int = CACHE_TTL):
    cp = _cache_path(url)
    if ttl > 0 and os.path.exists(cp) and (time.time() - os.path.getmtime(cp)) < ttl:
        try:
            with open(cp, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    req = urllib.request.Request(url, headers={"User-Agent": "zqc-cli/1.0.2"})
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            data = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise
    try:
        with open(cp, "w", encoding="utf-8") as f:
            json.dump(data, f)
    except Exception:
        pass
    return data


def _g(tool: dict, *keys, default=None):
    for k in keys:
        if tool.get(k) is not None:
            return tool.get(k)
    return default


def _grade_cn(g) -> str:
    return GRADE_LABEL.get(g, str(g))


def _trunc(s, n=120):
    if s is None:
        return ""
    s = str(s).replace("\n", " ").strip()
    return s if len(s) <= n else s[: n - 1] + "…"


def parse_ref(text: str) -> dict:
    """把用户输入解析为 lookup/search 线索。

    返回 {kind, slug?, keyword?, source_url?, note?}
      kind: slug | search | ambiguous
    """
    raw = (text or "").strip()
    if not raw:
        return {"kind": "ambiguous", "note": "空输入"}

    if raw.startswith("skillhub:") or raw.startswith("github:"):
        return {"kind": "slug", "slug": raw, "source_url": None}

    m = _SKILLHUB_RE.search(raw)
    if m:
        owner, name = m.group(1), m.group(2)
        name = urllib.parse.unquote(name)
        owner = urllib.parse.unquote(owner)
        return {
            "kind": "search",
            "keyword": name,
            "slug_guess": "skillhub:%s" % name,
            "source_url": "https://skillhub.cn/skills/%s/%s" % (owner, name),
            "note": "SkillHub 链接 → 先 search「%s」，再 lookup" % name,
        }

    m = _GITHUB_RE.search(raw)
    if m:
        owner, repo = m.group(1), m.group(2)
        if repo.endswith(".git"):
            repo = repo[:-4]
        slug = "github:%s/%s" % (owner, repo)
        return {
            "kind": "slug",
            "slug": slug,
            "keyword": "%s/%s" % (owner, repo),
            "source_url": "https://github.com/%s/%s" % (owner, repo),
            "note": "GitHub 链接 → lookup %s" % slug,
        }

    # 裸路径 owner/name 且无空格：可能是 github 短写
    if re.match(r"^[\w.-]+/[\w.-]+$", raw) and ":" not in raw:
        return {
            "kind": "slug",
            "slug": "github:%s" % raw,
            "keyword": raw,
            "source_url": None,
            "note": "短写路径，按 github: 尝试",
        }

    return {"kind": "search", "keyword": raw, "source_url": None}


def get_catalog():
    doc = fetch_json(DATA_ROOT + "catalog.json")
    if not doc or not isinstance(doc.get("rows"), list):
        return [], None
    cols = doc.get("cols", [])
    tools = []
    for row in doc["rows"]:
        o = dict(zip(cols, row))
        if o.get("summary") in (None, ""):
            fc = int(o.get("finding_count") or 0)
            o["summary"] = ("命中 %d 条证据" % fc) if fc > 0 else "暂未发现风险信号"
        tools.append(o)
    return tools, doc.get("exported_at")


def get_risk():
    return fetch_json(DATA_ROOT + "risk.json") or {}


def get_tool_detail(slug: str):
    sh = "%03d" % shard_of(slug)
    doc = fetch_json(DATA_ROOT + "tools/%s.json" % sh)
    if not doc:
        return None
    tool = doc.get("tools", {}).get(slug)
    if not tool:
        return None
    return {
        "tool": tool,
        "findings": doc.get("findings", {}).get(slug, []),
        "cve": doc.get("cveFindings", {}).get(slug, []),
        "exported_at": doc.get("exported_at"),
    }


def get_authors():
    doc = fetch_json(DATA_ROOT + "authors.json")
    return (doc.get("authors", []) if doc else []), (doc.get("exported_at") if doc else None)


def get_tool_domains(slug: str):
    """读取 tool_domains.json 中该 slug 的外联摘要。

    全量文件较大：优先读本地缓存；缓存未命中时短超时拉取一次并缓存。
    失败返回 None（隐私段仍可用外传类 findings / capabilities 降级）。
    """
    url = DATA_ROOT + "tool_domains.json"
    cp = _cache_path(url)
    doc = None
    if os.path.exists(cp):
        try:
            with open(cp, "r", encoding="utf-8") as f:
                doc = json.load(f)
        except Exception:
            doc = None
    if doc is None:
        # 冷启动：短超时，避免 lookup 被大文件拖死；成功则写入缓存供后续复用
        req = urllib.request.Request(url, headers={"User-Agent": "zqc-cli/1.0.2"})
        try:
            with urllib.request.urlopen(req, timeout=12) as r:
                doc = json.loads(r.read().decode("utf-8"))
            try:
                os.makedirs(CACHE_DIR, exist_ok=True)
                with open(cp, "w", encoding="utf-8") as f:
                    json.dump(doc, f)
            except Exception:
                pass
        except Exception:
            return None
    if not isinstance(doc, dict):
        return None
    td = doc.get("tool_domains") or {}
    return td.get(slug)


def detail_url(slug: str) -> str:
    return "%s/tool/%s" % (SITE_URL, urllib.parse.quote(str(slug), safe=""))


def _print_detail_link(slug: str | None):
    if not slug:
        return
    print("更多细节：%s" % detail_url(slug))


def _owasp_tags(finding: dict) -> list:
    raw = _g(finding, "owasp_category", default="") or ""
    return [s.strip() for s in str(raw).split(",") if s.strip()]


def _print_privacy(findings: list, tool: dict, domains):
    """隐私去向：外传规则命中 +（有则）外联域名摘要。"""
    exfil = [
        f for f in (findings or [])
        if _g(f, "rule_id") in EXFIL_RULES or "MCP04" in _owasp_tags(f)
    ]
    caps = _g(tool, "capabilities") or []
    priv_caps = []
    if isinstance(caps, list):
        for c in caps:
            if not isinstance(c, dict):
                continue
            name = str(c.get("capability") or "")
            if name in PRIVACY_CAPS or name.endswith("exfil") or "privacy" in name:
                priv_caps.append(c)

    print("隐私去向：")
    if domains and int(domains.get("total") or 0) > 0:
        total = int(domains.get("total") or 0)
        sus = int(domains.get("suspicious") or 0)
        off = int(domains.get("official_api") or 0)
        cdn = int(domains.get("cdn") or 0)
        print("  外联域名：共 %d（可疑 %d / 官方 %d / CDN %d）" % (total, sus, off, cdn))
        sample = domains.get("sample") or []
        shown = 0
        for ref in sample:
            if not isinstance(ref, dict):
                continue
            d = ref.get("domain") or ""
            if not d:
                continue
            cls = CLASS_CN.get(str(ref.get("classification") or ""), str(ref.get("classification") or ""))
            print("  - %s（%s）" % (d, cls))
            shown += 1
            if shown >= 5:
                break
        if total > shown:
            print("  …其余见详情页")
    elif exfil or priv_caps:
        print("  未见域名图谱抽样；检出可能涉及数据外传的信号（见下）。")
    else:
        print("  未见外传信号（当前规则与已公开域名摘要下）。")

    if exfil:
        print("  外传类证据 %d 条：" % len(exfil))
        for f in sorted(exfil, key=lambda x: SEV_RANK.get(_g(x, "severity"), 9))[:5]:
            print("  [%s] %s — %s" % (
                _g(f, "severity", default="—"),
                _g(f, "rule_id", default="?"),
                _trunc(_g(f, "evidence", default=""), 80),
            ))
    if priv_caps and not exfil:
        for c in priv_caps[:3]:
            label = c.get("label") or c.get("capability")
            ev = c.get("evidence")
            if isinstance(ev, list):
                ev = ev[0] if ev else ""
            print("  能力：%s — %s" % (label, _trunc(ev, 80)))


def _table(rows, headers):
    cols = list(headers.keys())
    widths = [len(headers[c]) for c in cols]
    str_rows = []
    for r in rows:
        cells = [str(r.get(c, "")) for c in cols]
        str_rows.append(cells)
        for i, c in enumerate(cells):
            widths[i] = max(widths[i], len(c))
    line = "  ".join(headers[c].ljust(widths[i]) for i, c in enumerate(cols))
    out = [line, "-" * len(line)]
    for cells in str_rows:
        out.append("  ".join(cells[i].ljust(widths[i]) for i, c in enumerate(cols)))
    return "\n".join(out)


def _resolve_slug_from_search(keyword: str, limit: int = 8):
    tools, exported_at = get_catalog()
    if not tools:
        return None, [], exported_at
    kw = keyword.lower().strip()
    matched = [
        t
        for t in tools
        if kw in str(_g(t, "name", default="")).lower()
        or kw in str(_g(t, "slug", default="")).lower()
        or kw in str(_g(t, "author", default="")).lower()
    ]
    matched.sort(key=lambda t: int(_g(t, "finding_count", default=0) or 0), reverse=True)
    matched = matched[:limit]
    if len(matched) == 1:
        return _g(matched[0], "slug", default=""), matched, exported_at
    # 精确 name / slug 优先
    for t in matched:
        if str(_g(t, "name", default="")).lower() == kw or str(_g(t, "slug", default="")).lower() == kw:
            return _g(t, "slug", default=""), matched, exported_at
        if str(_g(t, "slug", default="")).lower().endswith(":" + kw):
            return _g(t, "slug", default=""), matched, exported_at
    return None, matched, exported_at


def cmd_search(args):
    ref = parse_ref(args.keyword)
    kw = ref.get("keyword") or args.keyword
    tools, _exported_at = get_catalog()
    if not tools:
        print("无法加载目录数据（请检查网络或 ZQC_DATA_URL）")
        return
    if ref.get("note"):
        print("解析：%s" % ref["note"])
    kl = kw.lower().strip()
    matched = [
        t
        for t in tools
        if kl in str(_g(t, "name", default="")).lower()
        or kl in str(_g(t, "author", default="")).lower()
        or kl in str(_g(t, "source", default="")).lower()
        or kl in str(_g(t, "slug", default="")).lower()
    ]
    if args.grade:
        matched = [t for t in matched if _g(t, "grade") == args.grade]
    matched.sort(key=lambda t: int(_g(t, "finding_count", default=0) or 0), reverse=True)
    matched = matched[: args.limit]
    if not matched:
        print("未找到匹配「%s」的工具。" % kw)
        return
    rows = [
        {
            "slug": _g(t, "slug", default=""),
            "档位": _grade_cn(_g(t, "grade")),
            "工具名": _trunc(_g(t, "name", default=""), 28),
            "作者": _trunc(_g(t, "author", default=""), 16),
            "来源": _g(t, "source", default=""),
            "证据数": str(_g(t, "finding_count", default=0)),
        }
        for t in matched
    ]
    print("匹配 %d 个（按证据数降序，显示前 %d）：" % (len(matched), len(matched)))
    print(_table(rows, {"slug": "slug", "档位": "档位", "工具名": "工具名", "作者": "作者", "来源": "来源", "证据数": "证据数"}))
    print("\n用 `lookup <slug>` 查看评估证据详情。")
    if len(matched) == 1:
        _print_detail_link(_g(matched[0], "slug", default=""))
    else:
        print("更多细节：对命中项用 lookup 后可得装前查详情页链接。")


def cmd_lookup(args):
    ref = parse_ref(args.slug)
    slug = None
    source_hint = ref.get("source_url")

    if ref["kind"] == "slug" and ref.get("slug"):
        slug = ref["slug"]
        d = get_tool_detail(slug)
        if not d and ref.get("keyword"):
            slug2, matched, _exported_at = _resolve_slug_from_search(ref["keyword"])
            if slug2:
                slug = slug2
                d = get_tool_detail(slug)
            elif matched:
                print("未直接命中 %s。相近结果：" % ref.get("slug"))
                for t in matched[:5]:
                    print("  %s  %s  %s" % (_g(t, "slug"), _grade_cn(_g(t, "grade")), _g(t, "name")))
                print("请用准确 slug 再 lookup。")
                return
        elif d:
            pass
        else:
            d = None
    else:
        # search 路径：SkillHub URL 或关键词
        kw = ref.get("keyword") or args.slug
        if ref.get("slug_guess"):
            d = get_tool_detail(ref["slug_guess"])
            if d:
                slug = ref["slug_guess"]
            else:
                d = None
        else:
            d = None
        if not d:
            slug2, matched, _exported_at = _resolve_slug_from_search(kw)
            if slug2:
                slug = slug2
                d = get_tool_detail(slug)
            elif matched:
                print("未唯一命中「%s」。候选：" % kw)
                for t in matched[:8]:
                    print("  %s  %s  %s" % (_g(t, "slug"), _grade_cn(_g(t, "grade")), _g(t, "name")))
                print("请指定 slug 后再 lookup。")
                return
            else:
                print("未收录该工具（输入=%s）。可先用 search 查找。" % args.slug)
                return

    if not d:
        print("未收录该工具（slug=%s）。可先用 search 查找。" % (slug or args.slug))
        return

    t = d["tool"]
    findings = d["findings"] or []
    cve = d["cve"] or []
    slug = slug or _g(t, "slug", default="")
    g = _g(t, "grade", default="unknown")
    print("=" * 60)
    print("工具：%s" % _g(t, "name", default=slug))
    print("slug：%s" % slug)
    print("装前查评级：%s（%s）" % (_grade_cn(g), g))
    basis = _g(t, "grade_evidence_basis")
    if basis:
        print("证据依据：%s" % BASIS_CN.get(str(basis), str(basis)))
    if _g(t, "ungated"):
        print("标记：证据待取证（档位可能尚不完整）")
    print("作者：%s    来源：%s" % (_g(t, "author", default="匿名"), _g(t, "source", default="—")))
    url = _g(t, "source_url") or source_hint
    if url:
        print("来源链接：%s" % url)
    if _g(t, "description"):
        print("简介：%s" % _trunc(_g(t, "description"), 200))
    print("证据数：%s    最高严重度：%s" % (_g(t, "finding_count", default=0), _g(t, "top_severity", default="—")))
    at = _g(t, "author_tools")
    ar = _g(t, "author_reds")
    if at is not None:
        print("作者信誉：共 %s 个工具 · 其中高风险 %s" % (at, ar if ar is not None else "—"))
    if g in ("red", "orange"):
        print("⚠ 该工具被评为「%s」，安装前请确认你接受其权限范围与数据去向。" % _grade_cn(g))
    _print_detail_link(slug)
    print("-" * 60)
    domains = get_tool_domains(slug) if slug else None
    _print_privacy(findings, t, domains)
    print("-" * 60)
    if findings:
        print("评估证据（前 %d 条）：" % min(len(findings), args.limit))
        for f in sorted(findings, key=lambda x: SEV_RANK.get(_g(x, "severity"), 9))[: args.limit]:
            print("  [%s] %s — %s" % (
                _g(f, "severity", default="—"),
                _g(f, "rule_id", default="?"),
                _trunc(_g(f, "evidence", default=""), 100),
            ))
    else:
        print("暂未公开具体证据条目（现有规则下未见命中，或证据尚未公开）。")
    if cve:
        print("-" * 60)
        print("关联 CVE（%d）：" % len(cve))
        for c in cve[: args.limit]:
            print("  %s [%s] %s" % (
                _g(c, "cve_id"), _g(c, "severity", default="?"),
                _trunc(_g(c, "description"), 80),
            ))
    print("=" * 60)
    print("装前查基于公开代码与声明独立评估，结论不构成担保。")


def cmd_risk(args):
    doc = get_risk()
    tools = doc.get("tools", []) if doc else []
    if not tools:
        print("无法加载 risk.json（请检查网络或 ZQC_DATA_URL）。")
        return
    tools = sorted(
        tools,
        key=lambda t: (GRADE_RANK.get(_g(t, "grade"), 9), -int(_g(t, "finding_count", default=0) or 0)),
    )
    tools = tools[: args.limit]
    rows = [
        {
            "档位": _grade_cn(_g(t, "grade")),
            "工具名": _trunc(_g(t, "name", default=""), 30),
            "作者": _trunc(_g(t, "author", default=""), 16),
            "来源": _g(t, "source", default=""),
            "证据数": str(_g(t, "finding_count", default=0)),
            "slug": _g(t, "slug", default=""),
        }
        for t in tools
    ]
    print("装前查「高风险 + 谨慎」Top %d：" % len(tools))
    print(_table(rows, {"档位": "档位", "工具名": "工具名", "作者": "作者", "来源": "来源", "证据数": "证据数", "slug": "slug"}))
    print("更多细节：lookup <slug> → 装前查详情页。")


def cmd_author(args):
    authors, _exported_at = get_authors()
    if not authors:
        print("无法加载 authors.json（请检查网络或 ZQC_DATA_URL）。")
        return
    q = args.query.strip()
    hit = None
    for a in authors:
        if str(_g(a, "id")) == q:
            hit = a
            break
    if not hit:
        ql = q.lower()
        for a in authors:
            if ql in str(_g(a, "display_name", default="")).lower():
                hit = a
                break
    if not hit:
        print("未找到作者「%s」。" % q)
        return
    print("作者：%s（id=%s）" % (_g(hit, "display_name", default="—"), _g(hit, "id")))
    print(
        "工具总数：%s    红：%s  橙：%s  黄：%s  绿：%s"
        % (
            _g(hit, "tool_count", default=0),
            _g(hit, "red_count", default=0),
            _g(hit, "orange_count", default=0),
            _g(hit, "yellow_count", default=0),
            _g(hit, "green_count", default=0),
        )
    )
    if int(_g(hit, "red_count", default=0) or 0) > 0:
        print("⚠ 该作者有 %s 个高风险工具，建议谨慎对待其出品。" % _g(hit, "red_count"))
    aid = _g(hit, "id")
    if aid is not None:
        print("更多细节：%s/author/%s" % (SITE_URL, aid))


def main():
    p = argparse.ArgumentParser(description="装前查 CLI 1.0.2（纯文本）")
    sub = p.add_subparsers(dest="cmd")

    ps = sub.add_parser("search", help="按关键词或 URL 搜索")
    ps.add_argument("keyword", help="搜索词或 SkillHub/GitHub 链接")
    ps.add_argument("--limit", type=int, default=20)
    ps.add_argument("--grade", default=None, help="red/orange/yellow/green")

    pl = sub.add_parser("lookup", help="查看单个工具（支持 slug 或 URL）")
    pl.add_argument("slug", help="slug、SkillHub/GitHub URL 或工具名")
    pl.add_argument("--limit", type=int, default=15)

    pr = sub.add_parser("risk", help="高风险+谨慎 TopN")
    pr.add_argument("--limit", type=int, default=20)

    pa = sub.add_parser("author", help="查作者信誉")
    pa.add_argument("query", help="作者 id 或显示名")

    args = p.parse_args()
    if args.cmd == "search":
        cmd_search(args)
    elif args.cmd == "lookup":
        cmd_lookup(args)
    elif args.cmd == "risk":
        cmd_risk(args)
    elif args.cmd == "author":
        cmd_author(args)
    else:
        p.print_help()


if __name__ == "__main__":
    main()
