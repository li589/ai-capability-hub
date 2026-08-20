"""test_skill_metadata.py — Skill 元数据完整性测试

确保 SKILL.md / _meta.json / .skillhub.json / .claude-plugin/plugin.json
- 版本号一致
- 描述信息一致
- 关键字段齐全
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_skill_md_exists():
    assert (ROOT / "SKILL.md").exists()


def test_meta_json_exists():
    assert (ROOT / "_meta.json").exists()


def test_skillhub_json_exists():
    assert (ROOT / ".skillhub.json").exists()


def test_plugin_json_exists():
    assert (ROOT / ".claude-plugin" / "plugin.json").exists()


def test_pyproject_exists():
    assert (ROOT / "pyproject.toml").exists()


def _read_version(path: Path, pattern: str) -> str:
    src = path.read_text(encoding="utf-8")
    m = re.search(pattern, src)
    assert m, f"{path}: version not found with pattern {pattern}"
    return m.group(1)


def test_versions_consistent():
    """所有版本号必须一致"""
    # 注意 SKILL.md frontmatter 是 YAML "key: value" 形式
    skill_md = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    fm = skill_md.split("---")[1]
    m = re.search(r"^version:\s*([\d.]+)", fm, re.MULTILINE)
    assert m, "SKILL.md frontmatter 缺 version 字段"
    versions = {"SKILL.md": m.group(1)}

    sources_json = [
        (ROOT / "_meta.json", re.compile(r'"version":\s*"([\d.]+)"')),
        (ROOT / ".skillhub.json", re.compile(r'"version":\s*"([\d.]+)"')),
        (ROOT / ".claude-plugin" / "plugin.json", re.compile(r'"version":\s*"([\d.]+)"')),
    ]
    for p, pat in sources_json:
        text = p.read_text(encoding="utf-8")
        mm = pat.search(text)
        assert mm, f"{p} 缺 version 字段"
        versions[str(p.relative_to(ROOT))] = mm.group(1)

    # pyproject.toml
    pp = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    m2 = re.search(r'version\s*=\s*"([\d.]+)"', pp)
    assert m2, "pyproject.toml 缺 version"
    versions["pyproject.toml"] = m2.group(1)

    unique = set(versions.values())
    assert len(unique) == 1, f"版本号不一致: {versions}"


def test_skill_md_no_emoji():
    """SKILL.md frontmatter 不应包含 emoji。

    正文中的 🟢🟡🔴🔵 等为报告模板的状态语义图标（设计如此，自 v6 起），
    故仅约束 frontmatter 元信息保持纯文本。
    """
    src = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    fm = src.split("---")[1]
    emojis = re.findall(r"[\U0001F300-\U0001FAFF\U00002600-\U000027BF\u2700-\u27BF\u2B00-\u2BFF]", fm)
    assert not emojis, f"SKILL.md frontmatter 含 {len(emojis)} 个 emoji: {emojis[:10]}"


def test_skill_md_has_frontmatter():
    """SKILL.md 必须有 YAML frontmatter"""
    src = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    assert src.startswith("---\n"), "SKILL.md 必须以 --- 开头"
    assert "\n---\n" in src, "SKILL.md frontmatter 未正确关闭"


def test_skill_md_required_fields():
    """SKILL.md 必填字段"""
    src = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    # 提取 frontmatter
    fm = src.split("---")[1]
    for field in ["name:", "version:", "description:", "triggers:"]:
        assert field in fm, f"SKILL.md 缺字段: {field}"


def test_meta_json_valid():
    """_meta.json 必须合法 JSON"""
    with open(ROOT / "_meta.json", encoding="utf-8") as f:
        data = json.load(f)
    for key in ["name", "version", "description", "tags", "features"]:
        assert key in data, f"_meta.json 缺字段: {key}"


def test_skillhub_json_valid():
    """skillhub.json 必须合法"""
    with open(ROOT / ".skillhub.json", encoding="utf-8") as f:
        data = json.load(f)
    for key in ["name", "version", "description", "tags"]:
        assert key in data, f".skillhub.json 缺字段: {key}"


def test_manager_count_claim():
    """description 中说的经理人数应与真实数据匹配（占位骨架时跳过）"""
    with open(ROOT / "_meta.json", encoding="utf-8") as f:
        meta = json.load(f)
    managers_file = ROOT / "data" / "fund_managers_distilled.json"
    if managers_file.exists():
        with open(managers_file, encoding="utf-8") as f:
            data = json.load(f)
        # 占位骨架：空列存 _f=[] 且无 c 数据，说明数据未初始化（轻量化），跳过比对
        if isinstance(data.get("_f"), list) and not data.get("c"):
            return
        # 支持两种列式格式 + 标准格式
        if isinstance(data.get("_f"), list):
            # 新版列存：{"_f":[列名],"c":[列数组...]}，按唯一 manager_id 计数
            actual = len(set(data["c"][0])) if data.get("c") else 0
        elif data.get("_f") == "c":
            # 旧版行式：{"_f":"c","c":[列名],"d":[行...]}
            actual = len(data.get("d", []))
        else:
            actual = len(data.get("managers", data.get("items", [])))
        # _meta.json 至少要提一句，不能虚报
        if "databaseStats" in meta:
            assert meta["databaseStats"].get("fundManagers") == actual, \
                f"_meta.json databaseStats.fundManagers={meta['databaseStats'].get('fundManagers')} 实际={actual}"


def test_all_init_py_present():
    """scripts/ 下每个子目录都应有 __init__.py"""
    scripts = ROOT / "scripts"
    for d in scripts.iterdir():
        if d.is_dir() and d.name != "__pycache__":
            init = d / "__init__.py"
            assert init.exists(), f"缺 __init__.py: {init}"
