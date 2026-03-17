import ast
from pathlib import Path

from paladin.rule.no_cross_package_reexport import NoCrossPackageReexportRule
from paladin.rule.types import RuleMeta, SourceFile


def _make_source_file(
    source: str,
    filename: str = "src/paladin/check/__init__.py",
) -> SourceFile:
    return SourceFile(file_path=Path(filename), tree=ast.parse(source), source=source)


class TestNoCrossPackageReexportRuleMeta:
    """NoCrossPackageReexportRule.meta のテスト"""

    def test_meta_正常系_ルールメタ情報を返すこと(self):
        # Arrange
        rule = NoCrossPackageReexportRule()

        # Act
        result = rule.meta

        # Assert
        assert isinstance(result, RuleMeta)
        assert result.rule_id == "no-cross-package-reexport"
        assert result.rule_name != ""
        assert result.summary != ""
        assert result.intent != ""
        assert result.guidance != ""
        assert result.suggestion != ""


class TestNoCrossPackageReexportRuleCheck:
    """NoCrossPackageReexportRule.check のテスト"""

    def test_check_正常系_init_py以外のファイルは空タプルを返すこと(self):
        # Arrange
        rule = NoCrossPackageReexportRule()
        source = 'from paladin.rule import RuleMeta\n__all__ = ["RuleMeta"]\n'
        source_file = _make_source_file(source, "src/paladin/check/module.py")

        # Act
        result = rule.check(source_file)

        # Assert
        assert result == ()

    def test_check_正常系_別パッケージのシンボルを再エクスポートすると違反を返すこと(self):
        # Arrange
        rule = NoCrossPackageReexportRule()
        source = 'from paladin.rule import RuleMeta\n__all__ = ["RuleMeta"]\n'
        source_file = _make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1

    def test_check_正常系_違反のフィールド値が正しいこと(self):
        # Arrange
        rule = NoCrossPackageReexportRule()
        source = 'from paladin.rule import RuleMeta\n__all__ = ["RuleMeta"]\n'
        source_file = _make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1
        violation = result[0]
        assert violation.file == Path("src/paladin/check/__init__.py")
        assert violation.line == 2
        assert violation.column == 0
        assert violation.rule_id == "no-cross-package-reexport"
        assert violation.rule_name != ""
        assert "RuleMeta" in violation.message
        assert "paladin.rule" in violation.message
        assert "paladin.rule" in violation.reason
        assert "paladin.check" in violation.reason
        assert "from paladin.rule import RuleMeta" in violation.suggestion

    def test_check_正常系_自パッケージのシンボルのみの場合は空タプルを返すこと(self):
        # Arrange
        rule = NoCrossPackageReexportRule()
        source = 'from paladin.check.context import CheckContext\n__all__ = ["CheckContext"]\n'
        source_file = _make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert result == ()

    def test_check_エッジケース_allが未定義の場合は空タプルを返すこと(self):
        # Arrange
        rule = NoCrossPackageReexportRule()
        source = "from paladin.rule import RuleMeta\n"
        source_file = _make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert result == ()

    def test_check_エッジケース_allが空の場合は空タプルを返すこと(self):
        # Arrange
        rule = NoCrossPackageReexportRule()
        source = "from paladin.rule import RuleMeta\n__all__ = []\n"
        source_file = _make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert result == ()

    def test_check_エッジケース_複数の別パッケージシンボルがある場合は複数の違反を返すこと(self):
        # Arrange
        rule = NoCrossPackageReexportRule()
        source = (
            "from paladin.rule import RuleMeta, Violation, Violations\n"
            '__all__ = ["RuleMeta", "Violation", "Violations"]\n'
        )
        source_file = _make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 3

    def test_check_エッジケース_同一パッケージと別パッケージのシンボルが混在する場合は別パッケージのみ違反を返すこと(
        self,
    ):
        # Arrange
        rule = NoCrossPackageReexportRule()
        source = (
            "from paladin.check.context import CheckContext\n"
            "from paladin.rule import RuleMeta\n"
            '__all__ = ["CheckContext", "RuleMeta"]\n'
        )
        source_file = _make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1
        assert result[0].message.find("RuleMeta") != -1

    def test_check_エッジケース_サブパッケージからのインポートは準拠であること(self):
        # Arrange
        rule = NoCrossPackageReexportRule()
        source = 'from paladin.check.context import CheckContext\n__all__ = ["CheckContext"]\n'
        source_file = _make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert result == ()

    def test_check_エッジケース_allに含まれるがインポートマッピングにないシンボルはスキップすること(
        self,
    ):
        # Arrange: LocalClass はファイル内定義のためインポートマッピングに存在しない
        rule = NoCrossPackageReexportRule()
        source = 'class LocalClass:\n    pass\n\n__all__ = ["LocalClass"]\n'
        source_file = _make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert result == ()

    def test_check_エッジケース_asエイリアスがある場合はasnameをキーとすること(self):
        # Arrange
        rule = NoCrossPackageReexportRule()
        source = 'from paladin.rule import RuleMeta as RM\n__all__ = ["RM"]\n'
        source_file = _make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1
        assert "RM" in result[0].message

    def test_check_エッジケース_相対インポートは検査対象外であること(self):
        # Arrange
        rule = NoCrossPackageReexportRule()
        source = 'from .context import CheckContext\n__all__ = ["CheckContext"]\n'
        source_file = _make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert result == ()

    def test_check_エッジケース_source_packageが先頭2セグメントで算出されること(self):
        # Arrange
        rule = NoCrossPackageReexportRule()
        source = 'from paladin.rule.types import Violation\n__all__ = ["Violation"]\n'
        source_file = _make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1
        # source_package は paladin.rule（先頭2セグメント）
        assert "paladin.rule" in result[0].message
        assert "from paladin.rule import Violation" in result[0].suggestion

    def test_check_エッジケース_セグメント数が2未満のインポートはそのまま使用すること(self):
        # Arrange: from os import path で __all__ = ["path"]
        rule = NoCrossPackageReexportRule()
        source = 'from os import path\n__all__ = ["path"]\n'
        source_file = _make_source_file(source, "src/myapp/__init__.py")

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1
        # source_package は os（セグメント数 1 のためそのまま使用）
        assert "os" in result[0].message

    def test_check_エッジケース_srcディレクトリが存在しない場合のフォールバック(self):
        # Arrange: src/ なしのパス
        rule = NoCrossPackageReexportRule()
        source = 'from paladin.rule import RuleMeta\n__all__ = ["RuleMeta"]\n'
        source_file = _make_source_file(source, "paladin/check/__init__.py")

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1
        # current_package は paladin.check として導出される
        assert "paladin.check" in result[0].reason

    def test_check_エッジケース_extract_all_symbolsでallの値がリスト以外の場合は空タプルを返すこと(
        self,
    ):
        # Arrange: __all__ = "Foo" のように値がリストでない場合（_extract_all_symbols の L106 を踏む）
        rule = NoCrossPackageReexportRule()
        tree = ast.parse("")
        assign = ast.Assign(
            targets=[ast.Name(id="__all__", ctx=ast.Store())],
            value=ast.Constant(value="Foo"),
        )
        ast.fix_missing_locations(assign)
        tree.body = [assign]
        source_file = SourceFile(
            file_path=Path("src/paladin/check/__init__.py"), tree=tree, source=""
        )

        # Act
        result = rule.check(source_file)

        # Assert: _extract_all_symbols が空タプルを返して早期リターン
        assert result == ()

    def test_check_エッジケース_allの値がリスト以外の場合はcontinueすること(self):
        # Arrange: 1つ目の Assign は __all__ = ["RuleMeta"]（正常）で _extract_all_symbols が
        # 空でない値を返す。2つ目の Assign も __all__ ターゲットだが値が文字列定数で
        # check() ループの L54 に到達してスキップされることを確認する
        rule = NoCrossPackageReexportRule()
        tree = ast.parse("from paladin.rule import RuleMeta\n")
        # 1つ目: 通常の __all__ = ["RuleMeta"]（_extract_all_symbols に使われる）
        assign_normal = ast.Assign(
            targets=[ast.Name(id="__all__", ctx=ast.Store())],
            value=ast.List(
                elts=[ast.Constant(value="RuleMeta")],
                ctx=ast.Load(),
            ),
        )
        # 2つ目: __all__ = "Foo"（値がリストでない）— check() ループの L54 を踏む
        assign_non_list = ast.Assign(
            targets=[ast.Name(id="__all__", ctx=ast.Store())],
            value=ast.Constant(value="Foo"),
        )
        ast.fix_missing_locations(assign_normal)
        ast.fix_missing_locations(assign_non_list)
        tree.body.extend([assign_normal, assign_non_list])
        source_file = SourceFile(
            file_path=Path("src/paladin/check/__init__.py"), tree=tree, source=""
        )

        # Act
        result = rule.check(source_file)

        # Assert: 通常の __all__ から違反1件（assign_non_list はスキップ）
        assert len(result) == 1

    def test_check_エッジケース_allの要素に非定数が含まれる場合はスキップすること(self):
        # Arrange: _extract_all_symbols が空でない値を返すよう通常の __all__ を先に置き、
        # check() ループで要素が変数のリストに到達して L57 をスキップすることを確認する
        rule = NoCrossPackageReexportRule()
        tree = ast.parse("from paladin.rule import RuleMeta\n")
        # 1つ目: 通常の __all__ = ["RuleMeta"]（_extract_all_symbols が使う）
        assign_normal = ast.Assign(
            targets=[ast.Name(id="__all__", ctx=ast.Store())],
            value=ast.List(
                elts=[ast.Constant(value="RuleMeta")],
                ctx=ast.Load(),
            ),
        )
        # 2つ目: __all__ = [variable]（要素が変数）— check() ループの L57 を踏む
        assign_non_const = ast.Assign(
            targets=[ast.Name(id="__all__", ctx=ast.Store())],
            value=ast.List(
                elts=[ast.Name(id="variable", ctx=ast.Load())],
                ctx=ast.Load(),
            ),
        )
        ast.fix_missing_locations(assign_normal)
        ast.fix_missing_locations(assign_non_const)
        tree.body.extend([assign_normal, assign_non_const])
        source_file = SourceFile(
            file_path=Path("src/paladin/check/__init__.py"), tree=tree, source=""
        )

        # Act
        result = rule.check(source_file)

        # Assert: 通常の __all__ から違反1件（非定数要素の assign はスキップ）
        assert len(result) == 1

    def test_check_エッジケース_assignターゲットがall以外の場合はスキップすること(self):
        # Arrange: x = 1 と __all__ = ["RuleMeta"] が共存する場合
        rule = NoCrossPackageReexportRule()
        source = 'from paladin.rule import RuleMeta\nx = 1\n__all__ = ["RuleMeta"]\n'
        source_file = _make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert: x = 1 はスキップされ __all__ の違反のみ報告
        assert len(result) == 1

    def test_check_エッジケース_file_pathがinit_pyのみの場合は空タプルを返すこと(self):
        # Arrange: __init__.py だけのパス（ディレクトリなし）
        rule = NoCrossPackageReexportRule()
        source = 'from paladin.rule import RuleMeta\n__all__ = ["RuleMeta"]\n'
        source_file = _make_source_file(source, "__init__.py")

        # Act
        result = rule.check(source_file)

        # Assert: パッケージ名を導出できないため空タプルを返す
        assert result == ()

    def test_check_エッジケース_import_from_moduleがNoneの場合はスキップすること(self):
        # Arrange: AST を手動構築して node.module が None の ImportFrom を作成する
        # （from . import foo のような相対インポートで level=0 かつ module=None は
        # 通常の Python 構文では生成されないが、AST を直接操作すると再現できる）
        rule = NoCrossPackageReexportRule()
        tree = ast.parse("")
        import_from = ast.ImportFrom(
            module=None,
            names=[ast.alias(name="RuleMeta", asname=None)],
            level=0,
        )
        assign = ast.Assign(
            targets=[ast.Name(id="__all__", ctx=ast.Store())],
            value=ast.List(
                elts=[ast.Constant(value="RuleMeta")],
                ctx=ast.Load(),
            ),
        )
        ast.fix_missing_locations(import_from)
        ast.fix_missing_locations(assign)
        tree.body = [import_from, assign]
        source_file = SourceFile(
            file_path=Path("src/paladin/check/__init__.py"), tree=tree, source=""
        )

        # Act
        result = rule.check(source_file)

        # Assert: module=None のインポートはマッピングに含まれないため違反なし
        assert result == ()
