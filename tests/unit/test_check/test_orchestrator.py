import json
from pathlib import Path

from paladin.check.collector import FileCollector, PathExcluder
from paladin.check.context import CheckContext
from paladin.check.formatter import CheckFormatterFactory
from paladin.check.ignore import ViolationFilter
from paladin.check.orchestrator import CheckOrchestrator
from paladin.check.override import OverrideResolver
from paladin.check.parser import AstParser
from paladin.check.result import CheckReport
from paladin.check.rule_filter import RuleFilter
from paladin.foundation.output import OutputFormat
from paladin.rule import OverrideEntry, PerFileIgnoreEntry, RuleSet, Violation
from tests.unit.fakes import FakeRule, InMemoryFsReader


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
            violation_filter=ViolationFilter(),
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
            violation_filter=ViolationFilter(),
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

    def test_orchestrate_正常系_JSON形式でCheckReportを返すこと(self, tmp_path: Path):
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
            violation_filter=ViolationFilter(),
            rule_filter=RuleFilter(),
            path_excluder=PathExcluder(),
            override_resolver=OverrideResolver(),
        )
        context = CheckContext(targets=(tmp_path,), format=OutputFormat.JSON)

        # Act
        report = orchestrator.orchestrate(context)

        # Assert
        assert isinstance(report, CheckReport)
        parsed = json.loads(report.text)
        assert "status" in parsed

    def test_orchestrate_正常系_TEXT形式でCheckReportを返すこと(self, tmp_path: Path):
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
            violation_filter=ViolationFilter(),
            rule_filter=RuleFilter(),
            path_excluder=PathExcluder(),
            override_resolver=OverrideResolver(),
        )
        context = CheckContext(targets=(tmp_path,), format=OutputFormat.TEXT)

        # Act
        report = orchestrator.orchestrate(context)

        # Assert
        assert isinstance(report, CheckReport)
        assert "status: ok" in report.text

    def test_orchestrate_正常系_ignore_fileディレクティブで違反が除外されること(
        self, tmp_path: Path
    ):
        # Arrange
        init_file = tmp_path / "__init__.py"
        init_file.write_text("# paladin: ignore-file\nfrom foo import bar\n")
        reader = InMemoryFsReader(
            contents={str(init_file.resolve()): "# paladin: ignore-file\nfrom foo import bar\n"}
        )
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
            violation_filter=ViolationFilter(),
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

    def test_orchestrate_正常系_特定ルールignoreで該当ルールのみ除外されること(
        self, tmp_path: Path
    ):
        # Arrange
        init_file = tmp_path / "__init__.py"
        init_file.write_text("# paladin: ignore-file[fake-rule]\nfrom foo import bar\n")
        reader = InMemoryFsReader(
            contents={
                str(init_file.resolve()): (
                    "# paladin: ignore-file[fake-rule]\nfrom foo import bar\n"
                )
            }
        )
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
            violation_filter=ViolationFilter(),
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

    def test_orchestrate_正常系_直前コメントignoreで違反が除外されること(self, tmp_path: Path):
        # Arrange: FakeRule で line=2 の違反を返すよう設定する
        py_file = tmp_path / "example.py"
        source = "# paladin: ignore\nsome_code = 1\n"
        py_file.write_text(source)
        reader = InMemoryFsReader(contents={str(py_file.resolve()): source})
        parser = AstParser(reader=reader)
        violation = Violation(
            file=py_file.resolve(),
            line=2,
            column=0,
            rule_id="fake-rule",
            rule_name="Fake Rule",
            message="violation",
            reason="reason",
            suggestion="suggestion",
        )
        rule = FakeRule(violations=(violation,))
        rule_set = RuleSet(rules=(rule,))
        orchestrator = CheckOrchestrator(
            collector=FileCollector(),
            parser=parser,
            rule_set=rule_set,
            formatter=CheckFormatterFactory(),
            violation_filter=ViolationFilter(),
            rule_filter=RuleFilter(),
            path_excluder=PathExcluder(),
            override_resolver=OverrideResolver(),
        )
        context = CheckContext(targets=(tmp_path,))

        # Act
        result = orchestrator.orchestrate(context)

        # Assert: # paladin: ignore の直後行 (line=2) の違反が除外される
        assert isinstance(result, CheckReport)
        assert result.exit_code == 0

    def test_orchestrate_正常系_特定ルール直前コメントignoreで該当ルールのみ除外されること(
        self, tmp_path: Path
    ):
        # Arrange: FakeRule で line=2 の違反を返すよう設定する
        py_file = tmp_path / "example.py"
        source = "# paladin: ignore[fake-rule]\nsome_code = 1\n"
        py_file.write_text(source)
        reader = InMemoryFsReader(contents={str(py_file.resolve()): source})
        parser = AstParser(reader=reader)
        violation = Violation(
            file=py_file.resolve(),
            line=2,
            column=0,
            rule_id="fake-rule",
            rule_name="Fake Rule",
            message="violation",
            reason="reason",
            suggestion="suggestion",
        )
        rule = FakeRule(violations=(violation,))
        rule_set = RuleSet(rules=(rule,))
        orchestrator = CheckOrchestrator(
            collector=FileCollector(),
            parser=parser,
            rule_set=rule_set,
            formatter=CheckFormatterFactory(),
            violation_filter=ViolationFilter(),
            rule_filter=RuleFilter(),
            path_excluder=PathExcluder(),
            override_resolver=OverrideResolver(),
        )
        context = CheckContext(targets=(tmp_path,))

        # Act
        result = orchestrator.orchestrate(context)

        # Assert: # paladin: ignore[fake-rule] の直後行 (line=2) の該当ルール違反が除外される
        assert isinstance(result, CheckReport)
        assert result.exit_code == 0

    def test_orchestrate_正常系_設定ファイルのper_file_ignoresで違反が除外されること(
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
        rule = FakeRule(violations=(violation,))
        rule_set = RuleSet(rules=(rule,))
        orchestrator = CheckOrchestrator(
            collector=FileCollector(),
            parser=parser,
            rule_set=rule_set,
            formatter=CheckFormatterFactory(),
            violation_filter=ViolationFilter(),
            rule_filter=RuleFilter(),
            path_excluder=PathExcluder(),
            override_resolver=OverrideResolver(),
        )
        context = CheckContext(
            targets=(tmp_path,),
            per_file_ignores=(
                PerFileIgnoreEntry(
                    pattern="example.py",
                    rule_ids=frozenset({"fake-rule"}),
                    ignore_all=False,
                ),
            ),
        )

        # Act
        result = orchestrator.orchestrate(context)

        # Assert: 設定ファイルの per-file-ignores で違反が除外される
        assert isinstance(result, CheckReport)
        assert result.exit_code == 0

    def test_orchestrate_正常系_ignore_rulesで指定ルールの違反が除外されること(
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
        rule = FakeRule(violations=(violation,))
        rule_set = RuleSet(rules=(rule,))
        orchestrator = CheckOrchestrator(
            collector=FileCollector(),
            parser=parser,
            rule_set=rule_set,
            formatter=CheckFormatterFactory(),
            violation_filter=ViolationFilter(),
            rule_filter=RuleFilter(),
            path_excluder=PathExcluder(),
            override_resolver=OverrideResolver(),
        )
        context = CheckContext(targets=(tmp_path,), ignore_rules=frozenset({"fake-rule"}))

        # Act
        result = orchestrator.orchestrate(context)

        # Assert: ignore_rules で指定したルールの違反が除外される
        assert isinstance(result, CheckReport)
        assert result.exit_code == 0

    def test_orchestrate_正常系_設定ファイルignoreとコメントignoreが同時に適用されること(
        self, tmp_path: Path
    ):
        # Arrange
        py_file1 = tmp_path / "config_ignored.py"
        py_file1.write_text("x = 1\n")
        py_file2 = tmp_path / "comment_ignored.py"
        py_file2.write_text("# paladin: ignore-file\nx = 1\n")
        reader = InMemoryFsReader(
            contents={
                str(py_file1.resolve()): "x = 1\n",
                str(py_file2.resolve()): "# paladin: ignore-file\nx = 1\n",
            }
        )
        parser = AstParser(reader=reader)
        violation1 = Violation(
            file=py_file1.resolve(),
            line=1,
            column=0,
            rule_id="fake-rule",
            rule_name="Fake Rule",
            message="violation",
            reason="reason",
            suggestion="suggestion",
        )
        violation2 = Violation(
            file=py_file2.resolve(),
            line=1,
            column=0,
            rule_id="fake-rule",
            rule_name="Fake Rule",
            message="violation",
            reason="reason",
            suggestion="suggestion",
        )
        rule = FakeRule(violations=(violation1, violation2))
        rule_set = RuleSet(rules=(rule,))
        orchestrator = CheckOrchestrator(
            collector=FileCollector(),
            parser=parser,
            rule_set=rule_set,
            formatter=CheckFormatterFactory(),
            violation_filter=ViolationFilter(),
            rule_filter=RuleFilter(),
            path_excluder=PathExcluder(),
            override_resolver=OverrideResolver(),
        )
        context = CheckContext(
            targets=(tmp_path,),
            per_file_ignores=(
                PerFileIgnoreEntry(
                    pattern="config_ignored.py",
                    rule_ids=frozenset({"fake-rule"}),
                    ignore_all=False,
                ),
            ),
        )

        # Act
        result = orchestrator.orchestrate(context)

        # Assert: 設定ファイル由来と コメント由来の両方の ignore が適用されて両違反が除外される
        assert isinstance(result, CheckReport)
        assert result.exit_code == 0

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
            violation_filter=ViolationFilter(),
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
            violation_filter=ViolationFilter(),
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
            violation_filter=ViolationFilter(),
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
            violation_filter=ViolationFilter(),
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

    def test_orchestrate_正常系_overridesで後に定義されたオーバーライドが優先されること(
        self, tmp_path: Path
    ):
        # Arrange: 同一ファイルに2つのオーバーライドがマッチする場合、後者が優先
        tests_dir = tmp_path / "tests" / "unit"
        tests_dir.mkdir(parents=True)
        test_file = tests_dir / "test_foo.py"
        test_file.write_text("x = 1\n")
        reader = InMemoryFsReader(contents={str(test_file.resolve()): "x = 1\n"})
        parser = AstParser(reader=reader)
        violation = Violation(
            file=test_file.resolve(),
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
            violation_filter=ViolationFilter(),
            rule_filter=RuleFilter(),
            path_excluder=PathExcluder(),
            override_resolver=OverrideResolver(),
        )
        # override1: tests/** で fake-rule を無効化
        # override2: tests/unit/** で fake-rule を有効化（後勝ち）
        override1 = OverrideEntry(files=("tests/**",), rules={"fake-rule": False})
        override2 = OverrideEntry(files=("tests/unit/**",), rules={"fake-rule": True})
        context = CheckContext(
            targets=(tmp_path,),
            rules={"fake-rule": True},
            overrides=(override1, override2),
        )

        # Act
        result = orchestrator.orchestrate(context)

        # Assert: override2 が後勝ちで fake-rule が有効のため、違反あり
        assert isinstance(result, CheckReport)
        assert result.exit_code == 1


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
            violation_filter=ViolationFilter(),
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

    def test_orchestrate_正常系_select_rulesとrules_falseの組み合わせでAND条件が適用されること(
        self, tmp_path: Path
    ):
        # Arrange: rule-a に違反あり。select_rules={"rule-a"} かつ rules={"rule-a": False}
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
        rule_set = RuleSet(rules=(rule_a,))
        orchestrator = CheckOrchestrator(
            collector=FileCollector(),
            parser=parser,
            rule_set=rule_set,
            formatter=CheckFormatterFactory(),
            violation_filter=ViolationFilter(),
            rule_filter=RuleFilter(),
            path_excluder=PathExcluder(),
            override_resolver=OverrideResolver(),
        )
        context = CheckContext(
            targets=(tmp_path,),
            select_rules=frozenset({"rule-a"}),
            rules={"rule-a": False},
        )

        # Act
        result = orchestrator.orchestrate(context)

        # Assert: AND 条件で rule-a が rules:false により無効 → 違反なし
        assert isinstance(result, CheckReport)
        assert result.exit_code == 0

    def test_orchestrate_正常系_select_rulesとoverridesの組み合わせが正しく動作すること(
        self, tmp_path: Path
    ):
        # Arrange: rule-a に違反あり。select_rules={"rule-b"} → rule-a がスキップされる
        # overrides は _resolve_per_file_disabled でも select_rules が考慮されることを検証
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        test_file = tests_dir / "test_foo.py"
        test_file.write_text("x = 1\n")
        reader = InMemoryFsReader(contents={str(test_file.resolve()): "x = 1\n"})
        parser = AstParser(reader=reader)
        violation = Violation(
            file=test_file.resolve(),
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
            violation_filter=ViolationFilter(),
            rule_filter=RuleFilter(),
            path_excluder=PathExcluder(),
            override_resolver=OverrideResolver(),
        )
        override = OverrideEntry(files=("tests/**",), rules={"rule-a": True})
        context = CheckContext(
            targets=(tmp_path,),
            select_rules=frozenset({"rule-b"}),
            overrides=(override,),
        )

        # Act
        result = orchestrator.orchestrate(context)

        # Assert: select_rules により rule-a がスキップ → 違反なし
        assert isinstance(result, CheckReport)
        assert result.exit_code == 0
