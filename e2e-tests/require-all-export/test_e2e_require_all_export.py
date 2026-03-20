"""require-all-export ルールのE2Eテスト"""

import subprocess
from collections.abc import Callable
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestE2ERequireAllExport:
    """require-all-export ルールのE2Eテスト"""

    def test_check_違反検出_init_pyにall未定義で違反が報告されること(
        self,
        run_paladin_check: Callable[[Path], subprocess.CompletedProcess[str]],
    ):
        # Arrange
        target = FIXTURES_DIR / "violation" / "__init__.py"

        # Act
        result = run_paladin_check(target)

        # Assert
        assert result.returncode == 1
        assert "require-all-export" in result.stdout

    def test_check_準拠確認_init_pyにallが定義されていて違反が報告されないこと(
        self,
        run_paladin_check: Callable[[Path], subprocess.CompletedProcess[str]],
    ):
        # Arrange
        target = FIXTURES_DIR / "compliant" / "__init__.py"

        # Act
        result = run_paladin_check(target)

        # Assert
        assert result.returncode == 0
