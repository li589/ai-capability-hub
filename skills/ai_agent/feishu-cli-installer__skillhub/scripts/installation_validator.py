#!/usr/bin/env python3
"""
飞书CLI一键安装助手 - 安装验证器
验证安装是否成功
"""

import subprocess
import sys
import json
import os


class InstallationValidator:
    """安装验证器"""
    
    def __init__(self):
        self.progress_file = ".lark_cli_install_progress.json"
        self.results = []
    
    def check_lark_cli_version(self) -> dict:
        """检查 lark-cli 版本"""
        try:
            result = subprocess.run(
                ["lark-cli", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                version = result.stdout.strip()
                return {
                    "status": "success",
                    "message": f"lark-cli {version}",
                    "version": version
                }
            else:
                return {
                    "status": "error",
                    "message": "lark-cli 版本检查失败"
                }
        
        except FileNotFoundError:
            return {
                "status": "error",
                "message": "lark-cli 未安装或不在 PATH 中"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"检查 lark-cli 失败: {str(e)}"
            }
    
    def check_lark_cli_help(self) -> dict:
        """检查 lark-cli help 命令"""
        try:
            result = subprocess.run(
                ["lark-cli", "help"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                return {
                    "status": "success",
                    "message": "lark-cli help 正常"
                }
            else:
                return {
                    "status": "error",
                    "message": "lark-cli help 命令失败"
                }
        
        except FileNotFoundError:
            return {
                "status": "error",
                "message": "lark-cli 未安装或不在 PATH 中"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"检查 lark-cli help 失败: {str(e)}"
            }
    
    def check_auth_status(self) -> dict:
        """检查授权状态"""
        try:
            result = subprocess.run(
                ["lark-cli", "auth", "status"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            output = result.stdout + result.stderr
            
            if "logged in" in output.lower() or "已登录" in output:
                return {
                    "status": "success",
                    "message": "lark-cli auth status 正常（已授权）"
                }
            else:
                return {
                    "status": "warning",
                    "message": "lark-cli auth status 正常（未授权）"
                }
        
        except FileNotFoundError:
            return {
                "status": "error",
                "message": "lark-cli 未安装或不在 PATH 中"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"检查授权状态失败: {str(e)}"
            }
    
    def check_config_list(self) -> dict:
        """检查配置列表"""
        try:
            result = subprocess.run(
                ["lark-cli", "config", "list"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                return {
                    "status": "success",
                    "message": "lark-cli config list 正常"
                }
            else:
                return {
                    "status": "warning",
                    "message": "lark-cli config list 有问题"
                }
        
        except FileNotFoundError:
            return {
                "status": "error",
                "message": "lark-cli 未安装或不在 PATH 中"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"检查配置失败: {str(e)}"
            }
    
    def run_all_validations(self) -> dict:
        """运行所有验证"""
        print("🔍 验证安装...\n")
        
        self.results = [
            ("lark-cli version", self.check_lark_cli_version()),
            ("lark-cli help", self.check_lark_cli_help()),
            ("auth status", self.check_auth_status()),
            ("config list", self.check_config_list())
        ]
        
        # 打印结果
        all_success = True
        
        for check_name, result in self.results:
            status_icon = "✅" if result["status"] == "success" else ("⚠️" if result["status"] == "warning" else "❌")
            print(f"  {status_icon} {result['message']}")
            
            if result["status"] == "error":
                all_success = False
        
        print()
        
        # 读取安装信息
        progress_file = ".lark_cli_install_progress.json"
        app_id = None
        if os.path.exists(progress_file):
            with open(progress_file) as f:
                progress = json.load(f)
                app_id = progress.get("app_id")
        
        if all_success:
            print("🎉 安装完成！\n")
            print("📊 安装信息：")
            if app_id:
                print(f"  - App ID: {app_id}")
            print("  - 授权状态: 已授权\n")
            
            print("📚 接下来你可以：")
            print("  1. 运行 lark-cli help 查看所有命令")
            print("  2. 运行 lark-cli auth status 查看登录状态")
            print("  3. 开始使用飞书CLI操作飞书\n")
            
            print("💡 示例：")
            print('  - "帮我创建一篇云文档"')
            print('  - "查看我今天的日程"')
            print('  - "搜索包含\'项目\'的群聊"\n')
            
            return {
                "status": "success",
                "all_success": True,
                "results": dict(self.results)
            }
        else:
            print("⚠️ 安装验证发现问题\n")
            print("请检查上述错误项，或重新运行安装。\n")
            
            return {
                "status": "error",
                "all_success": False,
                "results": dict(self.results)
            }


def main():
    """主函数"""
    validator = InstallationValidator()
    result = validator.run_all_validations()
    
    sys.exit(0 if result["all_success"] else 1)


if __name__ == "__main__":
    main()
