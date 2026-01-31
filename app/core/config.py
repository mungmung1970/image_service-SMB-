# ad_creator_platform/app/core/config.py
"""
Global App Configuration

- 환경변수(.env) 기반 설정 로딩
- 앱 전역에서 참조하는 상수 정의
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import List

from dotenv import load_dotenv


# -----------------------------
# Environment
# -----------------------------
# Streamlit 실행 시 한 번만 로딩되면 충분
load_dotenv()


# -----------------------------
# Project Paths
# -----------------------------
PROJECT_ROOT: Path = Path(__file__).resolve().parents[2]

APP_DIR: Path = PROJECT_ROOT / "app"
MODULES_DIR: Path = PROJECT_ROOT / "modules"
ASSETS_DIR: Path = PROJECT_ROOT / "assets"
OUTPUTS_DIR: Path = PROJECT_ROOT / "outputs"

FONTS_DIR: Path = ASSETS_DIR / "fonts"


# -----------------------------
# App Info
# -----------------------------
APP_NAME: str = os.getenv("APP_NAME", "Ad Creator Platform")
ENV: str = os.getenv("ENV", "dev")  # dev | prod


# -----------------------------
# Admin
# -----------------------------
def _parse_admin_emails(raw: str) -> List[str]:
    return [e.strip().lower() for e in raw.split(",") if e.strip()]


ADMIN_EMAILS: List[str] = _parse_admin_emails(os.getenv("ADMIN_EMAILS", ""))


# -----------------------------
# Image Generation
# -----------------------------
IMAGE_PROVIDER: str = os.getenv("IMAGE_PROVIDER", "mock").lower()

# 기본 이미지 사이즈
INSTAGRAM_FEED_SIZE = (1080, 1080)


# -----------------------------
# SMTP (Email)
# -----------------------------
SMTP_HOST: str = os.getenv("SMTP_HOST", "")
SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER: str = os.getenv("SMTP_USER", "")
SMTP_FROM: str = os.getenv("SMTP_FROM", "")

# ⚠️ SMTP_PASS는 보안상 여기서 변수로 노출하지 않고
# email_service에서 직접 os.getenv으로 접근하는 것도 권장


# -----------------------------
# Validation / Debug
# -----------------------------
def print_config_summary() -> None:
    """
    디버깅용: 현재 설정 요약 출력
    """
    print("=== App Config Summary ===")
    print(f"APP_NAME: {APP_NAME}")
    print(f"ENV: {ENV}")
    print(f"IMAGE_PROVIDER: {IMAGE_PROVIDER}")
    print(f"ADMIN_EMAILS: {ADMIN_EMAILS}")
    print(f"OUTPUTS_DIR: {OUTPUTS_DIR}")
