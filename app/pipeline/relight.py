# IC-Light
# ad_creator_platform/pipeline/relight.py
"""
Relight Stage (Lighting & Shadow Composition)

역할:
- 배경 이미지와 전경(RGBA)을 입력받아
  조명과 그림자를 자연스럽게 맞춘 합성 이미지를 생성한다.
- 실무에서는 IC-Light / Diffusion 기반 Relighting 모델을 사용한다.

현재 구현:
- (기본) 폴백:
  - 간단한 소프트 그림자 생성
  - 배경 밝기 기반 전경 톤 보정
- (확장) IC-Light 모델 연결 훅 제공

주의:
- 이 단계에서는 텍스트를 절대 추가하지 않는다.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Literal, Tuple

import numpy as np
from PIL import Image, ImageFilter, ImageEnhance


Backend = Literal["fallback"]  # 추후: "ic_light"


@dataclass
class RelightConfig:
    backend: Backend = "fallback"

    # 폴백용 파라미터
    shadow_opacity: float = 0.35  # 그림자 투명도
    shadow_blur: int = 24  # 그림자 블러 반경
    shadow_offset: Tuple[int, int] = (0, 24)  # 그림자 위치 (x,y)
    tone_match_strength: float = 0.15  # 배경 밝기 반영 강도


# -----------------------------
# Public API
# -----------------------------
def relight_and_compose(
    *,
    background: Image.Image,
    foreground_rgba: Image.Image,
    config: Optional[RelightConfig] = None,
) -> Image.Image:
    """
    배경 + 전경을 조명에 맞게 합성한다.

    Args:
        background: 배경 이미지 (RGB)
        foreground_rgba: 배경 제거된 전경 (RGBA)
        config: 조명/그림자 설정

    Returns:
        composed_image: PIL Image (RGB)
    """
    cfg = config or RelightConfig()

    if cfg.backend == "fallback":
        return _relight_fallback(
            background=background,
            fg=foreground_rgba,
            cfg=cfg,
        )

    raise NotImplementedError(f"Unsupported relight backend: {cfg.backend}")


# -----------------------------
# Fallback Implementation
# -----------------------------
def _relight_fallback(
    *,
    background: Image.Image,
    fg: Image.Image,
    cfg: RelightConfig,
) -> Image.Image:
    """
    폴백 조명 합성:
    - 배경 중앙 밝기를 기준으로 전경 밝기 약간 보정
    - 전경 아래쪽에 소프트 그림자 추가
    """
    bg = background.convert("RGB")
    fg = fg.convert("RGBA")

    bg_w, bg_h = bg.size
    fg_w, fg_h = fg.size

    # 1) 전경 크기 조정 (배경의 약 60%)
    scale = min(bg_w / fg_w, bg_h / fg_h) * 0.6
    new_size = (int(fg_w * scale), int(fg_h * scale))
    fg = fg.resize(new_size, Image.LANCZOS)

    # 2) 전경 위치 (하단 중앙 살짝 위)
    x = (bg_w - fg.width) // 2
    y = int(bg_h * 0.55 - fg.height / 2)

    # 3) 그림자 생성
    shadow = _make_shadow(
        fg=fg,
        opacity=cfg.shadow_opacity,
        blur=cfg.shadow_blur,
        offset=cfg.shadow_offset,
    )

    canvas = bg.copy()
    canvas.paste(
        shadow,
        (x + cfg.shadow_offset[0], y + cfg.shadow_offset[1]),
        shadow,
    )

    # 4) 전경 톤 보정 (배경 밝기 반영)
    fg = _tone_match_foreground(
        background=bg,
        fg=fg,
        strength=cfg.tone_match_strength,
    )

    # 5) 전경 합성
    canvas.paste(fg, (x, y), fg)

    return canvas


# -----------------------------
# Helpers
# -----------------------------
def _make_shadow(
    *,
    fg: Image.Image,
    opacity: float,
    blur: int,
    offset: Tuple[int, int],
) -> Image.Image:
    """
    전경 알파를 기반으로 소프트 그림자 생성
    """
    # 알파 채널만 추출
    alpha = fg.split()[-1]

    shadow = Image.new("RGBA", fg.size, (0, 0, 0, 0))
    shadow.putalpha(alpha)

    # 검은색으로 채움
    shadow = ImageEnhance.Brightness(shadow).enhance(0.0)

    # 투명도 적용
    shadow_alpha = shadow.split()[-1]
    shadow_alpha = shadow_alpha.point(lambda p: int(p * opacity))
    shadow.putalpha(shadow_alpha)

    # 블러
    if blur > 0:
        shadow = shadow.filter(ImageFilter.GaussianBlur(radius=blur))

    return shadow


def _tone_match_foreground(
    *,
    background: Image.Image,
    fg: Image.Image,
    strength: float,
) -> Image.Image:
    """
    배경 평균 밝기를 기준으로 전경 밝기를 살짝 맞춘다.
    """
    # 배경 중앙 영역 평균 밝기
    bg_arr = np.asarray(background).astype("float32")
    h, w = bg_arr.shape[:2]
    center = bg_arr[int(h * 0.4) : int(h * 0.6), int(w * 0.4) : int(w * 0.6)]
    bg_lum = center.mean() / 255.0

    # 전경 밝기 보정
    enhancer = ImageEnhance.Brightness(fg)
    factor = 1.0 + (bg_lum - 0.5) * strength
    factor = max(0.85, min(1.15, factor))
    return enhancer.enhance(factor)
