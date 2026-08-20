# -*- coding: utf-8 -*-
"""v5.0.0 模块E：文档版本同步测试（SKILL.md / README / _meta.json）"""

import json
import re
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
SKILL_MD = SKILL_DIR / "SKILL.md"
README_MD = SKILL_DIR / "README.md"
META_JSON = SKILL_DIR / "_meta.json"
INIT_PY = SKILL_DIR / "scripts" / "__init__.py"


def _frontmatter(text):
    m = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    assert m, "SKILL.md 缺少 frontmatter"
    return m.group(1)


def test_skill_version_is_700():
    fm = _frontmatter(SKILL_MD.read_text(encoding="utf-8"))
    assert re.search(r"^version:\s*7\.2\.0\s*$", fm, re.MULTILINE), "SKILL version ≠ 7.2.0"


def test_skill_name_present():
    fm = _frontmatter(SKILL_MD.read_text(encoding="utf-8"))
    assert "name: cn-financial-scraper" in fm


def test_skill_line_count_under_450():
    lines = SKILL_MD.read_text(encoding="utf-8").splitlines()
    assert len(lines) <= 450, f"SKILL.md {len(lines)} 行 > 450（精简目标）"


def test_skill_description_concise():
    """description 不再堆叠版本 changelog（应 ≤ 25 行）"""
    fm = _frontmatter(SKILL_MD.read_text(encoding="utf-8"))
    m = re.search(r"description: \|(.*?)(?=auto_trigger)", fm, re.DOTALL)
    assert m, "description 缺失"
    desc_lines = [l for l in m.group(1).splitlines() if l.strip()]
    assert len(desc_lines) <= 25, f"description 过冗长（{len(desc_lines)} 行）"


def test_skill_keeps_auto_trigger():
    fm = _frontmatter(SKILL_MD.read_text(encoding="utf-8"))
    assert "keywords:" in fm, "auto_trigger keywords 缺失"
    assert "patterns:" in fm, "auto_trigger patterns 缺失"
    # 关键触发词保留
    assert "爬取机构" in fm
    assert "舆情爬取" in fm
    assert "东方财富" in fm


def test_skill_no_stale_changelog_blocks():
    """正文无残留 v4.x 长 changelog 块"""
    txt = SKILL_MD.read_text(encoding="utf-8")
    for stale in ["v4.9.0 反爬 + 数据源兜底", "任务清单 — 详细使用指南",
                  "🆕 v4.5.1 三项强化", "🆕 v4.5.0 核心新功能"]:
        assert stale not in txt, f"残留旧章节: {stale}"


def test_readme_version_is_700():
    txt = README_MD.read_text(encoding="utf-8")
    assert "# cn-financial-scraper v7.2.0" in txt, "README 头版本 ≠ v7.2.0"


def test_meta_json_version_valid():
    """_meta.json 版本为合法 semver（平台独立版本体系，与 SKILL 版本解耦）"""
    meta = json.loads(META_JSON.read_text(encoding="utf-8"))
    assert re.match(r"^\d+\.\d+\.\d+$", str(meta["version"])), "version 非 semver"
    assert "slug" in meta
    assert "ownerId" in meta


def test_init_version_is_700():
    txt = INIT_PY.read_text(encoding="utf-8")
    assert "__version__ = '7.2.0'" in txt


def test_all_versions_consistent():
    """SKILL / README / __init__ 三者版本一致（_meta.json 为平台独立 semver）"""
    skill = re.search(r"^version:\s*(7\.2\.0)", _frontmatter(SKILL_MD.read_text(encoding="utf-8")),
                      re.MULTILINE)
    assert skill
    readme = "v7.2.0" in README_MD.read_text(encoding="utf-8")
    init = "__version__ = '7.2.0'" in INIT_PY.read_text(encoding="utf-8")
    assert readme and init


def test_meta_json_valid():
    """_meta.json 合法 JSON"""
    json.loads(META_JSON.read_text(encoding="utf-8"))


def test_requirements_has_akshare():
    txt = (SKILL_DIR / "requirements.txt").read_text(encoding="utf-8")
    assert "akshare" in txt, "requirements.txt 未提及 akshare"
