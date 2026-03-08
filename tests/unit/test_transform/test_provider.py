from example.transform import TransformOrchestratorProvider
from example.transform.orchestrator import TransformOrchestrator


class TestTransformOrchestratorProvider:
    """TransformOrchestratorProviderクラスのテスト"""

    def test_provide_正常系_TransformOrchestratorインスタンスを返す(self):
        # Act
        result = TransformOrchestratorProvider().provide()

        # Assert
        assert isinstance(result, TransformOrchestrator)
