"""Check層の中核

対象列挙と AST 生成の処理フロー全体を制御し、結果を返す。
"""

from pathlib import Path

from paladin.check.collector import FileCollector
from paladin.check.config import ConfigIgnoreResolver, ProjectConfigLoader
from paladin.check.context import CheckContext
from paladin.check.formatter import CheckFormatterFactory
from paladin.check.ignore import (
    FileIgnoreDirective,
    FileIgnoreParser,
    LineIgnoreParser,
    ViolationFilter,
)
from paladin.check.parser import AstParser
from paladin.check.result import CheckReport, CheckResult
from paladin.foundation.log import log
from paladin.lint import RuleRunner


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
        violation_filter: ViolationFilter,
        config_loader: ProjectConfigLoader,
    ) -> None:
        """CheckOrchestratorを初期化

        Args:
            collector: ファイル列挙コレクター
            parser: ASTパーサー
            runner: ルール実行器
            formatter: レポートフォーマッター
            violation_filter: ignore フィルター
            config_loader: プロジェクト設定ローダー
        """
        self.collector = collector
        self.parser = parser
        self.runner = runner
        self.formatter = formatter
        self.violation_filter = violation_filter
        self.config_loader = config_loader

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
        config = self.config_loader.load()
        file_paths = tuple(pf.file_path for pf in parsed_files)
        config_directives = ConfigIgnoreResolver().resolve(config, file_paths)
        comment_directives = FileIgnoreParser().parse_all(parsed_files)
        merged_directives = self._merge_directives(config_directives, comment_directives)
        line_directives = LineIgnoreParser().parse_all(parsed_files)
        violations = self.violation_filter.filter(
            violations, merged_directives, line_directives, context.ignore_rules
        )
        result = CheckResult(
            target_files=target_files, parsed_files=parsed_files, violations=violations
        )
        return self.formatter.format(result, context.format)

    def _merge_directives(
        self,
        config_directives: tuple[FileIgnoreDirective, ...],
        comment_directives: tuple[FileIgnoreDirective, ...],
    ) -> tuple[FileIgnoreDirective, ...]:
        """設定ファイル由来とコメント由来の FileIgnoreDirective を統合する

        同一ファイルに対して両方が存在する場合は ignored_rules の和集合とし、
        いずれかが ignore_all=True なら ignore_all=True とする。
        """
        merged: dict[Path, FileIgnoreDirective] = {}
        for directive in (*config_directives, *comment_directives):
            existing = merged.get(directive.file_path)
            if existing is None:
                merged[directive.file_path] = directive
            else:
                merged[directive.file_path] = FileIgnoreDirective(
                    file_path=directive.file_path,
                    ignore_all=existing.ignore_all or directive.ignore_all,
                    ignored_rules=existing.ignored_rules | directive.ignored_rules,
                )
        return tuple(merged.values())
