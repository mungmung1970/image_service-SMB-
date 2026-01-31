# ad_creator_platform/modules/instagram/pages/generate.py
"""
Instagram Ad - Generate Page (Streamlit)

역할:
- 사용자 입력 UI
- 인스타 광고 생성 파이프라인 호출
- 결과 이미지 미리보기 / 다운로드
- 생성 이력 로컬 저장 (History 페이지 연동)
"""

from __future__ import annotations

import io
from datetime import datetime
from pathlib import Path

import streamlit as st
from PIL import Image

from modules.instagram.pipeline import generate_instagram_ad
from modules.instagram.pages.history import append_history


# -----------------------------
# Path Helpers
# -----------------------------
def _project_root() -> Path:
    # modules/instagram/pages/generate.py 기준
    return Path(__file__).resolve().parents[3]


def _output_image_dir() -> Path:
    path = _project_root() / "outputs" / "images"
    path.mkdir(parents=True, exist_ok=True)
    return path


# -----------------------------
# Page Entry
# -----------------------------
def run() -> None:
    st.title("📸 인스타그램 광고 이미지 만들기")
    st.caption("상품 정보만 입력하면 인스타 피드 광고 이미지를 자동으로 생성합니다.")

    st.divider()

    # -----------------------------
    # Input Form
    # -----------------------------
    with st.form("instagram_ad_form"):
        col1, col2 = st.columns(2)

        with col1:
            product = st.text_input(
                "상품 / 서비스명",
                placeholder="예: 시그니처 카페라떼",
            )

            tone = st.selectbox(
                "광고 톤",
                options=["캐주얼", "고급", "감성"],
                index=0,
            )

            discount = st.text_input(
                "할인 정보 (선택)",
                placeholder="예: 50% 할인, 오늘만 1+1",
            )

        with col2:
            prompt_extra = st.text_area(
                "배경 분위기 추가 요청 (선택)",
                placeholder="예: 나무 테이블이 있는 따뜻한 카페 분위기",
            )

            uploaded_image = st.file_uploader(
                "제품 이미지 업로드 (선택)",
                type=["png", "jpg", "jpeg"],
            )

        submitted = st.form_submit_button("🎨 광고 이미지 생성하기")

    # -----------------------------
    # Validation
    # -----------------------------
    if not submitted:
        return

    if not product.strip():
        st.error("상품 / 서비스명을 입력해 주세요.")
        return

    main_image: Image.Image | None = None
    if uploaded_image is not None:
        try:
            main_image = Image.open(uploaded_image).convert("RGB")
        except Exception:
            st.error("업로드한 이미지 파일을 불러올 수 없습니다.")
            return

    # -----------------------------
    # Generate
    # -----------------------------
    with st.spinner("광고 이미지를 생성 중입니다..."):
        try:
            result = generate_instagram_ad(
                product=product,
                tone=tone,
                discount=discount or None,
                prompt_extra=prompt_extra or None,
                main_image=main_image,
            )
        except Exception as e:
            st.error(f"광고 생성 중 오류가 발생했습니다.\n\n{e}")
            return

    final_image: Image.Image = result["image"]

    # -----------------------------
    # Save Image (Local)
    # -----------------------------
    output_dir = _output_image_dir()
    filename = f"instagram_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    image_path = output_dir / filename
    final_image.save(image_path, format="PNG")

    # -----------------------------
    # Save History
    # -----------------------------
    append_history(
        {
            "headline": result["copy"]["headline"],
            "product": product,
            "tone": tone,
            "discount": discount or "",
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "image_path": str(image_path),
        }
    )

    # -----------------------------
    # Result Display
    # -----------------------------
    st.success("✅ 광고 이미지가 생성되었습니다!")

    st.image(
        final_image,
        caption=result["copy"]["headline"],
        width=600,
    )

    # -----------------------------
    # Copy Preview
    # -----------------------------
    with st.expander("📝 생성된 광고 문구 보기"):
        st.markdown(
            f"""
**Headline**  
{result["copy"]["headline"]}

**Subcopy**  
{result["copy"]["subcopy"]}

**CTA**  
{result["copy"]["cta"]}
"""
        )

    # -----------------------------
    # Download
    # -----------------------------
    buf = io.BytesIO()
    final_image.save(buf, format="PNG")
    buf.seek(0)

    st.download_button(
        label="⬇️ 이미지 다운로드 (PNG)",
        data=buf,
        file_name=filename,
        mime="image/png",
        use_container_width=True,
    )

    st.info(
        "이 광고 이미지는 자동으로 저장되며, **[이력] 페이지**에서 다시 확인할 수 있습니다."
    )
