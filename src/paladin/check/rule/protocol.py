"""Rule Protocolの定義"""

from typing import Protocol, runtime_checkable

from paladin.check.types import ParsedFile, RuleMeta, Violation


@runtime_checkable
class Rule(Protocol):
    """単一ルール判定の抽象インターフェイス"""

    @property
    def meta(self) -> RuleMeta:
        """ルールのメタ情報を返す"""
        ...

    def check(self, parsed_file: ParsedFile) -> tuple[Violation, ...]:
        """単一ファイルに対する違反判定を行う

        Args:
            parsed_file: 解析対象ファイル

        Returns:
            違反がなければ空タプル、違反があれば Violation のタプル
        """
        ...
