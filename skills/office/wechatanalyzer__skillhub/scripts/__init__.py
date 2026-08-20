"""
微信聊天分析助手 - scripts 包

v2.0.0 保留 v1.2.0 的所有脚本文件以保证向后兼容。

子模块：
- main: CLI 入口
- main_setup: 一键配置
- text_analyzer: 旧版规则分析器（v1.2.0，向后兼容）
- conversation_predictor: 旧版对话预测器（v1.2.0）
- llm_analyzer: LLM 增强（可选）
- report_generator: 报告生成
- data_manager: 数据存储
- file_importer: 多格式导入
- calendar_manager: 日历事件
- scheduler: 定时任务
- web_server: Web 服务
- mirofish: MiroFish 高级功能（可选）
- archive_v1: v1.2.0 完整快照
"""

import sys
sys.dont_write_bytecode = True

__version__ = "2.1.0"
