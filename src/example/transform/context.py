"""Transform処理の実行時パラメータを保持する値オブジェクト

変換処理に必要な入力ファイル、出力先、実行日時を保持する。
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class TransformContext:
    """Transform処理の実行時コンテキスト

    Lifecycle:
        処理開始時に生成され、処理完了まで不変のまま保持される

    Attributes:
        target_file: 変換対象のテキストファイルパス
        tmp_dir: 一時ディレクトリパス（出力先の親ディレクトリ）
        current_datetime: 現在日時（変換結果の先頭に付与される）
    """

    target_file: Path
    tmp_dir: Path
    current_datetime: datetime
