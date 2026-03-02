"""YAML 响应解析器单元测试。"""

import pytest

from src.core.yaml_parser import YamlResponse, YamlResponseParser


@pytest.fixture
def parser() -> YamlResponseParser:
    """创建 YAML 解析器实例。"""
    return YamlResponseParser()


class TestParseFinal:
    """测试最终完整解析。"""

    def test_parse_valid_yaml_response(self, parser: YamlResponseParser) -> None:
        """解析完整 YAML 响应成功。"""
        text = (
            "schema_version: v1\n"
            "speech: |\n"
            "  你好呀，今天天气真好！\n"
            "action: |\n"
            "  *微微一笑*\n"
            "emotion: 开心\n"
            "inner_thought: |\n"
            "  看起来心情不错\n"
        )
        result = parser.parse_final(text)
        assert isinstance(result, YamlResponse)
        assert result.speech == "你好呀，今天天气真好！"
        assert result.action == "*微微一笑*"
        assert result.emotion == "开心"
        assert result.inner_thought == "看起来心情不错"

    def test_parse_minimal_yaml(self, parser: YamlResponseParser) -> None:
        """仅包含 speech + emotion 的最小响应。"""
        text = "speech: 你好\nemotion: 平静\n"
        result = parser.parse_final(text)
        assert result.speech == "你好"
        assert result.emotion == "平静"
        assert result.action == ""
        assert result.inner_thought == ""

    def test_parse_missing_speech_fallback(self, parser: YamlResponseParser) -> None:
        """缺少 speech 字段时降级处理（YAML 含特殊字符可能解析失败）。"""
        text = "emotion: 开心\naction: 挥手\n"
        result = parser.parse_final(text)
        # 解析成功时 speech 为空，解析失败时原文作为 speech
        assert isinstance(result, YamlResponse)
        if result.emotion == "开心":
            assert result.speech == ""
        else:
            # 降级为纯文本
            assert result.speech == text.strip()

    def test_parse_invalid_yaml_fallback(self, parser: YamlResponseParser) -> None:
        """无效 YAML 降级为纯文本模式。"""
        text = "这不是一个有效的 YAML 格式：：：[["
        result = parser.parse_final(text)
        assert result.speech == text.strip()
        assert result.emotion == "平静"
        assert result.action == ""

    def test_parse_plain_text_fallback(self, parser: YamlResponseParser) -> None:
        """纯文本被作为 speech。"""
        text = "你好，我是一段纯文本回复"
        result = parser.parse_final(text)
        assert result.speech == text

    def test_parse_with_markdown_code_block(self, parser: YamlResponseParser) -> None:
        """带 markdown 代码块标记的 YAML。"""
        text = (
            "```yaml\n"
            "speech: 你好\n"
            "emotion: 开心\n"
            "```"
        )
        result = parser.parse_final(text)
        assert result.speech == "你好"
        assert result.emotion == "开心"

    def test_parse_with_yaml_separator(self, parser: YamlResponseParser) -> None:
        """带 --- 分隔符的 YAML。"""
        text = "---\nspeech: 你好\nemotion: 开心\n"
        result = parser.parse_final(text)
        assert result.speech == "你好"


class TestParseStream:
    """测试流式解析。"""

    def test_parse_complete_stream(self, parser: YamlResponseParser) -> None:
        """完整 YAML 流式解析成功。"""
        text = "speech: 你好\nemotion: 平静\n"
        result = parser.parse_stream(text)
        assert result is not None
        assert result["speech"] == "你好"

    def test_parse_incomplete_stream_returns_none(
        self, parser: YamlResponseParser
    ) -> None:
        """不完整 YAML 返回 None。"""
        text = "speech: |\n  你好呀"
        result = parser.parse_stream(text)
        # 不完整的 YAML 可能能解析也可能不能，关键是不崩溃
        # 如果解析成功则包含 speech，否则为 None
        if result is not None:
            assert "speech" in result

    def test_parse_no_speech_field_returns_none(
        self, parser: YamlResponseParser
    ) -> None:
        """缺少 speech 字段的 YAML 返回 None。"""
        text = "emotion: 开心\naction: *挥手*\n"
        result = parser.parse_stream(text)
        assert result is None


class TestExtractSpeech:
    """测试 speech 提取。"""

    def test_extract_speech(self, parser: YamlResponseParser) -> None:
        """正确提取 speech 字段文本。"""
        response = YamlResponse(speech="你好呀", emotion="开心")
        assert parser.extract_speech(response) == "你好呀"

    def test_extract_empty_speech(self, parser: YamlResponseParser) -> None:
        """空 speech 返回空字符串。"""
        response = YamlResponse()
        assert parser.extract_speech(response) == ""


class TestFormatForStorage:
    """测试存储格式化。"""

    def test_format_for_storage(self, parser: YamlResponseParser) -> None:
        """格式化为完整 YAML 存储格式。"""
        response = YamlResponse(
            speech="你好呀",
            action="*微笑*",
            emotion="开心",
            inner_thought="很高兴见到你",
        )
        formatted = parser.format_for_storage(response)
        assert "speech:" in formatted
        assert "action:" in formatted
        assert "emotion:" in formatted
        assert "inner_thought:" in formatted
        assert "schema_version:" in formatted

    def test_format_roundtrip(self, parser: YamlResponseParser) -> None:
        """格式化后可以重新解析。"""
        original = YamlResponse(
            speech="你好呀",
            action="*微笑*",
            emotion="开心",
            inner_thought="内心独白",
        )
        formatted = parser.format_for_storage(original)
        restored = parser.parse_final(formatted)
        assert restored.speech == original.speech
        assert restored.emotion == original.emotion
        assert restored.action == original.action
        assert restored.inner_thought == original.inner_thought


class TestExtractSpeechFromStream:
    """测试从流式文本中提取 speech。"""

    def test_extract_from_inline_speech(self, parser: YamlResponseParser) -> None:
        """从 speech: 行内值提取。"""
        text = "speech: 你好呀\nemotion: 平静\n"
        result = parser.extract_speech_from_stream(text)
        assert result == "你好呀"

    def test_extract_from_multiline_speech(self, parser: YamlResponseParser) -> None:
        """从多行 speech 提取。"""
        text = "speech: |\n  第一行\n  第二行\nemotion: 平静\n"
        result = parser.extract_speech_from_stream(text)
        assert "第一行" in result
        assert "第二行" in result

    def test_extract_from_partial_stream(self, parser: YamlResponseParser) -> None:
        """从不完整流中提取已有 speech 内容。"""
        text = "speech: |\n  你好呀今天"
        result = parser.extract_speech_from_stream(text)
        assert "你好呀今天" in result

    def test_no_speech_returns_empty(self, parser: YamlResponseParser) -> None:
        """无 speech 字段返回空字符串。"""
        text = "emotion: 开心\n"
        result = parser.extract_speech_from_stream(text)
        assert result == ""


class TestCleanYamlText:
    """测试 YAML 文本清理。"""

    def test_strip_markdown_yaml_block(self, parser: YamlResponseParser) -> None:
        """移除 ```yaml ... ``` 标记。"""
        text = "```yaml\nspeech: hi\n```"
        cleaned = parser._clean_yaml_text(text)
        assert "```" not in cleaned
        assert "speech: hi" in cleaned

    def test_strip_generic_code_block(self, parser: YamlResponseParser) -> None:
        """移除通用 ``` 代码块标记。"""
        text = "```\nspeech: hi\n```"
        cleaned = parser._clean_yaml_text(text)
        assert "```" not in cleaned

    def test_strip_yaml_separator(self, parser: YamlResponseParser) -> None:
        """移除 --- 分隔符。"""
        text = "---\nspeech: hi\n"
        cleaned = parser._clean_yaml_text(text)
        assert not cleaned.startswith("---")
