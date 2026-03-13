"""ルールドメインの型定義"""

from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path


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
