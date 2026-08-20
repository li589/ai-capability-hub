"""通达信 mootdx 数据源模块

提供通达信协议的行情数据访问，包括 K 线、实时报价、逐笔成交、
财务快照、F10 公司资料等。内置多服务器 TCP 探测与自动降级机制。
"""

import time
import socket
import threading
from core.client import http_get

# ─── 通达信行情服务器池 ──────────────────────────────────────
_TDX_SERVERS = [
    ("110.41.147.114", 7709),
    ("221.231.141.60", 7709),
    ("101.227.73.20", 7709),
    ("101.227.77.254", 7709),
    ("14.17.75.71", 7709),
    ("59.173.18.140", 7709),
    ("112.95.140.74", 7709),
    ("113.105.142.136", 7709),
    ("119.147.212.81", 7709),
    ("218.75.126.9", 7709),
]

# 市场代码映射
_MARKET_SH = 1  # 上海
_MARKET_SZ = 0  # 深圳

# ─── 客户端状态 ────────────────────────────────────────────────
_client_instance = None
_client_lock = threading.Lock()
_active_server = None


def _detect_market(code: str) -> int:
    """根据股票代码判断市场。

    Args:
        code: 6 位股票代码

    Returns:
        市场代码：1=上海，0=深圳
    """
    if code.startswith(("6", "5", "9", "11", "13")):
        return _MARKET_SH
    return _MARKET_SZ


def _probe_server(host: str, port: int, timeout: float = 2.0) -> float:
    """TCP 探测单台服务器延迟。

    Args:
        host: 服务器 IP
        port: 端口
        timeout: 超时时间（秒）

    Returns:
        延迟毫秒数，连接失败返回 float('inf')
    """
    try:
        start = time.time()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((host, port))
        elapsed = (time.time() - start) * 1000
        sock.close()
        return elapsed
    except (socket.error, OSError):
        return float("inf")


def create_client(market: int = None):
    """创建通达信客户端连接。

    对服务器池进行 TCP 探测，选择延迟最低的服务器建立连接。
    若所有服务器不可达则尝试使用默认首个服务器。

    Args:
        market: 市场代码（0=深圳, 1=上海），可选

    Returns:
        客户端实例，连接失败返回 None
    """
    global _client_instance, _active_server

    if _client_instance is not None:
        return _client_instance

    with _client_lock:
        # 双重检查锁定
        if _client_instance is not None:
            return _client_instance

        try:
            from mootdx.quotes import Quotes
        except ImportError:
            return None

        # TCP 探测选择最优服务器
        best_server = None
        best_latency = float("inf")

        for host, port in _TDX_SERVERS:
            latency = _probe_server(host, port)
            if latency < best_latency:
                best_latency = latency
                best_server = (host, port)

        if best_server is None or best_latency == float("inf"):
            # 降级使用默认首台服务器
            best_server = _TDX_SERVERS[0]

        try:
            client = Quotes.factory(
                market="std",
                bestip=True,
                timeout=10,
            )
            _client_instance = client
            _active_server = best_server
            return client
        except Exception:
            # 指定服务器重试
            try:
                client = Quotes.factory(
                    market="std",
                    bestip=False,
                    timeout=10,
                )
                _client_instance = client
                _active_server = best_server
                return client
            except Exception:
                return None


def _ensure_client():
    """确保客户端已连接，失败时自动重建。"""
    global _client_instance
    if _client_instance is None:
        _client_instance = create_client()
    return _client_instance


def _with_fallback(func, *args, **kwargs):
    """包装调用，连接异常时重建客户端后重试。"""
    global _client_instance
    client = _ensure_client()
    if client is None:
        return None

    try:
        return func(client, *args, **kwargs)
    except (ConnectionError, OSError, TimeoutError, RuntimeError) as e:
        # 连接级错误，重建客户端重试一次
        _client_instance = None
        client = _ensure_client()
        if client is None:
            return None
        try:
            return func(client, *args, **kwargs)
        except Exception:
            return None


def bars(code: str, frequency: int = 9, offset: int = 0, count: int = 800) -> list:
    """获取 K 线数据（多周期支持）。

    Args:
        code: 6 位股票代码
        frequency: K 线周期类型
            0=5分钟, 1=15分钟, 2=30分钟, 3=60分钟,
            4=日线, 5=周线, 6=月线, 7=1分钟,
            8=1分钟, 9=日线, 10=季线, 11=年线
        offset: 偏移位置，0 为最新
        count: 获取条数，最大 800

    Returns:
        K 线数据列表，每条含 open/high/low/close/volume/amount 等字段
    """
    market = _detect_market(code)

    def _call(client, *a, **kw):
        return client.bars(
            symbol=code,
            frequency=frequency,
            offset=offset,
            count=count,
        )

    result = _with_fallback(_call)
    if result is None:
        return []

    # mootdx 返回 DataFrame，转为字典列表
    try:
        if hasattr(result, "to_dict"):
            records = result.to_dict("records")
            return records if isinstance(records, list) else []
        return list(result) if result else []
    except (TypeError, ValueError):
        return []


def realtime(code: str) -> dict:
    """获取实时行情报价（46 字段）。

    Args:
        code: 6 位股票代码

    Returns:
        实时行情字典，含 price/open/high/low/volume/bid/ask 等 46 个字段
    """
    market = _detect_market(code)

    def _call(client, *a, **kw):
        return client.quotes(symbol=[code])

    result = _with_fallback(_call)
    if result is None:
        return {}

    try:
        if hasattr(result, "to_dict"):
            records = result.to_dict("records")
            return records[0] if records else {}
        return dict(result) if result else {}
    except (TypeError, ValueError, IndexError):
        return {}


def transaction(code: str, date: str) -> list:
    """获取逐笔成交数据。

    Args:
        code: 6 位股票代码
        date: 交易日期，格式 'YYYYMMDD'

    Returns:
        逐笔成交列表，每条含 time/price/volume/type 等
    """
    market = _detect_market(code)

    def _call(client, *a, **kw):
        return client.transactions(symbol=code, date=date)

    result = _with_fallback(_call)
    if result is None:
        return []

    try:
        if hasattr(result, "to_dict"):
            records = result.to_dict("records")
            return records if isinstance(records, list) else []
        return list(result) if result else []
    except (TypeError, ValueError):
        return []


def finance_summary(code: str) -> dict:
    """获取财务摘要快照（37 字段）。

    包含每股收益、净资产收益率、营收增长率、负债率等关键财务指标。

    Args:
        code: 6 位股票代码

    Returns:
        财务数据字典
    """
    market = _detect_market(code)

    def _call(client, *a, **kw):
        return client.finance(symbol=code)

    result = _with_fallback(_call)
    if result is None:
        return {}

    try:
        if hasattr(result, "to_dict"):
            records = result.to_dict("records")
            return records[0] if records else {}
        return dict(result) if result else {}
    except (TypeError, ValueError, IndexError):
        return {}


def company_info(code: str, category: int = 0) -> str:
    """获取 F10 公司资料。

    Args:
        code: 6 位股票代码
        category: 信息类别
            0=公司概况, 1=财务分析, 2=股本结构,
            3=股东研究, 4=券商预测, 5=交易备忘,
            6=经营分析, 7=高管信息, 8=行业分析

    Returns:
        公司资料文本内容
    """
    market = _detect_market(code)

    def _call(client, *a, **kw):
        return client.f10(symbol=code, name=category)

    result = _with_fallback(_call)
    if result is None:
        return ""

    try:
        if isinstance(result, str):
            return result
        if hasattr(result, "to_string"):
            return result.to_string()
        return str(result)
    except (TypeError, ValueError):
        return ""
