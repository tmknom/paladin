from paladin.list.orchestrator import ListOrchestrator
from paladin.list.provider import ListOrchestratorProvider


class TestListOrchestratorProvider:
    """ListOrchestratorProviderクラスのテスト"""

    def test_provide_正常系_ListOrchestratorを返すこと(self):
        # Act
        result = ListOrchestratorProvider().provide()

        # Assert
        assert isinstance(result, ListOrchestrator)
