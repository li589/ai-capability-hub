# yescan-scan-qoder

[![ClawHub Downloads](https://img.shields.io/badge/ClawHub-1k_downloads-blue?logo=data:image/svg%2Bxml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0id2hpdGUiPjxwYXRoIGQ9Ik0xMiAyQzYuNDggMiAyIDYuNDggMiAxMnM0LjQ4IDEwIDEwIDEwIDEwLTQuNDggMTAtMTBTMTcuNTIgMiAxMiAyem0tMiAxNWwtNS01IDEuNDEtMS40MUwxMCAxNC4xN2w3LjU5LTcuNTlMMTkgOGwtOSA5eiIvPjwvc3ZnPg==)](https://clawhub.ai/yescan-ai/yescan-scan-universal)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> 夸克扫描王 · 图像增强 Agent Skill — 适用于 Qoder 平台
>
> 📦 ClawHub 主页：[yescan-scan-universal](https://clawhub.ai/yescan-ai/yescan-scan-universal)

当用户需要对图片、截图进行画质优化、瑕疵去除或视觉增强时，AI Agent 可通过本技能自动调用夸克扫描王图像增强 API，完成从意图识别到命令执行的全流程。

## 功能概览

- **13 种图像增强场景**：考试增强、画质增强、证件票据增强、去手写、去水印、去阴影、去屏纹、去底色、裁剪矫正、素描速写、提取线稿、扫描合同、通用扫描
- **多种输入方式**：图片 URL / 本地文件路径 / BASE64 字符串
- **自动落盘**：增强后的图片自动保存至本地临时目录，返回文件路径
- **结构化输出**：统一 JSON 格式响应（code / message / data）

## 场景列表

| # | 场景名称 | scene 标识 | 典型用途 |
|---|---------|-----------|---------|
| 1 | 考试增强 | `exam-enhance` | 试卷、笔记、教材清晰化 |
| 2 | 画质增强 | `image-hd-enhance` | 模糊/低清/老照片增强 |
| 3 | 证件票据增强 | `certificate-enhance` | 身份证、发票、护照优化 |
| 4 | 图像去手写 | `remove-handwriting` | 去笔迹，还原空白文档 |
| 5 | 图像去水印 | `remove-watermark` | 仅限有权或获授权图片，去 Logo、水印、标记 |
| 6 | 图像去阴影 | `remove-shadow` | 去阴影、光照不均修复 |
| 7 | 图像去屏纹 | `remove-screen-pattern` | 摩尔纹、翻拍屏幕修复 |
| 8 | 文档去底色 | `remove-background-color` | 彩色背景→白底黑字 |
| 9 | 图像裁剪矫正 | `image-crop-rectify` | 透视矫正、边缘裁剪 |
| 10 | 素描速写 | `sketch-drawing` | 照片转素描/速写风格 |
| 11 | 提取线稿 | `extract-lineart` | 提取轮廓线条 |
| 12 | 扫描合同 | `scan-contract` | 合同/协议画质增强归档 |
| 13 | 扫描文件 | `scan-document` | 通用兜底场景 |

## 快速开始

### 环境要求

- Python 3.9+
- `requests` 库（唯一第三方依赖）

```bash
pip install requests
```

### 配置 API Key

将夸克扫描王的 API Key 写入 `~/.yescan_env`：

```bash
echo 'SCAN_WEBSERVICE_KEY=<your_api_key>' > ~/.yescan_env
```

> 获取方式：访问 https://scan.quark.cn/business → 开发者后台 → 登录/注册 → 查看 API Key

### 使用示例

```bash
# URL 输入
python3 scripts/scan.py --scene image-hd-enhance --url "https://example.com/photo.jpg"

# 本地文件
python3 scripts/scan.py --scene exam-enhance --path "/path/to/exam.jpg"

# BASE64
python3 scripts/scan.py --scene remove-watermark --base64 "<base64_string>"

# 指定平台标识
python3 scripts/scan.py --scene scan-document --url "https://example.com/doc.jpg" --platform qoderWork
```

### 输出示例

```json
{
  "code": "00000",
  "message": "success",
  "data": {
    "path": "/tmp/imgs/1718529600_a1b2c3d4e5f6.png"
  }
}
```

## 项目结构

```
yescan-scan-qoder/
├── SKILL.md                      # Agent 技能描述文件（意图匹配 + 执行规范）
├── README.md                     # 本文档
├── LICENSE                       # 开源许可证
├── references/
│   ├── scenes.md                 # 各场景详细触发意图与示例指令
│   └── limitations.md            # 不适用场景与限制说明
├── evals/
│   └── evals.json                # 技能评估用例
└── scripts/
    ├── scan.py                   # 主入口脚本
    └── common/
        ├── __init__.py           # 模块导出
        ├── settings.py           # 部署配置（API 地址、平台、版本）
        ├── constants.py          # 公共常量
        ├── messages.py           # 用户提示消息
        ├── validators.py         # URL / 文件验证器
        ├── ocr_client.py         # API 客户端核心
        ├── scene_configs.py      # 场景配置映射
        ├── runner.py             # CLI 通用执行器
        ├── file_saver.py         # 图片落盘工具
        └── result_handlers.py    # 结果处理器
```

## 工作原理

```
用户指令 → Agent 意图匹配 → 确定 scene → 执行 scan.py
                                              ↓
                                     读取图片 (URL/路径/BASE64)
                                              ↓
                                     调用夸克图像增强 API
                                              ↓
                                     解码返回的 BASE64 图片
                                              ↓
                                     保存至本地 /tmp/imgs/
                                              ↓
                                     输出 JSON（含本地路径）
```

## 隐私说明

- 本技能会将图片通过 HTTPS 发送至夸克扫描王服务器 (`scan-business.quark.cn`) 进行处理
- 服务端处理后不会永久保存用户图片
- 处理结果图片保存在本地临时目录，直到用户手动清理
- 执行任何图片处理前，请确认用户已知悉图片会上传至第三方服务并同意处理；身份证、合同、票据、医疗记录、个人照片等敏感图片需获得明确授权
- `remove-watermark` 仅限处理用户拥有权利或已获授权的图片，不得用于移除第三方版权标识、平台水印、署名信息或其他权利声明

## 限制

- 仅支持单张静态图片，不支持视频或批量处理
- 本地文件大小限制 5MB
- 支持格式：jpg / jpeg / png / gif / bmp / webp / tiff / wbmp

## 相关资源

- [夸克扫描王开放平台](https://scan.quark.cn/business) — 密钥申请、API 文档
- [ClawHub 技能页](https://clawhub.ai/yescan-ai/yescan-scan-universal) — 安装、下载量、评分
- [QoderWork](https://qoder.com) — Agent 运行环境
- [yescan-ai GitHub Org](https://github.com/yescan-ai) — 更多技能

## License

见 [LICENSE](./LICENSE) 文件。
