# 依赖与安装说明（体验版）

本体验版不调用任何远端 API、不需要任何 Key，所有处理在本地完成。依赖如下外部二进制。

## 必需依赖

### ffmpeg + ffprobe

用于元数据探测、抽帧、音频提取。缺失则脚本退出码 8 并打印本说明。

安装：

- macOS：`brew install ffmpeg`
- Ubuntu/Debian：`sudo apt install ffmpeg`
- Windows：从 https://ffmpeg.org/download.html 下载并加入 PATH

校验：`ffmpeg -version` 与 `ffprobe -version` 均有输出即可。

### 一键自动安装（`--install-ffmpeg`）

若脚本探测不到 ffmpeg/ffprobe，可在命令行加 `--install-ffmpeg`，脚本按平台用包管理器自动安装后重新探测（Win/Mac 均支持）：

- **macOS（有 brew）** → `brew install ffmpeg`
- **Linux（有 apt-get）** → `sudo -n apt-get install -y ffmpeg`（非交互，需免密 sudo）
- **Windows（有 winget，Win10+ 自带）** → `winget install -e --id Gyan.FFmpeg`
- **其它（无 brew/apt-get/winget）** → 不自动装，直接提示手动安装命令

> 安装需联网、为系统级操作，耗时长、体积大，故仅在显式带 `--install-ffmpeg` 时执行；默认不擅自装包。安装超时（>10 分钟）或失败不会报错崩溃，而是降级为退出码 8 并把对应平台的手动安装命令转达给用户。agent 看到退出码 8 应主动询问用户是否自动安装，或直接转达手动命令：macOS `brew install ffmpeg`、Ubuntu/Debian `sudo apt install ffmpeg`、Windows `winget install Gyan.FFmpeg` 或从 https://ffmpeg.org/download.html 下载解压后把 bin 目录加入 PATH。

## 可选依赖（台词转写，选装）

用于把视频口播内容转写为文字。**未安装不报错**，脚本会自动降级为“仅画面分析”，并在报告中标注缺失台词。任选其一即可，脚本按以下顺序自动探测：

> ⚡ **转写速度提示**：若启用台词分析，转写是仅次于看帧的耗时项。**whisper-cpp（预编译、无 torch）在 CPU 上比 openai-whisper 快数倍**；想要台词又嫌慢，优先装 whisper-cpp + `ggml-base`/`ggml-small` 小模型（`medium` 更准但更慢）。不需要逐字台词时，直接 `--no-transcribe` 或不装 Whisper，走画面推断最快。

1. **whisper-cpp（推荐，跨平台最快、轻量纯本地、预编译无 torch）**
   - macOS：`brew install whisper-cpp`
   - 下载模型到默认目录，例如 `ggml-medium.bin`（也可用 `ggml-base` / `ggml-small`）。模型放入 `$(brew --prefix)/share/whisper-cpp/` 或通过 `WHISPER_CPP_MODEL` 环境变量指定绝对路径。
   - 项目：https://github.com/ggerganov/whisper.cpp
2. **mlx-whisper（Apple Silicon 友好，轻量无 torch）**
   - `pip install -i https://pypi.tuna.tsinghua.edu.cn/simple mlx-whisper`（国内免翻墙）
   - 首次运行自动下载模型。
3. **openai-whisper（Windows / Intel Mac / Linux，功能全，依赖 torch）**
   - `pip install -i https://pypi.tuna.tsinghua.edu.cn/simple openai-whisper`（国内免翻墙）
   - 提供 `whisper` CLI；CLI 不在 PATH 时脚本自动回退进程内 API。

### 一键自动安装（`--install-whisper`，Win/Mac 均支持）

若脚本探测不到任何 Whisper，可在命令行加 `--install-whisper`，脚本按平台自动安装后重新转写：

- **macOS（有 brew）** → 优先 `brew install whisper-cpp`（预编译最轻）
- **macOS Apple Silicon（无 brew）** → pip 装 `mlx-whisper`（国内镜像）
- **macOS Intel / Windows / Linux** → pip 装 `openai-whisper`（国内镜像，依赖 torch）

pip 统一走国内镜像（清华 `https://pypi.tuna.tsinghua.edu.cn/simple`，失败回退阿里），确保免翻墙。装了若 CLI 不在 PATH，转写会自动回退进程内 API，不影响使用。

> Whisper 为选装依赖，体积大、安装耗时，默认不强引导安装；未装时自动降级为画面推断、不影响出报告。仅当用户主动要启用台词分析时，带 `--install-whisper` 安装。安装与首次下模型需联网、一次性操作，不影响「全程本地处理视频」的隐私承诺。pip 安装失败不报错，降级为无台词模式并提示手动安装。

## 环境变量

- `WHISPER_CPP_MODEL`：可选，whisper-cpp 模型文件的绝对路径。未设置时脚本尝试在常见 brew 路径自动查找。
- `WHISPER_LANG`：可选，强制转写语言（如 `zh`、`en`）。未设置时由 Whisper 自动检测（建议中文视频设为 `zh`，见脚本 `--lang`）。

## 隐私

素材提取阶段全程本地执行：视频、画面帧、音频均不出本机，该阶段无网络请求、无 API Key。报告生成后，免费版会把报告**提交到服务端做登记**（报告正文发往零一数科提交端点，body 为 `{"content": 报告正文, "scene": "full_deconstruct"}`，仅报告文本、不含视频/帧/音频/路径/环境）；报告登记为免费版使用前提，启动一次性告知后自动执行、旁路非阻塞、失败不阻塞报告交付（详见 SKILL.md「📤 免费版报告登记说明」）。