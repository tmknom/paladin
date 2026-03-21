import ast
from pathlib import Path

import pytest

from paladin.check.parser import AstParser
from paladin.check.types import TargetFiles
from paladin.foundation.fs import FileSystemError
from paladin.rule import SourceFile
from tests.unit.fakes import ErrorFsReader, InMemoryFsReader


class TestAstParserParse:
    """AstParser.parse() のテスト"""

    def test_parse_正常系_SourceFileにソーステキストが保持されること(self):
        # Arrange
        reader = InMemoryFsReader(contents={"test.py": "x = 1\n"})
        parser = AstParser(reader=reader)

        # Act
        result = parser.parse(Path("test.py"))

        # Assert
        assert result.source == "x = 1\n"

    def test_parse_正常系_有効なPythonコードからSourceFileを返すこと(self):
        # Arrange
        reader = InMemoryFsReader(contents={"test.py": "x = 1\n"})
        parser = AstParser(reader=reader)

        # Act
        result = parser.parse(Path("test.py"))

        # Assert
        assert isinstance(result, SourceFile)
        assert result.file_path == Path("test.py")
        assert isinstance(result.tree, ast.Module)

    def test_parse_異常系_構文エラーのPythonコードでSyntaxErrorを送出すること(self):
        # Arrange
        reader = InMemoryFsReader(contents={"test.py": "def :\n"})
        parser = AstParser(reader=reader)

        # Act / Assert
        with pytest.raises(SyntaxError):
            parser.parse(Path("test.py"))

    def test_parse_異常系_ファイル読み込み失敗でFileSystemErrorが伝播すること(self):
        # Arrange
        parser = AstParser(
            reader=ErrorFsReader(FileSystemError(message="読み込み失敗", cause="read error"))
        )

        # Act / Assert
        with pytest.raises(FileSystemError):
            parser.parse(Path("test.py"))


class TestAstParserParseAll:
    """AstParser.parse_all() のテスト"""

    def test_parse_all_正常系_複数ファイルをSourceFilesとして返すこと(self):
        # Arrange
        reader = InMemoryFsReader(contents={"a.py": "x = 1\n", "b.py": "y = 2\n"})
        parser = AstParser(reader=reader)
        target_files = TargetFiles(files=(Path("a.py"), Path("b.py")))

        # Act
        result = parser.parse_all(target_files)

        # Assert
        assert len(result) == 2

    def test_parse_all_エッジケース_空のTargetFilesで空のSourceFilesを返すこと(self):
        # Arrange
        reader = InMemoryFsReader(contents={})
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
