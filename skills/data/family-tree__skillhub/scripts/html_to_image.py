#!/usr/bin/env python3
"""
HTML转图片工具
使用Playwright将HTML文件截图为PNG图片
"""

import argparse
import asyncio
from playwright.async_api import async_playwright


async def html_to_image(html_file: str, output_image: str, width: int = 1400, height: int = 650):
    """
    将HTML文件转换为图片
    
    Args:
        html_file: HTML文件路径
        output_image: 输出图片路径
        width: 浏览器视口宽度（默认1400）
        height: 浏览器视口高度（默认650）
    """
    async with async_playwright() as p:
        # 启动浏览器（使用chromium）
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--disable-gpu'
            ]
        )
        
        # 创建页面
        page = await browser.new_page(
            viewport={'width': width, 'height': height}
        )
        
        # 加载HTML文件
        await page.goto(f'file://{html_file}')
        
        # 等待页面加载完成
        await page.wait_for_load_state('networkidle')
        
        # 截图
        await page.screenshot(
            path=output_image,
            full_page=True,
            type='png'
        )
        
        # 关闭浏览器
        await browser.close()
        
        print(f"成功截图: {output_image}")


def main():
    parser = argparse.ArgumentParser(description='将HTML文件转换为图片')
    parser.add_argument('--html_file', required=True, help='HTML文件路径')
    parser.add_argument('--output_image', required=True, help='输出图片路径')
    parser.add_argument('--width', type=int, default=1400, help='浏览器视口宽度（默认1400）')
    parser.add_argument('--height', type=int, default=650, help='浏览器视口高度（默认650）')
    
    args = parser.parse_args()
    
    # 运行异步任务
    asyncio.run(html_to_image(
        html_file=args.html_file,
        output_image=args.output_image,
        width=args.width,
        height=args.height
    ))


if __name__ == '__main__':
    main()
