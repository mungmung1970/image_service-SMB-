# ad_creator_platform/modules/instagram/pipeline.py
"""
Instagram Feed Ad Pipeline

역할:
- 인스타 피드 광고 생성의 '전체 흐름'을 담당
- UI(Streamlit)와 비즈니스 로직을 분리
- 플랫폼 공통 서비스들을 조합

Flow:
1) 광고 문구 생성 (copy_service)
2) 배경 이미지 생성 (image_service)
3) 레이어 합성 (render_service)
4) 로컬 저장 + 이력 기록 (local_fs)
"""

from __future__ import annotations

from typing import Dict, Optional

from PIL import Image

from app.services.copy_service import generate_copy
from app.services.image_service import generate_background
from app.services.render_service import compose_ad_image
from app.storage.local_fs import (
    generate_image_id,
    save_image,
    append_history,
)
from app.core.logging import log_action
from app.core.metadata import AdMetadata
from app.core.config import IMAGE_PROVIDER


# -----------------------------
# Instagram Feed Config
# -----------------------------
INSTAGRAM_FEED_SIZE = (1080, 1080)


# -----------------------------
# Public Pipeline API
# -----------------------------
def generate_instagram_feed_ad(
    *,
    user_email: str,
    product: str,
    tone: str,
    discount: Optional[str] = None,
    prompt_extra: Optional[str] = None,
    main_image_path: Optional[str] = None,
) -> Dict[str, str]:
    """
    인스타 피드 광고 생성 파이프라인 (플랫폼 핵심 API)

    Args:
        user_email: 로그인한 사용자 이메일
        product: 상품/서비스명
        tone: 광고 톤 ("캐주얼" | "고급" | "감성")
        discount: 할인 정보 (선택)
        prompt_extra: 이미지 생성 추가 힌트 (선택)
        main_image_path: 메인 오브젝트 PNG 경로 (선택)

    Returns:
        {
          "image_id": str,
          "image_path": str,      # 사용자 기준 상대 경로
          "headline": str,
          "subcopy": str,
          "cta": str
        }
    """

    # -----------------------------
    # 1) 광고 문구 생성
    # -----------------------------
    copy = generate_copy(
        product=product,
        tone=tone,  # type: ignore[arg-type]
        discount=discount,
        extra_hint=prompt_extra,
    )

    # -----------------------------
    # 2) 배경 이미지 생성
    # -----------------------------
    bg = generate_background(
        size=INSTAGRAM_FEED_SIZE,
        prompt=_build_image_prompt(product, tone, prompt_extra),
        negative_prompt="text, watermark, logo",
    )

    # -----------------------------
    # 3) 레이어 합성
    # -----------------------------
    final_image: Image.Image = compose_ad_image(
        background=bg,
        copy=copy,
        size=INSTAGRAM_FEED_SIZE,
        main_image_path=main_image_path,
        user_email=user_email,
    )

    # -----------------------------
    # 4) 저장 + 이력 기록
    # -----------------------------
    image_id = generate_image_id(prefix="insta")
    image_rel_path = save_image(
        email=user_email,
        pil_image=final_image,
        image_id=image_id,
        ext="png",
    )

    metadata = AdMetadata(
        image_id=image_id,
        ad_type="instagram_feed",
        user_email=user_email,
        product=product,
        tone=tone,
        discount=discount,
        prompt=_build_image_prompt(product, tone, prompt_extra),
        prompt_extra=prompt_extra,
        image_provider=IMAGE_PROVIDER,
        image_path=image_rel_path,
        image_size=INSTAGRAM_FEED_SIZE,
        copy=copy,
    )

    append_history(
        email=user_email,
        record=metadata.to_dict(),
    )

    # -----------------------------
    # 5) 결과 반환
    # -----------------------------
    return {
        "image_id": image_id,
        "image_path": image_rel_path,
        "headline": copy["headline"],
        "subcopy": copy["subcopy"],
        "cta": copy["cta"],
    }


# -----------------------------
# Prompt Helper
# -----------------------------
def _build_image_prompt(
    product: str,
    tone: str,
    extra: Optional[str],
) -> str:
    """
    인스타 광고용 이미지 프롬프트 빌더
    - 텍스트는 절대 포함하지 않음
    """
    base = [
        "clean modern instagram ad background",
        "high quality",
        "minimal composition",
        "studio lighting",
        "no text",
    ]

    if tone == "고급":
        base.append("luxury, premium mood")
    elif tone == "감성":
        base.append("warm, emotional, cozy mood")
    else:
        base.append("bright, friendly, casual mood")

    if product:
        base.append(f"fits well with {product}")

    if extra:
        base.append(extra)

    return ", ".join(base)
