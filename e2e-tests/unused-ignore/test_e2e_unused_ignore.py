"""unused-ignore ルールのE2Eテスト"""

import subprocess
import sys
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestE2EUnusedIgnore:
    """unused-ignore ルールのE2Eテスト"""

    def test_check_違反検出_未使用インラインIgnoreが報告されること(self):
        # Arrange
        target = FIXTURES_DIR / "violation"

        # Act
        cmd = [sys.executable, "-m", "paladin.cli", "check", str(target)]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        # Assert
        assert result.returncode == 1
        assert "unused-ignore" in result.stdout

    def test_check_違反検出_未使用ファイル単位Ignoreが報告されること(self):
        # Arrange
        target = FIXTURES_DIR / "violation_file"

        # Act
        cmd = [sys.executable, "-m", "paladin.cli", "check", str(target)]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        # Assert
        assert result.returncode == 1
        assert "unused-ignore" in result.stdout

    def test_check_準拠確認_使用中のIgnoreで違反が報告されないこと(self):
        # Arrange
        target = FIXTURES_DIR / "compliant"

        # Act
        cmd = [sys.executable, "-m", "paladin.cli", "check", str(target)]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        # Assert: 使用中の Ignore コメントに対して unused-ignore は報告されない
        assert result.returncode == 0
