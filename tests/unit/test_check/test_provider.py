from paladin.check import CheckOrchestratorProvider
from paladin.check.collector import PathExcluder
from paladin.check.formatter import CheckFormatterFactory
from paladin.check.ignore import ViolationFilter
from paladin.check.orchestrator import CheckOrchestrator
from paladin.check.parser import AstParser
from paladin.check.rule_filter import RuleFilter
from paladin.rule import RuleSet


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

    def test_provide_正常系_RuleSetが注入されたOrchestratorを返すこと(self):
        # Act
        result = CheckOrchestratorProvider().provide()

        # Assert
        assert isinstance(result.rule_set, RuleSet)

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

    def test_provide_正常系_RuleFilterが注入されたOrchestratorを返すこと(self):
        # Act
        result = CheckOrchestratorProvider().provide()

        # Assert
        assert isinstance(result.rule_filter, RuleFilter)

    def test_provide_正常系_PathExcluderが注入されたOrchestratorを返すこと(self):
        # Act
        result = CheckOrchestratorProvider().provide()

        # Assert
        assert isinstance(result.path_excluder, PathExcluder)

    def test_provide_正常系_rule_optionsを渡してCheckOrchestratorが返ること(self):
        # Arrange
        rule_options = {"require-qualified-third-party": {"root-packages": ["myapp"]}}

        # Act
        result = CheckOrchestratorProvider().provide(rule_options=rule_options)

        # Assert
        assert isinstance(result, CheckOrchestrator)

    def test_provide_正常系_rule_optionsなしで従来通り動作すること(self):
        # Act
        result = CheckOrchestratorProvider().provide()

        # Assert
        assert isinstance(result, CheckOrchestrator)

    def test_provide_正常系_project_nameを渡してCheckOrchestratorが返ること(self):
        # Act
        result = CheckOrchestratorProvider().provide(project_name="myapp")

        # Assert
        assert isinstance(result, CheckOrchestrator)

    def test_provide_正常系_project_nameなしで従来通り動作すること(self):
        # Act
        result = CheckOrchestratorProvider().provide(project_name=None)

        # Assert
        assert isinstance(result, CheckOrchestrator)
