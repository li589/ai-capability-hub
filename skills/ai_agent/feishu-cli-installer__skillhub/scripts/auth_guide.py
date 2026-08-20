#!/usr/bin/env python3
"""
飞书CLI一键安装助手 - 授权引导器
引导用户完成授权
"""

import subprocess
import sys
import json
import os
import time
import re


class AuthGuide:
    """授权引导器"""
    
    def __init__(self):
        self.progress_file = ".lark_cli_install_progress.json"
        self.load_progress()
    
    def load_progress(self):
        """加载安装进度"""
        if os.path.exists(self.progress_file):
            with open(self.progress_file) as f:
                self.progress = json.load(f)
        else:
            self.progress = {
                "step": 0,
                "completed": [],
                "failed": None
            }
    
    def save_progress(self):
        """保存安装进度"""
        with open(self.progress_file, "w") as f:
            json.dump(self.progress, f, indent=2, ensure_ascii=False)
    
    def is_completed(self, step: str) -> bool:
        """检查步骤是否已完成"""
        return step in self.progress["completed"]
    
    def mark_completed(self, step: str):
        """标记步骤为已完成"""
        if step not in self.progress["completed"]:
            self.progress["completed"].append(step)
            self.save_progress()
    
    def mark_failed(self, step: str, error: str):
        """标记步骤为失败"""
        self.progress["failed"] = {"step": step, "error": error}
        self.save_progress()
    
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
            
            # 检查是否已授权
            if "logged in" in output.lower() or "已登录" in output:
                return {
                    "status": "success",
                    "authorized": True,
                    "message": "已授权"
                }
            else:
                return {
                    "status": "success",
                    "authorized": False,
                    "message": "未授权"
                }
        
        except Exception as e:
            return {
                "status": "error",
                "authorized": False,
                "message": f"检查授权状态失败: {str(e)}"
            }
    
    def guide_auth(self) -> dict:
        """
        引导用户授权
        """
        step = "user_auth"
        
        # 检查是否已完成
        if self.is_completed(step):
            print("✅ 用户已授权，跳过此步骤\n")
            return {
                "status": "success",
                "message": "用户已授权",
                "skipped": True
            }
        
        # 检查授权状态
        auth_status = self.check_auth_status()
        if auth_status.get("authorized"):
            print("✅ 检测到已授权\n")
            self.mark_completed(step)
            return {
                "status": "success",
                "message": "用户已授权"
            }
        
        print("🔐 [5/5] 用户授权...")
        
        try:
            # 执行授权命令
            print("  启动授权流程...\n")
            
            result = subprocess.run(
                ["lark-cli", "auth", "login"],
                capture_output=True,
                text=True,
                timeout=120  # 2分钟超时
            )
            
            output = result.stdout + result.stderr
            
            # 提取授权链接
            url_match = re.search(r'https://[^\s]+', output)
            
            if url_match:
                auth_url = url_match.group(0)
                
                print("  📝 请打开以下链接完成授权：")
                print(f"  {auth_url}\n")
                print("  ⏳ 等待授权完成...")
                print("  （授权完成后会自动继续）\n")
                
                # 等待用户授权（轮询检查）
                max_wait = 300  # 最多等待5分钟
                start_time = time.time()
                
                while time.time() - start_time < max_wait:
                    time.sleep(5)  # 每5秒检查一次
                    
                    # 检查授权状态
                    auth_status = self.check_auth_status()
                    if auth_status.get("authorized"):
                        print("  ✅ 授权成功\n")
                        self.mark_completed(step)
                        
                        return {
                            "status": "success",
                            "message": "用户授权成功"
                        }
                
                # 超时
                print("  ⚠️ 等待授权超时（超过5分钟）\n")
                print("  你可以稍后手动完成授权:\n")
                print("    lark-cli auth login\n")
                
                return {
                    "status": "warning",
                    "message": "等待授权超时，请手动完成授权",
                    "solution": "运行命令: lark-cli auth login"
                }
            
            else:
                # 没有找到授权链接
                if result.returncode == 0:
                    print("  ✅ 授权流程已启动\n")
                    self.mark_completed(step)
                    
                    return {
                        "status": "success",
                        "message": "授权流程已启动"
                    }
                else:
                    error_msg = output
                    print(f"  ❌ 启动授权失败: {error_msg}\n")
                    self.mark_failed(step, error_msg)
                    
                    return {
                        "status": "error",
                        "message": f"启动授权失败: {error_msg}",
                        "solution": "请手动授权:\n  lark-cli auth login"
                    }
        
        except subprocess.TimeoutExpired:
            error_msg = "授权流程超时"
            print(f"  ⚠️ {error_msg}\n")
            print("  你可以稍后手动完成授权:\n")
            print("    lark-cli auth login\n")
            
            return {
                "status": "warning",
                "message": "授权流程超时，请手动完成授权",
                "solution": "运行命令: lark-cli auth login"
            }
        
        except Exception as e:
            error_msg = str(e)
            print(f"  ❌ 授权失败: {error_msg}\n")
            self.mark_failed(step, error_msg)
            
            return {
                "status": "error",
                "message": f"授权失败: {error_msg}",
                "solution": "请手动授权:\n  lark-cli auth login"
            }


def main():
    """主函数"""
    guide = AuthGuide()
    result = guide.guide_auth()
    
    # 即使授权超时也不算失败，因为可以手动授权
    sys.exit(0)


if __name__ == "__main__":
    main()
