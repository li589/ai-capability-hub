"""Compose exact Chinese marketing copy over an approved raster visual."""

from __future__ import annotations

from pathlib import Path
import argparse
import json
from typing import Any

from PIL import Image, ImageDraw, ImageFont, ImageOps


FORBIDDEN = ("躺赚", "保证收益", "拉人头", "月入过万")
DEFAULT_FONTS = (
    "C:/Windows/Fonts/msyh.ttc",
    "C:/Windows/Fonts/msyhbd.ttc",
    "C:/Windows/Fonts/simhei.ttf",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
    "/System/Library/Fonts/PingFang.ttc",
)


def _font(spec: dict[str, Any], size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [spec.get("bold_font") if bold else spec.get("font")]
    if bold:
        candidates.append("C:/Windows/Fonts/msyhbd.ttc")
    candidates.extend(DEFAULT_FONTS)
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    raise FileNotFoundError("No Chinese font found")


def _wrap(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont,
    max_width: int,
) -> list[str]:
    lines: list[str] = []
    current = ""
    for char in text:
        trial = current + char
        if current and draw.textbbox((0, 0), trial, font=font)[2] > max_width:
            lines.append(current)
            current = char
        else:
            current = trial
    if current:
        lines.append(current)
    return lines or [""]


def _paste_contained(canvas: Image.Image, source: Path, box: tuple[int, int, int, int]) -> None:
    image = Image.open(source).convert("RGBA")
    width, height = box[2] - box[0], box[3] - box[1]
    image.thumbnail((width, height), Image.Resampling.LANCZOS)
    x = box[0] + (width - image.width) // 2
    y = box[1] + (height - image.height) // 2
    canvas.alpha_composite(image, (x, y))


def compose(spec: dict[str, Any], output: str | Path) -> str:
    required = ("size", "background", "title", "bullets", "footer")
    missing = [key for key in required if key not in spec]
    if missing:
        raise ValueError(f"missing poster fields: {', '.join(missing)}")
    all_text = " ".join(
        [
            str(spec.get("title", "")),
            str(spec.get("subtitle", "")),
            *[str(item) for item in spec.get("bullets", [])],
            str(spec.get("footer", "")),
        ]
    )
    hit = next((word for word in FORBIDDEN if word in all_text), None)
    if hit:
        raise ValueError(f"forbidden marketing claim: {hit}")
    if "不承诺收益" not in str(spec["footer"]):
        raise ValueError("footer must contain 不承诺收益")

    size = tuple(int(value) for value in spec["size"])
    if len(size) != 2 or min(size) < 640:
        raise ValueError("size must contain two dimensions of at least 640 pixels")
    width, height = size
    background = Path(spec["background"])
    if not background.exists():
        raise FileNotFoundError(background)
    canvas = ImageOps.fit(
        Image.open(background).convert("RGB"),
        size,
        method=Image.Resampling.LANCZOS,
    ).convert("RGBA")
    scale = width / 1080
    margin = round(54 * scale)
    inset = round(42 * scale)
    panel = (margin, margin, width - margin, height - margin)
    overlay = Image.new("RGBA", size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    overlay_draw.rounded_rectangle(
        panel,
        radius=round(28 * scale),
        fill=tuple(spec.get("panel_rgba", [255, 255, 255, 226])),
    )
    canvas = Image.alpha_composite(canvas, overlay)
    draw = ImageDraw.Draw(canvas)
    title_font = _font(spec, round(64 * scale), bold=True)
    subtitle_font = _font(spec, round(34 * scale))
    body_font = _font(spec, round(36 * scale))
    footer_font = _font(spec, round(23 * scale))
    colors = {
        "title": spec.get("title_color", "#00215E"),
        "body": spec.get("body_color", "#1F2937"),
        "muted": spec.get("muted_color", "#4B5563"),
        "accent": spec.get("accent_color", "#0047AB"),
    }

    x = panel[0] + inset
    y = panel[1] + inset
    max_width = panel[2] - panel[0] - 2 * inset
    boxes: list[dict[str, Any]] = []

    logo = spec.get("logo")
    if logo:
        logo_path = Path(logo)
        if not logo_path.exists():
            raise FileNotFoundError(logo_path)
        logo_box = (x, y, x + round(360 * scale), y + round(120 * scale))
        _paste_contained(canvas, logo_path, logo_box)
        boxes.append({"kind": "logo", "box": logo_box})
        y = logo_box[3] + round(30 * scale)

    for line in _wrap(draw, str(spec["title"]), title_font, max_width):
        box = draw.textbbox((x, y), line, font=title_font)
        draw.text((x, y), line, font=title_font, fill=colors["title"])
        boxes.append({"kind": "title", "text": line, "box": box})
        y = box[3] + round(18 * scale)

    subtitle = str(spec.get("subtitle", "")).strip()
    if subtitle:
        y += round(12 * scale)
        for line in _wrap(draw, subtitle, subtitle_font, max_width):
            box = draw.textbbox((x, y), line, font=subtitle_font)
            draw.text((x, y), line, font=subtitle_font, fill=colors["muted"])
            boxes.append({"kind": "subtitle", "text": line, "box": box})
            y = box[3] + round(12 * scale)

    y += round(42 * scale)
    for bullet in spec.get("bullets", []):
        lines = _wrap(draw, str(bullet), body_font, max_width - round(48 * scale))
        for index, line in enumerate(lines):
            text = ("• " if index == 0 else "  ") + line
            box = draw.textbbox((x, y), text, font=body_font)
            draw.text((x, y), text, font=body_font, fill=colors["body"])
            boxes.append({"kind": "bullet", "text": text, "box": box})
            y = box[3] + round(12 * scale)
        y += round(10 * scale)

    qr_size = round(200 * scale)
    qr_box = (
        panel[2] - inset - qr_size,
        panel[3] - inset - qr_size - round(70 * scale),
        panel[2] - inset,
        panel[3] - inset - round(70 * scale),
    )
    qr = spec.get("qr")
    if qr == "placeholder":
        draw.rectangle(qr_box, outline=colors["accent"], width=max(2, round(4 * scale)))
        label = "二维码位"
        label_box = draw.textbbox((0, 0), label, font=footer_font)
        draw.text(
            (
                qr_box[0] + (qr_size - (label_box[2] - label_box[0])) // 2,
                qr_box[1] + (qr_size - (label_box[3] - label_box[1])) // 2,
            ),
            label,
            font=footer_font,
            fill=colors["accent"],
        )
    elif qr:
        qr_path = Path(qr)
        if not qr_path.exists():
            raise FileNotFoundError(qr_path)
        _paste_contained(canvas, qr_path, qr_box)
    if qr:
        boxes.append({"kind": "qr", "box": qr_box})

    footer_y = panel[3] - inset - round(42 * scale)
    footer_width = max_width - (qr_size + round(36 * scale) if qr else 0)
    footer_lines = _wrap(draw, str(spec["footer"]), footer_font, footer_width)
    footer_y -= sum(
        draw.textbbox((0, 0), line, font=footer_font)[3] + round(7 * scale)
        for line in footer_lines
    )
    for line in footer_lines:
        box = draw.textbbox((x, footer_y), line, font=footer_font)
        draw.text((x, footer_y), line, font=footer_font, fill=colors["muted"])
        boxes.append({"kind": "footer", "text": line, "box": box})
        footer_y = box[3] + round(7 * scale)

    if y >= min(qr_box[1] if qr else panel[3], footer_y):
        raise ValueError("content overlaps footer or QR area")
    if any(
        box["box"][0] < 0
        or box["box"][1] < 0
        or box["box"][2] > width
        or box["box"][3] > height
        for box in boxes
    ):
        raise ValueError("text or image box exceeds canvas")

    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(output_path, quality=95)
    manifest = output_path.with_suffix(".layout.json")
    manifest.write_text(
        json.dumps(
            {"title": spec["title"], "size": list(size), "boxes": boxes},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return str(manifest)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec", type=Path, help="UTF-8 JSON poster specification")
    parser.add_argument("output", type=Path, help="Output PNG path")
    args = parser.parse_args()
    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    print(compose(spec, args.output))


if __name__ == "__main__":
    main()
