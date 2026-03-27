import ast
from pathlib import Path

import pytest

from paladin.rule.no_cross_package_reexport import (
    CrossPackageReexportDetector,
    ImportMappingCollector,
    NoCrossPackageReexportRule,
)
from paladin.rule.types import RuleMeta, SourceFile
from tests.unit.test_rule.helpers import make_source_file


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


class TestNoCrossPackageReexportRuleCheck:
    """NoCrossPackageReexportRule.check のテスト"""

    def test_check_エッジケース_複数の別パッケージシンボルがある場合は複数の違反を返すこと(self):
        # Arrange
        rule = NoCrossPackageReexportRule()
        source = (
            "from paladin.rule import RuleMeta, Violation, Violations\n"
            '__all__ = ["RuleMeta", "Violation", "Violations"]\n'
        )
        source_file = make_source_file(source, "src/paladin/check/__init__.py")

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
        source_file = make_source_file(source, "src/paladin/check/__init__.py")

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1

    @pytest.mark.parametrize(
        ("source", "filename"),
        [
            pytest.param(
                'from paladin.rule import RuleMeta\n__all__ = ["RuleMeta"]\n',
                "src/paladin/check/module.py",
                id="init_py以外のファイル",
            ),
            pytest.param(
                'from paladin.check.context import CheckContext\n__all__ = ["CheckContext"]\n',
                "src/paladin/check/__init__.py",
                id="自パッケージのシンボルのみ",
            ),
            pytest.param(
                "from paladin.rule import RuleMeta\n",
                "src/paladin/check/__init__.py",
                id="allが未定義",
            ),
            pytest.param(
                'class LocalClass:\n    pass\n\n__all__ = ["LocalClass"]\n',
                "src/paladin/check/__init__.py",
                id="allに含まれるがインポートマッピングにないシンボル",
            ),
            pytest.param(
                'from .context import CheckContext\n__all__ = ["CheckContext"]\n',
                "src/paladin/check/__init__.py",
                id="相対インポートは検査対象外",
            ),
            pytest.param(
                'import paladin.rule\n__all__ = ["paladin"]\n',
                "src/paladin/check/__init__.py",
                id="import文はインポートマッピングに含まれない",
            ),
            pytest.param(
                'from os import path\n__all__ = ["path"]\n',
                "src/paladin/__init__.py",
                id="トップレベルパッケージのinit_pyは検査対象外",
            ),
            pytest.param(
                'from paladin.rule import RuleMeta\n__all__ = ["RuleMeta"]\n',
                "__init__.py",
                id="file_pathがinit_pyのみ",
            ),
            pytest.param(
                'from tests.unit.fake.rule import FakeRule\n__all__ = ["FakeRule"]\n',
                "/fake/project/tests/unit/fake/__init__.py",
                id="tests配下の同一パッケージシンボルは違反なし",
            ),
        ],
    )
    def test_check_違反なしのケースで空を返すこと(self, source: str, filename: str) -> None:
        # Arrange
        rule = NoCrossPackageReexportRule()
        source_file = make_source_file(source, filename)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 0

    @pytest.mark.parametrize(
        ("source", "filename"),
        [
            pytest.param(
                'from paladin.rule import RuleMeta\n__all__ = ["RuleMeta"]\n',
                "src/paladin/check/__init__.py",
                id="別パッケージのシンボルを再エクスポート",
            ),
            pytest.param(
                'from paladin.rule import RuleMeta as RM\n__all__ = ["RM"]\n',
                "src/paladin/check/__init__.py",
                id="asエイリアスがある場合はasnameをキー",
            ),
            pytest.param(
                'from paladin.rule.types import Violation\n__all__ = ["Violation"]\n',
                "src/paladin/check/__init__.py",
                id="source_packageが先頭2セグメントで算出",
            ),
            pytest.param(
                'from os import path\n__all__ = ["path"]\n',
                "src/myapp/sub/__init__.py",
                id="セグメント数が2未満のインポート",
            ),
            pytest.param(
                'from paladin.rule import RuleMeta\n__all__ = ["RuleMeta"]\n',
                "paladin/check/__init__.py",
                id="srcディレクトリが存在しない場合のフォールバック",
            ),
            pytest.param(
                'from paladin.rule import RuleMeta\n__all__ = ["RuleMeta"]\n',
                "/fake/project/src/paladin/check/__init__.py",
                id="絶対パスでもsrcアンカー以降のパッケージを正しく導出",
            ),
            pytest.param(
                'from paladin.rule import RuleMeta\n__all__ = ["RuleMeta"]\n',
                "tests/unit/fake/__init__.py",
                id="tests配下の相対パスでもパッケージを正しく導出",
            ),
            pytest.param(
                'from paladin.rule import RuleMeta\n__all__ = ["RuleMeta"]\n',
                "/fake/project/tests/unit/fake/__init__.py",
                id="tests配下の絶対パスでもパッケージを正しく導出",
            ),
            pytest.param(
                'from paladin.rule import RuleMeta\nx = 1\n__all__ = ["RuleMeta"]\n',
                "src/paladin/check/__init__.py",
                id="assignターゲットがall以外の場合はスキップ",
            ),
        ],
    )
    def test_check_違反ありのケースで1件返すこと(self, source: str, filename: str) -> None:
        # Arrange
        rule = NoCrossPackageReexportRule()
        source_file = make_source_file(source, filename)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1

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
        assert len(result) == 0


class TestImportMappingCollector:
    """ImportMappingCollector のテスト"""

    def test_collect_正常系_from_importのマッピングを返すこと(self):
        source = 'from paladin.rule import RuleMeta\n__all__ = ["RuleMeta"]\n'
        source_file = make_source_file(source, "src/paladin/check/__init__.py")
        result = ImportMappingCollector.collect(source_file)
        assert result == {"RuleMeta": "paladin.rule"}

    def test_collect_正常系_相対インポートはスキップすること(self):
        source = 'from .formatter import Formatter\n__all__ = ["Formatter"]\n'
        source_file = make_source_file(source, "src/paladin/check/__init__.py")
        result = ImportMappingCollector.collect(source_file)
        assert result == {}


class TestCrossPackageReexportDetector:
    """CrossPackageReexportDetector のテスト"""

    def test_detect_正常系_Violationを返すこと(self):
        source = 'from paladin.rule import RuleMeta\n__all__ = ["RuleMeta"]\n'
        source_file = make_source_file(source, "src/paladin/check/__init__.py")
        rule = NoCrossPackageReexportRule()
        result = CrossPackageReexportDetector.detect(
            source_file=source_file,
            line=2,
            name="RuleMeta",
            source_package="paladin.rule",
            current_package="paladin.check",
            meta=rule.meta,
        )
        assert result.rule_id == "no-cross-package-reexport"
