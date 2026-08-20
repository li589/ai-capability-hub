"""
SAP 表数据查询客户端
明辉集团SAP表数据查询模块
"""

import requests
import json
import time
from typing import Dict, List, Any, Optional
from urllib.parse import urlencode
from enum import Enum

class FilterCalculation(Enum):
    """过滤计算符枚举"""
    EMPTY = "Empty"
    EQUAL = "Equal"
    GREAT = "Great"
    LESS = "Less"
    NOT_EQUAL = "NotEqual"
    GREAT_EQUAL = "GreatEqual"
    LESS_EQUAL = "LessEqual"
    BETWEEN = "Between"
    NOT_BETWEEN = "NotBetween"
    LIKE = "Like"
    NOT_LIKE = "NotLike"
    IN = "In"
    NOT_IN = "NotIn"

class OrderDirection(Enum):
    """排序方向枚举"""
    ASCEND = "Ascend"
    DESCEND = "Descend"
    NONE = ""

class SAPTableClient:
    """SAP表数据查询客户端"""
    
    def __init__(self, base_url: str, ticket: str):
        """
        初始化表查询客户端
        
        参数:
            base_url: API基础地址
            ticket: 认证票据
        """
        self.base_url = base_url.rstrip('/')
        self.columns_endpoint = f"{self.base_url}/sapinvoke/gettablecolumns"
        self.data_endpoint = f"{self.base_url}/sapinvoke/gettabledata"
        self.ticket = ticket
        
        # 请求配置
        self.timeout = 60
        self.max_retries = 2
        self.retry_delay = 1
        
        # 默认配置
        self.default_page_size = 10000
        self.max_page_size = 10000
        self.max_pages = 100
        
        # 缓存
        self.table_columns_cache = {}
        self.table_structure_cache = {}
        
        # 性能统计
        self.query_count = 0
        self.total_time = 0
        self.total_rows = 0
        self.error_count = 0
    
    def get_table_columns(self, table_name: str, use_cache: bool = True) -> List[Dict[str, Any]]:
        """
        获取表结构信息
        
        参数:
            table_name: 表名
            use_cache: 是否使用缓存
            
        返回: 表结构列表
        """
        if use_cache and table_name in self.table_columns_cache:
            print(f"使用缓存的表结构: {table_name}")
            return self.table_columns_cache[table_name]
        
        print(f"获取表结构: {table_name}")
        
        try:
            # 构建URL
            query_params = {
                "ticket": self.ticket,
                "tableName": table_name
            }
            url = f"{self.columns_endpoint}?{urlencode(query_params)}"
            
            headers = {
                "User-Agent": "SAPTableClient/1.0",
                "X-Table-Name": table_name
            }
            
            response = requests.get(
                url,
                headers=headers,
                timeout=self.timeout,
                verify=True
            )
            
            if response.status_code != 200:
                print(f"获取表结构失败，状态码: {response.status_code}")
                return []
            
            # 解析响应
            response_data = response.json()
            
            if response_data.get("Code") != 0:
                print(f"API错误: {response_data.get('Message')}")
                return []
            
            columns = response_data.get("Data", [])
            
            # 缓存结果
            if use_cache:
                self.table_columns_cache[table_name] = columns
            
            print(f"获取到 {len(columns)} 个字段")
            return columns
            
        except Exception as e:
            print(f"获取表结构异常: {e}")
            return []
    
    def query(self,
              table_name: str,
              fields: List[str] = None,
              filters: List[Dict] = None,
              orders: List[Dict] = None,
              current_page: int = 0,
              page_size: int = None,
              language_table: str = None) -> Dict[str, Any]:
        """
        查询表数据
        
        参数:
            table_name: 表名
            fields: 返回字段列表
            filters: 过滤条件列表
            orders: 排序条件列表
            current_page: 当前页码（从0开始）
            page_size: 每页数量
            language_table: 语言表
            
        返回: 查询结果
        """
        print(f"查询表数据: {table_name}")
        
        start_time = time.time()
        self.query_count += 1
        
        try:
            # 设置默认值
            if page_size is None:
                page_size = self.default_page_size
            elif page_size > self.max_page_size:
                page_size = self.max_page_size
                print(f"页大小超过限制，自动调整为: {page_size}")
            
            # 验证页码
            if current_page < 0:
                current_page = 0
                print(f"页码不能为负数，自动调整为: {current_page}")
            
            # 准备请求数据
            request_data = {
                "TableName": table_name,
                "CurrentPage": current_page,
                "PageSize": page_size
            }
            
            # 添加可选参数
            if fields:
                request_data["Fields"] = fields
            
            if filters:
                # 验证和格式化过滤条件
                validated_filters = self._validate_filters(filters)
                request_data["Filters"] = validated_filters
            
            if orders:
                # 验证和格式化排序条件
                validated_orders = self._validate_orders(orders)
                request_data["Orders"] = validated_orders
            
            if language_table:
                request_data["LanguageTable"] = language_table
            
            print(f"请求数据: {json.dumps(request_data, ensure_ascii=False, indent=2)}")
            
            # 发送查询请求
            response = self._make_query_request(table_name, request_data)
            
            # 计算执行时间
            execution_time = time.time() - start_time
            self.total_time += execution_time
            
            if response.get("success"):
                # 增强响应数据
                enhanced_response = self._enhance_query_response(
                    table_name, response, execution_time, request_data
                )
                
                # 更新统计
                data = response.get("data", {})
                self.total_rows += len(data.get("Data", []))
                
                print(f"查询成功，执行时间: {execution_time:.2f}秒")
                return enhanced_response
            else:
                self.error_count += 1
                print(f"查询失败: {response.get('error')}")
                return response
            
        except Exception as e:
            self.error_count += 1
            execution_time = time.time() - start_time
            
            error_msg = f"查询异常: {str(e)}"
            print(error_msg)
            
            return {
                "success": False,
                "error": error_msg,
                "error_type": "query_exception",
                "table_name": table_name,
                "execution_time": execution_time,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
    
    def _validate_filters(self, filters: List[Dict]) -> List[Dict]:
        """
        验证过滤条件
        
        参数:
            filters: 过滤条件列表
            
        返回: 验证后的过滤条件
        """
        validated_filters = []
        
        for i, filter_cond in enumerate(filters):
            # 复制条件
            validated = filter_cond.copy()
            
            # 验证必要字段
            if "FieldName" not in validated:
                print(f"警告: 过滤条件 {i} 缺少 FieldName，已跳过")
                continue
            
            # 验证计算符
            if "Calculation" in validated:
                calc = validated["Calculation"]
                try:
                    # 确保计算符有效
                    FilterCalculation(calc)
                except ValueError:
                    print(f"警告: 过滤条件 {i} 的计算符 '{calc}' 无效，使用默认值")
                    validated["Calculation"] = FilterCalculation.EQUAL.value
            
            # 验证逻辑运算符
            if "Logic" in validated:
                logic = validated["Logic"]
                if logic not in ["And", "Or", ""]:
                    print(f"警告: 过滤条件 {i} 的逻辑运算符 '{logic}' 无效，使用空值")
                    validated["Logic"] = ""
            
            validated_filters.append(validated)
        
        return validated_filters
    
    def _validate_orders(self, orders: List[Dict]) -> List[Dict]:
        """
        验证排序条件
        
        参数:
            orders: 排序条件列表
            
        返回: 验证后的排序条件
        """
        validated_orders = []
        
        for i, order_cond in enumerate(orders):
            # 复制条件
            validated = order_cond.copy()
            
            # 验证必要字段
            if "FieldName" not in validated:
                print(f"警告: 排序条件 {i} 缺少 FieldName，已跳过")
                continue
            
            # 验证方向
            if "Direction" in validated:
                direction = validated["Direction"]
                try:
                    # 确保方向有效
                    OrderDirection(direction)
                except ValueError:
                    print(f"警告: 排序条件 {i} 的方向 '{direction}' 无效，使用默认值")
                    validated["Direction"] = OrderDirection.ASCEND.value
            else:
                validated["Direction"] = OrderDirection.ASCEND.value
            
            validated_orders.append(validated)
        
        return validated_orders
    
    def _make_query_request(self, table_name: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        发送查询请求
        
        参数:
            table_name: 表名
            request_data: 请求数据
            
        返回: 响应数据
        """
        # 构建URL
        query_params = {"ticket": self.ticket}
        url = f"{self.data_endpoint}?{urlencode(query_params)}"
        
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "SAPTableClient/1.0",
            "X-Table-Name": table_name
        }
        
        for attempt in range(self.max_retries):
            try:
                print(f"发送查询请求 (尝试 {attempt + 1}/{self.max_retries})...")
                
                response = requests.post(
                    url,
                    json=request_data,
                    headers=headers,
                    timeout=self.timeout,
                    verify=True
                )
                
                print(f"响应状态码: {response.status_code}")
                
                # 检查HTTP状态码
                if response.status_code != 200:
                    error_msg = f"HTTP错误: {response.status_code}"
                    return {
                        "success": False,
                        "error": error_msg,
                        "error_type": "http_error",
                        "status_code": response.status_code,
                        "table_name": table_name
                    }
                
                # 解析响应数据
                try:
                    response_data = response.json()
                except json.JSONDecodeError:
                    return {
                        "success": False,
                        "error": "响应数据格式错误",
                        "error_type": "json_decode_error",
                        "table_name": table_name
                    }
                
                # 检查API响应状态
                if response_data.get("Code") != 0:
                    error_msg = response_data.get("Message", "查询失败")
                    return {
                        "success": False,
                        "error": error_msg,
                        "error_type": "api_error",
                        "api_code": response_data.get("Code"),
                        "table_name": table_name
                    }
                
                # 提取数据
                data = response_data.get("Data", {})
                
                return {
                    "success": True,
                    "data": data,
                    "raw_response": response_data,
                    "table_name": table_name
                }
                
            except requests.exceptions.Timeout:
                if attempt == self.max_retries - 1:
                    return {
                        "success": False,
                        "error": f"请求超时 ({self.timeout}秒)",
                        "error_type": "request_timeout",
                        "table_name": table_name
                    }
                print(f"请求超时，{self.retry_delay}秒后重试...")
                time.sleep(self.retry_delay)
                continue
                
            except requests.exceptions.ConnectionError:
                if attempt == self.max_retries - 1:
                    return {
                        "success": False,
                        "error": "无法连接到SAP服务器",
                        "error_type": "connection_error",
                        "table_name": table_name
                    }
                print(f"连接错误，{self.retry_delay}秒后重试...")
                time.sleep(self.retry_delay)
                continue
                
            except Exception as e:
                if attempt == self.max_retries - 1:
                    return {
                        "success": False,
                        "error": f"请求异常: {str(e)}",
                        "error_type": "request_exception",
                        "table_name": table_name
                    }
                print(f"请求错误: {e}，{self.retry_delay}秒后重试...")
                time.sleep(self.retry_delay)
                continue
    
    def _enhance_query_response(self,
                               table_name: str,
                               response: Dict[str, Any],
                               execution_time: float,
                               request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        增强查询响应数据
        
        参数:
            table_name: 表名
            response: 原始响应
            execution_time: 执行时间
            request_data: 请求数据
            
        返回: 增强后的响应
        """
        data = response.get("data", {})
        
        # 获取表结构信息
        columns = self.get_table_columns(table_name)
        
        # 分析数据结构
        structure_info = self._analyze_query_structure(data, columns)
        
        # 统计数据量
        statistics = self._calculate_query_statistics(data, request_data)
        
        # 字段映射信息
        field_mapping = self._create_field_mapping(data.get("Fields", []), columns)
        
        enhanced_response = {
            "success": True,
            "table_name": table_name,
            "execution_time": execution_time,
            "query_config": {
                "fields": request_data.get("Fields"),
                "filters": request_data.get("Filters"),
                "orders": request_data.get("Orders"),
                "page_size": request_data.get("PageSize"),
                "current_page": request_data.get("CurrentPage")
            },
            "data": data.get("Data", []),
            "statistics": statistics,
            "structure": structure_info,
            "field_mapping": field_mapping,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "raw_response": response.get("raw_response")
        }
        
        return enhanced_response
    
    def _analyze_query_structure(self, data: Dict[str, Any], columns: List[Dict]) -> Dict[str, Any]:
        """
        分析查询数据结构
        
        参数:
            data: 查询返回数据
            columns: 表结构信息
            
        返回: 结构信息
        """
        structure_info = {
            "total_rows": data.get("RowCount", 0),
            "returned_rows": len(data.get("Data", [])),
            "fields_count": len(data.get("Fields", [])),
            "columns_info": []
        }
        
        # 获取字段信息
        fields = data.get("Fields", [])
        for field in fields:
            column_info = self._find_column_info(field, columns)
            structure_info["columns_info"].append({
                "field_name": field,
                "display_name": column_info.get("DisplayName", field),
                "data_type": column_info.get("DataType", "未知"),
                "length": column_info.get("Length", 0),
                "description": column_info.get("Description", "")
            })
        
        return structure_info
    
    def _find_column_info(self, field_name: str, columns: List[Dict]) -> Dict[str, Any]:
        """查找字段信息"""
        for column in columns:
            if column.get("ColumnName") == field_name:
                return column
        return {}
    
    def _calculate_query_statistics(self, data: Dict[str, Any], request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        计算查询统计信息
        
        参数:
            data: 查询返回数据
            request_data: 请求数据
            
        返回: 统计信息
        """
        row_count = data.get("RowCount", 0)
        returned_rows = len(data.get("Data", []))
        page_size = request_data.get("PageSize", self.default_page_size)
        current_page = request_data.get("CurrentPage", 0)
        
        # 计算总页数
        total_pages = (row_count + page_size - 1) // page_size if page_size > 0 else 0
        
        return {
            "row_count": row_count,
            "query_rows": returned_rows,
            "page_size": page_size,
            "current_page": current_page,
            "total_pages": total_pages,
            "has_more": returned_rows > 0 and (current_page + 1) < total_pages,
            "fields_count": len(data.get("Fields", []))
        }
    
    def _create_field_mapping(self, fields: List[str], columns: List[Dict]) -> List[Dict[str, Any]]:
        """
        创建字段映射
        
        参数:
            fields: 字段列表
            columns: 表结构信息
            
        返回: 字段映射列表
        """
        field_mapping = []
        
        for field in fields:
            column_info = self._find_column_info(field, columns)
            field_mapping.append({
                "field_name": field,
                "display_name": column_info.get("DisplayName", field),
                "data_type": column_info.get("DataType", "未知"),
                "is_key": column_info.get("IsKey", False),
                "description": column_info.get("Description", "")
            })
        
        return field_mapping
    
    def create_filter(self,
                     field_name: str,
                     calculation: str,
                     lower_value: Any = None,
                     high_value: Any = None,
                     logic: str = "") -> Dict[str, Any]:
        """
        创建过滤条件
        
        参数:
            field_name: 字段名
            calculation: 计算符
            lower_value: 低值
            high_value: 高值（