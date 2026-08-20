#!/usr/bin/env python3
"""
Thesis Tutor v4.0 - 主路由
整合本地助手 + DeepSeek API + 多轮对话
"""

from core.api_client import UserConfig, DeepSeekClient
from core.local_assistant import LocalAssistant, KnowledgeBase, IntentMatcher, ConversationContext
import sys
import json
import re
from pathlib import Path
from typing import Dict, List, Optional

# 添加 core 到路径
sys.path.insert(0, str(Path(__file__).parent / "core"))


class ThesisTutor:
    """论文导师主类"""

    def __init__(self, knowledge_base_path: str = None):
        """初始化"""
        # 知识库路径
        if knowledge_base_path is None:
            knowledge_base_path = Path(__file__).parent / "knowledge_base"

        # 初始化组件
        self.kb = KnowledgeBase(str(knowledge_base_path))
        self.assistant = LocalAssistant(self.kb)
        self.config = UserConfig("default_user")

        # API 客户端（按需初始化）
        self.api_client = None
        if self.config.has_api_key():
            self.api_client = DeepSeekClient(self.config.get_api_key())

    def chat(self, user_input: str) -> Dict:
        """
        主对话入口

        返回: {
            "response": "回复内容",
            "type": "意图类型",
            "confidence": 置信度,
            "suggestions": ["建议"],
            "need_advanced": 是否需要高级AI,
            "context": 上下文信息,
            "used_api": 是否使用了API
        }
        """
        # 1. 检查是否是配置命令
        if self._is_config_command(user_input):
            return self._handle_config(user_input)

        # 2. 本地处理
        # 传递语言和学科信息
        user_context = {
            "language": self.config.get_preference("language", "zh"),
            "discipline": self.config.get_preference("discipline", "")
        }
        result = self.assistant.handle(user_input, user_context)

        # 3. 判断是否需要高级AI
        if result.get("need_advanced") and self.api_client:
            # 使用 DeepSeek API 进行深度分析
            api_response = self._call_api(user_input, result)
            if api_response:
                result["response"] = api_response
                result["used_api"] = True
            else:
                result["used_api"] = False
        else:
            result["used_api"] = False

        return result

    def _is_config_command(self, text: str) -> bool:
        """检查是否是配置命令"""
        config_patterns = [
            r"^\s*配置\s*",
            r"^\s*设置\s*",
            r"^\s*api\s*key\s*[:\uff1a]",
            r"^\s*key\s*[:\uff1a]",
            r"^\s*密钥\s*[:\uff1a]",
            r"^\s*configure\s+api\s+key\s*[:\s]",
            r"^\s*remove\s+api\s+key\s*$",
            r"^\s*删除\s*(api\s*)?key\s*$",
            r"^\s*移除\s*(api\s*)?key\s*$",
            r"^\s*check\s+(api\s*)?status\s*$",
            r"^\s*检查\s*(api\s*)?(状态|连接)\s*$",
            r"^\s*api\s*状态\s*$",
            r"^\s*switch\s+language\s+to\s+(\w+)\s*$",
            r"^\s*切换\s*语言\s*(到|为|成)?\s*(\w+)\s*$",
            r"^\s*help\s*$",
            r"^\s*帮助\s*$",
            r"^\s*帮助信息\s*$",
        ]
        for pattern in config_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

    def _handle_config(self, text: str) -> Dict:
        """处理配置命令"""
        text_lower = text.strip().lower()

        # 处理 Remove API Key
        if re.match(r"^\s*(remove\s+api\s+key|删除\s*(api\s*)?key|移除\s*(api\s*)?key)\s*$", text_lower):
            self.config.remove_api_key()
            self.api_client = None
            return {
                "response": "✅ API Key 已移除。\n\n你现在将使用本地引擎进行论文辅导。如需深度分析，可重新配置 API Key。",
                "type": "config",
                "confidence": 1.0,
                "suggestions": ["配置新 API Key", "开始论文辅导"],
                "need_advanced": False,
                "used_api": False
            }

        # 处理 Check API Status
        if re.match(r"^\s*(check\s+(api\s*)?status|检查\s*(api\s*)?(状态|连接)|api\s*状态)\s*$", text_lower):
            has_key = self.config.has_api_key()
            if has_key:
                return {
                    "response": "✅ API 状态：已配置\n- 本地引擎：可用\n- API 引擎：可用\n\n你已解锁深度分析功能！",
                    "type": "config",
                    "confidence": 1.0,
                    "suggestions": ["测试 API", "开始论文辅导"],
                    "need_advanced": False,
                    "used_api": False
                }
            else:
                return {
                    "response": "⚠️ API 状态：未配置\n- 本地引擎：可用\n- API 引擎：未激活\n\n配置 API Key 可解锁深度分析功能。\n输入：Configure API Key: <YOUR_API_KEY>",
                    "type": "config",
                    "confidence": 1.0,
                    "suggestions": ["配置 API Key", "使用本地引擎"],
                    "need_advanced": False,
                    "used_api": False
                }

        # 处理 Switch Language
        lang_match = re.match(
            r"^\s*(switch\s+language\s+to\s+(\w+)|切换\s*语言\s*(到|为|成)?\s*(\w+))\s*$", text_lower)
        if lang_match:
            lang = (lang_match.group(2) or lang_match.group(4) or "").lower()
            lang_map = {
                "chinese": "zh", "中文": "zh", "zh": "zh",
                "english": "en", "英文": "en", "en": "en",
                "japanese": "ja", "日语": "ja", "日文": "ja", "ja": "ja",
                "korean": "ko", "韩语": "ko", "韩文": "ko", "ko": "ko",
                "french": "fr", "法语": "fr", "法文": "fr", "fr": "fr",
                "german": "de", "德语": "de", "德文": "de", "de": "de",
                "spanish": "es", "西班牙语": "es", "es": "es"
            }
            target_lang = lang_map.get(lang)
            if target_lang:
                self.config.set_preference("language", target_lang)
                lang_names = {"zh": "中文", "en": "English", "ja": "日本語",
                              "ko": "한국어", "fr": "Français", "de": "Deutsch", "es": "Español"}
                return {
                    "response": f"✅ 语言已切换为：{lang_names.get(target_lang, target_lang)}\n\n现在我将用{lang_names.get(target_lang, target_lang)}为你提供论文辅导。",
                    "type": "config",
                    "confidence": 1.0,
                    "suggestions": ["开始论文辅导", "查看帮助"],
                    "need_advanced": False,
                    "used_api": False
                }
            else:
                return {
                    "response": "❌ 不支持的语言。\n\n支持的语言：\n- Chinese / 中文\n- English / 英文\n- Japanese / 日语\n- Korean / 韩语\n- French / 法语\n- German / 德语\n- Spanish / 西班牙语\n\n示例：Switch language to English",
                    "type": "config",
                    "confidence": 1.0,
                    "suggestions": ["切换到中文", "切换到英文"],
                    "need_advanced": False,
                    "used_api": False
                }

        # 处理 Help
        if re.match(r"^\s*(help|帮助|帮助信息)\s*$", text_lower):
            return {
                "response": "📚 Thesis Tutor 使用指南\n\n【基本功能】\n直接输入论文问题即可获得辅导\n\n【命令列表】\n- Configure API Key: <YOUR_API_KEY>  设置API Key\n- Remove API Key           移除API Key\n- Check API Status         检查API状态\n- Switch language to xx     切换语言\n- Help                     显示此帮助\n\n【支持语言】\n中文、English、日本語、한국어、Français、Deutsch、Español\n\n【支持学科】\n计算机、经济学、教育学、工程学、法学、文学、管理学、医学、心理学、艺术学、理学、农学、图书馆学、考古学、体育学\n\n试试问我：如何选择论文题目？",
                "type": "config",
                "confidence": 1.0,
                "suggestions": ["选择论文题目", "配置 API Key", "切换语言"],
                "need_advanced": False,
                "used_api": False
            }

        # 提取 API Key
        key_match = re.search(r"(?:sk-[a-zA-Z0-9]+)", text)

        if key_match:
            api_key = key_match.group(0)
            result = self.config.set_api_key(api_key)

            if result["success"]:
                # 初始化 API 客户端
                self.api_client = DeepSeekClient(api_key)

                return {
                    "response": result["message"] + "\n\n你现在可以：\n- 获得深度逻辑分析\n- 获得精准论证评估\n- 获得个性化学术建议\n\n试试粘贴一段论文内容？",
                    "type": "config",
                    "confidence": 1.0,
                    "suggestions": ["粘贴论文段落", "问学术问题"],
                    "need_advanced": False,
                    "used_api": False
                }
            else:
                return {
                    "response": result["message"] + "\n\n请检查 API Key 是否正确，或稍后重试。",
                    "type": "config",
                    "confidence": 1.0,
                    "suggestions": ["重新配置", "跳过配置"],
                    "need_advanced": False,
                    "used_api": False
                }
        else:
            return {
                "response": "请输入有效的 API Key（以 sk- 开头）。\n\n获取方式：\n1. 访问 https://platform.deepseek.com\n2. 注册账号\n3. 创建 API Key\n4. 复制以 sk- 开头的密钥\n\n示例：配置 API Key: <YOUR_API_KEY>",
                "type": "config",
                "confidence": 1.0,
                "suggestions": ["如何获取 API Key", "跳过配置"],
                "need_advanced": False,
                "used_api": False
            }

    def _call_api(self, user_input: str, local_result: Dict) -> Optional[str]:
        """调用 DeepSeek API 进行深度分析"""
        if not self.api_client:
            return None

        try:
            # 构建提示词
            context = local_result.get("context", {})
            discipline = context.get("discipline", "未知")
            level = context.get("level", "未知")
            stage = context.get("stage", "未知")

            prompt = f"""你是一位专业的学术论文导师，正在指导一位{level}{discipline}专业的学生。

学生当前阶段：{stage}
学生输入：{user_input}

本地分析结果：
- 意图类型：{local_result['type']}
- 置信度：{local_result['confidence']}
- 检测到问题数：{local_result.get('issues_count', 0)}

请提供深度、专业的学术指导。要求：
1. 分析深入，不仅指出问题，还要解释原因
2. 提供具体修改建议，给出修改前后的对比示例
3. 引用相关学术规范或方法论原则
4. 保持鼓励性语气，但要求严谨
5. 如果涉及专业知识，确保准确性

直接回复学生，不需要称呼。"""

            response = self.api_client.chat(prompt)
            return response

        except Exception as e:
            return f"[API 分析出错: {str(e)}]\n\n本地分析结果：\n{local_result['response']}"

    def get_status(self) -> Dict:
        """获取系统状态"""
        return {
            "version": "4.0.0",
            "local_engine": "就绪",
            "api_status": "已配置" if self.api_client else "未配置",
            "knowledge_base": str(self.kb.base_path),
            "context": self.assistant.context.get_all_state()
        }


# 兼容旧版 CLI
class ThesisTutorCLI:
    """命令行界面"""

    def __init__(self):
        self.tutor = ThesisTutor()

    def run(self):
        """运行交互式对话"""
        print("=" * 60)
        print("论文写作助手 v4.0")
        print("=" * 60)
        print("输入 'quit' 或 '退出' 结束对话")
        print("输入 'status' 查看状态")
        print("-" * 60)

        # 首次问候
        result = self.tutor.chat("你好")
        print(f"\n助手: {result['response']}\n")

        while True:
            try:
                user_input = input("你: ").strip()

                if not user_input:
                    continue

                if user_input.lower() in ["quit", "exit", "退出", "结束"]:
                    print("\n助手: 再见！论文写作顺利！")
                    break

                if user_input.lower() == "status":
                    status = self.tutor.get_status()
                    print(
                        f"\n状态: {json.dumps(status, ensure_ascii=False, indent=2)}\n")
                    continue

                # 处理输入
                result = self.tutor.chat(user_input)

                # 显示回复
                print(f"\n助手: {result['response']}\n")

                # 显示建议
                if result.get("suggestions"):
                    print(f"建议: {' | '.join(result['suggestions'])}\n")

                # 显示是否使用了API
                if result.get("used_api"):
                    print("[使用了 DeepSeek API 深度分析]\n")

            except KeyboardInterrupt:
                print("\n\n助手: 再见！")
                break
            except Exception as e:
                print(f"\n[错误: {str(e)}]\n")


if __name__ == "__main__":
    # 如果有命令行参数，直接处理
    if len(sys.argv) > 1:
        input_text = " ".join(sys.argv[1:])
        tutor = ThesisTutor()
        result = tutor.chat(input_text)
        print(result["response"])
    else:
        # 交互模式
        cli = ThesisTutorCLI()
        cli.run()
