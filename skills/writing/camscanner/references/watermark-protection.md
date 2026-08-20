# 文档水印保护工作流

> **前置阅读**：`references/image-processing.md`（image watermark 参数）、`references/pdf-processing.md`（pdf watermark/remove-watermark 参数）

## 场景

用户需要给文档添加水印保护后分享，或去除已有水印。

## 决策树

| 用户需求 | 输入类型 | 路由到 |
|----------|----------|--------|
| 加水印 | 图片 | `image watermark` |
| 加水印 | PDF | `pdf watermark` |
| 去水印 | PDF | `pdf remove-watermark` |
| 去水印 | 图片 | `image enhance --mode 10` |

## 参数推荐

| 场景 | 推荐参数 |
|------|----------|
| 内部文档 | `--text "内部资料" --opacity 0.3` |
| 草稿标记 | `--text "DRAFT" --opacity 0.2 --color "#999999"` |
| 版权保护 | `--text "© 公司名" --opacity 0.15 --size 36` |
| 机密文件 | `--text "机密" --opacity 0.4 --color "#FF0000"` |

## 注意事项

- PDF 水印最大支持 100 页
- 去水印效果取决于原始水印的复杂度
- 图片水印为不可逆操作（原图不会被修改，产出新文件）
