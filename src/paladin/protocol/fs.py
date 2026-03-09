"""ファイルシステム操作のプロトコル定義（OnionアーキテクチャのPort）

ビジネスロジック層と基盤層の境界を定義する抽象インターフェース。
複数の機能パッケージ（feature/）および基盤パッケージ（foundation/）から参照される。
"""

from pathlib import Path
from typing import Protocol


class TextFileSystemReaderProtocol(Protocol):
    """ファイルシステム読み取り専用プロトコル

    ファイル内容の読み込み機能のみを提供します。
    """

    def read(self, file_path: Path) -> str:
        """テキストファイルを文字列で読み込む

        Args:
            file_path: 読み込み対象のファイルパス

        Returns:
            ファイルの内容

        Raises:
            FileSystemError: ファイルシステムエラー時
        """
        ...


class TextFileSystemWriterProtocol(Protocol):
    """ファイルシステム書き込み専用プロトコル

    ファイル内容の書き込み機能のみを提供します。
    """

    def write(self, text: str, file_path: Path) -> None:
        """テキスト内容をファイルに書き込む

        Args:
            text: 書き込む文字列
            file_path: 書き込み先のファイルパス

        Raises:
            FileSystemError: ファイルシステムエラー時
        """
        ...
