"""VersionOrchestratorクラスのテスト"""

from importlib.metadata import version

from paladin.version.orchestrator import VersionOrchestrator
from paladin.version.resolver import VersionResolver


class TestVersionOrchestrator:
    """VersionOrchestratorクラスのテスト"""

    def test_orchestrate_正常系_バージョン文字列を返すこと(self):
        # Arrange
        resolver = VersionResolver(package_name="paladin")
        orchestrator = VersionOrchestrator(resolver=resolver)

        # Act
        result = orchestrator.orchestrate()

        # Assert
        assert result == version("paladin")
