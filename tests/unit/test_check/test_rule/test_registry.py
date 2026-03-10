from paladin.check.rule.registry import RuleRegistry
from paladin.check.rule.require_all_export import RequireAllExportRule
from paladin.check.types import RuleMeta


class TestRuleRegistry:
    """RuleRegistryクラスのテスト"""

    def test_list_rules_正常系_登録済みルールのメタ情報を返すこと(self):
        # Arrange
        rule = RequireAllExportRule()
        registry = RuleRegistry(rules=(rule,))

        # Act
        result = registry.list_rules()

        # Assert
        assert len(result) == 1
        assert isinstance(result[0], RuleMeta)
        assert result[0].rule_id == "require-all-export"
        assert result[0].rule_name == "Require __all__ Export"

    def test_list_rules_エッジケース_ルール未登録で空タプルを返すこと(self):
        # Arrange
        registry = RuleRegistry(rules=())

        # Act
        result = registry.list_rules()

        # Assert
        assert result == ()
