# ad_creator_platform/modules/admin/pages/overview.py
"""
Admin Overview Page (Streamlit)

역할:
- 관리자 전용 대시보드
- 전체 서비스 상태 요약
- 로그 및 사용자 활동 관측
"""

from __future__ import annotations

from pathlib import Path
import streamlit as st

from app.core.guards import require_admin
from app.core.config import OUTPUTS_DIR, LOG_FILE
from app.storage.local_fs import load_all_histories
from app.core.logging import read_recent_logs


# -----------------------------
# Page Entry
# -----------------------------
def run():
    # -----------------------------
    # Admin Guard
    # -----------------------------
    try:
        admin_email = require_admin()
    except PermissionError as e:
        st.error(str(e))
        st.stop()

    st.title("🧑‍💼 관리자 대시보드")
    st.caption(f"관리자 계정: {admin_email}")

    st.divider()

    # -----------------------------
    # Load Global History
    # -----------------------------
    try:
        histories = load_all_histories()
    except Exception as e:
        st.error("사용자 이력을 불러오는 중 오류가 발생했습니다.")
        st.stop()

    total_users = len(histories)
    total_ads = sum(len(h) for h in histories.values())

    # -----------------------------
    # KPI Summary
    # -----------------------------
    col1, col2 = st.columns(2)

    col1.metric("👥 전체 사용자 수", total_users)
    col2.metric("🖼️ 전체 광고 생성 수", total_ads)

    st.divider()

    # -----------------------------
    # Recent Activity
    # -----------------------------
    st.subheader("🕒 최근 광고 생성 이력")

    recent_items = []
    for email, items in histories.items():
        for item in items:
            item_copy = item.copy()
            item_copy["user_email"] = email
            recent_items.append(item_copy)

    # 최신순 정렬
    recent_items = sorted(
        recent_items,
        key=lambda x: x.get("created_at", ""),
        reverse=True,
    )[:10]

    if not recent_items:
        st.info("아직 생성된 광고가 없습니다.")
    else:
        for idx, item in enumerate(recent_items, start=1):
            with st.container(border=True):
                st.markdown(
                    f"""
**{idx}. {item.get('ad_type')}**  
- 사용자: `{item.get('user_email')}`  
- 상품: {item.get('product', '-')}  
- 톤: {item.get('tone', '-')}  
- 생성일: {item.get('created_at', '-')}
"""
                )

    st.divider()

    # -----------------------------
    # Recent Logs
    # -----------------------------
    st.subheader("📄 최근 시스템 로그")

    try:
        logs = read_recent_logs(limit=30)
    except Exception:
        st.warning("로그 파일을 불러올 수 없습니다.")
        return

    if not logs:
        st.info("로그가 없습니다.")
    else:
        for line in logs:
            st.code(line, language="text")
