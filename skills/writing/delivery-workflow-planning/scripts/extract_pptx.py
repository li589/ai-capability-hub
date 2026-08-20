# -*- coding: utf-8 -*-
"""
PPTX 文本提取（纯标准库，零依赖）
- 原理：pptx 本质是 zip + XML，直接解析 <a:t> 文本节点
- 用途：提取售前方案 / 蓝图 PPT 的全部文本内容
- 用法：python extract_pptx.py <file.pptx> [输出.json]
"""
import zipfile
import re
import json
import sys


def extract_pptx_text(path):
    """返回 [{slide, texts:[...]}, ...]"""
    with zipfile.ZipFile(path) as z:
        slide_files = sorted(
            [n for n in z.namelist() if re.match(r'ppt/slides/slide\d+\.xml$', n)],
            key=lambda n: int(re.search(r'slide(\d+)\.xml', n).group(1))
        )
        result = []
        for sf in slide_files:
            xml = z.read(sf).decode('utf-8', errors='replace')
            texts = re.findall(r'<a:t>([^<]*)</a:t>', xml)
            result.append({"slide": sf, "texts": texts})
        return result


def main():
    if len(sys.argv) < 2:
        print("用法: python extract_pptx.py <file.pptx> [输出.json]")
        return 1
    path = sys.argv[1]
    data = extract_pptx_text(path)
    out = sys.argv[2] if len(sys.argv) > 2 else path.replace(".pptx", "_文本.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    for d in data:
        joined = " | ".join(t for t in d["texts"] if t)
        num = re.search(r'slide(\d+)', d["slide"]).group(1)
        print(f"--- Slide {num} ---")
        print(joined[:400])
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
