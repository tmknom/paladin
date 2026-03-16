import ast
from pathlib import Path

from paladin.rule.require_all_export import RequireAllExportRule
from paladin.rule.types import RuleMeta, SourceFile


def _make_source_file(source: str, filename: str = "__init__.py") -> SourceFile:
    return SourceFile(file_path=Path(filename), tree=ast.parse(source), source=source)


class TestRequireAllExportRuleCheck:
    """RequireAllExportRule.check のテスト"""

    def test_check_正常系_init_py以外のファイルは空タプルを返すこと(self):
        # Arrange
        rule = RequireAllExportRule()
        source_file = _make_source_file("x = 1\n", "main.py")

        # Act
        result = rule.check(source_file)

        # Assert
        assert result == ()

    def test_check_エッジケース_空のinit_pyは違反なしを返すこと(self):
        # Arrange
        rule = RequireAllExportRule()
        source_file = _make_source_file("", "__init__.py")

        # Act
        result = rule.check(source_file)

        # Assert
        assert result == ()

    def test_check_エッジケース_コメントのみのinit_pyは違反なしを返すこと(self):
        # Arrange
        rule = RequireAllExportRule()
        source_file = _make_source_file("# namespace package\n", "__init__.py")

        # Act
        result = rule.check(source_file)

        # Assert
        assert result == ()

    def test_check_エッジケース_docstringのみのinit_pyは違反なしを返すこと(self):
        # Arrange
        rule = RequireAllExportRule()
        source_file = _make_source_file('"""Package."""\n', "__init__.py")

        # Act
        result = rule.check(source_file)

        # Assert
        assert result == ()

    def test_check_正常系_all未定義のinit_pyで違反を1件返すこと(self):
        # Arrange
        rule = RequireAllExportRule()
        source_file = _make_source_file("from foo import bar\n", "__init__.py")

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1

    def test_check_正常系_違反のフィールド値が正しいこと(self):
        # Arrange
        rule = RequireAllExportRule()
        source_file = _make_source_file("from foo import bar\n", "__init__.py")

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1
        violation = result[0]
        assert violation.file == Path("__init__.py")
        assert violation.line == 1
        assert violation.column == 0
        assert violation.rule_id == "require-all-export"
        assert violation.rule_name == "Require __all__ Export"

    def test_check_正常系_all定義済みのinit_pyは違反なしを返すこと(self):
        # Arrange
        rule = RequireAllExportRule()
        source = '__all__ = ["Foo"]\nfrom foo import Foo\n'
        source_file = _make_source_file(source, "__init__.py")

        # Act
        result = rule.check(source_file)

        # Assert
        assert result == ()

    def test_check_エッジケース_all定義がリスト形式でも違反なしを返すこと(self):
        # Arrange
        rule = RequireAllExportRule()
        source = '__all__ = ["Foo", "Bar"]\n'
        source_file = _make_source_file(source, "__init__.py")

        # Act
        result = rule.check(source_file)

        # Assert
        assert result == ()

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
        assert result == ()

    def test_check_正常系_相対インポートのシンボルを列挙したsuggestionを返すこと(self):
        # Arrange
        rule = RequireAllExportRule()
        source = "from .module import Foo, Bar\n"
        source_file = _make_source_file(source, "__init__.py")

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1
        violation = result[0]
        assert '__all__ = ["Bar", "Foo"]' in violation.suggestion

    def test_check_正常系_トップレベルクラスと関数を列挙したsuggestionを返すこと(self):
        # Arrange
        rule = RequireAllExportRule()
        source = "class MyClass:\n    pass\n\ndef my_func():\n    pass\n"
        source_file = _make_source_file(source, "__init__.py")

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1
        violation = result[0]
        assert '__all__ = ["MyClass", "my_func"]' in violation.suggestion

    def test_check_正常系_アンダースコア始まりのシンボルはsuggestionに含まれないこと(self):
        # Arrange
        rule = RequireAllExportRule()
        source = "from .module import _Private, Public\n"
        source_file = _make_source_file(source, "__init__.py")

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1
        violation = result[0]
        assert '"Public"' in violation.suggestion
        assert "_Private" not in violation.suggestion


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
        assert result.summary == "__init__.py に __all__ の定義を要求する"
        assert result.intent != ""
        assert result.guidance != ""
        assert result.suggestion != ""
