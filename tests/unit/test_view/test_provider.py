from paladin.view.orchestrator import ViewOrchestrator
from paladin.view.provider import ViewOrchestratorProvider


class TestViewOrchestratorProvider:
    """ViewOrchestratorProviderクラスのテスト"""

    def test_provide_正常系_ViewOrchestratorを返すこと(self):
        # Act
        result = ViewOrchestratorProvider().provide()

        # Assert
        assert isinstance(result, ViewOrchestrator)
