"""Check層の中核

対象列挙と AST 生成の処理フロー全体を制御し、結果を返す。
"""

from paladin.check.collector import FileCollector
from paladin.check.context import CheckContext
from paladin.check.parser import AstParser
from paladin.check.types import CheckResult
from paladin.foundation.log import log


class CheckOrchestrator:
    """対象列挙と AST 生成の処理フローを制御するオーケストレーター

    Flow:
        1. FileCollector で .py ファイルを列挙
        2. AstParser で各ファイルの AST を生成
        3. CheckResult として返す

    Returns:
        CheckResult: 列挙された .py ファイル群と AST 解析結果を含む実行結果
    """

    def __init__(self, collector: FileCollector, parser: AstParser) -> None:
        """CheckOrchestratorを初期化

        Args:
            collector: ファイル列挙コレクター
            parser: ASTパーサー
        """
        self.collector = collector
        self.parser = parser

    @log
    def orchestrate(self, context: CheckContext) -> CheckResult:
        """解析対象ファイルを列挙してAST生成し結果を返す

        Args:
            context: Check処理の実行時コンテキスト

        Returns:
            Check処理の実行結果
        """
        target_files = self.collector.collect(context.targets)
        parsed_files = self.parser.parse_all(target_files)
        return CheckResult(target_files=target_files, parsed_files=parsed_files)
