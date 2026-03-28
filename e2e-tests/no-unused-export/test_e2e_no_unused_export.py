"""no-unused-export ルールのE2Eテスト"""

import subprocess
import sys
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestE2ENoUnusedExport:
    """no-unused-export ルールのE2Eテスト"""

    def test_check_違反検出_未使用エクスポートが違反として報告されること(
        self,
    ):
        # Arrange
        target = FIXTURES_DIR / "violation" / "src" / "gamma"

        # Act
        cmd = [sys.executable, "-m", "paladin.cli", "check", str(target)]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        # Assert
        assert result.returncode == 1
        assert "no-unused-export" in result.stdout

    def test_check_準拠確認_全エクスポートが使用されて違反が報告されないこと(
        self,
    ):
        # Arrange
        compliant_dir = FIXTURES_DIR / "compliant"
        target = compliant_dir / "src" / "delta"

        # Act: cwd を compliant_dir にして pyproject.toml を読み込ませる
        cmd = [sys.executable, "-m", "paladin.cli", "check", str(target)]
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=30, cwd=str(compliant_dir)
        )

        # Assert
        assert result.returncode == 0

    def test_check_準拠確認_テストパッケージのエクスポートがテストから利用されて違反が報告されないこと(
        self,
    ):
        # Arrange: tests/unit/fake/__init__.py の FakeHelper が別テストから利用されている
        target = FIXTURES_DIR / "compliant_test_export"

        # Act
        cmd = [sys.executable, "-m", "paladin.cli", "check", str(target)]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        # Assert
        assert result.returncode == 0
