#!/usr/bin/env python3
"""
微信公众号发布一站式脚本（run_pipeline）

串联「发布侧」六步：压缩封面 → 上传封面 → 可选上传正文图并替换 → MD 转 HTML → 建草稿 → 归档。
写作（Step 1-2 素材/撰写）仍在对话中由写作 skill 完成，本脚本接管后续机械流程。

用法：
  python3 run_pipeline.py \
    --article article.md \
    --cover   cover.png \
    --title   "文章标题" \
    --author  "作者名" \
    --digest  "摘要（≤50字）" \
    [--theme cyan] \
    [--body-images img1.png,img2.png] \
    [--out-dir articles/published] \
    [--app_id ... --app_secret ...]   # 可选，覆盖 .env
"""

import os
import sys
import re
import json
import argparse
import tempfile
from datetime import datetime
from pathlib import Path

# 确保同目录模块可导入（无论从哪个目录运行本脚本）
SCRIPT_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(SCRIPT_DIR))

import config
import compress_image
import upload_material
import markdown_to_wechat_doocs
import create_draft


APP_ID = ''
APP_SECRET = ''


def _safe_filename(title):
    """标题转安全文件名（去非法字符，截断 40 字）。"""
    name = re.sub(r'[\\/:*?"<>|]', '', title).strip()
    return name[:40] or 'article'


def _replace_local_images(md_text, local_paths):
    """上传正文图，并把 markdown 中的本地路径替换为微信 url。"""
    for local in local_paths:
        local = local.strip()
        if not local:
            continue
        res = upload_material.upload_material(
            app_id=APP_ID, app_secret=APP_SECRET, image_path=local
        )
        url = res.get('url')
        if not url:
            print(f"⚠️ 正文图上传失败，跳过替换：{local}", file=sys.stderr)
            continue
        base = os.path.basename(local)
        # 精确路径匹配，退而求其次按文件名匹配
        md_text = md_text.replace(f']({local})', f']({url})')
        md_text = md_text.replace(f'src="{local}"', f'src="{url}"')
        md_text = md_text.replace(f']({base})', f']({url})')
        md_text = md_text.replace(f'src="{base}"', f'src="{url}"')
        print(f"✅ 正文图已替换：{base} → 微信素材 url", file=sys.stderr)
    return md_text


def main():
    parser = argparse.ArgumentParser(
        description="微信公众号发布一站式脚本（压缩封面→上传→转HTML→建草稿→归档）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument('--article', required=True, help='文章 Markdown 路径')
    parser.add_argument('--cover', required=True, help='封面图路径')
    parser.add_argument('--title', required=True, help='文章标题')
    parser.add_argument('--author', default=None, help='作者名（可选）')
    parser.add_argument('--digest', default=None, help='摘要（≤50字，可选）')
    parser.add_argument('--theme', default=None,
                        help='主题 default/green/purple/orange/cyan，留空=按内容自动选')
    parser.add_argument('--body-images', default='',
                        help='正文图路径，逗号分隔，自动上传并替换本地路径')
    parser.add_argument('--out-dir', default=str(SCRIPT_DIR.parent / 'articles' / 'published'),
                        help='归档目录（默认 <skill>/articles/published）')
    parser.add_argument('--app_id', default=None, help='AppID（覆盖 .env）')
    parser.add_argument('--app_secret', default=None, help='AppSecret（覆盖 .env）')
    args = parser.parse_args()

    global APP_ID, APP_SECRET
    cfg = config.get_wechat_config()
    APP_ID = args.app_id or cfg.get('app_id', '')
    APP_SECRET = args.app_secret or cfg.get('app_secret', '')
    if not APP_ID or not APP_SECRET:
        print("错误: 缺少微信公众号配置（请配置 .env 或传 --app_id/--app_secret）", file=sys.stderr)
        sys.exit(1)

    # 1. 压缩封面（≤800KB）
    cover_out = os.path.join(tempfile.gettempdir(), f"wap_cover_{os.getpid()}.jpg")
    compress_image.compress_image(args.cover, cover_out, max_size_kb=800)
    print(f"📦 封面已压缩：{cover_out}", file=sys.stderr)

    # 2. 上传封面 → thumb_media_id
    cover_res = upload_material.upload_material(APP_ID, APP_SECRET, cover_out)
    thumb_media_id = cover_res.get('thumb_media_id')
    if not thumb_media_id:
        print(f"错误: 封面上传失败：{cover_res}", file=sys.stderr)
        sys.exit(1)
    print(f"🖼️ 封面上传成功 thumb_media_id={thumb_media_id}", file=sys.stderr)

    # 3. 读取文章
    if not os.path.isfile(args.article):
        print(f"错误: 文章不存在：{args.article}", file=sys.stderr)
        sys.exit(1)
    with open(args.article, 'r', encoding='utf-8') as f:
        md_text = f.read()

    # 4. 正文图上传 + 替换
    if args.body_images.strip():
        paths = [p for p in args.body_images.split(',') if p.strip()]
        md_text = _replace_local_images(md_text, paths)

    # 5. 选主题
    theme = args.theme or config.select_theme_by_content(args.title, md_text)
    print(f"🎨 主题：{theme}", file=sys.stderr)

    # 6. MD → 微信 HTML
    html = markdown_to_wechat_doocs.markdown_to_html_doocs(md_text, theme)

    # 7. 建草稿
    result = create_draft.create_draft(
        app_id=APP_ID, app_secret=APP_SECRET,
        title=args.title, content=html,
        thumb_media_id=thumb_media_id,
        author=args.author, digest=args.digest,
    )
    if result.get('status') != 'success':
        print(f"错误: 建草稿失败：{result}", file=sys.stderr)
        sys.exit(1)
    media_id = result.get('media_id')
    print(f"📝 草稿已创建 media_id={media_id}", file=sys.stderr)

    # 8. 归档
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    date = datetime.now().strftime('%Y%m%d')
    stem = _safe_filename(args.title)
    md_dst = out_dir / f"{date}_{stem}.md"
    meta_dst = out_dir / f"{date}_{stem}_meta.json"
    with open(md_dst, 'w', encoding='utf-8') as f:
        f.write(md_text)
    with open(meta_dst, 'w', encoding='utf-8') as f:
        json.dump({
            'title': args.title,
            'media_id': media_id,
            'thumb_media_id': thumb_media_id,
            'theme': theme,
            'created_at': datetime.now().isoformat(),
        }, f, ensure_ascii=False, indent=2)
    print(f"📁 已归档：{md_dst}", file=sys.stderr)

    print(f"\n✅ 完成！草稿 media_id={media_id}（默认仅存草稿，群发请在公众号后台确认）")


if __name__ == '__main__':
    main()
