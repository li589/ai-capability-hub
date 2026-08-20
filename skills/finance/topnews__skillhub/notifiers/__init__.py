from __future__ import annotations

import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class BaseNotifier(ABC):
    @abstractmethod
    async def send(self, content: str) -> bool:
        ...


class ConsoleNotifier(BaseNotifier):
    async def send(self, content: str) -> bool:
        import sys
        import io
        if hasattr(sys.stdout, 'reconfigure'):
            try:
                sys.stdout.reconfigure(encoding='utf-8')
            except Exception:
                pass
        try:
            print(content)
        except UnicodeEncodeError:
            safe = content.encode('utf-8', errors='replace').decode('utf-8')
            print(safe)
        return True


class FileNotifier(BaseNotifier):
    def __init__(self, output_dir: str = "reports"):
        self.output_dir = output_dir

    async def send(self, content: str) -> bool:
        import os
        from datetime import datetime

        os.makedirs(self.output_dir, exist_ok=True)
        filename = datetime.now().strftime("%Y-%m-%d_morning_brief.txt")
        filepath = os.path.join(self.output_dir, filename)
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            logger.info("简报已保存到 %s", filepath)
            return True
        except Exception as e:
            logger.error("保存简报失败: %s", e)
            return False
