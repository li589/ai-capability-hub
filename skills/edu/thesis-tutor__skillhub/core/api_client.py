#!/usr/bin/env python3
"""
用户配置管理 + DeepSeek API 集成
"""

import json
import os
import re
from pathlib import Path
from typing import Dict, Optional
from urllib import request, error
import socket


class UserConfig:
    """用户配置管理"""

    def __init__(self, user_id: str, config_dir: str = "./user_configs"):
        self.user_id = user_id
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.config_path = self.config_dir / f"{user_id}.json"
        self.config = self._load()

    def _load(self) -> Dict:
        """加载配置"""
        if self.config_path.exists():
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "api_key": None,
            "model": "deepseek-chat",
            "base_url": "https://api.deepseek.com/v1",
            "preferences": {
                "discipline": None,
                "subfield": None,
                "level": "bachelor",
                "language": "zh",
                "citation_format": "GB/T 7714"
            },
            "stats": {
                "total_conversations": 0,
                "api_calls": 0,
                "first_use": None,
                "last_use": None
            }
        }

    def save(self):
        """保存配置"""
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)

    def get(self, key: str, default=None):
        """获取配置项"""
        return self.config.get(key, default)

    def get_preference(self, key: str, default=None):
        """获取偏好设置"""
        return self.config.get("preferences", {}).get(key, default)

    def set_preference(self, key: str, value) -> None:
        """设置偏好设置"""
        self.config.setdefault("preferences", {})[key] = value
        self.save()

    def set_language(self, language: str) -> Dict:
        """
        设置语言偏好

        Args:
            language: 语言代码 (zh/en/ja/ko/de/fr/es)
        """
        supported_languages = ["zh", "en", "ja", "ko", "de", "fr", "es"]
        if language not in supported_languages:
            return {
                "success": False,
                "message": f"不支持的语言: {language}，支持的语言: {', '.join(supported_languages)}"
            }

        self.config.setdefault("preferences", {})["language"] = language
        self.save()
        return {
            "success": True,
            "message": f"语言已设置为: {language}"
        }

    def set_discipline(self, discipline: str, subfield: str = None) -> Dict:
        """
        设置学科偏好

        Args:
            discipline: 学科代码
            subfield: 学科细分方向（可选）
        """
        self.config.setdefault("preferences", {})["discipline"] = discipline
        if subfield:
            self.config["preferences"]["subfield"] = subfield
        self.save()
        return {
            "success": True,
            "message": f"学科已设置为: {discipline}"
        }

    def set_citation_format(self, format_name: str) -> Dict:
        """
        设置引用格式偏好

        Args:
            format_name: 引用格式名称 (GB/T 7714/APA 7th/MLA 9th/IEEE/Chicago/Vancouver)
        """
        supported_formats = ["GB/T 7714", "APA 7th",
                             "MLA 9th", "IEEE", "Chicago", "Vancouver"]
        if format_name not in supported_formats:
            return {
                "success": False,
                "message": f"不支持的引用格式: {format_name}，支持的格式: {', '.join(supported_formats)}"
            }

        self.config.setdefault("preferences", {})[
            "citation_format"] = format_name
        self.save()
        return {
            "success": True,
            "message": f"引用格式已设置为: {format_name}"
        }

    def set_api_key(self, api_key: str) -> Dict:
        """
        设置 API Key

        返回: {"success": True/False, "message": "...", "valid": True/False}
        """
        # 格式验证
        if not api_key.startswith("sk-"):
            return {
                "success": False,
                "message": "API Key 格式错误，应以 'sk-' 开头",
                "valid": False
            }

        # 可选：调用测试接口验证
        validation = self._validate_api_key(api_key)

        if validation["valid"]:
            self.config["api_key"] = api_key
            self.save()
            return {
                "success": True,
                "message": f" API Key 配置成功！{validation.get('info', '')}",
                "valid": True
            }
        else:
            return {
                "success": False,
                "message": f" API Key 验证失败：{validation['error']}",
                "valid": False
            }

    def _validate_api_key(self, api_key: str) -> Dict:
        """验证 API Key 是否有效"""
        try:
            payload = json.dumps({
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": "Hi"}],
                "max_tokens": 5
            }).encode('utf-8')

            req = request.Request(
                f"{self.config['base_url']}/chat/completions",
                data=payload,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                method="POST"
            )

            with request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    return {
                        "valid": True,
                        "info": "已连接到 DeepSeek API"
                    }
                else:
                    return {"valid": False, "error": f"HTTP {response.status}"}

        except error.HTTPError as e:
            if e.code == 401:
                return {"valid": False, "error": "API Key 无效或已过期"}
            elif e.code == 429:
                return {"valid": False, "error": "请求过于频繁，请稍后再试"}
            else:
                return {"valid": False, "error": f"HTTP {e.code}"}
        except error.URLError:
            return {"valid": False, "error": "网络连接失败，请检查网络"}
        except socket.timeout:
            return {"valid": False, "error": "连接超时，请检查网络"}
        except Exception as e:
            return {"valid": False, "error": f"验证异常: {str(e)}"}

    def has_api_key(self) -> bool:
        """检查是否配置了 API Key"""
        return bool(self.config.get("api_key"))

    def get_api_key(self) -> Optional[str]:
        """获取 API Key"""
        return self.config.get("api_key")

    def remove_api_key(self):
        """移除 API Key"""
        self.config["api_key"] = None
        self.save()

    def update_stats(self, api_call: bool = False):
        """更新使用统计"""
        from datetime import datetime

        now = datetime.now().isoformat()

        if not self.config["stats"]["first_use"]:
            self.config["stats"]["first_use"] = now

        self.config["stats"]["last_use"] = now
        self.config["stats"]["total_conversations"] += 1

        if api_call:
            self.config["stats"]["api_calls"] += 1

        self.save()

    def get_stats(self) -> Dict:
        """获取使用统计"""
        return self.config["stats"]


class DeepSeekClient:
    """DeepSeek API 客户端"""

    def __init__(self, api_key: str, base_url: str = "https://api.deepseek.com/v1"):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    def chat(self,
             messages: list,
             model: str = "deepseek-chat",
             temperature: float = 0.7,
             max_tokens: int = 2000,
             system_prompt: str = None) -> Dict:
        """
        调用 DeepSeek 聊天接口

        返回: {
            "success": True/False,
            "content": "回复内容",
            "usage": {"prompt_tokens": ..., "completion_tokens": ...},
            "error": "错误信息（如果有）"
        }
        """
        if system_prompt:
            messages.insert(0, {
                "role": "system",
                "content": system_prompt
            })

        payload = json.dumps({
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }).encode('utf-8')

        req = request.Request(
            f"{self.base_url}/chat/completions",
            data=payload,
            headers=self.headers,
            method="POST"
        )

        try:
            with request.urlopen(req, timeout=60) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode('utf-8'))
                    return {
                        "success": True,
                        "content": data["choices"][0]["message"]["content"],
                        "usage": data.get("usage", {}),
                        "error": None
                    }
                else:
                    return {
                        "success": False,
                        "content": None,
                        "usage": {},
                        "error": f"HTTP {response.status}"
                    }

        except error.HTTPError as e:
            if e.code == 401:
                return {
                    "success": False,
                    "content": None,
                    "usage": {},
                    "error": "API Key 无效，请重新配置"
                }
            elif e.code == 429:
                return {
                    "success": False,
                    "content": None,
                    "usage": {},
                    "error": "请求过于频繁，请稍后再试"
                }
            elif e.code == 402:
                return {
                    "success": False,
                    "content": None,
                    "usage": {},
                    "error": "API 余额不足，请充值"
                }
            else:
                return {
                    "success": False,
                    "content": None,
                    "usage": {},
                    "error": f"API 错误: HTTP {e.code}"
                }
        except error.URLError:
            return {
                "success": False,
                "content": None,
                "usage": {},
                "error": "网络连接失败，请检查网络"
            }
        except socket.timeout:
            return {
                "success": False,
                "content": None,
                "usage": {},
                "error": "请求超时，请检查网络或稍后重试"
            }
        except Exception as e:
            return {
                "success": False,
                "content": None,
                "usage": {},
                "error": f"请求异常: {str(e)}"
            }

    def analyze_paper(self, text: str, context: str = "") -> Dict:
        """
        分析论文段落（专用接口）
        """
        system_prompt = """你是一位严格的论文导师，擅长学术写作指导。

任务：对学生提供的论文段落进行深度分析。

要求：
1. 结构分析：段落安排、逻辑顺序、过渡衔接
2. 论证分析：论据充分性、因果逻辑、概念准确性
3. 表述分析：学术用语、语法规范、冗余度
4. 给出具体修改建议（提供修改前后的对比示例）
5. 推荐相关文献方向（如适用）

原则：
- 不要直接代写，而是给出修改框架和方向
- 指出具体问题位置
- 保持学术规范
- 中文回复"""

        user_prompt = f"""请分析以下论文段落：

{text}

{context}

请从结构、论证、表述三个维度进行分析，并给出具体修改建议。"""

        return self.chat(
            messages=[{"role": "user", "content": user_prompt}],
            system_prompt=system_prompt,
            temperature=0.7,
            max_tokens=2500
        )

    def suggest_topics(self, discipline: str, level: str, interests: str = "") -> Dict:
        """
        推荐选题（专用接口）
        """
        system_prompt = """你是一位资深的论文导师，擅长帮助学生找到有价值的选题。

任务：根据学生的专业、学位级别和兴趣方向，推荐 3-5 个选题。

要求：
1. 每个选题包含：题目、研究问题、研究方法、创新点、难度评估
2. 评估维度：创新性、可行性、资料可得性、导师接受度
3. 给出选题避坑指南
4. 中文回复"""

        user_prompt = f"""请为以下学生推荐选题：

专业：{discipline}
学位级别：{level}
兴趣方向：{interests or "暂无具体方向"}

请推荐 3-5 个选题，并评估每个选题的可行性。"""

        return self.chat(
            messages=[{"role": "user", "content": user_prompt}],
            system_prompt=system_prompt,
            temperature=0.8,
            max_tokens=2000
        )

    def handle_feedback(self, feedback: str, paper_context: str = "") -> Dict:
        """
        处理导师反馈（专用接口）
        """
        system_prompt = """你是一位经验丰富的论文导师，擅长帮助学生理解和回应导师反馈。

任务：分析导师的反馈，给出具体的修改策略。

要求：
1. 识别反馈类型（内容/结构/方法/格式/语言）
2. 给出修改优先级排序
3. 提供具体修改步骤
4. 给出回应导师的话术建议
5. 中文回复"""

        user_prompt = f"""导师反馈："{feedback}"

论文背景：{paper_context or "暂无"}

请分析这条反馈的含义，并给出修改策略。"""

        return self.chat(
            messages=[{"role": "user", "content": user_prompt}],
            system_prompt=system_prompt,
            temperature=0.7,
            max_tokens=2000
        )


if __name__ == "__main__":
    # 测试配置管理
    config = UserConfig("test_user")

    print("=== 测试配置管理 ===")
    print(f"初始状态 - 有 API Key: {config.has_api_key()}")

    # 测试设置 API Key（使用假 Key，预期失败）
    result = config.set_api_key("<YOUR_API_KEY>")
    print(f"设置假 Key: {result}")

    # 测试统计
    config.update_stats(api_call=False)
    print(f"统计: {config.get_stats()}")

    print("\n=== 测试完成 ===")
