"""Transform層の入力を担当する薄いラッパー

基盤層への委譲のみを行い、例外処理やデータ変換は行わない。
"""

from pathlib import Path

from example.foundation.log import log
from example.protocol.fs import TextFileSystemReaderProtocol
from example.transform.types import SrcText


class TextReader:
    """テキストファイルを読み込んで文字列として返す

    基盤層への薄いラッパー。例外処理は行わず、そのまま伝播させる。
    """

    def __init__(
        self,
        fs_reader: TextFileSystemReaderProtocol,
    ):
        """初期化

        Args:
            fs_reader: ファイルシステム読み取り
        """
        self.fs_reader = fs_reader

    @log
    def read(self, path: Path) -> SrcText:
        r"""テキストファイルを読み込んで文字列を返す

        指定されたファイルパスのファイルを読み込み、
        文字列として返します。

        Args:
            path: 読み込むテキストファイル

        Returns:
            読み込んだ文字列
        """
        return SrcText(self.fs_reader.read(path))
