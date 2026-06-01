"""no-module-level-function ルールのユニットテスト"""

import ast

from paladin.rule.no_module_level_function import (
    DecoratorAllowChecker,
    ModuleLevelFunctionCollector,
    ModuleLevelFunctionDetector,
    NoModuleLevelFunctionRule,
)
from paladin.rule.types import RuleMeta, Violation
from tests.unit.test_rule.helper import SourceFileFactory


class TestModuleLevelFunctionCollector:
    """ModuleLevelFunctionCollector.collect のテスト"""

    def test_collect_正常系_モジュール直下のFunctionDefを収集すること(self):
        # Arrange
        source = "def foo():\n    pass\n"
        tree = ast.parse(source)

        # Act
        result = ModuleLevelFunctionCollector.collect(tree)

        # Assert
        assert len(result) == 1
        assert result[0].name == "foo"

    def test_collect_正常系_モジュール直下のAsyncFunctionDefを収集すること(self):
        # Arrange
        source = "async def bar():\n    pass\n"
        tree = ast.parse(source)

        # Act
        result = ModuleLevelFunctionCollector.collect(tree)

        # Assert
        assert len(result) == 1
        assert result[0].name == "bar"

    def test_collect_正常系_複数の関数を定義順に収集すること(self):
        # Arrange
        source = "def foo():\n    pass\ndef bar():\n    pass\n"
        tree = ast.parse(source)

        # Act
        result = ModuleLevelFunctionCollector.collect(tree)

        # Assert
        assert len(result) == 2
        assert result[0].name == "foo"
        assert result[1].name == "bar"

    def test_collect_正常系_ClassDef内のメソッドは収集しないこと(self):
        # Arrange
        source = "class C:\n    def m(self):\n        pass\n"
        tree = ast.parse(source)

        # Act
        result = ModuleLevelFunctionCollector.collect(tree)

        # Assert
        assert result == ()

    def test_collect_正常系_関数内のネスト関数は収集しないこと(self):
        # Arrange
        source = "def outer():\n    def inner():\n        pass\n"
        tree = ast.parse(source)

        # Act
        result = ModuleLevelFunctionCollector.collect(tree)

        # Assert
        assert len(result) == 1
        assert result[0].name == "outer"

    def test_collect_正常系_if__name___ブロック内の関数は収集しないこと(self):
        # Arrange
        source = 'if __name__ == "__main__":\n    def helper():\n        pass\n'
        tree = ast.parse(source)

        # Act
        result = ModuleLevelFunctionCollector.collect(tree)

        # Assert
        assert result == ()

    def test_collect_正常系_decorator_listを保持したノードを返すこと(self):
        # Arrange
        source = "import pytest\n\n@pytest.fixture\ndef tmp_source():\n    pass\n"
        tree = ast.parse(source)

        # Act
        result = ModuleLevelFunctionCollector.collect(tree)

        # Assert
        assert len(result) == 1
        assert len(result[0].decorator_list) > 0

    def test_collect_エッジケース_関数なしで空タプルを返すこと(self):
        # Arrange
        source = "x = 1\n"
        tree = ast.parse(source)

        # Act
        result = ModuleLevelFunctionCollector.collect(tree)

        # Assert
        assert result == ()


class TestDecoratorAllowChecker:
    """DecoratorAllowChecker のテスト"""

    def test_decorator_name_正常系_Name表記の名前を返すこと(self):
        # Arrange
        decorator = ast.parse("fixture", mode="eval").body

        # Act
        result = DecoratorAllowChecker.decorator_name(decorator)

        # Assert
        assert result == "fixture"

    def test_decorator_name_正常系_Attribute表記のドット連結を返すこと(self):
        # Arrange
        decorator = ast.parse("pytest.fixture", mode="eval").body

        # Act
        result = DecoratorAllowChecker.decorator_name(decorator)

        # Assert
        assert result == "pytest.fixture"

    def test_decorator_name_正常系_ネストAttributeのドット連結を返すこと(self):
        # Arrange
        decorator = ast.parse("some.deeper.path", mode="eval").body

        # Act
        result = DecoratorAllowChecker.decorator_name(decorator)

        # Assert
        assert result == "some.deeper.path"

    def test_decorator_name_正常系_Call表記のfuncを再帰的に文字列化すること(self):
        # Arrange
        decorator = ast.parse('pytest.fixture(scope="module")', mode="eval").body

        # Act
        result = DecoratorAllowChecker.decorator_name(decorator)

        # Assert
        assert result == "pytest.fixture"

    def test_decorator_name_エッジケース_文字列化不能な式でNoneを返すこと(self):
        # Arrange: ast.Constant は Name でも Attribute でも Call でもない
        decorator = ast.Constant(value=42)

        # Act
        result = DecoratorAllowChecker.decorator_name(decorator)

        # Assert
        assert result is None

    def test_decorator_name_エッジケース_Attributeの親が解決不能な場合NoneをReturnすること(self):
        # Arrange: Attribute の value が Constant（解決不能）な場合
        decorator = ast.Attribute(value=ast.Constant(value=42), attr="fixture")

        # Act
        result = DecoratorAllowChecker.decorator_name(decorator)

        # Assert
        assert result is None

    def test_is_allowed_正常系_許可リストに完全一致する場合Trueを返すこと(self):
        # Arrange
        source = "import pytest\n\n@pytest.fixture\ndef tmp_source():\n    pass\n"
        tree = ast.parse(source)
        node = next(n for n in tree.body if isinstance(n, ast.FunctionDef))
        allow = frozenset({"pytest.fixture"})

        # Act
        result = DecoratorAllowChecker.is_allowed(node, allow)

        # Assert
        assert result is True

    def test_is_allowed_正常系_許可リストに含まれない場合Falseを返すこと(self):
        # Arrange
        source = "from dataclasses import dataclass\n\n@dataclass\ndef foo():\n    pass\n"
        tree = ast.parse(source)
        node = next(n for n in tree.body if isinstance(n, ast.FunctionDef))
        allow = frozenset({"pytest.fixture"})

        # Act
        result = DecoratorAllowChecker.is_allowed(node, allow)

        # Assert
        assert result is False

    def test_is_allowed_正常系_decorator_listが空の場合Falseを返すこと(self):
        # Arrange
        source = "def foo():\n    pass\n"
        tree = ast.parse(source)
        node = next(n for n in tree.body if isinstance(n, ast.FunctionDef))
        allow = frozenset({"pytest.fixture"})

        # Act
        result = DecoratorAllowChecker.is_allowed(node, allow)

        # Assert
        assert result is False

    def test_is_allowed_正常系_複数デコレータのうち1つでも許可ならTrue(self):
        # Arrange
        source = (
            "from dataclasses import dataclass\nimport pytest\n\n"
            "@dataclass\n@pytest.fixture\ndef foo():\n    pass\n"
        )
        tree = ast.parse(source)
        node = next(n for n in tree.body if isinstance(n, ast.FunctionDef))
        allow = frozenset({"pytest.fixture"})

        # Act
        result = DecoratorAllowChecker.is_allowed(node, allow)

        # Assert
        assert result is True


class TestModuleLevelFunctionDetector:
    """ModuleLevelFunctionDetector.detect のテスト"""

    def _make_meta(self) -> RuleMeta:
        return RuleMeta(
            rule_id="no-module-level-function",
            rule_name="No Module Level Function",
            summary="summary",
            intent="intent",
            guidance="guidance",
            suggestion="suggestion",
        )

    def test_detect_正常系_関数名がmessageに含まれること(self):
        # Arrange
        source = "def calc_file_length():\n    pass\n"
        source_file = SourceFileFactory.make(source)
        tree = ast.parse(source)
        node = next(n for n in tree.body if isinstance(n, ast.FunctionDef))
        meta = self._make_meta()

        # Act
        result = ModuleLevelFunctionDetector.detect(node, source_file, meta)

        # Assert
        assert "calc_file_length" in result.message

    def test_detect_正常系_violation_lineがdef文の行番号と一致すること(self):
        # Arrange
        source = "\n\ndef foo():\n    pass\n"
        source_file = SourceFileFactory.make(source)
        tree = ast.parse(source)
        node = next(n for n in tree.body if isinstance(n, ast.FunctionDef))
        meta = self._make_meta()

        # Act
        result = ModuleLevelFunctionDetector.detect(node, source_file, meta)

        # Assert
        assert result.line == 3

    def test_detect_正常系_violation_columnがdef文の列位置と一致すること(self):
        # Arrange
        source = "def foo():\n    pass\n"
        source_file = SourceFileFactory.make(source)
        tree = ast.parse(source)
        node = next(n for n in tree.body if isinstance(n, ast.FunctionDef))
        meta = self._make_meta()

        # Act
        result = ModuleLevelFunctionDetector.detect(node, source_file, meta)

        # Assert
        assert result.column == 0

    def test_detect_正常系_rule_id_rule_name_reason_suggestionが固定値であること(self):
        # Arrange
        source = "def foo():\n    pass\n"
        source_file = SourceFileFactory.make(source)
        tree = ast.parse(source)
        node = next(n for n in tree.body if isinstance(n, ast.FunctionDef))
        meta = self._make_meta()

        # Act
        result = ModuleLevelFunctionDetector.detect(node, source_file, meta)

        # Assert
        assert result.rule_id == "no-module-level-function"
        assert result.rule_name == "No Module Level Function"

    def test_detect_正常系_AsyncFunctionDefでもViolationを生成すること(self):
        # Arrange
        source = "async def helper():\n    pass\n"
        source_file = SourceFileFactory.make(source)
        tree = ast.parse(source)
        node = next(n for n in tree.body if isinstance(n, ast.AsyncFunctionDef))
        meta = self._make_meta()

        # Act
        result = ModuleLevelFunctionDetector.detect(node, source_file, meta)

        # Assert
        assert isinstance(result, Violation)
        assert "helper" in result.message


class TestNoModuleLevelFunctionRuleMeta:
    """NoModuleLevelFunctionRule.meta プロパティのテスト"""

    def test_meta_正常系_ルールメタ情報を返すこと(self):
        # Arrange
        rule = NoModuleLevelFunctionRule()

        # Act
        result = rule.meta

        # Assert
        assert isinstance(result, RuleMeta)
        assert result.rule_id == "no-module-level-function"
        assert result.rule_name == "No Module Level Function"


class TestNoModuleLevelFunctionRuleCheck:
    """NoModuleLevelFunctionRule.check メソッドのテスト"""

    def test_check_正常系_モジュールレベル関数1件を違反として返すこと(self):
        # Arrange
        source = "def calc():\n    pass\n"
        source_file = SourceFileFactory.make(source)
        rule = NoModuleLevelFunctionRule()

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1
        assert result[0].rule_id == "no-module-level-function"
        assert result[0].line == 1

    def test_check_正常系_pytest_fixtureデコレータ付き関数は違反としないこと(self):
        # Arrange
        source = "import pytest\n\n@pytest.fixture\ndef tmp_source():\n    pass\n"
        source_file = SourceFileFactory.make(source)
        rule = NoModuleLevelFunctionRule()

        # Act
        result = rule.check(source_file)

        # Assert
        assert result == ()

    def test_check_正常系_fixture単独デコレータ付き関数も違反としないこと(self):
        # Arrange
        source = "from pytest import fixture\n\n@fixture\ndef tmp_source():\n    pass\n"
        source_file = SourceFileFactory.make(source)
        rule = NoModuleLevelFunctionRule()

        # Act
        result = rule.check(source_file)

        # Assert
        assert result == ()

    def test_check_正常系_class内メソッドは違反としないこと(self):
        # Arrange
        source = "class C:\n    def m(self):\n        pass\n"
        source_file = SourceFileFactory.make(source)
        rule = NoModuleLevelFunctionRule()

        # Act
        result = rule.check(source_file)

        # Assert
        assert result == ()

    def test_check_正常系_AsyncFunctionDefも違反として検出すること(self):
        # Arrange
        source = "async def helper():\n    pass\n"
        source_file = SourceFileFactory.make(source)
        rule = NoModuleLevelFunctionRule()

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1

    def test_check_正常系_複数のモジュールレベル関数を定義順に検出すること(self):
        # Arrange
        source = "def a():\n    pass\ndef b():\n    pass\n"
        source_file = SourceFileFactory.make(source)
        rule = NoModuleLevelFunctionRule()

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 2
        assert result[0].line < result[1].line

    def test_check_正常系_カスタムallow_decoratorsを尊重すること(self):
        # Arrange
        source = "from dataclasses import dataclass\n\n@dataclass\ndef foo():\n    pass\n"
        source_file = SourceFileFactory.make(source)
        rule = NoModuleLevelFunctionRule(allow_decorators=("dataclass",))

        # Act
        result = rule.check(source_file)

        # Assert
        assert result == ()

    def test_check_エッジケース_関数定義なしで空タプルを返すこと(self):
        # Arrange
        source = "x = 1\n"
        source_file = SourceFileFactory.make(source)
        rule = NoModuleLevelFunctionRule()

        # Act
        result = rule.check(source_file)

        # Assert
        assert result == ()

    def test_check_エッジケース_if__name___ブロック内の関数は違反としないこと(self):
        # Arrange
        source = 'if __name__ == "__main__":\n    def helper():\n        pass\n'
        source_file = SourceFileFactory.make(source)
        rule = NoModuleLevelFunctionRule()

        # Act
        result = rule.check(source_file)

        # Assert
        assert result == ()

    def test_check_正常系_allow_filesに完全一致するファイルは違反としないこと(self):
        # Arrange
        source = "def calc():\n    pass\n"
        source_file = SourceFileFactory.make(source, "src/paladin/cli.py")
        rule = NoModuleLevelFunctionRule(allow_files=("src/paladin/cli.py",))

        # Act
        result = rule.check(source_file)

        # Assert
        assert result == ()

    def test_check_正常系_allow_filesに一致しないファイルは違反として検出すること(self):
        # Arrange
        source = "def calc():\n    pass\n"
        source_file = SourceFileFactory.make(source, "src/paladin/other.py")
        rule = NoModuleLevelFunctionRule(allow_files=("src/paladin/cli.py",))

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1

    def test_check_正常系_allow_files引数なしのデフォルトで違反を検出すること(self):
        # Arrange
        source = "def calc():\n    pass\n"
        source_file = SourceFileFactory.make(source, "src/paladin/cli.py")
        rule = NoModuleLevelFunctionRule()

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1

    def test_check_正常系_allow_filesに前方一致するが完全一致しないパスは違反として検出すること(
        self,
    ):
        # Arrange
        source = "def calc():\n    pass\n"
        source_file = SourceFileFactory.make(source, "src/paladin/cli.py")
        rule = NoModuleLevelFunctionRule(allow_files=("src/paladin/cli",))

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1
