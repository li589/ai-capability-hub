#!/usr/bin/env python3
"""
飞书CLI一键安装助手 - 一键安装主程序
自动完成飞书CLI的完整安装流程
"""

import sys
import os
import json
import time
from datetime import datetime

# 导入各个安装模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from environment_checker import EnvironmentChecker
from lark_installer import LarkInstaller
from skills_installer import SkillsInstaller
from config_initializer import ConfigInitializer
from auth_guide import AuthGuide
from installation_validator import InstallationValidator


class OneClickInstaller:
    """一键安装主程序"""
    
    def __init__(self):
        self.progress_file = ".lark_cli_install_progress.json"
        self.start_time = time.time()
        self.steps = [
            ("环境检测", "environment_check"),
            ("安装 lark-cli", "install_lark_cli"),
            ("安装 Skills", "install_skills"),
            ("初始化配置", "init_config"),
            ("用户授权", "user_auth")
        ]
    
    def print_banner(self):
        """打印欢迎信息"""
        print("=" * 60)
        print("     飞书CLI一键安装助手")
        print("=" * 60)
        print()
        print("本工具将自动完成以下操作：")
        for i, (step_name, _) in enumerate(self.steps, 1):
            print(f"  [{i}] {step_name}")
        print()
        print("-" * 60)
        print()
    
    def print_summary(self, success: bool):
        """打印安装摘要"""
        elapsed_time = time.time() - self.start_time
        
        print()
        print("=" * 60)
        
        if success:
            print("✅ 安装完成！")
        else:
            print("⚠️ 安装过程中遇到问题")
        
        print()
        print(f"⏱️  总耗时: {elapsed_time:.1f} 秒")
        print()
        print("=" * 60)
        print()
    
    def run(self):
        """运行一键安装"""
        self.print_banner()
        
        # 步骤1: 环境检测
        print("[1/5] 环境检测")
        print("-" * 60)
        
        checker = EnvironmentChecker()
        env_result = checker.run_all_checks()
        
        if not env_result["all_satisfied"]:
            print("❌ 环境检测未通过，请先解决上述问题后重试。\n")
            self.print_summary(False)
            return False
        
        # 步骤2: 安装 lark-cli
        print("[2/5] 安装 lark-cli")
        print("-" * 60)
        
        lark_installer = LarkInstaller()
        lark_result = lark_installer.install_lark_cli()
        
        if lark_result["status"] == "error":
            print(f"❌ 安装 lark-cli 失败\n")
            self.print_summary(False)
            return False
        
        # 步骤3: 安装 Skills
        print("[3/5] 安装 Skills")
        print("-" * 60)
        
        skills_installer = SkillsInstaller()
        skills_result = skills_installer.install_skills()
        
        if skills_result["status"] == "error":
            print(f"❌ 安装 Skills 失败\n")
            self.print_summary(False)
            return False
        
        # 步骤4: 初始化配置
        print("[4/5] 初始化配置")
        print("-" * 60)
        
        config_initializer = ConfigInitializer()
        config_result = config_initializer.init_config()
        
        if config_result["status"] == "error":
            print(f"❌ 初始化配置失败\n")
            self.print_summary(False)
            return False
        
        # 步骤5: 用户授权
        print("[5/5] 用户授权")
        print("-" * 60)
        
        auth_guide = AuthGuide()
        auth_result = auth_guide.guide_auth()
        
        # 授权超时不算失败，可以手动完成
        if auth_result["status"] == "error":
            print(f"❌ 用户授权失败\n")
            self.print_summary(False)
            return False
        
        # 步骤6: 验证安装
        print()
        print("[验证] 验证安装")
        print("-" * 60)
        
        validator = InstallationValidator()
        validation_result = validator.run_all_validations()
        
        # 打印摘要
        self.print_summary(validation_result["all_success"])
        
        return validation_result["all_success"]


def main():
    """主函数"""
    installer = OneClickInstaller()
    success = installer.run()
    
    # 清理进度文件（安装成功后）
    if success:
        progress_file = ".lark_cli_install_progress.json"
        if os.path.exists(progress_file):
            os.remove(progress_file)
        
        env_file = ".environment_check_result.json"
        if os.path.exists(env_file):
            os.remove(env_file)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
