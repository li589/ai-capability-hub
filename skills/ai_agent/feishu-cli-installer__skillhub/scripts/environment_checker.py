#!/usr/bin/env python3
"""
飞书CLI一键安装助手 - 环境检测器
自动检测安装环境是否满足要求
"""

import subprocess
import sys
import json
from typing import Dict, Any


class EnvironmentChecker:
    """环境检测器"""
    
    def __init__(self):
        self.results = {}
    
    def check_node_version(self) -> Dict[str, Any]:
        """
        检测 Node.js 版本
        需要 Node.js >= 16.0
        """
        try:
            result = subprocess.run(
                ["node", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                version_str = result.stdout.strip().lstrip('v')
                major_version = int(version_str.split('.')[0])
                
                if major_version >= 16:
                    return {
                        "status": "success",
                        "message": f"Node.js v{version_str} (满足要求)",
                        "version": version_str,
                        "satisfied": True
                    }
                else:
                    return {
                        "status": "error",
                        "message": f"Node.js v{version_str} (版本过低，需要 >= 16.0)",
                        "version": version_str,
                        "satisfied": False,
                        "solution": "升级到 Node.js 16.0 或更高版本:\n  - macOS: brew install node@18\n  - Ubuntu: curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash - && sudo apt-get install -y nodejs\n  - 或使用 nvm: nvm install 18 && nvm use 18"
                    }
            else:
                return {
                    "status": "error",
                    "message": "Node.js 未安装",
                    "satisfied": False,
                    "solution": "安装 Node.js:\n  - macOS: brew install node\n  - Ubuntu: sudo apt-get install nodejs\n  - 或访问 https://nodejs.org/ 下载安装包"
                }
        except FileNotFoundError:
            return {
                "status": "error",
                "message": "Node.js 未安装",
                "satisfied": False,
                "solution": "安装 Node.js:\n  - macOS: brew install node\n  - Ubuntu: sudo apt-get install nodejs\n  - 或访问 https://nodejs.org/ 下载安装包"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"检测 Node.js 失败: {str(e)}",
                "satisfied": False
            }
    
    def check_npm(self) -> Dict[str, Any]:
        """
        检测 npm 是否可用
        """
        try:
            result = subprocess.run(
                ["npm", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                version = result.stdout.strip()
                return {
                    "status": "success",
                    "message": f"npm v{version} (可用)",
                    "version": version,
                    "satisfied": True
                }
            else:
                # 尝试检测 yarn
                yarn_result = subprocess.run(
                    ["yarn", "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if yarn_result.returncode == 0:
                    version = yarn_result.stdout.strip()
                    return {
                        "status": "success",
                        "message": f"yarn v{version} (可用)",
                        "version": version,
                        "package_manager": "yarn",
                        "satisfied": True
                    }
                else:
                    return {
                        "status": "error",
                        "message": "npm/yarn 未安装",
                        "satisfied": False,
                        "solution": "npm 通常随 Node.js 一起安装，请先安装 Node.js"
                    }
        except FileNotFoundError:
            # 尝试检测 yarn
            try:
                result = subprocess.run(
                    ["yarn", "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    version = result.stdout.strip()
                    return {
                        "status": "success",
                        "message": f"yarn v{version} (可用)",
                        "version": version,
                        "package_manager": "yarn",
                        "satisfied": True
                    }
            except:
                pass
            
            return {
                "status": "error",
                "message": "npm/yarn 未安装",
                "satisfied": False,
                "solution": "npm 通常随 Node.js 一起安装，请先安装 Node.js"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"检测 npm 失败: {str(e)}",
                "satisfied": False
            }
    
    def check_network(self) -> Dict[str, Any]:
        """
        检测网络连接
        """
        import socket
        
        try:
            # 尝试连接到 npm registry
            socket.create_connection(("registry.npmjs.org", 443), timeout=5)
            return {
                "status": "success",
                "message": "网络连接正常",
                "satisfied": True
            }
        except socket.timeout:
            return {
                "status": "error",
                "message": "网络连接超时",
                "satisfied": False,
                "solution": "检查网络连接，或使用镜像源:\n  npm config set registry https://registry.npmmirror.com"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"网络连接失败: {str(e)}",
                "satisfied": False,
                "solution": "检查网络连接，或使用镜像源:\n  npm config set registry https://registry.npmmirror.com"
            }
    
    def check_permissions(self) -> Dict[str, Any]:
        """
        检测系统权限
        """
        import os
        
        # 检查 npm 全局目录写入权限
        try:
            result = subprocess.run(
                ["npm", "config", "get", "prefix"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                npm_prefix = result.stdout.strip()
                
                # 检查是否可以写入
                test_file = os.path.join(npm_prefix, ".write_test")
                try:
                    with open(test_file, 'w') as f:
                        f.write("test")
                    os.remove(test_file)
                    
                    return {
                        "status": "success",
                        "message": "系统权限正常",
                        "npm_prefix": npm_prefix,
                        "satisfied": True
                    }
                except PermissionError:
                    return {
                        "status": "warning",
                        "message": f"npm 全局目录 {npm_prefix} 无写入权限",
                        "npm_prefix": npm_prefix,
                        "satisfied": False,
                        "solution": "使用以下方案之一:\n  1. 使用 sudo: sudo npm install -g @larksuite/cli\n  2. 修改 npm 全局目录:\n     mkdir ~/.npm-global\n     npm config set prefix '~/.npm-global'\n     echo 'export PATH=~/.npm-global/bin:$PATH' >> ~/.bashrc\n     source ~/.bashrc"
                    }
        except Exception as e:
            return {
                "status": "error",
                "message": f"检测权限失败: {str(e)}",
                "satisfied": False
            }
    
    def run_all_checks(self) -> Dict[str, Any]:
        """
        运行所有检测
        """
        print("🔍 检测环境...\n")
        
        self.results = {
            "node_version": self.check_node_version(),
            "npm_available": self.check_npm(),
            "network_connection": self.check_network(),
            "system_permissions": self.check_permissions()
        }
        
        # 打印结果
        all_satisfied = True
        
        for check_name, result in self.results.items():
            status_icon = "✅" if result["status"] == "success" else ("⚠️" if result["status"] == "warning" else "❌")
            print(f"  {status_icon} {result['message']}")
            
            if not result.get("satisfied", True):
                all_satisfied = False
                if "solution" in result:
                    print(f"\n💡 解决方案:\n{result['solution']}\n")
        
        print()
        
        if all_satisfied:
            print("✅ 环境检测通过！可以开始安装。\n")
            return {
                "status": "success",
                "all_satisfied": True,
                "results": self.results
            }
        else:
            print("❌ 环境检测未通过，请先解决上述问题。\n")
            return {
                "status": "error",
                "all_satisfied": False,
                "results": self.results
            }


def main():
    """主函数"""
    checker = EnvironmentChecker()
    result = checker.run_all_checks()
    
    # 保存检测结果
    with open(".environment_check_result.json", "w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    sys.exit(0 if result["all_satisfied"] else 1)


if __name__ == "__main__":
    main()
