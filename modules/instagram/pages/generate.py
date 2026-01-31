"""
Instagram Feed Ad - Generate Page (Streamlit)

역할:
- 사용자 입력 UI
- 인스타 광고 생성 트리거
- pipeline 호출
- 결과 이미지 표시 / 다운로드
"""

from __future__ import annotations

import streamlit as st

from app.core.guards import require_login, can_send_email
from app.storage.local_fs import resolve_image_path, save_uploaded_file
from modules.instagram.pipeline import generate_instagram_feed_ad
from app.services.email_service import send_image_email
from app.core.logging import log_error


# -----------------------------
# Page Entry
# -----------------------------
def run():
    # -----------------------------
    # Login Guard (Page Entry)
    # -----------------------------
    try:
        user_email = require_login()
    except RuntimeError as e:
        st.error(str(e))
        st.stop()

    st.title("📸 인스타 피드 광고 이미지 생성 (1:1)")
    st.caption("배경 → 메인 → 문구 레이어 순서로 광고 이미지를 생성합니다.")

    # -----------------------------
    # Input Form
    # -----------------------------
    with st.form("instagram_generate_form"):
        col1, col2 = st.columns(2)

        with col1:
            product = st.text_input(
                "상품 / 서비스명",
                placeholder="예: 시그니처 라떼",
            )

            tone = st.selectbox(
                "광고 톤",
                options=["캐주얼", "고급", "감성"],
                index=0,
            )

            discount = st.text_input(
                "할인 정보 (선택)",
                placeholder="예: 20% 할인, 오늘만 1+1",
            )

        with col2:
            prompt_extra = st.text_area(
                "이미지 분위기 추가 요청 (선택)",
                placeholder="예: 밝고 미니멀한 카페 분위기",
            )

            uploaded_main_image = st.file_uploader(
                "메인 이미지 업로드 (PNG/JPG, 선택)",
                type=["png", "jpg", "jpeg"],
            )

        submitted = st.form_submit_button("광고 이미지 생성하기")

    # -----------------------------
    # Generate
    # -----------------------------
    if not submitted:
        return

    if not product.strip():
        st.error("상품 / 서비스명을 입력해 주세요.")
        return

    # ✅ [추가] 업로드된 메인 이미지를 로컬에 저장하고 경로를 만든다 (pipeline 호출 직전)
    main_image_path = None
    try:
        if uploaded_main_image is not None:
            main_image_path = save_uploaded_file(
                email=user_email,
                uploaded_file=uploaded_main_image,
                subdir="uploads",
            )
            st.success("✅ 메인 이미지 업로드 완료")
    except Exception as e:
        log_error(
            message="Failed to save uploaded main image",
            user=user_email,
            action="save_uploaded_image",
            exc=e,
        )
        st.error("업로드한 메인 이미지를 저장하는 중 오류가 발생했습니다.")
        return

    # (선택) 업로드 이미지 미리보기
    if uploaded_main_image is not None:
        st.image(uploaded_main_image, caption="업로드한 메인 이미지", width=300)

    with st.spinner("🖼️ 광고 이미지 생성 중..."):
        try:
            result = generate_instagram_feed_ad(
                user_email=user_email,
                product=product,
                tone=tone,
                discount=discount or None,
                prompt_extra=prompt_extra or None,
                main_image_path=main_image_path,  # ✅ 여기로 전달
            )
        except Exception as e:
            log_error(
                message="Failed to generate Instagram ad",
                user=user_email,
                action="generate_instagram",
                exc=e,
            )
            st.error("광고 생성 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.")
            st.exception(e)  # 🔥 실제 에러 + traceback 표시
            return

    # -----------------------------
    # Result Display
    # -----------------------------
    st.success("✅ 광고 이미지가 생성되었습니다!")

    image_path = resolve_image_path(
        email=user_email,
        relative_path=result["image_path"],
    )

    st.image(
        str(image_path),
        caption=result["headline"],
        width=700,
    )

    # -----------------------------
    # Copy Preview
    # -----------------------------
    st.subheader("📝 생성된 광고 문구")
    st.markdown(
        f"""
**Headline**  
{result['headline']}

**Subcopy**  
{result['subcopy']}

**CTA**  
{result['cta']}
"""
    )

    # -----------------------------
    # Download
    # -----------------------------
    st.subheader("⬇️ 이미지 다운로드")
    with open(image_path, "rb") as f:
        st.download_button(
            label="이미지 다운로드",
            data=f,
            file_name=f"{result['image_id']}.png",
            mime="image/png",
            use_container_width=True,
        )

    st.info("이 이미지는 자동으로 저장되며, **이력** 메뉴에서 다시 확인할 수 있습니다.")

    # -----------------------------
    # Email Send
    # -----------------------------
    st.divider()
    st.subheader("✉️ 이메일로 이미지 받기")

    if not can_send_email():
        st.info("이메일 발송 기능이 설정되어 있지 않습니다.")
        return

    to_email = st.text_input(
        "받을 이메일 주소",
        value=user_email,
        placeholder="example@gmail.com",
    )

    if st.button("이메일로 발송", use_container_width=True):
        try:
            # 실행 직전 로그인 재확인
            require_login()

            send_image_email(
                to_email=to_email,
                subject="[Ad Creator] 인스타 광고 이미지",
                body_text=(
                    "요청하신 인스타 광고 이미지입니다.\n\n"
                    f"- 상품: {product}\n"
                    f"- 톤: {tone}\n"
                ),
                image_path=image_path,
            )
            st.success("📨 이메일 발송이 완료되었습니다!")
        except Exception as e:
            log_error(
                message="Failed to send Instagram ad email",
                user=user_email,
                action="send_instagram_email",
                exc=e,
            )
            st.error("이메일 발송 중 오류가 발생했습니다.")
