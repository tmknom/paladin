import json
from pathlib import Path

from paladin.check.collector import FileCollector
from paladin.check.context import CheckContext
from paladin.check.formatter import CheckFormatterFactory
from paladin.check.ignore import ViolationFilter
from paladin.check.orchestrator import CheckOrchestrator
from paladin.check.parser import AstParser
from paladin.check.result import CheckReport
from paladin.check.types import OutputFormat
from paladin.lint import RequireAllExportRule, RuleRunner
from paladin.lint.types import Violation
from tests.unit.test_check.fakes import FakeRule, InMemoryFsReader


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
        runner = RuleRunner(rules=(RequireAllExportRule(),))
        orchestrator = CheckOrchestrator(
            collector=FileCollector(),
            parser=parser,
            runner=runner,
            formatter=CheckFormatterFactory(),
            violation_filter=ViolationFilter(),
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
        runner = RuleRunner(rules=(RequireAllExportRule(),))
        orchestrator = CheckOrchestrator(
            collector=FileCollector(),
            parser=parser,
            runner=runner,
            formatter=CheckFormatterFactory(),
            violation_filter=ViolationFilter(),
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
        runner = RuleRunner(rules=(RequireAllExportRule(),))
        orchestrator = CheckOrchestrator(
            collector=FileCollector(),
            parser=parser,
            runner=runner,
            formatter=CheckFormatterFactory(),
            violation_filter=ViolationFilter(),
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
        runner = RuleRunner(rules=(RequireAllExportRule(),))
        orchestrator = CheckOrchestrator(
            collector=FileCollector(),
            parser=parser,
            runner=runner,
            formatter=CheckFormatterFactory(),
            violation_filter=ViolationFilter(),
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
        runner = RuleRunner(rules=(RequireAllExportRule(),))
        orchestrator = CheckOrchestrator(
            collector=FileCollector(),
            parser=parser,
            runner=runner,
            formatter=CheckFormatterFactory(),
            violation_filter=ViolationFilter(),
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
        init_file.write_text("# paladin: ignore-file[require-all-export]\nfrom foo import bar\n")
        reader = InMemoryFsReader(
            contents={
                str(init_file.resolve()): (
                    "# paladin: ignore-file[require-all-export]\nfrom foo import bar\n"
                )
            }
        )
        parser = AstParser(reader=reader)
        runner = RuleRunner(rules=(RequireAllExportRule(),))
        orchestrator = CheckOrchestrator(
            collector=FileCollector(),
            parser=parser,
            runner=runner,
            formatter=CheckFormatterFactory(),
            violation_filter=ViolationFilter(),
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
        runner = RuleRunner(rules=(rule,))
        orchestrator = CheckOrchestrator(
            collector=FileCollector(),
            parser=parser,
            runner=runner,
            formatter=CheckFormatterFactory(),
            violation_filter=ViolationFilter(),
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
        runner = RuleRunner(rules=(rule,))
        orchestrator = CheckOrchestrator(
            collector=FileCollector(),
            parser=parser,
            runner=runner,
            formatter=CheckFormatterFactory(),
            violation_filter=ViolationFilter(),
        )
        context = CheckContext(targets=(tmp_path,))

        # Act
        result = orchestrator.orchestrate(context)

        # Assert: # paladin: ignore[fake-rule] の直後行 (line=2) の該当ルール違反が除外される
        assert isinstance(result, CheckReport)
        assert result.exit_code == 0
