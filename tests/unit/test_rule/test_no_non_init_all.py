import ast
from pathlib import Path

from paladin.rule.no_non_init_all import NoNonInitAllRule
from paladin.rule.types import RuleMeta, SourceFile


def _make_source_file(source: str, filename: str = "module.py") -> SourceFile:
    return SourceFile(file_path=Path(filename), tree=ast.parse(source), source=source)


class TestNoNonInitAllRuleMeta:
    """NoNonInitAllRule.meta のテスト"""

    def test_meta_正常系_ルールメタ情報を返すこと(self):
        # Arrange
        rule = NoNonInitAllRule()

        # Act
        result = rule.meta

        # Assert
        assert isinstance(result, RuleMeta)
        assert result.rule_id == "no-non-init-all"
        assert result.rule_name == "No Non-Init All"
        assert result.summary != ""
        assert result.intent != ""
        assert result.guidance != ""
        assert result.suggestion != ""


class TestNoNonInitAllRuleCheck:
    """NoNonInitAllRule.check のテスト"""

    def test_check_正常系_init_pyの場合は空タプルを返すこと(self):
        # Arrange
        rule = NoNonInitAllRule()
        source_file = _make_source_file('__all__ = ["Foo"]\n', "__init__.py")

        # Act
        result = rule.check(source_file)

        # Assert
        assert result == ()

    def test_check_正常系_all定義のある非init_pyで違反を1件返すこと(self):
        # Arrange
        rule = NoNonInitAllRule()
        source_file = _make_source_file('__all__ = ["Foo"]\n', "module.py")

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1

    def test_check_正常系_違反のフィールド値が正しいこと(self):
        # Arrange
        rule = NoNonInitAllRule()
        source = '__all__ = ["Foo"]\n'
        source_file = _make_source_file(source, "module.py")

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1
        violation = result[0]
        assert violation.file == Path("module.py")
        assert violation.line == 1
        assert violation.column == 0
        assert violation.rule_id == "no-non-init-all"
        assert violation.rule_name == "No Non-Init All"
        assert violation.message == "__init__.py 以外のファイルに __all__ が定義されている"
        assert violation.reason != ""
        assert violation.suggestion != ""

    def test_check_エッジケース_augassign形式のall定義でも違反を返すこと(self):
        # Arrange: AugAssign パスをカバーするため AST を手動で構築する
        # (Python の構文上 Assign なしの AugAssign は NameError になるため、
        # ソースコードから parse すると Assign が先に来て AugAssign に到達しない)
        rule = NoNonInitAllRule()
        tree = ast.parse("")
        aug_assign = ast.AugAssign(
            target=ast.Name(id="__all__", ctx=ast.Store()),
            op=ast.Add(),
            value=ast.List(elts=[ast.Constant(value="bar")], ctx=ast.Load()),
        )
        ast.fix_missing_locations(aug_assign)
        tree.body = [aug_assign]
        source_file = SourceFile(file_path=Path("module.py"), tree=tree, source="")

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1

    def test_check_エッジケース_空のソースコードは空タプルを返すこと(self):
        # Arrange
        rule = NoNonInitAllRule()
        source_file = _make_source_file("", "module.py")

        # Act
        result = rule.check(source_file)

        # Assert
        assert result == ()

    def test_check_エッジケース_all定義のない非init_pyは空タプルを返すこと(self):
        # Arrange
        rule = NoNonInitAllRule()
        source_file = _make_source_file("x = 1\n", "module.py")

        # Act
        result = rule.check(source_file)

        # Assert
        assert result == ()

    def test_check_エッジケース_関数内のall代入は検出対象外であること(self):
        # Arrange
        rule = NoNonInitAllRule()
        source = 'def foo():\n    __all__ = ["bar"]\n'
        source_file = _make_source_file(source, "module.py")

        # Act
        result = rule.check(source_file)

        # Assert
        assert result == ()

    def test_check_エッジケース_複数のall代入がある場合は最初の1件のみ報告すること(self):
        # Arrange: AST を手動で構築して Assign と AugAssign を両方置く
        rule = NoNonInitAllRule()
        tree = ast.parse('__all__ = ["Foo"]\n')
        aug_assign = ast.AugAssign(
            target=ast.Name(id="__all__", ctx=ast.Store()),
            op=ast.Add(),
            value=ast.List(elts=[ast.Constant(value="Bar")], ctx=ast.Load()),
        )
        ast.fix_missing_locations(aug_assign)
        tree.body.append(aug_assign)
        source_file = SourceFile(
            file_path=Path("module.py"), tree=tree, source='__all__ = ["Foo"]\n'
        )

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1
