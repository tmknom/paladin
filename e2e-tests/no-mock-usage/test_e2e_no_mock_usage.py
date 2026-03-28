"""no-mock-usage ルールのE2Eテスト"""

import subprocess
import sys
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestE2ENoMockUsage:
    """no-mock-usage ルールのE2Eテスト"""

    def test_check_違反検出_Mockインポートが違反として報告されること(
        self,
    ):
        # Arrange
        target = FIXTURES_DIR / "violation" / "mock_import.py"

        # Act
        cmd = [sys.executable, "-m", "paladin.cli", "check", str(target)]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        # Assert
        assert result.returncode == 1
        assert "no-mock-usage" in result.stdout

    def test_check_準拠確認_通常インポートのみで違反が報告されないこと(
        self,
    ):
        # Arrange
        target = FIXTURES_DIR / "compliant" / "no_mock.py"

        # Act
        cmd = [sys.executable, "-m", "paladin.cli", "check", str(target)]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        # Assert
        assert result.returncode == 0
