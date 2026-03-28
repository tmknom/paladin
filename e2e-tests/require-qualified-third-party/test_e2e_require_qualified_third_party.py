"""require-qualified-third-party ルールのE2Eテスト"""

import subprocess
import sys
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestE2ERequireQualifiedThirdParty:
    """require-qualified-third-party ルールのE2Eテスト"""

    def test_check_違反検出_fromインポートが違反として報告されること(
        self,
    ):
        # Arrange
        target = FIXTURES_DIR / "violation" / "from_import.py"

        # Act
        cmd = [sys.executable, "-m", "paladin.cli", "check", str(target)]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        # Assert
        assert result.returncode == 1
        assert "require-qualified-third-party" in result.stdout

    def test_check_違反検出_エイリアスインポートが違反として報告されること(
        self,
    ):
        # Arrange
        target = FIXTURES_DIR / "violation" / "alias_import.py"

        # Act
        cmd = [sys.executable, "-m", "paladin.cli", "check", str(target)]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        # Assert
        assert result.returncode == 1
        assert "require-qualified-third-party" in result.stdout

    def test_check_準拠確認_完全修飾インポートで違反が報告されないこと(
        self,
    ):
        # Arrange
        target = FIXTURES_DIR / "compliant" / "qualified_import.py"

        # Act
        cmd = [sys.executable, "-m", "paladin.cli", "check", str(target)]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        # Assert
        assert result.returncode == 0
