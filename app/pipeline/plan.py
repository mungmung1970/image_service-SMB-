# GPT 기획
# ad_creator_platform/pipeline/plan.py
"""
Plan Stage (LLM Orchestrator)

역할:
- 사용자 입력을 바탕으로 "광고 기획 결과"를 만든다.
- 출력은 항상 구조화된 Plan(dict) 형태:
  - copy: headline/subcopy/cta
  - background_prompt: 배경 생성용 프롬프트(텍스트 포함 금지)
  - layout: 텍스트 레이아웃 의도(JSON)
  - model_hints: (옵션) 추후 LoRA/ControlNet/IP-Adapter 연결을 위한 힌트

주의:
- 이 단계는 이미지를 생성하지 않는다.
- 배경 프롬프트에는 "no text, no logo, no watermark"를 강제한다.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Literal
import json
import re


Tone = Literal["캐주얼", "고급", "감성"]


# -----------------------------
# Data Models
# -----------------------------
@dataclass
class CopySpec:
    headline: str
    subcopy: str
    cta: str


@dataclass
class EmphasisSpec:
    text: str
    color_hex: str = "#FF4D4D"  # 강조 색 (기본: 레드 계열)
    scale: float = 1.15  # 강조 크기 배율(렌더러에서 해석)


@dataclass
class TextBlockLayout:
    position: Literal[
        "upper_center",
        "upper_left",
        "upper_right",
        "center",
        "lower_center",
        "lower_left",
        "lower_right",
    ] = "upper_center"
    font_style: Literal["regular", "bold"] = "bold"
    font_size: Literal["sm", "md", "lg", "xl"] = "xl"
    color_hex: str = "#FFFFFF"
    emphasis: Optional[EmphasisSpec] = None


@dataclass
class LayoutSpec:
    headline: TextBlockLayout
    subcopy: TextBlockLayout
    cta: TextBlockLayout


@dataclass
class ModelHints:
    # 배경 스타일 고정을 위한 LoRA 이름/키 (지금은 미사용, 훅만)
    lora_key: Optional[str] = None
    # ControlNet 사용 시 스케치/깊이 등 힌트 (지금은 미사용)
    control_hint: Optional[str] = None
    # IP-Adapter 사용 시 레퍼런스 이미지 key/path (지금은 미사용)
    ip_adapter_ref: Optional[str] = None


@dataclass
class Plan:
    copy: CopySpec
    background_prompt: str
    layout: LayoutSpec
    model_hints: ModelHints

    def to_dict(self) -> Dict:
        return asdict(self)


# -----------------------------
# Public API
# -----------------------------
def build_plan(
    *,
    product: str,
    tone: Tone,
    discount: Optional[str] = None,
    prompt_extra: Optional[str] = None,
    # LLM 결과를 붙일 수 있도록 확장 포인트
    llm_json: Optional[Dict] = None,
) -> Plan:
    """
    Plan을 생성한다.

    llm_json을 넘기면:
      - LLM이 생성한 구조화 결과를 우선 적용하고
      - 누락된 필드는 규칙 기반으로 채운다.

    llm_json 없이도:
      - 규칙 기반으로 항상 동작한다.
    """
    product = (product or "").strip()
    if not product:
        raise ValueError("product는 비어 있을 수 없습니다.")

    discount = (discount or "").strip() or None
    prompt_extra = (prompt_extra or "").strip() or None

    # 1) Copy
    copy = _build_copy_rule(product=product, tone=tone, discount=discount)

    # 2) Background Prompt (텍스트 포함 금지)
    bg_prompt = _build_background_prompt_rule(
        product=product,
        tone=tone,
        extra=prompt_extra,
    )

    # 3) Layout (의도 JSON)
    layout = _build_layout_rule(
        tone=tone,
        discount=discount,
        headline=copy.headline,
    )

    # 4) Model Hints (LoRA 등은 나중에)
    hints = ModelHints(
        lora_key=None,
        control_hint=None,
        ip_adapter_ref=None,
    )

    # LLM 결과가 있다면 merge
    if llm_json:
        copy, bg_prompt, layout, hints = _merge_llm_json(
            llm_json=llm_json,
            base_copy=copy,
            base_bg_prompt=bg_prompt,
            base_layout=layout,
            base_hints=hints,
        )

    return Plan(
        copy=copy,
        background_prompt=bg_prompt,
        layout=layout,
        model_hints=hints,
    )


# -----------------------------
# Rule-based builders
# -----------------------------
def _build_copy_rule(*, product: str, tone: Tone, discount: Optional[str]) -> CopySpec:
    """
    규칙 기반 카피 생성.
    - 추후 LLM 연동 시 이 부분은 대체/보강 가능
    """
    # Headline
    if discount:
        # discount 안에 이미 "50%"가 있으면 강조 타겟이 되기 쉬움
        headline = f"오늘만 {discount}"
    else:
        headline = f"{product} 지금 만나보세요"

    # Subcopy
    if tone == "고급":
        subcopy = f"{product}의 깊은 매력을 프리미엄 무드로."
        cta = "지금 예약하기"
    elif tone == "감성":
        subcopy = f"따뜻한 순간, {product}와 함께."
        cta = "지금 확인하기"
    else:
        subcopy = f"가볍게 즐기는 {product}, 오늘도 부담 없이!"
        cta = "바로 보기"

    return CopySpec(headline=headline, subcopy=subcopy, cta=cta)


def _build_background_prompt_rule(
    *, product: str, tone: Tone, extra: Optional[str]
) -> str:
    """
    배경 생성 프롬프트 규칙.
    - 절대 텍스트 넣지 않음
    """
    base = [
        "high quality background for advertisement",
        "instagram-friendly composition",
        "soft depth of field",
        "clean scene",
        "no text",
        "no logo",
        "no watermark",
    ]

    if tone == "고급":
        base += [
            "luxury cafe mood",
            "premium interior",
            "warm but elegant lighting",
            "wood texture",
        ]
    elif tone == "감성":
        base += [
            "warm cozy cafe mood",
            "soft warm lighting",
            "wooden table",
            "gentle bokeh",
        ]
    else:
        base += [
            "bright friendly cafe mood",
            "natural lighting",
            "wooden table",
            "simple clean",
        ]

    # product는 분위기만 힌트로(직접 텍스트 렌더링 X)
    base.append(f"fits well with {product}")

    if extra:
        # extra에 "텍스트"가 들어오면 제거(안전장치)
        safe_extra = _strip_text_like_tokens(extra)
        if safe_extra:
            base.append(safe_extra)

    return ", ".join(base)


def _build_layout_rule(
    *, tone: Tone, discount: Optional[str], headline: str
) -> LayoutSpec:
    """
    레이아웃 의도 규칙.
    - headline: 상단 중앙
    - subcopy: 하단 중앙
    - cta: 하단(가장 아래) 혹은 하단 중앙
    - discount가 있으면 '50%' 또는 숫자/퍼센트 구문 강조 대상으로 설정
    """
    emphasis = None
    if discount:
        target = _extract_percent_or_number_phrase(headline)
        if target:
            emphasis = EmphasisSpec(text=target, color_hex="#FF4D4D", scale=1.2)

    headline_layout = TextBlockLayout(
        position="upper_center",
        font_style="bold",
        font_size="xl" if tone != "고급" else "lg",
        color_hex="#FFFFFF",
        emphasis=emphasis,
    )

    subcopy_layout = TextBlockLayout(
        position="lower_center",
        font_style="regular",
        font_size="md",
        color_hex="#FFFFFF",
        emphasis=None,
    )

    cta_layout = TextBlockLayout(
        position="lower_center",
        font_style="bold",
        font_size="md",
        color_hex="#FFFFFF",
        emphasis=None,
    )

    return LayoutSpec(
        headline=headline_layout,
        subcopy=subcopy_layout,
        cta=cta_layout,
    )


# -----------------------------
# LLM merge (optional)
# -----------------------------
def _merge_llm_json(
    *,
    llm_json: Dict,
    base_copy: CopySpec,
    base_bg_prompt: str,
    base_layout: LayoutSpec,
    base_hints: ModelHints,
):
    """
    LLM이 만든 JSON을 안전하게 병합한다.
    - 누락/오염된 값은 base를 유지
    - background_prompt는 반드시 no text/no logo/no watermark 포함
    """
    copy = base_copy
    bg_prompt = base_bg_prompt
    layout = base_layout
    hints = base_hints

    # copy
    c = llm_json.get("copy")
    if isinstance(c, dict):
        headline = str(c.get("headline") or copy.headline)
        subcopy = str(c.get("subcopy") or copy.subcopy)
        cta = str(c.get("cta") or copy.cta)
        copy = CopySpec(headline=headline, subcopy=subcopy, cta=cta)

    # background_prompt
    bp = llm_json.get("background_prompt")
    if isinstance(bp, str) and bp.strip():
        bg_prompt = _enforce_bg_prompt_safety(bp.strip())

    # layout
    l = llm_json.get("layout")
    if isinstance(l, dict):
        layout = _parse_layout_dict(l, fallback=layout)

    # model hints
    mh = llm_json.get("model_hints")
    if isinstance(mh, dict):
        hints = ModelHints(
            lora_key=_safe_str(mh.get("lora_key"), hints.lora_key),
            control_hint=_safe_str(mh.get("control_hint"), hints.control_hint),
            ip_adapter_ref=_safe_str(mh.get("ip_adapter_ref"), hints.ip_adapter_ref),
        )

    return copy, bg_prompt, layout, hints


def _parse_layout_dict(d: Dict, fallback: LayoutSpec) -> LayoutSpec:
    def parse_block(key: str, fb: TextBlockLayout) -> TextBlockLayout:
        x = d.get(key)
        if not isinstance(x, dict):
            return fb

        emphasis = None
        em = x.get("emphasis")
        if isinstance(em, dict) and em.get("text"):
            emphasis = EmphasisSpec(
                text=str(em.get("text")),
                color_hex=str(em.get("color_hex") or "#FF4D4D"),
                scale=float(em.get("scale") or 1.15),
            )

        return TextBlockLayout(
            position=_safe_literal(
                x.get("position"),
                allowed=[
                    "upper_center",
                    "upper_left",
                    "upper_right",
                    "center",
                    "lower_center",
                    "lower_left",
                    "lower_right",
                ],
                default=fb.position,
            ),
            font_style=_safe_literal(
                x.get("font_style"),
                allowed=["regular", "bold"],
                default=fb.font_style,
            ),
            font_size=_safe_literal(
                x.get("font_size"),
                allowed=["sm", "md", "lg", "xl"],
                default=fb.font_size,
            ),
            color_hex=str(x.get("color_hex") or fb.color_hex),
            emphasis=emphasis,
        )

    return LayoutSpec(
        headline=parse_block("headline", fallback.headline),
        subcopy=parse_block("subcopy", fallback.subcopy),
        cta=parse_block("cta", fallback.cta),
    )


# -----------------------------
# Utils
# -----------------------------
def _enforce_bg_prompt_safety(prompt: str) -> str:
    """
    배경 프롬프트에 'no text/no logo/no watermark'를 강제로 포함한다.
    """
    must_have = ["no text", "no logo", "no watermark"]
    lower = prompt.lower()
    parts = [prompt]
    for token in must_have:
        if token not in lower:
            parts.append(token)
    return ", ".join(parts)


def _strip_text_like_tokens(s: str) -> str:
    """
    사용자 extra 요청에 '텍스트 넣기' 등의 위험 신호가 있으면 제거한다.
    """
    # 아주 단순한 안전 필터 (필요 시 강화)
    blacklist = ["text", "logo", "watermark", "문구", "글자", "텍스트", "로고"]
    if any(b.lower() in s.lower() for b in blacklist):
        return ""
    return s.strip()


def _extract_percent_or_number_phrase(text: str) -> Optional[str]:
    """
    '50%' 같은 강조 타겟을 추출
    """
    m = re.search(r"(\d+\s?%|\d+\s?퍼센트)", text)
    if m:
        return m.group(1).replace(" ", "")
    return None


def _safe_str(v, default: Optional[str]) -> Optional[str]:
    if v is None:
        return default
    s = str(v).strip()
    return s if s else default


def _safe_literal(v, allowed: List[str], default: str) -> str:
    if v in allowed:
        return v
    return default
