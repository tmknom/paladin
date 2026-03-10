import ast
from pathlib import Path

from paladin.check.types import (
    CheckResult,
    ParsedFile,
    ParsedFiles,
    RuleMeta,
    TargetFiles,
    Violation,
    Violations,
)


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


class TestViolation:
    """Violationクラスのテスト"""

    def test_violation_init_正常系_全フィールドを保持すること(self):
        # Arrange & Act
        result = Violation(
            file=Path("src/paladin/__init__.py"),
            line=1,
            column=0,
            rule_id="require-all-export",
            rule_name="Require __all__ Export",
            message="__init__.py に __all__ が定義されていない",
            reason="__all__ が未定義の場合、パッケージの公開インタフェースが不明確になり、意図しないシンボルが外部に露出するリスクがある",
            suggestion="__all__ リストを定義し、公開するシンボルを明示的に列挙する",
        )

        # Assert
        assert result.file == Path("src/paladin/__init__.py")
        assert result.line == 1
        assert result.column == 0
        assert result.rule_id == "require-all-export"
        assert result.rule_name == "Require __all__ Export"
        assert result.message == "__init__.py に __all__ が定義されていない"
        assert (
            result.reason
            == "__all__ が未定義の場合、パッケージの公開インタフェースが不明確になり、意図しないシンボルが外部に露出するリスクがある"
        )
        assert result.suggestion == "__all__ リストを定義し、公開するシンボルを明示的に列挙する"


class TestViolations:
    """Violationsクラスのテスト"""

    def _make_violation(self, file: str = "src/paladin/__init__.py") -> Violation:
        return Violation(
            file=Path(file),
            line=1,
            column=0,
            rule_id="require-all-export",
            rule_name="Require __all__ Export",
            message="__init__.py に __all__ が定義されていない",
            reason="reason",
            suggestion="suggestion",
        )

    def test_violations_len_正常系_件数を返すこと(self):
        # Arrange
        v1 = self._make_violation("a/__init__.py")
        v2 = self._make_violation("b/__init__.py")
        violations = Violations(items=(v1, v2))

        # Act
        result = len(violations)

        # Assert
        assert result == 2

    def test_violations_iter_正常系_Violationをイテレーションできること(self):
        # Arrange
        v1 = self._make_violation("a/__init__.py")
        v2 = self._make_violation("b/__init__.py")
        violations = Violations(items=(v1, v2))

        # Act
        result = list(violations)

        # Assert
        assert result == [v1, v2]

    def test_violations_len_エッジケース_空で0を返すこと(self):
        # Arrange
        violations = Violations(items=())

        # Act
        result = len(violations)

        # Assert
        assert result == 0


class TestRuleMeta:
    """RuleMetaクラスのテスト"""

    def test_rule_meta_init_正常系_全フィールドを保持すること(self):
        # Arrange & Act
        result = RuleMeta(
            rule_id="require-all-export",
            rule_name="Require __all__ Export",
            summary="__init__.py に __all__ の定義を要求する",
        )

        # Assert
        assert result.rule_id == "require-all-export"
        assert result.rule_name == "Require __all__ Export"
        assert result.summary == "__init__.py に __all__ の定義を要求する"


class TestCheckResult:
    """CheckResultクラスのテスト"""

    def test_init_正常系_target_filesとparsed_filesとviolationsを保持すること(self):
        # Arrange
        target_files = TargetFiles(files=(Path("a.py"),))
        parsed_files = ParsedFiles(files=())
        violations = Violations(items=())

        # Act
        result = CheckResult(
            target_files=target_files,
            parsed_files=parsed_files,
            violations=violations,
        )

        # Assert
        assert result.target_files == target_files
        assert result.parsed_files == parsed_files
        assert result.violations == violations
