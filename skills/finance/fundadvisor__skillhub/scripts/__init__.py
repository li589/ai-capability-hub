"""fund-advisor scripts package — 让 scripts/ 可作为 Python 包导入

历史原因：fund-advisor 长期作为脚本目录直接 sys.path.insert 使用；
补齐 __init__.py 后即可作为正常包被外部 import 与打包工具识别。
"""
import sys
sys.dont_write_bytecode = True

__version__ = "8.0.0"
