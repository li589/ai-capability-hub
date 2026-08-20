# 答辩-skills 工具集

本目录包含两个独立但相关的 CLI 工具，用于学位论文答辩场景的文本处理与语音转写：

- thesis_parser.py: 将论文文本从 PDF/TXT/Markdown 中解析为结构化的 JSON，包含题名、摘要、章节、图表、参考文献等信息。
- audio_transcriber.py: 使用本地 OpenAI Whisper 实现音频转写，输出带分段的转写结果 JSON。

安装与依赖
- Python 3.8+ 环境
- 安装依赖（建议使用虚拟环境）
  - thesis_parser 依赖：无额外依赖；在 PDF 时可能会用到 pdfplumber 或 PyPDF2，需通过 Pip 安装：
    - pdfplumber（可选，最好同时安装 PyPDF2）
    - PyPDF2
- audio_transcriber 依赖：whisper，以及其运行所需的 ffmpeg
- ffmpeg：确保 ffmpeg 已安装并在系统路径中。
- 安装 Whisper：pip install whisper

用法示例
- 论文解析
  python /Users/eimei/Desktop/答辩-skill/tools/thesis_parser.py --input /path/to/thesis.pdf
  结果将输出到 stdout，为结构化的 JSON。

- 语音转写
  python /Users/eimei/Desktop/答辩-skill/tools/audio_transcriber.py --input /path/to/presentation.wav --output /path/to/result.json --model base
  结果写入 JSON 文件，同时在 stdout 给出简要信息。

注意事项
- thesis_parser 仅提取文本信息；不包含文本评审/阅览功能。
- audio_transcriber 使用开源 Whisper，所有处理均在本地进行，不调用任何付费 API。
- 若未安装依赖，首先通过 pip 安装所需包；如 pdf 解析出现问题，请确保 pdfplumber、PyPDF2 已正确安装。
