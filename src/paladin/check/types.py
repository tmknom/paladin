"""Check向けドメインモデル定義"""

from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class TargetFiles:
    """列挙された解析対象ファイル群を保持する不変な値オブジェクト

    Constraints:
        - インスタンス生成後は変更不可（frozen=True）
        - files は重複排除・ソート済みであることを前提とする
    """

    files: tuple[Path, ...]
    """重複排除・ソート済みの .py ファイルパス群"""

    def __len__(self) -> int:
        """ファイル数を返す

        Returns:
            列挙されたファイルの件数
        """
        return len(self.files)

    def __iter__(self) -> Iterator[Path]:
        """ファイルパスをイテレーションする

        Returns:
            ファイルパスのイテレータ
        """
        return iter(self.files)


@dataclass(frozen=True)
class CheckResult:
    """Check処理の実行結果を保持する不変オブジェクト

    Constraints:
        - インスタンス生成後は変更不可（frozen=True）
    """

    target_files: TargetFiles
    """列挙された解析対象ファイル群"""
