# -*- coding: utf-8 -*-
from __future__ import annotations
"""
金融分析写作引擎 v4.0
模板驱动 + 数据注入 + 自然语言衔接 + ChartBuilder 图表生成。

核心能力：
- ReportTemplate 系统：6套预制模板，章节结构可自定义
- FinancialWriter：模板渲染 + 数据注入 + 智能段落生成
- ChartBuilder：matplotlib 图表生成（趋势图/柱状图/饼图/雷达图）
- 内置中文字体自动检测与 fallback
- 输出：Markdown（含图表图片引用）+ 独立图表 PNG 文件

推荐安装: pip install matplotlib
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime
from dataclasses import dataclass, field

# matplotlib 可选
MPL_AVAILABLE = False
try:
    import matplotlib
    matplotlib.use('Agg')  # 非交互式后端
    import matplotlib.pyplot as plt
    import matplotlib.font_manager as fm
    from matplotlib import rcParams
    MPL_AVAILABLE = True
except ImportError:
    pass

try:
    from report_templates import (
        TEMPLATES, ReportTemplate, get_template,
        list_templates, render_template, get_template_outline
    )
    HAS_TEMPLATES = True
except ImportError:
    HAS_TEMPLATES = False
    TEMPLATES = {}

try:
    from content_compressor import ContentCompressor, CompressConfig, compress_content
    HAS_COMPRESSOR = True
except ImportError:
    HAS_COMPRESSOR = False

SKILL_DATA_DIR = Path(__file__).parent.parent / "data"
CHARTS_DIR = SKILL_DATA_DIR / "charts"
REPORTS_DIR = SKILL_DATA_DIR / "reports"

SKILL_DATA_DIR.mkdir(parents=True, exist_ok=True)
CHARTS_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


# ==================== 中文字体配置 ====================

def _detect_chinese_font() -> Optional[str]:
    """自动检测系统中文字体。
    v4.3.2: 增加 Windows 字体目录扫描和 matplotlib 字体缓存刷新。"""
    if not MPL_AVAILABLE:
        return None

    candidates = [
        "SimHei", "Microsoft YaHei", "WenQuanYi Micro Hei",
        "WenQuanYi Zen Hei", "Noto Sans CJK SC", "PingFang SC",
        "STHeiti", "Heiti SC", "STSong", "SimSun",
        "AR PL UMing CN", "AR PL UKai CN",
        "Source Han Sans SC", "Source Han Serif SC",
    ]

    available_fonts = {f.name for f in fm.fontManager.ttflist}

    for font_name in candidates:
        if font_name in available_fonts:
            return font_name

    # 尝试模糊匹配
    for font_name in candidates:
        for available in available_fonts:
            if font_name.lower().replace(' ', '') in available.lower().replace(' ', ''):
                return available

    # v4.3.2: 扫描 Windows 字体目录
    import platform
    if platform.system() == "Windows":
        windows_font_dirs = [
            Path(os.environ.get("WINDIR", "C:\\Windows")) / "Fonts",
        ]
        for font_dir in windows_font_dirs:
            if not font_dir.is_dir():
                continue
            for font_name in candidates:
                ttf_path = font_dir / f"{font_name}.ttf"
                ttc_path = font_dir / f"{font_name}.ttc"
                for fpath in (ttf_path, ttc_path):
                    if fpath.is_file():
                        try:
                            fm.fontManager.addfont(str(fpath))
                            # 验证添加成功
                            props = fm.FontProperties(fname=str(fpath))
                            return props.get_name()
                        except Exception:
                            continue

    return None

_CHINESE_FONT = None
_FONT_DETECTED = False


def _get_chinese_font(force_redetect: bool = False) -> str:
    """获取中文字体（带缓存）。
    v4.3.2: 支持 force_redetect 在运行时重新检测。"""
    global _CHINESE_FONT, _FONT_DETECTED
    if _CHINESE_FONT is None or force_redetect:
        _CHINESE_FONT = _detect_chinese_font() or "sans-serif"
        _FONT_DETECTED = True
    return _CHINESE_FONT


def _setup_matplotlib_chinese(force: bool = False):
    """配置 matplotlib 中文支持。
    v4.3.2: 支持按需重新配置。"""
    if not MPL_AVAILABLE:
        return

    font = _get_chinese_font(force_redetect=force)
    if font != "sans-serif":
        rcParams['font.sans-serif'] = [font, 'DejaVu Sans', 'sans-serif']
    rcParams['axes.unicode_minus'] = False


if MPL_AVAILABLE:
    _setup_matplotlib_chinese()


# ==================== ChartBuilder ====================

@dataclass
class ChartConfig:
    """图表配置"""
    title: str = ""
    xlabel: str = ""
    ylabel: str = ""
    figsize: Tuple[int, int] = (10, 6)
    dpi: int = 100
    save_format: str = "png"
    color_palette: str = "default"  # default / finance / cool / warm
    show_values: bool = True
    grid: bool = True


COLOR_PALETTES = {
    "default": ["#2E86AB", "#A23B72", "#F18F01", "#C73E1D", "#3B1F2B",
                "#33658A", "#86BBD8", "#B9CDDA", "#8D99AE", "#2B2D42"],
    "finance": ["#C0392B", "#27AE60", "#2980B9", "#F39C12", "#8E44AD",
                "#1ABC9C", "#E74C3C", "#2ECC71", "#3498DB", "#9B59B6"],
    "cool": ["#264653", "#2A9D8F", "#E9C46A", "#F4A261", "#E76F51",
             "#457B9D", "#1D3557", "#A8DADC", "#F1FAEE", "#E63946"],
    "warm": ["#FF6B6B", "#FFE66D", "#4ECDC4", "#45B7D1", "#96CEB4",
             "#FFEAA7", "#DDA0DD", "#98D8C8", "#F7DC6F", "#BB8FCE"],
}


class ChartBuilder:
    """基于 matplotlib 的图表生成器。"""

    def __init__(self, output_dir: str = ""):
        self.output_dir = Path(output_dir) if output_dir else CHARTS_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._chart_count = 0
        # v4.3.2: 延迟检测字体（可能 matplotlib 在 import 后才安装）
        if MPL_AVAILABLE:
            _setup_matplotlib_chinese(force=True)

    def line_chart(self, data: Dict[str, List[float]], labels: List[str],
                   config: Optional[ChartConfig] = None) -> str:
        """
        折线图（趋势图）。

        Args:
            data: {系列名: [值列表]}
            labels: X轴标签
            config: 图表配置

        返回: 图片文件路径
        """
        if not MPL_AVAILABLE:
            return self._ascii_fallback("折线图", data)

        config = config or ChartConfig(title="趋势图")
        palette = COLOR_PALETTES.get(config.color_palette, COLOR_PALETTES["default"])

        fig, ax = plt.subplots(figsize=config.figsize, dpi=config.dpi)

        x = range(len(labels))
        for i, (name, values) in enumerate(data.items()):
            color = palette[i % len(palette)]
            ax.plot(x, values, marker='o', linewidth=2, label=name, color=color,
                   markersize=6)
            if config.show_values:
                for j, v in enumerate(values):
                    ax.annotate(f'{v:.1f}', (j, v), textcoords="offset points",
                               xytext=(0, 10), ha='center', fontsize=8)

        ax.set_title(config.title, fontsize=14, fontweight='bold')
        ax.set_xlabel(config.xlabel, fontsize=11)
        ax.set_ylabel(config.ylabel, fontsize=11)
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=30, ha='right', fontsize=9)
        ax.legend(loc='best', fontsize=9)
        if config.grid:
            ax.grid(True, alpha=0.3)

        plt.tight_layout()
        path = self._save_figure(fig, config.title)
        plt.close(fig)
        return path

    def bar_chart(self, data: Dict[str, float],
                  config: Optional[ChartConfig] = None) -> str:
        """
        柱状图（对比图）。

        Args:
            data: {标签: 值}
            config: 图表配置

        返回: 图片文件路径
        """
        if not MPL_AVAILABLE:
            return self._ascii_fallback("柱状图", data)

        config = config or ChartConfig(title="对比分析")
        palette = COLOR_PALETTES.get(config.color_palette, COLOR_PALETTES["default"])

        fig, ax = plt.subplots(figsize=config.figsize, dpi=config.dpi)

        labels = list(data.keys())
        values = list(data.values())
        colors = [palette[i % len(palette)] for i in range(len(labels))]
        bars = ax.bar(range(len(labels)), values, color=colors, edgecolor='white')

        if config.show_values:
            for bar, val in zip(bars, values):
                ax.text(bar.get_x() + bar.get_width()/2., bar.get_height(),
                       f'{val:.1f}', ha='center', va='bottom', fontsize=9)

        ax.set_title(config.title, fontsize=14, fontweight='bold')
        ax.set_xlabel(config.xlabel, fontsize=11)
        ax.set_ylabel(config.ylabel, fontsize=11)
        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels, rotation=30, ha='right', fontsize=9)
        if config.grid:
            ax.grid(True, axis='y', alpha=0.3)

        plt.tight_layout()
        path = self._save_figure(fig, config.title)
        plt.close(fig)
        return path

    def pie_chart(self, data: Dict[str, float],
                  config: Optional[ChartConfig] = None) -> str:
        """
        饼图。

        Args:
            data: {标签: 值}
            config: 图表配置

        返回: 图片文件路径
        """
        if not MPL_AVAILABLE:
            return self._ascii_fallback("饼图", data)

        config = config or ChartConfig(title="占比分析")
        palette = COLOR_PALETTES.get(config.color_palette, COLOR_PALETTES["default"])

        fig, ax = plt.subplots(figsize=(8, 8), dpi=config.dpi)

        labels = list(data.keys())
        values = list(data.values())
        colors = [palette[i % len(palette)] for i in range(len(labels))]
        explode = [0.02] * len(labels)

        wedges, texts, autotexts = ax.pie(
            values, labels=None, autopct='%1.1f%%',
            colors=colors, explode=explode,
            shadow=False, startangle=90,
            textprops={'fontsize': 10}
        )

        ax.legend(wedges, labels, title="图例", loc="center left",
                 bbox_to_anchor=(1, 0, 0.5, 1), fontsize=9)
        ax.set_title(config.title, fontsize=14, fontweight='bold')

        plt.tight_layout()
        path = self._save_figure(fig, config.title)
        plt.close(fig)
        return path

    def radar_chart(self, data: Dict[str, List[float]], categories: List[str],
                    config: Optional[ChartConfig] = None) -> str:
        """
        雷达图。

        Args:
            data: {系列名: [值列表]}
            categories: 维度标签
            config: 图表配置

        返回: 图片文件路径
        """
        if not MPL_AVAILABLE:
            return self._ascii_fallback("雷达图",
                                       {k: dict(zip(categories, v)) for k, v in data.items()})

        config = config or ChartConfig(title="多维对比")
        palette = COLOR_PALETTES.get(config.color_palette, COLOR_PALETTES["default"])

        N = len(categories)
        angles = [n / float(N) * 2 * 3.1415926 for n in range(N)]
        angles += angles[:1]

        fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True), dpi=config.dpi)

        for i, (name, values) in enumerate(data.items()):
            values = list(values) + [values[0]]
            color = palette[i % len(palette)]
            ax.plot(angles, values, 'o-', linewidth=2, label=name, color=color)
            ax.fill(angles, values, alpha=0.1, color=color)

        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories, fontsize=10)
        ax.set_title(config.title, fontsize=14, fontweight='bold', pad=20)
        ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), fontsize=9)

        plt.tight_layout()
        path = self._save_figure(fig, config.title)
        plt.close(fig)
        return path

    def _save_figure(self, fig, title: str) -> str:
        """保存图表。"""
        self._chart_count += 1
        safe_title = re.sub(r'[^\w\u4e00-\u9fff]', '_', title)[:40]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        fname = f"chart_{self._chart_count:03d}_{safe_title}_{timestamp}.png"
        fpath = str(self.output_dir / fname)
        fig.savefig(fpath, bbox_inches='tight', dpi=fig.dpi)
        return fpath

    def _ascii_fallback(self, chart_type: str, data) -> str:
        """ASCII 图表 fallback。"""
        try:
            from visualization_reporter import ASCIIChart
            chart = ASCIIChart()
            if isinstance(data, dict) and all(isinstance(v, (int, float)) for v in data.values()):
                return f"```\n{chart.bar_chart(data, title=chart_type)}\n```"
        except ImportError:
            pass
        return f"[图表: {chart_type} — 数据: {data}]"


# ==================== FinancialWriter ====================

@dataclass
class WriterConfig:
    """写作配置"""
    template_id: str = "stock_research"
    output_format: str = "markdown"  # markdown / text / json
    include_charts: bool = True
    chart_format: str = "png"
    auto_compress: bool = False  # 是否先自动压缩输入
    focus_dimension: str = "全面"
    language: str = "zh"


class FinancialWriter:
    """
    金融分析写作引擎。
    接收结构化数据，按模板渲染为专业报告。
    """

    def __init__(self, chart_output_dir: str = ""):
        self.chart_builder = ChartBuilder(chart_output_dir)
        self._compressor = None
        if HAS_COMPRESSOR:
            self._compressor = ContentCompressor()

    def write(self, data: Dict[str, Any],
              config: Optional[WriterConfig] = None) -> Dict[str, Any]:
        """
        撰写报告。

        Args:
            data: 报告数据（需与模板章节对应）
            config: 写作配置

        返回: {
            markdown: str,
            charts: [str],  # 图表文件路径列表
            template_id: str,
            stats: {}
        }
        """
        if config is None:
            config = WriterConfig()

        # 自动选择模板
        template_id = config.template_id
        if template_id == "auto":
            template_id = self._auto_select_template(data)

        template = get_template(template_id) if HAS_TEMPLATES else None
        if not template:
            return {
                "markdown": f"# 未知模板: {template_id}",
                "charts": [],
                "template_id": template_id,
                "stats": {"error": "template_not_found"},
            }

        # 自动压缩（如果启用）
        if config.auto_compress and HAS_COMPRESSOR and self._compressor:
            data = self._auto_compress_data(data, config)

        # 生成图表（如果数据包含图表数据）
        charts = []
        if config.include_charts:
            charts = self._generate_charts(data, template)

        # 注入图表引用到数据中
        data_with_charts = self._inject_chart_refs(data, charts, template)

        # 渲染模板
        markdown = template.render(data_with_charts)
        markdown = self._post_process(markdown, charts)

        stats = {
            "template_id": template_id,
            "template_name": template.name,
            "section_count": len(template.sections),
            "chart_count": len(charts),
            "char_count": len(markdown),
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

        return {
            "markdown": markdown,
            "charts": charts,
            "template_id": template_id,
            "stats": stats,
        }

    def write_from_raw(self, raw_content: Any,
                       template_id: str = "stock_research",
                       title: str = "",
                       focus: str = "全面") -> Dict[str, Any]:
        """
        从原始内容自动撰写报告（一键式）。

        Args:
            raw_content: 原始文本/文件路径/解析结果
            template_id: 模板ID
            title: 报告标题
            focus: 关注维度

        返回: write() 返回的结果
        """
        config = WriterConfig(
            template_id=template_id,
            auto_compress=True,
            focus_dimension=focus,
        )

        data = {"raw_content": raw_content}
        if title:
            data["report_title"] = title

        if self._compressor and HAS_COMPRESSOR:
            try:
                compressed = compress_content(raw_content, focus=focus)
                data.update({
                    "report_title": title or compressed.title,
                    "摘要": compressed.summary,
                    "核心要点": compressed.key_points,
                    "财务数据": compressed.financial_highlights,
                    "风险提示": compressed.risk_summary,
                })

                # 映射到模板章节
                data_map = self._map_to_template(data, template_id)
                return self.write(data_map, config)
            except Exception as e:
                pass

        return self.write(data, config)

    def write_batch(self, items: List[Dict[str, Any]],
                    template_id: str = "stock_research",
                    config: Optional[WriterConfig] = None) -> List[Dict[str, Any]]:
        """批量撰写多份报告。"""
        return [self.write(item, config) for item in items]

    def save_report(self, result: Dict[str, Any],
                    output_path: str = "") -> str:
        """
        保存报告到文件。

        Args:
            result: write() 返回的结果
            output_path: 输出路径

        返回: 保存路径
        """
        if not output_path:
            template_id = result.get("template_id", "report")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = str(REPORTS_DIR / f"{template_id}_{timestamp}.md")

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(result["markdown"])

        return output_path

    # ---------- 内部方法 ----------

    def _auto_select_template(self, data: Dict[str, Any]) -> str:
        """根据数据内容自动选择模板。"""
        text = json.dumps(data, ensure_ascii=False).lower()

        if any(kw in text for kw in ["基金", "净值", "持仓", "基金经理", "fof"]):
            return "fund_evaluation"
        elif any(kw in text for kw in ["行业", "产业", "市场格局", "竞争"]):
            return "industry_analysis"
        elif any(kw in text for kw in ["公告", "披露", "临时报告"]):
            return "announcement_brief"
        elif any(kw in text for kw in ["机构", "股东", "注册资本", "监管"]):
            return "institution_survey"
        elif any(kw in text for kw in ["周报", "本周", "下周", "复盘"]):
            return "market_weekly"
        else:
            return "stock_research"

    def _auto_compress_data(self, data: Dict[str, Any],
                            config: WriterConfig) -> Dict[str, Any]:
        """自动压缩输入数据。"""
        if not self._compressor:
            return data

        raw = data.get("raw_content") or json.dumps(data, ensure_ascii=False)
        try:
            compressed = compress_content(raw, focus=config.focus_dimension)
            data.update({
                "摘要": compressed.summary,
                "核心要点": compressed.key_points,
                "财务数据": compressed.financial_highlights,
                "风险提示": compressed.risk_summary,
            })
        except Exception:
            pass
        return data

    def _generate_charts(self, data: Dict[str, Any],
                         template: ReportTemplate) -> List[str]:
        """根据数据生成图表。"""
        charts = []
        chart_data = data.get("charts") or data.get("图表数据") or {}

        if not chart_data:
            # 尝试从财务数据自动生成
            fin = data.get("财务数据") or data.get("core_financial") or {}
            if fin and isinstance(fin, dict):
                numeric_fin = {}
                for k, v in fin.items():
                    try:
                        numeric_fin[k] = float(v) if not isinstance(v, (int, float)) else v
                    except (ValueError, TypeError):
                        pass
                if numeric_fin:
                    # 柱状图
                    bar_path = self.chart_builder.bar_chart(
                        dict(list(numeric_fin.items())[:8]),
                        ChartConfig(title="核心财务指标", color_palette="finance")
                    )
                    if bar_path and not bar_path.startswith("[图表"):
                        charts.append(bar_path)

        # 按模板中的 chart 类型 section 生成
        if isinstance(chart_data, dict):
            for chart_key, chart_val in chart_data.items():
                if isinstance(chart_val, dict):
                    chart_type = chart_val.get("type", "bar")
                    chart_title = chart_val.get("title", chart_key)
                    chart_values = chart_val.get("data", {})

                    path = ""
                    if chart_type == "bar":
                        path = self.chart_builder.bar_chart(
                            chart_values,
                            ChartConfig(title=chart_title, color_palette="finance")
                        )
                    elif chart_type == "pie":
                        path = self.chart_builder.pie_chart(
                            chart_values,
                            ChartConfig(title=chart_title)
                        )
                    elif chart_type == "line":
                        path = self.chart_builder.line_chart(
                            chart_values, chart_val.get("labels", []),
                            ChartConfig(title=chart_title)
                        )

                    if path and not path.startswith("[图表"):
                        charts.append(path)

        return charts

    def _inject_chart_refs(self, data: Dict[str, Any], charts: List[str],
                           template: ReportTemplate) -> Dict[str, Any]:
        """将图表引用注入到数据中。"""
        result = dict(data)
        chart_idx = 0

        for sec in template.sections:
            if sec.get('type') == 'chart' and chart_idx < len(charts):
                chart_path = charts[chart_idx]
                fname = Path(chart_path).name
                result[sec['title']] = f"![{sec['title']}](charts/{fname})\n\n*图表: {sec['title']}*"
                chart_idx += 1

        return result

    def _map_to_template(self, compressed_data: Dict[str, Any],
                         template_id: str) -> Dict[str, Any]:
        """将压缩结果映射到模板字段。"""
        template = get_template(template_id) if HAS_TEMPLATES else None
        if not template:
            return compressed_data

        result = {}
        # 通用映射
        key_mapping = {
            "摘要": ["摘要", "summary", "overview"],
            "核心要点": ["关键要点", "核心要点", "key_points"],
            "财务数据": ["财务指标", "financial", "财务"],
            "风险提示": ["风险因素", "risk_factors", "风险"],
        }

        for sec in template.sections:
            sec_title = sec['title']
            # 尝试直接匹配
            if sec_title in compressed_data:
                result[sec_title] = compressed_data[sec_title]
                continue

            # 尝试映射
            for std_key, aliases in key_mapping.items():
                if sec_title in [std_key] + aliases:
                    if std_key in compressed_data:
                        result[sec_title] = compressed_data[std_key]
                    break

        return result

    def _post_process(self, markdown: str, charts: List[str]) -> str:
        """后处理：确保图表引用正确。"""
        # 添加生成信息
        footer = (f"\n\n---\n"
                  f"*报告由 cn-financial-scraper v4.0 自动生成*\n"
                  f"*生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"
                  f"*包含 {len(charts)} 张图表*")
        return markdown + footer


# ==================== 便捷函数 ====================

_writer = FinancialWriter()


def generate_report(data: Dict[str, Any], template_id: str = "stock_research",
                    title: str = "") -> Dict[str, Any]:
    """快速生成报告。"""
    if title:
        data["report_title"] = title
    config = WriterConfig(template_id=template_id)
    return _writer.write(data, config)


def generate_report_from_raw(raw_content: Any, template_id: str = "stock_research",
                              title: str = "", focus: str = "全面") -> Dict[str, Any]:
    """从原始内容一键生成报告。"""
    return _writer.write_from_raw(raw_content, template_id, title, focus)


def create_chart(chart_type: str, data: Dict, title: str = "",
                 output_dir: str = "") -> str:
    """快速创建图表。"""
    builder = ChartBuilder(output_dir)
    config = ChartConfig(title=title)

    if chart_type == "line":
        return builder.line_chart(data, [], config)
    elif chart_type == "bar":
        return builder.bar_chart(data, config)
    elif chart_type == "pie":
        return builder.pie_chart(data, config)
    else:
        return builder.bar_chart(data, config)


# ==================== CLI 入口 ====================

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("金融分析写作引擎 v4.0")
        print("\n用法:")
        print("  python financial_writer.py chart <type> <数据>  — 生成图表")
        print("  python financial_writer.py report <文件> [模板]  — 生成报告")
        print()
        print("图表类型: bar / line / pie / radar")
        print("模板: stock_research / industry_analysis / fund_evaluation / "
              "institution_survey / market_weekly / announcement_brief")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "chart":
        if len(sys.argv) < 4:
            print("用法: python financial_writer.py chart <type> <json数据>")
            sys.exit(1)

        chart_type = sys.argv[2]
        try:
            data = json.loads(sys.argv[3])
        except json.JSONDecodeError:
            print("数据格式错误，需要 JSON")
            sys.exit(1)

        path = create_chart(chart_type, data, title="自定义图表")
        print(f"图表已生成: {path}")

    elif cmd == "report":
        if len(sys.argv) < 3:
            print("请提供文件路径")
            sys.exit(1)

        file_path = sys.argv[2]
        template_id = sys.argv[3] if len(sys.argv) > 3 else "stock_research"

        result = generate_report_from_raw(file_path, template_id)
        saved = _writer.save_report(result)
        print(f"报告已生成: {saved}")
        print(f"\n{result['markdown'][:500]}...")

    else:
        print(f"未知命令: {cmd}")
