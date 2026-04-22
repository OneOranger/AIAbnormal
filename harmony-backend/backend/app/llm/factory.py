"""LLM Provider 工厂 — 按 .env 自动选择,支持显式覆盖。
优先级: settings.LLM_PROVIDER (显式) > OPENAI > QWEN > DEEPSEEK > MOCK
"""
from functools import lru_cache
from loguru import logger

from app.config import settings
from .base import BaseLLMProvider
from .openai_provider import OpenAICompatibleProvider
from .qwen_provider import QwenProvider
from .deepseek_provider import DeepSeekProvider
from .mock_provider import MockProvider


def _build_openai() -> BaseLLMProvider:
    return OpenAICompatibleProvider(
        api_key=settings.OPENAI_API_KEY or "",
        base_url=settings.OPENAI_BASE_URL,
        default_model=settings.OPENAI_MODEL,
        name="openai",
    )


def _build_qwen() -> BaseLLMProvider:
    return QwenProvider(api_key=settings.DASHSCOPE_API_KEY or "", model=settings.QWEN_MODEL)


def _build_deepseek() -> BaseLLMProvider:
    return DeepSeekProvider(
        api_key=settings.DEEPSEEK_API_KEY or "",
        base_url=settings.DEEPSEEK_BASE_URL,
        model=settings.DEEPSEEK_MODEL,
    )


@lru_cache(maxsize=1)
def get_llm() -> BaseLLMProvider:
    """返回当前激活的 LLM Provider(单例)。"""
    explicit = (settings.LLM_PROVIDER or "").strip().lower()
    if explicit == "openai" and settings.OPENAI_API_KEY:
        logger.info("LLM Provider = OpenAI (explicit)")
        return _build_openai()
    if explicit == "qwen" and settings.DASHSCOPE_API_KEY:
        logger.info("LLM Provider = Qwen (explicit)")
        return _build_qwen()
    if explicit == "deepseek" and settings.DEEPSEEK_API_KEY:
        logger.info("LLM Provider = DeepSeek (explicit)")
        return _build_deepseek()
    if explicit == "mock":
        logger.warning("LLM Provider = Mock (explicit)")
        return MockProvider()

    # 自动检测
    if settings.OPENAI_API_KEY:
        logger.info("LLM Provider = OpenAI (auto)")
        return _build_openai()
    if settings.DASHSCOPE_API_KEY:
        logger.info("LLM Provider = Qwen (auto)")
        return _build_qwen()
    if settings.DEEPSEEK_API_KEY:
        logger.info("LLM Provider = DeepSeek (auto)")
        return _build_deepseek()

    logger.warning("⚠ 无 LLM API Key,使用 Mock Provider — 在 .env 配置任一 Key 即可启用真实推理")
    return MockProvider()


def get_active_provider_name() -> str:
    return get_llm().name
