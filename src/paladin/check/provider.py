"""CheckOrchestratorとその依存を一括生成するファクトリー

具象クラスへの依存を隠蔽し、Check層の生成ロジックを一元化する。
"""

from paladin.check.collector import FileCollector
from paladin.check.orchestrator import CheckOrchestrator
from paladin.foundation.log import log


class CheckOrchestratorProvider:
    """CheckOrchestratorとその依存を生成するファクトリー

    具象クラスの選択と依存注入を一箇所に集約する。
    """

    def __init__(self) -> None:
        """Providerを初期化"""
        pass

    @log
    def provide(self) -> CheckOrchestrator:
        """CheckOrchestratorを構築

        Returns:
            設定済みのCheckOrchestrator
        """
        return CheckOrchestrator(collector=FileCollector())
