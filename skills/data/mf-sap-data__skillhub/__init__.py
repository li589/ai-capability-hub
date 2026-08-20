"""
SAP 数据查询 Skill
明辉集团专用 - SAP数据查询工具
"""

__version__ = "1.0.0"
__author__ = "明辉集团 IT 部门"
__description__ = "SAP数据查询Skill，支持企业微信认证、BAPI调用、表数据查询"

from .core.auth import MFAuthSkill
from .core.bapi_client import SAPBAPIClient
from .core.table_client import SAPTableClient
from .core.query_builder import SAPQueryBuilder
from .config.settings import SAPConfig

class SAPDataQuerySkill:
    """SAP数据查询Skill主类"""
    
    def __init__(self, config_path: str = None):
        """
        初始化SAP数据查询Skill
        
        参数:
            config_path: 配置文件路径，默认为None使用默认配置
        """
        self.config = SAPConfig(config_path)
        self.auth_skill = MFAuthSkill()
        self.bapi_client = None
        self.table_client = None
        self.query_builder = SAPQueryBuilder()
        
        # 状态跟踪
        self.is_authenticated = False
        self.current_ticket = None
        self.query_history = []
        
    def authenticate(self, work_code: str = None, identity: str = None) -> dict:
        """
        用户认证 - 获取SAP访问票据
        
        参数:
            work_code: 工号，默认为None（自动获取）
            identity: 身份证后六位，默认为None（交互式获取）
            
        返回: 认证结果
        """
        try:
            # 如果未提供参数，使用交互式获取
            if not identity:
                identity = self.auth_skill.collect_identity()
            
            if not work_code:
                work_code = self.auth_skill.get_work_code()
            
            # 执行认证
            auth_result = self.auth_skill.authenticate(
                work_code=work_code,
                identity=identity,
                app_name=self.config.app_name,
                app_version=self.config.app_version
            )
            
            if auth_result.get("success"):
                self.current_ticket = auth_result.get("ticket")
                self.is_authenticated = True
                
                # 初始化客户端
                self.bapi_client = SAPBAPIClient(
                    base_url=self.config.base_url,
                    ticket=self.current_ticket
                )
                self.table_client = SAPTableClient(
                    base_url=self.config.base_url,
                    ticket=self.current_ticket
                )
            
            return auth_result
            
        except Exception as e:
            return {
                "success": False,
                "error": f"认证失败: {str(e)}",
                "error_type": "authentication_failed"
            }
    
    def query_bapi(self, rfc_name: str, params: dict = None) -> dict:
        """
        调用SAP BAPI
        
        参数:
            rfc_name: BAPI名称
            params: 调用参数
            
        返回: BAPI调用结果
        """
        if not self.is_authenticated:
            return {
                "success": False,
                "error": "未认证，请先调用authenticate()方法",
                "error_type": "not_authenticated"
            }
        
        try:
            # 自动格式化参数
            formatted_params = self.query_builder.format_bapi_params(params or {})
            
            # 调用BAPI
            result = self.bapi_client.invoke_bapi(rfc_name, formatted_params)
            
            # 记录查询历史
            self.record_query({
                "type": "bapi",
                "rfc_name": rfc_name,
                "params": formatted_params,
                "result": result
            })
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": f"BAPI调用失败: {str(e)}",
                "error_type": "bapi_invoke_failed",
                "rfc_name": rfc_name
            }
    
    def query_table(self, 
                   table_name: str,
                   fields: list = None,
                   filters: list = None,
                   orders: list = None,
                   current_page: int = 0,
                   page_size: int = 10000,
                   language_table: str = None) -> dict:
        """
        查询SAP表数据
        
        参数:
            table_name: 表名
            fields: 返回字段列表
            filters: 过滤条件列表
            orders: 排序条件列表
            current_page: 当前页码（从0开始）
            page_size: 每页数量
            language_table: 语言表
            
        返回: 表查询结果
        """
        if not self.is_authenticated:
            return {
                "success": False,
                "error": "未认证，请先调用authenticate()方法",
                "error_type": "not_authenticated"
            }
        
        try:
            # 智能构建查询
            query_config = self.query_builder.build_table_query(
                table_name=table_name,
                fields=fields,
                filters=filters,
                orders=orders,
                page_size=page_size,
                language_table=language_table
            )
            
            # 执行查询
            result = self.table_client.query(
                table_name=table_name,
                fields=query_config.get("fields"),
                filters=query_config.get("filters"),
                orders=query_config.get("orders"),
                current_page=current_page,
                page_size=page_size,
                language_table=language_table
            )
            
            # 记录查询历史
            self.record_query({
                "type": "table",
                "table_name": table_name,
                "query_config": query_config,
                "result": result
            })
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": f"表查询失败: {str(e)}",
                "error_type": "table_query_failed",
                "table_name": table_name
            }
    
    def intelligent_query(self, 
                         table_name: str,
                         query_intent: str,
                         page_size: int = 10000) -> dict:
        """
        智能查询 - 根据用户意图自动构建查询
        
        参数:
            table_name: 表名
            query_intent: 查询意图描述
            page_size: 每页数量
            
        返回: 智能查询结果
        """
        if not self.is_authenticated:
            return {
                "success": False,
                "error": "未认证，请先调用authenticate()方法",
                "error_type": "not_authenticated"
            }
        
        try:
            # 使用查询构建器分析意图
            intent_analysis = self.query_builder.analyze_query_intent(
                query_intent, table_name
            )
            
            # 获取表结构
            table_structure = self.table_client.get_table_columns(table_name)
            
            # 构建智能查询配置
            query_config = self.query_builder.build_intelligent_query(
                intent_analysis, table_structure, page_size
            )
            
            # 执行查询
            result = self.table_client.query(
                table_name=table_name,
                fields=query_config.get("fields"),
                filters=query_config.get("filters"),
                orders=query_config.get("orders"),
                current_page=0,
                page_size=page_size,
                language_table=query_config.get("language_table")
            )
            
            # 增强结果处理
            enhanced_result = self.query_builder.enhance_query_result(
                result, query_config, intent_analysis
            )
            
            # 记录查询历史
            self.record_query({
                "type": "intelligent",
                "table_name": table_name,
                "query_intent": query_intent,
                "intent_analysis": intent_analysis,
                "query_config": query_config,
                "result": enhanced_result
            })
            
            return enhanced_result
            
        except Exception as e:
            return {
                "success": False,
                "error": f"智能查询失败: {str(e)}",
                "error_type": "intelligent_query_failed",
                "table_name": table_name,
                "query_intent": query_intent
            }
    
    def get_table_columns(self, table_name: str) -> dict:
        """
        获取表结构信息
        
        参数:
            table_name: 表名
            
        返回: 表结构信息
        """
        if not self.is_authenticated:
            return {
                "success": False,
                "error": "未认证，请先调用authenticate()方法",
                "error_type": "not_authenticated"
            }
        
        try:
            columns = self.table_client.get_table_columns(table_name)
            return {
                "success": True,
                "table_name": table_name,
                "columns": columns,
                "columns_count": len(columns)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"获取表结构失败: {str(e)}",
                "error_type": "get_columns_failed",
                "table_name": table_name
            }
    
    def export_results(self, result: dict, format: str = "json", file_path: str = None) -> dict:
        """
        导出查询结果
        
        参数:
            result: 查询结果
            format: 导出格式（json, excel, csv）
            file_path: 文件路径
            
        返回: 导出结果
        """
        try:
            from .utils.exporter import ResultExporter
            
            exporter = ResultExporter()
            export_result = exporter.export(result, format, file_path)
            
            return export_result
            
        except Exception as e:
            return {
                "success": False,
                "error": f"导出失败: {str(e)}",
                "error_type": "export_failed",
                "format": format
            }
    
    def get_query_history(self, limit: int = 10) -> list:
        """
        获取查询历史
        
        参数:
            limit: 返回的历史记录数量
            
        返回: 查询历史列表
        """
        return self.query_history[-limit:] if self.query_history else []
    
    def clear_query_history(self):
        """清空查询历史"""
        self.query_history = []
    
    def record_query(self, query_info: dict):
        """记录查询信息"""
        query_info["timestamp"] = self.query_builder.get_current_timestamp()
        self.query_history.append(query_info)
        
        # 限制历史记录数量
        if len(self.query_history) > 100:
            self.query_history = self.query_history[-100:]
    
    def get_status(self) -> dict:
        """获取Skill状态"""
        return {
            "version": __version__,
            "authenticated": self.is_authenticated,
            "ticket_valid": bool(self.current_ticket),
            "config_loaded": self.config.is_loaded(),
            "query_history_count": len(self.query_history),
            "last_query": self.query_history[-1] if self.query_history else None
        }
    
    def validate_query_params(self, params: dict) -> dict:
        """
        验证查询参数
        
        参数:
            params: 查询参数
            
        返回: 验证结果
        """
        return self.query_builder.validate_params(params)
    
    def format_material_code(self, material_code: str) -> str:
        """
        格式化物料条码（补0到18位）
        
        参数:
            material_code: 物料条码
            
        返回: 格式化后的物料条码
        """
        return self.query_builder.format_material_code(material_code)
    
    def format_production_order(self, order_number: str) -> str:
        """
        格式化生产订单号（补0到12位）
        
        参数:
            order_number: 生产订单号
            
        返回: 格式化后的生产订单号
        """
        return self.query_builder.format_production_order(order_number)


# 导出常用类
__all__ = [
    "SAPDataQuerySkill",
    "MFAuthSkill",
    "SAPBAPIClient",
    "SAPTableClient",
    "SAPQueryBuilder",
    "SAPConfig"
]