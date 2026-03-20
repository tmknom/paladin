"""ImportStatement ドメイン値オブジェクトのユニットテスト"""

import ast
from pathlib import Path

from paladin.rule.import_statement import (
    ImportedName,
    ImportStatement,
    ModulePath,
    SourceLocation,
)


class TestModulePath:
    """ModulePath 値オブジェクトのテスト"""

    def test_segments_正常系_ドット区切りのタプルを返すこと(self):
        mp = ModulePath("paladin.check.formatter")
        assert mp.segments == ("paladin", "check", "formatter")

    def test_segments_正常系_単一セグメントのとき1要素タプルを返すこと(self):
        mp = ModulePath("paladin")
        assert mp.segments == ("paladin",)

    def test_depth_正常系_セグメント数を返すこと(self):
        mp = ModulePath("paladin.check.formatter")
        assert mp.depth == 3

    def test_depth_正常系_単一セグメントのとき1を返すこと(self):
        mp = ModulePath("paladin")
        assert mp.depth == 1

    def test_top_level_正常系_先頭セグメントを返すこと(self):
        mp = ModulePath("paladin.check.formatter")
        assert mp.top_level == "paladin"

    def test_top_level_正常系_単一セグメントのとき自身を返すこと(self):
        mp = ModulePath("paladin")
        assert mp.top_level == "paladin"

    def test_package_key_正常系_先頭2セグメントを返すこと(self):
        mp = ModulePath("paladin.check.formatter")
        assert mp.package_key == "paladin.check"

    def test_package_key_正常系_2セグメントのときそのまま返すこと(self):
        mp = ModulePath("paladin.check")
        assert mp.package_key == "paladin.check"

    def test_package_key_正常系_1セグメントのときそのまま返すこと(self):
        mp = ModulePath("paladin")
        assert mp.package_key == "paladin"

    def test_is_subpackage_of_正常系_自身のとき真を返すこと(self):
        mp = ModulePath("paladin.check")
        parent = ModulePath("paladin.check")
        assert mp.is_subpackage_of(parent) is True

    def test_is_subpackage_of_正常系_サブパッケージのとき真を返すこと(self):
        mp = ModulePath("paladin.check.formatter")
        parent = ModulePath("paladin.check")
        assert mp.is_subpackage_of(parent) is True

    def test_is_subpackage_of_正常系_別パッケージのとき偽を返すこと(self):
        mp = ModulePath("paladin.rule")
        parent = ModulePath("paladin.check")
        assert mp.is_subpackage_of(parent) is False

    def test_is_subpackage_of_エッジケース_プレフィックス一致だが別パッケージのとき偽を返すこと(
        self,
    ):
        mp = ModulePath("paladin.checker")
        parent = ModulePath("paladin.check")
        assert mp.is_subpackage_of(parent) is False

    def test_str_正常系_value文字列を返すこと(self):
        mp = ModulePath("paladin.check.formatter")
        assert str(mp) == "paladin.check.formatter"


class TestImportedName:
    """ImportedName 値オブジェクトのテスト"""

    def test_bound_name_正常系_asnameがあるときasnameを返すこと(self):
        imported = ImportedName(name="numpy", asname="np")
        assert imported.bound_name == "np"

    def test_bound_name_正常系_asnameがないときnameを返すこと(self):
        imported = ImportedName(name="Foo", asname=None)
        assert imported.bound_name == "Foo"

    def test_has_alias_正常系_asnameがあるとき真を返すこと(self):
        imported = ImportedName(name="numpy", asname="np")
        assert imported.has_alias is True

    def test_has_alias_正常系_asnameがないとき偽を返すこと(self):
        imported = ImportedName(name="Foo", asname=None)
        assert imported.has_alias is False

    def test_from_alias_正常系_ast_aliasから生成すること(self):
        alias = ast.alias(name="Foo", asname="Bar")
        imported = ImportedName.from_alias(alias)
        assert imported.name == "Foo"
        assert imported.asname == "Bar"

    def test_from_alias_正常系_asnameなしのalias(self):
        alias = ast.alias(name="Foo")
        imported = ImportedName.from_alias(alias)
        assert imported.name == "Foo"
        assert imported.asname is None

    def test_from_aliases_正常系_複数aliasからタプルを生成すること(self):
        aliases = [ast.alias(name="Foo"), ast.alias(name="Bar", asname="B")]
        result = ImportedName.from_aliases(aliases)
        assert len(result) == 2
        assert result[0].name == "Foo"
        assert result[1].name == "Bar"
        assert result[1].asname == "B"


class TestImportStatement:
    """ImportStatement 値オブジェクトのテスト"""

    def test_is_relative_正常系_level1のとき真を返すこと(self):
        source = "from . import foo\n"
        node = ast.parse(source).body[0]
        assert isinstance(node, ast.ImportFrom)
        stmt = ImportStatement.from_import_from(node)
        assert stmt.is_relative is True

    def test_is_relative_正常系_level0のとき偽を返すこと(self):
        source = "from paladin import foo\n"
        node = ast.parse(source).body[0]
        assert isinstance(node, ast.ImportFrom)
        stmt = ImportStatement.from_import_from(node)
        assert stmt.is_relative is False

    def test_is_absolute_正常系_level0のとき真を返すこと(self):
        source = "from paladin import foo\n"
        node = ast.parse(source).body[0]
        assert isinstance(node, ast.ImportFrom)
        stmt = ImportStatement.from_import_from(node)
        assert stmt.is_absolute is True

    def test_level_dots_正常系_level数分のドットを返すこと(self):
        source = "from .. import foo\n"
        node = ast.parse(source).body[0]
        assert isinstance(node, ast.ImportFrom)
        stmt = ImportStatement.from_import_from(node)
        assert stmt.level_dots == ".."

    def test_module_str_正常系_モジュール文字列を返すこと(self):
        source = "from paladin.check import Foo\n"
        node = ast.parse(source).body[0]
        assert isinstance(node, ast.ImportFrom)
        stmt = ImportStatement.from_import_from(node)
        assert stmt.module_str == "paladin.check"

    def test_module_str_正常系_モジュールなしのとき空文字を返すこと(self):
        source = "from . import foo\n"
        node = ast.parse(source).body[0]
        assert isinstance(node, ast.ImportFrom)
        stmt = ImportStatement.from_import_from(node)
        assert stmt.module_str == ""

    def test_top_level_module_正常系_先頭セグメントを返すこと(self):
        source = "from paladin.check.formatter import Foo\n"
        node = ast.parse(source).body[0]
        assert isinstance(node, ast.ImportFrom)
        stmt = ImportStatement.from_import_from(node)
        assert stmt.top_level_module == "paladin"

    def test_top_level_module_正常系_モジュールなしのときNoneを返すこと(self):
        source = "from . import foo\n"
        node = ast.parse(source).body[0]
        assert isinstance(node, ast.ImportFrom)
        stmt = ImportStatement.from_import_from(node)
        assert stmt.top_level_module is None

    def test_has_module_正常系_モジュールがあるとき真を返すこと(self):
        source = "from paladin import foo\n"
        node = ast.parse(source).body[0]
        assert isinstance(node, ast.ImportFrom)
        stmt = ImportStatement.from_import_from(node)
        assert stmt.has_module is True

    def test_has_module_正常系_モジュールなしのとき偽を返すこと(self):
        source = "from . import foo\n"
        node = ast.parse(source).body[0]
        assert isinstance(node, ast.ImportFrom)
        stmt = ImportStatement.from_import_from(node)
        assert stmt.has_module is False

    def test_from_import_from_正常系_namesを正しく抽出すること(self):
        source = "from paladin.check import Foo, Bar as B\n"
        node = ast.parse(source).body[0]
        assert isinstance(node, ast.ImportFrom)
        stmt = ImportStatement.from_import_from(node)
        assert len(stmt.names) == 2
        assert stmt.names[0].name == "Foo"
        assert stmt.names[1].name == "Bar"
        assert stmt.names[1].asname == "B"
        assert stmt.is_import_from is True

    def test_from_import_正常系_import文を生成すること(self):
        source = "import numpy as np\n"
        node = ast.parse(source).body[0]
        assert isinstance(node, ast.Import)
        stmt = ImportStatement.from_import(node)
        assert stmt.is_import_from is False
        assert stmt.level == 0
        assert stmt.module is None
        assert stmt.names[0].name == "numpy"
        assert stmt.names[0].asname == "np"

    def test_from_import_from_正常系_行番号と列番号を保持すること(self):
        source = "from paladin import Foo\n"
        node = ast.parse(source).body[0]
        assert isinstance(node, ast.ImportFrom)
        stmt = ImportStatement.from_import_from(node)
        assert stmt.line == 1
        assert stmt.column == 0


class TestSourceLocation:
    """SourceLocation 値オブジェクトのテスト"""

    def test_init_正常系_全フィールドを保持すること(self):
        loc = SourceLocation(file=Path("src/paladin/foo.py"), line=10, column=4)
        assert loc.file == Path("src/paladin/foo.py")
        assert loc.line == 10
        assert loc.column == 4
