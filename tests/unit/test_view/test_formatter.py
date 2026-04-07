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
    background: str | None = None,
    steps: tuple[str, ...] | None = None,
    config_example: str | None = None,
    detection_example: str | None = None,
) -> RuleMeta:
    return RuleMeta(
        rule_id=rule_id,
        rule_name=rule_name,
        summary=summary,
        intent=intent,
        guidance=guidance,
        suggestion=suggestion,
        background=background,
        steps=steps,
        config_example=config_example,
        detection_example=detection_example,
    )


class TestViewTextFormatter:
    """ViewTextFormatterクラスのテスト"""

    def test_format_正常系_新フィールドが全てNoneでも既存6行が正常に出力されること(self):
        # Arrange
        rule = _make_rule_meta(
            background=None,
            steps=None,
            config_example=None,
            detection_example=None,
        )
        formatter = ViewTextFormatter()

        # Act
        result = formatter.format(rule)
        lines = result.splitlines()

        # Assert
        assert len(lines) == 6
        assert "Rule ID:" in result
        assert "my-rule" in result

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
        value_col_0 = len(lines[0]) - len("my-rule")
        value_col_1 = len(lines[1]) - len("My Rule")
        value_col_2 = len(lines[2]) - len("概要")
        value_col_3 = len(lines[3]) - len("意図")
        value_col_4 = len(lines[4]) - len("見方")
        value_col_5 = len(lines[5]) - len("修正方向")
        assert (
            value_col_0 == value_col_1 == value_col_2 == value_col_3 == value_col_4 == value_col_5
        )

    def test_format_正常系_backgroundが設定されている場合にセクション形式で表示されること(self):
        # Arrange
        rule = _make_rule_meta(background="背景テキストです。\n詳細説明です。")
        formatter = ViewTextFormatter()

        # Act
        result = formatter.format(rule)

        # Assert
        assert "背景と意図:" in result
        assert "  背景テキストです。" in result
        assert "  詳細説明です。" in result

    def test_format_エッジケース_backgroundがNoneの場合にセクションが表示されないこと(self):
        # Arrange
        rule = _make_rule_meta(background=None)
        formatter = ViewTextFormatter()

        # Act
        result = formatter.format(rule)

        # Assert
        assert "背景と意図:" not in result

    def test_format_正常系_stepsが設定されている場合に番号付きリスト形式で表示されること(self):
        # Arrange
        rule = _make_rule_meta(steps=("手順1", "手順2", "手順3"))
        formatter = ViewTextFormatter()

        # Act
        result = formatter.format(rule)

        # Assert
        assert "改善手順:" in result
        assert "  1. 手順1" in result
        assert "  2. 手順2" in result
        assert "  3. 手順3" in result

    def test_format_エッジケース_stepsがNoneの場合にセクションが表示されないこと(self):
        # Arrange
        rule = _make_rule_meta(steps=None)
        formatter = ViewTextFormatter()

        # Act
        result = formatter.format(rule)

        # Assert
        assert "改善手順:" not in result

    def test_format_正常系_config_exampleが設定されている場合にセクション形式で表示されること(self):
        # Arrange
        rule = _make_rule_meta(
            config_example="[tool.paladin.rule.max-file-length]\nmax-lines = 300"
        )
        formatter = ViewTextFormatter()

        # Act
        result = formatter.format(rule)

        # Assert
        assert "設定例:" in result
        assert "  [tool.paladin.rule.max-file-length]" in result
        assert "  max-lines = 300" in result

    def test_format_エッジケース_config_exampleがNoneの場合にセクションが表示されないこと(self):
        # Arrange
        rule = _make_rule_meta(config_example=None)
        formatter = ViewTextFormatter()

        # Act
        result = formatter.format(rule)

        # Assert
        assert "設定例:" not in result

    def test_format_正常系_detection_exampleが設定されている場合にセクション形式で表示されること(
        self,
    ):
        # Arrange
        rule = _make_rule_meta(detection_example="# 違反: ...\n# 準拠: ...")
        formatter = ViewTextFormatter()

        # Act
        result = formatter.format(rule)

        # Assert
        assert "検出パターン:" in result
        assert "  # 違反: ..." in result
        assert "  # 準拠: ..." in result

    def test_format_エッジケース_detection_exampleがNoneの場合にセクションが表示されないこと(self):
        # Arrange
        rule = _make_rule_meta(detection_example=None)
        formatter = ViewTextFormatter()

        # Act
        result = formatter.format(rule)

        # Assert
        assert "検出パターン:" not in result

    def test_format_正常系_全新フィールドが設定されている場合に既存6行の後にセクション形式で全て表示されること(
        self,
    ):
        # Arrange
        rule = _make_rule_meta(
            background="背景テキスト",
            steps=("手順A", "手順B"),
            config_example="[tool.paladin.rule.my-rule]\nkey = value",
            detection_example="# 違反例",
        )
        formatter = ViewTextFormatter()

        # Act
        result = formatter.format(rule)

        # Assert: 既存6行のラベルが含まれること
        assert "Rule ID:" in result
        assert "Suggestion:" in result
        # Assert: 新セクションが全て含まれること
        assert "背景と意図:" in result
        assert "改善手順:" in result
        assert "設定例:" in result
        assert "検出パターン:" in result
        # Assert: 順序が正しいこと（背景 -> 改善手順 -> 設定例 -> 検出パターン）
        bg_pos = result.index("背景と意図:")
        steps_pos = result.index("改善手順:")
        config_pos = result.index("設定例:")
        detection_pos = result.index("検出パターン:")
        assert bg_pos < steps_pos < config_pos < detection_pos


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

    def test_format_正常系_新フィールドが設定されている場合にJSONオブジェクトに含まれること(self):
        # Arrange
        rule = _make_rule_meta(
            background="背景テキスト",
            steps=("手順1", "手順2", "手順3"),
            config_example="[tool.paladin]\nkey = value",
            detection_example="# 違反例",
        )
        formatter = ViewJsonFormatter()

        # Act
        result = formatter.format(rule)
        data = json.loads(result)

        # Assert
        assert data["background"] == "背景テキスト"
        assert data["steps"] == ["手順1", "手順2", "手順3"]
        assert data["config_example"] == "[tool.paladin]\nkey = value"
        assert data["detection_example"] == "# 違反例"

    def test_format_エッジケース_新フィールドがNoneの場合にJSONオブジェクトのキーに含まれないこと(
        self,
    ):
        # Arrange
        rule = _make_rule_meta(
            background=None,
            steps=None,
            config_example=None,
            detection_example=None,
        )
        formatter = ViewJsonFormatter()

        # Act
        result = formatter.format(rule)
        data = json.loads(result)

        # Assert
        assert "background" not in data
        assert "steps" not in data
        assert "config_example" not in data
        assert "detection_example" not in data

    def test_format_エッジケース_一部の新フィールドのみ設定されている場合に設定済みフィールドのみ含まれること(
        self,
    ):
        # Arrange
        rule = _make_rule_meta(
            background="背景のみ設定", steps=None, config_example=None, detection_example=None
        )
        formatter = ViewJsonFormatter()

        # Act
        result = formatter.format(rule)
        data = json.loads(result)

        # Assert
        assert data["background"] == "背景のみ設定"
        assert "steps" not in data
        assert "config_example" not in data
        assert "detection_example" not in data


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
