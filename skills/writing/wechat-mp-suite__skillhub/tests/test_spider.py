#!/usr/bin/env python3
"""wechat-mp-suite 爬虫模块测试"""
import sys, os, pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from scripts.spider.scraper import extract_article_content, html_to_markdown
from scripts.spider.images import extract_images, get_image_filename

class TestScraper:
    def test_extract_title(self):
        html = '<html><head><meta property="og:title" content="测试标题"/></head><body><h1 class="rich_media_title">测试标题</h1><div id="js_content"><p>正文</p></div></body></html>'
        r = extract_article_content(html, 'https://mp.weixin.qq.com/s/test')
        assert r['title'] == '测试标题'
    def test_extract_no_title(self):
        r = extract_article_content('<html><body><div id="js_content"><p>正文</p></div></body></html>', 'https://mp.weixin.qq.com/s/test')
        assert '微信文章' in r['title']
    def test_extract_author(self):
        html = '<html><body><span class="rich_media_meta_nickname">作者名</span><div id="js_content"><p>正文</p></div></body></html>'
        r = extract_article_content(html, 'https://mp.weixin.qq.com/s/test')
        assert r['author'] == '作者名'
    def test_extract_no_content(self):
        r = extract_article_content('<html><body><p>无正文</p></body></html>', 'https://mp.weixin.qq.com/s/test')
        assert r['content_html'] == ''

class TestHtmlToMarkdown:
    def test_headings(self):
        md = html_to_markdown('<h1>H1</h1><h2>H2</h2><h3>H3</h3>', 'https://ex.com', {})
        assert '# H1' in md and '## H2' in md and '### H3' in md
    def test_paragraph(self):
        md = html_to_markdown('<p>段1</p><p>段2</p>', 'https://ex.com', {})
        assert '段1' in md and '段2' in md
    def test_image_mapped(self):
        md = html_to_markdown('<img src="https://ex.com/a.jpg" alt="图"/>', 'https://ex.com', {'https://ex.com/a.jpg': 'images/001.jpg'})
        assert 'images/001.jpg' in md
    def test_blockquote(self):
        md = html_to_markdown('<blockquote>引用</blockquote>', 'https://ex.com', {})
        assert '> 引用' in md
    def test_unordered_list(self):
        md = html_to_markdown('<ul><li>A</li><li>B</li></ul>', 'https://ex.com', {})
        assert '- A' in md and '- B' in md
    def test_ordered_list(self):
        md = html_to_markdown('<ol><li>一</li><li>二</li></ol>', 'https://ex.com', {})
        assert '1. 一' in md and '2. 二' in md

class TestImages:
    def test_filename_ext(self):
        n = get_image_filename('https://ex.com/photo.jpg', 1)
        assert n.endswith('.jpg') and n.startswith('img_001_')
    def test_filename_no_ext(self):
        n = get_image_filename('https://ex.com/photo', 2)
        assert n.endswith('.jpg')
    def test_extract_images(self):
        html = '<html><body><img src="https://ex.com/1.jpg"/><img data-src="https://ex.com/2.jpg"/></body></html>'
        imgs = extract_images(html, 'https://ex.com')
        assert len(imgs) == 2
