"""System Prompt 构建工具。"""

from __future__ import annotations


class CharacterPromptBuilder:
    """将角色定义转换为 system prompt。"""

    def build_system_prompt(self, definition: dict, user_display_name: str) -> str:
        """
        构建角色 system prompt。

        格式：
        你是{name}。
        背景：{background}
        核心信念：{core_belief}

        你的性格特点：{personality}

        说话风格：
        - 语调：{tone}
        - 口头禅：{catchphrases}
        - 标点习惯：{punctuation_habits}
        - 语言风格：{language_level}

        以下是你的对话示例，请严格模仿这种语气和风格：
        用户: ...
        你: ...
        """
        identity = definition.get("identity", {})
        name = identity.get("name", "角色")
        background = identity.get("background", "")
        core_belief = identity.get("core_belief", "")

        personality = ", ".join(definition.get("personality", []))

        speech_style = definition.get("speech_style", {})
        tone = speech_style.get("tone", "")
        catchphrases = ", ".join(speech_style.get("catchphrases", []))
        punctuation_habits = speech_style.get("punctuation_habits", "")
        language_level = speech_style.get("language_level", "")

        # 构建基础 prompt
        prompt_lines = [
            f"你是{name}。",
            f"背景：{background}",
            f"核心信念：{core_belief}",
            "",
            f"你的性格特点：{personality}",
            "",
            "说话风格：",
            f"- 语调：{tone}",
            f"- 口头禅：{catchphrases}",
            f"- 标点习惯：{punctuation_habits}",
            f"- 语言风格：{language_level}",
            "",
            "以下是你的对话示例，请严格模仿这种语气和风格：",
        ]

        # 添加示例对话
        sample_dialogues = definition.get("sample_dialogues", [])
        for dialogue in sample_dialogues:
            user_input = dialogue.get("user", "")
            char_response = dialogue.get("char", "")
            prompt_lines.append(f"用户: {user_input}")
            prompt_lines.append(f"你: {char_response}")

        return "\n".join(prompt_lines)

    def build_few_shot_messages(
        self, sample_dialogues: list[dict]
    ) -> list[dict[str, str]]:
        """将示例对话转换为 few-shot messages 格式。"""
        messages = []
        for dialogue in sample_dialogues:
            messages.append({"role": "user", "content": dialogue.get("user", "")})
            messages.append({"role": "assistant", "content": dialogue.get("char", "")})
        return messages


class ScenePromptBuilder:
    """将场景设定 + 角色定义合并为 system prompt。"""

    def __init__(self, character_builder: CharacterPromptBuilder):
        self._character_builder = character_builder

    def build_scene_system_prompt(
        self,
        scene_definition: str,
        scene_greeting: str,
        player_objective: str,
        character_definition: dict,
        user_display_name: str,
        genre: str = "",
        time_period: str = "",
        setting_location: str = "",
        mood: str = "",
    ) -> str:
        """
        合并场景元数据、世界观与角色 prompt。

        1. 变量替换（在注入 prompt 前统一执行）：
           - scene_definition 中的 {{char}} → character_definition["identity"]["name"]
           - scene_definition 中的 {{user}} → user_display_name
           - greeting 中同理
           - player_objective 中同理

        2. 构建 system prompt 结构：

        【场景氛围】
        类型：{genre}  时代：{time_period}  地点：{setting_location}
        语调：{mood}

        【场景设定】
        {scene_definition}  (变量已替换)

        【你的身份】
        你是{name}。背景：{background}
        ...

        【玩家目标】
        {player_objective}  (变量已替换)

        【开场】
        你的第一句话是：{greeting}  (变量已替换)
        """
        # 提取角色名
        char_name = character_definition.get("identity", {}).get("name", "角色")

        # 变量替换
        scene_definition_replaced = scene_definition.replace(
            "{{char}}", char_name
        ).replace("{{user}}", user_display_name)
        greeting_replaced = scene_greeting.replace("{{char}}", char_name).replace(
            "{{user}}", user_display_name
        )
        objective_replaced = player_objective.replace("{{char}}", char_name).replace(
            "{{user}}", user_display_name
        )

        # 构建场景氛围部分
        atmosphere_parts = []
        if genre:
            atmosphere_parts.append(f"类型：{genre}")
        if time_period:
            atmosphere_parts.append(f"时代：{time_period}")
        if setting_location:
            atmosphere_parts.append(f"地点：{setting_location}")
        if mood:
            atmosphere_parts.append(f"语调：{mood}")

        atmosphere = "  ".join(atmosphere_parts) if atmosphere_parts else ""

        # 构建角色身份部分（复用 CharacterPromptBuilder）
        character_prompt = self._character_builder.build_system_prompt(
            character_definition, user_display_name
        )

        # 合并 prompt
        prompt_lines = []

        if atmosphere:
            prompt_lines.append("【场景氛围】")
            prompt_lines.append(atmosphere)
            prompt_lines.append("")

        if scene_definition_replaced:
            prompt_lines.append("【场景设定】")
            prompt_lines.append(scene_definition_replaced)
            prompt_lines.append("")

        prompt_lines.append("【你的身份】")
        prompt_lines.append(character_prompt)
        prompt_lines.append("")

        if objective_replaced:
            prompt_lines.append("【玩家目标】")
            prompt_lines.append(objective_replaced)
            prompt_lines.append("")

        if greeting_replaced:
            prompt_lines.append("【开场】")
            prompt_lines.append(f"你的第一句话是：{greeting_replaced}")

        return "\n".join(prompt_lines)
