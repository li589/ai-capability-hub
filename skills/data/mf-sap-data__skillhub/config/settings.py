"""
SAP 数据查询 Skill 配置管理
"""

import os
import json
from typing import Dict, Any, Optional
from pathlib import Path

class SAPConfig:
    """SAP配置管理类"""
    
    def __init__(self, config_path: str = None):
        """
        初始化配置
        
        参数:
            config_path: 配置文件路径，默认为None使用默认配置
        """
        self.config_path = config_path
        self.config = self._load_config()
        self._validate_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置"""
        # 1. 尝试从指定路径加载
        if self.config_path and os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"加载配置文件失败 {self.config_path}: {e}")
        
        # 2. 尝试从环境变量加载
        env_config = self._load_from_env()
        if env_config:
            return env_config
        
        # 3. 使用默认配置
        return self._get_default_config()
    
    def _load_from_env(self) -> Optional[Dict[str, Any]]:
        """从环境变量加载配置"""
        config = {}
        
        # API端点
        endpoints = {}
        if os.getenv("SAP_AUTH_ENDPOINT"):
            endpoints["auth"] = os.getenv("SAP_AUTH_ENDPOINT")
        if os.getenv("SAP_BAPI_ENDPOINT"):
            endpoints["bapi"] = os.getenv("SAP_BAPI_ENDPOINT")
        if os.getenv("SAP_TABLE_COLUMNS_ENDPOINT"):
            endpoints["table_columns"] = os.getenv("SAP_TABLE_COLUMNS_ENDPOINT")
        if os.getenv("SAP_TABLE_DATA_ENDPOINT"):
            endpoints["table_data"] = os.getenv("SAP_TABLE_DATA_ENDPOINT")
        
        if endpoints:
            config["api_endpoints"] = endpoints
        
        # 应用信息
        app_info = {}
        if os.getenv("SAP_APP_NAME"):
            app_info["app_name"] = os.getenv("SAP_APP_NAME")
        if os.getenv("SAP_APP_VERSION"):
            app_info["app_version"] = os.getenv("SAP_APP_VERSION")
        
        if app_info:
            config["app_info"] = app_info
        
        # 性能配置
        performance = {}
        if os.getenv("SAP_TIMEOUT"):
            performance["timeout"] = int(os.getenv("SAP_TIMEOUT"))
        if os.getenv("SAP_MAX_PAGE_SIZE"):
            performance["max_page_size"] = int(os.getenv("SAP_MAX_PAGE_SIZE"))
        if os.getenv("SAP_DEFAULT_PAGE_SIZE"):
            performance["default_page_size"] = int(os.getenv("SAP_DEFAULT_PAGE_SIZE"))
        if os.getenv("SAP_MAX_PAGES"):
            performance["max_pages"] = int(os.getenv("SAP_MAX_PAGES"))
        
        if performance:
            config["performance"] = performance
        
        return config if config else None
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "api_endpoints": {
                "auth": "https://info02.mingfaigroup.com/api/account/agent/getticket",
                "bapi": "https://info02.mingfaigroup.com/api/sap/sapinvoke/invoke",
                "table_columns": "https://info02.mingfaigroup.com/api/sap/sapinvoke/gettablecolumns",
                "table_data": "https://info02.mingfaigroup.com/api/sap/sapinvoke/gettabledata"
            },
            "app_info": {
                "app_name": "mf.portal.agent",
                "app_version": "1.0"
            },
            "performance": {
                "timeout": 60,
                "max_page_size": 10000,
                "default_page_size": 1000,
                "max_pages": 100
            },
            "formatting": {
                "material_code_length": 18,
                "production_order_length": 12,
                "date_format": "YYYYMMDD"
            },
            "logging": {
                "level": "INFO",
                "file": "logs/sap_query.log",
                "max_size_mb": 10,
                "backup_count": 5
            }
        }
    
    def _validate_config(self):
        """验证配置"""
        required_sections = ["api_endpoints", "app_info"]
        
        for section in required_sections:
            if section not in self.config:
                raise ValueError(f"配置缺少必要部分: {section}")
        
        # 验证API端点
        endpoints = self.config["api_endpoints"]
        required_endpoints = ["auth", "bapi", "table_columns", "table_data"]
        
        for endpoint in required_endpoints:
            if endpoint not in endpoints:
                print(f"警告: 配置缺少API端点: {endpoint}")
        
        # 验证应用信息
        app_info = self.config["app_info"]
        if "app_name" not in app_info:
            app_info["app_name"] = "mf.portal.agent"
        if "app_version" not in app_info:
            app_info["app_version"] = "1.0"
        
        # 确保性能配置存在
        if "performance" not in self.config:
            self.config["performance"] = self._get_default_config()["performance"]
    
    @property
    def base_url(self) -> str:
        """获取基础URL"""
        # 从table_data端点提取基础URL
        table_data_url = self.config["api_endpoints"].get("table_data", "")
        if table_data_url:
            # 移除 /sapinvoke/gettabledata 部分
            if "/sapinvoke/gettabledata" in table_data_url:
                return table_data_url.split("/sapinvoke/gettabledata")[0]
        return "https://info02.mingfaigroup.com/api"
    
    @property
    def auth_endpoint(self) -> str:
        """获取认证端点"""
        return self.config["api_endpoints"].get("auth", "")
    
    @property
    def bapi_endpoint(self) -> str:
        """获取BAPI端点"""
        return self.config["api_endpoints"].get("bapi", "")
    
    @property
    def table_columns_endpoint(self) -> str:
        """获取表结构端点"""
        return self.config["api_endpoints"].get("table_columns", "")
    
    @property
    def table_data_endpoint(self) -> str:
        """获取表数据端点"""
        return self.config["api_endpoints"].get("table_data", "")
    
    @property
    def app_name(self) -> str:
        """获取应用名称"""
        return self.config["app_info"].get("app_name", "mf.portal.agent")
    
    @property
    def app_version(self) -> str:
        """获取应用版本"""
        return self.config["app_info"].get("app_version", "1.0")
    
    @property
    def timeout(self) -> int:
        """获取超时时间（秒）"""
        return self.config["performance"].get("timeout", 60)
    
    @property
    def max_page_size(self) -> int:
        """获取最大页大小"""
        return self.config["performance"].get("max_page_size", 10000)
    
    @property
    def default_page_size(self) -> int:
        """获取默认页大小"""
        return self.config["performance"].get("default_page_size", 1000)
    
    @property
    def max_pages(self) -> int:
        """获取最大页数"""
        return self.config["performance"].get("max_pages", 100)
    
    @property
    def material_code_length(self) -> int:
        """获取物料条码长度"""
        return self.config.get("formatting", {}).get("material_code_length", 18)
    
    @property
    def production_order_length(self) -> int:
        """获取生产订单号长度"""
        return self.config.get("formatting", {}).get("production_order_length", 12)
    
    def get_logging_config(self) -> Dict[str, Any]:
        """获取日志配置"""
        return self.config.get("logging", {})
    
    def update_config(self, updates: Dict[str, Any]):
        """
        更新配置
        
        参数:
            updates: 更新内容
        """
        for key, value in updates.items():
            if isinstance(value, dict) and key in self.config:
                # 合并字典
                self.config[key].update(value)
            else:
                # 直接设置
                self.config[key] = value
        
        # 重新验证
        self._validate_config()
    
    def save_config(self, file_path: str = None):
        """
        保存配置到文件
        
        参数:
            file_path: 文件路径，默认为初始化时的路径
        """
        save_path = file_path or self.config_path
        if not save_path:
            print("未指定保存路径，配置未保存")
            return
        
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            
            print(f"配置已保存到: {save_path}")
            
        except Exception as e:
            print(f"保存配置失败: {e}")
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return self.config.copy()
    
    def is_loaded(self) -> bool:
        """检查配置是否已加载"""
        return bool(self.config)
    
    def validate_endpoints(self) -> Dict[str, bool]:
        """
        验证API端点
        
        返回: 端点验证结果
        """
        import requests
        
        results = {}
        endpoints = self.config["api_endpoints"]
        
        for name, url in endpoints.items():
            if not url:
                results[name] = False
                continue
            
            try:
                # 发送HEAD请求检查端点是否可达
                response = requests.head(url, timeout=5, verify=True)
                results[name] = response.status_code < 400
            except Exception:
                results[name] = False
        
        return results
    
    def create_config_template(self, file_path: str):
        """
        创建配置模板
        
        参数:
            file_path: 模板文件路径
        """
        template = {
            "api_endpoints": {
                "auth": "https://info02.mingfaigroup.com/api/account/agent/getticket",
                "bapi": "https://info02.mingfaigroup.com/api/sap/sapinvoke/invoke",
                "table_columns": "https://info02.mingfaigroup.com/api/sap/sapinvoke/gettablecolumns",
                "table_data": "https://info02.mingfaigroup.com/api/sap/sapinvoke/gettabledata"
            },
            "app_info": {
                "app_name": "mf.portal.agent",
                "app_version": "1.0"
            },
            "performance": {
                "timeout": 60,
                "max_page_size": 10000,
                "default_page_size": 1000,
                "max_pages": 100
            },
            "formatting": {
                "material_code_length": 18,
                "production_order_length": 12,
                "date_format": "YYYYMMDD"
            },
            "logging": {
                "level": "INFO",
                "file": "logs/sap_query.log",
                "max_size_mb": 10,
                "backup_count": 5
            },
            "security": {
                "encrypt_sensitive_data": True,
                "mask_errors": True,
                "log_sanitization": True
            }
        }
        
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(template, f, ensure_ascii=False, indent=2)
            
            print(f"配置模板已创建: {file_path}")
            
        except Exception as e:
            print(f"创建配置模板失败: {e}")


# 配置工具函数
def load_config_from_file(file_path: str) -> Optional[SAPConfig]:
    """
    从文件加载配置
    
    参数:
        file_path: 配置文件路径
        
    返回: SAPConfig实例或None
    """
    try:
        return SAPConfig(file_path)
    except Exception as e:
        print(f"加载配置失败: {e}")
        return None

def create_default_config(file_path: str):
    """
    创建默认配置文件
    
    参数:
        file_path: 配置文件路径
    """
    config = SAPConfig()
    config.save_config(file_path)

def get_config_summary(config: SAPConfig) -> Dict[str, Any]:
    """
    获取配置摘要
    
    参数:
        config: SAPConfig实例
        
    返回: 配置摘要
    """
    if not config:
        return {"error": "配置未加载"}
    
    return {
        "api_endpoints": {
            "auth": config.auth_endpoint[:50] + "..." if len(config.auth_endpoint) > 50 else config.auth_endpoint,
            "bapi": config.bapi_endpoint[:50] + "..." if len(config.bapi_endpoint) > 50 else config.bapi_endpoint,
            "table_data": config.table_data_endpoint[:50] + "..." if len(config.table_data_endpoint) > 50 else config.table_data_endpoint
        },
        "app_info": {
            "name": config.app_name,
            "version": config.app_version
        },
        "performance": {
            "timeout": config.timeout,
            "max_page_size": config.max_page_size,
            "default_page_size": config.default_page_size
        },
        "formatting": {
            "material_code_length": config.material_code_length,
            "production_order_length": config.production_order_length
        }
    }


# 测试函数
def test_config():
    """测试配置功能"""
    print("测试SAP配置管理...")
    
    # 测试默认配置
    config = SAPConfig()
    print(f"默认配置加载: {'成功' if config.is_loaded() else '失败'}")
    print(f"基础URL: {config.base_url}")
    print(f"应用名称: {config.app_name}")
    print(f"超时时间: {config.timeout}秒")
    
    # 测试配置摘要
    summary = get_config_summary(config)
    print(f"配置摘要: {json.dumps(summary, ensure_ascii=False, indent=2)}")
    
    # 测试更新配置
    updates = {
        "performance": {
            "timeout": 90,
            "max_page_size": 5000
        }
    }
    config.update_config(updates)
    print(f"更新后超时时间: {config.timeout}秒")
    print(f"更新后最大页大小: {config.max_page_size}")
    
    print("\n测试完成")


if __name__ == "__main__":
    test_config()