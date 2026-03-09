from pathlib import Path

from paladin.check.collector import FileCollector
from paladin.check.context import CheckContext
from paladin.check.orchestrator import CheckOrchestrator
from paladin.check.types import CheckResult


class TestCheckOrchestrator:
    """CheckOrchestratorクラスのテスト"""

    def test_orchestrate_正常系_FileCollectorで列挙した結果をCheckResultとして返すこと(
        self, tmp_path: Path
    ):
        # Arrange
        py_file = tmp_path / "main.py"
        py_file.write_text("")
        orchestrator = CheckOrchestrator(collector=FileCollector())
        context = CheckContext(targets=(tmp_path,))

        # Act
        result = orchestrator.orchestrate(context)

        # Assert
        assert isinstance(result, CheckResult)
        assert len(result.target_files) == 1
        assert py_file.resolve() in list(result.target_files)
