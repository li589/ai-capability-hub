# -*- coding: utf-8 -*-
"""
蓝图报告素材提取脚本
- 输入：调研报告 (.doc/.docx)、实施报告 (.doc/.docx)、售前方案 (.pptx)
- 输出：
  - extracted/调研报告.txt / extracted/实施报告.txt / extracted/售前方案.json
  - extracted/chapters.json（按 23 页章节结构预填素材映射）
依赖：smart-delivery-survey/scripts/{extract_pptx,extract_docx,extract_doc}.py
"""
import os
import sys
import json
import argparse
import subprocess

EXTRACT_PPTX = r"{{HOME}}/.workbuddy/skills/smart-delivery-survey/scripts/extract_pptx.py"
EXTRACT_DOCX = r"{{HOME}}/.workbuddy/skills/smart-delivery-survey/scripts/extract_docx.py"
EXTRACT_DOC = r"{{HOME}}/.workbuddy/skills/smart-delivery-survey/scripts/extract_doc.py"
PYTHON = r"{{HOME}}/.workbuddy/binaries/python/envs/default/Scripts/python.exe"

# 23 页章节标题（与 智能交付助手-蓝图助手 配套）
CHAPTER_TITLES = [
    "封面", "报告大纲",
    "1.1 企业概况", "1.2 项目进度·实施主计划",
    "2.1 项目范围", "2.1 实施目标·8 大透明", "2.1 验收条件",
    "2.2 主流程总览·9 节点", "2.2 跨系统集成规划",
    "2.2 工单→派工→报工映射矩阵", "2.2 一期数采设备清单",
    "2.3 工艺路线 ①", "2.3 工艺路线 ②", "2.3 工艺路线 ③+④",
    "2.4 核心子流程 ① (派工/报工/质量/设备)", "2.4 核心子流程 ② (模具/上料/装箱/委外)",
    "2.5 报工点位规划", "2.6 关键性差异说明",
    "2.7 效益概述 As Is → To Be",
    "3.1 风险预警", "3.2 下阶段工作", "签字页", "Thank You",
]

# 章节→素材来源映射（key 关键词匹配）
CHAPTER_KEYWORDS = {
    3: ["企业概况", "主要产品", "主营", "公司概况", "信息化现状"],
    4: ["实施主计划", "项目进度", "里程碑", "I am here", "规划与启航", "蓝图与设计", "上线与赋能"],
    5: ["项目范围", "物理范围", "工艺路线", "工单类型", "暂缓", "软件范围"],
    6: ["8 大透明", "实施目标", "派工透明", "进度透明", "设备透明", "质量透明"],
    7: ["验收", "看板", "无纸化", "数采指标", "采集点率"],
    8: ["主流程", "9 节点", "工单下发", "产前准备", "过程检验", "入库", "结案"],
    9: ["集成", "ERP↔MES", "ESB", "IIoT", "飞书", "接口清单"],
    10: ["映射矩阵", "工单类型", "派工方式", "报工方式"],
    11: ["数采设备", "设备清单", "微孔加压", "退火烧结", "厚度测量"],
    12: ["工艺1", "微孔加压", "退火", "裁切", "烧结"],
    13: ["工艺2", "烤箱", "粘料板", "荷载测试", "切片", "去油", "清洗烘干"],
    14: ["工艺3", "工艺4", "委外", "激光切割"],
    15: ["派工", "报工", "首检", "末检", "设备点检", "设备保养", "稼动"],
    16: ["模具", "上料", "装箱", "委外"],
    17: ["点位", "工位机", "PDA", "工控机", "平板", "扫码枪"],
    18: ["关键差异", "个案", "二开", "待确认", "断料", "粘胶", "10 小时"],
    19: ["效益", "As Is", "To Be", "改善", "数据采集点率"],
    20: ["风险", "处置", "预警"],
    21: ["下阶段", "里程碑", "实施计划", "鼎华团队", "动量守恒团队"],
}


def run_extract(src_path: str, out_path: str):
    """调用 smart-delivery-survey 的提取脚本"""
    if not os.path.exists(src_path):
        print(f"[WARN] 输入文件不存在: {src_path}")
        return False
    ext = os.path.splitext(src_path)[1].lower()
    if ext == ".pptx":
        script = EXTRACT_PPTX
        args = [src_path, out_path]
    elif ext == ".docx":
        script = EXTRACT_DOCX
        args = [src_path, out_path]
    elif ext == ".doc":
        script = EXTRACT_DOC
        args = [src_path, out_path]
    else:
        print(f"[WARN] 不支持的文件格式: {src_path}")
        return False
    try:
        subprocess.run([PYTHON, script] + args, check=True, capture_output=True, encoding="utf-8", errors="replace")
        print(f"[OK] 提取: {os.path.basename(src_path)} → {os.path.basename(out_path)}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[FAIL] 提取失败 {src_path}: {e.stderr[:200]}")
        return False


def load_text(path: str) -> str:
    if not os.path.exists(path):
        return ""
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def chunk_paragraphs(text: str) -> list:
    """按段落切分文本"""
    return [p.strip() for p in text.split("\n") if p.strip()]


def map_chapters(extracted_text: str, label: str) -> dict:
    """按关键词把文本片段映射到章节"""
    paragraphs = chunk_paragraphs(extracted_text)
    chapter_map = {i: {"label": label, "snippets": []} for i in range(1, 24)}
    chapter_map[0] = {"label": label, "snippets": paragraphs[:3]}  # 封面
    chapter_map[1] = {"label": label, "snippets": []}  # 目录
    for para in paragraphs:
        for ch, keywords in CHAPTER_KEYWORDS.items():
            if any(kw in para for kw in keywords):
                if len(chapter_map[ch]["snippets"]) < 20:
                    chapter_map[ch]["snippets"].append(para)
                break
    # 剩余段落归到"实施主计划"（page 4）作兜底
    for ch in chapter_map:
        if not chapter_map[ch]["snippets"] and ch not in (0, 1, 22, 23):
            continue
    return chapter_map


def main():
    parser = argparse.ArgumentParser(description="蓝图报告素材提取")
    parser.add_argument("--project-dir", required=True, help="项目目录")
    parser.add_argument("--report", help="调研报告 .doc/.docx")
    parser.add_argument("--implement", help="实施报告 .doc/.docx")
    parser.add_argument("--pre-sales", help="售前方案 .pptx")
    parser.add_argument("--out", default="extracted", help="输出目录名（相对 project-dir）")
    args = parser.parse_args()

    out_dir = os.path.join(args.project_dir, args.out)
    os.makedirs(out_dir, exist_ok=True)

    print(f"=== 蓝图报告素材提取 ===")
    print(f"项目目录: {args.project_dir}")
    print(f"输出目录: {out_dir}\n")

    sources = []
    if args.report:
        src = os.path.join(out_dir, "调研报告.txt")
        run_extract(args.report, src)
        sources.append(("调研报告", src))
    if args.implement:
        src = os.path.join(out_dir, "实施报告.txt")
        run_extract(args.implement, src)
        sources.append(("实施报告", src))
    if args.pre_sales:
        # pptx 输出是 JSON，文件名改 .json
        base = "售前方案"
        src = os.path.join(out_dir, base + ".json")
        run_extract(args.pre_sales, src)
        sources.append(("售前方案", src))

    # 合并章节映射
    chapters = {i: {"title": CHAPTER_TITLES[i-1] if 0 < i <= 23 else "", "sources": {}} for i in range(24)}
    for label, src in sources:
        text = load_text(src) if src.endswith(".txt") else ""
        if src.endswith(".json"):
            # pptx 提取的 JSON：[{slide, texts}, ...]
            try:
                with open(src, encoding="utf-8") as f:
                    pptx_data = json.load(f)
                text = "\n".join(" | ".join(d.get("texts", [])) for d in pptx_data)
            except Exception:
                text = ""
        chapter_map = map_chapters(text, label)
        for ch, info in chapter_map.items():
            chapters[ch]["sources"][label] = info["snippets"][:10]  # 每章最多 10 段

    out_json = os.path.join(out_dir, "chapters.json")
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(chapters, f, ensure_ascii=False, indent=1)
    print(f"\n=== 章节素材映射已写入: {out_json} ===")

    # 摘要
    print("\n各章节素材片段数:")
    for i in range(1, 24):
        total = sum(len(v) for v in chapters[i]["sources"].values())
        title = CHAPTER_TITLES[i-1]
        print(f"  {i:2d}. {title}: {total} 段")
    return 0


if __name__ == "__main__":
    sys.exit(main())