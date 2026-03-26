"""Listパッケージの実行時コンテキスト

CLIから受け取ったパラメータを不変のまま処理完了まで保持する。
"""

from dataclasses import dataclass, field

from paladin.foundation.output import OutputFormat


@dataclass(frozen=True)
class ListContext:
    """List処理の実行時パラメータを保持する値オブジェクト

    Attributes:
        format: 出力フォーマット（text または json）。
    """

    format: OutputFormat = field(default=OutputFormat.TEXT)
