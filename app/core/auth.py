# ad_creator_platform/app/core/auth.py
"""
Auth / Identity module (Streamlit-friendly)

목표:
- '인증(Authentication)'이 아닌 '식별(Identification)'
- 이메일 기반 로그인
- Streamlit session_state 사용
- 관리자/일반 사용자 구분 가능
"""

from __future__ import annotations  # ✅ 반드시 여기!

import os
import re
from typing import List

import streamlit as st

from app.core.logging import log_action


# -----------------------------
# Constants & Config
# -----------------------------
EMAIL_REGEX = re.compile(r"[^@]+@[^@]+\.[^@]+")


def _get_admin_emails() -> List[str]:
    """
    .env 또는 환경변수의 ADMIN_EMAILS를 읽어옵니다.
    예: ADMIN_EMAILS=admin@example.com,owner@example.com
    """
    raw = os.getenv("ADMIN_EMAILS", "")
    return [e.strip().lower() for e in raw.split(",") if e.strip()]


# -----------------------------
# Session Helpers
# -----------------------------
def init_auth_state() -> None:
    """
    Streamlit session_state 초기화
    """
    if "user_email" not in st.session_state:
        st.session_state.user_email = None


def is_logged_in() -> bool:
    init_auth_state()
    return st.session_state.user_email is not None


def current_user_email() -> str | None:
    init_auth_state()
    return st.session_state.user_email


# -----------------------------
# Validation
# -----------------------------
def is_valid_email(email: str) -> bool:
    return bool(email) and bool(EMAIL_REGEX.match(email))


# -----------------------------
# Login / Logout
# -----------------------------
def login(email: str) -> bool:
    if not is_valid_email(email):
        return False

    email = email.strip().lower()
    st.session_state.user_email = email

    log_action(
        message="User logged in",
        user=email,
        action="login",
    )

    return True


def logout() -> None:
    """
    세션 로그아웃
    """
    st.session_state.user_email = None


# -----------------------------
# Guards (UI Helper)
# -----------------------------
def login_gate(
    title: str = "📧 이메일로 시작하기",
    description: str = "이메일을 입력하면 이전에 생성한 이력을 다시 불러올 수 있습니다.",
) -> None:
    """
    로그인되지 않았으면 로그인 화면을 보여주고,
    로그인되었으면 그대로 통과합니다.
    """
    init_auth_state()

    if is_logged_in():
        return

    st.title(title)
    st.caption(description)

    email = st.text_input("이메일 주소", placeholder="user@example.com")

    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("시작하기", use_container_width=True):
            if not login(email):
                st.error("올바른 이메일 주소를 입력하세요.")
            else:
                st.rerun()

    with col2:
        if st.button("초기화", use_container_width=True):
            logout()
            st.rerun()

    # 로그인 전에는 이후 코드 실행 방지
    st.stop()


def logout_button(label: str = "로그아웃") -> None:
    """
    사이드바 또는 헤더에 배치하는 로그아웃 버튼
    """
    if st.button(label):
        logout()
        st.rerun()


# -----------------------------
# Role / Permission
# -----------------------------
def is_admin() -> bool:
    """
    현재 사용자가 관리자 이메일인지 확인
    """
    email = current_user_email()
    if not email:
        return False

    admin_emails = _get_admin_emails()
    return email in admin_emails
