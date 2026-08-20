# 视频录屏 → Word 操作手册 工作流参考

## 总体流程

```
用户提供: 视频文件(.mp4) + 操作说明(文字描述步骤) + 参考文档(可选)
          ↓
Phase 1: 分析阶段 —— 理解视频内容和用户意图
Phase 2: 截图阶段 —— 提取关键帧，匹配步骤
Phase 3: 生成阶段 —— 组装 JSON 配置，调用脚本生成 Word 文档
```

## Phase 1：分析阶段

### 1.1 获取视频基本信息
使用 ffprobe 获取时长、分辨率、编码：
```bash
ffprobe -v quiet -print_format json -show_format -show_streams <video_path>
```

### 1.2 理解用户意图
- 用户通常会描述"视频展示的是什么操作"、"大致步骤"
- 以用户描述为主线索，视频帧仅用于**确认细节**和**截取对应画面**
- 如果用户没有提供描述，需要先基于视频帧分析出操作流程并请用户确认

## Phase 2：截图阶段

### 2.1 粗略扫描
以 30 秒间隔提取帧，快速了解视频全貌：
```bash
ffmpeg -i <video> -vf "fps=1/30" <output_dir>/frame_%04d.png -y
```

### 2.2 匹配步骤与帧
- 将用户的每一步描述与粗略帧进行匹配
- 找到每个步骤对应的正确时间戳
- 如果某些步骤的帧不准确，以更小的步长（5s, 1s）做精细扫描

### 2.3 提取最终截图
用 ffmpeg 在精确时间戳提取高分辨率截图：
```bash
ffmpeg -ss <timestamp> -i <video> -vframes 1 <output>.png -y
```

截图命名规则：`<序号>-<步骤简述>.png`（如 `01-seq-error-log.png`）

## Phase 3：生成阶段

### 3.1 组装 JSON 配置
按以下结构组织文档内容：

```json
{
  "title": "文档标题",
  "subtitle": "副标题（流程简述）",
  "date_line": "日期 + 视频来源",
  "output": "output.docx",
  "sections": [
    {"type": "heading", "text": "一、章节标题", "level": 1},

    {"type": "para", "text": "普通段落文字", "bold": false},
    {"type": "note", "text": "重要的提示信息（蓝色加粗）"},
    {"type": "bullet", "text": "列表项", "level": 0},
    {"type": "numbered", "text": "编号步骤"},

    {"type": "table", "headers": ["列1", "列2"], "rows": [["值1", "值2"]]},

    {"type": "screenshot", "file": "01-xxx.png", "caption": "图：截图说明"},

    {"type": "code", "text": "SET GLOBAL local_infile = ON;"},

    {"type": "page_break"},

    {"type": "heading", "text": "X. 附录", "level": 1}
  ]
}
```

### 3.2 调用生成脚本
```bash
python generate_manual.py config.json -o output.docx --screenshot-dir ./screenshots
```

### 3.3 验证和交付
- 确认文件大小合理
- 用 present_files 展示给用户

## 元素类型速查

| type | 说明 | 必需字段 |
|------|------|----------|
| heading | 章节标题 | text, level(1-3) |
| para | 普通段落 | text, bold(可选) |
| note | 重要提示 | text |
| bullet | 无序列表 | text |
| numbered | 有序列表 | text |
| code | 代码块 | text |
| table | 表格 | headers, rows |
| screenshot | 截图 | file, caption(可选) |
| page_break | 分页符 | 无 |

## 脱敏规则

以下信息必须替换为占位符：
- IP 地址 → `XXXX.XXXX.XXXX.XXXX`
- 端口号 → `XXXX`
- 密码 → `******` 或直接删除
- 具体服务器域名 → `XXXX`

在上层文档描述中直接使用脱敏后的值，不需要在 JSON 配置中再次替换。
