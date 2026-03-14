"""RulesDetailFormatterクラスのテスト"""

from paladin.lint import RuleMeta
from paladin.rules.detail_formatter import RulesDetailFormatter


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


class TestRulesDetailFormatter:
    """RulesDetailFormatterクラスのテスト"""

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
        formatter = RulesDetailFormatter()

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
        formatter = RulesDetailFormatter()

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
