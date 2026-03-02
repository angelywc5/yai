"""Gemini 模型适配器。"""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator

from google import genai
from google.genai import types

from src.core.model_provider import ModelConfig, ModelProvider, StreamChunk
from src.core.schemas import ModelTier

logger = logging.getLogger(__name__)


class GeminiProvider(ModelProvider):
    """
    Google Gemini 模型适配器。

    通过 google-genai SDK 实现流式对话和 token 计数。
    """

    def __init__(
        self,
        api_key: str,
        speed_model: str,
        pro_model: str,
        elite_model: str,
        timeout: int = 30,
    ):
        """
        初始化 Gemini 提供者。

        Args:
            api_key: Gemini API 密钥
            speed_model: Speed 档位模型名
            pro_model: Pro 档位模型名
            elite_model: Elite 档位模型名
            timeout: 请求超时秒数
        """
        self._client = genai.Client(api_key=api_key)
        self._model_map: dict[ModelTier, str] = {
            ModelTier.SPEED: speed_model,
            ModelTier.PRO: pro_model,
            ModelTier.ELITE: elite_model,
        }
        self._timeout = timeout

    async def stream_chat(
        self,
        messages: list[dict[str, str]],
        config: ModelConfig,
    ) -> AsyncGenerator[StreamChunk, None]:
        """
        流式对话。

        1. 将 messages 转换为 Gemini SDK 格式
        2. 调用 generate_content_async(stream=True)
        3. 逐 chunk yield StreamChunk
        4. 最后一个 chunk 设置 is_final=True + total_tokens
        """
        model_name = self._model_map.get(config.tier, config.model_name)
        system_instruction, contents = self._convert_messages(messages)

        gen_config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.85,
            top_p=0.95,
        )

        total_tokens = 0
        accumulated_text = ""

        try:
            async for response in self._client.aio.models.generate_content_stream(
                model=model_name,
                contents=contents,
                config=gen_config,
            ):
                if response.text:
                    accumulated_text += response.text
                    yield StreamChunk(content=response.text)

                if response.usage_metadata:
                    total_tokens = (
                        (response.usage_metadata.prompt_token_count or 0)
                        + (response.usage_metadata.candidates_token_count or 0)
                    )

            yield StreamChunk(
                content="",
                is_final=True,
                total_tokens=total_tokens,
            )
        except Exception as e:
            logger.error(f"Gemini 流式调用异常: {e}")
            raise

    async def count_tokens(self, text: str, model_name: str) -> int:
        """使用 Gemini count_tokens API。"""
        try:
            response = await self._client.aio.models.count_tokens(
                model=model_name,
                contents=text,
            )
            return response.total_tokens or 0
        except Exception as e:
            logger.warning(f"Token 计数失败: {e}")
            return len(text) // 4

    def _convert_messages(
        self, messages: list[dict[str, str]]
    ) -> tuple[str | None, list[types.Content]]:
        """
        将统一格式转换为 Gemini 格式。

        Args:
            messages: [{"role": "system/user/assistant", "content": "..."}]

        Returns:
            (system_instruction, contents)
        """
        system_instruction = None
        contents: list[types.Content] = []

        for msg in messages:
            role = msg["role"]
            content = msg["content"]

            if role == "system":
                if system_instruction is None:
                    system_instruction = content
                else:
                    system_instruction += "\n\n" + content
            elif role == "user":
                contents.append(
                    types.Content(
                        role="user",
                        parts=[types.Part.from_text(text=content)],
                    )
                )
            elif role == "assistant":
                contents.append(
                    types.Content(
                        role="model",
                        parts=[types.Part.from_text(text=content)],
                    )
                )

        return system_instruction, contents
