import ast
from pathlib import Path

import pytest

from paladin.check.parser import AstParser
from paladin.check.types import TargetFiles
from paladin.foundation.fs.error import FileSystemError
from paladin.source.types import ParsedFile
from tests.unit.test_check.fakes import InMemoryFsReader


class TestAstParserParse:
    """AstParser.parse() のテスト"""

    def test_parse_正常系_ParsedFileにソーステキストが保持されること(self):
        # Arrange
        reader = InMemoryFsReader(content="x = 1\n")
        parser = AstParser(reader=reader)

        # Act
        result = parser.parse(Path("test.py"))

        # Assert
        assert result.source == "x = 1\n"

    def test_parse_正常系_有効なPythonコードからParsedFileを返すこと(self):
        # Arrange
        reader = InMemoryFsReader(content="x = 1\n")
        parser = AstParser(reader=reader)

        # Act
        result = parser.parse(Path("test.py"))

        # Assert
        assert isinstance(result, ParsedFile)
        assert result.file_path == Path("test.py")
        assert isinstance(result.tree, ast.Module)

    def test_parse_異常系_構文エラーのPythonコードでSyntaxErrorを送出すること(self):
        # Arrange
        reader = InMemoryFsReader(content="def :\n")
        parser = AstParser(reader=reader)

        # Act / Assert
        with pytest.raises(SyntaxError):
            parser.parse(Path("test.py"))

    def test_parse_異常系_ファイル読み込み失敗でFileSystemErrorが伝播すること(self):
        # Arrange
        reader = InMemoryFsReader(error=FileSystemError(message="読み込み失敗", cause="read error"))
        parser = AstParser(reader=reader)

        # Act / Assert
        with pytest.raises(FileSystemError):
            parser.parse(Path("test.py"))


class TestAstParserParseAll:
    """AstParser.parse_all() のテスト"""

    def test_parse_all_正常系_複数ファイルをParsedFilesとして返すこと(self):
        # Arrange
        reader = InMemoryFsReader(contents={"a.py": "x = 1\n", "b.py": "y = 2\n"})
        parser = AstParser(reader=reader)
        target_files = TargetFiles(files=(Path("a.py"), Path("b.py")))

        # Act
        result = parser.parse_all(target_files)

        # Assert
        assert len(result) == 2

    def test_parse_all_エッジケース_空のTargetFilesで空のParsedFilesを返すこと(self):
        # Arrange
        reader = InMemoryFsReader()
        parser = AstParser(reader=reader)
        target_files = TargetFiles(files=())

        # Act
        result = parser.parse_all(target_files)

        # Assert
        assert len(result) == 0

    def test_parse_all_異常系_最初のエラーで即座に停止すること(self):
        # Arrange
        reader = InMemoryFsReader(contents={"a.py": "def :\n", "b.py": "y = 2\n"})
        parser = AstParser(reader=reader)
        target_files = TargetFiles(files=(Path("a.py"), Path("b.py")))

        # Act / Assert
        with pytest.raises(SyntaxError):
            parser.parse_all(target_files)
        assert len(reader.read_paths) == 1
