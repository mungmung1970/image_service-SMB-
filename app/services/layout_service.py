# ad_creator_platform/app/services/layout_service.py
"""
Layout Service

역할:
- LLM이 만든 '레이아웃 의도(JSON)'를
  실제 픽셀 좌표 / 폰트 크기 / 정렬 정보로 변환한다.
- 플랫폼별(인스타/포스터/배너) 안전 영역을 관리한다.

철학:
- AI는 '의도'만 표현
- 시스템은 '결정'을 담당
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple, Literal


Position = Literal[
    "upper_center",
    "upper_left",
    "upper_right",
    "center",
    "lower_center",
    "lower_left",
    "lower_right",
]

FontSize = Literal["sm", "md", "lg", "xl"]


# -----------------------------
# Data Model
# -----------------------------
@dataclass
class ResolvedTextLayout:
    x: int
    y: int
    font_px: int
    anchor: str  # PIL anchor: "mm", "la", "ra"
    color: Tuple[int, int, int, int]
    emphasis: Dict | None = None


# -----------------------------
# Public API
# -----------------------------
def resolve_text_layout(
    *,
    canvas_size: Tuple[int, int],
    position: Position,
    font_size: FontSize,
    color_hex: str,
    emphasis: Dict | None = None,
    platform: Literal["instagram", "poster", "banner"] = "instagram",
) -> ResolvedTextLayout:
    """
    텍스트 블록 레이아웃을 픽셀 기준으로 해석한다.

    Args:
        canvas_size: (width, height)
        position: 레이아웃 위치
        font_size: sm/md/lg/xl
        color_hex: "#RRGGBB"
        emphasis: 강조 정보(dict)
        platform: 출력 플랫폼

    Returns:
        ResolvedTextLayout
    """
    w, h = canvas_size

    safe_top, safe_bottom = _safe_vertical_margins(platform, h)
    font_px = _resolve_font_px(font_size, platform)

    # 기본 좌표
    x, y, anchor = _resolve_position_xy(
        position=position,
        w=w,
        h=h,
        safe_top=safe_top,
        safe_bottom=safe_bottom,
    )

    return ResolvedTextLayout(
        x=x,
        y=y,
        font_px=font_px,
        anchor=anchor,
        color=_hex_to_rgba(color_hex),
        emphasis=emphasis,
    )


# -----------------------------
# Helpers
# -----------------------------
def _safe_vertical_margins(platform: str, h: int) -> Tuple[int, int]:
    """
    플랫폼별 안전 영역 (텍스트 잘림 방지)
    """
    if platform == "instagram":
        return int(h * 0.10), int(h * 0.10)
    if platform == "poster":
        return int(h * 0.08), int(h * 0.08)
    if platform == "banner":
        return int(h * 0.15), int(h * 0.15)
    return int(h * 0.1), int(h * 0.1)


def _resolve_font_px(font_size: FontSize, platform: str) -> int:
    """
    추상 font_size → 실제 픽셀
    """
    base = {
        "instagram": {"sm": 36, "md": 52, "lg": 72, "xl": 96},
        "poster": {"sm": 48, "md": 72, "lg": 96, "xl": 140},
        "banner": {"sm": 32, "md": 48, "lg": 64, "xl": 88},
    }
    return base.get(platform, base["instagram"])[font_size]


def _resolve_position_xy(
    *,
    position: Position,
    w: int,
    h: int,
    safe_top: int,
    safe_bottom: int,
) -> Tuple[int, int, str]:
    """
    position → (x, y, anchor)
    """
    if position == "upper_center":
        return w // 2, safe_top, "ma"
    if position == "upper_left":
        return int(w * 0.08), safe_top, "la"
    if position == "upper_right":
        return int(w * 0.92), safe_top, "ra"

    if position == "center":
        return w // 2, h // 2, "mm"

    if position == "lower_center":
        return w // 2, h - safe_bottom, "md"
    if position == "lower_left":
        return int(w * 0.08), h - safe_bottom, "ld"
    if position == "lower_right":
        return int(w * 0.92), h - safe_bottom, "rd"

    # fallback
    return w // 2, h // 2, "mm"


def _hex_to_rgba(hex_color: str, alpha: int = 255) -> Tuple[int, int, int, int]:
    """
    "#RRGGBB" → (R,G,B,A)
    """
    hex_color = hex_color.lstrip("#")
    if len(hex_color) != 6:
        return (255, 255, 255, alpha)
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    return (r, g, b, alpha)
