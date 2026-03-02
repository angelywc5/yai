"""故事梗概引擎 — 纯逻辑，判断触发条件和构建 prompt。"""

from __future__ import annotations


class StorySummaryEngine:
    """
    故事梗概引擎 — 纯逻辑，参数从配置注入。

    职责：
    - 判断是否应触发梗概生成
    - 构建请求 AI 生成故事梗概的 prompt
    """

    def __init__(
        self,
        trigger_interval: int,
        max_key_dialogues: int,
        summary_max_length: int,
    ):
        """
        初始化梗概引擎。

        Args:
            trigger_interval: 触发间隔轮数（默认 10）
            max_key_dialogues: 最大关键对话数（默认 5）
            summary_max_length: 梗概最大字数（默认 200）
        """
        self._trigger_interval = trigger_interval
        self._max_key_dialogues = max_key_dialogues
        self._summary_max_length = summary_max_length

    def should_trigger(self, current_turn: int, last_summary_turn: int) -> bool:
        """
        判断是否应触发梗概生成。

        Args:
            current_turn: 当前轮次
            last_summary_turn: 上次梗概的结束轮次

        Returns:
            True 表示应触发
        """
        return (current_turn - last_summary_turn) >= self._trigger_interval

    def build_summary_prompt(
        self, messages: list[dict[str, str]], character_name: str
    ) -> str:
        """
        构建请求 AI 生成故事梗概的 prompt（YAML 格式要求）。

        Args:
            messages: 需要总结的消息列表
            character_name: 角色名称

        Returns:
            system prompt 字符串
        """
        dialogue_text = ""
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            speaker = character_name if role == "assistant" else "用户"
            dialogue_text += f"{speaker}: {content}\n"

        return (
            f"请根据以下 {character_name} 与用户的对话历史，"
            f"生成一份 YAML 格式的故事梗概：\n\n"
            f"{dialogue_text}\n"
            f"请输出以下 YAML 格式：\n"
            f"---\n"
            f"summary: |\n"
            f"  ({self._summary_max_length}字以内的故事摘要，"
            f"包含关键事件、情感转折、人物关系变化)\n"
            f"key_dialogues:\n"
            f"  - turn: (轮次号)\n"
            f"    speaker: (说话者)\n"
            f"    content: (原文摘录)\n"
            f"    significance: (为什么这段对话重要)\n"
            f"  ...最多{self._max_key_dialogues}段\n"
            f"mood_arc: (情感弧线描述，如：平静→紧张→释然)"
        )

    @property
    def trigger_interval(self) -> int:
        """触发间隔轮数。"""
        return self._trigger_interval
