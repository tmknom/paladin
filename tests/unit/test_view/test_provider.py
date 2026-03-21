"""ViewOrchestratorProviderクラスのテスト"""

from paladin.view.orchestrator import ViewOrchestrator
from paladin.view.provider import ViewOrchestratorProvider


class TestViewOrchestratorProvider:
    """ViewOrchestratorProviderクラスのテスト"""

    def test_provide_正常系_全ルールが登録されたViewOrchestratorを返すこと(self):
        # Act
        result = ViewOrchestratorProvider().provide()
        rules = result.rule_set.list_rules()

        # Assert
        assert isinstance(result, ViewOrchestrator)
        assert len(rules) == 14
        rule_ids = {r.rule_id for r in rules}
        assert "require-all-export" in rule_ids
        assert "no-relative-import" in rule_ids
        assert "no-local-import" in rule_ids
        assert "require-qualified-third-party" in rule_ids
        assert "no-direct-internal-import" in rule_ids
        assert "no-non-init-all" in rule_ids
        assert "no-cross-package-reexport" in rule_ids
        assert "no-mock-usage" in rule_ids
        assert "no-unused-export" in rule_ids
        assert "no-deep-nesting" in rule_ids
        assert "no-third-party-import" in rule_ids
        assert "no-cross-package-import" in rule_ids
        assert "no-testing-test-code" in rule_ids
        assert "max-method-length" in rule_ids
