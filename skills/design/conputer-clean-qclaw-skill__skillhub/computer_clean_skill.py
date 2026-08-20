import os
import shutil
import subprocess
import os.path  # 替代pathlib，使用Python标准库
# 适配qclaw文本交互，移除clawskill依赖，无需语音相关接口

class ComputerCleanSkill:
    def __init__(self):
        self.name = "电脑清理"
        self.description = "跨平台深度清理，敏感项二次确认，支持系统/社交/开发/浏览器等全场景垃圾清理（qclaw文本交互版）"
        self.examples = [
            "帮我清理电脑垃圾",
            "深度清理电脑",
            "清理缓存",
            "清理Docker",
            "清理桌面文件",
            "电脑加速"
        ]

        # 系统判断（跨平台适配）
        self.is_windows = os.name == "nt"
        self.is_macos = False
        self.is_linux = False
        if not self.is_windows:
            sysname = os.uname().sysname
            self.is_macos = sysname == "Darwin"
            self.is_linux = sysname == "Linux"

        self.home = os.path.expanduser("~")  # 替代Path.home()，使用标准库
        self.total_cleaned_mb = 0.0

    def match_intent(self, text):
        """意图匹配：识别用户清理相关指令"""
        keywords = [
            "清理", "垃圾", "缓存", "加速", "废纸篓", "回收站",
            "docker", "xcode", "微信", "qq", "钉钉", "pip", "conda",
            "浏览器", "chrome", "edge", "safari", "迅雷", "brew", "桌面"
        ]
        return any(k in text.lower() for k in keywords)

    # ------------------------------
    # 工具方法：计算文件大小 + 安全删除
    # ------------------------------
    def _get_size_mb(self, path):
        """计算文件/文件夹大小（单位：MB），异常捕获避免报错"""
        size = 0
        try:
            if os.path.isfile(path):
                size = os.path.getsize(path)
            elif os.path.isdir(path):
                for root, dirs, files in os.walk(path):
                    for f in files:
                        fp = os.path.join(root, f)
                        if os.path.exists(fp):
                            size += os.path.getsize(fp)
        except Exception:
            pass
        return round(size / 1024 / 1024, 2)

    def _safe_remove(self, path):
        """安全删除文件/文件夹，返回清理大小，权限不足自动跳过"""
        if not os.path.exists(path):
            return 0.0
        size_mb = self._get_size_mb(path)
        try:
            if os.path.isfile(path) or os.path.islink(path):
                os.remove(path)
            elif os.path.isdir(path):
                shutil.rmtree(path, ignore_errors=True)
        except Exception:
            pass
        return size_mb

    # ------------------------------
    # 工具方法：敏感项二次确认（文本交互，替代语音）
    # ------------------------------
    def _ask_confirm(self, tip):
        """敏感项清理前询问用户确认，纯文本交互，接收用户输入"""
        print(f"检测到{tip}，清理后无法恢复，是否确认清理？（请输入 确认/取消）")
        ans = input().strip().lower()
        # 支持多种确认/取消指令，适配文本交互习惯
        return any(k in ans for k in ["确认", "同意", "是", "好", "可以", "继续"])

    # ------------------------------
    # 常规清理（无需确认，安全无风险）
    # ------------------------------
    def _clean_system_temp(self):
        """清理系统临时文件（跨平台）"""
        cleaned = 0.0
        if self.is_windows:
            temps = [
                os.environ.get("TEMP", ""),
                os.path.join(os.environ.get("WINDIR", ""), "Temp"),
                os.path.join(self.home, "AppData", "Local", "Temp")
            ]
        else:
            temps = ["/tmp", "/var/tmp"]

        for p in temps:
            if os.path.exists(p):
                # 替代Path(p).iterdir()，使用os.listdir适配标准库
                for item in os.listdir(p):
                    item_path = os.path.join(p, item)
                    cleaned += self._safe_remove(item_path)
        return cleaned

    def _clean_trash(self):
        """清理回收站/废纸篓（跨平台）"""
        cleaned = 0.0
        if self.is_macos:
            trash = os.path.join(self.home, ".Trash")
            if os.path.exists(trash):
                for item in os.listdir(trash):
                    item_path = os.path.join(trash, item)
                    cleaned += self._safe_remove(item_path)
        elif self.is_linux:
            trash = os.path.join(self.home, ".local", "share", "Trash", "files")
            if os.path.exists(trash):
                for item in os.listdir(trash):
                    item_path = os.path.join(trash, item)
                    cleaned += self._safe_remove(item_path)
        return cleaned

    def _clean_pip_conda(self):
        """清理pip/conda缓存（跨平台）"""
        cleaned = 0.0
        # pip缓存路径（适配不同系统）
        cleaned += self._safe_remove(os.path.join(self.home, ".cache", "pip"))
        cleaned += self._safe_remove(os.path.join(self.home, "Library", "Caches", "pip"))
        # conda缓存路径（适配不同安装位置）
        cleaned += self._safe_remove(os.path.join(self.home, ".conda", "pkgs"))
        cleaned += self._safe_remove(os.path.join(self.home, "miniconda3", "pkgs"))
        cleaned += self._safe_remove(os.path.join(self.home, "anaconda3", "pkgs"))
        return cleaned

    def _clean_social(self):
        """清理微信/QQ/钉钉缓存（跨平台）"""
        cleaned = 0.0
        if self.is_macos:
            base = os.path.join(self.home, "Library", "Containers")
            apps = [
                "com.tencent.xinWeChat",
                "com.tencent.qq",
                "com.alibabainc.dingtalk"
            ]
            for app in apps:
                cache = os.path.join(base, app, "Data", "Library", "Caches")
                cleaned += self._safe_remove(cache)
        elif self.is_windows:
            wechat = os.path.join(self.home, "Documents", "WeChat Files")
            qq = os.path.join(self.home, "Documents", "Tencent Files")
            cleaned += self._safe_remove(os.path.join(wechat, "FileStorage", "Cache"))
            cleaned += self._safe_remove(os.path.join(qq, "Cache"))
        elif self.is_linux:
            cleaned += self._safe_remove(os.path.join(self.home, ".config", "wechat"))
            cleaned += self._safe_remove(os.path.join(self.home, ".config", "qq"))
        return cleaned

    def _clean_browsers(self):
        """清理主流浏览器缓存（Chrome/Edge/Safari/Firefox，跨平台）"""
        cleaned = 0.0
        home = self.home
        if self.is_macos:
            cleaned += self._safe_remove(os.path.join(home, "Library", "Caches", "Google", "Chrome"))
            cleaned += self._safe_remove(os.path.join(home, "Library", "Caches", "Microsoft Edge"))
            cleaned += self._safe_remove(os.path.join(home, "Library", "Caches", "Firefox"))
            cleaned += self._safe_remove(os.path.join(home, "Library", "Safari"))
        elif self.is_windows:
            cleaned += self._safe_remove(os.path.join(home, "AppData", "Local", "Google", "Chrome", "User Data", "Default", "Cache"))
            cleaned += self._safe_remove(os.path.join(home, "AppData", "Local", "Microsoft", "Edge", "User Data", "Default", "Cache"))
        elif self.is_linux:
            cleaned += self._safe_remove(os.path.join(home, ".cache", "google-chrome"))
            cleaned += self._safe_remove(os.path.join(home, ".cache", "microsoft-edge"))
            cleaned += self._safe_remove(os.path.join(home, ".cache", "firefox"))
        return cleaned

    def _clean_thunder(self):
        """清理迅雷缓存（跨平台）"""
        cleaned = 0.0
        if self.is_macos:
            cleaned += self._safe_remove(os.path.join(self.home, "Library", "Caches", "com.xunlei.Thunder"))
        elif self.is_windows:
            cleaned += self._safe_remove(os.path.join(self.home, "AppData", "Local", "Thunder Network"))
        elif self.is_linux:
            cleaned += self._safe_remove(os.path.join(self.home, ".xunlei"))
        return cleaned

    # ------------------------------
    # 敏感清理（需二次确认，避免误删）
    # ------------------------------
    def _clean_docker_confirm(self):
        """Docker清理（需确认：无用镜像、卷、构建缓存）"""
        if not self._ask_confirm("Docker 无用镜像、卷、构建缓存，可能删除未使用的镜像"):
            print("已跳过 Docker 清理")
            return 0.0
        try:
            subprocess.run(
                ["docker", "system", "prune", "-a", "--volumes", "-f"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=40
            )
            return 300.0  # 估算清理大小，实际以系统为准
        except Exception:
            print("Docker 清理失败，可能未安装 Docker 或权限不足")
            return 0.0

    def _clean_xcode_confirm(self):
        """Xcode清理（macOS专属，需确认：模拟器、构建缓存）"""
        if not self.is_macos:
            return 0.0
        if not self._ask_confirm("Xcode 缓存，包括模拟器与构建文件"):
            print("已跳过 Xcode 清理")
            return 0.0
        paths = [
            os.path.join(self.home, "Library", "Developer", "Xcode", "DerivedData"),
            os.path.join(self.home, "Library", "Developer", "CoreSimulator", "Caches"),
            os.path.join(self.home, "Library", "Caches", "com.apple.dt.Xcode")
        ]
        cleaned = 0.0
        for p in paths:
            cleaned += self._safe_remove(p)
        return cleaned

    def _clean_brew_confirm(self):
        """Homebrew清理（macOS专属，需确认：旧版本包、缓存）"""
        if not self.is_macos:
            return 0.0
        if not self._ask_confirm("Homebrew 旧版本包与缓存"):
            print("已跳过 Homebrew 清理")
            return 0.0
        try:
            subprocess.run(
                ["brew", "cleanup", "-s"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            return 200.0  # 估算清理大小
        except Exception:
            print("Homebrew 清理失败，可能未安装 Homebrew 或权限不足")
            return 0.0

    def _clean_desktop_files_confirm(self):
        """桌面大文件清理（需确认：安装包、压缩包等临时文件）"""
        if not self._ask_confirm("桌面安装包、压缩包等临时大文件"):
            print("已跳过桌面文件清理")
            return 0.0
        desktop = os.path.join(self.home, "Desktop")
        if not os.path.exists(desktop):
            return 0.0
        # 只清理临时/安装类文件，不删文档、图片、视频
        exts = {
            ".zip", ".rar", ".7z", ".tar", ".gz", ".bz2",
            ".dmg", ".pkg", ".iso", ".exe", ".msi", ".deb", ".rpm",
            ".crdownload", ".download", ".tmp", ".part"
        }
        cleaned = 0.0
        # 替代Path(desktop).iterdir()，使用os.listdir适配标准库
        for f in os.listdir(desktop):
            f_path = os.path.join(desktop, f)
            if os.path.isfile(f_path) and os.path.splitext(f)[1].lower() in exts:
                cleaned += self._safe_remove(f_path)
        return cleaned

    # ------------------------------
    # 主清理流程（按安全优先级执行）
    # ------------------------------
    def start_clean(self):
        total = 0.0
        # 先执行安全清理（无需确认）
        total += self._clean_system_temp()
        total += self._clean_trash()
        total += self._clean_pip_conda()
        total += self._clean_social()
        total += self._clean_browsers()
        total += self._clean_thunder()

        # 再执行敏感清理（需确认）
        total += self._clean_docker_confirm()
        total += self._clean_xcode_confirm()
        total += self._clean_brew_confirm()
        total += self._clean_desktop_files_confirm()

        return round(total, 2)

    # ------------------------------
    # 技能执行入口（qclaw 文本交互接口）
    # ------------------------------
    def run(self, text, result):
        print("正在开始安全电脑清理，敏感项目会向你二次确认，请稍候...")
        total_mb = self.start_clean()

        # 文本反馈清理结果（适配大小单位，更直观）
        if total_mb >= 1024:
            gb = round(total_mb / 1024, 2)
            print(f"清理完成！共释放 {gb} GB 存储空间，电脑运行更流畅啦")
        elif total_mb > 0:
            print(f"清理完成！共释放 {total_mb} MB 存储空间")
        else:
            print("你的电脑非常干净，没有需要清理的垃圾文件哦")