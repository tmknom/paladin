"""Check層の実行時パラメータ

CLIから受け取ったパラメータを不変のまま処理完了まで保持する。
"""

from dataclasses import dataclass, field
from pathlib import Path

from paladin.check.types import OutputFormat
from paladin.config import PerFileIgnoreEntry


@dataclass(frozen=True)
class CheckContext:
    """Check処理の実行時コンテキスト

    Lifecycle:
        処理開始時に生成され、処理完了まで不変のまま保持される

    Attributes:
        targets: CLIから受け取ったターゲットパス群（ファイルまたはディレクトリ）
        format: チェック結果の出力フォーマット
        ignore_rules: 無視するルールID群
        include: 解析対象パスのincludeパターン群
        exclude: 解析対象パスのexcludeパターン群
        rules: ルールの有効/無効設定
        per_file_ignores: ファイルごとのignore設定
    """

    targets: tuple[Path, ...]
    format: OutputFormat = OutputFormat.TEXT
    ignore_rules: frozenset[str] = frozenset()
    include: tuple[str, ...] = ()
    exclude: tuple[str, ...] = ()
    rules: dict[str, bool] = field(default_factory=lambda: {})
    per_file_ignores: tuple[PerFileIgnoreEntry, ...] = ()
