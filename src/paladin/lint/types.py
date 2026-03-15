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
