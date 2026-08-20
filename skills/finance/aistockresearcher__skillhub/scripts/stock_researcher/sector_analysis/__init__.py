"""Sector analysis"""
from .sectors import SectorAnalyzer
from .rotation import SectorRotation
# v9.0 深度板块分析
from .relative_strength import (
    SectorRelativeStrength,
    RelativeStrengthResult,
    relative_strength,
    rps_ranking,
)
from .breadth import SectorBreadth, BreadthResult, analyze_breadth
from .dispersion import SectorDispersion, DispersionResult, analyze_dispersion
from .themes import (
    THEME_SECTOR_MAP,
    list_themes,
    get_theme_stocks,
    analyze_theme,
    rank_themes,
)
from .rotation_cycle import (
    RotationCycleDetector,
    CycleStageResult,
    detect_cycle_stage,
)

__all__ = [
    # legacy
    "SectorAnalyzer",
    "SectorRotation",
    # v9.0 相对强度
    "SectorRelativeStrength",
    "RelativeStrengthResult",
    "relative_strength",
    "rps_ranking",
    # v9.0 宽度
    "SectorBreadth",
    "BreadthResult",
    "analyze_breadth",
    # v9.0 离散度
    "SectorDispersion",
    "DispersionResult",
    "analyze_dispersion",
    # v9.0 主题板块
    "THEME_SECTOR_MAP",
    "list_themes",
    "get_theme_stocks",
    "analyze_theme",
    "rank_themes",
    # v9.0 轮动周期
    "RotationCycleDetector",
    "CycleStageResult",
    "detect_cycle_stage",
]
