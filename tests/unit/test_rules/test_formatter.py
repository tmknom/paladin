"""RulesFormatterクラスのテスト"""

from paladin.lint import RuleMeta
from paladin.rules.formatter import RulesFormatter


def _make_rule_meta(
    rule_id: str = "PAL001",
    rule_name: str = "rule-name",
    summary: str = "概要テキスト",
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


class TestRulesFormatter:
    """RulesFormatterクラスのテスト"""

    def test_format_正常系_単一ルールのID名前概要をタブ区切り風に返すこと(self):
        # Arrange
        rules = (_make_rule_meta(rule_id="PAL001", rule_name="rule-name", summary="概要テキスト"),)

        # Act
        result = RulesFormatter().format(rules)

        # Assert
        assert "PAL001" in result
        assert "rule-name" in result
        assert "概要テキスト" in result

    def test_format_正常系_複数ルールで各行が整列されること(self):
        # Arrange
        rules = (
            _make_rule_meta(rule_id="PAL001", rule_name="short", summary="概要1"),
            _make_rule_meta(rule_id="PAL002", rule_name="longer-rule-name", summary="概要2"),
        )

        # Act
        result = RulesFormatter().format(rules)

        # Assert
        lines = result.splitlines()
        assert len(lines) == 2
        # rule_name 列がパディングで揃っているため、summary の開始位置が同じはず
        idx1 = lines[0].index("概要1")
        idx2 = lines[1].index("概要2")
        assert idx1 == idx2

    def test_format_エッジケース_ルール0件で空文字列を返すこと(self):
        # Arrange
        rules: tuple[()] = ()

        # Act
        result = RulesFormatter().format(rules)

        # Assert
        assert result == ""
