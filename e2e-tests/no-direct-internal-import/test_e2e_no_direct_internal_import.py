"""no-direct-internal-import ルールのE2Eテスト"""

import subprocess
import sys
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

    def test_check_準拠確認_initpy経由インポートで違反が報告されないこと(self):
        # Arrange
        compliant_dir = FIXTURES_DIR / "compliant"
        target = compliant_dir / "src" / "beta"
        cmd = [sys.executable, "-m", "paladin.cli", "check", str(target)]

        # Act: cwd を compliant_dir にして pyproject.toml を読み込ませる
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=30, cwd=str(compliant_dir)
        )

        # Assert
        assert result.returncode == 0
