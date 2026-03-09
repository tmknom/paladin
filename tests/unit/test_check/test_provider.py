from paladin.check import CheckOrchestratorProvider
from paladin.check.orchestrator import CheckOrchestrator
from paladin.check.parser import AstParser


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
