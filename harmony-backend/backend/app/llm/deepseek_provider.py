"""DeepSeek — 同样走 OpenAI 兼容协议。"""
from .openai_provider import OpenAICompatibleProvider


class DeepSeekProvider(OpenAICompatibleProvider):
    def __init__(self, *, api_key: str, base_url: str = "https://api.deepseek.com", model: str = "deepseek-chat"):
        super().__init__(
            api_key=api_key,
            base_url=base_url,
            default_model=model,
            name="deepseek",
        )
