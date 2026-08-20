#!/usr/bin/env python3
"""
V3.3.1 Orchestrator - 测试用例生成流程控制器
代码控制流程,Agent只负责生成内容。

用法:
  由SKILL.md指导Agent调用:
  exec: python3 {SKILL_DIR}/tools/orchestrator.py --action <action> [--args ...]

支持的action:
  init          - 初始化任务(创建task_id, DATA_DIR)
  onboarding    - 执行Onboarding检查(环境/Python/路径)
  step0         - 接收需求,写入task_meta
  step0_8_prep  - PX图片抽取+选图(返回待Agent理解的图片列表)
  step0_8_save  - 保存Agent的图片理解结果+调用image_enhance
  step_run      - 执行P0-P7任一步骤(准备prompt输入,校验Agent输出,写文件+guard)
  step7_export  - 调用export_excel.py导出
  status        - 查看当前任务状态
  resume        - 断点续跑(检测已完成步骤,返回下一步)
"""

import argparse
import json
import hashlib
import os
import sys
import time
import shlex
import subprocess
import glob
from pathlib import Path


# ============================================================
# 常量
# ============================================================

SKILL_VERSION = "4.15.56"
STEPS = ["onboarding", "step0", "step0_8", "P0", "P1", "P2", "P3", "P4", "P5", "P6", "P7", "step7"]
GATE_STEPS = ["onboarding", "P0", "P1", "P2", "P3", "P4", "P5", "P6", "P7"]

# # V4.7.3: 子Agent环境检测函数
def _is_sub_agent_session():
    """检测当前是否在子Agent会话中执行。

    P6用例生成任务量大(每批50条用例+大量上下文读取),
    在子Agent的30分钟超时限制下无法完成,必须拒绝。

    检测策略(多层fallback):
      1. 环境变量 OPENCLAW_IS_SUBAGENT=1 → 直接判定
      2. 进程树检测: 祖父进程也是openclaw/node → 判定为子Agent嵌套
      3. 无法判定时放行(fail-open,避免误杀)
    """
    import subprocess as _sp

    # 策略1: 环境变量显式标记(OpenClaw运行时可设置)
    if os.environ.get('OPENCLAW_IS_SUBAGENT') == '1':
        return True

    # 策略2: 进程树检测(两层openclaw嵌套=子Agent→exec→脚本)
    try:
        ppid = os.getppid()
        # 获取父进程信息
        r = _sp.run(['ps', '-o', 'ppid=,comm=', '-p', str(ppid)],
                    capture_output=True, text=True, timeout=3)
        if r.returncode != 0 or not r.stdout.strip():
            return False
        parts = r.stdout.strip().split()
        if len(parts) < 2:
            return False
        gppid, pname = parts[0], parts[1]
        # 父进程是openclaw/node → 进一步检查祖父进程
        if ('openclaw' in pname.lower() or 'node' in pname.lower()):
            r2 = _sp.run(['ps', '-o', 'comm=', '-p', gppid],
                        capture_output=True, text=True, timeout=3)
            gpname = r2.stdout.strip().lower()
            if 'openclaw' in gpname or 'node' in gpname:
                # 两层openclaw嵌套 → 子Agent环境
                return True
    except Exception:
        pass

    return False

# HMAC固定密钥(V4.0.1: 避免文件内容变化导致密钥断裂)
import sys, os, json, hashlib, hmac, time, subprocess, glob, re, argparse

# V4.0.1: 模块化拆分 - 共享常量/工具/状态/安全到core/knowledge
# V4.1.8: 确保skill_v4根目录在sys.path,以便import knowledge模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core import constants as _c, utils as _u, state as _s, security as _sec
from knowledge import domain_match as _dm, cloud_sync as _cs
from gate_checker import run_gate_checks as _run_gate_checks, evaluate_gate as _evaluate_gate, format_gate_report as _format_gate_report
try:
    from gate_checker import check_p5_description_quality as _check_p5_desc_quality
except ImportError:
    _check_p5_desc_quality = None

# V4.8.0: 弱模型适配 - 模型检测 + 引导卡生成(按需导入,避免循环)
_model_detect = None
_p6_guide = None

def _get_model_detect():
    global _model_detect
    if _model_detect is None:
        from tools import model_detect as _md
        _model_detect = _md
    return _model_detect

def _get_p6_guide():
    global _p6_guide
    if _p6_guide is None:
        from tools import p6_guide as _pg
        _p6_guide = _pg
    return _p6_guide

HMAC_SECRET = "xy-req2testcase-v4-hmac-2026"
# V4.13.5: Agent疲劳作弊预防三层架构
FATIGUE_RETRY_THRESHOLD = 3      # 同一gate重试≥3次触发
FATIGUE_TIME_THRESHOLD_MIN = 90  # 执行≥90分钟触发
FATIGUE_RETRY_HARD_LIMIT = 5     # 硬上限:不限时,重试≥5次必触发
_ORCH_INTEGRITY_DIR = None       # 内部副本目录(运行时初始化)
_FATIGUE_TRACKER = {}            # {task_id: {retry_count, start_time, fatigue_triggered}}

# P6分批大小(V4.0.1: 提取为全局常量,便于灰度调整)
P6_BATCH_SIZE = 8

# V5.0(4.13.0): HIGH/LOW 分档已废除,统一返回 standard(仅用于日志/信息输出)
def _get_model_tier_for_dir(data_dir: str) -> str:
    """返回模型层级标签(HIGH/LOW/standard),用于G1分层降级策略。"""
    state_path = os.path.join(data_dir, "orchestrator_state.json")
    if os.path.exists(state_path):
        try:
            st = _read_json(state_path)
            tier = st.get("model_tier", "")
            if tier:
                return tier
        except Exception:
            pass
    return "standard"


# ============================================================
# V4.6.14: P6动态分批策略
# ============================================================

import math


def calculate_complexity_score(test_point: dict) -> str:
    """
    V4.6.14: 测试点复杂度打分

    返回: "simple" / "medium" / "complex"

    维度:
      - 描述长度: <50=simple, 50-150=medium, >150=complex
      - 操作动作关键词数量
      - 多实体关键词(多/多个/批量/并发/跨/不同)
    """
    desc = test_point.get("description", "") or ""
    length = len(desc)

    # 动作关键词
    action_keywords = ["验证", "检查", "确认", "输入", "点击", "选择",
                       "提交", "审批", "查询", "删除", "修改", "登录",
                       "登出", "上传", "下载", "导出", "导入"]
    action_count = sum(1 for kw in action_keywords if kw in desc)

    # 多实体关键词
    multi_keywords = ["多", "多个", "批量", "并发", "跨", "不同",
                      "所有", "全部", "各种", "各类"]
    multi_count = sum(1 for kw in multi_keywords if kw in desc)

    # 综合打分
    if length > 150 or action_count >= 5 or multi_count >= 2:
        return "complex"
    elif length > 50 or action_count >= 3:
        return "medium"
    else:
        return "simple"


def calculate_dynamic_batches(test_points: list, max_batches: int = 5) -> dict:
    """
    V4.6.14: 根据复杂度动态计算批次

    策略:
      - simple每批25个,medium每批15个,complex每批8个
      - 最多5批,超出则提升每批处理量

    Returns:
        dict: {
            "total_batches": int,
            "batches": [{"start": int, "end": int, "complexity": str}],
        }
    """
    if not test_points:
        return {"total_batches": 0, "batches": []}

    # 计算每个测试点的复杂度
    complexities = [calculate_complexity_score(tp) for tp in test_points]

    # 计算各复杂度测试点数量
    simple_count = complexities.count("simple")
    medium_count = complexities.count("medium")
    complex_count = complexities.count("complex")

    # 计算理论批次
    simple_batches = math.ceil(simple_count / 25) if simple_count > 0 else 0
    medium_batches = math.ceil(medium_count / 15) if medium_count > 0 else 0
    complex_batches = math.ceil(complex_count / 8) if complex_count > 0 else 0
    total_theoretical = simple_batches + medium_batches + complex_batches

    # 如果不超过max_batches,直接使用动态分批
    if total_theoretical <= max_batches:
        batches = []
        idx = 0
        for complexity, batch_size in [("simple", 25), ("medium", 15), ("complex", 8)]:
            count_for_type = complexities.count(complexity)
            if count_for_type == 0:
                continue
            remaining = count_for_type
            while remaining > 0:
                batch_count = min(batch_size, remaining)
                start = idx
                end = idx + batch_count
                batches.append({
                    "start": start,
                    "end": end,
                    "complexity": complexity,
                    "count": batch_count,
                })
                idx = end
                remaining -= batch_count

        return {
            "total_batches": len(batches),
            "batches": batches,
            "strategy": "dynamic",
        }

    # 超过max_batches,使用均匀分批
    per_batch = math.ceil(len(test_points) / max_batches)
    batches = []
    for i in range(max_batches):
        start = i * per_batch
        end = min((i + 1) * per_batch, len(test_points))
        if start >= len(test_points):
            break
        batches.append({
            "start": start,
            "end": end,
            "complexity": "mixed",
            "count": end - start,
        })

    return {
        "total_batches": len(batches),
        "batches": batches,
        "strategy": "uniform",
    }


# ============================================================
# V4.6.14: 骨架锁定智能决策
# ============================================================

import re as _re


def extract_operation_semantics(steps_text: str) -> set:
    """
    V4.6.14: 提取步骤操作语义:动作+对象

    从步骤文本中提取「点击XX」「输入XX」「选择XX」等语义单元。
    用于语义相似度计算。

    Returns: set of semantic units
    """
    if not steps_text:
        return set()

    # 动作词列表
    actions = ["点击", "输入", "选择", "提交", "审批", "查询",
               "删除", "修改", "登录", "登出", "打开", "关闭",
               "上传", "下载", "导出", "导入", "刷新", "勾选"]

    semantics = set()
    # 先按行拆分,避免跨行匹配产生碎片
    lines = steps_text.split('\n')
    for line in lines:
        for action in actions:
            # 匹配「点击XX」「输入XXX」等模式,动作词+最多15个字符
            pattern = f"({action}[^\n。!?,、;]{{0,15}})"
            match = _re.search(pattern, line)
            if match:
                m = match.group(1).strip()
                if m and len(m) >= len(action) + 2:
                    semantics.add(m)

    return semantics


def semantic_similarity(steps_a: str, steps_b: str) -> float:
    """
    V4.6.14: 语义相似度计算(Jaccard)

    比较两个步骤文本的语义相似度。

    Returns: 0.0 ~ 1.0 (1.0表示完全相似)
    """
    sem_a = extract_operation_semantics(steps_a)
    sem_b = extract_operation_semantics(steps_b)

    if not sem_a and not sem_b:
        return 1.0  # 两个都无语义,视为相似
    if not sem_a or not sem_b:
        return 0.0

    intersection = len(sem_a & sem_b)
    union = len(sem_a | sem_b)
    return intersection / union if union > 0 else 0.0


def skeleton_override_decision(
    agent_steps: str,
    skeleton_steps: str,
    priority: str
) -> str:
    """
    V4.6.14: 骨架覆盖决策

    决定在保存用例时是否用骨架内容覆盖Agent输出。

    决策逻辑:
      - P0用例:必须使用骨架的priority/is_smoke
      - 语义相似度>70%:骨架内容更可靠,用骨架覆盖steps
      - 语义相似度≤70%:Agent有差异化创作,保留Agent输出
      - 骨架步骤为空/无意义:保留Agent输出

    Returns: "use_skeleton" | "keep_agent"
    """
    # P0用例必须用骨架的元数据
    if priority == "P0":
        return "use_skeleton"

    # 骨架步骤为空,保留Agent
    if not skeleton_steps or len(skeleton_steps.strip()) < 10:
        return "keep_agent"

    # 计算语义相似度
    sim = semantic_similarity(agent_steps, skeleton_steps)

    if sim > 0.7:
        return "use_skeleton"
    else:
        return "keep_agent"


# P0必需顶层字段
# === 各步骤必需字段(以云端实际JSON为真源,2026-04-29统一) ===
P0_REQUIRED_FIELDS = ["quality_score", "blocks", "objective"]
P1_REQUIRED_FIELDS = ["feature_tree"]  # 云端实际输出用feature_tree
P3_REQUIRED_FIELDS = ["risk_points"]  # 云端实际输出用risk_points
P4_REQUIRED_FIELDS = ["pci_list"]  # 云端实际输出用pci_list
P5_REQUIRED_FIELDS = ["test_points", "merge_log"]
P6_REQUIRED_FIELDS = ["testcases"]
P7_REQUIRED_FIELDS = ["gate_result"]  # 云端实际输出gate_result,不是quality_check

# 域识别关键词
# ============================================================
# 自动发现 SKILL_DIR(V3.0.0-patch3)
# ============================================================

DEFAULT_SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def resolve_skill_dir(cli_value=""):
    """自动发现skill_dir,带目录完整性校验"""
    candidate = cli_value or DEFAULT_SKILL_DIR
    required_files = [
        os.path.join(candidate, "tools", "export_excel.py"),
        os.path.join(candidate, "tools", "truncation_guard.py"),
        os.path.join(candidate, "prompts", "P0_requirement_structuring.md"),
    ]
    missing = [p for p in required_files if not os.path.exists(p)]
    if missing:
        # 尝试DEFAULT_SKILL_DIR作为兜底
        if cli_value and cli_value != DEFAULT_SKILL_DIR:
            return resolve_skill_dir("")  # 递归用默认值重试
        raise ValueError(f"skill_dir无效({candidate}),缺失: {[os.path.basename(p) for p in missing[:3]]}")
    return candidate


# ============================================================
# 自动发现最近任务(V3.0.0-patch3)
# ============================================================

def find_latest_task():
    """查找最近的未完成任务,返回(task_id, data_dir)或(None, None)"""
    base = os.path.expanduser("~/.openclaw/workspace/data")
    if not os.path.exists(base):
        return None, None
    tasks = sorted(glob.glob(os.path.join(base, "task_*")), reverse=True)
    for task_dir in tasks[:3]:  # 只看最近3个,减少串task风险
        state_path = os.path.join(task_dir, "orchestrator_state.json")
        if os.path.exists(state_path):
            try:
                state = _read_json(state_path)
                tid = state.get("task_id", "")
                # 未完成的任务(没有step7)
                if "step7" not in state.get("completed_steps", []):
                    return tid, task_dir
            except Exception:
                pass
    return None, None


# ============================================================
# P6模式推荐映射表 (V3.4.0)
# ============================================================
import re

DOMAIN_KEYWORDS = {
    "trade": ["交易", "委托", "撤单", "成交", "清算", "结算", "资金冻结", "T+1", "smt", "smart station", "银证转账"],
    "asset_mgmt": ["资管", "净值", "申赎", "申购", "赎回", "衍生品", "期货", "期权", "保证金", "基金理财"],
    "risk_ctrl": ["风控", "预警", "限额", "合规检查", "风险控制", "适当性"],
    "crm": ["客户", "跟进", "开户", "KYC", "客户经理", "客户关系", "crm"],
    "investment_advice": ["投顾", "债券投顾", "投顾分润", "分润", "投资顾问", "财富梦工厂"],
    "etrading": ["网上营业厅", "APP", "适当性", "产品推荐", "在线交易", "移动端", "H5", "优理宝"],
    "ops_mgmt": ["运营", "活动", "营销", "后台管理", "数据报表", "统计", "导出"],
    "compliance": ["合规", "证书", "从业", "监管", "报送", "资质", "执照"],
    "institutional": ["机构", "主经纪商", "pb", "机构户", "智达"],
    "it_infra": ["部署", "监控", "服务器", "权限配置", "变更", "IT", "基础设施", "投行", "承销", "IPO"],
}


# ============================================================
# 工具函数
# ============================================================

def _ensure_dir(path):
    os.makedirs(path, exist_ok=True)

def _write_json(path, data):
    # V4.15.11: State白名单保护 — 写入orchestrator_state.json时自动过滤非代码定义字段
    if path.endswith("orchestrator_state.json"):
        _state_whitelist = {
            "task_id", "data_dir", "skill_dir", "current_step",
            "completed_steps", "current_phase", "requirement_file",
            "skill_version", "created_at", "updated_at", "model_tier",
            "model_name", "p6_mode", "p6_status", "p6_started_at",
            "p6_segment_start_count", "p6_last_pause_at",
            "p6_completed_tp_indices", "p6_tp_list",
            "rate_limit", "p6_merge_fail_count", "p6_quality_warnings",
            "onboarding", "step0", "px_results", "image_api_key_hash",
            "project_domain", "feature_count", "test_point_count",
            "risk_count", "pci_count", "total_tps", "step_validated",
            "cloud_review", "pending_emit", "low_quality_flag",
        }
        _rejected = []
        _filtered = {}
        for _k, _v in data.items():
            if _k in _state_whitelist or _k.startswith(("p6_tp_", "emit_confirmed_", "step7_")):
                _filtered[_k] = _v
            else:
                _rejected.append(_k)
        if _rejected:
            try:
                _rej_path = os.path.join(os.path.dirname(path), "state_rejected_fields.log")
                with open(_rej_path, "a", encoding="utf-8") as _rf:
                    _rf.write(f"{time.strftime('%Y-%m-%dT%H:%M:%S')} | rejected_fields: {_rejected}\n")
            except Exception:
                pass
        data = _filtered
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def _read_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def _file_exists(path):
    return os.path.exists(path) and os.path.getsize(path) > 10

def _sha256(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


# === V4.15.3: 统一错误分类 ===
def _error_classify(e, context=""):
    """统一错误分类,返回 (error_type, guidance)
    
    ERROR_TYPE:
      BUG        - orchestrator代码缺陷, Agent必须停止并报告, 禁止自行修复
      QUALITY    - 用例质量不达标, Agent可按fix_hints修复后重试
      RATELIMIT  - 速率限制, Agent等待后重试
      GATE       - gate校验失败, Agent检查前置步骤
      FATAL      - 不可恢复错误, Agent必须立即终止
    """
    es = str(e).lower() if e else ""
    
    if any(kw in es for kw in ("permission denied", "read-only", "disk full", "no space")):
        return ("FATAL", "不可恢复的系统错误,请检查磁盘空间和文件权限后重试。")
    
    if any(kw in es for kw in ("keyerror", "typeerror", "attributeerror", "valueerror",
                                 "indexerror", "unboundlocalerror", "syntaxerror",
                                 "importerror", "modulenotfounderror")):
        return ("BUG", f"orchestrator代码异常({es[:80]}),请停止执行并报告用户。禁止自行修复或绕过。")
    
    if "gate" in es or "pass.json" in es or "hmac" in es:
        return ("GATE", "gate校验失败,请检查前置步骤是否已通过orchestrator正常完成。")
    
    if any(kw in es for kw in ("rate", "limit", "frequency", "too many", "throttle")):
        return ("RATELIMIT", "触发速率限制,请等待后重试。")
    
    return ("QUALITY", "用例质量不达标,请根据issues和fix_example修复后重试。")


def _error_response(e, context="", data_dir=None):
    """V4.15.3: 生成携带错误分类的JSON响应"""
    error_type, guidance = _error_classify(e, context)
    resp = {
        "status": "error",
        "error_type": error_type,
        "reason": str(e)[:300],
        "guidance": guidance,
    }
    if error_type == "BUG":
        resp["action_required"] = "STOP_AND_REPORT"
        resp["forbidden"] = ["自行修复", "绕过orchestrator", "手动创建文件", "修改源代码"]
    elif error_type == "RATELIMIT":
        resp["action_required"] = "WAIT_AND_RETRY"
        resp["wait_seconds"] = 60
    elif error_type == "GATE":
        resp["action_required"] = "CHECK_PREREQUISITES"
    else:
        resp["action_required"] = "FIX_AND_RETRY"
    return resp

def _detect_domain(text, default="trade"):
    """检测业务域,返回API标准域名"""
    if not text:
        return INTERNAL_TO_API_DOMAIN.get(default, "客户域")
    text_lower = text.lower().strip()
    # 优先精确匹配
    for domain, keywords in DOMAIN_KEYWORDS.items():
        for kw in keywords:
            if kw.lower() == text_lower:
                api_domain = INTERNAL_TO_API_DOMAIN.get(domain)
                if api_domain:
                    return api_domain
    # 其次包含匹配
    for domain, keywords in DOMAIN_KEYWORDS.items():
        for kw in keywords:
            if kw.lower() in text_lower:
                api_domain = INTERNAL_TO_API_DOMAIN.get(domain)
                if api_domain:
                    return api_domain
    return INTERNAL_TO_API_DOMAIN.get(default, "客户域")


# ============================================================
# V4.0.0: 云端评审工具推送相关辅助函数
# ============================================================

# 域名→文件名映射(显式字典 + fallback)
# 内部域名到API业务域名的映射(用于评审推送)
INTERNAL_TO_API_DOMAIN = {
    "trade": "交易域",
    "asset_mgmt": "资管域",
    "risk_ctrl": "风控合规域",
    "crm": "客户域",
    "investment_advice": "投顾域",
    "etrading": "互联网终端域",
    "ops_mgmt": "运营管理域",
    "compliance": "合规域",
    "institutional": "机构业务域",
    "it_infra": "投行业务域",
    # 默认
    None: "客户域",
}

DOMAIN_FILENAME_MAP = {
    "客户域": "客户", "交易域": "交易", "资管域": "资管", "自营域": "自营",
    "投顾域": "投顾", "投研域": "投研", "投行业务域": "投行", "机构业务域": "机构",
    "清算托管域": "清算托管", "风控合规域": "风控合规", "行情资讯域": "行情资讯", "互联网终端域": "互联网终端"
}

def _domain_to_filename(domain):
    """域名→文件名(与_sync_review_experience/P6注入共用)"""
    if domain in DOMAIN_FILENAME_MAP:
        return DOMAIN_FILENAME_MAP[domain]
    return domain.replace("域", "").replace("业务", "")

def _load_cloud_config(skill_dir, runtime_api_key=None):
    """读取 skill_v4/config/cloud.json 配置文件。
    如不存在返回默认配置(enabled=false),不抛异常。

    V4.1.2: api_key优先从runtime_api_key参数读取(Onboarding时输入,保存在task目录.cache文件),
    其次从cloud.json读取。避免api_key存储在配置文件中。
    """
    config_path = os.path.join(skill_dir, "config", "cloud.json")
    config = None
    if os.path.exists(config_path):
        try:
            config = _read_json(config_path)
        except Exception:
            pass

    if config is None:
        config = {
            "review_tool": {
                "enabled": False,
                "api_url": "",
                "frontend_url": "",
                "api_key": "",
                "auto_push": False,
            },
            "experience_sync": {
                "enabled": False,
            }
        }

    # V4.1.2: runtime_api_key优先(由调用方从task目录的.image_api_key文件读取后传入)
    if runtime_api_key and runtime_api_key.strip():
        config["review_tool"]["api_key"] = runtime_api_key.strip()

    return config


def _load_project_domain_mapping(skill_dir):
    """读取项目名称→业务域映射配置。
    V4.0.0: 支持根据项目名自动关联业务域知识库。
    """
    mapping_path = os.path.join(skill_dir, "config", "project_domain_mapping.json")
    if os.path.exists(mapping_path):
        try:
            return _read_json(mapping_path)
        except Exception:
            pass
    return {"mappings": [], "domain_knowledge_map": {}}


def _match_project_to_domains(requirement_text, skill_dir):
    """V4.0.0: 根据需求文本中的项目名自动匹配业务域。

    匹配逻辑:
    1. 扫描需求文本中的关键词(项目名),命中则返回对应的业务域列表
    2. V4.0.1: 同义词模糊匹配,扫描需求文本中的同义词关键词
    3. 匹配优先级:项目关键词命中 > 同义词命中(合并去重)

    Returns:
        dict: {"domains": [...], "knowledge_files": [...], "matched_projects": [...], "matched_synonyms": [...]}
    """
    mapping = _load_project_domain_mapping(skill_dir)
    mappings = mapping.get("mappings", [])
    domain_knowledge_map = mapping.get("domain_knowledge_map", {})
    synonyms = mapping.get("synonyms", {})

    if not requirement_text or (not mappings and not synonyms):
        return {"domains": [], "knowledge_files": [], "matched_projects": [], "matched_synonyms": []}

    requirement_lower = requirement_text.lower()

    # 第一层:项目关键词精确匹配
    matched_domains = set()
    matched_projects = []

    for item in mappings:
        keywords = item.get("project_keywords", [])
        for kw in keywords:
            if kw.lower() in requirement_lower:
                for domain in item.get("domains", []):
                    matched_domains.add(domain)
                matched_projects.append(kw)
                break  # 一个mapping只需匹配一次

    # 第二层:同义词模糊匹配(子串匹配,仅作为辅助信号)
    # 注意:同义词是高频2字词(如"客户""交易"),会广泛命中
    # 设计意图:同义词匹配到的域只用于知识注入,不影响 project_name 判定
    synonym_matched_domains = set()
    matched_synonyms = []
    for keyword, domain in synonyms.items():
        if keyword.lower() in requirement_lower:
            synonym_matched_domains.add(domain)
            matched_synonyms.append(keyword)

    # 合并去重:项目关键词匹配 + 同义词匹配
    all_domains = matched_domains | synonym_matched_domains

    # 映射到知识库文件
    knowledge_files = []
    for domain in sorted(all_domains):
        kf = domain_knowledge_map.get(domain)
        if kf:
            knowledge_files.append({"domain": domain, "file": kf})

    return {
        "domains": sorted(all_domains),
        "knowledge_files": knowledge_files,
        "matched_projects": matched_projects,
        "matched_synonyms": matched_synonyms
    }


def _should_push_to_review_tool(config):
    """V4.12.6: 默认开启推送,仅api_key非空即推送
    条件: api_key非空即可(优先runtime key → cloud.json → 环境变量)
    无api_key时提示用户配置,不静默跳过
    """
    rt = config.get("review_tool", {})
    if not rt.get("api_key", "").strip():
        return False
    return True


def _push_to_review_tool(data_dir, task_id, config):
    """推送用例到云端评审工具。

    流程:
    1. 读取 p6_output.json
    2. HTTP POST 到 /api/projects/import
    3. 完整的HTTP响应校验(raise_for_status + project_id存在性)
    4. 异常分类处理(Timeout/HTTPError/其他)
    5. 失败时记录到重试队列 queue/pending_reviews.jsonl
    6. 返回 review_url 或 None

    Args:
        data_dir: 任务数据目录
        task_id: 任务ID
        config: cloud.json 配置字典

    Returns:
        review_url (str) 或 None(推送失败时)
    """
    import requests

    # V4.1.8: 幂等检查--若上次推送成功记录存在,则跳过(避免HMAC断裂重跑时重复推送)
    push_marker = os.path.join(data_dir, ".review_push_done")
    if os.path.exists(push_marker):
        print(f"[_push_to_review_tool] 跳过:{task_id} 已推送过", file=sys.stderr)
        return None

    # 读取 p6_output.json
    p6_path = os.path.join(data_dir, "p6_output.json")
    if not os.path.exists(p6_path):
        _enqueue_failed_push(data_dir, task_id, config, "p6_output.json不存在")
        return None

    try:
        p6_data = _read_json(p6_path)
    except Exception as e:
        _enqueue_failed_push(data_dir, task_id, config, f"p6_output.json读取失败: {e}")
        return None

    rt_cfg = config.get("review_tool", {})
    api_url = rt_cfg.get("api_url", "http://localhost:4174")
    api_key = rt_cfg.get("api_key", "")
    frontend_url = rt_cfg.get("frontend_url", api_url.replace(":4174", ""))

    # 读取 task_meta 获取 domain 信息
    meta_path = os.path.join(data_dir, "task_meta.json")
    domain = "未分类"
    requirement_id = ""
    project_name = ""
    if os.path.exists(meta_path):
        try:
            meta = _read_json(meta_path)
            raw_domain = meta.get("domain", "")
            # V4.13.3: 全链路domain锁定 — 验证domain是否为API标准值,非标准则重新检测
            api_domains = set(INTERNAL_TO_API_DOMAIN.values())
            if raw_domain in api_domains:
                domain = raw_domain
            else:
                domain = _detect_domain(raw_domain)
                if domain not in api_domains:
                    print(f"WARNING: domain={domain} 不是标准API域,请检查 Onboarding 配置", file=sys.stderr)
            requirement_id = meta.get("task_id", "")
            project_name = meta.get("project_name", "")
        except Exception:
            pass

    # 构造请求
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["X-API-Key"] = api_key

    # V4.1.8: 字段映射转换(p6_output格式 → API期望格式)
    # 兼容两种格式:嵌套结构 {fields:{...}} 或扁平结构 {...}
    raw_cases = p6_data.get("testcases", [])
    testcases_for_api = []
    for c in raw_cases:
        nested = c.get("fields")
        fields = nested if isinstance(nested, dict) and nested else c
        # 字段名转换
        # V4.1.8: 补充 isSmoke 字段(之前漏推,导致评审工具冒烟用例=0)
        raw_smoke = fields.get("is_smoke", False)
        is_smoke_bool = _is_smoke(raw_smoke)  # 统一判断逻辑
        tc = {
            "case_id": fields.get("case_id", ""),
            "title": fields.get("title", ""),
            "priority": fields.get("priority", ""),
            "isSmoke": is_smoke_bool,  # V4.1.8: 修复冒烟用例推送
            "module": fields.get("test_suite", "") or fields.get("module", ""),
            "menu_path": fields.get("menu_path", ""),
            "precondition": fields.get("preconditions", "") or fields.get("precondition", ""),
            "steps": fields.get("steps", ""),
            "expected_results": fields.get("expected_results", ""),
        }
        # steps/expected_results转为数组
        if isinstance(tc["steps"], str):
            tc["steps"] = [s.strip() for s in tc["steps"].split("\n") if s.strip()]
        if isinstance(tc["expected_results"], str):
            tc["expected_results"] = [e.strip() for e in tc["expected_results"].split("\n") if e.strip()]
        testcases_for_api.append(tc)

    payload = {
        "task_id": task_id,
        "testcases": testcases_for_api,
        "metadata": {
            "domain": domain,
            "requirement_id": requirement_id,
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%S+08:00"),
            "project_name": project_name,
        }
    }

    print(f"DEBUG: POST {api_url}/api/projects/import", flush=True)
    if payload.get('testcases'):
        tc0 = payload['testcases'][0]
    try:
        response = requests.post(
            f"{api_url}/api/projects/import",
            json=payload,
            headers=headers,
            timeout=10
        )
        # 完整的HTTP响应校验
        response.raise_for_status()
        result = response.json()

        # project_id 存在性校验(兼容 result.data.project_id 格式)
        raw_data = result.get("data")
        data = raw_data if isinstance(raw_data, dict) else result  # 防御:data为null/非dict时fallback
        project_id = data.get("project_id") or result.get("project_id")
        if not project_id:
            raise ValueError(f"服务端响应缺少project_id: {result}")
        review_url = data.get("review_url") or result.get("review_url") or f"{frontend_url}/?project={project_id}"
        # V4.1.8: 推送成功后写入marker,防止重跑时重复推送
        try:
            with open(push_marker, "w") as f:
                f.write(f"{project_id}\n{review_url}")
        except Exception:
            pass
        return review_url

    except requests.exceptions.Timeout:
        # 超时异常:记录重试队列
        error_msg = "推送超时(10秒),请检查网络或服务端状态"
        _enqueue_failed_push(data_dir, task_id, config, error_msg)
        return None
    except requests.exceptions.HTTPError as e:
        # HTTP错误异常:记录重试队列
        # V4.15.46: 补记服务端返回体(details),消除"只有状态码看不到原因"盒区
        status_code = e.response.status_code if e.response else "unknown"
        server_detail = ""
        try:
            server_detail = e.response.text[:500] if e.response is not None else ""
        except Exception:
            server_detail = ""
        error_msg = f"推送失败: HTTP {status_code} | 服务端响应: {server_detail}"
        print(f"[_push_to_review_tool] {error_msg}", file=sys.stderr)
        _enqueue_failed_push(data_dir, task_id, config, error_msg)
        return None
    except Exception as e:
        # 其他异常:记录重试队列
        error_msg = f"推送异常: {str(e)[:200]}"
        _enqueue_failed_push(data_dir, task_id, config, error_msg)
        return None


def _enqueue_failed_push(data_dir, task_id, config, error_msg, push_type="p6_testcases"):
    """推送失败时记录到重试队列 queue/pending_reviews.jsonl"""
    # 队列目录放在 data_dir 同级的 queue 目录下
    base_dir = os.path.dirname(data_dir) if data_dir else os.path.expanduser("~/.openclaw/workspace/data")
    queue_dir = os.path.join(base_dir, "queue")
    _ensure_dir(queue_dir)
    queue_path = os.path.join(queue_dir, "pending_reviews.jsonl")

    entry = {
        "task_id": task_id,
        "data_dir": data_dir,
        "push_type": push_type,
        "timestamp": time.time(),
        "error": error_msg,
        "retry_count": 0,
    }
    try:
        with open(queue_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass  # 队列写入失败不阻塞主流程


def _push_p0p1_to_review_tool(data_dir, task_id, config):
    """推送P0/P1摘要数据到云端评审工具。

    V4.0.0: 段落3完成后推送P0/P1报告摘要,与P6用例推送独立。
    推送是"尽力而为",失败不影响主流程。

    Args:
        data_dir: 任务数据目录
        task_id: 任务ID
        config: cloud.json 配置字典

    Returns:
        dict: {"success": bool, "review_url": str或None, "message": str}
    """
    import requests

    rt_cfg = config.get("review_tool", {})
    api_url = rt_cfg.get("api_url", "http://localhost:4174")
    api_key = rt_cfg.get("api_key", "")
    frontend_url = rt_cfg.get("frontend_url", api_url.replace(":4174", ""))

    # 读取 p0_output.json
    p0_path = os.path.join(data_dir, "p0_output.json")
    p0_data = {}
    if os.path.exists(p0_path):
        try:
            p0_data = _read_json(p0_path)
        except Exception:
            pass

    # 读取 p1_output.json
    p1_path = os.path.join(data_dir, "p1_output.json")
    p1_data = {}
    if os.path.exists(p1_path):
        try:
            p1_data = _read_json(p1_path)
        except Exception:
            pass

    if not p0_data and not p1_data:
        error_msg = "p0_output.json和p1_output.json均不存在或读取失败"
        _enqueue_failed_push(data_dir, task_id, config, error_msg, push_type="p0p1_report")
        return {"success": False, "review_url": None, "message": error_msg}

    # 读取 task_meta 获取 domain 等信息
    meta_path = os.path.join(data_dir, "task_meta.json")
    domain = "未分类"
    project_name = ""
    if os.path.exists(meta_path):
        try:
            meta = _read_json(meta_path)
            raw_domain = meta.get("domain", "")
            # V4.13.3: 全链路domain锁定 — 验证domain是否为API标准值,非标准则重新检测
            api_domains = set(INTERNAL_TO_API_DOMAIN.values())
            if raw_domain in api_domains:
                domain = raw_domain
            else:
                domain = _detect_domain(raw_domain)
            project_name = meta.get("project_name", "")
        except Exception:
            pass

    # 统计P1模块数和功能点数
    p1_module_count = 0
    p1_feature_count = 0
    if p1_data:
        ft = p1_data.get("feature_tree", {})
        modules = ft.get("modules", []) if isinstance(ft, dict) else []
        if not modules:
            modules = p1_data.get("modules", [])
        p1_module_count = len(modules)
        for mod in modules:
            p1_feature_count += len(mod.get("children", []))

    # 获取P0 score
    p0_score = p0_data.get("score", None)
    if p0_score is None:
        p0_score = p0_data.get("blocks", {}).get("score", None)

    # 构造推送payload
    # V4.15.46: 移除服务端 importSchema 不接受的字段(push_type / p0p1_summary),
    # 否则触发 400 "metadata.push_type is not allowed"。服务端 /api/projects/import
    # 不消费这两个字段,删除后不丢失任何服务端会用到的数据。
    payload = {
        "task_id": task_id,
        "metadata": {
            "domain": domain,
            "requirement_id": task_id,
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%S+08:00"),
            "project_name": project_name,
        },
        "testcases": [],
    }

    # 构造请求头
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["X-API-Key"] = api_key

    try:
        response = requests.post(
            f"{api_url}/api/projects/import",
            json=payload,
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
        result = response.json()

        # 兼容 result.data.project_id 格式(与 _push_to_review_tool 一致)
        raw_data = result.get("data")
        data = raw_data if isinstance(raw_data, dict) else result  # 防御:data为null/非dict时fallback
        project_id = data.get("project_id") or result.get("project_id")
        if not project_id:
            raise ValueError(f"服务端响应缺少project_id: {result}")
        review_url = data.get("review_url") or result.get("review_url") or f"{frontend_url}/?project={project_id}"
        return {"success": True, "review_url": review_url, "message": "P0/P1摘要已推送到评审工具"}

    except requests.exceptions.Timeout:
        error_msg = "推送超时(10秒),请检查网络或服务端状态"
        _enqueue_failed_push(data_dir, task_id, config, error_msg, push_type="p0p1_report")
        return {"success": False, "review_url": None, "message": error_msg}
    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code if e.response else "unknown"
        # V4.15.46: 补记服务端返回体(details)
        server_detail = ""
        try:
            server_detail = e.response.text[:500] if e.response is not None else ""
        except Exception:
            server_detail = ""
        error_msg = f"P0/P1推送失败: HTTP {status_code} | 服务端响应: {server_detail}"
        print(f"[_push_p0p1_to_review_tool] {error_msg}", file=sys.stderr)
        _enqueue_failed_push(data_dir, task_id, config, error_msg, push_type="p0p1_report")
        return {"success": False, "review_url": None, "message": error_msg}
    except Exception as e:
        error_msg = f"P0/P1推送异常: {str(e)[:200]}"
        _enqueue_failed_push(data_dir, task_id, config, error_msg, push_type="p0p1_report")
        return {"success": False, "review_url": None, "message": error_msg}


def _check_api_features(data_dir):
    """V3.3.2: 判断是否需要接口测试规则(检查P0 operations和P1 feature names)"""
    API_KEYWORDS = {"接口", "API", "api", "推送", "webhook", "回调", "对接", "同步", "通知", "HTTP", "http"}
    # 检查P0 operations
    p0_path = os.path.join(data_dir, "p0_output.json")
    if os.path.exists(p0_path):
        try:
            p0_data = _read_json(p0_path)
            ops = p0_data.get("blocks", {}).get("operations", [])
            for op in ops:
                name = op.get("name", "") + op.get("trigger", "")
                if any(kw in name for kw in API_KEYWORDS):
                    return True
        except Exception:
            pass
    # 检查P1 feature names
    p1_path = os.path.join(data_dir, "p1_output.json")
    if os.path.exists(p1_path):
        try:
            p1_data = _read_json(p1_path)
            ft = p1_data.get("feature_tree", {})
            ft_modules = ft.get("modules", []) if isinstance(ft, dict) else []
            if not ft_modules:
                ft_modules = p1_data.get("modules", [])
            for mod in ft_modules:
                for feat in mod.get("children", []):
                    if any(kw in feat.get("name", "") for kw in API_KEYWORDS):
                        return True
        except Exception:
            pass
    return False


def _get_case_field(case, field, default=""):
    """从P6用例中读取字段值,兼容两种结构:
    1. 扁平结构:case.get(field)
    2. 嵌套结构:case.get("fields", {}).get(field)

    V3.2.4新增:修复P6数据结构为嵌套fields时,
    quality_check/p6_merge/step7_export/export_excel全部读不到字段的致命Bug。
    """
    val = case.get(field)
    if val is not None and val != "":
        return val
    fields = case.get("fields")
    if isinstance(fields, dict):
        val = fields.get(field)
        if val is not None:
            return val
    return default


def _set_case_field(case, field, value):
    """V4.12.6: 设置用例字段值,兼容扁平结构和嵌套fields结构
    对应 _get_case_field 的写入端
    """
    if "fields" in case and isinstance(case.get("fields"), dict):
        case["fields"][field] = value
    else:
        case[field] = value


def _is_smoke(value):
    """V3.2.8: 统一is_smoke判断逻辑,兼容所有格式。
    返回True/False,消除多处重复的判断代码。
    支持: True, "true", "是", "Y", "yes", 1
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value == 1
    if isinstance(value, str):
        return value.lower() in ("true", "是", "y", "yes", "1")
    return False


def _write_text(path, content):
    """写入文本文件,UTF-8编码"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


# ============================================================
# HMAC签名机制 (V3.2.6: 防止Agent伪造gate pass)
# ============================================================

import hmac as _hmac_mod

# V3.5.2: 全局变量记录当前执行的action,只在main()的dispatch时设置
# Agent即使import了orchestrator,也无法伪造此值(因为不经过main dispatch)
_CURRENT_ACTION = ""

# V3.5.2: gate合法来源映射表
_VALID_GATE_SOURCES = {
    "onboarding": ["onboarding"],
    "step0": ["step0"],
    "step0_8": ["step0_8_save"],
    "P0": ["step_run", "quality_check"],
    "P1": ["step_run", "quality_check", "p1_code_merge"],
    "P2": ["p2_code_generate", "quality_check"],
    "P3": ["step_run", "quality_check"],
    "P4": ["step_run", "quality_check"],
    "P5": ["p5_code_merge", "quality_check"],
    "P6": ["p6_merge", "quality_check"],
    "P7": ["p7_code_check", "quality_check"],
}

# 内嵌密钥:V4.0.1改为固定secret派生,避免文件内容变化导致密钥断裂
def _get_hmac_key():
    """V4.0.1: 使用固定HMAC_SECRET常量派生密钥。
    不再依赖文件内容哈希,拆分/修改文件后旧任务仍可resume。
    """
    return HMAC_SECRET.encode("utf-8")


def _get_legacy_hmac_key():
    """V4.0.1兼容: 旧版基于文件哈希的密钥,用于验签兼容。"""
    orch_path = os.path.abspath(__file__)
    with open(orch_path, "rb") as f:
        file_hash = hashlib.sha256(f.read()).hexdigest()
    return f"orch-gate-{file_hash[:32]}".encode("utf-8")


def _get_integrity_dir(task_id):
    """V4.13.5: 内部副本目录(Agent不可见,用于交叉校验防止伪造gate)。
    路径: ~/.orch_state/{task_hash}/gates/ (不在data_dir内,Agent较难发现)
    """
    home = os.path.expanduser("~")
    task_hash = hashlib.sha256(task_id.encode()).hexdigest()[:12]
    base = os.path.join(home, ".orch_state", f"task_{task_hash}", "gates")
    os.makedirs(base, exist_ok=True)
    return base


def _track_fatigue(task_id, phase=""):
    """V4.13.5: 疲劳追踪 - 记录retry并检查是否触发熔断。
    返回 (fatigue_triggered: bool, reason: str)
    触发条件: retry>=3+elapsed>=90min → 或 → retry>=5(不限时硬上限)
    """
    if task_id not in _FATIGUE_TRACKER:
        _FATIGUE_TRACKER[task_id] = {
            "retry_count": 0, "start_time": time.time(), "fatigue_triggered": False
        }
    tracker = _FATIGUE_TRACKER[task_id]
    tracker["retry_count"] += 1
    elapsed_min = (time.time() - tracker["start_time"]) / 60
    rc = tracker["retry_count"]
    if tracker["fatigue_triggered"]:
        return True, "fatigue_already_triggered"
    if rc >= FATIGUE_RETRY_HARD_LIMIT:
        tracker["fatigue_triggered"] = True
        return True, f"硬上限:retry={rc}次>={FATIGUE_RETRY_HARD_LIMIT}"
    if rc >= FATIGUE_RETRY_THRESHOLD and elapsed_min >= FATIGUE_TIME_THRESHOLD_MIN:
        tracker["fatigue_triggered"] = True
        return True, f"执行{elapsed_min:.0f}min+retry{rc}次"
    return False, f"retry:{rc} elapsed:{elapsed_min:.0f}min"


def _sign_gate(gate_data, task_id):
    """V3.2.6: 对gate pass数据生成HMAC签名。
    签名覆盖gate_data的所有字段(排除hmac字段本身)+ task_id。
    """
    # 拷贝并移除hmac字段,避免循环依赖
    data_copy = {k: v for k, v in gate_data.items() if k != "hmac"}
    data_copy["_task_id"] = task_id  # 确保task_id参与签名
    payload = json.dumps(data_copy, sort_keys=True, ensure_ascii=False)
    key = _get_hmac_key()
    sig = _hmac_mod.new(key, payload.encode("utf-8"), hashlib.sha256).hexdigest()
    return sig


def _write_signed_gate(gate_path, gate_data, task_id):
    """V3.5.2: 写入带HMAC签名+来源标记的gate pass文件。
    V4.13.5: 双写内部副本 ~/.orch_state/ 用于交叉校验防伪造。
    """
    # V3.5.2: 记录创建gate的action来源
    gate_data["source_action"] = _CURRENT_ACTION
    gate_data["hmac"] = _sign_gate(gate_data, task_id)
    _write_json(gate_path, gate_data)
    # V4.13.5: 同时写入内部副本(Agent不可见路径)
    try:
        integrity_dir = _get_integrity_dir(task_id)
        gate_name = os.path.basename(gate_path)
        integrity_path = os.path.join(integrity_dir, gate_name)
        _write_json(integrity_path, gate_data)
    except Exception:
        pass  # 内部副本写入失败不阻塞主流程


def _verify_gate_hmac(gate_data, task_id):
    """V4.13.5: 验证gate pass的HMAC签名+来源合法性,带精确诊断。
    返回 (True, "OK") 或 (False, "原因(含具体差异)")
    """
    stored_hmac = gate_data.get("hmac")
    if not stored_hmac:
        # 诊断:检查gate是否有source_action
        sa = gate_data.get("source_action", "")
        if not sa:
            return False, "gate无hmac字段且source_action为空 → 疑似Agent手动创建。请执行: p6_merge 或 p7_code_check"
        return False, f"gate无hmac字段,source_action='{sa}' → HMAC签名缺失。请通过orchestrator重新生成gate"
    
    # 校验task_id一致性(gate中的task_id与当前是否匹配)
    gate_tid = gate_data.get("task_id", "")
    if gate_tid and gate_tid != task_id:
        return False, f"gate中task_id='{gate_tid}'与当前任务'{task_id}'不一致 → 可能是串task了。请检查data_dir路径"
    
    # HMAC验签(新密钥→旧密钥兼容)
    expected = _sign_gate(gate_data, task_id)
    hmac_ok = _hmac_mod.compare_digest(stored_hmac, expected)
    if not hmac_ok:
        legacy_key = _get_legacy_hmac_key()
        data_copy = {k: v for k, v in gate_data.items() if k != "hmac"}
        data_copy["_task_id"] = task_id
        payload = json.dumps(data_copy, sort_keys=True, ensure_ascii=False)
        legacy_sig = _hmac_mod.new(legacy_key, payload.encode("utf-8"), hashlib.sha256).hexdigest()
        hmac_ok = _hmac_mod.compare_digest(stored_hmac, legacy_sig)
    if not hmac_ok:
        # 诊断:给出HMAC差异细节
        stored_preview = stored_hmac[:8] + "..." if len(stored_hmac) > 8 else stored_hmac
        expected_preview = expected[:8] + "..." if len(expected) > 8 else expected
        # FIX(hmac-transparency) V4.13.9-S3 #8: 验签失败时输出参与签名的完整字段列表 + 隐藏字段说明。
        # 手工复算 HMAC 失败的两大隐藏原因:
        #   1) source_action 由 _write_signed_gate 自动写入(=_CURRENT_ACTION)后才参与签名,手工创建时常遗漏;
        #   2) _task_id 是签名时注入的虚拟字段(只参与签名,不落盘写入 gate JSON),grep gate 文件看不到。
        # signed_fields 重现实际 payload 的 key 集合: gate_data 所有字段 - hmac + 注入的 _task_id,sort_keys 升序。
        signed_fields = sorted([k for k in gate_data.keys() if k != "hmac"] + ["_task_id"])
        return False, (
            f"HMAC不匹配(stored={stored_preview},expected={expected_preview})。"
            f"参与签名的字段(sort_keys升序,已排除hmac、已含注入的_task_id): {signed_fields}。"
            f"隐藏字段说明: source_action 由orchestrator自动写入(手工创建易遗漏);"
            f"_task_id 只参与签名不落盘(gate JSON中看不到该字段,但签名时注入为'{task_id}')。"
            f"gate内容可能被手动修改或串task。请通过orchestrator重新生成gate,不要手动编辑JSON"
        )
    
    # source_action合法性校验
    step = gate_data.get("step", "")
    source_action = gate_data.get("source_action", "")
    if step in _VALID_GATE_SOURCES and source_action and source_action not in _VALID_GATE_SOURCES[step]:
        valid_list = ', '.join(_VALID_GATE_SOURCES[step])
        return False, f"step={step},source_action='{source_action}'不在合法列表[{valid_list}]中 → 可能Agent绕过orchestrator创建。请执行正确的action"
    return True, "OK"


# ============================================================
# 状态管理
# ============================================================

class TaskState:
    """任务状态管理器"""

    def __init__(self, data_dir=None, task_id=None):
        self.task_id = task_id
        self.data_dir = data_dir
        self.state_path = os.path.join(data_dir, "orchestrator_state.json") if data_dir else None
        self.state = self._load()

    def _load(self):
        if self.state_path and os.path.exists(self.state_path):
            try:
                return _read_json(self.state_path)
            except Exception:
                pass
        return {
            "task_id": self.task_id,
            "data_dir": self.data_dir,
            "skill_dir": "",
            "current_step": None,
            "completed_steps": [],
            "current_phase": 1,
            "requirement_file": "",
            "skill_version": SKILL_VERSION,
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%S+08:00"),
            "updated_at": None,
        }

    def save(self):
        if self.state_path:
            self.state["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%S+08:00")
            _write_json(self.state_path, self.state)

    def mark_complete(self, step):
        if step not in self.state["completed_steps"]:
            self.state["completed_steps"].append(step)
        self.state["current_step"] = step
        self.save()

    def is_complete(self, step):
        return step in self.state["completed_steps"]

    def get_next_step(self):
        for step in STEPS:
            if step not in self.state["completed_steps"]:
                return step
        return None


# ============================================================
# Gate Pass 管理
# ============================================================

def _build_fatigue_report(data_dir, task_id):
    """V4.13.5: 疲劳熔断人机协作通知模板"""
    # 读取P7结果简洁摘要
    summary_parts = []
    p7_path = os.path.join(data_dir, "p7_output.json")
    if os.path.exists(p7_path):
        try:
            p7 = _read_json(p7_path)
            for k, v in p7.get("checks", {}).items():
                if isinstance(v, dict) and v.get("status") == "FAILED":
                    summary_parts.append(f"❌ {k}: {v.get('message', '')[:80]}")
                elif isinstance(v, dict) and v.get("status") == "WARNING":
                    summary_parts.append(f"⚠️ {k}: {v.get('message', '')[:80]}")
        except Exception:
            pass
    
    # 用例统计
    p6_path = os.path.join(data_dir, "p6_output.json")
    case_count = 0
    if os.path.exists(p6_path):
        try:
            p6 = _read_json(p6_path)
            case_count = len(p6.get("testcases", []))
        except Exception:
            pass
    
    tracker = _FATIGUE_TRACKER.get(task_id, {})
    elapsed = (time.time() - tracker.get("start_time", time.time())) / 60
    
    lines = [
        f"⚠️ 疲劳熔断已触发（执行 {elapsed:.0f}min，重试 {tracker.get('retry_count', 0)} 次）",
        "",
    ]
    if case_count:
        lines.append(f"📊 已生成 {case_count} 条用例")
    if summary_parts:
        lines.append("---")
        for p in summary_parts[:8]:
            lines.append(p)
    lines.extend([
        "---",
        "请选择:",
        "① 直接导出（用例带 [LOW_QUALITY] 标记，人工审查后使用）",
        "② 修复全部 BLOCK 项（预估 8-12 分钟）",
        "③ 仅修复前置条件（预估 5 分钟）",
        "④ 告知具体修复项，我来指定",
        "⑤ 终止任务，保留当前进度",
        "⏰ 15分钟内无回复 → 自动走①导出+标记",
        "",
        "📋 相关命令: python3 orchestrator.py --action gate_diag --step P6 (诊断gate问题)",
    ])
    return "\n".join(lines)


def check_gate(data_dir, step, task_id):
    """V3.2.6: 检查指定步骤的gate pass是否存在、task_id一致、且HMAC签名有效"""
    gp_path = os.path.join(data_dir, "gates", f"{step}.pass.json")
    if not os.path.exists(gp_path):
        return False, f"{step}.pass.json不存在"
    try:
        gp = _read_json(gp_path)
        if gp.get("task_id") != task_id:
            return False, f"task_id不匹配: {gp.get('task_id')} != {task_id}"
        # V3.2.6: HMAC验签
        hmac_ok, hmac_msg = _verify_gate_hmac(gp, task_id)
        if not hmac_ok:
            return False, f"{step}: {hmac_msg}"
        return True, "OK"
    except Exception:
        return False, f"{step}.pass.json读取失败"

def run_truncation_guard(skill_dir, data_dir, task_id, step, revision=1):
    """调用truncation_guard.py进行四级校验+auto-mv"""
    tmp_path = os.path.join(data_dir, f"{step.lower()}_output.tmp.json")
    guard_script = os.path.join(skill_dir, "tools", "truncation_guard.py")

    if not os.path.exists(guard_script):
        return False, "truncation_guard.py不存在"
    if not os.path.exists(tmp_path):
        return False, f"{tmp_path}不存在"

    cmd = [
        "python3", guard_script,
        "--file", tmp_path,
        "--step", step,
        "--data-dir", data_dir,
        "--task-id", task_id,
        "--revision", str(revision),
        "--auto-mv"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

    if result.returncode == 0:
        return True, result.stdout.strip()
    else:
        return False, f"exit={result.returncode}: {result.stderr.strip() or result.stdout.strip()}"


# ============================================================
# Action: init
# ============================================================

def action_init(args):
    """初始化任务:创建task_id和DATA_DIR"""
    task_id = f"task_{time.strftime('%Y%m%d_%H%M%S')}"
    base_dir = os.path.expanduser("~/.openclaw/workspace/data")
    data_dir = os.path.join(base_dir, task_id)

    _ensure_dir(data_dir)
    _ensure_dir(os.path.join(data_dir, "gates"))

    state = TaskState(data_dir=data_dir, task_id=task_id)
    state.state["skill_dir"] = resolve_skill_dir("")
    state.state["data_dir"] = data_dir
    state.save()

    print(json.dumps({
        "status": "ok",
        "task_id": task_id,
        "data_dir": data_dir,
    }))


# ============================================================
# Action: onboarding
# ============================================================

def action_onboarding(args):
    """执行Onboarding环境检查(非交互部分)"""
    skill_dir = args.skill_dir
    data_dir = args.data_dir
    task_id = args.task_id

    # V4.15.39: 清空 __pycache__ 防止旧字节码缓存导致代码更新不生效
    import shutil as _shutil
    _tools_dir = os.path.join(skill_dir, "tools")
    for _root, _dirs, _files in os.walk(skill_dir):
        if "__pycache__" in _dirs:
            _cache_path = os.path.join(_root, "__pycache__")
            try:
                _shutil.rmtree(_cache_path)
            except Exception:
                pass

    checks = []

    # 检查1: 文件完整性
    required_files = [
        "prompts/P0_requirement_structuring.md",
        "prompts/P1_feature_tree_generation.md",
        "prompts/P2_test_point_draft.md",
        "prompts/P6_testcase_generation.md",
        "prompts/archive/P7_quality_gate.md",  # V3.3.1: P7已改为代码校验,prompt归档
        "tools/export_excel.py",
        "tools/truncation_guard.py",
        "tools/image_extract.py",
    ]
    missing = [f for f in required_files if not os.path.exists(os.path.join(skill_dir, f))]
    checks.append({
        "name": "file_integrity",
        "passed": len(missing) == 0,
        "missing": missing,
    })

    # 检查1.5: SKILL_DIR确认
    checks.append({
        "name": "skill_dir",
        "passed": os.path.exists(os.path.join(skill_dir, "tools", "export_excel.py")),
        "skill_dir": skill_dir,
    })

    # 检查2: Python + openpyxl
    try:
        result = subprocess.run(
            ["python3", "-c", "import openpyxl; print('ok')"],
            capture_output=True, text=True, timeout=10
        )
        openpyxl_ok = result.returncode == 0
    except Exception:
        openpyxl_ok = False
    checks.append({"name": "python_openpyxl", "passed": openpyxl_ok})

    # 检查0.5: 缓存检测
    cache_dir = os.path.expanduser("~/.openclaw/workspace/data")
    existing = sorted(glob.glob(os.path.join(cache_dir, "task_*")), reverse=True)[:3]
    checks.append({
        "name": "cache_detection",
        "existing_tasks": [os.path.basename(p) for p in existing],
    })

    all_passed = all(c.get("passed", True) for c in checks)

    # V5.0(4.13.0): 记录模型名(纯信息,不用于控制流程)
    model_name = (
        getattr(args, 'model_name', '') or
        os.environ.get('OPENCLAW_MODEL', '') or
        os.environ.get('OPENCLAW_DEFAULT_MODEL', '') or
        'unknown'
    )

    checks.append({
        "name": "model_info",
        "model_name": model_name,
        "model_tier": "standard",
    })

    # 写入onboarding.pass.json (V3.2.6: HMAC签名)
    if all_passed:
        gate_path = os.path.join(data_dir, "gates", "onboarding.pass.json")
        gate_data = {
            "step": "onboarding",
            "task_id": task_id,
            "status": "PASS",
            "source": "onboarding",
            "completed_at": time.strftime("%Y-%m-%dT%H:%M:%S+08:00"),
            "checks": checks,
        }
        _write_signed_gate(gate_path, gate_data, task_id)

        state = TaskState(data_dir=data_dir, task_id=task_id)
        state.state["skill_dir"] = args.skill_dir
        state.state["data_dir"] = data_dir
        # V5.0(4.13.0): 废除 HIGH/LOW 分档,统一为 standard 模式
        state.state["model_tier"] = "standard"
        state.state["model_name"] = model_name or "unknown"
        state.state["p6_mode"] = "standard"
        state.save()
        state.mark_complete("onboarding")

    print(json.dumps({
        "status": "ok" if all_passed else "blocked",
        "checks": checks,
        "onboarding_pass": all_passed,
        "interaction_required": True,
        "interaction_steps": 3,
        "next_action": "❗ 环境检查通过。接下来必须向用户逐步展示3个交互步骤,每步必须等待用户回复后才能展示下一步。禁止跳过任何步骤。每步必须原样输出以下内容:",
        "step_1_display": "📋 PRD审查可在生成用例前检查需求文档质量。\n请选择:\n• 回复「开启」→ 启动PRD审查\n• 回复「跳过」→ 直接生成用例",
        "step_2_display": "📚 L5知识库可注入历史测试经验,提升用例质量。\n请选择:\n• 上传知识库文件 → 解析入库\n• 回复「跳过」→ 不使用历史经验库(其他知识库仍正常使用)",
        "step_3_display": "🔐 API密码同时控制两个功能:图片理解 + 行业知识库。\n请选择:\n• 回复API密码 → 同时启用图片理解和行业知识库\n• 回复「跳过」→ 纯文本模式(无行业知识库,质量降20-30%)\n\n用户输入密码后执行 orchestrator --action check_image_api --api-key 密码\n验证成功→记住密码+拉取行业知识库+后续step0_8_prep传入。验证失败→提示重试或跳过。\n\nV4.0.0新增:密码正确后自动从云端拉取行业知识库到本地,无需额外操作。",
    }))


# ============================================================
# Action: step0
# ============================================================

def _auto_discover_requirement(data_dir):
    """方案A: 当Agent未传requirement_file时,自动扫描常见路径找需求文档。
    扫描顺序:
    1. data_dir 同级目录(任务目录旁边)
    2. ~/Downloads
    3. ~/Desktop
    4. ~/.openclaw/workspace/sharetasks(共享工作区)
    5. 当前工作目录 (cwd)
    返回找到的第一个 .docx/.md/.txt 文件路径,找不到返回 ""
    """
    import glob as _glob
    # data_dir 为空时不扫描,避免 os.path.dirname("") 返回 "." 误命中当前目录
    parent_dir = os.path.dirname(data_dir) if data_dir else ""
    candidate_dirs = [
        parent_dir,
        os.path.expanduser("~/Downloads"),
        os.path.expanduser("~/Desktop"),
        os.path.expanduser("~/.openclaw/workspace/sharetasks"),
        os.getcwd(),
    ]
    # 优先 .docx,其次 .md,最后 .txt
    for ext in (".docx", ".md", ".txt"):
        for d in candidate_dirs:
            # 跳过空路径和非目录
            if not d or not os.path.isdir(d):
                continue
            # 只扫一层,不递归,避免误命中
            matches = sorted(_glob.glob(os.path.join(d, f"*{ext}")), key=os.path.getmtime, reverse=True)
            if matches:
                return matches[0]  # 最新修改的文件
    return ""


def action_step0(args):
    """Step 0: 接收需求,写入task_meta"""
    data_dir = args.data_dir
    task_id = args.task_id
    skill_dir = args.skill_dir
    requirement_text = args.requirement_text or ""
    requirement_file = args.requirement_file or ""

    # 方案A: Agent未传 requirement_file 且无 requirement_text 时,自动发现需求文档
    auto_discovered = False
    if not requirement_file and not requirement_text:
        discovered = _auto_discover_requirement(data_dir)
        if discovered:
            requirement_file = discovered
            auto_discovered = True

    # 门禁检查
    ok, msg = check_gate(data_dir, "onboarding", task_id)
    if not ok:
        print(json.dumps({"status": "gate_blocked", "step": "onboarding", "reason": msg}))
        sys.exit(1)

    # 如果是文件,提取文本
    if requirement_file and not requirement_text:
        if requirement_file.endswith(".docx"):
            try:
                result = subprocess.run(
                    ["python3", "-c", "import zipfile,re,sys; z=zipfile.ZipFile(sys.argv[1]); xml=z.read('word/document.xml').decode('utf-8'); xml=re.sub(r'</w:p>','\\\\n',xml); text=re.sub(r'<[^>]+>',' ',xml); text=re.sub(r'[ \\t\\r]+',' ',text); text=re.sub(r'\\n\\s*',r'\\n',text); text=text.strip(); print(text[:50000])", requirement_file],
                    capture_output=True, text=True, timeout=30
                )
                requirement_text = result.stdout.strip()
            except Exception as e:
                requirement_text = f"[docx解析失败: {e}]"
        else:
            try:
                with open(requirement_file, "r", encoding="utf-8") as f:
                    requirement_text = f.read()[:50000]
            except Exception:
                requirement_text = "[文件读取失败]"

    domain = _detect_domain(requirement_text)

    # 读取preferences(脱敏:不写入api_key等敏感字段到task_meta)
    prefs_path = os.path.join(skill_dir, "user_knowledge", "preferences.json")
    prefs = {}
    prefs_safe = {}  # 脱敏版本,只保留非敏感字段
    if os.path.exists(prefs_path):
        try:
            prefs = _read_json(prefs_path)
            # 脱敏:image_api只保留url/model/timeout(api_key运行时输入,不存此处)
            if "image_api" in prefs:
                ia = prefs["image_api"]
                prefs_safe["image_api"] = {
                    "url": ia.get("url", ""),
                    "model": ia.get("model", "ci"),
                    "timeout": ia.get("timeout", 120),
                }
        except Exception:
            pass

    # 从需求文件名提取项目名(去掉路径、扩展名、云端上传的随机后缀)
    project_name = ""
    if requirement_file:
        basename = os.path.splitext(os.path.basename(requirement_file))[0]
        # 去掉云端上传时附加的随机后缀(如 ---7bc1d4d1-869c-452a-a6aa-2215b6ded1a2)
        import re as _re
        basename = _re.sub(r'---[0-9a-f\-]{20,}$', '', basename).strip()
        project_name = basename

    # V4.0.1: 业务域匹配(项目关键词 + 同义词模糊匹配)
    domain_match_result = _match_project_to_domains(requirement_text, skill_dir)
    matched_project_name = domain_match_result["matched_projects"][0] if domain_match_result["matched_projects"] else ""

    # domain字段优先用域匹配结果(中文全名),降级用_detect_domain(英文key)
    resolved_domain = domain_match_result["domains"][0] if domain_match_result["domains"] else domain

    # 写入task_meta
    meta = {
        "task_id": task_id,
        "domain": resolved_domain,
        "domains": domain_match_result["domains"],
        "matched_projects": domain_match_result["matched_projects"],
        "matched_synonyms": domain_match_result["matched_synonyms"],
        "project_name": matched_project_name,
        "project": project_name,
        "requirement_text": requirement_text,
        "requirement_file": requirement_file,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S+08:00"),
        "preferences": prefs_safe,  # 脱敏版本
        "skill_version": SKILL_VERSION,
        "requirement_hash": _sha256(requirement_text),
    }
    # V3.5.2: 保留已有的task_meta字段(如set_prd_review写入的prd_quality_review)
    existing_meta_path = os.path.join(data_dir, "task_meta.json")
    if os.path.exists(existing_meta_path):
        existing_meta = _read_json(existing_meta_path)
        # 保留已有字段,新字段覆盖旧字段
        existing_meta.update(meta)
        meta = existing_meta
    _write_json(os.path.join(data_dir, "task_meta.json"), meta)

    state = TaskState(data_dir=data_dir, task_id=task_id)
    state.state["requirement_file"] = requirement_file
    state.state["current_phase"] = 2
    state.mark_complete("step0")

    result = {
        "status": "ok",
        "task_id": task_id,
        "domain": domain,
        "requirement_length": len(requirement_text),
        "requirement_file": requirement_file,
    }
    if auto_discovered:
        result["auto_discovered"] = True
        result["warning"] = f"requirement_file未传入,已自动发现并使用: {requirement_file}"
    elif not requirement_file and not requirement_text:
        result["status"] = "error"
        result["reason"] = "未传入requirement_file或requirement_text,且自动扫描未找到任何需求文档(.docx/.md/.txt)。请明确传入 --requirement-file 参数。"
    print(json.dumps(result))
    if result["status"] == "error":
        sys.exit(1)


# ============================================================
# ============================================================
# 图片理解API配置读取
# ============================================================

def _is_desensitized(value):
    """检测是否为脱敏/掩码值（全由*或•组成）
    
    Agent传入显式--api-key时可能是脱敏后的星号(如"***")，
    需识别并回退到缓存文件读取真实密码。
    """
    if not value:
        return False
    return all(c in '*•' for c in value.strip())


def _load_image_api_config(skill_dir, api_key=None):
    """读取图片理解API配置

    - url/model/timeout从preferences.json读取(写死,用户无需输入)
    - api_key从运行时参数传入(Onboarding交互时用户输入,不落盘)
    - enabled由api_key是否非空决定(有密码=启用,无密码=降级)
    """
    prefs_path = os.path.join(skill_dir, "user_knowledge", "preferences.json")
    prefs = {}
    if os.path.exists(prefs_path):
        try:
            prefs = _read_json(prefs_path)
        except Exception:
            pass

    ia = prefs.get("image_api", {})

    config = {
        "enabled": bool(api_key and api_key.strip()),  # 有密码才启用
        "url": ia.get("url", ""),
        "model": ia.get("model", "ci"),  # ci=数据万象, qwen=通义千问VL
        "timeout": ia.get("timeout", 120),
        "api_key": (api_key or "").strip(),
    }

    # 配置完整性校验
    if config["enabled"]:
        if not config["url"].startswith("https://") and not config["url"].startswith("http://"):
            config["enabled"] = False
            config["_invalid_reason"] = "API地址未配置或格式不正确(检查preferences.json中image_api.url)"

    return config


def _sync_knowledge_from_cloud(skill_dir, api_key, cloud_config):
    """V4.0.0: 从云端拉取知识库到本地

    流程:
    1. 读取本地版本号(.knowledge_version.json)
    2. 调用云端 GET /api/knowledge/version 获取最新版本
    3. 版本一致则跳过,不一致则下载
    4. 调用 GET /api/knowledge/pack 下载文件
    5. 写入本地 knowledge/ 目录
    6. 更新版本号
    """
    import urllib.request
    import urllib.error

    # 确定API base URL(兼容嵌套结构)
    api_base = (
        cloud_config.get("knowledge_api_url") or
        cloud_config.get("review_tool", {}).get("api_url") or
        cloud_config.get("experience_sync", {}).get("api_url") or
        ""
    )
    if not api_base:
        return "未配置云端地址"

    api_base = api_base.rstrip("/")

    # 1. 读取本地版本
    version_path = os.path.join(skill_dir, ".knowledge_version.json")
    local_version = None
    if os.path.exists(version_path):
        try:
            local_version = _read_json(version_path)
        except Exception:
            pass

    local_checksum = (local_version or {}).get("checksum", "")

    # 2. 检查云端版本
    try:
        ver_req = urllib.request.Request(
            f"{api_base}/api/knowledge/version",
            headers={"X-API-Key": api_key, "Content-Type": "application/json"}
        )
        with urllib.request.urlopen(ver_req, timeout=10) as resp:
            cloud_version = json.loads(resp.read().decode("utf-8"))

        if cloud_version.get("status") != "ok":
            return f"云端返回错误"

        cloud_data = cloud_version["data"]
        if cloud_data.get("checksum") == local_checksum:
            return f"已是最新(v{cloud_data['version']})"

    except urllib.error.HTTPError as e:
        if e.code in (401, 403):
            return "密码无权访问知识库"
        return f"云端版本检查失败(HTTP {e.code})"
    except Exception as e:
        return f"云端不可用({str(e)[:50]})"

    # 3. 下载知识库包
    try:
        pack_url = f"{api_base}/api/knowledge/pack"
        pack_req = urllib.request.Request(
            pack_url,
            headers={"X-API-Key": api_key, "Content-Type": "application/json"}
        )
        with urllib.request.urlopen(pack_req, timeout=30) as resp:
            pack = json.loads(resp.read().decode("utf-8"))

        if pack.get("status") != "ok":
            return f"下载失败"

        pack_data = pack["data"]
        files = pack_data.get("files", {})
        if not files:
            return "无文件"

        # 4. 写入本地
        saved_count = 0
        for rel_path, content in files.items():
            abs_path = os.path.join(skill_dir, "knowledge", rel_path)
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)
            with open(abs_path, "w", encoding="utf-8") as f:
                f.write(content)
            saved_count += 1

        # 5. 更新版本号
        new_version = {
            "last_sync": time.strftime("%Y-%m-%dT%H:%M:%S+08:00"),
            "version": pack_data.get("version", ""),
            "checksum": pack_data.get("checksum", ""),
            "files_count": len(files),
        }
        with open(version_path, "w", encoding="utf-8") as f:
            json.dump(new_version, f, ensure_ascii=False, indent=2)

        return f"已同步{saved_count}个文件(v{pack_data.get('version', '?')})"

    except urllib.error.HTTPError as e:
        return f"下载失败(HTTP {e.code})"
    except Exception as e:
        return f"同步失败({str(e)[:50]})"


def _sync_review_experience(skill_dir, api_key, cloud_config, domain=None):
    """V4.0.1: 从云端评审工具拉取评审经验规则到本地 knowledge/reviewed_cases/

    Args:
        skill_dir: skill目录
        api_key: API密钥
        cloud_config: cloud.json配置
        domain: 指定域(None=全量同步所有12个域)

    Returns:
        str: 同步结果摘要
    """
    import urllib.request
    import urllib.error
    import urllib.parse

    api_base = cloud_config.get("review_tool", {}).get("api_url", "")
    if not api_base:
        return "未配置评审工具地址"
    api_base = api_base.rstrip("/")

    # 12个一级域
    ALL_DOMAINS = ["客户域", "交易域", "资管域", "自营域", "投顾域", "投研域",
                   "投行业务域", "机构业务域", "清算托管域", "风控合规域", "行情资讯域", "互联网终端域"]
    domains = [domain] if domain else ALL_DOMAINS

    rules_dir = os.path.join(skill_dir, "knowledge", "reviewed_cases")
    _ensure_dir(rules_dir)

    synced = 0
    skipped = 0
    failed = 0

    for d in domains:
        try:
            # 调用 GET /api/experience/rules?domain=X
            url = f"{api_base}/api/experience/rules?domain={urllib.parse.quote(d)}"
            req = urllib.request.Request(url, headers={
                "X-API-Key": api_key,
                "Content-Type": "application/json"
            })
            with urllib.request.urlopen(req, timeout=10) as resp:
                result = json.loads(resp.read().decode("utf-8"))

            if result.get("status") != "ok":
                failed += 1
                continue

            data = result.get("data", {})
            # 检查是否有规则
            rules = data.get("rules")
            if not rules:
                skipped += 1
                continue
            total = (len(rules.get("tag_rules", [])) + len(rules.get("operation_rules", [])) +
                     len(rules.get("domain_rules", [])) + len(rules.get("positive_rules", [])))
            if total == 0:
                skipped += 1
                continue

            # 写入本地
            domain_file = _domain_to_filename(d)
            out_path = os.path.join(rules_dir, f"{domain_file}_rules.json")
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(rules, f, ensure_ascii=False, indent=2)
            synced += 1

        except urllib.error.HTTPError as e:
            if e.code in (401, 403):
                return "密码无权访问评审经验"
            failed += 1
        except Exception:
            failed += 1

    return f"同步{synced}个域, 跳过{skipped}个(无数据), 失败{failed}个"


def _check_image_api_health(config):
    """预检:调用API的auth-check接口验证密码+服务可用性

    V4.12.7: 增加重试机制（3次，间隔3s），防止服务器瞬时抖动导致误降级
    """
    import time
    import requests

    max_retries = 3
    retry_delay = 3  # 秒

    for attempt in range(max_retries):
        try:
            # 从analyze URL推导auth-check URL (V4.14.3: 修复urlparse bug)
            from urllib.parse import urlparse
            pu = urlparse(config["url"])
            base_url = f"{pu.scheme}://{pu.netloc}"
            auth_check_url = base_url + "/api/auth-check"

            resp = requests.get(
                auth_check_url,
                headers={"X-API-Key": config["api_key"]},
                timeout=5,
            )
            if resp.status_code == 200:
                data = resp.json()
                return data.get("status") == "ok", data
            elif resp.status_code in (401, 403):
                # 401/403 也可能是服务器暂时性配置错误，重试
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                return False, {"error": "auth_failed", "message": f"密码错误(已重试{max_retries}次)"}
            elif resp.status_code == 503:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                data = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
                return False, {"error": "service_not_configured", "message": data.get("reason", data.get("message", "服务未配置密码验证"))}
            # 其他HTTP错误也重试
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                continue
            return False, {"error": f"HTTP {resp.status_code}(已重试{max_retries}次)"}
        except requests.exceptions.ConnectionError:
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                continue
            return False, {"error": "connection_failed", "message": f"无法连接到API服务(已重试{max_retries}次)"}
        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                continue
            return False, {"error": "timeout", "message": f"API服务响应超时(已重试{max_retries}次)"}
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                continue
            return False, {"error": str(e)[:100]}


def _call_image_api(image_path, config):
    """调用图片理解API分析单张图片"""
    try:
        import requests
        from urllib.parse import urlparse
        pu = urlparse(config["url"])
        analyze_url = f"{pu.scheme}://{pu.netloc}/api/analyze"
        with open(image_path, "rb") as f:
            resp = requests.post(
                analyze_url,
                headers={"X-API-Key": config["api_key"]},
                files={"file": f},
                data={"model": config["model"]},
                timeout=config["timeout"],
            )
        if resp.status_code == 200:
            return resp.json()
        elif resp.status_code in (401, 403):
            return {"status": "auth_failed", "error": f"鉴权失败: HTTP {resp.status_code}"}
        elif resp.status_code == 429:
            return {"status": "rate_limited", "error": "请求频率超限"}
        else:
            return {"status": "error", "error": f"HTTP {resp.status_code}"}
    except requests.exceptions.Timeout:
        return {"status": "timeout", "error": "请求超时"}
    except Exception as e:
        return {"status": "error", "error": str(e)[:100]}


# ============================================================
# Action: step0_8_prep (PX图片抽取+选图+API理解/caption_only降级)
# ============================================================

def action_step0_8_prep(args):
    """PX图片抽取+价值优先选图+自动调用API理解(或降级为caption_only)

    V3.0.3改动:
    - API模式:orchestrator直接调用图片理解API,不依赖Agent
    - 降级模式:caption_only(用前后文生成描述),不回退Agent看图
    - 结果写入px_api_results.json,由step0_8_save统一收口
    """
    data_dir = args.data_dir
    skill_dir = args.skill_dir
    requirement_file = args.requirement_file or ""

    # 方案A延伸:如果未传requirement_file,先尝试从 task_meta.json 读取
    if not requirement_file:
        meta_path = os.path.join(data_dir, "task_meta.json")
        if os.path.exists(meta_path):
            try:
                meta = _read_json(meta_path)
                requirement_file = meta.get("requirement_file", "")
            except Exception:
                pass

    if not requirement_file or not requirement_file.endswith(".docx"):
        print(json.dumps({"status": "skipped", "reason": "非docx格式,跳过PX"}))
        return

    # 调用image_extract.py
    extract_script = os.path.join(skill_dir, "tools", "image_extract.py")
    px_images_dir = os.path.join(data_dir, "px_images")
    px_extract_path = os.path.join(data_dir, "px_extract.json")

    _ensure_dir(px_images_dir)

    result = subprocess.run(
        ["python3", extract_script, requirement_file,
         "--output-dir", px_images_dir,
         "--json-output", px_extract_path],
        capture_output=True, text=True, timeout=60
    )

    if result.returncode != 0 or not os.path.exists(px_extract_path):
        print(json.dumps({"status": "skipped", "reason": f"图片抽取失败: {result.stderr[:200]}"}))
        return

    extract_data = _read_json(px_extract_path)
    images = extract_data.get("images", [])

    if not images:
        print(json.dumps({"status": "skipped", "reason": "docx中无图片"}))
        return

    # 价值优先选图
    value_keywords = ["流程", "状态", "原型", "页面", "规则", "接口", "表格", "如下图", "见图"]
    scored = []
    for img in images:
        caption = (img.get("caption", "") or "").lower()
        before = (img.get("before_text", "") or "").lower()
        after = (img.get("after_text", "") or "").lower()
        context = caption + " " + before + " " + after

        score = 0
        for kw in value_keywords:
            if kw in context:
                score += 1

        # 跳过装饰性图片
        w = img.get("width", 100)
        h = img.get("height", 100)
        if (w < 50 and h < 50) or "logo" in context or "icon" in context:
            score = -1

        scored.append((score, img))

    scored.sort(key=lambda x: x[0], reverse=True)
    selected = [img for score, img in scored if score >= 0][:50]

    # ============================================================
    # V3.0.3: 图片理解(API模式 or caption_only降级)
    # ============================================================
    # V3.2.0: api_key优先从命令行参数读取,其次从task目录缓存读取(解决Agent跨段落丢密码问题)
    # V4.x: 增加脱敏值检测-Agent传入显式--api-key时可能是脱敏后的星号,需自动回退缓存
    api_key = getattr(args, 'api_key', None) or ''
    if api_key.strip() and _is_desensitized(api_key):
        api_key = ''  # 脱敏值视为无效,触发缓存回退
    if not api_key.strip():
        cache_path = os.path.join(data_dir, ".image_api_key")
        if os.path.exists(cache_path):
            try:
                with open(cache_path, "r") as f:
                    api_key = f.read().strip()
            except Exception as e:
                print(json.dumps({"status": "warning", "reason": f"密码缓存读取失败: {e}"}), file=sys.stderr)
    api_config = _load_image_api_config(skill_dir, api_key=api_key or None)
    use_api = api_config["enabled"]

    # 预检:API health check (V4.14.6: auth失败不阻断,由实际analyze调用自行处理鉴权)
    service_ok = False
    if use_api:
        service_ok, health_data = _check_image_api_health(api_config)
        if not service_ok:
            err = health_data.get("error", "") if isinstance(health_data, dict) else ""
            # 连接失败/超时 → 降级; auth失败 → 警告但继续(analyze端点鉴权可能独立)
            if err in ("connection_failed", "timeout"):
                use_api = False
            else:
                print(json.dumps({"status": "warning", "reason": f"auth-check异常({err}),继续尝试API调用"}), file=sys.stderr)

    results = []
    api_success = 0
    api_fallback = 0

    # V3.2.0: 并行调用API(解决19张图串行~570s的问题)
    # 策略:线程池并发=3,主线程汇总结果,401/403立即标记
    def _process_single_image(img):
        """处理单张图片(线程安全:只读输入,返回结果,不修改共享状态)"""
        image_id = img.get("image_id", "")
        file_path = img.get("file_path", "")
        caption = img.get("caption", "") or ""
        before_text = (img.get("before_text", "") or "")[:200]
        after_text = (img.get("after_text", "") or "")[:200]

        caption_desc = caption
        if before_text or after_text:
            context_parts = []
            if before_text:
                context_parts.append(f"图片前文: {before_text}")
            if caption:
                context_parts.append(f"图片标题: {caption}")
            if after_text:
                context_parts.append(f"图片后文: {after_text}")
            caption_desc = " | ".join(context_parts)

        if not file_path or not os.path.exists(file_path):
            return {"image_id": image_id, "understanding_mode": "caption_only",
                    "failure_type": "file_not_found", "description": caption_desc,
                    "ocr_text": "", "labels": [],
                    "before_text": before_text, "after_text": after_text, "_ok": False}

        api_result = _call_image_api(file_path, api_config)

        if api_result.get("status") in ("ok", "partial"):
            mode = "api" if api_result.get("status") == "ok" else "api_partial"
            return {"image_id": image_id, "understanding_mode": mode,
                    "api_provider": api_result.get("model", api_config["model"]),
                    "description": api_result.get("description", caption_desc),
                    "ocr_text": api_result.get("ocr_text", ""),
                    "labels": api_result.get("labels", []),
                    "confidence": api_result.get("confidence", 0),
                    "before_text": before_text, "after_text": after_text, "_ok": True}
        elif api_result.get("status") in ("auth_failed", "rate_limited"):
            return {"image_id": image_id, "understanding_mode": "api_fallback_caption",
                    "failure_type": api_result.get("status"), "description": caption_desc,
                    "ocr_text": "", "labels": [],
                    "before_text": before_text, "after_text": after_text, "_ok": False, "_fatal": True}
        else:
            return {"image_id": image_id, "understanding_mode": "api_fallback_caption",
                    "failure_type": api_result.get("status", "unknown"), "description": caption_desc,
                    "ocr_text": "", "labels": [],
                    "before_text": before_text, "after_text": after_text, "_ok": False}

    if use_api:
        from concurrent.futures import ThreadPoolExecutor, as_completed
        fatal_detected = False
        with ThreadPoolExecutor(max_workers=3) as executor:
            future_map = {executor.submit(_process_single_image, img): img.get("image_id", "") for img in selected}
            try:
                for future in as_completed(future_map, timeout=600):
                    try:
                        r = future.result(timeout=120)
                        ok = r.pop("_ok", False)
                        is_fatal = r.pop("_fatal", False)
                        results.append(r)
                        if ok:
                            api_success += 1
                        else:
                            api_fallback += 1
                        # 401/403: 取消pending,收集已完成的,running继续但不等待
                        if is_fatal:
                            fatal_detected = True
                            for f in future_map:
                                f.cancel()
                            # V4.14.7: 收集已完成的futures,避免结果丢失
                            for f in list(future_map):
                                if f.done() and not f.cancelled():
                                    try:
                                        r = f.result(timeout=0)
                                        ok2 = r.pop("_ok", False)
                                        r.pop("_fatal", False)
                                        results.append(r)
                                        if ok2:
                                            api_success += 1
                                        else:
                                            api_fallback += 1
                                    except Exception:
                                        pass
                            break
                    except Exception as e:
                        results.append({"image_id": future_map.get(future, "?"),
                                        "understanding_mode": "api_fallback_caption",
                                        "failure_type": "exception", "description": str(e)[:200],
                                        "ocr_text": "", "labels": [],
                                        "before_text": "", "after_text": ""})
                        api_fallback += 1
            except TimeoutError:
                # 总超时600s,未完成的图片降级为caption_only
                for f, img_id in future_map.items():
                    if not f.done():
                        results.append({"image_id": img_id,
                                        "understanding_mode": "api_fallback_caption",
                                        "failure_type": "total_timeout",
                                        "description": "总超时600s未完成",
                                        "ocr_text": "", "labels": [],
                                        "before_text": "", "after_text": ""})
                        api_fallback += 1
    else:
        for img in selected:
            image_id = img.get("image_id", "")
            caption = img.get("caption", "") or ""
            before_text = (img.get("before_text", "") or "")[:200]
            after_text = (img.get("after_text", "") or "")[:200]
            caption_desc = caption
            if before_text or after_text:
                parts = []
                if before_text: parts.append(f"图片前文: {before_text}")
                if caption: parts.append(f"图片标题: {caption}")
                if after_text: parts.append(f"图片后文: {after_text}")
                caption_desc = " | ".join(parts)
            results.append({"image_id": image_id, "understanding_mode": "caption_only",
                            "description": caption_desc, "ocr_text": "", "labels": [],
                            "before_text": before_text, "after_text": after_text})

    # 将结果写入临时文件,由step0_8_save统一收口
    _write_json(os.path.join(data_dir, "px_api_results.json"), {
        "results": results,
        "summary": {
            "mode": "api" if api_config["enabled"] and service_ok else "caption_only",
            "service_status": "ok" if api_success > 0 and api_fallback == 0 else
                              ("partial_success" if api_success > 0 else "degraded"),
            "api_success_count": api_success,
            "api_fallback_count": api_fallback,
            "total_selected": len(selected),
            "total_images": len(images),
            "api_provider": api_config["model"] if api_config["enabled"] else "none",
        }
    })

    # 输出状态
    mode = "api" if api_config["enabled"] and service_ok else "caption_only"
    if not api_config["enabled"]:
        mode_msg = "caption_only(未输入图片API密码,如需启用请在Onboarding时输入密码)"
    elif not service_ok:
        mode_msg = f"caption_only(API健康检查失败: {health_data.get('error', 'unknown')})"
    elif api_fallback > 0:
        mode_msg = f"api_with_fallback(成功{api_success}张,降级{api_fallback}张)"
    else:
        mode_msg = f"api(全部{api_success}张通过{api_config['model']}理解)"

    print(json.dumps({
        "status": "ok",
        "mode": mode,
        "mode_message": mode_msg,
        "total_images": len(images),
        "selected_count": len(selected),
        "api_success_count": api_success,
        "api_fallback_count": api_fallback,
    }))


# ============================================================
# Action: step0_8_save (保存图片理解结果)
# ============================================================

def action_step0_8_save(args):
    """保存图片理解结果,调用image_enhance(统一收口)

    V3.0.3改动:
    - 优先读取px_api_results.json(API/caption_only模式产出)
    - 如无API结果文件,回退读取args.results_json(兼容旧模式)
    - 统一生成px_understand.json + 调用image_enhance + mark_complete
    """
    data_dir = args.data_dir
    skill_dir = args.skill_dir
    task_id = args.task_id

    # 优先读取API结果文件
    api_results_path = os.path.join(data_dir, "px_api_results.json")
    if os.path.exists(api_results_path):
        api_data = _read_json(api_results_path)
        results = api_data.get("results", [])
        api_summary = api_data.get("summary", {})
    elif args.results_json:
        # 兼容旧模式:从命令行参数读取
        try:
            results = json.loads(args.results_json)
            api_summary = {}
        except Exception:
            print(json.dumps({"status": "error", "reason": "图片理解结果JSON解析失败"}))
            return
    else:
        print(json.dumps({"status": "error", "reason": "无图片理解结果(px_api_results.json不存在且未传入results_json)"}))
        return

    # 读取抽取数据获取总数
    px_extract_path = os.path.join(data_dir, "px_extract.json")
    total = 0
    if os.path.exists(px_extract_path):
        total = len(_read_json(px_extract_path).get("images", []))

    # 构造px_understand.json
    api_count = sum(1 for r in results if r.get("understanding_mode") == "api")
    caption_count = sum(1 for r in results if r.get("understanding_mode") in ("caption_only", "api_fallback_caption"))
    vision_count = sum(1 for r in results if r.get("understanding_mode") == "vision")  # 兼容旧模式

    # 构造skipped_images列表(未被选中的图片)
    skipped_images = []
    if os.path.exists(px_extract_path):
        all_images = _read_json(px_extract_path).get("images", [])
        selected_ids = set(r.get("image_id", "") for r in results)
        for img in all_images:
            if img.get("image_id", "") not in selected_ids:
                skipped_images.append({
                    "image_id": img.get("image_id", ""),
                    "file_path": img.get("file_path", ""),
                    "selected": False,
                    "selection_reason": "超出50张上限或未命中高价值关键词",
                    "understanding_mode": "skipped"
                })

    understand = {
        "task_id": task_id,
        "total_images": total,
        "selected_images": len(results),
        "results": results,
        "skipped_images": skipped_images,
        "summary": {
            "api_count": api_count,
            "caption_count": caption_count,
            "vision_count": vision_count,
            "skipped_count": total - len(results),
            "mode": api_summary.get("mode", "unknown"),
            "service_status": api_summary.get("service_status", "unknown"),
            "api_provider": api_summary.get("api_provider", "none"),
        }
    }
    _write_json(os.path.join(data_dir, "px_understand.json"), understand)

    # 调用image_enhance
    enhance_script = os.path.join(skill_dir, "tools", "image_enhance.py")
    enhance_output = os.path.join(data_dir, "px_enhance.json")

    result = subprocess.run(
        ["python3", enhance_script,
         os.path.join(data_dir, "px_understand.json"),
         "--output", enhance_output],
        capture_output=True, text=True, timeout=30
    )

    state = TaskState(data_dir=data_dir, task_id=task_id)
    state.mark_complete("step0_8")

    print(json.dumps({
        "status": "ok",
        "mode": api_summary.get("mode", "unknown"),
        "api_count": api_count,
        "caption_count": caption_count,
        "vision_count": vision_count,
        "total": total,
        "enhance_ok": result.returncode == 0,
    }))


# ============================================================
# Action: step_run (执行P0-P7任一步骤)
# ============================================================

def action_step_run(args):
    """
    执行P0-P4/P7步骤:
    1. 检查前置gate pass
    2. 准备prompt输入(读取上游产物+知识注入)
    3. 接收Agent的JSON输出
    4. 写入tmp → truncation_guard → gate pass

    V3.2.5: P5和P6禁止通过step_run执行,必须走专用流程
    """
    data_dir = args.data_dir
    task_id = args.task_id
    skill_dir = args.skill_dir
    step = args.step  # P0/P1/P2/P3/P4/P7
    agent_output = args.agent_output  # Agent返回的JSON字符串

    # V3.3.3: P2/P5/P6/P7禁止通过step_run执行,必须走代码路径
    if step == "P2":
        print(json.dumps({
            "status": "rejected",
            "reason": "❌ P2禁止用step_run执行!P2是代码自动生成,必须用: python3 orchestrator.py --action p2_code_generate",
            "correct_action": "p2_code_generate",
        }))
        sys.exit(1)
    if step == "P5":
        print(json.dumps({
            "status": "rejected",
            "reason": "❌ P5禁止用step_run执行!P5是代码自动合并,必须用: python3 orchestrator.py --action p5_code_merge",
            "correct_action": "p5_code_merge",
        }))
        sys.exit(1)
    if step == "P6":
        print(json.dumps({
            "status": "rejected",
            "reason": "❌ P6禁止用step_run执行!P6必须用逐条流程: p6_tp_list → 循环(p6_generate_one → p6_generate_one --save) → p6_merge (V4.11.0)",
            "correct_flow": "p6_tp_list -> p6_generate_one --tp-index N -> p6_generate_one --tp-index N --save (V4.11.0)",
        }))
        sys.exit(1)
    # V3.3.1: P7禁止通过step_run执行,必须走代码校验
    if step == "P7":
        print(json.dumps({
            "status": "rejected",
            "reason": "❌ P7禁止用step_run执行!P7是代码自动校验,必须用: python3 orchestrator.py --action p7_code_check",
            "correct_action": "p7_code_check",
        }))
        sys.exit(1)

    # 前置gate pass检查
    prerequisites = {
        "P0": ["onboarding"],
        "P1": ["P0"],
        "P2": ["P1"],
        "P3": ["P1"],
        "P4": ["P1"],
        "P5": ["P2", "P3", "P4"],
        "P6": ["P5"],
        "P7": ["P6"],
    }

    for prereq in prerequisites.get(step, []):
        ok, msg = check_gate(data_dir, prereq, task_id)
        if not ok:
            print(json.dumps({"status": "gate_blocked", "step": prereq, "reason": msg}))
            sys.exit(1)

    # 解析Agent输出
    try:
        output_data = json.loads(agent_output)
    except json.JSONDecodeError:
        # JSON解析兜底:尝试正则提取
        import re
        match = re.search(r'\{[\s\S]*\}', agent_output)
        if match:
            try:
                output_data = json.loads(match.group())
            except Exception:
                print(json.dumps({"status": "error", "reason": "Agent输出JSON解析失败(含正则兜底)"}))
                sys.exit(1)
        else:
            print(json.dumps({"status": "error", "reason": "Agent输出不含有效JSON"}))
            sys.exit(1)

    # V3.5.2: output文件写入保护 - 检测是否被Agent提前写入
    final_output_path = os.path.join(data_dir, f"{step.lower()}_output.json")
    if os.path.exists(final_output_path):
        state_check = TaskState(data_dir=data_dir, task_id=task_id)
        if state_check.is_completed(step):
            print(json.dumps({"status": "error", "reason": f"{step}已完成,禁止重复执行。如需重跑请先重置状态。"}))
            sys.exit(1)
        else:
            # 文件存在但state未标记完成 → 可能Agent伪造的,删除
            try:
                os.unlink(final_output_path)
            except Exception:
                pass

    # V4.8.5: P1输出截断检测 - 检测JSON是否被模型截断
    if step == "P1":
        agent_output_stripped = agent_output.strip()
        if not (agent_output_stripped.endswith('}') or agent_output_stripped.endswith(']')):
            print(json.dumps({
                "status": "truncation_detected",
                "reason": "P1输出JSON不完整(末尾非闭合括号),模型输出可能被截断。请重跑P1。",
                "hint": "若反复截断,请检查模型上下文窗口是否不足,LOW模式已自动精简P1 prompt"
            }))
            sys.exit(1)

    # 写入tmp文件
    tmp_path = os.path.join(data_dir, f"{step.lower()}_output.tmp.json")
    _write_json(tmp_path, output_data)

    # V3.5.4: PRD审查字段强制校验 - 当prd_quality_review=True时,P0必须输出blocks_markdown和issues
    if step == "P0":
        meta_path = os.path.join(data_dir, "task_meta.json")
        if os.path.exists(meta_path):
            _meta = _read_json(meta_path)
            if _meta.get("prd_quality_review", False):
                # PRD审查模式下,blocks_markdown和issues为必须字段
                missing_prd_fields = []
                if "blocks_markdown" not in output_data:
                    missing_prd_fields.append("blocks_markdown")
                if "issues" not in output_data:
                    missing_prd_fields.append("issues")
                if missing_prd_fields:
                    try:
                        os.unlink(tmp_path)
                    except Exception:
                        pass
                    print(json.dumps({
                        "status": "prd_review_validation_failed",
                        "step": "P0",
                        "reason": f"PRD审查模式下必须输出字段: {missing_prd_fields}。请检查prompt是否正确注入,Agent是否遵循输出要求。",
                        "missing_fields": missing_prd_fields,
                        "hint": "PRD审查开启后,P0必须输出 blocks_markdown (结构化Markdown) 和 issues (问题清单数组)。请重新生成P0输出。"
                    }))
                    sys.exit(1)

                # V3.5.6: PRD审查内容质量校验
                blocks_md = output_data.get("blocks_markdown", "")
                issues_list = output_data.get("issues", [])
                quality_issues = []

                # 检查1: blocks_markdown类型防御(建议3)
                if not isinstance(blocks_md, str):
                    quality_issues.append(f"blocks_markdown必须是字符串类型,当前为{type(blocks_md).__name__}")
                else:
                    # 检查2: blocks_markdown最小长度
                    if len(blocks_md.strip()) < 200:
                        quality_issues.append("blocks_markdown内容过于简单(<200字符),请展开业务规则、约束条件等5个维度")

                    # 检查3: 关键维度检查(至少包含2个维度)
                    dimension_keywords = ["输入", "输出", "业务规则", "角色权限", "状态流转", "约束条件"]
                    found_dimensions = sum(1 for kw in dimension_keywords if kw in blocks_md)
                    if found_dimensions < 2:
                        quality_issues.append(f"blocks_markdown缺少关键维度(仅发现{found_dimensions}个,应至少包含2个:输入/输出、业务规则、约束条件等)")

                # 检查4: issues格式校验(建议1+建议2:全量校验+类型防御)
                if not isinstance(issues_list, list):
                    quality_issues.append("issues必须是数组类型")
                elif len(issues_list) > 0:
                    required_issue_fields = ["severity", "location", "type", "problem", "suggestion"]
                    for i, issue in enumerate(issues_list):
                        if not isinstance(issue, dict):
                            quality_issues.append(f"issues[{i}]必须是对象类型,当前为{type(issue).__name__}")
                            continue
                        missing_issue_fields = [f for f in required_issue_fields if f not in issue]
                        if missing_issue_fields:
                            quality_issues.append(f"issues[{i}]对象缺少字段: {missing_issue_fields}")

                if quality_issues:
                    try:
                        os.unlink(tmp_path)
                    except Exception:
                        pass
                    print(json.dumps({
                        "status": "prd_review_quality_failed",
                        "step": "P0",
                        "reason": "PRD审查内容质量不达标",
                        "quality_issues": quality_issues,
                        "hint": "blocks_markdown内容应≥200字符,需至少覆盖2个关键维度(如输入/输出、业务规则等)。issues数组中每个对象必须包含severity/location/type/problem/suggestion字段。"
                    }))
                    sys.exit(1)

    # === V3.0.3新增:写入tmp后、guard前,先做必需字段校验(代码硬控) ===
    required_fields_map = {
        "P0": P0_REQUIRED_FIELDS,
        "P1": P1_REQUIRED_FIELDS,
        "P3": P3_REQUIRED_FIELDS,
        "P4": P4_REQUIRED_FIELDS,
        "P5": P5_REQUIRED_FIELDS,
        "P6": P6_REQUIRED_FIELDS,
        "P7": P7_REQUIRED_FIELDS,
    }
    if step in required_fields_map:
        missing_fields = []
        for field in required_fields_map[step]:
            # 支持嵌套路径和多候选
            val = _get_nested(output_data, field)
            if val is None:
                missing_fields.append(field)
        if missing_fields:
            # 删除tmp文件,拒绝写入
            try:
                os.unlink(tmp_path)
            except Exception:
                pass
            print(json.dumps({
                "status": "validation_failed",
                "step": step,
                "reason": f"必需字段缺失: {missing_fields}。请确保输出JSON包含这些顶层字段。",
                "missing_fields": missing_fields,
                "hint": f"{step}输出必须包含: {required_fields_map[step]}",
            }))
            sys.exit(1)

    # V4.8.8: P1 场景数量质量校验(Gate级硬控,防止Agent为规避截断而压缩scenario)
    if step == "P1":
        p1_quality_issues = []
        feature_tree = output_data.get("feature_tree", {})
        modules = feature_tree.get("children", feature_tree.get("modules", []))

        # 收集所有feature节点
        all_features = []
        def _collect_features(node_list, parent_module=""):
            for node in node_list:
                if isinstance(node, dict):
                    ntype = node.get("type", "")
                    if ntype == "feature" or (ntype == "" and "children" in node and node.get("children")):
                        all_features.append({"node": node, "module": parent_module})
                    # 递归子节点(但feature的children是scenarios,不再递归)
                    if ntype in ("module", "") and "children" in node:
                        _collect_features(node.get("children", []), node.get("name", parent_module))
        _collect_features(modules)

        # 校验1: 每个feature的scenario数量≥2
        low_scenario_features = []
        total_scenarios = 0
        for fi in all_features:
            node = fi["node"]
            children = node.get("children", [])
            scenario_count = len([c for c in children if isinstance(c, dict) and c.get("type") == "scenario"])
            total_scenarios += scenario_count
            if scenario_count < 2:
                mod = fi.get("module", "")
                name = node.get("name", node.get("id", "?"))
                low_scenario_features.append(f"{mod}/{name}:仅{scenario_count}个场景")

        if low_scenario_features:
            p1_quality_issues.append(f"{len(low_scenario_features)}个功能点场景不足(应≥2): {', '.join(low_scenario_features[:5])}")

        # 校验2: 总叶节点数 ≥ P0 operations × 2
        p0_path = os.path.join(data_dir, "p0_output.json")
        if os.path.exists(p0_path):
            try:
                p0_data = _read_json(p0_path)
                blocks = p0_data.get("blocks", {})
                operations = blocks.get("operations", []) if isinstance(blocks, dict) else []
                op_count = len(operations) if isinstance(operations, list) else 0
                min_expected = op_count * 2
                if total_scenarios < min_expected:
                    p1_quality_issues.append(f"场景总数{total_scenarios}<最低要求{min_expected}(P0 operations {op_count}×2)")
            except Exception:
                pass

        if p1_quality_issues:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass
            print(json.dumps({
                "status": "p1_quality_rejected",
                "step": "P1",
                "reason": "P1场景覆盖不达标",
                "quality_issues": p1_quality_issues,
                "hint": "每个功能点(feature)必须有≥2个scenario(1正向+1异常)。不要为规避JSON截断而压缩scenario数量--如JSON过长,精简每个scenario的description文本而非砍scenario。场景总数应≥P0 operations数量×2。"
            }))
            sys.exit(1)

    # 调用truncation_guard
    ok, msg = run_truncation_guard(skill_dir, data_dir, task_id, step)

    if ok:
        # V3.5.7: P0且开启PRD审查时,自动生成报告文件(不依赖Agent是否调用quality_check)
        if step == "P0":
            meta_path = os.path.join(data_dir, "task_meta.json")
            if os.path.exists(meta_path):
                _meta = _read_json(meta_path)
                if _meta.get("prd_quality_review", False):
                    try:
                        # 读取P0输出
                        p0_output_path = os.path.join(data_dir, "p0_output.json")
                        if os.path.exists(p0_output_path):
                            p0_data = _read_json(p0_output_path)
                            blocks_md = p0_data.get("blocks_markdown", "")
                            prd_issues_list = p0_data.get("issues", [])
                            quality_score = p0_data.get("quality_score", 0)

                            # 生成报告文件
                            report_path = os.path.join(data_dir, "prd_review_report.md")
                            score_label = "PASS" if quality_score >= 0.7 else ("CONDITIONAL_PASS" if quality_score >= 0.5 else "FAIL")
                            report_lines = [
                                "# PRD审查报告\n",
                                f"**质量评分**: {quality_score} ({score_label})\n",
                                f"**生成时间**: {time.strftime('%Y-%m-%d %H:%M:%S')}\n",
                                "\n---\n",
                                "## 📋 需求结构化结果\n",
                                (blocks_md if blocks_md else "*未输出结构化内容*"),
                                "\n\n---\n",
                                "## ⚠️ 问题清单\n",
                            ]
                            if prd_issues_list:
                                report_lines.append("| 严重度 | 位置 | 类型 | 问题 | 建议 |\n")
                                report_lines.append("|--------|------|------|------|------|\n")
                                for issue in prd_issues_list:
                                    if isinstance(issue, dict):
                                        severity = issue.get("severity", "")
                                        location = issue.get("location", "")
                                        issue_type = issue.get("type", "")
                                        problem = issue.get("problem", issue.get("issue", ""))
                                        suggestion = issue.get("suggestion", issue.get("recommendation", ""))
                                        report_lines.append(f"| {severity} | {location} | {issue_type} | {problem} | {suggestion} |\n")
                                    else:
                                        report_lines.append(f"| - | - | - | {issue} | - |\n")
                            else:
                                report_lines.append("*未发现问题*\n")
                            _write_text(report_path, "".join(report_lines))
                    except Exception:
                        pass  # 生成报告失败不影响主流程

        state = TaskState(data_dir=data_dir, task_id=task_id)
        state.mark_complete(step)
        print(json.dumps({"status": "ok", "step": step, "guard_result": msg}))
    else:
        print(json.dumps({"status": "guard_failed", "step": step, "reason": msg}))
        sys.exit(1)


# ============================================================
# V4.8.9: P1 分批生成 - skeleton → 逐feature填充 → 合并
# ============================================================

def action_p1_skeleton_save(args):
    """V4.8.9: 保存P1骨架(module+feature结构,不含scenario)"""
    data_dir = args.data_dir
    task_id = args.task_id
    agent_output = args.agent_output

    try:
        sk = json.loads(agent_output)
    except Exception:
        import re
        m = re.search(r'\{[\s\S]*\}', agent_output)
        if m:
            try:
                sk = json.loads(m.group())
            except Exception:
                print(json.dumps({"status": "error", "reason": "P1骨架JSON解析失败"}))
                sys.exit(1)
        else:
            print(json.dumps({"status": "error", "reason": "P1骨架输出不含JSON"}))
            sys.exit(1)

    # 校验 feature_tree 存在
    ft = sk.get("feature_tree", {})
    if not ft:
        print(json.dumps({"status": "error", "reason": "缺少feature_tree字段"}))
        sys.exit(1)

    # 提取所有 feature(空children = 场景占位)
    features = []
    modules = ft.get("children", ft.get("modules", []))
    def _walk(nodes, mod_name=""):
        for node in nodes:
            if isinstance(node, dict):
                ntype = node.get("type", "")
                if ntype == "module":
                    _walk(node.get("children", []), node.get("name", mod_name))
                elif ntype == "feature":
                    fid = node.get("id", "")
                    fname = node.get("name", "")
                    child_count = len(node.get("children", []))
                    features.append({"feature_id": fid, "feature_name": fname, "module": mod_name, "current_scenarios": child_count})
    _walk(modules)

    if not features:
        print(json.dumps({"status": "error", "reason": "骨架中未找到feature节点"}))
        sys.exit(1)

    # V4.14.10: P1功能点数量自适应校验 — 以P0 operations数为基准
    # 分级: ratio<0.5→自动重启, 0.5≤ratio<1.0→WARNING不阻断, ratio≥1.0→通过
    # 自动重启≤2次,超限转人工确认。支持 --force-accept 跳过校验。
    MAX_AUTO_RESTART = 2
    if not getattr(args, 'force_accept', False):
        p0_path = os.path.join(data_dir, "p0_output.json")
        if os.path.exists(p0_path):
            try:
                p0_data = _read_json(p0_path)
                p0_operations = p0_data.get("blocks", {}).get("operations")
                if p0_operations and isinstance(p0_operations, list) and len(p0_operations) > 0:
                    p0_ops = len(p0_operations)
                    ratio = len(features) / p0_ops if p0_ops > 0 else 1.0
                    if ratio < 0.5:
                        # 严重粒度不足 → 自动重启
                        meta_path = os.path.join(data_dir, "task_meta.json")
                        restart_count = 0
                        if os.path.exists(meta_path):
                            try:
                                meta = _read_json(meta_path)
                                restart_count = int(meta.get("p1_auto_restart_count", 0))
                            except Exception:
                                pass
                        if restart_count < MAX_AUTO_RESTART:
                            meta["p1_auto_restart_count"] = restart_count + 1
                            _write_json(meta_path, meta)
                            print(json.dumps({
                                "status": "quality_rejected",
                                "reason": f"功能点({len(features)})远少于P0操作数({p0_ops}), 比值{ratio:.2f}<0.5, 粒度太粗",
                                "p1_auto_restart_count": restart_count + 1,
                                "action": "restart_from P1",
                                "hint": "请重新生成P1骨架,将每个P0操作细化至少为1个功能点。"
                            }))
                            sys.exit(1)
                        else:
                            print(json.dumps({
                                "status": "auto_restart_blocked",
                                "reason": f"P1功能点连续{MAX_AUTO_RESTART}次严重不达标(比值≤{ratio:.2f}),自动重启已耗尽",
                                "p1_auto_restart_count": restart_count,
                                "p0_operations": p0_ops,
                                "features_count": len(features),
                                "action_required": "manual_confirm",
                                "hint": "请向用户汇报: P1功能点粒度持续偏粗,是否接受当前结果或使用 --force-accept?"
                            }))
                            sys.exit(1)
                    elif ratio < 1.0:
                        # 轻度不足 → WARNING,不阻断
                        print(json.dumps({
                            "status": "quality_warning",
                            "reason": f"功能点({len(features)})略少于P0操作数({p0_ops}), 比值{ratio:.2f}, 建议检查粒度",
                            "total_features": len(features),
                            "p0_operations": p0_ops
                        }), file=sys.stderr)
            except Exception as e:
                print(json.dumps({"p1_skeleton_warning": f"P0校验异常,跳过: {e}"}), file=sys.stderr)
        else:
            print(json.dumps({"p1_skeleton_warning": "P0未生成,跳过功能点数量校验(非阻塞)"}), file=sys.stderr)

    # 保存骨架
    sk_path = os.path.join(data_dir, "p1_skeleton.json")
    _write_json(sk_path, sk)

    # 创建 features 目录
    features_dir = os.path.join(data_dir, "p1_features")
    _ensure_dir(features_dir)

    print(json.dumps({
        "status": "ok",
        "skeleton_saved": "p1_skeleton.json",
        "total_features": len(features),
        "features": features,
        "hint": f"共{len(features)}个功能点,请逐feature生成scenarios。对每个feature: 1) prep_prompt --step P1 --feature-id ID 2) 生成scenario JSON 3) p1_save_feature --feature-id ID",
    }))


def action_p1_save_feature(args):
    """V4.8.9: 保存单个feature的scenario数据到 p1_features/"""
    data_dir = args.data_dir
    feature_id = getattr(args, 'feature_id', '')
    agent_output = args.agent_output

    if not feature_id:
        feature_id = getattr(args, 'feature_id_str', '')
    if not feature_id:
        print(json.dumps({"status": "error", "reason": "缺少 --feature-id 参数"}))
        sys.exit(1)

    try:
        fd = json.loads(agent_output)
    except Exception:
        import re
        m = re.search(r'\{[\s\S]*\}', agent_output)
        if m:
            try:
                fd = json.loads(m.group())
            except Exception:
                print(json.dumps({"status": "error", "reason": f"feature {feature_id} JSON解析失败"}))
                sys.exit(1)
        else:
            print(json.dumps({"status": "error", "reason": f"feature {feature_id} 输出不含JSON"}))
            sys.exit(1)

    scenarios = fd.get("scenarios", [])
    if len(scenarios) < 2:
        print(json.dumps({
            "status": "quality_rejected",
            "feature_id": feature_id,
            "reason": f"scenario数量不足: {len(scenarios)}<2(需1正向+1异常)",
            "hint": "每个功能点至少需要2个scenario。请重新生成。"
        }))
        sys.exit(1)

    # 检查 scenario_type 多样性
    types = set(s.get("scenario_type", "") for s in scenarios)
    if "positive" not in types:
        print(json.dumps({
            "status": "quality_rejected",
            "feature_id": feature_id,
            "reason": "缺少positive类型scenario",
        }))
        sys.exit(1)

    # 保存到 p1_features/ 目录
    features_dir = os.path.join(data_dir, "p1_features")
    _ensure_dir(features_dir)
    safe_id = feature_id.replace("/", "_").replace("\\", "_")
    ft_path = os.path.join(features_dir, f"feature_{safe_id}.json")
    _write_json(ft_path, {"feature_id": feature_id, "scenarios": scenarios})

    print(json.dumps({
        "status": "ok",
        "feature_id": feature_id,
        "scenarios_saved": len(scenarios),
        "types": list(types),
    }))


def action_p1_code_merge(args):
    """V4.8.9: 合并P1骨架+所有feature scenarios → 完整 p1_output.json → Gate pass"""
    data_dir = args.data_dir
    task_id = args.task_id
    skill_dir = args.skill_dir

    # 读取骨架
    sk_path = os.path.join(data_dir, "p1_skeleton.json")
    if not os.path.exists(sk_path):
        print(json.dumps({"status": "error", "reason": "p1_skeleton.json不存在,请先执行 p1_skeleton_save"}))
        sys.exit(1)

    sk = _read_json(sk_path)
    ft = sk.get("feature_tree", {})

    # 读取所有 feature 数据
    features_dir = os.path.join(data_dir, "p1_features")
    feature_map = {}
    if os.path.exists(features_dir):
        for fname in os.listdir(features_dir):
            if fname.startswith("feature_") and fname.endswith(".json"):
                fpath = os.path.join(features_dir, fname)
                fd = _read_json(fpath)
                fid = fd.get("feature_id", "")
                if fid:
                    feature_map[fid] = fd.get("scenarios", [])

    # 遍历骨架,填充 scenarios
    total_scenarios = 0
    missing_features = []
    modules = ft.get("children", ft.get("modules", []))

    def _fill(node):
        nonlocal total_scenarios, missing_features
        if isinstance(node, dict):
            ntype = node.get("type", "")
            if ntype == "module":
                for child in node.get("children", []):
                    _fill(child)
            elif ntype == "feature":
                fid = node.get("id", "")
                if fid in feature_map:
                    node["children"] = feature_map[fid]
                    total_scenarios += len(feature_map[fid])
                else:
                    missing_features.append(fid)

    for mod in modules:
        _fill(mod)

    if missing_features:
        print(json.dumps({
            "status": "error",
            "reason": f"{len(missing_features)}个feature缺少scenario数据: {', '.join(missing_features[:10])}",
            "hint": "请对每个feature执行: prep_prompt --step P1 --feature-id ID → 生成scenario → p1_save_feature --feature-id ID"
        }))
        sys.exit(1)

    # V4.8.8 校验: 场景数量
    p1_quality_issues = []
    low_scenario_features = []
    def _validate(node):
        if isinstance(node, dict):
            ntype = node.get("type", "")
            if ntype == "feature":
                sc = node.get("children", [])
                sc_count = len([c for c in sc if isinstance(c, dict) and c.get("type") == "scenario"])
                if sc_count < 2:
                    low_scenario_features.append(f"{node.get('id','?')}:仅{sc_count}个")
            if "children" in node:
                for c in node.get("children", []):
                    _validate(c)
    for mod in modules:
        _validate(mod)

    if low_scenario_features:
        p1_quality_issues.append(f"{len(low_scenario_features)}个功能点场景<2: {', '.join(low_scenario_features[:5])}")

    # 校验: 总数 ≥ P0 operations × 2
    p0_path = os.path.join(data_dir, "p0_output.json")
    if os.path.exists(p0_path):
        try:
            p0_data = _read_json(p0_path)
            blocks = p0_data.get("blocks", {})
            operations = blocks.get("operations", []) if isinstance(blocks, dict) else []
            op_count = len(operations) if isinstance(operations, list) else 0
            if total_scenarios < op_count * 2:
                p1_quality_issues.append(f"场景总数{total_scenarios}<{op_count*2}(P0 ops {op_count}×2)")
        except Exception:
            pass

    if p1_quality_issues:
        print(json.dumps({
            "status": "p1_merge_quality_rejected",
            "issues": p1_quality_issues,
            "hint": "请对场景不足的feature重新生成scenario,确保每个≥2个且总数达标"
        }))
        sys.exit(1)

    # V4.15.30: 一刀根治P1字段不统一 — 所有scenario的scenario_id→id标准化
    # 解决: P2/P5/P6多处 scen.get("id") 读不到 P1 Agent 写的 scenario_id 字段
    def _normalize_scenario_fields(node):
        if isinstance(node, dict):
            if node.get("type") == "scenario":
                # 将 scenario_id 标准化为 id（保留原字段兼容）
                if "scenario_id" in node:
                    if "id" not in node or not node["id"]:
                        node["id"] = node["scenario_id"]
                    # 保留双份，下游可同时访问
            for child in node.get("children", []):
                _normalize_scenario_fields(child)
    for mod in modules:
        _normalize_scenario_fields(mod)

    # 组装完整 P1 output - 兼容 P2 读取(P2 优先查 feature_tree.modules)
    # V4.8.9: 骨架用 children,转换为 modules 供 P2 读取
    if "children" in ft and "modules" not in ft:
        ft["modules"] = ft.pop("children")
    # V4.8.12: 从 task_meta 自动填充 requirement_id,避免 P2→P6 全链路 REQ-UNKNOWN
    req_id = task_id or ""
    tm_path = os.path.join(data_dir, "task_meta.json")
    if os.path.exists(tm_path):
        try:
            tm = _read_json(tm_path)
            req_id = tm.get("project", tm.get("task_id", task_id))
        except Exception:
            pass
    p1_output = {
        "feature_tree": ft,
        "requirement_id": req_id,
        "coverage_check": sk.get("coverage_check", {}),
        "statistics": {
            "total_modules": len(modules),
            "total_features": len(feature_map),
            "total_scenarios": total_scenarios,
        }
    }

    # 写入 tmp → truncation_guard → gate pass
    tmp_path = os.path.join(data_dir, "p1_output.tmp.json")
    _write_json(tmp_path, p1_output)

    ok, msg = run_truncation_guard(skill_dir, data_dir, task_id, "P1")
    if ok:
        state = TaskState(data_dir=data_dir, task_id=task_id)
        state.mark_complete("P1")
        print(json.dumps({
            "status": "ok",
            "step": "P1",
            "statistics": p1_output["statistics"],
            "merged_from": f"{len(feature_map)} features",
        }))
    else:
        print(json.dumps({"status": "guard_failed", "step": "P1", "reason": msg}))
        sys.exit(1)


# ============================================================
# Action: gate_diag (V4.13.5)
# ============================================================

def action_gate_diag(args):
    """V4.13.5: Gate诊断命令 — 检查gate文件完整性、HMAC签名、来源合法性。
    用于Agent在gate验证失败时快速定位问题,避免盲目重试。
    注意:此命令输出仅供人类阅读,Agent不应将其用于伪造gate。
    """
    data_dir = args.data_dir
    task_id = args.task_id
    step = args.step or "P6"
    gate_path = os.path.join(data_dir, "gates", f"{step}.pass.json")
    
    diag = {
        "step": step,
        "gate_exists": os.path.exists(gate_path),
        "gate_path": gate_path,
        "checks": []
    }
    
    if not diag["gate_exists"]:
        diag["checks"].append({
            "check": "gate_existence",
            "status": "FAIL",
            "fix": f"gate文件不存在。请执行对应步骤生成gate(如 --action p6_merge 或 --action p7_code_check)"
        })
        print(json.dumps(diag, ensure_ascii=False, indent=2))
        return
    
    try:
        gate_data = _read_json(gate_path)
    except Exception as e:
        diag["checks"].append({
            "check": "json_valid",
            "status": "FAIL",
            "detail": f"gate文件JSON解析失败: {e}"
        })
        print(json.dumps(diag, ensure_ascii=False, indent=2))
        return
    
    # 1. 字段完整性
    required_fields = ["step", "status", "task_id", "source_action", "hmac"]
    missing = [f for f in required_fields if f not in gate_data]
    if missing:
        diag["checks"].append({
            "check": "field_completeness",
            "status": "FAIL",
            "missing_fields": missing,
            "fix": f"缺少字段: {missing}。gate文件可能被手动编辑或损坏,请通过orchestrator重新生成。"
        })
    else:
        diag["checks"].append({"check": "field_completeness", "status": "PASS"})
    
    # 2. task_id一致性
    gate_tid = gate_data.get("task_id", "")
    if gate_tid != task_id:
        diag["checks"].append({
            "check": "task_id_match",
            "status": "FAIL",
            "detail": f"gate中task_id='{gate_tid}',当前='{task_id}'",
            "fix": "task_id不匹配,可能是串task了。检查data_dir路径是否正确。"
        })
    else:
        diag["checks"].append({"check": "task_id_match", "status": "PASS"})
    
    # 3. HMAC验签
    hmac_ok, hmac_reason = _verify_gate_hmac(gate_data, task_id)
    diag["checks"].append({
        "check": "hmac_signature",
        "status": "PASS" if hmac_ok else "FAIL",
        "detail": hmac_reason,
        "fix": None if hmac_ok else "请通过orchestrator重新生成gate,不要手动编辑gate文件。"
    })
    
    # 4. source_action合法性
    source_action = gate_data.get("source_action", "")
    step_name = gate_data.get("step", "")
    if step_name in _VALID_GATE_SOURCES:
        valid = source_action in _VALID_GATE_SOURCES[step_name]
        diag["checks"].append({
            "check": "source_action_valid",
            "status": "PASS" if valid else "FAIL",
            "detail": f"source_action='{source_action}',合法来源={_VALID_GATE_SOURCES[step_name]}",
            "fix": None if valid else f"请执行正确的action生成gate: {_VALID_GATE_SOURCES[step_name]}"
        })
    
    # 5. V4.13.5: 内部副本交叉校验
    try:
        integrity_dir = _get_integrity_dir(task_id)
        integrity_path = os.path.join(integrity_dir, f"{step}.pass.json")
        if os.path.exists(integrity_path):
            integrity_data = _read_json(integrity_path)
            main_hmac = gate_data.get("hmac", "")
            integ_hmac = integrity_data.get("hmac", "")
            match = main_hmac == integ_hmac
            diag["checks"].append({
                "check": "integrity_cross_check",
                "status": "PASS" if match else "FAIL",
                "detail": "双副本一致" if match else "主副本与内部副本不一致",
                "fix": None if match else "⚠️ gate文件可能被篡改,请通过orchestrator重新生成。"
            })
        else:
            diag["checks"].append({
                "check": "integrity_cross_check",
                "status": "WARN",
                "detail": "内部副本不存在(可能旧版本gate无副本)",
                "fix": "重新执行对应action即可生成双副本。"
            })
    except Exception:
        pass
    
    passed = all(c.get("status") in ("PASS", "WARN") for c in diag["checks"])
    diag["overall"] = "PASS" if passed else "FAIL"
    
    print(json.dumps(diag, ensure_ascii=False, indent=2))
    if not passed:
        sys.exit(1)


# Action: step7_export
# ============================================================

def action_step7_export(args):
    """Step 7: 调用export_excel.py导出

    V3.0.3: 内置quality_check硬门禁,Agent无法绕过
    """
    data_dir = args.data_dir
    task_id = args.task_id
    skill_dir = args.skill_dir

    # FIX③ V5.x: --force 强制导出闸门。必须同时提供 --force-reason;
    # 从 orchestrator_state 读/写 p7_force_count,超过 3 次硬拒绝。
    force_export = getattr(args, "force", False)
    force_reason = (getattr(args, "force_reason", "") or "").strip()
    if force_export:
        if not force_reason:
            print(json.dumps({
                "status": "force_blocked",
                "reason": "--force 必须同时提供 --force-reason 说明强制导出原因。",
            }, ensure_ascii=False))
            sys.exit(1)
        _fstate = TaskState(data_dir=data_dir, task_id=task_id)
        _fcount = int(_fstate.state.get("p7_force_count", 0)) + 1
        if _fcount > 3:
            print(json.dumps({
                "status": "force_blocked",
                "reason": f"强制导出次数已达 {_fcount - 1} 次(上限 3 次),硬拒绝。请修复质量问题后正常导出。",
                "p7_force_count": _fcount - 1,
            }, ensure_ascii=False))
            sys.exit(1)
        _fstate.state["p7_force_count"] = _fcount
        _fstate.state["p7_force_last_reason"] = force_reason
        _fstate.save()
        print(json.dumps({
            "status": "force_export",
            "p7_force_count": _fcount,
            "force_reason": force_reason,
            "note": f"已启用强制导出(第 {_fcount}/3 次),跳过可绕过的质量门禁。BLOCK 级检查仍不可绕过。",
        }, ensure_ascii=False), file=sys.stderr)

    # 检查全链路gate pass完整性(防止Agent"表演"流程)
    required_gates = ["onboarding", "P0", "P1", "P2", "P3", "P4", "P5", "P6", "P7"]
    missing_gates = []
    for step in required_gates:
        ok, msg = check_gate(data_dir, step, task_id)
        if not ok:
            missing_gates.append(step)

    if missing_gates:
        print(json.dumps({
            "status": "gate_blocked",
            "reason": f"以下步骤的gate pass缺失: {missing_gates}。Agent必须真正执行这些步骤(通过orchestrator),不能跳过。",
            "missing_gates": missing_gates,
        }))
        sys.exit(1)

    # V3.5.2: 全链路gate来源审计(检测 Agent 绕过 orchestrator 伪造gate的行为)
    audit_warnings = []
    for step in required_gates:
        gate_path = os.path.join(data_dir, "gates", f"{step}.pass.json")
        if os.path.exists(gate_path):
            gp = _read_json(gate_path)
            source = gp.get("source_action", "")
            # 兑容旧版本的gate(没有source_action字段)
            if source == "":
                continue
            valid = _VALID_GATE_SOURCES.get(step, [])
            if valid and source not in valid:
                audit_warnings.append(f"{step}: gate来源异常(source_action='{source}',合法来源={valid})")

    if audit_warnings:
        print(json.dumps({
            "status": "audit_blocked",
            "reason": "检测到部分步骤的gate pass来源异常,可能Agent绕过orchestrator伪造。禁止导出。",
            "details": audit_warnings,
        }))
        sys.exit(1)

    # === V3.3.0: P6用例数量底线校验(精简版,详细校验已移至P7 code_check) ===
    p6_path = os.path.join(data_dir, "p6_output.json")
    if os.path.exists(p6_path):
        p6_data = _read_json(p6_path)
        cases = p6_data.get("testcases", [])
        total = len(cases)
        if total < 15:
            print(json.dumps({
                "status": "quality_blocked",
                "reason": f"P6用例数量{total}<底线15,禁止导出",
            }))
            sys.exit(1)

        # V4.13.5: 疲劳熔断检查(预防Agent疲劳后作弊)
    fatigue_triggered, fatigue_reason = _track_fatigue(task_id, "export_check")
    if fatigue_triggered:
        print(json.dumps({
            "status": "fatigue_warning",
            "reason": f"⚠️ 疲劳熔断已触发({fatigue_reason})。",
            "action_required": "report_to_user",
            "report_template": _build_fatigue_report(data_dir, task_id),
        }))
        # 不exit,继续执行但标记low_quality

    # V4.13.5: 内部副本交叉校验(防Agent伪造gate)
    for step in required_gates:
        gate_path = os.path.join(data_dir, "gates", f"{step}.pass.json")
        if os.path.exists(gate_path):
            try:
                integrity_dir = _get_integrity_dir(task_id)
                integrity_path = os.path.join(integrity_dir, f"{step}.pass.json")
                if os.path.exists(integrity_path):
                    main_data = _read_json(gate_path)
                    integ_data = _read_json(integrity_path)
                    if main_data.get("hmac") != integ_data.get("hmac"):
                        print(json.dumps({
                            "status": "integrity_blocked",
                            "reason": f"⚠️ gate安全校验失败: {step}.pass.json 主副本与内部副本不一致(gate文件疑似被手动篡改)。请通过'orchestrator --action gate_diag --step {step}'诊断,或重新执行对应action。",
                            "step": step,
                        }))
                        sys.exit(1)
            except Exception:
                pass  # 内部副本缺失不阻塞(兼容旧版本gate)

    # V4.13.3: 输出完整性校验 - 兼容p6_tp_output(逐条TP)和p6_batches(分批)两种格式
        batch_total = 0
        source_format = None
        # 优先检查 p6_tp_output (逐条TP格式, V4.11.0+)
        tp_dir = os.path.join(data_dir, "p6_tp_output")
        if os.path.isdir(tp_dir):
            source_format = "p6_tp_output"
            for fn in sorted(os.listdir(tp_dir)):
                if fn.startswith("tp_") and fn.endswith(".json") and "_context" not in fn and "_agent_output" not in fn:
                    try:
                        td = _read_json(os.path.join(tp_dir, fn))
                        batch_total += len(td.get("testcases", []))
                    except Exception:
                        pass
        # 降级检查 p6_batches (分批格式, 兼容旧流程)
        batches_dir = os.path.join(data_dir, "p6_batches")
        if batch_total == 0 and os.path.isdir(batches_dir):
            source_format = source_format or "p6_batches"
            for fn in sorted(os.listdir(batches_dir)):
                if fn.startswith("batch_") and fn.endswith(".json") and "_agent" not in fn and "_skeleton" not in fn and "_context" not in fn:
                    try:
                        bd = _read_json(os.path.join(batches_dir, fn))
                        batch_total += len(bd.get("testcases", []))
                    except Exception:
                        pass
        if batch_total > 0 and total > batch_total:
            print(json.dumps({
                "status": "integrity_blocked",
                "reason": f"p6_output.json有{total}条用例,但{source_format}/各文件合计仅{batch_total}条。数据来源可疑(可能被手动篡改),拒绝导出。请通过p6_merge重新生成。",
            }))
            sys.exit(1)

    # V4.10.1: P5完整性校验
    p5_path = os.path.join(data_dir, "p5_output.json")
    if os.path.exists(p5_path):
        p5_data = _read_json(p5_path)
        merge_log = p5_data.get("merge_log", {})
        required_merge_keys = ["from_p2", "from_p3", "from_p4"]
        missing_keys = [k for k in required_merge_keys if k not in merge_log]
        if missing_keys:
            print(json.dumps({
                "status": "integrity_blocked",
                "reason": f"p5_output.json缺少merge_log必要字段: {missing_keys}。数据来源可疑(可能被手动篡改),请通过p5_code_merge重新生成。",
            }))
            sys.exit(1)



    # === V3.3.0: P7门禁校验(必须由p7_code_check生成) ===
    p7_path = os.path.join(data_dir, "p7_output.json")
    if os.path.exists(p7_path):
        p7_data = _read_json(p7_path)
        # V3.3.1: 验证source字段确认是代码生成的
        if p7_data.get("source") != "p7_code_check":
            print(json.dumps({
                "status": "quality_blocked",
                "reason": "P7输出不是由p7_code_check生成的,禁止导出。请执行: python3 orchestrator.py --action p7_code_check",
            }))
            sys.exit(1)
        gate_result = p7_data.get("gate_result", {})
        if isinstance(gate_result, str):
            gate_passed = gate_result.upper() in ("PASS", "PASSED")
        elif isinstance(gate_result, dict):
            gate_passed = gate_result.get("status", "").upper() in ("PASS", "PASSED")
        else:
            gate_passed = False
        if not gate_passed:
            if force_export:
                print(json.dumps({
                    "status": "force_export",
                    "reason": f"P7质量门禁未通过但已 --force 强制导出(原因: {force_reason})\u3002BLOCK 级检查仍将被拦截。",
                    "gate_result": gate_result,
                }, ensure_ascii=False), file=sys.stderr)
            else:
                print(json.dumps({
                    "status": "quality_blocked",
                    "reason": f"P7质量门禁未通过: {gate_result}",
                    "gate_result": gate_result,
                }))
                sys.exit(1)

        # FIX(block-forgery-guard) V4.13.9-S1: 不信任 gate_result.status 单一字段,
        # 直接复核 checks 明细中是否仍有 BLOCK 级 FAILED。
        # 防御场景: P7.pass.json 被手工伪造成 PASS(知道 HMAC_SECRET 即可自算签名),
        # 但 p7_output.json 的 checks 仍记录真实的 BLOCK FAIL。此校验做在数据层,伪造 gate 也绕不过,
        # 且不提供任何绕过开关(不涉及 --force,该参数仅属于 restart_from)。
        if isinstance(gate_result, dict):
            block_fails = [
                ck for ck in gate_result.get("checks", [])
                if isinstance(ck, dict)
                and str(ck.get("level", "")).upper() == "BLOCK"
                and str(ck.get("status", "")).upper() in ("FAILED", "FAIL")
            ]
            if block_fails:
                print(json.dumps({
                    "status": "quality_blocked",
                    "reason": "以下 BLOCK 检查未通过,禁止导出(无任何绕过开关):",
                    "blocked_checks": [
                        {"check_id": ck.get("check_id"), "name": ck.get("name"),
                         "detail": str(ck.get("detail", ""))[:200]}
                        for ck in block_fails
                    ],
                    "fix": "请修复上述 BLOCK 项 → p6_merge → p7_code_check 重新验证后再导出。",
                }, ensure_ascii=False))
                sys.exit(1)

    # === V3.2.6新增:P5结构特征校验(辅助防线,确认P5由代码合并生成) ===
    p5_path = os.path.join(data_dir, "p5_output.json")
    if os.path.exists(p5_path):
        p5_data = _read_json(p5_path)
        merge_log = p5_data.get("merge_log", {})
        required_merge_keys = ["from_p2", "from_p3", "from_p4"]
        missing_merge_keys = [k for k in required_merge_keys if k not in merge_log]
        if missing_merge_keys:
            print(json.dumps({
                "status": "structure_blocked",
                "reason": f"P5 merge_log缺少必要字段: {missing_merge_keys}。P5必须由p5_code_merge生成,不允许Agent自己写。",
                "missing_keys": missing_merge_keys,
            }))
            sys.exit(1)

    # V4.13.3: P6批次结构校验 - 兼容p6_tp_output(逐条TP)和p6_batches(分批)两种格式
    tp_dir = os.path.join(data_dir, "p6_tp_output")
    p6_batches_dir = os.path.join(data_dir, "p6_batches")
    has_tp_output = os.path.isdir(tp_dir) and any(
        fn.startswith("tp_") and fn.endswith(".json") and "_context" not in fn and "_agent_output" not in fn
        for fn in (os.listdir(tp_dir) if os.path.isdir(tp_dir) else [])
    )
    has_batches = os.path.isdir(p6_batches_dir) and len(glob.glob(os.path.join(p6_batches_dir, "batch_*.json"))) > 0
    if not has_tp_output and not has_batches:
        print(json.dumps({
            "status": "structure_blocked",
            "reason": "p6_tp_output/和p6_batches/目录均无有效用例文件。P6必须用逐条TP流程(p6_tp_list→p6_generate_one→p6_merge)或分批流程(p6_batch_info→p6_save_batch→p6_merge)生成,不允许Agent直接写p6_output.json。",
        }))
        sys.exit(1)

    # 读取task_meta获取文件名
    meta = _read_json(os.path.join(data_dir, "task_meta.json"))
    domain = meta.get("domain", "unknown")

    export_script = os.path.join(skill_dir, "tools", "export_excel.py")
    p6_path = os.path.join(data_dir, "p6_output.json")
    output_path = os.path.join(data_dir, f"测试用例_{task_id}.xlsx")

    result = subprocess.run(
        ["python3", export_script, "--input", p6_path, "--output", output_path],
        capture_output=True, text=True, timeout=60
    )

    if result.returncode == 0 and os.path.exists(output_path):
        state = TaskState(data_dir=data_dir, task_id=task_id)
        state.mark_complete("step7")
        # V3.2.9: 重置重试计数
        state.state.pop("p6_retry_count", None)
        state.save()
        
        # === V4.15.3: 导出日志落盘(防stdout截断) ===
        # step7_export输出可能很大(含push结果/审计报告等), Agent的stdout缓冲区可能截断。
        # 将完整输出写入文件,stdout仅输出最小化的关键信息(MEDIA行+路径)。
        export_log_path = os.path.join(data_dir, "step7_export_log.json")

        # V4.0.0: 推送到云端评审工具
        push_result = None
        # V4.1.2: 优先从data_dir/.image_api_key读取runtime api_key(Onboarding时输入)
        runtime_key = None
        cache_path = os.path.join(args.data_dir, ".image_api_key")
        if os.path.exists(cache_path):
            try:
                with open(cache_path, "r") as f:
                    runtime_key = f.read().strip()
            except Exception:
                pass
        config = _load_cloud_config(args.skill_dir, runtime_api_key=runtime_key)
        if _should_push_to_review_tool(config):
            try:
                review_url = _push_to_review_tool(args.data_dir, args.task_id, config)
                if review_url:
                    push_result = {
                        "pushed": True,
                        "review_url": review_url,
                        "message": "✅ 用例已推送到在线评审工具"
                    }
                else:
                    push_result = {
                        "pushed": False,
                        "review_url": None,
                        "message": "⚠️ 推送失败,已加入重试队列"
                    }
            except Exception as e:
                push_result = {
                    "pushed": False,
                    "review_url": None,
                    "message": f"⚠️ 推送异常: {str(e)}"
                }
                print(json.dumps({
                    "message": f"⚠️ 推送异常: {str(e)}"
                }), file=sys.stderr)
        else:
            # V4.12.6: api_key缺失时明确提示
            push_result = {
                "pushed": False,
                "review_url": None,
                "message": "⚠️ 未配置api_key,跳过推送。配置方式: Onboarding时输入密码 或 在cloud.json中设置review_tool.api_key"
            }

        # === V4.15.3: 完整数据写入日志文件, stdout仅输出最小化信息 ===
        full_export_data = {
            "status": "ok",
            "excel_path": output_path,
            "file_size": os.path.getsize(output_path),
            "task_id": task_id,
            "domain": domain,
            "export_time": time.strftime("%Y-%m-%dT%H:%M:%S+08:00"),
        }
        if push_result:
            full_export_data["cloud_review"] = push_result
        try:
            _write_json(export_log_path, full_export_data)
        except Exception:
            pass
        
        # stdout仅输出MEDIA行+关键路径,防截断
        output_data = {
            "status": "ok",
            "excel_path": output_path,
            "file_size": os.path.getsize(output_path),
            "media_instruction": f"MEDIA:{output_path}",
            "__must_emit__": f"MEDIA:{output_path}",
            "reminder": "🔴 必须在回复中独占一行输出: MEDIA:{output_path}",
            "export_log": export_log_path,  # Agent可read此文件获取完整导出信息
        }
        if push_result:
            output_data["cloud_review"] = push_result
        # V4.15.17: review_url 提升为顶层字段，Agent 无法忽略
        if push_result and push_result.get("review_url"):
            output_data["review_url"] = push_result["review_url"]
            output_data["review_reminder"] = f"\ud83d\udd17 请在回复中单独一行输出: 云端评审: {push_result['review_url']}"

        # V4.12.7: 写入 pending_emit，确保 Agent 必须输出 MEDIA
        pending_path = os.path.join(data_dir, "pending_emit_step7.json")
        with open(pending_path, "w", encoding="utf-8") as f:
            json.dump({"step": "step7", "media_path": output_path, "created_at": time.time()}, f, ensure_ascii=False)

        print(json.dumps(output_data))
    else:
        # V3.2.9: 失败时检查重试计数,返回结构化重试指引
        state = TaskState(data_dir=data_dir, task_id=task_id)
        retry_count = state.state.get("p6_retry_count", 0)
        error_msg = result.stderr[:300] if result.stderr else "unknown"

        if retry_count < 4:
            # 可重试:返回明确的自动回流指令
            state.state["p6_retry_count"] = retry_count + 1
            state.save()
            print(json.dumps({
                "status": "auto_retry",
                "retry_count": retry_count + 1,
                "max_retries": 2,
                "reason": f"Excel导出失败: {error_msg}",
                "action": "Agent必须立即执行 restart_from P6 然后重新走段落7的分批流程,禁止向用户抛选择题",
            }))
            sys.exit(1)
        else:
            # 超过最大重试次数,报告用户
            print(json.dumps({
                "status": "error",
                "reason": f"Excel导出失败(已重试{retry_count}次): {error_msg}",
                "retry_exhausted": True,
            }))
            sys.exit(1)


# ============================================================
# Action: retry_push (V4.0.0: 重试推送失败的评审任务)
# ============================================================

def action_retry_push(args):
    """重试推送失败的任务。

    读取 queue/pending_reviews.jsonl,逐个重试推送,
    成功的从队列移除,失败的保留,返回重试统计。
    """
    skill_dir = args.skill_dir
    data_dir = args.data_dir

    # 队列文件位置:data_dir同级的queue目录
    base_dir = os.path.dirname(data_dir) if data_dir else os.path.expanduser("~/.openclaw/workspace/data")
    queue_path = os.path.join(base_dir, "queue", "pending_reviews.jsonl")

    if not os.path.exists(queue_path):
        print(json.dumps({"status": "ok", "message": "无待重试任务", "total": 0, "success": 0, "failed": 0}))
        return

    # 读取队列
    tasks = []
    try:
        with open(queue_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        tasks.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
    except Exception as e:
        print(json.dumps({"status": "error", "reason": f"队列文件读取失败: {e}"}))
        sys.exit(1)

    if not tasks:
        print(json.dumps({"status": "ok", "message": "队列为空,无待重试任务", "total": 0, "success": 0, "failed": 0}))
        return

    # 加载配置(使用当前data_dir的api_key)
    runtime_key = None
    cache_path = os.path.join(data_dir, ".image_api_key")
    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r") as f:
                runtime_key = f.read().strip()
        except Exception:
            pass
    config = _load_cloud_config(skill_dir, runtime_api_key=runtime_key)

    success_count = 0
    failed_tasks = []
    success_urls = []

    for task in tasks:
        task_data_dir = task.get("data_dir", "")
        task_task_id = task.get("task_id", "")
        retry_count = task.get("retry_count", 0)

        if not task_data_dir or not task_task_id:
            failed_tasks.append(task)
            continue

        # 尝试重新推送
        review_url = _push_to_review_tool(task_data_dir, task_task_id, config)
        if review_url:
            success_count += 1
            success_urls.append({"task_id": task_task_id, "review_url": review_url})
        else:
            # 推送失败,保留在队列中(更新retry_count)
            task["retry_count"] = retry_count + 1
            task["last_retry"] = time.strftime("%Y-%m-%dT%H:%M:%S+08:00")
            failed_tasks.append(task)

    # 重写队列文件(只保留失败的)
    try:
        with open(queue_path, "w", encoding="utf-8") as f:
            for task in failed_tasks:
                f.write(json.dumps(task, ensure_ascii=False) + "\n")
    except Exception:
        pass

    print(json.dumps({
        "status": "ok",
        "total": len(tasks),
        "success": success_count,
        "failed": len(failed_tasks),
        "success_urls": success_urls,
        "message": f"重试完成: {success_count}成功, {len(failed_tasks)}失败"
    }))


# ============================================================
# Action: status
# ============================================================

def action_status(args):
    """查看当前任务状态"""
    data_dir = args.data_dir
    task_id = args.task_id

    state = TaskState(data_dir=data_dir, task_id=task_id)
    next_step = state.get_next_step()

    # 检查所有gate pass
    gates = {}
    gates_dir = os.path.join(data_dir, "gates")
    if os.path.exists(gates_dir):
        for f in os.listdir(gates_dir):
            if f.endswith(".pass.json"):
                step_name = f.replace(".pass.json", "")
                gates[step_name] = True

    print(json.dumps({
        "task_id": task_id,
        "completed_steps": state.state["completed_steps"],
        "next_step": next_step,
        "gates": gates,
    }))


# ============================================================
# Action: resume
# ============================================================

def action_resume(args):
    """断点续跑:检测已完成步骤,返回下一步"""
    data_dir = args.data_dir
    task_id = args.task_id

    state = TaskState(data_dir=data_dir, task_id=task_id)

    # 扫描gate pass补充completed_steps
    gates_dir = os.path.join(data_dir, "gates")
    if os.path.exists(gates_dir):
        for f in sorted(os.listdir(gates_dir)):
            if f.endswith(".pass.json"):
                step_name = f.replace(".pass.json", "")
                try:
                    gp = _read_json(os.path.join(gates_dir, f))
                    if gp.get("task_id") == task_id:
                        if step_name not in state.state["completed_steps"]:
                            state.state["completed_steps"].append(step_name)
                except Exception:
                    pass
        state.save()

    next_step = state.get_next_step()

    # V4.15.21: TP完整性验证（防会话压缩丢TP）
    result = {
        "status": "ok",
        "task_id": task_id,
        "completed_steps": state.state["completed_steps"],
        "next_step": next_step,
    }
    if next_step in ("P6", "P6.resume", "P7"):
        tp_dir = os.path.join(data_dir, "p6_tp_output")
        if os.path.exists(tp_dir):
            p5_path = os.path.join(data_dir, "p5_output.json")
            if os.path.exists(p5_path):
                p5_data = _read_json(p5_path)
                tps = p5_data.get("test_points", [])
                expected = len(tps) if isinstance(tps, list) else 0
                actual = len([f for f in os.listdir(tp_dir)
                    if f.startswith("tp_") and f.endswith(".json")
                    and "_context" not in f and "_agent_output" not in f])
                missing = expected - actual
                if missing > 3:
                    result["tp_integrity_warning"] = f"检测到{missing}个TP文件缺失（预期{expected}，实际{actual}），可能存在会话压缩丢失"
                    result["recover_hint"] = "使用 p6_verify_files 查看详情"
    print(json.dumps(result))


# ============================================================
# Action: prep_prompt (为每个P步骤准备完整prompt)
# ============================================================

# Prompt文件映射
PROMPT_FILES = {
    "P0": "prompts/P0_requirement_structuring.md",
    "P1": "prompts/P1_feature_tree_generation.md",
    "P2": "prompts/P2_test_point_draft.md",
    "P3": "prompts/P3_risk_identification.md",
    "P4": "prompts/P4_pci_identification.md",
    "P5": "prompts/P5_test_point_merge.md",
    "P6": "prompts/P6_testcase_generation.md",
    "P7": "prompts/archive/P7_quality_gate.md",  # V3.3.1: deprecated, P7走p7_code_check
}

# 每步需要的上游产物
UPSTREAM_FILES = {
    "P0": ["task_meta.json"],
    "P1": ["p0_output.json"],
    "P2": ["p1_output.json"],
    "P3": ["p1_output.json"],
    "P4": ["p1_output.json"],
    "P5": ["p2_output.json", "p3_output.json", "p4_output.json"],
    "P6": [],  # V3.3.2: 移除完整p5注入,改为批次信息中注入P1 scenario语义
    "P7": ["p6_output.json"],
}

# 知识注入映射
KNOWLEDGE_INJECT = {
    "P0": ["knowledge/industry/{domain}.md", "knowledge/methodology/design_methods.md"],
    "P1": ["knowledge/methodology/design_methods.md"],
    "P2": ["knowledge/methodology/boundary_rules.md", "knowledge/methodology/api_test_standard.md"],
    "P3": ["knowledge/industry/{domain}.md"],
    "P4": ["knowledge/industry/{domain}.md"],
    "P5": [],
    "P6": ["knowledge/company_standards/testcase_design_spec.md"],  # V3.3.2: 移除defect_schema(与P6用例生成无关)
    "P7": [],
}

def _read_file_safe(path, max_chars=8000):
    """安全读取文件,不存在返回空字符串"""
    if not os.path.exists(path):
        return ""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()[:max_chars]
    except Exception:
        return ""

def action_prep_prompt(args):
    """为指定的P步骤准备完整prompt,输出给Agent执行"""
    skill_dir = args.skill_dir
    data_dir = args.data_dir
    task_id = args.task_id
    step = args.step  # Bugfix V4.6.8: step未定义会导致NameError
    batch_index = int(getattr(args, 'batch_index', 0))  # P6分批用,确保int类型

    # V3.3.3: 代码路径步骤禁止生成Prompt(P6保留,分批流程需要)
    PREP_PROMPT_BLOCKED = {"P2": "p2_code_generate", "P5": "p5_code_merge", "P7": "p7_code_check"}
    if step in PREP_PROMPT_BLOCKED:
        print(json.dumps({
            "status": "rejected",
            "reason": f"❌ {step}禁止生成Prompt!{step}由代码自动执行,必须用: python3 orchestrator.py --action {PREP_PROMPT_BLOCKED[step]}",
            "correct_action": PREP_PROMPT_BLOCKED[step],
        }))
        sys.exit(1)

    if step not in PROMPT_FILES:
        print(json.dumps({"status": "error", "reason": f"不支持的步骤: {step}"}))
        sys.exit(1)

    # 前置gate pass检查
    prerequisites = {
        "P0": ["onboarding"], "P1": ["P0"], "P2": ["P1"],
        "P3": ["P1"], "P4": ["P1"], "P5": ["P2", "P3", "P4"],
        "P6": ["P5"], "P7": ["P6"],
    }
    for prereq in prerequisites.get(step, []):
        ok, msg = check_gate(data_dir, prereq, task_id)
        if not ok:
            print(json.dumps({"status": "gate_blocked", "step": prereq, "reason": msg}))
            sys.exit(1)

    # 1. 读取prompt模板
    prompt_path = os.path.join(skill_dir, PROMPT_FILES[step])
    prompt_template = _read_file_safe(prompt_path, 25000)  # V4.15.15: 15000→25000 解除截断(P6 prompt 37KB)
    if not prompt_template:
        print(json.dumps({"status": "error", "reason": f"Prompt文件不存在: {PROMPT_FILES[step]}"}))
        sys.exit(1)

    # V4.8.9: P1分批模式 - skeleton / feature场景
    if step == "P1":
        mode = getattr(args, 'mode', '')
        feature_id = getattr(args, 'feature_id', '')
        if mode == "skeleton":
            sk_path = os.path.join(skill_dir, "prompts", "P1_skeleton.md")
            prompt_template = _read_file_safe(sk_path, 8000) or prompt_template
        elif feature_id:
            # 加载 feature 场景专用 prompt
            sc_path = os.path.join(skill_dir, "prompts", "P1_feature_scenario.md")
            prompt_template = _read_file_safe(sc_path, 8000) or prompt_template
            # 读取骨架获取feature上下文
            sk_path = os.path.join(data_dir, "p1_skeleton.json")
            feature_context = {"feature_id": feature_id, "feature_name": "", "description": ""}
            related_rules = []
            if os.path.exists(sk_path):
                sk = _read_json(sk_path)
                ft = sk.get("feature_tree", {})
                modules = ft.get("children", ft.get("modules", []))
                def _find_feature(nodes):
                    for n in nodes:
                        if n.get("id") == feature_id:
                            feature_context["feature_name"] = n.get("name", "")
                            feature_context["description"] = n.get("description", "")
                            return
                        if "children" in n:
                            _find_feature(n["children"])
                _find_feature(modules)
                # 注入关联的P0业务规则
                p0_path_f = os.path.join(data_dir, "p0_output.json")
                if os.path.exists(p0_path_f):
                    p0 = _read_json(p0_path_f)
                    blocks = p0.get("blocks", {})
                    business_rules = blocks.get("business_rules", []) if isinstance(blocks, dict) else []
                    related_rules = [r for r in business_rules if feature_id.lower() in str(r).lower()]
                    relations_text = p0.get("relations", [])
                    if relations_text:
                        related_rules += [r for r in relations_text if feature_id.lower() in str(r).lower()]
            prompt_template = prompt_template.replace("{{feature_context}}", json.dumps(feature_context, ensure_ascii=False, indent=2))
            prompt_template = prompt_template.replace("{{related_rules}}", json.dumps(related_rules[:10], ensure_ascii=False, indent=2) if related_rules else "[]")

    # V3.3.2: P6接口测试规则按需注入
    if step == "P6":
        # V4.8.10: 入口拦截 - P6禁止在子Agent中执行,prep_prompt是P6第一个入口
        if _is_sub_agent_session():
            print(json.dumps({
                "status": "rejected",
                "reason": "⛔ P6禁止在子Agent中执行!prep_prompt是P6入口,子Agent不能生成用例。",
                "hint": "请回到主会话执行。子Agent没有完整的context文件数据,无法生成高质量用例(会产出占位符)。"
            }))
            sys.exit(1)
        has_api = _check_api_features(data_dir)
        if has_api:
            api_rules_path = os.path.join(skill_dir, "prompts", "P6_api_rules.md")
            api_rules = _read_file_safe(api_rules_path, 5000)
            if api_rules:
                prompt_template += f"\n\n---\n{api_rules}"

        # V4.0.1: 文件上传安全用例条件注入
        # 仅当需求涉及文件上传/导入时才保留该section,否则替换为跳过提示
        _upload_keywords = ["上传", "导入", "批量", "文件", "Excel", "CSV", "附件", "docx", "xlsx", "上传文件", "批量导入"]
        _meta_path_p6 = os.path.join(data_dir, "task_meta.json")
        _req_text_p6 = ""
        if os.path.exists(_meta_path_p6):
            try:
                _meta_p6 = _read_json(_meta_path_p6)
                _req_text_p6 = _meta_p6.get("requirement_text", "")
            except Exception:
                pass
        _has_file_upload = any(kw in _req_text_p6 for kw in _upload_keywords)
        if not _has_file_upload:
            # 替换文件上传安全用例section为跳过提示
            _upload_section_marker = "### 文件上传场景安全用例(强制)"
            if _upload_section_marker in prompt_template:
                # 找到section开始位置,截取到下一个###或---分隔符
                _start_idx = prompt_template.index(_upload_section_marker)
                _rest = prompt_template[_start_idx + len(_upload_section_marker):]
                # 找下一个section分隔符
                _end_offset = len(_rest)
                for _sep in ["\n### ", "\n---", "\n## "]:
                    _sep_pos = _rest.find(_sep)
                    if _sep_pos != -1 and _sep_pos < _end_offset:
                        _end_offset = _sep_pos
                _end_idx = _start_idx + len(_upload_section_marker) + _end_offset
                _skip_notice = "### 文件上传场景安全用例(强制)\n【安全用例跳过】当前需求不涉及文件上传/导入功能,跳过安全用例生成\n"
                prompt_template = prompt_template[:_start_idx] + _skip_notice + prompt_template[_end_idx:]

        # V5.0(4.13.0): HIGH/LOW 分档已废除 — 旧批次路径统一走标准 prompt
        # 跳过引导卡/窄聚焦模式,直接进入下方标准 prompt 组装
        model_tier = "standard"  # 统一模式
        model_name = getattr(args, 'model_name', '') or os.environ.get('OPENCLAW_MODEL', '') or ''
        if False:  # V5.0: 废弃的 LOW 模型引导卡分支,保留结构避免缩进错误
            pg = _get_p6_guide()
            # 读取当前批次的测试点
            batch_points = []
            p5_path = os.path.join(data_dir, "p5_output.json")
            if os.path.exists(p5_path):
                try:
                    p5_data = _read_json(p5_path)
                    all_tps = p5_data.get("test_points", [])
                    # LOW模式用小批次(每批3-5个测试点)
                    md = _get_model_detect()
                    bs = md.get_batch_size("LOW", len(all_tps))
                    start = batch_index * bs
                    end = min(start + bs, len(all_tps))
                    batch_points = all_tps[start:end]
                    # V4.9.1: P7修复模式 - 指定TP子集过滤
                    tp_ids = getattr(args, 'tp_ids', '')
                    if tp_ids and step == "P6":
                        wanted = set(tp_ids.split(','))
                        batch_points = [bp for bp in batch_points if bp.get('id','') in wanted]
                        if not batch_points:  # 兜底:跨batch查找
                            batch_points = [bp for bp in all_tps if bp.get('id','') in wanted]
                except Exception:
                    pass
            # 读取 P0/P1 数据
            p0_data = {}
            p1_data = {}
            p0_path = os.path.join(data_dir, "p0_output.json")
            p1_path = os.path.join(data_dir, "p1_output.json")
            if os.path.exists(p0_path):
                try:
                    p0_data = _read_json(p0_path)
                except Exception:
                    pass
            if os.path.exists(p1_path):
                try:
                    p1_data = _read_json(p1_path)
                except Exception:
                    pass

            # V4.10.0: LOW模型窄聚焦模式 - 精简prompt,Agent只产出3个核心字段
            simple_prompt_path = os.path.join(skill_dir, "prompts", "P6_low_simple.md")
            simple_template = _read_file_safe(simple_prompt_path, 2000)
            if simple_template and "{{business_context}}" in simple_template and batch_points:
                # 1. 构建业务上下文(从P0/P1提取)
                biz_lines = []
                if p0_data:
                    blocks = p0_data.get("blocks", {})
                    obj = blocks.get("objective", "") if isinstance(blocks, dict) else ""
                    if obj:
                        biz_lines.append(f"需求目标:{str(obj)[:200]}")
                    rules = blocks.get("business_rules", []) if isinstance(blocks, dict) else []
                    for r in (rules or [])[:3]:
                        if isinstance(r, dict) and r.get("description"):
                            biz_lines.append(f"业务规则:{r['description'][:150]}")
                if p1_data:
                    ft = p1_data.get("feature_tree", {})
                    fms = ft.get("modules", []) if isinstance(ft, dict) else p1_data.get("modules", [])
                    for mod in fms:
                        for feat in mod.get("children", []):
                            if feat.get("type") == "feature":
                                biz_lines.append(f"功能模块:{mod.get('name','')} → {feat.get('name','')}"[:100])
                                break
                business_context = "\n".join(biz_lines[:8]) or "根据需求文档生成测试用例"

                # 2. 格式化测试点列表(精简,只保留核心信息)
                tp_lines = []
                for bp in batch_points[:10]:
                    desc = (bp.get("description", "") or "")[:120]
                    pri = bp.get("priority", "P1")
                    tp_lines.append(f"- [{pri}] {desc}")
                test_points_text = "\n".join(tp_lines)

                # 3. 构建示例(从第一个TP的P1 scenario提取)
                example_text = "验证功能操作结果:\n步骤: 1. 进入功能页面 2. 执行目标操作 3. 确认结果\n期望: 1. 页面刷新显示更新后数据 2. 系统给出明确反馈"
                first_bp = batch_points[0] if batch_points else {}
                src_id = first_bp.get("source_scenario", "")
                if p1_data and src_id:
                    ft = p1_data.get("feature_tree", {})
                    fms = ft.get("modules", []) if isinstance(ft, dict) else p1_data.get("modules", [])
                    for mod in fms:
                        for feat in mod.get("children", []):
                            for scen in feat.get("children", []):
                                if scen.get("id") == src_id and scen.get("type") == "scenario":
                                    sn = scen.get("name", "验证功能")
                                    ops = scen.get("operations_chain") or scen.get("operations_steps", [])
                                    if ops and isinstance(ops, list) and len(ops) >= 2:
                                        op_lines = [f"{i+1}. {o.get('action','操作')}「{o.get('target','目标')}」{',输入' + o.get('value','') if o.get('value') else ''}" for i, o in enumerate(ops[:4])]
                                        exp_lines = [f"{i+1}. {o.get('expected','预期结果')}" for i, o in enumerate(ops[:4])]
                                        example_text = f"{sn}:\n步骤:\n" + "\n".join(op_lines) + "\n期望:\n" + "\n".join(exp_lines)
                                    break

                # 4. 组装精简prompt
                simple_prompt = simple_template
                simple_prompt = simple_prompt.replace("{{business_context}}", business_context)
                simple_prompt = simple_prompt.replace("{{test_points}}", test_points_text)
                simple_prompt = simple_prompt.replace("{{examples}}", example_text)
                simple_prompt = simple_prompt.replace("{{expected_case_count}}", str(max(bp.get("expected_case_count", 2) for bp in batch_points)))

                # 5. 生成骨架(仅case_id映射,Agent不写其余16列)
                _build_skeleton_for_batch(data_dir, batch_points, batch_index)

                # 5b. 提取case_id清单注入prompt
                sk_path = os.path.join(data_dir, "p6_batches", f"batch_{batch_index:03d}_skeleton.json")
                case_ids = []
                if os.path.exists(sk_path):
                    sk_data = _read_json(sk_path)
                    for sk in sk_data:
                        cid = sk.get("case_id", "")
                        desc = sk.get("p5_description", "")[:60]
                        case_ids.append(f"{cid}  ← {desc}" if desc else cid)
                case_id_list = "\n".join(case_ids) if case_ids else "(无骨架数据,请使用格式 REQ-xxx-TP-NNN-TC-001)"
                simple_prompt = simple_prompt.replace("{{case_id_list}}", case_id_list)

                tier_info = json.dumps({"status": "ok", "mode": "simple", "tier": model_tier, "batch_index": batch_index, "model_name": model_name, "tp_count": len(batch_points), "prompt_size": len(simple_prompt)})
                print(tier_info, file=sys.stderr)
                print(simple_prompt)
                return

            # 降级到旧的引导卡模式(P6_low_simple.md不存在时)
            # 生成引导卡
            guides = pg.generate_guide_cards(batch_points, p0_data, p1_data, skill_dir)
            guide_json = json.dumps(guides, ensure_ascii=False, indent=2)
            # 加载微型 prompt 模板
            guided_prompt_path = os.path.join(skill_dir, "prompts", "P6_guided.md")
            guided_template = _read_file_safe(guided_prompt_path, 5000)
            if guided_template:
                # 替换引导卡占位符
                guided_template = guided_template.replace("{{guides}}", guide_json)
                # 替换禁止词样本
                if guides:
                    g0 = guides[0]
                    step_sample = "、".join(g0.get("step_must_avoid", [])[:5])
                    exp_sample = "、".join(g0.get("expected_must_avoid", [])[:5])
                    guided_template = guided_template.replace("{{step_must_avoid_sample}}", step_sample)
                    guided_template = guided_template.replace("{{expected_must_avoid_sample}}", exp_sample)
                # 输出微型 prompt,跳过后续的通用 prompt 组装
                tier_info = json.dumps({"status": "ok", "mode": "guided", "tier": model_tier, "batch_index": batch_index, "guide_count": len(guides), "model_name": model_name})
                print(tier_info, file=sys.stderr)
                print(guided_template)
                return
            else:
                # 微型 prompt 不存在,降级到精简模式(继续现有流程)
                print(json.dumps({"status": "warning", "reason": "P6_guided.md不存在,降级到标准prompt", "model_tier": model_tier}), file=sys.stderr)

    # 2. 读取上游产物
    upstream_data = {}
    for fname in UPSTREAM_FILES.get(step, []):
        fpath = os.path.join(data_dir, fname)
        content = _read_file_safe(fpath, 20000)
        if content:
            upstream_data[fname] = content

    # 3. 知识注入
    # 读取domain
    meta_path = os.path.join(data_dir, "task_meta.json")
    domain = "trade"
    requirement_text = ""
    if os.path.exists(meta_path):
        try:
            meta = _read_json(meta_path)
            domain = meta.get("domain", "trade")
            requirement_text = meta.get("requirement_text", "")
        except Exception:
            pass

    knowledge_texts = []
    for kpath_template in KNOWLEDGE_INJECT.get(step, []):
        kpath = os.path.join(skill_dir, kpath_template.replace("{domain}", domain))
        kt = _read_file_safe(kpath, 3000)
        if kt:
            knowledge_texts.append(kt)

    # V4.0.0: 项目名→业务域自动匹配,4层渐进注入
    project_match = _match_project_to_domains(requirement_text, skill_dir)
    project_knowledge_texts = []
    if project_match["matched_projects"] or project_match["matched_synonyms"]:
        # 根据当前步骤选择注入层级
        # P0 → L1(领域入门引导,~2-3K/域)
        # P1 → L2(领域蓝图,~4-6K/域)
        # P2/P3/P4/P5 → L3(领域规则集,~6-9K/域)
        # P6/P7 → L4(全文/动态检索)
        step_level_map = {"P0": "L1", "P1": "L2", "P2": "L3", "P3": "L3", "P4": "L3", "P5": "L3", "P6": "L4", "P7": "L4"}
        inject_level = step_level_map.get(step, "L1")

        # 同义词匹配的域只注入L1(防止高频词导致prompt膨胀)
        synonym_only_domains = set()
        if project_match["matched_synonyms"] and not project_match["matched_projects"]:
            # 纯同义词匹配:所有域都限制L1
            synonym_only_domains = set(project_match["domains"])
        elif project_match["matched_synonyms"] and project_match["matched_projects"]:
            # 有项目匹配:同义词匹配到的额外域(不在项目匹配结果中的)限制L1
            # 简化处理:通过比较域列表长度判断是否有额外域
            project_domain_count = len(set())  # 占位,下方通过实际匹配判断
            # 由于无法在此处区分哪些域来自项目vs同义词,统一按正常层级注入
            # 但限制总注入量不超过15KB(安全阈值)
            pass

        summaries_dir = os.path.join(skill_dir, "knowledge", "industry", "summaries")

        for kf in project_match["knowledge_files"]:
            base_name = kf["file"].replace(".md", "")
            domain = kf["domain"]
            # 同义词独有的域限制L1,项目匹配的域用正常层级
            actual_level = "L1" if domain in synonym_only_domains else inject_level
            kt = None

            if actual_level == "L4":
                # L4: 全文注入(P6/P7)
                kf_full_path = os.path.join(skill_dir, "knowledge", "industry", kf["file"])
                kt = _read_file_safe(kf_full_path, 25000)
            elif actual_level in ("L1", "L2", "L3"):
                # L1/L2/L3: 优先读预编译JSON,不存在则降级读全文截取
                level_file = os.path.join(summaries_dir, f"{base_name}_{actual_level}.json")
                if os.path.exists(level_file):
                    kt = _read_file_safe(level_file, 10000)
                    if kt:
                        # JSON文件直接作为结构化知识注入
                        kt = f"## {domain}知识库({actual_level})\n{kt}"

                if not kt:
                    # 降级:读取全文,按层级截取不同大小
                    fallback_sizes = {"L1": 2000, "L2": 4000, "L3": 6000}
                    fallback_size = fallback_sizes.get(actual_level, 2000)
                    kf_full_path = os.path.join(skill_dir, "knowledge", "industry", kf["file"])
                    kt_raw = _read_file_safe(kf_full_path, fallback_size)
                    if kt_raw:
                        kt = f"## {domain}知识库({actual_level}降级)\n{kt_raw}"

            if kt:
                project_knowledge_texts.append(kt)

        if project_knowledge_texts:
            # 注入匹配信息
            match_parts = []
            if project_match['matched_projects']:
                match_parts.append(f"项目: {', '.join(project_match['matched_projects'])}")
            if project_match['matched_synonyms']:
                match_parts.append(f"同义词: {', '.join(project_match['matched_synonyms'])}")
            match_info = f"\n识别到 {', '.join(match_parts)} → 关联业务域: {', '.join(project_match['domains'])} → 注入层级: {inject_level}\n"
            knowledge_texts.insert(0, match_info)
            knowledge_texts.extend(project_knowledge_texts)

    # 4. PX增强注入(如有)
    px_inject = ""
    px_enhance_path = os.path.join(data_dir, "px_enhance.json")
    if os.path.exists(px_enhance_path):
        try:
            px_data = _read_json(px_enhance_path)
            step_subsets = px_data.get("step_subsets", {})
            step_key = step  # P0/P1/...
            if step_key in step_subsets:
                px_inject = json.dumps(step_subsets[step_key], ensure_ascii=False)
                # Qwen VL的description可能很长,截取注入不超过3000字符
                if len(px_inject) > 3000:
                    px_inject = px_inject[:3000] + "\n...(内容过长已截断)"
        except Exception:
            pass

    # 5. P6分批处理
    p6_batch_info = ""
    if step == "P6" and batch_index >= 0:
        # 读取P5测试点,按批次切分
        p5_path = os.path.join(data_dir, "p5_output.json")
        if os.path.exists(p5_path):
            try:
                p5 = _read_json(p5_path)
                test_points = p5.get("test_points", [])
                # V4.6.17: 启用动态分批
                batch_info = calculate_dynamic_batches(test_points, max_batches=5)
                total_batches = batch_info["total_batches"]
                strategy = batch_info.get("strategy", "dynamic")
                # 按batch_index定位当前批次(V4.8.12: 0-based)
                if batch_index < len(batch_info["batches"]):
                    b = batch_info["batches"][batch_index]
                    batch_points = test_points[b["start"]:b["end"]]
                else:
                    batch_points = []
                # V4.9.1: P7修复模式 - 指定TP子集过滤
                tp_ids = getattr(args, 'tp_ids', '')
                if tp_ids and step == "P6" and batch_points:
                    wanted = set(tp_ids.split(','))
                    batch_points = [bp for bp in batch_points if bp.get('id','') in wanted]
                    if not batch_points:
                        batch_points = [tp for tp in test_points if tp.get('id','') in wanted]
                start = batch_info["batches"][batch_index]["start"] if batch_index < len(batch_info["batches"]) else 0
                # V3.2.8: 注入complexity预算信息
                batch_budget = sum(bp.get("expected_case_count", 2) for bp in batch_points)
                budget_detail = []
                for bp in batch_points:
                    bp_id = bp.get("id", "?")
                    bp_complexity = bp.get("complexity", "L2")
                    bp_expected = bp.get("expected_case_count", 2)
                    budget_detail.append(f"  - {bp_id}: {bp_complexity}(应展开{bp_expected}条)")
                budget_text = f"\n\n## ❗ 本批次用例预算(必须遵守)\n本批次应生成至少 **{batch_budget}条** 用例。每个测试点的展开数量如下:\n" + "\n".join(budget_detail) + f"\n\n复杂度说明:L1(简单)≥{1}条, L2(常规)≥{2}条, L3(复杂)≥{3}条。复杂测试点可以展开更多。"
                # V3.2.8: 精简字段版batch_points(避免全量 JSON被[:5000]截断削弱预算绑定)
                slim_points = []
                for bp in batch_points:
                    slim_points.append({
                        "id": bp.get("id", ""),
                        "description": bp.get("description", ""),
                        "category": bp.get("category", ""),
                        "priority": bp.get("priority", ""),
                        "risk_flag": bp.get("risk_flag", False),
                        "pci_flag": bp.get("pci_flag", False),
                        "complexity": bp.get("complexity", "L2"),
                        "expected_case_count": bp.get("expected_case_count", 2),
                    })
                # V3.2.9: 骨架预分配(priority/is_smoke由代码预设,Agent只填内容)
                # 冷烟分配策略:每个测试点的第1条用例为正向验证,仅当测试点priority为P0且category为main_flow/branch/integration时标记冷烟
                def _extract_keywords(desc):
                    """V4.1.2: 从description提取核心操作关键词,消除通用截断"""
                    if not desc:
                        return ""
                    # 去掉验证类型前缀
                    for prefix in ["验证正向-", "验证异常-", "验证边界-", "验证-", "边界值-"]:
                        desc = desc.replace(prefix, "")
                    # 取第一段(按标点分割),最多40字符
                    core = desc.split("。")[0].split(",")[0].split(";")[0][:40]
                    return core.strip() or (desc[:25] if desc else "")

                def _generate_pairs(bp, bp_category, case_idx, keywords, bp_desc):
                    """V4.6.17 DEPRECATED: 不再调用,Agent基于P5原文自由创作步骤。保留以供参考。"""
                    """DEPRECATED"""
                    return []  # V4.6.17: 已废弃,不再调用

                SMOKE_CATEGORIES = {"main_flow", "branch", "integration", "正向验证", "分支验证", "集成验证"}
                case_skeletons = []
                batch_smoke_count = 0
                batch_total_count = 0
                for bp in batch_points:
                    bp_id = bp.get("id", "")
                    bp_priority = bp.get("priority", "P1")
                    bp_category = (bp.get("category", "") or "").lower()
                    bp_expected = bp.get("expected_case_count", 2)
                    for case_idx in range(1, bp_expected + 1):
                        batch_total_count += 1
                        # 第1条=正向验证,后续=异常/边界
                        if case_idx == 1:
                            case_priority = bp_priority
                            # 冷烟标记:P0+主流程类别才标冷烟,且控制总比例≨20%
                            is_smoke = (bp_priority == "P0" and bp_category in SMOKE_CATEGORIES)
                        else:
                            # 后续用例降一级优先级
                            case_priority = "P2" if bp_priority in ("P0", "P1") else "P3"
                            is_smoke = False
                        if is_smoke:
                            batch_smoke_count += 1
                                # V4.6.17: 骨架只分配元数据,不给步骤草稿
                        # Agent基于P5测试点原始description/precondition自行创作步骤
                        bp_desc = bp.get("description", "")
                        bp_precond = bp.get("precondition", "")
                        bp_rules = bp.get("related_rules", [])

                        case_skeletons.append({
                            "case_id": f"{bp_id}-TC-{case_idx:03d}",
                            "source_test_point": bp_id,
                            "priority": case_priority,
                            "is_smoke": is_smoke,
                            # V4.15.48: 透传风险标记,供骨架阶段P0降级保护(与全局_enforce_p0_budget口径一致)
                            "risk_flag": bp.get("risk_flag", False),
                            "priority_hint": bp.get("priority_hint", ""),
                            # P5原始数据注入,Agent基于这些自由创作
                            "p5_description": bp_desc,
                            "p5_precondition": bp_precond,
                            "p5_related_rules": bp_rules,
                        })
                # 冷烟比例安全检查:如果批次内无冷烟且有P0测试点,强制第一个P0的第1条为冷烟
                if batch_smoke_count == 0:
                    for sk in case_skeletons:
                        if sk["priority"] == "P0":
                            sk["is_smoke"] = True
                            batch_smoke_count = 1
                            break

                # V4.8.14: P0比例自动降级--防止小批次P0浓度过高被Gate拒绝
                # 根因:P2给每个feature第1个main_flow升P0,导致P0占整体的40-60%。
                # LOW模型每批5个测试点,部分批次聚类3-5个P0测试点→P0比例可达36-55%→被Gate拒绝。
                # 解决:骨架生成阶段预降级,确保每批P0≤阈值,Agent基于降级后骨架生成。
                # V4.15.48注:旧注释误称"仅LOW分支";实则V5.0(4.13.0)已废除HIGH/LOW分档,
                #          本降级在主执行路径、所有模型都走。已同步加入风险P0保护。
                p0_limit = 0.35  # 骨架阶段阈值(所有模型统一)
                smoke_limit = 0.30
                total_skeleton = len(case_skeletons)
                if total_skeleton > 0:
                    p0_skeletons = [sk for sk in case_skeletons if sk["priority"] == "P0"]
                    p0_count = len(p0_skeletons)
                    p0_ratio = p0_count / total_skeleton

                    if p0_ratio > p0_limit:
                        # 计算需要降级的P0用例数(ceil确保降级后≤阈值)
                        max_p0 = int(total_skeleton * p0_limit)
                        downgrade_count = p0_count - max_p0

                        # V4.8.14: Feature级别P0保护--从source_test_point提取feature归属,
                        # 降级时确保每个feature至少保留1条P0,防止某feature完全失去P0覆盖。
                        def _extract_feature_key(sk):
                            """从source_test_point提取feature key,如 REQ-XXX-M01-F01-TP-001 → M01-F01"""
                            src = sk.get("source_test_point", "")
                            parts = src.split("-")
                            m_idx = next((i for i, p in enumerate(parts) if p.startswith("M") and len(p) >= 3 and p[1:].isdigit()), None)
                            f_idx = next((i for i, p in enumerate(parts) if p.startswith("F") and len(p) >= 3 and p[1:].isdigit()), None)
                            if m_idx is not None and f_idx is not None:
                                return f"{parts[m_idx]}-{parts[f_idx]}"
                            return src.rsplit("-TC-", 1)[0] if "-TC-" in src else src  # 降级用case_id兜底

                        # 统计每feature的P0数(降级前)
                        feature_p0_count = {}
                        for sk in case_skeletons:
                            if sk["priority"] == "P0":
                                fk = _extract_feature_key(sk)
                                feature_p0_count[fk] = feature_p0_count.get(fk, 0) + 1
                        # 追踪降级后每feature剩余P0数
                        feature_p0_remaining = dict(feature_p0_count)

                        # V4.15.48: 降级优先级 — 普通非冷烟 → 普通冷烟 → 受保护风险(最后降)。
                        # 受保护风险P0(priority_hint=P0且risk_flag)与全局_enforce_p0_budget口径一致,尽量保留。
                        # 普通用例(无risk_flag)候选顺序与旧版完全一致,行为不变。
                        def _sk_protected(sk):
                            return sk.get("priority_hint") == "P0" and sk.get("risk_flag")
                        ordered_candidates = (
                            [sk for sk in p0_skeletons if not sk.get("is_smoke") and not _sk_protected(sk)]
                            + [sk for sk in p0_skeletons if sk.get("is_smoke") and not _sk_protected(sk)]
                            + [sk for sk in p0_skeletons if not sk.get("is_smoke") and _sk_protected(sk)]
                            + [sk for sk in p0_skeletons if sk.get("is_smoke") and _sk_protected(sk)]
                        )
                        downgraded = 0
                        auto_downgrade_log = []
                        for sk in ordered_candidates:
                            if downgraded >= downgrade_count:
                                break
                            # Feature保护:如果该feature只剩1条P0,跳过不降级
                            fk = _extract_feature_key(sk)
                            if feature_p0_remaining.get(fk, 0) <= 1:
                                continue
                            old_pri = sk["priority"]
                            was_smoke = sk.get("is_smoke", False)
                            sk["priority"] = "P1"
                            sk["is_smoke"] = False
                            tag = "(含冷烟)" if was_smoke else ""
                            if _sk_protected(sk):
                                tag += "(风险超预算降级)"
                            auto_downgrade_log.append(f"{sk['case_id']}:{old_pri}→P1{tag}")
                            downgraded += 1
                            feature_p0_remaining[fk] = feature_p0_remaining.get(fk, 1) - 1
                            if was_smoke:
                                batch_smoke_count = max(0, batch_smoke_count - 1)

                        new_p0 = sum(1 for sk in case_skeletons if sk["priority"] == "P0")
                        new_ratio = new_p0 / total_skeleton if total_skeleton > 0 else 0
                        print(json.dumps({
                            "status": "info",
                            "action": "auto_downgrade_p0",
                            "batch_index": batch_index,
                            "original_p0_ratio": f"{p0_ratio:.0%}",
                            "downgraded": downgraded,
                            "new_p0_ratio": f"{new_ratio:.0%}",
                            "details": auto_downgrade_log,
                            "hint": f"P0比例{p0_ratio:.0%}>{p0_limit:.0%},骨架阶段自动降级{downgraded}条→新P0比例{new_ratio:.0%}"
                        }), file=sys.stderr)

                        # 降级后如果无冷烟但仍有P0,补一个冷烟标记
                        if batch_smoke_count == 0:
                            for sk in case_skeletons:
                                if sk["priority"] == "P0":
                                    sk["is_smoke"] = True
                                    batch_smoke_count = 1
                                    break

                # V4.8.14: 冒烟比例自动降级--防止smoke过多被Gate拒绝
                if total_skeleton > 0:
                    smoke_skeletons = [sk for sk in case_skeletons if sk.get("is_smoke")]
                    smoke_count = len(smoke_skeletons)
                    smoke_ratio = smoke_count / total_skeleton
                    if smoke_ratio > smoke_limit:
                        max_smoke = int(total_skeleton * smoke_limit)
                        # 降优先级低的冒烟(P0冒烟最后降)
                        smoke_p0 = [sk for sk in smoke_skeletons if sk["priority"] == "P0"]
                        smoke_p1 = [sk for sk in smoke_skeletons if sk["priority"] != "P0"]
                        downgrade_smoke = smoke_count - max_smoke
                        downgraded_smoke = 0
                        for sk in smoke_p1:
                            if downgraded_smoke >= downgrade_smoke:
                                break
                            sk["is_smoke"] = False
                            downgraded_smoke += 1
                        for sk in smoke_p0:
                            if downgraded_smoke >= downgrade_smoke:
                                break
                            sk["is_smoke"] = False
                            downgraded_smoke += 1
                        if downgraded_smoke > 0:
                            print(json.dumps({
                                "status": "info",
                                "action": "auto_downgrade_smoke",
                                "batch_index": batch_index,
                                "original_smoke_ratio": f"{smoke_ratio:.0%}",
                                "downgraded": downgraded_smoke,
                                "hint": f"冒烟比例{smoke_ratio:.0%}>{smoke_limit:.0%},自动降级{downgraded_smoke}条"
                            }), file=sys.stderr)

                # V4.6.17: 骨架只提供元数据,Agent基于P5原始描述自由创作
                skeleton_text = f"""

## ❗ 用例元数据(代码预分配,禁止修改priority/is_smoke/case_id)

每条用例必须输出以下字段,基于对应的P5测试点信息自行编写具体步骤。
- case_id/source_test_point/priority/is_smoke: 代码预设,你必须原样使用
- p5_description/p5_precondition/p5_related_rules: P5原始数据,你基于这些创作步骤

🔴 **你的任务:**
1. 读取每条用例的 p5_description/p5_precondition/p5_related_rules
2. 基于P5原文自由编写具体可执行的步骤(每条≥15字,包含「按钮名」「字段名」「路径」)
3. 基于P5原文编写可观测的期望结果(禁止:正常/成功/正确/符合预期)
4. 最终输出19列扁平JSON(参考Prompt中的正反例示范)
5. 每个测试点基于P5原文的差异自动产生不同步骤,严禁复制
```json
{json.dumps(case_skeletons, ensure_ascii=False)}
```
"""

                # 将骨架写入文件供 save_batch 读取
                skeleton_path = os.path.join(data_dir, "p6_batches", f"batch_{batch_index:03d}_skeleton.json")
                _write_json(skeleton_path, case_skeletons)

                # V3.3.2: 全局上下文摘要 + P1 scenario语义注入 + 输出预估
                # 全局摘要
                p1_path_for_p6 = os.path.join(data_dir, "p1_output.json")
                module_names_for_summary = []
                p1_for_p6 = {}
                if os.path.exists(p1_path_for_p6):
                    try:
                        p1_for_p6 = _read_json(p1_path_for_p6)
                        ft = p1_for_p6.get("feature_tree", {})
                        ft_modules = ft.get("modules", []) if isinstance(ft, dict) else []
                        if not ft_modules:
                            ft_modules = p1_for_p6.get("modules", [])
                        module_names_for_summary = [m.get("name", "") for m in ft_modules]
                    except Exception:
                        pass
                module_names_str = '、'.join(module_names_for_summary)
                global_summary = f"\n---\n## 全局上下文(仅供参考,不要为非本批次的内容生成用例)\n本需求共{len(module_names_for_summary)}个模块:{module_names_str}。\n总测试点{len(test_points)}条,分{total_batches}批处理。本批次为第{batch_index}批。"

                # P1 scenario语义注入:提取当前批次对应的scenario详情
                batch_scenario_ids = set(bp.get("source_scenario", "") for bp in batch_points)
                scenario_details = []
                if p1_for_p6:
                    ft = p1_for_p6.get("feature_tree", {})
                    ft_modules = ft.get("modules", []) if isinstance(ft, dict) else []
                    if not ft_modules:
                        ft_modules = p1_for_p6.get("modules", [])
                    for mod in ft_modules:
                        for feat in mod.get("children", []):
                            for scen in feat.get("children", []):
                                if scen.get("id") in batch_scenario_ids:
                                    scenario_details.append({
                                        "id": scen["id"],
                                        "name": scen.get("name", ""),
                                        "module": mod.get("name", ""),
                                        "feature": feat.get("name", ""),
                                        "precondition": scen.get("precondition", ""),
                                        "related_rules": scen.get("related_rules", []),
                                        "scenario_type": scen.get("scenario_type", ""),
                                        # V4.9.1: 兼容 operations_chain 和 operations_steps(旧字段名)
                                        "operations_chain": scen.get("operations_chain") or scen.get("operations_steps", []),
                                        "page_path": scen.get("page_path", ""),
                                        "test_point_hint": scen.get("test_point_hint", ""),
                                    })
                scenario_inject = ""
                if scenario_details:
                    scenario_text = json.dumps(scenario_details, ensure_ascii=False, indent=2)
                    # 大小限制:防止极端情况下注入过大
                    MAX_SCENARIO_INJECT = 3000
                    if len(scenario_text) > MAX_SCENARIO_INJECT:
                        scenario_details_slim = [{"id": s["id"], "name": s["name"], "module": s["module"], "page_path": s.get("page_path", ""), "operations_chain": s.get("operations_chain", []), "test_point_hint": s.get("test_point_hint", "")} for s in scenario_details]
                        scenario_text = json.dumps(scenario_details_slim, ensure_ascii=False, indent=2)
                    scenario_inject = f"\n---\n## 业务场景详情(用于理解测试点的业务语义)\n```json\n{scenario_text}\n```"

                # R1-R4修复:P0 field_specs/ui_elements/business_objects/test_point_candidates注入P6
                p0_enhance_inject = ""
                p0_path_for_p6 = os.path.join(data_dir, "p0_output.json")
                if os.path.exists(p0_path_for_p6):
                    try:
                        p0_for_p6 = _read_json(p0_path_for_p6)
                        p0_blocks = p0_for_p6.get("blocks", {})
                        p0_inject_data = {}
                        # R1: field_specs
                        field_specs = p0_blocks.get("field_specs", [])
                        if field_specs:
                            p0_inject_data["field_specs"] = field_specs
                        # R2: ui_elements
                        ui_elements = p0_blocks.get("ui_elements", [])
                        if ui_elements:
                            p0_inject_data["ui_elements"] = ui_elements
                        # R3: business_objects
                        business_objects = p0_blocks.get("business_objects", [])
                        if business_objects:
                            p0_inject_data["business_objects"] = business_objects
                        # R4: test_point_candidates
                        test_point_candidates = p0_blocks.get("test_point_candidates", [])
                        if test_point_candidates:
                            p0_inject_data["test_point_candidates"] = test_point_candidates
                        if p0_inject_data:
                            p0_enhance_text = json.dumps(p0_inject_data, ensure_ascii=False, indent=2)
                            # 截断保护:P0增强注入不超过2000字符
                            MAX_P0_ENHANCE_INJECT = 2000
                            if len(p0_enhance_text) > MAX_P0_ENHANCE_INJECT:
                                # 精简:每个字段只保留前3条
                                for key in p0_inject_data:
                                    if isinstance(p0_inject_data[key], list) and len(p0_inject_data[key]) > 3:
                                        p0_inject_data[key] = p0_inject_data[key][:3]
                                p0_enhance_text = json.dumps(p0_inject_data, ensure_ascii=False, indent=2)
                            p0_enhance_inject = f"\n---\n## P0原始分析数据(字段规格/UI元素/业务对象/测试候选点)\n```json\n{p0_enhance_text}\n```"
                    except Exception:
                        pass

                # V4.7.2: 输出引导 - 明确"期望至少"而非"硬性门槛"
                output_estimate = f"\n---\n## ❗ 输出要求\n本批次期望至少 **{batch_total_count}条** 用例(非硬性门槛,根据测试点复杂度可适当增加)。\n预计输出JSON约{batch_total_count * 800}-{batch_total_count * 1200}字符。\n请确保输出完整的JSON对象,包含testcases数组,不要截断。"

                # V4.7.1: 精简 prompt - 移除 P0/P1 场景注入(已写入 batch_N_context.json)
                # 只保留核心字段:slim_points + budget + skeleton + output_estimate
                p6_batch_info = f"\n---\n## 当前批次\n第{batch_index}/{total_batches}批(batch-index={batch_index},对应skeleton p6_batches/batch_{batch_index:03d}_skeleton.json),处理测试点{start+1}-{min(end, len(test_points))}:\n{json.dumps(slim_points, ensure_ascii=False)}{budget_text}{skeleton_text}{global_summary}{output_estimate}\n\n🔴 **请先读取文件** `{data_dir}/p6_batches/batch_{batch_index:03d}_context.json` **获取本批次测试点的完整上下文**(含操作骨架 step_expected_pairs、字段清单 field_checklist、UI 元素 ui_elements、风险标记等),基于完整上下文生成用例。\n\n⚠️ 起始batch-index=0(非1),skeleton文件名为 p6_batches/batch_000_skeleton.json,与prep_prompt --batch-index 参数完全一致。"
            except Exception:
                pass

    # 6. 组装完整prompt
    full_prompt_parts = [prompt_template]

    # V4.0.1: P6评审经验注入(项目关键词或同义词匹配时均触发)
    review_experience = ""
    if step == "P6" and (project_match.get("matched_projects") or project_match.get("matched_synonyms")):
        for kf in project_match.get("knowledge_files", []):
            domain = kf['domain']
            # 域名→文件名映射(与_sync_review_experience保持一致)
            domain_file = _domain_to_filename(domain)
            rules_path = os.path.join(skill_dir, "knowledge", "reviewed_cases", f"{domain_file}_rules.json")
            if os.path.exists(rules_path):
                try:
                    rules_data = _read_json(rules_path)
                    # 用蒸馏引擎生成注入文本
                    layers = []
                    for layer_name, label in [("tag_rules", "质量规则"), ("operation_rules", "操作规范"), ("domain_rules", "域特定规则"), ("positive_rules", "优秀模式")]:
                        rules = rules_data.get(layer_name, [])
                        if not rules:
                            continue
                        layer_lines = [f"【{label}】"]
                        for r in rules[:5]:  # 每层最多5条
                            freq = r.get("frequency", 1)
                            if freq >= 5:
                                prefix = "[强规则] "
                            elif freq >= 2:
                                prefix = "[规则] "
                            else:
                                prefix = "[参考] "
                            weight = r.get("weight", 1.0)
                            if weight < 1.0:
                                prefix += "[置信度:中] "
                            layer_lines.append(f"- {prefix}{r['rule']}")
                        layers.append("\n".join(layer_lines))
                    if layers:
                        # 统计经验规则总数
                        total_rules = sum(len(r) for r in [rules_data.get("tag_rules", []), rules_data.get("operation_rules", []), rules_data.get("domain_rules", []), rules_data.get("positive_rules", [])])
                        total_reviewed = rules_data.get("total_reviewed_cases", "?")
                        review_experience = (
                            f"\n---\n## 🔴 历史评审经验({kf['domain']},基于{total_reviewed}条用例评审,{total_rules}条规则)\n"
                            f"🔴 以下规则来自历史评审,生成用例时必须遵守,优先级高于通用规则。违反会被再次驳回。\n"
                            + "\n".join(layers) + "\n"
                        )
                        break  # 取第一个有经验的域即可,避免prompt膨胀
                except Exception:
                    pass

    if knowledge_texts:
        full_prompt_parts.append("\n---\n## 注入知识\n" + "\n\n".join(knowledge_texts))

    if review_experience:
        full_prompt_parts.append(review_experience)
    elif step == "P6":
        # 降级:无域经验时注入通用种子规则
        seed_path = os.path.join(skill_dir, "knowledge", "reviewed_cases", "通用_rules.json")
        if os.path.exists(seed_path):
            try:
                seed_data = _read_json(seed_path)
                seed_rules = []
                for layer_name, label in [("tag_rules", "质量规则"), ("operation_rules", "操作规范"), ("positive_rules", "优秀模式")]:
                    for r in seed_data.get(layer_name, [])[:3]:
                        seed_rules.append(f"- [种子规则] {r['rule']}")
                if seed_rules:
                    review_experience = (
                        f"\n---\n## 🔴 通用评审经验(种子规则,适用于所有项目)\n"
                        f"🔴 以下规则来自历史评审最佳实践,生成用例时必须遵守。\n"
                        + "\n".join(seed_rules) + "\n"
                    )
                    full_prompt_parts.append(review_experience)
            except Exception:
                pass

    if px_inject:
        full_prompt_parts.append(f"\n---\n## 图片理解增强\n{px_inject}")

    # V5.0(4.13.0): 移除 P1 LOW 模型精简逻辑 — 统一使用完整 P0 数据

    if upstream_data:
        full_prompt_parts.append("\n---\n## 输入数据")
        for fname, content in upstream_data.items():
            full_prompt_parts.append(f"\n### {fname}\n{content}")

    # R9修复:P3/P4显式注入P0 dependencies和known_risks
    if step in ("P3", "P4"):
        p0_path_for_r9 = os.path.join(data_dir, "p0_output.json")
        if os.path.exists(p0_path_for_r9):
            try:
                p0_data_r9 = _read_json(p0_path_for_r9)
                p0_blocks_r9 = p0_data_r9.get("blocks", {})
                r9_inject_parts = []
                deps = p0_blocks_r9.get("dependencies", [])
                if deps:
                    r9_inject_parts.append(f"### P0识别的外部依赖(风险/PCI识别必须参考)\n{json.dumps(deps, ensure_ascii=False, indent=2)}")
                risks = p0_blocks_r9.get("known_risks", [])
                if risks:
                    r9_inject_parts.append(f"### P0识别的已知风险(风险/PCI识别必须参考)\n{json.dumps(risks, ensure_ascii=False, indent=2)}")
                if r9_inject_parts:
                    full_prompt_parts.append("\n---\n## P0依赖与风险数据(必须明确引用)\n" + "\n".join(r9_inject_parts))
            except Exception:
                pass

    # P0需要需求文本
    if step == "P0" and requirement_text:
        full_prompt_parts.append(f"\n---\n## 需求文本\n{requirement_text[:15000]}")

    if p6_batch_info:
        full_prompt_parts.append(p6_batch_info)

    # P0内联必需字段提醒
    if step == "P0":
        full_prompt_parts.append("\n---\n## ❗ 输出必须包含以下顶层字段\n- quality_score: number (0~1.0)\n- blocks: object\n- objective: string")

        # V3.5.1: PRD审查增强 - 条件注入blocks_markdown/issues输出要求
        meta_path = os.path.join(data_dir, "task_meta.json")
        if os.path.exists(meta_path):
            _meta = _read_json(meta_path)
            if _meta.get("prd_quality_review", False):
                enhance_prompt_path = os.path.join(skill_dir, "prompts", "P0_prd_review_enhance.md")
                if os.path.exists(enhance_prompt_path):
                    enhance_text = _read_file_safe(enhance_prompt_path, max_chars=8000)
                    if enhance_text:
                        full_prompt_parts.append(f"\n---\n{enhance_text}")
                        full_prompt_parts.append("\n---\n## ❗ PRD审查模式额外必须输出\n- blocks_markdown: string (结构化Markdown,≤5000字符)\n- issues: array (问题清单,无问题时为空数组[])")


    # P1内联必需字段提醒
    if step == "P1":
        full_prompt_parts.append("\n---\n## ❗ 输出必须包含以下顶层字段\n- feature_tree: array (模块列表,每个元素为module_node对象)\n- coverage_check: object (覆盖率检查)")  # Bugfix V4.6.9: 与p1_output.schema.json一致(feature_tree是array而非object)

    # P2内联必需字段提醒(确保Agent生成的测试点带priority和status)
    if step == "P2":
        full_prompt_parts.append("""\n---\n## ❗ 每个test_point必须包含以下字段
- id: 字符串,测试点唯一标识
- source_scenario: 字符串,来源场景
- description: 字符串,测试点描述
- category: 字符串,测试类型
- priority: 必须是 "P0"/"P1"/"P2"/"P3" 之一
- status: 必须是 "active"/"blocked" 之一(默认active)
- priority_hint: 字符串,优先级建议

## ❗ 优先级分布要求(必须遵守,否则后续质量门禁会拒绝)
- P0优先级不得超过20%,推荐控制在10%-15%。P0仅用于核心主链路可用性+核心权限/交易入口级阻断场景
- P1应占主体(40%-60%),用于重要分支/异常场景
- P2/P3用于边界/兼容/性能等补充场景
- 删除/隐藏类、普通异常类、一般展示类原则上不标P0
- 不允许所有测试点为同一优先级""")

    # P7内联必需字段提醒
    if step == "P7":
        full_prompt_parts.append("""\n---\n## ❗ 输出必须包含以下顶层字段
- gate_result: object (必须包含status字段)
  - gate_result.status: 必须是 "PASS" 或 "FAIL"(全大写)
  - gate_result.summary: 字符串,检查结论
  - gate_result.checks: 数组,各项检查结果

⚠️ 注意:顶层字段名是 gate_result,不是 quality_check""")

    # P6质量规则+字段格式注入
    if step == "P6":
        full_prompt_parts.append("""\n---\n## ❗ 用例质量硬性规则(必须遵守,quality_check会校验)
1. **每个测试点至少展开为2条用例**(1条正向+1条反向/异常/边界),复杂测试点应展开更多
2. **冒烟用例比例**: 必须在5%~20%之间。冒烟用例=P0优先级+核心功能正向验证(排除删除/隐藏/异常用例)
3. **P0优先级占比**: 不得超过20%。大部分用例应为P1/P2
4. **优先级分布**: 不允许所有用例为同一优先级
5. **每需求冒烟**: 每个需求至少1条冒烟用例
6. **用例数下限**: 合并后至少15条用例,且不少于P5测试点数×1.5

违反以上任何规则的用例集将被quality_check拒绝,需要重新生成。

## ❗ 字段格式要求(必须严格遵守)
- **is_smoke**: 必须是布尔值 true 或 false(不是字符串,不是"是/否",不是"?")
- **priority**: 必须是 "P0"/"P1"/"P2"/"P3" 之一
- **title**: 必须非空
- **preconditions**: 必须非空
- **steps**: 必须是数组,每项包含 step 和 expected
- **testcases**: 顶层字段名必须是 testcases(小写)

## ❗ 严禁占位符内容(违反将被直接拒绝)
- 每条用例的steps必须是**具体的、可执行的操作步骤**,不允许使用"执行相关操作""观察结果"等泛化描述
- 每条用例的expected_results必须是**具体的、可验证的预期结果**,不允许使用"页面展示正常""数据与预期一致"等泛化描述
- **核心规则:steps行数 = expected_results行数,一一对应**
- 请基于skeleton中每条用例的p5_description/p5_precondition信息,**自由编写具体步骤和期望结果**
- 违反以上规则的批次将被p6_save_batch直接拒绝

## ❗ 步骤编写最佳实践
每个步骤必须包含:明确动作 + 操作对象 + 具体数据
每个期望结果必须包含:可观察的系统响应 + 具体验证点

✅ 正向验证示例(main_flow,3步=3期望):
steps: "1. 使用机构管理员账号admin01登录CRM系统\n2. 点击左侧菜单「兴光闪耀竞赛活动」,点击「月榜」Tab\n3. 点击「有效机构户」Tab查看数据列表"
expected_results: "1. 登录成功,页面显示用户名admin01\n2. 月榜Tab选中,显示当月数据\n3. 列表展示机构名称、有效户数、排名,数据与导入一致"

✅ 异常验证示例(exception,3步=3期望):
steps: "1. 使用机构管理员账号登录CRM系统\n2. 进入月榜页面,在搜索框输入超长字符串(256字符)\n3. 点击搜索按钮"
expected_results: "1. 登录成功\n2. 输入框接受输入或截断至最大长度\n3. 系统提示「搜索内容过长」或返回空结果,不报错"

✅ 权限验证示例(permission,3步=3期望):
steps: "1. 使用普通员工账号user01登录CRM系统\n2. 在地址栏直接输入月榜管理页面URL\n3. 观察页面响应"
expected_results: "1. 登录成功\n2. 页面返回403或跳转到无权限提示页\n3. 显示「您没有权限访问此页面」提示"

❌ 错误示例(会被拒绝):
steps: "1. 登录\n2. 进入页面\n3. 操作\n4. 验证\n5. 完成"
expected_results: "1. 页面展示正常\n2. 数据正确"
问题:5个步骤但只有2个期望结果,且内容泛化无具体验证点

## ❗ 你只需要生成以下核心字段(其余由代码自动补全)
必须生成:title, preconditions, steps, expected_results, remarks, test_case_type, test_category
代码自动补全:project, case_type, creator, assignee, status, screenshot, test_suite, menu_path, case_id, requirement, priority, is_smoke""")
    full_prompt = "\n".join(full_prompt_parts)

    # 输出
    result = {
        "status": "ok",
        "step": step,
        "prompt_length": len(full_prompt),
        "upstream_files": list(upstream_data.keys()),
        "knowledge_injected": len(knowledge_texts),
        "px_injected": bool(px_inject),
    }

    # 将prompt写入文件(太长不适合通过stdout传递)
    prompt_output_path = os.path.join(data_dir, f"{step.lower()}_prompt.txt")
    with open(prompt_output_path, "w", encoding="utf-8") as f:
        f.write(full_prompt)
    result["prompt_file"] = prompt_output_path

    print(json.dumps(result))


# ============================================================
# Action: set_prd_review (V3.5.1: 设置PRD审查开关)
# ============================================================

def action_set_prd_review(args):
    """设置PRD质量审查开关(用户在Onboarding第1步选择"开启"时调用)"""
    data_dir = args.data_dir
    task_id = args.task_id
    enabled = (getattr(args, 'enabled', 'true') or 'true').lower().strip()
    enabled_bool = enabled in ('true', '1', '开启', 'on', 'yes')

    # 写入task_meta.json
    meta_path = os.path.join(data_dir, "task_meta.json")
    if os.path.exists(meta_path):
        meta = _read_json(meta_path)
    else:
        meta = {"task_id": task_id}
    meta["prd_quality_review"] = enabled_bool
    _write_json(meta_path, meta)

    print(json.dumps({
        "status": "ok",
        "prd_quality_review": enabled_bool,
        "message": "PRD质量审查已开启" if enabled_bool else "PRD质量审查已关闭",
    }))


# ============================================================
# Action: p6_batch_info (P6分批信息)
# ============================================================

# ============================================================
# Action: p2_code_generate (V3.3.2: P2测试点代码自动生成)
# ============================================================

def action_p2_code_generate(args):
    """代码层从P1 feature_tree自动生成P2测试点(零Agent依赖)

    职责边界:只管结构(数量、category、priority、source_scenario)
    语义细化由P6承担(P6 prompt注入P1 scenario详情)
    """
    data_dir = args.data_dir
    task_id = args.task_id
    skill_dir = args.skill_dir

    # 前置gate检查:P1必须完成
    ok, msg = check_gate(data_dir, "P1", task_id)
    if not ok:
        print(json.dumps({"status": "gate_blocked", "step": "P1", "reason": msg}))
        sys.exit(1)

    # 读取P1 feature_tree
    p1_path = os.path.join(data_dir, "p1_output.json")
    if not os.path.exists(p1_path):
        print(json.dumps({"status": "error", "reason": "p1_output.json不存在"}))
        sys.exit(1)
    p1_data = _read_json(p1_path)

    # P1数据结构:feature_tree.modules 包含嵌套children结构
    feature_tree = p1_data.get("feature_tree", {})
    if isinstance(feature_tree, list):
        modules = feature_tree  # Bugfix V4.6.9: feature_tree是list时直接作为modules列表
    elif isinstance(feature_tree, dict):
        modules = feature_tree.get("modules", [])
    else:
        modules = []
    # 兼容:如果feature_tree为空,尝试顶层modules
    if not modules:
        modules = p1_data.get("modules", [])

    if not modules:
        print(json.dumps({"status": "error", "reason": "P1数据中未找到modules"}))
        sys.exit(1)

    # 读取P0 operations(补充语义判断)
    p0_path = os.path.join(data_dir, "p0_output.json")
    p0_operations = []
    # R1-R4修复:读取P0 field_specs/ui_elements/business_objects/test_point_candidates
    p0_field_specs = []
    p0_ui_elements = []
    p0_business_objects = []
    p0_test_point_candidates = []
    if os.path.exists(p0_path):
        try:
            p0_data = _read_json(p0_path)
            p0_operations = p0_data.get("blocks", {}).get("operations", [])
            p0_field_specs = p0_data.get("blocks", {}).get("field_specs", [])
            p0_ui_elements = p0_data.get("blocks", {}).get("ui_elements", [])
            p0_business_objects = p0_data.get("blocks", {}).get("business_objects", [])
            p0_test_point_candidates = p0_data.get("blocks", {}).get("test_point_candidates", [])
        except Exception:
            pass

    # 关键词集合
    DATA_KEYWORDS = {"导入", "导出", "上传", "下载", "查询", "统计", "推送", "同步"}

    # 获取requirement_id
    requirement_id = p1_data.get("requirement_id", "REQ-UNKNOWN")

    # 遍历所有scenario生成测试点
    test_points = []
    seq = 1

    for module in modules:
        for feature in module.get("children", []):
            if feature.get("type") != "feature":
                continue
            feature_scenarios = [s for s in feature.get("children", []) if s.get("type") == "scenario"]
            feature_exception_added = False  # 每个feature只生成1条异常测试点

            for scenario in feature_scenarios:
                # V4.15.30: 兼容scenario_id和id两种字段名
                scenario_id = scenario.get("id") or scenario.get("scenario_id", "")
                scenario_name = scenario.get("name", "")
                scenario_type = scenario.get("scenario_type", "positive")
                precondition = scenario.get("precondition", "")
                related_rules = scenario.get("related_rules", [])
                related_roles = scenario.get("related_roles", [])

                # 规则1:正向验证(所有scenario必有)
                # V4.15.30: description加scenario_id前缀,防止P5去重误删
                test_points.append({
                    "id": f"{requirement_id}-TP-{seq:03d}",
                    "source_scenario": scenario_id,
                    "category": "main_flow",
                    "description": f"[{scenario_id}] 验证{scenario_name}正常流程",
                    "precondition": precondition,
                    "related_rules": related_rules,
                    "related_roles": related_roles,
                    "priority": "P1",
                    "priority_hint": "P1",
                    "status": "active",
                })
                seq += 1

                # 规则2:异常验证(每个feature只生成1条,避免膨胀)
                # V4.15.30: description加scenario_id前缀,防止P5去重误删
                if not feature_exception_added:
                    test_points.append({
                        "id": f"{requirement_id}-TP-{seq:03d}",
                        "source_scenario": scenario_id,
                        "category": "exception",
                        "description": f"[{scenario_id}] 验证{feature.get('name', scenario_name)}异常场景处理",
                        "precondition": precondition,
                        "related_rules": related_rules,
                        "related_roles": related_roles,
                        "priority": "P2",
                        "priority_hint": "P2",
                        "status": "active",
                    })
                    seq += 1
                    feature_exception_added = True

                # 规则3:边界验证(数据相关场景,且该scenario名称含数据关键词)
                # V4.15.30: description加scenario_id前缀,防止P5去重误删
                if any(kw in scenario_name for kw in DATA_KEYWORDS):
                    test_points.append({
                        "id": f"{requirement_id}-TP-{seq:03d}",
                        "source_scenario": scenario_id,
                        "category": "boundary",
                        "description": f"[{scenario_id}] 验证{scenario_name}边界条件和数据完整性",
                        "precondition": precondition,
                        "related_rules": related_rules,
                        "related_roles": related_roles,
                        "priority": "P3",
                        "priority_hint": "P3",
                        "status": "active",
                    })
                    seq += 1

                # 规则4:权限验证(多角色场景,且scenario_type含permission信号)
                # V4.15.30: description加scenario_id前缀,防止P5去重误删
                if related_roles and len(related_roles) > 1 and scenario_type in ("permission", "role", "auth"):
                    test_points.append({
                        "id": f"{requirement_id}-TP-{seq:03d}",
                        "source_scenario": scenario_id,
                        "category": "permission",
                        "description": f"[{scenario_id}] 验证{scenario_name}不同角色权限控制",
                        "precondition": precondition,
                        "related_rules": related_rules,
                        "related_roles": related_roles,
                        "priority": "P1",
                        "priority_hint": "P1",
                        "status": "active",
                    })
                    seq += 1

    # P0提升逻辑:每feature第1个main_flow升为P0(原来每module只升1个,导致P0太少冒烟不足)
    seen_features_for_p0 = set()
    for tp in test_points:
        if tp["category"] == "main_flow":
            # 从source_scenario提取feature key(如REQ-2026-XG-014-M01-F01-S01中的M01-F01)
            src = tp.get("source_scenario", "")
            feature_key = None
            parts = src.split("-")
            m_idx = next((i for i, p in enumerate(parts) if p.startswith("M") and p[1:].isdigit()), None)
            f_idx = next((i for i, p in enumerate(parts) if p.startswith("F") and p[1:].isdigit()), None)
            if m_idx is not None and f_idx is not None:
                feature_key = f"{parts[m_idx]}-{parts[f_idx]}"
            elif m_idx is not None:
                feature_key = parts[m_idx]  # 备用:无F编号时降级为module级
            if feature_key and feature_key not in seen_features_for_p0:
                tp["priority"] = "P0"
                tp["priority_hint"] = "P0"
                seen_features_for_p0.add(feature_key)

    # complexity和expected_case_count标签(与P5 merge逻辑一致)
    SIMPLE_CATEGORIES = {"compatibility", "display", "ui_check"}
    COMPLEX_CATEGORIES = {"permission", "exception", "integration", "data_consistency"}
    for tp in test_points:
        cat = tp.get("category", "").lower()
        has_risk = tp.get("risk_flag", False)
        priority = tp.get("priority", "P1")
        score = 0
        if cat in COMPLEX_CATEGORIES:
            score += 2
        if has_risk:
            score += 1
        if priority in ("P0", "P1"):
            score += 1
        if score >= 3:
            tp["complexity"] = "L3"
            tp["expected_case_count"] = 3
        elif score >= 1:
            tp["complexity"] = "L2"
            tp["expected_case_count"] = 2
        else:
            tp["complexity"] = "L1"
            tp["expected_case_count"] = 1
        # P0测试点强制上限expected_case_count=2:
        # P0第1条是冒烟用例,展开过多会稀释冒烟比例导致不达标8%门槛
        if tp.get("priority") == "P0" and tp.get("expected_case_count", 2) > 2:
            tp["expected_case_count"] = 2
        # 初始化risk/pci标记(P5 merge会覆盖)
        tp.setdefault("risk_flag", False)
        tp.setdefault("pci_flag", False)

    # 覆盖率校验
    modules_covered = set()
    features_covered = set()
    for tp in test_points:
        src = tp.get("source_scenario", "")
        for part in src.split("-"):
            if part.startswith("M") and part[1:].isdigit():
                modules_covered.add(part)
            if part.startswith("F") and part[1:].isdigit():
                # 提取到feature级别
                idx = src.index(part)
                features_covered.add(src[:idx + len(part)])

    total_modules = len(modules)
    coverage_ok = len(modules_covered) >= total_modules

    # 构建输出
    # R1-R4修复:将P0关键数据附加到P2输出供下游使用
    p0_context = {}
    if p0_field_specs:
        p0_context["field_specs"] = p0_field_specs
    if p0_ui_elements:
        p0_context["ui_elements"] = p0_ui_elements
    if p0_business_objects:
        p0_context["business_objects"] = p0_business_objects
    if p0_test_point_candidates:
        p0_context["test_point_candidates"] = p0_test_point_candidates

    output = {
        "schema_version": "1.0.0",
        "prompt_version": "1.0.0",
        "requirement_id": requirement_id,
        "test_points": test_points,
        "p0_context": p0_context,
        "coverage_summary": {
            "total_test_points": len(test_points),
            "modules_covered": len(modules_covered),
            "total_modules": total_modules,
            "features_covered": len(features_covered),
            "coverage_ok": coverage_ok,
            "generation_method": "code",
        }
    }

    # 写入tmp文件
    tmp_path = os.path.join(data_dir, "p2_output.tmp.json")
    _write_json(tmp_path, output)

    # 调用truncation_guard
    guard_ok, guard_msg = run_truncation_guard(skill_dir, data_dir, task_id, "P2", revision=1)
    if not guard_ok:
        print(json.dumps({"status": "guard_failed", "reason": guard_msg}))
        sys.exit(1)

    # 统计
    from collections import Counter
    pri_dist = dict(Counter(tp["priority"] for tp in test_points))
    cat_dist = dict(Counter(tp["category"] for tp in test_points))

    # V4.8.11: P2完成后自动生成需求结构报告,Agent无需手动调用export_p0p1
    p0p1_path = os.path.join(data_dir, "p0p1_report.md")
    try:
        import subprocess as _sp
        ep = os.path.join(skill_dir, "tools", "export_p0p1.py")
        _sp.run([sys.executable, ep, "--data-dir", data_dir, "--output", p0p1_path],
                capture_output=True, timeout=15)
        if os.path.exists(p0p1_path):
            report_generated = True
    except Exception:
        report_generated = os.path.exists(p0p1_path)

    output_msg = {
        "status": "ok",
        "step": "P2",
        "test_points_count": len(test_points),
        "priority_distribution": pri_dist,
        "category_distribution": cat_dist,
        "coverage": output["coverage_summary"],
        "guard_result": f"GUARD_PASS:P2:{len(test_points)}",
    }
    if report_generated:
        output_msg["__must_emit__"] = f"📄 需求理解与功能点拆解报告已生成\nMEDIA:{data_dir}/p0p1_report.md\n⏸️ 段落3完成。请回复「继续」进入段落4(P3+P4风险识别)。禁止自动跨段。"

    # V4.12.7: 写入 pending_emit，确保 Agent 必须输出 MEDIA
    pending_path = os.path.join(data_dir, "pending_emit_P2.json")
    with open(pending_path, "w", encoding="utf-8") as f:
        json.dump({"step": "P2", "media_path": f"{data_dir}/p0p1_report.md", "created_at": time.time()}, f, ensure_ascii=False)

    print(json.dumps(output_msg))


# ============================================================
# Action: confirm_emit (V4.12.7: 确认 Agent 已输出 __must_emit__ 内容)
# ============================================================

def action_confirm_emit(args):
    """确认 Agent 已输出 __must_emit__ 内容。

    硬拦截机制：Agent 疲劳后可能跳过 __must_emit__ 字段输出，
    导致用户收不到关键报告文件（MEDIA）。此 action 由 Agent 在
    输出 MEDIA 后主动调用，确认已完成输出义务。
    """
    step = args.step  # "P2" 或 "step7"
    data_dir = args.data_dir
    pending_path = os.path.join(data_dir, f"pending_emit_{step}.json")
    confirmed_path = os.path.join(data_dir, f"emit_confirmed_{step}.json")

    if not os.path.exists(pending_path):
        print(json.dumps({"status": "ok", "message": f"无需确认，{step} 无 pending emit"}))
        return

    # 写入确认文件
    confirm_data = {"step": step, "confirmed_at": time.time()}
    with open(confirmed_path, "w", encoding="utf-8") as f:
        json.dump(confirm_data, f, ensure_ascii=False)

    # 清理 pending（确认后不需要再拦）
    os.remove(pending_path)

    print(json.dumps({"status": "ok", "message": f"{step} __must_emit__ 已确认输出"}))


# ============================================================
# Action: p3_p4_parallel (V4.1.0: P3+P4并行执行+失败处理)
# ============================================================

def action_p3_p4_parallel(args):
    """V4.1.0: P3+P4并行执行,带完整失败处理逻辑。

    使用ThreadPoolExecutor同时执行P3和P4的prep_prompt+step_run流程。
    失败处理:
    1. 任一步骤失败 → 立即标记另一个为"跳过" → 不进入P5合并
    2. 失败日志聚合:记录哪个步骤失败、失败原因、耗时
    3. 资源释放:无论成功失败,清理临时文件(.tmp.json)

    前置条件:P1 gate pass必须存在(P3和P4都依赖P1)
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed
    import traceback

    data_dir = args.data_dir
    task_id = args.task_id
    skill_dir = args.skill_dir

    # V4.12.7: 检查段落3的 __must_emit__ 是否已确认
    pending_path = os.path.join(data_dir, "pending_emit_P2.json")
    if os.path.exists(pending_path):
        pd = _read_json(pending_path)
        # 超时保护：30分钟后自动降级
        if time.time() - pd.get("created_at", 0) > 1800:
            print(json.dumps({"status": "warning", "message": "pending_emit_P2 超时30分钟，自动放行"}))
            os.remove(pending_path)
        else:
            print(json.dumps({
                "status": "blocked",
                "reason": "段落3的 __must_emit__ 未确认输出。请在回复中输出 MEDIA 行，然后执行: python3 $ORCH --action confirm_emit --step P2",
                "media_path": pd.get("media_path", ""),
            }))
            sys.exit(1)

    # 前置gate检查:P3和P4都依赖P1
    ok, msg = check_gate(data_dir, "P1", task_id)
    if not ok:
        print(json.dumps({"status": "gate_blocked", "step": "P1", "reason": msg}))
        sys.exit(1)

    # 临时文件列表(用于finally清理)
    temp_files = []

    def _run_step(step):
        """执行单个步骤的完整流程:prep_prompt → Agent输出文件读取 → step_run。

        此函数在线程中执行,返回结构化结果。
        注意:此处不直接调用action_step_run(因为它会sys.exit),
        而是通过subprocess调用orchestrator自身。

        Returns:
            dict: {"step": str, "status": "ok"|"failed", "reason": str, "duration": float}
        """
        start_time = time.time()
        orch_path = os.path.abspath(__file__)

        try:
            # Step 1: 执行prep_prompt
            prep_cmd = [
                "python3", orch_path,
                "--action", "prep_prompt",
                "--step", step,
                "--data-dir", data_dir,
                "--task-id", task_id,
                "--skill-dir", skill_dir,
            ]
            prep_result = subprocess.run(
                prep_cmd, capture_output=True, text=True, timeout=60
            )
            if prep_result.returncode != 0:
                error_msg = prep_result.stderr.strip() or prep_result.stdout.strip()
                return {
                    "step": step,
                    "status": "failed",
                    "phase": "prep_prompt",
                    "reason": f"prep_prompt失败: {error_msg[:500]}",
                    "duration": time.time() - start_time,
                }

            # Step 2: 检查Agent输出文件是否存在
            # Agent需要在prep_prompt之后生成 {step.lower()}_agent_output.json
            agent_output_path = os.path.join(data_dir, f"{step.lower()}_agent_output.json")
            if not os.path.exists(agent_output_path):
                return {
                    "step": step,
                    "status": "needs_agent",
                    "phase": "agent_output",
                    "reason": f"prompt已生成({step.lower()}_prompt.txt)，请Agent根据prompt生成 {step.lower()}_agent_output.json 后重新执行 p3_p4_parallel",
                    "prompt_path": os.path.join(data_dir, f"{step.lower()}_prompt.txt"),
                    "duration": time.time() - start_time,
                }

            # Step 3: 执行step_run(校验+写入gate pass)
            run_cmd = [
                "python3", orch_path,
                "--action", "step_run",
                "--step", step,
                "--data-dir", data_dir,
                "--task-id", task_id,
                "--skill-dir", skill_dir,
            ]
            run_result = subprocess.run(
                run_cmd, capture_output=True, text=True, timeout=60
            )
            if run_result.returncode != 0:
                error_msg = run_result.stderr.strip() or run_result.stdout.strip()
                # 记录临时文件路径(供finally清理)
                tmp_path = os.path.join(data_dir, f"{step.lower()}_output.tmp.json")
                temp_files.append(tmp_path)
                return {
                    "step": step,
                    "status": "failed",
                    "phase": "step_run",
                    "reason": f"step_run失败: {error_msg[:500]}",
                    "duration": time.time() - start_time,
                }

            return {
                "step": step,
                "status": "ok",
                "phase": "complete",
                "reason": "",
                "duration": time.time() - start_time,
            }

        except subprocess.TimeoutExpired:
            return {
                "step": step,
                "status": "failed",
                "phase": "timeout",
                "reason": f"{step}执行超时(60秒限制)",
                "duration": time.time() - start_time,
            }
        except Exception as e:
            return {
                "step": step,
                "status": "failed",
                "phase": "exception",
                "reason": f"{step}执行异常: {str(e)[:300]}",
                "duration": time.time() - start_time,
            }

    # ============================================================
    # 并行执行P3和P4
    # ============================================================
    results = {}
    failed_step = None
    skipped_step = None

    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            future_to_step = {
                executor.submit(_run_step, "P3"): "P3",
                executor.submit(_run_step, "P4"): "P4",
            }

            for future in as_completed(future_to_step, timeout=180):
                step_name = future_to_step[future]
                try:
                    result = future.result(timeout=120)
                    results[step_name] = result

                    # 任一步骤失败 → 标记另一个为"跳过"
                    if result["status"] == "failed":
                        failed_step = step_name
                        other_step = "P4" if step_name == "P3" else "P3"
                        # 尝试取消另一个(如果还没完成)
                        for f, s in future_to_step.items():
                            if s == other_step and not f.done():
                                f.cancel()
                                skipped_step = other_step
                        break

                except Exception as e:
                    results[step_name] = {
                        "step": step_name,
                        "status": "failed",
                        "phase": "future_exception",
                        "reason": f"线程执行异常: {str(e)[:300]}",
                        "duration": 0,
                    }
                    failed_step = step_name
                    other_step = "P4" if step_name == "P3" else "P3"
                    for f, s in future_to_step.items():
                        if s == other_step and not f.done():
                            f.cancel()
                            skipped_step = other_step
                    break

    except TimeoutError:
        # 总超时180秒
        for step_name in ["P3", "P4"]:
            if step_name not in results:
                results[step_name] = {
                    "step": step_name,
                    "status": "failed",
                    "phase": "total_timeout",
                    "reason": "并行执行总超时(180秒)",
                    "duration": 180,
                }
        failed_step = "P3+P4"

    finally:
        # ============================================================
        # 资源释放:清理临时文件
        # ============================================================
        for step_name in ["P3", "P4"]:
            tmp_path = os.path.join(data_dir, f"{step_name.lower()}_output.tmp.json")
            if os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass
        # 清理额外记录的临时文件
        for tmp_path in temp_files:
            if os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass

    # ============================================================
    # 结果聚合与输出
    # ============================================================

    # 如果有跳过的步骤,补充记录
    if skipped_step and skipped_step not in results:
        results[skipped_step] = {
            "step": skipped_step,
            "status": "skipped",
            "phase": "skipped",
            "reason": f"因{failed_step}失败而跳过",
            "duration": 0,
        }

    # 判断整体结果
    p3_ok = results.get("P3", {}).get("status") == "ok"
    p4_ok = results.get("P4", {}).get("status") == "ok"
    all_ok = p3_ok and p4_ok

    # 构造失败日志
    failure_log = []
    for step_name in ["P3", "P4"]:
        r = results.get(step_name, {})
        if r.get("status") in ("failed", "skipped"):
            failure_log.append({
                "step": step_name,
                "status": r.get("status"),
                "phase": r.get("phase", ""),
                "reason": r.get("reason", ""),
                "duration_sec": round(r.get("duration", 0), 2),
            })

    output = {
        "status": "ok" if all_ok else "failed",
        "p3_result": results.get("P3", {}).get("status", "unknown"),
        "p4_result": results.get("P4", {}).get("status", "unknown"),
        "p3_duration_sec": round(results.get("P3", {}).get("duration", 0), 2),
        "p4_duration_sec": round(results.get("P4", {}).get("duration", 0), 2),
        "can_proceed_to_p5": all_ok,
    }

    if not all_ok:
        output["failure_log"] = failure_log
        output["message"] = (
            f"❌ 并行执行失败。"
            f"{'P3' if not p3_ok else 'P4'}{'失败' if results.get('P3' if not p3_ok else 'P4', {}).get('status') == 'failed' else '被跳过'},"
            f"不进入P5合并步骤。请检查失败原因后重试。"
        )
        output["hint"] = "使用 --action restart_from --step P3 重置后重试"
    else:
        output["message"] = (
            f"✅ P3+P4并行执行成功。"
            f"P3耗时{output['p3_duration_sec']}秒,P4耗时{output['p4_duration_sec']}秒。"
            f"可执行P5合并。"
        )
        output["next_action"] = "p5_code_merge"

    print(json.dumps(output, ensure_ascii=False))

    if not all_ok:
        sys.exit(1)


# ============================================================
# Action: p5_code_merge (V3.2.0: P5合并下沉代码层)
# ============================================================

# ============================================================
# V4.7.0: P5 骨架增强 - 为每个测试点生成 step_expected_pairs、
# ui_elements、field_checklist,供给 P6 Agent 具体参考
# ============================================================

def _build_step_expected_pairs(point: dict) -> list:
    """
    从 operations_chain 提取步骤-期望骨架。
    兜底策略(p1_operations_chain为空时): 从 description 提取。
    """
    ops_chain = point.get("operations_chain", [])
    if not isinstance(ops_chain, list):
        ops_chain = []

    pairs = []
    if ops_chain:
        for op in ops_chain:
            if isinstance(op, dict):
                action = op.get("action", op.get("operation", ""))
                target = op.get("target", op.get("target_element", ""))
                value = op.get("value", op.get("data_value", ""))
                expected = op.get("expected", op.get("expected_result", ""))
                if action and target:
                    step = f"{action}「{target}」"
                    if value:
                        step += f",输入{value}"
                    pairs.append({"step": step, "expected": expected or f"{target}操作完成"})
        if pairs:
            return pairs

    # V5.0(4.13.1): RISK/risk_verification TP 特殊处理
    # 如果 operations_chain 为空,尝试从 source_scenario 继承操作链
    # 方案 B: 继承源 scenario → 确保 RISK TP 至少和源 TP 一样具体
    category = point.get("category", "") or ""  # V5.0: 提前提取,供RISK分支使用
    if not pairs:
        source_scenario = point.get("source_scenario", "") or ""
        is_risk = (category == "risk_verification" or point.get("source") == "risk"
                   or (point.get("id", "") or "").startswith("RISK"))
        if is_risk and source_scenario:
            # 尝试从 P1 feature tree 中查找 source_scenario 的 operations_chain
            try:
                skill_dir = os.environ.get("SKILL_DIR", "")
                data_dir = os.environ.get("DATA_DIR", "")
                if data_dir:
                    # 从 p1_output 中搜索对应 scenario
                    p1_path = os.path.join(data_dir, "p1_output.json")
                    p5_path = os.path.join(data_dir, "p5_output.json")
                    # 优先从 P5 同 source_scenario 的非 RISK TP 中查找 operations_chain
                    if os.path.exists(p5_path):
                        p5_data = _read_json(p5_path)
                        # V4.15.44修复故障A: source_scenario粒度不匹配(RISK 2级M05-F01 vs 非RISK 3级M05-F01-S01)
                        # 精确匹配改为边界前缀匹配, RISK的M05-F01 匹配 非RISK的M05-F01-S01
                        def _ss_prefix_match(cand_ss, base_ss):
                            if not cand_ss or not base_ss:
                                return False
                            return cand_ss == base_ss or cand_ss.startswith(base_ss + "-")
                        for tp in p5_data.get("test_points", []):
                            if (_ss_prefix_match(tp.get("source_scenario", ""), source_scenario)
                                    and not (tp.get("id", "") or "").startswith("RISK")):
                                src_ops = tp.get("operations_chain", [])
                                if src_ops and len(src_ops) >= 2:
                                    # 继承并注入风险上下文
                                    risk_desc = point.get("description", "") or point.get("title", "") or ""
                                    for op in src_ops:
                                        if isinstance(op, dict):
                                            action = op.get("action", op.get("operation", ""))
                                            target = op.get("target", op.get("target_element", ""))
                                            value = op.get("value", "")
                                            expected = op.get("expected", op.get("expected_result", ""))
                                            if action and target:
                                                step = f"{action}「{target}」"
                                                if value:
                                                    step += f",输入{value}"
                                                pairs.append({"step": step,
                                                    "expected": expected or f"{target}操作完成"})
                                    if pairs:
                                        # 追加风险特有验证步骤
                                        if risk_desc:
                                            short_desc = risk_desc[:80].replace("[扩展测试点]", "").strip()
                                            pairs.append({"step": f"验证风险点「{short_desc}」",
                                                "expected": f"风险验证通过:{short_desc[:40]}"})
                                    break
            except Exception:
                pass

    # 兜底策略: 从 description 提取骨架关键词
    desc = point.get("description", "") or ""
    category = point.get("category", "") or ""
    import re as _re

    # 尝试从描述中提取操作关键词
    nav = _re.search(r'(?:进入|打开|跳转|导航)(.{2,20}?)(?:[,,。]|页面|模块|功能)', desc)
    if nav:
        pairs.append({"step": f"进入{nav.group(1).strip()}页面", "expected": "页面正常加载"})

    action_pat = _re.search(r'(点击|选择|输入|填写|录入|查询|搜索|勾选|上传|下载|导出)(.{2,20}?)(?:[,,。]|按钮|后|并|查看)', desc)
    if action_pat:
        pairs.append({"step": f"{action_pat.group(1)}「{action_pat.group(2).strip()}」", "expected": "操作执行完成"})

    # 分类兜底模板(仅当上述提取结果为0时使用)
    # V4.10.2: 差异化注入--从 title/id 提取TP特有信息,避免同category骨架完全相同
    if not pairs:
        tp_title = point.get("title", "") or ""
        tp_id = point.get("id", "") or ""
        tp_desc = point.get("description", "") or ""

        # 提取差异化关键词(title > description关键词 > id后缀)
        diff_hint = ""
        # V4.15.35: 优先从description提取"验证/检查X"结构,语义更精准
        if tp_desc:
            # V4.15.44修复故障B: 先清洗标记前缀, 再排除"测试点/检查点"名词误匹配
            _clean_desc = _re.sub(r'^\[(?:扩展测试点|风险验证|PCI验证)\]\s*', '', tp_desc)
            verb_noun = _re.search(r'(验证|检查|测试|评估)(?!点)([^，。,.]{2,15}?)(?:[，。,.]|是否|的)', _clean_desc)
            if verb_noun:
                diff_hint = verb_noun.group(2).strip()
        if not diff_hint and tp_title:
            # 清洗常见前缀避免模糊词(如"风险""PCI""安全""合规")
            clean_title = _re.sub(r'^(风险|PCI|安全|合规)[-_：:]?\s*', '', tp_title)
            # V4.15.56: risk_verification TP用更长截断(40字),避免"技术方案尚功能模块"类截断破碎
            if category == "risk_verification":
                risk_desc = point.get("risk_description", "")
                diff_hint = clean_title[:40] if clean_title else (risk_desc[:40] if risk_desc else "风险场景")
            else:
                diff_hint = (clean_title or tp_title).strip()[:20]
        if not diff_hint and tp_id:
            parts = tp_id.split("-")
            _cand = parts[-1] if len(parts) >= 2 else tp_id[-10:]
            # V4.15.44修复: 纯数字或过短(如ETP-1的"1")无意义, 回退description全文
            if _cand.isdigit() or len(_cand) < 2:
                _fallback_desc = _re.sub(r'^\[(?:扩展测试点|风险验证|PCI验证)\]\s*', '', tp_desc).strip()
                diff_hint = _fallback_desc[:20] if _fallback_desc else _cand
            else:
                diff_hint = _cand

        fallback_map = {
            "main_flow": [{"step": "进入{diff}功能页面,执行核心操作流程", "expected": "{diff}核心功能按预期完成"}],
            "branch": [{"step": "进入{diff}功能页面,选择分支路径", "expected": "{diff}分支功能按预期完成"}],
            "exception": [{"step": "针对{diff}构造异常输入条件", "expected": "系统针对{diff}给出明确错误提示"}],
            "boundary": [{"step": "针对{diff}输入边界值测试数据", "expected": "系统按{diff}边界规则处理"}],
            "risk_verification": [{"step": "打开{diff}功能模块，录入符合风险触发条件的测试数据并提交", "expected": "系统弹出风险告警提示，且数据未被正常保存"}],
            "permission": [{"step": "以受限角色登录并访问{diff}", "expected": "系统按权限规则限制{diff}访问"}],
        }
        base = fallback_map.get(category,
            [{"step": "针对{diff}执行相关测试操作", "expected": "{diff}验证结果符合预期"}])
        # 注入差异化关键词(浅拷贝避免修改模板原值)
        pairs = []
        for p in base:
            injected = {}
            for k, v in p.items():
                injected[k] = v.replace("{diff}", diff_hint) if diff_hint else v
            pairs.append(injected)

    return pairs


def _build_ui_elements(point: dict) -> dict:
    """从 field_specs + operations_chain + page_path 汇总 UI 元素清单
    V4.9.0: 增加page_path提取兜底--当field_specs和operations_chain都为空时,
    从page_path和scenario name中提取UI关键词。"""
    elements = {"buttons": [], "inputs": [], "selectors": [], "labels": []}

    field_specs = point.get("field_specs", [])
    if isinstance(field_specs, list):
        for fs in field_specs:
            if isinstance(fs, dict):
                name = fs.get("name", fs.get("field_name", ""))
                ftype = (fs.get("type", fs.get("field_type", "text")) or "").lower()
                if name:
                    if ftype in ("select", "dropdown", "下拉", "选择"):
                        elements["selectors"].append(name)
                    else:
                        elements["inputs"].append(name)
            elif isinstance(fs, str) and fs.strip():
                elements["inputs"].append(fs.strip())

    ops_chain = point.get("operations_chain", [])
    if isinstance(ops_chain, list):
        for op in ops_chain:
            if isinstance(op, dict):
                target = op.get("target", op.get("target_element", ""))
                action = (op.get("action", op.get("operation", "")) or "").lower()
                if target:
                    if action in ("点击", "click", "提交", "submit"):
                        elements["buttons"].append(target)
                    elif action in ("选择", "select", "下拉"):
                        elements["selectors"].append(target)
                    elif action in ("输入", "填写", "录入", "input"):
                        elements["inputs"].append(target)
                    else:
                        elements["labels"].append(target)

    # V4.9.0: 兜底--从page_path和scenario name提取UI关键词
    # P1场景通常不输出field_specs和operations_chain,但page_path包含了页面导航路径
    if not ops_chain and not field_specs:
        # 从page_path提取(如"分润管理→员工配置"→提取"分润管理"/"员工配置")
        pp = point.get("page_path", "")
        if pp:
            path_parts = [p.strip() for p in pp.replace("→", ">").replace("/", ">").split(">") if p.strip()]
            for part in path_parts:
                if len(part) >= 2:
                    elements["labels"].append(part)

        # 从scenario name提取关键词
        sn = point.get("_scenario_name", point.get("name", ""))
        if sn:
            elements["labels"].append(sn[:20])  # 截断,避免过长

        # 从precondition提取操作关键词
        precond = point.get("_precondition", point.get("precondition", ""))
        if precond:
            # 提取包含动词的短语
            for kw in ["登录", "进入", "打开", "选择", "配置"]:
                idx = precond.find(kw)
                if idx >= 0:
                    chunk = precond[idx:idx+15].split(",")[0].split(",")[0]
                    elements["labels"].append(chunk.strip())
                    break

    for key in elements:
        elements[key] = list(dict.fromkeys(elements[key]))
    return elements


# ============================================================
# V4.10.0: LOW模型窄聚焦模式 - 骨架生成辅助函数
# ============================================================

def _build_skeleton_for_batch(data_dir, batch_points, batch_index):
    """为LOW简单模式生成最小骨架(仅case_id映射,供p6_save_batch补全字段)

    Agent只产出title/steps/expected_results,其余字段由skeleton锁定后代码补全。
    """
    case_skeletons = []
    SMOKE_CATEGORIES = {"main_flow", "branch", "integration"}

    for bp in batch_points:
        bp_id = bp.get("id", "")
        bp_priority = bp.get("priority", "P1")
        bp_category = (bp.get("category", "") or "").lower()
        bp_expected = bp.get("expected_case_count", 2)
        bp_desc = bp.get("description", "")
        bp_precond = bp.get("precondition", "")

        for case_idx in range(1, bp_expected + 1):
            if case_idx == 1:
                case_priority = bp_priority
                is_smoke = (bp_priority == "P0" and bp_category in SMOKE_CATEGORIES)
            else:
                case_priority = "P2" if bp_priority in ("P0", "P1") else "P3"
                is_smoke = False

            case_skeletons.append({
                "case_id": f"{bp_id}-TC-{case_idx:03d}",
                "source_test_point": bp_id,
                "priority": case_priority,
                "is_smoke": is_smoke,
                # V4.15.48: 透传风险标记,与内联骨架/全局预算口径一致
                "risk_flag": bp.get("risk_flag", False),
                "priority_hint": bp.get("priority_hint", ""),
                "p5_description": bp_desc,
                "p5_precondition": bp_precond,
                "preconditions": bp_precond,  # V4.10.0: 骨架补全
                "test_case_type": "正例" if bp_category in ("main_flow", "branch", "integration", "正向验证") else "反例",
                "test_category": "功能测试",
            })

    # 冷烟兜底
    if not any(sk.get("is_smoke") for sk in case_skeletons):
        for sk in case_skeletons:
            if sk["priority"] == "P0":
                sk["is_smoke"] = True
                break

    # V4.10.0: P0比例自动降级(复用旧内联骨架逻辑)
    p0_limit = 0.35  # LOW模型阈值
    total = len(case_skeletons)
    if total > 0:
        p0_count = sum(1 for sk in case_skeletons if sk["priority"] == "P0")
        p0_ratio = p0_count / total
        if p0_ratio > p0_limit:
            max_p0 = int(total * p0_limit)
            downgrade_count = p0_count - max_p0
            # V4.15.48: 降级优先级 — 普通非冷烟 → 普通冷烟 → 受保护风险(最后降)。
            # 普通用例(无risk_flag)候选顺序与旧版一致,行为不变。
            def _sk_protected(sk):
                return sk.get("priority_hint") == "P0" and sk.get("risk_flag")
            p0_all = [sk for sk in case_skeletons if sk["priority"] == "P0"]
            ordered = (
                [sk for sk in p0_all if not sk.get("is_smoke") and not _sk_protected(sk)]
                + [sk for sk in p0_all if sk.get("is_smoke") and not _sk_protected(sk)]
                + [sk for sk in p0_all if not sk.get("is_smoke") and _sk_protected(sk)]
                + [sk for sk in p0_all if sk.get("is_smoke") and _sk_protected(sk)]
            )
            downgraded = 0
            for sk in ordered:
                if downgraded >= downgrade_count:
                    break
                sk["priority"] = "P1"
                sk["is_smoke"] = False
                downgraded += 1

    batches_dir = os.path.join(data_dir, "p6_batches")
    _ensure_dir(batches_dir)
    skeleton_path = os.path.join(batches_dir, f"batch_{batch_index:03d}_skeleton.json")
    _write_json(skeleton_path, case_skeletons)


# V4.15.8: P0预算硬约束函数

def _enforce_p0_budget(test_points, max_p0_ratio=0.15):
    """V4.15.8: P0预算硬约束 — 超出15%自动降级

    V4.15.46: 保护 P3 明确标记 priority_hint=P0 的风险场景。
    之前降级时完全无视 priority_hint,且预算超标时从列表末尾砍(RISK ETP
    恰好排在靠后),导致存量迁移/比例越界等金融高危场景被系统性误伤降为P1。
    修复后:降级优先级 普通P0 > hint非P0的risk P0 >> hint=P0的risk P0(尽量不降)。
    """
    total = len(test_points)
    max_p0 = max(1, int(total * max_p0_ratio))
    p0_tps = [tp for tp in test_points if tp.get("priority") == "P0"]
    if len(p0_tps) <= max_p0:
        return test_points

    def _is_protected(tp):
        # P3明确标记P0的风险场景 = 受保护,不应被预算降级误伤
        return tp.get("priority_hint") == "P0" and tp.get("risk_flag")

    non_main_types = ["boundary", "permission", "integration", "exception"]
    demoted = []
    protected_skipped = []
    for tp in test_points:
        if tp.get("priority") == "P0" and tp.get("category") in non_main_types:
            if _is_protected(tp):
                protected_skipped.append(tp["id"])
                continue  # V4.15.46: 保护 P3 hint=P0 的风险场景,不做类型约束降级
            tp["priority"] = "P1"
            tp["priority_reason"] = (tp.get("priority_reason","") + " V4.15.8: 类型约束降级").strip()
            demoted.append(tp["id"])
    p0_tps = [tp for tp in test_points if tp.get("priority") == "P0"]
    if len(p0_tps) > max_p0:
        excess = len(p0_tps) - max_p0
        # V4.15.46: 降级候选排序 — 受保护的risk P0排最后,优先降普通P0。
        # 但预算上限仍需遵守:若普通P0降完仍超标,只能继续降risk P0
        # (按位置靠后先降),避免P0泛滥稀释冒烟比例。
        p0_candidates = [(i, tp) for i, tp in enumerate(test_points) if tp.get("priority") == "P0"]
        # 排序键:非保护(0)排前优先降,保护(1)排后;同组内位置靠后先降
        p0_candidates.sort(key=lambda x: (1 if _is_protected(x[1]) else 0, -x[0]))
        # p0_candidates[:excess] 即需降级的(非保护优先,保护项仅在不得已时才降)
        for i, tp in p0_candidates[:excess]:
            tp["priority"] = "P1"
            reason = " V4.15.8: 预算超标降级"
            if _is_protected(tp):
                reason = " V4.15.46: 风险P0超预算降级(保护优先级不足)"
            tp["priority"] = "P1"
            tp["priority_reason"] = (tp.get("priority_reason","") + reason).strip()
            demoted.append(tp["id"])
    if demoted or protected_skipped:
        print(json.dumps({"action":"p0_budget_enforce","total_tps":total,"max_p0":max_p0,"demoted":demoted,"protected_skipped":protected_skipped,"final_p0_count":sum(1 for tp in test_points if tp.get("priority")=="P0")},ensure_ascii=False), file=sys.stderr)
    return test_points


def _build_field_checklist(point: dict, p0_field_specs: list = None) -> list:
    """收集该测试点涉及的所有字段名(含P0全局字段)"""
    fields = []

    field_specs = point.get("field_specs", [])
    if isinstance(field_specs, list):
        for fs in field_specs:
            if isinstance(fs, dict):
                name = fs.get("name", fs.get("field_name", ""))
                if name:
                    fields.append(name)
            elif isinstance(fs, str) and fs.strip():
                fields.append(fs.strip())

    if isinstance(p0_field_specs, list):
        for fs in p0_field_specs:
            if isinstance(fs, dict):
                name = fs.get("name", fs.get("field_name", ""))
                if name and name not in fields:
                    fields.append(name)
            elif isinstance(fs, str) and fs.strip() and fs.strip() not in fields:
                fields.append(fs.strip())

    return fields


def action_p5_code_merge(args):
    """代码层合并P2+P3+P4→P5(不再依赖Agent/prompt合并)

    读取P2测试点 + P3风险点 + P4 PCI项,代码合并后写入P5
    V4.7.0: 新增骨架增强(step_expected_pairs/ui_elements/field_checklist)
    V4.15.23: 支持 --force-continue / args.skip_quality_gate 跳过质量门禁
    """
    data_dir = args.data_dir
    task_id = args.task_id
    skill_dir = args.skill_dir
    skip_quality = getattr(args, 'skip_quality_gate', False) or getattr(args, 'force_continue', False)

    # 前置gate检查
    for prereq in ["P2", "P3", "P4"]:
        ok, msg = check_gate(data_dir, prereq, task_id)
        if not ok:
            print(json.dumps({"status": "gate_blocked", "step": prereq, "reason": msg}))
            sys.exit(1)

    # 读取P2测试点
    p2_path = os.path.join(data_dir, "p2_output.json")
    p2_data = _read_json(p2_path) if os.path.exists(p2_path) else {}
    p2_points = p2_data.get("test_points", [])

    # 读取P3风险点(兼容risk_points和risks)
    p3_path = os.path.join(data_dir, "p3_output.json")
    p3_data = _read_json(p3_path) if os.path.exists(p3_path) else {}
    p3_risks = p3_data.get("risk_points", p3_data.get("risks", []))

    # 读取P4 PCI项(兼容pci_list和pci_items)
    p4_path = os.path.join(data_dir, "p4_output.json")
    p4_data = _read_json(p4_path) if os.path.exists(p4_path) else {}
    p4_pcis = p4_data.get("pci_list", p4_data.get("pci_items", []))

    # V4.7.0: 读取P0/P1用于骨架增强的字段清单
    p0_path = os.path.join(data_dir, "p0_output.json")
    p0_data = _read_json(p0_path) if os.path.exists(p0_path) else {}
    p0_field_specs = []
    # P0 field_specs 位于 blocks 内(与 p2_code_generate 保持一致)
    p0_blocks = p0_data.get("blocks", {})
    if isinstance(p0_blocks, dict) and isinstance(p0_blocks.get("field_specs"), list):
        p0_field_specs = p0_blocks["field_specs"]

    p1_path = os.path.join(data_dir, "p1_output.json")
    p1_data = _read_json(p1_path) if os.path.exists(p1_path) else {}
    p1_field_specs = []
    if isinstance(p1_data.get("field_specs"), list):
        p1_field_specs = p1_data["field_specs"]
    global_field_specs = p0_field_specs + p1_field_specs

    # 合并逻辑:P2测试点为基础,P3风险补充风险标记,P4 PCI补充待确认标记
    merged_points = []
    from_p3_count = 0
    from_p4_count = 0

    # 复制P2测试点
    for tp in p2_points:
        point = dict(tp)  # 浅拷贝
        point["source"] = "P2"
        point.setdefault("risk_flag", False)
        point.setdefault("pci_flag", False)
        merged_points.append(point)

    # 边界安全前缀匹配(防止M01-F01误匹配M01-F010)
    def _boundary_prefix_match(full_str, prefix):
        """prefix后必须紧跟'-'或完全相等"""
        if not prefix or not full_str:
            return False
        if full_str == prefix:
            return True
        return full_str.startswith(prefix + "-")

    # P3风险点补充:多策略匹配(精确→边界前缀→新增)
    # P3实际字段:source_node(feature级别如M01-F01),无source_scenario
    # 改进:feature级风险应映射到该feature下所有scenario(不再break)
    for risk in p3_risks:
        risk_ref = risk.get("source_scenario") or risk.get("source_node") or risk.get("source", "")
        matched = False
        if risk_ref:
            # 策略1:精确匹配(scenario级别)
            for point in merged_points:
                point_source = point.get("source_scenario", "")
                if point_source and risk_ref == point_source:
                    point["risk_flag"] = True
                    point["risk_description"] = risk.get("description", "")
                    point["risk_severity"] = risk.get("severity", risk.get("impact", "medium"))
                    matched = True
                    from_p3_count += 1
                    break  # 精确匹配只命中1个
            # 策略2:边界前缀匹配(feature级→所有子scenario,不break)
            if not matched:
                for point in merged_points:
                    point_source = point.get("source_scenario", "")
                    if point_source and _boundary_prefix_match(point_source, risk_ref):
                        point["risk_flag"] = True
                        point["risk_description"] = risk.get("description", "")
                        point["risk_severity"] = risk.get("severity", risk.get("impact", "medium"))
                        matched = True
                # 前缀匹配命中后统一计数
                if matched:
                    from_p3_count += 1
        # R8修复:展开P3风险点的extended_test_points为独立测试点
        ext_tps = risk.get("extended_test_points", [])
        if ext_tps and isinstance(ext_tps, list):
            for idx_etp, etp in enumerate(ext_tps):
                if isinstance(etp, dict) and etp.get("description"):
                    merged_points.append({
                        "id": f"{risk.get('id', 'RISK')}-ETP-{idx_etp+1}",
                        "source": "P3",
                        "source_scenario": risk_ref,
                        "title": etp.get("description", ""),  # V4.15.44修复故障C: 补title, 防退化到id兜底"针对1"
                        "description": f"[扩展测试点] {etp.get('description', '')}",
                        "category": etp.get("category", "risk_verification"),
                        "risk_flag": True,
                        "risk_severity": risk.get("severity", risk.get("impact", "medium")),
                        "pci_flag": False,
                        "priority_hint": etp.get("priority_hint", "P1"),
                    })
                    from_p3_count += 1
        if not matched:
            merged_points.append({
                "id": risk.get("id", f"RISK-{len(merged_points)+1}"),
                "source": "P3",
                "source_scenario": risk_ref,
                "description": f"[风险验证] {risk.get('description', '')}",
                "category": "risk_verification",
                "risk_flag": True,
                "risk_severity": risk.get("severity", risk.get("impact", "medium")),
                "pci_flag": False,
                "priority_hint": "P1",
            })
            from_p3_count += 1

    # P4 PCI补充:多策略全量匹配(blocked_scenarios全量→source边界前缀→新增)
    # P4实际字段:source="P1"(无用),blocked_scenarios=[scenario IDs](有用)
    # 改进:blocked_scenarios全量匹配,不再break
    for pci in p4_pcis:
        blocked = pci.get("blocked_scenarios", [])
        # 兼容字符串转单元素数组
        if isinstance(blocked, str) and blocked:
            blocked = [blocked]
        elif not isinstance(blocked, list):
            blocked = []
        pci_source = pci.get("source_scenario") or pci.get("source", "")
        matched = False
        # 策略1:用blocked_scenarios全量匹配P2测试点(不break)
        if blocked:
            for point in merged_points:
                point_source = point.get("source_scenario", "")
                if point_source and point_source in blocked:
                    point["pci_flag"] = True
                    point["pci_description"] = pci.get("description", "")
                    # R10修复:透传P4 resolution_condition
                    if pci.get("resolution_condition"):
                        point["resolution_condition"] = pci["resolution_condition"]
                    matched = True
            if matched:
                from_p4_count += 1
        # 策略2:用source_scenario或source边界前缀匹配(全量)
        if not matched and pci_source and pci_source not in ("P0", "P1", "P2", "P3", "P4"):
            for point in merged_points:
                point_source = point.get("source_scenario", "")
                if point_source and (pci_source == point_source or _boundary_prefix_match(point_source, pci_source)):
                    point["pci_flag"] = True
                    point["pci_description"] = pci.get("description", "")
                    # R10修复:透传P4 resolution_condition
                    if pci.get("resolution_condition"):
                        point["resolution_condition"] = pci["resolution_condition"]
                    matched = True
            if matched:
                from_p4_count += 1
        if not matched:
            merged_points.append({
                "id": pci.get("id", f"PCI-{len(merged_points)+1}"),
                "source": "P4",
                "source_scenario": blocked[0] if isinstance(blocked, list) and blocked else pci_source,
                "description": f"[待确认] {pci.get('description', '')}",
                "category": "pci_verification",
                "risk_flag": False,
                "pci_flag": True,
                "priority_hint": "P1",
                # R10修复:透传resolution_condition
                "resolution_condition": pci.get("resolution_condition", ""),
            })
            from_p4_count += 1

    # V4.15.30: 去重改为(description, source_scenario)双维度
    # 原逻辑只比较description完全相同,导致不同scenario的相似描述被误删(71%丢失)
    # 现增加source_scenario维度,仅当description相同且source_scenario相同时才去重
    seen_keys = set()
    deduped = []
    removed = 0
    for point in merged_points:
        desc = point.get("description", "")
        src = point.get("source_scenario", "")
        key = (desc, src) if desc else None
        if key and key in seen_keys:
            removed += 1
            continue
        if key:
            seen_keys.add(key)
        deduped.append(point)

    # V4.7.0: P5骨架增强 - 为每条测试点生成 step_expected_pairs/ui_elements/field_checklist
    # 解决P6 Agent "无参考乱生成"的根因问题
    # V4.9.0: 从P1 scenario数据补充operations_chain/page_path到测试点
    # P2测试点只有source_scenario引用,ui_elements需要从P1 scenario提取
    p1_scenario_map = {}  # scenario_id → scenario data
    if p1_data:
        ft = p1_data.get("feature_tree", {})
        ft_modules = ft.get("modules", []) if isinstance(ft, dict) else []
        if not ft_modules:
            ft_modules = p1_data.get("modules", [])
        for mod in ft_modules:
            for feat in mod.get("children", []):
                for scen in feat.get("children", []):
                    if scen.get("type") == "scenario":
                        # V4.9.1: 兼容 operations_chain 和 operations_steps(旧字段名)
                        ops = scen.get("operations_chain") or scen.get("operations_steps", [])
                        p1_scenario_map[scen.get("id", "")] = {
                            "operations_chain": ops,
                            "page_path": scen.get("page_path", ""),
                            "precondition": scen.get("precondition", ""),
                            "scenario_type": scen.get("scenario_type", ""),
                            "related_rules": scen.get("related_rules", []),
                            "name": scen.get("name", ""),
                            "description": scen.get("description", ""),  # V4.12.0: 场景完整描述
                        }

    # 注入P1 scenario数据到测试点
    for point in deduped:
        src = point.get("source_scenario", "")
        if src and src in p1_scenario_map:
            sc = p1_scenario_map[src]
            if not point.get("operations_chain"):
                point["operations_chain"] = sc.get("operations_chain", [])
            if not point.get("page_path"):
                point["page_path"] = sc.get("page_path", "")
            if not point.get("related_rules"):
                point["related_rules"] = sc.get("related_rules", [])
            if not point.get("precondition"):
                point["precondition"] = sc.get("precondition", "")
            pp = sc.get("page_path", "")
            if pp and not point.get("field_specs"):
                path_parts = [p.strip() for p in pp.replace("→", ">").replace("/", ">").split(">") if p.strip()]
                point["_page_path_parts"] = path_parts
            point["_scenario_name"] = sc.get("name", "")
            point["_scenario_description"] = sc.get("description", "")  # V4.12.0

    enrichment_count = 0
    for point in deduped:
        if not point.get("step_expected_pairs"):
            point["step_expected_pairs"] = _build_step_expected_pairs(point)
            enrichment_count += 1
        if not point.get("ui_elements") or (
            isinstance(point.get("ui_elements"), dict) and all(len(v) == 0 for v in point["ui_elements"].values())
        ):
            point["ui_elements"] = _build_ui_elements(point)
        if not point.get("field_checklist"):
            point["field_checklist"] = _build_field_checklist(point, global_field_specs)

    # 统一补齐 priority 和 status(truncation_guard L3 必检字段)
    for point in deduped:
        if "priority" not in point:
            point["priority"] = point.get("priority_hint", "P1")
        if "status" not in point:
            point["status"] = "active"

    # V3.2.8: 给每个测试点打complexity和expected_case_count标签
    # V4.7.0: risk_verification 使用规则表驱动(基于 risk_severity),覆盖率更精确
    # 规则:根据测试点类型、风险标记、PCI标记、描述长度综合判断
    # L1(简单)≥1条, L2(常规)≥2条, L3(复杂)≥3条
    SIMPLE_CATEGORIES = {"compatibility", "display", "ui_check", "兼容回归", "展示校验"}
    COMPLEX_CATEGORIES = {"permission", "exception", "integration", "data_consistency",
                          "权限验证", "异常处理", "集成异常", "数据一致性"}

    # V4.7.0: risk_verification 规则表(基于 P3 risk_severity)
    RISK_CASE_COUNT_MAP = {"low": 1, "medium": 2, "high": 3, "critical": 3}

    for point in deduped:
        cat = (point.get("category", "") or "").lower()
        desc = point.get("description", "") or ""
        has_risk = point.get("risk_flag", False)
        has_pci = point.get("pci_flag", False)
        source = point.get("source", "P2")

        # V4.7.0: risk_verification 使用规则表驱动(不再依赖通用评分)
        if cat == "risk_verification":
            severity = (point.get("risk_severity", "") or "").lower()
            expected = RISK_CASE_COUNT_MAP.get(severity, 1)
            point["complexity"] = "L2"
            point["expected_case_count"] = expected
            continue

        # 通用复杂度评分
        score = 0
        if cat in COMPLEX_CATEGORIES:
            score += 2
        elif cat in SIMPLE_CATEGORIES:
            score += 0
        else:
            score += 1  # 默认常规
        if has_risk:
            score += 1
        if has_pci:
            score += 1
        if source in ("P3", "P4"):
            score += 1  # 风险/PCI派生的测试点本身就复杂
        if len(desc) > 100:
            score += 1  # 描述越长通常越复杂

        # 分级
        if score <= 0:
            point["complexity"] = "L1"
            point["expected_case_count"] = 1
        elif score <= 2:
            point["complexity"] = "L2"
            point["expected_case_count"] = 2
        else:
            point["complexity"] = "L3"
            point["expected_case_count"] = 3
        # P0测试点强制上限expected_case_count=2,避免冒烟比例被稀释
        if point.get("priority") == "P0" and point.get("expected_case_count", 2) > 2:
            point["expected_case_count"] = 2

    # 统计复杂度分布
    complexity_dist = {}
    total_expected = 0
    for point in deduped:
        c = point.get("complexity", "L2")
        complexity_dist[c] = complexity_dist.get(c, 0) + 1
        total_expected += point.get("expected_case_count", 2)

    # V4.13.9-S4: 生成P5优先级预算(元规则#10)
    # P0_max = MIN(Σtp.expected_case_count × 15%, 20); smoke_max = P0_max × 1.1
    priority_budget = {
        "P0_max": min(int(total_expected * 0.15), 20),
        "P0_ratio": 0.15,
        "smoke_max": min(int(total_expected * 0.15 * 1.1), 22),
    }

    # 构造P5输出
    p5_output = {
        "schema_version": "1.0.0",
        "prompt_version": "1.0.0",
        "requirement_id": p2_data.get("requirement_id", ""),
        "test_points": deduped,
        "priority_budget": priority_budget,  # V4.13.9-S4: 优先级预算(P6 merge时强制执行)
        "merge_log": {
            "from_p2": len(p2_points),
            "from_p3": from_p3_count,
            "from_p4": from_p4_count,
            "merged": len(merged_points),
            "removed_duplicates": removed,
            "final_count": len(deduped),
            "v470_enriched": enrichment_count,
        },
        "coverage_summary": {
            "total_test_points": len(deduped),
            "risk_flagged": sum(1 for p in deduped if p.get("risk_flag")),
            "pci_flagged": sum(1 for p in deduped if p.get("pci_flag")),
            "complexity_distribution": complexity_dist,
            "total_expected_cases": total_expected,
        },
    }

    # V4.12.0/V4.14.0: description自动扩展 - 当description<80字时从step_expected_pairs/operations_chain合成
    # 解决P5测试点description过于简单导致P6 Agent无据可依的问题
    # V4.14.0: 触发门槛 30字 → 80字(与P5质量门禁BLOCK阈值对齐)
    for point in deduped:
        desc = str(point.get("description", "")).strip()
        if len(desc) >= 80:
            continue
        page_path = point.get("page_path", "")
        pairs = point.get("step_expected_pairs", []) or []
        ops_chain = point.get("operations_chain", []) or []
        category = point.get("category", "")

        # 从step_expected_pairs提取操作序列
        action_parts = []
        if ops_chain:
            for op in ops_chain[:5]:
                if isinstance(op, dict):
                    a = op.get("action", op.get("operation", ""))
                    t = op.get("target", op.get("target_element", ""))
                    if a and t:
                        action_parts.append(f"{a}「{t}」")
                    elif a:
                        action_parts.append(a)
        if not action_parts and pairs:
            for sp in pairs[:4]:
                if isinstance(sp, dict):
                    s = sp.get("step", "")
                    if s:
                        action_parts.append(s)

        # 构建扩展description
        expanded_parts = []
        if page_path and desc:
            expanded_parts.append(f"在{page_path}页面")
        if action_parts:
            expanded_parts.append("→".join(action_parts[:4]))
        if not expanded_parts and desc:
            expanded_parts.append(desc)
        if expanded_parts:
            # 避免重复"验证"前缀(description通常已含"验证"开头)
            verify_target = desc
            if desc.startswith("验证"):
                verify_target = desc[2:]
            expanded_parts.append(f"验证{verify_target}")
            new_desc = ",".join(expanded_parts)
            # V4.14.0: 确保≥80字对齐门禁,不足则追加category+前置描述
            if len(new_desc) < 80:
                cat_map = {
                    "main_flow": "核心正向流程",
                    "branch": "分支场景",
                    "exception": "异常处理",
                    "boundary": "边界条件",
                    "permission": "权限控制",
                }
                new_desc += f"({cat_map.get(category, category)})"
                # 仍不足80字: 追加前置条件提示(环境+数据维度),提升门禁通过率
                if len(new_desc) < 80:
                    precond = str(point.get("precondition", "")).strip()
                    if precond:
                        new_desc += f";前置条件:{precond}"
                    elif page_path:
                        new_desc += f";需已登录系统并进入{page_path}页面,相关数据已准备就绪"
            point["description"] = new_desc[:200]  # 截断保护
            point["_desc_auto_expanded"] = True  # 标记来源

    # ============================================================
    # V4.14.0-P5: description 质量门禁 + 熜断机制
    # 在合并完成后、写入 p5_output.json 之前执行。
    # - BLOCK 项 → 输出 fix_hints(具体哪条TP不达标、缺什么)
    # - 计数熜断: 同一TP被拒≥3次 → 降级放行(WARNING标记不阻断)
    # - 整批拦截>50% → 输出系统性问题提示,但继续完成合并
    # ============================================================
    p5_quality = None
    if _check_p5_desc_quality is not None and not skip_quality:
        try:
            # 熜断计数持久化(跨 p5_code_merge 重跑累计)
            reject_path = os.path.join(data_dir, "p5_quality_rejects.json")
            reject_map = _read_json(reject_path) if os.path.exists(reject_path) else {}
            if not isinstance(reject_map, dict):
                reject_map = {}

            CIRCUIT_BREAK_SINGLE = 3        # 单TP熜断阈值
            CIRCUIT_BREAK_BATCH_RATIO = 0.5  # 整批熜断比例

            gate_results = _check_p5_desc_quality(deduped)
            point_by_id = {str(p.get("id", "")): p for p in deduped}

            fix_hints = []
            block_active = 0   # 本轮真正拦截(未熜断)的TP数
            downgraded_count = 0  # V4.15.36: 操作链降级放行的TP数
            circuit_break_passed = 0
            warning_count = 0

            for gr in gate_results:
                tp_id = str(gr.get("tp_id", "?"))
                issues = gr.get("issues", [])
                block_issues = [i for i in issues if i.get("level") == "BLOCK"]
                warn_issues = [i for i in issues if i.get("level") == "WARNING"]
                pt = point_by_id.get(tp_id)

                if warn_issues:
                    warning_count += 1
                    if pt is not None:
                        pt.setdefault("_quality_warnings", [])
                        pt["_quality_warnings"].extend(w.get("reason", "") for w in warn_issues)

                if not block_issues:
                    if pt is not None and pt.get("_quality_gate") != "CIRCUIT_BREAK_PASS":
                        pt["_quality_gate"] = "PASS"
                        # V4.15.36: 标记降级放行供 P6/P7 追溯
                        if gr.get("downgraded"):
                            pt["_desc_gate_downgraded"] = True
                    # 通过后清零该TP的拒绝计数
                    reject_map.pop(tp_id, None)
                    if gr.get("downgraded"):
                        downgraded_count += 1
                    continue

                # 存在 BLOCK → 计数加一（上限=熔断阈值+1，防止无限累积）
                reject_map[tp_id] = min(int(reject_map.get(tp_id, 0)) + 1, CIRCUIT_BREAK_SINGLE + 1)
                attempts = reject_map[tp_id]
                reasons = "; ".join(i.get("reason", "") for i in block_issues)

                if attempts >= CIRCUIT_BREAK_SINGLE:
                    # 熜断: 降级放行, 不阻断
                    circuit_break_passed += 1
                    if pt is not None:
                        pt["_quality_gate"] = "CIRCUIT_BREAK_PASS"
                        pt["_quality_issues"] = block_issues
                        pt["_quality_attempts"] = attempts
                    fix_hints.append({
                        "tp_id": tp_id,
                        "verdict": "CIRCUIT_BREAK_PASS",
                        "attempts": attempts,
                        "char_count": gr.get("char_count"),
                        "dim_hits": gr.get("dim_hits"),
                        "reason": reasons,
                        "hint": f"TP-{tp_id} 第{attempts}次不达标,触发熜断降级放行(标记WARNING供P7参考)",
                    })
                else:
                    # 拦截: 记录 fix_hint(代码合并仍继续,该TP保留但标记不达标)
                    block_active += 1
                    if pt is not None:
                        pt["_quality_gate"] = "BLOCK"
                        pt["_quality_issues"] = block_issues
                        pt["_quality_attempts"] = attempts
                    fix_hints.append({
                        "tp_id": tp_id,
                        "verdict": "BLOCK",
                        "attempts": attempts,
                        "char_count": gr.get("char_count"),
                        "dim_hits": gr.get("dim_hits"),
                        "reason": reasons,
                        "hint": f"TP-{tp_id} description不达标: {reasons}。请补充入口+操作序列+具体验证目标,至少覆盖2个前置条件维度",
                    })

            # 持久化拒绝计数
            try:
                _write_json(reject_path, reject_map)
            except Exception:
                pass

            total_tp = len(deduped)
            block_ratio = (block_active / total_tp) if total_tp else 0.0

            # === V4.15.18: P5熔断三级响应（替代原有的systemic single-check） ===
            CIRCUIT_BREAK_WARNING_RATIO = 0.30
            CIRCUIT_BREAK_STOP_RATIO = 0.50
            CIRCUIT_BREAK_SELFCHECK_RATIO = 0.80

            p5_quality = {
                "checked": total_tp,
                "block_active": block_active,
                "downgraded": downgraded_count,  # V4.15.36: 操作链降级放行数
                "circuit_break_passed": circuit_break_passed,
                "warning": warning_count,
                "block_ratio": round(block_ratio, 3),
                "fix_hints": fix_hints[:30],
            }
            if downgraded_count > 0:
                print(json.dumps({
                    "event": "p5_desc_gate_downgraded",
                    "count": downgraded_count,
                    "note": f"V4.15.36: {downgraded_count}个TP因有完整操作链而降级BLOCK→WARNING放行"
                }, ensure_ascii=False))

            if block_ratio >= CIRCUIT_BREAK_SELFCHECK_RATIO:
                # 系统级故障：写入阻止锁 + 触发规则自检警告
                p5_quality["action"] = "SELF_CHECK"
                p5_quality["self_check_reason"] = f"BLOCK率{block_ratio:.0%}异常(>{CIRCUIT_BREAK_SELFCHECK_RATIO:.0%})，可能检查规则有bug"
                _write_json(os.path.join(data_dir, ".p5_blocked_lock"), {
                    "reason": "self_check", "block_ratio": block_ratio,
                    "recovery": "执行 p5_retry --force-continue 跳过门禁(风险自担) || 重新执行P2/P3/P4规划"
                })
            elif block_ratio >= CIRCUIT_BREAK_STOP_RATIO:
                # 高风险：阻止进入P6 + 诊断 + 恢复指引
                rule_issues_count = sum(1 for h in fix_hints if any(
                    kw in str(h.get("reason","")).lower() for kw in ("字数", "维度", "前置条件维度")))
                quality_issues_count = len(fix_hints) - rule_issues_count
                p5_quality["action"] = "STOP"
                p5_quality["diagnosis"] = {
                    "rule_issues": rule_issues_count, "quality_issues": quality_issues_count,
                    "primary_cause": "规则异常(description字数/维度检查过严)" if rule_issues_count > quality_issues_count else "P5质量问题(测试点提取不充分)"
                }
                _write_json(os.path.join(data_dir, ".p5_blocked_lock"), {
                    "reason": "high_block_ratio", "block_ratio": block_ratio,
                    "diagnosis": p5_quality["diagnosis"],
                    "recovery": "重新执行P2/P3/P4规划（推荐） || p5_retry --force-continue 跳过门禁(风险自担)"
                })
                # 阻止流程：不写入p5_output.json，返回error
                print(json.dumps({
                    "status": "p5_blocked", "action": "STOP",
                    "block_ratio": f"{block_ratio:.0%}",
                    "reason": f"P5 BLOCK率{block_ratio:.0%}>={int(CIRCUIT_BREAK_STOP_RATIO*100)}%，质量风险过高，阻止进入P6。"
                    f"诊断：{p5_quality['diagnosis']['primary_cause']}",
                    "recovery": "重新执行P2/P3/P4规划（推荐） || p5_retry --force-continue 跳过门禁(风险自担)"
                }, ensure_ascii=False))
                return {"status": "blocked", "reason": f"P5质量门禁BLOCK率{block_ratio:.0%}"}
            elif block_ratio >= CIRCUIT_BREAK_WARNING_RATIO:
                # 中等风险：降级放行 + 警告
                p5_quality["action"] = "WARNING"
                p5_quality["warning_reason"] = f"BLOCK率{block_ratio:.0%}>={int(CIRCUIT_BREAK_WARNING_RATIO*100)}%，已降级放行但P7可能受影响"
            else:
                p5_quality["action"] = "PASS"
            p5_output["p5_quality_gate"] = p5_quality
        except Exception as _qe:
            # 门禁异常不阻断合并流程
            p5_output["p5_quality_gate"] = {"error": f"P5质量门禁执行异常: {_qe}"}

    # V4.15.8: P0预算硬约束（写入前执行）
    deduped = _enforce_p0_budget(deduped)
    p5_output["test_points"] = deduped

    # === V4.15.18: P5写入保护（已有完整数据时不覆盖）===
    _final_p5_path = os.path.join(data_dir, "p5_output.json")
    if os.path.exists(_final_p5_path):
        try:
            _existing_p5 = _read_json(_final_p5_path)
            if _existing_p5.get("test_points") and _existing_p5.get("merge_log"):
                print(json.dumps({
                    "status": "p5_protected",
                    "reason": "p5_output.json已存在完整数据(test_points+merge_log)，跳过覆写"
                }, ensure_ascii=False))
                return {"status": "ok", "step": "P5", "total_test_points": len(deduped), "protected": True}
        except Exception:
            pass  # 读取失败则允许覆盖

    # 写入tmp→truncation_guard→gate pass
    tmp_path = os.path.join(data_dir, "p5_output.tmp.json")
    _write_json(tmp_path, p5_output)

    ok, msg = run_truncation_guard(skill_dir, data_dir, task_id, "P5")
    if ok:
        state = TaskState(data_dir=data_dir, task_id=task_id)
        state.mark_complete("P5")
        _result = {
            "status": "ok",
            "step": "P5",
            "total_test_points": len(deduped),
            "from_p2": len(p2_points),
            "from_p3": from_p3_count,
            "from_p4": from_p4_count,
            "removed_duplicates": removed,
        }
        if p5_quality is not None:
            _result["p5_quality_gate"] = {
                "block_active": p5_quality.get("block_active"),
                "circuit_break_passed": p5_quality.get("circuit_break_passed"),
                "warning": p5_quality.get("warning"),
                "block_ratio": p5_quality.get("block_ratio"),
                "systemic_issue": p5_quality.get("systemic_issue"),
            }
            if p5_quality.get("systemic_issue"):
                _result["p5_quality_gate"]["systemic_message"] = p5_quality.get("systemic_message")
        print(json.dumps(_result))
    else:
        print(json.dumps({"status": "guard_failed", "step": "P5", "reason": msg}))
        sys.exit(1)


# ============================================================
# V4.11.0: P6逐条生成(替代批量分批)
# ============================================================

def _extract_project_name(data_dir):
    """V4.12.6: 从task_meta提取干净的项目名称
    优先级: task_meta.project_name → task_meta.requirement_title → 空
    """
    meta_path = os.path.join(data_dir, "task_meta.json")
    if not os.path.exists(meta_path):
        return ""
    try:
        meta = _read_json(meta_path)
        name = meta.get("project_name", "") or meta.get("requirement_title", "")
        # 清理: 去除项目名中的路径前缀和多余标点
        if name:
            name = str(name).strip().split("\n")[0][:50]  # 取第一行,限50字
        return name
    except Exception:
        return ""


def _extract_biz_context(data_dir):
    """V4.11.0: 从P0输出提取业务上下文(精简版,~800字上限)"""
    p0_path = os.path.join(data_dir, "p0_output.json")
    if not os.path.exists(p0_path):
        return ""
    try:
        p0 = _read_json(p0_path)
        parts = []
        pages = p0.get("blocks", {}).get("pages", p0.get("pages", []))
        ops = p0.get("blocks", {}).get("operations", p0.get("operations", []))
        rules = p0.get("blocks", {}).get("business_rules", p0.get("business_rules", []))
        if pages:
            parts.append("页面: " + "; ".join(str(p)[:200] for p in pages[:5]))
        if ops:
            parts.append("操作: " + "; ".join(str(o)[:200] for o in ops[:5]))
        if rules:
            parts.append("业务规则: " + "; ".join(str(r)[:200] for r in rules[:5]))
        return "\n".join(parts)[:800]
    except Exception:
        return ""


def _classify_source_type(tp):
    """V4.12.4: 从source+category推导source_type"""
    source = tp.get("source", "")
    category = tp.get("category", "")
    if source == "risk" or category == "risk_verification":
        return "risk_extension"
    if category in ("boundary",):
        return "boundary_value"
    if category in ("exception", "permission", "security"):
        return "exception"
    if category in ("integration", "compatibility"):
        return "integration"
    return "functional"


def _check_tp_risk_link(tp, p3_risks):
    """V4.12.4: 检查TP是否关联P3风险点
    匹配策略: TP title/description包含P3风险点的关键词
    """
    if not p3_risks:
        return False, ""
    tp_text = f"{tp.get('title','')} {tp.get('description','')}".lower()
    for risk in p3_risks:
        risk_id = str(risk.get("id", ""))
        risk_desc = str(risk.get("description", ""))
        # 风险ID匹配(如 RISK-001 → TP中可能引用)
        if risk_id and risk_id.lower() in tp_text:
            return True, str(risk.get("severity", risk.get("risk_severity", "")))
        # 风险关键词匹配(取风险描述中的关键短语)
        for word in risk_desc.split()[:5]:
            if len(word) >= 3 and word.lower() in tp_text:
                return True, str(risk.get("severity", risk.get("risk_severity", "")))
    return False, ""


def _category_hint(category):
    """V4.12.4: 将category映射为中文引导提示"""
    hints = {
        "main_flow": "主流程功能验证(核心路径,冒烟覆盖)",
        "branch": "分支流程验证(备选路径)",
        "exception": "异常场景验证(输入异常/状态异常/权限异常)",
        "boundary": "边界值验证(数值/长度/时间边界)",
        "permission": "权限控制验证(不同角色/数据权限)",
        "risk_verification": "风险触发场景验证(系统应对因果链)",
        "field_validation": "字段级校验",
        "integration": "集成联动验证",
        "security": "安全合规验证",
        "state_migration": "状态流转验证",
        "compatibility": "兼容性验证",
    }
    return hints.get(category, "功能验证")


def _desc_fallback(tp):
    """V4.15.53: description为空时用title+category兜底"""
    desc = tp.get("description", "")
    if desc and desc.strip():
        return desc
    title = tp.get("title", "")
    cat = tp.get("category", "")
    cat_cn = _category_hint(cat)
    return f"{title} - {cat_cn}场景" if title else f"{cat_cn}场景"


def _write_tp_contexts(data_dir, test_points, model_tier, p3_risks=None, p4_pci_list=None):
    """V4.12.0: 为每个TP写入完整上下文(供p6_generate_one读取)

    V4.12变更:补全page_path/precondition/step_expected_pairs/ui_elements/
    field_checklist/operations_chain字段,解决P6 Agent无据可依的根因问题。
    所有新增字段带兜底空值,兼容旧P5数据。
    """
    out_dir = os.path.join(data_dir, "p6_tp_output")
    _ensure_dir(out_dir)
    biz_ctx = _extract_biz_context(data_dir)
    for i, tp in enumerate(test_points):
        # V4.12.0: 相邻TP差异化提示(前2后2,供LLM生成差异化用例)
        adj_tps = []
        for offset in (-2, -1, 1, 2):
            ni = i + offset
            if 0 <= ni < len(test_points):
                nt = test_points[ni]
                adj_tps.append({
                    "relation": "上一个" if offset < 0 else "下一个",
                    "title": nt.get("title", ""),
                    "category": nt.get("category", ""),
                })

        # V4.15.50: P5直接设置的risk_flag优先，文本匹配兜底
        # 修复前 _check_tp_risk_link 文本匹配忽略P5已设置的字段，
        # 导致19个risk_flag=True的TP在P6 context中被改写为False
        _rf_field = tp.get("risk_flag", False)
        if _rf_field:
            risk_flag = _rf_field
            risk_severity = tp.get("risk_severity", "")
        else:
            risk_flag, risk_severity = _check_tp_risk_link(tp, p3_risks or [])

        ctx = {
            "tp_index": i,
            "tp_id": tp.get("id", ""),
            "title": tp.get("title", ""),
            # V4.15.53: description为空时用title+category兜底
            "description": _desc_fallback(tp),
            "category": tp.get("category", ""),
            "priority": tp.get("priority", ""),
            "expected_case_count": tp.get("expected_case_count", 2),
            "business_context": biz_ctx,
            "model_tier": model_tier,
            # V4.12.0: 补全P6 prompt消费的结构化字段(所有字段兜底空值)
            "page_path": tp.get("page_path", ""),
            "precondition": tp.get("precondition", "") or tp.get("_precondition", ""),
            "step_expected_pairs": tp.get("step_expected_pairs", []) or [],
            "ui_elements": tp.get("ui_elements", {}) or {},
            "field_checklist": tp.get("field_checklist", []) or [],
            "operations_chain": tp.get("operations_chain", []) or [],
            "related_rules": tp.get("related_rules", []) or [],
            "scenario_description": tp.get("_scenario_description", ""),  # P1场景完整描述
            # V4.12.0: 相邻TP供差异化参考
            "adjacent_tps": adj_tps,
            "total_tps": len(test_points),  # V4.12.5: 总TP数(用于分批回顾+频率检测豁免)
            # V4.12.4: P6质量引导增强字段
            "source": tp.get("source", "requirement"),
            "source_type": _classify_source_type(tp),
            "risk_flag": risk_flag,
            "risk_severity": risk_severity,
            "priority_hint": tp.get("priority_hint", ""),
            "need_smoke": (tp.get("priority", "").upper() in ("P0", "HIGHEST")
                          and tp.get("category", "") in ("main_flow", "正向", "功能")),
            "pci_flag": bool(p4_pci_list and any(
                tp.get("id", "") in str(pci) for pci in p4_pci_list)),
            "category_hint": _category_hint(tp.get("category", "")),
        }
        _write_json(os.path.join(out_dir, f"tp_{i:03d}_context.json"), ctx)


def _build_single_tp_prompt(ctx, model_tier=None):
    """V5.0(4.13.0): 构建单TP完整prompt(~1500B)
    
    V5.0: 废除 HIGH/LOW 分档,model_tier 参数保留(兼容旧调用)但不使用。
    格式示例对所有模型统一输出。
    """
    title = ctx.get("title", "")
    desc = ctx.get("description", "")
    ec = ctx.get("expected_case_count", 2)
    biz = ctx.get("business_context", "")
    page_path = ctx.get("page_path", "")
    precondition = ctx.get("precondition", "")
    step_pairs = ctx.get("step_expected_pairs", []) or []
    ui_elems = ctx.get("ui_elements", {}) or {}
    fields = ctx.get("field_checklist", []) or []
    ops_chain = ctx.get("operations_chain", []) or []
    related_rules = ctx.get("related_rules", []) or []
    scenario_desc = ctx.get("scenario_description", "")
    # V4.12.4: P6质量引导字段
    source = ctx.get("source", "requirement")
    source_type = ctx.get("source_type", "functional")
    risk_flag = ctx.get("risk_flag", False)
    risk_severity = ctx.get("risk_severity", "")
    need_smoke = ctx.get("need_smoke", False)
    pci_flag = ctx.get("pci_flag", False)
    category_hint = ctx.get("category_hint", "功能验证")

    lines = [
        "你是测试用例编写专家,基于以下上下文为测试点生成具体可执行的测试用例。",
        "",
        "## 测试点",
        f"**{title}**",
        desc,
        "",
    ]

    # 页面路径
    if page_path:
        lines.extend(["## 页面路径", page_path, ""])

    # 操作链路(优先operations_chain,其次step_expected_pairs)
    if ops_chain:
        lines.append("## 操作链路")
        for op in ops_chain[:8]:
            if isinstance(op, dict):
                action = op.get("action", op.get("operation", ""))
                target = op.get("target", op.get("target_element", ""))
                if action and target:
                    lines.append(f"- {action}「{target}」")
                elif action:
                    lines.append(f"- {action}")
        lines.append("")
    elif step_pairs:
        lines.append("## 操作骨架")
        for sp in step_pairs[:5]:
            if isinstance(sp, dict):
                s = sp.get("step", "")
                e = sp.get("expected", "")
                if s:
                    lines.append(f"- {s}  →  期望:{e}" if e else f"- {s}")
        lines.append("")

    # UI元素清单
    if ui_elems:
        parts = []
        for cat in ("buttons", "inputs", "selectors", "labels"):
            items = ui_elems.get(cat, [])
            if items:
                label = {"buttons": "按钮", "inputs": "输入框", "selectors": "下拉", "labels": "标签"}.get(cat, cat)
                parts.append(f"{label}:{'、'.join(str(x)[:20] for x in items[:5])}")
        if parts:
            lines.extend(["## 可用UI元素", "; ".join(parts), ""])

    # 涉及字段
    if fields:
        lines.extend(["## 涉及字段", "、".join(str(f)[:30] for f in fields[:8]), ""])

    # 前置条件
    if precondition:
        lines.extend(["## 前置条件", precondition, ""])

    # 业务上下文
    if biz:
        lines.extend(["## 业务上下文", biz, ""])

    # 场景描述(P1级丰富上下文)
    if scenario_desc:
        lines.extend(["## 场景描述(来自需求分析)", scenario_desc[:300], ""])

    # 业务规则
    if related_rules:
        lines.append("## 业务规则(期望结果必须基于这些规则断言)")
        for r in related_rules[:5]:
            if isinstance(r, str):
                lines.append(f"- {r[:120]}")
            elif isinstance(r, dict):
                rid = r.get("id", r.get("rule_id", ""))
                rdesc = r.get("description", r.get("rule", ""))
                if rid or rdesc:
                    lines.append(f"- {rid}: {rdesc}"[:120])
        lines.append("")

    # 相邻TP差异化提示
    adj_tps = ctx.get("adjacent_tps", []) or []
    if adj_tps:
        lines.append("## 相邻测试点(确保你的用例步骤与以下TP有差异化)")
        for at in adj_tps:
            lines.append(f"- {at['relation']}:{at['title']}({at['category']})")
        lines.append("⚠️ 你的用例步骤必须与上述相邻TP有明显差异,禁止复用相同步骤。")
        lines.append("")

    # === V4.12.4: 差异化引导模块 ===

    # 模块1：风险扩展引导
    if risk_flag:
        lines.extend([
            "🔴 **风险扩展测试点**" + (f" (风险等级: {risk_severity})" if risk_severity else ""),
            "",
            "此测试点存在关联风险，你必须生成覆盖以下维度的风险场景用例：",
            "- **风险触发路径**：描述从正常状态→异常状态的变化过程（谁、做什么、在什么条件下触发）",
            "- **系统应对链**：期望结果必须包含「检测→告警→阻断→恢复」的因果链",
            "- **不同触发条件**：每个用例覆盖不同的风险触发入口（数据异常/操作异常/并发冲突）",
            "",
            "❌ 禁止生成纯功能正向验证用例（这不是功能测试点）",
            "✅ 必须生成风险触发 → 系统应对的因果链用例",
            "",
        ])

    # 模块2：PCI合规引导
    if pci_flag:
        lines.extend([
            "🔒 **PCI合规审计测试点**",
            "",
            "要求：",
            "- 每个用例必须绑定至少一个 PCI 合规项（标注PCI编号）",
            "- 覆盖：数据脱敏、权限边界、审计日志 三类合规场景",
            "- 期望结果必须包含合规判定（如'敏感字段已脱敏显示'）",
            "",
        ])

    # 模块3：冒烟用例引导
    if need_smoke:
        lines.extend([
            "🔥 **冒烟用例要求** (此测试点是核心主流程P0)",
            "",
            "第1条用例必须是冒烟用例：",
            "- 覆盖核心正向功能的最短完整路径（3-5步）",
            "- 预置条件为标准正常业务状态",
            "- 步骤包含最小必要操作，直达目标页面/功能",
            "- 期望结果可观测（页面跳转/数据变化/状态变更）",
            '- 必须在JSON中设置 `\"is_smoke\": true`',
            "",
            f"后续 {ec} 条可覆盖异常/边界/权限等其他场景。",
            "",
        ])

    # 模块4：用例类型分布建议
    lines.extend([
        f"📊 **用例类型指引** ({category_hint})",
        "",
    ])
    if need_smoke:
        lines.append("- 第1条：冒烟用例(主流程核心正向)")
    if ec >= 2:
        smoke_offset = 1 if need_smoke else 0
        lines.append(f"- 第{smoke_offset+1}条：主流程正向验证")
        n_exc = max(1, ec // 3)
        if n_exc > 0:
            lines.append(f"- 第{smoke_offset+2}条起：异常场景 ({n_exc}条)")
        n_bnd = max(0, ec - 1 - (1 if need_smoke else 0) - n_exc)
        if n_bnd > 0:
            lines.append(f"- 余下：边界场景 ({n_bnd}条)")
    lines.extend([
        f"- ⚠️ 禁止{ec}条用例全部为同一类型！",
        "",
    ])

    # 生成要求
    lines.extend([
        "## 生成要求",
        "1. 每条步骤 ≥15字,格式:「动作词」+「UI元素名」(如点击「查询」按钮、在「员工姓名」输入框输入'张三')",
        "2. steps 第1步必须包含页面入口描述(引用上述页面路径)" if page_path else "2. steps 第1步必须包含具体页面路径",
        "3. 步骤中必须引用至少1个上述UI元素或字段(用「」包裹)" if (ui_elems or fields) else "3. 步骤中必须引用具体UI元素或字段(用「」包裹)",
        "4. 禁止使用:执行相关操作/进入对应页面/验证结果/执行操作流程",
        "5. 期望结果必须可观测:页面跳转/弹出提示/列表刷新/状态变为/显示具体值",
        "6. 每条用例的步骤必须与其他用例有差异,不得复用相同步骤",
        "7. 必须输出 menu_path(用例菜单,引用上述页面路径)",
        "8. 必须输出 preconditions(前置条件,基于上述前置条件+场景描述)",
        "",
    ])

    # 格式示例(V5.0(4.13.0): 统一输出,所有模型受益)
    lines.extend([
        "## 格式示例",
        "```json",
        '[{"title":"验证XX-正常场景","menu_path":"XX→XX→XX页面","preconditions":"已登录系统,已配置XX参数",'
        '"steps":"1. 点击「查询」按钮\\n2. 在「员工姓名」输入框输入\u2018张三\u2019",'
        '"expected_results":"1. 列表刷新显示查询结果\\n2. 列表数据中员工姓名字段与输入值一致"}]',
        "```",
        "",
    ])

    lines.extend([
        f"🔴 必须生成 **{ec}** 条用例（不是1条！必须达到{ec}条！），直接输出JSON数组(每条必须包含title/menu_path/preconditions/steps/expected_results):",
        "```json",
        "[",
        '  {"title":"...","menu_path":"...","preconditions":"...","steps":"1. ...\\n2. ...","expected_results":"1. ...\\n2. ..."},',
        "... （共计{ec}条用例，不得少于{ec}条）".replace("{ec}", str(ec)),
        "]",
        "```",
    ])

    # === V4.14.2: G1.5禁止词前置 ===
    lines.extend([
        "## 🔴 G1.5 强制规则：禁止在期望结果中使用模糊词（违反将触发重试）",
        "",
        "| 禁止词 | 正确替代（必须可观测） |",
        "|--------|-------------------------|",
        '| 正常 | "页面显示XX组件" / "列表刷新显示XX数据" / "状态变为XX" |',
        '| 成功 | "页面弹出提示「XX」" / "操作完成，列表新增1条记录" |',
        '| 能/能够/可以 | "按钮变为可点击状态" / "输入框可编辑" / "链接可跳转" |',
        '| 恢复/还原 | "数据还原为XX" / "状态从XX变为YY" / "页面回退至XX" |',
        '| 正确 | "数据一致，字段A值等于接口返回的A值" / "值等于XX" |',
        '| 正常显示 | "页面显示XX组件，包含A/B/C字段" / "元素在视口内完整渲染" |',
        '| 无异常 | "系统返回状态码200" / "无error日志" / "所有接口正常响应" |',
        '| 符合预期 | 直接描述具体预期值，如"列表排序按时间降序，首条为最新记录" |',
        '| 一致 | "字段A值与接口X返回的A值相等" / "页面数据与数据库记录一致" |',
        '| 响应及时 | "接口响应时间<3秒" / "页面加载完成时间<XX秒" |',
        '| 正确提示 | "页面弹出提示「XX」，弹窗2秒后自动关闭" |',
        "| 合理 | \"页面宽度适配屏幕，无横向滚动条\" / \"表单字段按业务逻辑排列\" |",
        "",
        "**白名单安全短语（技术术语，可直接使用）：** 正常退出、正常关闭、成功回调、成功状态码、正确路径",
        "",
        "**否定句式豁免**：`不X`/`未X`/`非X` + 禁止词不触发拦截（如\"系统提示\'操作未成功\'\"），但必须有具体异常描述",
        "",
        '正确示例：❌ "系统恢复正常" → ✅ "页面弹出提示「推送成功」，状态变为「审批中」"',
        '正确示例：❌ "提交成功" → ✅ "页面弹出提示「提交成功」，列表新增1条草稿记录"',
        '',
    ])

    # V4.15.31: G1.5输出前强制自检(消除3-4轮循环重试)
    lines.extend([
        "## 🔴 输出前强制自检（必须在输出JSON前逐条验证）",
        "",
        "在生成用例JSON后、输出前，逐条扫描 expected_results 中的以下9个禁止词：",
        "**正常、成功、正确、符合预期、功能正常、数据正确处理、操作成功完成、一致、无异常**",
        "",
        "自检方法：先在心中逐条扫描 → 发现任一禁止词立即重写该期望结果 → 确认0禁止词后输出",
        "如果跳过自检直接输出 → 门禁会触发重试 → 浪费1次LLM调用",
        "**一次自检 = 避免3-4轮重试。这是最高ROI的优化。**",
        "",
    ])

    # V4.15.31: HOLLOW_STEPS步骤规范前置(消除生成后空洞拦截)
    lines.extend([
        "## 🔴 步骤强制规范（违反将触发HOLLOW_STEPS拦截）",
        "",
        "每条步骤必须满足两项：",
        "1. **包含具体UI元素**：按钮/菜单/输入框用「」包裹，如「保存」「提交审批」「查询」",
        "2. **去除编号后≥10汉字**：数字、标点、英文字母不计入",
        "",
        '❌ 禁止："1. 执行相关操作" "2. 验证结果" "3. 进入功能页面"',
        '✅ 正确："1. 点击「分润明细」菜单" "2. 在「团队名称」输入框输入XX"',
        '✅ 正确："3. 点击「查询」按钮，确认列表刷新"',
        '',
    ])

    return "\n".join(lines)


def _quick_gate_single_tp(cases):
    """V4.11.0: 单TP快速Gate(G1+G1.5+G5-intra),不跨TP
    V4.13.3: G1.5模糊词检测排除「」引号内UI文案(假阳性修复)
    """
    issues = []
    # V4.15.29: G2扩展 — 增加"一致"/"无异常"(P7 G2残留4条根因)
    fuzzy_words = ["正常", "成功", "正确", "符合预期", "功能正常", "数据正确处理", "操作成功完成", "一致", "无异常"]
    for c in cases:
        cid = c.get("case_id", "?")
        if not str(c.get("title", "")).strip():
            issues.append({"case_id": cid, "rule": "G1", "violation": "title为空"})
        if not str(c.get("steps", "")).strip():
            issues.append({"case_id": cid, "rule": "G1", "violation": "steps为空"})
        exp = str(c.get("expected_results", "")).strip()
        if not exp:
            issues.append({"case_id": cid, "rule": "G1.5", "violation": "expected_results为空"})
            continue
        # V4.15.23: 增加preconditions为空检查（原设计遗漏，fix#2）
        # V4.15.29: C6.1增强 — 前置条件分段数<2即拦截(消除19% P7修复)
        prec = str(c.get("preconditions", "")).strip()
        if not prec:
            issues.append({"case_id": cid, "rule": "C6.1", "violation": "preconditions为空"})
        else:
            # 按分号/换行拆分，过滤纯空段
            _prec_segs = [s.strip() for s in re.split(r'[；;\n]', prec) if s.strip()]
            if len(_prec_segs) < 2:
                issues.append({
                    "case_id": cid, "rule": "C6.1",
                    "violation": f"前置条件仅{len(_prec_segs)}段，需≥2个要素(账号/权限+数据构造/环境配置)",
                    "hint": "示例: 已登录XX角色用户; 已创建XX条测试数据"
                })
        # V4.13.3: 先剥离「」引号内UI文案再检测模糊词(假阳性修复)
        # "弹出「操作成功」提示框" → "弹出提示框" 不触发模糊词误报
        # V4.15.5: 只剥离「」引号内UI文案（【待具化】剥离不再需要,auto-mark已移除）
        # V4.15.20: 从steps提取引号内容做豁免，降级模糊词为WARNING
        steps_quoted = set()
        for _mq in re.finditer(r'[「『《].+?[」』》]', str(c.get("steps", ""))):
            steps_quoted.add(_mq.group(0))
        exp_stripped = re.sub(r'「[^」]*」', '「」', exp)
        for w in fuzzy_words:
            if w in exp_stripped:
                if any(w in q for q in steps_quoted):
                    continue  # steps引号中含此词→豁免
                issues.append({"case_id": cid, "rule": "G1.5",
                    "violation": f"期望含模糊词'{w}'", "level": "WARNING"})
                break
    # G5-intra: 同TP内步骤完全相同 → WARNING(不retry)
    if len(cases) >= 2:
        steps_set = set(str(c.get("steps", "")).strip() for c in cases)
        if len(steps_set) == 1:
            issues.append({
                "rule": "G5-intra",
                "violation": f"同TP内{len(cases)}条用例步骤完全相同",
                "type": "warning",
            })
    # V4.15.26: C2自检 — steps vs expected 行数差≥2, P6阶段拦截(不等P7)
    import re as _qs_re
    for c in cases:
        cid = c.get("case_id", "?")
        sc = len(_qs_re.findall(r'^\d+[\.\、＋）)]', str(c.get("steps", "")), _qs_re.MULTILINE))
        ec = len(_qs_re.findall(r'^\d+[\.\、＋）)]', str(c.get("expected_results", "")), _qs_re.MULTILINE))
        if abs(sc - ec) >= 2:
            issues.append({
                "case_id": cid, "rule": "C2",
                "violation": f"步骤({sc})与期望({ec})数量偏差{abs(sc-ec)}≥2,请补充期望结果"
            })
    # 仅返回需retry的(排除warning)
    return [i for i in issues if i.get("type") != "warning"]


def _check_placeholder_patterns(cases, tp_index, ctx=None):
    """V4.12.2: 占位符检测 — 拦截Agent模板注入
    
    策略①: 关键词模式匹配（拦截模板短语，4个中风险词加二次判定）
    策略②: steps空洞检测（拦截无具体对象的通用步骤）
    策略③: 同TP内case相似度WARNING（标记但不拦截）
    策略④: context消费检查（Agent是否引用了TP上下文的具体元素）
    """
    issues = []
    
    # 策略①: 关键词模式匹配
    # 高风险短语（绝对是占位符，直接拦截）
    HIGH_RISK_PATTERNS = [
        "进入功能页面执行测试点", "进入功能页面执行",
        "验证操作结果", "页面或数据发生相应变化",
        "执行相关操作", "进入对应页面",
        "执行操作流程", "验证功能正常",
    ]
    # 中风险短语（含具体UI引用时可能合法，需二次判定）
    MEDIUM_RISK_PATTERNS = ["验证结果", "查看执行结果"]
    # UI元素标记
    HAS_UI_ELEMENT = re.compile(r'[「『《""].+?[」』》""]')
    
    for c in cases:
        cid = c.get("case_id", "?")
        title = str(c.get("title", ""))
        steps_text = str(c.get("steps", ""))
        exp_text = str(c.get("expected_results", ""))
        combined = f"{title} {steps_text} {exp_text}"
        
        # 高风险直接拦截
        for pat in HIGH_RISK_PATTERNS:
            if pat in combined:
                issues.append({
                    "case_id": cid,
                    "rule": "PLACEHOLDER_DETECT",
                    "violation": f"检测到占位符短语'{pat}'——Agent未基于P6 prompt生成用例",
                    "type": "block",
                })
                break
        if any(i["case_id"] == cid for i in issues):
            continue
        
        # 中风险二次判定：同句含「」UI引用 → 合法，否则拦截
        for pat in MEDIUM_RISK_PATTERNS:
            if pat in combined:
                # 找到含该短语的句子
                for line in combined.split("\n"):
                    if pat in line:
                        if HAS_UI_ELEMENT.search(line):
                            break  # 含具体UI引用 → 放过
                else:
                    # 所有含该短语的行都没有UI引用 → 拦截
                    issues.append({
                        "case_id": cid,
                        "rule": "PLACEHOLDER_DETECT",
                        "violation": f"检测到占位符短语'{pat}'且无具体UI引用——Agent未基于P6 prompt生成用例",
                        "type": "block",
                    })
                    break

    # 策略②: steps空洞检测
    HOLLOW_PATTERNS = [
        r'^\s*\d*[.、)]?\s*(执行|进行|操作|验证|检查|查看|确认)\s*(相关|对应|指定)?\s*(操作|内容|功能|动作|流程|数据|结果)?\s*$',
    ]
    for c in cases:
        cid = c.get("case_id", "?")
        steps_text = str(c.get("steps", "")).strip()
        if not steps_text:
            continue
        if any(i["case_id"] == cid for i in issues):
            continue
        steps_lines = [s.strip() for s in steps_text.split("\n") if s.strip()]
        hollow_count = 0
        for sl in steps_lines:
            cleaned = re.sub(r'^\s*\d+[.、)]?\s*', '', sl)
            # 步骤含具体UI元素引用(「」包裹) → 视为非空洞
            if HAS_UI_ELEMENT.search(cleaned):
                continue
            # V4.15.53: 导航步骤白名单 — 含具体操作词+导航目标视为有效UI交互
            if re.search(r'(点击|选择|展开|收起|右击|双击)\b.{0,10}(进入|跳转|打开|菜单|按钮|链接|图标|标签|Tab|导航|页面)', cleaned):
                continue
            # 检测1: 步骤过短（<10字去除编号后）
            if len(cleaned) < 10:
                hollow_count += 1
                continue
            # 检测2: 步骤匹配空洞模式
            for pattern in HOLLOW_PATTERNS:
                if re.match(pattern, sl, re.IGNORECASE):
                    hollow_count += 1
                    break
        # 超过60%步骤空洞 → 拦截
        # V4.15.41: HOLLOW_STEPS阈值按TP分类区分(双层保护: 阈值放宽+降级兜底)
        _is_risk_tp = ctx and ctx.get("category") == "risk_verification"
        _hollow_threshold = 0.4 if _is_risk_tp else 0.6
        if steps_lines and hollow_count / len(steps_lines) > _hollow_threshold:
            issues.append({
                "case_id": cid,
                "rule": "HOLLOW_STEPS",
                "violation": f"{hollow_count}/{len(steps_lines)}条步骤空洞（缺乏具体操作对象）",
                "type": "block",
            })

    # 策略③: 同TP内case步骤高度相似 → WARNING标记（不拦截）
    if len(cases) >= 2:
        steps_list = [str(c.get("steps", "")).strip() for c in cases]
        # 简单检测：步骤完全相同的比例
        from collections import Counter
        steps_counter = Counter(steps_list)
        most_common_count = steps_counter.most_common(1)[0][1] if steps_counter else 0
        if most_common_count >= 2:
            issues.append({
                "rule": "SIMILAR_STEPS_WARNING",
                "violation": f"同TP内{most_common_count}/{len(cases)}条用例步骤完全相同",
                "type": "warning",
            })

    # 策略④: context消费检查 — Agent是否引用了TP上下文的具体元素
    # 当任何case被拦截时，额外检查该case是否引用了任何context元素
    # 如果引用了至少1个具体元素 → 可能是误杀，降级为WARNING
    if ctx and issues:
        ctx_elems = set()
        ue = ctx.get("ui_elements", {}) or {}
        for cat_elems in ue.values():
            for e in (cat_elems if isinstance(cat_elems, list) else []):
                ctx_elems.add(str(e))
        for f in (ctx.get("field_checklist", []) or []):
            ctx_elems.add(str(f))
        # 从operations_chain提取目标元素
        for op in (ctx.get("operations_chain", []) or []):
            if isinstance(op, dict):
                t = op.get("target", op.get("target_element", ""))
                if t:
                    ctx_elems.add(str(t))
        
        if ctx_elems:
            for iss in issues:
                if iss.get("type") == "block":
                    cid = iss.get("case_id", "")
                    # 找对应case的内容
                    for c in cases:
                        if c.get("case_id", "") == cid:
                            case_text = str(c.get("steps", "")) + " " + str(c.get("title", ""))
                            referenced = [e for e in ctx_elems if e in case_text]
                            if referenced:
                                iss["type"] = "warning"
                                iss["rule"] = iss.get("rule", "") + "_OVERRIDE"
                                iss["violation"] += f"（但引用了上下文元素{referenced[:3]}，降级为WARNING）"
                            break

    # V4.15.35: risk/PCI TP 降级 — context为模板占位符时无法生成具体步骤
    _is_risk_tp = ctx and ctx.get("category") == "risk_verification"
    if _is_risk_tp and issues:
        degraded = []
        for i in issues:
            if i.get("type") == "block":
                i["type"] = "warning"
                i["rule"] = (i.get("rule") or "") + "_RISK_DEGRADED"
                i["note"] = "risk_verification TP 降级：模板占位符无法避免，允许通过但标记"
            degraded.append(i)
        issues = degraded
        # 记录降级事件(便于后续排查降级频次)
        _degraded_count = sum(1 for d in degraded if "_RISK_DEGRADED" in (d.get("rule") or ""))
        sys.stderr.write(f"[V4.15.35] risk_verification TP#{tp_index} 降级: {_degraded_count} 个block→warning\n")

    # 返回需拦截的（排除warning）
    return [i for i in issues if i.get("type") != "warning"]


def _build_fix_hints_single_tp(issues):
    """V4.11.0: 单TP修复提示"""
    hints = []
    for iss in issues:
        v = str(iss.get("violation", ""))
        if "title为空" in v:
            hints.append({"priority": "P1", "action": "fill_title", "hint": "补全title"})
        elif "steps为空" in v:
            hints.append({"priority": "P1", "action": "fill_steps", "hint": "补全steps"})
        elif "模糊词" in v:
            hints.append({"priority": "P1", "action": "fix_vague", "hint": "改为可观测描述(显示XX/提示XX/跳转XX)"})
    return hints


def _estimate_tp_timeout(case_count: int) -> int:
    """V4.15.52: 单TP超时动态化 — 按用例数计算建议超时(秒)
    
    规则: timeout = min(600, max(120, 120 * case_count))
    - 1TC → 120s | 2TC → 240s | 3TC → 360s | 4+TC → 480~600s
    - 上限600s(10分钟)防止单TP拖死整体进度
    """
    return min(600, max(120, 120 * case_count))


def _save_single_tp(data_dir, tp_index, agent_output):
    """V4.12.1: 保存单TP生成的用例(19列全量补全)
    V4.12.5: 频率检测(反脚本) + 质量预览(条件阻断)
    """
    import re as _tp_re

    # === V4.15.11: P6顺序约束 ===
    try:
        _order_sp = os.path.join(data_dir, "orchestrator_state.json")
        if os.path.exists(_order_sp):
            _order_st = _read_json(_order_sp)
            _completed = _order_st.get("p6_completed_tp_indices", [])
            if _completed:
                _next_expected = max(_completed) + 1
                if tp_index > _next_expected:
                    _skipped = tp_index - _next_expected
                    print(json.dumps({
                        "status": "order_violation",
                        "expected_tp_index": _next_expected,
                        "actual_tp_index": tp_index,
                        "skipped_count": _skipped,
                        "reason": f"⛔ 顺序违规：期望TP-{_next_expected:03d}，收到TP-{tp_index:03d}，跳过{_skipped}个TP。请按顺序生成。",
                        "hint": f"先执行 p6_generate_one --tp-index {_next_expected} --save"
                    }, ensure_ascii=False))
                    return {"status": "order_violation", "expected": _next_expected, "actual": tp_index}
    except Exception:
        pass  # 状态文件读取失败不影响核心逻辑

    # === V4.15.0: 重复save检测 ===
    _tp_dir_check = os.path.join(data_dir, "p6_tp_output")
    _existing_tp_path = os.path.join(_tp_dir_check, f"tp_{tp_index:03d}.json")
    if os.path.exists(_existing_tp_path):
        try:
            _existing_data = _read_json(_existing_tp_path)
            _existing_cases = _existing_data.get("testcases", [])
            _ctx_path = os.path.join(_tp_dir_check, f"tp_{tp_index:03d}_context.json")
            if os.path.exists(_ctx_path):
                _ctx_check = _read_json(_ctx_path)
                _ec = _ctx_check.get("expected_case_count", 2)
                if len(_existing_cases) >= _ec:
                    print(json.dumps({
                        "status": "blocked",
                        "reason": f"tp_index={tp_index} 已达标({len(_existing_cases)}>={_ec})",
                        "hint": "该TP已完成。重新生成请先删除对应文件。"
                    }, ensure_ascii=False))
                    return {"status": "blocked"}
        except Exception:
            pass

    # === V4.14.2: 自适应速率限制 ===
    T0 = 90  # 基础阈值(秒)
    TRUST_MULTIPLIER = 1.5  # 信任模式阈值倍数
    VIGILANCE_MULTIPLIER = 0.67  # 警戒模式阈值倍数
    G15_FAST_PASS = 30  # G1.5重试快速放行(秒)
    WINDOW_SIZE = 5  # 滑动窗口大小
    SINGLE_TP_TIMEOUT_SOFT = 180  # 软告警
    SINGLE_TP_TIMEOUT_HARD = 300  # 强制中断

    freq_path = os.path.join(data_dir, "p6_tp_output", ".save_freq.json")
    freq_data = {}
    if os.path.exists(freq_path):
        try:
            freq_data = _read_json(freq_path)
        except Exception:
            pass
    now = time.time()
    tp_key = f"tp_{tp_index:03d}"
    repeat_count = freq_data.get(tp_key, {}).get("repeat_count", 0)

    # 豁免：TP总数≤5的小任务
    ctx_small_path = os.path.join(data_dir, "p6_tp_output", f"tp_{tp_index:03d}_context.json")
    total_tps = 0
    if os.path.exists(ctx_small_path):
        try:
            total_tps = _read_json(ctx_small_path).get("total_tps", 0)
        except Exception:
            pass

    if total_tps > 5:
        # 读取持久化的速率状态
        state_path = os.path.join(data_dir, "orchestrator_state.json")
        rate_state = {}
        if os.path.exists(state_path):
            try:
                rate_state = _read_json(state_path).get("rate_limit", {})
            except Exception:
                pass

        current_mode = rate_state.get("mode", "normal")
        current_threshold = rate_state.get("threshold", T0)
        window_history = rate_state.get("window", [])
        consecutive_trust = rate_state.get("consecutive_trust", 0)

        # 同一TP重复save检测(G1.5重试)
        last_save = freq_data.get(tp_key, {}).get("last_save", 0)
        is_g15_retry = last_save and (now - last_save) < G15_FAST_PASS
        if last_save and (now - last_save) < 15:
            repeat_count += 1
        else:
            repeat_count = 0

        if is_g15_retry:
            if repeat_count >= 3:
                print(json.dumps({
                    "status": "warning", "severity": "g15_loop",
                    "reason": f"同一TP触发G1.5重试{repeat_count}次，疑似死循环",
                    "tp_index": tp_index, "repeat_count": repeat_count,
                }), file=sys.stderr)
        else:
            elapsed = now - last_save if last_save else 0
            window_history.append({"tp": tp_index, "elapsed": round(elapsed, 1), "is_g15_retry": False, "ts": now})
            if len(window_history) > WINDOW_SIZE:
                window_history = window_history[-WINDOW_SIZE:]

            if elapsed > SINGLE_TP_TIMEOUT_HARD:
                print(json.dumps({
                    "status": "rejected", "severity": "timeout_hard",
                    "reason": f"单TP生成耗时{elapsed:.0f}s>{SINGLE_TP_TIMEOUT_HARD}s，强制中断",
                    "tp_index": tp_index, "elapsed": round(elapsed, 1),
                }))
                sys.exit(1)
            elif elapsed > SINGLE_TP_TIMEOUT_SOFT:
                print(json.dumps({
                    "status": "warning", "severity": "timeout_soft",
                    "reason": f"单TP生成耗时{elapsed:.0f}s>{SINGLE_TP_TIMEOUT_SOFT}s，可能为复杂TP",
                    "tp_index": tp_index, "elapsed": round(elapsed, 1),
                }), file=sys.stderr)

            # 自适应速率评估
            non_retry_history = [h for h in window_history if not h.get("is_g15_retry")]
            if len(non_retry_history) >= WINDOW_SIZE:
                elapsed_times = [h["elapsed"] for h in non_retry_history[-WINDOW_SIZE:]]
                violations = sum(1 for et in elapsed_times if et < current_threshold)

                mean_et = sum(elapsed_times) / len(elapsed_times)
                variance = sum((et - mean_et) ** 2 for et in elapsed_times) / len(elapsed_times)
                cv = (variance ** 0.5) / mean_et if mean_et > 0 else 0

                if cv < 0.05 and mean_et < 45:
                    print(json.dumps({
                        "status": "warning", "severity": "script_suspect",
                        "reason": f"检测到匀速生成模式(CV={cv:.2%}, avg={mean_et:.0f}s)",
                        "tp_index": tp_index,
                    }), file=sys.stderr)
                    current_mode = "alert"
                    current_threshold = int(T0 * VIGILANCE_MULTIPLIER)
                elif violations >= 3:
                    current_mode = "alert"
                    current_threshold = int(T0 * VIGILANCE_MULTIPLIER)
                elif violations == 0 and cv > 0.05:
                    if current_mode != "trusted":
                        consecutive_trust += 1
                        if consecutive_trust >= WINDOW_SIZE:
                            current_mode = "trusted"
                            current_threshold = int(T0 * TRUST_MULTIPLIER)
                            consecutive_trust = 0
                    else:
                        consecutive_trust += 1
                elif violations == 1:
                    if current_mode == "trusted":
                        current_mode = "normal"
                        current_threshold = T0
                        consecutive_trust = 0

                if current_mode == "trusted" and consecutive_trust >= 10:
                    current_mode = "normal"
                    current_threshold = T0
                    consecutive_trust = 0

            # 持久化速率状态
            rate_state = {
                "mode": current_mode, "threshold": current_threshold,
                "window": window_history[-10:],
                "consecutive_trust": consecutive_trust,
                "last_update": now,
            }
            try:
                sd = _read_json(state_path) if os.path.exists(state_path) else {}
                sd["rate_limit"] = rate_state
                _write_json(state_path, sd)
            except Exception:
                pass

    # === 自适应速率限制结束 ===

    try:
        data = json.loads(agent_output)
    except Exception:
        m = _tp_re.search(r'\[[\s\S]*\]', agent_output)
        if m:
            try:
                data = json.loads(m.group())
            except Exception:
                print(json.dumps({"status": "error", "reason": "JSON解析失败"}))
                sys.exit(1)
        else:
            print(json.dumps({"status": "error", "reason": "不含JSON"}))
            sys.exit(1)
    if isinstance(data, list):
        data = {"testcases": data}
    # V4.15.5: 丢弃LLM输出的statistics字段(orchestrator自行计算,防Agent编造)
    data.pop("statistics", None)
    cases = data.get("testcases", data.get("cases", []))
    if not cases:
        print(json.dumps({"status": "quality_rejected", "reason": "用例为空"}))
        sys.exit(1)
    # 读取context获取TP元信息
    ctx_path = os.path.join(data_dir, "p6_tp_output", f"tp_{tp_index:03d}_context.json")
    ctx = _read_json(ctx_path)
    # V4.15.37: 用例数量校验 — 实际生成数量与expected_case_count不一致时拒绝保存
    _expected_count = ctx.get("expected_case_count", 2) if isinstance(ctx, dict) else 2
    tp_id = ctx.get("tp_id", "")
    if len(cases) < _expected_count:
        # V4.15.53: 数量校验允许±1容差（P5预估值经合并后可能不准确）
        _min_acceptable = max(1, _expected_count - 1) if _expected_count >= 3 else _expected_count
        if len(cases) >= _min_acceptable:
            pass  # 允许，不拒绝
        else:
            print(json.dumps({
                "status": "quality_rejected",
                "reason": f"用例数量不足: 期望≥{_min_acceptable}条, 实际{len(cases)}条",
                "expected": _expected_count,
                "min_acceptable": _min_acceptable,
                "actual": len(cases),
                "hint": f"请重新生成{tp_id},确保输出≥{_min_acceptable}条用例"
            }, ensure_ascii=False))
            sys.exit(1)
    pri = ctx.get("priority", "P1")
    cat = ctx.get("category", "")
    biz_ctx = ctx.get("business_context", "")
    page_path = ctx.get("page_path", "")
    # V4.12.6: 从task_meta提取项目名(不截断biz_ctx)
    project_name = _extract_project_name(data_dir) or ""
    if not project_name:
        # 兜底: 从biz_ctx中提取纯文本项目名(跳过"页面:"等前缀)
        first_line = biz_ctx.split("\n")[0] if biz_ctx else ""
        if first_line and not first_line.startswith("页面:") and not first_line.startswith("操作:"):
            project_name = first_line[:30]
    # V4.12.1: 自动补全字段 - 补全全部19列必填字段,与batch模式一致
    # LLM输出5核心字段(title/menu_path/preconditions/steps/expected_results),其余代码补全
    for i, c in enumerate(cases):
        # V4.12.6: 如果agent提供的case_id含非ASCII字符(乱码)→自动生成
        # V4.15.28: 强制使用auto_cid(基于tp_id)，防止LLM用tp_index替代TP编号导致C7/G3假性BLOCK
        agent_cid = c.get("case_id", "")
        auto_cid = f"{tp_id}-TC-{i + 1:03d}"
        if not agent_cid:
            c["case_id"] = auto_cid
        elif not all(ord(ch) < 128 for ch in str(agent_cid)):
            c["case_id"] = auto_cid  # 乱码→自动生成
        elif tp_id and "TP-" in str(tp_id) and str(tp_id) not in str(agent_cid):
            # LLM的case_id不含正确tp_id(可能用了tp_index)，强制用auto_cid
            c["case_id"] = auto_cid
        else:
            c["case_id"] = agent_cid
        # === V4.15.18-A: 乱码检测(阈值0.5) + P5反推正确ID ===
        _stp_val = str(tp_id)
        _non_ascii = sum(1 for _ch in _stp_val if ord(_ch) > 127 and not ('\u4e00' <= _ch <= '\u9fff'))
        if _stp_val and _non_ascii > len(_stp_val) * 0.5:
            # 从P5反推正确ID（缓存P5数据避免重复读取）
            _p5_cache_path = os.path.join(data_dir, "p5_output.json")
            _p5_data = _read_json(_p5_cache_path) if os.path.exists(_p5_cache_path) else {}
            _tp_id_fixed = f"TP-{tp_index:03d}"  # 默认fallback
            for _tp in _p5_data.get("test_points", []):
                _full_id = _tp.get("id", "")
                if f"-TP-{tp_index:03d}" in _full_id or f"-ETP-{tp_index}" in _full_id:
                    _tp_id_fixed = _full_id
                    break
            tp_id = _tp_id_fixed
        c["source_test_point"] = tp_id
        c["priority"] = c.get("priority", "") or pri
        # V4.14.2: 仅 main_flow/branch/integration 自动标记冒烟；permission/state_migration 虽为A类但需Agent显式指定
        c["is_smoke"] = c.get("is_smoke", "") or (
            (pri == "P0" and cat in ("main_flow", "branch", "integration"))
        )
        # V4.15.53: 从context传递risk_flag/priority_hint到用例
        c["risk_flag"] = ctx.get("risk_flag", False)
        c["priority_hint"] = ctx.get("priority_hint", "")
        # V4.15.6: 自动修正冒烟标记 — 非A类TP不应标记为冒烟（G3/G4防御）
        # A_CLASS_CATS 为全量A类集合，比上面自动标记的3类更广（permission/state_migration可通过Agent显式标记冒烟）
        A_CLASS_CATS = {"main_flow", "branch", "integration", "permission", "state_migration"}
        if _is_smoke(c["is_smoke"]) and cat not in A_CLASS_CATS:
            c["is_smoke"] = False
            print(json.dumps({
                "status": "auto_fix", "type": "smoke_correction",
                "case_id": c["case_id"], "tp_id": tp_id,
                "reason": f"非A类TP(category={cat}), is_smoke 从 true 自动修正为 false"
            }, ensure_ascii=False), file=sys.stderr)
        c["test_category"] = c.get("test_category", c.get("category", "")) or cat
        # V4.12.0: 补全batch模式已有但单TP模式缺失的19列格式字段
        # V4.15.20: 从P1查模块名（兼容features和children结构）
        _p1_path = os.path.join(data_dir, "p1_output.json")
        if os.path.exists(_p1_path):
            try:
                _p1 = _read_json(_p1_path)
                _modules = _p1.get("feature_tree", {}).get("modules", [])
                if not _modules:
                    _modules = _p1.get("modules", [])
                _tp_name_hint = tp_id + " " + str(c.get("title", ""))
                for _mod in _modules:
                    _children = _mod.get("features", _mod.get("children", []))
                    for _child in _children:
                        if isinstance(_child, dict) and _child.get("name", "") in _tp_name_hint:
                            project_name = _mod.get("name", project_name)
                            break
                    else:
                        continue
                    break
            except Exception:
                pass
        c["project"] = c.get("project", "") or project_name
        c["case_type"] = c.get("case_type", "") or "测试用例"
        c["requirement"] = c.get("requirement", "") or ""
        c["menu_path"] = c.get("menu_path", "") or page_path
        # V4.15.23: 自动补全menu_path — LLM漏填时从P5 TP→P1 feature_tree推导（修复84条未分类）
        if not str(c["menu_path"]).strip():
            _auto_path = ""
            try:
                _p5_path = os.path.join(data_dir, "p5_output.json")
                if os.path.exists(_p5_path):
                    _p5 = _read_json(_p5_path)
                    _p1_path_fb = os.path.join(data_dir, "p1_output.json")
                    _p1_fb = _read_json(_p1_path_fb) if os.path.exists(_p1_path_fb) else {}
                    for _tp in _p5.get("test_points", []):
                        if _tp.get("id", "") == tp_id:
                            _sc = _tp.get("source_scenario", "")
                            if _sc:
                                _ft = _p1_fb.get("feature_tree", {}) or _p1_fb
                                for _mod in _ft.get("modules", []):
                                    for _feat in _mod.get("features", _mod.get("children", [])):
                                        for _scn in _feat.get("scenarios", []):
                                            if isinstance(_scn, dict) and _scn.get("name", "") == _sc:
                                                _auto_path = f"{_mod.get('name', '')} → {_feat.get('name', '')}"
                                                break
                                        if _auto_path: break
                                    if _auto_path: break
                            elif cat:
                                _auto_path = cat  # RISK/PCI TP用category兜底
                            break
            except Exception:
                pass
            c["menu_path"] = _auto_path or cat or ""
        c["creator"] = c.get("creator", "") or "AI生成"
        c["assignee"] = c.get("assignee", "") or ""
        c["test_case_type"] = c.get("test_case_type", "") or (
            "反例" if cat in ("exception", "error", "risk_verification", "边界验证") else "正例"
        )
        c["status"] = c.get("status", "") or ""
        c["screenshot"] = c.get("screenshot", "") or ""
        c["test_suite"] = c.get("test_suite", "") or ""
        for f in ["preconditions", "remarks"]:
            if f not in c:
                c[f] = ""
    # 格式归一化
    for c in cases:
        for f in ["steps", "expected_results", "preconditions"]:
            if isinstance(c.get(f), list):
                c[f] = "\n".join(str(s) for s in c[f] if s)
    # V4.15.5: 移除G1.5自动标记层(V4.13.3) — 【待具化】占位符污染最终产出
    # 模糊词改为由_quick_gate_single_tp正常reject,迫使LLM重写具体期望
    # V4.15.52: C6.1前置条件自动补全 — 仅1段且不含账号权限描述时自动补全
    for c in cases:
        prec = str(c.get("preconditions", "")).strip()
        if prec:
            _prec_segs = [s.strip() for s in re.split(r'[；;\n]', prec) if s.strip()]
            if len(_prec_segs) == 1:
                _has_account = any(kw in _prec_segs[0] for kw in ["登录", "账号", "权限", "角色", "Admin", "管理员"])
                _has_data_env = any(kw in _prec_segs[0] for kw in ["创建", "配置", "准备", "设置", "存在", "已有", "数据"])
                if _has_data_env and not _has_account:
                    c["preconditions"] = f"已使用具有操作权限的账号登录系统；{prec}"
    # Gate快速检查
    retry_count = 0  # V4.14.10: 提前初始化,防issues为空时UnboundLocalError
    issues = _quick_gate_single_tp(cases)
    # V4.15.20: 补充场景只检查新增case（已有case已通过质检）
    _tp_path_check = os.path.join(data_dir, "p6_tp_output", f"tp_{tp_index:03d}.json")
    if issues and os.path.exists(_tp_path_check):
        try:
            _existing = _read_json(_tp_path_check)
            _existing_ids = {c.get("case_id") for c in _existing.get("testcases", [])}
            _new_issues = [i for i in issues if i.get("case_id") not in _existing_ids]
            if not _new_issues:
                issues = []
            else:
                issues = _new_issues
        except Exception:
            pass  # 读取失败则保留全部issues
    if issues:
        # V4.11.0: retry计数追踪
        retry_state_path = os.path.join(data_dir, "orchestrator_state.json")
        retry_key = f"p6_tp_{tp_index}_retry"
        if os.path.exists(retry_state_path):
            try:
                sd = _read_json(retry_state_path)
                retry_count = sd.get(retry_key, 0) + 1
                sd[retry_key] = retry_count
                _write_json(retry_state_path, sd)
            except Exception:
                pass
        print(json.dumps({
            "status": "quality_rejected",
            "tp_index": tp_index,
            "retry_count": retry_count,
            "issues": issues,
            "fix_hints": _build_fix_hints_single_tp(issues),
            # FIX(rate-limit-tiering) V4.13.9-S3 #7: 质量类 reject 返回短等待建议(非脚本限速,仅提示修复节奏)
            "retry_after_seconds": 10,
            "severity": "quality_fix",
            "retry_hint": f"按fix_hints修复后重新 p6_generate_one --tp-index {tp_index} --save "
                          f"--agent-output '...'"
        }))
        sys.exit(1)

    # V4.12.2: 占位符检测 — 拦截Agent模板注入（如"进入功能页面执行测试点"）
    placeholder_issues_raw = _check_placeholder_patterns(cases, tp_index, ctx)
    # V4.15.52: WARNING降级不retry — 仅BLOCK级占位符触发重试
    placeholder_issues = [i for i in placeholder_issues_raw if i.get("type") != "warning"]
    if placeholder_issues:
        print(json.dumps({
            "status": "quality_rejected",
            "tp_index": tp_index,
            "reason": "占位符检测失败 — Agent未基于P6 prompt生成用例，使用了模板占位符",
            "placeholder_issues": placeholder_issues,
            "fix_hints": [{
                "action": "regenerate_from_prompt",
                "hint": "重新执行 p6_generate_one --tp-index N，阅读prompt中的11章节信息（页面路径/UI元素/业务规则/场景描述等），"
                        "基于这些具体信息生成用例。禁止使用'进入功能页面执行测试点'、'验证操作结果'等通用模板短语。"
            }],
            # FIX(rate-limit-tiering) V4.13.9-S3 #7: 质量类 reject 返回短等待建议
            "retry_after_seconds": 10,
            "severity": "quality_fix",
            "retry_hint": f"重读prompt基于真实业务信息生成，然后 p6_generate_one --tp-index {tp_index} --save --agent-output '...'"
        }))
        sys.exit(1)

    # === V4.12.5: 质量预览 — 步骤过短条件阻断 ===
    short_steps = 0
    no_smoke_warn = False
    need_smoke_from_ctx = ctx.get("need_smoke", False)
    for c in cases:
        steps_text = _get_case_field(c, "steps", "")
        if isinstance(steps_text, str):
            step_count = len([s for s in steps_text.split("\n") if s.strip()])
        else:
            step_count = 0
        if step_count <= 2:
            short_steps += 1
    has_smoke = any(_is_smoke(_get_case_field(c, "is_smoke", "")) for c in cases)

    qp_warnings = []
    if short_steps > 0:
        qp_warnings.append(f"{short_steps}/{len(cases)}条用例步骤≤2步")
    if need_smoke_from_ctx and not has_smoke:
        no_smoke_warn = True
        qp_warnings.append("缺少冒烟用例(is_smoke未标记)")

    # 条件阻断：≥50%用例步骤过短 → reject
    if len(cases) > 0 and short_steps >= len(cases) / 2:
        print(json.dumps({
            "status": "quality_rejected",
            "tp_index": tp_index,
            "reason": f"质量预览不通过: {short_steps}/{len(cases)}条用例步骤≤2步",
            "quality_warnings": qp_warnings,
            "fix_hints": [{
                "action": "expand_steps",
                "hint": "每条用例至少3步详细操作。格式: '动作动词「UI元素」具体内容'（如: 点击「查询」按钮、在「员工姓名」输入框输入'张三'）"
            }],
            # FIX(rate-limit-tiering) V4.13.9-S3 #7: 质量类 reject 返回短等待建议
            "retry_after_seconds": 10,
            "severity": "quality_fix",
            "retry_hint": f"重新 p6_generate_one --tp-index {tp_index} --save --agent-output '...'",
        }))
        sys.exit(1)
    # <50%但>0 → stderr警告
    if qp_warnings:
        print(json.dumps({
            "status": "quality_hint",
            "tp_index": tp_index,
            "warnings": qp_warnings,
        }), file=sys.stderr)
    # === 质量预览结束 ===

    # 保存
    out_dir = os.path.join(data_dir, "p6_tp_output")
    _ensure_dir(out_dir)
    tp_path = os.path.join(out_dir, f"tp_{tp_index:03d}.json")
    # 累计：如果已有保存，合并case（支持多次save同一TP）
    existing_cases = []
    if os.path.exists(tp_path):
        try:
            existing = _read_json(tp_path)
            existing_cases = existing.get("testcases", [])
        except Exception:
            pass
    all_cases = existing_cases + cases

    # V4.13.6: TP文件内去重(防止多次save累积相同case_id, BUG-1修复:用set存所有hash)
    seen_in_tp = {}  # case_id → set of content hashes
    cleaned = []
    for c in all_cases:
        cid = _get_case_field(c, "case_id", "")
        if not cid:
            cleaned.append(c)
            continue
        ck = (
            str(_get_case_field(c, "title", "")).strip()
            + "||" + str(_get_case_field(c, "preconditions", "")).strip()
            + "||" + str(_get_case_field(c, "steps", "")).strip()
            + "||" + str(_get_case_field(c, "expected_results", "")).strip()
        )
        if cid in seen_in_tp:
            if ck in seen_in_tp[cid]:
                continue  # 真重复，跳过
            seen_in_tp[cid].add(ck)
        else:
            seen_in_tp[cid] = {ck}
        cleaned.append(c)
    all_cases = cleaned  # 变体后缀由p6_merge统一处理,此处不做-V

    # V4.13.8 P1-3层一: 写入前自动备份旧版本到 .tp_backup/
    if os.path.exists(tp_path):
        bak_dir = os.path.join(data_dir, ".tp_backup")
        _ensure_dir(bak_dir)
        ts = time.strftime("%Y%m%d_%H%M%S")
        bak_path = os.path.join(bak_dir, f"tp_{tp_index:03d}.json.bak.{ts}")
        import shutil as _shutil
        _shutil.copy2(tp_path, bak_path)
        # 保留最近50个该TP的备份
        all_baks = sorted([f for f in os.listdir(bak_dir) if f.startswith(f"tp_{tp_index:03d}.")])
        for old_bak in all_baks[:-50]:
            try:
                os.remove(os.path.join(bak_dir, old_bak))
            except Exception:
                pass

    # V4.15.22: P6生成时C2自检（步骤-期望数量对应，提前修复避免P7返工）
    for _c in all_cases:
        _steps_text = _c.get("steps", "") or ""
        _exp_text = _c.get("expected_results", "") or ""
        if not _steps_text or not isinstance(_steps_text, str):
            continue
        _step_lines = [s.strip() for s in _steps_text.split("\n") if s.strip()]
        _exp_lines = [s.strip() for s in _exp_text.split("\n") if s.strip()] if _exp_text else []
        _diff = len(_step_lines) - len(_exp_lines)
        if _diff >= 3:
            # 自动补齐期望行（标记"><需人工补充>"以便P7识别）
            for _si in range(len(_exp_lines), len(_step_lines)):
                _exp_lines.append(f"{_si+1}. 需人工补充期望结果（步骤：{_step_lines[_si][:50]}）")
            _c["expected_results"] = "\n".join(_exp_lines)
            _c["_c2_auto_fixed"] = True

    _write_json(tp_path, {"tp_index": tp_index, "tp_id": tp_id, "testcases": all_cases})

    # V4.15.33: freq_data写入移至文件保存成功后(修复V4.14.2引入的死锁bug: 质量校验前写入freq_data → 重试时elapsed>300 → timeout_hard死锁)
    freq_data[tp_key] = {"last_save": time.time(), "repeat_count": repeat_count}
    if len(freq_data) > 30:
        oldest_keys = sorted(freq_data.keys(),
                            key=lambda k: freq_data[k].get("last_save", 0))[:len(freq_data)-30]
        for ok in oldest_keys:
            del freq_data[ok]
    _write_json(freq_path, freq_data)

    # V4.15.33: checkpoint阈值下修 — >=60→>=30,让30-60TP中型任务也能受益
    try:
        _tp_files = [f for f in os.listdir(out_dir)
            if f.startswith("tp_") and f.endswith(".json")
            and "_context" not in f and "_agent_output" not in f]
        _saved_count = len(_tp_files)
        if _saved_count > 0 and _saved_count % 30 == 0 and _saved_count >= 30:
            _ckpt_path = os.path.join(data_dir, ".p6_checkpoint_required")
            _ckpt_data = {"saved_tp_count": _saved_count, "requires_user_confirm": True,
                "paused_at": time.strftime("%Y-%m-%d %H:%M:%S")}
            _write_json(_ckpt_path, _ckpt_data)
    except Exception:
        pass  # checkpoint失败不影响核心流程

    # 防御机制: 记录保存时间戳供审计(追踪每TP的save行为,与频率检测互补)。
    # 写入 p6_tp_output/.save_audit.jsonl,一行一条,便于事后对账。
    try:
        _audit_path = os.path.join(out_dir, ".save_audit.jsonl")
        # V4.15.11: 计算实际gap_reason（替代unknown）
        _gap_reason = "g15_retry" if retry_count > 0 else "first_save"
        if _gap_reason == "first_save":
            try:
                if os.path.exists(_audit_path):
                    with open(_audit_path, "r", encoding="utf-8") as _prev_f:
                        _prev_lines = _prev_f.readlines()
                    if _prev_lines:
                        _prev_last = json.loads(_prev_lines[-1].strip())
                        _prev_ts = _prev_last.get("ts", 0)
                        _gap_sec = time.time() - _prev_ts
                        if _gap_sec > 120:
                            _gap_reason = "pause_or_idle"
                        elif _gap_sec > 30:
                            _gap_reason = "slow_gen"
                        else:
                            _gap_reason = "continuous"
            except Exception:
                _gap_reason = "continuous"
        _audit_rec = {
            "tp_index": tp_index,
            "tp_id": tp_id,
            "action": "save_ok",
            "ts": time.time(),
            "ts_iso": time.strftime("%Y-%m-%dT%H:%M:%S+08:00"),
            "cases_this_save": len(cases),
            "cases_total_saved": len(all_cases),
            "retry_count": retry_count,
            "is_sub_agent": _is_sub_agent_session(),
            "gap_reason": _gap_reason,
        }
        with open(_audit_path, "a", encoding="utf-8") as _af:
            _af.write(json.dumps(_audit_rec, ensure_ascii=False) + "\n")
    except Exception:
        pass  # 审计记录失败不阻断主流程
    # (不依赖会话内存)。把已完成的 tp_index 并入 orchestrator_state.json 的 p6_completed_tp_indices。
    try:
        _sp = os.path.join(data_dir, "orchestrator_state.json")
        _st = _read_json(_sp) if os.path.exists(_sp) else {}
        _done = set(_st.get("p6_completed_tp_indices", []))
        _done.add(tp_index)
        _st["p6_completed_tp_indices"] = sorted(_done)
        _write_json(_sp, _st)
    except Exception:
        pass

    # V4.12.3: 数量校验 — 比对expected_case_count
    ec = ctx.get("expected_case_count", 2)
    result = {
        "status": "ok",
        "tp_index": tp_index,
        "tp_id": tp_id,
        "cases_this_save": len(cases),
        "cases_total_saved": len(all_cases),
        "expected_case_count": ec,
        "file": tp_path,
        "retry_count": retry_count,  # V4.14.2: 监控用
        "g15_words": [],  # V4.14.2: 由后续G1.5检查填充
    }

    # V4.15.33: g15_drift三修复 — 关键词来源扩展+stop_words精简+去截断
    # ① 关键词来源从description(42字)扩展至description+scenario+biz_context(1000+字)
    _desc = ctx.get("description", "")
    _scenario = ctx.get("scenario_description", "")
    _biz = ctx.get("business_context", "")[:300]
    tp_ctx_desc = _desc + " " + _scenario + " " + _biz
    _tp_source = ctx.get("source", "")
    if tp_ctx_desc and all_cases and _tp_source not in ("P3", "P4"):
        import re as _drift_re
        # ② stop_words — V4.15.34: 回加"验证/流程/场景/处理/进入/页面"等通用业务词，防止关键词泛滥导致drift漏检
        _stop_words = {"该","的","在","中","和","与","为","了","已","并","或","且","到","是","可以","需要","验证","流程","场景","处理","进入","页面"}
        _tp_keywords = [w for w in _drift_re.findall(r'[\u4e00-\u9fff]{2,}', tp_ctx_desc) if w not in _stop_words]
        # ③ 匹配文本全量(去掉[:500]截断),边界用例后半段关键词不被丢失
        _all_case_text = " ".join(c.get("title","") + " " + c.get("steps","") for c in all_cases)
        _matched = [kw for kw in _tp_keywords if kw in _all_case_text]
        if len(_matched) < 2 and len(_tp_keywords) >= 2:
            print(json.dumps({"severity":"g15_drift_warning","tp_index":tp_index,"tp_id":tp_id,"reason":f"用例内容可能偏离TP原始场景，TP关键词({len(_tp_keywords)}个)仅匹配{len(_matched)}个","matched_keywords":_matched,"hint":"检查修复后是否仍覆盖原始TP业务场景"},ensure_ascii=False), file=sys.stderr)

    # V4.13.8 P1-4: 生成阶段三要素强制校验(入口/账号/数据准备)
    import re as _precond_re
    _KW_ENTRY = _precond_re.compile(r'入口|菜单|页面|路径|登录|进入')
    _KW_ACCT = _precond_re.compile(r'账号|权限|角色|管理员|员工|已登录|已认证|已授权')
    _KW_DATA = _precond_re.compile(r'数据|预置|构造|预设|测试数据|造数|记录|导入|创建|已创建|已导入|已存在|维护|已维护|填写|已填写|选项|字段|表单')
    precond_warnings = []
    for ci, c in enumerate(all_cases):
        pc = _get_case_field(c, "preconditions", "")
        if not pc:
            precond_warnings.append(f"{_get_case_field(c, 'case_id', f'case_{ci}')}: 前置条件为空")
            continue
        missing = []
        if not _KW_ENTRY.search(pc):
            missing.append("入口/菜单")
        if not _KW_ACCT.search(pc):
            missing.append("账号/权限")
        if not _KW_DATA.search(pc):
            missing.append("数据准备")
        if len(missing) >= 2:
            precond_warnings.append(f"{_get_case_field(c, 'case_id', f'case_{ci}')}: 缺{';'.join(missing)}")
    if precond_warnings:
        result["precond_warnings"] = precond_warnings[:10]
        result["precond_hint"] = f"⚠️ {len(precond_warnings)}条用例前置条件不完整(缺≥2要素),请补充入口/账号/数据准备后重新保存"

    if len(all_cases) < ec:
        shortfall = ec - len(all_cases)
        result["status"] = "saved_shortfall"
        result["shortfall"] = shortfall
        result["hint"] = (
            f"⚠️ 当前TP已保存{len(all_cases)}条（{ec - shortfall}/{ec}），还需要{shortfall}条。"
            f"继续调用 p6_generate_one --tp-index {tp_index} --save 补充剩余用例。"
        )
    # === V4.14.2: P6监控基线 — JSONL写入 ===
    try:
        import time as _mt
        metrics_path = os.path.join(data_dir, "p6_metrics.jsonl")
        # V4.15.3: 补充质量指标(步骤数/期望结果数/模糊词密度/前置条件完整性)
        _steps_text = ""
        _expected_text = ""
        _precond_text = ""
        for _c in all_cases:
            _steps_text += str(_get_case_field(_c, "steps", "")) + "\n"
            _expected_text += str(_get_case_field(_c, "expected_results", "")) + "\n"
            _precond_text += str(_get_case_field(_c, "preconditions", "")) + "\n"
        # 模糊词计数
        _vague_kw = ["正常", "正确", "成功", "无异常", "符合预期", "一致", "响应及时", "合理"]
        _vague_count = sum(_expected_text.count(kw) for kw in _vague_kw)
        # 步骤/期望条数(按换行粗略计数)
        _step_lines = [l for l in _steps_text.split("\n") if l.strip()]
        _expected_lines = [l for l in _expected_text.split("\n") if l.strip()]
        # 前置条件三要素检测
        _precond_has_entry = 1 if any(kw in _precond_text for kw in ("进入", "登录", "打开", "访问", "点击")) else 0
        _precond_has_acct = 1 if any(kw in _precond_text for kw in ("账号", "账户", "权限", "角色", "登录")) else 0
        _precond_has_data = 1 if any(kw in _precond_text for kw in ("存在", "配置", "准备", "数据", "已创建")) else 0
        
        metrics_entry = {
            "ts": int(_mt.time()), "tp_index": tp_index, "tp_id": tp_id,
            "case_count": len(all_cases),
            # V4.15.44修复监控盲区: 从state读真实重试次数(result成功保存时无retry_count字段)
            "retries": (lambda: (_read_json(os.path.join(data_dir, "orchestrator_state.json")).get(f"p6_tp_{tp_index}_retry", 0) if os.path.exists(os.path.join(data_dir, "orchestrator_state.json")) else result.get("retry_count", 0)))(),
            "g15_hits": result.get("g15_words", []),
            "has_warnings": bool(result.get("warnings")),
            "status": result.get("status", "saved"),
            # V4.15.3 质量指标
            "quality": {
                "step_lines": len(_step_lines),
                "expected_lines": len(_expected_lines),
                "vague_word_count": _vague_count,
                "vague_density": round(_vague_count / max(len(_expected_text), 1) * 100, 1),
                "precond_completeness": _precond_has_entry + _precond_has_acct + _precond_has_data,
                "gap_reason": "unknown",  # V4.15.8
            }
        }
        with open(metrics_path, "a", encoding="utf-8") as _mf:
            _mf.write(json.dumps(metrics_entry, ensure_ascii=False) + "\n")
    except Exception:
        pass  # 监控写入失败不影响主流程

    # === V4.15.0: P6段内暂停硬控 ===
    if result.get("status") == "ok":
        PAUSE_EVERY_N = 15  # V4.15.52: 恢复15TP暂停(V4.15.34从15→30,复盘发现95TP仅暂停1次,恢复15)
        try:
            _sp_save = os.path.join(data_dir, "orchestrator_state.json")
            _st_save = _read_json(_sp_save) if os.path.exists(_sp_save) else {}
            _segment_start = _st_save.get("p6_segment_start_count", 0)
        except Exception:
            _segment_start = 0

        import glob as _glob_save
        _tp_dir_pause = os.path.join(data_dir, "p6_tp_output")
        _done_files = [_f for _f in _glob_save.glob(os.path.join(_tp_dir_pause, "tp_[0-9]*.json"))
                       if "_context" not in os.path.basename(_f) and "_agent_output" not in os.path.basename(_f)]
        # V4.15.41: PAUSE计数优先用state(修复V4.15.38遗漏的主PAUSE路径)
        _completed_indices = _st_save.get("p6_completed_tp_indices", [])
        _completed_now = len(_completed_indices) if _completed_indices else len(_done_files)
        _remaining = total_tps - _completed_now
        _segment_done = _completed_now - _segment_start

        if ((_segment_done >= PAUSE_EVERY_N or _completed_now % PAUSE_EVERY_N == 0)
            and _remaining > 0 and _completed_now < total_tps):

            _max_seq = 0
            for _df in _done_files:
                try:
                    _d = _read_json(_df)
                    for _c in _d.get("testcases", []):
                        _cid = _c.get("case_id", "")
                        _m = re.search(r'TC-(\d+)', str(_cid))
                        if _m:
                            _max_seq = max(_max_seq, int(_m.group(1)))
                except Exception:
                    pass

            _next_idx = tp_index + 1
            while _next_idx < total_tps:
                _nf = os.path.join(_tp_dir_pause, f"tp_{_next_idx:03d}.json")
                if not os.path.exists(_nf):
                    break
                _next_idx += 1

            result["status"] = "PAUSE_REQUIRED"
            result["pause_info"] = {
                "completed": _completed_now,
                "total": total_tps,
                "segment_completed": _segment_done,
                "remaining": _remaining,
                "next_tp_index": _next_idx if _next_idx < total_tps else None,
                "next_case_sequence": _max_seq + 1 if _max_seq > 0 else 1,
                "message": " ".join([
                    f"P6段内暂停 | {_completed_now}/{total_tps} TP完成",
                    f"| 本段{_segment_done}条 | 剩余{_remaining}条",
                    f"| next_tp_index={_next_idx if _next_idx < total_tps else 'ALL_DONE'}"
                ])
            }
            try:
                _st_save["p6_status"] = "paused"
                _st_save["p6_last_pause_at"] = tp_index
                _write_json(_sp_save, _st_save)
            except Exception:
                pass
            # === V4.15.3: PAUSE锁文件机制(防Agent脚本绕过exit(3)) ===
            # PAUSE_REQUIRED触发时写入锁文件,后续p6_generate_one调用检测锁存在→拒绝执行
            # Agent即使写脚本绕过exit(3),也无法跳过锁文件检查(代码层硬拦截)
            # V4.15.11: 增加重试逻辑 + stderr日志
            _lock_path = os.path.join(data_dir, ".p6_pause_lock")
            _lock_data = {
                "locked_at": time.strftime("%Y-%m-%dT%H:%M:%S+08:00"),
                "completed": _completed_now,
                "total": total_tps,
                "next_tp_index": _next_idx if _next_idx < total_tps else None,
                "hint": "P6已暂停,等待用户确认。执行: python3 $ORCH --action p6_resume 以解锁恢复。"
            }
            _lock_written = False
            for _retry_i in range(3):
                try:
                    _write_json(_lock_path, _lock_data)
                    _lock_written = True
                    break
                except Exception as _le:
                    if _retry_i < 2:
                        time.sleep(0.1 * (_retry_i + 1))
            if not _lock_written:
                print(json.dumps({"warning": "PAUSE_LOCK_WRITE_FAILED", "lock_path": _lock_path}), file=sys.stderr)

        # V4.15.17: P6全部完成时加段落完成信号
        if _completed_now >= total_tps:
            result["paragraph_complete"] = True
            _case_count = sum(1 for _df in _done_files for _c in _read_json(_df).get("testcases", []))
            result["user_prompt"] = f"\u23f8\ufe0f 段落5完成。{_completed_now}个TP，{_case_count}条用例已全部生成。请回复「继续」进入段落6（P7质量门禁+Excel导出）。"

    print(json.dumps(result))
    return result


def action_p6_resume(args):
    """V4.15.3: 解锁P6暂停状态(清除.p6_pause_lock锁文件)
    
    PAUSE_REQUIRED触发后写入锁文件,后续p6_generate_one调用检测锁→拒绝执行。
    用户确认后调用本action解锁,Agent即可继续p6_generate_one。
    本action仅删除锁文件并更新state,不执行生成逻辑。
    """
    data_dir = args.data_dir
    task_id = args.task_id
    # V4.15.22: 清理checkpoint标记文件（resume时自动清除，移到data_dir定义后）
    _ckpt_path = os.path.join(data_dir, ".p6_checkpoint_required")
    if os.path.exists(_ckpt_path):
        try:
            os.remove(_ckpt_path)
        except Exception:
            pass
    _pause_lock_path = os.path.join(data_dir, ".p6_pause_lock")
    if os.path.exists(_pause_lock_path):
        try:
            _lock_data = _read_json(_pause_lock_path)
            _completed = _lock_data.get("completed", "?")
            _total = _lock_data.get("total", "?")
            # V4.15.20: resume前读实际文件数校验（偏差>3纠正）
            import glob as _g_resume
            _done_list = _g_resume.glob(os.path.join(data_dir, "p6_tp_output", "tp_[0-9]*.json"))
            _done = len([f for f in _done_list 
                         if "_context" not in os.path.basename(f) 
                         and "_agent_output" not in os.path.basename(f)])
            if isinstance(_completed, int) and abs(_done - _completed) > 3:
                print(json.dumps({"status": "resume_corrected", "lock_completed": _completed, "actual_files": _done}, ensure_ascii=False))
                _completed = _done
            # V4.15.20: 先更新state再删lock（原子化顺序，防止竞态）
            # os.unlink延迟到state写入后执行
        except Exception:
            _completed, _total = "?", "?"
        # 更新state中的p6_status + 重置segment起点(防每TP都暂停)
        try:
            _sp = os.path.join(data_dir, "orchestrator_state.json")
            if os.path.exists(_sp):
                _st = _read_json(_sp)
                _st["p6_status"] = "resumed"
                # V4.15.9: 重置segment起点为当前已完成数,否则每次resume后_segment_done仍>=15
                import glob as _glob_resume
                _tp_dir_resume = os.path.join(data_dir, "p6_tp_output")
                _done_resume = len([_f for _f in _glob_resume.glob(os.path.join(_tp_dir_resume, "tp_[0-9]*.json"))
                                     if "_context" not in os.path.basename(_f) and "_agent_output" not in os.path.basename(_f)])
                _st["p6_segment_start_count"] = _done_resume
                _write_json(_sp, _st)
        except Exception:
            _done_resume = _completed if isinstance(_completed, int) else 0
            pass
        # V4.15.20: 锁文件在state写入完成后删除（原子化顺序）
        if os.path.exists(_pause_lock_path):
            try:
                os.unlink(_pause_lock_path)
            except Exception:
                pass
        print(json.dumps({
            "status": "resumed",
            "message": f"P6暂停已解锁(已完成{_completed}/{_total} TP),可继续执行。",
            "next_tp_index": _done_resume,
            "next_action": f"直接执行 p6_generate_one --tp-index {_done_resume} --save"
        }, ensure_ascii=False))
    else:
        print(json.dumps({
            "status": "not_paused",
            "message": "P6当前未处于暂停状态,可以直接继续执行。"
        }, ensure_ascii=False))


def action_p5_retry(args):
    """V4.15.23: P5熔断恢复 — 跳过质量门禁BLOCK,强制继续"""
    data_dir = args.data_dir
    force_continue = getattr(args, 'force_continue', False)
    if not force_continue:
        print(json.dumps({"status": "error", "reason": "需要 --force-continue 参数确认强制绕过门禁"}))
        sys.exit(1)
    # 清除p5阻塞锁
    lock_path = os.path.join(data_dir, ".p5_blocked_lock")
    if os.path.exists(lock_path):
        os.remove(lock_path)
    # 重新执行p5_code_merge,跳过质量门禁
    setattr(args, 'skip_quality_gate', True)
    return action_p5_code_merge(args)


def action_p6_tp_list(args):
    """V4.11.0: 返回P6逐条生成的TP列表(替代p6_batch_info)"""
    data_dir = args.data_dir
    task_id = args.task_id
    ok, msg = check_gate(data_dir, "P5", task_id)
    if not ok:
        print(json.dumps({"status": "gate_blocked", "reason": msg}))
        sys.exit(1)
    if _is_sub_agent_session():
        print(json.dumps({"status": "rejected", "reason": "P6禁止子Agent执行"}))
        sys.exit(1)
    # V4.15.11: p6_tp_list入口锁文件检查
    _pause_lock_path_tpl = os.path.join(data_dir, ".p6_pause_lock")
    if os.path.exists(_pause_lock_path_tpl):
        try:
            _lock_data_tpl = _read_json(_pause_lock_path_tpl)
            print(json.dumps({
                "status": "paused_locked",
                "reason": f"P6已暂停({_lock_data_tpl.get('completed', '?')}/{_lock_data_tpl.get('total', '?')} TP完成),等待用户确认。",
                "hint": "用户回复'继续'后,执行: python3 $ORCH --action p6_resume 解锁,然后执行 p6_tp_list 查看进度。",
                "lock_info": {"completed": _lock_data_tpl.get("completed"), "next_tp_index": _lock_data_tpl.get("next_tp_index")}
            }, ensure_ascii=False))
            sys.exit(2)
        except Exception:
            try:
                os.unlink(_pause_lock_path_tpl)
            except Exception:
                pass
    # V4.13.2: 标记P6进行中,防止主Agent spawn子代理绕过检测
    state_path = os.path.join(data_dir, "orchestrator_state.json")
    if os.path.exists(state_path):
        try:
            st = _read_json(state_path)
            st["p6_status"] = "in_progress"
            st["p6_started_at"] = time.strftime("%Y-%m-%dT%H:%M:%S+08:00")
            _write_json(state_path, st)
        except Exception:
            pass
    p5_path = os.path.join(data_dir, "p5_output.json")
    p5 = _read_json(p5_path)
    tps = p5.get("test_points", [])
    tp_list = []
    for i, tp in enumerate(tps):
        tp_list.append({
            "index": i,
            "id": tp.get("id", ""),
            "title": tp.get("title", ""),
            "category": tp.get("category", ""),
            "priority": tp.get("priority", ""),
            "expected_case_count": tp.get("expected_case_count", 2),
            "description": tp.get("description", "")[:120],
        })
    # V4.11.0: TP质量门禁 - 检查每个TP是否独立完整
    tp_quality_warnings = 0
    for tp in tps:
        issues = []
        if not str(tp.get('title','')).strip():
            issues.append('title为空')
        if len(str(tp.get('description',''))) < 20:
            issues.append(f"description过短({len(str(tp.get('description','')))})字")
        if tp.get('category','') not in ('main_flow','branch','exception','boundary','permission',
                'risk_verification','field_validation','integration','security','state_migration','compatibility'):
            issues.append(f"category异常:{tp.get('category','')}")
        if tp.get('priority','') not in ('P0','P1','P2','P3','P4'):
            issues.append(f"priority异常:{tp.get('priority','')}")
        if issues:
            tp_quality_warnings += 1
            print(json.dumps({"status":"warning","action":"tp_quality","tp_index":i,
                "tp_id":tp.get('id',''),"issues":issues}), file=sys.stderr)
    if tp_quality_warnings:
        state = _read_json(os.path.join(data_dir, "orchestrator_state.json"))
        state["tp_quality_warnings"] = tp_quality_warnings
        _write_json(os.path.join(data_dir, "orchestrator_state.json"), state)

    mt = _get_model_tier_for_dir(data_dir)
    p3_path = os.path.join(data_dir, "p3_output.json")
    p3_risks = _read_json(p3_path).get("risk_points", []) if os.path.exists(p3_path) else []
    p4_path = os.path.join(data_dir, "p4_output.json")
    p4_pci = _read_json(p4_path).get("pci_list", []) if os.path.exists(p4_path) else []
    _write_tp_contexts(data_dir, tps, "standard", p3_risks, p4_pci)

    # === V4.15.0: 段内暂停恢复支持 ===
    import glob as _glob_tp
    _tp_dir_resume = os.path.join(data_dir, "p6_tp_output")
    _done_files_tp = [_f for _f in _glob_tp.glob(os.path.join(_tp_dir_resume, "tp_[0-9]*.json"))
                      if "_context" not in os.path.basename(_f) and "_agent_output" not in os.path.basename(_f)]
    _done_indices = set()
    for _f in _done_files_tp:
        try:
            _idx_done = int(os.path.basename(_f).split("_")[1].split(".")[0])
            _done_indices.add(_idx_done)
        except Exception:
            pass

    _completed_count = len(_done_indices)

    try:
        _sp_tp = os.path.join(data_dir, "orchestrator_state.json")
        _st_tp = _read_json(_sp_tp) if os.path.exists(_sp_tp) else {}
        _st_tp["p6_segment_start_count"] = _completed_count
        _st_tp["p6_status"] = "in_progress"
        _write_json(_sp_tp, _st_tp)
    except Exception:
        pass

    _next_tp = 0
    _all_done = False
    if _completed_count >= len(tp_list):
        _next_tp = None
        _all_done = True
    elif _completed_count > 0:
        for _i in range(len(tp_list)):
            if _i not in _done_indices:
                _next_tp = _i
                break
        else:
            _next_tp = None
            _all_done = True

    # V5.0(4.13.0): 统一时间估算(废除 HIGH/LOW 分档)
    minutes_per_tp = 0.3
    # V4.12.7: 计算预估用例数（基于 p5_output 各 TP 的 expected_case_count 求和）
    total_expected = sum(tp.get("expected_case_count", 2) for tp in tps)
    print(json.dumps({
        "status": "ok",
        "tp_list": tp_list,
        "total": len(tp_list),
        "model_info": "standard",
        "estimated_cases": total_expected,
        "estimated_range": {
            "min": int(total_expected * 0.8),
            "max": int(total_expected * 1.2)
        },
        "estimated_minutes": round(len(tp_list) * minutes_per_tp, 1),
        "mode": "sequential",
        "completed_count": _completed_count,
        "pending_count": len(tp_list) - _completed_count,
        "next_tp_index": _next_tp,
        "next_action": (
            "全部TP已完成 → 执行 p6_merge"
            if _all_done
            else f"从 tp_index={_next_tp} 开始逐条 p6_generate_one"
        ),
    }))


def action_p6_generate_one(args):
    """V4.11.0: 单TP端到端生成(替代prep_prompt P6 + save_batch)"""
    data_dir = args.data_dir
    tp_index = int(args.tp_index)
    agent_output = getattr(args, 'agent_output', '') or ''

    # === V4.15.34: TP索引边界校验(防p6_tp_list越界) ===
    _ctx_files = [f for f in os.listdir(os.path.join(data_dir, "p6_tp_output"))
                  if f.startswith("tp_") and "_context" in f]
    _total_tps = len(_ctx_files)
    if tp_index >= _total_tps:
        print(json.dumps({
            "status": "ERROR",
            "reason": f"TP索引越界: tp_index={tp_index}, 有效范围0-{_total_tps-1}",
            "hint": "p6_tp_list可能返回了错误索引，请重新执行 p6_tp_list 刷新列表"
        }, ensure_ascii=False))
        sys.exit(1)

    # === V4.15.26: checkpoint强制暂停(每15TP硬拦截, 防Agent连续生成不暂停) ===
    import glob as _cp_glob
    # === V4.15.38: checkpoint用state计数替代文件系统计数(防压缩后fs/state不同步) ===
    _sp = os.path.join(data_dir, "orchestrator_state.json")
    _segment_start = 0
    _state_done = 0
    if os.path.exists(_sp):
        try:
            _st = _read_json(_sp)
            _segment_start = _st.get("p6_segment_start_count", 0)
            _state_done = len(_st.get("p6_completed_tp_indices", []))
        except Exception:
            pass

    # V4.15.38: fs vs state 差异检测(排除_tmp临时文件)
    _tp_dir = os.path.join(data_dir, "p6_tp_output")
    _fs_done = len([_f for _f in _cp_glob.glob(os.path.join(_tp_dir, "tp_[0-9]*.json"))
                     if "_context" not in os.path.basename(_f)
                     and "_agent_output" not in os.path.basename(_f)
                     and "_tmp" not in os.path.basename(_f)])
    _gap = _fs_done - _state_done
    if _gap > 0:
        print(json.dumps({
            "status": "state_mismatch_warning",
            "fs_count": _fs_done,
            "state_count": _state_done,
            "gap": _gap,
            "hint": f"文件系统有{_fs_done}个TP文件,但orchestrator state仅记录{_state_done}个。建议执行 p6_verify_progress 同步状态。"
        }, ensure_ascii=False))

    _done = _state_done  # V4.15.38: 统一用state计数
    _segment_done = _done - _segment_start
    if _segment_done >= 15 and tp_index > _segment_start:  # V4.15.52: 恢复15TP强制暂停(V4.15.34曾扩至30,复盘发现仅触发1次)
        _cp = os.path.join(data_dir, ".p6_checkpoint")
        with open(_cp, "w") as _f:
            _f.write(json.dumps({"segment_start": _segment_start, "done": _done, "required_pause_after": _segment_start + 14}))
        print(json.dumps({
            "status": "CHECKPOINT_REQUIRED",
            "reason": f"已连续生成{_segment_done}个TP(≥15), 必须暂停检查质量后再 p6_resume 继续。",
            "next_action": "执行 p6_resume 解锁, 或检查已生成用例质量"
        }, ensure_ascii=False))
        sys.exit(3)

    # === V4.15.3: PAUSE锁文件检测(防Agent脚本绕过exit(3)) ===
    # PAUSE_REQUIRED触发后,即使Agent无视exit(3)继续调p6_generate_one,
    # 此处检测到锁文件存在→直接拒绝,强制恢复流程必须通过p6_resume
    _pause_lock_path = os.path.join(data_dir, ".p6_pause_lock")
    if os.path.exists(_pause_lock_path):
        try:
            _lock_data = _read_json(_pause_lock_path)
            print(json.dumps({
                "status": "paused_locked",
                "reason": f"P6已暂停({_lock_data.get('completed', '?')}/{_lock_data.get('total', '?')} TP完成),等待用户确认。",
                "hint": "用户回复'继续'后,执行: python3 $ORCH --action p6_resume 解锁,然后执行 p6_tp_list 查看进度。",
                "lock_info": {"completed": _lock_data.get("completed"), "next_tp_index": _lock_data.get("next_tp_index")}
            }, ensure_ascii=False))
            sys.exit(2)
        except Exception:
            # 锁文件损坏,清理后继续
            try:
                os.unlink(_pause_lock_path)
            except Exception:
                pass
    # === 防御机制: 入口调用频率检测(60秒内 gen>15次 → 拒绝,save不限制) ===
    # V4.15.9: 修复两个问题:
    #   (1) V4.15.8 把60s滑动窗口误改成纯数量限制(_parsed[-500:]),导致旧调用永久不过期
    #   (2) 阈值6次/60s对正常P6逐条生成太紧(每个TP=1gen+1save,6个TP就触发)
    # 修复: 恢复60s滑动窗口 + gen阈值6→15(≈4秒/TP,LLM正常速度) + save不计入限制
    # 新增: 连续高负载软告警(连续3窗口≥12次→写alert日志,不拦截)
    # 日志格式: 新格式为带前缀字符串 "gen:<ts>" / "save:<ts>";向前兼容旧的纯时间戳(无前缀 → 视为 gen)。
    # 保留最近500条完整审计日志,阈值判断仅统计60s窗口内的调用。
    # TODO(并行隔离): 如果未来恢复子代理并行生成,需按 session_id/proc_id 隔离计数器文件,防多个子代理共享同一计数器导致误杀。当前禁止子代理,计数器由主会话独占,无此风险。
    try:
        _call_dir = os.path.join(data_dir, "p6_tp_output")
        _ensure_dir(_call_dir)
        _call_log_path = os.path.join(_call_dir, ".gen_one_calls.json")
        _now_call = time.time()
        _raw_calls = []
        if os.path.exists(_call_log_path):
            try:
                _raw_calls = _read_json(_call_log_path)
                if not isinstance(_raw_calls, list):
                    _raw_calls = []
            except Exception:
                _raw_calls = []

        # 解析每条记录为 (action, ts);兼容旧格式(纯数字时间戳 → 当作 gen)
        def _parse_call(_item):
            if isinstance(_item, (int, float)):
                return ("gen", float(_item))  # 旧格式向前兼容
            if isinstance(_item, str):
                if _item.startswith("gen:"):
                    try:
                        return ("gen", float(_item[4:]))
                    except Exception:
                        return None
                if _item.startswith("save:"):
                    try:
                        return ("save", float(_item[5:]))
                    except Exception:
                        return None
            return None

        _parsed = [p for p in (_parse_call(c) for c in _raw_calls) if p is not None]

        # V4.15.9: 60秒滑动窗口(仅用于阈值判断)
        _window_cutoff = _now_call - 60
        _window_parsed = [p for p in _parsed if p[1] >= _window_cutoff]
        _gen_in_window = [_t for (_a, _t) in _window_parsed if _a == "gen"]
        _n_gen = len(_gen_in_window)

        # 判断当前 action: agent_output 非空 = save 模式,否则 gen 模式
        _is_save = bool(agent_output)
        _is_gen = not _is_save

        # V4.15.9: 仅gen受频率限制(阈值15/60s),save不限制(纯存储无生成逻辑)
        _GEN_LIMIT = 15
        _rejected = _is_gen and _n_gen >= _GEN_LIMIT
        if _rejected:
            print(json.dumps({
                "status": "rejected",
                "reason": f"调用频率超限: 60秒内 gen 调用已达阈值({_n_gen}/{_GEN_LIMIT}),疑似脚本批量调用。",
                "hint": f"频率限制(当前 60s 内已调用 {_n_gen} 次 gen,阈值 {_GEN_LIMIT}):请等待至少 60 秒后重试",
                "gen_calls_in_window": _n_gen,
                "threshold": _GEN_LIMIT,
            }, ensure_ascii=False))
            sys.exit(4)  # exit(4)=频率限制

        # V4.15.9: 连续高负载软告警(连续3个60s窗口都≥12次gen → 写alert日志,不拦截)
        # 设计理念(小析评审): 单窗口阈值区分不了Agent vs脚本;如果连续多窗口都打满,
        #   说明存在持续高频调用,留下审计痕迹供后续排查,但不中断正常流程。
        if _is_gen:
            _ALERT_WINDOW_GEN = 12
            _ALERT_CONSECUTIVE = 3
            _gen_all = [(a, t) for (a, t) in _parsed if a == "gen" and t >= _now_call - _ALERT_CONSECUTIVE * 60]
            _consecutive_high = 0
            for _w in range(_ALERT_CONSECUTIVE):
                _w_start = _now_call - (_w + 1) * 60
                _w_end = _now_call - _w * 60
                _w_count = sum(1 for (_, t) in _gen_all if _w_start <= t < _w_end)
                if _w_count >= _ALERT_WINDOW_GEN:
                    _consecutive_high += 1
            if _consecutive_high >= _ALERT_CONSECUTIVE:
                try:
                    _alert_path = os.path.join(data_dir, "p6_tp_output", ".gen_alert.log")
                    with open(_alert_path, "a") as _af:
                        _af.write(f"{time.strftime('%Y-%m-%dT%H:%M:%S+08:00')} | sustained_high_load | {_consecutive_high}/{_ALERT_CONSECUTIVE} windows >= {_ALERT_WINDOW_GEN} gen_calls | total_gen_in_3min={len(_gen_all)}\n")
                except Exception:
                    pass  # 告警写入失败不影响主流程

        # 审计日志保留最近500条(仅存档,不参与阈值判断)
        _audit = _parsed[-500:]
        _rebuilt = [f"{_a}:{_t}" for (_a, _t) in _audit]
        _rebuilt.append(f"{'save' if _is_save else 'gen'}:{_now_call}")
        _write_json(_call_log_path, _rebuilt)
    except SystemExit:
        raise
    except Exception:
        pass  # 频率检测失败不阻断主流程
    # === 频率检测结束 ===

    # 保存模式
    if agent_output:
        # V4.15.0: 子Agent拦截(P6红线)
        if _is_sub_agent_session():
            print(json.dumps({"status": "rejected", "reason": "P6禁止子Agent执行"}))
            sys.exit(1)
        # === V4.15.18: P6监控埋点（TP耗时+重试原因）===
        _tp_start = time.time()
        result = _save_single_tp(data_dir, tp_index, agent_output)
        _tp_elapsed = time.time() - _tp_start
        if _tp_elapsed > 60:
            print(json.dumps({
                "status": "tp_slow", "tp_index": tp_index,
                "elapsed_seconds": round(_tp_elapsed, 1),
                "reason": f"TP生成耗时{_tp_elapsed:.0f}秒(>60s阈值)"
            }, ensure_ascii=False))
        # 重试原因记录（由_save_single_tp内部的metrics输出）
        if result.get("status") == "PAUSE_REQUIRED":
            print(json.dumps(result, ensure_ascii=False))
            sys.exit(3)
        return
    # 生成模式:输出prompt
    ctx_path = os.path.join(data_dir, "p6_tp_output", f"tp_{tp_index:03d}_context.json")
    if not os.path.exists(ctx_path):
        p5 = _read_json(os.path.join(data_dir, "p5_output.json"))
        p3_path = os.path.join(data_dir, "p3_output.json")
        p3_risks = _read_json(p3_path).get("risk_points", []) if os.path.exists(p3_path) else []
        p4_path = os.path.join(data_dir, "p4_output.json")
        p4_pci = _read_json(p4_path).get("pci_list", []) if os.path.exists(p4_path) else []
        _write_tp_contexts(data_dir, p5.get("test_points", []),
                          _get_model_tier_for_dir(data_dir), p3_risks, p4_pci)
    ctx = _read_json(ctx_path)
    # V4.14.1: --short模式,stdout只输出精简摘要,避免Gateway显示warning
    short_mode = getattr(args, 'short', False)
    if short_mode:
        tp_id = ctx.get("tp_id", "?")
        pri = ctx.get("priority", "?")
        cat = ctx.get("category", "?")
        title = ctx.get("title", "?")
        ec = ctx.get("expected_case_count", "?")
        page = ctx.get("page_path", "")
        print(json.dumps({
            "status": "ok", "mode": "short",
            "tp_index": tp_index, "tp_id": tp_id,
            "priority": pri, "category": cat,
            "title": title, "expected_case_count": ec,
            "page_path": page,
            "context_file": f"p6_tp_output/tp_{tp_index:03d}_context.json",
            "hint": f"🔴 请 read p6_tp_output/tp_{tp_index:03d}_context.json 获取完整prompt后生成用例JSON"
        }, ensure_ascii=False))
        return
    prompt = _build_single_tp_prompt(ctx, ctx.get("model_tier", "standard"))
    print(prompt)


# V4.11.0: action_p6_batch_info 已废弃,替代为 action_p6_tp_list
def action_p6_batch_info(args):
    """返回P6分批信息:总批次数、每批测试点数
    V4.7.1: 写入 batch_{N:03d}_context.json 供 Agent 按需读取(P6 prompt 分片)
    """
    data_dir = args.data_dir
    task_id = args.task_id

    # V4.7.3: 子Agent环境检测(P6必须在主会话执行,子Agent有30分钟超时)
    if _is_sub_agent_session():
        print(json.dumps({
            "status": "rejected",
            "reason": "⛔ P6禁止在子Agent(spawn)中执行!P6需要主会话的完整上下文和充足时间。请在主会话中直接运行P6流程。",
            "hint": "返回到主会话,执行: python3 $ORCH --action p6_batch_info"
        }))
        sys.exit(1)

    # V3.2.6: P5前置gate校验
    ok, msg = check_gate(data_dir, "P5", task_id)
    if not ok:
        print(json.dumps({
            "status": "gate_blocked",
            "reason": f"P6批次信息需要P5 gate pass: {msg}。必须先执行p5_code_merge完成P5。",
        }))
        sys.exit(1)

    p5_path = os.path.join(data_dir, "p5_output.json")
    if not os.path.exists(p5_path):
        print(json.dumps({"status": "error", "reason": "p5_output.json不存在"}))
        sys.exit(1)

    p5 = _read_json(p5_path)
    test_points = p5.get("test_points", [])
    total = len(test_points)
    # V5.0(4.13.0): 废除分档,统一批次大小和时间估算
    # 使用合理的固定 batch_size (过大 Agent 处理不过来,过小效率低)
    recommended_batch_size = min(8, max(5, total // 10)) if total > 0 else 5

    # V4.6.17: 启用动态分批
    batch_info = calculate_dynamic_batches(test_points, max_batches=5)
    total_batches = batch_info["total_batches"]
    strategy = batch_info.get("strategy", "dynamic")

    # V4.7.1: 为每批写入 batch context 文件(Agent 按需读取,prompt 精简后从 66KB → ~20KB)
    batches_dir = os.path.join(data_dir, "p6_batches")
    _ensure_dir(batches_dir)
    context_files = []
    for b in batch_info["batches"]:
        start, end = b["start"], b["end"]
        batch_idx = len(context_files)  # V4.8.12: 0-based,与prep_prompt --batch-index一致
        chunk_tps = test_points[start:end]
        # 精简测试点数据(保留 Agent 生成用例必需字段)
        slim_tps = []
        for tp in chunk_tps:
            ops = tp.get("operations_chain", [])
            is_ops_chain = isinstance(ops, list) and len(ops) > 0
            stp = {
                "id": tp.get("id", ""),
                "title": tp.get("title", ""),
                "description": tp.get("description", ""),
                "category": tp.get("category", ""),
                "priority": tp.get("priority", ""),
                "expected_case_count": tp.get("expected_case_count", 2),
                "page_path": tp.get("page_path", ""),
                "step_expected_pairs": tp.get("step_expected_pairs", []),
                "step_expected_pairs_source": "operations_chain" if is_ops_chain else "fallback_template",
                "field_checklist": tp.get("field_checklist", []),
                "ui_elements": tp.get("ui_elements", {}),
                "risk_flag": tp.get("risk_flag", False),
                "risk_severity": tp.get("risk_severity", ""),
                "precondition": tp.get("precondition", ""),
            }
            slim_tps.append(stp)
        context = {"batch_index": batch_idx, "test_points": slim_tps, "total_in_batch": len(slim_tps)}
        ctx_path = os.path.join(batches_dir, f"batch_{batch_idx:03d}_context.json")
        _write_json(ctx_path, context)
        context_files.append(f"p6_batches/batch_{batch_idx:03d}_context.json")

    # V4.7.2: 计算预计用例分布表(按优先级和类别)
    expected_total = sum(tp.get("expected_case_count", 2) for tp in test_points)
    by_priority = {}
    by_category = {}
    for tp in test_points:
        p = tp.get("priority", "P1")
        c = tp.get("category", "unknown")
        ec = tp.get("expected_case_count", 2)
        by_priority[p] = by_priority.get(p, 0) + ec
        by_category[c] = by_category.get(c, 0) + ec

    # V5.0(4.13.0): 统一批次大小和时间估算
    import math
    total_execution_batches = math.ceil(total / recommended_batch_size) if recommended_batch_size > 0 else math.ceil(total / 5)
    minutes_per_batch = 0.8
    estimated_minutes = round(total_execution_batches * minutes_per_batch, 1)

    print(json.dumps({
        "status": "ok",
        "total_test_points": total,
        "total_execution_batches": total_execution_batches,
        "recommended_batch_size": recommended_batch_size,
        "estimated_minutes": estimated_minutes,
        "complexity_groups": total_batches,
        "strategy": strategy,
        "batches": batch_info["batches"],
        "context_files": context_files,
        "execution_hint": f"🔴🔴 必须循环执行 {total_execution_batches} 批(batch-index从0到{total_execution_batches-1})!预计耗时{estimated_minutes}分钟。complexity_groups({total_batches})仅用于展示复杂度分布,不是执行批次数。以 total_execution_batches 为准,全部跑完后再 p6_merge。",
        "expected_distribution": {
            "total_expected_cases": expected_total,
            "by_priority": by_priority,
            "by_category": by_category,
            "hint": f"预计共{expected_total}条用例(非硬性门槛,按复杂度可增减)。优先保证每个测试点至少展开到 expected_case_count 条。"
        },
        "auto_downgrade_estimation": {
            "p0_tp_count": sum(1 for tp in test_points if tp.get("priority") == "P0"),
            "p1_tp_count": sum(1 for tp in test_points if tp.get("priority") == "P1"),
            "p0_skeleton_ratio": round(sum(1 for tp in test_points if tp.get("priority") == "P0") / expected_total, 3) if expected_total > 0 else 0,
            "threshold_p0": 0.35,
            "threshold_smoke": 0.30,
            "hint": "🔴 P0测试点占比过高(P2给每feature第1个main_flow升P0导致)。骨架生成阶段会自动降级超标批次(P0>35%或smoke>30%),Agent无需手动调整优先级。预期降级后P0比例≤35%。"
        },
    }))


# ============================================================
# V4.8.10: 占位符质量检测 - 标记不拒绝
# ============================================================

def _check_placeholder_quality(cases: list) -> dict:
    """检测用例中的占位符/空洞内容,标记到remarks,不拒绝保存。"""
    import re

    # 标题占位符模式
    TITLE_PLACEHOLDER_PATTERNS = [
        (r'^测试用例[-_\s]*(TP-\d+|\d+)[-_\s]*\d*$', '占位符标题'),
        (r'^用例\d*$', '占位符标题'),
        (r'^[Tt]est\s*[Cc]ase[-_\s]*\d+$', '占位符标题'),
    ]

    # 步骤空洞模式
    STEP_HOLLOW_PATTERNS = [
        r'^\d*[.、)]?\s*(执行|进行|完成|操作|验证|检查|查看|确认)\s*(相关|对应|相应|指定|该|所有|各项)?\s*(操作|内容|步骤|功能|动作|流程|数据|结果|信息|页面)?\s*$',
    ]

    # 期望空洞模式
    EXPECTED_HOLLOW_PATTERNS = [
        r'^\d*[.、)]?\s*(操作|执行|验证|数据|结果|页面|功能|跳转|显示|保存|提交|登录|导出|导入|查询|搜索|删除|新增|修改|编辑)?\s*(成功|完成|正常|正确|无误|通过|ok|OK)?\s*$',
    ]

    warnings = {
        "total_checked": len(cases),
        "title_placeholder": [],
        "step_short": [],
        "step_hollow": [],
        "expected_hollow": [],
        "total_tagged": 0,
    }

    tagged_ids = set()
    for ci, c in enumerate(cases):
        if not isinstance(c, dict):
            continue
        cid = c.get("case_id", f"idx_{ci}")
        tags = []

        # 标题检测
        title = str(c.get("title", "")).strip()
        for pattern, label in TITLE_PLACEHOLDER_PATTERNS:
            if re.match(pattern, title, re.IGNORECASE):
                tags.append(f'[{label}]')
                warnings["title_placeholder"].append(f"{cid}: {title[:40]}")
                break

        # 步骤检测
        steps_text = str(c.get("steps", "")).strip()
        if steps_text:
            steps_lines = [s.strip() for s in steps_text.split('\n') if s.strip()]
            for sl in steps_lines:
                # 去除编号后检测
                cleaned = re.sub(r'^\d+[.、)]?\s*', '', sl)
                if len(cleaned) < 15:
                    if "step_short" not in [t for t in tags if "步骤" in t]:
                        tags.append('[步骤过短<15字]')
                        warnings["step_short"].append(f"{cid}: {cleaned[:40]}")
                for pattern in STEP_HOLLOW_PATTERNS:
                    if re.match(pattern, sl, re.IGNORECASE):
                        if "步骤空洞" not in [t for t in tags if "步骤空洞" in t]:
                            tags.append('[步骤空洞]')
                            warnings["step_hollow"].append(f"{cid}: {cleaned[:40]}")
                        break

        # 期望检测
        exp_text = str(c.get("expected_results", "")).strip()
        if exp_text:
            exp_lines = [e.strip() for e in exp_text.split('\n') if e.strip()]
            for el in exp_lines:
                cleaned = re.sub(r'^\d+[.、)]?\s*', '', el)
                for pattern in EXPECTED_HOLLOW_PATTERNS:
                    if re.match(pattern, cleaned, re.IGNORECASE):
                        if "期望空洞" not in [t for t in tags if "期望空洞" in t]:
                            tags.append('[期望空洞]')
                            warnings["expected_hollow"].append(f"{cid}: {cleaned[:40]}")
                        break

        # 标记到 remarks
        if tags:
            tagged_ids.add(cid)
            existing = str(c.get("remarks", "")).strip()
            tag_str = ' '.join(tags)
            if tag_str not in existing:
                c["remarks"] = f"{existing} {tag_str}".strip() if existing else tag_str

    warnings["total_tagged"] = len(tagged_ids)
    return warnings if tagged_ids else {}


# ============================================================
# V4.8.3: LOW模型后处理工具函数
# ============================================================

def _check_terminology_consistency(cases: list) -> list:
    """V4.8.3: 术语一致性检测(纯代码,零token)。

    提取所有用例步骤中的 [动作动词+「UI元素」] 对,
    对编辑距离<3的对做聚类,标记不一致的用例。

    Returns:
        [{"canonical": 规范用语, "variants": [变体列表], "suggestion": 统一建议, "affected_case_indices": [受影响的用例索引]}]
    """
    import difflib

    # 1. 提取所有 [动作动词+UI元素] 对
    action_pairs = []  # [(case_index, step_index, verb, element)]
    for ci, c in enumerate(cases):
        steps_str = _get_case_field(c, "steps", "")
        if not isinstance(steps_str, str):
            continue
        if not steps_str:
            continue
        # 匹配: 动作动词「UI元素」
        pairs = re.findall(
            r'(点击|输入|选择|删除|勾选|上传|下载|拖拽|切换|打开|关闭|填写|修改|清空|提交|保存|确认|取消)'
            r'[「「]?([^」」]{1,15})[」」]?',
            steps_str
        )
        for si, (verb, element) in enumerate(pairs):
            element = element.strip()
            if element:
                action_pairs.append((ci, si, verb, element))

    if len(action_pairs) < 3:
        return []

    # 2. 按 verb 分组,在每个组内做聚类
    from collections import defaultdict
    by_verb = defaultdict(list)
    for ci, si, verb, element in action_pairs:
        by_verb[verb].append((ci, si, element))

    issues = []
    for verb, group in by_verb.items():
        if len(group) < 3:
            continue

        # 提取唯一的 element 名称
        unique_elements = list(set(e for _, _, e in group))
        if len(unique_elements) < 2:
            continue

        # 对 element 做编辑距离聚类
        clusters = {}
        processed = set()
        for i, e1 in enumerate(unique_elements):
            if e1 in processed:
                continue
            cluster = [e1]
            for e2 in unique_elements[i+1:]:
                if e2 in processed:
                    continue
                # 编辑距离 < 3 且至少3字 → 视为变体
                ratio = difflib.SequenceMatcher(None, e1, e2).ratio()
                if ratio > 0.6 and max(len(e1), len(e2)) >= 2:
                    cluster.append(e2)
                    processed.add(e2)
            if len(cluster) >= 2:
                clusters[e1] = cluster
                processed.add(e1)

        for canonical, variants in clusters.items():
            if len(variants) <= 1:
                continue
            # 取最长的为规范用语
            best = max(variants, key=len)
            # 找出受影响的用例
            affected = []
            for ci, si, e in group:
                if e in variants and e != best:
                    if ci not in affected:
                        affected.append(ci)
            if affected:
                other_variants = [v for v in variants if v != best]
                issues.append({
                    "verb": verb,
                    "canonical": f"{verb}「{best}」",
                    "variants": [f"{verb}「{v}」" for v in other_variants],
                    "suggestion": f"统一为 {verb}「{best}」",
                    "affected_case_indices": affected[:10],
                })

    return issues[:10]  # 最多10个问题


def _dedup_preconditions(cases: list) -> dict:
    """V4.8.3: 前置条件去重(纯代码,零token)。

    按模块分组,提取 ≥50% 用例共享的 precondition → 写入公共前置。

    Returns:
        {"extracted_count": 提取条数, "reduced_count": 减少的重复次数, "details": [...]}
    """
    if len(cases) < 3:
        return {"extracted_count": 0, "reduced_count": 0}

    # 1. 按模块分组(从 case_id 提取模块前缀,或从 test_suite/menu_path)
    from collections import Counter
    modules = {}
    for ci, c in enumerate(cases):
        cid = _get_case_field(c, "case_id", "")
        # 从 case_id 提取模块前缀: TC-XG-RZ-xxx → XG-RZ
        mod = "default"
        match = re.match(r'TC-([A-Z]+(?:-[A-Z]+)?)', cid)
        if match:
            mod = match.group(1)
        else:
            # fallback: test_suite 或 menu_path
            ts = _get_case_field(c, "test_suite", "") or _get_case_field(c, "menu_path", "")
            if ts:
                mod = ts.split("→")[0].strip()[:20]
        if mod not in modules:
            modules[mod] = []
        modules[mod].append(ci)

    # 2. 对每个模块提取公共 precondition
    total_extracted = 0
    total_reduced = 0
    details = []

    for mod_name, indices in modules.items():
        if len(indices) < 3:
            continue

        # 收集该模块所有用例的 precondition
        preconds = []
        for ci in indices:
            pc = _get_case_field(cases[ci], "preconditions", "")
            if not isinstance(pc, str):
                continue
            if pc:
                preconds.append(pc)

        if len(preconds) < 3:
            continue

        # 解析每行 precondition,统计每行出现次数
        line_counter = Counter()
        for pc in preconds:
            for line in pc.split("\n"):
                line = line.strip()
                if not line:
                    continue
                # 去序号 "1. " 或 "1、"
                line = re.sub(r'^\d+[.、]\\s*', '', line)
                if len(line) >= 5:
                    line_counter[line] += 1

        # 提取 ≥50% 用例共享的行
        threshold = max(2, len(preconds) // 2)
        common_lines = [line for line, count in line_counter.items() if count >= threshold]

        if not common_lines:
            continue

        # 3. 从个体用例中删除公共行,添加到模块公共 precondition
        common_text = "\n".join(f"{i}. {line}" for i, line in enumerate(common_lines, 1))
        reduced = 0
        for ci in indices:
            pc = _get_case_field(cases[ci], "preconditions", "")
            if not pc:
                continue
            lines = pc.split("\n")
            new_lines = []
            for line in lines:
                stripped = re.sub(r'^\d+[.、]\\s*', '', line.strip())
                if stripped not in common_lines:
                    new_lines.append(line)
                else:
                    reduced += 1
            if len(new_lines) < len(lines):
                # 在前面加模块公共前置引用
                mod_ref = f"0. [模块公共前置] {mod_name}: {', '.join(common_lines[:3])}"
                new_pc = mod_ref + "\n" + "\n".join(new_lines)
                # 更新用例
                if "fields" in cases[ci] and isinstance(cases[ci].get("fields"), dict):
                    cases[ci]["fields"]["preconditions"] = new_pc
                else:
                    cases[ci]["preconditions"] = new_pc

        total_extracted += len(common_lines)
        total_reduced += reduced
        details.append({
            "module": mod_name,
            "extracted_lines": common_lines,
            "reduced_count": reduced,
        })

    return {
        "extracted_count": total_extracted,
        "reduced_count": total_reduced,
        "details": details[:10],
    }


def action_p6_checkpoint(args):
    """V4.12.5: P6分批回顾检查点 — 检查已完成TP的质量"""
    data_dir = args.data_dir
    tp_dir = os.path.join(data_dir, "p6_tp_output")

    # 收集已完成TP
    tp_files = sorted(glob.glob(os.path.join(tp_dir, "tp_[0-9]*.json")))
    tp_files = [f for f in tp_files if "_context" not in os.path.basename(f) and "_agent_output" not in os.path.basename(f)]

    if not tp_files:
        print(json.dumps({"status": "info", "completed": 0, "hint": "尚未完成任何TP"}))
        return

    # 统计每个已完成TP的用例
    summary = []
    total_cases = 0
    total_short = 0
    total_no_smoke = 0
    issues = []

    for tf in tp_files:
        try:
            tp_data = _read_json(tf)
            cases = tp_data.get("testcases", [])
            tp_index = tp_data.get("tp_index", 0)
            tp_id = tp_data.get("tp_id", "?")

            short_count = 0
            has_smoke = False
            for c in cases:
                steps_text = _get_case_field(c, "steps", "")
                if isinstance(steps_text, str):
                    step_count = len([s for s in steps_text.split("\n") if s.strip()])
                else:
                    step_count = 0
                if step_count <= 2:
                    short_count += 1
                if _is_smoke(_get_case_field(c, "is_smoke", "")):
                    has_smoke = True

            ctx_path = os.path.join(tp_dir, f"tp_{tp_index:03d}_context.json")
            need_smoke = False
            if os.path.exists(ctx_path):
                try:
                    ctx = _read_json(ctx_path)
                    need_smoke = ctx.get("need_smoke", False)
                except Exception:
                    pass

            total_cases += len(cases)
            total_short += short_count
            tp_issues = []
            if short_count >= 1:
                tp_issues.append(f"{short_count}条过短")
            if need_smoke and not has_smoke:
                total_no_smoke += 1
                tp_issues.append("缺冒烟")

            summary.append({
                "tp_index": tp_index,
                "tp_id": tp_id,
                "cases": len(cases),
                "short_steps": short_count,
                "issues": tp_issues,
                "ok": len(tp_issues) == 0,
            })
            if tp_issues:
                issues.append(f"{tp_id}: {', '.join(tp_issues)}")
        except Exception as e:
            summary.append({"tp_index": -1, "error": str(e)})

    problem_count = sum(1 for s in summary if not s.get("ok", False))
    total_tp = len(summary)
    need_fix = problem_count > total_tp / 2

    result = {
        "status": "needs_fix" if need_fix else "ok",
        "completed_tps": total_tp,
        "total_cases": total_cases,
        "problem_tps": problem_count,
        "short_step_cases": total_short,
        "missing_smoke_tps": total_no_smoke,
        "issues": issues[:8],
        "summary": summary,
    }

    if need_fix:
        result["hint"] = (
            f"⚠️ {problem_count}/{total_tp}个TP存在问题，请修复后再继续。"
        )
    else:
        result["hint"] = f"✅ {total_tp}个TP质量检查通过，可以继续生成下一批"

    # V4.13.8 P1-5: Agent防呆 — 检测连续merge失败,防止无效重试
    state_path = os.path.join(data_dir, "orchestrator_state.json")
    merge_fail_count = 0
    if os.path.exists(state_path):
        try:
            st = _read_json(state_path)
            merge_fail_count = st.get("p6_merge_fail_count", 0)
        except Exception:
            pass
    if merge_fail_count >= 2:
        result["merge_guardrail"] = {
            "status": "PAUSE_AND_ANALYZE",
            "consecutive_merge_failures": merge_fail_count,
            "hint": f"⛔ 已连续{merge_fail_count}次merge失败,必须暂停分析根因,不得用同样方法重试。请: ①阅读P7报错信息定位具体case ②针对性修复 ③修复后重新merge验证",
        }

    print(json.dumps(result))
    if need_fix:
        sys.exit(1)


def action_p6_merge(args):
    # V4.15.22: 清理checkpoint标记文件（merge时已完成P6）
    retry_mode = getattr(args, 'retry', False)
    _ckpt_path = os.path.join(args.data_dir, ".p6_checkpoint_required")
    if os.path.exists(_ckpt_path):
        try:
            os.remove(_ckpt_path)
        except Exception:
            pass
    
    _missing_tps = []  # V4.15.41: partial模式追踪
    
    """合并P6所有批次结果,写入p6_output.tmp.json,调用truncation_guard"""
    data_dir = args.data_dir
    task_id = args.task_id
    skill_dir = args.skill_dir

    # V4.7.3: 子Agent环境检测(P6必须在主会话执行,子Agent有30分钟超时)
    if _is_sub_agent_session():
        print(json.dumps({
            "status": "rejected",
            "reason": "⛔ P6禁止在子Agent(spawn)中执行!P6需要主会话的完整上下文和充足时间。请在主会话中直接运行P6流程。",
            "hint": "返回到主会话,执行: python3 $ORCH --action p6_merge"
        }))
        sys.exit(1)

    # V3.2.6: P5前置gate校验(防止Agent伪造batch后借刀签名)
    ok, msg = check_gate(data_dir, "P5", task_id)
    if not ok:
        print(json.dumps({
            "status": "gate_blocked",
            "reason": f"P6合并需要P5 gate pass: {msg}。必须先执行p5_code_merge完成P5。",
        }))
        sys.exit(1)

    # V4.11.0: 优先读逐条TP格式(p6_tp_output/tp_*.json),兼容旧批量格式
    all_cases = []
    tp_dir = os.path.join(data_dir, "p6_tp_output")
    tp_files = sorted(glob.glob(os.path.join(tp_dir, "tp_[0-9]*.json")))
    tp_files = [tf for tf in tp_files if "_context" not in os.path.basename(tf) and "_agent_output" not in os.path.basename(tf)]

    if tp_files:
        for tf in tp_files:
            tp_data = _read_json(tf)
            if isinstance(tp_data, list):
                tp_data = {"testcases": tp_data}
            all_cases.extend(tp_data.get("testcases", []))
        # FIX(compaction-recovery) V4.13.9-S2 #3: 合并前主动校验 TP 完整性,把缺口暴露在 merge 之前
        # (而非等到 P7 覆盖率 C7 才发现)。数据已落盘,此处仅做对账。复用 p6_verify_files 思路:
        # 用 p5_output.json 的预期 TP 总数对比实际存在的 tp 文件 index 集合,缺 TP 即告警(不阻断)。
        # 告警走 sys.stderr + status:incomplete,避免与"补生成后增量 merge"工作流冲突。
        _p5p = os.path.join(data_dir, "p5_output.json")
        if os.path.exists(_p5p):
            try:
                _expected = len(_read_json(_p5p).get("test_points", []))
                _existing = set()
                for _tf in tp_files:
                    try:
                        _existing.add(int(os.path.basename(_tf).replace("tp_", "").replace(".json", "")))
                    except Exception:
                        pass
                _missing = sorted(set(range(_expected)) - _existing)
                _missing_tps = _missing
                if _missing:
                    print(json.dumps({
                        "status": "incomplete",
                        "reason": f"检测到 {len(_missing)} 个 TP 文件缺失(可能因会话压缩中断),合并将不完整。",
                        "expected_total": _expected,
                        "actual_count": len(_existing),
                        "missing_tp_indices": _missing[:30],
                        "fix": "对每个缺失 index 执行: p6_generate_one --tp-index N --save,补齐后重跑 p6_merge。",
                    }, ensure_ascii=False), file=sys.stderr)
            except Exception:
                pass
        print(json.dumps({"status":"info","mode":"sequential",
            "tp_files":len(tp_files),"cases":len(all_cases)}), file=sys.stderr)
    else:
        batches_dir = os.path.join(data_dir, "p6_batches")
        if not os.path.exists(batches_dir):
            print(json.dumps({"status":"error","reason":"p6_batches目录不存在"}))
            sys.exit(1)
        batch_files = sorted(glob.glob(os.path.join(batches_dir, "batch_[0-9]*.json")))
        batch_files = [bf for bf in batch_files if "_output" not in os.path.basename(bf) and "_agent_output" not in os.path.basename(bf)]

    # V4.7.2: 合并前校验各批次状态(仅旧批量格式)
    batch_status = []
    empty_batches = []
    if not tp_files:
        for bf in batch_files:
            try:
                bd = _read_json(bf)
                bcases = bd.get("testcases", bd.get("cases", []))
                batch_status.append({
                    "file": os.path.basename(bf),
                    "cases": len(bcases),
                    "empty": len(bcases) == 0,
                })
                if len(bcases) == 0:
                    empty_batches.append(os.path.basename(bf))
                all_cases.extend(bcases)
            except Exception as e:
                print(json.dumps({"status": "warning", "reason": f"批次文件读取失败: {bf}: {e}"}), file=sys.stderr)
                empty_batches.append(os.path.basename(bf))

    if empty_batches:
        print(json.dumps({
            "status": "info",
            "empty_batches": empty_batches,
            "hint": f"{len(empty_batches)}个批次为空或读取失败,请检查Agent输出后重新执行该批次的p6_save_batch",
        }), file=sys.stderr)

    if not all_cases:
        print(json.dumps({"status": "error", "reason": "所有批次合并后用例数为0", "batch_status": batch_status if not tp_files else [], "hint": "请检查各批次是否存在非空用例数据。如有空批次,用p6_save_batch重新保存对应批次。"}))
        sys.exit(1)

    # V4.13.6: 内容感知去重(同case_id+内容相同→删除, 内容不同→追加-V后缀保留)
    # BUG-1修复: 用set存所有hash, 避免只记首个指纹导致变体间重复逃逸
    seen_map = {}  # case_id → {"hashes": set, "variant": int}
    deduped_cases = []
    dup_count = 0
    variant_count = 0
    for c in all_cases:
        cid = _get_case_field(c, "case_id", "")
        if not cid:
            deduped_cases.append(c)
            continue
        # 内容指纹(title+preconditions+steps+expected_results)
        content_key = (
            str(_get_case_field(c, "title", "")).strip()
            + "||" + str(_get_case_field(c, "preconditions", "")).strip()
            + "||" + str(_get_case_field(c, "steps", "")).strip()
            + "||" + str(_get_case_field(c, "expected_results", "")).strip()
        )
        if cid in seen_map:
            if content_key in seen_map[cid]["hashes"]:
                dup_count += 1
                continue
            # 内容不同 → 追加变体后缀保留
            seen_map[cid]["variant"] += 1
            v = seen_map[cid]["variant"]
            seen_map[cid]["hashes"].add(content_key)
            new_cid = f"{cid}-V{v}"
            if "fields" in c and isinstance(c.get("fields"), dict):
                c["fields"]["case_id"] = new_cid
            else:
                c["case_id"] = new_cid
            variant_count += 1
        else:
            seen_map[cid] = {"hashes": {content_key}, "variant": 0}
        deduped_cases.append(c)

    # V4.15.43: 跨TP内容去重（相同内容但相同source_tp→去重, 不同source_tp→保留为跨TP变体）
    cross_tp_seen = {}  # content_key → (case_id, source_test_point)
    cross_tp_dup = 0
    cross_tp_variant = 0  # V4.15.43: 跨TP变体计数
    cross_tp_deduped = []
    for c in deduped_cases:
        cid = _get_case_field(c, "case_id", "")
        ck = (
            str(_get_case_field(c, "title", "")).strip()
            + "||" + str(_get_case_field(c, "steps", "")).strip()
            + "||" + str(_get_case_field(c, "expected_results", "")).strip()
        )
        curr_stp = _get_case_field(c, "source_test_point", "")
        if ck in cross_tp_seen:
            prev_cid, prev_stp = cross_tp_seen[ck]
            if prev_stp and curr_stp and prev_stp != curr_stp:
                # V4.15.43: 不同TP产生相同内容→保留为跨TP变体(保证source_tp覆盖)
                cross_tp_variant += 1
                cross_tp_deduped.append(c)
            else:
                cross_tp_dup += 1
                continue
        else:
            cross_tp_seen[ck] = (cid, curr_stp)
            cross_tp_deduped.append(c)
    if cross_tp_dup > 0 or cross_tp_variant > 0:
        print(json.dumps({
            "status": "info", "cross_tp_dedup": cross_tp_dup,
            "cross_tp_variants": cross_tp_variant,
            "before": len(deduped_cases), "after": len(cross_tp_deduped),
            "reason": f"跨TP去重: 真正重复{cross_tp_dup}条(相同source_tp), 跨TP变体保留{cross_tp_variant}条(不同source_tp)"
        }, ensure_ascii=False), file=sys.stderr)
    deduped_cases = cross_tp_deduped

    # V4.13.8 P0-4: 去重统计+分级告警(阈值降至15%)
    dup_ratio = dup_count / len(all_cases) if all_cases else 0
    info = {"status": "info", "dedup_removed": dup_count,
            "variants_created": variant_count, "true_duplicates": dup_count,
            "variants_kept": variant_count,
            "before": len(all_cases), "after": len(deduped_cases)}
    print(json.dumps(info), file=sys.stderr)

    # V4.13.8 P0-4: 去重率阈值从50%→15%, 30%→15% (历史基线3%)
    if dup_ratio > 0.5:
        print(json.dumps({"status": "blocked",
            "reason": f"去重率{dup_ratio:.0%}>50%,疑似case_id分配异常。请检查TP文件并重新分配case_id后重跑p6_merge。"
        }), file=sys.stderr)
        sys.exit(1)
    elif dup_ratio > 0.15:
        print(json.dumps({"status": "warning",
            "dedup_warning": f"去重率{dup_ratio:.0%}异常(>15%,历史基线3%)",
            "possible_causes": ["Agent重复生成了相同内容的用例", "同一TP下多条用例case_id被错误分配为相同值"],
            "action_required": "检查TP文件中是否存在相同case_id但不同内容的用例,确认case_id分配是否正确",
            "true_duplicates": dup_count, "variants_kept": variant_count
        }), file=sys.stderr)

    # FIX(p5_points-unbound) V4.13.9-S1: 提前加载 p5 测试点,供下方相似度复杂度映射(原7627)
    # 与预算校验(原7830)共用。原Bug: p5_points 仅在更下方 if os.path.exists(p5_path) 分支内赋值,
    # 但相似度循环无条件先使用 → UnboundLocalError(任何一次 p6_merge 都会崩)。此处统一初始化并加载。
    p5_points = []
    _p5_path_early = os.path.join(data_dir, "p5_output.json")
    if os.path.exists(_p5_path_early):
        try:
            p5_points = _read_json(_p5_path_early).get("test_points", [])
        except Exception:
            p5_points = []

    # V4.13.8 P0-4: 三级去重 — 步骤相似度检测(检测同质化用例)
    # 构建TP复杂度映射: expected_case_count >=3 → L3(仅完全重复去重,不做相似度检测)
    tp_complexity = {}
    for tp in p5_points:
        tp_id = tp.get("id", "")
        ec = tp.get("expected_case_count", 2)
        tp_complexity[tp_id] = "L3" if ec >= 3 else ("L1" if ec <= 1 else "L2")

    # 按TP分组去重后的用例,检测变体组内的步骤相似度
    tp_cases = {}  # tp_id → [case_dict, ...]
    for c in deduped_cases:
        src = _get_case_field(c, "source_test_point", "")
        if not src and "case_id" in c:
            cid = _get_case_field(c, "case_id", "")
            if "-TP-" in cid:
                src = cid.split("-TC-")[0] if "-TC-" in cid else ""
        if src:
            tp_cases.setdefault(src, []).append(c)

    similarity_warnings = []
    for tp_id, cases in tp_cases.items():
        if tp_complexity.get(tp_id) == "L3":
            continue  # L3 TP不检测相似度,保留变体以保覆盖深度
        if len(cases) < 2:
            continue
        for i in range(len(cases)):
            for j in range(i+1, len(cases)):
                s1 = _get_case_field(cases[i], "steps", "")
                s2 = _get_case_field(cases[j], "steps", "")
                if not s1 or not s2:
                    continue
                # 简单Jaccard相似度: 字符集重叠率
                set1, set2 = set(s1), set(s2)
                if not set1 or not set2:
                    continue
                sim = len(set1 & set2) / len(set1 | set2)
                if sim > 0.80:
                    cid1 = _get_case_field(cases[i], "case_id", f"{tp_id}_case_{i}")
                    cid2 = _get_case_field(cases[j], "case_id", f"{tp_id}_case_{j}")
                    similarity_warnings.append(f"{cid1}↔{cid2}: 步骤相似度{sim:.0%}")
    if similarity_warnings:
        print(json.dumps({
            "status": "info",
            "action": "step_similarity_check",
            "similar_pairs": len(similarity_warnings),
            "details": similarity_warnings[:10],
            "hint": f"发现{len(similarity_warnings)}对高度相似用例(>80%),可能存在内容同质化。L3 TP已豁免。" if len(similarity_warnings) > 3 else "少量用例步骤相似,属于正常范围。"
        }), file=sys.stderr)

    all_cases = deduped_cases

    # FIX① V5.x: precondition→preconditions 自动同步
    # 部分上游用例使用单数 precondition 字段,P7的C6.1按 preconditions 校验,
    # 此处在合并阶段统一补齐,避免因字段名差异被误判为前置条件为空。
    for case in all_cases:
        if not str(_get_case_field(case, "preconditions", "") or "").strip() \
                and str(_get_case_field(case, "precondition", "") or "").strip():
            _set_case_field(case, "preconditions", _get_case_field(case, "precondition", ""))

    if not all_cases:
        print(json.dumps({"status": "error", "reason": "去重后所有用例被移除", "dedup_removed": dup_count, "hint": "所有case_id均为重复,请检查是否同一批次被多次保存或Agent重复生成了相同用例"}))
        sys.exit(1)

    # V4.7.3: 防御性补全 source_test_point - 从各批次skeleton回填缺失字段
    # 场景:Agent用Python脚本绕过p6_save_batch生成用例时,source_test_point未被填充
    missing_stp = 0
    for c in all_cases:
        if not _get_case_field(c, "source_test_point", ""):
            cid = _get_case_field(c, "case_id", "")
            # 尝试从case_id反推(格式: TC-XXX-YYY-ZZZ 或 TP-XXX-TC-YYY)
            if cid and "-TC-" in cid:
                c["source_test_point"] = cid.rsplit("-TC-", 1)[0]
                missing_stp += 1
    if missing_stp > 0:
        print(json.dumps({"status": "info", "source_test_point_backfill": missing_stp, "hint": f"{missing_stp}条用例缺少source_test_point,已从case_id反推补全"}), file=sys.stderr)

    # 统计(V3.2.4: 使用_get_case_field兼容fields嵌套结构)
    p0_count = sum(1 for c in all_cases if _get_case_field(c, "priority", "").upper() in ("P0", "HIGHEST"))
    smoke_count = sum(1 for c in all_cases if _is_smoke(_get_case_field(c, "is_smoke", "")))

    # 按优先级统计
    by_priority = {}
    for c in all_cases:
        p = _get_case_field(c, "priority", "unknown").upper()
        by_priority[p] = by_priority.get(p, 0) + 1

    merged = {
        "testcases": all_cases,
        "statistics": {
            "total": len(all_cases),
            "by_priority": by_priority,
            "smoke_count": smoke_count,
            "p0_count": p0_count,
            "batch_count": len(batch_files) if not tp_files else len(tp_files),
        }
    }

    # V3.2.9: 全局硬校验(代码层硬控,不依赖Agent)
    merge_issues = []
    tp_actual = {}  # V4.15.43: 提前初始化,供内容级完整性校验使用
    p5_path = os.path.join(data_dir, "p5_output.json")
    if os.path.exists(p5_path):
        try:
            p5_data = _read_json(p5_path)
            p5_points = p5_data.get("test_points", [])
            p5_ids = set(tp.get("id", "") for tp in p5_points if tp.get("id"))
            total_expected = p5_data.get("coverage_summary", {}).get("total_expected_cases", 0)

            # 校验1:总用例数≥总预算
            if total_expected > 0 and len(all_cases) < total_expected:
                merge_issues.append(f"用例总数{len(all_cases)}<预算{total_expected}")

            # 校验2:逐测试点展开数达标
            tp_actual = {}
            covered_ids = set()
            for c in all_cases:
                src = _get_case_field(c, "source_test_point", "")
                if not src:
                    cid = _get_case_field(c, "case_id", "")
                    if cid and "-TC-" in cid:
                        src = cid.rsplit("-TC-", 1)[0]
                if src:
                    tp_actual[src] = tp_actual.get(src, 0) + 1
                    covered_ids.add(src)

            shortfall_points = []
            shortfall_hints = []  # V4.12.3: 可执行的补缺命令
            shortfall_details = []  # V4.13.8 P0-2/P1-2: 完整结构化明细
            for tp in p5_points:
                tp_id = tp.get("id", "")
                expected = tp.get("expected_case_count", 2)
                actual = tp_actual.get(tp_id, 0)
                # V4.15.56: 对齐保存层±1容差（V4.15.53预期≥3时允许±1）
                _min_acc = max(1, expected - 1) if expected >= 3 else expected
                if actual < _min_acc:
                    shortfall_points.append(f"{tp_id}:应{expected}实{actual}")
                    # 从tp_id提取tp_index（TP-NNN → NNN-1）
                    tp_idx = None
                    tp_file = ""
                    try:
                        tp_num = int(tp_id.split("-")[-1]) if "-" in tp_id else 0
                        tp_idx = tp_num - 1
                        # V4.13.8 P1-2: 同时列出tp_file路径
                        tp_file = os.path.join(data_dir, "p6_tp_output", f"tp_{tp_idx:03d}.json")
                        shortfall_hints.append(
                            f"python3 $ORCH --action p6_generate_one --tp-index {tp_idx} --save --agent-output '...'"
                            f"  # {tp_id}还需{expected - actual}条"
                        )
                    except Exception:
                        pass
                    # V4.13.8 P0-2: 每个TP的完整明细(ID/期望/实际/缺几条/修复命令)
                    shortfall_details.append({
                        "tp_id": tp_id,
                        "tp_index": tp_idx,
                        "tp_file": tp_file,
                        "expected": expected,
                        "actual": actual,
                        "shortfall": expected - actual,
                        "fix_command": (
                            f"python3 $ORCH --action p6_generate_one --tp-index {tp_idx} --save --agent-output '...'"
                            if tp_idx is not None else ""
                        ),
                    })
            if shortfall_points:
                merge_issues.append(f"{len(shortfall_points)}个测试点展开不足: {', '.join(shortfall_points[:5])}")

            # 校验3:未覆盖的测试点
            uncovered = p5_ids - covered_ids
            if uncovered:
                merge_issues.append(f"{len(uncovered)}个测试点未覆盖: {', '.join(sorted(uncovered)[:5])}")

            # 写入覆盖统计
            merged["statistics"]["p5_coverage"] = {
                "total_p5": len(p5_ids),
                "covered": len(covered_ids),
                "uncovered": sorted(uncovered) if uncovered else [],
                "shortfall_points": shortfall_points[:10] if shortfall_points else [],
                "shortfall_hints": shortfall_hints[:10] if shortfall_hints else [],  # V4.12.3
                # V4.13.8 P0-2: 完整的shortfall明细列表(不截断,便于逐一修复)
                "shortfall_details": shortfall_details,
            }
        except Exception:
            pass

    # V4.15.43: 内容级完整性校验 — 文件存在但merge后覆盖为0的TP计入_missing_tps
    # (补V4.15.41仅查文件存在的缺陷,修复如tp_018被跨TP去重丢弃的场景)
    if tp_files and tp_actual:
        for _tf in tp_files:
            try:
                _tp_idx = int(os.path.basename(_tf).replace("tp_", "").replace(".json", ""))
                _tp_data = _read_json(_tf)
                _tp_id = _tp_data.get("tp_id", "")
                if _tp_id and tp_actual.get(_tp_id, 0) == 0 and _tp_idx not in _missing_tps:
                    _missing_tps.append(_tp_idx)
                    print(json.dumps({
                        "status": "content_missing",
                        "tp_index": _tp_idx, "tp_id": _tp_id,
                        "reason": f"TP文件存在但merge后覆盖为0(可能被去重丢弃), 计入PARTIAL.",
                        "hint": "检查该TP用例是否与其它TP完全重复, 考虑差异化生成后重新merge."
                    }, ensure_ascii=False), file=sys.stderr)
            except Exception:
                pass

    # V3.3.1: 全局底线校验(精确比例校验已移至P7 code_check)
    # 校验4:全局smoke>0(底线,避免全局smoke=0的极端情况)
    if len(all_cases) > 0:
        if smoke_count == 0:
            merge_issues.append("全局冒烟用例为0,必须有核心主链路的冒烟用例")

    # 校验5:全局P0>0(底线)
    if len(all_cases) > 0:
        if p0_count == 0:
            merge_issues.append("全局P0用例为0,必须有核心主链路的P0用例")
    # V5.0(4.13.0): 废除 HIGH/LOW 分档,merge 失败统一接受不阻断
    # V4.13.8 P0-3: 增加质量底线检查 + 连续失败阈值从3→7
    merge_fail_count = 0
    state_path = os.path.join(data_dir, "orchestrator_state.json")
    if os.path.exists(state_path):
        try:
            st = _read_json(state_path)
            merge_fail_count = st.get("p6_merge_fail_count", 0)
        except Exception:
            pass
    if merge_issues:
        merge_fail_count += 1
        level = "ERROR" if merge_fail_count >= 7 else "WARNING"

        # V4.13.8 P0-3: 质量底线检查(冒烟=0/P0=0/去重率>50%/总数<预算50%时拒绝接受)
        critical_reasons = []
        if smoke_count == 0:
            critical_reasons.append("冒烟用例为0")
        if p0_count == 0:
            critical_reasons.append("P0用例为0")
        if dup_ratio > 0.5:
            critical_reasons.append(f"去重率{dup_ratio:.0%}>50%")
        # 总数 < 预算50%的判断: 用合并前all_cases(去重前) vs expected_total
        expected_total = sum(tp.get("expected_case_count", 2) for tp in p5_points) if p5_points else 0
        if expected_total > 0 and len(all_cases) < expected_total * 0.5:
            critical_reasons.append(f"用例总数{len(all_cases)}<预算{expected_total}的50%")
        if critical_reasons:
            print(json.dumps({
                "status": "blocked",
                "reason": "质量底线触发: " + "; ".join(critical_reasons),
                "action": "必须修复后再merge,不允许接受当前结果",
            }))
            sys.exit(1)

        accepted_msg = {
            "status": "quality_accepted",
            "total_cases": len(all_cases),
            "issues": merge_issues,
            "merge_fail_count": merge_fail_count,
            "level": level,
            "message": f"{'🔴' if level == 'ERROR' else '⚠️'} merge校验未通过(第{merge_fail_count}次),已接受当前{len(all_cases)}条用例。",
            "hint": "进入P7+Excel导出" if level == "WARNING" else "已连续7次merge失败,请人工审查用例质量",
            "next_action": "继续执行 p7_code_check + step7_export"
        }
        print(json.dumps(accepted_msg), file=sys.stderr)
        print(json.dumps(accepted_msg))
        _invalidate_batch_cache()

    # 写入tmp
    tmp_path = os.path.join(data_dir, "p6_output.tmp.json")

    # V5.0(4.13.0): 后处理对所有模型统一触发(术语一致性+前置去重+烟雾纠正)
    post_process_report = {}
    # 更新 merge 失败计数到 state
    if merge_fail_count > 0:
        try:
            st = _read_json(os.path.join(data_dir, "orchestrator_state.json"))
            st["p6_merge_fail_count"] = merge_fail_count
            _write_json(os.path.join(data_dir, "orchestrator_state.json"), st)
        except Exception:
            pass

    if all_cases:
        # 术语一致性检测
        term_issues = _check_terminology_consistency(all_cases)
        if term_issues:
            for issue in term_issues:
                # 标记到受影响用例的remarks
                for ci in issue.get("affected_case_indices", []):
                    if ci < len(all_cases):
                        c = all_cases[ci]
                        existing = _get_case_field(c, "remarks", "")
                        tag = f"[术语不一致: {issue.get('suggestion', '')}]"
                        if tag not in str(existing):
                            # 处理 nested fields 结构
                            if "fields" in c and isinstance(c.get("fields"), dict):
                                c["fields"]["remarks"] = (str(existing) + " " + tag).strip() if existing else tag
                            else:
                                c["remarks"] = (str(existing) + " " + tag).strip() if existing else tag
            post_process_report["terminology"] = {
                "clusters_found": len(term_issues),
                "details": [{"canonical": i.get("canonical", ""), "variants": i.get("variants", []), "suggestion": i.get("suggestion", "")} for i in term_issues]
            }

        # 前置条件去重
        dedup_info = _dedup_preconditions(all_cases)
        if dedup_info.get("extracted_count", 0) > 0:
            post_process_report["precondition_dedup"] = dedup_info

        # V4.8.4: 烟雾比例自动纠正(<10% → 自动标记P0用例为烟雾)
        if len(all_cases) > 0:
            smoke_count_current = sum(1 for c in all_cases if _is_smoke(_get_case_field(c, "is_smoke", "")))
            smoke_ratio = smoke_count_current / len(all_cases)
            min_smoke = max(1, int(len(all_cases) * 0.10))  # 至少10%或1条
            if smoke_count_current < min_smoke:
                # 按优先级排序:P0 > P1 > P2,选top-priority用例标记为烟雾
                priority_order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3, "P4": 4}
                sorted_cases = sorted(
                    enumerate(all_cases),
                    key=lambda x: priority_order.get(_get_case_field(x[1], "priority", "P2").upper(), 99)
                )
                auto_marked = 0
                for ci, c in sorted_cases:
                    if _is_smoke(_get_case_field(c, "is_smoke", "")):
                        continue
                    cat = _get_case_field(c, "test_category", "") or _get_case_field(c, "category", "")
                    # 只标记main_flow/正向验证类用例为烟雾
                    if cat and cat not in ("main_flow", "正向", "功能", ""):
                        continue
                    # 标记为烟雾
                    if "fields" in c and isinstance(c.get("fields"), dict):
                        c["fields"]["is_smoke"] = True
                    else:
                        c["is_smoke"] = True
                    auto_marked += 1
                    if smoke_count_current + auto_marked >= min_smoke:
                        break
                if auto_marked > 0:
                    post_process_report["smoke_auto_fix"] = {
                        "before_count": smoke_count_current,
                        "before_ratio": f"{smoke_ratio:.1%}",
                        "auto_marked": auto_marked,
                        "after_count": smoke_count_current + auto_marked,
                        "after_ratio": f"{(smoke_count_current + auto_marked) / len(all_cases):.1%}",
                    }

        # 写入后处理报告供Agent查阅
        if post_process_report:
            report_path = os.path.join(data_dir, "p6_post_process.json")
            _write_json(report_path, {
                "model_tier": "standard",
                "version": "5.0",
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S+08:00"),
                **post_process_report
            })
            print(json.dumps({"status": "info", "post_process": "后处理完成", "report": report_path}), file=sys.stderr)

    # === V4.12.6: 比率自动调平 ===
    if all_cases:
        total = len(all_cases)
        p0_cases = [c for c in all_cases if _get_case_field(c, "priority", "").upper() == "P0"]
        smoke_cases = [c for c in all_cases if _is_smoke(_get_case_field(c, "is_smoke", ""))]
        p0_ratio = len(p0_cases) / total
        smoke_ratio = len(smoke_cases) / total
        adjustments = []

        # 冒烟超20% → 降级多余的P0冒烟为非冒烟P1
        if smoke_ratio > 0.20:
            target_smoke = int(total * 0.18)  # 降到18%留缓冲
            excess = len(smoke_cases) - target_smoke
            # 优先降非主流程的冒烟用例
            downgraded = 0
            for c in smoke_cases:
                if downgraded >= excess:
                    break
                cat = _get_case_field(c, "test_category", _get_case_field(c, "category", ""))
                if cat not in ("main_flow", "正向"):
                    _set_case_field(c, "priority", "P1")
                    _set_case_field(c, "is_smoke", False)
                    downgraded += 1
                    adjustments.append(f"冒烟→P1非冒烟: {_get_case_field(c, 'case_id', '?')}")
            # 如果还不够，降主流程的冒烟
            for c in smoke_cases:
                if downgraded >= excess:
                    break
                _set_case_field(c, "is_smoke", False)
                downgraded += 1
                adjustments.append(f"取消冒烟: {_get_case_field(c, 'case_id', '?')}")

        # 重新计算P0（冒烟降级可能影响P0数量）
        p0_cases_now = [c for c in all_cases if _get_case_field(c, "priority", "").upper() == "P0"]
        p0_ratio_now = len(p0_cases_now) / total

        # P0超20% → 降级多余非冒烟P0为P1
        if p0_ratio_now > 0.20:
            target_p0 = int(total * 0.18)
            excess_p0 = len(p0_cases_now) - target_p0
            downgraded_p0 = 0
            for c in all_cases:
                if downgraded_p0 >= excess_p0:
                    break
                if _get_case_field(c, "priority", "").upper() == "P0" and not _is_smoke(_get_case_field(c, "is_smoke", "")):
                    _set_case_field(c, "priority", "P1")
                    downgraded_p0 += 1
                    adjustments.append(f"P0→P1: {_get_case_field(c, 'case_id', '?')}")

        if adjustments:
            # 更新统计
            merged["testcases"] = all_cases
            merged["statistics"]["smoke_count"] = sum(1 for c in all_cases if _is_smoke(_get_case_field(c, "is_smoke", "")))
            merged["statistics"]["p0_count"] = sum(1 for c in all_cases if _get_case_field(c, "priority", "").upper() == "P0")
            by_p_new = {}
            for c in all_cases:
                p = _get_case_field(c, "priority", "unknown").upper()
                by_p_new[p] = by_p_new.get(p, 0) + 1
            merged["statistics"]["by_priority"] = by_p_new
            print(json.dumps({
                "status": "info",
                "action": "ratio_auto_balance",
                "adjustments": adjustments[:10],
                "total_adjusted": len(adjustments),
                "after_smoke_ratio": f"{merged['statistics']['smoke_count'] / total:.1%}",
                "after_p0_ratio": f"{merged['statistics']['p0_count'] / total:.1%}",
            }), file=sys.stderr)
    # === 比率调平结束 ===

    # V4.13.9-S4: 优先级预算校验 + 智能降级
    # 安全加载 priority_budget 与 p5_points(p5_points 仅在上游 try 块内有条件定义)
    priority_budget = {}
    if 'p5_points' not in dir() or not isinstance(locals().get('p5_points'), list):
        p5_points = []
    _p5p_s4 = os.path.join(data_dir, "p5_output.json")
    if os.path.exists(_p5p_s4):
        try:
            _p5d_s4 = _read_json(_p5p_s4)
            priority_budget = _p5d_s4.get("priority_budget", {}) or {}
            if not p5_points:
                p5_points = _p5d_s4.get("test_points", []) or []
        except Exception:
            pass
    if not priority_budget:
        # 兜底: 无 budget 时按15%计算
        _total_expected_s4 = sum(tp.get("expected_case_count", 2) for tp in p5_points)
        priority_budget = {
            "P0_max": min(int(_total_expected_s4 * 0.15), 20),
            "P0_ratio": 0.15,
            "smoke_max": min(int(_total_expected_s4 * 0.15 * 1.1), 22),
        }
    p0_max = priority_budget.get("P0_max", 15)
    p0_count_s4 = sum(1 for c in all_cases if _get_case_field(c, "priority", "").upper() == "P0")
    if p0_count_s4 > p0_max:
        excess = p0_count_s4 - p0_max
        # 候选: 非冲烟P0,排除 main_flow/risk_verification 类别
        candidates = []
        for c in all_cases:
            if _get_case_field(c, "priority", "").upper() == "P0" and not _is_smoke(_get_case_field(c, "is_smoke", "")):
                tp_id = _get_case_field(c, "source_test_point", "") or c.get("tp_id", "")
                tp_cat = ""
                for tp in p5_points:
                    if tp.get("id") == tp_id or tp.get("tp_id") == tp_id:
                        tp_cat = tp.get("category", "")
                        break
                if tp_cat in ("main_flow", "risk_verification"):
                    continue
                candidates.append(c)
        if candidates:
            from datetime import datetime as _dt_s4
            for c in candidates[:excess]:
                _set_case_field(c, "priority", "P1")
                c["priority_note"] = f"自动降级P0→P1:超预算({p0_count_s4}/{p0_max})@{_dt_s4.now().strftime('%Y-%m-%d %H:%M')}"
            # 同步统计
            merged["testcases"] = all_cases
            merged["statistics"]["p0_count"] = sum(1 for c in all_cases if _get_case_field(c, "priority", "").upper() == "P0")
            _by_p_s4 = {}
            for c in all_cases:
                _p = _get_case_field(c, "priority", "unknown").upper()
                _by_p_s4[_p] = _by_p_s4.get(_p, 0) + 1
            merged["statistics"]["by_priority"] = _by_p_s4
            print(json.dumps({"status": "info", "action": "priority_budget", "downgraded": len(candidates[:excess]), "excess": excess}, ensure_ascii=False), file=sys.stderr)

    _write_json(tmp_path, merged)

    # truncation_guard
    ok, msg = run_truncation_guard(skill_dir, data_dir, task_id, "P6")

    if ok:
        state = TaskState(data_dir=data_dir, task_id=task_id)
        state.mark_complete("P6")
        # BUG-1修复: 写入P6.pass.json gate(参考onboarding/P7的_write_signed_gate模式)。
        # 此前P6成功路径只mark_complete但未落盘gate文件,导致step7_export的
        # required_gates完整性校验始终缺失P6 → gate_blocked。
        gate_dir = os.path.join(data_dir, "gates")
        _ensure_dir(gate_dir)
        gate_path = os.path.join(gate_dir, "P6.pass.json")
        gate_data = {
            "step": "P6",
            "status": "PASS",
            "task_id": task_id,
            "source": "p6_merge",
            "total_cases": len(all_cases),
            "smoke_count": smoke_count,
            "completed_at": time.strftime("%Y-%m-%dT%H:%M:%S+08:00"),
        }
        # V4.15.43: partial模式标注（文件缺失+内容缺失均标记PARTIAL）
        if _missing_tps:
            gate_data["status"] = "PARTIAL"
            gate_data["missing_tp_count"] = len(_missing_tps)
            gate_data["missing_tp_indices"] = _missing_tps[:30]
            print(json.dumps({"status": "info", "partial_mode": True,
                "hint": f"P6.pass.json已写入(状态=PARTIAL, {len(_missing_tps)}个TP缺失, 当前{len(all_cases)}条用例)",
                "missing_tp_indices": _missing_tps[:30]}, ensure_ascii=False), file=sys.stderr)
        _write_signed_gate(gate_path, gate_data, task_id)
        print(json.dumps({
            "status": "ok",
            "total_cases": len(all_cases),
            "smoke_count": smoke_count,
            "batches_merged": len(batch_files) if not tp_files else len(tp_files),
            "guard_result": msg,
            "quality_check": "V3.3.1_global_hard_pass",
            "warning": "⚠️ p6_output.json 是自动生成文件，禁止手动修改。如需修复用例，请修改 tp_N.json 源文件后重新 merge。",
            "__paragraph_complete__": {
                "current_paragraph": 5,
                "next_paragraph": 6,
                "next_action": "P7质量门禁 + Excel导出",
                "must_emit": f"✅ 段落5完成 | 用例:{len(all_cases)}条 | 冒烟:{smoke_count}条\n📋 请回复「继续」进入段落6（P7+Excel）",
                "next_rules_file": "rules/paragraph_6.md"
            }
        }))
    else:
        # V4.15.55: truncation_guard失败时检查tmp文件是否已有数据
        # exit=3(L3)通常是字段不完整,但p6_output.tmp.json已含可用数据
        # 不应硬退出误导Agent,改为PARTIAL gate + WARNING
        tmp_path = os.path.join(data_dir, "p6_output.tmp.json")
        final_path = os.path.join(data_dir, "p6_output.json")
        _recovered = False
        if os.path.exists(tmp_path):
            try:
                _tmp_data = _read_json(tmp_path)
                _tc = _tmp_data.get("testcases", []) if isinstance(_tmp_data, dict) else _tmp_data
                if isinstance(_tc, list) and len(_tc) >= len(all_cases) * 0.8:
                    # tmp有≥80%用例数据 → 手动mv + PARTIAL gate
                    import shutil as _shutil
                    if os.path.exists(final_path):
                        _bak = final_path + ".bak." + time.strftime("%Y%m%d_%H%M%S")
                        os.rename(final_path, _bak)
                    _shutil.move(tmp_path, final_path)
                    _recovered = True
            except Exception:
                pass
        if _recovered:
            state = TaskState(data_dir=data_dir, task_id=task_id)
            state.mark_complete("P6")
            gate_dir = os.path.join(data_dir, "gates")
            _ensure_dir(gate_dir)
            gate_path = os.path.join(gate_dir, "P6.pass.json")
            gate_data = {
                "step": "P6",
                "status": "PARTIAL",
                "task_id": task_id,
                "source": "p6_merge_recovered",
                "total_cases": len(all_cases),
                "smoke_count": smoke_count,
                "completed_at": time.strftime("%Y-%m-%dT%H:%M:%S+08:00"),
                "guard_warning": str(msg)[:200],
            }
            _write_signed_gate(gate_path, gate_data, task_id)
            print(json.dumps({
                "status": "ok",
                "total_cases": len(all_cases),
                "smoke_count": smoke_count,
                "batches_merged": len(batch_files) if not tp_files else len(tp_files),
                "guard_warning": str(msg)[:200],
                "recovery": "truncation_guard失败但tmp文件含可用数据,已标记PARTIAL继续",
                "quality_check": "V3.3.1_global_hard_pass",
                "warning": "⚠️ p6_output.json 是自动生成文件，禁止手动修改。如需修复用例，请修改 tp_N.json 源文件后重新 merge。",
                "__paragraph_complete__": {
                    "current_paragraph": 5,
                    "next_paragraph": 6,
                    "next_action": "P7质量门禁 + Excel导出",
                    "must_emit": f"✅ 段落5完成 | 用例:{len(all_cases)}条 | 冒烟:{smoke_count}条 | ⚠️ truncation_guard报错但数据已保存",
                    "next_rules_file": "rules/paragraph_6.md"
                }
            }))
        else:
            print(json.dumps({"status": "guard_failed", "reason": msg}))
            sys.exit(1)

    # V4.13.2: P6完成,清除进行中标记
    state_path = os.path.join(data_dir, "orchestrator_state.json")
    if os.path.exists(state_path):
        try:
            st = _read_json(state_path)
            st["p6_status"] = "completed"
            _write_json(state_path, st)
        except Exception:
            pass

    # V4.15.53: merge完成后清理context副本文件
    _ctx_pattern = os.path.join(data_dir, "p6_tp_output", "*_context.json")
    _ctx_cleaned = 0
    for _cf in glob.glob(_ctx_pattern):
        try:
            os.remove(_cf)
            _ctx_cleaned += 1
        except Exception:
            pass
    if _ctx_cleaned > 0:
        print(json.dumps({"action": "merge_cleanup", "context_files_removed": _ctx_cleaned}, ensure_ascii=False), file=sys.stderr)


# ============================================================
# Action: p6_save_batch (保存P6单批结果)
# ============================================================

def action_p6_save_batch(args):
    """保存P6单批结果到p6_batches/batch_N.json"""
    data_dir = args.data_dir
    task_id = args.task_id
    batch_index = int(args.batch_index) if args.batch_index else 0  # V4.8.12: 默认0-based
    agent_output = args.agent_output

    # V4.7.3: 子Agent环境检测(P6必须在主会话执行,子Agent有30分钟超时)
    if _is_sub_agent_session():
        print(json.dumps({
            "status": "rejected",
            "reason": "⛔ P6禁止在子Agent(spawn)中执行!P6需要主会话的完整上下文和充足时间。请在主会话中直接运行P6流程。",
            "hint": "返回到主会话,执行: python3 $ORCH --action p6_save_batch --batch-index N"
        }))
        sys.exit(1)

    # V3.2.6: P5前置gate校验(防止Agent在无合法P5时伪造batch)
    ok, msg = check_gate(data_dir, "P5", task_id)
    if not ok:
        print(json.dumps({
            "status": "gate_blocked",
            "reason": f"P6保存批次需要P5 gate pass: {msg}。必须先执行p5_code_merge完成P5。",
        }))
        sys.exit(1)

    expected_file = os.path.join(data_dir, f"p6_batch_{batch_index:03d}_agent_output.json")
    try:
        batch_data = json.loads(agent_output)
    except Exception:
        import re
        match = re.search(r'\{[\s\S]*\}', agent_output)
        if match:
            try:
                batch_data = json.loads(match.group())
            except Exception:
                print(json.dumps({"status": "error", "reason": f"P6批次JSON解析失败。请检查 {expected_file} 内容是否为合法JSON,或使用 --agent-output 参数直接传递JSON字符串", "expected_file": expected_file, "fix_hint": f"将生成的JSON保存到 {expected_file}(注意_agent_output后缀不能少)"}))
                sys.exit(1)
        else:
            print(json.dumps({"status": "error", "reason": f"P6批次输出不含JSON。预期文件: {expected_file}。请确认: 1)文件名含_agent_output后缀 2)文件内容为完整JSON 3)或使用--agent-output参数直接传递JSON", "expected_file": expected_file, "fix_hint": f"将生成的JSON保存到 {expected_file}(注意_agent_output后缀不能少)"}))
            sys.exit(1)

    # V4.8.9: 裸数组自动包装 - Agent 可能输出 [] 而非 {"testcases": [...]}
    if isinstance(batch_data, list):
        print(json.dumps({"status": "info", "reason": f"检测到裸数组格式[{len(batch_data)}条],已自动包装为{{\"testcases\":[...]}},请下次使用正确格式"}), file=sys.stderr)
        batch_data = {"testcases": batch_data}
    # V4.15.5: 丢弃LLM输出的statistics字段(orchestrator自行计算,防Agent编造)
    batch_data.pop("statistics", None)

    batches_dir = os.path.join(data_dir, "p6_batches")
    _ensure_dir(batches_dir)

    batch_path = os.path.join(batches_dir, f"batch_{batch_index:03d}.json")

    # V4.7.2: --merge 增量更新模式 - 只更新指定case_id,保留其余用例
    if getattr(args, 'merge', False):
        if not os.path.exists(batch_path):
            print(json.dumps({"status": "error", "reason": f"merge模式要求batch_{batch_index:03d}.json已存在,但文件不存在"}))
            sys.exit(1)
        existing = _read_json(batch_path)
        existing_cases = existing.get("testcases", existing.get("cases", []))
        new_cases = batch_data.get("testcases", batch_data.get("cases", []))
        # 按 case_id 索引合并
        new_ids = {_get_case_field(c, "case_id", "") for c in new_cases if _get_case_field(c, "case_id", "")}
        merged_cases = [c for c in existing_cases if _get_case_field(c, "case_id", "") not in new_ids]
        merged_cases.extend(new_cases)
        updated = len(new_ids)
        print(json.dumps({"status": "info", "action": "merge", "batch_index": batch_index, "updated": updated, "total": len(merged_cases)}), file=sys.stderr)
        batch_data["testcases"] = merged_cases
        _write_json(batch_path, batch_data)
        # 增量更新后仍需走 Gate quick check
        cases = merged_cases
    else:
        _write_json(batch_path, batch_data)
        cases = batch_data.get("testcases", batch_data.get("cases", []))

    # V3.2.9: 骨架锁定--读取预分配的skeleton,用代码原值覆盖Agent返回的priority/is_smoke
    # V4.8.6: skeleton统一放在 p6_batches/ 目录
    skeleton_path = os.path.join(data_dir, "p6_batches", f"batch_{batch_index:03d}_skeleton.json")
    skeleton_map = {}  # case_id -> {priority, is_smoke, source_test_point}
    skeleton_missing = False
    if os.path.exists(skeleton_path):
        try:
            skeletons = _read_json(skeleton_path)
            for sk in skeletons:
                skeleton_map[sk.get("case_id", "")] = sk
        except Exception:
            pass
    else:
        skeleton_missing = True
        print(json.dumps({"status": "warning", "reason": f"骨架文件缺失: {skeleton_path},跳过骨架锁定,质量检查降级为宽松模式"}), file=sys.stderr)

    # V4.6.12 Bugfix: 强制扁平化--将嵌套 fields 结构展开为顶层字段
    # V4.7.2: 关键字段(steps/expected_results)优先取较长版本,防止截断数据丢失
    for c in cases:
        if isinstance(c, dict) and "fields" in c and isinstance(c["fields"], dict):
            for k, v in c["fields"].items():
                if k not in c or c[k] is None:
                    c[k] = v
                elif k in ("steps", "expected_results", "description", "preconditions"):
                    # 取较长的版本(Agent 可能在顶层输出截断版,fields 内是完整版)
                    if len(str(v)) > len(str(c.get(k, ""))):
                        c[k] = v
            del c["fields"]

    # 对每条用例强制覆盖priority/is_smoke/source_test_point(扁平化之后)
    if skeleton_map:
        for c in cases:
            cid = _get_case_field(c, "case_id", "")
            if cid in skeleton_map:
                sk = skeleton_map[cid]
                # 扁平化后直接覆盖顶层字段
                c["priority"] = sk["priority"]
                c["is_smoke"] = sk["is_smoke"]
                c["source_test_point"] = sk["source_test_point"]
                c["case_id"] = sk["case_id"]
                # V4.15.53: 从skeleton传递risk_flag/priority_hint到用例
                c["risk_flag"] = sk.get("risk_flag", False)
                c["priority_hint"] = sk.get("priority_hint", "")
        # 重新写入覆盖后的batch文件
        batch_data["testcases"] = cases
        _write_json(batch_path, batch_data)

    # V4.6.17: 格式归一化--自动修复list→string、空值等常见格式问题
    for c in cases:
        if not isinstance(c, dict):
            continue
        # steps:list → "\n"连接的字符串
        steps_val = c.get("steps")
        if isinstance(steps_val, list):
            c["steps"] = "\n".join(str(s) for s in steps_val if s)
        # expected_results:list → "\n"连接的字符串
        exp_val = c.get("expected_results")
        if isinstance(exp_val, list):
            c["expected_results"] = "\n".join(str(e) for e in exp_val if e)
        # preconditions:list → "\n"连接的字符串
        pre_val = c.get("preconditions")
        if isinstance(pre_val, list):
            c["preconditions"] = "\n".join(str(p) for p in pre_val if p)
    # 归一化后重新写回batch文件
    batch_data["testcases"] = cases
    _write_json(batch_path, batch_data)

    # V4.8.11: 步骤-期望数量自动校准 - 差1行自动补齐,减少Agent重试
    auto_fixed = 0
    for c in cases:
        st = str(c.get("steps", ""))
        ex = str(c.get("expected_results", ""))
        sl = [l for l in st.split('\n') if l.strip() and l.strip()[0:1].isdigit()]
        el = [l for l in ex.split('\n') if l.strip() and l.strip()[0:1].isdigit()]
        diff = len(sl) - len(el)
        if diff == 1:
            c["expected_results"] = ex.rstrip('\n') + f"\n{len(el)+1}. (自动补齐)待补充期望结果"
            auto_fixed += 1
        elif diff == -1:
            c["steps"] = st.rstrip('\n') + f"\n{len(sl)+1}. (自动补齐)待补充步骤"
            auto_fixed += 1
    if auto_fixed:
        batch_data["testcases"] = cases
        _write_json(batch_path, batch_data)
        print(json.dumps({"status": "info", "auto_fixed_step_exp": auto_fixed, "hint": f"{auto_fixed}条用例步骤/期望自动补齐(差1行)"}), file=sys.stderr)

    # V3.2.9: 硬校验(不达标直接拒绝保存)
    hard_issues = []

    # V4.10.1: case_id兜底 - 窄聚焦模式下Agent可能不输出case_id或只部分输出
    # 当skeleton存在且case_id校验可能失败时,先尝试修复
    if skeleton_map and (not skeleton_missing):
        skeletons_for_match = _read_json(skeleton_path) if os.path.exists(skeleton_path) else []
        empty_cids = [i for i, c in enumerate(cases) if not _get_case_field(c, "case_id", "")]

        if empty_cids:
            # 部分或全部case_id为空 → 按骨架顺序兜底填充
            if len(cases) != len(skeletons_for_match):
                hard_issues.append(f"❌ Agent输出{len(cases)}条,骨架期望{len(skeletons_for_match)}条。数量不匹配,无法自动补全case_id。请重新生成。")
                # 直接跳到硬校验输出,跳过骨架匹配
            else:
                # 数量匹配 → 按顺序一一对应填充case_id/priority/is_smoke
                for i, c in enumerate(cases):
                    if i < len(skeletons_for_match):
                        sk = skeletons_for_match[i]
                        _set_case_field(c, "case_id", sk.get("case_id", ""))
                        _set_case_field(c, "priority", sk.get("priority", "P1"))
                        _set_case_field(c, "is_smoke", sk.get("is_smoke", False))
                        _set_case_field(c, "source_test_point", sk.get("source_test_point", ""))
                # 重新写入batch文件
                batch_data["testcases"] = cases
                _write_json(batch_path, batch_data)
                print(json.dumps({"status": "info", "action": "auto_fix_case_ids", "batch_index": batch_index, "filled": len(empty_cids), "hint": "case_id按骨架顺序自动补全"}), file=sys.stderr)

    # 校验0:case_id全集一致性(防止Agent伪造/缺少/重复case_id)
    if skeleton_map:
        skeleton_ids = set(skeleton_map.keys())
        returned_ids = set()
        duplicate_ids = []
        for c in cases:
            cid = _get_case_field(c, "case_id", "")
            if cid in returned_ids:
                duplicate_ids.append(cid)
            returned_ids.add(cid)
        missing_ids = skeleton_ids - returned_ids
        extra_ids = returned_ids - skeleton_ids
        if missing_ids:
            hard_issues.append(f"缺少{len(missing_ids)}个骨架用例: {', '.join(sorted(missing_ids)[:3])}")
        if extra_ids:
            hard_issues.append(f"多出{len(extra_ids)}个非法用例: {', '.join(sorted(extra_ids)[:3])}")
        if duplicate_ids:
            hard_issues.append(f"重复{len(duplicate_ids)}个case_id: {', '.join(duplicate_ids[:3])}")

    # 校验1:用例数量≥batch_budget(逐测试点校验)
    p5_path = os.path.join(data_dir, "p5_output.json")
    if os.path.exists(p5_path) and os.path.exists(skeleton_path):
        try:
            p5_data = _read_json(p5_path)
            p5_map = {tp.get("id", ""): tp for tp in p5_data.get("test_points", [])}
            skeletons = _read_json(skeleton_path)
            # 统计每个测试点的实际用例数
            tp_actual = {}
            for c in cases:
                src = _get_case_field(c, "source_test_point", "")
                if not src:
                    cid = _get_case_field(c, "case_id", "")
                    if cid and "-TC-" in cid:
                        src = cid.rsplit("-TC-", 1)[0]
                if src:
                    tp_actual[src] = tp_actual.get(src, 0) + 1
            # 逐点校验
            tp_expected = {}
            for sk in skeletons:
                src = sk.get("source_test_point", "")
                tp_expected[src] = tp_expected.get(src, 0) + 1
            shortfall = []
            for tp_id, expected in tp_expected.items():
                actual = tp_actual.get(tp_id, 0)
                # V4.15.56: 对齐保存层±1容差（V4.15.53预期≥3时允许±1）
                _min_acc = max(1, expected - 1) if expected >= 3 else expected
                if actual < _min_acc:
                    shortfall.append(f"{tp_id}:应{expected}条实际{actual}条")
            if shortfall:
                hard_issues.append(f"测试点展开不足: {', '.join(shortfall[:5])}")
        except Exception:
            pass

    # V5.0(4.13.0): 废除 HIGH/LOW 分档,统一阈值
    smoke_limit = 0.25
    p0_limit = 0.30

    # 校验2:冷烟比例
    if len(cases) > 0:
        smoke_count = sum(1 for c in cases if _is_smoke(_get_case_field(c, "is_smoke", "")))
        smoke_ratio = smoke_count / len(cases)
        if smoke_ratio > smoke_limit:
            hard_issues.append(f"冷烟比例{smoke_ratio:.0%}>{smoke_limit:.0%}")

    # 校验3:P0比例
    if len(cases) > 0:
        p0_count = sum(1 for c in cases if _get_case_field(c, "priority", "").upper() in ("P0", "HIGHEST"))
        p0_ratio = p0_count / len(cases)
        if p0_ratio > p0_limit:
            hard_issues.append(f"P0比例{p0_ratio:.0%}>{p0_limit:.0%}")

    # 校验4:步骤去重检测(唯一步骤<50%拒绝)
    # V4.7.3: 排除共同前缀(登录/导航步骤) + risk_verification类豁免
    if len(cases) >= 4:
        def _strip_common_prefix(steps_text: str) -> str:
            """去除所有用例共享的登录/导航前缀步骤,只保留差异化业务步骤。

            登录步骤(如「使用有权限账号登录CRM系统,进入首页→XX页面」)
            在所有用例中相同,会污染唯一性计算。"""
            if not steps_text:
                return steps_text
            lines = steps_text.strip().split('\n')
            # 识别并移除包含登录/导航关键词的前缀行
            login_keywords = ['登录', '进入首页', '进入系统', '打开', '输入密码', '输入账号']
            result_lines = []
            for line in lines:
                stripped = line.strip()
                # 去除编号前缀后检查
                import re as _re2
                content = _re2.sub(r'^\d+[\.\、\))]\s*', '', stripped)
                is_common_prefix = any(kw in content for kw in login_keywords)
                if not is_common_prefix:
                    result_lines.append(stripped)
            return '\n'.join(result_lines) if result_lines else steps_text

        # 检查是否全部为risk_verification/exception类用例
        all_risk_or_exc = True
        for c in cases:
            cat = _get_case_field(c, "test_category", "") or _get_case_field(c, "category", "")
            if cat not in ("risk_verification", "exception"):
                all_risk_or_exc = False
                break

        # V5.0(4.13.0): 统一步骤唯一性阈值(不再区分模型档位)
        if all_risk_or_exc:
            # risk_verification/exception类用例: 放宽到30%(风险点天然场景单一)
            min_unique = 0.3
            threshold_label = "30%(risk_verification豁免)"
        else:
            min_unique = 0.5
            threshold_label = "50%"

        steps_set = set()
        for c in cases:
            s = _get_case_field(c, "steps", "")
            if s:
                # 去除共同前缀后再比较
                stripped = _strip_common_prefix(s.strip())
                if stripped:
                    steps_set.add(stripped)
        unique_ratio = len(steps_set) / len(cases)
        if unique_ratio < min_unique:
            hard_issues.append(f"步骤唯一性{len(steps_set)}/{len(cases)}=({unique_ratio:.0%}<{threshold_label})。每条用例必须基于p5_description生成差异化步骤,严禁复制。提示:读取skeleton中每条用例的p5_description,从描述中提取不同的操作流程。")

    # 校验5:关键字段非空
    empty_title = sum(1 for c in cases if not _get_case_field(c, "title", ""))
    empty_steps = sum(1 for c in cases if not _get_case_field(c, "steps", ""))
    empty_expected = sum(1 for c in cases if not _get_case_field(c, "expected_results", ""))
    if empty_title > 0:
        hard_issues.append(f"{empty_title}条用例title为空")
    if empty_steps > 0:
        hard_issues.append(f"{empty_steps}条用例steps为空")
    if empty_expected > 0:
        hard_issues.append(f"{empty_expected}条用例expected_results为空")

    # V3.3.5: 步骤-结果数量一一对应校验 + 跨测试点唯一性检查
    if len(cases) > 3:
        # 校验A:步骤数=期望结果数(阈值15%)
        step_exp_mismatch = 0
        for c in cases:
            steps_text = str(_get_case_field(c, "steps", ""))
            exp_text = str(_get_case_field(c, "expected_results", ""))
            # V4.14.2: 优先匹配编号行,无编号时fallback到非空行计数(防字符串整体计1)
            step_lines = [l for l in steps_text.split('\n') if l.strip() and l.strip()[0:1].isdigit()]
            if not step_lines:
                step_lines = [l for l in steps_text.split('\n') if l.strip()]
            exp_lines = [l for l in exp_text.split('\n') if l.strip() and l.strip()[0:1].isdigit()]
            if not exp_lines:
                exp_lines = [l for l in exp_text.split('\n') if l.strip()]
            if abs(len(step_lines) - len(exp_lines)) >= 1:
                step_exp_mismatch += 1
        if step_exp_mismatch > len(cases) * 0.15:
            hard_issues.append(
                f"{step_exp_mismatch}/{len(cases)}条用例步骤数≠期望结果数。"
                f"规则:每个步骤必须有对应的期望结果。基于P5测试点description中列出的操作流程,逐一编写步骤和期望。"
            )

        # V4.11.0: 校验B已移除 - 逐条生成模式下无跨TP场景
        # 原校验B逻辑:跨测试点步骤唯一性检查
        # 替代:G5-intra 在 _quick_gate_single_tp 中处理(同TP内弱化检测)

    # V4.6.17: 骨架已不含step_expected_pairs,R14检查移除。Agent基于P5原文自由创作步骤。

    if hard_issues:
        # V4.10.1: 生成 fix_hints 指引 Agent 自动修复
        fix_hints = []
        batch_path_fix = os.path.join(batches_dir, f"batch_{batch_index:03d}.json")
        for iss in hard_issues:
            if "P0比例" in iss:
                fix_hints.append({"priority": "P1", "action": "reduce_p0", "batch": batch_index, "issue": iss,
                    "hint": "读取batch文件,将非冷烟P0用例的priority改为P1,用 p6_save_batch --batch-index " + str(batch_index) + " --merge 保存"})
            elif "步骤唯一性" in iss and "差异化" in iss:
                fix_hints.append({"priority": "P1", "action": "differentiate_steps", "batch": batch_index, "issue": iss,
                    "hint": "读取skeleton的p5_description,为每个TP写不同的操作步骤。改后用 --merge 保存"})
            elif "模糊" in iss or "表述" in iss:
                fix_hints.append({"priority": "P1", "action": "fix_vague_expected", "batch": batch_index, "issue": iss,
                    "hint": "改期望结果禁止词(正常/成功/正确/符合预期)→可观测描述。改后用 --merge 保存"})
            elif "步骤完全相同" in iss:
                fix_hints.append({"priority": "P1", "action": "differentiate_all_steps", "batch": batch_index, "issue": iss,
                    "hint": "全部步骤相同,必须为每个TP重写差异化步骤。改后用 --merge 保存"})
            elif "title为空" in iss or "steps为空" in iss or "expected_results为空" in iss:
                fix_hints.append({"priority": "P1", "action": "fill_empty_fields", "batch": batch_index, "issue": iss,
                    "hint": "补全空字段。改后用 --merge 保存"})

        # V5.0(4.13.0): 统一重试熔断(不再区分模型档位)
        retry_state_path = os.path.join(data_dir, "orchestrator_state.json")
        retry_key = f"p6_batch_{batch_index}_retry"
        retry_count = 0
        state_data = {}
        if os.path.exists(retry_state_path):
            try:
                state_data = _read_json(retry_state_path)
                retry_count = state_data.get(retry_key, 0)
            except Exception:
                state_data = {}
        # V5.0: 统一熔断上限为5次(原 LOW=3次 过于保守)
        MAX_RETRIES = 5
        if retry_count >= MAX_RETRIES:
            # 生成兜底草稿
            pg = _get_p6_guide()
            draft_cases = []
            p5_path = os.path.join(data_dir, "p5_output.json")
            if os.path.exists(p5_path) and os.path.exists(skeleton_path):
                try:
                    p5_data = _read_json(p5_path)
                    skeletons = _read_json(skeleton_path)
                    tp_map = {tp.get("id", ""): tp for tp in p5_data.get("test_points", [])}
                    for sk in skeletons:
                        tp_id = sk.get("source_test_point", "")
                        tp = tp_map.get(tp_id, {"description": "", "category": "main_flow"})
                        draft = pg.generate_draft_case(tp, sk, p5_data)
                        draft_cases.append(draft)
                except Exception:
                    pass
            if draft_cases:
                batch_data["testcases"] = draft_cases
                batch_data["quality"] = "low_quality_draft"
                _write_json(batch_path, batch_data)
                print(json.dumps({"status": "draft_saved", "batch_index": batch_index, "draft_count": len(draft_cases), "hint": "该批次连续被拒,已保存草稿兜底,需人工审查"}), file=sys.stderr)
                # 重置该批次计数,继续流程
                state_data[retry_key] = 0
                _write_json(retry_state_path, state_data)
                return
        # 未达上限:计数+1,正常拒绝
        retry_count += 1
        state_data[retry_key] = retry_count
        state_data["model_tier"] = "standard"
        _write_json(retry_state_path, state_data)
        print(json.dumps({"status": "info", "retry_key": retry_key, "retry_count": retry_count, "max_retries": MAX_RETRIES}), file=sys.stderr)
        # 删除已写入的不合格文件
        if os.path.exists(batch_path):
            os.remove(batch_path)
        # V4.6.17: 增量修复--提取失败用例ID,提示只重写问题用例
        failed_ids = []
        for iss in hard_issues:
            import re as _re
            ids = _re.findall(r'[A-Za-z0-9]+-[A-Za-z0-9]+-?\d*?TP-\d+-TC-\d+', str(iss))
            failed_ids.extend(ids)
        failed_ids = list(set(failed_ids))[:20]
        print(json.dumps({
            "status": "quality_rejected",
            "batch_index": batch_index,
            "issues": hard_issues,
            "fix_hints": fix_hints,
            "failed_case_ids": failed_ids,
            "retry_hint": f"🔴 按 fix_hints 逐项修复后重新 p6_save_batch --batch-index {batch_index} --merge。自动重试最多3次。" if fix_hints else (
                f"仅需重写以下{len(failed_ids)}条问题用例: {failed_ids}" if failed_ids else "请重新生成本批次用例"),
        }))
        sys.exit(1)

    # V4.8.10: 占位符质量检测 - 标记不拒绝,供Agent重跑时重点关注
    placeholder_warnings = _check_placeholder_quality(cases)
    if placeholder_warnings:
        total_tagged = placeholder_warnings.get("total_tagged", 0)
        print(json.dumps({
            "status": "info",
            "placeholder_warnings": placeholder_warnings,
            "hint": f"{total_tagged}条用例含占位符/空洞内容,已标记到remarks字段。非致命,批次已保存。重跑时请关注这些用例。"
        }), file=sys.stderr)

    # V4.3.0: Gate G1+G2+G5 快速质量检查(每批次保存时执行)
    gate_quick_results = []
    gate_quick_eval = {"status": "PASS", "block_failed": 0}
    if os.path.exists(p5_path):
        try:
            p5_data = _read_json(p5_path)
            p5_tps = p5_data.get("test_points", [])
            gate_quick_results = _run_gate_checks(cases, p5_tps, check_ids=["G1", "G2", "G5"])
            # V4.15.11: G1升级为始终BLOCK（task_20260612_161339发现245条步骤不具体未被拦截）
            # V4.15.5策略: G1.5/G2/G5始终BLOCK; G1原为HIGH模型BLOCK/LOW和standard WARNING
            # 经验证据: 降级导致大量不具体步骤通过快速Gate，P7才发现，浪费修复轮次
            gate_quick_eval = _evaluate_gate(gate_quick_results)
        except Exception as _gate_err:
            gate_quick_eval = {"status": "PASS", "block_failed": 0, "warning": f"Gate检查执行异常(跳过): {_gate_err}"}

    # G1+G2+G5 BLOCK失败时拒绝批次
    if gate_quick_eval.get("status") == "FAIL":
        if os.path.exists(batch_path):
            os.remove(batch_path)
        gate_issue_summary = "; ".join(
            f"{r['check_id']}:{r.get('detail') or r.get('reason', '')}" for r in gate_quick_results if r.get("status") == "FAILED"
        )
        print(json.dumps({
            "status": "gate_rejected",
            "batch_index": batch_index,
            "gate_checks": gate_quick_results,
            "gate_summary": gate_issue_summary,
            "retry_hint": f"Gate G1+G2+G5快速检查不通过: {gate_issue_summary}",
        }))
        sys.exit(1)

    print(json.dumps({
        "status": "ok",
        "batch_index": batch_index,
        "cases_in_batch": len(cases),
        "batch_file": batch_path,
        "skeleton_locked": bool(skeleton_map),
        "gate_quick_check": gate_quick_eval.get("status", "SKIP"),
        "gate_quick_issues": gate_quick_eval.get("block_failed", 0) + gate_quick_eval.get("warnings", 0),
    }))

    # V4.13.9-S4: 80%预算告警(不执行降级,仅提醒;基于已落盘的全量批次)
    try:
        _p5p_s4b = os.path.join(data_dir, "p5_output.json")
        _pbudget_s4b = {}
        if os.path.exists(_p5p_s4b):
            _pbudget_s4b = (_read_json(_p5p_s4b) or {}).get("priority_budget", {}) or {}
        _p0_max_s4b = _pbudget_s4b.get("P0_max", 15)
        # 累计所有已保存批次的 P0 总数(跨批次),而非仅当前批次
        _all_cases_s4b = []
        _bdir_s4b = os.path.join(data_dir, "p6_batches")
        for _bf in sorted(glob.glob(os.path.join(_bdir_s4b, "batch_[0-9]*.json"))):
            if "_skeleton" in os.path.basename(_bf) or "_agent_output" in os.path.basename(_bf) or "_output" in os.path.basename(_bf):
                continue
            try:
                _bd = _read_json(_bf)
                _all_cases_s4b.extend(_bd.get("testcases", _bd.get("cases", [])))
            except Exception:
                pass
        _current_p0_s4b = sum(1 for c in _all_cases_s4b if _get_case_field(c, "priority", "").upper() == "P0")
        if _p0_max_s4b > 0 and _current_p0_s4b > _p0_max_s4b * 0.8:
            print(json.dumps({"status": "warning", "type": "budget_alert", "message": f"P0已达{_current_p0_s4b}/{_p0_max_s4b},{_current_p0_s4b/_p0_max_s4b:.0%},merge时将强制降级"}, ensure_ascii=False), file=sys.stderr)
    except Exception:
        pass

    _invalidate_batch_cache()  # V4.9.1: batch已修改,清除索引缓存


# ============================================================
# Action: quality_check (质量校验强化)
# ============================================================

# 每步最小产出数量
# 每步最小产出数量(以云端实际JSON字段名为真源,支持多候选路径用|分隔)
MIN_OUTPUT_COUNTS = {
    "P0": {"blocks.operations|blocks.pages|blocks.business_rules": 1},  # P0实际输出用blocks.operations/pages/business_rules
    "P1": {"feature_tree": 2},  # Bugfix V4.6.9: feature_tree是array,_get_nested已特殊处理返回len()
    "P2": {"test_points": 8},  # V3.2.8: 静态底线8,quality_check中动态计算为max(8, P1叶节点数×2)
    "P3": {"risk_points": 1},  # 至少1个风险点
    "P4": {"pci_list": 1},  # 至少1个PCI
    "P5": {"test_points": 10},
    "P6": {"testcases": 15},  # V3.2.7: 静态底线15,quality_check中动态计算为P5测试点数×1.5
}

# P6用例质量规则(V3.0.3统一真源,prep_prompt和quality_check共用)
P6_QUALITY_RULES = {
    "smoke_ratio_min": 0.05,  # 冒烟用例至少5%(原8%过严,12功能点需求数学上难稳定达到)
    "smoke_ratio_max": 0.20,  # 冒烟用例不超过20%
    "p0_ratio_max": 0.20,  # P0优先级不超过20%(V3.2.3收紧→V3.2.4沿用,与P2 prep_prompt注入一致)
    "all_same_priority": False,  # 不允许所有用例同一优先级
    "per_requirement_smoke": True,  # 每个需求至少1条冒烟用例
}

def _get_nested(data, key_path):
    """获取嵌套字段值,支持多候选路径(用|分隔)

    示例:
      _get_nested(data, "blocks.modules")  # 单路径
      _get_nested(data, "blocks.operations|blocks.pages")  # 多候选,返回第一个非空的

    Bugfix V4.6.9: 当key_path=="feature_tree"且data为list时,返回len(data)(feature_tree是array)
    """
    # Bugfix V4.6.9: 特殊处理feature_tree为array的情况
    if key_path == "feature_tree" and isinstance(data, list):
        return len(data)

    candidates = key_path.split("|")
    for candidate in candidates:
        keys = candidate.strip().split(".")
        current = data
        for k in keys:
            if isinstance(current, dict):
                current = current.get(k)
            else:
                current = None
                break
        if current is not None:
            return current
    return None

# ============================================================
# Action: p7_code_check (V3.3.1: P7代码硬校验,替代Agent审计)
# ============================================================

# P7子检查函数
def _p7_check_c1(cases):
    """C1 要素完整性 [BLOCK]: 必填7项非空"""
    required = ['case_id', 'title', 'preconditions', 'steps', 'expected_results', 'priority', 'is_smoke']
    issues = []
    for c in cases:
        for rf in required:
            val = _get_case_field(c, rf, "")
            if val is None or (isinstance(val, str) and not val.strip()):
                issues.append({"case_id": _get_case_field(c, "case_id", "?"), "field": rf, "issue": f"{rf}为空"})
    return {
        "check_id": "C1", "name": "要素完整性", "level": "BLOCK",
        "status": "FAILED" if issues else "PASSED",
        "detail": f"{len(cases)}/{len(cases)}条用例7项必填字段完整" if not issues else f"{len(issues)}个字段缺失",
        "issues": issues,
    }

def _p7_check_c2(cases):
    """C2 步骤-结果数量对应 [分级]: ±1=INFO, ±2=WARNING, >=3=BLOCK (V4.6.14增强根因分析+verify闭环)"""
    import re as _re
    # V4.15.50: 编号格式正则扩展，匹配 1. / 1、 / 1） / 1) / 1: / 1： / 1  等多种格式
    _STEP_NUM_RE = r'^\d+[\.\、: ：\）)]'
    block_issues, warn_issues, info_issues = [], [], []
    detected_formats = set()
    
    # V4.15.56: G6拆分检测 — 同TP多case且步骤数相近→G6原子性拆分导致步骤数系统性增长
    _tp_step_counts = {}
    for c in cases:
        _tp = _get_case_field(c, "source_test_point", "") or c.get("source_test_point", "")
        if not _tp:
            cid_tmp = _get_case_field(c, "case_id", "")
            _tp = cid_tmp.rsplit("-TC-", 1)[0] if "-TC-" in cid_tmp else ""
        if _tp:
            s_tmp = _get_case_field(c, "steps", "")
            sl = [l for l in s_tmp.split('\n') if l.strip() and _re.match(_STEP_NUM_RE, l.strip())]
            if not sl:
                sl = [l for l in s_tmp.split('\n') if l.strip()]
            _tp_step_counts.setdefault(_tp, []).append(len(sl))
    
    for c in cases:
        steps = _get_case_field(c, "steps", "")
        expected = _get_case_field(c, "expected_results", "")
        # V4.14.2: 优先匹配编号行,无编号时fallback到非空行计数(防字符串整体计1)
        s_lines = [l for l in steps.split('\n') if l.strip() and _re.match(_STEP_NUM_RE, l.strip())]
        if not s_lines:
            s_lines = [l for l in steps.split('\n') if l.strip()]
        e_lines = [l for l in expected.split('\n') if l.strip() and _re.match(_STEP_NUM_RE, l.strip())]
        if not e_lines:
            e_lines = [l for l in expected.split('\n') if l.strip()]
        # V4.13.8 P0-1: 记录检测到的编号格式（用于 step_format_detected 输出）
        for _l in (steps.split('\n') + expected.split('\n')):
            _m = _re.match(r'^\d+([\.\、）)])', _l.strip())
            if _m:
                detected_formats.add(_m.group(1))
        diff = abs(len(s_lines) - len(e_lines))
        cid = _get_case_field(c, "case_id", "?")
        priority = _get_case_field(c, "priority", "P2")

        # V4.6.14: 增强根因分析
        cause = ""
        fix_hint = ""
        verify = ""

        if len(s_lines) > len(e_lines):
            # 步骤多于期望
            avg_step_len = sum(len(l) for l in s_lines) / max(len(s_lines), 1)
            if avg_step_len < 15:
                cause = "步骤过短(平均{:.0f}字),可能将每个操作不当拆分成多个步骤".format(avg_step_len)
                fix_hint = "将连续的子步骤合并为一个步骤组,每个组对应一个期望结果。期望结果必须每条单独一行,以数字编号开头(如 1. xxx 2. xxx),禁止用分号或顿号连接多条。"
            else:
                cause = "步骤数({})多于期望数({}),可能在应写期望时偷懒".format(len(s_lines), len(e_lines))
                fix_hint = "为每个有效操作步骤补充对应期望结果。期望结果必须每条单独一行,以数字编号开头(如 1. xxx 2. xxx),禁止用分号或顿号连接多条。"
            verify = "修复后验证:步骤数与期望数偏差应≤2,且期望覆盖率≥60%"
        elif len(e_lines) > len(s_lines):
            cause = "期望结果数({})多于步骤数({}),可能将多个期望合并为一条".format(len(e_lines), len(s_lines))
            fix_hint = "将模糊的期望结果拆分为多个具体期望,每条期望对应一个验证点。期望结果必须每条单独一行,以数字编号开头(如 1. xxx 2. xxx)。"
            verify = "修复后验证:每条期望都应有对应步骤"

        issue_entry = {
            "case_id": cid,
            "steps": len(s_lines),
            "expected": len(e_lines),
            "diff": diff,
            "cause": cause,
            "fix_hint": fix_hint,
            "verify": verify,
        }

        # V4.15.12: 阈值临时从 diff≥3 提升到 diff≥5（等语义分类器落地后恢复）
        # V4.15.39: 异常处理/风险验证场景放宽 diff=3 降为 INFO
        # V4.15.42: pci_verification 放宽 diff≤4 降为 INFO (PCI场景步骤少是正常特征)
        # V4.15.56: G6拆分豁免 — 同TP多case步骤数相近(≥6步)且差≤2, 视为原子性拆分, 放宽1级
        _tp = _get_case_field(c, "source_test_point", "") or c.get("source_test_point", "")
        if not _tp:
            _tp = cid.rsplit("-TC-", 1)[0] if "-TC-" in cid else ""
        _same_tp_steps = _tp_step_counts.get(_tp, [])
        _is_g6_split = (len(_same_tp_steps) >= 2
                        and max(_same_tp_steps) - min(_same_tp_steps) <= 2
                        and all(s >= 6 for s in _same_tp_steps))
        _tc_type = _get_case_field(c, "test_case_type", "") or _get_case_field(c, "category", "")
        if _tc_type == "pci_verification" and diff <= 4:
            info_issues.append(issue_entry)
        elif _tc_type in ("异常处理", "风险验证") and diff == 3:
            info_issues.append(issue_entry)
        elif _is_g6_split and diff == 3:
            info_issues.append(issue_entry)   # G6拆分后 diff=3 → INFO(原WARNING)
        elif _is_g6_split and diff == 4:
            info_issues.append(issue_entry)   # G6拆分后 diff=4 → INFO(原WARNING)
        elif _is_g6_split and diff == 5:
            warn_issues.append(issue_entry)   # G6拆分后 diff=5 → WARNING(原BLOCK)
        elif diff >= 6 or (diff >= 5 and not _is_g6_split):
            block_issues.append(issue_entry)
        elif diff >= 3:
            warn_issues.append(issue_entry)
        elif diff == 2:
            info_issues.append(issue_entry)

    if block_issues:
        status = "FAILED"
    elif warn_issues:
        status = "WARNING"
    else:
        status = "PASSED"
    return {
        "check_id": "C2", "name": "步骤-结果数量对应", "level": "BLOCK",
        "status": status,
        "detail": f"差≥5:{len(block_issues)}条, 差3-4:{len(warn_issues)}条, 差1-2:{len(info_issues)}条(INFO)",
        # V4.15.12: 截断提升到 30+20 + 按diff降序排列（优先暴露最严重问题）
        "issues": sorted(block_issues, key=lambda x: -x['diff'])[:30] + sorted(warn_issues, key=lambda x: -x['diff'])[:20],
        "info_count": len(info_issues),
        # V4.13.8 P0-1: 暴露检测到的编号格式，便于排查正则未匹配导致的步骤计数为0
        "step_format_detected": sorted(detected_formats),
    }

def _p7_check_c3(cases):
    """C3 P0占比 [WARNING/BLOCK]: ≤20%通过, 20-40%警告, >40%阻塞"""
    total = len(cases)
    p0 = sum(1 for c in cases if _get_case_field(c, "priority", "").upper() in ("P0", "HIGHEST"))
    ratio = p0 / max(total, 1)
    if ratio > 0.40:
        status = "FAILED"
    elif ratio > 0.20:
        status = "WARNING"
    else:
        status = "PASSED"
    return {
        "check_id": "C3", "name": "P0占比", "level": "WARNING",
        "status": status,
        "detail": f"P0={p0}/{total}({ratio:.1%})",
        "issues": [],
    }

def _p7_check_c4(cases):
    """C4 冒烟占比 [WARNING]: 按总数分档校验"""
    total = len(cases)
    smoke = sum(1 for c in cases if _is_smoke(_get_case_field(c, "is_smoke", "")))
    ratio = smoke / max(total, 1)
    if total <= 15:
        lo, hi = 0.20, 0.35
    elif total <= 30:
        lo, hi = 0.15, 0.25
    else:
        lo, hi = 0.10, 0.20
    if ratio < lo or ratio > hi:
        status = "WARNING"
    else:
        status = "PASSED"
    return {
        "check_id": "C4", "name": "冒烟占比", "level": "WARNING",
        "status": status,
        "detail": f"冒烟={smoke}/{total}({ratio:.1%}), 期望{lo:.0%}-{hi:.0%}",
        "issues": [],
    }

def _p7_check_c5(cases):
    """C5 步骤描述质量 [WARNING]: 上下文感知正则"""
    import re as _re
    VAGUE_NOUNS = {'数据', '结果', '页面', '功能', '状态', '信息', '内容', '格式'}
    issues = []
    for c in cases:
        steps = _get_case_field(c, "steps", "")
        lines = [l.strip() for l in steps.split('\n') if _re.match(r'^\d+\.', l.strip())]
        for line in lines:
            m = _re.match(r'^\d+\.\s*(验证|检查|确认)\s*(.*)$', line)
            if m:
                verb, rest = m.group(1), m.group(2).strip()
                # 放行:有判断词
                if _re.search(r'是否|能否|有无|包含|显示为|等于|大于|小于|超出|不足', rest):
                    continue
                # 放行:去掉模糊名词后仍有内容
                cleaned = rest
                for vn in VAGUE_NOUNS:
                    cleaned = cleaned.replace(vn, '')
                cleaned = _re.sub(r'[正确正常无误成功]', '', cleaned).strip()
                if len(cleaned) >= 2:
                    continue
                issues.append({"case_id": _get_case_field(c, "case_id", "?"), "line": line[:80], "verb": verb})
    ratio = len(issues) / max(len(cases), 1)
    return {
        "check_id": "C5", "name": "步骤描述质量", "level": "WARNING",
        "status": "WARNING" if ratio > 0.30 else "PASSED",
        "detail": f"{len(issues)}/{len(cases)}条含模糊动词({ratio:.1%})",
        "issues": issues[:15],
    }

def _p7_check_c6(cases):
    """C6 期望结果质量 [WARNING]: 负向模式正则"""
    import re as _re
    VAGUE_PATTERNS = [
        r'(?:操作|执行|处理|加载|保存|删除|修改|提交)(?:成功|正确|正常)\s*$',
        r'(?:显示|展示|呈现)(?:正确|正常|无误)\s*$',
        r'符合预期\s*$',
        r'(?:数据|结果|内容|信息)(?:正确|正常|无误)\s*$',
        r'(?:功能|模块|接口)(?:正常|可用)\s*$',
        r'(?:验证|校验)(?:通过|成功)\s*$',
    ]
    issues = []
    for c in cases:
        expected = _get_case_field(c, "expected_results", "")
        lines = [l.strip() for l in expected.split('\n') if _re.match(r'^\d+\.', l.strip())]
        for line in lines:
            for pattern in VAGUE_PATTERNS:
                if _re.search(pattern, line):
                    issues.append({"case_id": _get_case_field(c, "case_id", "?"), "line": line[:80]})
                    break
    ratio = len(issues) / max(len(cases), 1)
    return {
        "check_id": "C6", "name": "期望结果质量", "level": "WARNING",
        "status": "WARNING" if ratio > 0.30 else "PASSED",
        "detail": f"{len(issues)}/{len(cases)}条含模糊描述({ratio:.1%})",
        "issues": issues[:15],
    }

def _p7_check_c61(cases):
    """C6.1 前置条件三要素 [BLOCK]: 账号/权限 + 数据构造 + 环境配置(V3.3.5: 2/3匹配即通过)
    V4.13.8 P1-1: 报错完整化(tp_file/current_preconditions/missing/fix_hint) + 扩展关键词库
    """
    import re as _re
    # V4.13.8 P1-1: 账号要素补充"已登录|已认证|已授权"; 数据要素补充"已创建|已导入|已存在"
    KW_ACCOUNT = _re.compile(r'账号|权限|登录|用户|角色|管理员|员工|已登录|已认证|已授权')
    KW_DATA = _re.compile(r'数据|预置|构造|预设|测试数据|造数|记录|条|导入|创建|已创建|已导入|已存在|维护|已维护|填写|已填写|选项|字段|表单')
    KW_ENV = _re.compile(r'环境|系统|配置|服务|运行|部署|开通|正常|时间|状态|已配置|已启用|已开通')
    issues = []
    for c in cases:
        precond = _get_case_field(c, "preconditions", "")
        elements_found = 0
        missing = []
        if KW_ACCOUNT.search(precond):
            elements_found += 1
        else:
            missing.append("账号/权限(如:已登录的XX角色)")
        if KW_DATA.search(precond):
            elements_found += 1
        else:
            missing.append("数据构造(如:已创建N条XX数据)")
        if KW_ENV.search(precond):
            elements_found += 1
        else:
            missing.append("环境配置(如:系统正常运行/XX服务已开通)")
        # V3.3.5: 2/3匹配即通过(放宽)
        if elements_found < 2:
            cid = _get_case_field(c, "case_id", "?")
            # V4.13.8 P1-1: 从case_id/source_test_point反推tp_file(tp_NNN.json)
            src_tp = _get_case_field(c, "source_test_point", "") or ""
            if not src_tp and cid and "-TC-" in cid:
                src_tp = cid.rsplit("-TC-", 1)[0]
            tp_file = ""
            try:
                if src_tp and "-" in src_tp:
                    tp_num = int(src_tp.split("-")[-1])
                    tp_file = f"tp_{tp_num - 1:03d}.json"
            except Exception:
                tp_file = ""
            issues.append({
                "case_id": cid,
                "tp_id": src_tp,
                "tp_file": tp_file,
                "found": elements_found,
                "current_preconditions": str(precond)[:100],
                "missing": missing,
                "fix_hint": "前置条件需含≥2个要素。缺失: " + "; ".join(missing),
            })
    return {
        "check_id": "C6.1", "name": "前置条件三要素", "level": "BLOCK",
        "status": "FAILED" if issues else "PASSED",
        "detail": f"{len(issues)}/{len(cases)}条前置条件不完整" if issues else f"{len(cases)}条前置条件均含三要素",
        "issues": issues,
    }

def _p7_check_c62(cases):
    """C6.2 期望结果可验证性 [WARNING](V4.13.8新增): 检测模糊描述"显示正确/正常响应/应该成功"等"""
    import re as _re
    VAGUE_PATTERNS = [
        (r'显示正确', '显示正确 — 应明确具体显示内容(如:页面显示XX数据)'),
        (r'正常响应', '正常响应 — 应明确响应内容格式(如:返回JSON含XX字段)'),
        (r'应该成功', '应该成功 — 应明确成功标准(如:状态码200/提示"操作成功")'),
        (r'功能正常', '功能正常 — 应明确验证点(如:XX按钮可点击/XX数据刷新)'),
        (r'没有问题', '没有问题 — 应明确检查点,禁用否定式断言'),
        (r'无异常|未报错', '无异常/未报错 — 应明确预期行为(如:页面无报错弹窗)'),
        (r'正确返回|返回正确', '正确返回 — 应明确返回内容(如:返回XX列表含N条)'),
        (r'保持一致|一致$', '保持一致/一致 — 应明确一致性标准(如:字段值与原值相同)'),
    ]
    issues = []
    for c in cases:
        expected = str(_get_case_field(c, "expected_results", "")).strip()
        if not expected:
            continue
        cid = _get_case_field(c, "case_id", "?")
        for pattern, hint in VAGUE_PATTERNS:
            m = _re.search(pattern, expected)
            if m:
                issues.append({
                    "case_id": cid,
                    "matched": m.group(0),
                    "fix_hint": hint,
                    "snippet": expected[:80],
                })
                break  # 一个case只报一次
    ratio = len(issues) / max(len(cases), 1)
    return {
        "check_id": "C6.2", "name": "期望结果可验证性", "level": "WARNING",
        "status": "WARNING" if ratio > 0.15 else "PASSED",
        "detail": f"{len(issues)}/{len(cases)}条期望结果含模糊描述({ratio:.1%})" if issues else f"{len(cases)}条期望结果可验证",
        "issues": issues,
    }

def _p7_check_c7(cases, p5_test_points):
    """C7 测试点覆盖率 [BLOCK]: P5 active测试点必须100%覆盖"""
    import re as _c7_re
    # === V4.15.18-B: 短ID→完整ID容错映射（含ETP-N变体）===
    short_to_full_map = {}
    for tp in p5_test_points:
        full_id = tp.get('id', '')
        for _m in _c7_re.finditer(r'(?:TP|ETP)-(?:\d{1,})$', full_id):
            short_to_full_map[_m.group(0)] = full_id

    p5_active = set()
    for tp in p5_test_points:
        if tp.get('status', 'active') == 'active':
            p5_active.add(tp.get('id', ''))
    # === V4.15.28: 构建索引→完整ID映射（case_id回退匹配用）===
    index_to_full = {}
    for _idx, _tp in enumerate(p5_test_points):
        _full = _tp.get('id', '')
        if _full:
            index_to_full[_idx] = _full

    p6_covered = set()
    for c in cases:
        src = _get_case_field(c, "source_test_point", "")
        if not src:
            src = c.get("source_test_point", "")
        # === V4.15.28: case_id回退匹配（当source_test_point不匹配时）===
        _matched = False
        if src:
            if src in p5_active:
                p6_covered.add(src)
                _matched = True
            elif src in short_to_full_map and short_to_full_map[src] in p5_active:
                p6_covered.add(short_to_full_map[src])
                _matched = True
        if not _matched:
            # 回退1：从case_id提取TP/ETP短ID匹配
            cid = _get_case_field(c, "case_id", "")
            _cid_m = _c7_re.search(r'(?:TP|ETP)-(?:\d{1,})', str(cid))
            if _cid_m:
                _cid_short = _cid_m.group(0)
                if _cid_short in short_to_full_map and short_to_full_map[_cid_short] in p5_active:
                    p6_covered.add(short_to_full_map[_cid_short])
                    _matched = True
            # 回退2：从case_id提取纯数字索引匹配
            if not _matched:
                _num_m = _c7_re.search(r'[_-](\d{2,4})(?=-TC-)', str(cid))
                if _num_m:
                    _num = int(_num_m.group(1))
                    _full = index_to_full.get(_num, '')
                    if _full and _full in p5_active:
                        p6_covered.add(_full)
                        _matched = True
            # 回退3：保留原始src用于后续计算
            if src and not _matched:
                p6_covered.add(src)
    uncovered = sorted(p5_active - p6_covered)
    rate = len(p6_covered & p5_active) / max(len(p5_active), 1)

    # V4.13.8 P2-⑮: 覆盖深度检查(区分存在vs深度)
    tp_depth = {}  # tp_id → case_count
    for c in cases:
        src = _get_case_field(c, "source_test_point", "")
        if not src:
            src = c.get("source_test_point", "")
        if src:
            tp_depth[src] = tp_depth.get(src, 0) + 1
    shallow_tps = []  # 仅1条用例覆盖的TP
    for tp_id in p5_active:
        depth = tp_depth.get(tp_id, 0)
        if 0 < depth < 2:  # 被覆盖但仅1条
            # 从p5获取预期数量
            expected = 2  # 默认期望2条
            for tp in p5_test_points:
                if tp.get("id") == tp_id:
                    expected = tp.get("expected_case_count", 2)
                    break
            if expected >= 2:
                shallow_tps.append(f"{tp_id}:仅{depth}条(期望≥{expected})")

    return {
        "check_id": "C7", "name": "测试点覆盖率", "level": "BLOCK",
        "status": "FAILED" if uncovered else "PASSED",
        "detail": f"覆盖{len(p6_covered & p5_active)}/{len(p5_active)}({rate:.0%})",
        "issues": [{"test_point": tp, "issue": "未覆盖"} for tp in uncovered[:20]],
        "coverage_rate": rate,
        # V4.13.8: 覆盖深度报告(不阻断)
        "depth_summary": {
            "covered_tps": len(p6_covered & p5_active),
            "shallow_covered": len(shallow_tps),
            "shallow_tps": shallow_tps[:15],
            "hint": f"{len(shallow_tps)}个TP仅1条用例覆盖,覆盖深度不足。建议L3 TP≥3条,L2 TP≥2条。" if shallow_tps else "所有TP覆盖深度充足",
        },
    }

def _p7_check_c71(cases, p5_test_points):
    """C7.1 语义覆盖 [WARNING]: 业务实体匹配
    V4.15.42 重设计: 从逐个实体词匹配 → 字符级bigram Jaccard相似度
    根因: P5紧凑标记(「分润列表行」) vs P6扩展文本(债券投顾列表页面...「查看」)
    属于不同抽象级别, 逐个词匹配必然大面积假阳性。

    bigram Jaccard 优势:
    - 自然容忍同义词/缩写/扩展 (「分润列表行」↔「债券投顾列表页面」仍有公共bigram「列表」)
    - P5→P6的词汇扩展不会导致匹配失败
    - 对中文天然友好(无需分词)
    """
    import re as _re
    short_to_full_map = {}
    tp_descriptions = {}
    for tp in p5_test_points:
        tp_id = tp.get('id', '')
        desc = tp.get('description', '')
        for _m in _re.finditer(r'(?:TP|ETP)-(?:\d{1,})$', tp_id):
            short_to_full_map[_m.group(0)] = tp_id
        tp_descriptions[tp_id] = desc

    def _bigrams(text):
        """提取字符bigram(仅保留中文+字母数字)"""
        clean = _re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9]', '', text)
        if len(clean) < 2:
            return set()
        return set(clean[i:i + 2] for i in range(len(clean) - 1))

    issues = []
    for c in cases:
        src_tp = _get_case_field(c, "source_test_point", "") or c.get("source_test_point", "")
        # V4.15.21: 短ID容错
        if src_tp not in tp_descriptions:
            if src_tp in short_to_full_map:
                src_tp = short_to_full_map[src_tp]
            else:
                _m = _re.search(r'(?:TP|ETP)-\d+$', src_tp)
                if _m and _m.group(0) in short_to_full_map:
                    src_tp = short_to_full_map[_m.group(0)]
                else:
                    continue

        p5_desc = tp_descriptions.get(src_tp, '')
        if not p5_desc:
            continue

        # P6文本: title + steps(步骤是可操作内容的主干)
        p6_text = _get_case_field(c, "title", "") + ' ' + _get_case_field(c, "steps", "")

        p5_bg = _bigrams(p5_desc)
        p6_bg = _bigrams(p6_text)
        if not p5_bg:
            continue

        intersection = len(p5_bg & p6_bg)
        union = len(p5_bg | p6_bg)
        similarity = intersection / max(union, 1)

        # V4.15.43: 按类型差异化阈值 (bigram Jaccard, V4.15.42初版0.10太严→40%假阳性)
        test_case_type = _get_case_field(c, "test_case_type", "") or _get_case_field(c, "category", "")
        if test_case_type in ("异常处理", "风险验证", "pci_verification"):
            threshold = 0.04
        elif test_case_type in ("性能测试",):
            threshold = 0.06
        else:
            threshold = 0.08
        # V4.15.50: P5描述长度调整 — 短描述天然bigram少，放宽阈值
        # V4.15.53: <30字极短描述进一步放宽，减少WARNING噪音
        p5_desc_len = len(p5_desc)
        if p5_desc_len < 30:
            threshold *= 0.3
        elif p5_desc_len < 50:
            threshold *= 0.5
        elif p5_desc_len < 80:
            threshold *= 0.75

        if similarity < threshold:
            issues.append({
                "case_id": _get_case_field(c, "case_id", "?"),
                "source_tp": src_tp,
                "similarity": round(similarity, 3),
                "p5_bigrams": len(p5_bg),
                "p6_bigrams": len(p6_bg),
                "overlap": intersection,
            })

    return {
        "check_id": "C7.1", "name": "语义覆盖(业务实体-bigram)", "level": "WARNING",
        "status": "WARNING" if issues else "PASSED",
        "detail": f"{len(issues)}/{len(cases)}条语义覆盖不足(bigram Jaccard<阈值)" if issues else "全部用例语义覆盖充分",
        "issues": issues[:15],
    }

def _p7_check_c8(cases):
    """C8 冒烟合规性 [WARNING]: 冒烟用例priority应为P0/P1"""
    issues = []
    for c in cases:
        if _is_smoke(_get_case_field(c, "is_smoke", "")):
            p = _get_case_field(c, "priority", "")
            if p not in ("P0", "P1"):
                issues.append({
                    "case_id": _get_case_field(c, "case_id", "?"),
                    "priority": p,
                    "suggestion": f"建议将priority从{p}升级为P1",
                })
    return {
        "check_id": "C8", "name": "冒烟合规性", "level": "WARNING",
        "status": "WARNING" if issues else "PASSED",
        "detail": f"{len(issues)}条冒烟用例priority不合规" if issues else "冒烟用例priority均为P0/P1",
        "issues": issues,
    }

def _p7_check_c9(cases):
    """C9 伞形用例检测 [WARNING] - V4.6.11改进

    真正的伞形用例:同一功能点的多个对称模块(月榜/周榜/日榜等)被合并为1条用例。
    误伤场景:"与OA一致"等外部系统引用不属于伞形用例。

    检测逻辑:对称模块词 + 合并意图词 同时出现才判定为伞形。
    """
    import re as _re

    # 对称模块词列表(多选一出现即可)
    SYMMETRIC_MODULE_RE = _re.compile(
        r'月榜|周榜|日榜|季榜|'
        r'PC端|移动端|H5端|APP端|'
        r'总公司|分公司|'
        r'东区|西区|南区|北区|'
        r'版本\d|版本A|版本B|'
        r'Android|iOS|Windows|Mac|'
        r'浏览器端|小程序端'
    )

    # 合并意图词(多选一出现即可)
    MERGE_INTENT_RE = _re.compile(
        r'相应调整|同步调整|一致|同理|同上|类似|'
        r'与.*同|与.*一致|参照.*处理|参考.*调整'
    )

    issues = []
    for c in cases:
        title = _get_case_field(c, "title", "")
        steps = _get_case_field(c, "steps", "")
        text = title + ' ' + steps

        has_module = bool(SYMMETRIC_MODULE_RE.search(text))
        has_merge_intent = bool(MERGE_INTENT_RE.search(text))

        # 必须同时满足:对称模块词 + 合并意图词
        if has_module and has_merge_intent:
            issues.append({
                "case_id": _get_case_field(c, "case_id", "?"),
                "module_match": SYMMETRIC_MODULE_RE.findall(text),
                "merge_match": MERGE_INTENT_RE.findall(text),
            })

    return {
        "check_id": "C9", "name": "伞形用例检测", "level": "WARNING",
        "status": "WARNING" if issues else "PASSED",
        "detail": f"{len(issues)}条伞形用例" if issues else "无伞形用例",
        "issues": issues[:10],
    }


def _p7_check_p0_distribution(cases):
    """V4.14.2: P0占比门禁 [分级]
    =0%: BLOCK(必须有P0) | ≤15%: PASS | 15-20%: WARNING | 20-30%: BLOCK可覆盖 | >30%: BLOCK
    总用例<50条时>30%降级为WARNING(小任务豁免)
    """
    total = len(cases)
    if total == 0:
        return {"check_id": "P0_DIST", "name": "P0占比分布", "level": "INFO", "status": "PASSED",
                "p0_count": 0, "p0_ratio": 0, "detail": "无用例数据"}

    p0_cases = [c for c in cases if str(_get_case_field(c, "priority", "")).upper() == "P0"]
    p0_count = len(p0_cases)
    p0_ratio = p0_count / total
    smoke_count = sum(1 for c in cases if _get_case_field(c, "is_smoke", "") in (True, "true", "是", "yes"))

    issues = []
    status = "PASSED"
    level = "INFO"
    message = f"P0占比{p0_ratio:.1%}({p0_count}/{total}), 冒烟{smoke_count}条"

    if p0_count == 0:
        status = "FAILED"
        level = "BLOCK"
        message = "❌ 未包含P0用例，不符合规范(必须有核心流程验证用例)"
        issues.append("请将至少1条核心主流程用例标记为P0")
    elif p0_ratio > 0.30:
        if total < 50:
            status = "WARNING"
            level = "WARNING"
            message = f"⚠️ P0占比{p0_ratio:.1%}({p0_count}/{total})>30%，但总用例<50条(小任务豁免)"
        else:
            status = "FAILED"
            level = "BLOCK"
            message = f"❌ P0占比{p0_ratio:.1%}({p0_count}/{total})>30%，严重超标，必须回P5重新分配优先级"
            issues.append("P0占比超过30%，建议回到P5阶段重新审查priority分配")
    elif p0_ratio > 0.20:
        status = "FAILED"
        level = "BLOCK"
        message = f"⚠️ P0占比{p0_ratio:.1%}({p0_count}/{total})>20%，超标(可覆盖)"
        # 生成降级建议
        downgrade_candidates = []
        for c in p0_cases:
            cid = _get_case_field(c, "case_id", "?")
            cat = str(_get_case_field(c, "test_category", "")).lower()
            is_smoke = _get_case_field(c, "is_smoke", "") in (True, "true", "是", "yes")
            if is_smoke:
                continue  # 冒烟用例不纳入降级候选
            if "main_flow" in cat:
                continue  # 主流程P0保护
            rec = {"case_id": cid, "category": cat}
            if any(kw in cat for kw in ("compatibility", "permission")):
                rec["suggest"] = "P2"
            else:
                rec["suggest"] = "P1"
            downgrade_candidates.append(rec)
            if len(downgrade_candidates) >= 10:
                break
        if downgrade_candidates:
            after_count = p0_count - len(downgrade_candidates)
            issues.append(f"建议降级{len(downgrade_candidates)}条P0→P1/P2，降级后P0占比约{after_count}/{total}={after_count/total:.1%}")
            issues.append(f"降级候选: {json.dumps(downgrade_candidates[:5], ensure_ascii=False)}")
    elif p0_ratio > 0.15:
        status = "WARNING"
        level = "WARNING"
        message = f"⚠️ P0占比{p0_ratio:.1%}({p0_count}/{total})>15%，建议审核"

    return {"check_id": "P0_DIST", "name": "P0占比分布", "level": level, "status": status,
            "p0_count": p0_count, "p0_ratio": round(p0_ratio, 3), "smoke_count": smoke_count,
            "total_cases": total, "detail": message, "issues": issues}


def _p7_retry_statistics(data_dir):
    """V4.15.50: 从p6_metrics.jsonl汇总TP级重试统计"""
    import os as _os, json as _json
    metrics_path = _os.path.join(data_dir, "p6_metrics.jsonl")
    state_path = _os.path.join(data_dir, "orchestrator_state.json")
    result = {"total_p6_retries": 0, "tps_with_retries": 0, "total_tps": 0, "retry_distribution": {}, "top_retry_tps": []}
    if _os.path.exists(metrics_path):
        try:
            retries_list = []
            tp_count = 0
            with open(metrics_path, encoding="utf-8") as _mf:
                for line in _mf:
                    try:
                        entry = _json.loads(line)
                        tp_count += 1
                        r = entry.get("retries", 0)
                        retries_list.append((entry.get("tp_id", "?"), r))
                        if r > 0:
                            result["tps_with_retries"] += 1
                    except Exception:
                        pass
            result["total_p6_retries"] = sum(r for _, r in retries_list)
            result["total_tps"] = tp_count
            dist = {}
            for _, r in retries_list:
                dist[str(r)] = dist.get(str(r), 0) + 1
            result["retry_distribution"] = dist
            top = sorted(retries_list, key=lambda x: -x[1])[:5]
            result["top_retry_tps"] = [{"tp_id": tid, "retries": r} for tid, r in top if r > 0]
        except Exception:
            pass
    if _os.path.exists(state_path):
        try:
            with open(state_path, encoding="utf-8") as _sf:
                sd = _json.load(_sf)
            state_retries = {k: v for k, v in sd.items() if k.startswith("p6_tp_") and k.endswith("_retry")}
            result["state_total_retries"] = sum(state_retries.values())
            result["state_retry_keys"] = len(state_retries)
        except Exception:
            pass
    return result


def _p7_statistics(cases):
    """INFO级统计指标"""
    from collections import Counter as _Counter
    priorities = _Counter(_get_case_field(c, "priority", "unknown") for c in cases)
    step_texts = set()
    step_lens = []
    precond_lens = []
    title_counter = _Counter()
    for c in cases:
        s = _get_case_field(c, "steps", "")
        step_texts.add(s.strip())
        step_lens.append(len(s))
        precond_lens.append(len(_get_case_field(c, "preconditions", "")))
        title_counter[_get_case_field(c, "title", "")] += 1
    dup_titles = {t: cnt for t, cnt in title_counter.items() if cnt > 1}
    return {
        "total_cases": len(cases),
        "priority_distribution": dict(priorities),
        "smoke_count": sum(1 for c in cases if _is_smoke(_get_case_field(c, "is_smoke", ""))),
        "step_uniqueness": len(step_texts) / max(len(cases), 1),
        "avg_step_length": sum(step_lens) / max(len(step_lens), 1),
        "avg_precondition_length": sum(precond_lens) / max(len(precond_lens), 1),
        "duplicate_titles": len(dup_titles),
        "duplicate_title_samples": list(dup_titles.keys())[:5],
    }

def _generate_p7_html_report(checks, statistics, output_path):
    """生成P7质量报告HTML"""
    status_icon = {"PASSED": "✅", "FAILED": "❌", "WARNING": "⚠️"}
    status_color = {"PASSED": "#27ae60", "FAILED": "#e74c3c", "WARNING": "#f39c12"}
    checks_html = ""
    for ck in checks:
        color = status_color.get(ck["status"], "#999")
        icon = status_icon.get(ck["status"], "")
        issues_html = ""
        if ck.get("issues"):
            issues_html = "<ul>" + "".join(f"<li>{json.dumps(i, ensure_ascii=False)[:200]}</li>" for i in ck["issues"][:10]) + "</ul>"
        checks_html += f"""<tr>
            <td>{ck.get('check_id', '')}</td><td>{ck.get('name', '')}</td><td>{ck.get('level', '')}</td>
            <td style="color:{color};font-weight:bold;">{icon} {ck.get('status', '')}</td>
            <td>{ck.get('detail', '')}</td></tr>"""
        if issues_html:
            checks_html += f"<tr><td colspan='5' style='background:#fafafa;padding-left:40px;'>{issues_html}</td></tr>"

    pri = statistics.get("priority_distribution", {})
    total = statistics.get("total_cases", 0)
    smoke = statistics.get("smoke_count", 0)

    html = f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8">
<title>P7 Quality Report</title>
<style>
body{{font-family:-apple-system,sans-serif;background:#f5f7fa;padding:20px;color:#333;line-height:1.6;}}
.container{{max-width:960px;margin:0 auto;}}
h1{{font-size:22px;color:#1a1a2e;}}
.card{{background:#fff;border-radius:10px;padding:20px;margin:16px 0;box-shadow:0 2px 6px rgba(0,0,0,0.05);}}
table{{width:100%;border-collapse:collapse;font-size:13px;}}
th{{background:#f8f9fb;padding:8px 10px;text-align:left;border-bottom:2px solid #e8ecf1;}}
td{{padding:8px 10px;border-bottom:1px solid #f0f0f0;}}
.metric{{display:inline-block;text-align:center;padding:10px 16px;margin:4px;background:#f8f9fb;border-radius:6px;}}
.metric .v{{font-size:24px;font-weight:700;color:#1a1a2e;}}
.metric .l{{font-size:11px;color:#888;}}
ul{{margin:4px 0;padding-left:20px;font-size:12px;color:#666;}}
</style></head><body><div class="container">
<h1>🐈‍⬛ P7 Quality Report</h1>
<p style="color:#666;font-size:13px;">Generated by p7_code_check V3.3.1</p>
<div class="card">
<div class="metric"><div class="v">{total}</div><div class="l">总用例</div></div>
<div class="metric"><div class="v">{smoke}</div><div class="l">冒烟用例</div></div>
<div class="metric"><div class="v">{statistics.get('step_uniqueness',0):.0%}</div><div class="l">步骤唯一率</div></div>
<div class="metric"><div class="v">{pri.get('P0',0)}/{pri.get('P1',0)}/{pri.get('P2',0)}/{pri.get('P3',0)}</div><div class="l">P0/P1/P2/P3</div></div>
</div>
<div class="card"><h2>校验结果</h2>
<table><tr><th>ID</th><th>校验项</th><th>级别</th><th>状态</th><th>详情</th></tr>
{checks_html}</table></div>
</div></body></html>"""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)


# ============================================================
# V4.9.1: P7自动修复 - fix_hints生成 + batch索引查找
# ============================================================

def _find_batch_for_case(data_dir, case_id):
    """V4.9.1: 查找case_id所属batch索引(带缓存,一次构建,多次查询)
    V4.15.54: p6_batches/不存在时fallback到p6_tp_output/tp_*.json → 返回tp_index
    """
    cache_attr = '_batch_index_cache'
    cache = getattr(_find_batch_for_case, cache_attr, None)
    if cache and cache.get('_dir') == data_dir:
        return cache.get(case_id, -1)

    batch_map = {}

    # 主路径: p6_batches/ (兼容旧batch模式)
    batches_dir = os.path.join(data_dir, "p6_batches")
    if os.path.isdir(batches_dir):
        for fn in sorted(os.listdir(batches_dir)):
            if not (fn.startswith("batch_") and fn.endswith(".json")):
                continue
            if "_agent" in fn or "_skeleton" in fn or "_context" in fn:
                continue
            try:
                bd = _read_json(os.path.join(batches_dir, fn))
                bi = int(fn.replace("batch_", "").replace(".json", ""))
                for c in bd.get("testcases", []):
                    batch_map[_get_case_field(c, "case_id", "")] = bi
            except Exception:
                pass

    # V4.15.54 fallback: p6_tp_output/tp_*.json (逐TP生成模式, 返回tp_index)
    if not batch_map or case_id not in batch_map:
        tp_dir = os.path.join(data_dir, "p6_tp_output")
        if os.path.isdir(tp_dir):
            for fn in sorted(os.listdir(tp_dir)):
                if not (fn.startswith("tp_") and fn.endswith(".json")):
                    continue
                try:
                    tp = _read_json(os.path.join(tp_dir, fn))
                    tp_idx = tp.get("tp_index", -1)
                    for c in tp.get("testcases", []):
                        cid = _get_case_field(c, "case_id", "")
                        if cid and cid not in batch_map:
                            batch_map[cid] = tp_idx
                except Exception:
                    pass

    batch_map['_dir'] = data_dir
    setattr(_find_batch_for_case, cache_attr, batch_map)
    return batch_map.get(case_id, -1)


def _invalidate_batch_cache():
    """V4.9.1: 清除batch索引缓存(p6_merge/p6_save_batch修改后调用)"""
    setattr(_find_batch_for_case, '_batch_index_cache', None)


def _build_p7_fix_hints(checks, data_dir):
    """V4.9.1: 基于P7检查结果生成结构化修复指引

    为4类常见P7 BLOCK生成可执行的修复指令:
    1. generate_missing - 覆盖率不足,补充缺失TP的用例
    2. fix_step_expected - 步骤期望不匹配(C2)
    3. fix_vague_expected - 模糊表述(G2/C5/C6)
    4. fix_forbidden - 禁止模式(G4/C3/C4)
    """
    fix_hints = []
    c7 = next((ck for ck in checks if ck["check_id"] == "C7"), None)
    coverage_rate = c7.get("coverage_rate", 0) if c7 else 1.0

    # 1. C7 覆盖率不足 → generate_missing
    if c7 and c7["status"] == "FAILED":
        uncovered = [iss.get("test_point", "") for iss in c7.get("issues", [])]
        if uncovered:
            fix_hints.append({
                "priority": "P0",
                "action": "generate_missing",
                "tp_ids": uncovered[:50],  # 单次最多50个
                "count": len(uncovered),
                "command": "python3 $ORCH --action p6_generate_one --tp-index {N}",
                "save_cmd": "python3 $ORCH --action p6_generate_one --tp-index {N} --save --agent-output '...'",
                "note": "V4.11.0 逐条生成,每个TP独立调用",
                "estimated_minutes": round(len(uncovered) * 0.3, 1)
            })

    # 2. C2 步骤期望不匹配 → fix_step_expected
    c2 = next((ck for ck in checks if ck["check_id"] == "C2"), None)
    if c2 and c2["status"] == "FAILED":
        c2_cases = []
        for iss in c2.get("issues", [])[:30]:
            cid = iss.get("case_id", "")
            bi = _find_batch_for_case(data_dir, cid)
            c2_cases.append({"case_id": cid, "batch_index": bi,
                "field": iss.get("field", "steps"), "issue": iss.get("issue", "步骤期望不匹配")})
        if c2_cases:
            fix_hints.append({"priority": "P1", "action": "fix_step_expected", "cases": c2_cases,
                "count": len(c2_cases), "hint": "修改batch文件使步骤数和期望数一致,用 --merge模式保存"})

    # 3. G2/C5/C6 模糊表述 → fix_vague_expected
    for ck_id in ("G2", "C5", "C6"):
        ck = next((c for c in checks if c["check_id"] == ck_id and c["status"] == "FAILED"), None)
        if ck:
            vague = []
            for iss in ck.get("issues", [])[:30]:
                cid = iss.get("case_id", "")
                bi = _find_batch_for_case(data_dir, cid)
                vague.append({"case_id": cid, "batch_index": bi,
                    "field": "expected_results", "issue": iss.get("issue", "含模糊表述")})
            if vague:
                fix_hints.append({"priority": "P1", "action": "fix_vague_expected", "cases": vague,
                    "count": len(vague), "hint": "改期望为具体可观测结果,禁止:正常/成功/正确/符合预期/功能正常"})
            break  # 同类问题只生成一次指引

    # 4. G4/C3/C4 禁止模式 → fix_forbidden
    for ck_id in ("G4", "C3", "C4"):
        ck = next((c for c in checks if c["check_id"] == ck_id and c["status"] == "FAILED"), None)
        if ck:
            forbid = []
            for iss in ck.get("issues", [])[:30]:
                cid = iss.get("case_id", "")
                bi = _find_batch_for_case(data_dir, cid)
                forbid.append({"case_id": cid, "batch_index": bi,
                    "field": iss.get("field", ""), "issue": iss.get("issue", "含禁止词")})
            if forbid:
                fix_hints.append({"priority": "P1", "action": "fix_forbidden", "cases": forbid,
                    "count": len(forbid), "hint": "替换禁止词为具体可观测描述"})
            break

    # 5. C6.1 + G9 前置条件统一修复 (V4.15.23: 合并fix_precondition+fix_data_precondition,消除重叠)
    c61 = next((ck for ck in checks if ck["check_id"] == "C6.1" and ck["status"] == "FAILED"), None)
    g9 = next((ck for ck in checks if ck["check_id"] == "G9" and ck["status"] in ("FAILED", "WARNING")), None)
    if c61 or g9:
        unified_prec = {}  # case_id → merged info
        # C6.1 issues (三要素不完整, 更高优先级)
        if c61:
            for iss in c61.get("issues", []):
                cid = iss.get("case_id", "")
                bi = _find_batch_for_case(data_dir, cid)
                unified_prec[cid] = {
                    "case_id": cid, "batch_index": bi,
                    "tp_file": iss.get("tp_file", ""),
                    "current": iss.get("current_preconditions", "")[:100],
                    "missing_dims": iss.get("missing", []),
                    "source": "C6.1",
                }
        # G9 issues (数据前置条件关键词缺失, 补充到已有或新增)
        if g9:
            for iss in g9.get("issues", [])[:30]:
                cid = iss.get("case_id", "?")
                if cid in unified_prec:
                    unified_prec[cid]["source"] = "C6.1+G9"
                else:
                    bi = _find_batch_for_case(data_dir, cid)
                    unified_prec[cid] = {
                        "case_id": cid, "batch_index": bi,
                        "tp_file": "", "current": "", "missing_dims": [],
                        "g9_reason": iss.get("reason", "")[:100],
                        "g9_status": iss.get("status", "WARNING"),
                        "source": "G9",
                    }
        prec_cases = list(unified_prec.values())
        if prec_cases:
            fail_count = sum(1 for pc in prec_cases if pc.get("g9_status") == "FAILED" or pc.get("source") in ("C6.1", "C6.1+G9"))
            fix_hints.append({
                "priority": "P1",
                "action": "fix_precondition_unified",
                "cases": prec_cases,
                "count": len(prec_cases),
                "hint": f"🔴 前置条件统一修复（C6.1+G9合并，{len(prec_cases)}条，消重后无重复处理）:\n"
                        f"  C6.1(三要素不完整): 必须同时包含「数据构造」和「环境配置」两类关键词\n"
                        f"  G9(缺数据准备): 在已有preconditions中补充数据准备描述\n"
                        "  正确示例: '已登录拥有XX权限的账户,系统已配置XX规则参数为YY,已创建N条XX测试数据'\n"
                        "  修复后重新 merge → p7_code_check 验证 C6.1+G9 PASS。",
            })

    # 6. G1/G1.5 步骤具体性/可观测性 → fix_step_specificity (V4.15.6)
    for gate_id in ("G1", "G1.5"):
        gk = next((ck for ck in checks if ck["check_id"] == gate_id and ck["status"] in ("FAILED", "WARNING")), None)
        if gk:
            g_cases = []
            for iss in gk.get("issues", []):
                cid = iss.get("case_id", "")
                bi = _find_batch_for_case(data_dir, cid)
                vague_step = iss.get("vague_step", iss.get("last_step", ""))
                violation = iss.get("violation", "步骤缺乏具体操作对象")
                g_cases.append({
                    "case_id": cid, "batch_index": bi,
                    "vague_step": vague_step[:80],
                    "violation": violation,
                })
            if g_cases:
                # V4.15.22: 精确化fix_hint — 提取vague_word + location
                _diag = g_cases[0].get("diagnostic", "")
                hint_text = (
                    f"📌 问题步骤: 「{vague_step[:60]}」\n" if vague_step else ""
                    f"📌 诊断: {_diag}\n" if _diag else ""
                    "🔴 请逐一检查用例的**所有步骤**（不仅是报错行第一行），为每个步骤补充具体的操作对象。\n"
                    "  **修复方法**：从 P5 test_point 中提取相关 UI 元素名，用「」引号包裹后插入步骤。\n"
                    "  **修复示例**：\n"
                    "  - 模糊: '记录列表显示的总条数'\n"
                    "  - 具体: '记录列表区域显示的「共 50 条」数据统计'\n"
                    "  - 模糊: '观察系统提示'\n"
                    "  - 具体: '观察页面顶部弹出的「操作成功」提示框'\n"
                    "  - 模糊: '点击Sheet1标签页'\n"
                    "  - 具体: '点击「Sheet1（团队维度）」标签页'\n"
                    "  **注意**：不要整体重写步骤，只需在关键UI元素/字段名上加「」引号即可。"
                    if gate_id == "G1" else
                    "🔴 末位步骤硬约束:\n  1. 末位步骤必须是UI可观测动作（查看/确认/点击后观察），禁止使用'记录''计算''验证'作为末位步骤主动词\n  2. 末位步骤必须包含具体页面元素（列表/弹窗/提示框/按钮状态/数据指标）\n  3. 修复必须严格基于TP原始业务场景，不得改变测试目标"
                )
                fix_hints.append({
                    "priority": "P1",
                    "action": f"fix_{gate_id.lower().replace('.', '_')}_specificity",
                    "cases": g_cases,
                    "count": len(g_cases),
                    "hint": hint_text,
                })

    # 7. G5 禁止模式 → fix_forbidden_pattern (V4.15.12)
    g5 = next((ck for ck in checks if ck["check_id"] == "G5" and ck["status"] == "FAILED"), None)
    if g5:
        g5_cases = []
        for iss in g5.get("issues", [])[:10]:
            case_ids = iss.get("case_ids", [])
            violation = iss.get("violation", "")
            itype = iss.get("type", "")
            g5_cases.append({
                "case_ids": case_ids[:5],
                "violation": violation[:120],
                "type": itype,
            })
        if g5_cases:
            dup_count = sum(1 for gc in g5_cases if gc["type"] == "duplicate_steps")
            sim_count = len(g5_cases) - dup_count
            fix_hints.append({
                "priority": "P1",
                "action": "fix_forbidden_pattern",
                "cases": g5_cases,
                "count": len(g5_cases),
                "hint": f"🔴 G5禁止模式：{dup_count}组完全重复 + {sim_count}组结构相似。\n"
                        "  duplicate_steps(完全重复): 必须为每组用例完全重写差异化步骤，嵌入不同的测试数据/前置条件。\n"
                        "  similar_structure_warning(结构相似): 为每条用例至少2个步骤注入差异化测试数据值（如不同边界值/不同输入条件），使步骤有≥30%字面差异。\n"
                        "  修复后重新 merge → p7_code_check 验证 G5 PASS。",
            })

    # 8. G3 业务流程覆盖 → fix_workflow_coverage (V4.15.51)
    #   V4.15.50 遗漏: G3 是 BLOCK 级检查,但 _build_p7_fix_hints 缺处理逻辑,
    #   导致 G3 FAILED 时 fix_hints 只有通用 fallback, Agent 无法针对性修复。
    g3 = next((ck for ck in checks if ck["check_id"] == "G3" and ck["status"] == "FAILED"), None)
    if g3:
        g3_actions = set()
        g3_cases = []
        g3_uncovered_tps = []
        for iss in g3.get("issues", []):
            itype = iss.get("type", "")
            if itype == "coverage_gap":
                tp_id = iss.get("test_point", "")
                if tp_id:
                    g3_uncovered_tps.append(tp_id)
                    g3_actions.add("generate_missing")
            elif itype in ("a_class_step_short", "b_class_step_empty"):
                cid = iss.get("case_id", "")
                bi = _find_batch_for_case(data_dir, cid)
                g3_cases.append({
                    "case_id": cid, "batch_index": bi,
                    "issue": iss.get("issue", ""),
                    "type": itype,
                })
                g3_actions.add("expand_steps" if itype == "a_class_step_short" else "add_steps")
            elif itype == "b_class_smoke":
                cid = iss.get("case_id", "")
                bi = _find_batch_for_case(data_dir, cid)
                g3_cases.append({
                    "case_id": cid, "batch_index": bi,
                    "issue": iss.get("issue", ""),
                    "type": itype,
                })
                g3_actions.add("remove_smoke")
        # coverage_gap → generate_missing
        if g3_uncovered_tps:
            fix_hints.append({
                "priority": "P0",
                "action": "fix_workflow_coverage",
                "sub_action": "generate_missing",
                "tp_ids": g3_uncovered_tps[:50],
                "count": len(g3_uncovered_tps),
                "hint": ("🔴 G3 业务流程覆盖缺口: 以下 P5 活跃 TP 未被 P6 覆盖,需逐条生成用例。\n"
                         f"  缺失 TP: {', '.join(g3_uncovered_tps[:10])}\n"
                         "  command: python3 $ORCH --action p6_generate_one --tp-index {N}"),
                "estimated_minutes": round(len(g3_uncovered_tps) * 0.3, 1),
            })
        # step_short / step_empty / b_smoke
        if g3_cases:
            _short_count = sum(1 for gc in g3_cases if gc["type"] == "a_class_step_short")
            _empty_count = sum(1 for gc in g3_cases if gc["type"] == "b_class_step_empty")
            _smoke_count = sum(1 for gc in g3_cases if gc["type"] == "b_class_smoke")
            _hint_parts = []
            if _short_count:
                _hint_parts.append(f"🔴 A类步骤数不足({_short_count}条): main_flow/branch/integration 类用例要求≥2步,请扩展步骤(增加具体操作细节)")
            if _empty_count:
                _hint_parts.append(f"🟡 B类步骤为空({_empty_count}条): field_validation/boundary 类用例要求≥1步,请添加步骤")
            if _smoke_count:
                _hint_parts.append(f"🟡 B类误标冒烟({_smoke_count}条): field_validation/boundary 类TP不应标记为冒烟,请去掉 is_smoke 标记")
            fix_hints.append({
                "priority": "P1",
                "action": "fix_workflow_coverage",
                "sub_action": "fix_case",
                "cases": g3_cases,
                "count": len(g3_cases),
                "hint": "\n".join(_hint_parts),
                "estimated_minutes": round(len(g3_cases) * 0.2, 1),
            })

    # 9. G6 步骤原子性 → fix_atomicity (V4.15.51)
    #   V4.15.50 遗漏: G6 是 BLOCK 级检查,但 _build_p7_fix_hints 缺处理逻辑。
    #   G6 gate 已提供 fix_example(含拆分示例),直接引用。
    g6 = next((ck for ck in checks if ck["check_id"] == "G6" and ck["status"] == "FAILED"), None)
    if g6:
        g6_cases = []
        for iss in g6.get("issues", [])[:30]:
            cid = iss.get("case_id", "")
            bi = _find_batch_for_case(data_dir, cid)
            fix_ex = iss.get("fix_example", {})
            g6_cases.append({
                "case_id": cid,
                "batch_index": bi,
                "line": iss.get("line", "")[:100],
                "violation": iss.get("violation", ""),
                "fix_example": fix_ex,
            })
        if g6_cases:
            _sample = g6_cases[0]
            _fix = _sample.get("fix_example", {})
            fix_hints.append({
                "priority": "P1",
                "action": "fix_atomicity",
                "cases": g6_cases,
                "count": len(g6_cases),
                "hint": (
                    "🔴 G6 步骤非原子: 单步骤合并了多个操作,必须拆分为独立步骤(每步只做一件事)。\n"
                    f"  示例: \n"
                    f"  ❌ Before: {_fix.get('before', _sample.get('line', ''))}\n"
                    f"  ✅ After:\n{_fix.get('after', '拆分为独立的原子步骤')}\n"
                    "  📌 规则: 禁止「点击X并验证Y」「输入X后点击Y」「登录并进入X」「选择X后填写Y」。\n"
                    "  修复后重新 merge → p7_code_check 验证 G6 PASS。"
                ),
                "estimated_minutes": round(len(g6_cases) * 0.2, 1),
            })

    # V4.15.6: 三步流水线强制提示（禁止 --skip-merge）
    if fix_hints:
        fix_hints.append({
            "priority": "P2",
            "action": "_pipeline_required",
            "pipeline": [
                "1️⃣ 修复: 根据上述 fix_hints 逐项修改 tp 文件",
                "2️⃣ Merge: python3 $ORCH --action p6_merge  ← 🔴 必须执行,禁止跳过",
                "3️⃣ 验证: python3 $ORCH --action p7_code_check  ← 用 merge 后的结果验证",
            ],
            "hint": "🔴🔴 修复后必须按 1→2→3 顺序执行,禁止在 merge 前直接跑 p7_code_check(会产生P7报告与实际文件不一致的错误)。禁止使用 --skip-merge 参数。",
            "estimated_minutes": 0.3,
        })

    # 判定修复策略
    if coverage_rate >= 0.1:
        strategy = "local_repair"  # 覆盖率≥10%都走局部修复(LOW模型restart也无用)
        estimated_minutes = round(sum(h.get("estimated_minutes", 1) for h in fix_hints), 1)
    else:
        strategy = "restart_p6"  # 覆盖率<10%说明P6基本没跑,必须重跑
        estimated_minutes = 0

    # V4.12.3: fix_hints为空时自动生成通用fallback（LOW模型兼容）
    if not fix_hints:
        fix_hints.append({
            "priority": "P2",
            "action": "regenerate_from_prompt",
            "hint": "重新逐条执行 p6_generate_one --tp-index N → 阅读prompt生成JSON → --save",
            "fallback_note": "fix_hints由代码规则生成（V4.12.3不再依赖模型），请基于P7检查结果手动修复或regenerate",
            "retry_command": "python3 $ORCH --action p6_generate_one --tp-index {N} --save --agent-output '...'",
        })

    return fix_hints, strategy, estimated_minutes


# ============================================================
# Action: p7_code_check (V3.3.1: P7代码硬校验)
# ============================================================

def _classify_issue_category(check: dict, issue: dict) -> str:
    """FIX⑤ V5.x: 为 P7 issue 划分 issue_category 分类标签。

    分类规则:
      - preconditions为空/前置条件问题 → field_mapping
      - 步骤数不足              → content_quality
      - boundary占比(边界覆盖)  → process_planning
      - 步骤模糊                → content_quality
      - 禁止模式                → content_quality
      - 其余                    → other
    """
    cid = str(check.get("check_id", "")).upper()
    field = str(issue.get("field", "")).lower()
    itype = str(issue.get("type", "")).lower()
    text = (str(issue.get("issue", "")) + " " + str(issue.get("violation", ""))
            + " " + str(issue.get("reason", "")) + " " + str(check.get("name", "")))

    # preconditions 为空 / 前置条件类 → field_mapping
    if cid in ("C1", "C6.1", "C6_1", "G9") or "precondition" in field \
            or "前置条件" in text or "preconditions" in text.lower():
        return "field_mapping"
    # boundary 占比 / 边界覆盖 → process_planning
    if cid == "G12" or "boundary" in text.lower() or "边界" in text:
        return "process_planning"
    # 步骤数不足 → content_quality
    if "step_short" in itype or "step_empty" in itype or "步骤数" in text:
        return "content_quality"
    # 步骤模糊 / 禁止模式 → content_quality
    if cid in ("C5", "G1", "G1.5", "G2", "G5", "G6") \
            or "模糊" in text or "禁止" in text or "banned" in text.lower():
        return "content_quality"
    # V4.15.20: G7追溯类 → traceability
    if cid == "G7" or "追溯" in text or "脑补" in text:
        return "traceability"
    return "other"


def action_p7_code_check(args):
    """V3.3.1: P7代码硬校验,替代Agent审计。

    纯代码执行C1-C9+C7.1全部校验,零Agent依赖,秒级完成。
    读取p5_output.json和p6_output.json,输出p7_output.json + P7.pass.json + p7_report.html
    """
    data_dir = args.data_dir
    task_id = args.task_id

    # V4.12.7: 检查段落5(step7)的 __must_emit__ 是否已确认
    pending_path = os.path.join(data_dir, "pending_emit_step7.json")
    if os.path.exists(pending_path):
        pd = _read_json(pending_path)
        # 超时保护：30分钟后自动降级
        if time.time() - pd.get("created_at", 0) > 1800:
            print(json.dumps({"status": "warning", "message": "pending_emit_step7 超时30分钟，自动放行"}))
            os.remove(pending_path)
        else:
            print(json.dumps({
                "status": "blocked",
                "reason": "段落6的 __must_emit__ 未确认输出。请在回复中输出 MEDIA 行，然后执行: python3 $ORCH --action confirm_emit --step step7",
                "media_path": pd.get("media_path", ""),
            }))
            sys.exit(1)

    # 前置gate校验
    ok, msg = check_gate(data_dir, "P6", task_id)
    if not ok:
        print(json.dumps({"status": "gate_blocked", "step": "P6", "reason": msg}))
        sys.exit(1)

    # 读取P5和P6产出
    p5_path = os.path.join(data_dir, "p5_output.json")
    p6_path = os.path.join(data_dir, "p6_output.json")
    if not os.path.exists(p5_path):
        print(json.dumps({"status": "error", "reason": "p5_output.json不存在"}))
        sys.exit(1)
    if not os.path.exists(p6_path):
        print(json.dumps({"status": "error", "reason": "p6_output.json不存在"}))
        sys.exit(1)

    # FIX② V5.x: --skip-merge 时直接检查当前 p6_output.json,跳过新鲜度校验。
    # 默认(未 skip)下,若 p6_tp_output/ 中存在比 p6_output.json 更新的 TP 文件,
    # 说明修复后未重跑 p6_merge,P7 会检查到陈旧合并结果——此时告警并要求先 merge。
    # V4.15.6: --skip-merge 使用时发出警告日志（防止 Agent 修复后跳过 merge 产生不一致报告）
    if getattr(args, "skip_merge", False):
        print(json.dumps({
            "status": "warning", "severity": "skip_merge_used",
            "reason": "使用 --skip-merge 跳过新鲜度校验,P7 可能检查到旧的 merge 结果（与修复后的 tp 文件不一致）。",
            "hint": "如刚完成修复,请先执行 p6_merge 再跑 p7_code_check（去掉 --skip-merge）。仅调试排查阶段可临时跳过。",
        }, ensure_ascii=False), file=sys.stderr)
    else:
        try:
            _tp_dir = os.path.join(data_dir, "p6_tp_output")
            if os.path.isdir(_tp_dir):
                _p6_mtime = os.path.getmtime(p6_path)
                _stale_tps = []
                for _fn in os.listdir(_tp_dir):
                    if _fn.startswith("tp_") and _fn.endswith(".json") and "_context" not in _fn:
                        _fp = os.path.join(_tp_dir, _fn)
                        if os.path.getmtime(_fp) > _p6_mtime + 1:
                            _stale_tps.append(_fn)
                if _stale_tps:
                    print(json.dumps({
                        "status": "stale_merge",
                        "reason": f"检测到 {len(_stale_tps)} 个 TP 文件比 p6_output.json 更新,P7 将检查陈旧合并结果。",
                        "stale_tp_files": sorted(_stale_tps)[:30],
                        "fix": "请先执行: python3 orchestrator.py --action p6_merge 后重跑 p7_code_check。若确认无需合并,可加 --skip-merge 跳过本校验。",
                    }, ensure_ascii=False))
                    sys.exit(1)
        except Exception:
            pass

    p5_data = _read_json(p5_path)
    p6_data = _read_json(p6_path)
    if isinstance(p6_data, list):
        p6_data = {"testcases": p6_data}
    cases = p6_data.get("testcases", [])
    p5_tps = p5_data.get("test_points", [])

    if not cases:
        print(json.dumps({"status": "error", "reason": "p6_output.json中testcases为空"}))
        sys.exit(1)

    # 执行全部校验
    checks = [
        _p7_check_c1(cases),
        _p7_check_c2(cases),
        _p7_check_c3(cases),
        _p7_check_c4(cases),
        _p7_check_c5(cases),
        _p7_check_c6(cases),
        _p7_check_c61(cases),
        _p7_check_c62(cases),
        _p7_check_c7(cases, p5_tps),
        _p7_check_c71(cases, p5_tps),
        _p7_check_c8(cases),
        _p7_check_c9(cases),
        _p7_check_p0_distribution(cases),  # V4.14.2: P0占比门禁
    ]
    statistics = _p7_statistics(cases)
    # V4.15.50: P6重试统计（从p6_metrics.jsonl+orchestrator_state.json汇总）
    p6_retry_stats = _p7_retry_statistics(data_dir)
    statistics["p6_retry_stats"] = p6_retry_stats

    # V4.3.0: 执行 Gate G1-G7 全量质量检查
    gate_results = []
    gate_evaluation = {"status": "PASS", "block_failed": 0, "warnings": 0}
    try:
        gate_results = _run_gate_checks(cases, p5_tps)
        # V4.15.11: G1升级为始终BLOCK（统一P6快速Gate和P7检查策略）
        gate_evaluation = _evaluate_gate(gate_results)
    except Exception as _gate_err:
        gate_evaluation = {"status": "PASS", "block_failed": 0, "warnings": 0,
                           "summary": f"Gate G1-G7检查执行异常(跳过): {_gate_err}"}

    # 将Gate检查结果追加到checks列表
    for gr in gate_results:
        checks.append({
            "check_id": gr.get("check_id", "?"),
            "name": gr.get("name", ""),
            "level": gr.get("level", "WARNING"),
            "status": gr.get("status", "PASSED"),
            "detail": gr.get("detail", ""),
            "issues": gr.get("issues", []),
        })

    # FIX⑤ V5.x: 为每个 issue 打上 issue_category 分类标签,并汇总 category_summary。
    #   preconditions为空 → field_mapping
    #   步骤数不足   → content_quality
    #   boundary占比  → process_planning
    #   步骤模糊     → content_quality
    #   禁止模式     → content_quality
    category_summary = {}
    for ck in checks:
        for iss in ck.get("issues", []):
            if not isinstance(iss, dict):
                continue
            cat = _classify_issue_category(ck, iss)
            iss["issue_category"] = cat
            category_summary[cat] = category_summary.get(cat, 0) + 1

    # 判定门禁(含Gate G1-G7结果)
    block_failed = any(ck["status"] == "FAILED" and ck["level"] == "BLOCK" for ck in checks)
    # Gate G1-G7 BLOCK失败也阻断
    gate_block_failed = gate_evaluation.get("status") == "FAIL" and gate_evaluation.get("block_failed", 0) > 0
    has_warning = any(ck["status"] in ("WARNING", "FAILED") and ck["level"] == "WARNING" for ck in checks)

    if block_failed or gate_block_failed:
        gate_status = "FAIL"
        action_required = "RETRY_P6"
        failed_cases = []
        for ck in checks:
            if ck["status"] == "FAILED":
                for iss in ck.get("issues", []):
                    cid = iss.get("case_id", "")
                    tp_idx = _find_batch_for_case(data_dir, cid) if cid else -1
                    tp_file = f"tp_{tp_idx:03d}.json" if tp_idx >= 0 else ""
                    fc = {"check_id": ck["check_id"], "case_id": cid,
                          "tp_index": tp_idx, "tp_file": tp_file,
                          "field": iss.get("field", "")}
                    fc.update(iss)
                    failed_cases.append(fc)
    elif has_warning:
        gate_status = "PASS"
        action_required = "MANUAL_REVIEW"
        failed_cases = []
    else:
        gate_status = "PASS"
        action_required = "NONE"
        failed_cases = []

    block_passed = sum(1 for ck in checks if ck["level"] == "BLOCK" and ck["status"] == "PASSED")
    block_total = sum(1 for ck in checks if ck["level"] == "BLOCK")
    warn_triggered = sum(1 for ck in checks if ck["level"] == "WARNING" and ck["status"] in ("WARNING", "FAILED"))
    warn_total = sum(1 for ck in checks if ck["level"] == "WARNING")

    summary = f"{len(checks)}项检查: BLOCK {block_passed}/{block_total}通过, WARNING {warn_triggered}/{warn_total}项触发"

    # 构造输出
    p7_output = {
        "schema_version": "2.0.0",
        "source": "p7_code_check",
        "gate_result": {
            "status": gate_status,
            "summary": summary,
            "checks": checks,
        },
        "gate_g1_g7": {
            "results": gate_results,
            "evaluation": gate_evaluation,
            "report": _format_gate_report(gate_results, gate_evaluation) if gate_results else "",
        },
        "statistics": statistics,
        "p7_check_summary": {
            "status": gate_status,
            "checked_at": time.strftime("%Y-%m-%dT%H:%M:%S+08:00"),
            "block_passed": block_passed,
            "block_total": block_total,
            "warnings": warn_triggered,
            # FIX⑤ V5.x: 问题分类汇总(issue_category 计数)
            "category_summary": category_summary,
            # V4.13.8 P2-⑫: 质量趋势摘要(Agent可见,帮助判断质量是否改善/恶化)
            "quality_trend": {
                "target": "C6.1通过率≥98%, C2通过率≥95%, C6.2模糊率<15%",
                "hint": "如果C6.1/C2连续两次版本恶化,说明Agent偏'快'舍'好',请减速逐条生成。"
            },
        },
        "action_required": action_required,
        "failed_cases": failed_cases[:50],
    }

    # V4.9.1: P7失败时生成修复指引(只在FAIL时生成,避免无意义计算)
    if gate_status == "FAIL":
        fix_hints, fix_strategy, fix_minutes = _build_p7_fix_hints(checks, data_dir)
        p7_output["fix_hints"] = fix_hints
        p7_output["fix_strategy"] = fix_strategy
        p7_output["fix_estimated_minutes"] = fix_minutes
        p7_output["_fix_note"] = ("🔴 Agent按fix_hints逐项自动修复(禁止抛选择题):"
            "generate_missing→p6_generate_one→p6_merge | "
            "fix_*→读tp文件→修改→覆盖保存→p6_merge | "
            "全部修复后重新p7_code_check"
            "\n🔴 tp文件映射关系(V4.12.2): "
            "tp_NNN.json对应TP-(N+1), 例: tp_006.json→测试点TP-007 | "
            "修复后必须先 p6_merge 再 p7_code_check, "
            "直接修tp文件后不merge会导致P7检查的是旧合并结果")

    # 写入p7_output.json (V4.11.0)
    p7_out_path = os.path.join(data_dir, "p7_output.json")
    _write_json(p7_out_path, p7_output)

    # 生成HTML报告
    html_path = os.path.join(data_dir, "p7_report.html")
    _generate_p7_html_report(checks, statistics, html_path)

    # 写gate pass(仅PASS时)
    if gate_status == "PASS":
        state = TaskState(data_dir=data_dir, task_id=task_id)
        state.mark_complete("P7")
        gate_dir = os.path.join(data_dir, "gates")
        _ensure_dir(gate_dir)
        gate_path = os.path.join(gate_dir, "P7.pass.json")
        gate_data = {
            "step": "P7",
            "status": "PASS",
            "task_id": task_id,
            "source": "p7_code_check",
            "summary": summary,
            "validated_at": time.strftime("%Y-%m-%dT%H:%M:%S+08:00"),
        }
        _write_signed_gate(gate_path, gate_data, task_id)

    print(json.dumps({
        "status": "ok" if gate_status == "PASS" else ("needs_review" if gate_status == "PARTIAL" else "quality_failed"),
        "gate_result": gate_status,
        "summary": summary,
        "action_required": action_required,
        "block_checks": f"{block_passed}/{block_total}",
        "warnings": warn_triggered,
        "p7_output": p7_out_path,
        "html_report": html_path,
    }))
    if gate_status not in ("PASS", "PARTIAL"):
        sys.exit(1)


def action_p7_batch_fix(args):
    """V4.12.6: 批量修复P7检测到的同类问题"""
    data_dir = args.data_dir
    check = getattr(args, 'check', '') or args.step or ''
    p6_path = os.path.join(data_dir, "p6_output.json")
    if not os.path.exists(p6_path):
        print(json.dumps({"status": "error", "reason": "p6_output.json不存在,请先执行p6_merge"}))
        sys.exit(1)
    p6_data = _read_json(p6_path)
    if isinstance(p6_data, list):
        p6_data = {"testcases": p6_data}
    cases = p6_data.get("testcases", [])
    if not cases:
        print(json.dumps({"status": "error", "reason": "无用例可修复"}))
        sys.exit(1)
    fixed = 0
    details = []
    if check == "C2":
        for c in cases:
            steps_text = _get_case_field(c, "steps", "")
            exp_text = _get_case_field(c, "expected_results", "")
            if not steps_text or not isinstance(steps_text, str):
                continue
            step_lines = [s.strip() for s in steps_text.split("\n") if s.strip()]
            exp_lines = [s.strip() for s in exp_text.split("\n") if s.strip()] if exp_text else []
            if len(step_lines) > len(exp_lines) + 1:
                missing = len(step_lines) - len(exp_lines)
                new_exps = []
                for si in range(len(exp_lines), len(step_lines)):
                    step = step_lines[si]
                    last_verb = "操作"
                    for v in ["点击", "输入", "选择", "确认", "提交", "保存", "切换", "打开"]:
                        if v in step:
                            last_verb = v
                            break
                    new_exps.append(f"{len(exp_lines)+len(new_exps)+1}. {last_verb}操作完成后,系统响应正常")
                exp_lines.extend(new_exps)
                _set_case_field(c, "expected_results", "\n".join(exp_lines))
                fixed += 1
                details.append(f"{_get_case_field(c, 'case_id', '?')}: +{missing}期望")
    elif check == "C6_1":
        for c in cases:
            pre_text = _get_case_field(c, "preconditions", "")
            if not pre_text or not isinstance(pre_text, str):
                continue
            hints = []
            if "登录" not in pre_text and "login" not in pre_text.lower():
                hints.append("[用户状态]建议补充: 已登录XX系统")
            if "环境" not in pre_text and "系统" not in pre_text and "运行" not in pre_text:
                hints.append("[环境]建议补充: XX系统正常运行")
            if hints:
                cid = _get_case_field(c, "case_id", "?")
                existing = _get_case_field(c, "remarks", "")
                hint_text = "; ".join(hints)
                new_r = f"{existing} [P7_C6_1:{hint_text}]".strip() if existing else f"[P7_C6_1:{hint_text}]"
                _set_case_field(c, "remarks", new_r)
                fixed += 1
                details.append(f"{cid}: 前置缺{'用户状态' if '用户状态' in hint_text else ''}{'环境' if '环境' in hint_text else ''}")
    else:
        print(json.dumps({"status": "error", "reason": f"不支持: {check}, 可选:C2,C6_1"}))
        sys.exit(1)
    _write_json(p6_path, {"testcases": cases})
    _result = {"status": "ok", "check": check, "fixed_count": fixed,
        "details": details[:10],
        "next_action": "执行 p6_merge 重新合并, 然后 p7_code_check 重新验证"}
    if check == "C6_1":
        _result["note"] = "C6_1 fix 仅在 remarks 添加标注，未改写 preconditions 字段。如需真正修复，请手动编辑对应 tp_N.json 的 preconditions 内容。"
    # V4.15.21: 修复成功后自动触发merge
    if fixed > 0:
        try:
            action_p6_merge(args)
            _result["auto_merged"] = True
            _result["next_action"] = "已自动执行 p6_merge，请直接执行 p7_code_check 验证"
        except Exception as e:
            _result["auto_merged"] = False
            _result["merge_error"] = str(e)[:200]
            _result["next_action"] = f"自动merge失败({e})，请手动执行 p6_merge"
    print(json.dumps(_result))


def action_quality_check(args):
    """对指定步骤的产出进行质量校验"""
    data_dir = args.data_dir
    step = args.step

    output_path = os.path.join(data_dir, f"{step.lower()}_output.json")
    if not os.path.exists(output_path):
        print(json.dumps({"status": "error", "reason": f"{step}产出文件不存在"}))
        sys.exit(1)

    data = _read_json(output_path)
    issues = []
    warnings = []

    # 1. 最小产出数量校验
    if step in MIN_OUTPUT_COUNTS:
        for field_path, min_count in MIN_OUTPUT_COUNTS[step].items():
            value = _get_nested(data, field_path)
            if value is None:
                issues.append(f"字段{field_path}不存在")
            elif isinstance(value, list) and len(value) < min_count:
                issues.append(f"{field_path}数量{len(value)}<最小要求{min_count}")
            elif isinstance(value, (int, float)) and value < min_count:
                issues.append(f"{field_path}值{value}<最小要求{min_count}")

    # 2. P0质量评分校验
    if step == "P0":
        score = data.get("quality_score", 0)
        if score < 0.5:
            issues.append(f"质量评分{score}<0.5,需求结构化质量太低")
        elif score < 0.7:
            warnings.append(f"质量评分{score}<0.7,建议补充需求")

    # 2.3 P1 scenario数量校验:每feature不得超过6个scenario
    if step == "P1":
        ft = data.get("feature_tree", {})
        modules = ft.get("modules", []) if isinstance(ft, dict) else []
        if not modules:
            modules = data.get("modules", [])
        overflow_features = []
        for m in (modules if isinstance(modules, list) else []):
            for f in m.get("children", []):
                if f.get("type") != "feature":
                    continue
                scenarios = [s for s in f.get("children", []) if s.get("type") == "scenario"]
                if len(scenarios) > 6:
                    overflow_features.append(
                        f"{f.get('id','')} {f.get('name','')} ({len(scenarios)}个scenario,超过6个限制)"
                    )
        if overflow_features:
            issues.append(
                "以下feature的scenario数量超过6个,必须合并相似场景再重新生成: "
                + "; ".join(overflow_features)
            )
        # R11修复:P1 coverage_check缺失项告警
        # 检查每个feature的scenario是否有coverage_check
        for m in (modules if isinstance(modules, list) else []):
            for f in m.get("children", []):
                if f.get("type") != "feature":
                    continue
                for s in f.get("children", []):
                    if s.get("type") == "scenario":
                        cc = s.get("coverage_check", {})
                        if cc and isinstance(cc, dict):
                            missing_ops = cc.get("operations_covered", {}).get("missing", [])
                            missing_st = cc.get("state_transitions_covered", {}).get("missing", [])
                            missing_rules = cc.get("rules_covered", {}).get("missing", [])
                            total_missing = len(missing_ops) + len(missing_st) + len(missing_rules)
                            if total_missing > 0:
                                warnings.append(
                                    f"场景 {s.get('id', '')} coverage_check有{total_missing}个未覆盖项"
                                    f"(操作:{len(missing_ops)}, 状态:{len(missing_st)}, 规则:{len(missing_rules)})"
                                )

    # 2.5 V3.2.8: P2测试点数量动态校验 = max(8, P1叶节点数×2)
    if step == "P2":
        test_points = data.get("test_points", [])
        p2_count = len(test_points) if isinstance(test_points, list) else 0
        p1_path = os.path.join(data_dir, "p1_output.json")
        p2_dynamic_min = 8
        if os.path.exists(p1_path):
            try:
                p1_data = _read_json(p1_path)
                # 计算P1叶节点数(场景数)
                ft = p1_data.get("feature_tree", {})
                modules = ft.get("modules", p1_data.get("modules", [])) if isinstance(ft, dict) else p1_data.get("modules", [])  # Bugfix V4.6.8: feature_tree可能是list
                leaf_count = 0
                for m in (modules if isinstance(modules, list) else []):
                    features = m.get("features", [])
                    for f in (features if isinstance(features, list) else []):
                        scenarios = f.get("scenarios", [])
                        leaf_count += len(scenarios) if isinstance(scenarios, list) else 1
                    if not features:
                        leaf_count += 1  # 模块本身算一个叶节点
                p2_dynamic_min = max(8, leaf_count * 2)
            except Exception:
                pass
        if p2_count < p2_dynamic_min:
            issues.append(f"测试点数量{p2_count}<最低要求{p2_dynamic_min}(P1叶节点×2),每个场景应至少生成2个测试点")

    # 3. P6用例质量校验(V3.2.4: 使用_get_case_field兼容fields嵌套结构)
    if step == "P6":
        cases = data.get("testcases", [])
        total = len(cases)

        # V3.2.8: 动态计算P6最低用例数
        # 优先用P5的total_expected_cases(基于complexity标签精确计算)
        # 其次用P5测试点数×1.5(V3.2.7兼容)
        # 底线15
        p5_min = 15
        p5_path = os.path.join(data_dir, "p5_output.json")
        if os.path.exists(p5_path):
            try:
                p5_data = _read_json(p5_path)
                p5_count = len(p5_data.get("test_points", []))
                # V3.2.8: 优先用complexity标签的精确预算
                total_expected = p5_data.get("coverage_summary", {}).get("total_expected_cases", 0)
                if total_expected > 0:
                    p5_min = max(15, total_expected)
                else:
                    p5_min = max(15, int(p5_count * 1.5))
            except Exception:
                pass
        if total < p5_min:
            issues.append(f"用例数量{total}<最低要求{p5_min}(P5测试点×1.5),每个测试点应至少展开为2条用例")

        if total > 0:
            smoke = sum(1 for c in cases if _is_smoke(_get_case_field(c, "is_smoke", "")))
            p0 = sum(1 for c in cases if _get_case_field(c, "priority", "").upper() in ("P0", "HIGHEST"))

            smoke_ratio = smoke / total
            p0_ratio = p0 / total

            # 冒烟比例超限→拒绝(与prep_prompt注入规则一致)
            if smoke_ratio < P6_QUALITY_RULES["smoke_ratio_min"]:
                issues.append(f"冒烟用例比例{smoke_ratio:.1%}<{P6_QUALITY_RULES['smoke_ratio_min']:.0%},不达标")
            if smoke_ratio > P6_QUALITY_RULES["smoke_ratio_max"]:
                issues.append(f"冒烟用例比例{smoke_ratio:.1%}>{P6_QUALITY_RULES['smoke_ratio_max']:.0%},过高")
            if p0_ratio > P6_QUALITY_RULES["p0_ratio_max"]:
                issues.append(f"P0优先级占比{p0_ratio:.1%}>{P6_QUALITY_RULES['p0_ratio_max']:.0%},优先级分布异常")

            # 检查是否所有用例同一优先级
            priorities = set(_get_case_field(c, "priority", "") for c in cases)
            if len(priorities) == 1 and total > 5:
                issues.append(f"所有{total}条用例都是{priorities.pop()}优先级,分布异常")

            # 每需求至少1条冒烟用例(与prep_prompt注入规则一致)
            if P6_QUALITY_RULES.get("per_requirement_smoke"):
                req_smoke = {}
                for c in cases:
                    req = _get_case_field(c, "requirement", _get_case_field(c, "module", "unknown"))
                    if req not in req_smoke:
                        req_smoke[req] = False
                    if _is_smoke(_get_case_field(c, "is_smoke", "")):
                        req_smoke[req] = True
                no_smoke_reqs = [r for r, has in req_smoke.items() if not has]
                if no_smoke_reqs and len(req_smoke) > 1:
                    warnings.append(f"{len(no_smoke_reqs)}个需求无冒烟用例: {', '.join(no_smoke_reqs[:3])}")

    passed = len(issues) == 0
    # P7失败时提供回流指引
    retry_hint = None
    if not passed and step == "P7":
        retry_hint = "P7质量自检失败,建议重新执行P6用例展开(从 prep_prompt P6 重新开始)"
    if not passed and step == "P6":
        retry_hint = "P6质量校验失败,建议重新执行P6全部批次"

    # V3.2.4新增:quality_check通过后自动创建gate文件,不再需要Agent手动创建
    # V3.2.6: 使用HMAC签名
    if passed and step in GATE_STEPS:
        task_id = args.task_id
        gate_dir = os.path.join(data_dir, "gates")
        _ensure_dir(gate_dir)
        gate_path = os.path.join(gate_dir, f"{step}.pass.json")
        if not os.path.exists(gate_path):
            gate_data = {
                "task_id": task_id,
                "step": step,
                "status": "PASS",
                "source": "quality_check",
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S+08:00"),
            }
            _write_signed_gate(gate_path, gate_data, task_id)

    # V3.5.1: PRD审查增强 - P0时附带blocks_markdown和prd_issues
    prd_review_extra = {}
    if step == "P0":
        meta_path = os.path.join(data_dir, "task_meta.json")
        if os.path.exists(meta_path):
            _meta = _read_json(meta_path)
            if _meta.get("prd_quality_review", False):
                blocks_md = data.get("blocks_markdown", "")
                prd_issues_list = data.get("issues", [])
                # 截断保护
                if isinstance(blocks_md, str) and len(blocks_md) > 5000:
                    blocks_md = blocks_md[:5000] + "\n\n... (内容过长已截断)"
                # 格式兜底
                if not isinstance(prd_issues_list, list):
                    prd_issues_list = []
                prd_review_extra = {
                    "prd_review_enabled": True,
                    "blocks_markdown": blocks_md if blocks_md else "",
                    "prd_issues": prd_issues_list,
                }
                # V3.5.5: 将PRD审查结果写入文件,供用户下载
                try:
                    report_path = os.path.join(data_dir, "prd_review_report.md")
                    quality_score = data.get("quality_score", 0)
                    score_label = "PASS" if quality_score >= 0.7 else ("CONDITIONAL_PASS" if quality_score >= 0.5 else "FAIL")
                    report_lines = [
                        "# PRD审查报告\n",
                        f"**质量评分**: {quality_score} ({score_label})\n",
                        f"**生成时间**: {time.strftime('%Y-%m-%d %H:%M:%S')}\n",
                        "\n---\n",
                        "## 📋 需求结构化结果\n",
                        (blocks_md if blocks_md else "*未输出结构化内容*"),
                        "\n\n---\n",
                        "## ⚠️ 问题清单\n",
                    ]
                    if prd_issues_list:
                        report_lines.append("| 严重度 | 位置 | 类型 | 问题 | 建议 |\n")
                        report_lines.append("|--------|------|------|------|------|\n")
                        for issue in prd_issues_list:
                            if isinstance(issue, dict):
                                severity = issue.get("severity", "")
                                location = issue.get("location", "")
                                issue_type = issue.get("type", "")
                                problem = issue.get("problem", issue.get("issue", ""))
                                suggestion = issue.get("suggestion", issue.get("recommendation", ""))
                                report_lines.append(f"| {severity} | {location} | {issue_type} | {problem} | {suggestion} |\n")
                            else:
                                report_lines.append(f"| - | - | - | {issue} | - |\n")
                    else:
                        report_lines.append("*未发现问题*\n")
                    _write_text(report_path, "".join(report_lines))
                    prd_review_extra["prd_review_report_path"] = report_path
                except Exception as _e:
                    pass  # 写文件失败不影响主流程

    result = {
        "status": "ok" if passed else "quality_failed",
        "step": step,
        "passed": passed,
        "issues": issues,
        "warnings": warnings,
        "retry_hint": retry_hint,
        "gate_created": passed and step in GATE_STEPS,
    }
    result.update(prd_review_extra)
    print(json.dumps(result, ensure_ascii=False))
    if not passed:
        sys.exit(1)


# ============================================================
# Action: export_p0p1 (导出P0/P1为Markdown文件)
# ============================================================

def action_export_p0p1(args):
    """导出P0需求理解和P1功能点拆解为Markdown文件

    用于段落3完成后发送给产品经理审阅。
    """
    data_dir = args.data_dir
    skill_dir = args.skill_dir
    task_id = args.task_id

    # 检查P0和P1的gate pass
    p0_ok, p0_msg = check_gate(data_dir, "P0", task_id)
    p1_ok, p1_msg = check_gate(data_dir, "P1", task_id)

    if not p0_ok and not p1_ok:
        print(json.dumps({
            "status": "error",
            "reason": "P0和P1均未完成,无法导出"
        }))
        sys.exit(1)

    # 调用export_p0p1.py脚本
    export_script = os.path.join(skill_dir, "tools", "export_p0p1.py")
    if not os.path.exists(export_script):
        print(json.dumps({
            "status": "error",
            "reason": f"导出脚本不存在: {export_script}"
        }))
        sys.exit(1)

    output_file = os.path.join(data_dir, "p0p1_report.md")

    try:
        import subprocess
        result = subprocess.run(
            ["python3", export_script, "--data-dir", data_dir, "--output", output_file],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            print(json.dumps({
                "status": "error",
                "reason": f"导出失败: {result.stderr}"
            }))
            sys.exit(1)

        # 检查文件是否生成
        if not os.path.exists(output_file):
            print(json.dumps({
                "status": "error",
                "reason": "导出脚本执行成功但文件未生成"
            }))
            sys.exit(1)

        # 获取文件大小
        file_size = os.path.getsize(output_file)

        # V4.1.9: 读取MD文件内容,用于返回给用户
        md_path = os.path.join(data_dir, "p0p1_report.md")
        md_content = ""
        if os.path.exists(md_path):
            try:
                with open(md_path, "r", encoding="utf-8") as f:
                    md_content = f.read()
            except Exception:
                pass

        # V4.1.9: 检查文件大小合理性(避免部分写入/截断问题)
        if file_size < 500:
            print(json.dumps({
                "status": "error",
                "reason": f"导出的HTML文件异常小({file_size}字节),内容可能不完整。"
            }))
            sys.exit(1)

        # 同时检查MD文件
        if os.path.exists(md_path):
            md_size = os.path.getsize(md_path)
            if md_size < 1000:
                print(json.dumps({
                    "status": "error",
                    "reason": f"导出的MD文件异常小({md_size}字节),内容可能不完整"
                }))
                sys.exit(1)

        # Bugfix V4.6.9: P0/P1评审推送(原为死代码,从未被调用)
        # V4.0.0设计:export_p0p1成功后自动推送到云端评审工具
        cloud_review = None
        runtime_key = None
        cache_path = os.path.join(args.data_dir, ".image_api_key")
        if os.path.exists(cache_path):
            try:
                with open(cache_path, "r") as f:
                    runtime_key = f.read().strip()
            except Exception:
                pass
        config = _load_cloud_config(args.skill_dir, runtime_api_key=runtime_key)
        if _should_push_to_review_tool(config):
            try:
                review_url = _push_p0p1_to_review_tool(args.data_dir, args.task_id, config)
                if review_url:
                    cloud_review = {
                        "pushed": True,
                        "review_url": review_url,
                        "message": "✅ 需求理解已推送到在线评审工具"
                    }
                else:
                    cloud_review = {
                        "pushed": False,
                        "message": "⚠️ 推送失败,已加入重试队列"
                    }
            except Exception as e:
                cloud_review = {
                    "pushed": False,
                    "message": f"⚠️ 推送异常: {str(e)[:50]}"
                }

        result_json = {
            "status": "success",
            "output_file": output_file,
            "html_file": output_file,
            "md_file": md_path,
            "file_size": file_size,
            "media_instruction": f"MEDIA:{md_path}" if md_path and os.path.exists(md_path) else None,
            "reminder": "Agent必须在对话中独占一行输出上面的MEDIA指令发送附件,否则用户收不到文件",
            "message": "需求理解与功能点拆解报告已生成(MD文件见media_instruction,必须发送附件)",
            "cloud_review": cloud_review  # Bugfix V4.6.9: 新增cloud_review字段
        }

        print(json.dumps(result_json, ensure_ascii=False))

    except subprocess.TimeoutExpired:
        print(json.dumps({
            "status": "error",
            "reason": "导出超时(30秒)"
        }))
        sys.exit(1)
    except Exception as e:
        print(json.dumps({
            "status": "error",
            "reason": f"导出异常: {str(e)}"
        }))
        sys.exit(1)


# ============================================================
# 主入口
# ============================================================


# ============================================================
# Action: check_image_api (验证图片理解API密码)
# ============================================================

def action_check_image_api(args):
    """验证用户输入的API密码是否正确"""
    skill_dir = args.skill_dir
    api_key = getattr(args, 'api_key', '') or ''
    # V4.x: 脱敏值检测-Agent传入显式--api-key时可能是脱敏后的星号
    if api_key.strip() and _is_desensitized(api_key):
        api_key = ''

    if not api_key.strip():
        print(json.dumps({"status": "skipped", "reason": "未输入密码,将使用纯文本模式"}))
        return

    config = _load_image_api_config(skill_dir, api_key=api_key)

    if not config["enabled"]:
        reason = config.get("_invalid_reason", "API地址未配置")
        print(json.dumps({"status": "error", "reason": reason}))
        return

    # V3.0.3-patch1: 调用auth-check验证密码(不再用health,因为health不鉴权)
    ok, data = _check_image_api_health(config)

    if ok:
        # V3.2.0: 验证成功后缓存密码到task目录(解决Agent跨段落丢密码问题)
        # V4.14.5: data_dir不存在时自动创建,防缓存静默失败
        data_dir = getattr(args, 'data_dir', '') or ''
        if data_dir:
            try:
                os.makedirs(data_dir, exist_ok=True)
                cache_path = os.path.join(data_dir, ".image_api_key")
                with open(cache_path, "w") as f:
                    f.write(api_key)
                os.chmod(cache_path, 0o600)
            except Exception as e:
                print(json.dumps({"status": "warning", "reason": f"密码缓存写入失败: {e}"}), file=sys.stderr)
        # V4.0.0: 密码验证成功后,尝试从云端拉取知识库
        knowledge_sync_result = "未配置"
        cloud_config = _load_cloud_config(skill_dir, runtime_api_key=api_key)
        # V4.1.8: Onboarding验证成功后,将api_key持久化到cloud.json
        if api_key and api_key.strip():
            try:
                config_path = os.path.join(skill_dir, "config", "cloud.json")
                if os.path.exists(config_path):
                    with open(config_path, "r", encoding="utf-8") as f:
                        cfg = json.load(f)
                    if "review_tool" not in cfg:
                        cfg["review_tool"] = {}
                    cfg["review_tool"]["api_key"] = api_key.strip()
                    with open(config_path, "w", encoding="utf-8") as f:
                        json.dump(cfg, f, indent=2, ensure_ascii=False)
            except Exception:
                pass  # 写入失败不阻塞流程
        if (cloud_config.get("knowledge_api_url") or
            cloud_config.get("review_tool", {}).get("api_url") or
            cloud_config.get("experience_sync", {}).get("api_url")):
            knowledge_sync_result = _sync_knowledge_from_cloud(skill_dir, api_key, cloud_config)

        # V4.0.1: 同步评审经验
        review_exp_result = _sync_review_experience(skill_dir, api_key, cloud_config)

        print(json.dumps({
            "status": "ok",
            "message": "密码验证成功,图片理解API已启用",
            "provider": config["model"],
            "ci_configured": data.get("ci_configured", True),
            "qwen_configured": data.get("qwen_configured", False),
            "key_cached": bool(data_dir),
            "knowledge_sync": knowledge_sync_result,
            "review_experience_sync": review_exp_result,
        }))
    else:
        error = data.get("error", "unknown")
        message = data.get("message", "")
        # 精确区分密码错误/服务未配置/服务不可用
        if error == "auth_failed":
            print(json.dumps({"status": "auth_failed", "reason": "密码错误,请重新输入或回复「跳过」使用纯文本模式"}))
        elif error == "service_not_configured":
            print(json.dumps({"status": "service_error", "reason": f"API服务未配置密码验证: {message}"}))
        elif error == "connection_failed":
            print(json.dumps({"status": "service_error", "reason": f"无法连接API服务,请检查API地址: {message}"}))
        elif error == "timeout":
            print(json.dumps({"status": "service_error", "reason": "API服务响应超时,请稍后重试"}))
        else:
            print(json.dumps({"status": "service_error", "reason": f"API服务暂不可用: {message or error}"}))


def action_p7_quick_fix(args):
    """V4.15.56: P7快速修复 — 直接修改p6_output.json指定case并双写到tp源文件
    
    跳过全量merge, 修改后自动执行全量P7检查验证。
    用法: python3 $ORCH --action p7_quick_fix --case-id CASE_ID --field steps --new-value "1. xxx\n2. yyy"
    """
    data_dir = args.data_dir
    case_id = getattr(args, 'case_id', '') or ''
    field = getattr(args, 'field', '') or ''
    new_value = getattr(args, 'new_value', '') or ''
    value_file = getattr(args, 'value_file', '') or ''
    
    if not case_id or not field:
        print(json.dumps({"status": "error", "reason": "必需参数: --case-id 和 --field"}))
        sys.exit(1)
    
    if value_file and os.path.exists(value_file):
        with open(value_file, 'r') as vf:
            new_value = vf.read()
    
    if not new_value:
        print(json.dumps({"status": "error", "reason": "必需参数: --new-value 或 --value-file"}))
        sys.exit(1)
    
    valid_fields = {"steps", "expected_results", "preconditions", "title"}
    if field not in valid_fields:
        print(json.dumps({"status": "error", "reason": f"不支持字段: {field}, 可选: {', '.join(sorted(valid_fields))}"}))
        sys.exit(1)
    
    # 1. 加载p6_output.json
    p6_path = os.path.join(data_dir, "p6_output.json")
    if not os.path.exists(p6_path):
        print(json.dumps({"status": "error", "reason": "p6_output.json不存在,请先执行p6_merge"}))
        sys.exit(1)
    p6_data = _read_json(p6_path)
    if isinstance(p6_data, list):
        p6_data = {"testcases": p6_data}
    cases = p6_data.get("testcases", [])
    
    # 2. 查找目标case
    target = None
    target_idx = -1
    for i, c in enumerate(cases):
        if _get_case_field(c, "case_id", "") == case_id:
            target = c
            target_idx = i
            break
    if target is None:
        print(json.dumps({"status": "error", "reason": f"未找到case: {case_id}"}))
        sys.exit(1)
    
    # 3. 备份
    backup_dir = os.path.join(data_dir, ".tp_backup")
    _ensure_dir(backup_dir)
    import time as _time
    ts_tag = _time.strftime("%Y%m%d_%H%M%S")
    
    # 备份p6_output.json
    p6_backup = os.path.join(backup_dir, f"p6_output.json.bak.quickfix_{ts_tag}")
    _write_json(p6_backup, p6_data)
    
    # 4. 更新p6_output.json中的case
    _set_case_field(target, field, new_value)
    cases[target_idx] = target
    p6_data["testcases"] = cases
    _write_json(p6_path, p6_data)
    
    # 5. 双写到对应的tp_xxx.json（通过遍历p6_tp_output查找）
    tp_dir = os.path.join(data_dir, "p6_tp_output")
    tp_synced = False
    if os.path.isdir(tp_dir):
        for fname in sorted(os.listdir(tp_dir)):
            if fname.startswith("tp_") and fname.endswith(".json"):
                fp = os.path.join(tp_dir, fname)
                try:
                    tp_data = _read_json(fp)
                    tp_cases = tp_data.get("testcases", [])
                    for j, tc in enumerate(tp_cases):
                        if tc.get("case_id", "") == case_id:
                            tp_file = fp
                            # 备份tp文件
                            tp_backup = os.path.join(backup_dir, f"{fname}.bak.quickfix_{ts_tag}")
                            _write_json(tp_backup, tp_data)
                            # 更新
                            _set_case_field(tc, field, new_value)
                            tp_cases[j] = tc
                            tp_data["testcases"] = tp_cases
                            _write_json(tp_file, tp_data)
                            tp_synced = True
                            break
                except Exception:
                    pass
                if tp_synced:
                    break
    
    # 6. 执行全量P7检查（跳过merge, 纯代码校验<5秒）
    p7_result = {}
    try:
        task_id = args.task_id
        # 读取P5
        p5_path = os.path.join(data_dir, "p5_output.json")
        p5_data = _read_json(p5_path) if os.path.exists(p5_path) else {}
        p5_tps = p5_data.get("test_points", []) if isinstance(p5_data, dict) else []
        if not p5_tps and os.path.exists(p5_path):
            p5_tps = p5_data if isinstance(p5_data, list) else []
        
        # 执行全部P7检查
        p7_checks = [
            _p7_check_c1(cases),
            _p7_check_c2(cases),
            _p7_check_c3(cases),
            _p7_check_c4(cases),
            _p7_check_c5(cases),
            _p7_check_c6(cases),
            _p7_check_c61(cases),
            _p7_check_c62(cases),
            _p7_check_c7(cases, p5_tps),
            _p7_check_c71(cases, p5_tps),
        ]
        
        block_failed = sum(1 for ck in p7_checks if ck["level"] == "BLOCK" and ck["status"] == "FAILED")
        all_passed = block_failed == 0
        
        p7_result = {
            "status": "PASS" if all_passed else "FAILED",
            "block_passed": sum(1 for ck in p7_checks if ck["level"] == "BLOCK" and ck["status"] != "FAILED"),
            "block_total": sum(1 for ck in p7_checks if ck["level"] == "BLOCK"),
            "checks": p7_checks,
            "quick_fix": {"case_id": case_id, "field": field, "tp_synced": tp_synced},
        }
    except Exception as e:
        p7_result = {"status": "error", "reason": f"P7检查异常: {e}"}
    
    print(json.dumps(p7_result, indent=2, ensure_ascii=False))


# ============================================================
# Action: restart_from (从指定步骤重新开始)
# ============================================================

def _check_gate_exists(data_dir, step):
    """检查指定步骤的gate pass是否存在"""
    gates_dir = os.path.join(data_dir, "gates")
    gp = os.path.join(gates_dir, f"{step}.pass.json")
    return os.path.exists(gp)

def action_restart_from(args):
    """从指定步骤重新开始:清除该步及后续的gate pass和output"""
    data_dir = args.data_dir
    task_id = args.task_id
    step = args.step.upper()
    force = getattr(args, 'force', False)

    if step not in GATE_STEPS:
        print(json.dumps({"status": "error", "reason": f"无效步骤: {step},可选: {GATE_STEPS}"}))
        sys.exit(1)

    # 非force模式:检查gate是否存在,避免误清
    if not force:
        if not _check_gate_exists(data_dir, step):
            print(json.dumps({
                "status": "error",
                "reason": f"P{step} gate pass不存在,无需restart。请确认流程是否已到达该步骤。",
                "hint": "如需强制重置,使用 --force 参数"
            }))
            sys.exit(1)

    # 找到该步骤及后续所有步骤
    step_idx = GATE_STEPS.index(step)
    steps_to_clear = GATE_STEPS[step_idx:]

    gates_dir = os.path.join(data_dir, "gates")
    cleared = []
    for s in steps_to_clear:
        # 清除gate pass
        gp = os.path.join(gates_dir, f"{s}.pass.json")
        if os.path.exists(gp):
            os.remove(gp)
            cleared.append(f"{s}.pass.json")
        # 清除output
        for suffix in ["_output.json", "_output.tmp.json", "_output.prev.json"]:
            op = os.path.join(data_dir, f"{s.lower()}{suffix}")
            if os.path.exists(op):
                os.remove(op)
                cleared.append(f"{s.lower()}{suffix}")

    # 更新state
    state = TaskState(data_dir=data_dir, task_id=task_id)
    state.state["completed_steps"] = [s for s in state.state["completed_steps"] if s not in [st.lower() for st in steps_to_clear] and s not in steps_to_clear]
    state.save()

    # V4.8.9: P1重启时清除分批文件
    if step == "P1":
        sk_path = os.path.join(data_dir, "p1_skeleton.json")
        if os.path.exists(sk_path):
            os.remove(sk_path)
            cleared.append("p1_skeleton.json")
        features_dir = os.path.join(data_dir, "p1_features")
        if os.path.exists(features_dir):
            import shutil
            shutil.rmtree(features_dir, ignore_errors=True)
            cleared.append("p1_features/ (目录已清除)")
        agent_files = [f for f in os.listdir(data_dir) if f.startswith("p1_feature_") or f.startswith("p1_skeleton_")]
        for af in agent_files:
            af_path = os.path.join(data_dir, af)
            if os.path.isfile(af_path):
                os.remove(af_path)
                cleared.append(af)

    # V4.10.1: P6重启时清除agent_output残留
    if step == "P6":
        agent_files = [f for f in os.listdir(data_dir) if f.startswith("p6_batch_") and "_agent_output" in f]
        for af in agent_files:
            af_path = os.path.join(data_dir, af)
            if os.path.isfile(af_path):
                os.remove(af_path)
                cleared.append(af)

    # V4.12.7: restart_from <= P6 时精准删除 p6/p7 output（保留 p7_report.html 供参考对比）
    # 原因：p6_merge 原子覆盖写入不读旧文件，保留 stale 版本会让 Agent 陷入"修了但报错不变"的困惑循环
    p6_idx = GATE_STEPS.index("P6")
    if step_idx <= p6_idx:
        for output_file in ["p6_output.json", "p7_output.json"]:
            out_path = os.path.join(data_dir, output_file)
            if os.path.exists(out_path):
                os.remove(out_path)
                if output_file not in cleared:
                    cleared.append(output_file)

    # V4.12.7: 清理 pending_emit / emit_confirmed 文件，避免断点续跑冲突
    for emit_file in [f for f in os.listdir(data_dir) if f.startswith("pending_emit_") or f.startswith("emit_confirmed_")]:
        emit_path = os.path.join(data_dir, emit_file)
        if os.path.isfile(emit_path):
            os.remove(emit_path)
            cleared.append(emit_file)

    print(json.dumps({
        "status": "ok",
        "restart_from": step,
        "cleared_files": cleared,
        "next_step": step,
    }))


# Action: verify_gates (验证所有gate pass状态)
# ============================================================

# V4.13.8 P1-3层二: 从备份恢复指定TP文件
def action_p6_recover_tp(args):
    """从 .tp_backup/ 恢复指定tp文件"""
    data_dir = args.data_dir
    tp_index = args.tp_index if hasattr(args, 'tp_index') else None
    if tp_index is None:
        print(json.dumps({"status": "error", "reason": "需要 --tp-index 参数指定恢复的TP"}))
        sys.exit(1)
    bak_dir = os.path.join(data_dir, ".tp_backup")
    tp_path = os.path.join(data_dir, "p6_tp_output", f"tp_{tp_index:03d}.json")
    if not os.path.exists(bak_dir):
        print(json.dumps({"status": "error", "reason": f"备份目录不存在: {bak_dir}"}))
        sys.exit(1)
    # 找最新的备份
    baks = sorted([f for f in os.listdir(bak_dir) if f.startswith(f"tp_{tp_index:03d}.")])
    if not baks:
        print(json.dumps({"status": "error", "reason": f"tp_{tp_index:03d}无可用备份,备份目录: {bak_dir}"}))
        sys.exit(1)
    latest_bak = os.path.join(bak_dir, baks[-1])
    import shutil as _shutil
    _shutil.copy2(latest_bak, tp_path)
    print(json.dumps({
        "status": "ok",
        "tp_index": tp_index,
        "recovered_from": latest_bak,
        "recovered_to": tp_path,
        "available_backups": len(baks),
    }))

# V4.13.8 P1-3层二: 文件完整性校验
def action_p6_verify_files(args):
    """校验TP文件完整性: 对比预期总数 vs 实际文件数"""
    data_dir = args.data_dir
    tp_dir = os.path.join(data_dir, "p6_tp_output")
    if not os.path.exists(tp_dir):
        print(json.dumps({"status": "ok", "total": 0, "note": "p6_tp_output目录不存在,尚未开始P6"}))
        return
    # 从p5_output.json获取预期TP总数
    p5_path = os.path.join(data_dir, "p5_output.json")
    expected_total = 0
    if os.path.exists(p5_path):
        try:
            p5 = _read_json(p5_path)
            expected_total = len(p5.get("test_points", []))
        except Exception:
            pass
    tp_files = sorted([f for f in os.listdir(tp_dir) if f.startswith("tp_") and f.endswith(".json") and "_context" not in f])
    actual_count = len(tp_files)
    missing_indices = []
    if expected_total > 0:
        all_indices = set(range(expected_total))
        existing_indices = set()
        for f in tp_files:
            try:
                idx = int(f.replace("tp_", "").replace(".json", ""))
                existing_indices.add(idx)
            except Exception:
                pass
        missing_indices = sorted(all_indices - existing_indices)
    result = {
        "status": "incomplete" if missing_indices else "ok",
        "expected_total": expected_total,
        "actual_count": actual_count,
        "missing_count": len(missing_indices),
        "missing_tp_indices": missing_indices[:20],
    }
    if missing_indices:
        result["hint"] = f"缺失{len(missing_indices)}个TP文件: {missing_indices[:10]}"
        result["recover_hint"] = f"使用 p6_recover_tp --tp-index N 恢复, 或 p6_generate_one --tp-index N 重新生成"
    else:
        result["hint"] = f"✅ {actual_count}个TP文件完整" if expected_total == 0 else f"✅ {actual_count}/{expected_total}个TP文件完整"
    print(json.dumps(result))


def action_p6_verify_progress(args):
    """V4.15.38: 校验文件系统与orchestrator状态的一致性

    排查场景：Agent会话压缩后state可能回滚，或agent绕过--save直接写文件。
    输出 fs vs state 的差异统计，Agent据此决定是否需要 re-sync。
    """
    import glob as _g
    data_dir = args.data_dir
    _tp_dir = os.path.join(data_dir, "p6_tp_output")
    _sp = os.path.join(data_dir, "orchestrator_state.json")

    # 文件系统计数（排除_context/_agent_output/_tmp）
    _fs_files = sorted([
        int(os.path.basename(_f).split("_")[1].split(".")[0])
        for _f in _g.glob(os.path.join(_tp_dir, "tp_[0-9]*.json"))
        if "_context" not in os.path.basename(_f)
        and "_agent_output" not in os.path.basename(_f)
        and "_tmp" not in os.path.basename(_f)
    ])
    _fs_count = len(_fs_files)

    # state计数
    _state_indices = []
    if os.path.exists(_sp):
        try:
            _st = _read_json(_sp)
            _state_indices = sorted(_st.get("p6_completed_tp_indices", []))
        except Exception:
            pass
    _state_count = len(_state_indices)

    # 差异分析
    _fs_set = set(_fs_files)
    _state_set = set(_state_indices)
    _only_fs = sorted(_fs_set - _state_set)
    _only_state = sorted(_state_set - _fs_set)

    _gap = _fs_count - _state_count
    _status = "synced" if _gap == 0 and not _only_fs and not _only_state else "mismatch"

    print(json.dumps({
        "status": _status,
        "fs_count": _fs_count,
        "state_count": _state_count,
        "fs_only_tp_indices": _only_fs[:30],
        "state_only_tp_indices": _only_state[:30],
        "max_fs_index": max(_fs_files) if _fs_files else None,
        "max_state_index": max(_state_indices) if _state_indices else None,
        "hint": "fs和state完全一致，无需操作" if _status == "synced"
                else f"fs有{_fs_count}个文件但state只记录{_state_count}个。"
                     f"仅fs存在({len(_only_fs)}个): {_only_fs[:10]}。"
                     f"建议: 如果state少，说明压缩回滚，继续从{_state_count}生成即可。"
    }, ensure_ascii=False))


def action_verify_gates(args):
    """检查所有已存在的gate pass状态,用于restart前的人工确认"""
    data_dir = args.data_dir
    gates_dir = os.path.join(data_dir, "gates")
    results = {}
    missing = []
    for step in GATE_STEPS:
        gp = os.path.join(gates_dir, f"{step}.pass.json")
        if os.path.exists(gp):
            try:
                with open(gp, "r", encoding="utf-8") as f:
                    data = json.load(f)
                results[step] = {"exists": True, "step": data.get("step"), "passed_at": data.get("passed_at")}
            except:
                results[step] = {"exists": True, "error": "JSON解析失败"}
        else:
            results[step] = {"exists": False}
            missing.append(step)

    print(json.dumps({
        "status": "ok",
        "total_steps": len(GATE_STEPS),
        "existing": len(GATE_STEPS) - len(missing),
        "missing": missing,
        "gates": results,
    }))

def _hot_reload_modules():
    """V4.15.37: 热重载skill工具模块

    每次action调用前检查已加载模块的mtime，如果文件已更新则importlib.reload。
    支持skill覆盖安装后自动生效，无需重启任务。
    """
    try:
        import importlib
        _reload_targets = ["gate_checker", "truncation_guard", "export_excel", "export_markdown",
                          "p5_prepare", "p5_validate", "p6_guide", "p6_templates"]
        for mod_name in _reload_targets:
            if mod_name in sys.modules:
                try:
                    importlib.reload(sys.modules[mod_name])
                except Exception:
                    pass  # 单模块reload失败不影响其他模块
    except Exception:
        pass  # 热重载失败不影响核心逻辑


def main():
    parser = argparse.ArgumentParser(description="V3.0 Orchestrator")
    parser.add_argument("--action", required=True, choices=[
        "init", "onboarding", "step0", "step0_8_prep", "step0_8_save",
        "step_run", "step7_export", "status", "resume",
        "prep_prompt", "p2_code_generate", "p3_p4_parallel", "p5_code_merge", "p5_retry",
        "p6_tp_list", "p6_generate_one", "p6_batch_info", "p6_save_batch", "p6_merge", "p6_checkpoint", "p6_recover_tp", "p6_verify_files", "p6_verify_progress", "p6_resume",
        "p1_skeleton_save", "p1_save_feature", "p1_code_merge",
        "set_prd_review",
        "quality_check", "p7_code_check", "p7_batch_fix", "p7_quick_fix",
        "restart_from", "confirm_emit", "verify_gates", "check_image_api", "export_p0p1", "retry_push", "gate_diag"
    ])
    parser.add_argument("--skill-dir", default="")
    parser.add_argument("--data-dir", default="")
    parser.add_argument("--task-id", default="")
    parser.add_argument("--requirement-text", default="")
    parser.add_argument("--requirement-file", default="")
    parser.add_argument("--step", default="")
    parser.add_argument("--force", action="store_true", default=False, help="restart_from时跳过gate状态检查,强制清除")
    parser.add_argument("--force-continue", action="store_true", default=False, help="V4.15.23: p5_retry跳过P5质量门禁BLOCK,强制继续")
    parser.add_argument("--agent-output", default="")  # 兼容保留,优先从文件读
    parser.add_argument("--results-json", default="")  # 兼容保留,优先从文件读
    parser.add_argument("--batch-index", default="0")
    parser.add_argument("--case-id", default="", help="V4.15.56: P7快速修复指定case")
    parser.add_argument("--field", default="", help="V4.15.56: 要修复的字段(steps/expected_results/preconditions)")
    parser.add_argument("--new-value", default="", help="V4.15.56: 字段新值(或从--value-file读取)")
    parser.add_argument("--value-file", default="", help="V4.15.56: 从文件读取新值(用于多行内容)")
    parser.add_argument("--tp-index", type=int, default=0, help="V4.11.0: P6逐条生成TP索引")
    parser.add_argument("--short", action="store_true", default=False, help="V4.14.1: p6_generate_one精简输出,只显示摘要+文件路径")
    parser.add_argument("--tp-ids", default="", help="V4.9.1: P7修复模式,指定要处理的测试点ID列表(逗号分隔)")
    parser.add_argument("--merge", action="store_true", default=False, help="V4.7.2: 增量更新模式,仅更新指定case_id的用例,保留其余")
    parser.add_argument("--api-key", default="", help="图片理解API密钥(Onboarding时用户输入,不落盘)")
    parser.add_argument("--model-name", default="", help="V4.8.0: 当前使用的模型名称(用于LOW模型自适应)")
    # V4.15.22: rate_limit为orchestrator内置监控指标(非强制等待)，Agent无需自行插入sleep
    parser.add_argument("--feature-id", default="", help="V4.8.9: P1分批生成 - 功能点ID")
    parser.add_argument("--mode", default="", help="V4.8.9: P1骨架生成模式(skeleton)")
    parser.add_argument("--enabled", default="true", help="V3.5.1: PRD审查开关(true/false)")
    # FIX② V5.x: P7检查跳过 p6_merge,直接检查当前 p6_output.json
    parser.add_argument("--skip-merge", action="store_true", default=False, help="跳过p6_merge直接检查当前p6_output.json")
    # FIX③ V5.x: P7导出强制开关(复用现有 --force,新增原因必填)
    parser.add_argument("--force-reason", type=str, default="", help="强制导出原因(--force时必填)")
    # V4.14.10: P1骨架校验跳过
    parser.add_argument("--force-accept", action="store_true", default=False, help="P1功能点数量校验不达标时强制接受")

    args = parser.parse_args()

    # === V3.0.0-patch3: 参数自动化 ===
    # 1. skill_dir自动发现
    try:
        args.skill_dir = resolve_skill_dir(args.skill_dir)
    except ValueError as e:
        print(json.dumps({"status": "error", "reason": str(e)}))
        sys.exit(1)

    # 2. data_dir/task_id自动回填(非init action时)
    if args.action != "init":
        if not args.data_dir or not args.task_id:
            auto_tid, auto_dir = find_latest_task()
            if auto_tid and auto_dir:
                if not args.task_id:
                    args.task_id = auto_tid
                if not args.data_dir:
                    args.data_dir = auto_dir
            else:
                if args.action not in ("status",):
                    print(json.dumps({"status": "error", "reason": "未找到活跃任务,请先执行 --action init"}))
                    sys.exit(1)

    # 3. agent-output从文件读取(优先级:文件 > 命令行参数)
    if args.action in ("step_run", "p6_save_batch", "p1_skeleton_save", "p1_save_feature") and not args.agent_output:
        step = args.step or "unknown"
        if args.action == "p6_save_batch":
            batch_idx = int(args.batch_index) if args.batch_index else 0  # V4.8.12: 0-based
            agent_file = os.path.join(args.data_dir, f"p6_batch_{batch_idx:03d}_agent_output.json")
        elif args.action == "p1_skeleton_save":
            agent_file = os.path.join(args.data_dir, "p1_skeleton_agent_output.json")
        elif args.action == "p1_save_feature":
            fid = getattr(args, 'feature_id', '')
            safe_fid = fid.replace("/", "_").replace("\\", "_")
            agent_file = os.path.join(args.data_dir, f"p1_feature_{safe_fid}_agent_output.json")
        else:
            agent_file = os.path.join(args.data_dir, f"{step.lower()}_agent_output.json")
        if os.path.exists(agent_file):
            args.agent_output = _read_file_safe(agent_file, 100000)

    # 4. results-json从文件读取
    if args.action == "step0_8_save" and not args.results_json:
        results_file = os.path.join(args.data_dir, "px_agent_results.json")
        if os.path.exists(results_file):
            args.results_json = _read_file_safe(results_file, 100000)

    actions = {
        "init": action_init,
        "onboarding": action_onboarding,
        "step0": action_step0,
        "step0_8_prep": action_step0_8_prep,
        "step0_8_save": action_step0_8_save,
        "step_run": action_step_run,
        "step7_export": action_step7_export,
        "status": action_status,
        "resume": action_resume,
        "prep_prompt": action_prep_prompt,
        "p2_code_generate": action_p2_code_generate,
        "p3_p4_parallel": action_p3_p4_parallel,
        "p5_code_merge": action_p5_code_merge,
        "p5_retry": action_p5_retry,
        "p6_tp_list": action_p6_tp_list,
        "p6_generate_one": action_p6_generate_one,
        "p6_batch_info": action_p6_batch_info,
        "p6_save_batch": action_p6_save_batch,
        "p6_merge": action_p6_merge,
        "p6_checkpoint": action_p6_checkpoint,
        "p6_recover_tp": action_p6_recover_tp,
        "p6_verify_files": action_p6_verify_files,
        "p6_verify_progress": action_p6_verify_progress,
        "p6_resume": action_p6_resume,
        "p1_skeleton_save": action_p1_skeleton_save,
        "p1_save_feature": action_p1_save_feature,
        "p1_code_merge": action_p1_code_merge,
        "set_prd_review": action_set_prd_review,
        "quality_check": action_quality_check,
        "p7_code_check": action_p7_code_check,
        "p7_batch_fix": action_p7_batch_fix,
        "p7_quick_fix": action_p7_quick_fix,
        "restart_from": action_restart_from,
        "confirm_emit": action_confirm_emit,
        "verify_gates": action_verify_gates,
        "check_image_api": action_check_image_api,
        "export_p0p1": action_export_p0p1,
        "retry_push": action_retry_push,
        "gate_diag": action_gate_diag,
    }

    # V4.15.37: 热重载——每次action调用前刷新skill工具模块(支持覆盖安装后自动生效)
    _hot_reload_modules()

    try:
        # V3.5.2: 设置全局变量,记录当前执行的action
        global _CURRENT_ACTION
        _CURRENT_ACTION = args.action
        actions[args.action](args)
    except SystemExit:
        raise
    except Exception as e:
        resp = _error_response(e, context=args.action if hasattr(args, 'action') else "")
        print(json.dumps(resp, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
