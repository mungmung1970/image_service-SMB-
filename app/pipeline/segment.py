# BiRefNet
# ad_creator_platform/pipeline/segment.py
"""
Segment Stage (Product Cutout)

역할:
- 제품/주제 이미지를 입력받아 배경을 제거한 RGBA(PIL Image)를 반환한다.
- 실무 파이프라인에서는 BiRefNet / SAM + Refine / U2Net 등을 사용할 수 있다.

현재 구현:
- (기본) 간단한 휴리스틱 폴백(중앙 객체 가정 + 가장자리 배경 추정) 제공
- (옵션) 외부 세그멘테이션 모델을 붙이기 쉬운 인터페이스 제공

주의:
- 이 파일은 "모델 호출"을 위한 자리입니다.
- 실제 BiRefNet 모델을 바로 설치/호출하는 코드는 환경 의존성이 크므로,
  현재는 연결 훅 + 폴백을 제공합니다.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Literal

import numpy as np
from PIL import Image, ImageFilter


SegmentBackend = Literal["fallback"]  # 추후: "birefnet" | "sam" | "u2net" 등으로 확장


@dataclass
class SegmentConfig:
    backend: SegmentBackend = "fallback"
    # 폴백 품질 파라미터
    feather_radius: int = 6  # 가장자리 블러(부드럽게)
    bg_sample_border: int = 24  # 배경색 추정용 가장자리 샘플 두께
    fg_center_margin: float = 0.18  # 전경 추정 영역(중앙 비율)


# -----------------------------
# Public API
# -----------------------------
def segment_product(
    *,
    image: Image.Image,
    config: Optional[SegmentConfig] = None,
) -> Image.Image:
    """
    제품(전경)을 분리하여 RGBA 이미지로 반환한다.

    Args:
        image: 입력 이미지 (RGB/RGBA 모두 가능)
        config: 분리 설정

    Returns:
        product_rgba: 배경이 투명한 RGBA 이미지
    """
    cfg = config or SegmentConfig()

    if cfg.backend == "fallback":
        return _segment_fallback(image=image, cfg=cfg)

    # 확장 포인트(현재는 미사용)
    raise NotImplementedError(f"Unsupported segment backend: {cfg.backend}")


# -----------------------------
# Fallback Implementation
# -----------------------------
def _segment_fallback(*, image: Image.Image, cfg: SegmentConfig) -> Image.Image:
    """
    폴백 세그멘테이션:
    - 전경이 "중앙"에 있고 배경이 "가장자리"에 있다는 가정
    - 가장자리 배경색을 추정한 뒤, 색 거리로 마스크 생성
    - 간단하지만 제품 사진(스튜디오/단순 배경)에는 의외로 잘 맞음

    한계:
    - 복잡한 배경에는 부정확할 수 있음
    - 실무에서는 BiRefNet/SAM 등으로 교체 권장
    """
    img = image.convert("RGB")
    arr = np.array(img).astype(np.int16)
    h, w = arr.shape[:2]

    # 1) 배경 색상 추정: 이미지 가장자리(border) 픽셀의 평균
    b = max(4, int(cfg.bg_sample_border))
    border_pixels = np.concatenate(
        [
            arr[:b, :, :].reshape(-1, 3),
            arr[-b:, :, :].reshape(-1, 3),
            arr[:, :b, :].reshape(-1, 3),
            arr[:, -b:, :].reshape(-1, 3),
        ],
        axis=0,
    )
    bg_color = border_pixels.mean(axis=0)  # (3,)

    # 2) 색 거리 기반 마스크
    dist = np.sqrt(((arr - bg_color) ** 2).sum(axis=2))  # (h,w)
    # 임계값: 배경/전경 대비가 약하면 오동작 가능 -> 중앙 영역을 이용해 보정
    center = _center_box(h=h, w=w, margin=cfg.fg_center_margin)
    center_dist = dist[center[0] : center[1], center[2] : center[3]]
    # 중앙 영역에서 거리 평균이 높을수록 전경이 더 "배경과 다르다"
    center_mean = float(center_dist.mean())
    # 동적 임계값: 중앙 평균의 일부 + 최소값
    thr = max(18.0, center_mean * 0.55)

    mask = (dist > thr).astype(np.uint8) * 255  # 0 or 255

    # 3) 마스크 후처리(가장자리 부드럽게)
    mask_img = Image.fromarray(mask, mode="L")
    if cfg.feather_radius > 0:
        mask_img = mask_img.filter(ImageFilter.GaussianBlur(radius=cfg.feather_radius))

    # 4) RGBA 합성
    rgba = image.convert("RGBA")
    r, g, b2, _a = rgba.split()
    out = Image.merge("RGBA", (r, g, b2, mask_img))

    # 5) 오브젝트 바운딩 박스 크롭(투명 여백 줄이기)
    bbox = mask_img.getbbox()
    if bbox:
        out = out.crop(bbox)

    return out


def _center_box(*, h: int, w: int, margin: float) -> tuple[int, int, int, int]:
    """
    중앙 박스 영역 계산 (전경 추정용)
    margin: 0~0.4 권장 (클수록 중앙 영역이 작아짐)
    """
    m = max(0.0, min(0.45, float(margin)))
    top = int(h * m)
    bottom = int(h * (1.0 - m))
    left = int(w * m)
    right = int(w * (1.0 - m))
    return top, bottom, left, right
