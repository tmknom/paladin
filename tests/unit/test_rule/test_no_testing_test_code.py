"""NoTestingTestCodeRule のテスト"""

import ast
from pathlib import Path

from paladin.rule.no_testing_test_code import NoTestingTestCodeRule
from paladin.rule.types import RuleMeta, SourceFile, SourceFiles


def _make_source_file(source: str, filename: str = "tests/unit/test_foo.py") -> SourceFile:
    return SourceFile(file_path=Path(filename), tree=ast.parse(source), source=source)


def _make_source_files(*files: tuple[str, str]) -> SourceFiles:
    return SourceFiles(files=tuple(_make_source_file(src, name) for src, name in files))


class TestNoTestingTestCodeRuleMeta:
    """Phase 1: メタ情報のテスト"""

    def test_meta_正常系_RuleMetaインスタンスを返すこと(self):
        rule = NoTestingTestCodeRule()
        assert isinstance(rule.meta, RuleMeta)

    def test_meta_正常系_rule_idが正しいこと(self):
        rule = NoTestingTestCodeRule()
        assert rule.meta.rule_id == "no-testing-test-code"

    def test_meta_正常系_rule_nameが正しいこと(self):
        rule = NoTestingTestCodeRule()
        assert rule.meta.rule_name == "No Testing Test Code"


class TestNoTestingTestCodeRuleClassBased:
    """Phase 2: TestXxx クラス名ベースの違反検出"""

    def test_check_違反検出_TestXxxクラスがtestsからのインポートと名前一致する場合に違反を検出すること(
        self,
    ):
        # Arrange: TestInMemoryFsReader は InMemoryFsReader をテストしている
        source = (
            "from tests.unit.fakes.fs import InMemoryFsReader\n"
            "\n"
            "class TestInMemoryFsReader:\n"
            "    def test_read(self) -> None:\n"
            "        pass\n"
        )
        source_files = _make_source_files((source, "tests/unit/test_fakes/test_fs.py"))

        # Act
        violations = NoTestingTestCodeRule().check(source_files)

        # Assert
        assert len(violations) == 1
        assert violations[0].rule_id == "no-testing-test-code"
        assert "InMemoryFsReader" in violations[0].message

    def test_check_準拠確認_TestXxxがtestsからのインポートと名前不一致の場合は違反なし(self):
        # Arrange: TestCheckOrchestrator は InMemoryFsReader をセットアップに使っているだけ
        source = (
            "from tests.unit.fakes.fs import InMemoryFsReader\n"
            "\n"
            "class TestCheckOrchestrator:\n"
            "    def test_orchestrate(self) -> None:\n"
            "        reader = InMemoryFsReader()\n"
        )
        source_files = _make_source_files((source, "tests/unit/test_check/test_orchestrator.py"))

        # Act
        violations = NoTestingTestCodeRule().check(source_files)

        # Assert
        assert len(violations) == 0

    def test_check_準拠確認_srcからのインポートはtests検出対象外であること(self):
        # Arrange: src/ からインポートしたクラスのテストは正当
        source = (
            "from paladin.check.orchestrator import CheckOrchestrator\n"
            "\n"
            "class TestCheckOrchestrator:\n"
            "    def test_orchestrate(self) -> None:\n"
            "        pass\n"
        )
        source_files = _make_source_files((source, "tests/unit/test_check/test_orchestrator.py"))

        # Act
        violations = NoTestingTestCodeRule().check(source_files)

        # Assert
        assert len(violations) == 0

    def test_check_準拠確認_テストファイルでないファイルはスキップされること(self):
        # Arrange: src/ 配下のファイルは対象外
        source = (
            "from tests.unit.fakes.fs import InMemoryFsReader\n"
            "\n"
            "class TestInMemoryFsReader:\n"
            "    pass\n"
        )
        source_files = _make_source_files((source, "src/paladin/some_module.py"))

        # Act
        violations = NoTestingTestCodeRule().check(source_files)

        # Assert
        assert len(violations) == 0


class TestNoTestingTestCodeRuleFunctionBased:
    """Phase 3: test_xxx 関数名ベースの違反検出"""

    def test_check_違反検出_test_xxx関数がtestsインポートのsnake_case名と一致する場合に違反を検出すること(
        self,
    ):
        # Arrange: test_in_memory_fs_reader_xxx は InMemoryFsReader をテストしている
        source = (
            "from tests.unit.fakes.fs import InMemoryFsReader\n"
            "\n"
            "def test_in_memory_fs_reader_returns_content() -> None:\n"
            "    pass\n"
        )
        source_files = _make_source_files((source, "tests/unit/test_fakes/test_fs.py"))

        # Act
        violations = NoTestingTestCodeRule().check(source_files)

        # Assert
        assert len(violations) == 1
        assert "InMemoryFsReader" in violations[0].message

    def test_check_準拠確認_test_xxx関数がtestsインポートのsnake_case名と不一致の場合は違反なし(
        self,
    ):
        # Arrange: test_orchestrate は InMemoryFsReader と名前が一致しない
        source = (
            "from tests.unit.fakes.fs import InMemoryFsReader\n"
            "\n"
            "def test_orchestrate() -> None:\n"
            "    reader = InMemoryFsReader()\n"
        )
        source_files = _make_source_files((source, "tests/unit/test_check/test_orchestrator.py"))

        # Act
        violations = NoTestingTestCodeRule().check(source_files)

        # Assert
        assert len(violations) == 0

    def test_check_違反検出_test_xxx関数がsnake_case名と完全一致する場合に違反を検出すること(self):
        # Arrange: test_in_memory_fs_reader (サフィックスなし完全一致)
        source = (
            "from tests.unit.fakes.fs import InMemoryFsReader\n"
            "\n"
            "def test_in_memory_fs_reader() -> None:\n"
            "    pass\n"
        )
        source_files = _make_source_files((source, "tests/unit/test_fakes/test_fs.py"))

        # Act
        violations = NoTestingTestCodeRule().check(source_files)

        # Assert
        assert len(violations) == 1


class TestNoTestingTestCodeRuleConftestExclusion:
    """Phase 4: conftest.py の除外"""

    def test_check_準拠確認_conftestpyはスキップされること(self):
        # Arrange: conftest.py は除外対象
        source = (
            "from tests.unit.fakes.fs import InMemoryFsReader\n"
            "\n"
            "class TestInMemoryFsReader:\n"
            "    pass\n"
        )
        source_files = _make_source_files((source, "tests/unit/conftest.py"))

        # Act
        violations = NoTestingTestCodeRule().check(source_files)

        # Assert
        assert len(violations) == 0


class TestNoTestingTestCodeRuleEdgeCases:
    """Phase 5: エッジケース"""

    def test_check_正常系_空のSourceFilesで違反なし(self):
        source_files = SourceFiles(files=())
        violations = NoTestingTestCodeRule().check(source_files)
        assert violations == ()

    def test_check_正常系_testsインポートなしのテストファイルで違反なし(self):
        source = "class TestFoo:\n    def test_something(self) -> None:\n        pass\n"
        source_files = _make_source_files((source, "tests/unit/test_foo.py"))
        violations = NoTestingTestCodeRule().check(source_files)
        assert len(violations) == 0

    def test_check_違反検出_エイリアスインポートでも元の名前が診断メッセージに表示されること(self):
        # Arrange: alias で別名インポートしている場合
        source = (
            "from tests.unit.fakes.fs import InMemoryFsReader as FakeReader\n"
            "\n"
            "class TestFakeReader:\n"
            "    pass\n"
        )
        source_files = _make_source_files((source, "tests/unit/test_fakes/test_fs.py"))

        # Act
        violations = NoTestingTestCodeRule().check(source_files)

        # Assert: bound_name=FakeReader が TestFakeReader と一致、message に InMemoryFsReader
        assert len(violations) == 1
        assert "InMemoryFsReader" in violations[0].message

    def test_check_違反検出_複数違反がある場合にすべて検出されること(self):
        # Arrange: 2つの Fake クラスに対して2つのテストクラスがある
        source = (
            "from tests.unit.fakes.fs import InMemoryFsReader\n"
            "from tests.unit.fakes.db import FakeDatabase\n"
            "\n"
            "class TestInMemoryFsReader:\n"
            "    pass\n"
            "\n"
            "class TestFakeDatabase:\n"
            "    pass\n"
        )
        source_files = _make_source_files((source, "tests/unit/test_fakes/test_all.py"))

        # Act
        violations = NoTestingTestCodeRule().check(source_files)

        # Assert
        assert len(violations) == 2

    def test_check_準拠確認_Testで始まらないクラスと非test_関数は対象外であること(self):
        # Arrange: Fake クラス自体や通常のヘルパー関数を定義しているだけ
        source = (
            "from tests.unit.fakes.fs import InMemoryFsReader\n"
            "\n"
            "class HelperClass:\n"
            "    pass\n"
            "\n"
            "def helper_function() -> None:\n"
            "    pass\n"
        )
        source_files = _make_source_files((source, "tests/unit/test_fakes/test_fs.py"))

        # Act
        violations = NoTestingTestCodeRule().check(source_files)

        # Assert: ClassDef/FunctionDef だがプレフィックスが一致しないため違反なし
        assert len(violations) == 0

    def test_check_正常系_違反のViolationフィールド値が正しいこと(self):
        source = (
            "from tests.unit.fakes.fs import InMemoryFsReader\n"
            "\n"
            "class TestInMemoryFsReader:\n"
            "    pass\n"
        )
        source_files = _make_source_files((source, "tests/unit/test_fakes/test_fs.py"))
        violations = NoTestingTestCodeRule().check(source_files)

        assert len(violations) == 1
        v = violations[0]
        assert v.rule_id == "no-testing-test-code"
        assert v.rule_name == "No Testing Test Code"
        assert "`InMemoryFsReader`" in v.message
        assert "tests/" in v.message
        assert "InMemoryFsReader" in v.suggestion
        assert v.line == 3  # class TestInMemoryFsReader は3行目
