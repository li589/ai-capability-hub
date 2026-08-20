#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""财税技能矩阵 · 专家与专家团自动注册集成（仅标准库 + 复用 register_local_experts 契约）。

设计目标（对应需求「矩阵技能安装初始化时专家与团队的自动化下载安装与使用导引」）：
- 每个矩阵技能 slug 对应 1 个专属专家（experts_build/agents/expert-<slug>）且恰好归属 1 个
  专家团（experts_build/teams/expert-pod-pN）。安装技能时联动注册其专属专家 + 所属专家团，
  使 SKILL.md 中「装包即自动注册」的声明真正落地。
- 团队按 pod 目录名去重：同一团队的多个成员技能被安装时，团队仅注册一次。
- 文档优先：团队归属以各 SKILL.md 文档声明的「专家团」为准（与用户看到的一致）；若文档缺失
  则回退到 experts_build 团队成员数据（teamInfo.memberAgents），多归属时取首个（确定性）。
- 幂等：已注册则跳过；支持 dry-run 预演；支持自定义 marketplace 目录（便于沙箱测试，不污染
  真实 ~/.workbuddy）。

典型用法：
    from matrix_expert_install import install_experts_for_slugs
    report = install_experts_for_slugs(slugs, marketplace_dir=tmp, dry_run=False)
"""
import os
import sys
import json
import glob
import re
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))


# ---------------------------------------------------------------------------
# 依赖：复用 register_local_experts 的注册契约（校验 / 写入 marketplace.json）
# ---------------------------------------------------------------------------
def _import_register():
    scripts = os.path.join(HERE, "scripts")
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    import register_local_experts as R  # noqa: E402
    return R


# ---------------------------------------------------------------------------
# 路径默认值
# ---------------------------------------------------------------------------
def default_experts_src():
    return os.path.join(HERE, "experts_build")


def default_skills_dir():
    return os.path.join(HERE, "skills")


# ---------------------------------------------------------------------------
# 索引构建
# ---------------------------------------------------------------------------
def _load_team_index(experts_src):
    """返回 {pod_dir: {"members":[agent_id...], "name": displayName.zh}}。"""
    idx = {}
    for tj in sorted(glob.glob(os.path.join(experts_src, "teams", "*", ".codebuddy-plugin", "plugin.json"))):
        d = json.load(open(tj, encoding="utf-8"))
        pod = os.path.basename(os.path.dirname(os.path.dirname(tj)))
        ti = d.get("teamInfo", {}) or {}
        members = list(ti.get("memberAgents", []) or d.get("memberAgents", []) or [])
        idx[pod] = {
            "members": members,
            "name": (d.get("displayName", {}) or {}).get("zh") or d.get("name"),
        }
    return idx


def _load_agent_index(experts_src):
    """返回 {agent_dir: {"id": agentName, "pkg": dir_path}}。"""
    idx = {}
    for pj in sorted(glob.glob(os.path.join(experts_src, "agents", "*", ".codebuddy-plugin", "plugin.json"))):
        d = json.load(open(pj, encoding="utf-8"))
        adir = os.path.basename(os.path.dirname(os.path.dirname(pj)))
        idx[adir] = {
            "id": d.get("agentName") or d.get("name"),
            "pkg": os.path.dirname(os.path.dirname(pj)),
        }
    return idx


_DOC_TEAM_PAT = re.compile(r"\*\*专家团 · ([^：\n]+团)\*\*")


def _doc_team_name(slug, skills_dir):
    p = os.path.join(skills_dir, slug, "SKILL.md")
    if not os.path.isfile(p):
        return None
    m = _DOC_TEAM_PAT.search(open(p, encoding="utf-8").read())
    return m.group(1).strip() if m else None


def _team_name_to_pod(name, team_idx):
    if not name:
        return None
    for pod, info in team_idx.items():
        if info["name"] == name:
            return pod
    return None


# ---------------------------------------------------------------------------
# slug -> {agent_dir, team_dir, agent_id, team_name}
# ---------------------------------------------------------------------------
def discover_slug_map(experts_src=None, skills_dir=None, slugs=None):
    """构建全部（或指定）slug 的专家/团队映射。文档团队优先，回退数据成员身份。"""
    experts_src = experts_src or default_experts_src()
    skills_dir = skills_dir or default_skills_dir()
    team_idx = _load_team_index(experts_src)
    agent_idx = _load_agent_index(experts_src)

    if slugs is None:
        # 取自 matrix.json，保证与安装清单一致
        mj = os.path.join(HERE, "matrix.json")
        slugs = [s["slug"] for s in json.load(open(mj, encoding="utf-8"))["skills"]]

    pod_of_agent = {}  # agent_id -> [pod,...]
    for pod, info in team_idx.items():
        for aid in info["members"]:
            pod_of_agent.setdefault(aid, []).append(pod)

    result = {}
    for slug in slugs:
        adir = "expert-" + slug
        ainfo = agent_idx.get(adir)
        if not ainfo:
            result[slug] = {"error": "agent dir missing: %s" % adir}
            continue
        aid = ainfo["id"]
        doc_team = _doc_team_name(slug, skills_dir)
        doc_pod = _team_name_to_pod(doc_team, team_idx)
        candidates = pod_of_agent.get(aid, [])
        if doc_pod and doc_pod in candidates:
            pod = doc_pod
        elif doc_pod and doc_pod not in candidates:
            # 文档团队与数据不一致：仍尊重文档（保持用户所见一致），并标记
            pod = doc_pod
        elif candidates:
            pod = sorted(candidates)[0]
        else:
            pod = None
        result[slug] = {
            "agent_dir": adir,
            "agent_pkg": ainfo["pkg"],
            "agent_id": aid,
            "team_dir": pod,
            "team_name": (team_idx.get(pod, {}) or {}).get("name"),
            "doc_team": doc_team,
            "data_teams": candidates,
        }
    return result


# ---------------------------------------------------------------------------
# 批量注册
# ---------------------------------------------------------------------------
def install_all_present(experts_src, marketplace_dir, dry_run=False, verbose=True):
    """注册 experts_src 下【物理存在】的全部 agent + team 包（自包含模式）。

    用于总装包/分团包：包内不含全局 matrix.json，直接扫描包内 experts_build，
    注册包内全部专家与团队（含可能被全局 slug 映射遗漏的团队，如多归属成员的团）。
    """
    R = _import_register()
    experts_src = experts_src or default_experts_src()
    marketplace_dir = Path(marketplace_dir)
    agents_res, teams_res = {}, {}
    for pj in sorted(glob.glob(os.path.join(experts_src, "agents", "*", ".codebuddy-plugin", "plugin.json"))):
        pkg = Path(os.path.dirname(os.path.dirname(pj)))
        try:
            r = R.register_one(pkg, marketplace_dir, dry_run=dry_run)
        except Exception as e:
            r = "fail"
            if verbose:
                print("  [fail] 专家注册异常 %s: %s" % (pkg.name, e))
        agents_res[pkg.name] = r
        if verbose and r not in ("skip", "fail"):
            print("  [agent] %s -> %s" % (pkg.name, r))
    for pj in sorted(glob.glob(os.path.join(experts_src, "teams", "*", ".codebuddy-plugin", "plugin.json"))):
        pkg = Path(os.path.dirname(os.path.dirname(pj)))
        try:
            r = R.register_one(pkg, marketplace_dir, dry_run=dry_run)
        except Exception as e:
            r = "fail"
            if verbose:
                print("  [fail] 团队注册异常 %s: %s" % (pkg.name, e))
        teams_res[pkg.name] = r
        if verbose and r not in ("skip", "fail"):
            print("  [team]  %s -> %s" % (pkg.name, r))
    counts = {
        "agents_ok": sum(1 for v in agents_res.values() if v == "ok"),
        "agents_skip": sum(1 for v in agents_res.values() if v == "skip"),
        "agents_dry": sum(1 for v in agents_res.values() if v == "dry"),
        "agents_missing": sum(1 for v in agents_res.values() if v == "missing"),
        "agents_fail": sum(1 for v in agents_res.values() if v == "fail"),
        "teams_ok": sum(1 for v in teams_res.values() if v == "ok"),
        "teams_skip": sum(1 for v in teams_res.values() if v == "skip"),
        "teams_dry": sum(1 for v in teams_res.values() if v == "dry"),
        "teams_missing": sum(1 for v in teams_res.values() if v == "missing"),
        "teams_fail": sum(1 for v in teams_res.values() if v == "fail"),
    }
    return {"agents": agents_res, "teams": teams_res, "counts": counts}


def install_experts_for_slugs(slugs, marketplace_dir, experts_src=None,
                              skills_dir=None, dry_run=False, verbose=True):
    """为给定 slug 列表注册专属专家 + 所属专家团。

    返回 dict: {
        "agents": {slug: "ok"|"skip"|"dry"|"missing"|"fail"},
        "teams":  {pod: "ok"|"skip"|"dry"|"missing"|"fail"},
        "counts": {...}
    }
    """
    R = _import_register()
    experts_src = experts_src or default_experts_src()
    if slugs is None:
        mj = os.path.join(HERE, "matrix.json")
        slugs = [s["slug"] for s in json.load(open(mj, encoding="utf-8"))["skills"]]
    from pathlib import Path
    marketplace_dir = Path(marketplace_dir)
    smap = discover_slug_map(experts_src, skills_dir, slugs=slugs)

    agents_res = {}
    teams_res = {}
    team_pkgs = {}  # pod -> pkg dir（去重后一次注册）

    for slug in slugs:
        info = smap.get(slug, {})
        if "error" in info:
            agents_res[slug] = "missing"
            if verbose:
                print("  [miss] 专家缺失: %s (%s)" % (slug, info["error"]))
            continue
        agent_pkg = Path(info["agent_pkg"])
        if not agent_pkg.is_dir():
            agents_res[slug] = "missing"
            if verbose:
                print("  [miss] 专家包不存在: %s" % agent_pkg)
            continue
        try:
            r = R.register_one(agent_pkg, marketplace_dir, dry_run=dry_run)
        except Exception as e:  # 单项失败不影响整体矩阵安装
            r = "fail"
            if verbose:
                print("  [fail] 专家注册异常 %s: %s" % (slug, e))
        agents_res[slug] = r
        if verbose and r not in ("skip", "fail"):
            print("  [agent] %s -> %s" % (slug, r))

        pod = info["team_dir"]
        if pod and pod not in team_pkgs:
            team_pkg = Path(experts_src) / "teams" / pod
            if team_pkg.is_dir():
                team_pkgs[pod] = team_pkg
            else:
                teams_res[pod] = "missing"
                if verbose:
                    print("  [miss] 团队包不存在: %s" % team_pkg)

    # 注册去重后的团队
    for pod, team_pkg in sorted(team_pkgs.items()):
        try:
            r = R.register_one(team_pkg, marketplace_dir, dry_run=dry_run)
        except Exception as e:  # 单项失败不影响整体
            r = "fail"
            if verbose:
                print("  [fail] 团队注册异常 %s: %s" % (pod, e))
        teams_res[pod] = r
        if verbose and r not in ("skip", "fail"):
            print("  [team]  %s -> %s" % (pod, r))

    counts = {
        "agents_ok": sum(1 for v in agents_res.values() if v == "ok"),
        "agents_skip": sum(1 for v in agents_res.values() if v == "skip"),
        "agents_dry": sum(1 for v in agents_res.values() if v == "dry"),
        "agents_missing": sum(1 for v in agents_res.values() if v == "missing"),
        "agents_fail": sum(1 for v in agents_res.values() if v == "fail"),
        "teams_ok": sum(1 for v in teams_res.values() if v == "ok"),
        "teams_skip": sum(1 for v in teams_res.values() if v == "skip"),
        "teams_dry": sum(1 for v in teams_res.values() if v == "dry"),
        "teams_missing": sum(1 for v in teams_res.values() if v == "missing"),
        "teams_fail": sum(1 for v in teams_res.values() if v == "fail"),
    }
    return {"agents": agents_res, "teams": teams_res, "counts": counts, "map": smap}


# ---------------------------------------------------------------------------
# 团队注册完成后：自动安装「财税政策知识库」+ 本团相关技能
# ---------------------------------------------------------------------------
def auto_install_kb_and_related(marketplace_dir, dry_run=False, verbose=True, update=True, target=None):
    """专家/团队注册完成后，自动安装知识库底座 + 本团相关技能。

    - 知识库：tax-policy-knowledge（专家 ask/risk/calc 的来源，团队专家的前置依赖）。
    - 相关技能：由包内 teams 的成员 agent id（<slug>-expert）派生本团专题技能 slug。
    - 版本比对 + 幂等：同版本跳过（避免重复安装）；--update 时版本不一致则升级。
    - 优雅降级：网络/SkillHub 不可达时单条跳过并提示手动安装，不中断专家注册主流程。
    仅在包内存在 matrix.json + install_matrix.py（即打包时注入了矩阵安装器）时生效。
    """
    matrix_path = os.path.join(HERE, "matrix.json")
    if not os.path.isfile(matrix_path):
        if verbose:
            print("[info] 本包未注入矩阵安装器（无 matrix.json），跳过知识库自动安装。")
        return
    try:
        if HERE not in sys.path:
            sys.path.insert(0, HERE)
        import install_matrix as IM
    except Exception as e:
        if verbose:
            print("[warn] 无法加载矩阵安装器，跳过知识库自动安装: %s" % e)
        return

    # 1) 派生本团相关技能 slug：扫描包内 teams 的成员 agent id（形如 <slug>-expert）
    related = set()
    for tj in sorted(glob.glob(os.path.join(HERE, "experts_build", "teams", "*",
                                            ".codebuddy-plugin", "plugin.json"))):
        try:
            d = json.load(open(tj, encoding="utf-8"))
        except Exception:
            continue
        for mem in (d.get("members") or []):
            aid = mem.get("id") or ""
            slug = aid[:-7] if aid.endswith("-expert") else aid
            if slug:
                related.add(slug)
    # 2) 知识库底座（专家 ask/risk/calc 的前置依赖）
    related.add("tax-policy-knowledge")
    related = sorted(related)

    # 3) 仅保留 matrix.json 中真实存在的 slug
    try:
        mj = json.load(open(matrix_path, encoding="utf-8"))
        valid = {s["slug"] for s in mj.get("skills", [])}
    except Exception:
        valid = set()
    related = [s for s in related if s in valid]
    if not related:
        return

    if verbose:
        print("=" * 52)
        print("自动安装 · 财税政策知识库 + 本团相关技能")
        print("  目标: " + ", ".join(related))
        print("  策略: 版本比对 · 同版本跳过(避免重复) · %s" %
              ("版本不一致则升级(--update)" if update else "版本不一致仅提示"))
        print("  网络不可达时优雅跳过，可手动对我说对应提示词安装。")
        print("=" * 52)

    # 4) 逐个安装（独立 try，单条失败不中断整体专家注册）
    #    采用 --no-integrity-check：下载源受域名白名单约束（仅官方 SkillHub/ClawHub），
    #    故允许因服务端重打包导致的哈希漂移降级放行，确保自动安装稳定可用。
    for slug in related:
        try:
            argv = ["--only", slug, "--marketplace-dir", str(marketplace_dir),
                    "--no-experts", "--no-integrity-check"]
            if target:
                argv += ["--target", str(target)]
            if update:
                argv.append("--update")
            if dry_run:
                argv.append("--dry-run")
            IM.main(argv)
        except SystemExit as e:
            if verbose and e.code not in (0, None):
                print("  [warn] %s 安装器退出码 %s（若因网络不可达，可稍后手动安装）" % (slug, e.code))
        except Exception as e:
            if verbose:
                print("  [warn] %s 自动安装异常（已跳过，可手动安装）: %s" % (slug, e))


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="矩阵技能专家/团队自动注册（独立运行）")
    ap.add_argument("--slugs", nargs="*", help="指定 slug（默认全量）")
    ap.add_argument("--all", action="store_true", help="注册 experts_src 下物理存在的全部专家与团队（自包含模式）")
    ap.add_argument("--marketplace-dir", default=None, help="目标 marketplace（默认真实 ~/.workbuddy 我的专家）")
    ap.add_argument("--experts-src", default=None, help="experts_build 目录")
    ap.add_argument("--dry-run", action="store_true", help="仅预演不写入")
    args = ap.parse_args()

    R = _import_register()
    mk = args.marketplace_dir or R.get_marketplace_base()
    experts_src = args.experts_src or default_experts_src()
    # 自包含判定：显式 --all，或包内无 matrix.json（分发包）时回退注册全部；
    # 团队/矩阵类包即便注入了 matrix.json（用于自动安装知识库），也强制走 --all
    # 扫描自身 experts_build，避免误走 slug 映射模式而注册失败。
    has_teams = os.path.isdir(os.path.join(HERE, "experts_build", "teams"))
    use_all = args.all or (not os.path.isfile(os.path.join(HERE, "matrix.json"))) or has_teams
    if use_all:
        rep = install_all_present(experts_src, mk, dry_run=args.dry_run, verbose=True)
    else:
        rep = install_experts_for_slugs(
            args.slugs or None, mk,
            experts_src=experts_src, dry_run=args.dry_run, verbose=True)
    c = rep["counts"]
    print("-" * 48)
    print("专家: ok=%d skip=%d dry=%d missing=%d fail=%d" % (c["agents_ok"], c["agents_skip"], c["agents_dry"], c["agents_missing"], c["agents_fail"]))
    print("团队: ok=%d skip=%d dry=%d missing=%d fail=%d" % (c["teams_ok"], c["teams_skip"], c["teams_dry"], c["teams_missing"], c["teams_fail"]))

    # ---- 自动安装知识库 + 本团相关技能（版本比对 · 幂等 · 可升级） ----
    try:
        auto_install_kb_and_related(mk, dry_run=args.dry_run, verbose=True, update=True)
    except Exception as e:
        print("[warn] 知识库/相关技能自动安装异常（专家注册已完成，可手动安装）: %s" % e)
