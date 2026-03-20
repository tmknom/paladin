"""no-local-import ルールのE2Eテスト"""

import subprocess
from collections.abc import Callable
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestE2ENoLocalImport:
    """no-local-import ルールのE2Eテスト"""

    def test_check_違反検出_関数内インポートが違反として報告されること(
        self,
        run_paladin_check: Callable[[Path], subprocess.CompletedProcess[str]],
    ):
        # Arrange
        target = FIXTURES_DIR / "violation" / "local_import.py"

        # Act
        result = run_paladin_check(target)

        # Assert
        assert result.returncode == 1
        assert "no-local-import" in result.stdout

    def test_check_準拠確認_トップレベルインポートのみで違反が報告されないこと(
        self,
        run_paladin_check: Callable[[Path], subprocess.CompletedProcess[str]],
    ):
        # Arrange
        target = FIXTURES_DIR / "compliant" / "top_level_import.py"

        # Act
        result = run_paladin_check(target)

        # Assert
        assert result.returncode == 0
