from paladin.lint.registry import RuleRegistry
from paladin.lint.types import RuleMeta
from tests.unit.test_check.fakes import FakeRule


class TestRuleRegistry:
    """RuleRegistryクラスのテスト"""

    def test_list_rules_正常系_登録済みルールのメタ情報を返すこと(self):
        # Arrange
        rule = FakeRule()
        registry = RuleRegistry(rules=(rule,))

        # Act
        result = registry.list_rules()

        # Assert
        assert len(result) == 1
        assert isinstance(result[0], RuleMeta)
        assert result[0].rule_id == "fake-rule"
        assert result[0].rule_name == "Fake Rule"

    def test_list_rules_エッジケース_ルール未登録で空タプルを返すこと(self):
        # Arrange
        registry = RuleRegistry(rules=())

        # Act
        result = registry.list_rules()

        # Assert
        assert result == ()

    def test_find_rule_正常系_登録済みrule_idに一致するRuleMetaを返すこと(self):
        # Arrange
        rule = FakeRule(rule_id="PAL001", rule_name="Fake Rule", summary="Fake summary")
        registry = RuleRegistry(rules=(rule,))

        # Act
        result = registry.find_rule("PAL001")

        # Assert
        assert result is not None
        assert isinstance(result, RuleMeta)
        assert result.rule_id == "PAL001"
        assert result.rule_name == "Fake Rule"

    def test_find_rule_エッジケース_存在しないrule_idでNoneを返すこと(self):
        # Arrange
        rule = FakeRule(rule_id="PAL001")
        registry = RuleRegistry(rules=(rule,))

        # Act
        result = registry.find_rule("nonexistent")

        # Assert
        assert result is None
