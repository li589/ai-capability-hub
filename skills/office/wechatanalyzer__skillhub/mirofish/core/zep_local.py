"""
ZepLocalGraph - 本地轻量图谱引擎（v2.1.0）

README/SKILL.md 中宣传的"本地图谱"功能的落地实现，
替代 Zep Cloud，完全离线运行：

- 实体（entities）：消息发送者（person）+ jieba 抽取的高频关键词（keyword）
- 关系（relations）：同一消息/对话窗口内实体共现（mentions / co_occurs）
- 记忆（memories）：消息文本摘要（按内容哈希去重，重复 build 幂等）

仅使用 stdlib sqlite3 + 项目内 core.utils（jieba 可选），零新增依赖。
"""

import hashlib
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.message import Message
from core.utils import tokenize
from core.data_paths import resolve_graph_db_path


# 单条消息最多抽取的关键词数
MAX_KEYWORDS_PER_MESSAGE = 5
# 关键词最小长度（过滤单字噪音）
MIN_KEYWORD_LEN = 2
# 记忆摘要最大长度
MAX_SUMMARY_LEN = 80


class ZepLocalGraph:
    """本地 SQLite 图谱

    Args:
        db_path: 数据库文件路径，默认 <项目根>/data/mirofish_graph.db
    """

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            db_path = str(resolve_graph_db_path())
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    # ---------- 内部 ----------

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with closing(self._connect()) as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS entities (
                    name  TEXT NOT NULL,
                    type  TEXT NOT NULL,
                    count INTEGER NOT NULL DEFAULT 0,
                    PRIMARY KEY (name, type)
                );
                CREATE TABLE IF NOT EXISTS relations (
                    source TEXT NOT NULL,
                    target TEXT NOT NULL,
                    type   TEXT NOT NULL,
                    weight INTEGER NOT NULL DEFAULT 0,
                    PRIMARY KEY (source, target, type)
                );
                CREATE TABLE IF NOT EXISTS memories (
                    hash      TEXT PRIMARY KEY,
                    sender    TEXT,
                    summary   TEXT,
                    timestamp TEXT
                );
                """
            )
            conn.commit()

    @staticmethod
    def _memory_hash(msg: Message) -> str:
        """消息内容哈希（用于幂等去重）"""
        ts = msg.timestamp.isoformat() if msg.timestamp else ""
        raw = f"{msg.sender}|{ts}|{msg.content}"
        return hashlib.sha1(raw.encode("utf-8")).hexdigest()

    @staticmethod
    def _extract_keywords(content: str) -> List[str]:
        """从单条消息中抽取高频关键词（jieba 分词，过滤停用词/单字）"""
        if not content:
            return []
        counts: Dict[str, int] = {}
        for token in tokenize(content, use_jieba=True):
            token = token.strip()
            if len(token) < MIN_KEYWORD_LEN:
                continue
            counts[token] = counts.get(token, 0) + 1
        # 词频降序，取前 N 个
        return [
            w for w, _ in sorted(counts.items(), key=lambda x: (-x[1], x[0]))
            [:MAX_KEYWORDS_PER_MESSAGE]
        ]

    @staticmethod
    def _summarize(content: str) -> str:
        """消息文本摘要（截断）"""
        text = " ".join((content or "").split())
        if len(text) > MAX_SUMMARY_LEN:
            return text[:MAX_SUMMARY_LEN] + "..."
        return text

    def _upsert_entity(self, conn: sqlite3.Connection, name: str, etype: str) -> None:
        conn.execute(
            """
            INSERT INTO entities (name, type, count) VALUES (?, ?, 1)
            ON CONFLICT(name, type) DO UPDATE SET count = count + 1
            """,
            (name, etype),
        )

    def _upsert_relation(self, conn: sqlite3.Connection,
                         source: str, target: str, rtype: str) -> None:
        conn.execute(
            """
            INSERT INTO relations (source, target, type, weight) VALUES (?, ?, ?, 1)
            ON CONFLICT(source, target, type) DO UPDATE SET weight = weight + 1
            """,
            (source, target, rtype),
        )

    # ---------- 公开接口 ----------

    def build_from_messages(self, messages: List[Message]) -> int:
        """从消息列表构建/增量更新图谱

        重复调用幂等：已存在的记忆按内容哈希跳过，
        实体计数与关系权重只随新增记忆更新，不会无限重复插入。

        Args:
            messages: core.message.Message 列表

        Returns:
            本次新增的记忆条数
        """
        added = 0
        with closing(self._connect()) as conn:
            for msg in messages:
                if not isinstance(msg, Message):
                    # 兼容 dict 输入
                    if isinstance(msg, dict):
                        msg = Message.from_dict(msg)
                    else:
                        continue
                if not msg.has_content():
                    continue

                mem_hash = self._memory_hash(msg)
                cursor = conn.execute(
                    """
                    INSERT OR IGNORE INTO memories (hash, sender, summary, timestamp)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        mem_hash,
                        msg.sender,
                        self._summarize(msg.content),
                        msg.timestamp.isoformat() if msg.timestamp else None,
                    ),
                )
                if cursor.rowcount == 0:
                    continue  # 已存在的记忆，跳过（幂等）
                added += 1

                # 实体：发送者 + 关键词
                sender_name = msg.sender or "unknown"
                self._upsert_entity(conn, sender_name, "person")
                keywords = self._extract_keywords(msg.content)
                for kw in keywords:
                    self._upsert_entity(conn, kw, "keyword")

                # 关系：发送者 --提及--> 关键词；关键词两两共现
                for kw in keywords:
                    self._upsert_relation(conn, sender_name, kw, "mentions")
                for i in range(len(keywords)):
                    for j in range(i + 1, len(keywords)):
                        a, b = sorted((keywords[i], keywords[j]))
                        self._upsert_relation(conn, a, b, "co_occurs")
            conn.commit()
        return added

    def get_stats(self) -> Dict[str, int]:
        """图谱统计：实体数 / 关系数 / 记忆数"""
        with closing(self._connect()) as conn:
            entities = conn.execute("SELECT COUNT(*) FROM entities").fetchone()[0]
            relations = conn.execute("SELECT COUNT(*) FROM relations").fetchone()[0]
            memories = conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
        return {"entities": entities, "relations": relations, "memories": memories}

    def get_graph(self) -> Dict[str, List[Dict[str, Any]]]:
        """导出图谱数据

        Returns:
            {
                "entities": [{"name": str, "type": str, "count": int}, ...],
                "relations": [{"source": str, "target": str, "type": str, "weight": int}, ...],
            }
        """
        with closing(self._connect()) as conn:
            entities = [
                {"name": row["name"], "type": row["type"], "count": row["count"]}
                for row in conn.execute(
                    "SELECT name, type, count FROM entities ORDER BY count DESC"
                )
            ]
            relations = [
                {
                    "source": row["source"],
                    "target": row["target"],
                    "type": row["type"],
                    "weight": row["weight"],
                }
                for row in conn.execute(
                    "SELECT source, target, type, weight FROM relations ORDER BY weight DESC"
                )
            ]
        return {"entities": entities, "relations": relations}

    def clear(self) -> None:
        """清空图谱（调试用）"""
        with closing(self._connect()) as conn:
            conn.executescript(
                "DELETE FROM entities; DELETE FROM relations; DELETE FROM memories;"
            )
            conn.commit()
