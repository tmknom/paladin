"""Rules層の実行時パラメータ

CLIから受け取ったパラメータを不変のまま処理完了まで保持する。
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class RulesContext:
    """Rules処理の実行時コンテキスト

    Attributes:
        rule_id: 詳細表示する対象の rule_id。None の場合は全ルール一覧を表示する
    """

    rule_id: str | None = None
