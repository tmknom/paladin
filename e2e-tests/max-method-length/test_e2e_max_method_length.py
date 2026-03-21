"""max-method-length ルールのE2Eテスト"""

import subprocess
from collections.abc import Callable
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestE2EMaxMethodLength:
    """max-method-length ルールのE2Eテスト"""

    def test_check_違反検出_上限超過の関数が違反として報告されること(
        self,
        run_paladin_check: Callable[[Path], subprocess.CompletedProcess[str]],
    ):
        # Arrange
        target = FIXTURES_DIR / "violation"

        # Act
        result = run_paladin_check(target)

        # Assert
        assert result.returncode == 1
        assert "max-method-length" in result.stdout

    def test_check_準拠確認_上限以下の関数で違反が報告されないこと(
        self,
        run_paladin_check: Callable[[Path], subprocess.CompletedProcess[str]],
    ):
        # Arrange
        target = FIXTURES_DIR / "compliant"

        # Act
        result = run_paladin_check(target)

        # Assert
        assert result.returncode == 0
