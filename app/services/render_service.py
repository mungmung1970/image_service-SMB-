# ad_creator_platform/app/services/render_service.py
"""
Render Service

역할:
- 배경 / 메인 이미지 / 문구 레이어를 합성
- 한글 지원 폰트 명시적 사용
- 상대 경로 → 절대 경로 변환 책임 보유
"""

from __future__ import annotations

from typing import Dict, Tuple
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from app.storage.local_fs import resolve_image_path


# -----------------------------
# Font Config (⭐ 핵심)
# -----------------------------
FONT_DIR = Path("assets/fonts")
FONT_REGULAR = FONT_DIR / "NotoSansKR-Medium.ttf"
FONT_BOLD = FONT_DIR / "NotoSansKR-VF.ttf"


def _load_font(*, bold: bool, size: int) -> ImageFont.FreeTypeFont:
    """
    한글 지원 폰트 로드 (실패 시 즉시 에러)
    """
    font_path = FONT_BOLD if bold else FONT_REGULAR

    if not font_path.exists():
        raise FileNotFoundError(f"폰트 파일을 찾을 수 없습니다: {font_path}")

    return ImageFont.truetype(str(font_path), size=size)


# -----------------------------
# Public API
# -----------------------------
def compose_ad_image(
    *,
    background: Image.Image,
    copy: Dict[str, str],
    size: Tuple[int, int],
    main_image_path: str | None,
    user_email: str,
) -> Image.Image:
    """
    광고 이미지 최종 합성
    """
    canvas = background.convert("RGBA").resize(size)

    # -----------------------------
    # Main Image Layer
    # -----------------------------
    if main_image_path:
        canvas = _add_main_layer(
            canvas=canvas,
            main_image_path=main_image_path,
            user_email=user_email,
        )

    # -----------------------------
    # Text Layer
    # -----------------------------
    canvas = _add_text_layer(
        canvas=canvas,
        copy=copy,
    )

    return canvas


# -----------------------------
# Internal Helpers
# -----------------------------
def _add_main_layer(
    *,
    canvas: Image.Image,
    main_image_path: str,
    user_email: str,
) -> Image.Image:
    """
    메인 이미지 레이어 합성
    """
    abs_path = resolve_image_path(
        email=user_email,
        relative_path=main_image_path,
    )

    main = Image.open(abs_path).convert("RGBA")

    canvas_w, canvas_h = canvas.size
    main_w, main_h = main.size

    scale = min(canvas_w / main_w, canvas_h / main_h) * 0.6
    new_size = (int(main_w * scale), int(main_h * scale))
    main = main.resize(new_size, Image.LANCZOS)

    x = (canvas_w - main.width) // 2
    y = (canvas_h - main.height) // 2

    canvas.paste(main, (x, y), main)
    return canvas


def _add_text_layer(
    *,
    canvas: Image.Image,
    copy: Dict[str, str],
) -> Image.Image:
    """
    광고 문구 레이어 합성 (한글 완전 지원)
    """
    draw = ImageDraw.Draw(canvas)
    w, h = canvas.size

    # -----------------------------
    # Fonts (⭐ 한글 OK)
    # -----------------------------
    headline_font = _load_font(bold=True, size=72)
    subcopy_font = _load_font(bold=False, size=40)
    cta_font = _load_font(bold=True, size=36)

    headline = copy.get("headline", "")
    subcopy = copy.get("subcopy", "")
    cta = copy.get("cta", "")

    margin = int(h * 0.08)
    y = h - margin

    # CTA
    if cta:
        bbox = draw.textbbox((0, 0), cta, font=cta_font)
        text_w = bbox[2] - bbox[0]
        draw.text(
            ((w - text_w) // 2, y - 40),
            cta,
            font=cta_font,
            fill=(255, 255, 255, 255),
        )
        y -= 60

    # Subcopy
    if subcopy:
        bbox = draw.textbbox((0, 0), subcopy, font=subcopy_font)
        text_w = bbox[2] - bbox[0]
        draw.text(
            ((w - text_w) // 2, y - 35),
            subcopy,
            font=subcopy_font,
            fill=(255, 255, 255, 220),
        )
        y -= 55

    # Headline
    if headline:
        bbox = draw.textbbox((0, 0), headline, font=headline_font)
        text_w = bbox[2] - bbox[0]
        draw.text(
            ((w - text_w) // 2, y - 50),
            headline,
            font=headline_font,
            fill=(255, 255, 255, 255),
        )

    return canvas
