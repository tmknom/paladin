"""ViewOrchestratorProviderクラスのテスト"""

from paladin.view.provider import ViewOrchestratorProvider


class TestViewOrchestratorProvider:
    """ViewOrchestratorProviderクラスのテスト"""

    def test_provide_正常系_全ルールが登録されたViewOrchestratorを返すこと(self):
        # Act
        result = ViewOrchestratorProvider().provide()
        rules = result.rule_set.list_rules()

        # Assert
        rule_ids = {r.rule_id for r in rules}
        expected_ids = {
            "require-empty-test-init",
            "require-all-export",
            "no-relative-import",
            "no-local-import",
            "require-qualified-third-party",
            "no-direct-internal-import",
            "no-non-init-all",
            "no-cross-package-reexport",
            "no-mock-usage",
            "no-unused-export",
            "no-deep-nesting",
            "no-third-party-import",
            "no-cross-package-import",
            "no-testing-test-code",
            "max-method-length",
            "max-class-length",
            "max-file-length",
            "require-docstring",
            "unused-ignore",
            "require-aaa-comment",
            "no-error-message-test",
            "no-frozen-instance-test",
            "no-nested-test-class",
        }
        assert rule_ids == expected_ids
