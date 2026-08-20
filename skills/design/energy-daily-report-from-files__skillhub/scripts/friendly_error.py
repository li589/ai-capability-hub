#!/usr/bin/env python3
"""Convert Python exceptions into concise, actionable Chinese guidance."""

from __future__ import annotations

import csv
import errno
import json
import sqlite3
import subprocess
import zipfile


def describe_error(exc: BaseException) -> dict[str, str]:
    """Return a stable code, plain-language cause and next action."""
    message = str(exc)
    folded = message.casefold()

    if isinstance(exc, FileNotFoundError):
        return {
            "code": "FILE_NOT_FOUND",
            "message": "找不到需要的文件或程序。",
            "action": "确认路径和文件名；若文件刚下载，请先完整解压后重试。",
        }
    if isinstance(exc, PermissionError) or (
        isinstance(exc, OSError) and getattr(exc, "winerror", None) in {5, 32, 33}
    ):
        return {
            "code": "FILE_LOCKED_OR_DENIED",
            "message": "文件可能正被 Excel、WPS、同步软件占用，或当前目录不可写。",
            "action": "关闭占用程序，换到有写入权限的目录，然后重试。",
        }
    if isinstance(exc, UnicodeError):
        return {
            "code": "TEXT_ENCODING_UNSUPPORTED",
            "message": "文件文字编码无法识别。",
            "action": "用原软件另存为 UTF-8、UTF-8 BOM 或 GB18030 后重试。",
        }
    if isinstance(exc, json.JSONDecodeError):
        return {
            "code": "JSON_INVALID",
            "message": "配置文件格式不完整或已损坏。",
            "action": "检查错误位置附近的逗号、引号和括号，或从模板重新生成。",
        }
    if isinstance(exc, zipfile.BadZipFile):
        return {
            "code": "ZIP_CORRUPT",
            "message": "压缩包已损坏或不是真正的 ZIP 文件。",
            "action": "从原始来源重新获取，或用压缩软件重新打包后重试。",
        }
    if isinstance(exc, sqlite3.DatabaseError):
        return {
            "code": "DATABASE_ERROR",
            "message": "数据库无法安全读取或写入。",
            "action": "停止继续写入，保留故障文件，并从最近备份恢复。",
        }
    if isinstance(exc, subprocess.TimeoutExpired):
        return {
            "code": "OPERATION_TIMEOUT",
            "message": "操作等待时间过长，已安全停止。",
            "action": "检查网络或磁盘状态；依赖安装可改用已校验的离线 wheels。",
        }
    if isinstance(exc, MemoryError):
        return {
            "code": "MEMORY_INSUFFICIENT",
            "message": "可用内存不足。",
            "action": "关闭其他程序，拆分大文件，再从原步骤继续。",
        }
    if isinstance(exc, OSError) and getattr(exc, "errno", None) == errno.ENOSPC:
        return {
            "code": "DISK_FULL",
            "message": "磁盘可用空间不足。",
            "action": "清理空间或更换输出目录后重试。",
        }
    if isinstance(exc, (ImportError, ModuleNotFoundError)):
        return {
            "code": "DEPENDENCY_MISSING",
            "message": "缺少完成当前步骤所需的 Python 组件。",
            "action": "运行统一依赖安装脚本；离线环境请使用带哈希清单的 wheels。",
        }
    if isinstance(exc, csv.Error):
        return {
            "code": "DELIMITED_FORMAT_INVALID",
            "message": "CSV 或 TSV 的分隔符、引号或换行格式不兼容。",
            "action": "用 Excel 或 WPS 打开并重新另存为 CSV UTF-8。",
        }
    if any(
        marker in folded
        for marker in (
            "timeout", "timed out", "connection", "getaddrinfo", "name resolution",
            "network is unreachable", "temporary failure", "remote end closed",
        )
    ):
        return {
            "code": "NETWORK_TEMPORARY",
            "message": "网络或软件源暂时不可达。",
            "action": "已停止当前尝试；稍后重试，切换备用源，或使用离线依赖包。",
        }
    if isinstance(exc, ValueError):
        return {
            "code": "DATA_INVALID",
            "message": message.splitlines()[0] or "输入数据不符合要求。",
            "action": "按提示修正对应字段或格式后重试。",
        }
    if isinstance(exc, OSError):
        return {
            "code": "FILE_IO_FAILED",
            "message": "文件读写没有完成。",
            "action": "检查磁盘空间、文件权限和占用状态，然后重试。",
        }
    return {
        "code": "OPERATION_FAILED",
        "message": "操作未完成，但现有数据没有被删除。",
        "action": "运行 quick_check.py 获取恢复步骤；需要排查时再查看 JSON 技术详情。",
    }


def friendly_error(exc: BaseException, *, include_code: bool = False) -> str:
    """Return a user-facing sentence without traceback or local paths."""
    detail = describe_error(exc)
    prefix = f"[{detail['code']}] " if include_code else ""
    return f"{prefix}{detail['message']} 处理：{detail['action']}"
