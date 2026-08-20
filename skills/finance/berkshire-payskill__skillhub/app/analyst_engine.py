"""AI Berkshire 四维投资分析引擎"""
import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
from openai import AsyncOpenAI

from app.config import DASHSCOPE_API_KEY, DASHSCOPE_BASE_URL, ANALYSIS_DIMENSIONS

logger = logging.getLogger(__name__)


class AnalystEngine:
    """四维投资分析引擎：段永平（商业模式）、巴菲特（财务）、芒格（行业）、李录（风险）"""
    
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=DASHSCOPE_API_KEY,
            base_url=DASHSCOPE_BASE_URL
        )
    
    async def analyze(
        self,
        stock_code: str,
        company_name: str,
        output_dir: Path,
        progress_callback=None
    ) -> Dict:
        """执行四维投资分析"""
        
        logger.info(f"开始分析: {company_name} ({stock_code})")
        
        # 更新进度
        if progress_callback:
            await progress_callback("启动", "正在初始化四维分析团队...")
        
        # 并行分析四个维度
        tasks = []
        for dim in ANALYSIS_DIMENSIONS:
            task = asyncio.create_task(
                self._analyze_dimension(dim, stock_code, company_name, progress_callback)
            )
            tasks.append((dim['id'], task))
        
        # 等待所有分析完成
        results = {}
        for dim_id, task in tasks:
            try:
                result = await task
                results[dim_id] = result
            except Exception as e:
                logger.error(f"{dim_id} 分析失败: {e}")
                results[dim_id] = {
                    "status": "error",
                    "error": str(e),
                    "score": 0,
                    "summary": "分析失败"
                }
        
        # 生成综合评估
        if progress_callback:
            await progress_callback("汇总", "正在生成综合投资报告...")
        
        synthesis = await self._synthesize(results, stock_code, company_name)
        
        # 保存结果
        final_result = {
            "stock_code": stock_code,
            "company_name": company_name,
            "analysis_time": datetime.now().isoformat(),
            "dimensions": results,
            "synthesis": synthesis
        }
        
        output_file = output_dir / "analysis_result.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(final_result, f, ensure_ascii=False, indent=2)
        
        logger.info(f"分析完成: {output_file}")
        return final_result
    
    async def _analyze_dimension(
        self,
        dimension: Dict,
        stock_code: str,
        company_name: str,
        progress_callback=None
    ) -> Dict:
        """分析单个维度"""
        
        dim_id = dimension['id']
        dim_name = dimension['name']
        analyst = dimension['analyst']
        
        logger.info(f"[{dim_name}] 开始分析...")
        
        if progress_callback:
            await progress_callback(dim_id, f"{analyst}正在分析{dim_name}...")
        
        # 构建分析提示词
        prompt = self._build_prompt(dimension, stock_code, company_name)
        
        try:
            response = await self.client.chat.completions.create(
                model="qwen-max",
                messages=[
                    {"role": "system", "content": f"你是一位专业的投资分析师，以{analyst}的投资理念和视角进行分析。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=4000
            )
            
            content = response.choices[0].message.content
            
            # 尝试解析 JSON
            try:
                # 提取 JSON 部分
                if "```json" in content:
                    json_str = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    json_str = content.split("```")[1].split("```")[0].strip()
                else:
                    json_str = content.strip()
                
                result = json.loads(json_str)
                result['status'] = 'success'
            except json.JSONDecodeError:
                # JSON 解析失败，构造默认结构
                result = {
                    "status": "success",
                    "score": 3,
                    "summary": content[:500],
                    "analysis": content,
                    "key_points": [],
                    "conclusion": "分析完成，但结果格式异常"
                }
            
            logger.info(f"[{dim_name}] 分析完成，评分: {result.get('score', 'N/A')}")
            
            if progress_callback:
                await progress_callback(dim_id, f"{dim_name}分析完成")
            
            return result
            
        except Exception as e:
            logger.error(f"[{dim_name}] 分析失败: {e}")
            return {
                "status": "error",
                "error": str(e),
                "score": 0,
                "summary": f"分析失败: {str(e)}"
            }
    
    def _build_prompt(self, dimension: Dict, stock_code: str, company_name: str) -> str:
        """构建分析提示词"""
        
        dim_id = dimension['id']
        analyst = dimension['analyst']
        
        prompts = {
            "business": f"""请从{analyst}（步步高创始人、著名投资人）的视角，对{company_name}（{stock_code}）进行商业模式分析。

分析要点：
1. **生意本质**：这家公司到底在做什么生意？用一句话概括核心商业模式
2. **护城河分析**：
   - 品牌护城河（品牌认知度、用户忠诚度）
   - 转换成本（用户迁移成本）
   - 网络效应（用户规模带来的价值）
   - 规模效应（成本优势）
   - 技术壁垒（专利、技术领先性）
3. **差异化与定价权**：产品/服务是否有差异化？是否有定价权？
4. **可持续竞争优势**：竞争优势是否可持续？10年后还在吗？
5. **管理层评估**：管理层的战略眼光、执行力、诚信度

请以 JSON 格式返回分析结果：
```json
{{
  "score": 1-5的整数评分（5分最优）,
  "summary": "100字以内的核心总结",
  "business_model": "商业模式描述",
  "segments": [
    {{"name": "业务板块", "revenue_pct": "收入占比%", "growth": "增速", "margin": "毛利率"}}
  ],
  "moat_analysis": {{
    "brand": {{"score": 1-5, "desc": "品牌护城河分析"}},
    "switching_cost": {{"score": 1-5, "desc": "转换成本分析"}},
    "network_effect": {{"score": 1-5, "desc": "网络效应分析"}},
    "scale_economy": {{"score": 1-5, "desc": "规模效应分析"}},
    "tech_barrier": {{"score": 1-5, "desc": "技术壁垒分析"}}
  }},
  "moat_radar": [品牌分数, 转换成本分数, 网络效应分数, 规模效应分数, 技术壁垒分数],
  "differentiation": "差异化与定价权分析",
  "competitive_advantage": "可持续竞争优势分析",
  "management": "管理层评估",
  "key_points": ["要点1", "要点2", "要点3"],
  "conclusion": "段永平视角的投资结论",
  "risk_warnings": ["风险1", "风险2"]
}}
```""",
            
            "financial": f"""请从{analyst}（价值投资之父）的视角，对{company_name}（{stock_code}）进行财务分析。

分析要点：
1. **盈利能力**：ROE、ROA、毛利率、净利率趋势
2. **现金流质量**：经营性现金流、自由现金流、现金流与利润的匹配度
3. **资产负债健康度**：资产负债率、流动比率、有息负债
4. **成长性**：营收增长率、利润增长率、增长质量
5. **估值分析**：当前PE/PB、历史估值区间、相对估值
6. **安全边际**：当前价格相对内在价值的位置

请以 JSON 格式返回分析结果：
```json
{{
  "score": 1-5的整数评分（5分最优）,
  "summary": "100字以内的核心总结",
  "profitability": {{
    "roe_trend": "ROE趋势分析",
    "margin_trend": "毛利率/净利率趋势",
    "analysis": "盈利能力综合评估"
  }},
  "cash_flow": {{
    "operating_cash": "经营性现金流分析",
    "free_cash": "自由现金流分析",
    "quality": "现金流质量评估"
  }},
  "balance_sheet": {{
    "debt_ratio": "资产负债率分析",
    "liquidity": "流动性分析",
    "health": "资产负债健康度评估"
  }},
  "growth": {{
    "revenue_growth": "营收增长率",
    "profit_growth": "利润增长率",
    "quality": "增长质量评估"
  }},
  "valuation": {{
    "current_pe": "当前PE",
    "current_pb": "当前PB",
    "historical": "历史估值对比",
    "assessment": "估值合理性评估"
  }},
  "margin_of_safety": "安全边际分析",
  "key_metrics": [
    {{"name": "指标名", "value": "数值", "assessment": "评估", "industry_avg": "行业平均", "trend": "趋势"}}
  ],
  "financial_trends_5y": {{
    "years": ["2019", "2020", "2021", "2022", "2023"],
    "revenue": [近5年营收数据],
    "profit": [近5年利润数据],
    "roe": [近5年ROE数据],
    "cash_flow": [近5年现金流数据]
  }},
  "segment_financials": [
    {{"name": "业务板块", "revenue": "收入(亿)", "growth": "增速%", "margin": "毛利率%", "contribution": "利润贡献%"}}
  ],
  "peer_comparison": {{
    "pe": {{"company": "公司PE", "avg": "行业平均PE", "rank": "排名"}},
    "pb": {{"company": "公司PB", "avg": "行业平均PB", "rank": "排名"}},
    "roe": {{"company": "公司ROE", "avg": "行业平均ROE", "rank": "排名"}}
  }},
  "conclusion": "巴菲特视角的投资结论",
  "buy_criteria": ["符合巴菲特买入标准的要点"]
}}
```""",
            
            "industry": f"""请从{analyst}（多元思维模型大师）的视角，对{company_name}（{stock_code}）进行行业格局分析。

分析要点：
1. **行业空间**：市场规模、增长率、渗透率、天花板
2. **竞争格局**：市场集中度、主要竞争对手、竞争态势
3. **产业链位置**：在产业链中的位置、上下游议价能力
4. **行业趋势**：技术变革、政策影响、消费升级等趋势
5. **护城河持续性**：行业变化对护城河的影响
6. **替代风险**：是否有被替代的风险

请以 JSON 格式返回分析结果：
```json
{{
  "score": 1-5的整数评分（5分最优）,
  "summary": "100字以内的核心总结",
  "market_size": {{
    "current": "当前市场规模",
    "growth_rate": "增长率",
    "ceiling": "市场天花板",
    "assessment": "行业空间评估"
  }},
  "competition": {{
    "concentration": "市场集中度（CR3/CR5）",
    "players": [{{"name": "竞争对手", "share": "市场份额", "strength": "优势"}}],
    "position": "公司市场地位",
    "dynamics": "竞争态势分析"
  }},
  "market_share_data": {{
    "company": "公司份额",
    "top1": "第一名份额",
    "top2": "第二名份额",
    "top3": "第三名份额"
  }},
  "value_chain": {{
    "position": "产业链位置",
    "bargaining_power": "议价能力分析",
    "value_distribution": "价值分配"
  }},
  "trends": {{
    "technology": "技术变革趋势",
    "policy": "政策影响",
    "consumption": "消费升级趋势",
    "impact": "对行业的影响"
  }},
  "moat_sustainability": "护城河持续性分析",
  "substitution_risk": "替代风险分析",
  "industry_metrics": [
    {{"name": "行业指标", "value": "数值", "trend": "趋势"}}
  ],
  "key_points": ["要点1", "要点2", "要点3"],
  "conclusion": "芒格视角的投资结论"
}}
```""",
            
            "risk": f"""请从{analyst}（著名价值投资人、喜马拉雅资本创始人）的视角，对{company_name}（{stock_code}）进行风险评估。

分析要点：
1. **系统性风险**：宏观经济、政策风险、行业周期
2. **公司特定风险**：经营风险、财务风险、治理风险
3. **估值风险**：当前估值是否透支未来增长
4. **黑天鹅风险**：潜在的极端风险事件
5. **长期风险**：10年维度下的主要风险
6. **风险收益比**：当前价格下的风险收益评估

请以 JSON 格式返回分析结果：
```json
{{
  "score": 1-5的整数评分（5分风险最低，1分风险最高）,
  "summary": "100字以内的核心总结",
  "systematic_risks": {{
    "macro": "宏观经济风险",
    "policy": "政策风险",
    "cycle": "行业周期风险",
    "assessment": "系统性风险评估"
  }},
  "company_risks": {{
    "operational": "经营风险",
    "financial": "财务风险",
    "governance": "治理风险",
    "assessment": "公司特定风险评估"
  }},
  "valuation_risk": "估值风险分析",
  "black_swan": ["黑天鹅风险1", "黑天鹅风险2"],
  "long_term_risks": ["长期风险1", "长期风险2", "长期风险3"],
  "risk_reward": {{
    "upside": "潜在上涨空间(%)",
    "downside": "潜在下跌空间(%)",
    "ratio": "风险收益比评估"
  }},
  "risk_matrix": [
    {{"risk": "风险名称", "probability": 1-5, "impact": 1-5, "score": "概率×影响", "mitigation": "应对措施"}}
  ],
  "key_risks": ["核心风险1", "核心风险2", "核心风险3"],
  "mitigation": ["风险缓释因素1", "风险缓释因素2"],
  "monitoring_indicators": [
    {{"indicator": "监测指标", "frequency": "监测频率(周/月/季)", "threshold": "预警阈值", "action": "触发行动"}}
  ],
  "event_calendar": [
    {{"event": "事件名称", "date": "预计时间", "impact": "潜在影响(高/中/低)", "strategy": "应对策略"}}
  ],
  "conclusion": "李录视角的风险评估结论"
}}
```"""
        }
        
        return prompts.get(dim_id, prompts["business"])
    
    async def _synthesize(self, results: Dict, stock_code: str, company_name: str) -> Dict:
        """综合四维分析，生成最终投资建议"""
        
        # 计算综合评分
        scores = []
        for dim_id, result in results.items():
            if result.get('status') == 'success' and 'score' in result:
                scores.append(result['score'])
        
        if scores:
            avg_score = sum(scores) / len(scores)
        else:
            avg_score = 0
        
        # 构建综合评估
        synthesis_prompt = f"""基于以下四个维度的分析结果，为{company_name}（{stock_code}）生成综合投资评估：

**商业模式分析（段永平视角）**：
评分：{results.get('business', {}).get('score', 'N/A')}/5
总结：{results.get('business', {}).get('summary', 'N/A')}

**财务分析（巴菲特视角）**：
评分：{results.get('financial', {}).get('score', 'N/A')}/5
总结：{results.get('financial', {}).get('summary', 'N/A')}

**行业格局分析（芒格视角）**：
评分：{results.get('industry', {}).get('score', 'N/A')}/5
总结：{results.get('industry', {}).get('summary', 'N/A')}

**风险评估（李录视角）**：
评分：{results.get('risk', {}).get('score', 'N/A')}/5
总结：{results.get('risk', {}).get('summary', 'N/A')}

请生成综合投资评估（JSON格式）：
```json
{{
  "overall_score": {avg_score:.1f},
  "score_level": "根据综合评分判断：优秀(≥4)/良好(3-4)/一般(2-3)/较差(<2)",
  "investment_thesis": "200字以内的投资论点",
  "bull_case": ["看多理由1", "看多理由2", "看多理由3"],
  "bear_case": ["看空理由1", "看空理由2", "看空理由3"],
  "key_metrics": [
    {{"name": "关键指标1", "value": "数值", "insight": "洞察"}}
  ],
  "action_recommendation": {{
    "type": "买入/观望/卖出",
    "position_size": "建议仓位比例",
    "entry_strategy": "建仓策略",
    "exit_conditions": "退出条件"
  }},
  "checklist": [
    {{"item": "巴菲特买入标准1", "pass": true/false, "note": "说明"}},
    {{"item": "巴菲特买入标准2", "pass": true/false, "note": "说明"}}
  ],
  "monitoring_indicators": [
    {{"indicator": "监测指标", "frequency": "监测频率(周/月/季)", "threshold": "预警阈值", "action": "触发行动", "priority": "高/中/低"}}
  ],
  "event_calendar": [
    {{"event": "事件名称", "date": "预计时间", "impact": "潜在影响(高/中/低)", "strategy": "应对策略", "probability": "发生概率%"}}
  ],
  "final_verdict": "最终投资结论（100字）"
}}
```"""
        
        try:
            response = await self.client.chat.completions.create(
                model="qwen-max",
                messages=[
                    {"role": "system", "content": "你是一位资深投资顾问，擅长综合多维度分析并给出投资建议。"},
                    {"role": "user", "content": synthesis_prompt}
                ],
                temperature=0.7,
                max_tokens=3000
            )
            
            content = response.choices[0].message.content
            
            # 解析 JSON
            try:
                if "```json" in content:
                    json_str = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    json_str = content.split("```")[1].split("```")[0].strip()
                else:
                    json_str = content.strip()
                
                return json.loads(json_str)
            except json.JSONDecodeError:
                return {
                    "overall_score": avg_score,
                    "score_level": "评估中",
                    "investment_thesis": content[:500],
                    "bull_case": [],
                    "bear_case": [],
                    "key_metrics": [],
                    "action_recommendation": {
                        "type": "观望",
                        "position_size": "待定",
                        "entry_strategy": "待定",
                        "exit_conditions": "待定"
                    },
                    "checklist": [],
                    "final_verdict": "综合评估完成，但结果格式异常"
                }
        
        except Exception as e:
            logger.error(f"综合评估失败: {e}")
            return {
                "overall_score": avg_score,
                "score_level": "评估失败",
                "investment_thesis": f"综合评估过程中出现错误: {str(e)}",
                "bull_case": [],
                "bear_case": [],
                "key_metrics": [],
                "action_recommendation": {
                    "type": "观望",
                    "position_size": "待定",
                    "entry_strategy": "待定",
                    "exit_conditions": "待定"
                },
                "checklist": [],
                "final_verdict": "评估失败，请稍后重试"
            }
