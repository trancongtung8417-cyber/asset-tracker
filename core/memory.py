"""
core/memory.py
Lưu lịch sử hội thoại bằng plain Python list (không dùng ConversationBufferWindowMemory)
"""
import streamlit as st
import logging

logger = logging.getLogger(__name__)

MEMORY_KEY = "chat_history"
MAX_HISTORY = 20  # Giữ tối đa N cặp tin nhắn


def get_history() -> list:
    """Lấy lịch sử hội thoại từ session_state."""
    if MEMORY_KEY not in st.session_state:
        st.session_state[MEMORY_KEY] = []
    return st.session_state[MEMORY_KEY]


def add_message(role: str, content: str) -> None:
    """Thêm tin nhắn vào lịch sử."""
    history = get_history()
    history.append({"role": role, "content": content})
    # Giữ N tin nhắn gần nhất (cả user + assistant)
    if len(history) > MAX_HISTORY * 2:
        st.session_state[MEMORY_KEY] = history[-(MAX_HISTORY * 2):]
    logger.debug(f"Thêm tin nhắn [{role}]: {content[:50]}...")


def clear_history() -> None:
    """Xóa toàn bộ lịch sử hội thoại."""
    st.session_state[MEMORY_KEY] = []
    logger.info("Đã xóa lịch sử hội thoại.")


def format_history_for_llm() -> list:
    """Chuyển lịch sử sang format LangChain messages."""
    from langchain_core.messages import HumanMessage, AIMessage
    messages = []
    for msg in get_history():
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        else:
            messages.append(AIMessage(content=msg["content"]))
    return messages
