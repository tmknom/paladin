"""FileIgnoreParser / LineIgnoreParser のテスト"""

from pathlib import Path

from paladin.check.ignore.parser import FileIgnoreParser, LineIgnoreParser
from paladin.rule import SourceFiles
from tests.unit.test_check.test_ignore.helper import make_source_file


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

    def test_parse_正常系_理由コメント付きignore_fileで全ルールignoreを返すこと(self):
        # Arrange
        parser = FileIgnoreParser()
        source = "# paladin: ignore-file -- レガシーコード\nimport os\n"

        # Act
        result = parser.parse(Path("example.py"), source)

        # Assert
        assert result.ignore_all is True
        assert result.ignored_rules == frozenset()

    def test_parse_正常系_理由コメント付きignore_file_with_rule_idで特定ルールignoreを返すこと(
        self,
    ):
        # Arrange
        parser = FileIgnoreParser()
        source = "# paladin: ignore-file[rule-a] -- 理由テキスト\nimport os\n"

        # Act
        result = parser.parse(Path("example.py"), source)

        # Assert
        assert result.ignore_all is False
        assert result.ignored_rules == frozenset({"rule-a"})

    def test_parse_エッジケース_理由コメントの理由部分が空白のみでもignoreとして有効であること(
        self,
    ):
        # Arrange
        parser = FileIgnoreParser()
        source = "# paladin: ignore-file -- \nimport os\n"

        # Act
        result = parser.parse(Path("example.py"), source)

        # Assert
        assert result.ignore_all is True

    def test_parse_エッジケース_ダブルダッシュ直後にスペースがない場合はディレクティブとして認識されないこと(
        self,
    ):
        # Arrange
        parser = FileIgnoreParser()
        source = "# paladin: ignore-file --理由\nimport os\n"

        # Act
        result = parser.parse(Path("example.py"), source)

        # Assert
        assert result.ignore_all is False

    def test_parse_エッジケース_ダブルダッシュのみでスペースがない場合はディレクティブとして認識されないこと(
        self,
    ):
        # Arrange
        parser = FileIgnoreParser()
        source = "# paladin: ignore-file--\nimport os\n"

        # Act
        result = parser.parse(Path("example.py"), source)

        # Assert
        assert result.ignore_all is False


class TestFileIgnoreParserParseAll:
    """FileIgnoreParser.parse_all() のテスト"""

    def test_parse_all_正常系_複数ファイルのディレクティブをタプルで返すこと(self):
        # Arrange
        parser = FileIgnoreParser()
        pf_with_directive = make_source_file("# paladin: ignore-file\nimport os\n", "a.py")
        pf_without_directive = make_source_file("import os\n", "b.py")
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

    def test_parse_正常系_理由コメント付きignoreで全ルールignoreを返すこと(self):
        # Arrange
        parser = LineIgnoreParser()
        source = "# paladin: ignore -- 理由テキスト\nviolating_code\n"

        # Act
        result = parser.parse(Path("example.py"), source)

        # Assert
        assert len(result) == 1
        assert result[0].ignore_all is True
        assert result[0].target_line == 2

    def test_parse_正常系_理由コメント付きignore_with_rule_idで特定ルールignoreを返すこと(self):
        # Arrange
        parser = LineIgnoreParser()
        source = "# paladin: ignore[rule-a] -- 理由\nviolating_code\n"

        # Act
        result = parser.parse(Path("example.py"), source)

        # Assert
        assert len(result) == 1
        assert result[0].ignored_rules == frozenset({"rule-a"})
        assert result[0].target_line == 2

    def test_parse_エッジケース_直前コメントの理由部分が空白のみでもignoreとして有効であること(
        self,
    ):
        # Arrange
        parser = LineIgnoreParser()
        source = "# paladin: ignore -- \ncode\n"

        # Act
        result = parser.parse(Path("example.py"), source)

        # Assert
        assert len(result) == 1
        assert result[0].ignore_all is True

    def test_parse_エッジケース_直前コメントのダブルダッシュ直後にスペースがない場合はディレクティブとして認識されないこと(
        self,
    ):
        # Arrange
        parser = LineIgnoreParser()
        source = "# paladin: ignore --理由\ncode\n"

        # Act
        result = parser.parse(Path("example.py"), source)

        # Assert
        assert result == ()


class TestLineIgnoreParserParseTrailing:
    """LineIgnoreParser.parse() 行末コメントのテスト"""

    def test_parse_正常系_行末ignoreディレクティブで全ルールignoreを返すこと(self):
        # Arrange
        parser = LineIgnoreParser()
        source = "violating_code  # paladin: ignore\n"

        # Act
        result = parser.parse(Path("example.py"), source)

        # Assert
        assert len(result) == 1
        assert result[0].target_line == 1
        assert result[0].ignore_all is True
        assert result[0].ignored_rules == frozenset()

    def test_parse_正常系_行末ignore_with_rule_idで特定ルールignoreを返すこと(self):
        # Arrange
        parser = LineIgnoreParser()
        source = "violating_code  # paladin: ignore[rule-a]\n"

        # Act
        result = parser.parse(Path("example.py"), source)

        # Assert
        assert len(result) == 1
        assert result[0].target_line == 1
        assert result[0].ignore_all is False
        assert result[0].ignored_rules == frozenset({"rule-a"})

    def test_parse_正常系_行末コメントで複数ルールIDをカンマ区切りで指定できること(self):
        # Arrange
        parser = LineIgnoreParser()
        source = "code  # paladin: ignore[rule-a, rule-b]\n"

        # Act
        result = parser.parse(Path("example.py"), source)

        # Assert
        assert len(result) == 1
        assert result[0].ignored_rules == frozenset({"rule-a", "rule-b"})

    def test_parse_正常系_直前コメントと行末コメントが同一ファイルで共存できること(self):
        # Arrange
        parser = LineIgnoreParser()
        source = "# paladin: ignore[rule-a]\ncode  # paladin: ignore[rule-b]\n"

        # Act
        result = parser.parse(Path("example.py"), source)

        # Assert
        assert len(result) == 2
        # 直前コメントは2行目対象
        preceding = next(d for d in result if d.ignored_rules == frozenset({"rule-a"}))
        assert preceding.target_line == 2
        # 行末コメントも2行目対象
        trailing = next(d for d in result if d.ignored_rules == frozenset({"rule-b"}))
        assert trailing.target_line == 2

    def test_parse_エッジケース_接頭辞前に空白がない場合は行末コメントとして検出されないこと(self):
        # Arrange
        parser = LineIgnoreParser()
        source = "code# paladin: ignore\n"

        # Act
        result = parser.parse(Path("example.py"), source)

        # Assert
        assert result == ()

    def test_parse_エッジケース_ignore_fileディレクティブは行末コメントとして検出されないこと(self):
        # Arrange
        parser = LineIgnoreParser()
        source = "code  # paladin: ignore-file\n"

        # Act
        result = parser.parse(Path("example.py"), source)

        # Assert
        assert result == ()

    def test_parse_正常系_行末理由コメント付きignoreで全ルールignoreを返すこと(self):
        # Arrange
        parser = LineIgnoreParser()
        source = "violating_code  # paladin: ignore -- 理由テキスト\n"

        # Act
        result = parser.parse(Path("example.py"), source)

        # Assert
        assert len(result) == 1
        assert result[0].ignore_all is True
        assert result[0].target_line == 1

    def test_parse_正常系_行末理由コメント付きignore_with_rule_idで特定ルールignoreを返すこと(self):
        # Arrange
        parser = LineIgnoreParser()
        ignore_comment = "# paladin: ignore[rule-a] -- 理由"
        source = f"violating_code  {ignore_comment}\n"

        # Act
        result = parser.parse(Path("example.py"), source)

        # Assert
        assert len(result) == 1
        assert result[0].ignored_rules == frozenset({"rule-a"})
        assert result[0].target_line == 1

    def test_parse_エッジケース_行末コメントの理由部分が空白のみでもignoreとして有効であること(
        self,
    ):
        # Arrange
        parser = LineIgnoreParser()
        source = "code  # paladin: ignore -- \n"

        # Act
        result = parser.parse(Path("example.py"), source)

        # Assert
        assert len(result) == 1
        assert result[0].ignore_all is True

    def test_parse_エッジケース_行末コメントのダブルダッシュ直後にスペースがない場合はディレクティブとして認識されないこと(
        self,
    ):
        # Arrange
        parser = LineIgnoreParser()
        source = "code  # paladin: ignore --理由\n"

        # Act
        result = parser.parse(Path("example.py"), source)

        # Assert
        assert result == ()


class TestLineIgnoreParserParseAll:
    """LineIgnoreParser.parse_all() のテスト"""

    def test_parse_all_正常系_複数ファイルのディレクティブをタプルで返すこと(self):
        # Arrange
        parser = LineIgnoreParser()
        pf_with_directive = make_source_file("# paladin: ignore\nfrom foo import bar\n", "a.py")
        pf_without_directive = make_source_file("import os\n", "b.py")
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
