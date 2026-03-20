"""no-non-init-all ルールのE2Eテスト"""

import subprocess
from collections.abc import Callable
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestE2ENoNonInitAll:
    """no-non-init-all ルールのE2Eテスト"""

    def test_check_違反検出_非initファイルのallが違反として報告されること(
        self,
        run_paladin_check: Callable[[Path], subprocess.CompletedProcess[str]],
    ):
        # Arrange
        target = FIXTURES_DIR / "violation" / "with_all.py"

        # Act
        result = run_paladin_check(target)

        # Assert
        assert result.returncode == 1
        assert "no-non-init-all" in result.stdout

    def test_check_準拠確認_allなし通常モジュールで違反が報告されないこと(
        self,
        run_paladin_check: Callable[[Path], subprocess.CompletedProcess[str]],
    ):
        # Arrange
        target = FIXTURES_DIR / "compliant" / "without_all.py"

        # Act
        result = run_paladin_check(target)

        # Assert
        assert result.returncode == 0
