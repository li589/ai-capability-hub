"""五运六气年度运势引擎"""

from datetime import datetime
from typing import Dict, Tuple, List

# 天干地支
TIANGAN = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
DIZHI = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

# 五运（天干化运）
# 甲己化土，乙庚化金，丙辛化水，丁壬化木，戊癸化火
WUYUN_MAP = {
    "甲": "土运", "己": "土运",
    "乙": "金运", "庚": "金运",
    "丙": "水运", "辛": "水运",
    "丁": "木运", "壬": "木运",
    "戊": "火运", "癸": "火运"
}

# 五运太过不及（阳干太过，阴干不及）
WUYUN_STRENGTH = {
    "甲": "太过", "丙": "太过", "戊": "太过", "庚": "太过", "壬": "太过",
    "乙": "不及", "丁": "不及", "己": "不及", "辛": "不及", "癸": "不及"
}

# 六气（地支化气）
# 子午少阴君火，丑未太阴湿土，寅申少阳相火，卯酉阳明燥金，辰戌太阳寒水，巳亥厥阴风木
LIUQI_MAP = {
    "子": "少阴君火", "午": "少阴君火",
    "丑": "太阴湿土", "未": "太阴湿土",
    "寅": "少阳相火", "申": "少阳相火",
    "卯": "阳明燥金", "酉": "阳明燥金",
    "辰": "太阳寒水", "戌": "太阳寒水",
    "巳": "厥阴风木", "亥": "厥阴风木"
}

# 五运特征
WUYUN_CHARACTERISTICS = {
    "木运": {
        "element": "木",
        "season": "春",
        "climate": "风",
        "organ": "肝",
        "characteristics": "风气主事，万物生发",
        "health_focus": "肝胆系统、筋骨、情绪调节"
    },
    "火运": {
        "element": "火",
        "season": "夏",
        "climate": "热",
        "organ": "心",
        "characteristics": "热气主事，万物繁茂",
        "health_focus": "心脑血管、小肠、精神状态"
    },
    "土运": {
        "element": "土",
        "season": "长夏",
        "climate": "湿",
        "organ": "脾",
        "characteristics": "湿气主事，万物化生",
        "health_focus": "脾胃系统、肌肉、消化吸收"
    },
    "金运": {
        "element": "金",
        "season": "秋",
        "climate": "燥",
        "organ": "肺",
        "characteristics": "燥气主事，万物收敛",
        "health_focus": "肺系呼吸、大肠、皮肤毛发"
    },
    "水运": {
        "element": "水",
        "season": "冬",
        "climate": "寒",
        "organ": "肾",
        "characteristics": "寒气主事，万物闭藏",
        "health_focus": "肾与膀胱、骨髓、生殖泌尿"
    }
}

# 六气特征
LIUQI_CHARACTERISTICS = {
    "厥阴风木": {
        "element": "木",
        "climate": "风",
        "characteristics": "风木主事，气候多变",
        "health_risk": "肝风内动、眩晕、抽搐",
        "prevention": "养肝息风，避免过度劳累"
    },
    "少阴君火": {
        "element": "火",
        "climate": "热",
        "characteristics": "君火主事，温热气候",
        "health_risk": "心火上炎、失眠、口舌生疮",
        "prevention": "清心降火，养阴安神"
    },
    "少阳相火": {
        "element": "火",
        "climate": "暑热",
        "characteristics": "相火主事，暑热气候",
        "health_risk": "肝胆湿热、目赤、胁痛",
        "prevention": "清利肝胆，疏泄郁热"
    },
    "太阴湿土": {
        "element": "土",
        "climate": "湿",
        "characteristics": "湿土主事，潮湿气候",
        "health_risk": "脾虚湿困、腹胀、泄泻",
        "prevention": "健脾祛湿，饮食清淡"
    },
    "阳明燥金": {
        "element": "金",
        "climate": "燥",
        "characteristics": "燥金主事，干燥气候",
        "health_risk": "肺燥干咳、皮肤干燥、便秘",
        "prevention": "润肺生津，多饮水"
    },
    "太阳寒水": {
        "element": "水",
        "climate": "寒",
        "characteristics": "寒水主事，寒冷气候",
        "health_risk": "寒邪伤阳、关节痛、水肿",
        "prevention": "温阳散寒，保暖防寒"
    }
}


def get_ganzhi_year(year: int) -> Tuple[str, str]:
    """
    计算年份的天干地支
    
    Args:
        year: 公历年份
        
    Returns:
        (天干, 地支)
    """
    # 天干：(年份 - 3) % 10
    tiangan_idx = (year - 4) % 10
    # 地支：(年份 - 3) % 12
    dizhi_idx = (year - 4) % 12
    
    return TIANGAN[tiangan_idx], DIZHI[dizhi_idx]


def calculate_wuyun_liuqi(year: int) -> Dict:
    """
    计算五运六气
    
    Args:
        year: 公历年份
        
    Returns:
        五运六气信息字典
    """
    tiangan, dizhi = get_ganzhi_year(year)
    
    # 计算五运
    wuyun = WUYUN_MAP[tiangan]
    wuyun_strength = WUYUN_STRENGTH[tiangan]
    wuyun_info = WUYUN_CHARACTERISTICS[wuyun]
    
    # 计算六气
    liuqi = LIUQI_MAP[dizhi]
    liuqi_info = LIUQI_CHARACTERISTICS[liuqi]
    
    return {
        "year": year,
        "ganzhi": f"{tiangan}{dizhi}",
        "tiangan": tiangan,
        "dizhi": dizhi,
        "wuyun": wuyun,
        "wuyun_strength": wuyun_strength,
        "wuyun_info": wuyun_info,
        "liuqi": liuqi,
        "liuqi_info": liuqi_info
    }


def generate_fortune_summary(wuyun_liuqi: Dict) -> str:
    """
    生成运势概要
    
    Args:
        wuyun_liuqi: 五运六气信息
        
    Returns:
        运势概要文本
    """
    year = wuyun_liuqi["year"]
    ganzhi = wuyun_liuqi["ganzhi"]
    wuyun = wuyun_liuqi["wuyun"]
    wuyun_strength = wuyun_liuqi["wuyun_strength"]
    liuqi = wuyun_liuqi["liuqi"]
    wuyun_info = wuyun_liuqi["wuyun_info"]
    liuqi_info = wuyun_liuqi["liuqi_info"]
    
    summary = f"""{year}年为{ganzhi}年，{wuyun}（{wuyun_strength}），{liuqi}司天。

【气候特点】
{wuyun_info["characteristics"]}，{liuqi_info["characteristics"]}。全年以{wuyun_info["climate"]}气和{liuqi_info["climate"]}气为主要气候特征。

【健康关注】
五运影响：{wuyun_info["health_focus"]}
六气风险：{liuqi_info["health_risk"]}

【养生要点】
{liuqi_info["prevention"]}"""
    
    return summary


def analyze_yearly_fortune(year: int, constitution_type: str = None) -> Dict:
    """
    分析年度运势
    
    Args:
        year: 公历年份
        constitution_type: 用户体质类型（可选）
        
    Returns:
        完整运势分析
    """
    # 计算五运六气
    wuyun_liuqi = calculate_wuyun_liuqi(year)
    
    # 生成概要
    summary = generate_fortune_summary(wuyun_liuqi)
    
    # 分析运势评分（简化版，基于五行生克）
    score = _calculate_fortune_score(wuyun_liuqi, constitution_type)
    
    return {
        "wuyun_liuqi": wuyun_liuqi,
        "summary": summary,
        "score": score,
        "constitution_type": constitution_type
    }


def _calculate_fortune_score(wuyun_liuqi: Dict, constitution_type: str = None) -> Dict:
    """
    计算运势评分
    
    Args:
        wuyun_liuqi: 五运六气信息
        constitution_type: 用户体质类型
        
    Returns:
        评分字典
    """
    # 基础评分（简化版，实际应该更复杂）
    wuyun = wuyun_liuqi["wuyun"]
    wuyun_strength = wuyun_liuqi["wuyun_strength"]
    
    # 五运强度评分
    if wuyun_strength == "太过":
        health_score = 70  # 太过可能导致偏盛
        fortune_score = 75
    else:
        health_score = 75  # 不及可能导致偏衰
        fortune_score = 70
    
    # 根据体质调整（如果有）
    if constitution_type:
        # 简化逻辑：平和质评分更高
        if constitution_type == "平和质":
            health_score += 10
            fortune_score += 10
    
    return {
        "overall": (health_score + fortune_score) / 2,
        "health": health_score,
        "fortune": fortune_score
    }


def get_available_years() -> List[int]:
    """
    获取可分析的年份范围
    
    Returns:
        年份列表
    """
    current_year = datetime.now().year
    # 提供当前年份及前后2年
    return list(range(current_year - 2, current_year + 3))
