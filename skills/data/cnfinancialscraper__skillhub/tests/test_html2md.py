# -*- coding: utf-8 -*-
"""html2md.py 单元测试 — 覆盖块级/行内/表格/图片/代码/边界。"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.dont_write_bytecode = True

import unittest
from scripts.html2md import convert, convert_with_tables


class TestHtml2MdBasic(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(convert(""), "")
        self.assertEqual(convert(None), "")

    def test_paragraph(self):
        md = convert("<p>hello world</p>")
        self.assertIn("hello world", md)

    def test_headings(self):
        for i in range(1, 7):
            md = convert(f"<h{i}>标题</h{i}>")
            self.assertIn(f"{'#' * i} 标题", md)

    def test_bold_italic(self):
        md = convert("<p><strong>bold</strong> and <em>italic</em></p>")
        self.assertIn("**bold**", md)
        self.assertIn("*italic*", md)

    def test_link(self):
        md = convert('<a href="https://example.com">链接</a>')
        self.assertIn("[链接](https://example.com)", md)

    def test_image_with_map(self):
        md = convert('<img src="https://x.com/a.png" alt="图">',
                     image_map={"https://x.com/a.png": "./a.png"})
        self.assertIn("![图](./a.png)", md)

    def test_image_without_map(self):
        md = convert('<img src="https://x.com/a.png" alt="图">')
        self.assertIn("![图](https://x.com/a.png)", md)

    def test_line_break(self):
        md = convert("a<br>b")
        self.assertIn("a\nb", md)

    def test_horizontal_rule(self):
        md = convert("<hr>")
        self.assertIn("---", md)

    def test_drop_script(self):
        md = convert("<p>前<script>alert(1)</script>后</p>")
        self.assertNotIn("alert", md)
        self.assertIn("前后", md)

    def test_drop_style(self):
        md = convert("<style>body{}</style><p>内容</p>")
        self.assertNotIn("body", md)
        self.assertIn("内容", md)

    def test_blockquote(self):
        md = convert("<blockquote>引用文字</blockquote>")
        self.assertIn("引用文字", md)

    def test_unordered_list(self):
        md = convert("<ul><li>a</li><li>b</li></ul>")
        self.assertIn("- a", md)
        self.assertIn("- b", md)

    def test_ordered_list(self):
        md = convert("<ol><li>a</li><li>b</li></ol>")
        self.assertIn("1. a", md)
        self.assertIn("1. b", md)


class TestHtml2MdCode(unittest.TestCase):
    def test_inline_code(self):
        md = convert("<p>看 <code>x</code> 变量</p>")
        self.assertIn("`x`", md)

    def test_pre_block(self):
        md = convert("<pre>print('hi')</pre>")
        self.assertIn("```", md)
        self.assertIn("print('hi')", md)

    def test_pre_with_language(self):
        md = convert('<pre><code class="language-python">print(1)</code></pre>')
        self.assertIn("```python", md)


class TestHtml2MdTable(unittest.TestCase):
    def test_simple_table(self):
        html = ('<table><thead><tr><th>A</th><th>B</th></tr></thead>'
                '<tbody><tr><td>1</td><td>2</td></tr></tbody></table>')
        md = convert_with_tables(html)
        self.assertIn("| A | B |", md)
        self.assertIn("| --- | --- |", md)
        self.assertIn("| 1 | 2 |", md)

    def test_table_with_pipe_in_cell(self):
        html = ('<table><thead><tr><th>标题</th></tr></thead>'
                '<tbody><tr><td>有|竖线</td></tr></tbody></table>')
        md = convert_with_tables(html)
        # | 应被转义
        self.assertIn("\\|", md)


class TestHtml2MdEdge(unittest.TestCase):
    def test_relative_url_resolved(self):
        md = convert('<a href="/page">链接</a>', base_url="https://x.com")
        self.assertIn("https://x.com/page", md)

    def test_already_absolute(self):
        md = convert('<a href="https://y.com/p">x</a>', base_url="https://x.com")
        self.assertIn("https://y.com/p", md)

    def test_nested_strong_in_link(self):
        md = convert('<a href="https://x.com"><strong>重点</strong></a>')
        self.assertIn("**重点**", md)
        self.assertIn("https://x.com", md)

    def test_iframe_to_text(self):
        md = convert('<iframe src="https://x.com/embed"></iframe>')
        self.assertIn("[iframe:", md)
        self.assertIn("x.com/embed", md)

    def test_unclosed_tag_tolerant(self):
        # 容错：未闭合的 <p> 不应崩
        md = convert("<p>hello")
        self.assertIn("hello", md)

    def test_html_entities_decoded(self):
        # html.parser 默认 decode entity；这是预期行为
        md = convert("<p>5 &lt; 10 &amp; true</p>")
        self.assertIn("5 < 10", md)
        self.assertIn("& true", md)


class TestHtml2MdWhitespace(unittest.TestCase):
    def test_multiple_newlines_collapsed(self):
        md = convert("<p>a</p>\n\n\n\n<p>b</p>")
        # 不应超过 2 个连续换行
        self.assertNotIn("\n\n\n", md)

    def test_whitespace_in_text_collapsed(self):
        md = convert("<p>hello     world</p>")
        self.assertIn("hello world", md)


if __name__ == "__main__":
    unittest.main()