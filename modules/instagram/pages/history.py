"""
Instagram Feed Ad - History Page (Streamlit)

역할:
- 로그인한 사용자의 인스타 광고 생성 이력 조회
- 생성된 이미지 미리보기
- 이미지 재다운로드
"""

from __future__ import annotations

import streamlit as st

from app.core.guards import require_login, ensure_safe_path
from app.core.config import OUTPUTS_DIR
from app.storage.local_fs import load_history, resolve_image_path


# -----------------------------
# Page Entry
# -----------------------------
def run():
    # -----------------------------
    # Login Guard
    # -----------------------------
    try:
        user_email = require_login()
    except RuntimeError as e:
        st.error(str(e))
        st.stop()

    st.title("📚 내 인스타 광고 이력")

    # -----------------------------
    # Load History
    # -----------------------------
    try:
        history = load_history(user_email)
    except Exception:
        st.error("이력 데이터를 불러오는 중 문제가 발생했습니다.")
        return

    insta_history = [h for h in history if h.get("ad_type") == "instagram_feed"]

    if not insta_history:
        st.info("아직 생성한 인스타 광고가 없습니다. 먼저 광고를 만들어 보세요.")
        return

    insta_history = list(reversed(insta_history))

    # -----------------------------
    # Render History
    # -----------------------------
    for idx, item in enumerate(insta_history, start=1):
        image_id = item.get("image_id", "-")
        product = item.get("product", "-")
        tone = item.get("tone", "-")
        created_at = item.get("created_at", "-")
        copy = item.get("copy", {})

        raw_path = resolve_image_path(
            email=user_email,
            relative_path=item.get("image_path", ""),
        )

        image_path = ensure_safe_path(
            OUTPUTS_DIR,
            raw_path,
        )

        with st.container(border=True):
            st.subheader(f"🖼️ {idx}. {image_id}")
            st.caption(f"상품: {product} · 톤: {tone} · 생성일: {created_at}")

            st.image(
                str(image_path),
                caption=copy.get("headline", ""),
                use_column_width=True,
            )

            with st.expander("📝 광고 문구 보기"):
                st.markdown(
                    f"""
**Headline**  
{copy.get("headline", "")}

**Subcopy**  
{copy.get("subcopy", "")}

**CTA**  
{copy.get("cta", "")}
"""
                )

            with open(image_path, "rb") as f:
                st.download_button(
                    label="⬇️ 이미지 다운로드",
                    data=f,
                    file_name=f"{image_id}.png",
                    mime="image/png",
                    use_container_width=True,
                )
