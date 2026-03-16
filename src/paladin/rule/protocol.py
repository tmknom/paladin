"""ルール判定の抽象インターフェイス

単一ファイルルール（Rule）および複数ファイルルール（MultiFileRule）の
Protocol を定義する。ルール具象クラスへの直接依存を排除し、
新規ルール追加時の変更を局所化する。
"""

from typing import Protocol, runtime_checkable

from paladin.rule.types import RuleMeta, SourceFile, SourceFiles, Violation


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


@runtime_checkable
class MultiFileRule(Protocol):
    """複数ファイルルール判定の抽象インターフェイス"""

    @property
    def meta(self) -> RuleMeta:
        """ルールのメタ情報を返す"""
        ...

    def check(self, source_files: SourceFiles) -> tuple[Violation, ...]:
        """複数ファイルに対する違反判定を行う

        Args:
            source_files: 検査対象のソースファイル群

        Returns:
            違反がなければ空タプル、違反があれば Violation のタプル
        """
        ...
