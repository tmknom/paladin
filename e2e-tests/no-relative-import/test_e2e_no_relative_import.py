"""no-relative-import ルールのE2Eテスト"""

import subprocess
from collections.abc import Callable
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestE2ENoRelativeImport:
    """no-relative-import ルールのE2Eテスト"""

    def test_check_違反検出_相対インポートが違反として報告されること(
        self,
        run_paladin_check: Callable[[Path], subprocess.CompletedProcess[str]],
    ):
        # Arrange
        target = FIXTURES_DIR / "violation" / "relative_import.py"

        # Act
        result = run_paladin_check(target)

        # Assert
        assert result.returncode == 1
        assert "no-relative-import" in result.stdout

    def test_check_準拠確認_絶対インポートのみで違反が報告されないこと(
        self,
        run_paladin_check: Callable[[Path], subprocess.CompletedProcess[str]],
    ):
        # Arrange
        target = FIXTURES_DIR / "compliant" / "absolute_import.py"

        # Act
        result = run_paladin_check(target)

        # Assert
        assert result.returncode == 0
