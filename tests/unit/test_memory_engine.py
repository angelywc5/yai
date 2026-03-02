"""记忆引擎单元测试。"""

from unittest.mock import MagicMock

import pytest

from src.core.memory_engine import MemoryContext, MemoryContextBuilder


# ============================================================================
# MemoryContext 测试
# ============================================================================


class TestMemoryContext:
    """测试 MemoryContext 消息构建。"""

    def test_build_messages_system_prompt_first(self) -> None:
        """system prompt 作为第一条消息。"""
        ctx = MemoryContext(system_prompt="你是测试角色。")
        messages = ctx.build_messages()
        assert len(messages) >= 1
        assert messages[0]["role"] == "system"
        assert "测试角色" in messages[0]["content"]

    def test_build_messages_with_all_layers(self) -> None:
        """短期 + 长效 + 故事梗概 + 固定消息 全部合并。"""
        ctx = MemoryContext(
            system_prompt="你是角色A。",
            story_summaries=[{"summary": "第一幕剧情"}],
            pinned_messages=[{"role": "user", "content": "重要记忆"}],
            long_term=[{"content": "长效记忆片段"}],
            short_term=[
                {"role": "user", "content": "最近消息1"},
                {"role": "assistant", "content": "最近回复1"},
            ],
        )
        messages = ctx.build_messages()

        # 验证顺序：system → story_summary → pinned → long_term → short_term
        roles = [m["role"] for m in messages]
        assert roles[0] == "system"  # system prompt

        # 检查所有层都有内容
        all_content = " ".join(m["content"] for m in messages)
        assert "角色A" in all_content
        assert "第一幕剧情" in all_content
        assert "重要记忆" in all_content
        assert "长效记忆片段" in all_content
        assert "最近消息1" in all_content

    def test_build_messages_story_summary_as_system(self) -> None:
        """故事梗概作为 system 角色注入。"""
        ctx = MemoryContext(
            system_prompt="prompt",
            story_summaries=[{"summary": "第一幕"}, {"summary": "第二幕"}],
        )
        messages = ctx.build_messages()
        summary_msgs = [
            m for m in messages
            if m["role"] == "system" and "故事回顾" in m["content"]
        ]
        assert len(summary_msgs) == 1
        assert "第一幕" in summary_msgs[0]["content"]
        assert "第二幕" in summary_msgs[0]["content"]

    def test_build_messages_long_term_as_system(self) -> None:
        """长效记忆片段作为 system 角色注入。"""
        ctx = MemoryContext(
            system_prompt="prompt",
            long_term=[{"content": "记忆A"}, {"content": "记忆B"}],
        )
        messages = ctx.build_messages()
        memory_msgs = [
            m for m in messages
            if m["role"] == "system" and "相关记忆片段" in m["content"]
        ]
        assert len(memory_msgs) == 1
        assert "记忆A" in memory_msgs[0]["content"]

    def test_build_messages_empty_layers(self) -> None:
        """所有记忆层为空时仅有 system prompt。"""
        ctx = MemoryContext(system_prompt="你是角色。")
        messages = ctx.build_messages()
        assert len(messages) == 1
        assert messages[0]["role"] == "system"

    def test_short_term_messages_preserve_order(self) -> None:
        """短期记忆保持原始顺序。"""
        short_term = [
            {"role": "user", "content": f"消息{i}"}
            for i in range(5)
        ]
        ctx = MemoryContext(system_prompt="prompt", short_term=short_term)
        messages = ctx.build_messages()
        user_msgs = [m for m in messages if m["role"] == "user"]
        for i, msg in enumerate(user_msgs):
            assert msg["content"] == f"消息{i}"

    def test_custom_prompt_appended(self) -> None:
        """用户自定义 prompt 追加到 system 末尾。"""
        ctx = MemoryContext(
            system_prompt="你是角色。",
            custom_prompt="请用古文回复。",
        )
        messages = ctx.build_messages()
        assert "用户自定义指令" in messages[0]["content"]
        assert "请用古文回复" in messages[0]["content"]


# ============================================================================
# MemoryContextBuilder 测试
# ============================================================================


class TestMemoryContextBuilder:
    """测试 MemoryContextBuilder 构建逻辑。"""

    @pytest.fixture
    def mock_prompt_builder(self) -> MagicMock:
        """Mock CharacterPromptBuilder。"""
        builder = MagicMock()
        builder.build = MagicMock(return_value="你是测试角色。")
        return builder

    @pytest.fixture
    def mock_scene_prompt_builder(self) -> MagicMock:
        """Mock ScenePromptBuilder。"""
        builder = MagicMock()
        builder.build = MagicMock(return_value="[场景] 测试场景设定。")
        return builder

    @pytest.fixture
    def context_builder(
        self, mock_prompt_builder, mock_scene_prompt_builder
    ) -> MemoryContextBuilder:
        """创建 MemoryContextBuilder 实例。"""
        return MemoryContextBuilder(
            prompt_builder=mock_prompt_builder,
            scene_prompt_builder=mock_scene_prompt_builder,
            max_short_term=20,
            max_long_term=5,
            max_summaries=3,
        )

    @pytest.fixture
    def character_definition(self) -> dict:
        """测试用角色定义。"""
        return {
            "identity": {"name": "小明", "background": "学生", "beliefs": "努力"},
            "personality": ["温柔", "善良", "聪明"],
        }

    def test_short_term_limit(
        self,
        context_builder: MemoryContextBuilder,
        character_definition: dict,
    ) -> None:
        """超过 max_short_term 条时截取最近 N 条。"""
        messages = [
            {"role": "user", "content": f"msg_{i}"}
            for i in range(30)
        ]
        ctx = context_builder.build(
            character_definition=character_definition,
            short_term_messages=messages,
            long_term_fragments=[],
            story_summaries=[],
            pinned_messages=[],
            current_message="hello",
        )
        assert len(ctx.short_term) == 20
        # 应该保留最后 20 条
        assert ctx.short_term[0]["content"] == "msg_10"

    def test_long_term_limit(
        self,
        context_builder: MemoryContextBuilder,
        character_definition: dict,
    ) -> None:
        """超过 max_long_term 条时截取前 N 条。"""
        fragments = [
            {"content": f"fragment_{i}"}
            for i in range(10)
        ]
        ctx = context_builder.build(
            character_definition=character_definition,
            short_term_messages=[],
            long_term_fragments=fragments,
            story_summaries=[],
            pinned_messages=[],
            current_message="hello",
        )
        assert len(ctx.long_term) == 5

    def test_summaries_limit(
        self,
        context_builder: MemoryContextBuilder,
        character_definition: dict,
    ) -> None:
        """超过 max_summaries 条时截取前 N 条。"""
        summaries = [
            {"summary": f"summary_{i}"}
            for i in range(8)
        ]
        ctx = context_builder.build(
            character_definition=character_definition,
            short_term_messages=[],
            long_term_fragments=[],
            story_summaries=summaries,
            pinned_messages=[],
            current_message="hello",
        )
        assert len(ctx.story_summaries) == 3

    def test_empty_long_term_ok(
        self,
        context_builder: MemoryContextBuilder,
        character_definition: dict,
    ) -> None:
        """无长效记忆时正常构建。"""
        ctx = context_builder.build(
            character_definition=character_definition,
            short_term_messages=[],
            long_term_fragments=[],
            story_summaries=[],
            pinned_messages=[],
            current_message="hello",
        )
        assert ctx.long_term == []
        assert ctx.system_prompt != ""

    def test_system_prompt_includes_yaml_instruction(
        self,
        context_builder: MemoryContextBuilder,
        character_definition: dict,
    ) -> None:
        """system prompt 包含 YAML 格式指令。"""
        ctx = context_builder.build(
            character_definition=character_definition,
            short_term_messages=[],
            long_term_fragments=[],
            story_summaries=[],
            pinned_messages=[],
            current_message="hello",
        )
        assert "YAML" in ctx.system_prompt
        assert "schema_version" in ctx.system_prompt

    def test_character_prompt_used_without_scene(
        self,
        context_builder: MemoryContextBuilder,
        mock_prompt_builder: MagicMock,
        character_definition: dict,
    ) -> None:
        """无场景时使用角色 prompt 构建器。"""
        context_builder.build(
            character_definition=character_definition,
            short_term_messages=[],
            long_term_fragments=[],
            story_summaries=[],
            pinned_messages=[],
            current_message="hello",
        )
        mock_prompt_builder.build.assert_called_once_with(character_definition)

    def test_scene_prompt_used_with_scene(
        self,
        context_builder: MemoryContextBuilder,
        mock_scene_prompt_builder: MagicMock,
        character_definition: dict,
    ) -> None:
        """有场景时使用场景 prompt 构建器。"""
        context_builder.build(
            character_definition=character_definition,
            short_term_messages=[],
            long_term_fragments=[],
            story_summaries=[],
            pinned_messages=[],
            current_message="hello",
            scene_definition="这是一个测试场景",
            scene_greeting="欢迎来到场景",
        )
        mock_scene_prompt_builder.build.assert_called_once()

    def test_custom_prompt_passed_through(
        self,
        context_builder: MemoryContextBuilder,
        character_definition: dict,
    ) -> None:
        """自定义 prompt 正确传递到 MemoryContext。"""
        ctx = context_builder.build(
            character_definition=character_definition,
            short_term_messages=[],
            long_term_fragments=[],
            story_summaries=[],
            pinned_messages=[],
            current_message="hello",
            custom_prompt="请用古文回复",
        )
        assert ctx.custom_prompt == "请用古文回复"

    def test_pinned_messages_not_limited(
        self,
        context_builder: MemoryContextBuilder,
        character_definition: dict,
    ) -> None:
        """固定消息不受 max_short_term 限制，全部保留。"""
        pinned = [
            {"role": "user", "content": f"pinned_{i}"}
            for i in range(25)
        ]
        ctx = context_builder.build(
            character_definition=character_definition,
            short_term_messages=[],
            long_term_fragments=[],
            story_summaries=[],
            pinned_messages=pinned,
            current_message="hello",
        )
        assert len(ctx.pinned_messages) == 25
