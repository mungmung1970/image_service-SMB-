# ad_creator_platform/modules/instagram/pipeline.py
"""
Instagram Ad Generation Pipeline

역할:
- 인스타그램 피드 광고 1장을 생성하는 '플랫폼 전용 파이프라인'
- 하위 파이프라인(plan/segment/background/relight/upscale/render)을 조합
- Streamlit UI 및 이력 저장에서 바로 사용할 수 있는 결과를 반환

출력:
- 최종 이미지 (PIL Image)
- copy (headline/subcopy/cta)
- layout (LayoutSpec)
"""

from __future__ import annotations

from typing import Dict, Optional

from PIL import Image

# ---- Pipeline Stages ----
from pipeline.plan import build_plan
from pipeline.segment import segment_product, SegmentConfig
from pipeline.background import generate_background, BackgroundConfig
from pipeline.relight import relight_and_compose, RelightConfig
from pipeline.upscale import upscale_image, UpscaleConfig

# ---- Render ----
from app.services.render_service import render_text_layers


# -----------------------------
# Public API
# -----------------------------
def generate_instagram_ad(
    *,
    product: str,
    tone: str,
    discount: Optional[str] = None,
    prompt_extra: Optional[str] = None,
    # 사용자 업로드 메인 이미지(선택)
    main_image: Optional[Image.Image] = None,
    # 출력 옵션
    canvas_size: tuple[int, int] = (1080, 1080),
) -> Dict:
    """
    인스타 피드 광고 1장 생성

    Args:
        product: 상품/서비스명
        tone: "캐주얼" | "고급" | "감성"
        discount: "50%" 등 할인 문구 (선택)
        prompt_extra: 배경 분위기 추가 힌트 (선택)
        main_image: 사용자가 업로드한 제품 이미지 (선택)
        canvas_size: 인스타 피드 기본 1080x1080

    Returns:
        {
          "image": PIL.Image,
          "copy": {headline, subcopy, cta},
          "layout": LayoutSpec,
          "background_prompt": str
        }
    """

    # -----------------------------
    # 1) PLAN (LLM / Rule)
    # -----------------------------
    plan = build_plan(
        product=product,
        tone=tone,  # type: ignore[arg-type]
        discount=discount,
        prompt_extra=prompt_extra,
    )

    # -----------------------------
    # 2) BACKGROUND
    # -----------------------------
    bg = generate_background(
        prompt=plan.background_prompt,
        config=BackgroundConfig(
            size=canvas_size,
            lora_key=plan.model_hints.lora_key,
            control_hint=plan.model_hints.control_hint,
            ip_adapter_ref=plan.model_hints.ip_adapter_ref,
        ),
    )

    # -----------------------------
    # 3) SEGMENT (optional)
    # -----------------------------
    fg_rgba: Optional[Image.Image] = None
    if main_image is not None:
        fg_rgba = segment_product(
            image=main_image,
            config=SegmentConfig(
                backend="fallback",  # 나중에 "birefnet"으로 교체
            ),
        )

    # -----------------------------
    # 4) RELIGHT (compose)
    # -----------------------------
    if fg_rgba is not None:
        composed = relight_and_compose(
            background=bg,
            foreground_rgba=fg_rgba,
            config=RelightConfig(
                backend="fallback",  # 나중에 "ic_light"로 교체
            ),
        )
    else:
        composed = bg

    # -----------------------------
    # 5) UPSCALE
    # -----------------------------
    upscaled = upscale_image(
        image=composed,
        config=UpscaleConfig(
            backend="fallback",
            scale=1,  # 인스타 기본은 1 (나중에 2x/4x 가능)
            max_size=canvas_size,
        ),
    )

    # -----------------------------
    # 6) RENDER TEXT (FINAL)
    # -----------------------------
    final_image = render_text_layers(
        image=upscaled,
        copy={
            "headline": plan.copy.headline,
            "subcopy": plan.copy.subcopy,
            "cta": plan.copy.cta,
        },
        layout=plan.layout,
        platform="instagram",
    )

    # -----------------------------
    # Result
    # -----------------------------
    return {
        "image": final_image,
        "copy": {
            "headline": plan.copy.headline,
            "subcopy": plan.copy.subcopy,
            "cta": plan.copy.cta,
        },
        "layout": plan.layout,
        "background_prompt": plan.background_prompt,
    }
