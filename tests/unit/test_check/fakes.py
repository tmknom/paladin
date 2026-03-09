"""check パッケージ用の Fake 実装"""

from pathlib import Path


class InMemoryFsReader:
    """TextFileSystemReaderProtocol の InMemory 実装"""

    def __init__(
        self,
        content: str = "",
        contents: dict[str, str] | None = None,
        error: Exception | None = None,
    ) -> None:
        self.content = content
        self.contents = contents
        self.error = error
        self.read_paths: list[Path] = []

    def read(self, file_path: Path) -> str:
        """ファイルを読み込む（InMemory実装）"""
        self.read_paths.append(file_path)
        if self.error is not None:
            raise self.error
        if self.contents is not None:
            return self.contents[str(file_path)]
        return self.content
