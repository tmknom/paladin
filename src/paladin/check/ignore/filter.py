"""Ignoreパッケージの違反フィルタリング

ignore ディレクティブに基づいて違反を除外する。
"""

from pathlib import Path

from paladin.check.ignore.directive import FileIgnoreDirective, LineIgnoreDirective
from paladin.rule import Violation, Violations


class ViolationFilter:
    """FileIgnoreDirective / LineIgnoreDirective に基づいて Violations から ignore 対象の違反を除外するフィルター"""

    def filter(
        self,
        violations: Violations,
        directives: tuple[FileIgnoreDirective, ...],
        line_directives: tuple[LineIgnoreDirective, ...] = (),
        ignore_rules: frozenset[str] = frozenset(),
    ) -> Violations:
        """Ignore 対象の違反を除外した新しい Violations を返す

        Args:
            violations: フィルタリング対象の違反群
            directives: ファイルごとの ignore ディレクティブ群
            line_directives: 行単位の ignore ディレクティブ群
            ignore_rules: CLI から指定されたグローバル ignore ルール ID 群

        Returns:
            ignore 対象を除外した Violations
        """
        file_directive_map = {d.file_path: d for d in directives}
        line_directive_map = {(d.file_path, d.target_line): d for d in line_directives}
        filtered = tuple(
            v
            for v in violations
            if not self._should_ignore_by_cli(v, ignore_rules)
            and not self._should_ignore_by_file(v, file_directive_map)
            and not self._should_ignore_by_line(v, line_directive_map)
        )
        return Violations(items=filtered)

    def _should_ignore_by_cli(
        self,
        violation: Violation,
        ignore_rules: frozenset[str],
    ) -> bool:
        return violation.rule_id in ignore_rules

    def _should_ignore_by_file(
        self,
        violation: Violation,
        directive_map: dict[Path, FileIgnoreDirective],
    ) -> bool:
        directive = directive_map.get(violation.file)
        if directive is None:
            return False
        if directive.ignore_all:
            return True
        return violation.rule_id in directive.ignored_rules

    def _should_ignore_by_line(
        self,
        violation: Violation,
        line_directive_map: dict[tuple[Path, int], LineIgnoreDirective],
    ) -> bool:
        directive = line_directive_map.get((violation.file, violation.line))
        if directive is None:
            return False
        if directive.ignore_all:
            return True
        return violation.rule_id in directive.ignored_rules
