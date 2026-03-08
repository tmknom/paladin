"""ファイルシステム操作クラス（Adapter実装）"""

from pathlib import Path

from example.foundation.fs.error import FileSystemError
from example.protocol.fs import TextFileSystemReaderProtocol, TextFileSystemWriterProtocol


class TextFileSystemReader(TextFileSystemReaderProtocol):
    """ファイル読み取り専用クラス

    ファイルシステムからのテキストファイル読み取り機能のみを提供します。
    """

    def read(self, file_path: Path) -> str:
        """テキストファイルの内容を読み込み、文字列で返す

        Args:
            file_path: 読み込み対象のファイルパス

        Returns:
            ファイルの内容（改行文字を含む、フィルタリングなし）

        Raises:
            FileSystemError: ファイルシステムでエラーが発生した場合
        """
        try:
            with file_path.open(encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError as e:
            raise FileSystemError(
                message=f"ファイルが見つかりません: {file_path}",
                cause=e,
            ) from e
        except Exception as e:
            raise FileSystemError(
                message=f"ファイル読み込み中にエラーが発生しました: {file_path}",
                cause=e,
            ) from e


class TextFileSystemWriter(TextFileSystemWriterProtocol):
    """ファイル書き込み専用クラス

    ファイルシステムへのテキストファイル書き込み機能のみを提供します。
    """

    def write(self, text: str, file_path: Path) -> None:
        """テキスト内容をファイルに書き込む

        書き込み先のディレクトリが存在しない場合は自動的に作成します。

        Args:
            text: 書き込む文字列
            file_path: 書き込み先のファイルパス

        Raises:
            FileSystemError: ファイルシステムでエラーが発生した場合
        """
        self._ensure_parent_directory(file_path)
        self._write_content(text, file_path)

    def _ensure_parent_directory(self, file_path: Path) -> None:
        """親ディレクトリの存在を保証する

        Args:
            file_path: ファイルパス

        Raises:
            FileSystemError: ディレクトリ作成でエラーが発生した場合
        """
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
        except PermissionError as e:
            raise FileSystemError(
                message=f"ディレクトリの作成権限がありません: {file_path.parent}",
                cause=e,
            ) from e
        except Exception as e:
            raise FileSystemError(
                message=f"ディレクトリの作成に失敗しました: {file_path.parent}",
                cause=e,
            ) from e

    def _write_content(self, text: str, file_path: Path) -> None:
        """ファイルに内容を書き込む

        Args:
            text: 書き込む文字列
            file_path: 書き込み先のファイルパス

        Raises:
            FileSystemError: ファイル書き込みでエラーが発生した場合
        """
        try:
            with file_path.open("w", encoding="utf-8") as f:
                f.write(text)
        except PermissionError as e:
            raise FileSystemError(
                message=f"ファイルへの書き込み権限がありません: {file_path}",
                cause=e,
            ) from e
        except IsADirectoryError as e:
            raise FileSystemError(
                message=f"指定されたパスはディレクトリです: {file_path}",
                cause=e,
            ) from e
        except Exception as e:
            raise FileSystemError(
                message=f"ファイル書き込み中にエラーが発生しました: {file_path}",
                cause=e,
            ) from e
