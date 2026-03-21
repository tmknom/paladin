"""no-deep-nesting ルールのE2Eテスト"""

import subprocess
from collections.abc import Callable
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestE2ENoDeepNesting:
    """no-deep-nesting ルールのE2Eテスト"""

    def test_check_違反検出_3段階以上のネストが違反として報告されること(
        self,
        run_paladin_check: Callable[[Path], subprocess.CompletedProcess[str]],
    ):
        # Arrange
        target = FIXTURES_DIR / "violation"

        # Act
        result = run_paladin_check(target)

        # Assert
        assert result.returncode == 1
        assert "no-deep-nesting" in result.stdout

    def test_check_準拠確認_2段階以下のネストで違反が報告されないこと(
        self,
        run_paladin_check: Callable[[Path], subprocess.CompletedProcess[str]],
    ):
        # Arrange
        target = FIXTURES_DIR / "compliant"

        # Act
        result = run_paladin_check(target)

        # Assert
        assert result.returncode == 0
