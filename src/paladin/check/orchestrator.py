"""Check層の中核

対象列挙と AST 生成の処理フロー全体を制御し、結果を返す。
"""

from paladin.check.collector import FileCollector
from paladin.check.context import CheckContext
from paladin.check.formatter import CheckFormatterFactory
from paladin.check.parser import AstParser
from paladin.check.result import CheckReport, CheckResult
from paladin.check.rule.runner import RuleRunner
from paladin.foundation.log import log


class CheckOrchestrator:
    """対象列挙と AST 生成の処理フローを制御するオーケストレーター

    Flow:
        1. FileCollector で .py ファイルを列挙
        2. AstParser で各ファイルの AST を生成
        3. RuleRunner でルールを適用し Violations を収集
        4. CheckReportFormatter で CheckReport に変換して返す

    Returns:
        CheckReport: フォーマット済みレポート文字列と終了コードを含む実行結果
    """

    def __init__(
        self,
        collector: FileCollector,
        parser: AstParser,
        runner: RuleRunner,
        formatter: CheckFormatterFactory,
    ) -> None:
        """CheckOrchestratorを初期化

        Args:
            collector: ファイル列挙コレクター
            parser: ASTパーサー
            runner: ルール実行器
            formatter: レポートフォーマッター
        """
        self.collector = collector
        self.parser = parser
        self.runner = runner
        self.formatter = formatter

    @log
    def orchestrate(self, context: CheckContext) -> CheckReport:
        """解析対象ファイルを列挙してAST生成し、ルール適用後にレポートを返す

        Args:
            context: Check処理の実行時コンテキスト

        Returns:
            Check処理のフォーマット済みレポート
        """
        target_files = self.collector.collect(context.targets)
        parsed_files = self.parser.parse_all(target_files)
        violations = self.runner.run(parsed_files)
        result = CheckResult(
            target_files=target_files, parsed_files=parsed_files, violations=violations
        )
        return self.formatter.format(result, context.format)
