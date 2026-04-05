"""require-empty-test-init ルールのE2Eテスト"""

import subprocess
import sys
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestE2ERequireEmptyTestInit:
    """require-empty-test-init ルールのE2Eテスト"""

    def test_check_違反検出_テストinit_pyにコードがある場合に違反として報告されること(self):
        # Arrange
        target = FIXTURES_DIR / "violation" / "tests" / "__init__.py"

        # Act
        cmd = [sys.executable, "-m", "paladin.cli", "check", str(target)]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        # Assert
        assert result.returncode == 1
        assert "require-empty-test-init" in result.stdout

    def test_check_準拠確認_空のテストinit_pyで違反が報告されないこと(self):
        # Arrange
        target = FIXTURES_DIR / "compliant" / "tests" / "__init__.py"

        # Act
        cmd = [sys.executable, "-m", "paladin.cli", "check", str(target)]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        # Assert
        assert result.returncode == 0
