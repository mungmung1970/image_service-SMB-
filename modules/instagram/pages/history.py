# ad_creator_platform/modules/instagram/pages/history.py
"""
Instagram Ad - History Page (Streamlit)

역할:
- 인스타 광고 생성 이력 조회
- 결과 이미지 미리보기
- 재다운로드

저장 방식(현재):
- 로컬 파일 기반 JSON 기록
- outputs/history/instagram_history.json

추후:
- Supabase / Firestore / DB로 교체 가능
"""

from __future__ import annotations

import json
from pathlib import Path
import streamlit as st


# -----------------------------
# History Store (Local JSON)
# -----------------------------
def _history_file() -> Path:
    root = Path(__file__).resolve().parents[3]  # ad_creator_platform/
    return root / "outputs" / "history" / "instagram_history.json"


def _load_history() -> list[dict]:
    path = _history_file()
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []


def _save_history(items: list[dict]) -> None:
    path = _history_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")


# -----------------------------
# Page Entry
# -----------------------------
def run() -> None:
    st.title("📚 인스타 광고 생성 이력")
    st.caption("이전에 생성한 광고 이미지를 다시 확인하고 다운로드할 수 있습니다.")

    st.divider()

    history = _load_history()

    if not history:
        st.info("아직 생성된 이력이 없습니다. 먼저 광고를 만들어 보세요.")
        return

    # 최신순
    history = list(reversed(history))

    # -----------------------------
    # Render
    # -----------------------------
    for idx, item in enumerate(history, start=1):
        image_path = item.get("image_path")
        headline = item.get("headline", "")
        created_at = item.get("created_at", "")
        product = item.get("product", "")
        tone = item.get("tone", "")
        discount = item.get("discount", "")

        with st.container(border=True):
            st.subheader(f"🖼️ {idx}. {headline}")
            st.caption(
                f"상품: {product} · 톤: {tone} · 할인: {discount} · 생성일: {created_at}"
            )

            if image_path and Path(image_path).exists():
                st.image(str(image_path), width=600)

                with open(image_path, "rb") as f:
                    st.download_button(
                        label="⬇️ 이미지 다운로드 (PNG)",
                        data=f,
                        file_name=Path(image_path).name,
                        mime="image/png",
                        use_container_width=True,
                    )
            else:
                st.warning(
                    "이미지 파일이 존재하지 않습니다. (로컬 파일 경로 확인 필요)"
                )


# -----------------------------
# Helper for saving history
# (Generate 페이지에서 호출 가능)
# -----------------------------
def append_history(record: dict) -> None:
    """
    Generate Page가 광고 생성 후 이력을 남길 때 사용
    record 예시:
      {
        "headline": "...",
        "product": "...",
        "tone": "...",
        "discount": "...",
        "created_at": "2026-01-31 10:00",
        "image_path": "outputs/images/xxx.png"
      }
    """
    items = _load_history()
    items.append(record)
    _save_history(items)
