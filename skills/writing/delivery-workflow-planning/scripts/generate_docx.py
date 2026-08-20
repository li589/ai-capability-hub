# -*- coding: utf-8 -*-
"""
生成 Word 业务流程规划文档（依赖 tencent-local-office-edit skill 的 edsdk.py）
- create_doc 创建空白文档 → doc_insert_html_content 分块插入 HTML → save_file 保存
- 用法: python generate_docx.py <输出.docx> <章节JSON文件>
- 章节JSON: [{"idx": n, "html": "..."}, ...] 或 [{"html": "..."}, ...]（自动推进 idx）
"""
import subprocess
import json
import sys
import os
import re

PY = sys.executable
EDIT_SDK_DIR = r"C:/Program Files/WorkBuddy/resources/app.asar.unpacked/resources/plugins/workbuddy-builtin/skills/tencent-local-office-edit"
EDIT_SDK_PY = os.path.join(EDIT_SDK_DIR, "edsdk.py")


def call(tool, **kwargs):
    cmd = [PY, EDIT_SDK_PY, "call", tool]
    for k, v in kwargs.items():
        cmd.append(f"{k}={v}")
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    try:
        return json.loads(r.stdout)
    except Exception:
        # create_doc 等工具返回纯文本: "Created blank doc ... file_id=xxx, file_path=..."
        raw = r.stdout.strip()
        if "file_id=" in raw:
            m = re.search(r"file_id=([\w_-]+)", raw)
            if m:
                return {"file_id": m.group(1), "raw": raw}
        return {"raw": raw[:500]}


def build_doc(chapters, target):
    """chapters: list of HTML 片段；target: 输出路径"""
    # 1. 创建空白文档
    created = call("create_doc")
    if "file_id" not in created:
        print("create_doc 失败:", created)
        return False
    fid = created["file_id"]
    print("已创建文档:", fid)

    # 2. 顺序插入 HTML
    idx = 0
    for i, html in enumerate(chapters):
        r = call("doc_insert_html_content", file_id=fid, idx=str(idx), html_text=html)
        if isinstance(r, dict) and "position" in r:
            idx = r["position"] + 1
        else:
            idx += 1
        print(f"插入第{i+1}/{len(chapters)}段, idx≈{idx}")

    # 3. 保存到目标路径
    saved = call("save_file", file_id=fid, file_path=target)
    print("保存:", str(saved)[:200])
    return True


def main():
    if len(sys.argv) < 3:
        print("用法: python generate_docx.py <输出.docx> <章节JSON文件>")
        return 1
    target = sys.argv[1]
    with open(sys.argv[2], encoding="utf-8") as f:
        chapters = json.load(f)
    if isinstance(chapters, list) and chapters and isinstance(chapters[0], dict) and "html" in chapters[0]:
        chapters = [c["html"] for c in chapters]
    build_doc(chapters, target)
    return 0


if __name__ == "__main__":
    sys.exit(main())
