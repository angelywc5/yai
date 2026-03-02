"""YAML 响应解析器 — 解析 AI 的 YAML 格式回复。"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

import yaml

logger = logging.getLogger(__name__)


@dataclass
class YamlResponse:
    """AI YAML 响应结构。"""

    schema_version: str = "v1"
    speech: str = ""
    action: str = ""
    emotion: str = "平静"
    inner_thought: str = ""


class YamlResponseParser:
    """
    解析 AI 的 YAML 格式回复。

    支持：
    - 流式渐进式解析（从不完整文本中尝试提取 speech）
    - 最终完整解析
    - 降级处理（解析失败时将原文作为 speech）
    """

    def parse_stream(self, accumulated_text: str) -> dict | None:
        """
        尝试解析流式累积的文本为 YAML。

        流式过程中 YAML 可能不完整，返回 None 表示解析失败（继续累积）。

        Args:
            accumulated_text: 流式累积的文本

        Returns:
            解析结果字典，或 None
        """
        cleaned = self._clean_yaml_text(accumulated_text)
        try:
            result = yaml.safe_load(cleaned)
            if isinstance(result, dict) and "speech" in result:
                return result
        except yaml.YAMLError:
            pass
        return None

    def parse_final(self, text: str) -> YamlResponse:
        """
        解析最终完整的 YAML 响应。

        解析失败时降级为纯文本模式：将原文作为 speech。

        Args:
            text: 完整的 AI 回复文本

        Returns:
            YamlResponse 对象
        """
        cleaned = self._clean_yaml_text(text)
        try:
            result = yaml.safe_load(cleaned)
            if isinstance(result, dict):
                return YamlResponse(
                    schema_version=result.get("schema_version", "v1"),
                    speech=str(result.get("speech", "")).strip(),
                    action=str(result.get("action", "")).strip(),
                    emotion=str(result.get("emotion", "平静")).strip(),
                    inner_thought=str(result.get("inner_thought", "")).strip(),
                )
        except yaml.YAMLError as e:
            logger.warning(f"YAML 解析失败，降级为纯文本: {e}")

        return YamlResponse(
            speech=text.strip(),
            action="",
            emotion="平静",
            inner_thought="",
        )

    def extract_speech(self, response: YamlResponse) -> str:
        """
        提取 speech 字段作为展示给用户的文本。

        Args:
            response: YAML 响应对象

        Returns:
            speech 文本
        """
        return response.speech

    def format_for_storage(self, response: YamlResponse) -> str:
        """
        格式化为存储格式（完整 YAML 存入 Message.content）。

        Args:
            response: YAML 响应对象

        Returns:
            YAML 格式字符串
        """
        data = {
            "schema_version": response.schema_version,
            "speech": response.speech,
            "action": response.action,
            "emotion": response.emotion,
            "inner_thought": response.inner_thought,
        }
        return yaml.dump(data, allow_unicode=True, default_flow_style=False)

    def extract_speech_from_stream(self, accumulated_text: str) -> str:
        """
        从流式累积文本中尽可能提取 speech 内容。

        用于在 YAML 尚不完整时提取已有的 speech 字段内容。

        Args:
            accumulated_text: 流式累积的文本

        Returns:
            提取到的 speech 内容，提取失败返回空字符串
        """
        lines = accumulated_text.split("\n")
        in_speech = False
        speech_lines: list[str] = []

        for line in lines:
            if line.startswith("speech:"):
                in_speech = True
                rest = line[len("speech:"):].strip()
                if rest and rest != "|":
                    speech_lines.append(rest)
                continue

            if in_speech:
                if line and not line.startswith(" ") and ":" in line:
                    break
                if line.startswith("  "):
                    speech_lines.append(line[2:])
                elif not line.strip():
                    speech_lines.append("")

        return "\n".join(speech_lines).strip()

    def _clean_yaml_text(self, text: str) -> str:
        """清理 YAML 文本（移除 markdown 代码块标记等）。"""
        text = text.strip()
        if text.startswith("```yaml"):
            text = text[len("```yaml"):]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        if text.startswith("---"):
            text = text[3:]
        return text.strip()
