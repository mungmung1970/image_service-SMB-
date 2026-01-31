# Real-ESRGAN
# ad_creator_platform/pipeline/upscale.py
"""
Upscale Stage (Super Resolution)

역할:
- 합성된 광고 이미지를 고해상도로 업스케일한다.
- 실무에서는 Real-ESRGAN, SwinIR 등의 모델을 사용한다.

현재 구현:
- (기본) 폴백: PIL 기반 고품질 리사이즈 (LANCZOS)
- (확장) Real-ESRGAN 연결 훅 제공

주의:
- 텍스트 레이어는 이 단계 이후(render 단계)에서 추가해야 한다.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Literal, Tuple

from PIL import Image


Backend = Literal["fallback"]  # 추후: "realesrgan" | "swinir"


@dataclass
class UpscaleConfig:
    backend: Backend = "fallback"
    scale: int = 2  # 2x, 4x 등
    max_size: Optional[Tuple[int, int]] = None  # (w,h) 제한 (옵션)


# -----------------------------
# Public API
# -----------------------------
def upscale_image(
    *,
    image: Image.Image,
    config: Optional[UpscaleConfig] = None,
) -> Image.Image:
    """
    이미지를 고해상도로 업스케일한다.

    Args:
        image: 입력 이미지 (RGB or RGBA)
        config: 업스케일 설정

    Returns:
        upscaled_image: PIL Image
    """
    cfg = config or UpscaleConfig()

    if cfg.backend == "fallback":
        return _upscale_fallback(image=image, cfg=cfg)

    raise NotImplementedError(f"Unsupported upscale backend: {cfg.backend}")


# -----------------------------
# Fallback Implementation
# -----------------------------
def _upscale_fallback(
    *,
    image: Image.Image,
    cfg: UpscaleConfig,
) -> Image.Image:
    """
    폴백 업스케일:
    - PIL LANCZOS 리사이즈
    - 초해상화 모델이 없어도 전체 파이프라인 검증 가능
    """
    w, h = image.size
    new_w = int(w * cfg.scale)
    new_h = int(h * cfg.scale)

    # 최대 크기 제한
    if cfg.max_size:
        max_w, max_h = cfg.max_size
        scale_w = max_w / new_w if max_w else 1.0
        scale_h = max_h / new_h if max_h else 1.0
        scale = min(scale_w, scale_h, 1.0)
        new_w = int(new_w * scale)
        new_h = int(new_h * scale)

    return image.resize((new_w, new_h), Image.LANCZOS)
