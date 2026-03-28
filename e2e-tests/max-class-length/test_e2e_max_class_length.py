"""max-class-length ルールのE2Eテスト"""

import subprocess
import sys
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestE2EMaxClassLength:
    """max-class-length ルールのE2Eテスト"""

    def test_check_違反検出_上限超過のクラスが違反として報告されること(
        self,
    ):
        # Arrange
        target = FIXTURES_DIR / "violation"

        # Act
        cmd = [sys.executable, "-m", "paladin.cli", "check", str(target)]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        # Assert
        assert result.returncode == 1
        assert "max-class-length" in result.stdout

    def test_check_準拠確認_上限以下のクラスで違反が報告されないこと(
        self,
    ):
        # Arrange
        target = FIXTURES_DIR / "compliant"

        # Act
        cmd = [sys.executable, "-m", "paladin.cli", "check", str(target)]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        # Assert
        assert result.returncode == 0
