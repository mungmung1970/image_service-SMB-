# render_service.py
#  ├─ _draw_headline()
#  ├─ _draw_subcopy()
#  ├─ _draw_cta()
#  ├─ _apply_emphasis()
#  └─ _resolve_position()

# ad_creator_platform/app/services/render_service.py
"""
Render Service (Final Composition)

역할:
- 업스케일된 이미지 위에
  광고 텍스트(Headline/Subcopy/CTA)를 최종 합성한다.
- 한글 폰트 정상 처리
- 강조 텍스트 부분 렌더링 지원

주의:
- 이 단계 이후에는 이미지 픽셀을 변경하지 않는다.
"""

from __future__ import annotations

from typing import Dict, Tuple, Optional

from PIL import Image, ImageDraw, ImageFont

from app.services.layout_service import resolve_text_layout
from app.pipeline.plan import LayoutSpec, TextBlockLayout


# -----------------------------
# Font Config (중요)
# -----------------------------
# assets/fonts/ 에 폰트 파일을 넣어주세요
FONT_REGULAR = "assets/fonts/NotoSansKR-Regular.otf"
FONT_BOLD = "assets/fonts/NotoSansKR-Bold.otf"


# -----------------------------
# Public API
# -----------------------------
def render_text_layers(
    *,
    image: Image.Image,
    copy: Dict[str, str],
    layout: LayoutSpec,
    platform: str = "instagram",
) -> Image.Image:
    """
    최종 텍스트 레이어 합성

    Args:
        image: 업스케일 완료된 이미지 (RGB/RGBA)
        copy: {"headline", "subcopy", "cta"}
        layout: LayoutSpec (from plan.py)
        platform: instagram | poster | banner

    Returns:
        PIL Image (RGBA)
    """
    canvas = image.convert("RGBA")
    draw = ImageDraw.Draw(canvas)

    # Headline
    _draw_text_block(
        draw=draw,
        canvas=canvas,
        text=copy.get("headline", ""),
        spec=layout.headline,
        platform=platform,
    )

    # Subcopy
    _draw_text_block(
        draw=draw,
        canvas=canvas,
        text=copy.get("subcopy", ""),
        spec=layout.subcopy,
        platform=platform,
    )

    # CTA
    _draw_text_block(
        draw=draw,
        canvas=canvas,
        text=copy.get("cta", ""),
        spec=layout.cta,
        platform=platform,
    )

    return canvas


# -----------------------------
# Internal Helpers
# -----------------------------
def _draw_text_block(
    *,
    draw: ImageDraw.ImageDraw,
    canvas: Image.Image,
    text: str,
    spec: TextBlockLayout,
    platform: str,
) -> None:
    """
    단일 텍스트 블록 렌더링
    """
    if not text:
        return

    resolved = resolve_text_layout(
        canvas_size=canvas.size,
        position=spec.position,
        font_size=spec.font_size,
        color_hex=spec.color_hex,
        emphasis=spec.emphasis.__dict__ if spec.emphasis else None,
        platform=platform,
    )

    font = _load_font(
        style=spec.font_style,
        size=resolved.font_px,
    )

    # 강조 텍스트가 없는 경우 → 한 번에 렌더
    if not resolved.emphasis:
        draw.text(
            (resolved.x, resolved.y),
            text,
            font=font,
            fill=resolved.color,
            anchor=resolved.anchor,
        )
        return

    # 강조 텍스트 처리
    _draw_text_with_emphasis(
        draw=draw,
        base_xy=(resolved.x, resolved.y),
        anchor=resolved.anchor,
        base_font=font,
        base_color=resolved.color,
        text=text,
        emphasis=resolved.emphasis,
    )


def _draw_text_with_emphasis(
    *,
    draw: ImageDraw.ImageDraw,
    base_xy: Tuple[int, int],
    anchor: str,
    base_font: ImageFont.FreeTypeFont,
    base_color: Tuple[int, int, int, int],
    text: str,
    emphasis: Dict,
) -> None:
    """
    문자열 중 특정 부분만 강조 렌더링
    """
    target = emphasis.get("text")
    if not target or target not in text:
        draw.text(base_xy, text, font=base_font, fill=base_color, anchor=anchor)
        return

    before, after = text.split(target, 1)

    # 강조 폰트
    scale = float(emphasis.get("scale", 1.2))
    emph_font = _load_font(
        style="bold",
        size=int(base_font.size * scale),
    )
    emph_color = _hex_to_rgba(emphasis.get("color_hex", "#FF4D4D"))

    # 기준점 보정: anchor 중앙 기준으로 왼쪽부터 직접 배치
    x, y = base_xy

    # 전체 폭 계산
    bw = base_font.getlength(before)
    tw = emph_font.getlength(target)
    aw = base_font.getlength(after)
    total_w = bw + tw + aw

    start_x = x - total_w / 2

    # before
    draw.text((start_x, y), before, font=base_font, fill=base_color, anchor="lm")
    cur_x = start_x + bw

    # target
    draw.text((cur_x, y), target, font=emph_font, fill=emph_color, anchor="lm")
    cur_x += tw

    # after
    draw.text((cur_x, y), after, font=base_font, fill=base_color, anchor="lm")


def _load_font(*, style: str, size: int) -> ImageFont.FreeTypeFont:
    """
    한글 폰트 로드
    """
    path = FONT_BOLD if style == "bold" else FONT_REGULAR
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        # 최후의 폴백 (깨질 수 있음)
        return ImageFont.load_default()


def _hex_to_rgba(hex_color: str, alpha: int = 255) -> Tuple[int, int, int, int]:
    hex_color = hex_color.lstrip("#")
    if len(hex_color) != 6:
        return (255, 255, 255, alpha)
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    return (r, g, b, alpha)
