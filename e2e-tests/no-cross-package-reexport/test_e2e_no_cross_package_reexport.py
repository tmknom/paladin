"""no-cross-package-reexport ルールのE2Eテスト"""

import subprocess
import sys
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestE2ENoCrossPackageReexport:
    """no-cross-package-reexport ルールのE2Eテスト"""

    def test_check_違反検出_別パッケージ再エクスポートが違反として報告されること(
        self,
    ):
        # Arrange
        target = FIXTURES_DIR / "violation" / "src" / "alpha"

        # Act
        cmd = [sys.executable, "-m", "paladin.cli", "check", str(target)]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        # Assert
        assert result.returncode == 1
        assert "no-cross-package-reexport" in result.stdout

    def test_check_準拠確認_自パッケージシンボルのみで違反が報告されないこと(
        self,
    ):
        # Arrange
        compliant_dir = FIXTURES_DIR / "compliant"
        target = compliant_dir / "src" / "beta"

        # Act: cwd を compliant_dir にして pyproject.toml を読み込ませる
        cmd = [sys.executable, "-m", "paladin.cli", "check", str(target)]
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=30, cwd=str(compliant_dir)
        )

        # Assert
        assert result.returncode == 0
