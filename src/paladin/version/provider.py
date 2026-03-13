"""VersionOrchestratorProviderの実装"""

from paladin.foundation.log import log
from paladin.version.orchestrator import VersionOrchestrator
from paladin.version.resolver import VersionResolver


class VersionOrchestratorProvider:
    """VersionOrchestratorとその依存を生成するファクトリー

    具象クラスの選択と依存注入を一箇所に集約する。
    """

    @log
    def provide(self) -> VersionOrchestrator:
        """VersionOrchestratorを構築する

        Returns:
            設定済みの VersionOrchestrator
        """
        resolver = VersionResolver(package_name="paladin")
        return VersionOrchestrator(resolver=resolver)
