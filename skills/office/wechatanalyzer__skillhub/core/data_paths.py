"""
运行时数据路径解析（v2.6.0）

所有运行时持久化数据（SQLite 数据库等）默认放到系统 tempdir，
避免在 skill 包内生成二进制文件导致上传/同步被拒（与 .pyc 同类问题）。

可通过环境变量覆盖：
    WECHAT_ANALYZER_DATA_DIR    运行时数据根目录（默认 tempdir/wechat-analyzer）

优先级（以聊天历史 DB 为例）：
    1. config 里显式传入的「绝对路径」
    2. 环境变量 WECHAT_ANALYZER_DATA_DIR 下的 sessions/chat_history.db
    3. 系统 tempdir/wechat-analyzer/sessions/chat_history.db
"""

import os
import tempfile
from pathlib import Path

APP_NAME = "wechat-analyzer"


def resolve_data_dir() -> Path:
    """返回运行时数据根目录（默认 tempdir/wechat-analyzer）。"""
    env = os.environ.get("WECHAT_ANALYZER_DATA_DIR")
    if env:
        return Path(env)
    return Path(tempfile.gettempdir()) / APP_NAME


def resolve_db_path(config_db_path: str | None = None) -> Path:
    """解析聊天历史 DB 路径。

    仅当 config 传入「绝对路径」时使用之；相对路径（如
    ``data/sessions/chat_history.db``）一律忽略，改走 tempdir，
    避免在 skill 包内重新生成二进制数据库。
    """
    if config_db_path:
        p = Path(config_db_path)
        if p.is_absolute():
            return p
    return resolve_data_dir() / "sessions" / "chat_history.db"


def resolve_graph_db_path() -> Path:
    """解析本地图谱（ZepLocalGraph）DB 路径。"""
    return resolve_data_dir() / "mirofish_graph.db"
