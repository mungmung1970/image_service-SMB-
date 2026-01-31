"""
Local File System Storage

역할:
- 사용자별 파일 저장 (outputs/users/{email}/...)
- 생성 이미지 저장
- 업로드 파일 저장
- 생성 이력(history.json) 관리
- 상대 경로 ↔ 절대 경로 변환의 단일 진실(Single Source of Truth)
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

from PIL import Image


# ======================================================
# Base Directories (⭐ 단일 기준)
# ======================================================
BASE_OUTPUT_DIR = Path("outputs")
USERS_DIR = BASE_OUTPUT_DIR / "users"

BASE_OUTPUT_DIR.mkdir(exist_ok=True)
USERS_DIR.mkdir(exist_ok=True)


# ======================================================
# Utils
# ======================================================
def _safe_email(email: str) -> str:
    """
    이메일을 파일 경로에 안전한 문자열로 변환
    """
    return email.lower().replace("@", "_at_").replace(".", "_dot_")


def _user_root(email: str) -> Path:
    root = USERS_DIR / _safe_email(email)
    root.mkdir(parents=True, exist_ok=True)
    return root


def generate_image_id(prefix: str = "img") -> str:
    return f"{prefix}_{uuid.uuid4().hex}"


# ======================================================
# Image Save / Load
# ======================================================
def save_image(
    *,
    email: str,
    pil_image: Image.Image,
    image_id: str,
    ext: str = "png",
) -> str:
    """
    생성된 이미지를 저장

    Returns:
        사용자 기준 상대 경로 (예: images/xxx.png)
    """
    user_root = _user_root(email)
    images_dir = user_root / "images"
    images_dir.mkdir(exist_ok=True)

    filename = f"{image_id}.{ext}"
    file_path = images_dir / filename

    pil_image.save(file_path)

    return f"images/{filename}"


def save_uploaded_file(
    *,
    email: str,
    uploaded_file,
    subdir: str = "uploads",
) -> str:
    """
    Streamlit file_uploader로 받은 파일 저장

    Returns:
        사용자 기준 상대 경로 (예: uploads/xxx.png)
    """
    user_root = _user_root(email)
    upload_dir = user_root / subdir
    upload_dir.mkdir(exist_ok=True)

    ext = Path(uploaded_file.name).suffix.lower()
    filename = f"{uuid.uuid4().hex}{ext}"
    file_path = upload_dir / filename

    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    return f"{subdir}/{filename}"


def resolve_image_path(*, email: str, relative_path: str) -> Path:
    """
    사용자 기준 상대 경로 → 절대 경로 변환
    """
    return _user_root(email) / relative_path


# ======================================================
# History (JSON)
# ======================================================
def _history_file(email: str) -> Path:
    return _user_root(email) / "history.json"


def load_history(email: str) -> List[Dict[str, Any]]:
    history_path = _history_file(email)

    if not history_path.exists():
        return []

    with open(history_path, "r", encoding="utf-8") as f:
        return json.load(f)


def append_history(
    *,
    email: str,
    record: Dict[str, Any],
) -> None:
    """
    생성 이력 추가 (자동 timestamp 포함)
    """
    history = load_history(email)

    record = dict(record)
    record["created_at"] = datetime.utcnow().isoformat()

    history.append(record)

    with open(_history_file(email), "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)
