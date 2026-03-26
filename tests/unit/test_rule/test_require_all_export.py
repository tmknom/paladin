import ast
from pathlib import Path

import pytest

from paladin.rule.require_all_export import (
    AllExportDetector,
    PublicSymbolCollector,
    RequireAllExportRule,
)
from paladin.rule.types import RuleMeta, SourceFile
from tests.unit.test_rule.helpers import make_source_file


class TestRequireAllExportRuleMeta:
    """RequireAllExportRule.meta のテスト"""

    def test_meta_正常系_ルールメタ情報を返すこと(self):
        # Arrange
        rule = RequireAllExportRule()

        # Act
        result = rule.meta

        # Assert
        assert isinstance(result, RuleMeta)
        assert result.rule_id == "require-all-export"
        assert result.rule_name == "Require __all__ Export"


class TestRequireAllExportRuleCheck:
    """RequireAllExportRule.check のテスト"""

    @pytest.mark.parametrize(
        ("source", "filename"),
        [
            pytest.param("x = 1\n", "main.py", id="init_py以外"),
            pytest.param("# namespace package\n", "__init__.py", id="コメントのみ"),
            pytest.param(
                '__all__ = ["Foo"]\nfrom foo import Foo\n', "__init__.py", id="all定義済み"
            ),
            pytest.param('__all__ = ["Foo", "Bar"]\n', "__init__.py", id="allリスト形式"),
        ],
    )
    def test_check_違反なしのケースで空を返すこと(self, source: str, filename: str) -> None:
        # Arrange
        rule = RequireAllExportRule()
        source_file = make_source_file(source, filename)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 0

    @pytest.mark.parametrize(
        ("source", "filename"),
        [
            pytest.param("from foo import bar\n", "__init__.py", id="all未定義のinit_py"),
        ],
    )
    def test_check_違反ありのケースで1件返すこと(self, source: str, filename: str) -> None:
        # Arrange
        rule = RequireAllExportRule()
        source_file = make_source_file(source, filename)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1

    def test_check_エッジケース_all追加代入でも違反なしを返すこと(self):
        # Arrange: AugAssign パスをカバーするため AST を手動で構築する
        # (Python の構文上 Assign なしの AugAssign は NameError になるため、
        # ソースコードから parse すると Assign が先に来て AugAssign に到達しない)
        rule = RequireAllExportRule()
        tree = ast.parse("")
        aug_assign = ast.AugAssign(
            target=ast.Name(id="__all__", ctx=ast.Store()),
            op=ast.Add(),
            value=ast.List(elts=[ast.Constant(value="bar")], ctx=ast.Load()),
        )
        ast.fix_missing_locations(aug_assign)
        import_node = ast.parse("from foo import bar\n").body[0]
        tree.body = [import_node, aug_assign]
        source_file = SourceFile(file_path=Path("__init__.py"), tree=tree, source="")

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 0


class TestPublicSymbolCollector:
    """PublicSymbolCollector のテスト"""

    def test_collect_正常系_相対インポートのシンボルを返すこと(self):
        source = "from .module import Foo, Bar\n"
        source_file = make_source_file(source, "__init__.py")
        result = PublicSymbolCollector.collect(source_file)
        assert sorted(result) == ["Bar", "Foo"]

    def test_collect_正常系_クラスと関数を返すこと(self):
        source = "class MyClass:\n    pass\n\ndef my_func():\n    pass\n"
        source_file = make_source_file(source, "__init__.py")
        result = PublicSymbolCollector.collect(source_file)
        assert sorted(result) == ["MyClass", "my_func"]

    def test_collect_正常系_アンダースコア始まりは除外されること(self):
        source = "from .module import _Private, Public\n"
        source_file = make_source_file(source, "__init__.py")
        result = PublicSymbolCollector.collect(source_file)
        assert result == ["Public"]

    def test_has_substantial_code_正常系_コードがあればTrueを返すこと(self):
        tree = ast.parse("x = 1\n")
        assert PublicSymbolCollector.has_substantial_code(tree) is True

    def test_has_substantial_code_正常系_docstringのみはFalseを返すこと(self):
        tree = ast.parse('"""docstring"""\n')
        assert PublicSymbolCollector.has_substantial_code(tree) is False

    def test_has_substantial_code_正常系_空ファイルはFalseを返すこと(self):
        tree = ast.parse("")
        assert PublicSymbolCollector.has_substantial_code(tree) is False


class TestAllExportDetector:
    """AllExportDetector のテスト"""

    def test_detect_正常系_シンボルありのViolationを返すこと(self):
        source = "from .module import Foo\n"
        source_file = make_source_file(source, "__init__.py")
        rule = RequireAllExportRule()
        result = AllExportDetector.detect(source_file, ["Foo"], rule.meta)
        assert result.rule_id == "require-all-export"

    def test_detect_正常系_シンボルなしのViolationを返すこと(self):
        source = "x = 1\n"
        source_file = make_source_file(source, "__init__.py")
        rule = RequireAllExportRule()
        result = AllExportDetector.detect(source_file, [], rule.meta)
        assert result.rule_id == "require-all-export"
