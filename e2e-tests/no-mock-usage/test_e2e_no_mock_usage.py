"""no-mock-usage ルールのE2Eテスト"""

import subprocess
from collections.abc import Callable
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestE2ENoMockUsage:
    """no-mock-usage ルールのE2Eテスト"""

    def test_check_違反検出_Mockインポートが違反として報告されること(
        self,
        run_paladin_check: Callable[[Path], subprocess.CompletedProcess[str]],
    ):
        # Arrange
        target = FIXTURES_DIR / "violation" / "mock_import.py"

        # Act
        result = run_paladin_check(target)

        # Assert
        assert result.returncode == 1
        assert "no-mock-usage" in result.stdout

    def test_check_準拠確認_通常インポートのみで違反が報告されないこと(
        self,
        run_paladin_check: Callable[[Path], subprocess.CompletedProcess[str]],
    ):
        # Arrange
        target = FIXTURES_DIR / "compliant" / "no_mock.py"

        # Act
        result = run_paladin_check(target)

        # Assert
        assert result.returncode == 0
