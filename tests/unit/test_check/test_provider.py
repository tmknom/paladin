from paladin.check import CheckOrchestratorProvider
from paladin.check.config import ProjectConfigLoader
from paladin.check.formatter import CheckFormatterFactory
from paladin.check.ignore import ViolationFilter
from paladin.check.orchestrator import CheckOrchestrator
from paladin.check.parser import AstParser
from paladin.lint import RuleRunner


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

    def test_provide_正常系_CheckFormatterFactoryが注入されたOrchestratorを返すこと(self):
        # Act
        result = CheckOrchestratorProvider().provide()

        # Assert
        assert isinstance(result.formatter, CheckFormatterFactory)

    def test_provide_正常系_ViolationFilterが注入されたOrchestratorを返すこと(self):
        # Act
        result = CheckOrchestratorProvider().provide()

        # Assert
        assert isinstance(result.violation_filter, ViolationFilter)

    def test_provide_正常系_ProjectConfigLoaderが注入されたOrchestratorを返すこと(self):
        # Act
        result = CheckOrchestratorProvider().provide()

        # Assert
        assert isinstance(result.config_loader, ProjectConfigLoader)
