from pathlib import Path

from paladin.check.collector import FileCollector, PathExcluder
from paladin.check.context import CheckContext
from paladin.check.formatter import CheckFormatterFactory
from paladin.check.ignore import IgnoreProcessor
from paladin.check.orchestrator import CheckOrchestrator
from paladin.check.override import OverrideResolver
from paladin.check.parser import AstParser
from paladin.check.result import CheckReport
from paladin.check.rule_filter import RuleFilter
from paladin.rule import OverrideEntry, RuleSet, Violation
from paladin.rule.unused_ignore import UnusedIgnoreRule
from tests.fake import FakeRule, InMemoryFsReader


class TestCheckOrchestrator:
    """CheckOrchestratorクラスのテスト"""

    def test_orchestrate_正常系_列挙とAST生成の結果をCheckReportとして返すこと(
        self, tmp_path: Path
    ):
        # Arrange
        py_file = tmp_path / "main.py"
        py_file.write_text("x = 1\n")
        reader = InMemoryFsReader(contents={str(py_file.resolve()): "x = 1\n"})
        parser = AstParser(reader=reader)
        rule_set = RuleSet(rules=(FakeRule(violations=()),))
        orchestrator = CheckOrchestrator(
            collector=FileCollector(),
            parser=parser,
            rule_set=rule_set,
            formatter=CheckFormatterFactory(),
            ignore_processor=IgnoreProcessor(),
            rule_filter=RuleFilter(),
            path_excluder=PathExcluder(),
            override_resolver=OverrideResolver(),
        )
        context = CheckContext(targets=(tmp_path,))

        # Act
        result = orchestrator.orchestrate(context)

        # Assert
        assert isinstance(result, CheckReport)
        assert result.exit_code == 0

    def test_orchestrate_正常系_ルール適用結果をCheckReportに含めること(self, tmp_path: Path):
        # Arrange
        init_file = tmp_path / "__init__.py"
        init_file.write_text("from foo import bar\n")
        reader = InMemoryFsReader(contents={str(init_file.resolve()): "from foo import bar\n"})
        parser = AstParser(reader=reader)
        violation = Violation(
            file=init_file.resolve(),
            line=1,
            column=0,
            rule_id="fake-rule",
            rule_name="Fake Rule",
            message="violation",
            reason="reason",
            suggestion="suggestion",
        )
        rule_set = RuleSet(rules=(FakeRule(violations=(violation,)),))
        orchestrator = CheckOrchestrator(
            collector=FileCollector(),
            parser=parser,
            rule_set=rule_set,
            formatter=CheckFormatterFactory(),
            ignore_processor=IgnoreProcessor(),
            rule_filter=RuleFilter(),
            path_excluder=PathExcluder(),
            override_resolver=OverrideResolver(),
        )
        context = CheckContext(targets=(tmp_path,))

        # Act
        result = orchestrator.orchestrate(context)

        # Assert
        assert isinstance(result, CheckReport)
        assert result.exit_code == 1

    def test_orchestrate_正常系_rulesセクションでfalseに設定されたルールの違反が出力されないこと(
        self, tmp_path: Path
    ):
        # Arrange
        py_file = tmp_path / "example.py"
        py_file.write_text("x = 1\n")
        reader = InMemoryFsReader(contents={str(py_file.resolve()): "x = 1\n"})
        parser = AstParser(reader=reader)
        violation = Violation(
            file=py_file.resolve(),
            line=1,
            column=0,
            rule_id="fake-rule",
            rule_name="Fake Rule",
            message="violation",
            reason="reason",
            suggestion="suggestion",
        )
        rule = FakeRule(rule_id="fake-rule", violations=(violation,))
        rule_set = RuleSet(rules=(rule,))
        orchestrator = CheckOrchestrator(
            collector=FileCollector(),
            parser=parser,
            rule_set=rule_set,
            formatter=CheckFormatterFactory(),
            ignore_processor=IgnoreProcessor(),
            rule_filter=RuleFilter(),
            path_excluder=PathExcluder(),
            override_resolver=OverrideResolver(),
        )
        context = CheckContext(targets=(tmp_path,), rules={"fake-rule": False})

        # Act
        result = orchestrator.orchestrate(context)

        # Assert: ルール自体がスキップされるため違反なし
        assert isinstance(result, CheckReport)
        assert result.exit_code == 0

    def test_orchestrate_正常系_存在しないルールIDを指定しても処理が継続すること(
        self, tmp_path: Path
    ):
        # Arrange
        py_file = tmp_path / "main.py"
        py_file.write_text("x = 1\n")
        reader = InMemoryFsReader(contents={str(py_file.resolve()): "x = 1\n"})
        parser = AstParser(reader=reader)
        rule_set = RuleSet(rules=(FakeRule(violations=()),))
        orchestrator = CheckOrchestrator(
            collector=FileCollector(),
            parser=parser,
            rule_set=rule_set,
            formatter=CheckFormatterFactory(),
            ignore_processor=IgnoreProcessor(),
            rule_filter=RuleFilter(),
            path_excluder=PathExcluder(),
            override_resolver=OverrideResolver(),
        )
        context = CheckContext(targets=(tmp_path,), rules={"unknown-rule": False})

        # Act: 警告が出るが処理は完了する
        result = orchestrator.orchestrate(context)

        # Assert: 処理が正常に完了する
        assert isinstance(result, CheckReport)

    def test_orchestrate_正常系_excludeパターンでファイルが除外されること(self, tmp_path: Path):
        # Arrange: 違反ファイルを exclude パターンで除外する
        py_file = tmp_path / "example.py"
        py_file.write_text("x = 1\n")
        reader = InMemoryFsReader(contents={str(py_file.resolve()): "x = 1\n"})
        parser = AstParser(reader=reader)
        violation = Violation(
            file=py_file.resolve(),
            line=1,
            column=0,
            rule_id="fake-rule",
            rule_name="Fake Rule",
            message="violation",
            reason="reason",
            suggestion="suggestion",
        )
        rule = FakeRule(rule_id="fake-rule", violations=(violation,))
        rule_set = RuleSet(rules=(rule,))
        orchestrator = CheckOrchestrator(
            collector=FileCollector(),
            parser=parser,
            rule_set=rule_set,
            formatter=CheckFormatterFactory(),
            ignore_processor=IgnoreProcessor(),
            rule_filter=RuleFilter(),
            path_excluder=PathExcluder(),
            override_resolver=OverrideResolver(),
        )
        context = CheckContext(targets=(tmp_path,), exclude=(py_file.name,))

        # Act
        result = orchestrator.orchestrate(context)

        # Assert: exclude パターンで example.py が除外されるため違反なし
        assert isinstance(result, CheckReport)
        assert result.exit_code == 0

    def test_orchestrate_正常系_overridesで特定ディレクトリのルールを無効化できること(
        self, tmp_path: Path
    ):
        # Arrange: tests/ 配下のファイルで fake-rule を無効化する
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        test_file = tests_dir / "test_foo.py"
        test_file.write_text("x = 1\n")
        src_file = tmp_path / "main.py"
        src_file.write_text("x = 1\n")

        reader = InMemoryFsReader(
            contents={
                str(test_file.resolve()): "x = 1\n",
                str(src_file.resolve()): "x = 1\n",
            }
        )
        parser = AstParser(reader=reader)
        # tests/ の違反と src/ の違反を両方返すルール
        violation_tests = Violation(
            file=test_file.resolve(),
            line=1,
            column=0,
            rule_id="fake-rule",
            rule_name="Fake Rule",
            message="violation",
            reason="reason",
            suggestion="suggestion",
        )
        violation_src = Violation(
            file=src_file.resolve(),
            line=1,
            column=0,
            rule_id="fake-rule",
            rule_name="Fake Rule",
            message="violation",
            reason="reason",
            suggestion="suggestion",
        )
        rule = FakeRule(rule_id="fake-rule", violations=(violation_tests, violation_src))
        rule_set = RuleSet(rules=(rule,))
        orchestrator = CheckOrchestrator(
            collector=FileCollector(),
            parser=parser,
            rule_set=rule_set,
            formatter=CheckFormatterFactory(),
            ignore_processor=IgnoreProcessor(),
            rule_filter=RuleFilter(),
            path_excluder=PathExcluder(),
            override_resolver=OverrideResolver(),
        )
        override = OverrideEntry(files=("tests/**",), rules={"fake-rule": False})
        context = CheckContext(
            targets=(tmp_path,),
            rules={"fake-rule": True},
            overrides=(override,),
        )

        # Act
        result = orchestrator.orchestrate(context)

        # Assert: tests/ 配下の違反のみ除外され、src/ の違反は残る
        assert isinstance(result, CheckReport)
        assert result.exit_code == 1  # src/ の違反あり


class TestCheckOrchestratorUnusedIgnore:
    """CheckOrchestrator の unused-ignore 検出テスト"""

    def test_orchestrate_正常系_未使用Ignoreが違反として報告されること(self, tmp_path: Path):
        # Arrange: ignore コメントがあるが FakeRule は違反を返さない
        py_file = tmp_path / "example.py"
        source = "# paladin: ignore[fake-rule]\nx = 1\n"
        py_file.write_text(source)
        reader = InMemoryFsReader(contents={str(py_file.resolve()): source})
        parser = AstParser(reader=reader)
        rule_set = RuleSet(
            rules=(FakeRule(rule_id="fake-rule", violations=()),),
            unused_ignore_rule=UnusedIgnoreRule(),
        )
        orchestrator = CheckOrchestrator(
            collector=FileCollector(),
            parser=parser,
            rule_set=rule_set,
            formatter=CheckFormatterFactory(),
            ignore_processor=IgnoreProcessor(),
            rule_filter=RuleFilter(),
            path_excluder=PathExcluder(),
            override_resolver=OverrideResolver(),
        )
        context = CheckContext(targets=(tmp_path,))

        # Act
        result = orchestrator.orchestrate(context)

        # Assert: 未使用 Ignore として違反が報告される
        assert isinstance(result, CheckReport)
        assert result.exit_code == 1
        assert "unused-ignore" in result.text

    def test_orchestrate_正常系_使用中のIgnoreは違反として報告されないこと(self, tmp_path: Path):
        # Arrange: FakeRule が行3（ignore 対象行）で違反を返す
        py_file = tmp_path / "example.py"
        source = "x = 1\n# paladin: ignore[fake-rule]\ny = 2\n"
        py_file.write_text(source)
        reader = InMemoryFsReader(contents={str(py_file.resolve()): source})
        parser = AstParser(reader=reader)
        violation = Violation(
            file=py_file.resolve(),
            line=3,
            column=0,
            rule_id="fake-rule",
            rule_name="Fake Rule",
            message="violation",
            reason="reason",
            suggestion="suggestion",
        )
        rule_set = RuleSet(
            rules=(FakeRule(rule_id="fake-rule", violations=(violation,)),),
            unused_ignore_rule=UnusedIgnoreRule(),
        )
        orchestrator = CheckOrchestrator(
            collector=FileCollector(),
            parser=parser,
            rule_set=rule_set,
            formatter=CheckFormatterFactory(),
            ignore_processor=IgnoreProcessor(),
            rule_filter=RuleFilter(),
            path_excluder=PathExcluder(),
            override_resolver=OverrideResolver(),
        )
        context = CheckContext(targets=(tmp_path,))

        # Act
        result = orchestrator.orchestrate(context)

        # Assert: ignore が適用されているため違反なし
        assert isinstance(result, CheckReport)
        assert result.exit_code == 0

    def test_orchestrate_正常系_unused_ignore自身の違反もIgnoreコメントで抑制可能であること(
        self, tmp_path: Path
    ):
        # Arrange: ignore-file[unused-ignore] でファイル全体の unused-ignore を抑制する
        # ファイルに fake-rule の unused ignore があるが、unused-ignore ルール自体を
        # ignore-file で無効化することで、unused-ignore の違反が報告されないようにする
        py_file = tmp_path / "example.py"
        source = "# paladin: ignore-file[unused-ignore]\n# paladin: ignore[fake-rule]\nx = 1\n"
        py_file.write_text(source)
        reader = InMemoryFsReader(contents={str(py_file.resolve()): source})
        parser = AstParser(reader=reader)
        rule_set = RuleSet(
            rules=(FakeRule(rule_id="fake-rule", violations=()),),
            unused_ignore_rule=UnusedIgnoreRule(),
        )
        orchestrator = CheckOrchestrator(
            collector=FileCollector(),
            parser=parser,
            rule_set=rule_set,
            formatter=CheckFormatterFactory(),
            ignore_processor=IgnoreProcessor(),
            rule_filter=RuleFilter(),
            path_excluder=PathExcluder(),
            override_resolver=OverrideResolver(),
        )
        context = CheckContext(targets=(tmp_path,))

        # Act
        result = orchestrator.orchestrate(context)

        # Assert: ignore-file[unused-ignore] で unused-ignore の違反が抑制される
        assert isinstance(result, CheckReport)
        assert result.exit_code == 0


class TestCheckOrchestratorSelectRules:
    """select_rules 機能に関する CheckOrchestrator のテスト"""

    def test_orchestrate_正常系_select_rulesで指定ルールのみ実行されること(self, tmp_path: Path):
        # Arrange: rule-a に違反あり、rule-b に違反なし。select_rules で rule-b のみ指定
        py_file = tmp_path / "example.py"
        py_file.write_text("x = 1\n")
        reader = InMemoryFsReader(contents={str(py_file.resolve()): "x = 1\n"})
        parser = AstParser(reader=reader)
        violation = Violation(
            file=py_file.resolve(),
            line=1,
            column=0,
            rule_id="rule-a",
            rule_name="Rule A",
            message="violation",
            reason="reason",
            suggestion="suggestion",
        )
        rule_a = FakeRule(rule_id="rule-a", violations=(violation,))
        rule_b = FakeRule(rule_id="rule-b", violations=())
        rule_set = RuleSet(rules=(rule_a, rule_b))
        orchestrator = CheckOrchestrator(
            collector=FileCollector(),
            parser=parser,
            rule_set=rule_set,
            formatter=CheckFormatterFactory(),
            ignore_processor=IgnoreProcessor(),
            rule_filter=RuleFilter(),
            path_excluder=PathExcluder(),
            override_resolver=OverrideResolver(),
        )
        context = CheckContext(targets=(tmp_path,), select_rules=frozenset({"rule-b"}))

        # Act
        result = orchestrator.orchestrate(context)

        # Assert: rule-a がスキップされるため違反なし
        assert isinstance(result, CheckReport)
        assert result.exit_code == 0
