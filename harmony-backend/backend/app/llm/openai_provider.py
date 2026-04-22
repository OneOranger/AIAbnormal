"""OpenAI 兼容 Provider — 用于 OpenAI / Qwen(DashScope OpenAI 兼容端点) / DeepSeek。
他们三家都遵循 OpenAI Chat Completions API。
"""
import time
import json
from typing import AsyncIterator, List, Optional, Dict, Any
import httpx
from loguru import logger

from .base import BaseLLMProvider, LLMMessage, LLMResponse


class OpenAICompatibleProvider(BaseLLMProvider):
    def __init__(self, *, api_key: str, base_url: str, default_model: str, name: str):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.default_model = default_model
        self.name = name
        self._client = httpx.AsyncClient(timeout=httpx.Timeout(60.0))

    async def chat(
        self,
        messages: List[LLMMessage],
        *,
        model: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 2048,
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
    ) -> LLMResponse:
        model = model or self.default_model
        body = {
            "model": model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if tools:
            body["tools"] = tools
            body["tool_choice"] = kwargs.get("tool_choice", "auto")

        t0 = time.time()
        r = await self._client.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            json=body,
        )
        latency = int((time.time() - t0) * 1000)
        if r.status_code != 200:
            logger.error(f"[{self.name}] {r.status_code}: {r.text[:300]}")
            raise RuntimeError(f"LLM API error {r.status_code}: {r.text[:200]}")

        data = r.json()
        choice = data["choices"][0]["message"]
        usage = data.get("usage", {})
        return LLMResponse(
            content=choice.get("content") or "",
            tokens_in=usage.get("prompt_tokens", 0),
            tokens_out=usage.get("completion_tokens", 0),
            latency_ms=latency,
            model=model,
            provider=self.name,
            raw=data,
        )

    async def chat_stream(
        self,
        messages: List[LLMMessage],
        *,
        model: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 2048,
        **kwargs,
    ) -> AsyncIterator[str]:
        model = model or self.default_model
        body = {
            "model": model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }
        async with self._client.stream(
            "POST",
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            json=body,
        ) as r:
            if r.status_code != 200:
                txt = await r.aread()
                raise RuntimeError(f"LLM stream error {r.status_code}: {txt[:200]}")
            async for line in r.aiter_lines():
                if not line or not line.startswith("data: "):
                    continue
                payload = line[6:].strip()
                if payload == "[DONE]":
                    break
                try:
                    obj = json.loads(payload)
                    delta = obj["choices"][0]["delta"].get("content")
                    if delta:
                        yield delta
                except Exception:
                    continue
