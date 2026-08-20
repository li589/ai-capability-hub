"""MiroFish 核心模块"""

import sys
sys.dont_write_bytecode = True

from mirofish.core.zep_local import ZepLocalGraph

__all__ = ["ZepLocalGraph"]
