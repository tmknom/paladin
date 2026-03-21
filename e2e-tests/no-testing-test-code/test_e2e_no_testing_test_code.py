"""no-testing-test-code ルールのE2Eテスト"""

import subprocess
from collections.abc import Callable
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestE2ENoTestingTestCode:
    """no-testing-test-code ルールのE2Eテスト"""

    def test_check_違反検出_Fakeクラスに対するテストが違反として報告されること(
        self,
        run_paladin_check: Callable[[Path], subprocess.CompletedProcess[str]],
    ):
        # Arrange
        target = FIXTURES_DIR / "violation" / "tests"

        # Act
        result = run_paladin_check(target)

        # Assert
        assert result.returncode == 1
        assert "no-testing-test-code" in result.stdout

    def test_check_準拠確認_Fakeをセットアップに使うだけでは違反が報告されないこと(
        self,
        run_paladin_check: Callable[[Path], subprocess.CompletedProcess[str]],
    ):
        # Arrange
        target = FIXTURES_DIR / "compliant" / "tests"

        # Act
        result = run_paladin_check(target)

        # Assert
        assert result.returncode == 0
