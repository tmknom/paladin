"""ルールドメインの型定義

ルール判定の入出力・メタ情報・検査対象を表す値オブジェクトを定義する。
"""

import ast
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path


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

    def create_violation(
        self,
        file: Path,
        line: int,
        column: int,
        message: str,
        reason: str,
        suggestion: str,
    ) -> Violation:
        """rule_id, rule_name を自動補完して Violation を生成する"""
        return Violation(
            file=file,
            line=line,
            column=column,
            rule_id=self.rule_id,
            rule_name=self.rule_name,
            message=message,
            reason=reason,
            suggestion=suggestion,
        )
