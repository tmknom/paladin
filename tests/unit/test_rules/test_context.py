"""RulesContextクラスのテスト"""

from paladin.rules.context import RulesContext


class TestRulesContext:
    """RulesContextクラスのテスト"""

    def test_RulesContext_正常系_rule_id指定でインスタンス生成できること(self):
        # Act
        result = RulesContext(rule_id="require-all-export")

        # Assert
        assert result.rule_id == "require-all-export"
