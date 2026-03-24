"""NoTestingTestCodeRule のテスト"""

import pytest

from paladin.rule.no_testing_test_code import NoTestingTestCodeRule
from paladin.rule.types import RuleMeta, SourceFiles
from tests.unit.test_rule.helpers import make_source_files


class TestNoTestingTestCodeRuleMeta:
    def test_meta_正常系_ルールメタ情報を返すこと(self):
        # Arrange
        rule = NoTestingTestCodeRule()

        # Act
        meta = rule.meta

        # Assert
        assert isinstance(meta, RuleMeta)
        assert meta.rule_id == "no-testing-test-code"
        assert meta.rule_name == "No Testing Test Code"


class TestNoTestingTestCodeRuleCheck:
    def test_check_正常系_違反のViolationフィールド値が正しいこと(self):
        # Arrange
        source = (
            "from tests.unit.fakes.fs import InMemoryFsReader\n"
            "\n"
            "class TestInMemoryFsReader:\n"
            "    pass\n"
        )
        source_files = make_source_files((source, "tests/unit/test_fakes/test_fs.py"))
        rule = NoTestingTestCodeRule()

        # Act
        violations = rule.check(source_files)

        # Assert
        assert len(violations) == 1
        v = violations[0]
        assert v.rule_id == "no-testing-test-code"
        assert v.rule_name == "No Testing Test Code"
        assert "`InMemoryFsReader`" in v.message
        assert "tests/" in v.message
        assert "InMemoryFsReader" in v.suggestion
        assert v.line == 3  # class TestInMemoryFsReader は3行目

    def test_check_正常系_空のSourceFilesで違反なし(self):
        # Arrange
        source_files = SourceFiles(files=())
        rule = NoTestingTestCodeRule()

        # Act
        violations = rule.check(source_files)

        # Assert
        assert len(violations) == 0

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
        source_files = make_source_files((source, "tests/unit/test_fakes/test_all.py"))

        # Act
        violations = NoTestingTestCodeRule().check(source_files)

        # Assert
        assert len(violations) == 2

    def test_check_違反検出_エイリアスインポートでも元の名前が診断メッセージに表示されること(self):
        # Arrange: alias で別名インポートしている場合
        source = (
            "from tests.unit.fakes.fs import InMemoryFsReader as FakeReader\n"
            "\n"
            "class TestFakeReader:\n"
            "    pass\n"
        )
        source_files = make_source_files((source, "tests/unit/test_fakes/test_fs.py"))

        # Act
        violations = NoTestingTestCodeRule().check(source_files)

        # Assert: bound_name=FakeReader が TestFakeReader と一致、message に InMemoryFsReader
        assert len(violations) == 1
        assert "InMemoryFsReader" in violations[0].message

    @pytest.mark.parametrize(
        ("source", "filename"),
        [
            pytest.param(
                "class TestFoo:\n    def test_something(self) -> None:\n        pass\n",
                "tests/unit/test_foo.py",
                id="testsインポートなし",
            ),
            pytest.param(
                "from tests.unit.fakes.fs import InMemoryFsReader\n"
                "\n"
                "class TestCheckOrchestrator:\n"
                "    def test_orchestrate(self) -> None:\n"
                "        reader = InMemoryFsReader()\n",
                "tests/unit/test_check/test_orchestrator.py",
                id="クラス名不一致",
            ),
            pytest.param(
                "from paladin.check.orchestrator import CheckOrchestrator\n"
                "\n"
                "class TestCheckOrchestrator:\n"
                "    def test_orchestrate(self) -> None:\n"
                "        pass\n",
                "tests/unit/test_check/test_orchestrator.py",
                id="srcからのインポート",
            ),
            pytest.param(
                "from tests.unit.fakes.fs import InMemoryFsReader\n"
                "\n"
                "class TestInMemoryFsReader:\n"
                "    pass\n",
                "src/paladin/some_module.py",
                id="テストファイルでない",
            ),
            pytest.param(
                "from tests.unit.fakes.fs import InMemoryFsReader\n"
                "\n"
                "class TestInMemoryFsReader:\n"
                "    pass\n",
                "tests/unit/conftest.py",
                id="conftest",
            ),
            pytest.param(
                "from tests.unit.fakes.fs import InMemoryFsReader\n"
                "\n"
                "def test_orchestrate() -> None:\n"
                "    reader = InMemoryFsReader()\n",
                "tests/unit/test_check/test_orchestrator.py",
                id="関数名不一致",
            ),
            pytest.param(
                "from tests.unit.fakes.fs import InMemoryFsReader\n"
                "\n"
                "class HelperClass:\n"
                "    pass\n"
                "\n"
                "def helper_function() -> None:\n"
                "    pass\n",
                "tests/unit/test_fakes/test_fs.py",
                id="プレフィックス不一致",
            ),
        ],
    )
    def test_check_違反なしのケースで空を返すこと(self, source: str, filename: str) -> None:
        # Arrange
        source_files = make_source_files((source, filename))
        rule = NoTestingTestCodeRule()

        # Act
        violations = rule.check(source_files)

        # Assert
        assert len(violations) == 0

    @pytest.mark.parametrize(
        ("source", "filename"),
        [
            pytest.param(
                "from tests.unit.fakes.fs import InMemoryFsReader\n"
                "\n"
                "class TestInMemoryFsReader:\n"
                "    def test_read(self) -> None:\n"
                "        pass\n",
                "tests/unit/test_fakes/test_fs.py",
                id="クラス名一致",
            ),
            pytest.param(
                "from tests.unit.fakes.fs import InMemoryFsReader\n"
                "\n"
                "def test_in_memory_fs_reader_returns_content() -> None:\n"
                "    pass\n",
                "tests/unit/test_fakes/test_fs.py",
                id="関数名一致_サフィックスあり",
            ),
            pytest.param(
                "from tests.unit.fakes.fs import InMemoryFsReader\n"
                "\n"
                "def test_in_memory_fs_reader() -> None:\n"
                "    pass\n",
                "tests/unit/test_fakes/test_fs.py",
                id="関数名一致_完全一致",
            ),
        ],
    )
    def test_check_違反ありのケースで1件返すこと(self, source: str, filename: str) -> None:
        # Arrange
        source_files = make_source_files((source, filename))
        rule = NoTestingTestCodeRule()

        # Act
        violations = rule.check(source_files)

        # Assert
        assert len(violations) == 1
