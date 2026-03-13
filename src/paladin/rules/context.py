"""Rules処理の実行時パラメータを保持する値オブジェクト"""

from dataclasses import dataclass


@dataclass(frozen=True)
class RulesContext:
    """Rules処理の実行時コンテキスト

    Attributes:
        rule_id: 詳細表示する対象の rule_id。None の場合は全ルール一覧を表示する
    """

    rule_id: str | None = None
