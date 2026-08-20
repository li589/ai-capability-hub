"""
MiroFish 本地图谱包 - v2.1.0

完全本地运行的轻量图谱实现（Zep Cloud 的本地替代品）。
仅依赖 stdlib sqlite3 + jieba（可选），零外部服务、零数据外传。

用法：
    from mirofish.core.zep_local import ZepLocalGraph
    graph = ZepLocalGraph()
    graph.build_from_messages(messages)
    print(graph.get_stats())
"""

import sys
sys.dont_write_bytecode = True

from mirofish.core.zep_local import ZepLocalGraph

__version__ = "2.1.0"

__all__ = ["ZepLocalGraph"]
