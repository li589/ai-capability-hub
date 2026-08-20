"""Poster-specific post-processing for generated images."""

import logging
import os

from PIL import Image, ImageCms

logger = logging.getLogger(__name__)


def ensure_rgb(image: Image.Image) -> Image.Image:
    """Convert image to RGB mode, compositing RGBA onto white background."""
    if image.mode == "RGBA":
        bg = Image.new("RGB", image.size, (255, 255, 255))
        bg.paste(image, mask=image.split()[3])
        return bg
    if image.mode != "RGB":
        return image.convert("RGB")
    return image


def embed_srgb_profile(image: Image.Image) -> Image.Image:
    """Embed sRGB ICC profile into the image."""
    srgb_profile = ImageCms.createProfile("sRGB")
    icc_data = ImageCms.ImageCmsProfile(srgb_profile).tobytes()
    image.info["icc_profile"] = icc_data
    return image


def optimize_file_size(image: Image.Image, output_path: str,
                       max_mb: float = 10.0, initial_quality: int = 92) -> str:
    """Save image as JPEG, reducing quality if file size exceeds max_mb."""
    quality = initial_quality
    icc_profile = image.info.get("icc_profile")

    while quality >= 70:
        save_kwargs = {"quality": quality, "optimize": True}
        if icc_profile:
            save_kwargs["icc_profile"] = icc_profile
        image.save(output_path, "JPEG", **save_kwargs)

        file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
        if file_size_mb <= max_mb:
            logger.info("Saved %s (%.1f MB, quality=%d)", output_path, file_size_mb, quality)
            return output_path

        logger.debug("File size %.1f MB exceeds %.1f MB at quality %d, reducing...",
                     file_size_mb, max_mb, quality)
        quality -= 5

    logger.warning("Could not reduce %s below %.1f MB (final: %.1f MB)",
                   output_path, max_mb, os.path.getsize(output_path) / (1024 * 1024))
    return output_path


def resize_poster(image: Image.Image, target_width: int, target_height: int,
                  fit_mode: str = "fit",
                  bg_color: tuple[int, int, int] = (255, 255, 255)) -> Image.Image:
    """Resize image for poster output.

    Args:
        fit_mode: "fit" (pad), "cover" (center-crop), or "stretch".
    """
    orig_w, orig_h = image.size

    if fit_mode == "stretch":
        return image.resize((target_width, target_height), Image.LANCZOS)

    if fit_mode == "cover":
        scale = max(target_width / orig_w, target_height / orig_h)
        new_w = int(orig_w * scale)
        new_h = int(orig_h * scale)
        resized = image.resize((new_w, new_h), Image.LANCZOS)
        left = (new_w - target_width) // 2
        top = (new_h - target_height) // 2
        return resized.crop((left, top, left + target_width, top + target_height))

    # fit mode (default)
    scale = min(target_width / orig_w, target_height / orig_h)
    new_w = int(orig_w * scale)
    new_h = int(orig_h * scale)
    resized = image.resize((new_w, new_h), Image.LANCZOS)

    canvas = Image.new("RGB", (target_width, target_height), bg_color)
    offset_x = (target_width - new_w) // 2
    offset_y = (target_height - new_h) // 2
    canvas.paste(resized, (offset_x, offset_y))
    return canvas


def postprocess_poster(input_path: str, output_path: str, size_config: dict,
                       format_settings: dict | None = None) -> str:
    """Full post-processing pipeline for a poster image."""
    if format_settings is None:
        format_settings = size_config.get("format_settings", {})

    target_w = size_config.get("width", 2000)
    target_h = size_config.get("height", 3000)
    category = size_config.get("category", "general")
    output_format = format_settings.get("format", "PNG")
    embed_icc = format_settings.get("embed_icc", True)

    fit_mode = "cover" if category == "social" else "fit"

    logger.info("Post-processing poster: %s -> %s (%dx%d, %s, %s)",
                input_path, output_path, target_w, target_h, output_format, fit_mode)

    image = Image.open(input_path)
    image = ensure_rgb(image)
    image = resize_poster(image, target_w, target_h, fit_mode)

    if embed_icc:
        image = embed_srgb_profile(image)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    if output_format.upper() == "JPEG":
        jpeg_quality = format_settings.get("jpeg_quality", 92)
        max_size_mb = format_settings.get("max_file_size_mb", 10)
        if not output_path.lower().endswith((".jpg", ".jpeg")):
            output_path = os.path.splitext(output_path)[0] + ".jpg"
        optimize_file_size(image, output_path, max_size_mb, jpeg_quality)
    else:
        if not output_path.lower().endswith(".png"):
            output_path = os.path.splitext(output_path)[0] + ".png"
        save_kwargs = {"optimize": True}
        icc_profile = image.info.get("icc_profile")
        if icc_profile:
            save_kwargs["icc_profile"] = icc_profile
        image.save(output_path, "PNG", **save_kwargs)
        file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
        logger.info("Saved %s (%.1f MB)", output_path, file_size_mb)

    return output_path
