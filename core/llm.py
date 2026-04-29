"""
core/llm.py
Khởi tạo Gemini LLM qua langchain-google-genai
"""
import os
import logging
from functools import lru_cache
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_llm():
    """Trả về Gemini LLM instance (singleton)."""
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        import yaml

        with open("config/settings.yaml", "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)

        llm_cfg = cfg.get("llm", {})
        api_key = os.getenv("GOOGLE_API_KEY", "")

        if not api_key:
            logger.warning("GOOGLE_API_KEY chưa được cấu hình — LLM sẽ không hoạt động.")
            return None

        llm = ChatGoogleGenerativeAI(
            model=llm_cfg.get("model", "gemma-3-27b-it"),
            temperature=llm_cfg.get("temperature", 0.2),
            max_tokens=llm_cfg.get("max_tokens", 2048),
            google_api_key=api_key,
        )
        logger.info("LLM Gemini khởi tạo thành công.")
        return llm

    except Exception as e:
        logger.error(f"Lỗi khởi tạo LLM: {e}")
        return None


def check_llm_available() -> bool:
    """Kiểm tra LLM có sẵn sàng không."""
    return get_llm() is not None
