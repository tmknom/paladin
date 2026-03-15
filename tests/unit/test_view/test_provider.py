"""ViewOrchestratorProviderクラスのテスト"""

from paladin.view.orchestrator import ViewOrchestrator
from paladin.view.provider import ViewOrchestratorProvider


class TestViewOrchestratorProvider:
    """ViewOrchestratorProviderクラスのテスト"""

    def test_provide_正常系_全ルールが登録されたViewOrchestratorを返すこと(self):
        # Act
        result = ViewOrchestratorProvider().provide()
        rules = result.registry.list_rules()

        # Assert
        assert isinstance(result, ViewOrchestrator)
        assert len(rules) == 4
        rule_ids = {r.rule_id for r in rules}
        assert "require-all-export" in rule_ids
        assert "no-relative-import" in rule_ids
        assert "no-local-import" in rule_ids
        assert "require-qualified-third-party" in rule_ids
