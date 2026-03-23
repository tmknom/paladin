"""IgnoreProcessor の実装"""

from paladin.check.ignore.directive import FileIgnoreDirective
from paladin.check.ignore.filter import ViolationFilter
from paladin.check.ignore.parser import FileIgnoreParser, LineIgnoreParser
from paladin.check.ignore.resolver import ConfigIgnoreResolver
from paladin.rule import PerFileIgnoreEntry, SourceFiles, Violations


class IgnoreProcessor:
    """Ignore ディレクティブの解析・統合・フィルタリングを一括実行するファサード"""

    def apply(
        self,
        violations: Violations,
        source_files: SourceFiles,
        per_file_ignores: tuple[PerFileIgnoreEntry, ...],
        ignore_rules: frozenset[str],
    ) -> Violations:
        """Ignore 処理を一括実行して違反を除外した Violations を返す

        Args:
            violations: フィルタリング対象の違反群
            source_files: 解析対象のソースファイル群
            per_file_ignores: 設定ファイル由来のファイル単位 ignore エントリ群
            ignore_rules: CLI から指定されたグローバル ignore ルール ID 群

        Returns:
            ignore 対象を除外した Violations
        """
        file_paths = tuple(sf.file_path for sf in source_files)
        config_directives = ConfigIgnoreResolver().resolve(per_file_ignores, file_paths)
        comment_directives = FileIgnoreParser().parse_all(source_files)
        merged_directives = FileIgnoreDirective.merge(config_directives, comment_directives)
        line_directives = LineIgnoreParser().parse_all(source_files)
        return ViolationFilter().filter(
            violations, merged_directives, line_directives, ignore_rules
        )
