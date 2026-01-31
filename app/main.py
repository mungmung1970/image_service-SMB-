# ad_creator_platform/app/main.py
"""
Ad Creator Platform - Main Entry (Streamlit)

역할:
- Streamlit 앱 단일 엔트리 포인트
- 로그인 UI 제공
- 글로벌 네비게이션(navbar) 처리
- 페이지 라우팅
"""

from __future__ import annotations

# -----------------------------
# Path Fix (IMPORTANT)
# -----------------------------
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]  # ad_creator_platform/
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# -----------------------------
# Imports
# -----------------------------
import streamlit as st

from app.core.auth import login_gate, current_user_email
from ui.components.navbar import render_navbar


# -----------------------------
# Streamlit Config
# -----------------------------
st.set_page_config(
    page_title="Ad Creator Platform",
    page_icon="🎨",
    layout="wide",
)


# -----------------------------
# Main App
# -----------------------------
def main():
    # -----------------------------
    # Login UI (ENTRY POINT)
    # -----------------------------
    login_gate(
        title="📧 Ad Creator 로그인",
        description="이메일로 로그인하면 광고 생성 이력을 다시 불러올 수 있습니다.",
    )

    user_email = current_user_email()
    assert user_email is not None

    # -----------------------------
    # Navbar
    # -----------------------------
    selected = render_navbar()

    # -----------------------------
    # Page Routing
    # -----------------------------
    if selected == "instagram_generate":
        from modules.instagram.pages.generate import run

        run()

    elif selected == "instagram_history":
        from modules.instagram.pages.history import run

        run()

    elif selected == "admin_overview":
        from modules.admin.pages.overview import run

        run()

    else:
        # Home
        st.title("🏠 Ad Creator Platform")
        st.caption("소상공인을 위한 AI 광고 콘텐츠 생성 서비스")

        st.markdown(
            f"""
### 👋 환영합니다!
**{user_email}** 님,

좌측 메뉴에서 원하는 기능을 선택해 주세요.

---

#### 📸 인스타 광고
- 상품 정보 입력만으로 광고 이미지 자동 생성
- 생성 이력 관리 및 재다운로드 지원

#### 🧑‍💼 관리자 기능
- 전체 사용자 및 광고 생성 현황 확인
- 시스템 로그 모니터링
"""
        )


# -----------------------------
# Run
# -----------------------------
if __name__ == "__main__":
    main()
