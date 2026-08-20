"""
天天基金网吧评论爬虫
从东方财富股吧获取基金用户讨论和评价
"""
import requests
import re
import json
import time
import random
from datetime import datetime
from bs4 import BeautifulSoup

class GubaScraper:
    """股吧爬虫"""

    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Referer': 'https://guba.eastmoney.com/',
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def scrape_fund_comments(self, fund_code, pages=5):
        """
        爬取基金讨论区帖子
        :param fund_code: 基金代码（如 000001）
        :param pages: 爬取页数
        :return: 评论列表
        """
        comments = []
        fund_code = str(fund_code).zfill(6)

        # 尝试多种URL格式
        url_formats = [
            f'https://guba.eastmoney.com/list,f{fund_code},{{page}},f.html',
            f'https://guba.eastmoney.com/list,fund{fund_code},{{page}},f.html',
        ]

        for url_format in url_formats:
            print(f"尝试格式: {url_format[:60]}...")

            for page in range(1, pages + 1):
                url = url_format.format(page=page)

                try:
                    r = self.session.get(url, timeout=10)

                    # 检测是否有有效内容
                    if r.status_code == 200 and len(r.text) > 10000:
                        page_comments = self._parse_page(r.text, fund_code)
                        if page_comments:
                            comments.extend(page_comments)
                            print(f"  第{page}页: 找到{len(page_comments)}条评论")
                        else:
                            print(f"  第{page}页: 无有效评论")
                    else:
                        print(f"  第{page}页: 状态={r.status_code}, 长度={len(r.text)}")

                except Exception as e:
                    print(f"  第{page}页错误: {e}")

                time.sleep(random.uniform(0.5, 1.5))

            if comments:
                break  # 找到有效数据后不再尝试其他格式

        return comments

    def _parse_page(self, html, fund_code):
        """解析页面，提取评论"""
        comments = []

        try:
            soup = BeautifulSoup(html, 'html.parser')

            # 尝试查找帖子列表容器
            post_list = soup.find('div', class_='post-list')
            if not post_list:
                post_list = soup.find('div', id='post-list')
            if not post_list:
                post_list = soup.find('ul', class_='list')

            if post_list:
                posts = post_list.find_all('div', class_='post-item')
                for post in posts:
                    comment = self._extract_post(post, fund_code)
                    if comment:
                        comments.append(comment)
            else:
                # 直接从HTML中正则提取
                comments = self._extract_from_html(html, fund_code)

        except Exception as e:
            print(f"解析错误: {e}")

        return comments

    def _extract_post(self, post_elem, fund_code):
        """从帖子元素中提取信息"""
        try:
            # 标题
            title_elem = post_elem.find('a', class_='title')
            title = title_elem.text.strip() if title_elem else ''

            # 回复数、阅读数
            reply_elem = post_elem.find('span', class_='reply')
            reply_count = int(reply_elem.text.strip()) if reply_elem else 0

            view_elem = post_elem.find('span', class_='view')
            view_count = int(view_elem.text.strip()) if view_elem else 0

            # 作者
            author_elem = post_elem.find('span', class_='author')
            author = author_elem.text.strip() if author_elem else '匿名'

            # 发布时间
            time_elem = post_elem.find('span', class_='time')
            post_time = time_elem.text.strip() if time_elem else ''

            if title:
                return {
                    'fund_code': fund_code,
                    'title': title,
                    'author': author,
                    'reply_count': reply_count,
                    'view_count': view_count,
                    'post_time': post_time,
                    'source': 'eastmoney_guba'
                }

        except Exception as e:
            pass

        return None

    def _extract_from_html(self, html, fund_code):
        """直接从HTML文本提取评论数据"""
        comments = []

        # 尝试多种正则模式
        patterns = [
            # 模式1: JSON格式
            r'\{"title":"([^"]+)","replycount":(\d+),"viewcount":(\d+)[^}]*"username":"([^"]+)"[^}]*\}',
            # 模式2: HTML属性
            r'data-title="([^"]+)"[^>]*data-reply="(\d+)"[^>]*data-view="(\d+)"',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, html)
            for match in matches:
                if len(match) >= 4:
                    title, reply, view, author = match[:4]
                    comments.append({
                        'fund_code': fund_code,
                        'title': title,
                        'reply_count': int(reply),
                        'view_count': int(view),
                        'author': author,
                        'source': 'eastmoney_guba'
                    })

        return comments

    def scrape_with_search(self, fund_code, keywords=None):
        """
        通过搜索引擎方式获取讨论（备用方案）
        """
        # 这是一个备用方案，当直接爬取失败时使用
        fund_code = str(fund_code).zfill(6)

        # 使用东方财富的搜索API
        search_url = f'https://search-api-web.eastmoney.com/search/jsonp?cb=&param={{"uid":"","keyword":"{fund_code}基金","type":[\"POST\"],\"client":"web","clientType":"pc","clientVersion":"curr","param":{{"pageindex":1,"pagesize":10,"sort":"tbSttSort","keyword":"{fund_code}","classify":"sb","market":" fund","row":"title,replycount,viewcount,username,postdate","time":"","filtermodel":"","keywords":""}}}}'

        try:
            r = self.session.get(search_url, timeout=10)
            if r.status_code == 200:
                # 解析返回的JSONP
                text = r.text
                # 提取JSON部分
                match = re.search(r'\((\{.*\})\)', text)
                if match:
                    data = json.loads(match.group(1))
                    return data.get('result', [])
        except Exception as e:
            print(f"搜索API错误: {e}")

        return []


def scrape_major_funds(fund_codes, output_path):
    """批量爬取主要基金的讨论"""
    scraper = GubaScraper()

    all_comments = []
    total = len(fund_codes)

    for i, code in enumerate(fund_codes):
        print(f"\n[{i+1}/{total}] 爬取基金 {code}...")

        comments = scraper.scrape_fund_comments(code, pages=3)

        for c in comments:
            c['fund_code'] = str(code).zfill(6)
            c['scraped_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        all_comments.extend(comments)

        print(f"  获取到 {len(comments)} 条讨论")

        # 保存进度
        if (i + 1) % 10 == 0:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'comments': all_comments,
                    'meta': {
                        'total': len(all_comments),
                        'last_update': datetime.now().strftime('%Y-%m-%d'),
                        'funds_scraped': i + 1
                    }
                }, f, ensure_ascii=False, indent=2)
            print(f"  进度已保存: {len(all_comments)} 条")

        time.sleep(random.uniform(1, 2))

    return all_comments


def main():
    scraper = GubaScraper()

    print("=" * 60)
    print("天天基金网吧评论爬虫")
    print("=" * 60)

    # 测试单个基金
    test_codes = ['000001', '110011', '270007']

    for code in test_codes:
        print(f"\n{'='*40}")
        print(f"爬取基金: {code}")
        print(f"{'='*40}")

        comments = scraper.scrape_fund_comments(code, pages=2)

        if comments:
            print(f"\n获取到 {len(comments)} 条讨论:")
            for c in comments[:5]:
                print(f"  [{c.get('reply_count', 0)}回复] {c.get('title', '')[:50]}")
                print(f"    作者: {c.get('author', '匿名')} | 时间: {c.get('post_time', '')}")
        else:
            print("  未能获取到评论数据")

        time.sleep(1)

    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()