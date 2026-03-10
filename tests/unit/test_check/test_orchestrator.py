from pathlib import Path

from paladin.check.collector import FileCollector
from paladin.check.context import CheckContext
from paladin.check.orchestrator import CheckOrchestrator
from paladin.check.parser import AstParser
from paladin.check.rule.require_all_export import RequireAllExportRule
from paladin.check.rule.runner import RuleRunner
from paladin.check.types import CheckResult, Violations
from tests.unit.test_check.fakes import InMemoryFsReader


class TestCheckOrchestrator:
    """CheckOrchestratorクラスのテスト"""

    def test_orchestrate_正常系_列挙とAST生成の結果をCheckResultとして返すこと(
        self, tmp_path: Path
    ):
        # Arrange
        py_file = tmp_path / "main.py"
        py_file.write_text("x = 1\n")
        reader = InMemoryFsReader(contents={str(py_file.resolve()): "x = 1\n"})
        parser = AstParser(reader=reader)
        runner = RuleRunner(rules=(RequireAllExportRule(),))
        orchestrator = CheckOrchestrator(collector=FileCollector(), parser=parser, runner=runner)
        context = CheckContext(targets=(tmp_path,))

        # Act
        result = orchestrator.orchestrate(context)

        # Assert
        assert isinstance(result, CheckResult)
        assert len(result.target_files) == 1
        assert py_file.resolve() in list(result.target_files)
        assert len(result.parsed_files) == 1

    def test_orchestrate_正常系_ルール適用結果をCheckResultに含めること(self, tmp_path: Path):
        # Arrange
        init_file = tmp_path / "__init__.py"
        init_file.write_text("from foo import bar\n")
        reader = InMemoryFsReader(contents={str(init_file.resolve()): "from foo import bar\n"})
        parser = AstParser(reader=reader)
        runner = RuleRunner(rules=(RequireAllExportRule(),))
        orchestrator = CheckOrchestrator(collector=FileCollector(), parser=parser, runner=runner)
        context = CheckContext(targets=(tmp_path,))

        # Act
        result = orchestrator.orchestrate(context)

        # Assert
        assert isinstance(result.violations, Violations)
        assert len(result.violations) == 1
