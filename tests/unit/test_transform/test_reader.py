from pathlib import Path

from example.transform.reader import TextReader
from example.transform.types import SrcText
from tests.unit.test_transform.fakes import InMemoryFsReader


class TestTextReader:
    """TextReaderクラスのテスト"""

    def test_read_正常系_指定パスのコンテンツを返すこと(self):
        # Arrange
        path = Path("some/file.txt")
        fs_reader = InMemoryFsReader(content="test content")
        reader = TextReader(fs_reader)

        # Act
        result = reader.read(path)

        # Assert
        assert result == SrcText("test content")
        assert fs_reader.read_path == path
