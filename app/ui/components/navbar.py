# ad_creator_platform/ui/components/navbar.py
"""
Global Navbar (Streamlit Sidebar)

역할:
- 사이드바 네비게이션 UI
- 선택된 메뉴 key 반환
- 관리자 여부에 따라 메뉴 분기
"""

from __future__ import annotations

import streamlit as st

from app.core.auth import current_user_email, is_admin, logout


def render_navbar() -> str:
    """
    사이드바 네비게이션을 렌더링하고
    선택된 메뉴 key를 반환합니다.
    """
    user_email = current_user_email()
    if not user_email:
        # 로그인 UI 단계에서는 navbar를 그리지 않음
        return "home"

    with st.sidebar:
        st.title("🎨 Ad Creator")
        st.caption(f"👤 {user_email}")

        st.divider()

        # -----------------------------
        # Menu Definition
        # -----------------------------
        menu = {
            "🏠 홈": "home",
            "📸 인스타 광고 만들기": "instagram_generate",
            "📚 인스타 광고 이력": "instagram_history",
        }

        if is_admin():
            menu["🧑‍💼 관리자 대시보드"] = "admin_overview"

        selected_label = st.radio(
            "메뉴",
            list(menu.keys()),
            label_visibility="collapsed",
        )

        st.divider()

        if st.button("🔓 로그아웃", use_container_width=True):
            logout()
            st.rerun()

        return menu[selected_label]
