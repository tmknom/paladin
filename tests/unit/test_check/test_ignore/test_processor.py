"""IgnoreProcessor のテスト"""

import ast
from pathlib import Path

from paladin.check.ignore import IgnoreProcessor
from paladin.rule import PerFileIgnoreEntry, SourceFile, SourceFiles, Violation, Violations


def _make_source_file(source: str, filename: str = "example.py") -> SourceFile:
    return SourceFile(file_path=Path(filename), tree=ast.parse(source), source=source)


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


class TestIgnoreProcessor:
    """IgnoreProcessor クラスのテスト"""

    def test_apply_正常系_ディレクティブなしで全違反が保持されること(self):
        # Arrange
        source_file = _make_source_file("x = 1\n")
        source_files = SourceFiles(files=(source_file,))
        violation = _make_violation(Path("example.py"), "rule-a")
        violations = Violations(items=(violation,))
        processor = IgnoreProcessor()

        # Act
        result = processor.apply(violations, source_files, (), frozenset())

        # Assert
        assert len(result) == 1

    def test_apply_正常系_コメント由来ignore_fileで違反が除外されること(self):
        # Arrange
        source = "# paladin: ignore-file\nx = 1\n"
        source_file = _make_source_file(source)
        source_files = SourceFiles(files=(source_file,))
        violation = _make_violation(Path("example.py"), "rule-a")
        violations = Violations(items=(violation,))
        processor = IgnoreProcessor()

        # Act
        result = processor.apply(violations, source_files, (), frozenset())

        # Assert
        assert len(result) == 0

    def test_apply_正常系_設定ファイルper_file_ignoresで違反が除外されること(self):
        # Arrange
        source_file = _make_source_file("x = 1\n")
        source_files = SourceFiles(files=(source_file,))
        violation = _make_violation(Path("example.py"), "rule-a")
        violations = Violations(items=(violation,))
        per_file_ignores = (
            PerFileIgnoreEntry(
                pattern="example.py",
                rule_ids=frozenset({"rule-a"}),
                ignore_all=False,
            ),
        )
        processor = IgnoreProcessor()

        # Act
        result = processor.apply(violations, source_files, per_file_ignores, frozenset())

        # Assert
        assert len(result) == 0

    def test_apply_正常系_行単位ignoreで違反が除外されること(self):
        # Arrange
        source = "# paladin: ignore\nx = 1\n"
        source_file = _make_source_file(source)
        source_files = SourceFiles(files=(source_file,))
        violation = _make_violation(Path("example.py"), "rule-a", line=2)
        violations = Violations(items=(violation,))
        processor = IgnoreProcessor()

        # Act
        result = processor.apply(violations, source_files, (), frozenset())

        # Assert
        assert len(result) == 0

    def test_apply_正常系_ignore_rulesで違反が除外されること(self):
        # Arrange
        source_file = _make_source_file("x = 1\n")
        source_files = SourceFiles(files=(source_file,))
        violation = _make_violation(Path("example.py"), "rule-a")
        violations = Violations(items=(violation,))
        processor = IgnoreProcessor()

        # Act
        result = processor.apply(violations, source_files, (), frozenset({"rule-a"}))

        # Assert
        assert len(result) == 0
