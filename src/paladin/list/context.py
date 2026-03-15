"""List層の実行時パラメータ

CLIから受け取ったパラメータを不変のまま処理完了まで保持する。
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ListContext:
    """List処理の実行時コンテキスト

    現時点ではフィールドなし。将来 --format 等を追加する余地がある。
    """
