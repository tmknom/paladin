"""RulesOrchestratorProviderクラスのテスト"""

from paladin.rules.orchestrator import RulesOrchestrator
from paladin.rules.provider import RulesOrchestratorProvider


class TestRulesOrchestratorProvider:
    """RulesOrchestratorProviderクラスのテスト"""

    def test_provide_正常系_全ルールが登録されたRulesOrchestratorを返すこと(self):
        # Act
        result = RulesOrchestratorProvider().provide()
        rules = result.registry.list_rules()

        # Assert
        assert isinstance(result, RulesOrchestrator)
        assert len(rules) == 4
        rule_ids = {r.rule_id for r in rules}
        assert "require-all-export" in rule_ids
        assert "no-relative-import" in rule_ids
        assert "no-local-import" in rule_ids
        assert "require-qualified-third-party" in rule_ids
