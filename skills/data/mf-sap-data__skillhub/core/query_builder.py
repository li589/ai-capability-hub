"""
SAP 查询构建器
智能查询构建和参数格式化
"""

import json
import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, date
from enum import Enum

class QueryType(Enum):
    """查询类型枚举"""
    DATA_QUERY = "data_query"
    COUNT_QUERY = "count_query"
    LIST_QUERY = "list_query"
    INTELLIGENT_QUERY = "intelligent_query"

class SAPQueryBuilder:
    """SAP查询构建器"""
    
    def __init__(self):
        """初始化查询构建器"""
        # 关键词到字段映射
        self.keyword_mapping = {
            # 物料相关
            "物料": ["MATNR", "MAKTX", "MATKL", "MEINS"],
            "材料": ["MATNR", "MAKTX"],
            "产品": ["MATNR", "MAKTX"],
            "货品": ["MATNR", "MAKTX"],
            "原材料": ["MATNR", "MAKTX", "MATKL"],
            "半成品": ["MATNR", "MAKTX", "MATKL"],
            "成品": ["MATNR", "MAKTX", "MATKL"],
            
            # 订单相关
            "订单": ["AUFNR", "VBELN", "EBELN"],
            "生产订单": ["AUFNR", "KTEXT", "GAMNG", "GLTRP"],
            "销售订单": ["VBELN", "NETWR", "VKORG", "ERDAT"],
            "采购订单": ["EBELN", "NETWR", "EKORG"],
            "工单": ["AUFNR", "KTEXT", "GAMNG"],
            
            # 客户供应商
            "客户": ["KUNNR", "NAME1", "ORT01"],
            "供应商": ["LIFNR", "NAME1", "ORT01"],
            "工厂": ["WERKS", "NAME1"],
            "仓库": ["LGORT", "LGOBE"],
            "部门": ["EKORG", "VKORG"],
            
            # 数量金额
            "数量": ["MENGE", "GAMNG", "LFIMG"],
            "金额": ["NETWR", "WRBTR", "DMBTR"],
            "价格": ["NETPR", "PEINH"],
            "价值": ["NETWR", "WRBTR"],
            "成本": ["STPRS", "VERPR"],
            
            # 状态
            "状态": ["STAT", "LOEKZ", "MBSTA"],
            "完成": ["STAT"],
            "进行中": ["STAT"],
            "已取消": ["STAT"],
            "已关闭": ["STAT"],
            
            # 日期时间
            "日期": ["ERSDA", "ERDAT", "AEDAT", "BUDAT"],
            "时间": ["ERZET", "AEZET"],
            "创建": ["ERSDA", "ERDAT"],
            "修改": ["LAEDA", "AEDAT"],
            "过账": ["BUDAT"],
            "交货": ["WADAT"],
            
            # 单位
            "单位": ["MEINS", "BSTME"],
            "货币": ["WAERK"],
            "批次": ["CHARG"],
            "版本": ["VERSION"]
        }
        
        # 表配置
        self.table_configs = {
            "MARA": {
                "name": "物料主数据",
                "primary_key": ["MATNR"],
                "essential_fields": ["MATNR", "MAKTX", "MEINS", "MATKL", "ERSDA"],
                "date_fields": ["ERSDA", "LAEDA"],
                "text_fields": ["MAKTX"],
                "code_fields": ["MATNR", "MATKL", "MEINS"],
                "language_table": "MAKT",
                "field_aliases": {
                    "物料号": "MATNR",
                    "物料描述": "MAKTX",
                    "物料名称": "MAKTX",
                    "基本单位": "MEINS",
                    "物料组": "MATKL",
                    "创建日期": "ERSDA",
                    "最后修改": "LAEDA"
                }
            },
            "AUFK": {
                "name": "生产订单",
                "primary_key": ["AUFNR"],
                "essential_fields": ["AUFNR", "KTEXT", "GAMNG", "GLTRP", "WERKS", "AUART", "STAT"],
                "date_fields": ["GLTRP", "FTRMI", "ERDAT"],
                "text_fields": ["KTEXT"],
                "code_fields": ["AUFNR", "WERKS", "AUART", "STAT"],
                "field_aliases": {
                    "生产订单": "AUFNR",
                    "订单号": "AUFNR",
                    "订单描述": "KTEXT",
                    "订单数量": "GAMNG",
                    "完成日期": "GLTRP",
                    "工厂": "WERKS",
                    "订单类型": "AUART",
                    "状态": "STAT",
                    "实际完成": "FTRMI"
                }
            },
            "VBAK": {
                "name": "销售订单",
                "primary_key": ["VBELN"],
                "essential_fields": ["VBELN", "ERDAT", "NETWR", "WAERK", "VKORG", "VTWEG"],
                "date_fields": ["ERDAT", "AEDAT"],
                "text_fields": [],
                "code_fields": ["VBELN", "VKORG", "VTWEG", "SPART", "WAERK"],
                "field_aliases": {
                    "销售订单": "VBELN",
                    "订单号": "VBELN",
                    "创建日期": "ERDAT",
                    "净价值": "NETWR",
                    "货币": "WAERK",
                    "销售组织": "VKORG",
                    "分销渠道": "VTWEG"
                }
            },
            "MAKT": {
                "name": "物料描述",
                "primary_key": ["MATNR", "SPRAS"],
                "essential_fields": ["MATNR", "SPRAS", "MAKTX"],
                "text_fields": ["MAKTX", "MAKTG"],
                "field_aliases": {
                    "物料号": "MATNR",
                    "语言": "SPRAS",
                    "物料描述": "MAKTX"
                }
            },
            "MBEW": {
                "name": "物料评估",
                "primary_key": ["MATNR", "BWKEY"],
                "essential_fields": ["MATNR", "BWKEY", "STPRS", "VERPR", "PEINH"],
                "field_aliases": {
                    "物料号": "MATNR",
                    "评估范围": "BWKEY",
                    "标准价格": "STPRS",
                    "移动平均价": "VERPR",
                    "价格单位": "PEINH"
                }
            }
        }
        
        # 查询历史
        self.query_history = []
    
    def format_material_code(self, material_code: str) -> str:
        """
        格式化物料条码（补0到18位）
        
        参数:
            material_code: 物料条码
            
        返回: 格式化后的物料条码
        """
        if not material_code:
            return material_code
        
        # 移除可能的空格和特殊字符
        cleaned = str(material_code).strip()
        
        # 如果是数字，补0到18位
        if cleaned.isdigit():
            return cleaned.zfill(18)
        
        # 如果不是纯数字，尝试提取数字部分
        numbers = re.findall(r'\d+', cleaned)
        if numbers:
            # 取最长的数字序列
            longest = max(numbers, key=len)
            return longest.zfill(18)
        
        # 如果无法提取数字，返回原值
        return cleaned
    
    def format_production_order(self, order_number: str) -> str:
        """
        格式化生产订单号（补0到12位）
        
        参数:
            order_number: 生产订单号
            
        返回: 格式化后的生产订单号
        """
        if not order_number:
            return order_number
        
        # 移除可能的空格和特殊字符
        cleaned = str(order_number).strip()
        
        # 如果是数字，补0到12位
        if cleaned.isdigit():
            return cleaned.zfill(12)
        
        # 如果不是纯数字，尝试提取数字部分
        numbers = re.findall(r'\d+', cleaned)
        if numbers:
            # 取最长的数字序列
            longest = max(numbers, key=len)
            return longest.zfill(12)
        
        # 如果无法提取数字，返回原值
        return cleaned
    
    def format_bapi_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        格式化BAPI参数
        
        参数:
            params: BAPI参数
            
        返回: 格式化后的参数
        """
        if not params:
            return {}
        
        formatted_params = params.copy()
        
        for key, value in formatted_params.items():
            if isinstance(value, str):
                # 物料号格式化
                if key.upper() in ["MATERIAL", "MATNR"]:
                    formatted_params[key] = self.format_material_code(value)
                
                # 生产订单号格式化
                elif key.upper() in ["ORDER_NUMBER", "AUFNR"]:
                    formatted_params[key] = self.format_production_order(value)
                
                # 日期格式化（YYYY-MM-DD -> YYYYMMDD）
                elif self._looks_like_date(value):
                    formatted_params[key] = self._format_date(value)
        
        return formatted_params
    
    def _looks_like_date(self, value: str) -> bool:
        """判断字符串是否像日期"""
        date_patterns = [
            r'^\d{4}-\d{1,2}-\d{1,2}$',
            r'^\d{4}/\d{1,2}/\d{1,2}$',
            r'^\d{4}年\d{1,2}月\d{1,2}日$'
        ]
        
        for pattern in date_patterns:
            if re.match(pattern, value):
                return True
        
        return False
    
    def _format_date(self, date_str: str) -> str:
        """格式化日期为YYYYMMDD"""
        try:
            # 尝试不同格式解析
            formats = [
                "%Y-%m-%d",
                "%Y/%m/%d",
                "%Y年%m月%d日"
            ]
            
            for fmt in formats:
                try:
                    dt = datetime.strptime(date_str, fmt)
                    return dt.strftime("%Y%m%d")
                except ValueError:
                    continue
            
            # 如果无法解析，返回原值
            return date_str
            
        except Exception:
            return date_str
    
    def analyze_query_intent(self, query_intent: str, table_name: str) -> Dict[str, Any]:
        """
        分析查询意图
        
        参数:
            query_intent: 查询意图描述
            table_name: 表名
            
        返回: 意图分析结果
        """
        analysis = {
            "original_intent": query_intent,
            "table_name": table_name,
            "query_type": QueryType.DATA_QUERY.value,
            "keywords": [],
            "field_requirements": [],
            "filter_requirements": [],
            "sort_requirements": [],
            "date_constraints": [],
            "value_constraints": [],
            "limit_constraint": None,
            "exact_match": False,
            "fuzzy_search": False
        }
        
        # 转换为小写便于分析
        intent_lower = query_intent.lower()
        
        # 1. 识别查询类型
        if any(word in intent_lower for word in ["统计", "计数", "多少", "总数", "数量", "count"]):
            analysis["query_type"] = QueryType.COUNT_QUERY.value
        elif any(word in intent_lower for word in ["列表", "所有", "全部", "list", "all"]):
            analysis["query_type"] = QueryType.LIST_QUERY.value
        elif any(word in intent_lower for word in ["智能", "自动", "根据", "意图"]):
            analysis["query_type"] = QueryType.INTELLIGENT_QUERY.value
        
        # 2. 识别匹配方式
        if any(word in intent_lower for word in ["精确", "等于", "=", "完全匹配"]):
            analysis["exact_match"] = True
        elif any(word in intent_lower for word in ["模糊", "包含", "类似", "模糊匹配"]):
            analysis["fuzzy_search"] = True
        
        # 3. 提取关键词
        extracted_keywords = []
        for keyword, fields in self.keyword_mapping.items():
            if keyword in query_intent:
                extracted_keywords.append({
                    "keyword": keyword,
                    "fields": fields,
                    "position": query_intent.find(keyword)
                })
        
        # 按出现位置排序
        extracted_keywords.sort(key=lambda x: x["position"])
        analysis["keywords"] = [k["keyword"] for k in extracted_keywords]
        
        # 4. 识别字段要求（通过别名）
        if table_name in self.table_configs:
            table_config = self.table_configs[table_name]
            for alias, field_name in table_config.get("field_aliases", {}).items():
                if alias in query_intent:
                    analysis["field_requirements"].append({
                        "alias": alias,
                        "field": field_name
                    })
        
        # 5. 识别日期约束
        date_patterns = [
            (r'(\d{4})年(\d{1,2})月(\d{1,2})日', "date_exact"),
            (r'(\d{4})-(\d{1,2})-(\d{1,2})', "date_exact"),
            (r'(\d{4})年(\d{1,2})月', "date_month"),
            (r'(\d{4})年', "date_year"),
            (r'最近(\d+)(天|日)', "recent_days"),
            (r'最近(\d+)周', "recent_weeks"),
            (r'最近(\d+)月', "recent_months"),
            (r'最近(\d+)年', "recent_years"),
            (r'(\d{4})年.*到.*(\d{4})年', "date_range_years"),
            (r'(\d{4})年(\d{1,2})月.*到.*(\d{4})年(\d{1,2})月', "date_range_months")
        ]
        
        for pattern, pattern_type in date_patterns:
            matches = re.findall(pattern, query_intent)
            if matches:
                analysis["date_constraints"].append({
                    "pattern": pattern,
                    "type": pattern_type,
                    "matches": matches
                })
        
        # 6. 识别数值约束
        value_patterns = [
            (r'大于(\d+)', "greater_than"),
            (r'小于(\d+)', "less_than"),
            (r'等于(\d+)', "equal_to"),
            (r'(\d+)以上', "greater_equal"),
            (r'(\d+)以下', "less_equal"),
            (r'(\d+)到(\d+)', "between"),
            (r'介于(\d+)和(\d+)之间', "between")
        ]
        
        for pattern, pattern_type in value_patterns:
            matches = re.findall(pattern, query_intent)
            if matches:
                analysis["value_constraints"].append({
                    "pattern": pattern,
                    "type": pattern_type,
                    "matches": matches
                })
        
        # 7. 识别排序要求
        sort_patterns = [
            (r'按(.+?)排序', "field_sort"),
            (r'按(.+?)降序', "desc_sort"),
            (r'按(.+?)升序', "asc_sort"),
            (r'按(.+?)从大到小', "desc_sort"),
            (r'按(.+?)从小到大', "asc_sort")
        ]
        
        for pattern, pattern_type in sort_patterns:
            match = re.search(pattern, query_intent)
            if match:
                sort_field = match.group(1)
                direction = "DESCEND" if "降序" in pattern_type or "从大到小" in pattern_type else "ASCEND"
                analysis["sort_requirements"].append({
                    "field": sort_field,
                    "direction": direction,
                    "type": pattern_type
                })
        
        # 8. 识别数量限制
        limit_pattern = r'[前后显示](\d+)[个条项]'
        limit_match = re.search(limit_pattern, query_intent)
        if limit_match:
            analysis["limit_constraint"] = int(limit_match.group(1))
        
        return analysis
    
    def build_table_query(self,
                         table_name: str,
                         fields: List[str] = None,
                         filters: List[Dict] = None,
                         orders: List[Dict] = None,
                         page_size: int = 10000,
                         language_table: str = None) -> Dict[str, Any]:
        """
        构建表查询配置
        
        参数:
            table_name: 表名
            fields: 返回字段列表
            filters: 过滤条件列表
            orders: 排序条件列表
            page_size: 每页数量
            language_table: 语言表
            
        返回: 查询配置
        """
        query_config = {
            "table_name": table_name,
            "fields": fields or [],
            "filters": filters or [],
            "orders": orders or [],
            "page_size": page_size,
            "language_table": language_table
        }
        
        # 如果未指定字段，使用默认字段
        if not query_config["fields"] and table_name in self.table_configs:
            table_config = self.table_configs[table_name]
            query_config["fields"] = table_config.get("essential_fields", [])[:10]  # 限制前10个字段
        
        # 如果未指定语言表，根据表配置确定
        if not query_config["language_table"] and table_name in self.table_configs:
            table_config = self.table_configs[table_name]
            query_config["language_table"] = table