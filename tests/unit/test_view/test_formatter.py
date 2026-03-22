"""ViewFormatterクラスのテスト"""

import json

from paladin.foundation.output import OutputFormat
from paladin.rule import RuleMeta
from paladin.view.formatter import ViewFormatterFactory, ViewJsonFormatter, ViewTextFormatter


def _make_rule_meta(
    rule_id: str = "my-rule",
    rule_name: str = "My Rule",
    summary: str = "概要",
    intent: str = "意図",
    guidance: str = "見方",
    suggestion: str = "修正方向",
) -> RuleMeta:
    return RuleMeta(
        rule_id=rule_id,
        rule_name=rule_name,
        summary=summary,
        intent=intent,
        guidance=guidance,
        suggestion=suggestion,
    )


class TestViewTextFormatter:
    """ViewTextFormatterクラスのテスト"""

    def test_format_正常系_RuleMetaの全フィールドがラベル付きで出力されること(self):
        # Arrange
        rule = _make_rule_meta(
            rule_id="require-all-export",
            rule_name="Require All Export",
            summary="全モジュールに__all__を要求する",
            intent="公開インターフェースを明示する",
            guidance="__init__.py に __all__ が定義されているか確認する",
            suggestion="__all__ リストを定義する",
        )
        formatter = ViewTextFormatter()

        # Act
        result = formatter.format(rule)

        # Assert
        assert "require-all-export" in result
        assert "Require All Export" in result
        assert "全モジュールに__all__を要求する" in result
        assert "公開インターフェースを明示する" in result
        assert "__init__.py に __all__ が定義されているか確認する" in result
        assert "__all__ リストを定義する" in result
        assert "Rule ID:" in result
        assert "Name:" in result
        assert "Summary:" in result
        assert "Intent:" in result
        assert "Guidance:" in result
        assert "Suggestion:" in result

    def test_format_正常系_ラベルの値が整列されること(self):
        # Arrange
        rule = _make_rule_meta()
        formatter = ViewTextFormatter()

        # Act
        result = formatter.format(rule)
        lines = result.splitlines()

        # Assert
        assert len(lines) == 6
        # 各行の値部分が同じ列から始まること（固定幅ラベル列による整列）
        assert lines[0].endswith("my-rule")
        assert lines[1].endswith("My Rule")
        assert lines[2].endswith("概要")
        assert lines[3].endswith("意図")
        assert lines[4].endswith("見方")
        assert lines[5].endswith("修正方向")
        value_col_0 = len(lines[0]) - len("my-rule")
        value_col_1 = len(lines[1]) - len("My Rule")
        value_col_2 = len(lines[2]) - len("概要")
        value_col_3 = len(lines[3]) - len("意図")
        value_col_4 = len(lines[4]) - len("見方")
        value_col_5 = len(lines[5]) - len("修正方向")
        assert (
            value_col_0 == value_col_1 == value_col_2 == value_col_3 == value_col_4 == value_col_5
        )


class TestViewJsonFormatter:
    """ViewJsonFormatterクラスのテスト"""

    def test_format_正常系_RuleMetaの全6フィールドがJSONオブジェクトに含まれること(self):
        # Arrange
        rule = _make_rule_meta(
            rule_id="require-all-export",
            rule_name="Require All Export",
            summary="概要テキスト",
            intent="意図テキスト",
            guidance="見方テキスト",
            suggestion="修正方向テキスト",
        )
        formatter = ViewJsonFormatter()

        # Act
        result = formatter.format(rule)
        data = json.loads(result)

        # Assert
        assert data["rule_id"] == "require-all-export"
        assert data["rule_name"] == "Require All Export"
        assert data["summary"] == "概要テキスト"
        assert data["intent"] == "意図テキスト"
        assert data["guidance"] == "見方テキスト"
        assert data["suggestion"] == "修正方向テキスト"

    def test_format_正常系_出力がvalid_JSONであること(self):
        # Arrange
        rule = _make_rule_meta()
        formatter = ViewJsonFormatter()

        # Act
        result = formatter.format(rule)

        # Assert: json.loads が例外なく成功する
        json.loads(result)

    def test_format_正常系_日本語を含むフィールドがエスケープされずに出力されること(self):
        # Arrange
        rule = _make_rule_meta(summary="日本語テキスト")
        formatter = ViewJsonFormatter()

        # Act
        result = formatter.format(rule)

        # Assert: 日本語がそのまま含まれる（\uXXXX 形式にエスケープされない）
        assert "日本語テキスト" in result

    def test_format_正常系_インデント付きで整形されること(self):
        # Arrange
        rule = _make_rule_meta()
        formatter = ViewJsonFormatter()

        # Act
        result = formatter.format(rule)

        # Assert: 2スペースインデントが含まれる
        assert "  " in result
        assert "\n" in result


class TestViewFormatterFactory:
    """ViewFormatterFactoryクラスのテスト"""

    def test_format_正常系_TEXT指定でラベル付きテキスト形式を返すこと(self):
        # Arrange
        rule = _make_rule_meta(rule_id="my-rule")
        factory = ViewFormatterFactory()

        # Act
        result = factory.format(rule, OutputFormat.TEXT)

        # Assert
        assert "Rule ID:" in result
        assert "my-rule" in result

    def test_format_正常系_JSON指定でJSON形式を返すこと(self):
        # Arrange
        rule = _make_rule_meta(rule_id="my-rule")
        factory = ViewFormatterFactory()

        # Act
        result = factory.format(rule, OutputFormat.JSON)
        data = json.loads(result)

        # Assert
        assert data["rule_id"] == "my-rule"
        assert "rule_name" in data
        assert "summary" in data
        assert "intent" in data
        assert "guidance" in data
        assert "suggestion" in data

    def test_format_error_正常系_TEXT指定でメッセージ文字列をそのまま返すこと(self):
        # Arrange
        factory = ViewFormatterFactory()
        message = "Error: Rule 'nonexistent' not found."

        # Act
        result = factory.format_error(message, OutputFormat.TEXT)

        # Assert
        assert result == message

    def test_format_error_正常系_JSON指定でerrorキーを含むJSONを返すこと(self):
        # Arrange
        factory = ViewFormatterFactory()
        message = "Error: Rule 'nonexistent' not found."

        # Act
        result = factory.format_error(message, OutputFormat.JSON)
        data = json.loads(result)

        # Assert
        assert data["error"] == message
