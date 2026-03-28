"""no-relative-import ルールのE2Eテスト"""

import subprocess
import sys
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestE2ENoRelativeImport:
    """no-relative-import ルールのE2Eテスト"""

    def test_check_違反検出_相対インポートが違反として報告されること(
        self,
    ):
        # Arrange
        target = FIXTURES_DIR / "violation" / "relative_import.py"

        # Act
        cmd = [sys.executable, "-m", "paladin.cli", "check", str(target)]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        # Assert
        assert result.returncode == 1
        assert "no-relative-import" in result.stdout

    def test_check_準拠確認_絶対インポートのみで違反が報告されないこと(
        self,
    ):
        # Arrange
        target = FIXTURES_DIR / "compliant" / "absolute_import.py"

        # Act
        cmd = [sys.executable, "-m", "paladin.cli", "check", str(target)]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        # Assert
        assert result.returncode == 0
