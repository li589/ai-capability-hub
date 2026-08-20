"""图片下载处理模块 — 并行下载 + 重试 + 进度显示"""
import os
import re
import time
import hashlib
import logging
import concurrent.futures
from urllib.parse import urlparse, urljoin
from typing import List, Tuple
from functools import lru_cache

import requests

logger = logging.getLogger(__name__)

# 重试配置
MAX_RETRIES = 3
RETRY_DELAYS = [1, 3, 7]  # 指数退避（秒）
DEFAULT_THREADS = 5

# 尝试从 config_loader 读取配置
try:
    from spider.config_loader import config
    MAX_WORKERS = config.get("download.threads", DEFAULT_THREADS)
    MAX_RETRIES = config.get("download.max_retries", MAX_RETRIES)
    RETRY_DELAYS = config.get("download.retry_delays", RETRY_DELAYS)
except ImportError:
    logger.debug("config_loader not available, using default settings")
    MAX_WORKERS = DEFAULT_THREADS
except Exception:
    logger.debug("config_loader error, using default settings")
    MAX_WORKERS = DEFAULT_THREADS


def get_image_filename(url: str, index: int) -> str:
    """生成图片文件名，使用 12 位哈希避免重复"""
    parsed = urlparse(url)
    ext = os.path.splitext(parsed.path)[1]

    # 如果没有扩展名，尝试从 Content-Type 推断
    if not ext or len(ext) > 5:
        ext = '.jpg'  # 默认

    # 使用 URL 哈希生成唯一文件名，12 位降低碰撞概率
    url_hash = hashlib.md5(url.encode()).hexdigest()[:12]
    return f"img_{index:04d}_{url_hash}{ext}"


def download_image_with_retry(url: str, save_path: str, timeout: int = 15) -> bool:
    """下载单张图片，带重试和指数退避"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://mp.weixin.qq.com/'
    }

    last_exception = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.get(url, headers=headers, timeout=timeout, stream=True)
            response.raise_for_status()

            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            return True

        except Exception as e:
            last_exception = e
            if attempt < MAX_RETRIES:
                delay = RETRY_DELAYS[min(attempt - 1, len(RETRY_DELAYS) - 1)]
                logger.warning(f"⚠️ 下载失败（第{attempt}次/共{MAX_RETRIES}次）：{url} - {e}，{delay}s 后重试...")
                time.sleep(delay)

    logger.error(f"❌ 图片下载彻底失败（已重试{MAX_RETRIES}次）：{url} - {last_exception}")
    return False


def _download_one(args: tuple) -> tuple:
    """单个下载任务，用于线程池调度。返回 (img_url, success)"""
    img_url, save_path, idx, total = args
    success = download_image_with_retry(img_url, save_path)
    return (img_url, success)


def extract_images(html_content: str, base_url: str) -> List[Tuple[str, any]]:
    """从 HTML 中提取所有图片 URL"""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html_content, 'lxml')
    images = []

    # 查找所有 img 标签
    for img in soup.find_all('img'):
        src = img.get('src') or img.get('data-src')
        if src:
            # 处理相对 URL
            full_url = urljoin(base_url, src)
            images.append((full_url, img))

    return images


def save_images_and_update_html(images: List[Tuple[str, any]], output_dir: str, base_url: str) -> dict:
    """
    并行下载所有图片并返回 URL 到本地路径的映射
    """
    import logging as _logging
    _logging.basicConfig(level=_logging.INFO, format='%(message)s')

    images_dir = os.path.join(output_dir, 'images')
    os.makedirs(images_dir, exist_ok=True)

    # 去重：保留首次出现的 URL
    seen = set()
    unique_images = []
    for img_url, img_tag in images:
        if img_url not in seen:
            seen.add(img_url)
            unique_images.append((img_url, img_tag))

    total = len(unique_images)
    logger.info(f"📸 准备下载 {total} 张图片（去重后），使用 {MAX_WORKERS} 个线程")

    # 构建下载任务列表
    tasks = []
    filename_map = {}  # url -> filename
    for idx, (img_url, img_tag) in enumerate(unique_images, 1):
        filename = get_image_filename(img_url, idx)
        save_path = os.path.join(images_dir, filename)
        filename_map[img_url] = filename
        tasks.append((img_url, save_path, idx, total))

    url_mapping = {}
    downloaded_count = 0

    # 并行下载
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(_download_one, t): t for t in tasks}

        completed = 0
        for future in concurrent.futures.as_completed(futures):
            completed += 1
            img_url, success = future.result()
            filename = filename_map[img_url]

            if success:
                downloaded_count += 1
                relative_path = f"images/{filename}"
                url_mapping[img_url] = relative_path

            # 进度显示
            progress_bar = _format_progress(completed, total)
            logger.info(f"{progress_bar} [{completed}/{total}] {'✅' if success else '❌'} {filename}")

    logger.info(f"✅ 下载完成：{downloaded_count}/{total} 张图片成功")
    return url_mapping


def _format_progress(done: int, total: int, bar_width: int = 20) -> str:
    """生成进度条文本，如 ████████░░░░░░ 60%"""
    if total == 0:
        return "█" * bar_width + " 100%"
    filled = int(bar_width * done / total)
    bar = "█" * filled + "░" * (bar_width - filled)
    pct = int(100 * done / total)
    return f"|{bar}| {pct:3d}%"
