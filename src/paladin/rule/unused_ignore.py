"""未使用 Ignore コメントを検出するルール

ルール ID を指定した Ignore コメント（`# paladin: ignore[rule-id]` /
`# paladin: ignore-file[rule-id]`）のうち、対応する違反が実際には存在しないものを検出する。
"""

import re
from dataclasses import dataclass
from pathlib import Path

from paladin.rule.types import RuleMeta, SourceFile, Violation, Violations


@dataclass(frozen=True)
class IgnoreDirectiveEntry:
    """個別の Ignore ディレクティブの中間表現"""

    file_path: Path
    line: int
    rule_id: str
    is_file_ignore: bool
    target_line: int = 0


class IgnoreDirectiveCollector:
    """ソースファイルから Ignore ディレクティブを収集する"""

    _FILE_IGNORE_PATTERN = re.compile(r"^\s*# paladin: ignore-file\[([^\]]+)\](\s+--\s.*)?$")
    _INLINE_PRECEDING_PATTERN = re.compile(r"^\s*# paladin: ignore\[([^\]]+)\](\s+--\s.*)?$")
    _INLINE_TRAILING_PATTERN = re.compile(r"\s+# paladin: ignore\[([^\]]+)\](\s+--\s.*)?$")

    @staticmethod
    def collect(source_file: SourceFile) -> tuple[IgnoreDirectiveEntry, ...]:
        """ソースファイルから Ignore ディレクティブを収集する"""
        entries: list[IgnoreDirectiveEntry] = []
        lines = source_file.source.splitlines()

        for i, line in enumerate(lines):
            line_number = i + 1
            IgnoreDirectiveCollector._collect_line(source_file, line, line_number, entries)

        return tuple(entries)

    @staticmethod
    def _collect_line(
        source_file: SourceFile,
        line: str,
        line_number: int,
        entries: list[IgnoreDirectiveEntry],
    ) -> None:
        """1行から Ignore ディレクティブを収集してentriesに追加する"""
        file_ignore_match = IgnoreDirectiveCollector._FILE_IGNORE_PATTERN.match(line)
        if file_ignore_match:
            rule_ids = (r.strip() for r in file_ignore_match.group(1).split(","))
            entries.extend(
                IgnoreDirectiveEntry(
                    file_path=source_file.file_path,
                    line=line_number,
                    rule_id=rule_id,
                    is_file_ignore=True,
                )
                for rule_id in rule_ids
            )
            return

        preceding_match = IgnoreDirectiveCollector._INLINE_PRECEDING_PATTERN.match(line)
        if preceding_match:
            rule_ids = (r.strip() for r in preceding_match.group(1).split(","))
            entries.extend(
                IgnoreDirectiveEntry(
                    file_path=source_file.file_path,
                    line=line_number,
                    rule_id=rule_id,
                    is_file_ignore=False,
                    target_line=line_number + 1,
                )
                for rule_id in rule_ids
            )
            return

        trailing_match = IgnoreDirectiveCollector._INLINE_TRAILING_PATTERN.search(line)
        if trailing_match:
            rule_ids = (r.strip() for r in trailing_match.group(1).split(","))
            entries.extend(
                IgnoreDirectiveEntry(
                    file_path=source_file.file_path,
                    line=line_number,
                    rule_id=rule_id,
                    is_file_ignore=False,
                    target_line=line_number,
                )
                for rule_id in rule_ids
            )


class UnusedIgnoreDetector:
    """生の違反リストと Ignore ディレクティブを照合し、未使用の Ignore を検出する"""

    @staticmethod
    def detect(
        entries: tuple[IgnoreDirectiveEntry, ...],
        raw_violations: Violations,
        disabled_rule_ids: frozenset[str],
        source_file: SourceFile,
        meta: RuleMeta,
    ) -> tuple[Violation, ...]:
        """未使用 Ignore ディレクティブを Violation として返す"""
        violations: list[Violation] = []
        for entry in entries:
            if entry.rule_id in disabled_rule_ids:
                continue
            if not UnusedIgnoreDetector._is_used(entry, raw_violations):
                violations.append(UnusedIgnoreDetector._make_violation(entry, source_file, meta))
        return tuple(violations)

    @staticmethod
    def _is_used(entry: IgnoreDirectiveEntry, raw_violations: Violations) -> bool:
        """Ignore ディレクティブが実際に使用されているか確認する"""
        if entry.is_file_ignore:
            return any(
                v.file == entry.file_path and v.rule_id == entry.rule_id for v in raw_violations
            )
        return any(
            v.file == entry.file_path and v.line == entry.target_line and v.rule_id == entry.rule_id
            for v in raw_violations
        )

    @staticmethod
    def _make_violation(
        entry: IgnoreDirectiveEntry, source_file: SourceFile, meta: RuleMeta
    ) -> Violation:
        """未使用 Ignore ディレクティブの Violation を生成する"""
        if entry.is_file_ignore:
            message = (
                f"`# paladin: ignore-file` コメントで指定されたルール `{entry.rule_id}` は、"
                "ファイル内で違反を検出していません"
            )
        else:
            message = (
                f"`# paladin: ignore` コメントで指定されたルール `{entry.rule_id}` は、"
                "対象行で違反を検出していません"
            )
        return meta.create_violation_at(
            location=source_file.location(line=entry.line),
            message=message,
            reason="未使用の Ignore コメントはコードの可読性を低下させ、存在しない違反があるという誤解を招きます",
            suggestion=f"不要なルール ID `{entry.rule_id}` を Ignore コメントから削除してください",
        )


class UnusedIgnoreRule:
    """未使用 Ignore コメントを検出するルール"""

    def __init__(self) -> None:
        """ルールを初期化する"""
        self._meta = RuleMeta(
            rule_id="unused-ignore",
            rule_name="Unused Ignore",
            summary="使用されていない Ignore コメントを検出する",
            intent="不要な Ignore コメントを削除してコードの意図を明確にする",
            guidance="各 Ignore コメントに対応する違反が存在することを確認する",
            suggestion="対応する違反がない Ignore コメントを削除してください",
        )

    @property
    def meta(self) -> RuleMeta:
        """ルールのメタ情報を返す"""
        return self._meta

    def check(
        self,
        source_file: SourceFile,
        raw_violations: Violations,
        disabled_rule_ids: frozenset[str] = frozenset(),
    ) -> tuple[Violation, ...]:
        """未使用 Ignore コメントを検出する"""
        entries = IgnoreDirectiveCollector.collect(source_file)
        return UnusedIgnoreDetector.detect(
            entries, raw_violations, disabled_rule_ids, source_file, self._meta
        )
