from pathlib import Path


class InMemoryFsReader:
    """TextFileSystemReaderProtocol の InMemory 実装"""

    def __init__(self, content: str = ""):
        self.content = content
        self.read_path: Path | None = None

    def read(self, file_path: Path) -> str:
        self.read_path = file_path
        return self.content


class InMemoryFsWriter:
    """TextFileSystemWriterProtocol の InMemory 実装"""

    def __init__(self):
        self.written_text: str | None = None
        self.written_path: Path | None = None

    def write(self, text: str, file_path: Path) -> None:
        self.written_text = text
        self.written_path = file_path
