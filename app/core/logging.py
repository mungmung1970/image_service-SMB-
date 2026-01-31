# ad_creator_platform/app/core/logging.py
"""
Application Logging

역할:
- 사용자 행동 로그
- 에러 로그
- 파일 기반 로깅 (PC 환경)
"""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

from app.core.config import PROJECT_ROOT


# -----------------------------
# Log Paths
# -----------------------------
LOG_DIR = PROJECT_ROOT / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

APP_LOG_PATH = LOG_DIR / "app.log"
ERROR_LOG_PATH = LOG_DIR / "error.log"


# -----------------------------
# Formatters
# -----------------------------
DEFAULT_FORMAT = (
    "%(asctime)s | %(levelname)s | %(name)s | "
    "user=%(user)s | action=%(action)s | %(message)s"
)

DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


class ContextFilter(logging.Filter):
    """
    로그에 user / action 필드를 강제로 주입하기 위한 Filter
    """

    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "user"):
            record.user = "-"
        if not hasattr(record, "action"):
            record.action = "-"
        return True


# -----------------------------
# Logger Factory
# -----------------------------
def _create_logger(
    name: str,
    level: int,
    file_path: Path,
) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if logger.handlers:
        return logger  # 중복 핸들러 방지

    handler = RotatingFileHandler(
        file_path,
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=3,
        encoding="utf-8",
    )

    formatter = logging.Formatter(DEFAULT_FORMAT, DATE_FORMAT)
    handler.setFormatter(formatter)
    handler.addFilter(ContextFilter())

    logger.addHandler(handler)
    logger.propagate = False
    return logger


# -----------------------------
# Public Loggers
# -----------------------------
app_logger = _create_logger(
    name="app",
    level=logging.INFO,
    file_path=APP_LOG_PATH,
)

error_logger = _create_logger(
    name="error",
    level=logging.ERROR,
    file_path=ERROR_LOG_PATH,
)


# -----------------------------
# Helper Functions
# -----------------------------
def log_action(
    *,
    message: str,
    user: Optional[str] = None,
    action: Optional[str] = None,
) -> None:
    """
    일반 사용자 행동 로그
    """
    app_logger.info(
        message,
        extra={
            "user": user or "-",
            "action": action or "-",
        },
    )


def log_error(
    *,
    message: str,
    user: Optional[str] = None,
    action: Optional[str] = None,
    exc: Optional[Exception] = None,
) -> None:
    """
    에러 로그
    """
    error_logger.error(
        message,
        extra={
            "user": user or "-",
            "action": action or "-",
        },
        exc_info=exc,
    )


def read_recent_logs(limit: int = 50) -> list[str]:
    if not LOG_FILE.exists():
        return []

    with open(LOG_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()

    return lines[-limit:]
