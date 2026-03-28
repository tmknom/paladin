"""require-all-export ルールのE2Eテスト"""

import subprocess
import sys
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestE2ERequireAllExport:
    """require-all-export ルールのE2Eテスト"""

    def test_check_違反検出_init_pyにall未定義で違反が報告されること(
        self,
    ):
        # Arrange
        target = FIXTURES_DIR / "violation" / "__init__.py"

        # Act
        cmd = [sys.executable, "-m", "paladin.cli", "check", str(target)]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        # Assert
        assert result.returncode == 1
        assert "require-all-export" in result.stdout

    def test_check_準拠確認_init_pyにallが定義されていて違反が報告されないこと(
        self,
    ):
        # Arrange
        target = FIXTURES_DIR / "compliant" / "__init__.py"

        # Act
        cmd = [sys.executable, "-m", "paladin.cli", "check", str(target)]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        # Assert
        assert result.returncode == 0
