"""VersionOrchestratorProviderクラスのテスト"""

from paladin.version.orchestrator import VersionOrchestrator
from paladin.version.provider import VersionOrchestratorProvider


class TestVersionOrchestratorProvider:
    """VersionOrchestratorProviderクラスのテスト"""

    def test_provide_正常系_VersionOrchestratorを返すこと(self):
        # Act
        result = VersionOrchestratorProvider().provide()

        # Assert
        assert isinstance(result, VersionOrchestrator)
