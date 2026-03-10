from paladin.check import CheckOrchestratorProvider
from paladin.check.orchestrator import CheckOrchestrator
from paladin.check.parser import AstParser
from paladin.check.rule.no_relative_import import NoRelativeImportRule
from paladin.check.rule.require_all_export import RequireAllExportRule
from paladin.check.rule.runner import RuleRunner


class TestCheckOrchestratorProvider:
    """CheckOrchestratorProviderクラスのテスト"""

    def test_provide_正常系_CheckOrchestratorインスタンスを返すこと(self):
        # Act
        result = CheckOrchestratorProvider().provide()

        # Assert
        assert isinstance(result, CheckOrchestrator)

    def test_provide_正常系_AstParserが注入されたOrchestratorを返すこと(self):
        # Act
        result = CheckOrchestratorProvider().provide()

        # Assert
        assert isinstance(result.parser, AstParser)

    def test_provide_正常系_RuleRunnerが注入されたOrchestratorを返すこと(self):
        # Act
        result = CheckOrchestratorProvider().provide()

        # Assert
        assert isinstance(result.runner, RuleRunner)

    def test_provide_正常系_RuleRunnerに2つのルールが登録されていること(self):
        # Act
        result = CheckOrchestratorProvider().provide()

        # Assert
        rules: tuple[object, ...] = result.runner._rules  # type: ignore[attr-defined]
        assert len(rules) == 2
        assert any(isinstance(r, RequireAllExportRule) for r in rules)
        assert any(isinstance(r, NoRelativeImportRule) for r in rules)
