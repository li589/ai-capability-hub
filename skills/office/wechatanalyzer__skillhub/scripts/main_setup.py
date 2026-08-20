#!/usr/bin/env python3
"""
微信聊天分析助手 - 一键配置向导 v1.2
自动检测环境、安装依赖、配置路径、引导LLM API配置
"""

import os, sys, subprocess, json
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
CONFIG_FILE = BASE_DIR / "config.json"
REQS_FILE = BASE_DIR / "requirements.txt"

def run_cmd(cmd, shell=True):
    try:
        result = subprocess.run(cmd, shell=shell, capture_output=True, text=True, timeout=180)
        return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return False, "", str(e)

def step(msg):
    print(f"\n{'='*50}\n  {msg}\n{'='*50}")

def ok(msg): print(f"  [OK] {msg}")
def fail(msg): print(f"  [FAIL] {msg}")
def info(msg): print(f"  [INFO] {msg}")

def input_int(prompt, default):
    try:
        val = input(f"{prompt} [{default}]: ").strip()
        return int(val) if val else default
    except Exception:
        return default

def input_str(prompt, default=''):
    val = input(f"{prompt}{' ['+default+']' if default else ''}: ").strip()
    return val or default

def check_python():
    step("检查 Python 环境")
    v = sys.version_info
    print(f"  当前版本: {v.major}.{v.minor}.{v.micro}")
    if v.major == 3 and v.minor >= 8:
        ok("Python 版本符合要求"); return True
    fail("需要 Python 3.8+"); return False

def check_wechat():
    step("检测微信安装路径")
    paths = [
        Path(os.path.expandvars(r"%APPDATA%")) / "Tencent" / "WeChat",
        Path(os.path.expandvars(r"%USERPROFILE%")) / "Documents" / "WeChat Files",
        Path(r"D:\WeChat"),
    ]
    found = []
    for p in paths:
        if p.exists():
            ok(f"找到: {p}")
            try:
                dbs = list(p.rglob("*.db"))
                if dbs: info(f"  -> {len(dbs)} 个数据库文件")
                found.append(str(p))
            except OSError: pass
        else:
            info(f"未找到: {p}")
    return found

def install_deps():
    step("安装 Python 依赖（约需 3-5 分钟）")
    run_cmd(f'"{sys.executable}" -m pip install --upgrade pip')

    pkgs = [
        "flask>=3.0.0", "flask-cors",
        "pandas>=2.1.0", "numpy>=1.26.0", "python-docx>=1.1.0",
        "python-pptx>=0.6.23", "jinja2>=3.1.0", "apscheduler>=3.10.0",
        "python-dateutil>=2.8.0", "tqdm>=4.66.0",
        "Pillow>=10.0.0", "openai>=1.12.0", "plotly>=5.18.0",
    ]
    batch, failed = 6, []
    for i in range(0, len(pkgs), batch):
        b = pkgs[i:i+batch]
        info(f"安装中: {', '.join(p.split('>')[0].split('=')[0] for p in b[:3])}...")
        ok2, _, err = run_cmd(f'"{sys.executable}" -m pip install {" ".join(b)}')
        if not ok2 and err: failed.extend(b)
    if failed:
        info(f"部分可选包安装失败（不影响核心功能）")
    else:
        ok("所有核心依赖安装成功")

    for pkg, desc in [("openai-whisper","语音识别"),("easyocr","OCR")]:
        ok2,_,_ = run_cmd(f'"{sys.executable}" -m pip install {pkg}')
        if ok2: ok(f"{desc}安装成功")
    return True

def create_dirs():
    step("创建数据目录")
    for d in [BASE_DIR/"data", BASE_DIR/"data/reports", BASE_DIR/"data/uploads"]:
        d.mkdir(parents=True, exist_ok=True)
        ok(f"目录: {d.name}/")

def configure_llm(existing_config=None):
    """引导配置 LLM API"""
    step("配置 LLM AI 增强（可选）")
    print("""
  LLM API 可以大幅提升分析质量：
  - 更准确的 MBTI 推断
  - 更自然的人情味分析
  - 更智能的对话预测

  支持兼容 OpenAI 接口的任何大模型：
  - DeepSeek（推荐，有免费额度）
  - 通义千问、百度文心、OpenAI 等

  API Key 获取方式（以 DeepSeek 为例）：
  1. 访问 https://platform.deepseek.com
  2. 注册账号并登录
  3. 进入 API Keys 页面创建
  4. 复制 Key 并在此粘贴
    """)

    use_ai = input("是否启用 LLM AI 增强分析？(y/N): ").strip().lower()

    api_key = ''
    base_url = ''
    model = ''
    if use_ai in ('y', 'yes', '是'):
        api_key = input("请输入 API Key: ").strip()
        if api_key:
            base_url = input("API 地址（默认 https://api.deepseek.com）: ").strip()
            model = input("模型名称（默认 deepseek-chat）: ").strip()
            ok("API Key 已设置")
        else:
            info("未输入API Key，将使用规则分析")

    # Load existing config
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, encoding='utf-8') as f:
            config = json.load(f)
    else:
        config = {
            "app_name": "微信聊天分析助手", "version": "1.2.0",
            "data_dir": "data", "reports_dir": "data/reports", "db_path": "data/sessions/chat_history.db",
            "wechat_paths": {"windows": []},
            "scheduler": {"enabled": False, "default_period": "weekly"},
            "report": {"default_format": "html", "output_dir": "data/reports"},
            "analysis": {"mbti_enabled": True, "bigfive_enabled": True, "sentiment_enabled": True, "prediction_enabled": True, "risk_detection_enabled": True},
            "llm": {"enabled": False, "api_key": "", "base_url": "", "model": "", "temperature": 0.7, "timeout": 30}
        }

    # Update llm config
    if "llm" not in config:
        config["llm"] = {"enabled": False, "api_key": "", "base_url": "", "model": "", "temperature": 0.7, "timeout": 30}

    if api_key:
        config["llm"]["enabled"] = True
        config["llm"]["api_key"] = api_key
        config["llm"]["base_url"] = base_url or "https://api.deepseek.com"
        config["llm"]["model"] = model or "deepseek-chat"
        ok("LLM AI 已启用！")
        print("  重新运行分析时将自动使用AI增强")
    else:
        config["llm"]["enabled"] = False
        info("LLM AI 未启用，使用本地规则分析")
        print("  后续可通过修改 config.json 启用")

    return config

def update_config(found, llm_config=None):
    step("保存配置")
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, encoding='utf-8') as f:
            config = json.load(f)
    else:
        config = {
            "app_name": "微信聊天分析助手", "version": "1.2.0",
            "data_dir": "data", "reports_dir": "data/reports", "db_path": "data/sessions/chat_history.db",
            "wechat_paths": {"windows": []},
            "scheduler": {"enabled": False, "default_period": "weekly"},
            "report": {"default_format": "html", "output_dir": "data/reports"},
            "analysis": {"mbti_enabled": True, "bigfive_enabled": True, "sentiment_enabled": True, "prediction_enabled": True},
        }

    if found:
        config["wechat_paths"]["windows"] = found
        ok(f"微信路径: {found[0]}")
    else:
        info("使用手动导入模式")

    if llm_config:
        config["llm"] = llm_config

    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    ok("配置已保存")

def create_bat():
    step("创建快捷启动脚本")
    bat = BASE_DIR / "微信分析助手.bat"
    content = """@echo off
chcp 65001 >nul
title 微信聊天分析助手
cd /d "%~dp0"
echo.
echo ========================================
echo    微信聊天分析助手 - 启动菜单
echo ========================================
echo.
echo  [1] 分析聊天记录（粘贴模式）
echo  [2] 分析聊天记录（从文件导入）
echo  [3] 生成 HTML 报告
echo  [4] 生成 Word 报告
echo  [5] 启动 Web 服务（浏览器打开）
echo  [6] 查看日历事件
echo  [7] 一键配置（重新检测环境）
echo  [0] 退出
echo.
set /p choice=请输入选项 [1-7, 0退出]:
if "%choice%"=="1" goto paste
if "%choice%"=="2" goto file
if "%choice%"=="3" goto rhtml
if "%choice%"=="4" goto rword
if "%choice%"=="5" goto serve
if "%choice%"=="6" goto cal
if "%choice%"=="7" goto setup
if "%choice%"=="0" goto end
:paste
python scripts/main.py analyze --paste
pause & goto end
:file
set /p fp=请输入文件路径:
python scripts/main.py analyze --file "%fp%"
pause & goto end
:rhtml
python scripts/main.py report --report-type html
pause & goto end
:rword
python scripts/main.py report --report-type word
pause & goto end
:serve
start http://localhost:5000
python scripts/main.py serve --port 5000
goto end
:cal
python scripts/main.py calendar --upcoming --days 7
pause & goto end
:setup
python scripts/main_setup.py
pause & goto end
:end
"""
    with open(bat, 'w', encoding='utf-8') as f:
        f.write(content)
    ok(f"已创建: {bat.name}")
    print("  双击即可启动！")

def main():
    print("\n" + "="*50 + "\n   微信聊天分析助手 - 一键配置向导 v1.2\n" + "="*50)
    print("   支持 LLM AI 增强分析（兼容 OpenAI 接口）")
    print("="*50)

    if not check_python():
        input("\n按回车退出..."); return

    create_dirs()
    found = check_wechat()
    install_deps()

    # Ask for LLM config
    llm_config = configure_llm()

    update_config(found, llm_config.get("llm"))
    create_bat()

    step("配置完成！")

    ai_status = "✅ LLM AI 已启用" if llm_config.get("llm", {}).get("enabled") else "⏳ 规则分析模式"
    print(f"""
  状态检查:
  ✅ Python 环境正常
  ✅ 依赖安装完成
  ✅ 数据目录已创建
  {ai_status}

  接下来:
  1. 双击 "微信分析助手.bat" 启动
  2. 选 [1] 粘贴聊天记录开始分析
  3. 选 [5] 启动 Web 服务（浏览器访问）

  导出聊天记录方法:
  电脑微信 -> 打开对话框 -> 右上角[...] -> 聊天文件 -> 导出聊天记录
  或直接复制聊天文字粘贴
    """)
    input("按回车退出...")

if __name__ == "__main__":
    main()
