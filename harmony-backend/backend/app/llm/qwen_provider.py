"""Qwen (通义千问 / DashScope) — 通过 OpenAI 兼容端点接入。"""
from .openai_provider import OpenAICompatibleProvider


class QwenProvider(OpenAICompatibleProvider):
    """https://help.aliyun.com/zh/dashscope/developer-reference/compatibility-of-openai-with-dashscope"""

    def __init__(self, *, api_key: str, model: str = "qwen-max"):
        super().__init__(
            api_key=api_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            default_model=model,
            name="qwen",
        )
