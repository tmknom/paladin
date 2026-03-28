"""no-testing-test-code ルールのE2Eテスト"""

import subprocess
import sys
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestE2ENoTestingTestCode:
    """no-testing-test-code ルールのE2Eテスト"""

    def test_check_違反検出_Fakeクラスに対するテストが違反として報告されること(
        self,
    ):
        # Arrange
        target = FIXTURES_DIR / "violation" / "tests"

        # Act
        cmd = [sys.executable, "-m", "paladin.cli", "check", str(target)]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        # Assert
        assert result.returncode == 1
        assert "no-testing-test-code" in result.stdout

    def test_check_準拠確認_Fakeをセットアップに使うだけでは違反が報告されないこと(
        self,
    ):
        # Arrange
        target = FIXTURES_DIR / "compliant" / "tests"

        # Act
        cmd = [sys.executable, "-m", "paladin.cli", "check", str(target)]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        # Assert
        assert result.returncode == 0
