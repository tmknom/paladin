"""Check層の実行時パラメータ

CLIから受け取ったパラメータを不変のまま処理完了まで保持する。
"""

from dataclasses import dataclass
from pathlib import Path

from paladin.check.types import OutputFormat


@dataclass(frozen=True)
class CheckContext:
    """Check処理の実行時コンテキスト

    Lifecycle:
        処理開始時に生成され、処理完了まで不変のまま保持される

    Attributes:
        targets: CLIから受け取ったターゲットパス群（ファイルまたはディレクトリ）
        format: チェック結果の出力フォーマット
    """

    targets: tuple[Path, ...]
    format: OutputFormat = OutputFormat.TEXT
