import ast
from pathlib import Path

from paladin.rule.types import RuleMeta, SourceFile, SourceFiles, Violation, Violations


class TestSourceFile:
    """SourceFileクラスのテスト"""

    def test_init_正常系_file_pathとtreeとsourceを保持すること(self):
        # Arrange
        tree = ast.parse("x = 1\n")

        # Act
        result = SourceFile(file_path=Path("test.py"), tree=tree, source="x = 1\n")

        # Assert
        assert result.file_path == Path("test.py")
        assert isinstance(result.tree, ast.Module)
        assert result.source == "x = 1\n"


class TestSourceFiles:
    """SourceFilesクラスのテスト"""

    def test_len_正常系_ファイル数を返すこと(self):
        # Arrange
        tree = ast.parse("x = 1\n")
        source_files = SourceFiles(
            files=(
                SourceFile(file_path=Path("a.py"), tree=tree, source="x = 1\n"),
                SourceFile(file_path=Path("b.py"), tree=tree, source="x = 1\n"),
            )
        )

        # Act
        result = len(source_files)

        # Assert
        assert result == 2

    def test_iter_正常系_SourceFileをイテレーションできること(self):
        # Arrange
        tree = ast.parse("x = 1\n")
        sf_a = SourceFile(file_path=Path("a.py"), tree=tree, source="x = 1\n")
        sf_b = SourceFile(file_path=Path("b.py"), tree=tree, source="x = 1\n")
        source_files = SourceFiles(files=(sf_a, sf_b))

        # Act
        result = list(source_files)

        # Assert
        assert result == [sf_a, sf_b]

    def test_len_エッジケース_空で0を返すこと(self):
        # Arrange
        source_files = SourceFiles(files=())

        # Act
        result = len(source_files)

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


class TestSourceFileProperties:
    """SourceFile プロパティのテスト"""

    def test_is_init_py_正常系_init_pyのとき真を返すこと(self):
        tree = ast.parse("")
        sf = SourceFile(file_path=Path("src/paladin/__init__.py"), tree=tree, source="")
        assert sf.is_init_py is True

    def test_is_init_py_正常系_通常ファイルのとき偽を返すこと(self):
        tree = ast.parse("")
        sf = SourceFile(file_path=Path("src/paladin/foo.py"), tree=tree, source="")
        assert sf.is_init_py is False

    def test_is_test_file_正常系_tests配下のとき真を返すこと(self):
        tree = ast.parse("")
        sf = SourceFile(file_path=Path("tests/unit/test_foo.py"), tree=tree, source="")
        assert sf.is_test_file is True

    def test_is_test_file_正常系_src配下のとき偽を返すこと(self):
        tree = ast.parse("")
        sf = SourceFile(file_path=Path("src/paladin/foo.py"), tree=tree, source="")
        assert sf.is_test_file is False


class TestSourceFileGetLine:
    """SourceFile.get_line() のテスト"""

    def _sf(self, source: str) -> SourceFile:
        return SourceFile(file_path=Path("test.py"), tree=ast.parse(source), source=source)

    def test_正常系_1行目を返すこと(self):
        sf = self._sf("x = 1\ny = 2\n")
        assert sf.get_line(1) == "x = 1"

    def test_正常系_2行目を返すこと(self):
        sf = self._sf("x = 1\ny = 2\n")
        assert sf.get_line(2) == "y = 2"

    def test_正常系_前後空白をstripすること(self):
        # SourceFile を直接構築して source に空白付きの行を持たせる
        sf = SourceFile(file_path=Path("test.py"), tree=ast.parse(""), source="    x = 1\n")
        assert sf.get_line(1) == "x = 1"

    def test_エッジケース_行番号が範囲外のとき空文字を返すこと(self):
        sf = self._sf("x = 1\n")
        assert sf.get_line(99) == ""

    def test_エッジケース_行番号0のとき空文字を返すこと(self):
        sf = self._sf("x = 1\n")
        assert sf.get_line(0) == ""


class TestSourceFilesFilters:
    """SourceFiles フィルタメソッドのテスト"""

    def _sf(self, path: str) -> SourceFile:
        tree = ast.parse("")
        return SourceFile(file_path=Path(path), tree=tree, source="")

    def test_init_files_正常系_init_pyのみを返すこと(self):
        sf_init = self._sf("src/paladin/__init__.py")
        sf_other = self._sf("src/paladin/foo.py")
        source_files = SourceFiles(files=(sf_init, sf_other))
        result = list(source_files.init_files())
        assert result == [sf_init]

    def test_production_files_正常系_tests配下を除外すること(self):
        sf_prod = self._sf("src/paladin/foo.py")
        sf_test = self._sf("tests/unit/test_foo.py")
        source_files = SourceFiles(files=(sf_prod, sf_test))
        result = list(source_files.production_files())
        assert result == [sf_prod]

    def test_init_files_エッジケース_空の場合空を返すこと(self):
        source_files = SourceFiles(files=())
        result = list(source_files.init_files())
        assert result == []

    def test_production_files_エッジケース_空の場合空を返すこと(self):
        source_files = SourceFiles(files=())
        result = list(source_files.production_files())
        assert result == []


class TestRuleMeta:
    """RuleMetaクラスのテスト"""

    def _meta(self) -> RuleMeta:
        return RuleMeta(
            rule_id="require-all-export",
            rule_name="Require __all__ Export",
            summary="__init__.py に __all__ の定義を要求する",
            intent="パッケージの公開インターフェースを明示し、意図しないシンボルの露出を防ぐ",
            guidance="__init__.py に __all__ が定義されているかを確認する",
            suggestion="__all__ リストを定義し、公開するシンボルを明示的に列挙する",
        )

    def test_rule_meta_init_正常系_全フィールドを保持すること(self):
        # Arrange & Act
        result = self._meta()

        # Assert
        assert result.rule_id == "require-all-export"
        assert result.rule_name == "Require __all__ Export"
        assert result.summary == "__init__.py に __all__ の定義を要求する"
        assert (
            result.intent
            == "パッケージの公開インターフェースを明示し、意図しないシンボルの露出を防ぐ"
        )
        assert result.guidance == "__init__.py に __all__ が定義されているかを確認する"
        assert result.suggestion == "__all__ リストを定義し、公開するシンボルを明示的に列挙する"

    def test_create_violation_正常系_rule_idとrule_nameが自動補完されること(self):
        meta = self._meta()
        result = meta.create_violation(
            file=Path("src/paladin/__init__.py"),
            line=1,
            column=0,
            message="テストメッセージ",
            reason="テスト理由",
            suggestion="テスト提案",
        )
        assert result.rule_id == "require-all-export"
        assert result.rule_name == "Require __all__ Export"
        assert result.file == Path("src/paladin/__init__.py")
        assert result.line == 1
        assert result.column == 0
        assert result.message == "テストメッセージ"
        assert result.reason == "テスト理由"
        assert result.suggestion == "テスト提案"
