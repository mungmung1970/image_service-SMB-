# ad_creator_platform/app/services/email_service.py
"""
Email Service (SMTP)

역할:
- 생성된 광고 이미지를 이메일로 발송
- Gmail SMTP 기준 구현
- Streamlit / Pipeline 어디서든 호출 가능

필수 환경변수 (.env):
SMTP_HOST
SMTP_PORT
SMTP_USER
SMTP_PASS
SMTP_FROM
"""

from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage
from pathlib import Path


# -----------------------------
# Config Loader
# -----------------------------
def _get_smtp_config() -> dict:
    return {
        "host": os.getenv("SMTP_HOST", ""),
        "port": int(os.getenv("SMTP_PORT", "587")),
        "user": os.getenv("SMTP_USER", ""),
        "password": os.getenv("SMTP_PASS", ""),
        "from_email": os.getenv("SMTP_FROM", ""),
    }


def _validate_config(cfg: dict) -> None:
    missing = [k for k, v in cfg.items() if not v]
    if missing:
        raise RuntimeError(f"SMTP 설정이 누락되었습니다: {', '.join(missing)}")


# -----------------------------
# Public API
# -----------------------------
def send_image_email(
    *,
    to_email: str,
    subject: str,
    body_text: str,
    image_path: str | Path,
) -> None:
    """
    이미지 첨부 이메일 발송

    Args:
        to_email: 수신자 이메일
        subject: 이메일 제목
        body_text: 본문 텍스트
        image_path: 첨부할 이미지 경로 (png)
    """
    cfg = _get_smtp_config()
    _validate_config(cfg)

    image_path = Path(image_path)
    if not image_path.exists():
        raise FileNotFoundError(f"이미지 파일이 존재하지 않습니다: {image_path}")

    # -----------------------------
    # Build Email
    # -----------------------------
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = cfg["from_email"]
    msg["To"] = to_email
    msg.set_content(body_text)

    with open(image_path, "rb") as f:
        img_data = f.read()

    msg.add_attachment(
        img_data,
        maintype="image",
        subtype="png",
        filename=image_path.name,
    )

    # -----------------------------
    # Send
    # -----------------------------
    with smtplib.SMTP(cfg["host"], cfg["port"]) as server:
        server.starttls()
        server.login(cfg["user"], cfg["password"])
        server.send_message(msg)
