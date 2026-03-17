"""ListOrchestratorProviderクラスのテスト"""

from paladin.list.orchestrator import ListOrchestrator
from paladin.list.provider import ListOrchestratorProvider


class TestListOrchestratorProvider:
    """ListOrchestratorProviderクラスのテスト"""

    def test_provide_正常系_全ルールが登録されたListOrchestratorを返すこと(self):
        # Act
        result = ListOrchestratorProvider().provide()
        rules = result.rule_set.list_rules()

        # Assert
        assert isinstance(result, ListOrchestrator)
        assert len(rules) == 8
        rule_ids = {r.rule_id for r in rules}
        assert "require-all-export" in rule_ids
        assert "no-relative-import" in rule_ids
        assert "no-local-import" in rule_ids
        assert "require-qualified-third-party" in rule_ids
        assert "no-direct-internal-import" in rule_ids
        assert "no-non-init-all" in rule_ids
        assert "no-cross-package-reexport" in rule_ids
        assert "no-mock-usage" in rule_ids
