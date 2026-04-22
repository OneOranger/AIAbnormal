"""LLM Provider 抽象基类。
所有 Provider 实现统一接口,业务代码不感知底层差异。
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import AsyncIterator, List, Optional, Dict, Any


@dataclass
class LLMMessage:
    role: str  # "system" | "user" | "assistant"
    content: str


@dataclass
class LLMResponse:
    content: str
    tokens_in: int = 0
    tokens_out: int = 0
    latency_ms: int = 0
    model: str = ""
    provider: str = ""
    raw: Optional[Dict[str, Any]] = field(default=None)


class BaseLLMProvider(ABC):
    """所有 LLM Provider 必须实现的接口。"""

    name: str = "base"
    default_model: str = ""

    @abstractmethod
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
        """非流式 chat 完成。"""
        ...

    @abstractmethod
    async def chat_stream(
        self,
        messages: List[LLMMessage],
        *,
        model: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 2048,
        **kwargs,
    ) -> AsyncIterator[str]:
        """流式 chat — 逐 token 返回字符串增量。"""
        ...
