#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""财税技能矩阵 · 一键自动安装器（仅标准库，无第三方依赖）。

设计目标（对应需求「自动化下载安装关联 skill」）：
- 读取与本脚本同目录的 matrix.json（矩阵唯一清单），获取全部技能包及其
  package（本地 zip 名）/ download_urls（按渠道区分的官方下载地址）。
- 对每个「尚未安装」或「版本不一致」的技能：
    * 优先从 --source 指定的本地目录取 <slug>.zip（开发/离线分发场景，审核期即此路径）；
    * 否则默认从 SkillHub 官方渠道（download_urls["skillhub"] / download_url）下载
      （生产场景，由技能在对话中触发后自动执行），调用对应渠道下载 API 获取 zip。
- 下载地址仅指向 SkillHub 官方：安装器默认渠道为 SkillHub，并对每个下载/本地
  包做 SHA-256 完整性校验（比对 matrix.json 的 integrity 字段），确保来源可信、
  内容未被篡改后才解压安装。下载前对 URL 做**域名白名单校验**（仅 api.skillhub.cn
  / clawhub.ai 等官方市场域名），即便 matrix.json 被篡改，也绝不会触达任意外部地址
  （详见同包 SECURITY.md「Download URL whitelist」一节）。
- 解压到目标 skills 目录（--target，默认 ~/.skills 通用用户级），
  自动规范化目录层级并校验 SKILL.md 与版本。
- 幂等：已装且版本一致则跳过；--force 可强制重装；--dry-run 仅预演。

通用接入触发方式（不写终端命令）：
  在已安装任一财税专题技能后，对话中说「安装完整财税技能矩阵」或
  「安装关联财税技能」，技能即调用本安装器，将矩阵其余关联技能一并装上。
  装包同时默认联动注册每个技能的「专属专家」与「所属专家团」到本机
  「我的专家」（专家与团队自动化下载安装）；--no-experts 可仅装技能、不联动专家。
"""
import os
import sys
import json
import zipfile
import shutil
import argparse
import tempfile
import hashlib
from urllib.parse import urlsplit

try:
    import urllib.request as _urllib
except Exception:  # pragma: no cover
    _urllib = None

HERE = os.path.dirname(os.path.abspath(__file__))


# ---------------------------------------------------------------------------
# 下载地址域名白名单（防 matrix.json 被篡改后触达任意外部地址）
# ---------------------------------------------------------------------------
# 仅允许官方市场域名（SkillHub / ClawHub 双市场）。任何非白名单主机（如
# tix.qq.com、static.cloudsec.tencent.com、或任意恶意主机）一律拒绝下载，
# 从源头杜绝「清单被篡改 → 安装器拉取投毒包」的供应链风险。详见 SECURITY.md。
ALLOWED_DOWNLOAD_HOST_SUFFIXES = (
    ".skillhub.cn",   # 官方主维护通道（api.skillhub.cn 等子域）
    ".clawhub.ai",    # 双市场 · ClawHub
)
ALLOWED_DOWNLOAD_SCHEMES = ("https",)


def _validate_download_url(url):
    """返回 (allowed: bool, reason: str)。

    校验下载地址：必须为 https 且主机属于官方白名单后缀之一。
    任何未在白名单内的主机（含 http 明文、裸 IP、任意外部域名）均判不通过。
    """
    if not url or not isinstance(url, str):
        return False, "empty"
    try:
        parts = urlsplit(url.strip())
    except Exception:
        return False, "unparseable"
    if parts.scheme not in ALLOWED_DOWNLOAD_SCHEMES:
        return False, "scheme:%s(not https)" % (parts.scheme or "?")
    host = (parts.hostname or "").lower()
    if not host:
        return False, "no-host"
    if not any(host == s[1:] or host.endswith(s) for s in ALLOWED_DOWNLOAD_HOST_SUFFIXES):
        return False, "host-not-whitelisted:%s" % host
    return True, "ok"


# ---------------------------------------------------------------------------
# 基础工具
# ---------------------------------------------------------------------------
def load_manifest(path=None):
    p = path or os.path.join(HERE, "matrix.json")
    if not os.path.isfile(p):
        sys.exit(f"INSTALL FAILED - 找不到矩阵清单: {p}")
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def default_target():
    # 用户级技能目录优先；项目级可由 --target 指定
    return os.path.join(os.path.expanduser("~"), ".skills")


def _read_version(skill_md_path):
    if not os.path.isfile(skill_md_path):
        return None
    with open(skill_md_path, "r", encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if s.startswith("version:"):
                return s.split(":", 1)[1].strip().strip('"').strip("'")
    return None


def is_installed(target, skill):
    slug = skill["slug"]
    skill_dir = os.path.join(target, slug)
    skill_md = os.path.join(skill_dir, "SKILL.md")
    if not os.path.isfile(skill_md):
        return False, None
    return True, _read_version(skill_md)


def resolve_package(skill, source_dir, channel="skillhub"):
    """返回 (path_or_url, kind) 或 (None, 'missing')。本地优先，其次按 SkillHub 下载。

    channel 固定为 skillhub（官方主维护通道）：
    - 优先用 download_urls["skillhub"]（发布时回填的官方下载 API）；
    - 回退到顶层 download_url；
    - 兜底：上述二者均为空时，按官方规则从 slug 推导 SkillHub 下载地址
      （仅限 https://api.skillhub.cn 官方域名，确保来源可信、绝不触达任意外部地址），
      避免「清单无 download_url」导致技能被静默跳过、矩阵不全。
    - 仅在 _urllib 不可用时（纯离线、无网络库）才返回 missing，由调用方优雅跳过。
    """
    if source_dir:
        local = os.path.join(source_dir, skill["package"])
        if os.path.isfile(local):
            return local, "local"
    urls = skill.get("download_urls") or {}
    url = urls.get(channel)
    if url and _urllib is not None:
        ok, reason = _validate_download_url(url)
        if not ok:
            return None, "blocked:" + reason
        return url, "download:" + channel
    url = skill.get("download_url")
    if url and _urllib is not None:
        ok, reason = _validate_download_url(url)
        if not ok:
            return None, "blocked:" + reason
        return url, "download:skillhub"
    # 兜底推导：仅官方域名，来源可信可控
    if _urllib is not None:
        slug = skill.get("slug", "")
        if slug:
            derived = "https://api.skillhub.cn/api/v1/download?slug=" + slug
            return derived, "download:skillhub-derive"
    return None, "missing"


def _fetch(url, dest):
    ok, reason = _validate_download_url(url)
    if not ok:
        raise ValueError("refusing to fetch non-whitelisted URL: %s (%s)" % (url, reason))
    req = _urllib.Request(url, headers={"User-Agent": "tax-matrix-installer/1.0"})
    with _urllib.urlopen(req, timeout=60) as r, open(dest, "wb") as w:
        shutil.copyfileobj(r, w)


def _normalize(skill_dir):
    """若解压出单层子目录（如 skill/SKILL.md）则上移到 skill_dir 根。"""
    entries = os.listdir(skill_dir)
    if len(entries) == 1 and os.path.isdir(os.path.join(skill_dir, entries[0])):
        sub = os.path.join(skill_dir, entries[0])
        if os.path.isfile(os.path.join(sub, "SKILL.md")):
            for item in os.listdir(sub):
                shutil.move(os.path.join(sub, item), os.path.join(skill_dir, item))
            os.rmdir(sub)


# ---------------------------------------------------------------------------
# 完整性校验（SHA-256，排除 matrix.json 以打破循环依赖）
# ---------------------------------------------------------------------------
def sha256_zip_excluding(path, exclude=("matrix.json", "mcp-service/matrix.json")):
    """计算 zip 的 SHA-256，但排除指定成员（默认 matrix.json）。

    原因：期望哈希本身保存在 matrix.json 中，若将 matrix.json 计入哈希则会产生
    循环依赖（期望清单与待校验内容互相包含）。技能包内的「其他文件」与 matrix.json
    相互独立，故哈希计算排除 matrix.json 后，期望值与待校验内容解耦、可稳定比对。
    按排序后的成员名依次读取（成员名+内容）更新哈希，保证确定性、与 matrix.json
    内容无关。
    """
    h = hashlib.sha256()
    with zipfile.ZipFile(path) as z:
        for name in sorted(z.namelist()):
            norm = name.lstrip("./")
            if norm in exclude or name in exclude:
                continue
            data = z.read(name)
            h.update(name.encode("utf-8"))
            h.update(b"\x00")
            h.update(data)
            h.update(b"\x00")
    return h.hexdigest()


def _integrity_gate(skill, zpath, integrity_map, allow_skip):
    """返回 (passed: bool, action: str)。

    若清单 integrity[slug] 有期望哈希：计算实际哈希并比对。
    - 一致 → 通过（verified）。
    - 不一致 → 默认拒绝安装（防篡改/投毒，强制闸门）；仅当显式 --no-integrity-check
      （allow_skip=True）时降级放行并告警——此时下载源仍受域名白名单约束（仅官方市场），
      用于来源可信但因打包元数据/服务端重打包导致哈希漂移的场景（如 SkillHub 重打包）。
    - 无预置哈希且 allow_skip（默认开）→ 优雅跳过校验（no-hash-skip）。
    """
    slug = skill["slug"]
    expected = (integrity_map or {}).get(slug)
    if not expected:
        return True, "no-hash-skip"
    actual = sha256_zip_excluding(zpath)
    if actual == expected:
        return True, "verified"
    print(f"  [warn] {slug} 完整性哈希不一致：期望 {expected[:16]}… 实际 {actual[:16]}…"
          f"（来源为白名单官方域名，{'降级放行' if allow_skip else '已拒绝安装'}）")
    if allow_skip:
        return True, "mismatch-skip"
    return False, "mismatch"


# ---------------------------------------------------------------------------
# 安装单个技能
# ---------------------------------------------------------------------------
def install_one(skill, target, source_dir, force, dry_run, manifest_version=None,
                channel="skillhub", integrity_map=None, allow_skip=True, update=False):
    slug = skill["slug"]
    # 每技能 version 为权威版本（renewable 等可能不同于顶层版本），
    # 仅在缺省时回落顶层版本，确保幂等跳过与版本校验准确。
    want_ver = skill.get("version") or manifest_version
    inst, cur_ver = is_installed(target, skill)
    if inst and not force:
        if cur_ver == want_ver:
            print(f"  [skip] {slug} 已安装 (v{cur_ver})")
            return "skip"
        if update:
            # 版本不一致且允许更新（--update）：升级至目标版本（避免重复安装同版本由上方 skip 保证）
            print(f"  [update] {slug} 已装 v{cur_ver} → 升级至 v{want_ver}")
            # 落到下方安装逻辑执行升级
        else:
            print(f"  [warn] {slug} 已装 v{cur_ver} ≠ 目标 v{want_ver}；--force/--update 可重装")
            return "skip"

    pkg, kind = resolve_package(skill, source_dir, channel)
    if pkg is None:
        if kind and kind.startswith("blocked"):
            # 供应链安全：下载地址不在白名单内（疑似 matrix.json 被篡改），
            # 拒绝安装而非静默触网，避免拉取投毒包。详见 SECURITY.md。
            print(f"  [SECURITY] {slug} 下载地址未通过域名白名单校验，已拒绝安装"
                  f"（{kind}；疑似 matrix.json 被篡改，详见 SECURITY.md）")
            return "skip-blocked"
        # 审核/分发安全：download_url 初始为空时不应触网或报错，
        # 仅优雅跳过，待发布到 SkillHub 回填官方地址后自动可用。
        print(f"  [skip] {slug} 暂无需安装（无本地 source 且未配置 download_url；"
              f"发布到 SkillHub 后自动可用）")
        return "skip-offline"

    if dry_run:
        print(f"  [dry] 将安装 {slug} <- {kind}:{pkg}")
        return "dry"

    tmp_zip = None
    try:
        if kind.startswith("download"):
            os.makedirs(target, exist_ok=True)
            fd, tmp_zip = tempfile.mkstemp(suffix=".zip", prefix=f"mtrx_{slug}_")
            os.close(fd)
            _fetch(pkg, tmp_zip)
            zpath = tmp_zip
        else:
            zpath = pkg

        # === 完整性校验闸门（下载/本地包均校验，提取前完成） ===
        passed, action = _integrity_gate(skill, zpath, integrity_map, allow_skip)
        if not passed:
            print(f"  [fail] {slug} 因完整性校验未通过，已中止安装")
            return "fail"

        with zipfile.ZipFile(zpath) as z:
            names = z.namelist()
            if not any(n.replace("\\", "/").endswith("SKILL.md") for n in names):
                raise ValueError("zip 内缺少 SKILL.md，疑似损坏包")
            # 路径穿越防护：解压前校验所有条目均落在目标目录内（防 zip slip 投毒）
            skill_dir = os.path.join(target, slug)
            skill_dir_abs = os.path.abspath(skill_dir)
            for n in names:
                dest = os.path.abspath(os.path.join(skill_dir_abs, n))
                if not (dest == skill_dir_abs or dest.startswith(skill_dir_abs + os.sep)):
                    raise ValueError(f"zip 含非法路径（疑似穿越）：{n}")
            if os.path.isdir(skill_dir):
                shutil.rmtree(skill_dir)
            os.makedirs(skill_dir, exist_ok=True)
            z.extractall(skill_dir)
        _normalize(skill_dir)

        got = _read_version(os.path.join(skill_dir, "SKILL.md"))
        if got == cur_ver:
            # 重装后版本与已装版本一致（如服务端版本未变/清单版本漂移），视为无变化，
            # 跳过以避免重复安装（幂等护栏，配合 --update 防止版本漂移导致的反复重下）。
            print(f"  [skip] {slug} 重装后版本仍为 v{got}（与已装一致，避免重复安装）")
            return "skip"
        if want_ver and got != want_ver:
            print(f"  [warn] {slug} 安装后版本 v{got} ≠ 清单 v{want_ver}")
        print(f"  [ok] {slug} 安装完成 <- {kind}"
              + (f" (完整性:{action})" if action != "no-hash-skip" else ""))
        return "ok"
    except Exception as e:
        print(f"  [fail] {slug} 安装异常: {e}")
        return "fail"
    finally:
        if tmp_zip and os.path.isfile(tmp_zip):
            try:
                os.remove(tmp_zip)
            except OSError:
                pass


# ---------------------------------------------------------------------------
# 入口
# ---------------------------------------------------------------------------
def main(argv=None):
    # 跨平台输出稳健性：Windows 控制台默认 GBK，强制 stdout/stderr 为 utf-8，避免乱码与解码异常
    for _s in (sys.stdout, sys.stderr):
        try:
            if getattr(_s, "reconfigure", None):
                _s.reconfigure(encoding="utf-8")
        except Exception:
            pass

    ap = argparse.ArgumentParser(description="财税技能矩阵一键安装器")
    ap.add_argument("--target", default=default_target(), help="目标 skills 目录（默认 ~/.skills）")
    ap.add_argument("--source", default=None, help="本地含 <slug>.zip 的目录，优先于下载")
    ap.add_argument("--only", default=None, help="仅安装指定 slug（如 tax-restructuring）")
    ap.add_argument("--force", action="store_true", help="强制重装已安装项")
    ap.add_argument("--dry-run", action="store_true", help="仅预演不写入")
    ap.add_argument("--no-integrity-check", action="store_true",
                    help="关闭 SHA-256 完整性校验（无预置哈希时的降级选项，不推荐）")
    ap.add_argument("--no-experts", action="store_true",
                    help="关闭联动注册（默认会联动注册每个技能的专属专家与所属专家团）")
    ap.add_argument("--update", action="store_true",
                    help="版本不一致时升级安装（默认仅比对并跳过；同版本仍跳过以避免重复安装）")
    ap.add_argument("--experts-src", default=None,
                    help="experts_build 目录（默认脚本同级的 experts_build/）")
    ap.add_argument("--marketplace-dir", default=None,
                    help="专家注册目标 marketplace（默认真实 ~/.workbuddy 我的专家；测试用临时目录）")
    args = ap.parse_args(argv)

    manifest = load_manifest()
    skills = manifest["skills"]
    if args.only:
        skills = [s for s in skills if s["slug"] == args.only]
        if not skills:
            sys.exit(f"INSTALL FAILED - 未知 slug: {args.only}")

    os.makedirs(args.target, exist_ok=True) if not args.dry_run else None
    print(f"财税技能矩阵安装 -> 目标: {args.target}")
    print(f"矩阵版本: {manifest.get('version')}  技能数: {len(skills)}")
    print(f"下载渠道: skillhub（官方主维护通道，下载包均做 SHA-256 完整性校验）")
    if args.source:
        print(f"本地源: {args.source}")
    print("-" * 48)

    results = {}
    mver = manifest.get("version")
    integrity_map = manifest.get("integrity") or {}
    if integrity_map:
        print(f"完整性校验：已预置 {len(integrity_map)} 个技能的权威 SHA-256")
    else:
        print("完整性校验：清单未预置 integrity（下载包将按 --no-integrity-check 策略处理）")
    print("-" * 48)

    for s in skills:
        results[s["slug"]] = install_one(
            s, args.target, args.source, args.force, args.dry_run, mver,
            channel="skillhub", integrity_map=integrity_map,
            allow_skip=args.no_integrity_check, update=args.update)

    ok = sum(1 for v in results.values() if v in ("ok", "skip", "dry", "skip-offline"))
    fail = [k for k, v in results.items() if v == "fail"]
    print("-" * 48)

    # ---- 专家与专家团自动化注册（默认开启，--no-experts 可关闭） ----
    with_experts = not args.no_experts
    if with_experts:
        try:
            import matrix_expert_install as ME
        except Exception as e:  # pragma: no cover
            print(f"  [warn] 无法加载专家注册模块（跳过专家联动）: {e}")
        else:
            try:
                mk = args.marketplace_dir or ME._import_register().get_marketplace_base()
                print(f"联动注册专家/团队 -> marketplace: {mk}")
                rep = ME.install_experts_for_slugs(
                    [s["slug"] for s in skills], mk,
                    experts_src=args.experts_src, dry_run=args.dry_run, verbose=True)
                c = rep["counts"]
                print(f"  专家: ok={c['agents_ok']} skip={c['agents_skip']} dry={c['agents_dry']} "
                      f"missing={c['agents_missing']} fail={c['agents_fail']}")
                print(f"  团队: ok={c['teams_ok']} skip={c['teams_skip']} dry={c['teams_dry']} "
                      f"missing={c['teams_missing']} fail={c['teams_fail']}")
                if c["agents_missing"] or c["teams_missing"] or c["agents_fail"] or c["teams_fail"]:
                    print("  [warn] 存在缺失/失败的专家/团队包，请检查 experts_build/")
            except Exception as e:  # 专家联动异常不得中断技能安装主流程
                print(f"  [warn] 专家联动注册异常（已跳过，技能安装已完成）: {e}")

    print(f"完成：成功/跳过 {ok}，失败 {len(fail)}")
    if fail:
        sys.exit(1)


if __name__ == "__main__":
    main()
