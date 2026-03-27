"""TextFileSystemReaderProtocol の InMemory 実装"""

from pathlib import Path

from paladin.foundation.fs import FileSystemError

FileContents = dict[str, str]
"""パス文字列をキー、ファイル内容を値とする辞書"""


class InMemoryFsReader:
    """TextFileSystemReaderProtocol の InMemory 実装"""

    def __init__(self, contents: FileContents) -> None:
        self._contents = contents

    def read(self, file_path: Path) -> str:
        return self._contents[str(file_path)]


class ErrorFsReader:
    """read() が常に FileSystemError を送出する Fake"""

    def __init__(self, error: FileSystemError) -> None:
        self._error = error

    def read(self, file_path: Path) -> str:
        raise self._error
