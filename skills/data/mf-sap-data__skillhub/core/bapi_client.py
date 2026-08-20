"""
SAP BAPI调用客户端
明辉集团SAP BAPI调用模块
"""

import requests
import json
import time
from typing import Dict, List, Any, Optional
from urllib.parse import urlencode

class SAPBAPIClient:
    """SAP BAPI调用客户端"""
    
    def __init__(self, base_url: str, ticket: str):
        """
        初始化BAPI客户端
        
        参数:
            base_url: API基础地址
            ticket: 认证票据
        """
        self.base_url = base_url.rstrip('/')
        self.bapi_endpoint = f"{self.base_url}/sapinvoke/invoke"
        self.ticket = ticket
        
        # 请求配置
        self.timeout = 60
        self.max_retries = 2
        self.retry_delay = 1
        
        # BAPI映射配置
        self.bapi_configs = self._load_bapi_configs()
        
        # 性能统计
        self.call_count = 0
        self.total_time = 0
        self.error_count = 0
    
    def _load_bapi_configs(self) -> Dict[str, Dict]:
        """加载BAPI配置"""
        return {
            "BAPI_MATERIAL_GET_DETAIL": {
                "name": "获取物料详细信息",
                "description": "获取物料主数据详细信息",
                "input_params": ["MATERIAL"],
                "output_structure": ["MATERIAL_GENERAL_DATA", "PLANT_DATA"],
                "requires_formatting": ["MATERIAL"]
            },
            "BAPI_MATERIAL_GET_LIST": {
                "name": "获取物料列表",
                "description": "根据条件获取物料列表",
                "input_params": ["MATERIAL", "MATERIAL_TYPE", "INDUSTRY_SECTOR"],
                "output_structure": ["MATERIAL_LIST"],
                "requires_formatting": ["MATERIAL"]
            },
            "BAPI_PO_GETDETAIL": {
                "name": "获取采购订单详情",
                "description": "获取采购订单详细信息",
                "input_params": ["PURCHASEORDER"],
                "output_structure": ["PO_HEADER", "PO_ITEMS"],
                "requires_formatting": []
            },
            "BAPI_SALESORDER_GETDETAIL": {
                "name": "获取销售订单详情",
                "description": "获取销售订单详细信息",
                "input_params": ["SALESDOCUMENT"],
                "output_structure": ["ORDER_HEADER_IN", "ORDER_ITEMS_IN"],
                "requires_formatting": []
            },
            "BAPI_PRODORD_GET_DETAIL": {
                "name": "获取生产订单详情",
                "description": "获取生产订单详细信息",
                "input_params": ["ORDER_NUMBER"],
                "output_structure": ["ORDER_HEADER", "ORDER_OPERATIONS"],
                "requires_formatting": ["ORDER_NUMBER"]
            }
        }
    
    def invoke_bapi(self, rfc_name: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        调用SAP BAPI
        
        参数:
            rfc_name: BAPI名称
            params: 调用参数
            
        返回: BAPI调用结果
        """
        print(f"调用BAPI: {rfc_name}")
        
        start_time = time.time()
        self.call_count += 1
        
        try:
            # 验证BAPI名称
            if rfc_name not in self.bapi_configs:
                print(f"警告: BAPI '{rfc_name}' 不在配置列表中")
            
            # 准备请求参数
            request_params = params or {}
            
            # 自动格式化参数
            formatted_params = self._format_bapi_params(rfc_name, request_params)
            
            # 构建请求数据
            request_data = {
                "RfcName": rfc_name,
                "Data": formatted_params
            }
            
            print(f"请求数据: {json.dumps(request_data, ensure_ascii=False)}")
            
            # 发送请求
            response = self._make_bapi_request(rfc_name, request_data)
            
            # 计算执行时间
            execution_time = time.time() - start_time
            self.total_time += execution_time
            
            if response.get("success"):
                # 增强响应数据
                enhanced_response = self._enhance_bapi_response(
                    rfc_name, response, execution_time
                )
                
                print(f"BAPI调用成功，执行时间: {execution_time:.2f}秒")
                return enhanced_response
            else:
                self.error_count += 1
                print(f"BAPI调用失败: {response.get('error')}")
                return response
            
        except Exception as e:
            self.error_count += 1
            execution_time = time.time() - start_time
            
            error_msg = f"BAPI调用异常: {str(e)}"
            print(error_msg)
            
            return {
                "success": False,
                "error": error_msg,
                "error_type": "bapi_exception",
                "rfc_name": rfc_name,
                "execution_time": execution_time,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
    
    def _format_bapi_params(self, rfc_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        格式化BAPI参数
        
        参数:
            rfc_name: BAPI名称
            params: 原始参数
            
        返回: 格式化后的参数
        """
        formatted_params = params.copy()
        
        # 获取BAPI配置
        bapi_config = self.bapi_configs.get(rfc_name, {})
        format_fields = bapi_config.get("requires_formatting", [])
        
        # 格式化特定字段
        for field in format_fields:
            if field in formatted_params:
                value = formatted_params[field]
                
                # 物料号格式化（补0到18位）
                if field == "MATERIAL" and isinstance(value, str) and value.isdigit():
                    formatted_params[field] = value.zfill(18)
                    print(f"格式化物料号: {value} -> {formatted_params[field]}")
                
                # 生产订单号格式化（补0到12位）
                elif field == "ORDER_NUMBER" and isinstance(value, str) and value.isdigit():
                    formatted_params[field] = value.zfill(12)
                    print(f"格式化生产订单号: {value} -> {formatted_params[field]}")
        
        return formatted_params
    
    def _make_bapi_request(self, rfc_name: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        发送BAPI请求
        
        参数:
            rfc_name: BAPI名称
            request_data: 请求数据
            
        返回: 响应数据
        """
        # 构建URL
        query_params = {"ticket": self.ticket}
        url = f"{self.bapi_endpoint}?{urlencode(query_params)}"
        
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "SAPBAPIClient/1.0",
            "X-BAPI-Name": rfc_name
        }
        
        for attempt in range(self.max_retries):
            try:
                print(f"发送BAPI请求 (尝试 {attempt + 1}/{self.max_retries})...")
                
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
                        "rfc_name": rfc_name
                    }
                
                # 解析响应数据
                try:
                    response_data = response.json()
                except json.JSONDecodeError:
                    return {
                        "success": False,
                        "error": "响应数据格式错误",
                        "error_type": "json_decode_error",
                        "rfc_name": rfc_name
                    }
                
                print(f"响应数据: {json.dumps(response_data, ensure_ascii=False, indent=2)}")
                
                # 检查API响应状态
                if response_data.get("Code") != 0:
                    error_msg = response_data.get("Message", "BAPI调用失败")
                    return {
                        "success": False,
                        "error": error_msg,
                        "error_type": "api_error",
                        "api_code": response_data.get("Code"),
                        "rfc_name": rfc_name
                    }
                
                # 提取数据
                data = response_data.get("Data", {})
                
                return {
                    "success": True,
                    "data": data,
                    "raw_response": response_data,
                    "rfc_name": rfc_name
                }
                
            except requests.exceptions.Timeout:
                if attempt == self.max_retries - 1:
                    return {
                        "success": False,
                        "error": f"请求超时 ({self.timeout}秒)",
                        "error_type": "request_timeout",
                        "rfc_name": rfc_name
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
                        "rfc_name": rfc_name
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
                        "rfc_name": rfc_name
                    }
                print(f"请求错误: {e}，{self.retry_delay}秒后重试...")
                time.sleep(self.retry_delay)
                continue
    
    def _enhance_bapi_response(self, 
                              rfc_name: str, 
                              response: Dict[str, Any], 
                              execution_time: float) -> Dict[str, Any]:
        """
        增强BAPI响应数据
        
        参数:
            rfc_name: BAPI名称
            response: 原始响应
            execution_time: 执行时间
            
        返回: 增强后的响应
        """
        data = response.get("data", {})
        
        # 获取BAPI配置
        bapi_config = self.bapi_configs.get(rfc_name, {})
        
        # 分析数据结构
        structure_info = self._analyze_bapi_structure(data)
        
        # 统计数据量
        statistics = self._calculate_bapi_statistics(data, bapi_config)
        
        enhanced_response = {
            "success": True,
            "rfc_name": rfc_name,
            "bapi_name": bapi_config.get("name", rfc_name),
            "description": bapi_config.get("description", ""),
            "execution_time": execution_time,
            "data": data,
            "structure": structure_info,
            "statistics": statistics,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "raw_response": response.get("raw_response")
        }
        
        return enhanced_response
    
    def _analyze_bapi_structure(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析BAPI数据结构
        
        参数:
            data: BAPI返回数据
            
        返回: 结构信息
        """
        structure_info = {
            "tables": [],
            "structures": [],
            "simple_fields": []
        }
        
        for key, value in data.items():
            if isinstance(value, list):
                # 表类型
                if value:
                    first_item = value[0]
                    if isinstance(first_item, dict):
                        structure_info["tables"].append({
                            "name": key,
                            "row_count": len(value),
                            "columns": list(first_item.keys()) if first_item else []
                        })
            elif isinstance(value, dict):
                # 结构类型
                structure_info["structures"].append({
                    "name": key,
                    "fields": list(value.keys())
                })
            else:
                # 简单字段
                structure_info["simple_fields"].append({
                    "name": key,
                    "type": type(value).__name__,
                    "value": str(value)[:100]  # 限制长度
                })
        
        return structure_info
    
    def _calculate_bapi_statistics(self, data: Dict[str, Any], bapi_config: Dict) -> Dict[str, Any]:
        """
        计算BAPI统计信息
        
        参数:
            data: BAPI返回数据
            bapi_config: BAPI配置
            
        返回: 统计信息
        """
        statistics = {
            "tables_count": 0,
            "structures_count": 0,
            "total_rows": 0,
            "fields_count": 0
        }
        
        # 计算表信息
        for key, value in data.items():
            if isinstance(value, list):
                statistics["tables_count"] += 1
                statistics["total_rows"] += len(value)
                if value and isinstance(value[0], dict):
                    statistics["fields_count"] += len(value[0].keys())
            elif isinstance(value, dict):
                statistics["structures_count"] += 1
                statistics["fields_count"] += len(value.keys())
        
        return statistics
    
    def get_available_bapis(self) -> List[Dict[str, Any]]:
        """
        获取可用的BAPI列表
        
        返回: BAPI列表
        """
        bapi_list = []
        
        for rfc_name, config in self.bapi_configs.items():
            bapi_list.append({
                "rfc_name": rfc_name,
                "name": config.get("name", rfc_name),
                "description": config.get("description", ""),
                "input_params": config.get("input_params", []),
                "output_structure": config.get("output_structure", [])
            })
        
        return bapi_list
    
    def get_bapi_info(self, rfc_name: str) -> Optional[Dict[str, Any]]:
        """
        获取BAPI详细信息
        
        参数:
            rfc_name: BAPI名称
            
        返回: BAPI信息或None
        """
        if rfc_name not in self.bapi_configs:
            return None
        
        config = self.bapi_configs[rfc_name]
        
        return {
            "rfc_name": rfc_name,
            "name": config.get("name", rfc_name),
            "description": config.get("description", ""),
            "input_params": config.get("input_params", []),
            "output_structure": config.get("output_structure", []),
            "requires_formatting": config.get("requires_formatting", []),
            "usage_example": self._generate_usage_example(rfc_name, config)
        }
    
    def _generate_usage_example(self, rfc_name: str, config: Dict) -> Dict[str, Any]:
        """生成使用示例"""
        example_params = {}
        
        for param in config.get("input_params", []):
            if param == "MATERIAL":
                example_params[param] = "000000000000001234"
            elif param == "ORDER_NUMBER":
                example_params[param] = "000000005678"
            else:
                example_params[param] = "示例值"
        
        return {
            "python": f"""
skill.query_bapi(
    rfc_name="{rfc_name}",
    params={json.dumps(example_params, indent=4, ensure_ascii=False)}
)
""",
            "parameters": example_params
        }
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """
        获取性能统计
        
        返回: 性能统计信息
        """
        avg_time = self.total_time / self.call_count if self.call_count > 0 else 0
        success_rate = ((self.call_count - self.error_count) / self.call_count * 100) if self.call_count > 0 else 0
        
        return {
            "total_calls": self.call_count,
            "error_calls": self.error_count,
            "success_rate": f"{success_rate:.1f}%",
            "total_time": f"{self.total_time:.2f}秒",
            "average_time": f"{avg_time:.2f}秒",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    
    def validate_bapi_params(self, rfc_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证BAPI参数
        
        参数:
            rfc_name: BAPI名称
            params: 参数
            
        返回: 验证结果
        """
        if rfc_name not in self.bapi_configs:
            return {
                "valid": False,
                "error": f"未知的BAPI: {rfc_name}",
                "suggestion": f"可用BAPI: {', '.join(self.bapi_configs.keys())}"
            }
        
        config = self.bapi_configs[rfc_name]
        required_params = config.get("input_params", [])
        
        missing_params = []
        for param in required_params:
            if param not in params:
                missing_params.append(param)
        
        if missing_params:
            return {
                "valid": False,
                "error": f"缺少必要参数: {', '.join(missing_params)}",
                "missing_params": missing_params,
                "required_params": required_params
            }
        
        return {
            "valid": True,
            "message": "参数验证通过",
            "required_params": required_params,
            "provided_params": list(params.keys())
        }


# 测试函数
def test_bapi_client():
    """测试BAPI客户端"""
    print("测试BAPI客户端...")
    
    # 注意：需要有效的ticket才能实际测试
    client = SAPBAPIClient(
        base_url="https://info02.mingfaigroup.com/api/sap",
        ticket="test_ticket"
    )
    
    # 测试获取BAPI列表
    bapis