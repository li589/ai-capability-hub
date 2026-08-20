"""Poster prompt template loading and rendering engine."""

import logging
import os
from collections import defaultdict
from math import gcd

from utils import load_yaml

logger = logging.getLogger(__name__)

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Smart defaults: poster_type → recommended settings for missing fields
SMART_DEFAULTS = {
    "event": {
        "style_preset": "retro",
        "output_size": "a3_portrait",
        "layout_strategy": "three-band vertical: top 25% title, center 50% visual, bottom 25% details",
        "title_position": "upper third",
        "focal_point": "center",
        "visual_elements": "dramatic event scene with atmospheric lighting",
    },
    "promotional": {
        "style_preset": "bold_modern",
        "output_size": "portrait_2x3",
        "layout_strategy": "asymmetric diagonal with product hero on one side",
        "title_position": "upper third",
        "focal_point": "center-left",
        "visual_elements": "product showcase with premium studio lighting",
    },
    "social_media": {
        "style_preset": "bold_modern",
        "output_size": "instagram_square",
        "layout_strategy": "centered with bold graphics",
        "title_position": "center",
        "focal_point": "center",
        "visual_elements": "bold graphic elements with strong visual impact",
    },
    "movie": {
        "style_preset": "cyberpunk",
        "output_size": "movie_poster",
        "layout_strategy": "centered vertical with character dominant",
        "title_position": "lower third",
        "focal_point": "center",
        "visual_elements": "cinematic character portrait with dramatic lighting",
    },
    "educational": {
        "style_preset": "minimalist",
        "output_size": "a3_portrait",
        "layout_strategy": "grid sections with color-coded areas",
        "title_position": "top",
        "focal_point": "center",
        "visual_elements": "clean diagrams and simple flat illustrations",
    },
    "motivational": {
        "style_preset": "watercolor",
        "output_size": "portrait_2x3",
        "layout_strategy": "centered vertical with atmospheric backdrop",
        "title_position": "center",
        "focal_point": "center",
        "visual_elements": "powerful atmospheric landscape or nature scene",
    },
    "generic": {
        "style_preset": "minimalist",
        "output_size": "portrait_2x3",
        "layout_strategy": "centered vertical",
        "title_position": "upper third",
        "focal_point": "center",
        "visual_elements": "abstract artistic background",
    },
}

VALID_POSTER_TYPES = set(SMART_DEFAULTS.keys())


def apply_smart_defaults(poster_spec: dict) -> dict:
    """Fill missing fields using smart defaults based on poster_type."""
    poster_type = poster_spec.get("poster_type", "generic")
    defaults = SMART_DEFAULTS.get(poster_type, SMART_DEFAULTS["generic"])

    for key, default_value in defaults.items():
        if not poster_spec.get(key):
            poster_spec[key] = default_value
            logger.info("Smart default: %s = %s (from %s type)", key, default_value, poster_type)

    return poster_spec


def validate_poster_spec(spec: dict) -> list[str]:
    """Validate poster spec required fields. Returns list of issues."""
    issues = []

    if not spec.get("title"):
        issues.append("ERROR: Missing required field 'title'")

    poster_type = spec.get("poster_type", "")
    if not poster_type:
        issues.append("ERROR: Missing required field 'poster_type'")
    elif poster_type not in VALID_POSTER_TYPES:
        issues.append(f"WARNING: Unknown poster_type '{poster_type}', will use generic. Valid: {VALID_POSTER_TYPES}")

    if not spec.get("visual_elements"):
        issues.append("WARNING: No visual_elements specified — will use generic background")

    if not spec.get("text_elements"):
        issues.append("WARNING: No text_elements specified — poster will have minimal text")

    return issues


def load_poster_templates(prompts_dir: str | None = None) -> dict:
    """Load poster templates YAML (templates + variation_instructions + text_rendering_rules)."""
    if prompts_dir is None:
        prompts_dir = os.path.join(SKILL_DIR, "prompts")
    path = os.path.join(prompts_dir, "poster_templates.yaml")
    data = load_yaml(path)
    logger.info("Loaded %d poster templates", len(data.get("templates", [])))
    return data


def load_style_preset(style_name: str, prompts_dir: str | None = None) -> dict | None:
    """Load a specific style preset by name."""
    if prompts_dir is None:
        prompts_dir = os.path.join(SKILL_DIR, "prompts")
    path = os.path.join(prompts_dir, "style_presets.yaml")
    data = load_yaml(path)
    presets = data.get("presets", {})
    preset = presets.get(style_name)
    if preset:
        logger.info("Loaded style preset: %s", style_name)
    else:
        logger.warning("Style preset '%s' not found", style_name)
    return preset


def load_all_style_presets(prompts_dir: str | None = None) -> dict:
    """Load all style presets."""
    if prompts_dir is None:
        prompts_dir = os.path.join(SKILL_DIR, "prompts")
    path = os.path.join(prompts_dir, "style_presets.yaml")
    data = load_yaml(path)
    return data.get("presets", {})


def load_type_overrides(poster_type: str, prompts_dir: str | None = None) -> dict | None:
    """Load type-specific prompt overrides if available."""
    if prompts_dir is None:
        prompts_dir = os.path.join(SKILL_DIR, "prompts")
    override_path = os.path.join(prompts_dir, "type_overrides", f"{poster_type}.yaml")
    if not os.path.exists(override_path):
        logger.debug("No type override found for '%s'", poster_type)
        return None
    data = load_yaml(override_path)
    logger.info("Loaded type overrides for '%s'", poster_type)
    return data.get("overrides", {})


def load_size_config(size_name: str, config_dir: str | None = None) -> dict:
    """Load output size configuration by preset name or parse WxH."""
    if config_dir is None:
        config_dir = os.path.join(SKILL_DIR, "config")
    path = os.path.join(config_dir, "poster_sizes.yaml")
    data = load_yaml(path)

    sizes = data.get("sizes", {})
    default_name = data.get("default", "portrait_2x3")
    format_settings = data.get("format_settings", {})

    # Check if it's a custom WxH format
    if "x" in size_name.lower() and size_name not in sizes:
        try:
            w, h = size_name.lower().split("x")
            w_int, h_int = int(w), int(h)
            divisor = gcd(w_int, h_int)
            simplified_ratio = f"{w_int // divisor}:{h_int // divisor}"
            return {
                "name": f"Custom ({size_name})",
                "width": w_int,
                "height": h_int,
                "aspect_ratio": simplified_ratio,
                "category": "general",
                "format_settings": format_settings.get("general", {}),
            }
        except ValueError:
            logger.warning("Invalid custom size '%s', using default", size_name)

    # Look up preset
    size_key = size_name if size_name in sizes else default_name
    size_cfg = sizes[size_key].copy()
    category = size_cfg.get("category", "general")
    size_cfg["format_settings"] = format_settings.get(category, {})
    return size_cfg


def format_text_elements(text_elements: list[dict] | str) -> str:
    """Format text_elements list into a readable string for prompt injection."""
    if isinstance(text_elements, str):
        return text_elements
    if not text_elements:
        return "(none)"
    lines = []
    for elem in text_elements:
        if isinstance(elem, dict):
            role = elem.get("role", "text")
            text = elem.get("text", "")
            lines.append(f'  - {role.upper()}: "{text}"')
        else:
            lines.append(f"  - {elem}")
    return "\n".join(lines)


def build_chinese_instruction(language: str) -> str:
    """Generate Chinese text rendering instructions based on language setting."""
    if language not in ("zh", "bilingual"):
        return ""

    base = """
      CHINESE TEXT REQUIREMENTS (CRITICAL):
      - Render each Chinese character with clean, complete strokes. No broken, merged,
        or incorrect characters. Every stroke must be distinct.
      - Use BOLD, thick-stroke fonts (黑体 / Heiti style) for titles — they render most reliably.
        Avoid thin strokes (宋体) or brush calligraphy for small text — they break at lower resolutions.
      - Character spacing: Use wider-than-default spacing between Chinese characters (tracking +5-10%).
        Chinese characters are denser than Latin letters and need more breathing room.
      - Line height for Chinese text: 1.6-1.8x the font size (taller than English 1.4x).
      - Minimum character size: Chinese text must be at least 4% of poster height.
        Characters below this size will have broken strokes."""

    if language == "bilingual":
        base += """
      - BILINGUAL LAYOUT: Chinese text is PRIMARY (larger, more prominent).
        English text is secondary, placed below the Chinese at 60-70% of the Chinese font size.
      - Do NOT mix Chinese and English on the same line. Separate them into distinct text blocks.
      - Use a sans-serif font for English that pairs well with the Chinese heiti style."""

    return base


def validate_text_content(poster_spec: dict) -> list[str]:
    """Validate text content for common issues. Returns list of warnings."""
    warnings = []
    title = poster_spec.get("title", "")
    language = poster_spec.get("language", "en")

    if len(title) > 30:
        warnings.append(f"Title is {len(title)} chars — consider shortening to under 30 for reliable rendering.")

    text_elements = poster_spec.get("text_elements", [])
    if isinstance(text_elements, list):
        total_text_items = len(text_elements)
        if total_text_items > 8:
            warnings.append(f"Too many text elements ({total_text_items}). Gemini works best with 5-6 max.")

        for elem in text_elements:
            if isinstance(elem, dict):
                text = elem.get("text", "")
                if len(text) > 50:
                    warnings.append(f"Text element '{text[:20]}...' is {len(text)} chars — may be truncated.")

    if language == "bilingual":
        warnings.append("Bilingual posters have higher text rendering failure rate (~20-30%). Consider generating Chinese-only and English-only versions separately.")

    return warnings


def get_variation_instructions(poster_type: str, template_data: dict, color_info: dict) -> list[str]:
    """Get type-aware variation instructions."""
    variations_config = template_data.get("variation_instructions", {})

    # Try type-specific variations first
    type_variations = variations_config.get(poster_type, [])
    default_variations = variations_config.get("default", [])

    if type_variations:
        # Use type-specific variations, format with color info
        result = []
        for v in type_variations:
            try:
                result.append(v.format_map(defaultdict(lambda: "", color_info)))
            except (KeyError, ValueError):
                result.append(v)
        return result

    # Fall back to default variations
    result = []
    for v in default_variations:
        try:
            result.append(v.format_map(defaultdict(lambda: "", color_info)))
        except (KeyError, ValueError):
            result.append(v)
    return result


def _build_style_modifiers(preset: dict) -> str:
    """Combine style_modifiers and negative_constraints into a single string."""
    parts = []
    modifiers = preset.get("style_modifiers", "").strip()
    if modifiers:
        parts.append(modifiers)
    constraints = preset.get("negative_constraints", "").strip()
    if constraints:
        parts.append(constraints)
    return "\n".join(parts)


def build_poster_prompt(poster_spec: dict, prompts_dir: str | None = None,
                        config_dir: str | None = None) -> list[dict]:
    """Build rendered prompt(s) for a poster specification.

    Args:
        poster_spec: Dict with poster specification fields.
        prompts_dir: Override prompts directory.
        config_dir: Override config directory.

    Returns:
        List of dicts, one per variant, each with keys:
            - variant: int (1-based variant number)
            - filename: str (output filename stem)
            - prompt: str (rendered prompt text)
            - poster_type: str
            - requires_reference_image: bool
            - warnings: list[str] (text validation warnings)
    """
    # Apply smart defaults for missing fields
    poster_spec = apply_smart_defaults(poster_spec)

    # Validate spec
    spec_issues = validate_poster_spec(poster_spec)
    for issue in spec_issues:
        if issue.startswith("ERROR"):
            logger.error(issue)
        else:
            logger.warning(issue)

    template_data = load_poster_templates(prompts_dir)
    templates = template_data.get("templates", [])
    text_rendering_rules = template_data.get("text_rendering_rules", "")
    poster_type = poster_spec.get("poster_type", "generic")

    # Validate text content
    warnings = validate_text_content(poster_spec)
    warnings.extend([i for i in spec_issues if i.startswith("WARNING")])

    # Find the matching template
    template = None
    for t in templates:
        if t["type"] == poster_type:
            template = t
            break
    if template is None:
        for t in templates:
            if t["type"] == "generic":
                template = t
                break
    if template is None:
        raise ValueError(f"No template found for poster type '{poster_type}'")

    # Load style preset
    style_name = poster_spec.get("style_preset", "minimalist")
    preset = load_style_preset(style_name, prompts_dir)
    if preset is None:
        preset = load_style_preset("minimalist", prompts_dir) or {}

    # Load size config
    size_name = poster_spec.get("output_size", "portrait_2x3")
    size_cfg = load_size_config(size_name, config_dir)

    # Resolve color palette
    color_palette = poster_spec.get("color_palette", [])
    if not color_palette or color_palette == "auto":
        suggested = preset.get("suggested_palettes", [])
        color_palette = suggested[0] if suggested else ["#212121", "#FFFFFF", "#E53935"]

    # Build the template variables
    language = poster_spec.get("language", "en")
    text_elements = poster_spec.get("text_elements", [])

    primary_color = color_palette[0] if len(color_palette) > 0 else "#212121"
    secondary_color = color_palette[1] if len(color_palette) > 1 else "#FFFFFF"
    accent_color = color_palette[2] if len(color_palette) > 2 else "#E53935"

    info = defaultdict(lambda: "", {
        "title": poster_spec.get("title", ""),
        "subtitle": poster_spec.get("subtitle", ""),
        "cta": poster_spec.get("cta", poster_spec.get("key_message", "")),
        "visual_elements": poster_spec.get("visual_elements", "abstract artistic background"),
        "text_elements_formatted": format_text_elements(text_elements),
        "title_position": poster_spec.get("title_position", "upper third"),
        "layout_strategy": poster_spec.get("layout_strategy", "centered vertical"),
        "focal_point": poster_spec.get("focal_point", "center"),
        "aspect_ratio": size_cfg.get("aspect_ratio", "2:3"),
        "output_width": str(size_cfg.get("width", 2000)),
        "output_height": str(size_cfg.get("height", 3000)),
        "language": language,
        "chinese_text_instruction": build_chinese_instruction(language),
        "text_rendering_rules": text_rendering_rules,
        "primary_color": primary_color,
        "secondary_color": secondary_color,
        "accent_color": accent_color,
        "style_description": preset.get("style_description", "professional, polished design"),
        "style_modifiers": _build_style_modifiers(preset),
        "title_font_style": preset.get("title_font_style", "bold sans-serif"),
        "body_font_style": preset.get("body_font_style", "regular sans-serif"),
    })

    # Render the base prompt
    base_prompt = template["prompt"].format_map(info)

    # Apply type overrides
    overrides = load_type_overrides(poster_type, prompts_dir)
    if overrides:
        template_id = template["id"]
        override = overrides.get(template_id, {})
        append_text = override.get("prompt_append", "")
        if append_text:
            base_prompt = base_prompt.rstrip() + "\n\n" + append_text.format_map(info)

    base_prompt = base_prompt.strip()

    # Generate variants with type-aware variation instructions
    num_variants = max(1, min(4, poster_spec.get("variants", 1)))
    color_info = {
        "primary_color": primary_color,
        "secondary_color": secondary_color,
        "accent_color": accent_color,
    }
    variation_list = get_variation_instructions(poster_type, template_data, color_info)

    results = []
    for i in range(num_variants):
        prompt = base_prompt
        suffix = f"_v{i + 1}" if num_variants > 1 else ""

        # Append variation instruction for variants 2+
        if i > 0 and i - 1 < len(variation_list):
            prompt = prompt + "\n\n" + variation_list[i - 1]
        elif i > 0:
            prompt = prompt + f"\n\nVARIATION {i + 1}: Create a distinctly different composition and color arrangement."

        results.append({
            "variant": i + 1,
            "filename": f"{template['filename']}{suffix}",
            "prompt": prompt,
            "poster_type": poster_type,
            "requires_reference_image": template.get("requires_reference_image", False),
            "warnings": warnings if i == 0 else [],  # Only attach warnings to first variant
        })

    logger.info("Built %d prompt(s) for poster '%s' (type=%s, style=%s)",
                len(results), poster_spec.get("title", "?"), poster_type, style_name)
    return results
