"""ファイル単位の Ignore 機能

ファイル先頭コメントから ignore-file ディレクティブを抽出し、
Violations から該当違反を除外する。
"""

import re
from dataclasses import dataclass
from pathlib import Path

from paladin.lint.types import Violation, Violations
from paladin.source.types import ParsedFiles


@dataclass(frozen=True)
class FileIgnoreDirective:
    """単一ファイルの ignore-file ディレクティブ情報を保持する値オブジェクト"""

    file_path: Path
    ignore_all: bool
    ignored_rules: frozenset[str]


class FileIgnoreParser:
    """ソーステキストの先頭コメントから ignore-file ディレクティブを抽出するパーサー"""

    _DIRECTIVE_PATTERN = re.compile(r"^# paladin: ignore-file(\[(.+)\])?$")
    _SHEBANG_PATTERN = re.compile(r"^#!")
    _ENCODING_PATTERN = re.compile(r"# -\*- coding:")

    def parse(self, file_path: Path, source: str) -> FileIgnoreDirective:
        """ソーステキストのヘッダー領域から ignore-file ディレクティブを抽出する

        Args:
            file_path: 対象ファイルのパス
            source: ソーステキスト

        Returns:
            FileIgnoreDirective。ディレクティブなしの場合は ignore_all=False、ignored_rules=frozenset()
        """
        lines = source.splitlines()
        i = 0
        in_docstring = False
        docstring_quote = ""

        while i < len(lines):
            line = lines[i]
            stripped = line.strip()

            # docstring 内をスキップ
            if in_docstring:
                if docstring_quote in line:
                    in_docstring = False
                i += 1
                continue

            # 空行をスキップ
            if stripped == "":
                i += 1
                continue

            # shebang 行をスキップ
            if self._SHEBANG_PATTERN.match(stripped):
                i += 1
                continue

            # エンコーディング宣言をスキップ
            if self._ENCODING_PATTERN.search(stripped):
                i += 1
                continue

            # docstring 開始の検出
            if stripped.startswith('"""') or stripped.startswith("'''"):
                docstring_quote = stripped[:3]
                # 同一行で閉じている場合
                rest = stripped[3:]
                if docstring_quote in rest:
                    i += 1
                    continue
                in_docstring = True
                i += 1
                continue

            # ignore-file ディレクティブの検出
            match = self._DIRECTIVE_PATTERN.match(stripped)
            if match:
                rule_spec = match.group(2)
                if rule_spec is None:
                    return FileIgnoreDirective(
                        file_path=file_path,
                        ignore_all=True,
                        ignored_rules=frozenset(),
                    )
                rules = frozenset(r.strip() for r in rule_spec.split(","))
                return FileIgnoreDirective(
                    file_path=file_path,
                    ignore_all=False,
                    ignored_rules=rules,
                )

            # 通常コメント行（# paladin: ではない）をスキップ
            if stripped.startswith("#"):
                i += 1
                continue

            # ヘッダー領域外（import 文や実行コードなど）に到達したら走査終了
            break

        return FileIgnoreDirective(
            file_path=file_path,
            ignore_all=False,
            ignored_rules=frozenset(),
        )

    def parse_all(self, parsed_files: ParsedFiles) -> tuple[FileIgnoreDirective, ...]:
        """複数ファイルのディレクティブをタプルで返す

        Args:
            parsed_files: 解析済みファイル群

        Returns:
            各ファイルの FileIgnoreDirective のタプル
        """
        return tuple(self.parse(pf.file_path, pf.source) for pf in parsed_files)


class ViolationFilter:
    """FileIgnoreDirective に基づいて Violations から ignore 対象の違反を除外するフィルター"""

    def filter(
        self,
        violations: Violations,
        directives: tuple[FileIgnoreDirective, ...],
    ) -> Violations:
        """Ignore 対象の違反を除外した新しい Violations を返す

        Args:
            violations: フィルタリング対象の違反群
            directives: ファイルごとの ignore ディレクティブ群

        Returns:
            ignore 対象を除外した Violations
        """
        directive_map = {d.file_path: d for d in directives}
        filtered = tuple(v for v in violations if not self._should_ignore(v, directive_map))
        return Violations(items=filtered)

    def _should_ignore(
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
