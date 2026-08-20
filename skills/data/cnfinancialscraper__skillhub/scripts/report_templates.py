# -*- coding: utf-8 -*-
"""
金融分析报告模板库 v4.0
6套预置 Markdown 模板，涵盖主流金融报告类型。
每套模板包含：章节结构、图表占位符、数据表格模板、风险提示段、免责声明。

模板列表：
1. stock_research    — 个股深度研报
2. industry_analysis — 行业分析报告
3. fund_evaluation   — 基金评价报告
4. institution_survey — 机构调研报告
5. market_weekly     — 市场周报
6. announcement_brief — 公告解读
"""

from typing import Dict, List, Any, Optional
from datetime import datetime


# ==================== 模板定义 ====================

class ReportTemplate:
    """单套报告模板。"""

    def __init__(self, template_id: str, name: str, description: str,
                 sections: List[Dict[str, Any]]):
        self.template_id = template_id
        self.name = name
        self.description = description
        self.sections = sections  # [{title, type, required, placeholder}]

    def render_outline(self) -> str:
        """渲染模板大纲。"""
        lines = [f"# {self.name}", f"", f"> {self.description}", ""]
        for i, sec in enumerate(self.sections, 1):
            required = " *必填*" if sec.get("required") else ""
            stype = f" [{sec.get('type', 'text')}]"
            lines.append(f"{i}. **{sec['title']}**{stype}{required}")
            if sec.get("placeholder"):
                lines.append(f"   > {sec['placeholder']}")
            lines.append("")
        return '\n'.join(lines)

    def render(self, data: Dict[str, Any],
               title_override: str = "") -> str:
        """
        渲染完整报告。

        Args:
            data: 报告数据字典，键对应 section title
            title_override: 自定义标题

        返回: Markdown 文本
        """
        lines = []

        # 标题
        title = title_override or data.get("report_title") or self.name
        lines.append(f"# {title}")
        lines.append("")

        # 元信息栏
        meta_parts = []
        if data.get("report_date"):
            meta_parts.append(f"📅 {data['report_date']}")
        if data.get("author"):
            meta_parts.append(f"✍️ {data['author']}")
        if meta_parts:
            lines.append(" | ".join(meta_parts))
            lines.append("")

        lines.append("---")
        lines.append("")

        # 逐节渲染
        for sec in self.sections:
            sec_title = sec['title']
            sec_data = data.get(sec_title, data.get(sec_title.replace(' ', '_'), ""))

            lines.append(f"## {sec_title}")
            lines.append("")

            if isinstance(sec_data, str) and sec_data:
                lines.append(sec_data)
            elif isinstance(sec_data, list):
                for item in sec_data:
                    if isinstance(item, str):
                        lines.append(f"- {item}")
                    elif isinstance(item, dict):
                        k = item.get("key", "")
                        v = item.get("value", "")
                        lines.append(f"- **{k}**: {v}")
            elif isinstance(sec_data, dict):
                if sec.get('type') == 'table':
                    lines.extend(self._render_table(sec_data))
                elif sec.get('type') == 'chart':
                    lines.extend(self._render_chart_hint(sec_data))
                else:
                    lines.append(str(sec_data))
            elif sec.get("placeholder"):
                lines.append(f"> *{sec['placeholder']}*")

            lines.append("")

        # 风险提示
        if data.get("risk_warning"):
            lines.append("## ⚠️ 风险提示")
            lines.append("")
            if isinstance(data["risk_warning"], list):
                for r in data["risk_warning"]:
                    lines.append(f"- {r}")
            else:
                lines.append(str(data["risk_warning"]))
            lines.append("")

        # 免责声明
        lines.append("---")
        lines.append("## 📜 免责声明")
        lines.append("")
        lines.append("本报告由 cn-financial-scraper 自动生成，仅供研究参考，不构成投资建议。")
        lines.append(f"数据来源为公开信息，生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}。")
        lines.append("投资者据此操作，风险自担。")

        return '\n'.join(lines)

    def _render_table(self, data: Dict[str, Any]) -> List[str]:
        """渲染表格。"""
        if not data:
            return ["> *暂无数据*"]

        headers = data.get("headers", [])
        rows = data.get("rows", [])
        if not headers:
            return ["> *暂无数据*"]

        lines = ["| " + " | ".join(str(h) for h in headers) + " |"]
        lines.append("| " + " | ".join("------" for _ in headers) + " |")
        for row in rows:
            if isinstance(row, dict):
                vals = [str(row.get(h, "")) for h in headers]
            elif isinstance(row, (list, tuple)):
                vals = [str(v) for v in row]
            else:
                vals = [str(row)]
            lines.append("| " + " | ".join(vals) + " |")

        return lines

    def _render_chart_hint(self, data: Dict[str, Any]) -> List[str]:
        """渲染图表占位符。"""
        chart_type = data.get("chart_type", "bar")
        title = data.get("chart_title", "图表")
        return [
            f"```chart",
            f"type: {chart_type}",
            f"title: {title}",
            f"data: {data.get('data', {})}",
            f"```",
            f"*[图表: {title}]*",
        ]


# ==================== 6套标准模板 ====================

TEMPLATES: Dict[str, ReportTemplate] = {}


def _register(template_id: str, name: str, description: str,
              sections: List[Dict[str, Any]]):
    TEMPLATES[template_id] = ReportTemplate(template_id, name, description, sections)


# --- 1. 个股深度研报 ---
_register("stock_research", "个股深度研究报告", "对单只股票进行基本面、估值、技术面、机构观点的全面分析",
[
    {"title": "公司概况", "type": "text", "required": True,
     "placeholder": "公司全称、股票代码、所属行业、主营业务、上市时间"},
    {"title": "核心财务数据", "type": "table", "required": True,
     "placeholder": "近3年营收/净利润/ROE/毛利率等关键指标对比"},
    {"title": "估值分析", "type": "text", "required": True,
     "placeholder": "PE/PB/PS 当前值 vs 历史分位 vs 行业均值"},
    {"title": "业务拆解", "type": "text", "required": False,
     "placeholder": "按业务板块拆分收入结构和增长驱动"},
    {"title": "技术面分析", "type": "chart", "required": False,
     "placeholder": "股价走势图、均线、MACD、成交量"},
    {"title": "盈利预测", "type": "table", "required": False,
     "placeholder": "未来2-3年营收/净利润一致预期"},
    {"title": "机构观点汇总", "type": "text", "required": False,
     "placeholder": "近3个月券商研报评级、目标价分布"},
    {"title": "同业对比", "type": "table", "required": False,
     "placeholder": "与同行业3-5家公司核心指标对比"},
    {"title": "投资建议", "type": "text", "required": True,
     "placeholder": "综合评级(买入/增持/中性/减持)、目标价、核心逻辑"},
    {"title": "催化剂与风险", "type": "text", "required": True,
     "placeholder": "短期催化剂事件 + 需关注的下行风险"},
])

# --- 2. 行业分析报告 ---
_register("industry_analysis", "行业深度分析报告", "对某个行业进行全景分析，包括产业链、竞争格局、政策环境",
[
    {"title": "行业概述", "type": "text", "required": True,
     "placeholder": "行业定义、分类、发展阶段、市场规模"},
    {"title": "产业链分析", "type": "text", "required": True,
     "placeholder": "上/中/下游结构、各环节代表公司、利润分布"},
    {"title": "竞争格局", "type": "text", "required": True,
     "placeholder": "市场集中度(CR5/CR10)、主要玩家市场份额"},
    {"title": "驱动因素", "type": "text", "required": True,
     "placeholder": "需求驱动、技术驱动、政策驱动"},
    {"title": "宏观环境", "type": "text", "required": False,
     "placeholder": "近2年重要宏观与行业环境变化及其影响分析"},
    {"title": "行业数据", "type": "table", "required": False,
     "placeholder": "行业规模、增速、利润率等关键数据"},
    {"title": "重点公司分析", "type": "text", "required": False,
     "placeholder": "3-5家代表性公司的竞争优势和风险"},
    {"title": "估值对比", "type": "table", "required": False,
     "placeholder": "行业平均估值 vs 重点公司估值"},
    {"title": "行业展望", "type": "text", "required": True,
     "placeholder": "未来3-5年发展趋势、机会与挑战"},
    {"title": "投资策略", "type": "text", "required": True,
     "placeholder": "行业配置建议、推荐标的、关注时点"},
])

# --- 3. 基金评价报告 ---
_register("fund_evaluation", "基金综合评价报告", "对公募/私募基金进行多维评价，包括业绩、风险、持仓、经理分析",
[
    {"title": "基金概况", "type": "text", "required": True,
     "placeholder": "基金全称、代码、类型、规模、成立时间、基金经理"},
    {"title": "业绩表现", "type": "table", "required": True,
     "placeholder": "近1月/3月/6月/1年/3年/成立以来收益率 + 同类排名"},
    {"title": "风险指标", "type": "table", "required": True,
     "placeholder": "波动率、最大回撤、夏普比率、信息比率"},
    {"title": "持仓分析", "type": "text", "required": False,
     "placeholder": "前十大持仓、行业分布、持仓集中度"},
    {"title": "资产配置", "type": "chart", "required": False,
     "placeholder": "股/债/现金配置比例变化"},
    {"title": "经理画像", "type": "text", "required": False,
     "placeholder": "基金经理从业年限、管理规模、投资风格、历史业绩"},
    {"title": "同类对比", "type": "table", "required": False,
     "placeholder": "与同类基金在收益/风险/费率维度对比"},
    {"title": "综合评价", "type": "text", "required": True,
     "placeholder": "综合评分、适合投资者类型、推荐意见"},
])

# --- 4. 机构调研报告 ---
_register("institution_survey", "机构调研报告", "对金融机构的资质、业务、风险进行全面调研分析",
[
    {"title": "机构概况", "type": "text", "required": True,
     "placeholder": "机构全称、类型、注册资本、成立时间、注册地"},
    {"title": "股东结构", "type": "text", "required": False,
     "placeholder": "主要股东及持股比例、实际控制人"},
    {"title": "业务分析", "type": "text", "required": True,
     "placeholder": "业务板块、收入结构、核心竞争优势"},
    {"title": "财务概览", "type": "table", "required": False,
     "placeholder": "近3年总资产/净资产/营收/净利润"},
    {"title": "监管信息", "type": "text", "required": False,
     "placeholder": "最近监管评级、处罚记录、合规状况"},
    {"title": "行业地位", "type": "text", "required": False,
     "placeholder": "在同类机构中的排名和市场份额"},
    {"title": "风险提示", "type": "text", "required": True,
     "placeholder": "信用风险、流动性风险、操作风险等"},
    {"title": "调研结论", "type": "text", "required": True,
     "placeholder": "综合评价、合作建议、关注要点"},
])

# --- 5. 市场周报 ---
_register("market_weekly", "市场周度观察报告", "对一周A股/港股/海外市场进行全面复盘与展望",
[
    {"title": "市场综述", "type": "text", "required": True,
     "placeholder": "本周上证/深成指/创业板/恒生指数涨跌幅、日均成交额"},
    {"title": "板块轮动", "type": "table", "required": True,
     "placeholder": "本周涨幅前5和后5板块、资金流向"},
    {"title": "个股扫描", "type": "text", "required": False,
     "placeholder": "周涨幅/跌幅最大个股、创历史新高/新低个股"},
    {"title": "资金面", "type": "text", "required": False,
     "placeholder": "北向资金/南向资金/融资余额变化"},
    {"title": "估值温度", "type": "chart", "required": False,
     "placeholder": "主要指数 PE/PB 当前值 & 历史分位"},
    {"title": "要闻回顾", "type": "text", "required": True,
     "placeholder": "本周重要财经事件(3-5条)及市场影响简评"},
    {"title": "机构观点", "type": "text", "required": False,
     "placeholder": "本周主要券商/基金观点摘要"},
    {"title": "下周展望", "type": "text", "required": True,
     "placeholder": "下周关注事件、配置建议、风险提示"},
])

# --- 6. 公告解读 ---
_register("announcement_brief", "上市公司公告解读", "对上市公司重大公告进行要点解读和影响分析",
[
    {"title": "公告摘要", "type": "text", "required": True,
     "placeholder": "公告标题、发布日期、公告类型、核心内容一句话总结"},
    {"title": "公告全文要点", "type": "text", "required": True,
     "placeholder": "逐条提取公告中的关键信息"},
    {"title": "财务影响", "type": "table", "required": False,
     "placeholder": "对营收/利润/资产/负债的预期影响"},
    {"title": "历史参考", "type": "text", "required": False,
     "placeholder": "同类公告的历史市场反应和数据对比"},
    {"title": "市场预期", "type": "text", "required": False,
     "placeholder": "市场一致预期 vs 公告实际情况"},
    {"title": "投资影响", "type": "text", "required": True,
     "placeholder": "对股价/估值的短期和长期影响判断"},
    {"title": "后续关注", "type": "text", "required": False,
     "placeholder": "需要持续跟踪的后续事件和时间节点"},
])


# ==================== API ====================

def get_template(template_id: str) -> Optional[ReportTemplate]:
    """获取指定模板。"""
    return TEMPLATES.get(template_id)


def list_templates() -> List[Dict[str, str]]:
    """列出所有可用模板。"""
    return [
        {"id": t.template_id, "name": t.name, "description": t.description}
        for t in TEMPLATES.values()
    ]


def render_template(template_id: str, data: Dict[str, Any],
                    title: str = "") -> str:
    """渲染指定模板为 Markdown。"""
    template = get_template(template_id)
    if not template:
        return f"# 错误\n\n未知模板: {template_id}\n\n可用模板: {', '.join(TEMPLATES.keys())}"
    return template.render(data, title_override=title)


def get_template_outline(template_id: str) -> str:
    """获取模板大纲。"""
    template = get_template(template_id)
    if not template:
        return f"未知模板: {template_id}"
    return template.render_outline()


# ==================== CLI 入口 ====================

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("金融分析报告模板库 v4.0")
        print("\n可用模板:")
        for t in TEMPLATES.values():
            print(f"  {t.template_id:<25} — {t.name}")
        print("\n用法:")
        print("  python report_templates.py list         — 列出模板")
        print("  python report_templates.py outline <id> — 显示模板大纲")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "list":
        for t_info in list_templates():
            print(f"\n### {t_info['name']} (`{t_info['id']}`)")
            print(f"> {t_info['description']}")
            template = get_template(t_info['id'])
            if template:
                print(f"   章节数: {len(template.sections)}")
                for sec in template.sections:
                    req = " [必填]" if sec.get("required") else ""
                    print(f"   - {sec['title']} ({sec['type']}){req}")

    elif cmd == "outline":
        if len(sys.argv) < 3:
            print("请提供模板ID")
            sys.exit(1)
        outline = get_template_outline(sys.argv[2])
        print(outline)

    else:
        print(f"未知命令: {cmd}")
