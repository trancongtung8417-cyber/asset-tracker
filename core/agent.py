"""
core/agent.py
LangGraph workflow — AI assistant cho Asset Tracker
"""
import logging
from typing import TypedDict, Annotated
from core.llm import get_llm
from core.memory import format_history_for_llm

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Bạn là trợ lý AI chuyên quản lý tài sản văn phòng cho doanh nghiệp Việt Nam.
Bạn giúp người dùng:
- Tra cứu thông tin tài sản, thiết bị
- Kiểm tra tình trạng bảo hành
- Tư vấn quy trình bàn giao / thu hồi thiết bị
- Phân tích báo cáo tài sản
- Đề xuất xử lý tài sản hỏng hoặc sắp hết bảo hành

Trả lời BẰNG TIẾNG VIỆT, ngắn gọn, chuyên nghiệp.
Nếu không chắc, hãy nói rõ và đề nghị người dùng kiểm tra lại dữ liệu.
Context tài sản hiện tại: {asset_context}
"""


class AgentState(TypedDict):
    messages: list
    asset_context: str
    response: str
    error: str


def build_graph():
    """Xây dựng LangGraph workflow."""
    try:
        from langgraph.graph import StateGraph, END

        def chat_node(state: AgentState) -> AgentState:
            """Node xử lý tin nhắn người dùng."""
            try:
                llm = get_llm()
                if llm is None:
                    return {**state, "response": "⚠️ LLM chưa được cấu hình. Vui lòng kiểm tra GOOGLE_API_KEY.", "error": ""}

                from langchain_core.messages import SystemMessage
                system = SystemMessage(
                    content=SYSTEM_PROMPT.format(
                        asset_context=state.get("asset_context", "Không có dữ liệu")
                    )
                )
                all_messages = [system] + state.get("messages", [])
                result = llm.invoke(all_messages)
                return {**state, "response": result.content, "error": ""}

            except Exception as e:
                logger.error(f"Lỗi chat_node: {e}")
                return {**state, "response": "", "error": "Hệ thống đang xử lý, vui lòng thử lại."}

        graph = StateGraph(AgentState)
        graph.add_node("chat", chat_node)
        graph.set_entry_point("chat")
        graph.add_edge("chat", END)
        return graph.compile()

    except Exception as e:
        logger.error(f"Lỗi build_graph: {e}")
        return None


_graph = None


def get_agent_response(user_message: str, asset_context: str = "") -> str:
    """Gọi agent và trả về phản hồi."""
    global _graph
    try:
        if _graph is None:
            _graph = build_graph()
        if _graph is None:
            return "Hệ thống đang xử lý, vui lòng thử lại."

        from langchain_core.messages import HumanMessage
        history = format_history_for_llm()
        history.append(HumanMessage(content=user_message))

        result = _graph.invoke({
            "messages": history,
            "asset_context": asset_context,
            "response": "",
            "error": "",
        })

        if result.get("error"):
            return result["error"]
        return result.get("response", "Không có phản hồi.")

    except Exception as e:
        logger.error(f"Lỗi get_agent_response: {e}")
        return "Hệ thống đang xử lý, vui lòng thử lại."
