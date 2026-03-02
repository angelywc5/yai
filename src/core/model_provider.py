"""AI 模型抽象层 — 定义统一接口和数据类。"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from dataclasses import dataclass

from src.core.schemas import ModelTier


@dataclass(frozen=True)
class ModelConfig:
    """模型调用配置。"""

    tier: ModelTier
    model_name: str
    credits_per_1k_tokens: int


@dataclass
class StreamChunk:
    """流式输出的单个片段。"""

    content: str
    is_final: bool = False
    total_tokens: int = 0


class ModelProvider(ABC):
    """AI 模型抽象基类。"""

    @abstractmethod
    async def stream_chat(
        self,
        messages: list[dict[str, str]],
        config: ModelConfig,
    ) -> AsyncGenerator[StreamChunk, None]:
        """
        流式对话，逐 chunk yield。

        Args:
            messages: 消息列表 [{"role": "system/user/assistant", "content": "..."}]
            config: 模型配置

        Yields:
            StreamChunk: 流式片段，最后一个 chunk 的 is_final=True
        """
        ...

    @abstractmethod
    async def count_tokens(self, text: str, model_name: str) -> int:
        """
        计算文本的 token 数量。

        Args:
            text: 待计算文本
            model_name: 模型名称

        Returns:
            token 数量
        """
        ...


class ModelProviderFactory:
    """模型提供者工厂。"""

    def __init__(self) -> None:
        self._providers: dict[str, ModelProvider] = {}
        self._default_name: str = ""

    def register(self, name: str, provider: ModelProvider) -> None:
        """注册模型提供者。"""
        self._providers[name] = provider
        if not self._default_name:
            self._default_name = name

    def get(self, name: str) -> ModelProvider:
        """获取指定模型提供者。"""
        if name not in self._providers:
            raise KeyError(f"模型提供者不存在: {name}")
        return self._providers[name]

    def get_default(self) -> ModelProvider:
        """获取默认模型提供者。"""
        if not self._default_name:
            raise RuntimeError("未注册任何模型提供者")
        return self._providers[self._default_name]
