"""ルール判定の抽象インターフェイス

ルール具象クラスへの直接依存を排除し、新規ルール追加時の変更を局所化する。
"""

from typing import Protocol, runtime_checkable

from paladin.lint.types import RuleMeta, SourceFile, Violation


@runtime_checkable
class Rule(Protocol):
    """単一ルール判定の抽象インターフェイス"""

    @property
    def meta(self) -> RuleMeta:
        """ルールのメタ情報を返す"""
        ...

    def check(self, source_file: SourceFile) -> tuple[Violation, ...]:
        """単一ファイルに対する違反判定を行う

        Args:
            source_file: 検査対象のソースファイル

        Returns:
            違反がなければ空タプル、違反があれば Violation のタプル
        """
        ...
