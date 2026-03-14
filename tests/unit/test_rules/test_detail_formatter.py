"""RulesDetailFormatterクラスのテスト"""

from paladin.lint import RuleMeta
from paladin.rules.detail_formatter import RulesDetailFormatter


class TestRulesDetailFormatter:
    """RulesDetailFormatterクラスのテスト"""

    def test_format_正常系_RuleMetaの全フィールドがラベル付きで出力されること(self):
        # Arrange
        rule = RuleMeta(
            rule_id="require-all-export",
            rule_name="Require All Export",
            summary="全モジュールに__all__を要求する",
        )
        formatter = RulesDetailFormatter()

        # Act
        result = formatter.format(rule)

        # Assert
        assert "require-all-export" in result
        assert "Require All Export" in result
        assert "全モジュールに__all__を要求する" in result
        assert "Rule ID:" in result
        assert "Name:" in result
        assert "Summary:" in result

    def test_format_正常系_ラベルの値が整列されること(self):
        # Arrange
        rule = RuleMeta(rule_id="my-rule", rule_name="My Rule", summary="概要")
        formatter = RulesDetailFormatter()

        # Act
        result = formatter.format(rule)
        lines = result.splitlines()

        # Assert
        assert len(lines) == 3
        # 各行の値部分が同じ列から始まること（固定幅ラベル列による整列）
        # 値の開始位置: 行の末尾から値文字列を差し引いた位置
        assert lines[0].endswith("my-rule")
        assert lines[1].endswith("My Rule")
        assert lines[2].endswith("概要")
        value_col_0 = len(lines[0]) - len("my-rule")
        value_col_1 = len(lines[1]) - len("My Rule")
        value_col_2 = len(lines[2]) - len("概要")
        assert value_col_0 == value_col_1 == value_col_2
