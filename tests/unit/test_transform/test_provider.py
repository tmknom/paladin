from paladin.transform import TransformOrchestratorProvider
from paladin.transform.orchestrator import TransformOrchestrator


class TestTransformOrchestratorProvider:
    """TransformOrchestratorProviderクラスのテスト"""

    def test_provide_正常系_TransformOrchestratorインスタンスを返す(self):
        # Act
        result = TransformOrchestratorProvider().provide()

        # Assert
        assert isinstance(result, TransformOrchestrator)
