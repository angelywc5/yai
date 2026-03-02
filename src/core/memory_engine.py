"""记忆引擎 — 记忆上下文构建（纯逻辑，无 I/O）。"""

from __future__ import annotations

from dataclasses import dataclass, field

from src.core.prompt_builder import CharacterPromptBuilder, ScenePromptBuilder


@dataclass
class MemoryContext:
    """记忆上下文。"""

    short_term: list[dict[str, str]] = field(default_factory=list)
    long_term: list[dict[str, str]] = field(default_factory=list)
    story_summaries: list[dict[str, str]] = field(default_factory=list)
    pinned_messages: list[dict[str, str]] = field(default_factory=list)
    character_definition: dict = field(default_factory=dict)
    custom_prompt: str | None = None
    scene_definition: str | None = None
    scene_greeting: str | None = None
    player_objective: str | None = None
    scene_genre: str | None = None
    scene_mood: str | None = None
    scene_time_period: str | None = None
    scene_setting_location: str | None = None
    system_prompt: str = ""

    def build_messages(self) -> list[dict[str, str]]:
        """
        合并记忆层，构建完整消息列表。

        消息顺序：
        1. system prompt（角色定义 + 场景设定 + YAML 格式指令）
        2. 故事梗概（作为 system 注入）
        3. 固定消息（用户标记的关键记忆）
        4. 长效记忆片段（向量检索结果）
        5. 短期记忆（最近 N 条）
        """
        messages: list[dict[str, str]] = []

        # 1. System prompt
        system_parts = [self.system_prompt]

        # 用户自定义 prompt 追加到 system 末尾
        if self.custom_prompt:
            system_parts.append(f"\n[用户自定义指令]\n{self.custom_prompt}")

        messages.append({"role": "system", "content": "\n".join(system_parts)})

        # 2. 故事梗概注入
        if self.story_summaries:
            summary_text = "\n".join(
                f"[梗概 {i + 1}] {s.get('summary', '')}"
                for i, s in enumerate(self.story_summaries)
            )
            messages.append({
                "role": "system",
                "content": f"[故事回顾]\n{summary_text}",
            })

        # 3. 固定消息（高优先级记忆）
        for msg in self.pinned_messages:
            messages.append(msg)

        # 4. 长效记忆片段
        if self.long_term:
            memory_text = "\n".join(
                f"- {m.get('content', '')}" for m in self.long_term
            )
            messages.append({
                "role": "system",
                "content": f"[相关记忆片段]\n{memory_text}",
            })

        # 5. 短期记忆
        for msg in self.short_term:
            messages.append(msg)

        return messages


class MemoryContextBuilder:
    """记忆上下文构建器。"""

    def __init__(
        self,
        prompt_builder: CharacterPromptBuilder,
        scene_prompt_builder: ScenePromptBuilder,
        max_short_term: int,
        max_long_term: int,
        max_summaries: int,
    ):
        """
        初始化构建器。

        Args:
            prompt_builder: 角色 prompt 构建器
            scene_prompt_builder: 场景 prompt 构建器
            max_short_term: 短期记忆最大条数
            max_long_term: 长效记忆最大片段数
            max_summaries: 故事梗概最大数量
        """
        self._prompt_builder = prompt_builder
        self._scene_prompt_builder = scene_prompt_builder
        self._max_short_term = max_short_term
        self._max_long_term = max_long_term
        self._max_summaries = max_summaries

    def build(
        self,
        character_definition: dict,
        short_term_messages: list[dict[str, str]],
        long_term_fragments: list[dict[str, str]],
        story_summaries: list[dict[str, str]],
        pinned_messages: list[dict[str, str]],
        current_message: str,
        custom_prompt: str | None = None,
        scene_definition: str | None = None,
        scene_greeting: str | None = None,
        player_objective: str | None = None,
        scene_genre: str | None = None,
        scene_mood: str | None = None,
        scene_time_period: str | None = None,
        scene_setting_location: str | None = None,
    ) -> MemoryContext:
        """
        构建完整的记忆上下文。

        Args:
            character_definition: 角色定义字典
            short_term_messages: 短期记忆消息列表
            long_term_fragments: 长效记忆片段
            story_summaries: 故事梗概列表
            pinned_messages: 用户固定的消息
            current_message: 当前用户输入
            custom_prompt: 用户自定义 prompt
            scene_*: 场景相关属性

        Returns:
            构建完成的 MemoryContext
        """
        # 构建 system prompt
        if scene_definition:
            system_prompt = self._scene_prompt_builder.build(
                scene_definition=scene_definition,
                character_definitions=[character_definition],
                user_name="用户",
                greeting=scene_greeting,
                player_objective=player_objective,
                genre=scene_genre,
                mood=scene_mood,
                time_period=scene_time_period,
                setting_location=scene_setting_location,
            )
        else:
            system_prompt = self._prompt_builder.build(character_definition)

        # 追加 YAML 格式指令
        yaml_instruction = self._build_yaml_instruction()
        system_prompt += f"\n\n{yaml_instruction}"

        return MemoryContext(
            short_term=short_term_messages[-self._max_short_term:],
            long_term=long_term_fragments[:self._max_long_term],
            story_summaries=story_summaries[:self._max_summaries],
            pinned_messages=pinned_messages,
            character_definition=character_definition,
            custom_prompt=custom_prompt,
            scene_definition=scene_definition,
            scene_greeting=scene_greeting,
            player_objective=player_objective,
            scene_genre=scene_genre,
            scene_mood=scene_mood,
            scene_time_period=scene_time_period,
            scene_setting_location=scene_setting_location,
            system_prompt=system_prompt,
        )

    def _build_yaml_instruction(self) -> str:
        """构建 YAML 格式约束指令。"""
        return (
            "[回复格式]\n"
            "请始终以 YAML 格式输出你的回复。格式如下：\n"
            "---\n"
            "schema_version: v1\n"
            "speech: |\n"
            "  (你的对话内容，可以多行)\n"
            "action: |\n"
            "  (可选：动作描述，如 *微微低下头*，缺省时输出空字符串)\n"
            "emotion: (当前情绪标签，如：开心/难过/愤怒/平静/害羞)\n"
            "inner_thought: |\n"
            "  (可选：内心独白，仅用于角色一致性，缺省时输出空字符串)"
        )
