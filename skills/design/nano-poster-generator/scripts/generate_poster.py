#!/usr/bin/env python3
"""Poster Generator - CLI entry point.

Generates high-quality posters using AI (NANO-BANANA / Gemini).

Usage:
    # From JSON poster specification:
    python scripts/generate_poster.py --from-json poster_spec.json

    # From command-line arguments:
    python scripts/generate_poster.py \\
        --title "Summer Jazz Festival 2026" \\
        --poster-type event \\
        --style retro \\
        --size a3_portrait

    # Dry run (print prompts without calling API):
    python scripts/generate_poster.py --from-json poster_spec.json --dry-run

    # Generate multiple variants:
    python scripts/generate_poster.py --from-json poster_spec.json --variants 3 -v
"""

import argparse
import json
import logging
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# All imports are local — no cross-skill dependencies
SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_DIR = os.path.join(SKILL_DIR, "scripts")

sys.path.insert(0, SCRIPTS_DIR)

from api_client import NanoBananaClient
from poster_prompt_engine import build_poster_prompt, load_size_config
from poster_postprocess import postprocess_poster
from utils import setup_logging, slugify, load_yaml, resolve_env_vars

logger = logging.getLogger(__name__)

MAX_RETRIES = 2  # Retry failed generations up to 2 times


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate high-quality posters using AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    # Input source
    input_group = parser.add_argument_group("Input")
    input_group.add_argument("--from-json", type=str, help="Path to JSON file with poster spec")
    input_group.add_argument("--title", type=str, help="Poster title / headline")
    input_group.add_argument("--subtitle", type=str, default="", help="Subtitle or tagline")
    input_group.add_argument("--poster-type", type=str, default="generic",
                             choices=["event", "promotional", "social_media", "movie",
                                      "educational", "motivational", "generic"],
                             help="Poster type")
    input_group.add_argument("--style", type=str, default="minimalist",
                             help="Style preset name")
    input_group.add_argument("--size", type=str, default="portrait_2x3",
                             help="Output size preset name or WxH (e.g., 1080x1920)")
    input_group.add_argument("--language", type=str, default="en",
                             choices=["en", "zh", "bilingual"], help="Text language")
    input_group.add_argument("--visual-elements", type=str, default="",
                             help="Description of visual elements")
    input_group.add_argument("--cta", type=str, default="", help="Call to action text")
    input_group.add_argument("--reference-image", type=str, default="",
                             help="Reference image path or URL")
    input_group.add_argument("--colors", type=str, default="",
                             help="Comma-separated hex colors (e.g., '#E53935,#FFFFFF,#212121')")

    # Output
    output_group = parser.add_argument_group("Output")
    output_group.add_argument("--output-dir", type=str,
                              help="Output directory (default: output/<slug>)")

    # Control
    control_group = parser.add_argument_group("Control")
    control_group.add_argument("--variants", type=int, default=1,
                               help="Number of variants to generate (1-4, default 1)")
    control_group.add_argument("--dry-run", action="store_true",
                               help="Print rendered prompts without calling the API")
    control_group.add_argument("--skip-postprocess", action="store_true",
                               help="Skip post-processing (keep raw images)")
    control_group.add_argument("--no-retry", action="store_true",
                               help="Disable automatic retry on failure")
    control_group.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")

    return parser.parse_args()


def build_poster_spec(args: argparse.Namespace) -> dict:
    """Build poster specification dict from CLI args or JSON file."""
    if args.from_json:
        with open(args.from_json, "r", encoding="utf-8") as f:
            spec = json.load(f)
        logger.info("Loaded poster spec from %s", args.from_json)
        return spec

    if not args.title:
        print("Error: --title is required when not using --from-json", file=sys.stderr)
        sys.exit(1)

    spec = {
        "title": args.title,
        "subtitle": args.subtitle,
        "poster_type": args.poster_type,
        "style_preset": args.style,
        "output_size": args.size,
        "language": args.language,
        "visual_elements": args.visual_elements,
        "cta": args.cta,
        "reference_image_url": args.reference_image,
        "variants": args.variants,
    }

    if args.colors:
        spec["color_palette"] = [c.strip() for c in args.colors.split(",")]

    return spec


def generate_single_poster(client: NanoBananaClient, prompt_info: dict,
                           reference_image_url: str | None, output_dir: str,
                           max_retries: int = MAX_RETRIES) -> dict:
    """Generate a single poster image with retry logic."""
    variant = prompt_info["variant"]
    prompt = prompt_info["prompt"]
    filename = prompt_info["filename"]

    ref_url = reference_image_url or None

    for attempt in range(1, max_retries + 2):  # +2 because range is exclusive and attempt 1 is the first try
        if attempt > 1:
            logger.info("Variant %d: Retry %d/%d...", variant, attempt - 1, max_retries)
            time.sleep(3)  # Brief pause before retry

        try:
            logger.info("Variant %d: Submitting (attempt %d)...", variant, attempt)
            result = client.submit_and_wait(prompt, ref_url)

            if result.status != "FINISHED" or not result.image_url:
                error_msg = f"Generation failed (status: {result.status})"
                logger.warning("Variant %d: %s", variant, error_msg)
                if attempt <= max_retries:
                    continue  # Retry
                return {"variant": variant, "filename": filename, "success": False,
                        "error": error_msg, "attempts": attempt}

            # Success — download raw image
            raw_path = os.path.join(output_dir, f"{filename}.png")
            client.download_image(result.image_url, raw_path)

            return {"variant": variant, "filename": filename, "success": True,
                    "raw_path": raw_path, "attempts": attempt}

        except Exception as e:
            error_msg = str(e)
            logger.warning("Variant %d: Error on attempt %d - %s", variant, attempt, error_msg)
            if attempt <= max_retries:
                continue  # Retry
            return {"variant": variant, "filename": filename, "success": False,
                    "error": error_msg, "attempts": attempt}

    # Should not reach here, but safety fallback
    return {"variant": variant, "filename": filename, "success": False,
            "error": "Exhausted retries", "attempts": max_retries + 1}


def main():
    args = parse_args()
    setup_logging(args.verbose)

    # Build poster spec
    poster_spec = build_poster_spec(args)
    poster_spec["variants"] = max(1, min(4, poster_spec.get("variants", args.variants)))
    title = poster_spec.get("title", "poster")
    reference_image_url = poster_spec.get("reference_image_url", "")

    # Determine output directory
    visual_root = os.path.dirname(os.path.dirname(SKILL_DIR))
    if args.output_dir:
        output_dir = args.output_dir
    else:
        output_dir = os.path.join(visual_root, "output", "posters", slugify(title))

    # Build prompts
    prompts_dir = os.path.join(SKILL_DIR, "prompts")
    config_dir = os.path.join(SKILL_DIR, "config")
    all_prompts = build_poster_prompt(poster_spec, prompts_dir, config_dir)

    # Print text validation warnings
    for p in all_prompts:
        for warning in p.get("warnings", []):
            print(f"  WARNING: {warning}")

    # Dry run mode
    if args.dry_run:
        print(f"\n{'=' * 60}")
        print(f"DRY RUN - Poster: {title}")
        print(f"Type: {poster_spec.get('poster_type', 'generic')}")
        print(f"Style: {poster_spec.get('style_preset', 'minimalist')}")
        print(f"Size: {poster_spec.get('output_size', 'portrait_2x3')}")
        print(f"Language: {poster_spec.get('language', 'en')}")
        print(f"Variants: {len(all_prompts)}")
        print(f"{'=' * 60}\n")
        for p in all_prompts:
            print(f"--- Variant {p['variant']}: {p['filename']} ---")
            print(f"\nPrompt:\n{p['prompt']}")
            print(f"\n{'=' * 60}\n")
        print(f"Total: {len(all_prompts)} poster(s) would be generated.")
        return

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    # Load API config
    api_config_path = os.path.join(SKILL_DIR, "config", "api.yaml")
    api_config = load_yaml(api_config_path)
    api_config = resolve_env_vars(api_config)
    client = NanoBananaClient(api_config)

    retry_count = 0 if args.no_retry else MAX_RETRIES

    # Generate all variants concurrently
    print(f"\nGenerating {len(all_prompts)} poster(s) for: {title}")
    print(f"Output: {output_dir}")
    if retry_count > 0:
        print(f"Auto-retry: up to {retry_count} retries per variant on failure")
    print()

    results = []
    max_workers = min(4, len(all_prompts))
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(generate_single_poster, client, p, reference_image_url,
                            output_dir, retry_count): p
            for p in all_prompts
        }
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            attempts = result.get("attempts", 1)
            retry_info = f" (after {attempts} attempts)" if attempts > 1 else ""
            status = "OK" + retry_info if result["success"] else "FAILED" + retry_info
            print(f"  Variant {result['variant']} [{result['filename']}]: {status}")

    # Post-process
    if not args.skip_postprocess:
        size_name = poster_spec.get("output_size", "portrait_2x3")
        size_cfg = load_size_config(size_name, config_dir)
        fmt_settings = size_cfg.get("format_settings", {})
        output_ext = ".jpg" if fmt_settings.get("format", "PNG").upper() == "JPEG" else ".png"

        for result in results:
            if result["success"]:
                raw_path = result["raw_path"]
                final_filename = os.path.splitext(os.path.basename(raw_path))[0] + output_ext
                final_path = os.path.join(output_dir, final_filename)
                try:
                    postprocess_poster(raw_path, final_path, size_cfg, fmt_settings)
                    result["final_path"] = final_path
                    # Clean up raw file if different from final
                    if os.path.exists(raw_path) and raw_path != final_path:
                        os.remove(raw_path)
                except Exception as e:
                    logger.error("Post-processing failed for variant %d: %s",
                                 result["variant"], str(e))
                    result["postprocess_error"] = str(e)
                    result["final_path"] = raw_path

    # Print summary
    results.sort(key=lambda r: r["variant"])
    print(f"\n{'=' * 60}")
    print("SUMMARY")
    print(f"{'=' * 60}")

    success_count = 0
    for r in results:
        if r["success"]:
            success_count += 1
            final = r.get("final_path", r.get("raw_path", ""))
            print(f"  Variant {r['variant']} [{r['filename']}]: {final}")
        else:
            print(f"  Variant {r['variant']} [{r['filename']}]: FAILED - {r.get('error', 'unknown')}")

    failed_count = len(results) - success_count
    print(f"\nResult: {success_count}/{len(results)} poster(s) generated successfully.")
    if failed_count > 0:
        print(f"\nTROUBLESHOOTING for {failed_count} failed variant(s):")
        print("  - Simplify the prompt: use shorter title, fewer text elements")
        print("  - Try a different style preset (minimalist and bold_modern are most reliable)")
        print("  - For Chinese text issues, try language='zh' instead of 'bilingual'")
        print("  - Re-run with --verbose for detailed error logs")
        print("  - Re-run specific variants by creating a new spec with variants=1")
    print(f"Output directory: {output_dir}")


if __name__ == "__main__":
    main()
