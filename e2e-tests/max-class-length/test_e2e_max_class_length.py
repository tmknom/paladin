"""max-class-length ルールのE2Eテスト"""

import subprocess
from collections.abc import Callable
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestE2EMaxClassLength:
    """max-class-length ルールのE2Eテスト"""

    def test_check_違反検出_上限超過のクラスが違反として報告されること(
        self,
        run_paladin_check: Callable[[Path], subprocess.CompletedProcess[str]],
    ):
        # Arrange
        target = FIXTURES_DIR / "violation"

        # Act
        result = run_paladin_check(target)

        # Assert
        assert result.returncode == 1
        assert "max-class-length" in result.stdout

    def test_check_準拠確認_上限以下のクラスで違反が報告されないこと(
        self,
        run_paladin_check: Callable[[Path], subprocess.CompletedProcess[str]],
    ):
        # Arrange
        target = FIXTURES_DIR / "compliant"

        # Act
        result = run_paladin_check(target)

        # Assert
        assert result.returncode == 0
