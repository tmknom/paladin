"""ルールドメインの型定義

ルール判定の入出力・メタ情報・検査対象を表す値オブジェクトを定義する。
"""

from __future__ import annotations

import ast
from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass
from pathlib import Path

from paladin.rule.import_statement import AbsoluteFromImport, ImportStatement, SourceLocation


def _collect_imports(nodes: Iterable[ast.AST]) -> tuple[ImportStatement, ...]:
    """AST ノード列からインポート文を収集して返す"""
    result: list[ImportStatement] = []
    for node in nodes:
        if isinstance(node, ast.ImportFrom):
            result.append(ImportStatement.from_import_from(node))
        elif isinstance(node, ast.Import):
            result.append(ImportStatement.from_import(node))
    return tuple(result)


@dataclass(frozen=True)
class SourceFile:
    """単一Pythonソースファイルの情報を保持する不変な値オブジェクト"""

    file_path: Path
    tree: ast.Module
    source: str

    @property
    def is_init_py(self) -> bool:
        """__init__.py かどうかを返す"""
        return self.file_path.name == "__init__.py"

    @property
    def is_test_file(self) -> bool:
        """tests/ 配下のファイルかどうかを返す"""
        return "tests" in self.file_path.parts

    def get_line(self, lineno: int) -> str:
        """指定した行番号（1-based）のソース行テキストを返す（前後空白は strip 済み）"""
        lines = self.source.splitlines()
        if 1 <= lineno <= len(lines):
            return lines[lineno - 1].strip()
        return ""

    @property
    def imports(self) -> tuple[ImportStatement, ...]:
        """全インポート文を抽出して返す（AST 全走査）"""
        return _collect_imports(ast.walk(self.tree))

    @property
    def top_level_imports(self) -> tuple[ImportStatement, ...]:
        """トップレベルのインポート文のみを抽出して返す"""
        return _collect_imports(self.tree.body)

    @property
    def absolute_from_imports(self) -> tuple[AbsoluteFromImport, ...]:
        """絶対 from import 文のみを抽出して返す"""
        return tuple(
            AbsoluteFromImport(
                module=stmt.module,
                names=stmt.names,
                line=stmt.line,
                column=stmt.column,
            )
            for stmt in self.imports
            if stmt.is_absolute_from_import and stmt.module is not None
        )

    def location(self, line: int, column: int = 0) -> SourceLocation:
        """指定した行・列の SourceLocation を返す"""
        return SourceLocation(file=self.file_path, line=line, column=column)

    def location_from(self, stmt: ImportStatement | AbsoluteFromImport) -> SourceLocation:
        """ImportStatement または AbsoluteFromImport の位置から SourceLocation を返す"""
        return SourceLocation(file=self.file_path, line=stmt.line, column=stmt.column)


@dataclass(frozen=True)
class SourceFiles:
    """複数Pythonソースファイルを集約する不変な値オブジェクト"""

    files: tuple[SourceFile, ...]

    def __len__(self) -> int:
        """ソースファイル数を返す"""
        return len(self.files)

    def __iter__(self) -> Iterator[SourceFile]:
        """ソースファイルをイテレーションする"""
        return iter(self.files)

    def init_files(self) -> Iterator[SourceFile]:
        """__init__.py のみをイテレーションする"""
        return (f for f in self.files if f.is_init_py)

    def production_files(self) -> Iterator[SourceFile]:
        """tests/ 以外のファイルをイテレーションする"""
        return (f for f in self.files if not f.is_test_file)


@dataclass(frozen=True)
class Violation:
    """単一ルール違反の情報を保持する値オブジェクト"""

    file: Path
    line: int
    column: int
    rule_id: str
    rule_name: str
    message: str
    reason: str
    suggestion: str


@dataclass(frozen=True)
class Violations:
    """複数Violationを集約する値オブジェクト"""

    items: tuple[Violation, ...]

    def __len__(self) -> int:
        """違反件数を返す"""
        return len(self.items)

    def __iter__(self) -> Iterator[Violation]:
        """Violationをイテレーションする"""
        return iter(self.items)


@dataclass(frozen=True)
class RuleMeta:
    """ルールのメタ情報を保持する値オブジェクト"""

    rule_id: str
    rule_name: str
    summary: str
    intent: str
    guidance: str
    suggestion: str

    def create_violation_at(
        self,
        location: SourceLocation,
        message: str,
        reason: str,
        suggestion: str,
    ) -> Violation:
        """SourceLocation を受け取り Violation を生成する"""
        return Violation(
            file=location.file,
            line=location.line,
            column=location.column,
            rule_id=self.rule_id,
            rule_name=self.rule_name,
            message=message,
            reason=reason,
            suggestion=suggestion,
        )


@dataclass(frozen=True)
class OverrideEntry:
    """[[tool.paladin.overrides]] の単一エントリを保持する値オブジェクト"""

    files: tuple[str, ...]
    rules: Mapping[str, bool]


@dataclass(frozen=True)
class PerFileIgnoreEntry:
    """per-file-ignores の単一エントリを保持する値オブジェクト"""

    pattern: str
    rule_ids: frozenset[str]
    ignore_all: bool  # ["*"] 指定時に True
