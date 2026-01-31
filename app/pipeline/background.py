# Flux
# ad_creator_platform/pipeline/background.py
"""
Background Generation Stage

역할:
- 광고용 '배경 이미지'만 생성한다.
- 텍스트/로고/워터마크는 절대 포함하지 않는다.
- Flux / SD / OpenAI Image 등으로 쉽게 교체 가능하도록 인터페이스를 고정한다.

현재 구현:
- (기본) 폴백: 단색 + 그라데이션 배경 생성
- (확장) HuggingFace / OpenAI / Flux 호출 훅 제공 (주석)

주의:
- 이 단계에서는 '이미지 합성'이나 '텍스트 렌더링'을 하지 않는다.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Literal, Tuple

import random
from PIL import Image, ImageDraw


Backend = Literal["fallback"]  # 추후: "flux" | "sd" | "openai" 등


@dataclass
class BackgroundConfig:
    backend: Backend = "fallback"
    size: Tuple[int, int] = (1080, 1080)

    # 모델 관련 힌트 (지금은 미사용, 훅만)
    lora_key: Optional[str] = None
    control_hint: Optional[str] = None
    ip_adapter_ref: Optional[str] = None


# -----------------------------
# Public API
# -----------------------------
def generate_background(
    *,
    prompt: str,
    config: Optional[BackgroundConfig] = None,
) -> Image.Image:
    """
    배경 이미지 생성

    Args:
        prompt: 배경 생성용 프롬프트 (no text/no logo/no watermark 포함되어야 함)
        config: 배경 생성 설정

    Returns:
        background_image: PIL Image (RGB)
    """
    cfg = config or BackgroundConfig()

    # 안전장치: 텍스트 관련 키워드가 들어오면 제거
    _assert_prompt_safe(prompt)

    if cfg.backend == "fallback":
        return _generate_fallback_background(prompt=prompt, size=cfg.size)

    # 확장 포인트 (아직 미구현)
    raise NotImplementedError(f"Unsupported background backend: {cfg.backend}")


# -----------------------------
# Fallback Implementation
# -----------------------------
def _generate_fallback_background(
    *,
    prompt: str,
    size: Tuple[int, int],
) -> Image.Image:
    """
    폴백 배경:
    - 프롬프트의 톤을 아주 약하게 반영한
      '부드러운 그라데이션 배경'
    - 실제 Flux/SD 연결 전 테스트 및 파이프라인 검증용
    """
    w, h = size
    img = Image.new("RGB", (w, h), (240, 240, 240))
    draw = ImageDraw.Draw(img)

    # 프롬프트에서 톤 힌트 추출 (아주 단순)
    prompt_l = prompt.lower()
    if "luxury" in prompt_l or "premium" in prompt_l:
        base_colors = [(40, 30, 20), (90, 70, 50)]
    elif "warm" in prompt_l or "cozy" in prompt_l:
        base_colors = [(120, 80, 50), (220, 180, 140)]
    else:
        base_colors = [(200, 200, 200), (245, 245, 245)]

    c1, c2 = (
        random.sample(base_colors, 2)
        if len(base_colors) > 1
        else (base_colors[0], base_colors[0])
    )

    # 수직 그라데이션
    for y in range(h):
        t = y / max(1, h - 1)
        r = int(c1[0] * (1 - t) + c2[0] * t)
        g = int(c1[1] * (1 - t) + c2[1] * t)
        b = int(c1[2] * (1 - t) + c2[2] * t)
        draw.line([(0, y), (w, y)], fill=(r, g, b))

    return img


# -----------------------------
# Utils
# -----------------------------
def _assert_prompt_safe(prompt: str) -> None:
    """
    배경 프롬프트 안전 검사:
    - 텍스트/로고/워터마크 요청이 있으면 차단
    """
    blacklist = ["text", "logo", "watermark", "글자", "문구", "텍스트", "로고"]
    low = prompt.lower()
    for b in blacklist:
        if b in low:
            raise ValueError(
                f"Background prompt contains forbidden token '{b}'. "
                "Text must be added only in render stage."
            )
