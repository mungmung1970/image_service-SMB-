import streamlit as st

st.set_page_config(page_title="ChatGPT-style UI", layout="centered")

# -----------------------------
# 1. 세션 상태 초기화
# -----------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "task_mode" not in st.session_state:
    st.session_state.task_mode = "문서 생성"

# -----------------------------
# 2. 작업 모드 정의
# -----------------------------
TASK_CONFIG = {
    "문서 생성": {
        "placeholder": "작성할 문서의 주제나 요구사항을 입력하세요",
        "system_hint": "문서를 생성합니다."
    },
    "번역": {
        "placeholder": "번역할 텍스트를 입력하세요",
        "system_hint": "번역을 수행합니다."
    },
    "요약": {
        "placeholder": "요약할 내용을 입력하세요",
        "system_hint": "요약을 수행합니다."
    },
    "코드 작성": {
        "placeholder": "작성할 코드에 대한 설명을 입력하세요",
        "system_hint": "코드를 생성합니다."
    },
}

# -----------------------------
# 3. 기존 대화 렌더링 (말풍선)
# -----------------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# -----------------------------
# 4. 하단 작업 선택 바 (ChatGPT 스타일)
# -----------------------------
cols = st.columns(len(TASK_CONFIG))

for col, mode in zip(cols, TASK_CONFIG.keys()):
    with col:
        if st.button(
            mode,
            use_container_width=True,
            type="primary" if st.session_state.task_mode == mode else "secondary",
        ):
            st.session_state.task_mode = mode

# -----------------------------
# 5. 선택에 따라 placeholder 변경
# -----------------------------
user_input = st.chat_input(
    placeholder=TASK_CONFIG[st.session_state.task_mode]["placeholder"]
)

# -----------------------------
# 6. 입력 처리
# -----------------------------
if user_input:
    # 사용자 메시지 저장
    st.session_state.messages.append(
        {"role": "user", "content": user_input}
    )

    # 사용자 말풍선
    with st.chat_message("user"):
        st.markdown(user_input)

    # (예시용) 어시스턴트 응답
    assistant_response = (
        f"🛠 선택된 작업: **{st.session_state.task_mode}**\n\n"
        f"{TASK_CONFIG[st.session_state.task_mode]['system_hint']}\n\n"
        f"입력 내용:\n{user_input}"
    )

    st.session_state.messages.append(
        {"role": "assistant", "content": assistant_response}
    )

    with st.chat_message("assistant"):
        st.markdown(assistant_response)
