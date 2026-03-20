"""require-qualified-third-party ルールのE2Eテスト"""

import subprocess
from collections.abc import Callable
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestE2ERequireQualifiedThirdParty:
    """require-qualified-third-party ルールのE2Eテスト"""

    def test_check_違反検出_fromインポートが違反として報告されること(
        self,
        run_paladin_check: Callable[[Path], subprocess.CompletedProcess[str]],
    ):
        # Arrange
        target = FIXTURES_DIR / "violation" / "from_import.py"

        # Act
        result = run_paladin_check(target)

        # Assert
        assert result.returncode == 1
        assert "require-qualified-third-party" in result.stdout

    def test_check_準拠確認_完全修飾インポートで違反が報告されないこと(
        self,
        run_paladin_check: Callable[[Path], subprocess.CompletedProcess[str]],
    ):
        # Arrange
        target = FIXTURES_DIR / "compliant" / "qualified_import.py"

        # Act
        result = run_paladin_check(target)

        # Assert
        assert result.returncode == 0
