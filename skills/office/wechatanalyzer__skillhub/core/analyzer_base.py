"""
分析器抽象基类

所有分析器（MBTI、大五、情感、风险等）必须继承 AnalyzerBase，
保证接口一致，方便 AnalyzerRegistry 统一调度。
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import time

from core.message import Message
from core.result import AnalysisResult


class AnalyzerBase(ABC):
    """分析器抽象基类

    子类需实现：
        - name: 唯一标识
        - analyze(): 核心分析逻辑
        - validate(): 前置校验

    可选重写：
        - get_confidence(): 置信度计算
        - get_summary(): 人类可读摘要
    """

    # 子类必须设置
    name: str = "base"
    version: str = "2.2.0"
    description: str = ""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

    @abstractmethod
    def analyze(self, messages: List[Message], **kwargs) -> AnalysisResult:
        """执行分析

        Args:
            messages: 消息列表
            **kwargs: 分析器特定参数

        Returns:
            AnalysisResult
        """
        pass

    @abstractmethod
    def validate(self, messages: List[Message]) -> bool:
        """前置校验：消息数量、格式等是否满足要求

        Returns:
            True 表示可分析，False 表示跳过
        """
        pass

    def get_confidence(self, result: AnalysisResult) -> float:
        """获取置信度（默认直接返回 result.confidence）"""
        return result.confidence

    def get_summary(self, result: AnalysisResult) -> str:
        """人类可读摘要（默认由 details 拼装）"""
        return f"[{self.name}] score={result.score}, confidence={result.confidence}"

    def _measure_time(self, func, *args, **kwargs):
        """带耗时测量的执行包装"""
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        if isinstance(result, AnalysisResult):
            result.metadata.setdefault("elapsed_seconds", round(elapsed, 4))
        return result


class AnalyzerRegistry:
    """分析器注册中心

    用于统一调度多个分析器，避免在 main.py 中硬编码。
    用法：
        registry = AnalyzerRegistry()
        registry.register(MBTIAnalyzer(config))
        registry.register(SentimentAnalyzer(config))
        results = registry.run_all(messages)
    """

    def __init__(self):
        self._analyzers: Dict[str, AnalyzerBase] = {}

    def register(self, analyzer: AnalyzerBase) -> None:
        """注册一个分析器"""
        if not isinstance(analyzer, AnalyzerBase):
            raise TypeError(f"Expected AnalyzerBase, got {type(analyzer)}")
        if analyzer.name in self._analyzers:
            raise ValueError(f"Analyzer '{analyzer.name}' already registered")
        self._analyzers[analyzer.name] = analyzer

    def unregister(self, name: str) -> None:
        """注销"""
        self._analyzers.pop(name, None)

    def get(self, name: str) -> Optional[AnalyzerBase]:
        """获取分析器"""
        return self._analyzers.get(name)

    def list(self) -> List[str]:
        """列出所有已注册分析器"""
        return list(self._analyzers.keys())

    def run_all(self, messages: List[Message], skip_invalid: bool = True,
                progress_callback=None) -> Dict[str, AnalysisResult]:
        """运行所有分析器

        Args:
            messages: 消息列表
            skip_invalid: 校验失败的分析器是否跳过（默认 True）
            progress_callback: 可选进度回调（v2.1.0 新增），签名为
                callback(event, name, index, total, elapsed)
                event 为 "start" / "done" / "skip" / "error"，
                elapsed 仅在 "done" 时有意义（秒）

        Returns:
            {analyzer_name: AnalysisResult}
        """
        results: Dict[str, AnalysisResult] = {}
        total = len(self._analyzers)
        for index, (name, analyzer) in enumerate(self._analyzers.items(), 1):
            if progress_callback:
                progress_callback("start", name, index, total, 0.0)
            start = time.time()
            try:
                if not analyzer.validate(messages):
                    if skip_invalid:
                        if progress_callback:
                            progress_callback(
                                "skip", name, index, total, time.time() - start)
                        continue
                    else:
                        raise ValueError(f"Validation failed for {name}")
                result = analyzer.analyze(messages)
                results[name] = result
                if progress_callback:
                    progress_callback("done", name, index, total, time.time() - start)
            except Exception as e:
                # 记录错误但不中断其他分析器
                results[name] = AnalysisResult(
                    analyzer_name=name,
                    score=0.0,
                    confidence=0.0,
                    details={"error": str(e)},
                    metadata={"status": "failed"},
                )
                if progress_callback:
                    progress_callback("error", name, index, total, time.time() - start)
        return results

    def run_one(self, name: str, messages: List[Message], **kwargs) -> AnalysisResult:
        """运行单个分析器"""
        if name not in self._analyzers:
            raise KeyError(f"Analyzer '{name}' not registered")
        analyzer = self._analyzers[name]
        if not analyzer.validate(messages):
            raise ValueError(f"Validation failed for {name}")
        return analyzer.analyze(messages, **kwargs)
