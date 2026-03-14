"""FileIgnoreDirective / FileIgnoreParser / LineIgnoreDirective / LineIgnoreParser / ViolationFilter のテスト"""

import ast
from pathlib import Path

from paladin.check.ignore import (
    FileIgnoreDirective,
    FileIgnoreParser,
    LineIgnoreDirective,
    LineIgnoreParser,
    ViolationFilter,
)
from paladin.lint.types import Violation, Violations
from paladin.source.types import ParsedFile, ParsedFiles


def _make_violation(
    file: Path,
    rule_id: str = "rule-a",
    line: int = 1,
) -> Violation:
    return Violation(
        file=file,
        line=line,
        column=0,
        rule_id=rule_id,
        rule_name="Rule A",
        message="violation",
        reason="reason",
        suggestion="suggestion",
    )


def _make_parsed_file(source: str, filename: str = "example.py") -> ParsedFile:
    return ParsedFile(file_path=Path(filename), tree=ast.parse(source), source=source)


class TestFileIgnoreDirective:
    """FileIgnoreDirective クラスのテスト"""

    def test_FileIgnoreDirective_正常系_全ルールignoreのインスタンスを生成できること(self):
        # Arrange / Act
        directive = FileIgnoreDirective(
            file_path=Path("example.py"),
            ignore_all=True,
            ignored_rules=frozenset(),
        )

        # Assert
        assert directive.file_path == Path("example.py")
        assert directive.ignore_all is True
        assert directive.ignored_rules == frozenset()

    def test_FileIgnoreDirective_正常系_特定ルールignoreのインスタンスを生成できること(self):
        # Arrange / Act
        directive = FileIgnoreDirective(
            file_path=Path("example.py"),
            ignore_all=False,
            ignored_rules=frozenset({"rule-a"}),
        )

        # Assert
        assert directive.file_path == Path("example.py")
        assert directive.ignore_all is False
        assert directive.ignored_rules == frozenset({"rule-a"})


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
        pf_with_directive = _make_parsed_file("# paladin: ignore-file\nimport os\n", "a.py")
        pf_without_directive = _make_parsed_file("import os\n", "b.py")
        parsed_files = ParsedFiles(files=(pf_with_directive, pf_without_directive))

        # Act
        result = parser.parse_all(parsed_files)

        # Assert
        assert len(result) == 2
        assert result[0].ignore_all is True
        assert result[1].ignore_all is False

    def test_parse_all_エッジケース_空のParsedFilesで空タプルを返すこと(self):
        # Arrange
        parser = FileIgnoreParser()
        parsed_files = ParsedFiles(files=())

        # Act
        result = parser.parse_all(parsed_files)

        # Assert
        assert result == ()


class TestViolationFilter:
    """ViolationFilter クラスのテスト"""

    def test_filter_正常系_ignore_allで該当ファイルの全違反が除外されること(self):
        # Arrange
        file_path = Path("example.py")
        violation = _make_violation(file_path, "rule-a")
        violations = Violations(items=(violation,))
        directive = FileIgnoreDirective(
            file_path=file_path, ignore_all=True, ignored_rules=frozenset()
        )
        vf = ViolationFilter()

        # Act
        result = vf.filter(violations, (directive,))

        # Assert
        assert len(result) == 0

    def test_filter_正常系_特定ルールignoreで該当ルールの違反のみ除外されること(self):
        # Arrange
        file_path = Path("example.py")
        v_a = _make_violation(file_path, "rule-a")
        v_b = _make_violation(file_path, "rule-b")
        violations = Violations(items=(v_a, v_b))
        directive = FileIgnoreDirective(
            file_path=file_path,
            ignore_all=False,
            ignored_rules=frozenset({"rule-a"}),
        )
        vf = ViolationFilter()

        # Act
        result = vf.filter(violations, (directive,))

        # Assert
        assert len(result) == 1
        assert next(iter(result)).rule_id == "rule-b"

    def test_filter_正常系_ignore対象外のファイルの違反は保持されること(self):
        # Arrange
        file_a = Path("a.py")
        file_b = Path("b.py")
        v_a = _make_violation(file_a, "rule-a")
        v_b = _make_violation(file_b, "rule-a")
        violations = Violations(items=(v_a, v_b))
        directive = FileIgnoreDirective(
            file_path=file_a, ignore_all=True, ignored_rules=frozenset()
        )
        vf = ViolationFilter()

        # Act
        result = vf.filter(violations, (directive,))

        # Assert
        assert len(result) == 1
        assert next(iter(result)).file == file_b

    def test_filter_エッジケース_空のViolationsで空のViolationsを返すこと(self):
        # Arrange
        violations = Violations(items=())
        vf = ViolationFilter()

        # Act
        result = vf.filter(violations, ())

        # Assert
        assert len(result) == 0

    def test_filter_エッジケース_空のディレクティブで全違反を保持すること(self):
        # Arrange
        file_path = Path("example.py")
        violation = _make_violation(file_path, "rule-a")
        violations = Violations(items=(violation,))
        vf = ViolationFilter()

        # Act
        result = vf.filter(violations, ())

        # Assert
        assert len(result) == 1

    def test_filter_正常系_複数ファイルで各ファイルのディレクティブが正しく適用されること(self):
        # Arrange
        file_a = Path("a.py")
        file_b = Path("b.py")
        v_a1 = _make_violation(file_a, "rule-a")
        v_a2 = _make_violation(file_a, "rule-b")
        v_b1 = _make_violation(file_b, "rule-a")
        v_b2 = _make_violation(file_b, "rule-b")
        violations = Violations(items=(v_a1, v_a2, v_b1, v_b2))
        directive_a = FileIgnoreDirective(
            file_path=file_a, ignore_all=True, ignored_rules=frozenset()
        )
        directive_b = FileIgnoreDirective(
            file_path=file_b, ignore_all=False, ignored_rules=frozenset({"rule-a"})
        )
        vf = ViolationFilter()

        # Act
        result = vf.filter(violations, (directive_a, directive_b))

        # Assert
        assert len(result) == 1
        remaining = next(iter(result))
        assert remaining.file == file_b
        assert remaining.rule_id == "rule-b"


class TestLineIgnoreDirective:
    """LineIgnoreDirective クラスのテスト"""

    def test_LineIgnoreDirective_正常系_全ルールignoreのインスタンスを生成できること(self):
        # Arrange / Act
        directive = LineIgnoreDirective(
            file_path=Path("example.py"),
            target_line=5,
            ignore_all=True,
            ignored_rules=frozenset(),
        )

        # Assert
        assert directive.file_path == Path("example.py")
        assert directive.target_line == 5
        assert directive.ignore_all is True
        assert directive.ignored_rules == frozenset()

    def test_LineIgnoreDirective_正常系_特定ルールignoreのインスタンスを生成できること(self):
        # Arrange / Act
        directive = LineIgnoreDirective(
            file_path=Path("example.py"),
            target_line=3,
            ignore_all=False,
            ignored_rules=frozenset({"rule-a"}),
        )

        # Assert
        assert directive.file_path == Path("example.py")
        assert directive.target_line == 3
        assert directive.ignore_all is False
        assert directive.ignored_rules == frozenset({"rule-a"})


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
        pf_with_directive = _make_parsed_file("# paladin: ignore\nfrom foo import bar\n", "a.py")
        pf_without_directive = _make_parsed_file("import os\n", "b.py")
        parsed_files = ParsedFiles(files=(pf_with_directive, pf_without_directive))

        # Act
        result = parser.parse_all(parsed_files)

        # Assert
        assert len(result) == 1
        assert result[0].file_path == Path("a.py")
        assert result[0].target_line == 2

    def test_parse_all_エッジケース_空のParsedFilesで空タプルを返すこと(self):
        # Arrange
        parser = LineIgnoreParser()
        parsed_files = ParsedFiles(files=())

        # Act
        result = parser.parse_all(parsed_files)

        # Assert
        assert result == ()


class TestViolationFilterLineIgnore:
    """ViolationFilter の行単位 Ignore テスト"""

    def test_filter_正常系_行単位ignore_allで該当行の全違反が除外されること(self):
        # Arrange
        file_path = Path("example.py")
        violation = _make_violation(file_path, "rule-a", line=5)
        violations = Violations(items=(violation,))
        line_directive = LineIgnoreDirective(
            file_path=file_path,
            target_line=5,
            ignore_all=True,
            ignored_rules=frozenset(),
        )
        vf = ViolationFilter()

        # Act
        result = vf.filter(violations, (), (line_directive,))

        # Assert
        assert len(result) == 0

    def test_filter_正常系_行単位特定ルールignoreで該当ルールの違反のみ除外されること(self):
        # Arrange
        file_path = Path("example.py")
        v_a = _make_violation(file_path, "rule-a", line=5)
        v_b = _make_violation(file_path, "rule-b", line=5)
        violations = Violations(items=(v_a, v_b))
        line_directive = LineIgnoreDirective(
            file_path=file_path,
            target_line=5,
            ignore_all=False,
            ignored_rules=frozenset({"rule-a"}),
        )
        vf = ViolationFilter()

        # Act
        result = vf.filter(violations, (), (line_directive,))

        # Assert
        assert len(result) == 1
        assert next(iter(result)).rule_id == "rule-b"

    def test_filter_正常系_行単位ignoreが異なる行の違反に影響しないこと(self):
        # Arrange
        file_path = Path("example.py")
        violation = _make_violation(file_path, "rule-a", line=3)
        violations = Violations(items=(violation,))
        line_directive = LineIgnoreDirective(
            file_path=file_path,
            target_line=5,
            ignore_all=True,
            ignored_rules=frozenset(),
        )
        vf = ViolationFilter()

        # Act
        result = vf.filter(violations, (), (line_directive,))

        # Assert
        assert len(result) == 1

    def test_filter_正常系_ファイル単位と行単位のignoreが同時に適用されること(self):
        # Arrange
        file_a = Path("a.py")
        file_b = Path("b.py")
        v_a = _make_violation(file_a, "rule-a", line=1)
        v_b_line3 = _make_violation(file_b, "rule-a", line=3)
        v_b_line5 = _make_violation(file_b, "rule-a", line=5)
        violations = Violations(items=(v_a, v_b_line3, v_b_line5))
        file_directive = FileIgnoreDirective(
            file_path=file_a, ignore_all=True, ignored_rules=frozenset()
        )
        line_directive = LineIgnoreDirective(
            file_path=file_b,
            target_line=3,
            ignore_all=True,
            ignored_rules=frozenset(),
        )
        vf = ViolationFilter()

        # Act
        result = vf.filter(violations, (file_directive,), (line_directive,))

        # Assert
        assert len(result) == 1
        assert next(iter(result)).file == file_b
        assert next(iter(result)).line == 5

    def test_filter_エッジケース_空のline_directivesで既存動作が維持されること(self):
        # Arrange
        file_path = Path("example.py")
        violation = _make_violation(file_path, "rule-a")
        violations = Violations(items=(violation,))
        file_directive = FileIgnoreDirective(
            file_path=file_path, ignore_all=True, ignored_rules=frozenset()
        )
        vf = ViolationFilter()

        # Act
        result = vf.filter(violations, (file_directive,), ())

        # Assert
        assert len(result) == 0

    def test_filter_正常系_行単位ignoreが異なるファイルの違反に影響しないこと(self):
        # Arrange: 違反は a.py、ディレクティブは b.py を対象とするケース
        file_a = Path("a.py")
        file_b = Path("b.py")
        violation = _make_violation(file_a, "rule-a", line=5)
        violations = Violations(items=(violation,))
        line_directive = LineIgnoreDirective(
            file_path=file_b,
            target_line=5,
            ignore_all=True,
            ignored_rules=frozenset(),
        )
        vf = ViolationFilter()

        # Act
        result = vf.filter(violations, (), (line_directive,))

        # Assert
        assert len(result) == 1
