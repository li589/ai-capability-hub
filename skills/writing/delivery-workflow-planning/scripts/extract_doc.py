# -*- coding: utf-8 -*-
"""
DOC（老格式 .doc）文本提取（依赖 win32com + 本机 WPS/Word）
- 依次尝试 WPS (KWPS.Application) 和 MS Word (Word.Application)
- 用法: python extract_doc.py <file.doc> [输出.txt]
"""
import sys
import os
import win32com.client


def extract_doc_text(path):
    app = None
    try:
        app = win32com.client.Dispatch("KWPS.Application")
        app.Visible = False
        print("using KWPS")
    except Exception:
        try:
            app = win32com.client.Dispatch("Word.Application")
            app.Visible = False
            print("using Word")
        except Exception as e:
            raise RuntimeError(f"本机无 WPS/Word COM 接口: {e}")
    doc = app.Documents.Open(path, ReadOnly=True)
    text = doc.Content.Text
    doc.Close(False)
    app.Quit()
    return text


def main():
    if len(sys.argv) < 2:
        print("用法: python extract_doc.py <file.doc> [输出.txt]")
        return 1
    path = sys.argv[1]
    text = extract_doc_text(path)
    out = sys.argv[2] if len(sys.argv) > 2 else path.replace(".doc", "_文本.txt")
    with open(out, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"字数: {len(text)}")
    print(text[:2000])
    return 0


if __name__ == "__main__":
    sys.exit(main())
