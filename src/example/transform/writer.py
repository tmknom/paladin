"""Transform層の出力を担当する薄いラッパー

基盤層への委譲のみを行い、例外処理やデータ変換は行わない。
"""

from pathlib import Path

from example.foundation.log import log
from example.protocol.fs import TextFileSystemWriterProtocol
from example.transform.types import DstText


class TextWriter:
    """変換済みテキストを指定パスへ書き出す

    基盤層への薄いラッパー。例外処理は行わず、そのまま伝播させる。
    """

    def __init__(
        self,
        fs_writer: TextFileSystemWriterProtocol,
    ):
        """TextWriterインスタンスを初期化

        Args:
            fs_writer: ファイルシステム書き込み
        """
        self.fs_writer = fs_writer

    @log
    def write(self, text: DstText, path: Path) -> None:
        """テキストをファイルに保存

        指定されたテキストをそのままテキストファイルに保存します。
        基盤層のTextFileSystemWriterに委譲し、例外はそのまま伝播させます。

        Args:
            text: 保存するテキスト（str型）
            path: 保存先ファイルパス

        Raises:
            FileSystemError: ファイルシステムでエラーが発生した場合
        """
        self.fs_writer.write(str(text), path)
