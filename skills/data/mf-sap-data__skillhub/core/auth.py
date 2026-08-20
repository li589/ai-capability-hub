"""
企业微信认证模块
明辉集团SAP访问认证
"""

import requests
import json
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

class MFAuthSkill:
    """企业微信认证Skill"""
    
    def __init__(self, base_url: str = None):
        """
        初始化认证模块
        
        参数:
            base_url: API基础地址，默认为None使用默认地址
        """
        self.base_url = base_url or "https://info02.mingfaigroup.com/api/account/agent"
        self.auth_endpoint = f"{self.base_url}/getticket"
        
        # 认证信息缓存
        self.current_ticket = None
        self.ticket_expiry = None
        self.user_info = {}
        
        # 请求配置
        self.timeout = 30
        self.max_retries = 3
        
    def collect_identity(self) -> str:
        """
        收集用户身份证后六位（交互式）
        
        返回: 身份证后六位
        """
        print("=" * 50)
        print("SAP 系统认证")
        print("=" * 50)
        print("请输入您的身份证后六位数字：")
        
        while True:
            try:
                identity = input("身份证后六位: ").strip()
                
                # 验证输入
                if self.validate_identity(identity):
                    return identity
                else:
                    print("输入无效，请输入6位数字")
                    
            except KeyboardInterrupt:
                print("\n认证已取消")
                raise
            except Exception as e:
                print(f"输入错误: {e}")
    
    def get_work_code(self) -> str:
        """
        获取工号（从环境或交互式）
        
        返回: 工号
        """
        # 这里可以根据实际情况从环境变量或配置获取
        # 暂时返回默认值，实际使用中需要根据具体情况调整
        return "MS00051286"
    
    def validate_identity(self, identity: str) -> bool:
        """
        验证身份证后六位格式
        
        参数:
            identity: 身份证后六位
            
        返回: 是否有效
        """
        if not identity:
            return False
        
        # 检查是否为6位数字
        if len(identity) != 6:
            return False
        
        if not identity.isdigit():
            return False
        
        return True
    
    def authenticate(self, 
                    work_code: str,
                    identity: str,
                    app_name: str = "mf.portal.agent",
                    app_version: str = "1.0") -> Dict[str, Any]:
        """
        执行认证
        
        参数:
            work_code: 工号
            identity: 身份证后六位
            app_name: 应用名称
            app_version: 应用版本
            
        返回: 认证结果
        """
        print(f"开始认证，工号: {work_code}")
        
        try:
            # 验证输入
            if not self.validate_identity(identity):
                return {
                    "success": False,
                    "error": "身份证格式无效，请输入6位数字",
                    "error_type": "invalid_identity_format"
                }
            
            # 准备请求参数
            params = {
                "WorkCode": work_code,
                "Identity": identity,
                "AppName": app_name,
                "AppVersion": app_version
            }
            
            print(f"请求参数: {json.dumps(params, ensure_ascii=False)}")
            
            # 发送认证请求
            response = self._make_request(params)
            
            if response.get("success"):
                # 解析响应数据
                auth_data = response.get("data", {})
                
                # 提取认证信息
                self.current_ticket = auth_data.get("Ticket")
                self.user_info = {
                    "work_code": auth_data.get("WorkCode"),
                    "user_name": auth_data.get("UserName"),
                    "department": auth_data.get("Department")
                }
                
                # 设置票据有效期（假设24小时）
                self.ticket_expiry = datetime.now() + timedelta(hours=24)
                
                print(f"认证成功！用户: {self.user_info.get('user_name')}")
                print(f"票据有效期至: {self.ticket_expiry.strftime('%Y-%m-%d %H:%M:%S')}")
                
                return {
                    "success": True,
                    "ticket": self.current_ticket,
                    "work_code": self.user_info.get("work_code"),
                    "user_name": self.user_info.get("user_name"),
                    "expires_at": self.ticket_expiry.isoformat(),
                    "department": self.user_info.get("department"),
                    "message": "认证成功"
                }
            else:
                error_msg = response.get("error", "未知错误")
                print(f"认证失败: {error_msg}")
                
                return {
                    "success": False,
                    "error": error_msg,
                    "error_type": response.get("error_type", "authentication_failed"),
                    "suggestion": self._get_auth_suggestion(error_msg)
                }
                
        except requests.exceptions.Timeout:
            error_msg = "认证请求超时"
            print(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "error_type": "request_timeout",
                "suggestion": "请检查网络连接后重试"
            }
            
        except requests.exceptions.ConnectionError:
            error_msg = "无法连接到认证服务器"
            print(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "error_type": "connection_error",
                "suggestion": "请检查网络连接和服务器地址"
            }
            
        except Exception as e:
            error_msg = f"认证过程发生错误: {str(e)}"
            print(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "error_type": "authentication_error",
                "suggestion": "请联系系统管理员"
            }
    
    def _make_request(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        发送认证请求
        
        参数:
            params: 请求参数
            
        返回: 响应数据
        """
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "MFAuthSkill/1.0"
        }
        
        for attempt in range(self.max_retries):
            try:
                print(f"发送认证请求 (尝试 {attempt + 1}/{self.max_retries})...")
                
                response = requests.post(
                    self.auth_endpoint,
                    json=params,
                    headers=headers,
                    timeout=self.timeout,
                    verify=True  # 启用SSL验证
                )
                
                print(f"响应状态码: {response.status_code}")
                
                # 检查HTTP状态码
                if response.status_code != 200:
                    return {
                        "success": False,
                        "error": f"HTTP错误: {response.status_code}",
                        "error_type": "http_error",
                        "status_code": response.status_code
                    }
                
                # 解析响应数据
                response_data = response.json()
                print(f"响应数据: {json.dumps(response_data, ensure_ascii=False)}")
                
                # 检查API响应状态
                if response_data.get("Code") != 0:
                    error_msg = response_data.get("Message", "认证失败")
                    return {
                        "success": False,
                        "error": error_msg,
                        "error_type": "api_error",
                        "api_code": response_data.get("Code")
                    }
                
                # 提取数据
                data = response_data.get("Data", {})
                
                # 验证必要字段
                required_fields = ["Ticket", "WorkCode", "UserName"]
                for field in required_fields:
                    if field not in data:
                        return {
                            "success": False,
                            "error": f"响应缺少必要字段: {field}",
                            "error_type": "missing_field"
                        }
                
                return {
                    "success": True,
                    "data": data,
                    "raw_response": response_data
                }
                
            except requests.exceptions.Timeout:
                if attempt == self.max_retries - 1:
                    raise
                print(f"请求超时，{self.timeout}秒后重试...")
                continue
                
            except json.JSONDecodeError:
                return {
                    "success": False,
                    "error": "响应数据格式错误",
                    "error_type": "json_decode_error"
                }
                
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise
                print(f"请求错误: {e}，重试中...")
                continue
    
    def _get_auth_suggestion(self, error_msg: str) -> str:
        """
        根据错误信息提供建议
        
        参数:
            error_msg: 错误信息
            
        返回: 建议信息
        """
        error_lower = error_msg.lower()
        
        suggestions = {
            "身份证": "请检查身份证后六位是否正确",
            "工号": "请检查工号是否正确",
            "权限": "您的账号没有访问权限，请联系管理员",
            "过期": "认证已过期，请重新认证",
            "网络": "请检查网络连接",
            "服务器": "服务器暂时不可用，请稍后重试"
        }
        
        for keyword, suggestion in suggestions.items():
            if keyword in error_lower:
                return suggestion
        
        return "请检查输入信息或联系系统管理员"
    
    def is_ticket_valid(self) -> bool:
        """
        检查票据是否有效
        
        返回: 票据是否有效
        """
        if not self.current_ticket or not self.ticket_expiry:
            return False
        
        return datetime.now() < self.ticket_expiry
    
    def get_ticket(self) -> Optional[str]:
        """
        获取当前票据
        
        返回: 票据字符串或None
        """
        if self.is_ticket_valid():
            return self.current_ticket
        return None
    
    def refresh_ticket(self) -> Dict[str, Any]:
        """
        刷新票据（重新认证）
        
        返回: 刷新结果
        """
        print("刷新认证票据...")
        
        # 清除当前票据
        self.current_ticket = None
        self.ticket_expiry = None
        
        # 重新收集身份信息
        identity = self.collect_identity()
        work_code = self.get_work_code()
        
        # 重新认证
        return self.authenticate(work_code, identity)
    
    def get_user_info(self) -> Dict[str, Any]:
        """
        获取用户信息
        
        返回: 用户信息
        """
        return self.user_info.copy()
    
    def logout(self):
        """注销登录"""
        print("注销用户认证...")
        self.current_ticket = None
        self.ticket_expiry = None
        self.user_info = {}
        print("注销完成")
    
    def get_auth_status(self) -> Dict[str, Any]:
        """
        获取认证状态
        
        返回: 认证状态信息
        """
        return {
            "authenticated": self.is_ticket_valid(),
            "ticket": self.current_ticket,
            "ticket_expiry": self.ticket_expiry.isoformat() if self.ticket_expiry else None,
            "user_info": self.user_info,
            "remaining_time": self._get_remaining_time()
        }
    
    def _get_remaining_time(self) -> Optional[int]:
        """
        获取票据剩余时间（秒）
        
        返回: 剩余秒数或None
        """
        if not self.ticket_expiry:
            return None
        
        remaining = self.ticket_expiry - datetime.now()
        return max(0, int(remaining.total_seconds()))


# 测试函数
def test_auth():
    """测试认证功能"""
    print("测试企业微信认证...")
    
    auth_skill = MFAuthSkill()
    
    # 测试身份验证
    test_identities = ["123456", "abc123", "123", "1234567", ""]
    for identity in test_identities:
        is_valid = auth_skill.validate_identity(identity)
        print(f"身份证 '{identity}': {'有效' if is_valid else '无效'}")
    
    # 获取工号
    work_code = auth_skill.get_work_code()
    print(f"工号: {work_code}")
    
    print("\n测试完成")


if __name__ == "__main__":
    test_auth()