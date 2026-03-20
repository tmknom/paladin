"""no-unused-export ルールのE2Eテスト"""

import subprocess
from collections.abc import Callable
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestE2ENoUnusedExport:
    """no-unused-export ルールのE2Eテスト"""

    def test_check_違反検出_未使用エクスポートが違反として報告されること(
        self,
        run_paladin_check: Callable[[Path], subprocess.CompletedProcess[str]],
    ):
        # Arrange
        target = FIXTURES_DIR / "violation" / "src" / "gamma"

        # Act
        result = run_paladin_check(target)

        # Assert
        assert result.returncode == 1
        assert "no-unused-export" in result.stdout

    def test_check_準拠確認_全エクスポートが使用されて違反が報告されないこと(
        self,
        run_paladin_check: Callable[[Path], subprocess.CompletedProcess[str]],
    ):
        # Arrange
        target = FIXTURES_DIR / "compliant" / "src" / "delta"

        # Act
        result = run_paladin_check(target)

        # Assert
        assert result.returncode == 0
