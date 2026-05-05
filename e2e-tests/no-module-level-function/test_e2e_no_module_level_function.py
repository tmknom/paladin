"""no-module-level-function ルールのE2Eテスト"""

import subprocess
import sys
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestE2ENoModuleLevelFunction:
    """no-module-level-function ルールのE2Eテスト"""

    def test_check_違反検出_モジュールレベル関数が違反として報告されること(self):
        # Arrange
        target = FIXTURES_DIR / "violation"

        # Act
        cmd = [sys.executable, "-m", "paladin.cli", "check", str(target)]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        # Assert
        assert result.returncode == 1
        assert "no-module-level-function" in result.stdout

    def test_check_準拠確認_クラスメソッドのみで違反が報告されないこと(self):
        # Arrange
        target = FIXTURES_DIR / "compliant" / "method_only.py"

        # Act
        cmd = [sys.executable, "-m", "paladin.cli", "check", str(target)]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        # Assert
        assert result.returncode == 0

    def test_check_準拠確認_pytest_fixture付き関数で違反が報告されないこと(self):
        # Arrange: @pytest.fixture デコレータが許可リストに含まれることを確認
        target = FIXTURES_DIR / "compliant" / "tests" / "with_fixture.py"

        # Act
        cmd = [sys.executable, "-m", "paladin.cli", "check", str(target)]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        # Assert
        assert result.returncode == 0
