"""
Cross-file consistency validator for xuanzang-skill.
Catches the class of bugs this project has repeatedly suffered:
  - version drift (SKILL.md vs README vs REFERENCE)
  - ghost references (links to non-existent files)
  - duplicated blocks out of sync (P8 loop in SKILL.md vs role-rulai-pro.md)
  - stale terminology (flavors residue)
  - role-key orphans (listed in switch protocol but missing role-*.md)
"""

import re
import os
import sys
import ast
from pathlib import Path
from typing import List, Tuple, Dict, Set

ROOT = Path(__file__).resolve().parent.parent
REFERENCES = ROOT / "references"
SCRIPTS = ROOT / "scripts"
MD_ROOT = ROOT / ".."

SKILL_MD = ROOT / "SKILL.md"
README_MD = ROOT / "README.md"
REFERENCE_MD = ROOT / "REFERENCE.md"

ROLE_RULAI_PRO = REFERENCES / "role-rulai-pro.md"
ROLE_SWITCH_PROTOCOL = REFERENCES / "role-switch-protocol.md"

FAIL = 0
PASS = 0


def report(ok: bool, msg: str, details: str = ""):
    global PASS, FAIL
    if ok:
        PASS += 1
        print(f"  [PASS] {msg}")
    else:
        FAIL += 1
        print(f"  [FAIL] {msg}" + (f"  → {details}" if details else ""))


def section(text: str):
    print(f"\n{'=' * 60}")
    print(f"  {text}")
    print(f"{'=' * 60}")


def extract_version(path: Path) -> str | None:
    """Extract version string from frontmatter or inline version marker."""
    if not path.exists():
        return None
    content = path.read_text(encoding="utf-8")
    # SKILL.md format: version: "1.0.7"
    m = re.search(r'^version:\s*"([^"]+)"', content, re.MULTILINE)
    if m:
        return m.group(1)
    # README/REFERENCE inline: **版本 1.0.7**
    m = re.search(r'\*\*版本\s+([\d.]+)\*\*', content)
    if m:
        return m.group(1)
    # README/REFERENCE changelog table: | 1.0.7 | 2026-06-16 | ...  (take first row = latest)
    m = re.search(r'^\|\s*(\d+\.\d+\.\d+)\s*\|', content, re.MULTILINE)
    if m:
        return m.group(1)
    # version: 1.0.7 (no quotes)
    m = re.search(r'^version:\s*([\d.]+)', content, re.MULTILINE)
    if m:
        return m.group(1)
    return None


def extract_md_links_nocode(content: str) -> List[Tuple[str, str]]:
    """Extract [text](path) links, skipping content inside fenced code blocks and inline code."""
    # Remove fenced code blocks
    no_code = re.sub(r'```.*?```', '', content, flags=re.DOTALL)
    # Remove inline code spans (backtick-enclosed)
    no_code = re.sub(r'`[^`]+`', '', no_code)
    return [(m.group(1), m.group(2)) for m in
            re.finditer(r'\[([^\]]+)\]\(([^)]+)\)', no_code)]


def extract_code_blocks(content: str, lang: str = "") -> List[str]:
    """Extract fenced code blocks, optionally filtered by language."""
    pattern = rf'```{lang}\s*\n(.*?)```' if lang else r'```\w*\s*\n(.*?)```'
    return [m.group(1).strip() for m in re.finditer(pattern, content, re.DOTALL)]


def extract_section(content: str, heading: str) -> str:
    """Extract content under a ## heading until next ## or EOF."""
    pattern = rf'^##\s+{re.escape(heading)}.*?\n(.*?)(?=^##|\Z)'
    m = re.search(pattern, content, re.MULTILINE | re.DOTALL)
    return m.group(1).strip() if m else ""


# ── 1. VERSION DRIFT ──────────────────────────────────────────
section("1. Version drift (SKILL.md vs README.md vs REFERENCE.md)")

skill_ver = extract_version(SKILL_MD)
readme_ver = extract_version(README_MD)
ref_ver = extract_version(REFERENCE_MD)

if not skill_ver:
    report(False, f"SKILL.md: version not found")

if skill_ver and readme_ver:
    report(skill_ver == readme_ver,
           f"SKILL.md ({skill_ver}) == README.md ({readme_ver})",
           f"Mismatch: {skill_ver} vs {readme_ver}")

if skill_ver and ref_ver:
    report(skill_ver == ref_ver,
           f"SKILL.md ({skill_ver}) == REFERENCE.md ({ref_ver})",
           f"Mismatch: {skill_ver} vs {ref_ver}")


# ── 2. P8 SCHEDULING LOOP SYNC ────────────────────────────────
section("2. P8 scheduling loop (SKILL.md ↔ role-rulai-pro.md)")

if not ROLE_RULAI_PRO.exists():
    report(False, "role-rulai-pro.md exists", "File not found")
else:
    skill_p8 = SKILL_MD.read_text(encoding="utf-8")
    rulai_p8 = ROLE_RULAI_PRO.read_text(encoding="utf-8")

    # Extract the P8 scheduling loop block
    # It starts after "## P8 自动化调度循环" or "P8 自动化调度循环"
    def extract_p8_loop(content: str) -> str:
        patterns = [
            r'自动化调度循环（必执行.*?\n(.*?)(?=^Teardown|\Z)',
            r'P8 自动化调度循环.*?\n(.*?)(?=^Teardown|\Z)',
        ]
        for pat in patterns:
            m = re.search(pat, content, re.MULTILINE | re.DOTALL)
            if m:
                return m.group(1).strip()
        return ""

    skill_p8_loop = extract_p8_loop(skill_p8)
    rulai_p8_loop = extract_p8_loop(rulai_p8)

    if not skill_p8_loop:
        report(False, "SKILL.md: P8 scheduling loop found")
    if not rulai_p8_loop:
        report(False, "role-rulai-pro.md: P8 scheduling loop found")

    if skill_p8_loop and rulai_p8_loop:
        # Normalize for comparison: strip markdown link syntax and normalize whitespace
        def normalize(text: str) -> str:
            # Collapse markdown links: [text](path) → path
            text = re.sub(r'\[`?([^`\]]+)`?\]\([^)]+\)', r'\1', text)
            # Strip inline code backticks: `path` → path
            text = re.sub(r'`([^`]+)`', r'\1', text)
            # Normalize relative paths: strip references/ prefix for comparison
            text = re.sub(r'\breferences/([^\s`]+)', r'\1', text)
            return text.strip()

        skill_lines = [normalize(l) for l in skill_p8_loop.splitlines() if l.strip()]
        rulai_lines = [normalize(l) for l in rulai_p8_loop.splitlines() if l.strip()]

        if skill_lines == rulai_lines:
            report(True, "P8 loop blocks are identical")
        else:
            # Find the first difference
            for i, (s, r) in enumerate(zip(skill_lines, rulai_lines)):
                if s != r:
                    report(False,
                           f"P8 loop blocks differ at line {i + 1}",
                           f"SKILL.md: {s[:80]}...\n    role-rulai-pro.md: {r[:80]}...")
                    break
            else:
                len_diff = abs(len(skill_lines) - len(rulai_lines))
                report(False,
                       "P8 loop blocks same lines but different lengths",
                       f"SKILL.md: {len(skill_lines)} lines, role-rulai-pro.md: {len(rulai_lines)} lines")


# ── 3. CROSS-FILE REFERENCES ──────────────────────────────────
section("3. Cross-file references (all .md → existence check)")

# Scan all .md files for references/ links
all_md = list(ROOT.rglob("*.md"))
dangling = False
for md_file in sorted(all_md):
    content = md_file.read_text(encoding="utf-8")
    links = extract_md_links_nocode(content)
    base_dir = md_file.parent
    for text, link in links:
        if link.startswith("http:") or link.startswith("https:") or link.startswith("#"):
            continue
        # Resolve relative to the file's directory
        target = (base_dir / link).resolve()
        if not target.exists():
            dangling = True
            report(False,
                   f"{md_file.name} → {link}",
                   f"Target does not exist: {target}")

if not dangling:
    report(True, "All cross-file references resolve")


# ── 4. STALE TERMINOLOGY ───────────────────────────────────────
section("4. Stale terminology scan (flavors/flavor residue)")

# Files that are allowed to mention flavors (changelog, historical docs)
ALLOW_FLAVOR = {"CHANGELOG.md", "REFERENCE.md", "teardown-protocol.md", "README.md", "Emotional_Prompting.md"}

stale_found = False
for md_file in sorted(all_md):
    content = md_file.read_text(encoding="utf-8").lower()
    if "flavor" in content and md_file.name not in ALLOW_FLAVOR:
        # Check context: is it in a code block or in explanation?
        lines_with_flavor = [l for l in md_file.read_text(encoding="utf-8").splitlines()
                             if "flavor" in l.lower() and "flavor" not in l.lower().split(
                                 "flavor")[0]]
        for line in lines_with_flavor:
            stale_found = True
            report(False,
                   f"{md_file.name}:{line.strip()[:80]}",
                   f"Contains 'flavor(s)' — flavors were removed in 1.0.7")

if not stale_found:
    report(True, "No stale 'flavors' references in non-changelog files")


# ── 5. ROLE-KEY CONSISTENCY ────────────────────────────────────
section("5. Role-key consistency (role-switch-protocol ↔ role-*.md)")

# Extract role-keys from role-switch-protocol.md
switch_content = ROLE_SWITCH_PROTOCOL.read_text(encoding="utf-8") if ROLE_SWITCH_PROTOCOL.exists() else ""
switch_role_keys: Set[str] = set()
for m in re.finditer(r'\|\s*`([a-z]+)`\s*\|', switch_content):
    switch_role_keys.add(m.group(1))

# Find all role-*.md files (excluding *-pro.md etc. but tracking them separately)
# Also exclude non-role files like role-router.md, role-switch-protocol.md
NON_ROLE_FILES = {"role-router.md", "role-switch-protocol.md", "role-guanyin-pro.md", "role-xuanzang-pro.md"}
existing_base_roles: Set[str] = set()
pro_only_roles: Set[str] = set()
for f in REFERENCES.glob("role-*.md"):
    if f.name in NON_ROLE_FILES:
        continue
    m = re.match(r'role-([a-z-]+)\.md', f.name)
    if not m:
        continue
    key = m.group(1)
    if any(key.endswith(s) for s in ("-pro", "-de", "-escalation", "-breaker", "-override")):
        # This is a pro/support file, not a base role
        continue
    existing_base_roles.add(key)

# Also check for pro-only roles (have role-X-pro.md but no role-X.md)
for f in REFERENCES.glob("role-*-pro.md"):
    if f.name in NON_ROLE_FILES:
        continue
    m = re.match(r'role-([a-z-]+)-pro\.md', f.name)
    if m:
        base_key = m.group(1)
        if base_key not in existing_base_roles:
            pro_only_roles.add(base_key)

# Protocol mentions a role but no file exists (pro-only roles are OK)
for rk in sorted(switch_role_keys):
    if rk not in existing_base_roles and rk not in pro_only_roles:
        report(False,
               f"role-switch protocol lists '{rk}' but no role-{rk}.md",
               "Missing base role file")

# File exists but protocol doesn't list it (pro-only roles reported as INFO)
for rk in sorted(existing_base_roles):
    if rk not in switch_role_keys:
        report(False,
               f"role-{rk}.md exists but not in switch protocol",
               "Orphan file or protocol missing entry")

for rk in sorted(pro_only_roles):
    if rk not in switch_role_keys:
        report(False,
               f"role-{rk}-pro.md exists but '{rk}' not in switch protocol",
               "Pro file for unlisted role")

if not FAIL:
    total_roles = len(existing_base_roles) + len(pro_only_roles)
    report(True, f"All {total_roles} roles ({len(existing_base_roles)} base + {len(pro_only_roles)} pro-only) match between protocol and filesystem")


# ── 6. SCRIPT SYNTAX ──────────────────────────────────────────
section("6. Python script syntax check")

for py_file in sorted(SCRIPTS.glob("*.py")):
    code = py_file.read_text(encoding="utf-8")
    try:
        ast.parse(code)
        report(True, f"{py_file.name} syntax OK")
    except SyntaxError as e:
        report(False, f"{py_file.name} syntax error", str(e))


# ── 7. DISPLAY-PROTOCOL DENSITY TABLE WIRING ──────────────────
section("7. Display-protocol density table wiring")

dp_content = (REFERENCES / "display-protocol.md").read_text(
    encoding="utf-8") if (REFERENCES / "display-protocol.md").exists() else ""

# Check that both SKILL.md and role-rulai-pro.md reference the density table
skill_content = SKILL_MD.read_text(encoding="utf-8")
rulai_content = ROLE_RULAI_PRO.read_text(encoding="utf-8") if ROLE_RULAI_PRO.exists() else ""

density_refs = {
    "SKILL.md": "密度分级表" in skill_content and "display-protocol.md" in skill_content,
    "role-rulai-pro.md": "密度分级表" in rulai_content and "display-protocol.md" in rulai_content,
}

all_wired = True
for file, wired in density_refs.items():
    if not wired:
        all_wired = False
        report(False, f"{file}: density table not referenced",
               "P8 scheduling loop should reference display-protocol density table")
    else:
        report(True, f"{file}: density table is wired")


# ── 8. FILES DECLARED IN SKILL.md EXIST ────────────────────────
section("8. Files declared in SKILL.md lazyload chain exist")

skill_text = SKILL_MD.read_text(encoding="utf-8")

# Find all references/*.md links in SKILL.md
skill_links = extract_md_links_nocode(skill_text)
all_exist = True
for text, link in skill_links:
    if link.startswith("references/") and link.endswith(".md"):
        target = (ROOT / link).resolve()
        if not target.exists():
            all_exist = False
            report(False, f"SKILL.md references {link}", "File does not exist")

if all_exist:
    report(True, "All files declared in SKILL.md lazyload chain exist")


# ── SUMMARY ────────────────────────────────────────────────────
print(f"\n{'=' * 60}")
total = PASS + FAIL
if FAIL == 0:
    print(f"  ALL {PASS} CHECKS PASSED")
    sys.exit(0)
else:
    print(f"  {PASS}/{total} PASSED  |  {FAIL}/{total} FAILED")
    sys.exit(1)