#!/usr/bin/env python3
"""
飞书CLI一键安装助手 - CLI安装器
自动安装 lark-cli
"""

import subprocess
import sys
import json
import os


class LarkInstaller:
    """lark-cli 安装器"""
    
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
    
    def install_lark_cli(self) -> dict:
        """
        安装 lark-cli
        """
        step = "install_lark_cli"
        
        # 检查是否已完成
        if self.is_completed(step):
            print("✅ lark-cli 已安装，跳过此步骤\n")
            return {
                "status": "success",
                "message": "lark-cli 已安装",
                "skipped": True
            }
        
        print("📦 [2/5] 安装 lark-cli...")
        
        try:
            # 检测包管理器
            package_manager = "npm"
            try:
                result = subprocess.run(
                    ["yarn", "--version"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    package_manager = "yarn"
            except:
                pass
            
            # 执行安装
            print(f"  使用 {package_manager} 安装...")
            
            if package_manager == "yarn":
                cmd = ["yarn", "global", "add", "@larksuite/cli"]
            else:
                cmd = ["npm", "install", "-g", "@larksuite/cli"]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )
            
            if result.returncode == 0:
                print("  ✅ 安装成功\n")
                self.mark_completed(step)
                
                return {
                    "status": "success",
                    "message": "lark-cli 安装成功"
                }
            else:
                error_msg = result.stderr or result.stdout
                print(f"  ❌ 安装失败: {error_msg}\n")
                self.mark_failed(step, error_msg)
                
                # 提供解决方案
                if "EACCES" in error_msg or "permission denied" in error_msg.lower():
                    solution = "权限不足，使用以下方案之一:\n  1. 使用 sudo: sudo npm install -g @larksuite/cli\n  2. 修改 npm 全局目录（推荐）"
                elif "network" in error_msg.lower() or "ETIMEDOUT" in error_msg:
                    solution = "网络问题，使用镜像源:\n  npm config set registry https://registry.npmmirror.com\n  npm install -g @larksuite/cli"
                else:
                    solution = f"请手动安装:\n  npm install -g @larksuite/cli"
                
                return {
                    "status": "error",
                    "message": f"安装失败: {error_msg}",
                    "solution": solution
                }
        
        except subprocess.TimeoutExpired:
            error_msg = "安装超时（超过5分钟）"
            print(f"  ❌ {error_msg}\n")
            self.mark_failed(step, error_msg)
            
            return {
                "status": "error",
                "message": error_msg,
                "solution": "网络较慢，请使用镜像源:\n  npm config set registry https://registry.npmmirror.com\n  npm install -g @larksuite/cli"
            }
        
        except Exception as e:
            error_msg = str(e)
            print(f"  ❌ 安装失败: {error_msg}\n")
            self.mark_failed(step, error_msg)
            
            return {
                "status": "error",
                "message": f"安装失败: {error_msg}",
                "solution": f"请手动安装:\n  npm install -g @larksuite/cli"
            }
    
    def verify_installation(self) -> bool:
        """验证安装"""
        try:
            result = subprocess.run(
                ["lark-cli", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except:
            return False


def main():
    """主函数"""
    installer = LarkInstaller()
    result = installer.install_lark_cli()
    
    # 验证安装
    if result["status"] == "success" and not result.get("skipped"):
        if installer.verify_installation():
            print("  ✅ 安装验证成功\n")
        else:
            print("  ⚠️ 安装验证失败，但安装命令已执行成功\n")
    
    sys.exit(0 if result["status"] == "success" else 1)


if __name__ == "__main__":
    main()
