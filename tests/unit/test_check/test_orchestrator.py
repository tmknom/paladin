import json
from pathlib import Path

from paladin.check.collector import FileCollector
from paladin.check.context import CheckContext
from paladin.check.formatter import CheckFormatterFactory
from paladin.check.orchestrator import CheckOrchestrator
from paladin.check.parser import AstParser
from paladin.check.result import CheckReport
from paladin.check.rule.require_all_export import RequireAllExportRule
from paladin.check.rule.runner import RuleRunner
from paladin.check.types import OutputFormat
from tests.unit.test_check.fakes import InMemoryFsReader


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
        )
        context = CheckContext(targets=(tmp_path,), format=OutputFormat.TEXT)

        # Act
        report = orchestrator.orchestrate(context)

        # Assert
        assert isinstance(report, CheckReport)
        assert "status: ok" in report.text
