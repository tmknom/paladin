"""View層の実行時パラメータ

CLIから受け取ったパラメータを不変のまま処理完了まで保持する。
"""

from dataclasses import dataclass, field

from paladin.foundation.output import OutputFormat


@dataclass(frozen=True)
class ViewContext:
    """View処理の実行時コンテキスト

    Attributes:
        rule_id: 詳細表示する対象の rule_id（必須）
        format: 出力形式（デフォルト: TEXT）
    """

    rule_id: str
    format: OutputFormat = field(default=OutputFormat.TEXT)
