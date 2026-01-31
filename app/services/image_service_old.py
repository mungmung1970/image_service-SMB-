# ad_creator_platform/app/services/image_service.py
"""
Image Generation Service (Platform-level)

역할:
- 광고 배경 이미지 생성
- Provider 추상화: mock / openai / huggingface
- 항상 '텍스트 없는 배경'만 생성 (문구는 render_service 담당)

IMAGE_PROVIDER 환경변수:
- mock     : 로컬 더미 이미지 (기본)
- openai   : GPT-image-1-mini (추후 연결)
- hf       : HuggingFace SDXL (추후 연결)
"""

from __future__ import annotations

import os
from typing import Tuple

from PIL import Image, ImageDraw


# -----------------------------
# Public API
# -----------------------------
def generate_background(
    *,
    size: Tuple[int, int],
    prompt: str,
    negative_prompt: str | None = None,
) -> Image.Image:
    """
    광고 배경 이미지 생성 (텍스트 없음)

    Args:
        size: (width, height)
        prompt: 이미지 컨셉 설명
        negative_prompt: 배제 요소 (선택)

    Returns:
        PIL.Image
    """
    provider = os.getenv("IMAGE_PROVIDER", "mock").lower()

    if provider == "openai":
        return _generate_openai(size, prompt, negative_prompt)

    if provider in ("hf", "huggingface"):
        return _generate_huggingface(size, prompt, negative_prompt)

    # default: mock
    return _generate_mock(size, prompt)


# -----------------------------
# Provider Implementations
# -----------------------------
def _generate_mock(
    size: Tuple[int, int],
    prompt: str,
) -> Image.Image:
    """
    로컬 더미 이미지 생성
    - 개발/디버깅용
    - 프롬프트 내용이 시각적으로 구분되도록 간단한 배경 생성
    """
    width, height = size
    img = Image.new("RGB", (width, height), (245, 245, 245))
    draw = ImageDraw.Draw(img)

    # 간단한 컬러 블록
    draw.rectangle(
        [(0, 0), (width, int(height * 0.6))],
        fill=(230, 230, 230),
    )

    draw.rectangle(
        [(0, int(height * 0.6)), (width, height)],
        fill=(210, 210, 210),
    )

    return img


def _generate_openai(
    size: Tuple[int, int],
    prompt: str,
    negative_prompt: str | None,
) -> Image.Image:
    """
    OpenAI GPT-image-1-mini 기반 이미지 생성

    ⚠️ 현재는 NotImplemented
    → 다음 단계에서 실제 API 호출 코드로 교체 예정
    """
    raise NotImplementedError(
        "OpenAI 이미지 생성은 아직 연결되지 않았습니다. "
        "IMAGE_PROVIDER=mock 으로 먼저 진행하세요."
    )


def _generate_huggingface(
    size: Tuple[int, int],
    prompt: str,
    negative_prompt: str | None,
) -> Image.Image:
    """
    HuggingFace (SDXL 등) 기반 이미지 생성

    ⚠️ 현재는 NotImplemented
    → diffusers 파이프라인 연결 예정
    """
    raise NotImplementedError(
        "HuggingFace 이미지 생성은 아직 연결되지 않았습니다. "
        "IMAGE_PROVIDER=mock 으로 먼저 진행하세요."
    )
