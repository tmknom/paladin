import ast
from pathlib import Path

from paladin.check.types import ParsedFile, ParsedFiles, TargetFiles


class TestTargetFiles:
    """TargetFilesクラスのテスト"""

    def test_len_正常系_ファイル数を返すこと(self):
        # Arrange
        target_files = TargetFiles(files=(Path("a.py"), Path("b.py")))

        # Act
        result = len(target_files)

        # Assert
        assert result == 2

    def test_iter_正常系_ファイルパスをイテレーションできること(self):
        # Arrange
        paths = (Path("a.py"), Path("b.py"))
        target_files = TargetFiles(files=paths)

        # Act
        result = list(target_files)

        # Assert
        assert result == [Path("a.py"), Path("b.py")]

    def test_len_エッジケース_空のファイル群で0を返すこと(self):
        # Arrange
        target_files = TargetFiles(files=())

        # Act
        result = len(target_files)

        # Assert
        assert result == 0


class TestParsedFile:
    """ParsedFileクラスのテスト"""

    def test_init_正常系_file_pathとtreeを保持すること(self):
        # Arrange
        tree = ast.parse("x = 1\n")

        # Act
        result = ParsedFile(file_path=Path("test.py"), tree=tree)

        # Assert
        assert result.file_path == Path("test.py")
        assert isinstance(result.tree, ast.Module)


class TestParsedFiles:
    """ParsedFilesクラスのテスト"""

    def test_len_正常系_ファイル数を返すこと(self):
        # Arrange
        tree = ast.parse("x = 1\n")
        parsed_files = ParsedFiles(
            files=(
                ParsedFile(file_path=Path("a.py"), tree=tree),
                ParsedFile(file_path=Path("b.py"), tree=tree),
            )
        )

        # Act
        result = len(parsed_files)

        # Assert
        assert result == 2

    def test_iter_正常系_ParsedFileをイテレーションできること(self):
        # Arrange
        tree = ast.parse("x = 1\n")
        pf_a = ParsedFile(file_path=Path("a.py"), tree=tree)
        pf_b = ParsedFile(file_path=Path("b.py"), tree=tree)
        parsed_files = ParsedFiles(files=(pf_a, pf_b))

        # Act
        result = list(parsed_files)

        # Assert
        assert result == [pf_a, pf_b]

    def test_len_エッジケース_空で0を返すこと(self):
        # Arrange
        parsed_files = ParsedFiles(files=())

        # Act
        result = len(parsed_files)

        # Assert
        assert result == 0
