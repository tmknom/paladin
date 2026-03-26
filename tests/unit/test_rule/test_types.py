import ast
from pathlib import Path

from paladin.rule.import_statement import ImportStatement, SourceLocation
from paladin.rule.types import RuleMeta, SourceFile, SourceFiles, Violation, Violations


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


class TestSourceFileImports:
    """SourceFile.imports / top_level_imports / location / location_from のテスト"""

    def _sf(self, source: str) -> SourceFile:
        return SourceFile(
            file_path=Path("src/paladin/foo.py"), tree=ast.parse(source), source=source
        )

    def test_imports_正常系_全インポートを返すこと(self):
        source = "import os\nfrom paladin import Foo\n"
        sf = self._sf(source)
        result = sf.imports
        assert len(result) == 2

    def test_imports_正常系_ネストしたインポートも返すこと(self):
        source = "def f():\n    import os\n"
        sf = self._sf(source)
        result = sf.imports
        assert len(result) == 1

    def test_top_level_imports_正常系_トップレベルのみ返すこと(self):
        source = "import os\ndef f():\n    import sys\n"
        sf = self._sf(source)
        result = sf.top_level_imports
        assert len(result) == 1
        assert result[0].names[0].name == "os"

    def test_imports_エッジケース_インポートなしのとき空タプルを返すこと(self):
        sf = self._sf("x = 1\n")
        assert sf.imports == ()

    def test_top_level_imports_エッジケース_インポートなしのとき空タプルを返すこと(self):
        sf = self._sf("x = 1\n")
        assert sf.top_level_imports == ()

    def test_location_正常系_SourceLocationを返すこと(self):
        sf = self._sf("x = 1\n")
        loc = sf.location(line=5, column=2)
        assert loc.file == Path("src/paladin/foo.py")
        assert loc.line == 5
        assert loc.column == 2

    def test_location_正常系_デフォルトcolumnは0であること(self):
        sf = self._sf("x = 1\n")
        loc = sf.location(line=3)
        assert loc.column == 0

    def test_location_from_正常系_ImportStatementから位置を返すこと(self):
        source = "from paladin import Foo\n"
        tree = ast.parse(source)
        sf = SourceFile(file_path=Path("src/paladin/foo.py"), tree=tree, source=source)
        node = tree.body[0]
        assert isinstance(node, ast.ImportFrom)
        stmt = ImportStatement.from_import_from(node)
        loc = sf.location_from(stmt)
        assert loc.file == Path("src/paladin/foo.py")
        assert loc.line == 1
        assert loc.column == 0

    def test_location_from_正常系_AbsoluteFromImportから位置を返すこと(self):
        source = "from paladin import Foo\n"
        sf = SourceFile(file_path=Path("src/paladin/foo.py"), tree=ast.parse(source), source=source)
        imps = sf.absolute_from_imports
        assert len(imps) == 1
        loc = sf.location_from(imps[0])
        assert loc.file == Path("src/paladin/foo.py")
        assert loc.line == 1
        assert loc.column == 0


class TestSourceFileAbsoluteFromImports:
    """SourceFile.absolute_from_imports プロパティのテスト"""

    def _sf(self, source: str) -> SourceFile:
        return SourceFile(
            file_path=Path("src/paladin/foo.py"), tree=ast.parse(source), source=source
        )

    def test_正常系_絶対fromインポートを抽出すること(self):
        source = "from paladin.check import Foo\n"
        sf = self._sf(source)
        result = sf.absolute_from_imports
        assert len(result) == 1
        assert result[0].module_str == "paladin.check"
        assert result[0].names[0].name == "Foo"

    def test_正常系_相対インポートを除外すること(self):
        source = "from .check import Foo\n"
        sf = self._sf(source)
        assert sf.absolute_from_imports == ()

    def test_正常系_通常importを除外すること(self):
        source = "import paladin\n"
        sf = self._sf(source)
        assert sf.absolute_from_imports == ()

    def test_正常系_moduleなしのfromインポートを除外すること(self):
        source = "from . import foo\n"
        sf = self._sf(source)
        assert sf.absolute_from_imports == ()

    def test_正常系_複数インポートが混在するとき絶対fromのみを返すこと(self):
        source = "from paladin.check import Foo\nfrom .rule import Bar\nimport os\n"
        sf = self._sf(source)
        result = sf.absolute_from_imports
        assert len(result) == 1
        assert result[0].module_str == "paladin.check"

    def test_エッジケース_インポートなしのとき空タプルを返すこと(self):
        sf = self._sf("x = 1\n")
        assert sf.absolute_from_imports == ()


class TestRuleMetaCreateViolationAt:
    """RuleMeta.create_violation_at() のテスト"""

    def _meta(self) -> RuleMeta:
        return RuleMeta(
            rule_id="test-rule",
            rule_name="Test Rule",
            summary="テスト",
            intent="テスト",
            guidance="テスト",
            suggestion="テスト",
        )

    def test_正常系_SourceLocationからViolationを生成すること(self):
        meta = self._meta()
        loc = SourceLocation(file=Path("src/paladin/foo.py"), line=10, column=4)
        result = meta.create_violation_at(
            location=loc,
            message="テストメッセージ",
            reason="テスト理由",
            suggestion="テスト提案",
        )
        assert result.file == Path("src/paladin/foo.py")
        assert result.line == 10
        assert result.column == 4
        assert result.rule_id == "test-rule"
        assert result.rule_name == "Test Rule"
        assert result.message == "テストメッセージ"
        assert result.reason == "テスト理由"
        assert result.suggestion == "テスト提案"
