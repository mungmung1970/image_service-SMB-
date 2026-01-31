# ad_creator_platform/app/services/copy_service.py
"""
Ad Copy Generation Service

역할:
- 광고 문구(headline / subcopy / CTA) 생성
- 현재: Rule-based (안정적 MVP)
- 추후: LLM(OpenAI/HF)로 내부 구현 교체 가능

이 파일의 함수 시그니처는 '절대' 바꾸지 않는 것을 권장
"""

from __future__ import annotations

from typing import Dict, Literal


Tone = Literal["캐주얼", "고급", "감성"]


# -----------------------------
# Public API
# -----------------------------
def generate_copy(
    *,
    product: str,
    tone: Tone,
    discount: str | None = None,
    extra_hint: str | None = None,
) -> Dict[str, str]:
    """
    광고 문구 생성 (플랫폼 공통 인터페이스)

    Args:
        product: 상품/서비스명
        tone: 광고 톤 ("캐주얼" | "고급" | "감성")
        discount: 할인 정보 (선택)
        extra_hint: 추가 힌트 (선택)

    Returns:
        {
          "headline": str,
          "subcopy": str,
          "cta": str
        }
    """
    product = (product or "").strip()
    discount = (discount or "").strip()
    extra_hint = (extra_hint or "").strip()

    if tone == "고급":
        return _premium_copy(product, discount, extra_hint)

    if tone == "감성":
        return _emotional_copy(product, discount, extra_hint)

    # default: 캐주얼
    return _casual_copy(product, discount, extra_hint)


# -----------------------------
# Tone-specific implementations
# -----------------------------
def _casual_copy(product: str, discount: str, extra: str) -> Dict[str, str]:
    headline = _pick(
        primary=f"{discount} 지금!" if discount else f"{product} 추천!",
        fallback=f"{product} 어떠세요?",
    )

    subcopy = _pick(
        primary="가볍게 즐기기 딱 좋아요",
        fallback="지금 가장 인기 있는 선택",
    )

    cta = "바로 확인하기"

    return _finalize(headline, subcopy, cta, extra)


def _premium_copy(product: str, discount: str, extra: str) -> Dict[str, str]:
    headline = _pick(
        primary=f"{product} {discount}" if discount else f"{product} 런칭",
        fallback=f"{product} 컬렉션",
    )

    subcopy = _pick(
        primary="완성도 높은 선택을 경험하세요",
        fallback="프리미엄 무드를 담았습니다",
    )

    cta = "자세히 보기"

    return _finalize(headline, subcopy, cta, extra)


def _emotional_copy(product: str, discount: str, extra: str) -> Dict[str, str]:
    headline = _pick(
        primary=f"{discount} 오늘만" if discount else f"{product} 한 잔의 여유",
        fallback=f"{product}의 순간",
    )

    subcopy = _pick(
        primary="일상 속 작은 행복을 전해요",
        fallback="잠시 쉬어가도 괜찮아요",
    )

    cta = "지금 만나보세요"

    return _finalize(headline, subcopy, cta, extra)


# -----------------------------
# Utilities
# -----------------------------
def _pick(primary: str, fallback: str) -> str:
    """
    빈 문자열 방지용 선택 유틸
    """
    return primary if primary.strip() else fallback


def _finalize(headline: str, subcopy: str, cta: str, extra: str) -> Dict[str, str]:
    """
    최종 정제 단계:
    - 길이 정리
    - extra 힌트 반영 (가볍게)
    """
    headline = headline.strip()
    subcopy = subcopy.strip()
    cta = cta.strip()

    # 너무 길면 컷 (인스타 피드 기준)
    if len(headline) > 20:
        headline = headline[:18] + "…"

    if len(subcopy) > 40:
        subcopy = subcopy[:38] + "…"

    # extra 힌트는 subcopy 뒤에 살짝만 반영
    if extra:
        subcopy = f"{subcopy}"

    return {
        "headline": headline,
        "subcopy": subcopy,
        "cta": cta,
    }
