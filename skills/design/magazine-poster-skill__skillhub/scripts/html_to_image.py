#!/usr/bin/env python3
"""Render a single-file magazine-poster HTML page to a PNG image.

Usage:
    python html_to_image.py <input.html> <output.png> [--scale 2] [--selector ".page-wrapper"] [--width 840]

Opens <input.html> in a real Chromium-based browser (prefers the system's
installed Chrome or Edge, falls back to Playwright's bundled Chromium),
waits for Google Fonts to finish loading, then screenshots the
".page-wrapper" element only (not the full viewport), so the output PNG is
cropped tightly to the poster content with no extra background margin.
"""
import argparse
import sys
from pathlib import Path


def render(input_path: Path, output_path: Path, selector: str, scale: int, width: int) -> None:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print(
            "ERROR: Playwright is not installed. Install it with:\n"
            "  pip install playwright\n"
            "  playwright install chromium\n"
            "(or skip the image step and just deliver the HTML file instead).",
            file=sys.stderr,
        )
        sys.exit(1)

    uri = input_path.resolve().as_uri()

    with sync_playwright() as p:
        browser = None
        last_err = None
        for channel in ("chrome", "msedge", None):
            try:
                browser = p.chromium.launch(channel=channel) if channel else p.chromium.launch()
                break
            except Exception as e:  # noqa: BLE001 - want to try every fallback
                last_err = e
        if browser is None:
            print(f"ERROR: could not launch any Chromium-based browser: {last_err}", file=sys.stderr)
            sys.exit(1)

        page = browser.new_page(viewport={"width": width, "height": 1000}, device_scale_factor=scale)
        page.goto(uri, wait_until="load")
        page.evaluate("document.fonts && document.fonts.ready ? document.fonts.ready : Promise.resolve()")
        page.wait_for_timeout(300)  # settle webfont swap / layout shift

        target = page.locator(selector)
        if target.count() == 0:
            print(f"ERROR: selector '{selector}' not found in {input_path}", file=sys.stderr)
            browser.close()
            sys.exit(1)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        target.first.screenshot(path=str(output_path))
        browser.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert a magazine-poster HTML file into a PNG image.")
    parser.add_argument("input", type=Path, help="path to the source .html file")
    parser.add_argument("output", type=Path, help="path to write the .png file")
    parser.add_argument("--selector", default=".page-wrapper", help="CSS selector of the element to capture (default: .page-wrapper)")
    parser.add_argument("--scale", type=int, default=2, help="device scale factor / retina multiplier (default: 2)")
    parser.add_argument("--width", type=int, default=840, help="viewport width in CSS px (default: 840, comfortably above the 760px page-wrapper)")
    args = parser.parse_args()

    if not args.input.exists():
        print(f"ERROR: input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    render(args.input, args.output, args.selector, args.scale, args.width)
    print(f"OK: wrote {args.output}")


if __name__ == "__main__":
    main()
