# -*- coding: utf-8 -*-
"""紫微斗数命盘计算引擎 - 增强版

核心功能：
1. 阳历转农历
2. 安命宫、身宫
3. 安宫干（天干）
4. 安紫微星系 + 天府星系（14主星）
5. 安六吉星（文昌文曲左辅右弼天魁天钺）
6. 安六煞星（擎羊陀罗火星铃星地空地劫）
7. 安禄存天马
8. 安小星/神煞
9. 安大限
10. 调用 DashScope LLM 生成深度解读
"""

from datetime import datetime
from lunardate import LunarDate
import httpx
import os
import time
import logging
import json

logger = logging.getLogger(__name__)

# 天干地支
HEAVENLY_STEMS = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
EARTHLY_BRANCHES = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

# 十二宫位名称（从命宫逆时针排列）
TWELVE_PALACES = [
    "命宫", "兄弟宫", "夫妻宫", "子女宫", "财帛宫", "疾厄宫",
    "迁移宫", "交友宫", "事业宫", "田宅宫", "福德宫", "父母宫"
]

# 十四主星
MAIN_STARS = [
    "紫微", "天机", "太阳", "武曲", "天同", "廉贞",
    "天府", "太阴", "贪狼", "巨门", "天相", "天梁", "七杀", "破军"
]

# 六吉星
LUCKY_STARS = ["文昌", "文曲", "左辅", "右弼", "天魁", "天钺"]

# 六煞星
BAD_STARS = ["擎羊", "陀罗", "火星", "铃星", "地空", "地劫"]

# 辅助星
AUX_STARS = ["禄存", "天马"]

# 小星/神煞
MINOR_STARS = [
    "天刑", "天姚", "天喜", "红鸾", "天巫", "天月",
    "三台", "八座", "恩光", "天贵", "龙池", "凤阁",
    "台辅", "封诰", "天空", "截空", "旬空", "孤辰", "寡宿",
    "华盖", "咸池", "天德", "月德", "天才", "天寿",
    "解神", "破碎", "蜚廉", "阴煞", "天伤", "天使",
    "命主", "身主"
]

# 星曜颜色分类（用于UI渲染）
STAR_COLORS = {
    # 主星 - 金色
    "紫微": "main", "天机": "main", "太阳": "main", "武曲": "main",
    "天同": "main", "廉贞": "main", "天府": "main", "太阴": "main",
    "贪狼": "main", "巨门": "main", "天相": "main", "天梁": "main",
    "七杀": "main", "破军": "main",
    # 吉星 - 红色
    "文昌": "lucky", "文曲": "lucky", "左辅": "lucky", "右弼": "lucky",
    "天魁": "lucky", "天钺": "lucky", "禄存": "lucky", "天马": "lucky",
    # 煞星 - 绿色
    "擎羊": "bad", "陀罗": "bad", "火星": "bad", "铃星": "bad",
    "地空": "bad", "地劫": "bad",
    # 桃花星 - 粉色
    "红鸾": "peach", "天喜": "peach", "天姚": "peach", "咸池": "peach",
    # 其他小星 - 灰色
}

# 星曜亮度等级（庙、旺、得地、利、平、不、陷）
# 每个主星在十二宫的亮度
STAR_BRIGHTNESS = {
    "紫微": {0: "旺", 1: "庙", 2: "得地", 3: "利", 4: "平", 5: "不", 6: "陷", 7: "平", 8: "利", 9: "得地", 10: "庙", 11: "旺"},
    "天机": {0: "陷", 1: "平", 2: "庙", 3: "旺", 4: "得地", 5: "利", 6: "平", 7: "不", 8: "庙", 9: "旺", 10: "得地", 11: "利"},
    "太阳": {0: "陷", 1: "平", 2: "庙", 3: "旺", 4: "得地", 5: "利", 6: "平", 7: "不", 8: "庙", 9: "旺", 10: "得地", 11: "利"},
    "武曲": {0: "旺", 1: "庙", 2: "得地", 3: "利", 4: "平", 5: "不", 6: "陷", 7: "平", 8: "利", 9: "得地", 10: "庙", 11: "旺"},
    "天同": {0: "旺", 1: "庙", 2: "得地", 3: "利", 4: "平", 5: "不", 6: "陷", 7: "平", 8: "利", 9: "得地", 10: "庙", 11: "旺"},
    "廉贞": {0: "平", 1: "不", 2: "陷", 3: "平", 4: "利", 5: "得地", 6: "庙", 7: "旺", 8: "得地", 9: "利", 10: "平", 11: "不"},
    "天府": {0: "庙", 1: "旺", 2: "得地", 3: "利", 4: "平", 5: "不", 6: "陷", 7: "平", 8: "利", 9: "得地", 10: "庙", 11: "旺"},
    "太阴": {0: "旺", 1: "庙", 2: "得地", 3: "利", 4: "平", 5: "不", 6: "陷", 7: "平", 8: "利", 9: "得地", 10: "庙", 11: "旺"},
    "贪狼": {0: "旺", 1: "庙", 2: "得地", 3: "利", 4: "平", 5: "不", 6: "陷", 7: "平", 8: "利", 9: "得地", 10: "庙", 11: "旺"},
    "巨门": {0: "旺", 1: "庙", 2: "得地", 3: "利", 4: "平", 5: "不", 6: "陷", 7: "平", 8: "利", 9: "得地", 10: "庙", 11: "旺"},
    "天相": {0: "旺", 1: "庙", 2: "得地", 3: "利", 4: "平", 5: "不", 6: "陷", 7: "平", 8: "利", 9: "得地", 10: "庙", 11: "旺"},
    "天梁": {0: "旺", 1: "庙", 2: "得地", 3: "利", 4: "平", 5: "不", 6: "陷", 7: "平", 8: "利", 9: "得地", 10: "庙", 11: "旺"},
    "七杀": {0: "旺", 1: "庙", 2: "得地", 3: "利", 4: "平", 5: "不", 6: "陷", 7: "平", 8: "利", 9: "得地", 10: "庙", 11: "旺"},
    "破军": {0: "旺", 1: "庙", 2: "得地", 3: "利", 4: "平", 5: "不", 6: "陷", 7: "平", 8: "利", 9: "得地", 10: "庙", 11: "旺"},
}

# 四化表（根据年干）
SIHUA_TABLE = {
    "甲": {"化禄": "廉贞", "化权": "破军", "化科": "武曲", "化忌": "太阳"},
    "乙": {"化禄": "天机", "化权": "天梁", "化科": "紫微", "化忌": "太阴"},
    "丙": {"化禄": "天同", "化权": "天机", "化科": "文昌", "化忌": "廉贞"},
    "丁": {"化禄": "太阴", "化权": "天同", "化科": "天机", "化忌": "巨门"},
    "戊": {"化禄": "贪狼", "化权": "太阴", "化科": "右弼", "化忌": "天机"},
    "己": {"化禄": "武曲", "化权": "贪狼", "化科": "天梁", "化忌": "文曲"},
    "庚": {"化禄": "太阳", "化权": "武曲", "化科": "太阴", "化忌": "天同"},
    "辛": {"化禄": "巨门", "化权": "太阳", "化科": "文曲", "化忌": "文昌"},
    "壬": {"化禄": "天梁", "化权": "紫微", "化科": "左辅", "化忌": "武曲"},
    "癸": {"化禄": "破军", "化权": "巨门", "化科": "太阴", "化忌": "贪狼"},
}

# DashScope API
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
DASHSCOPE_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"


# ==================== 基础计算 ====================

def solar_to_lunar(year: int, month: int, day: int) -> dict:
    """阳历转农历"""
    try:
        lunar = LunarDate.fromSolarDate(year, month, day)
        return {
            "year": lunar.year,
            "month": lunar.month,
            "day": lunar.day,
            "is_leap": lunar.isLeapMonth
        }
    except Exception as e:
        logger.error(f"农历转换失败: {e}")
        raise ValueError(f"日期转换失败: {e}")


def get_year_stem_branch(year: int) -> tuple:
    """获取年份的天干地支"""
    stem_index = (year - 4) % 10
    branch_index = (year - 4) % 12
    return HEAVENLY_STEMS[stem_index], EARTHLY_BRANCHES[branch_index]


def calculate_ming_gong(lunar_month: int, birth_hour_branch: int) -> int:
    """计算命宫位置: (14 - 农历月份 + 时辰地支序号) % 12"""
    return (14 - lunar_month + birth_hour_branch) % 12


def calculate_shen_gong(lunar_month: int, birth_hour_branch: int) -> int:
    """计算身宫位置: (农历月份 + 时辰地支序号) % 12"""
    return (lunar_month + birth_hour_branch) % 12


# ==================== 安宫干 ====================

def calculate_palace_stems(year_stem_index: int, ming_gong: int) -> dict:
    """
    安宫干（十二宫天干）
    根据年干推算每个宫位的天干
    规则：甲己起丙寅，乙庚起戊寅，丙辛起庚寅，丁壬起壬寅，戊癸起甲寅
    """
    start_stems = {0: 2, 5: 2, 1: 4, 6: 4, 2: 6, 7: 6, 3: 8, 8: 8, 4: 0, 9: 0}
    
    # 寅宫起始天干
    yin_position = 2  # 寅 = index 2
    start_stem = start_stems[year_stem_index]
    
    palace_stems = {}
    for i in range(12):
        branch_idx = (yin_position + i) % 12
        stem_idx = (start_stem + i) % 10
        palace_stems[branch_idx] = stem_idx
    
    return palace_stems


# ==================== 安主星 ====================

def place_ziwei_star(lunar_day: int, year_stem_index: int) -> int:
    """安紫微星 - 根据农历日期和年干"""
    # 五行局对应的起算数
    wuxing_base = {0: 3, 1: 4, 2: 2, 3: 6, 4: 5, 5: 6, 6: 3, 7: 4, 8: 2, 9: 5}
    base = wuxing_base[year_stem_index]
    
    # 紫微星位置计算
    day = lunar_day
    quotient = day // base
    remainder = day % base
    
    if remainder == 0:
        position = quotient - 1
    else:
        position = quotient + (base - remainder)
    
    return position % 12


def place_all_main_stars(ziwei_pos: int) -> dict:
    """安十四主星"""
    stars = {}
    
    # 紫微星系（逆时针）: 紫微、天机、太阳、武曲、天同、廉贞
    ziwei_series = ["紫微", "天机", "太阳", "武曲", "天同", "廉贞"]
    gaps = [0, 1, 3, 4, 5, 8]  # 相对紫微的偏移
    for i, star in enumerate(ziwei_series):
        stars[star] = (ziwei_pos - gaps[i]) % 12
    
    # 天府位置 = 与紫微对称（相对寅宫轴）
    tianfu_pos = (4 + 4 - ziwei_pos) % 12 if ziwei_pos <= 4 else (12 + 4 - ziwei_pos) % 12
    # 简化：天府与紫微的关系
    tianfu_offset = [4, 3, 2, 1, 0, 11, 10, 9, 8, 7, 6, 5]
    tianfu_pos = tianfu_offset[ziwei_pos]
    
    # 天府星系（顺时针）: 天府、太阴、贪狼、巨门、天相、天梁、七杀、破军
    tianfu_series = ["天府", "太阴", "贪狼", "巨门", "天相", "天梁", "七杀", "破军"]
    for i, star in enumerate(tianfu_series):
        stars[star] = (tianfu_pos + i) % 12
    
    return stars


# ==================== 安辅星 ====================

def place_lucky_stars(lunar_month: int, lunar_day: int, hour_branch: int, year_branch: int) -> dict:
    """安六吉星"""
    stars = {}
    
    # 文昌：从戌宫起子时，逆数至生时
    stars["文昌"] = (10 - hour_branch) % 12
    
    # 文曲：从辰宫起子时，顺数至生时
    stars["文曲"] = (4 + hour_branch) % 12
    
    # 左辅：从辰宫起正月，顺数至生月
    stars["左辅"] = (4 + lunar_month - 1) % 12
    
    # 右弼：从戌宫起正月，逆数至生月
    stars["右弼"] = (10 - lunar_month + 1) % 12
    
    # 天魁（阳贵人）：根据年支
    tiankui_table = {0: 1, 1: 0, 2: 11, 3: 9, 4: 1, 5: 0, 6: 9, 7: 6, 8: 1, 9: 0, 10: 11, 11: 9}
    stars["天魁"] = tiankui_table.get(year_branch, 1)
    
    # 天钺（阴贵人）：根据年支
    tianyue_table = {0: 7, 1: 8, 2: 9, 3: 5, 4: 7, 5: 8, 6: 5, 7: 2, 8: 7, 9: 8, 10: 9, 11: 5}
    stars["天钺"] = tianyue_table.get(year_branch, 7)
    
    return stars


def place_bad_stars(lunar_month: int, lunar_day: int, hour_branch: int, year_branch: int) -> dict:
    """安六煞星"""
    stars = {}
    
    # 擎羊：禄前一位
    lucun_table = {2: 5, 3: 2, 4: 2, 5: 5, 6: 8, 7: 5, 8: 8, 9: 11, 10: 11, 11: 8, 0: 2, 1: 11}
    lucun_pos = lucun_table.get(year_branch, 5)
    stars["擎羊"] = (lucun_pos + 1) % 12
    
    # 陀罗：禄后一位
    stars["陀罗"] = (lucun_pos - 1) % 12
    
    # 火星：根据年支和生时
    fire_start = {0: 2, 1: 3, 2: 1, 3: 9, 4: 2, 5: 3, 6: 1, 7: 9, 8: 2, 9: 3, 10: 1, 11: 9}
    stars["火星"] = (fire_start.get(year_branch, 2) + hour_branch) % 12
    
    # 铃星：根据年支和生时
    bell_start = {0: 3, 1: 10, 2: 3, 3: 10, 4: 3, 5: 10, 6: 3, 7: 10, 8: 3, 9: 10, 10: 3, 11: 10}
    stars["铃星"] = (bell_start.get(year_branch, 3) + hour_branch) % 12
    
    # 地空：从亥宫起子时，逆数至生时
    stars["地空"] = (11 - hour_branch) % 12
    
    # 地劫：从亥宫起子时，顺数至生时
    stars["地劫"] = (11 + hour_branch) % 12
    
    return stars


def place_aux_stars(year_branch: int) -> dict:
    """安禄存、天马"""
    stars = {}
    
    # 禄存：根据年支
    lucun_table = {2: 5, 3: 2, 4: 2, 5: 5, 6: 8, 7: 5, 8: 8, 9: 11, 10: 11, 11: 8, 0: 2, 1: 11}
    stars["禄存"] = lucun_table.get(year_branch, 5)
    
    # 天马：根据年支
    tianma_table = {0: 2, 4: 2, 8: 2, 1: 11, 5: 11, 9: 11, 2: 8, 6: 8, 10: 8, 3: 5, 7: 5, 11: 5}
    stars["天马"] = tianma_table.get(year_branch, 2)
    
    return stars


def place_minor_stars(lunar_month: int, hour_branch: int, year_branch: int) -> list:
    """安小星/神煞（返回 [(name, position), ...]）"""
    stars = []
    
    # === 已有 ===
    # 天刑：从酉宫起正月，顺数
    stars.append(("天刑", (9 + lunar_month - 1) % 12))
    
    # 天姚：从丑宫起正月，顺数
    stars.append(("天姚", (1 + lunar_month - 1) % 12))
    
    # 天喜：从戌宫起正月，逆数
    stars.append(("天喜", (10 - lunar_month + 1) % 12))
    
    # 红鸾：从卯宫起子年，逆数
    stars.append(("红鸾", (3 - year_branch) % 12))
    
    # 孤辰：根据年支三合局
    branch_group = year_branch % 4
    guchen_table = {0: 2, 1: 5, 2: 8, 3: 11}
    stars.append(("孤辰", guchen_table[branch_group]))
    
    # 寡宿：根据年支三合局
    guasu_table = {0: 11, 1: 2, 2: 5, 3: 8}
    stars.append(("寡宿", guasu_table[branch_group]))
    
    # 华盖：根据年支三合局
    huagai_table = {0: 4, 1: 7, 2: 10, 3: 1}
    stars.append(("华盖", huagai_table[branch_group]))
    
    # 天德：从酉宫起正月，顺数
    stars.append(("天德", (9 + lunar_month - 1) % 12))
    
    # 月德：从巳宫起正月，顺数
    stars.append(("月德", (5 + lunar_month - 1) % 12))
    
    # 解神：根据生月
    jieshen_table = [10, 8, 6, 4, 2, 0, 10, 8, 6, 4, 2, 0]
    stars.append(("解神", jieshen_table[(lunar_month - 1) % 12]))
    
    # === 新增 ===
    # 天巫：从巳宫起正月，顺数
    stars.append(("天巫", (5 + lunar_month - 1) % 12))
    
    # 天月：从戌宫起正月，顺数
    stars.append(("天月", (10 + lunar_month - 1) % 12))
    
    # 三台：从辰宫起正月，顺数
    stars.append(("三台", (4 + lunar_month - 1) % 12))
    
    # 八座：从寅宫起正月，顺数
    stars.append(("八座", (2 + lunar_month - 1) % 12))
    
    # 恩光：从寅宫起正月，顺数
    stars.append(("恩光", (2 + lunar_month - 1) % 12))
    
    # 天贵：从子宫起正月，顺数
    stars.append(("天贵", (0 + lunar_month - 1) % 12))
    
    # 龙池：从辰宫起子年，顺数
    stars.append(("龙池", (4 + year_branch) % 12))
    
    # 凤阁：从戌宫起子年，逆数
    stars.append(("凤阁", (10 - year_branch) % 12))
    
    # 台辅：从寅宫起子时，顺数
    stars.append(("台辅", (2 + hour_branch) % 12))
    
    # 封诰：从寅宫起子时，顺数
    stars.append(("封诰", (2 + hour_branch) % 12))
    
    # 天空：从丑宫起子年，逆数
    stars.append(("天空", (1 - year_branch) % 12))
    
    # 截空：根据年干（甲己年在申酉，乙庚年在午未，丙辛年在辰巳，丁壬年在寅卯，戊癸年在子丑）
    year_stem_idx = (year_branch + 6) % 10  # 粗略推算年干
    jiekong_table = {0: 8, 5: 8, 1: 6, 6: 6, 2: 4, 7: 4, 3: 2, 8: 2, 4: 0, 9: 0}
    stars.append(("截空", jiekong_table.get(year_stem_idx, 8)))
    
    # 旬空：根据年支
    xunkong_table = {0: 10, 1: 10, 2: 0, 3: 0, 4: 2, 5: 2, 6: 4, 7: 4, 8: 6, 9: 6, 10: 8, 11: 8}
    stars.append(("旬空", xunkong_table.get(year_branch, 10)))
    
    # 咸池（桃花煞）：根据年支三合局
    xianchi_table = {0: 9, 1: 6, 2: 3, 3: 0, 4: 9, 5: 6, 6: 3, 7: 0, 8: 9, 9: 6, 10: 3, 11: 0}
    stars.append(("咸池", xianchi_table.get(year_branch, 9)))
    
    # 天才：根据命宫和年支
    stars.append(("天才", (year_branch + 1) % 12))
    
    # 天寿：根据身宫和年支
    stars.append(("天寿", (year_branch + 1) % 12))
    
    # 破碎：从巳宫起子年，顺数
    stars.append(("破碎", (5 + year_branch) % 12))
    
    # 蜚廉：从申宫起子年，顺数
    stars.append(("蜚廉", (8 + year_branch) % 12))
    
    # 阴煞：从寅宫起正月，逆数
    stars.append(("阴煞", (2 - lunar_month + 1) % 12))
    
    # 天伤：从午宫起子时，顺数
    stars.append(("天伤", (6 + hour_branch) % 12))
    
    # 天使：从子宫起子时，逆数
    stars.append(("天使", (0 - hour_branch) % 12))
    
    return stars


# ==================== 安大限 ====================

def calculate_daxian(ming_gong: int, year_stem_index: int, gender: str) -> dict:
    """
    计算大限（每十年一个宫位）
    阳男阴女顺行，阴男阳女逆行
    """
    # 判断顺逆
    yang_stems = [0, 2, 4, 6, 8]  # 甲丙戊庚壬
    is_yang = year_stem_index in yang_stems
    is_male = gender == "男"
    
    if (is_yang and is_male) or (not is_yang and not is_male):
        direction = 1  # 顺行
    else:
        direction = -1  # 逆行
    
    daxian = {}
    for i in range(12):
        palace_pos = (ming_gong + direction * i) % 12
        age_start = 5 + i * 10  # 大限起始年龄（虚岁）
        age_end = age_start + 9
        daxian[palace_pos] = f"{age_start}-{age_end}"
    
    return daxian


# ==================== 获取当前大限 ====================

def get_current_daxian(age: int, daxian: dict) -> str:
    """获取当前年龄所在的大限宫位"""
    for pos, age_range in daxian.items():
        start, end = map(int, age_range.split("-"))
        if start <= age <= end:
            return f"{age_range} ({EARTHLY_BRANCHES[pos]}宫)"
    return ""


# ==================== 星曜亮度 ====================

def calculate_star_brightness(main_stars: dict) -> dict:
    """
    计算主星在各宫位的亮度
    返回: {star_name: {"position": pos, "branch": branch, "brightness": brightness}}
    """
    brightness_info = {}
    for star, pos in main_stars.items():
        if star in STAR_BRIGHTNESS:
            brightness = STAR_BRIGHTNESS[star][pos]
            branch = EARTHLY_BRANCHES[pos]
            brightness_info[star] = {
                "position": pos,
                "branch": branch,
                "brightness": brightness
            }
    return brightness_info


# ==================== 三方四正 ====================

def calculate_sanfang_sizheng(ming_gong: int) -> dict:
    """
    计算命宫的三方四正
    三方：命宫、财帛宫、官禄宫（事业宫）
    四正：三方 + 对宫（迁移宫）
    
    返回: {
        "三方": [命宫位, 财帛宫位, 事业宫位],
        "四正": [命宫位, 财帛宫位, 事业宫位, 迁移宫位],
        "对宫": 迁移宫位
    }
    """
    # 命宫
    ming_pos = ming_gong
    
    # 财帛宫：命宫顺时针第5位（隔4位）
    caibo_pos = (ming_gong + 4) % 12
    
    # 事业宫（官禄宫）：命宫顺时针第9位（隔8位）
    shiye_pos = (ming_gong + 8) % 12
    
    # 迁移宫：命宫对宫（+6位）
    qianyi_pos = (ming_gong + 6) % 12
    
    return {
        "三方": [ming_pos, caibo_pos, shiye_pos],
        "四正": [ming_pos, caibo_pos, shiye_pos, qianyi_pos],
        "对宫": qianyi_pos,
        "三方名称": ["命宫", "财帛宫", "事业宫"],
        "四正名称": ["命宫", "财帛宫", "事业宫", "迁移宫"]
    }


# ==================== 四化 ====================

def calculate_sihua(year_stem: str, main_stars: dict, lucky_stars: dict) -> dict:
    """
    计算四化（化禄、化权、化科、化忌）
    根据年干确定四化星
    
    返回: {
        "化禄": {"star": star_name, "position": pos, "branch": branch},
        "化权": {...},
        "化科": {...},
        "化忌": {...}
    }
    """
    if year_stem not in SIHUA_TABLE:
        return {}
    
    sihua_data = SIHUA_TABLE[year_stem]
    result = {}
    
    # 合并所有星曜位置
    all_stars = {}
    all_stars.update(main_stars)
    all_stars.update(lucky_stars)
    
    for hua_type, star_name in sihua_data.items():
        if star_name in all_stars:
            pos = all_stars[star_name]
            branch = EARTHLY_BRANCHES[pos]
            result[hua_type] = {
                "star": star_name,
                "position": pos,
                "branch": branch
            }
    
    return result


# ==================== 流年 ====================

def calculate_liunian(current_year: int, birth_year: int, ming_gong: int) -> dict:
    """
    计算流年
    流年命宫 = 流年地支对应的位置
    
    返回: {
        "year": current_year,
        "year_branch": 流年地支,
        "ming_gong": 流年命宫位置,
        "ming_gong_branch": 流年命宫地支
    }
    """
    # 流年地支
    year_branch_index = (current_year - 4) % 12
    year_branch = EARTHLY_BRANCHES[year_branch_index]
    
    # 流年命宫 = 流年地支位置
    liunian_ming = year_branch_index
    liunian_ming_branch = EARTHLY_BRANCHES[liunian_ming]
    
    return {
        "year": current_year,
        "year_branch": year_branch,
        "ming_gong": liunian_ming,
        "ming_gong_branch": liunian_ming_branch
    }


# ==================== 小限 ====================

def calculate_xiaoxian(age: int, ming_gong: int, year_branch: int, gender: str) -> dict:
    """
    计算小限
    小限每年移动一宫
    起法：子午卯酉年生人，男从辰宫起1岁，女从戌宫起1岁
         寅申巳亥年生人，男从戌宫起1岁，女从辰宫起1岁
         辰戌丑未年生人，男从午宫起1岁，女从子宫起1岁
    
    返回: {
        "age": age,
        "position": 小限宫位,
        "branch": 小限宫位地支
    }
    """
    # 判断年支三合局
    if year_branch in [0, 6, 3, 9]:  # 子午卯酉
        if gender == "男":
            start_pos = 4  # 辰宫
        else:
            start_pos = 10  # 戌宫
    elif year_branch in [2, 8, 5, 11]:  # 寅申巳亥
        if gender == "男":
            start_pos = 10  # 戌宫
        else:
            start_pos = 4  # 辰宫
    else:  # 辰戌丑未
        if gender == "男":
            start_pos = 6  # 午宫
        else:
            start_pos = 0  # 子宫
    
    # 小限宫位 = 起始宫位 + (年龄 - 1)
    xiaoxian_pos = (start_pos + age - 1) % 12
    xiaoxian_branch = EARTHLY_BRANCHES[xiaoxian_pos]
    
    return {
        "age": age,
        "position": xiaoxian_pos,
        "branch": xiaoxian_branch
    }


# ==================== LLM 解读 ====================

async def generate_interpretation(
    birth_info, lunar_info, ming_gong, shen_gong,
    year_stem_branch, main_stars, palaces, gender,
    all_stars_by_palace, daxian, current_age
):
    """调用 DashScope 生成深度解读"""
    if not DASHSCOPE_API_KEY:
        return _fallback_interpretation(ming_gong, year_stem_branch)
    
    # 构建每个宫位的星曜列表
    palace_star_text = []
    for palace_name in TWELVE_PALACES:
        pinfo = palaces[palace_name]
        pos = pinfo["position"]
        branch = pinfo["branch"]
        star_list = all_stars_by_palace.get(pos, [])
        daxian_range = daxian.get(pos, "")
        
        star_names = [s["name"] for s in star_list]
        palace_star_text.append(
            f"- {palace_name}（{branch}宫）[{daxian_range}]：{', '.join(star_names) if star_names else '空宫'}"
        )
    
    # 主星分布
    main_star_text = "\n".join([
        f"- {star}：{EARTHLY_BRANCHES[pos]}宫"
        for star, pos in main_stars.items()
    ])
    
    current_daxian = get_current_daxian(current_age, daxian)
    
    prompt = f"""你是一位精通紫微斗数的资深命理大师，拥有30年实践经验。请进行深度专业解读。

## 命盘基础信息
- 性别：{gender}
- 出生：{birth_info['year']}年{birth_info['month']}月{birth_info['day']}日 {birth_info['hour']}时
- 农历：{lunar_info['year']}年{lunar_info['month']}月{lunar_info['day']}日
- 年柱：{year_stem_branch}
- 命宫：{EARTHLY_BRANCHES[ming_gong]}宫 | 身宫：{EARTHLY_BRANCHES[shen_gong]}宫
- 当前年龄：{current_age}岁 | 当前大限：{current_daxian}

## 十四主星分布
{main_star_text}

## 十二宫位（含大限年龄段）
{chr(10).join(palace_star_text)}

---

请按以下结构深度解读（3000-4000字）：

## 一、命盘格局总论（400字）
## 二、命宫深度解析（500字）
### 性格特质
### 天赋才能
### 人生格局
## 三、事业运势（500字）
### 适合行业
### 发展轨迹
### 职场建议
## 四、财运分析（500字）
### 财运特点
### 理财建议
### 财富积累策略
## 五、感情婚姻（500字）
### 感情特质
### 婚姻分析
### 感情建议
## 六、健康运势（400字）
### 体质特点
### 养生建议
### 健康预警期
## 七、人际关系与贵人运（300字）
## 八、当前大限与流年运势（400字）
### 当前大限特点
### 2026年运势
### 关键月份
## 九、人生建议与开运方法（300字）

**要求：**
1. 结合具体星曜，不泛泛而谈
2. 建议具体可操作
3. 专业术语要解释
4. Markdown格式"""

    try:
        async with httpx.AsyncClient(timeout=120.0, trust_env=False) as client:
            resp = await client.post(
                f"{DASHSCOPE_BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {DASHSCOPE_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "qwen-plus",
                    "messages": [
                        {"role": "system", "content": "你是一位专业的紫微斗数命理师。"},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 4000
                }
            )
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"]
            logger.error(f"DashScope API failed: {resp.status_code}")
    except Exception as e:
        logger.error(f"LLM generation failed: {e}")
    
    return _fallback_interpretation(ming_gong, year_stem_branch)


def _fallback_interpretation(ming_gong, year_stem_branch):
    ming_branch = EARTHLY_BRANCHES[ming_gong]
    return f"""## 紫微斗数命盘解读

## 基本信息
- 年柱：{year_stem_branch}
- 命宫：{ming_branch}宫

## 命宫特质
您的命宫位于{ming_branch}宫，代表独特的性格特质和人生格局。

## 事业运势
建议选择稳定行业，发挥专业优势。

## 财运分析
财运平稳，适合稳健理财。

## 感情婚姻
感情需耐心经营，找性格互补的伴侣。

## 健康提示
注意劳逸结合，定期体检。

*注：此为简化版解读，完整解读需配置 DASHSCOPE_API_KEY。*"""


def generate_scores(main_stars, ming_gong, palaces):
    """生成运势评分"""
    import random
    random.seed(int(time.time()) % 10000)
    
    base = 70
    ming_stars = [s for s, p in main_stars.items() if p == ming_gong]
    lucky = ["紫微", "天府", "太阳", "太阴", "天同", "天梁"]
    bonus = len([s for s in ming_stars if s in lucky]) * 5
    
    return {
        "overall": min(95, base + bonus + random.randint(-5, 5)),
        "career": min(95, base + random.randint(-8, 15)),
        "wealth": min(95, base + random.randint(-8, 15)),
        "love": min(95, base + random.randint(-8, 15)),
        "health": min(95, base + random.randint(-8, 15)),
        "luck": min(95, base + random.randint(-8, 15)),
    }


# ==================== 主计算函数 ====================

async def calculate_ziwei_chart(year, month, day, hour, gender):
    """计算完整紫微斗数命盘"""
    
    # 1. 阳历转农历
    lunar = solar_to_lunar(year, month, day)
    
    # 2. 时辰地支
    hour_branch = ((hour + 1) // 2) % 12
    
    # 3. 命宫和身宫
    ming_gong = calculate_ming_gong(lunar["month"], hour_branch)
    shen_gong = calculate_shen_gong(lunar["month"], hour_branch)
    
    # 4. 年干支
    year_stem, year_branch = get_year_stem_branch(lunar["year"])
    year_stem_index = HEAVENLY_STEMS.index(year_stem)
    year_branch_index = EARTHLY_BRANCHES.index(year_branch)
    year_stem_branch = f"{year_stem}{year_branch}"
    
    # 5. 宫干
    palace_stems = calculate_palace_stems(year_stem_index, ming_gong)
    
    # 6. 紫微星 + 十四主星
    ziwei_pos = place_ziwei_star(lunar["day"], year_stem_index)
    main_stars = place_all_main_stars(ziwei_pos)
    
    # 7. 六吉星
    lucky_stars = place_lucky_stars(lunar["month"], lunar["day"], hour_branch, year_branch_index)
    
    # 8. 六煞星
    bad_stars = place_bad_stars(lunar["month"], lunar["day"], hour_branch, year_branch_index)
    
    # 9. 禄存天马
    aux_stars = place_aux_stars(year_branch_index)
    
    # 10. 小星/神煞
    minor_stars = place_minor_stars(lunar["month"], hour_branch, year_branch_index)
    
    # 11. 十二宫位
    palaces = {}
    for i, palace_name in enumerate(TWELVE_PALACES):
        pos = (ming_gong - i) % 12
        branch = EARTHLY_BRANCHES[pos]
        stem_idx = palace_stems.get(pos, 0)
        palaces[palace_name] = {
            "position": pos,
            "branch": branch,
            "stem": HEAVENLY_STEMS[stem_idx],
            "stem_branch": f"{HEAVENLY_STEMS[stem_idx]}{branch}"
        }
    
    # 12. 大限
    current_year = datetime.now().year
    current_age = current_year - year + 1  # 虚岁
    daxian = calculate_daxian(ming_gong, year_stem_index, gender)
    
    # 13. 整合所有星曜到宫位
    all_stars_by_palace = {i: [] for i in range(12)}
    
    # 主星
    for star, pos in main_stars.items():
        all_stars_by_palace[pos].append({
            "name": star, "type": STAR_COLORS.get(star, "main")
        })
    
    # 吉星
    for star, pos in lucky_stars.items():
        all_stars_by_palace[pos].append({
            "name": star, "type": STAR_COLORS.get(star, "lucky")
        })
    
    # 煞星
    for star, pos in bad_stars.items():
        all_stars_by_palace[pos].append({
            "name": star, "type": STAR_COLORS.get(star, "bad")
        })
    
    # 辅星
    for star, pos in aux_stars.items():
        all_stars_by_palace[pos].append({
            "name": star, "type": STAR_COLORS.get(star, "lucky")
        })
    
    # 小星
    for star_name, pos in minor_stars:
        all_stars_by_palace[pos].append({
            "name": star_name, "type": STAR_COLORS.get(star_name, "minor")
        })
    
    # 14. 运势评分
    scores = generate_scores(main_stars, ming_gong, palaces)
    
    # 15. LLM 解读
    interpretation = await generate_interpretation(
        {"year": year, "month": month, "day": day, "hour": hour},
        lunar, ming_gong, shen_gong,
        year_stem_branch, main_stars, palaces, gender,
        all_stars_by_palace, daxian, current_age
    )
    
    # 16. 计算星曜亮度（庙旺利平陷）
    star_brightness = calculate_star_brightness(main_stars)
    
    # 17. 计算三方四正
    sanfang_sizheng = calculate_sanfang_sizheng(ming_gong)
    
    # 18. 计算四化
    sihua = calculate_sihua(year_stem, main_stars, lucky_stars)
    
    # 19. 计算流年
    liunian = calculate_liunian(current_year, year, ming_gong)
    
    # 20. 计算小限
    xiaoxian = calculate_xiaoxian(current_age, ming_gong, year_branch_index, gender)
    
    # 21. 组装返回
    return {
        "birth_info": {"year": year, "month": month, "day": day, "hour": hour},
        "lunar_info": lunar,
        "year_stem_branch": year_stem_branch,
        "gender": gender,
        "current_age": current_age,
        "current_daxian": get_current_daxian(current_age, daxian),
        "ming_gong": {"position": ming_gong, "branch": EARTHLY_BRANCHES[ming_gong]},
        "shen_gong": {"position": shen_gong, "branch": EARTHLY_BRANCHES[shen_gong]},
        "main_stars": {star: EARTHLY_BRANCHES[pos] for star, pos in main_stars.items()},
        "star_brightness": star_brightness,
        "sanfang_sizheng": sanfang_sizheng,
        "sihua": sihua,
        "liunian": liunian,
        "xiaoxian": xiaoxian,
        "palaces": palaces,
        "daxian": daxian,
        "all_stars_by_palace": {
            str(k): v for k, v in all_stars_by_palace.items()
        },
        "scores": scores,
        "interpretation": interpretation,
        "chart_generated_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }
