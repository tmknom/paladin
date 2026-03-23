"""FileIgnoreParser / LineIgnoreParser のテスト"""

import ast
from pathlib import Path

from paladin.check.ignore import FileIgnoreParser, LineIgnoreParser
from paladin.rule import SourceFile, SourceFiles


def _make_source_file(source: str, filename: str = "example.py") -> SourceFile:
    return SourceFile(file_path=Path(filename), tree=ast.parse(source), source=source)


class TestFileIgnoreParserParse:
    """FileIgnoreParser.parse() のテスト"""

    def test_parse_正常系_ignore_fileディレクティブで全ルールignoreを返すこと(self):
        # Arrange
        parser = FileIgnoreParser()
        source = "# paladin: ignore-file\nimport os\n"

        # Act
        result = parser.parse(Path("example.py"), source)

        # Assert
        assert result.ignore_all is True
        assert result.ignored_rules == frozenset()
        assert result.file_path == Path("example.py")

    def test_parse_正常系_ignore_file_with_rule_idで特定ルールignoreを返すこと(self):
        # Arrange
        parser = FileIgnoreParser()
        source = "# paladin: ignore-file[rule-a]\nimport os\n"

        # Act
        result = parser.parse(Path("example.py"), source)

        # Assert
        assert result.ignore_all is False
        assert result.ignored_rules == frozenset({"rule-a"})

    def test_parse_正常系_複数ルールIDをカンマ区切りで指定できること(self):
        # Arrange
        parser = FileIgnoreParser()
        source = "# paladin: ignore-file[rule-a, rule-b]\nimport os\n"

        # Act
        result = parser.parse(Path("example.py"), source)

        # Assert
        assert result.ignore_all is False
        assert result.ignored_rules == frozenset({"rule-a", "rule-b"})

    def test_parse_正常系_shebang行の後にディレクティブを検出できること(self):
        # Arrange
        parser = FileIgnoreParser()
        source = "#!/usr/bin/env python3\n# paladin: ignore-file\n"

        # Act
        result = parser.parse(Path("example.py"), source)

        # Assert
        assert result.ignore_all is True

    def test_parse_正常系_エンコーディング宣言の後にディレクティブを検出できること(self):
        # Arrange
        parser = FileIgnoreParser()
        source = "# -*- coding: utf-8 -*-\n# paladin: ignore-file\n"

        # Act
        result = parser.parse(Path("example.py"), source)

        # Assert
        assert result.ignore_all is True

    def test_parse_正常系_通常コメントの後にディレクティブを検出できること(self):
        # Arrange
        parser = FileIgnoreParser()
        source = "# some comment\n# paladin: ignore-file\n"

        # Act
        result = parser.parse(Path("example.py"), source)

        # Assert
        assert result.ignore_all is True

    def test_parse_エッジケース_ディレクティブなしでignore無しを返すこと(self):
        # Arrange
        parser = FileIgnoreParser()
        source = "import os\n"

        # Act
        result = parser.parse(Path("example.py"), source)

        # Assert
        assert result.ignore_all is False
        assert result.ignored_rules == frozenset()

    def test_parse_エッジケース_空ファイルでignore無しを返すこと(self):
        # Arrange
        parser = FileIgnoreParser()
        source = ""

        # Act
        result = parser.parse(Path("example.py"), source)

        # Assert
        assert result.ignore_all is False
        assert result.ignored_rules == frozenset()

    def test_parse_エッジケース_import文の後のディレクティブは無視されること(self):
        # Arrange
        parser = FileIgnoreParser()
        source = "import os\n# paladin: ignore-file\n"

        # Act
        result = parser.parse(Path("example.py"), source)

        # Assert
        assert result.ignore_all is False
        assert result.ignored_rules == frozenset()

    def test_parse_エッジケース_空行の後にディレクティブを検出できること(self):
        # Arrange
        parser = FileIgnoreParser()
        source = "\n\n# paladin: ignore-file\n"

        # Act
        result = parser.parse(Path("example.py"), source)

        # Assert
        assert result.ignore_all is True

    def test_parse_エッジケース_docstringの後にディレクティブを検出できること(self):
        # Arrange
        parser = FileIgnoreParser()
        source = '"""module docstring"""\n# paladin: ignore-file\n'

        # Act
        result = parser.parse(Path("example.py"), source)

        # Assert
        assert result.ignore_all is True

    def test_parse_エッジケース_複数行docstringの後にディレクティブを検出できること(self):
        # Arrange: 複数行 docstring（閉じタグが別行）の後にディレクティブが続くケース
        parser = FileIgnoreParser()
        source = '"""module\ndocstring\n"""\n# paladin: ignore-file\n'

        # Act
        result = parser.parse(Path("example.py"), source)

        # Assert
        assert result.ignore_all is True


class TestFileIgnoreParserParseAll:
    """FileIgnoreParser.parse_all() のテスト"""

    def test_parse_all_正常系_複数ファイルのディレクティブをタプルで返すこと(self):
        # Arrange
        parser = FileIgnoreParser()
        pf_with_directive = _make_source_file("# paladin: ignore-file\nimport os\n", "a.py")
        pf_without_directive = _make_source_file("import os\n", "b.py")
        source_files = SourceFiles(files=(pf_with_directive, pf_without_directive))

        # Act
        result = parser.parse_all(source_files)

        # Assert
        assert len(result) == 2
        assert result[0].ignore_all is True
        assert result[1].ignore_all is False

    def test_parse_all_エッジケース_空のSourceFilesで空タプルを返すこと(self):
        # Arrange
        parser = FileIgnoreParser()
        source_files = SourceFiles(files=())

        # Act
        result = parser.parse_all(source_files)

        # Assert
        assert result == ()


class TestLineIgnoreParserParse:
    """LineIgnoreParser.parse() のテスト"""

    def test_parse_正常系_ignoreディレクティブで全ルールignoreを返すこと(self):
        # Arrange
        parser = LineIgnoreParser()
        source = "# paladin: ignore\nviolating_code\n"

        # Act
        result = parser.parse(Path("example.py"), source)

        # Assert
        assert len(result) == 1
        assert result[0].target_line == 2
        assert result[0].ignore_all is True
        assert result[0].ignored_rules == frozenset()

    def test_parse_正常系_ignore_with_rule_idで特定ルールignoreを返すこと(self):
        # Arrange
        parser = LineIgnoreParser()
        source = "# paladin: ignore[rule-a]\nviolating_code\n"

        # Act
        result = parser.parse(Path("example.py"), source)

        # Assert
        assert len(result) == 1
        assert result[0].target_line == 2
        assert result[0].ignore_all is False
        assert result[0].ignored_rules == frozenset({"rule-a"})

    def test_parse_正常系_複数ルールIDをカンマ区切りで指定できること(self):
        # Arrange
        parser = LineIgnoreParser()
        source = "# paladin: ignore[rule-a, rule-b]\nviolating_code\n"

        # Act
        result = parser.parse(Path("example.py"), source)

        # Assert
        assert len(result) == 1
        assert result[0].ignored_rules == frozenset({"rule-a", "rule-b"})

    def test_parse_正常系_複数のignoreディレクティブを検出できること(self):
        # Arrange
        parser = LineIgnoreParser()
        source = "# paladin: ignore\nfrom foo import bar\n# paladin: ignore\nfrom baz import qux\n"

        # Act
        result = parser.parse(Path("example.py"), source)

        # Assert
        assert len(result) == 2

    def test_parse_正常系_コード行の間にあるディレクティブを検出できること(self):
        # Arrange
        parser = LineIgnoreParser()
        source = "import os\n# paladin: ignore\nfrom . import bar\n"

        # Act
        result = parser.parse(Path("example.py"), source)

        # Assert
        assert len(result) == 1
        assert result[0].target_line == 3

    def test_parse_エッジケース_ディレクティブなしで空タプルを返すこと(self):
        # Arrange
        parser = LineIgnoreParser()
        source = "import os\n"

        # Act
        result = parser.parse(Path("example.py"), source)

        # Assert
        assert result == ()

    def test_parse_エッジケース_空ファイルで空タプルを返すこと(self):
        # Arrange
        parser = LineIgnoreParser()
        source = ""

        # Act
        result = parser.parse(Path("example.py"), source)

        # Assert
        assert result == ()

    def test_parse_エッジケース_直後が空行の場合はディレクティブ無効となること(self):
        # Arrange
        parser = LineIgnoreParser()
        source = "# paladin: ignore\n\nviolating_code\n"

        # Act
        result = parser.parse(Path("example.py"), source)

        # Assert
        assert result == ()

    def test_parse_エッジケース_ファイル末尾のディレクティブは無視されること(self):
        # Arrange
        parser = LineIgnoreParser()
        source = "import os\n# paladin: ignore\n"

        # Act
        result = parser.parse(Path("example.py"), source)

        # Assert
        assert result == ()

    def test_parse_エッジケース_ファイル末尾改行なしのディレクティブは無視されること(self):
        # Arrange
        parser = LineIgnoreParser()
        source = "import os\n# paladin: ignore"

        # Act
        result = parser.parse(Path("example.py"), source)

        # Assert
        assert result == ()

    def test_parse_エッジケース_ignore_fileディレクティブは行単位ignoreとして検出しないこと(self):
        # Arrange
        parser = LineIgnoreParser()
        source = "# paladin: ignore-file\nimport os\n"

        # Act
        result = parser.parse(Path("example.py"), source)

        # Assert
        assert result == ()


class TestLineIgnoreParserParseAll:
    """LineIgnoreParser.parse_all() のテスト"""

    def test_parse_all_正常系_複数ファイルのディレクティブをタプルで返すこと(self):
        # Arrange
        parser = LineIgnoreParser()
        pf_with_directive = _make_source_file("# paladin: ignore\nfrom foo import bar\n", "a.py")
        pf_without_directive = _make_source_file("import os\n", "b.py")
        source_files = SourceFiles(files=(pf_with_directive, pf_without_directive))

        # Act
        result = parser.parse_all(source_files)

        # Assert
        assert len(result) == 1
        assert result[0].file_path == Path("a.py")
        assert result[0].target_line == 2

    def test_parse_all_エッジケース_空のSourceFilesで空タプルを返すこと(self):
        # Arrange
        parser = LineIgnoreParser()
        source_files = SourceFiles(files=())

        # Act
        result = parser.parse_all(source_files)

        # Assert
        assert result == ()
