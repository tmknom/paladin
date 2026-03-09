"""Check層の中核

対象列挙の処理フロー全体を制御し、FileCollector を呼び出して結果を返す。
"""

from paladin.check.collector import FileCollector
from paladin.check.context import CheckContext
from paladin.check.types import CheckResult
from paladin.foundation.log import log


class CheckOrchestrator:
    """対象列挙の処理フローを制御するオーケストレーター

    Flow:
        1. FileCollector で .py ファイルを列挙
        2. CheckResult として返す

    Returns:
        CheckResult: 列挙された .py ファイル群を含む実行結果
    """

    def __init__(self, collector: FileCollector) -> None:
        """CheckOrchestratorを初期化

        Args:
            collector: ファイル列挙コレクター
        """
        self.collector = collector

    @log
    def orchestrate(self, context: CheckContext) -> CheckResult:
        """解析対象ファイルを列挙して結果を返す

        Args:
            context: Check処理の実行時コンテキスト

        Returns:
            Check処理の実行結果
        """
        target_files = self.collector.collect(context.targets)
        return CheckResult(target_files=target_files)
