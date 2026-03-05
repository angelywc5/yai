"""向量嵌入提供者 — 抽象接口和具体实现。"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod

from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

_EMBEDDING_DIMENSION = 768


class EmbeddingProvider(ABC):
    """向量嵌入抽象接口。"""

    @abstractmethod
    async def embed(self, text: str) -> list[float]:
        """
        生成单条文本的向量嵌入。

        Args:
            text: 输入文本

        Returns:
            嵌入向量
        """
        ...

    @abstractmethod
    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """
        批量生成向量嵌入。

        Args:
            texts: 输入文本列表

        Returns:
            嵌入向量列表
        """
        ...


class GeminiEmbeddingProvider(EmbeddingProvider):
    """使用 Gemini Embedding API 的向量嵌入提供者。"""

    def __init__(self, api_key: str, model_name: str):
        """
        初始化 Gemini 嵌入提供者。

        Args:
            api_key: Gemini API 密钥
            model_name: 嵌入模型名（如 gemini-embedding-001）
        """
        self._client = genai.Client(api_key=api_key)
        self._model_name = model_name
        self._config = types.EmbedContentConfig(
            output_dimensionality=_EMBEDDING_DIMENSION,
        )

    async def embed(self, text: str) -> list[float]:
        """生成单条文本的向量嵌入。"""
        try:
            result = await self._client.aio.models.embed_content(
                model=self._model_name,
                contents=text,
                config=self._config,
            )
            return list(result.embeddings[0].values)
        except Exception as e:
            logger.error(f"Gemini embedding 失败: {e}")
            raise

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """批量生成向量嵌入。"""
        try:
            result = await self._client.aio.models.embed_content(
                model=self._model_name,
                contents=texts,
                config=self._config,
            )
            return [list(emb.values) for emb in result.embeddings]
        except Exception as e:
            logger.error(f"Gemini batch embedding 失败: {e}")
            raise
