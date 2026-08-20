#!/usr/bin/env python3
"""
飞书CLI一键安装助手 - 配置初始化器
自动创建应用并初始化配置
"""

import subprocess
import sys
import json
import os
import re


class ConfigInitializer:
    """配置初始化器"""
    
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
                "failed": None,
                "app_id": None,
                "app_secret": None
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
    
    def init_config(self) -> dict:
        """
        初始化应用配置
        """
        step = "init_config"
        
        # 检查是否已完成
        if self.is_completed(step):
            print("✅ 应用配置已初始化，跳过此步骤\n")
            return {
                "status": "success",
                "message": "应用配置已初始化",
                "skipped": True,
                "app_id": self.progress.get("app_id"),
                "app_secret": self.progress.get("app_secret")
            }
        
        print("🔧 [4/5] 初始化应用配置...")
        
        try:
            # 执行初始化
            print("  创建新应用...")
            
            result = subprocess.run(
                ["lark-cli", "config", "init", "--new"],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                output = result.stdout + result.stderr
                
                # 提取 App ID 和 App Secret
                app_id_match = re.search(r'App ID[:\s]+([^\n]+)', output, re.IGNORECASE)
                app_secret_match = re.search(r'App Secret[:\s]+([^\n]+)', output, re.IGNORECASE)
                
                app_id = app_id_match.group(1).strip() if app_id_match else None
                app_secret = app_secret_match.group(1).strip() if app_secret_match else None
                
                # 保存到进度
                if app_id:
                    self.progress["app_id"] = app_id
                if app_secret:
                    self.progress["app_secret"] = app_secret
                self.save_progress()
                
                print("  ✅ 应用创建成功")
                if app_id:
                    print(f"  📋 App ID: {app_id}")
                if app_secret:
                    print(f"  🔑 App Secret: {app_secret[:8]}...")
                print()
                
                self.mark_completed(step)
                
                return {
                    "status": "success",
                    "message": "应用配置初始化成功",
                    "app_id": app_id,
                    "app_secret": app_secret
                }
            else:
                error_msg = result.stderr or result.stdout
                print(f"  ❌ 应用创建失败: {error_msg}\n")
                self.mark_failed(step, error_msg)
                
                return {
                    "status": "error",
                    "message": f"应用创建失败: {error_msg}",
                    "solution": "请手动初始化:\n  lark-cli config init --new"
                }
        
        except subprocess.TimeoutExpired:
            error_msg = "应用创建超时（超过1分钟）"
            print(f"  ❌ {error_msg}\n")
            self.mark_failed(step, error_msg)
            
            return {
                "status": "error",
                "message": error_msg,
                "solution": "请手动初始化:\n  lark-cli config init --new"
            }
        
        except Exception as e:
            error_msg = str(e)
            print(f"  ❌ 应用创建失败: {error_msg}\n")
            self.mark_failed(step, error_msg)
            
            return {
                "status": "error",
                "message": f"应用创建失败: {error_msg}",
                "solution": "请手动初始化:\n  lark-cli config init --new"
            }


def main():
    """主函数"""
    initializer = ConfigInitializer()
    result = initializer.init_config()
    
    sys.exit(0 if result["status"] == "success" else 1)


if __name__ == "__main__":
    main()
