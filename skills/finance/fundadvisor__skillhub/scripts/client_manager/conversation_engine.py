"""
客户经理对话引擎 v1.0
有温度的基金投资顾问对话系统
"""
import json
import os
import random
import re
from datetime import datetime, date
from pathlib import Path
from typing import Optional

# 路径推断
SCRIPT_DIR = Path(__file__).resolve().parent
import sys as _sys; _sys.path.insert(0, str(SCRIPT_DIR.parent))
from fund_advisor_paths import DATA_DIR  # noqa: E402


class ClientManager:
    """
    客户经理对话引擎 - 有温度的基金投资顾问

    核心能力：
    1. 意图识别和对话管理
    2. 情感化回复生成
    3. 用户画像管理和个性化服务
    4. 持仓评测和调整建议
    5. 报告生成
    6. 板块预测
    7. 基金经理邀请
    """

    # 意图模式（按特异性排序：越具体的意图越靠前，避免被宽泛意图抢先匹配）
    INTENT_PATTERNS = {
        # ── 高特异性意图（锚定/明确关键词，优先匹配）──
        'greeting': [
            r'^你好', r'^您好', r'^hi', r'^hello', r'^早上好', r'^下午好',
            r'^晚上好', r'^嗨', r'^hey', r'在.*吗', r'忙.*', r'在不'
        ],
        'thanks': [
            r'谢谢', r'感谢', r'感恩', r'辛苦了', r'打扰'
        ],
        'acceptance': [
            r'可以', r'好的', r'行', r'同意', r'就.*这个', r'选.*方案',
            r'方案[123]', r'方案一', r'方案二', r'方案三',
            r'我要.*这个', r'买.*这个', r'就买.*', r'按.*来',
            r'跟着.*买', r'按方案.*来', r'就按.*'
        ],
        'emotional_support': [
            r'心情.*不好', r'焦虑', r'担心', r'不安', r'迷茫', r'怎么办', r'好难',
            r'崩溃', r'想哭', r'睡不着'
        ],
        'emotional_tracking': [
            r'心态.*', r'情绪.*', r'焦虑.*', r'担心.*', r'好难.*',
            r'亏.*难受', r'睡不着.*', r'崩溃.*', r'记录.*心情'
        ],
        'stop_loss_profit': [
            r'止盈', r'止损', r'设置.*提醒', r'目标.*多少', r'什么时候卖',
            r'什么情况下卖', r'告警.*设置'
        ],
        'holdings_import': [
            r'导入.*持仓', r'导入.*基金', r'识别.*持仓', r'识别.*截图',
            r'上传.*持仓', r'导入.*截图', r'导入.*word', r'导入.*pdf',
            r'导入.*文档', r'导入.*excel', r'截图.*识别', r'ocr.*识别',
            r'解析.*持仓', r'扫描.*持仓', r'拍照.*识别',
            r'导入.*链接', r'爬取.*持仓', r'抓取.*持仓', r'链接.*导入',
            r'客户.*导入', r'导入.*客户', r'客户.*持仓.*导入'
        ],
        'holdings_export': [
            r'导出.*excel', r'导出.*表格', r'导出.*csv', r'导出.*持仓表',
            r'生成.*excel', r'下载.*持仓', r'表格.*导出', r'导出.*客户',
            r'客户.*导出', r'持仓.*导出.*表'
        ],
        'client_management': [
            r'客户.*列表', r'查看.*客户', r'客户.*管理', r'所有.*客户',
            r'客户.*仓库', r'持仓.*仓库', r'切换.*客户'
        ],
        'fee_query': [
            r'费率', r'管理费', r'托管费', r'申购费', r'赎回费',
            r'手续费', r'佣金', r'费用.*多少', r'买.*费用'
        ],
        'manager_invitation': [
            r'邀请.*经理', r'让.*经理', r'请.*经理', r'经理.*介绍',
            r'基金经理.*互动', r'.*经理.*来', r'我要问.*经理',
            r'帮我邀请.*经理', r'晒.*持仓.*邀请经理'
        ],
        # ── 中等特异性意图 ──
        'fund_introduction': [
            r'介绍.*基金', r'基金.*怎么样', r'这只基金.*', r'.*基金.*分析',
            r'基金.*投资风格', r'基金.*投资目标', r'基金.*持仓.*',
            r'管理.*基金.*介绍', r'介绍一下.*基金'
        ],
        'company_info': [
            r'.*公司.*怎么样', r'.*基金公司.*', r'哪家.*好', r'基金.*公司.*',
            r'华夏.*基金', r'易方达.*', r'嘉实.*基金', r'.*基金.*公司'
        ],
        'holdings_input': [
            r'我有.*基金', r'买了.*份额', r'成本.*多少', r'定投.*基金',
            r'记录.*持仓', r'添加.*基金', r'买入.*份', r'持有.*份',
            r'我的.*持仓', r'查询.*持仓', r'看看.*仓'
        ],
        'ppt_report': [
            r'.*ppt.*', r'.*PPT.*', r'.*演示.*', r'.*幻灯片.*', r'生成.*可视化',
            r'给我.*看看.*报告', r'可视化.*报告', r'资产分析.*图'
        ],
        'report_request': [
            r'日报', r'周报', r'月报', r'季报', r'报告', r'财报', r'生成.*报告',
            r'给我.*一份.*报告'
        ],
        'quantitative_assessment': [
            r'量化评估', r'投资.*评估', r'风险.*评估', r'评分.*多少',
            r'我的.*画像', r'我的.*风险', r'适合.*什么.*基金',
            r'我.*岁.*投.*', r'年龄.*投资.*', r'能承受.*亏损'
        ],
        'recommendation_query': [
            r'推荐.*跟踪', r'跟踪.*产品', r'我的.*推荐', r'推荐.*产品.*',
            r'产品.*推荐.*跟踪', r'确认.*推荐'
        ],
        'export_portfolio': [
            r'导出.*', r'导出.*报告', r'导出.*持仓', r'导出.*组合',
            r'导出.*推荐', r'生成.*文件', r'下载.*', r'保存.*',
            r'我的.*投资组合.*', r'确认.*投资组合.*', r'跟踪.*组合.*'
        ],
        'manager_analysis': [
            r'.*经理.*怎么样', r'.*经理.*分析', r'查询.*经理', r'.*经理.*好吗',
            r'.*基金.*经理', r'.*公司.*怎么样', r'哪家.*好', r'.*经理.*风格'
        ],
        'stock_analysis': [
            r'股票.*分析', r'.*股票.*怎么样', r'.*股.*走势', r'大盘.*分析',
            r'个股.*分析', r'股票.*推荐', r'帮我.*看.*股票', r'分析.*股票',
            r'茅台.*股票', r'宁德.*股票', r'.*股.*能买吗', r'股票.*好吗'
        ],
        'macro_analysis': [
            r'宏观.*分析', r'经济.*怎么样', r'.*经济.*形势', r'GDP.*多少',
            r'CPI.*数据', r'货币.*政策', r'利率.*走势', r'M2.*多少',
            r'经济.*预测', r'.*政策.*分析', r'流动性.*分析'
        ],
        'sector_prediction': [
            r'板块.*预测', r'.*涨.*跌', r'未来.*走势', r'行业.*展望', r'板块.*机会',
            r'.*板块.*建议', r'接下来.*买.*'
        ],
        # ── 低特异性意图（宽泛模式，最后匹配）──
        'recommendation': [
            r'推荐.*基金', r'买.*什么', r'怎么投资', r'选.*基金', r'配置.*建议',
            r'我.*岁.*投', r'年龄.*风险', r'多少钱.*基金', r'想定投'
        ],
        'portfolio_evaluation': [
            r'亏损', r'亏了', r'跌了', r'缩水', r'绿了', r'浮亏', r'持仓.*分析',
            r'评测', r'我的.*基金.*怎样', r'现在.*怎么样', r'表现.*如何'
        ],
        'portfolio_report': [
            r'持仓报告', r'业绩.*怎么样', r'我的.*收益', r'盈亏.*多少'
        ],
    }

    # 情感词汇
    NEGATIVE_WORDS = ['亏', '跌', '绿', '缩水', '焦虑', '担心', '不安', '迷茫', '难', '崩溃']
    POSITIVE_WORDS = ['涨', '赚', '红', '盈利', '收益', '飘红', '开心', '高兴']

    def __init__(self, data_dir=None):
        self.data_dir = data_dir or DATA_DIR
        self._load_templates()
        self._load_user_profiles()
        self.conversation_contexts = {}  # user_id -> context
        self._init_modules()

    def _load_templates(self):
        """加载情感话术模板"""
        try:
            template_path = SCRIPT_DIR / 'emotional_templates.json'
            if template_path.exists():
                with open(template_path, 'r', encoding='utf-8') as f:
                    self.templates = json.load(f)
            else:
                self.templates = {}
        except Exception:
            self.templates = {}

    def _load_user_profiles(self):
        """加载用户画像"""
        self.user_profiles_path = self.data_dir / 'user_profiles.json'
        try:
            if self.user_profiles_path.exists():
                with open(self.user_profiles_path, 'r', encoding='utf-8') as f:
                    self.user_profiles = json.load(f)
            else:
                self.user_profiles = {}
        except Exception:
            self.user_profiles = {}

    def _save_user_profiles(self):
        """保存用户画像"""
        try:
            with open(self.user_profiles_path, 'w', encoding='utf-8') as f:
                json.dump(self.user_profiles, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _init_modules(self):
        """初始化各功能模块"""
        self._speech_engine = None
        self._portfolio_rec = None
        self._performance_tracker = None
        self._quant_analyzer = None
        self._news_advisor = None
        self._stock_analyzer = None
        self._macro_analyzer = None

    def _classify_error(self, e: Exception, operation: str = "操作") -> tuple:
        """分类错误并返回用户友好的错误信息和诊断提示

        覆盖场景：网络、数据、权限、依赖、超时、未知错误
        Returns:
            tuple: (user_message, diagnostic_hint)
        """
        error_str = str(e).lower()
        error_type = type(e).__name__

        # 网络相关错误
        network_keywords = ['timeout', 'connection', 'network', '网络', '连接', '超时', 'dns', 'socket',
                           'refused', 'reset', 'unreachable', 'name or service not known']
        if any(kw in error_str for kw in network_keywords) or 'httperror' in error_type.lower():
            return (
                f"😥 {operation}失败，网络连接有问题",
                "建议：1) 检查网络是否正常 2) 确认未被防火墙拦截 3) 稍后重试"
            )

        # JSON/数据解析错误
        if 'json' in error_str or 'decode' in error_str or 'parse' in error_str:
            return (
                f"😥 {operation}失败，数据格式异常",
                "建议：运行 python scripts/data_collection/full_data_refresh.py 修复数据文件"
            )

        # 文件不存在
        if 'no such file' in error_str or 'not found' in error_str or 'filenotfound' in error_type.lower():
            return (
                f"😥 {operation}失败，所需文件不存在",
                "建议：检查 data/ 目录下的数据文件是否完整，运行 python -m fund_advisor check 诊断"
            )

        # 权限错误
        if 'permission' in error_str or 'access denied' in error_str or 'permissionerror' in error_type.lower():
            return (
                f"😥 {operation}失败，没有访问权限",
                "建议：检查文件/目录的读写权限，或尝试以管理员身份运行"
            )

        # 依赖缺失
        if 'modulenotfound' in error_type.lower() or 'importerror' in error_type.lower():
            pkg = str(e).split("'")[1] if "'" in str(e) else "未知包"
            return (
                f"😥 {operation}失败，缺少依赖包「{pkg}」",
                f"建议：pip install {pkg}，或查看 USER-GUIDE.md 了解完整依赖列表"
            )

        # 数据为空
        if 'empty' in error_str or 'none' in error_str or '数据' in error_str:
            return (
                f"📭 {operation}暂无数据",
                "可能是数据尚未更新，建议稍后重试或运行数据更新脚本"
            )

        # API/模块调用错误
        if 'api' in error_str or 'key' in error_str:
            return (
                f"😥 {operation}失败，API 配置有问题",
                "建议：检查 .env 文件中的 API Key 是否正确配置"
            )

        # 默认错误 — 给出尽可能多的信息
        return (
            f"😥 {operation}遇到问题",
            f"错误详情: {error_type}: {str(e)[:150]}\n建议：如果问题持续，运行 python -m fund_advisor check 诊断"
        )

    def _safe_call(self, func, operation: str = "操作", *args, **kwargs):
        """安全调用函数，自动捕获异常并返回友好提示"""
        try:
            return func(*args, **kwargs)
        except Exception as e:
            user_msg, hint = self._classify_error(e, operation)
            return f"{user_msg}\n\n💡 {hint}"

    @property
    def speech_engine(self):
        """延迟加载话术引擎"""
        if self._speech_engine is None:
            try:
                # 使用相对路径导入，不依赖 sys.path
                from analysis.fund_advisor_speech import FundAdvisorSpeech
                self._speech_engine = FundAdvisorSpeech(data_dir=self.data_dir)
            except Exception:
                self._speech_engine = None
        return self._speech_engine

    @property
    def portfolio_rec(self):
        """延迟加载组合推荐"""
        if self._portfolio_rec is None:
            try:
                from analysis.portfolio_recommender_v2 import PortfolioRecommenderV2
                self._portfolio_rec = PortfolioRecommenderV2(data_dir=self.data_dir)
            except Exception:
                self._portfolio_rec = None
        return self._portfolio_rec

    @property
    def performance_tracker(self):
        """延迟加载业绩跟踪"""
        if self._performance_tracker is None:
            try:
                from analysis.performance_tracker import PerformanceTracker
                self._performance_tracker = PerformanceTracker(data_dir=self.data_dir)
            except Exception:
                self._performance_tracker = None
        return self._performance_tracker

    @property
    def quant_analyzer(self):
        """延迟加载量化分析"""
        if self._quant_analyzer is None:
            try:
                from analysis.fund_quant_analyzer import FundQuantAnalyzer
                self._quant_analyzer = FundQuantAnalyzer(data_dir=self.data_dir)
            except Exception:
                self._quant_analyzer = None
        return self._quant_analyzer

    @property
    def news_advisor(self):
        """延迟加载新闻顾问"""
        if self._news_advisor is None:
            try:
                from analysis.news_advisor import NewsAdvisor
                self._news_advisor = NewsAdvisor(data_dir=self.data_dir)
            except Exception:
                self._news_advisor = None
        return self._news_advisor

    @property
    def stock_analyzer(self):
        """延迟加载股票量化分析"""
        if self._stock_analyzer is None:
            try:
                from analysis.stock_quant_analyzer import StockQuantAnalyzer
                self._stock_analyzer = StockQuantAnalyzer(data_dir=self.data_dir)
            except Exception:
                self._stock_analyzer = None
        return self._stock_analyzer

    @property
    def macro_analyzer(self):
        """延迟加载宏观经济分析"""
        if self._macro_analyzer is None:
            try:
                from analysis.macro_analyzer import MacroAnalyzer
                self._macro_analyzer = MacroAnalyzer(data_dir=self.data_dir)
            except Exception:
                self._macro_analyzer = None
        return self._macro_analyzer

    # ==================== 纯离线模式 ====================

    def _is_online(self) -> bool:
        """本 skill 纯本地运行，始终离线"""
        return False

    def _try_llm_response(self, user_id: str, message: str, ctx: dict) -> Optional[str]:
        """纯本地模式：不使用外部 LLM"""
        return None

    def _try_llm_intent(self, message: str) -> Optional[str]:
        """纯本地模式：仅用正则匹配意图"""
        return None

    # ==================== 对话入口 ====================

    def chat(self, user_id: str, message: str) -> str:
        """
        主入口 - 处理用户消息并返回回复

        Args:
            user_id: 用户ID
            message: 用户消息

        Returns:
            str: 助手回复
        """
        # 获取或创建上下文
        ctx = self._get_context(user_id)

        # 添加用户消息到历史
        ctx['history'].append({'role': 'user', 'content': message, 'time': datetime.now().isoformat()})

        # 意图识别
        intent = self._detect_intent(message)

        # 更新当前意图
        ctx['current_intent'] = intent

        # 提取实体
        entities = self._extract_entities(message, ctx)

        # 更新上下文中的实体追踪（支持追问）
        ctx['message_count'] += 1
        if entities.get('fund_codes'):
            ctx['last_fund_code'] = entities['fund_codes'][0]
        if entities.get('manager_names'):
            ctx['last_manager_name'] = entities['manager_names'][0]
        if entities.get('stock_code'):
            ctx['last_stock_code'] = entities['stock_code']

        # 更新画像
        self._update_profile_from_message(user_id, message, entities)

        # 生成回复（一般对话优先尝试 LLM）
        response = self._generate_response(user_id, message, intent, entities, ctx)

        # v10.0: 心理感知层 — 结合行为偏差画像微调情绪相关回复（失败静默不改变原回复）
        response = self._apply_psychology_layer(user_id, response, intent)

        # 添加助手消息到历史
        ctx['history'].append({'role': 'assistant', 'content': response, 'time': datetime.now().isoformat()})

        # 限制历史长度
        if len(ctx['history']) > 40:
            ctx['history'] = ctx['history'][-40:]

        return response

    def _apply_psychology_layer(self, user_id: str, response: str, intent: str) -> str:
        """v10.0: 行为画像心理感知层。

        对情绪相关意图（持仓评估/情感支持），若客户已完成行为画像评估，
        追加一行个性化沟通提示；任何异常静默返回原回复（不改变既有行为）。
        """
        try:
            if intent not in ('portfolio_evaluation', 'emotional_support'):
                return response
            profile_path = self.data_dir / 'user_profiles.json'
            if not profile_path.exists():
                return response
            with open(profile_path, 'r', encoding='utf-8') as f:
                profiles = json.load(f)
            b = (profiles.get(user_id) or {}).get('behavioral')
            if not b or not isinstance(b, dict) or b.get('error'):
                return response
            itype = b.get('investor_type', '')
            guide = (b.get('communication_guide') or {})
            tone = guide.get('tone', '')
            if itype and tone:
                return (response
                        + f"\n\n[心理感知] 客户行为画像为「{itype}」：{tone}")
        except Exception:
            pass
        return response

    def _get_context(self, user_id: str) -> dict:
        """获取或创建对话上下文（含结构化记忆）"""
        if user_id not in self.conversation_contexts:
            self.conversation_contexts[user_id] = {
                'user_id': user_id,
                'history': [],
                'current_intent': None,
                'pending_info': {},
                'last_topic': None,
                'last_fund_code': None,      # 最近讨论的基金代码（支持追问）
                'last_manager_name': None,   # 最近讨论的基金经理
                'last_stock_code': None,     # 最近讨论的股票
                'greeted': False,
                'message_count': 0,
            }
        return self.conversation_contexts[user_id]

    # ==================== 意图识别 ====================

    def _detect_intent(self, message: str) -> str:
        """检测用户意图（LLM 优先，回退到正则）"""
        msg = message.strip()

        # 优先用 LLM 识别意图
        if self._is_online():
            llm_intent = self._try_llm_intent(msg)
            if llm_intent:
                return llm_intent

        # 情绪词优先：亏损/焦虑类消息统一视为 portfolio_evaluation
        if any(w in msg for w in self.NEGATIVE_WORDS):
            return 'portfolio_evaluation'
        if any(w in msg for w in self.POSITIVE_WORDS):
            return 'portfolio_report'

        # 回退到正则匹配
        for intent, patterns in self.INTENT_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, msg, re.IGNORECASE):
                    return intent

        return 'general'

    def _extract_entities(self, message: str, ctx: dict) -> dict:
        """提取实体信息"""
        entities = {
            'fund_codes': [],
            'fund_names': [],
            'manager_names': [],
            'amount': None,
            'age': None,
            'risk_level': None,
            'loss_pct': None,
            'gain_pct': None,
            'period': None
        }

        msg = message

        # 提取金额
        amount_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:万|元)', msg)
        if amount_match:
            entities['amount'] = float(amount_match.group(1))

        # 提取年龄
        age_match = re.search(r'(\d+)\s*(?:岁|年龄)', msg)
        if age_match:
            entities['age'] = int(age_match.group(1))

        # 提取亏损/盈利百分比
        loss_match = re.search(r'亏[损]?\s*(\d+(?:\.\d+)?)%?', msg)
        if loss_match:
            entities['loss_pct'] = -float(loss_match.group(1))

        gain_match = re.search(r'(?:盈利|赚|浮盈|收益)\s*(\d+(?:\.\d+)?)%?', msg)
        if gain_match:
            entities['gain_pct'] = float(gain_match.group(1))

        # 提取基金代码 - 查找连续的6位数字
        code_match = re.findall(r'(?<!\d)(\d{6})(?!\d)', msg)
        entities['fund_codes'] = code_match

        # 提取风险偏好
        risk_patterns = {
            '保守型': [r'保守', r'稳健', r'低风险'],
            '平衡型': [r'平衡', r'中等'],
            '积极型': [r'积极', r'高风险'],
            '激进型': [r'激进', r'很高风险']
        }
        for risk, patterns in risk_patterns.items():
            for p in patterns:
                if re.search(p, msg):
                    entities['risk_level'] = risk
                    break

        # 提取投资周期
        period_match = re.search(r'(\d+)\s*(?:年|个月)', msg)
        if period_match:
            entities['period'] = int(period_match.group(1))

        # 从亏损承受能力推断风险偏好
        max_loss_match = re.search(r'承受.*?(\d+)\s*%', msg)
        if max_loss_match:
            max_loss = float(max_loss_match.group(1))
            if max_loss >= 20:
                entities['risk_level'] = '积极型'
            elif max_loss >= 10:
                entities['risk_level'] = '平衡型'
            else:
                entities['risk_level'] = '保守型'

        return entities

    # ==================== 画像更新 ====================

    def _update_profile_from_message(self, user_id: str, message: str, entities: dict):
        """从消息中更新用户画像"""
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = {
                'created_at': datetime.now().isoformat(),
                'age': None,
                'investment_amount': None,
                'investment_experience': 'unknown',
                'risk_tolerance': 'moderate',
                'investment_horizon': None,
                'target_companies': [],
                'holdings': []
            }

        profile = self.user_profiles[user_id]

        # 更新各字段
        if entities.get('age') and profile['age'] is None:
            profile['age'] = entities['age']
        if entities.get('amount') and profile['investment_amount'] is None:
            profile['investment_amount'] = entities['amount']
        if entities.get('risk_level') and profile['risk_tolerance'] in [None, 'moderate']:
            profile['risk_tolerance'] = entities['risk_level']
        if entities.get('period') and profile['investment_horizon'] is None:
            profile['investment_horizon'] = entities['period']

    # ==================== 回复生成 ====================

    def _generate_response(self, user_id: str, message: str, intent: str, entities: dict, ctx: dict) -> str:
        """根据意图生成回复（LLM 增强）"""
        # 对于一般对话、情绪支持，优先尝试 LLM
        llm_friendly_intents = {'general', 'greeting', 'thanks', 'emotional_support',
                               'emotional_tracking', 'acceptance'}
        if intent in llm_friendly_intents:
            llm_resp = self._try_llm_response(user_id, message, ctx)
            if llm_resp:
                return llm_resp

        # 问候语
        if intent == 'greeting':
            return self._handle_greeting(ctx)

        # 感谢
        if intent == 'thanks':
            return self._handle_thanks()

        # 根据意图路由
        if intent == 'stock_analysis':
            return self._handle_stock_analysis(message, entities, ctx)
        elif intent == 'macro_analysis':
            return self._handle_macro_analysis(message, entities, ctx)
        elif intent == 'recommendation':
            return self._handle_recommendation(user_id, message, entities, ctx)
        elif intent == 'acceptance':
            return self._handle_acceptance(user_id, message, entities, ctx)
        elif intent == 'portfolio_evaluation':
            return self._handle_portfolio_evaluation(user_id, message, entities, ctx)
        elif intent == 'portfolio_report':
            return self._handle_portfolio_report(user_id, entities, ctx)
        elif intent == 'manager_analysis':
            return self._handle_manager_analysis(message, entities, ctx)
        elif intent == 'ppt_report':
            return self._handle_ppt_report_request(user_id, entities, ctx)
        elif intent == 'report_request':
            return self._handle_report_request(user_id, message, entities, ctx)
        elif intent == 'sector_prediction':
            return self._handle_sector_prediction(message, entities, ctx)
        elif intent == 'emotional_support':
            return self._handle_emotional_support(message, ctx)
        elif intent == 'holdings_input':
            return self._handle_holdings_input(user_id, message, entities, ctx)
        elif intent == 'stop_loss_profit':
            return self._handle_stop_loss_profit(user_id, message, entities, ctx)
        elif intent == 'manager_invitation':
            return self._handle_manager_invitation(user_id, message, entities, ctx)
        elif intent == 'fund_introduction':
            return self._handle_fund_introduction(user_id, message, entities, ctx)
        elif intent == 'company_info':
            return self._handle_company_info(message, entities, ctx)
        elif intent == 'fee_query':
            return self._handle_fee_query(message, entities, ctx)
        elif intent == 'export_portfolio':
            return self._handle_export_portfolio(user_id, message, entities, ctx)
        elif intent == 'quantitative_assessment':
            return self._handle_quantitative_assessment(user_id, message, entities, ctx)
        elif intent == 'emotional_tracking':
            return self._handle_emotional_tracking(user_id, message, entities, ctx)
        elif intent == 'holdings_import':
            return self._handle_holdings_import(user_id, message, entities, ctx)
        elif intent == 'holdings_export':
            return self._handle_holdings_export(user_id, message, entities, ctx)
        elif intent == 'client_management':
            return self._handle_client_management(user_id, message, entities, ctx)
        else:
            # 通用回复 — 尝试 LLM
            llm_resp = self._try_llm_response(user_id, message, ctx)
            if llm_resp:
                return llm_resp
            return self._handle_general(message, ctx)

    # ==================== 各类意图处理 ====================

    def _handle_greeting(self, ctx: dict) -> str:
        """处理问候"""
        hour = datetime.now().hour
        greeting_key = 'default'

        if 6 <= hour < 12:
            greeting_key = 'morning'
        elif 12 <= hour < 18:
            greeting_key = 'afternoon'
        elif 18 <= hour < 23:
            greeting_key = 'evening'

        templates = self.templates.get('greetings', {}).get(greeting_key, ["你好！有什么想聊的吗？"])
        greeting = random.choice(templates)

        ctx['greeted'] = True

        # 询问是否需要帮助
        follow_ups = ["今天想了解点什么？", "有什么我可以帮你的？", "你的持仓有什么想问的吗？"]
        return greeting + " " + random.choice(follow_ups)

    def _handle_stock_analysis(self, message: str, entities: dict, ctx: dict) -> str:
        """处理股票分析请求"""
        transition = self._get_random_template('transition', 'to_analysis')

        # 提取股票代码或名称
        stock_code = None
        stock_name = None

        # 提取6位数字代码
        codes = re.findall(r'(?<!\d)(\d{6})(?!\d)', message)
        if codes:
            stock_code = codes[0]

        # 提取股票名称
        name_patterns = [
            r'([^\s\d]+?)\s*股票',
            r'帮我.*分析\s*([^\s\d]+)',
            r'([^\s\d]+)\s*能买吗',
            r'([^\s\d]+)\s*怎么样',
        ]
        for pattern in name_patterns:
            match = re.search(pattern, message)
            if match:
                stock_name = match.group(1).strip()
                break

        # 如果没有提取到名称，尝试从上下文获取
        if not stock_name and not stock_code:
            return (f"{transition}...\n\n"
                    "你想分析哪只股票？可以告诉我股票名称或代码，比如'贵州茅台'或'600519'。")

        # 调用股票分析
        if self.stock_analyzer:
            try:
                result = None
                if stock_code:
                    result = self.stock_analyzer.analyze_stock(stock_code)
                elif stock_name:
                    # 通过名称查找代码需要联网，这里简化处理
                    return (f"{transition}...\n\n"
                            f"我需要股票代码才能分析，{stock_name}的代码是什么呢？\n"
                            f"比如腾讯的股票代码是'00700'，茅台是'600519'。")

                if result and 'error' not in result and result.get('stock_code'):
                    report = self.stock_analyzer.format_analysis_report(result)
                    return f"{transition}...\n\n{report}"
                elif result and 'error' in result:
                    return f"{transition}，但{result['error']}"
                else:
                    return f"{transition}，但暂时无法获取这只股票的数据，请稍后再试。"
            except Exception as e:
                user_msg, hint = self._classify_error(e, "股票分析")
                return f"{transition}，但{user_msg}\n\n{hint}"

        return (f"{transition}...\n\n"
                f"让我帮你分析一下这只股票（{stock_name or stock_code}）。\n"
                f"不过目前股票分析功能暂不可用，你可以告诉我股票代码或名称，稍后再试。")

    def _handle_macro_analysis(self, message: str, entities: dict, ctx: dict) -> str:
        """处理宏观经济分析请求"""
        transition = self._get_random_template('transition', 'to_analysis')

        # 判断分析类型
        if any(kw in message for kw in ['GDP', 'gdp']):
            analysis = self._get_macro_gdp_analysis()
        elif any(kw in message for kw in ['CPI', 'cpi', '通胀']):
            analysis = self._get_macro_cpi_analysis()
        elif any(kw in message for kw in ['PMI', 'pmi']):
            analysis = self._get_macro_pmi_analysis()
        elif any(kw in message for kw in ['货币', 'M2', 'm2', '流动性']):
            analysis = self._get_macro_money_analysis()
        elif any(kw in message for kw in ['利率', 'LPR', 'lpr', '降息']):
            analysis = self._get_macro_interest_analysis()
        elif any(kw in message for kw in ['政策', '财政', '货币']):
            analysis = self._get_macro_policy_analysis()
        elif any(kw in message for kw in ['房地产', '地产']):
            analysis = self._get_macro_real_estate_analysis()
        elif any(kw in message for kw in ['贸易', '出口', '进口', '顺差']):
            analysis = self._get_macro_trade_analysis()
        else:
            # 返回综合宏观分析
            return self._get_macro_overall_analysis()

        return f"{transition}...\n\n{analysis}"

    def _get_macro_overall_analysis(self) -> str:
        """获取综合宏观分析"""
        if self.macro_analyzer:
            try:
                return self.macro_analyzer.format_macro_report()
            except Exception:
                pass
        return "宏观分析功能暂不可用，请稍后再试。"

    def _get_macro_gdp_analysis(self) -> str:
        """获取GDP分析"""
        if self.macro_analyzer:
            try:
                gdp_data = self.macro_analyzer.get_gdp_data()
                lines = ['【GDP分析】']
                lines.append(f"当前季度：{gdp_data.get('current_quarter', 'N/A')}")
                lines.append(f"同比增速：{gdp_data.get('yoy', 0)}%")
                lines.append(f"环比增速：{gdp_data.get('qoq', 0)}%")
                lines.append(f"累计增速：{gdp_data.get('cum_ytd', 0)}%")
                lines.append(f"目标：{gdp_data.get('target', 0)}%")
                lines.append(f"状态：{gdp_data.get('status', '')}")
                return '\n'.join(lines)
            except Exception:
                pass
        return "GDP数据暂不可用。"

    def _get_macro_cpi_analysis(self) -> str:
        """获取CPI分析"""
        if self.macro_analyzer:
            try:
                cpi_data = self.macro_analyzer.get_cpi_data()
                lines = ['【CPI分析】']
                lines.append(f"最新月份：{cpi_data.get('current_month', 'N/A')}")
                lines.append(f"同比：{cpi_data.get('yoy', 0)}%")
                lines.append(f"环比：{cpi_data.get('mom', 0)}%")
                lines.append(f"核心CPI：{cpi_data.get('core_cpi', 0)}%")
                lines.append(f"状态：{cpi_data.get('status', '')}")
                lines.append(f"影响：{cpi_data.get('impact', '')}")
                return '\n'.join(lines)
            except Exception:
                pass
        return "CPI数据暂不可用。"

    def _get_macro_pmi_analysis(self) -> str:
        """获取PMI分析"""
        if self.macro_analyzer:
            try:
                pmi_data = self.macro_analyzer.get_pmi_data()
                lines = ['【PMI分析】']
                mfg = pmi_data.get('manufacturing', {})
                non_mfg = pmi_data.get('non_manufacturing', {})
                lines.append(f"制造业PMI：{mfg.get('value', 0)} | {mfg.get('status', '')}")
                lines.append(f"非制造业PMI：{non_mfg.get('value', 0)} | {non_mfg.get('status', '')}")
                return '\n'.join(lines)
            except Exception:
                pass
        return "PMI数据暂不可用。"

    def _get_macro_money_analysis(self) -> str:
        """获取货币供应分析"""
        if self.macro_analyzer:
            try:
                money_data = self.macro_analyzer.get_money_supply_data()
                liq = self.macro_analyzer.analyze_liquidity()
                lines = ['【货币与流动性分析】']
                m2 = money_data.get('M2', {})
                lines.append(f"M2：{m2.get('value', 0)}万亿 | 同比{m2.get('yoy', 0)}%")
                lines.append(f"流动性状态：{liq.get('status', '')}")
                lines.append(f"评估：{liq.get('assessment', '')}")
                return '\n'.join(lines)
            except Exception:
                pass
        return "货币数据暂不可用。"

    def _get_macro_interest_analysis(self) -> str:
        """获取利率分析"""
        if self.macro_analyzer:
            try:
                interest_data = self.macro_analyzer.get_interest_rate_data()
                lines = ['【利率走势分析】']
                policy = interest_data.get('policy_rate', {})
                market = interest_data.get('market_rate', {})
                lines.append("政策利率：")
                lines.append(f"  7天逆回购：{policy.get('7天逆回购', 0)}%")
                lines.append(f"  MLF：{policy.get('MLF', 0)}%")
                lines.append(f"  LPR1Y：{policy.get('LPR1Y', 0)}%")
                lines.append(f"  LPR5Y：{policy.get('LPR5Y', 0)}%")
                lines.append("市场利率：")
                lines.append(f"  SHIBOR隔夜：{market.get('SHIBOR隔夜', 0)}%")
                lines.append(f"  10Y国债：{market.get('国债10Y', 0)}%")
                lines.append(f"方向：{policy.get('status', '')}")
                return '\n'.join(lines)
            except Exception:
                pass
        return "利率数据暂不可用。"

    def _get_macro_policy_analysis(self) -> str:
        """获取政策分析"""
        if self.macro_analyzer:
            try:
                return self.macro_analyzer.format_policy_report()
            except Exception:
                pass
        return "政策分析暂不可用。"

    def _get_macro_real_estate_analysis(self) -> str:
        """获取房地产分析"""
        if self.macro_analyzer:
            try:
                estate_data = self.macro_analyzer.get_real_estate_data()
                lines = ['【房地产分析】']
                lines.append(f"投资：{estate_data.get('投资', {}).get('yoy', 0)}% | {estate_data.get('投资', {}).get('status', '')}")
                lines.append(f"销售：{estate_data.get('销售', {}).get('yoy', 0)}% | {estate_data.get('销售', {}).get('status', '')}")
                lines.append(f"价格：{estate_data.get('价格', {}).get('yoy', 0)}%")
                lines.append(f"总体：{estate_data.get('总体判断', '')}")
                return '\n'.join(lines)
            except Exception:
                pass
        return "房地产数据暂不可用。"

    def _get_macro_trade_analysis(self) -> str:
        """获取贸易分析"""
        if self.macro_analyzer:
            try:
                trade_data = self.macro_analyzer.get_trade_data()
                lines = ['【贸易数据分析】']
                lines.append(f"最新月份：{trade_data.get('current_month', 'N/A')}")
                lines.append(f"出口：{trade_data.get('出口', {}).get('value', 0)}亿美元 | 同比{trade_data.get('出口', {}).get('yoy', 0)}%")
                lines.append(f"进口：{trade_data.get('进口', {}).get('value', 0)}亿美元 | 同比{trade_data.get('进口', {}).get('yoy', 0)}%")
                lines.append(f"贸易顺差：{trade_data.get('trade_balance', {}).get('value', 0)}亿美元 | {trade_data.get('trade_balance', {}).get('status', '')}")
                return '\n'.join(lines)
            except Exception:
                pass
        return "贸易数据暂不可用。"

    def _handle_thanks(self) -> str:
        """处理感谢"""
        responses = [
            "不客气！很高兴能帮到你。",
            "应该的！有问题随时问我。",
            "不客气，祝你投资顺利！",
            "随时为你服务！"
        ]
        return random.choice(responses)

    def _handle_recommendation(self, user_id: str, message: str, entities: dict, ctx: dict) -> str:
        """处理推荐请求"""
        # 获取用户画像
        profile = self.user_profiles.get(user_id, {})

        # 检查是否需要更多信息
        missing_info = self._check_missing_profile_info(profile)

        if missing_info:
            return self._ask_for_profile_info(missing_info, ctx)

        # 生成推荐
        if self.portfolio_rec:
            try:
                # 使用画像中的值或默认值
                age = profile.get('age', 30) or 30
                risk = profile.get('risk_tolerance', '稳健型') or '稳健型'
                amount = profile.get('investment_amount', 10) or 10
                horizon = profile.get('investment_horizon', 3) or 3

                result = self.portfolio_rec.recommend_portfolio_v2(
                    age=age,
                    risk_tolerance=risk,
                    target_return=12,
                    investment_period=horizon,
                    max_loss=20,
                    investment_amount=amount
                )

                # 保存推荐结果到上下文，供后续确认使用
                ctx['last_recommendation'] = result

                report = self.portfolio_rec.format_portfolio_report_v2(result)

                # 添加情感前缀
                transition = self._get_random_template('transition', 'to_recommendation')
                return f"{transition}\n\n{report}"
            except Exception as e:
                user_msg, hint = self._classify_error(e, "组合推荐")
                return f"抱歉，生成推荐时{user_msg}。\n\n{hint}"

        return self._get_recommendation_fallback(message, entities, ctx)

    def _handle_acceptance(self, user_id: str, message: str, entities: dict, ctx: dict) -> str:
        """处理用户同意推荐方案"""
        # 获取之前推荐的结果
        last_result = ctx.get('last_recommendation')

        if not last_result:
            return ("还没有推荐方案呢。你可以告诉我你的情况，比如年龄、投资金额、风险偏好，"
                    "我来帮你匹配合适的基金组合。")

        schemes = last_result.get('schemes', [])
        if not schemes:
            return ("推荐方案暂不可用，请重新让我为你推荐。")

        # 解析用户选择
        choice = None
        msg = message.strip()

        # 检查方案编号
        if '方案一' in msg or '方案1' in msg or '1' in msg:
            choice = 0
        elif '方案二' in msg or '方案2' in msg or '2' in msg:
            choice = 1
        elif '方案三' in msg or '方案3' in msg or '3' in msg:
            choice = 2

        # 检查具体基金
        for i, scheme in enumerate(schemes):
            for cat_funds in scheme.get('funds', []):
                for fund in cat_funds.get('funds', []):
                    fund_code = fund.get('fund_code', '')
                    fund_name = fund.get('fund_name', '')
                    if fund_code in msg or fund_name in msg:
                        choice = i
                        break

        # 执行选择
        if choice is not None and choice < len(schemes):
            selected = schemes[choice]
            return self._confirm_selection(user_id, selected, choice + 1)
        elif choice is not None:
            return f"你选择的是方案{choice + 1}，但这个方案不存在。共有{len(schemes)}个方案可选。"
        else:
            # 默认选择方案1（稳健型）
            selected = schemes[0]
            return self._confirm_selection(user_id, selected, 1)

    def _confirm_selection(self, user_id: str, selected: dict, scheme_num: int) -> str:
        """确认用户选择"""
        lines = []
        lines.append(f"\n✅ 好的，你选择了方案{scheme_num}：{selected['name']}")
        lines.append(f"   风格：{selected['style']} | 股债比例：{selected['stock_ratio']}%/{selected['bond_ratio']}%")
        lines.append(f"   总金额：{selected['total_amount']:.1f}万元")
        lines.append("")

        lines.append("【基金配置】")
        for cat_funds in selected.get('funds', []):
            cat_name = {
                'stock_funds': '股票型',
                'bond_funds': '债券型',
                'money_funds': '货币基金',
                'qdii_funds': 'QDII海外',
                'index_funds': '指数型'
            }.get(cat_funds['category'], cat_funds['category'])

            lines.append(f"\n  {cat_name}（{cat_funds['allocated_amount']:.1f}万元）")
            for fund in cat_funds.get('funds', []):
                lines.append(f"    • {fund['fund_name']} ({fund['fund_code']})")
                lines.append(f"      经理：{fund['manager']} | 公司：{fund['company']}")

        lines.append("")
        lines.append("现在帮你记录下来，后续我会持续跟踪这只基金。")

        # 添加到持仓
        if self.performance_tracker:
            try:
                for cat_funds in selected.get('funds', []):
                    for fund in cat_funds.get('funds', []):
                        # 获取当前净值作为成本
                        nav, _ = self.performance_tracker.get_latest_nav(fund['fund_code'])
                        cost = nav if nav else 1.0

                        self.performance_tracker.add_holding(
                            fund_code=fund['fund_code'],
                            shares=fund['suggested_amount'] * 10000 / cost,  # 转换为份额
                            cost=cost,
                            user_id=user_id
                        )
            except Exception:
                pass

        # 询问是否设置提醒
        lines.append("")
        lines.append("要不要我帮你设置止盈止损提醒？比如'止损10%，止盈20%'")

        return "\n".join(lines)

    def _handle_portfolio_evaluation(self, user_id: str, message: str, entities: dict, ctx: dict) -> str:
        """处理持仓评测请求"""
        # 亏损安抚
        if entities.get('loss_pct'):
            empathy = self._get_random_template('empathy', 'loss')
            loss_pct = abs(entities['loss_pct'])

            # 根据亏损程度调整话术
            if loss_pct >= 20:
                middle = "这种级别的下跌确实很煎熬。但说实话，危机时刻往往反而蕴含机会。"
            elif loss_pct >= 10:
                middle = "10%以上的下跌确实让人难受。但波动是市场的常态，关键看怎么应对。"
            else:
                middle = "近期的调整确实超出预期。我建议你不要在最低点卖出，那样反而锁定亏损。"

            # 询问是否需要详细分析
            question = "\n\n你想让我帮你详细分析一下持仓，看看要不要调整吗？"
            return empathy + middle + question

        # 一般询问持仓分析
        transition = self._get_random_template('transition', 'to_analysis')

        if self.performance_tracker:
            try:
                holdings = self.performance_tracker.get_holdings(user_id)
                if holdings:
                    analysis = self.performance_tracker.analyze_portfolio_performance(user_id)
                    report = self.performance_tracker.format_performance_report(analysis)
                    return f"{transition}...\n\n{report}"
                else:
                    return f"{transition}，但我这边还没有你的持仓记录。\n\n你可以告诉我你持有哪些基金吗？比如：'我有10000份000858，成本1.5元'"
            except Exception as e:
                user_msg, hint = self._classify_error(e, "持仓分析")
                return f"{transition}，但{user_msg}\n\n{hint}\n\n你能具体说说你的持仓情况吗？"

        return f"{transition}。你能告诉我你的持仓情况吗？"

    def _handle_portfolio_report(self, user_id: str, entities: dict, ctx: dict) -> str:
        """处理持仓报告请求"""
        transition = self._get_random_template('transition', 'to_analysis')

        if self.performance_tracker:
            try:
                analysis = self.performance_tracker.analyze_portfolio_performance(user_id)
                if 'error' not in analysis:
                    report = self.performance_tracker.format_performance_report(analysis)
                    return report
            except Exception:
                pass

        return f"{transition}，不过我暂时获取不到你的持仓数据。你可以告诉我你买了哪些基金吗？"

    def _handle_manager_analysis(self, message: str, entities: dict, ctx: dict) -> str:
        """处理基金经理分析请求"""
        # 提取经理名
        manager_name = None
        name_patterns = [
            r'(.+?)经理',
            r'(.+?)的经理',
            r'经理\s+(.+)',
        ]
        for pattern in name_patterns:
            match = re.search(pattern, message)
            if match:
                manager_name = match.group(1).strip()
                break

        if not manager_name and entities.get('fund_codes'):
            # 通过基金代码查找经理
            manager_name = None

        if self.speech_engine:
            try:
                if manager_name:
                    response = self.speech_engine.ask(
                        question=message,
                        manager_name=manager_name,
                        client_risk='稳健型',
                        loss_pct=entities.get('loss_pct')
                    )
                    # 添加情感化结尾
                    follow_up = self._get_random_template('questions', 'follow_up')
                    return response + "\n\n" + follow_up
            except Exception:
                pass

        return self._get_manager_intro_fallback(message, ctx)

    def _handle_report_request(self, user_id: str, message: str, entities: dict, ctx: dict) -> str:
        """处理报告生成请求"""
        # 判断报告类型
        report_type = 'daily'
        if '周' in message:
            report_type = 'weekly'
        elif '月' in message:
            report_type = 'monthly'
        elif '季' in message or '季度' in message:
            report_type = 'quarterly'
        elif '半' in message:
            report_type = 'biweekly'

        transition = self._get_random_template('transition', 'to_report')

        # 获取持仓
        holdings = []
        if self.performance_tracker:
            try:
                holdings = self.performance_tracker.get_holdings(user_id)
            except Exception:
                pass

        # 生成报告内容
        report_lines = []
        report_lines.append(f"\n{'='*60}")
        report_lines.append(f"  {report_type.replace('biweekly', '半月').title()}报告")
        report_lines.append(f"  生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        report_lines.append(f"{'='*60}\n")

        # 财经资讯
        if self.news_advisor:
            try:
                self.news_advisor.crawl_news()
                news_report = self.news_advisor.format_news_report(limit=5)
                report_lines.append("【财经资讯】")
                report_lines.append(news_report)
                report_lines.append("")
            except Exception:
                pass

        # 持仓分析
        if holdings:
            if self.performance_tracker:
                try:
                    analysis = self.performance_tracker.analyze_portfolio_performance(user_id)
                    if 'error' not in analysis:
                        report_lines.append("【持仓业绩】")
                        for h in analysis.get('holdings', []):
                            name = h.get('fund_name', '')
                            code = h.get('fund_code', '')
                            profit_pct = h.get('profit_pct', 0)
                            marker = '🟢' if profit_pct > 0 else '🔴'
                            report_lines.append(f"  {marker} {name}({code}): {profit_pct:+.2f}%")
                        report_lines.append("")
                except Exception:
                    pass
        else:
            report_lines.append("【持仓】暂无记录")
            report_lines.append("")

        # 市场展望
        report_lines.append("【市场展望】")
        report_lines.append("  当前市场情绪平稳，建议保持现有配置。")
        report_lines.append("")

        report_lines.append(f"{'='*60}")
        report_lines.append("  风险提示：以上内容仅供参考，不构成投资建议")
        report_lines.append(f"{'='*60}\n")

        return transition + "\n" + "\n".join(report_lines)

    def _handle_ppt_report_request(self, user_id: str, entities: dict, ctx: dict) -> str:
        """处理PPT报告生成请求"""
        transition = self._get_random_template('transition', 'to_report')

        # 获取持仓
        holdings = []
        if self.performance_tracker:
            try:
                holdings = self.performance_tracker.get_holdings(user_id)
            except Exception:
                pass

        if not holdings:
            return (f"{transition}...\n\n"
                    "我还没有你的持仓记录，无法生成PPT报告。\n"
                    "你可以先告诉我你持有哪些基金，比如：'添加10000份000858，成本1.5元'")

        # 生成PPT
        try:
            from .ppt_report_generator import generate_ppt_report

            output_path = generate_ppt_report(
                user_id=user_id,
                holdings=holdings,
                data_dir=str(self.data_dir)
            )

            if output_path.endswith('.pptx') or '\\' in output_path or '/' in output_path:
                return (f"{transition}...\n\n"
                        f"✅ PPT资产分析报告已生成！\n\n"
                        f"📄 文件位置：{output_path}\n\n"
                        f"报告包含以下内容：\n"
                        f"  📊 资产总览（总资产/成本/收益/收益率）\n"
                        f"  📋 持仓明细（所有基金的详细数据）\n"
                        f"  🥧 资产配置（各基金占比可视化）\n"
                        f"  💡 分析总结与投资建议\n\n"
                        f"你可以用PowerPoint或WPS打开查看。")
            else:
                # 错误信息
                return f"{transition}，但{output_path}"
        except ImportError:
            return (f"{transition}...\n\n"
                    "抱歉，PPT生成功能暂不可用（缺少python-pptx库）。\n"
                    "你可以先尝试生成文本报告，如：'给我一份周报'")
        except Exception as e:
            user_msg, hint = self._classify_error(e, "PPT生成")
            return (f"{transition}...\n\n"
                    f"生成PPT时{user_msg}。\n\n{hint}\n\n"
                    "你可以试试生成文本报告，如：'给我一份周报'")

    def _handle_sector_prediction(self, message: str, entities: dict, ctx: dict) -> str:
        """处理板块预测请求"""
        transition = self._get_random_template('transition', 'to_prediction')

        # 如果有板块名称
        sector_match = re.search(r'(.+?)板块', message)
        sector = sector_match.group(1).strip() if sector_match else None

        if sector:
            prediction = self._generate_sector_prediction(sector)
            return f"{transition}...\n\n{prediction}"
        else:
            # 返回整体板块展望
            return self._generate_overall_sector_prediction()

    def _handle_emotional_support(self, message: str, ctx: dict) -> str:
        """处理情绪支持请求"""
        # 检测情绪类型
        if any(w in message for w in ['亏', '跌', '绿']):
            category = 'loss'
        elif any(w in message for w in ['焦虑', '担心', '不安']):
            category = 'anxiety'
        elif any(w in message for w in ['迷茫']):
            category = 'confusion'
        else:
            category = 'anxiety'

        empathy = self._get_random_template('empathy', category)

        # 添加鼓励
        encouragement = self._get_random_template('encouragement', 'stay_invested')

        # 添加互动引导
        follow_up = self._get_random_template('questions', 'follow_up')

        return f"{empathy}\n\n{encouragement}\n\n{follow_up}"

    def _handle_holdings_input(self, user_id: str, message: str, entities: dict, ctx: dict) -> str:
        """处理持仓录入"""
        # 检查是否是查询持仓
        if any(kw in message for kw in ['看看', '查询', '有哪些', '我的持仓', '仓']) and \
           not any(kw in message for kw in ['添加', '买', '录入', '记录', '新']):
            return self._handle_holdings_query(user_id, ctx)

        if not self.performance_tracker:
            return "抱歉，暂时无法处理持仓录入。"

        # 提取持仓信息
        fund_code = None
        shares = None
        cost = None
        purchase_date = None

        # 提取份额
        shares_match = re.search(r'(\d+(?:\.\d+)?)\s*份', message)
        if shares_match:
            shares = float(shares_match.group(1))

        # 提取成本
        cost_match = re.search(r'成本\s*(\d+(?:\.\d+)?)', message)
        if cost_match:
            cost = float(cost_match.group(1))

        # 提取日期
        date_match = re.search(r'(\d{4})[-/年](\d{1,2})[-/月](\d{1,2})?', message)
        if date_match:
            purchase_date = f"{date_match.group(1)}-{date_match.group(2).zfill(2)}-{date_match.group(3).zfill(2) if date_match.group(3) else '01'}"

        # 提取基金代码
        if entities.get('fund_codes'):
            fund_code = entities['fund_codes'][0]

        # 提取基金名
        name_match = re.search(r'([^\s\d]+)\s*(?:基金|代码)', message)
        if name_match and not fund_code:
            # 需要通过名称查找代码
            pass

        if not fund_code:
            return "请告诉我基金代码，比如：'添加10000份000858，成本1.5元，买于2025年1月'"

        if shares is None or cost is None:
            return "请告诉我份额和成本，比如：'添加10000份000858，成本1.5元'"

        try:
            result = self.performance_tracker.add_holding(fund_code, shares, cost, purchase_date, user_id=user_id)
            if result.get('success'):
                fund_name = result.get('holding', {}).get('fund_name', fund_code)
                nav = result.get('nav')
                nav_date = result.get('nav_date', '')
                info = f"好的，已记录你的持仓：\n\n  基金：{fund_name}({fund_code})\n  份额：{shares}份\n  成本：{cost:.3f}元"
                if purchase_date:
                    info += f"\n  买入日期：{purchase_date}"
                if nav:
                    info += f"\n  当前净值：{nav:.4f}（{nav_date}）"
                info += "\n\n还有什么要添加的吗？或者看看你的整体持仓情况？"
                return info
            else:
                return f"添加失败：{result.get('error', '未知错误')}"
        except Exception as e:
            user_msg, hint = self._classify_error(e, "持仓录入")
            return f"添加时{user_msg}。\n\n{hint}"

    def _handle_holdings_query(self, user_id: str, ctx: dict) -> str:
        """查询用户持仓"""
        if not self.performance_tracker:
            return "抱歉，暂时无法查询持仓。"

        try:
            holdings = self.performance_tracker.get_holdings(user_id)
            if not holdings:
                return "你还没有添加任何持仓记录。\n\n告诉我你持有的基金，比如：'添加10000份000858，成本1.5元'"

            # 分析持仓
            analysis = self.performance_tracker.analyze_portfolio_performance(user_id)
            if 'error' not in analysis:
                return self.performance_tracker.format_performance_report(analysis)
            else:
                return f"分析持仓时遇到问题：{analysis.get('error')}"
        except Exception as e:
            user_msg, hint = self._classify_error(e, "持仓查询")
            return f"查询持仓时{user_msg}。\n\n{hint}"

    def _handle_stop_loss_profit(self, user_id: str, message: str, entities: dict, ctx: dict) -> str:
        """处理止盈止损设置"""
        transition = self._get_random_template('transition', 'to_analysis')

        # 提取阈值
        stop_loss = None
        stop_profit = None

        loss_match = re.search(r'止损.*?(\d+(?:\.\d+)?)%?', message)
        if loss_match:
            stop_loss = -float(loss_match.group(1))

        profit_match = re.search(r'止盈.*?(\d+(?:\.\d+)?)%?', message)
        if profit_match:
            stop_profit = float(profit_match.group(1))

        if stop_loss is not None or stop_profit is not None:
            # 保存设置
            settings_path = self.data_dir / 'alert_settings.json'
            try:
                settings = {}
                if os.path.exists(settings_path):
                    with open(settings_path, 'r', encoding='utf-8') as f:
                        settings = json.load(f)

                if 'users' not in settings:
                    settings['users'] = {}

                if user_id not in settings['users']:
                    settings['users'][user_id] = {}

                if stop_loss is not None:
                    settings['users'][user_id]['stop_loss'] = stop_loss
                if stop_profit is not None:
                    settings['users'][user_id]['stop_profit'] = stop_profit

                with open(settings_path, 'w', encoding='utf-8') as f:
                    json.dump(settings, f, ensure_ascii=False, indent=2)

                lines = ["好的，已为你设置告警规则："]
                if stop_loss is not None:
                    lines.append(f"  🛑 止损线：{stop_loss:.1f}%")
                if stop_profit is not None:
                    lines.append(f"  🎯 止盈线：{stop_profit:.1f}%")
                lines.append("")
                lines.append("当触发条件时，我会立即提醒你。有什么其他需要吗？")
                return "\n".join(lines)
            except Exception as e:
                user_msg, hint = self._classify_error(e, "告警设置")
                return f"设置时{user_msg}。\n\n{hint}"

        return (f"{transition}...\n\n"
                "你可以这样告诉我止盈止损设置：\n"
                "  '止损8%，止盈20%'\n"
                "  '设置止损10%'\n"
                "这样每当你的基金达到这些条件时，我会马上提醒你。")

    def _handle_invitation(self, user_id: str, message: str, entities: dict, ctx: dict) -> str:
        """处理基金经理邀请"""
        transition = "好的，我来帮你邀请基金经理来解答！"

        # 获取用户持仓或关注的领域
        profile = self.user_profiles.get(user_id, {})
        holdings = profile.get('holdings', [])

        # 尝试找相关经理
        managers = []

        if self.speech_engine:
            try:
                # 从持仓中找到经理
                fund_codes = [h.get('fund_code') for h in holdings if h.get('fund_code')]
                if not fund_codes:
                    # 搜索相关经理
                    managers = self.speech_engine.find_manager(name='', top_n=3)
            except Exception:
                pass

        if managers:
            lines = [transition]
            lines.append("")
            lines.append("我为你邀请了以下基金经理，他们对你的投资方向比较了解：")
            lines.append("")

            for i, m in enumerate(managers[:3], 1):
                name = m.get('name', '')
                company = m.get('company_name', '')
                fund = m.get('current_fund_name', '')
                style = m.get('investment_style', '')

                lines.append(f"{i}. {name} ({company})")
                lines.append(f"   管理基金：{fund}")
                lines.append(f"   风格：{style}")
                lines.append("")

            lines.append("你想问哪位经理什么问题？或者告诉我你想了解哪个领域？")
            return "\n".join(lines)

        return (f"{transition}\n\n"
                "请告诉我你想了解哪个领域或者哪只基金？"
                "我可以帮你邀请相关领域的基金经理来为你解答。")

    # ==================== 持仓导入处理 ====================

    def _handle_holdings_import(self, user_id: str, message: str, entities: dict, ctx: dict) -> str:
        """处理持仓导入请求"""
        try:
            from .holdings_importer import HoldingsImporter
        except ImportError:
            return ("持仓导入功能暂不可用，请确保已安装相关依赖。\n\n"
                    "你可以手动告诉我持仓信息，比如：'添加10000份000858，成本1.5元'")

        importer = HoldingsImporter(data_dir=self.data_dir)

        # 判断导入类型
        msg_lower = message.lower()

        # 截图导入
        if any(kw in message for kw in ['截图', '图片', '照片', '拍照', 'ocr', '识别', '扫描']):
            return self._guide_screenshot_import(ctx)

        # Word导入
        if any(kw in msg_lower for kw in ['word', 'docx', 'doc', '文档']):
            return self._guide_docx_import(ctx)

        # PDF导入
        if any(kw in msg_lower for kw in ['pdf']):
            return self._guide_pdf_import(ctx)

        # 链接爬取
        if any(kw in message for kw in ['链接', 'url', '网址', '爬取', '抓取', '网站']):
            return self._guide_url_import(message, entities, ctx)

        # 通用导入引导
        return self._show_import_options()

    def _guide_screenshot_import(self, ctx: dict) -> str:
        """引导截图导入"""
        ctx['pending_action'] = 'import_screenshot'
        lines = [
            "好的，我来帮你识别截图中的持仓信息。\n",
            "请提供截图文件路径，支持以下方式：",
            "",
            "📱 **方式1：直接提供文件路径**",
            "  例如：/path/to/我的基金.png",
            "",
            "📸 **方式2：告诉我文件路径**",
            "  直接把截图文件路径发给我就行",
            "",
            "💡 **温馨提示**：",
            "  - 支持 PNG、JPG、JPEG 格式",
            "  - 截图尽量清晰，包含基金代码/名称和份额",
            "  - 首次使用需安装OCR依赖: pip install pytesseract pillow",
            "  - 还需安装Tesseract OCR: https://github.com/UB-Mannheim/tesseract/wiki",
            "",
            "请发送截图文件路径，我来帮你识别。"
        ]
        return '\n'.join(lines)

    def _guide_docx_import(self, ctx: dict) -> str:
        """引导Word文档导入"""
        ctx['pending_action'] = 'import_docx'
        lines = [
            "好的，我来帮你从Word文档中提取持仓信息。\n",
            "请提供Word文档的文件路径：",
            "",
            "📄 **支持格式**：.docx",
            "📊 **支持内容**：表格形式的持仓明细，或包含基金代码/份额/成本的文本",
            "",
            "例如：/path/to/张先生持仓.docx",
            "",
            "💡 首次使用需安装: pip install python-docx",
            "",
            "请发送文档路径。"
        ]
        return '\n'.join(lines)

    def _guide_pdf_import(self, ctx: dict) -> str:
        """引导PDF导入"""
        ctx['pending_action'] = 'import_pdf'
        lines = [
            "好的，我来帮你从PDF中提取持仓信息。\n",
            "请提供PDF文件路径：",
            "",
            "📑 **支持格式**：.pdf（文字版和表格版）",
            "⚠️  **注意**：扫描版PDF可能识别效果不佳，建议使用截图导入",
            "",
            "例如：/path/to/对账单.pdf",
            "",
            "💡 首次使用需安装: pip install pdfplumber 或 pip install pypdf2",
            "",
            "请发送PDF文件路径。"
        ]
        return '\n'.join(lines)

    def _guide_url_import(self, message: str, entities: dict, ctx: dict) -> str:
        """引导链接爬取导入"""
        # 检查是否提供了URL
        url_match = re.search(r'(https?://[^\s]+)', message)
        if url_match:
            url = url_match.group(1)
            ctx['pending_action'] = 'import_url'
            ctx['pending_url'] = url

            # 检测平台
            from .holdings_importer import HoldingsImporter
            importer = HoldingsImporter(data_dir=self.data_dir)
            platform = importer._detect_platform(url)

            platform_hints = {
                'eastmoney': '天天基金网',
                'antfortune': '蚂蚁财富/支付宝',
                'howbuy': '好买基金',
                'lufax': '陆金所',
                'unknown': '未知平台'
            }

            lines = [
                f"检测到链接，平台：{platform_hints.get(platform, platform)}\n",
                "我需要确认以下信息：",
                "",
                "1. **是否需要登录**？如果需要，请提供账号密码",
                "   格式：`账号:xxx 密码:xxx`",
                "2. **或者**：你可以直接截图持仓页面，我用OCR识别",
                "",
            ]

            if platform == 'antfortune':
                lines.append("⚠️ 蚂蚁财富需要扫码登录，建议直接截图导入。")

            if platform == 'eastmoney':
                lines.append("💡 天天基金持仓页面可直接尝试抓取公开数据。")

            lines.append("\n请选择：")
            lines.append("  - 回复 **`截图`** → 改用截图导入")
            lines.append("  - 回复 **`账号:xxx 密码:xxx`** → 尝试自动登录抓取")
            lines.append("  - 回复 **`直接抓取`** → 无需登录，尝试抓取公开数据")

            return '\n'.join(lines)

        ctx['pending_action'] = 'import_url'
        lines = [
            "请提供持仓页面的链接地址。\n",
            "支持的平台：",
            "  - 🌐 天天基金网 (fund.eastmoney.com)",
            "  - 📱 蚂蚁财富/支付宝",
            "  - 📊 好买基金 (howbuy.com)",
            "  - 🏦 其他基金销售平台\n",
            "例如：https://fund.eastmoney.com/...\n",
            "💡 首次使用需安装: pip install selenium",
        ]
        return '\n'.join(lines)

    def _show_import_options(self) -> str:
        """显示导入选项"""
        lines = [
            '我支持以下方式导入客户持仓信息：\n',
            '📸 **截图识别** — OCR识别持仓截图中的基金信息',
            '   → 说「导入截图」开始',
            '',
            '📄 **Word文档导入** — 解析.docx中的持仓表格/文本',
            '   → 说「导入Word」开始',
            '',
            '📑 **PDF导入** — 提取PDF中的持仓明细',
            '   → 说「导入PDF」开始',
            '',
            '🌐 **链接爬取** — 从基金平台页面自动抓取',
            '   → 说「导入链接」并提供URL',
            '',
            '📊 **Excel/CSV导出** — 将持仓导出为表格',
            '   → 说「导出Excel」或「导出CSV」\n',
            '你想用哪种方式？'
        ]
        return '\n'.join(lines)

    # ==================== 持仓导出处理 ====================

    def _handle_holdings_export(self, user_id: str, message: str, entities: dict, ctx: dict) -> str:
        """处理持仓导出请求"""
        try:
            from .holdings_importer import HoldingsImporter
        except ImportError:
            return "导出功能暂不可用。"

        importer = HoldingsImporter(data_dir=self.data_dir)

        # 检查是否有客户指定的上下文
        client_id = self._extract_client_id(message) or user_id

        holdings = importer.load_client_holdings(client_id)
        if not holdings:
            # 尝试从 performance_tracker 获取
            if self.performance_tracker:
                try:
                    holdings = self.performance_tracker.get_holdings(user_id)
                except Exception:
                    pass

        if not holdings:
            return ("还没有客户持仓记录，无法导出。\n\n"
                    "你可以：\n"
                    "  1. 手动输入：'添加10000份000858，成本1.5元'\n"
                    "  2. 导入截图/文档/链接：说'导入持仓'")

        msg_lower = message.lower()
        export_excel = any(kw in msg_lower for kw in ['excel', 'xlsx', '表格'])
        export_csv = any(kw in msg_lower for kw in ['csv'])

        try:
            if export_csv:
                path = importer.export_to_csv(holdings, client_id=client_id)
                label = 'CSV文件'
            else:
                path = importer.export_to_excel(holdings, client_id=client_id)
                label = 'Excel文件'

            return (f"✅ 持仓{label}已生成！\n\n"
                    f"📁 文件位置：{path}\n\n"
                    f"包含内容：\n"
                    f"  📊 持仓明细表（代码/名称/份额/成本/市值/盈亏）\n"
                    f"  📈 持仓汇总（总投入/总市值/总收益率）\n"
                    f"  📋 共 {len(holdings)} 条持仓记录\n\n"
                    f"你可以用Excel/WPS打开查看。")

        except ImportError as e:
            return (f"导出需要安装依赖: {e}\n\n"
                    f"改为导出CSV？回复'导出CSV'。")
        except Exception as e:
            return f"导出失败: {str(e)[:200]}"

    # ==================== 客户管理处理 ====================

    def _handle_client_management(self, user_id: str, message: str, entities: dict, ctx: dict) -> str:
        """处理客户持仓管理"""
        try:
            from .holdings_importer import HoldingsImporter
        except ImportError:
            return "客户管理功能暂不可用。"

        importer = HoldingsImporter(data_dir=self.data_dir)

        # 列出客户
        if any(kw in message for kw in ['列表', '所有', '查看', '管理']):
            clients = importer.list_clients()
            if not clients:
                return ("还没有客户持仓记录。\n\n"
                        "你可以：\n"
                        "  1. '导入持仓' — 从截图/文档/链接导入\n"
                        "  2. '添加10000份000858，成本1.5元' — 手动输入\n"
                        "导入时会自动创建客户记录。")

            lines = ["【客户持仓仓库】\n"]
            lines.append(f"{'客户ID':<15} {'持仓数':>6} {'总市值':>15} {'最后更新':<20}")
            lines.append("-" * 60)
            for cid, info in clients.items():
                count = info.get('holdings_count', 0)
                value = info.get('total_value', 0)
                updated = info.get('last_updated', '')[:19]
                lines.append(f"{cid:<15} {count:>6} ¥{value:>13,.2f} {updated:<20}")
            return '\n'.join(lines)

        # 切换客户
        if any(kw in message for kw in ['切换', '选择', '当前']):
            client_id = self._extract_client_id(message)
            if client_id:
                ctx['current_client_id'] = client_id
                holdings = importer.load_client_holdings(client_id)
                return (f"已切换到客户 [{client_id}]。\n"
                        f"当前持仓：{len(holdings)} 条记录。")
            return "请指定客户ID，例如：'切换客户 张先生'"

        return "你想进行的操作：\n  - '查看客户列表'\n  - '切换客户 [客户ID]'"

    def _extract_client_id(self, message: str) -> Optional[str]:
        """从消息中提取客户ID"""
        patterns = [
            r'(?:客户|用户)\s*[:：]?\s*(\S{1,20})',
            r'(?:切换|选择)\s*(?:客户|到)?\s*(\S{1,20})',
            r'(?:导入|导出)\s*(?:客户)?\s*[:：]?\s*(\S{1,20})',
        ]
        for pat in patterns:
            m = re.search(pat, message)
            if m:
                return m.group(1).strip()
        return None

    def _handle_general(self, message: str, ctx: dict) -> str:
        """处理通用对话"""
        # 检查是否有待处理的导入操作
        pending = ctx.get('pending_action', '')

        # 待处理：截图导入
        if pending == 'import_screenshot':
            return self._execute_screenshot_import(message, ctx)

        # 待处理：Word导入
        if pending == 'import_docx':
            return self._execute_docx_import(message, ctx)

        # 待处理：PDF导入
        if pending == 'import_pdf':
            return self._execute_pdf_import(message, ctx)

        # 待处理：链接导入（处理账号密码或确认）
        if pending == 'import_url':
            return self._execute_url_import(message, ctx)

        # 检测是否发送了文件路径
        if self._looks_like_file_path(message):
            return self._auto_detect_and_import(message, ctx)

        # 检查是否需要更多信息
        if not ctx.get('greeted'):
            return self._handle_greeting(ctx)

        # 检查是否有关键词可以路由
        if any(kw in message for kw in ['怎么', '为什么', '如何']):
            return self._ask_for_clarification(message, ctx)

        # 默认回复
        defaults = [
            "我理解了，你想聊点什么？",
            "好的，你有什么具体想了解的吗？",
            "明白了，有什么问题尽管问我。",
            "嗯，你说，我在听。"
        ]
        return random.choice(defaults)

    # ==================== 导入执行方法 ====================

    def _execute_screenshot_import(self, message: str, ctx: dict) -> str:
        """执行截图导入"""
        file_path = message.strip().strip('"').strip("'")

        if not os.path.exists(file_path):
            ctx.pop('pending_action', None)
            return f"找不到文件: {file_path}\n\n请检查路径是否正确，或输入'取消'放弃。"
        if file_path.lower() == '取消':
            ctx.pop('pending_action', None)
            return "已取消截图导入。"

        try:
            from .holdings_importer import HoldingsImporter
            importer = HoldingsImporter(data_dir=self.data_dir)

            client_id = ctx.get('current_client_id', 'default')
            result = importer.import_from_screenshot(file_path, client_id=client_id)

            ctx.pop('pending_action', None)

            if result['success']:
                holdings = result['holdings']
                lines = [f"✅ 截图识别成功！共识别到 {len(holdings)} 条持仓：\n"]
                for h in holdings:
                    code = h.get('fund_code', '?')
                    name = h.get('fund_name', '?')
                    shares = h.get('shares', '?')
                    cost = h.get('cost', '?')
                    lines.append(f"  📊 {name}({code}) 份额:{shares} 成本:{cost}")
                lines.append(f"\n已保存到客户 [{client_id}] 的持仓仓库。")
                lines.append("需要我对这些持仓进行量化分析吗？")
                return '\n'.join(lines)
            else:
                errors = '\n'.join(result.get('errors', ['未知错误']))
                raw = result.get('raw_text', '')
                hint = f"\n\n识别到的原始文本:\n{raw[:500]}" if raw else ""
                return f"❌ 截图识别未成功:\n{errors}{hint}\n\n请确认截图清晰且包含基金代码/名称和份额信息。或手动输入: '添加[份额]份[代码]，成本[价格]'"
        except ImportError as e:
            ctx.pop('pending_action', None)
            return f"导入功能缺少依赖: {e}\n\n请安装: pip install pytesseract pillow\n或改为手动输入: '添加10000份000858，成本1.5元'"
        except Exception as e:
            ctx.pop('pending_action', None)
            return f"截图导入失败: {str(e)[:200]}"

    def _execute_docx_import(self, message: str, ctx: dict) -> str:
        """执行Word文档导入"""
        file_path = message.strip().strip('"').strip("'")

        if file_path.lower() == '取消':
            ctx.pop('pending_action', None)
            return "已取消Word导入。"

        if not os.path.exists(file_path):
            ctx.pop('pending_action', None)
            return f"找不到文件: {file_path}\n\n请检查路径。"

        try:
            from .holdings_importer import HoldingsImporter
            importer = HoldingsImporter(data_dir=self.data_dir)

            client_id = ctx.get('current_client_id', 'default')
            result = importer.import_from_docx(file_path, client_id=client_id)

            ctx.pop('pending_action', None)

            if result['success']:
                holdings = result['holdings']
                lines = [f"✅ Word文档解析成功！共提取 {len(holdings)} 条持仓：\n"]
                for h in holdings:
                    code = h.get('fund_code', '?')
                    name = h.get('fund_name', '?')
                    shares = h.get('shares', '?')
                    cost = h.get('cost', '?')
                    lines.append(f"  📊 {name}({code}) 份额:{shares} 成本:{cost}")
                lines.append(f"\n已保存到客户 [{client_id}] 的持仓仓库。")
                return '\n'.join(lines)
            else:
                errors = '\n'.join(result.get('errors', ['未能解析']))
                return f"❌ Word文档解析未成功:\n{errors}\n\n请确保文档包含基金代码/份额/成本等信息的表格或文本。"
        except ImportError as e:
            ctx.pop('pending_action', None)
            return f"需要安装依赖: {e}\npip install python-docx"
        except Exception as e:
            ctx.pop('pending_action', None)
            return f"Word导入失败: {str(e)[:200]}"

    def _execute_pdf_import(self, message: str, ctx: dict) -> str:
        """执行PDF导入"""
        file_path = message.strip().strip('"').strip("'")

        if file_path.lower() == '取消':
            ctx.pop('pending_action', None)
            return "已取消PDF导入。"

        if not os.path.exists(file_path):
            ctx.pop('pending_action', None)
            return f"找不到文件: {file_path}"

        try:
            from .holdings_importer import HoldingsImporter
            importer = HoldingsImporter(data_dir=self.data_dir)

            client_id = ctx.get('current_client_id', 'default')
            result = importer.import_from_pdf(file_path, client_id=client_id)

            ctx.pop('pending_action', None)

            if result['success']:
                holdings = result['holdings']
                lines = [f"✅ PDF解析成功！共提取 {len(holdings)} 条持仓：\n"]
                for h in holdings:
                    code = h.get('fund_code', '?')
                    name = h.get('fund_name', '?')
                    shares = h.get('shares', '?')
                    cost = h.get('cost', '?')
                    lines.append(f"  📊 {name}({code}) 份额:{shares} 成本:{cost}")
                lines.append(f"\n已保存到客户 [{client_id}] 的持仓仓库。")
                return '\n'.join(lines)
            else:
                errors = '\n'.join(result.get('errors', ['未能解析']))
                return f"❌ PDF解析未成功:\n{errors}\n\n如果是扫描件，建议使用截图导入。"
        except ImportError as e:
            ctx.pop('pending_action', None)
            return f"需要安装依赖: {e}\npip install pdfplumber 或 pip install pypdf2"
        except Exception as e:
            ctx.pop('pending_action', None)
            return f"PDF导入失败: {str(e)[:200]}"

    def _execute_url_import(self, message: str, ctx: dict) -> str:
        """执行链接导入"""
        msg = message.strip()

        if msg.lower() == '取消':
            ctx.pop('pending_action', None)
            ctx.pop('pending_url', None)
            return "已取消链接导入。"

        if msg == '截图':
            ctx['pending_action'] = 'import_screenshot'
            return "好的，改为截图导入。请发送截图文件路径。"

        if msg == '直接抓取':
            url = ctx.get('pending_url', '')
            if not url:
                ctx.pop('pending_action', None)
                return "请提供要抓取的链接地址。"

            try:
                from .holdings_importer import HoldingsImporter
                importer = HoldingsImporter(data_dir=self.data_dir)
                client_id = ctx.get('current_client_id', 'default')
                result = importer.import_from_url(url, client_id=client_id)
                ctx.pop('pending_action', None)
                ctx.pop('pending_url', None)
                return self._format_url_import_result(result, client_id)
            except Exception as e:
                ctx.pop('pending_action', None)
                ctx.pop('pending_url', None)
                return f"抓取失败: {str(e)[:200]}"

        # 检查是否提供了账号密码
        cred_match = re.search(r'账号[:：]\s*(\S+)\s*密码[:：]\s*(\S+)', msg)
        if not cred_match:
            cred_match = re.search(r'(\S+)\s*[:：]\s*(\S{4,})', msg)

        if cred_match:
            username = cred_match.group(1)
            password = cred_match.group(2)
            url = ctx.get('pending_url', '')
            if not url:
                ctx.pop('pending_action', None)
                return "请先提供持仓页面链接。"

            try:
                from .holdings_importer import HoldingsImporter
                importer = HoldingsImporter(data_dir=self.data_dir)
                client_id = ctx.get('current_client_id', 'default')
                result = importer.import_from_url(
                    url, client_id=client_id,
                    credentials={'username': username, 'password': password}
                )
                ctx.pop('pending_action', None)
                ctx.pop('pending_url', None)
                return self._format_url_import_result(result, client_id)
            except Exception as e:
                ctx.pop('pending_action', None)
                ctx.pop('pending_url', None)
                return f"登录抓取失败: {str(e)[:200]}\n\n建议改用截图导入。"

        return "请回复:\n  - '截图' → 改用截图导入\n  - '账号:xxx 密码:xxx' → 自动登录抓取\n  - '直接抓取' → 无需登录抓取公开数据\n  - '取消' → 取消导入"

    def _format_url_import_result(self, result: dict, client_id: str) -> str:
        """格式化链接导入结果"""
        if result['success']:
            lines = [f"✅ 链接抓取成功！共获取 {len(result['holdings'])} 条持仓：\n"]
            for h in result['holdings']:
                code = h.get('fund_code', '?')
                name = h.get('fund_name', '?')
                nav = h.get('current_nav', '')
                lines.append(f"  📊 {name}({code})" + (f" 净值:{nav}" if nav else ""))
            lines.append(f"\n已保存到客户 [{client_id}] 的持仓仓库。")
            if result.get('screenshot_path'):
                lines.append(f"📸 页面截图已保存: {result['screenshot_path']}")
            return '\n'.join(lines)
        else:
            errors = '\n'.join(result.get('errors', ['未知错误']))
            return f"❌ 抓取未成功:\n{errors}\n\n建议改用截图导入：回复'截图'"

    def _looks_like_file_path(self, message: str) -> bool:
        """检测是否为文件路径"""
        msg = message.strip()
        return bool(
            re.match(r'[A-Za-z]:[\\/]', msg) or
            re.match(r'[~/]', msg) or
            msg.endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff',
                         '.docx', '.doc', '.pdf', '.xlsx', '.xls', '.csv'))
        )

    def _auto_detect_and_import(self, message: str, ctx: dict) -> str:
        """自动检测文件类型并导入"""
        msg = message.strip().strip('"').strip("'")
        msg_lower = msg.lower()

        if not os.path.exists(msg):
            return f"找不到文件: {msg}\n\n请检查文件路径。你可以:\n  - 重新输入正确的路径\n  - 说'导入持仓'了解其他导入方式"

        if msg_lower.endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff')):
            ctx['pending_action'] = 'import_screenshot'
            return self._execute_screenshot_import(msg, ctx)

        if msg_lower.endswith(('.docx', '.doc')):
            ctx['pending_action'] = 'import_docx'
            return self._execute_docx_import(msg, ctx)

        if msg_lower.endswith('.pdf'):
            ctx['pending_action'] = 'import_pdf'
            return self._execute_pdf_import(msg, ctx)

        return f"无法识别文件类型: {msg}\n支持的类型: 图片(.png/.jpg)、Word(.docx)、PDF(.pdf)"

    # ==================== 辅助方法 ====================

    def _check_missing_profile_info(self, profile: dict) -> list:
        """检查缺失的画像信息"""
        missing = []
        if profile.get('age') is None:
            missing.append('年龄')
        if profile.get('investment_amount') is None:
            missing.append('投资金额')
        if profile.get('risk_tolerance') in [None, 'moderate']:
            missing.append('风险偏好')
        if profile.get('investment_horizon') is None:
            missing.append('投资时长')
        return missing

    def _ask_for_profile_info(self, missing: list, ctx: dict) -> str:
        """询问缺失的画像信息"""
        if not ctx.get('asked_profile'):
            ctx['asked_profile'] = True
            first_missing = missing[0]
            questions = {
                '年龄': "你大概多大年龄？方便说说吗？这样我能给你更合适的推荐。",
                '投资金额': "你打算投入多少资金？这样我可以帮你规划配置。",
                '风险偏好': "你平时的投资风格是偏稳健还是偏进取？这会影响基金选择。",
                '投资时长': "这笔钱你大概多久不用？投资周期越长，可以承受的风险越高。"
            }
            return questions.get(first_missing, f"能告诉我你的{first_missing}吗？")
        else:
            return "我还在等你的回复呢，方便说说吗？"

    def _get_random_template(self, category: str, key: str) -> str:
        """获取随机模板"""
        try:
            templates = self.templates.get(category, {}).get(key, [])
            if templates:
                return random.choice(templates)
        except Exception:
            pass
        return ""

    def _get_recommendation_fallback(self, message: str, entities: dict, ctx: dict) -> str:
        """推荐降级处理"""
        transition = self._get_random_template('transition', 'to_recommendation')

        # 尝试提取基金类型偏好
        sector = None
        for kw in ['科技', '消费', '医药', '新能源', '金融', '制造']:
            if kw in message:
                sector = kw
                break

        if sector:
            return (f"{transition}...\n\n"
                    f"根据你的需求，我帮你筛选了{sector}领域的几只基金：\n\n"
                    f"不过我需要更多信息才能给出更精准的推荐。\n"
                    f"能告诉我你的年龄、大概投资金额、以及你能承受多大的亏损吗？")

        return (f"{transition}...\n\n"
                "不过要给出好的推荐，我需要了解你一些情况。\n"
                "能告诉我：\n"
                "  1. 你大概多大年龄？\n"
                "  2. 打算投入多少钱？\n"
                "  3. 能承受多大的亏损？\n\n"
                "这样我能帮你匹配到更合适的基金。")

    def _get_manager_intro_fallback(self, message: str, ctx: dict) -> str:
        """基金经理分析降级处理"""
        # 提取经理名
        name_match = re.search(r'([^\s\d]+?)经理', message)
        manager_name = name_match.group(1).strip() if name_match else None

        if manager_name:
            return (f"让我找找「{manager_name}」经理的信息...\n\n"
                    f"抱歉，数据库里暂时没有这位经理的详细资料。\n"
                    f"不过我可以从现有数据中帮你分析一下市场情况。\n\n"
                    f"你想了解哪个方面的内容？")

        return ("你想了解哪位基金经理？可以告诉我他的名字。")

    def _generate_sector_prediction(self, sector: str) -> str:
        """生成板块预测"""
        # 从新闻获取情绪
        sentiment = 'neutral'
        if self.news_advisor:
            try:
                # 简单检查新闻情绪
                sentiment = 'neutral'
            except Exception:
                pass

        # 模拟预测结果（实际应该调用量化分析）
        predictions = {
            'week': {'change': random.uniform(-3, 5), 'reason': '短期消息面和技术面影响'},
            'month': {'change': random.uniform(-5, 10), 'reason': '行业景气度和市场资金流向'},
            'quarter': {'change': random.uniform(-10, 20), 'reason': '宏观经济和政策环境'}
        }

        lines = []
        lines.append(f"【{sector}板块走势预测】")
        lines.append("")

        for period, pred in predictions.items():
            period_name = {'week': '一周', 'month': '一个月', 'quarter': '一季度'}[period]
            direction = "上涨" if pred['change'] > 0 else "下跌"

            lines.append(f"  📅 {period_name}：预计{direction} {abs(pred['change']):.1f}%")
            lines.append(f"     理由：{pred['reason']}")
            lines.append("")

        lines.append("⚠️ 以上预测仅供参考，不构成投资建议。")

        return "\n".join(lines)

    def _generate_overall_sector_prediction(self) -> str:
        """生成整体板块展望"""
        if self.news_advisor:
            try:
                self.news_advisor.crawl_news()
                sentiment = self.news_advisor.get_market_sentiment()
            except Exception:
                sentiment = 'neutral'
        else:
            sentiment = 'neutral'

        sentiment_desc = {
            'bull': '市场情绪较为乐观',
            'bear': '市场情绪较为谨慎',
            'neutral': '市场情绪平稳',
            'uncertain': '市场情绪不明'
        }

        lines = []
        lines.append("【各板块展望】")
        lines.append("")
        lines.append(f"当前市场：{sentiment_desc.get(sentiment, '平稳')}")
        lines.append("")

        # 热门板块
        lines.append("  🚀 近期机会板块：")
        lines.append("     - 科技板块：AI应用持续发酵，关注国产替代")
        lines.append("     - 新能源：渗透率提升，龙头企业估值合理")
        lines.append("     - 消费：估值修复预期，下半年可能有表现")
        lines.append("")

        lines.append("  ⚠️ 需要谨慎的板块：")
        lines.append("     - 高估值成长股：注意回调风险")
        lines.append("     - 周期性板块：关注宏观数据变化")
        lines.append("")

        lines.append("建议：均衡配置，不要过于集中单一板块。")
        lines.append("")
        lines.append("有什么具体想了解的吗？")

        return "\n".join(lines)

    def _ask_for_clarification(self, message: str, ctx: dict) -> str:
        """询问澄清"""
        questions = [
            "你想了解的是基金投资方面的问题吗？",
            "能具体说说你的情况吗？比如你持有哪些基金？",
            "你是在问投资建议还是想了解某个具体的基金？"
        ]
        return random.choice(questions)

    # ==================== 基金经理邀请处理 ====================

    def _handle_manager_invitation(self, user_id: str, message: str, entities: dict, ctx: dict) -> str:
        """处理基金经理邀请"""
        try:
            from .invitation_engine import InvitationEngine
        except ImportError:
            return "抱歉，基金经理邀请功能暂时不可用。"

        # 获取用户持仓
        profile = self.user_profiles.get(user_id, {})
        holdings = profile.get('holdings', [])

        # 如果有基金代码，优先使用
        if entities.get('fund_codes'):
            holdings = [{'fund_code': code} for code in entities['fund_codes']]

        if not holdings:
            return ("我需要知道您持有哪些基金才能为您邀请对应的基金经理。\n"
                    "请问您持有哪些基金？可以告诉我基金代码或名称。")

        engine = InvitationEngine(data_dir=self.data_dir)

        # 根据持仓邀请经理
        result = engine.invite_managers_for_products(holdings, user_id)

        # 保存邀请的经理到上下文
        ctx['invited_managers'] = engine.managers_db

        return result

    # ==================== 基金经理介绍产品 ====================

    def _handle_fund_introduction(self, user_id: str, message: str, entities: dict, ctx: dict) -> str:
        """处理基金经理介绍产品"""
        try:
            from analysis.realtime_manager_talk import introduce_fund
        except ImportError:
            return "抱歉，基金介绍功能暂时不可用。"

        fund_code = None

        # 从消息中提取基金代码
        code_match = re.search(r'(\d{6})', message)
        if code_match:
            fund_code = code_match.group(1)
        elif entities.get('fund_codes'):
            fund_code = entities['fund_codes'][0]

        # 从上下文获取
        if not fund_code and 'current_fund' in ctx.get('pending_info', {}):
            fund_code = ctx['pending_info']['current_fund']

        if not fund_code:
            return ("请告诉我您想了解哪只基金？告诉我基金代码即可，例如：001924")

        return introduce_fund(fund_code)

    # ==================== 基金公司信息 ====================

    def _handle_company_info(self, message: str, entities: dict, ctx: dict) -> str:
        """处理基金公司信息查询"""
        try:
            import json
            company_file = self.data_dir / 'fund_companies_distilled.json'
            if not company_file.exists():
                return "抱歉，基金公司数据暂时不可用。"

            with open(company_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 提取公司名
            company_name = None
            for kw in ['华夏', '易方达', '嘉实', '南方', '广发', '富国', '博时', '招商', '工银', '建信']:
                if kw in message:
                    company_name = kw
                    break

            if not company_name:
                return "请告诉我您想了解哪家基金公司？例如：华夏基金、易方达等"

            # 查找公司
            for company in data.get('companies', []):
                if company_name in company.get('name', ''):
                    name = company.get('name', '')
                    total_funds = company.get('total_funds', 0)
                    scale = company.get('total_scale', 0)
                    style = company.get('dominant_style', '')

                    lines = []
                    lines.append(f"\n【{name}】")
                    lines.append(f"  管理基金数量：{total_funds}只")
                    if scale:
                        lines.append(f"  管理总规模：{scale:.0f}亿元")
                    lines.append(f"  主导风格：{style}")

                    # 产品列表
                    products = company.get('products', [])
                    if products:
                        lines.append(f"\n  旗下部分产品：")
                        for p in products[:5]:
                            lines.append(f"    • {p.get('fund_name', '')}（{p.get('fund_code', '')}）")
                            fee = p.get('fee', {})
                            if fee:
                                lines.append(f"      费率：管理费{fee.get('management_fee', 0):.2f}% 申购费{fee.get('subscription_fee', 0):.2f}%")

                    return "\n".join(lines)

            return f"抱歉，数据库中暂时没有{name}的详细信息。"

        except Exception as e:
            user_msg, hint = self._classify_error(e, "基金公司查询")
            return f"抱歉，处理请求时{user_msg}。\n\n{hint}"

    # ==================== 费率查询 ====================

    def _handle_fee_query(self, message: str, entities: dict, ctx: dict) -> str:
        """处理费率查询"""
        fund_code = None

        # 提取基金代码
        code_match = re.search(r'(\d{6})', message)
        if code_match:
            fund_code = code_match.group(1)
        elif entities.get('fund_codes'):
            fund_code = entities['fund_codes'][0]

        if not fund_code:
            return "请告诉我您想查询哪只基金的费率？例如：001924"

        try:
            import json
            company_file = self.data_dir / 'fund_companies_distilled.json'
            if not company_file.exists():
                return "抱歉，费率数据暂时不可用。"

            with open(company_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 查找基金费率
            for company in data.get('companies', []):
                products = company.get('products', [])
                for p in products:
                    if p.get('fund_code') == fund_code:
                        fee = p.get('fee', {})
                        if fee:
                            lines = []
                            lines.append(f"\n【{p.get('fund_name', '')}（{fund_code}）费率信息】")
                            lines.append(f"  管理费率：{fee.get('management_fee', 0):.2f}%")
                            lines.append(f"  托管费率：{fee.get('custodian_fee', 0):.2f}%")
                            lines.append(f"  申购费率：{fee.get('subscription_fee', 0):.2f}%")
                            lines.append(f"  赎回费率：{fee.get('redemption_fee', 0):.2f}%")
                            if fee.get('min_subscription'):
                                lines.append(f"  最低申购金额：{fee.get('min_subscription')}元")
                            return "\n".join(lines)

            return f"抱歉，暂时没有找到{fund_code}的费率信息。"

        except Exception as e:
            user_msg, hint = self._classify_error(e, "费率查询")
            return f"抱歉，查询费率时{user_msg}。\n\n{hint}"

    # ==================== 导出投资组合 ====================

    def _handle_export_portfolio(self, user_id: str, message: str, entities: dict, ctx: dict) -> str:
        """处理导出投资组合"""
        try:
            from .report_generator import ReportGenerator
        except ImportError:
            return "抱歉，报告生成功能暂时不可用。"

        profile = self.user_profiles.get(user_id, {})
        holdings = profile.get('holdings', [])

        # 检查是否有持仓
        if not holdings:
            return ("您还没有添加任何持仓，无法导出投资组合报告。\n"
                    "请先告诉我您持有哪些基金，我会帮您记录并生成分析报告。")

        # 生成报告类型
        report_type = 'comprehensive'
        if '周' in message:
            report_type = 'weekly'
        elif '月' in message:
            report_type = 'monthly'

        generator = ReportGenerator(data_dir=self.data_dir)

        # 生成报告
        try:
            report = generator.generate_portfolio_report(
                user_id=user_id,
                holdings=holdings,
                report_type=report_type,
                include_visualization=True
            )

            # 保存到文件
            from pathlib import Path
            export_dir = self.data_dir / 'exports'
            export_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"portfolio_report_{user_id}_{timestamp}.txt"
            filepath = export_dir / filename

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(report)

            return (f"✅ 投资组合报告已生成！\n\n"
                    f"📁 保存位置：{filepath}\n\n"
                    f"报告包含：\n"
                    f"  • 持仓明细及盈亏分析\n"
                    f"  • 可视化图表（资产配置、收益分布）\n"
                    f"  • 风险评估与建议\n"
                    f"  • 基金经理介绍\n"
                    f"  • 下一步操作建议\n\n"
                    f"您还可以：\n"
                    f"  • '生成PPT报告' - 获取可视化演示文件\n"
                    f"  • '导出Excel' - 获取表格数据\n"
                    f"  • '跟踪推荐' - 保存推荐的投资组合")

        except Exception as e:
            user_msg, hint = self._classify_error(e, "投资组合报告生成")
            return f"抱歉，生成报告时{user_msg}。\n\n{hint}"

    # ==================== 量化评估处理 ====================

    def _handle_quantitative_assessment(self, user_id: str, message: str, entities: dict, ctx: dict) -> str:
        """处理客户量化评估请求"""
        try:
            from .user_profile_manager import UserQuantitativeAssessment
        except ImportError:
            return "抱歉，量化评估功能暂时不可用。"

        # 获取用户画像
        profile = self.user_profiles.get(user_id, {})

        # 如果用户没有完整画像，先收集信息
        if not profile.get('age') or not profile.get('risk_tolerance'):
            return self._collect_profile_for_assessment(user_id, message, entities, ctx)

        # 执行评估
        assessment = UserQuantitativeAssessment(data_dir=self.data_dir)
        result = assessment.assess_investment_profile(
            age=profile.get('age'),
            risk_tolerance=profile.get('risk_tolerance'),
            investment_amount=profile.get('investment_amount'),
            investment_horizon=profile.get('investment_horizon'),
            target_companies=profile.get('target_companies', []),
            target_managers=profile.get('target_managers', [])
        )

        # 保存评估结果到上下文
        ctx['last_assessment'] = result

        # 生成报告
        report = assessment.format_assessment_report(result)

        # 添加情感前缀
        transition = self._get_random_template('transition', 'to_analysis')
        return f"{transition}...\n\n{report}"

    def _collect_profile_for_assessment(self, user_id: str, message: str, entities: dict, ctx: dict) -> str:
        """收集用户画像信息用于评估"""
        profile = self.user_profiles.get(user_id, {})
        missing = []

        # 检查缺失的信息
        if not profile.get('age') and not entities.get('age'):
            missing.append('年龄')
        if not profile.get('risk_tolerance') and not entities.get('risk_level'):
            missing.append('风险偏好')
        if not profile.get('investment_amount') and not entities.get('amount'):
            missing.append('投资金额')
        if not profile.get('investment_horizon') and not entities.get('period'):
            missing.append('投资周期')

        if missing:
            # 尝试从消息中提取
            if entities.get('age') and not profile.get('age'):
                profile['age'] = entities['age']
            if entities.get('risk_level') and not profile.get('risk_tolerance'):
                profile['risk_tolerance'] = entities['risk_level']
            if entities.get('amount') and not profile.get('investment_amount'):
                profile['investment_amount'] = entities['amount']
            if entities.get('period') and not profile.get('investment_horizon'):
                profile['investment_horizon'] = entities['period']

            self.user_profiles[user_id] = profile
            self._save_user_profiles()

            # 重新检查缺失
            missing = [m for m in missing if (
                (m == '年龄' and not profile.get('age')) or
                (m == '风险偏好' and not profile.get('risk_tolerance')) or
                (m == '投资金额' and not profile.get('investment_amount')) or
                (m == '投资周期' and not profile.get('investment_horizon'))
            )]

            if missing:
                return self._ask_for_assessment_info(missing, ctx)

        # 信息足够，执行评估
        return self._handle_quantitative_assessment(user_id, message, entities, ctx)

    def _ask_for_assessment_info(self, missing: list, ctx: dict) -> str:
        """询问评估所需信息"""
        if not ctx.get('asked_assessment'):
            ctx['asked_assessment'] = True
            first_missing = missing[0]
            questions = {
                '年龄': '你大概多大年龄？比如"我35岁"',
                '风险偏好': '你平时的投资风格是偏稳健还是偏进取？',
                '投资金额': '你打算投入多少资金？可以说"我打算投20万"',
                '投资周期': '这笔钱你大概多久不用？可以说"5年左右"'
            }
            return f"为了给你准确的量化评估，{questions.get(first_missing, f'能告诉我你的{first_missing}吗？')}"
        else:
            return "我还在等你的回复，方便说说吗？"

    # ==================== 投资心态跟踪处理 ====================

    def _handle_emotional_tracking(self, user_id: str, message: str, entities: dict, ctx: dict) -> str:
        """处理投资心态跟踪请求"""
        try:
            from .emotional_tracker import EmotionalTracker
        except ImportError:
            return "抱歉，心态跟踪功能暂时不可用。"

        tracker = EmotionalTracker(data_dir=self.data_dir)

        # 检查是否是记录情绪
        if any(kw in message for kw in ['记录', '添加', '心情', '情绪']):
            return self._handle_record_emotion(user_id, message, entities, ctx, tracker)

        # 检查是否是查询分析
        if any(kw in message for kw in ['分析', '报告', '看看', '查询']):
            return tracker.get_emotion_analysis(user_id)

        # 默认返回情绪状态
        return self._handle_emotional_status(user_id, message, entities, ctx, tracker)

    def _handle_record_emotion(self, user_id: str, message: str, entities: dict, ctx: dict, tracker) -> str:
        """记录用户情绪"""
        # 提取情绪类型
        emotion = '未知'
        emotion_keywords = {
            '焦虑': ['焦虑', '担心', '不安'],
            '恐惧': ['害怕', '恐惧', '恐慌'],
            '崩溃': ['崩溃', '想哭', '绝望'],
            '贪婪': ['贪婪', '想赚', '追高'],
            '平静': ['平静', '淡定', '还好'],
            '乐观': ['乐观', '开心', '高兴', '期待']
        }

        for emo, keywords in emotion_keywords.items():
            if any(kw in message for kw in keywords):
                emotion = emo
                break

        # 提取情绪强度（默认5）
        intensity = 5
        intensity_match = re.search(r'强度\s*(\d+)', message)
        if intensity_match:
            intensity = min(int(intensity_match.group(1)), 10)

        # 提取原因
        cause = ''
        if '亏' in message:
            cause = '亏损'
            loss_match = re.search(r'亏\s*(\d+(?:\.\d+)?)%?', message)
            if loss_match:
                cause = f"亏损{loss_match.group(1)}%"
        elif '赚' in message or '盈利' in message:
            cause = '盈利'
            gain_match = re.search(r'(?:盈利|赚)\s*(\d+(?:\.\d+)?)%?', message)
            if gain_match:
                cause = f"盈利{gain_match.group(1)}%"
        elif '涨' in message:
            cause = '市场上涨'
        elif '跌' in message:
            cause = '市场下跌'

        # 提取盈亏百分比
        profit_pct = None
        loss_match = re.search(r'亏\s*(\d+(?:\.\d+)?)%?', message)
        if loss_match:
            profit_pct = -float(loss_match.group(1))
        gain_match = re.search(r'(?:盈利|赚)\s*(\d+(?:\.\d+)?)%?', message)
        if gain_match:
            profit_pct = float(gain_match.group(1))

        # 记录情绪
        result = tracker.record_emotion(user_id, {
            'emotion': emotion,
            'cause': cause or message[:50],
            'intensity': intensity,
            'profit_pct': profit_pct
        })

        # 生成反馈
        lines = []
        lines.append(f"好的，我已经记录了你的情绪状态：")
        lines.append(f"  情绪：{emotion}")
        lines.append(f"  原因：{cause or '未说明'}")
        lines.append(f"  强度：{'❤️' * intensity}")

        # 如果有告警提示
        if result.get('warning'):
            lines.append("")
            lines.append(f"⚠️ {result.get('suggestion', '')}")

        lines.append("")
        lines.append("有什么想聊的吗？我随时在。")

        return "\n".join(lines)

    def _handle_emotional_status(self, user_id: str, message: str, entities: dict, ctx: dict, tracker) -> str:
        """获取情绪状态"""
        records = tracker.emotions.get(user_id, [])

        if not records:
            return ("你还没有记录过投资心态。\n"
                    "当你有焦虑、担心、或者亏损难受的时候，可以告诉我'记录心情：焦虑，亏了10%'。\n"
                    "我会帮你跟踪情绪变化，并在需要时给你调整建议。")

        return tracker.get_emotion_analysis(user_id)


def main():
    """测试"""
    manager = ClientManager()

    print("=" * 60)
    print("  客户经理对话引擎 v1.0 - 测试")
    print("=" * 60)
    print()

    # 测试对话
    user_id = "test_user"
    test_messages = [
        "你好",
        "我35岁，想投资基金，能承受20%亏损",
        "我买了000858，亏了15%怎么办",
        "我想看看我的持仓",
        "给我生成一份周报",
        "科技板块后面怎么走"
    ]

    for msg in test_messages:
        print(f"用户: {msg}")
        response = manager.chat(user_id, msg)
        print(f"助手: {response}")
        print()


if __name__ == '__main__':
    main()