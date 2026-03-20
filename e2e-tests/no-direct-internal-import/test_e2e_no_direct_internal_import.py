"""no-direct-internal-import ルールのE2Eテスト"""

import subprocess
from collections.abc import Callable
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestE2ENoDirectInternalImport:
    """no-direct-internal-import ルールのE2Eテスト"""

    def test_check_違反検出_内部モジュール直接インポートが違反として報告されること(
        self,
        run_paladin_check: Callable[[Path], subprocess.CompletedProcess[str]],
    ):
        # Arrange
        target = FIXTURES_DIR / "violation" / "src" / "alpha"

        # Act
        result = run_paladin_check(target)

        # Assert
        assert result.returncode == 1
        assert "no-direct-internal-import" in result.stdout

    def test_check_準拠確認_initpy経由インポートで違反が報告されないこと(
        self,
        run_paladin_check: Callable[[Path], subprocess.CompletedProcess[str]],
    ):
        # Arrange
        target = FIXTURES_DIR / "compliant" / "src" / "beta"

        # Act
        result = run_paladin_check(target)

        # Assert
        assert result.returncode == 0
