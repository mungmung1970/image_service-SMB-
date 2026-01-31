# ad_creator_platform/app/core/guards.py
"""
Guards (Pre-condition / Authorization Checks)

역할:
- 로그인 여부 확인
- 관리자 권한 확인
- 기능 사용 가능 여부 판단
- 위험한 요청 사전 차단
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from app.core.config import ADMIN_EMAILS
from app.core.auth import current_user_email


# -----------------------------
# Auth Guards
# -----------------------------
def require_login() -> str:
    """
    로그인 필수 가드

    Returns:
        로그인된 사용자 이메일

    Raises:
        RuntimeError: 로그인되지 않은 경우
    """
    email = current_user_email()
    if not email:
        raise RuntimeError("로그인이 필요합니다.")
    return email


def is_admin(email: Optional[str] = None) -> bool:
    """
    관리자 여부 확인
    """
    email = email or current_user_email()
    if not email:
        return False
    return email.lower() in ADMIN_EMAILS


def require_admin(email: Optional[str] = None) -> str:
    """
    관리자 권한 필수 가드

    Returns:
        관리자 이메일

    Raises:
        PermissionError: 관리자가 아닌 경우
    """
    email = email or current_user_email()
    if not email:
        raise PermissionError("로그인이 필요합니다.")
    if email.lower() not in ADMIN_EMAILS:
        raise PermissionError("관리자 권한이 필요합니다.")
    return email


# -----------------------------
# Feature Guards
# -----------------------------
def can_send_email() -> bool:
    """
    이메일 발송 기능 사용 가능 여부
    - SMTP 설정이 되어 있는지 확인
    """
    from app.services.email_service import _get_smtp_config

    cfg = _get_smtp_config()
    return all(cfg.values())


# -----------------------------
# Path / File Guards
# -----------------------------
def ensure_safe_path(
    base_dir: Path,
    target_path: Path,
) -> Path:
    """
    Path Traversal 방지

    Args:
        base_dir: 기준 디렉토리
        target_path: 접근하려는 경로

    Returns:
        검증된 절대 경로

    Raises:
        ValueError: base_dir 밖을 접근하려는 경우
    """
    base_dir = base_dir.resolve()
    target_path = target_path.resolve()

    if not str(target_path).startswith(str(base_dir)):
        raise ValueError("허용되지 않은 파일 접근입니다.")

    return target_path
