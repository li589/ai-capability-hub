#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""multi_source 包 - 多源数据采集层 (v6.0 新增)

统一 DataSource 基类 + MultiSourceProvider 聚合器。
每源独立 try/except 优雅降级，源溯源 provenance，不阻断其他源。
不再限于天天基金/东方财富，新增 8 类源。
"""
from .base import (
    DataSource, SourceResponse, MultiSourceProvider, get_provider,
)
from .akshare_provider import AkshareProvider
from .cls_provider import ClsProvider
from .wallstreetcn_provider import WallstreetcnProvider
from .csindex_provider import CsindexProvider
from .morningstar_provider import MorningstarProvider
from .howbuy_provider import HowbuyProvider
from .jiucaiban_provider import JiucaibanProvider
from .danjuan_provider import DanjuanProvider
from .eastmoney_v2_provider import EastmoneyV2Provider
from .tushare_provider import TushareProvider

__all__ = [
    "DataSource", "SourceResponse", "MultiSourceProvider", "get_provider",
    "AkshareProvider", "ClsProvider", "WallstreetcnProvider",
    "CsindexProvider", "MorningstarProvider", "HowbuyProvider",
    "JiucaibanProvider", "DanjuanProvider", "EastmoneyV2Provider",
    "TushareProvider",
]
