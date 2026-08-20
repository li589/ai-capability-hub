#!/usr/bin/env python3
"""
飞书CLI一键安装助手 - Skills安装器
自动安装飞书CLI相关Skills
"""

import subprocess
import sys
import json
import os


class SkillsInstaller:
    """Skills 安装器"""
    
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
    
    def install_skills(self) -> dict:
        """
        安装飞书CLI相关Skills
        """
        step = "install_skills"
        
        # 检查是否已完成
        if self.is_completed(step):
            print("✅ Skills 已安装，跳过此步骤\n")
            return {
                "status": "success",
                "message": "Skills 已安装",
                "skipped": True
            }
        
        print("📦 [3/5] 安装 Skills...")
        
        try:
            # 执行安装
            print("  从 GitHub 安装 Skills...")
            
            result = subprocess.run(
                ["npx", "skills", "add", "https://github.com/larksuite/cli", "-y", "-g"],
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )
            
            if result.returncode == 0:
                print("  ✅ Skills 安装成功\n")
                self.mark_completed(step)
                
                return {
                    "status": "success",
                    "message": "Skills 安装成功"
                }
            else:
                error_msg = result.stderr or result.stdout
                print(f"  ❌ Skills 安装失败: {error_msg}\n")
                self.mark_failed(step, error_msg)
                
                return {
                    "status": "error",
                    "message": f"Skills 安装失败: {error_msg}",
                    "solution": "请手动安装:\n  npx skills add https://github.com/larksuite/cli -y -g"
                }
        
        except subprocess.TimeoutExpired:
            error_msg = "Skills 安装超时（超过5分钟）"
            print(f"  ❌ {error_msg}\n")
            self.mark_failed(step, error_msg)
            
            return {
                "status": "error",
                "message": error_msg,
                "solution": "网络较慢，请重试或手动安装:\n  npx skills add https://github.com/larksuite/cli -y -g"
            }
        
        except Exception as e:
            error_msg = str(e)
            print(f"  ❌ Skills 安装失败: {error_msg}\n")
            self.mark_failed(step, error_msg)
            
            return {
                "status": "error",
                "message": f"Skills 安装失败: {error_msg}",
                "solution": "请手动安装:\n  npx skills add https://github.com/larksuite/cli -y -g"
            }


def main():
    """主函数"""
    installer = SkillsInstaller()
    result = installer.install_skills()
    
    sys.exit(0 if result["status"] == "success" else 1)


if __name__ == "__main__":
    main()
