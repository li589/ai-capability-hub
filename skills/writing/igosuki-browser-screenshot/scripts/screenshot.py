#!/usr/bin/env python3
"""
Browser Screenshot Tool

Takes screenshots of web pages using Playwright with various options for
viewport size, full page capture, and responsive testing.

Requirements:
    pip install playwright
    playwright install chromium
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Optional, List, Dict
from playwright.async_api import async_playwright, Browser, Page


# Common responsive viewport presets
VIEWPORT_PRESETS = {
    "mobile": {"width": 375, "height": 667, "name": "Mobile (iPhone SE)"},
    "mobile-large": {"width": 414, "height": 896, "name": "Mobile Large (iPhone 11)"},
    "tablet": {"width": 768, "height": 1024, "name": "Tablet (iPad)"},
    "desktop": {"width": 1920, "height": 1080, "name": "Desktop (1080p)"},
    "desktop-small": {"width": 1366, "height": 768, "name": "Desktop Small (720p)"},
}


async def take_screenshot(
    url: str,
    output_path: str,
    width: int = 1920,
    height: int = 1080,
    full_page: bool = False,
    wait_for_network_idle: bool = True,
    wait_for_selector: Optional[str] = None,
    delay: Optional[int] = None,
    element_selector: Optional[str] = None,
    browser_type: str = "chromium",
) -> None:
    """
    Take a screenshot of a web page.

    Args:
        url: The URL to screenshot
        output_path: Where to save the screenshot
        width: Viewport width in pixels
        height: Viewport height in pixels
        full_page: Whether to capture the full scrollable page
        wait_for_network_idle: Wait for network to be idle before screenshot
        wait_for_selector: CSS selector to wait for before screenshot
        delay: Additional delay in milliseconds before screenshot
        element_selector: CSS selector of specific element to screenshot
        browser_type: Browser to use (chromium, firefox, webkit)
    """
    async with async_playwright() as p:
        # Launch browser
        browser_launcher = getattr(p, browser_type)
        browser: Browser = await browser_launcher.launch()

        # Create context with specified viewport
        context = await browser.new_context(
            viewport={"width": width, "height": height}
        )

        # Create page
        page: Page = await context.new_page()

        # Navigate to URL
        print(f"Navigating to {url}...")

        # Navigate with appropriate wait condition
        if wait_for_network_idle:
            await page.goto(url, wait_until="networkidle")
        else:
            await page.goto(url, wait_until="load")

        # Wait for specific selector if provided
        if wait_for_selector:
            print(f"Waiting for selector: {wait_for_selector}")
            await page.wait_for_selector(wait_for_selector)

        # Additional delay if specified
        if delay:
            print(f"Waiting {delay}ms...")
            await page.wait_for_timeout(delay)

        # Ensure output directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        # Take screenshot
        print(f"Taking screenshot...")
        if element_selector:
            # Screenshot specific element
            element = await page.query_selector(element_selector)
            if element:
                await element.screenshot(path=output_path)
                print(f"✓ Element screenshot saved to {output_path}")
            else:
                print(f"✗ Element not found: {element_selector}", file=sys.stderr)
                sys.exit(1)
        else:
            # Screenshot entire page or viewport
            await page.screenshot(path=output_path, full_page=full_page)
            screenshot_type = "Full page" if full_page else "Viewport"
            print(f"✓ {screenshot_type} screenshot saved to {output_path}")

        # Close browser
        await browser.close()


async def take_responsive_screenshots(
    url: str,
    output_dir: str,
    viewports: List[str],
    full_page: bool = False,
    wait_for_network_idle: bool = True,
    wait_for_selector: Optional[str] = None,
    delay: Optional[int] = None,
    browser_type: str = "chromium",
) -> None:
    """
    Take screenshots across multiple viewport sizes.

    Args:
        url: The URL to screenshot
        output_dir: Directory to save screenshots
        viewports: List of viewport preset names or "WIDTHxHEIGHT" strings
        full_page: Whether to capture the full scrollable page
        wait_for_network_idle: Wait for network to be idle before screenshot
        wait_for_selector: CSS selector to wait for before screenshot
        delay: Additional delay in milliseconds before screenshot
        browser_type: Browser to use (chromium, firefox, webkit)
    """
    # Ensure output directory exists
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Parse viewports
    viewport_configs = []
    for vp in viewports:
        if vp in VIEWPORT_PRESETS:
            preset = VIEWPORT_PRESETS[vp]
            viewport_configs.append({
                "width": preset["width"],
                "height": preset["height"],
                "name": vp,
                "description": preset["name"]
            })
        elif "x" in vp.lower():
            # Parse custom viewport (e.g., "1024x768")
            try:
                width, height = map(int, vp.lower().split("x"))
                viewport_configs.append({
                    "width": width,
                    "height": height,
                    "name": f"{width}x{height}",
                    "description": f"Custom {width}x{height}"
                })
            except ValueError:
                print(f"✗ Invalid viewport format: {vp}", file=sys.stderr)
                continue
        else:
            print(f"✗ Unknown viewport preset: {vp}", file=sys.stderr)
            continue

    if not viewport_configs:
        print("✗ No valid viewports specified", file=sys.stderr)
        sys.exit(1)

    print(f"Taking screenshots across {len(viewport_configs)} viewports...")

    # Take screenshots for each viewport
    for config in viewport_configs:
        output_file = output_path / f"{config['name']}.png"
        print(f"\n{config['description']} ({config['width']}x{config['height']}):")

        await take_screenshot(
            url=url,
            output_path=str(output_file),
            width=config["width"],
            height=config["height"],
            full_page=full_page,
            wait_for_network_idle=wait_for_network_idle,
            wait_for_selector=wait_for_selector,
            delay=delay,
            element_selector=None,
            browser_type=browser_type,
        )

    print(f"\n✓ All screenshots saved to {output_dir}/")


def main():
    parser = argparse.ArgumentParser(
        description="Take screenshots of web pages using Playwright",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic screenshot
  %(prog)s https://example.com output.png

  # Full page screenshot
  %(prog)s https://example.com output.png --full-page

  # Custom viewport size
  %(prog)s https://example.com output.png --width 1024 --height 768

  # Screenshot specific element
  %(prog)s https://example.com output.png --element "#main-content"

  # Responsive screenshots (multiple viewports)
  %(prog)s https://example.com screenshots/ --responsive mobile tablet desktop

  # Wait for specific element
  %(prog)s https://example.com output.png --wait-for-selector ".loaded"

  # Custom delay
  %(prog)s https://example.com output.png --delay 2000

Available viewport presets for --responsive:
  mobile         - 375x667   (iPhone SE)
  mobile-large   - 414x896   (iPhone 11)
  tablet         - 768x1024  (iPad)
  desktop-small  - 1366x768  (720p)
  desktop        - 1920x1080 (1080p)

  Or use custom: 1024x768, 1440x900, etc.
        """
    )

    parser.add_argument("url", help="URL to screenshot")
    parser.add_argument("output", help="Output file path or directory (for --responsive)")

    # Viewport options
    viewport_group = parser.add_argument_group("viewport options")
    viewport_group.add_argument(
        "-w", "--width",
        type=int,
        default=1920,
        help="Viewport width in pixels (default: 1920)"
    )
    viewport_group.add_argument(
        "-h", "--height",
        type=int,
        default=1080,
        help="Viewport height in pixels (default: 1080)"
    )
    viewport_group.add_argument(
        "-r", "--responsive",
        nargs="+",
        metavar="VIEWPORT",
        help="Take screenshots at multiple viewports (saves to output directory)"
    )

    # Screenshot options
    screenshot_group = parser.add_argument_group("screenshot options")
    screenshot_group.add_argument(
        "-f", "--full-page",
        action="store_true",
        help="Capture full scrollable page instead of just viewport"
    )
    screenshot_group.add_argument(
        "-e", "--element",
        metavar="SELECTOR",
        help="CSS selector of specific element to screenshot"
    )

    # Wait options
    wait_group = parser.add_argument_group("wait options")
    wait_group.add_argument(
        "--no-wait-network-idle",
        action="store_true",
        help="Don't wait for network idle (faster but may miss content)"
    )
    wait_group.add_argument(
        "--wait-for-selector",
        metavar="SELECTOR",
        help="Wait for specific CSS selector before screenshot"
    )
    wait_group.add_argument(
        "-d", "--delay",
        type=int,
        metavar="MS",
        help="Additional delay in milliseconds before screenshot"
    )

    # Browser options
    parser.add_argument(
        "-b", "--browser",
        choices=["chromium", "firefox", "webkit"],
        default="chromium",
        help="Browser to use (default: chromium)"
    )

    args = parser.parse_args()

    # Handle responsive mode
    if args.responsive:
        asyncio.run(take_responsive_screenshots(
            url=args.url,
            output_dir=args.output,
            viewports=args.responsive,
            full_page=args.full_page,
            wait_for_network_idle=not args.no_wait_network_idle,
            wait_for_selector=args.wait_for_selector,
            delay=args.delay,
            browser_type=args.browser,
        ))
    else:
        asyncio.run(take_screenshot(
            url=args.url,
            output_path=args.output,
            width=args.width,
            height=args.height,
            full_page=args.full_page,
            wait_for_network_idle=not args.no_wait_network_idle,
            wait_for_selector=args.wait_for_selector,
            delay=args.delay,
            element_selector=args.element,
            browser_type=args.browser,
        ))


if __name__ == "__main__":
    main()
