"""no-cross-package-import ルールのE2Eテスト"""

import subprocess
import sys
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestE2ENoCrossPackageImport:
    """no-cross-package-import ルールのE2Eテスト"""

    def test_check_違反検出_allow_dirs外のパッケージからのクロスパッケージインポートが違反として報告されること(
        self,
    ):
        # Arrange: violation ディレクトリに pyproject.toml を置いて allow-dirs を設定
        violation_dir = FIXTURES_DIR / "violation"
        target = violation_dir / "src" / "myapp" / "view" / "handler.py"

        # Act: cwd を violation_dir にして pyproject.toml を読み込ませる
        cmd = [sys.executable, "-m", "paladin.cli", "check", str(target)]
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=30, cwd=str(violation_dir)
        )

        # Assert
        assert result.returncode == 1
        assert "no-cross-package-import" in result.stdout

    def test_check_準拠確認_allow_dirsに含まれるパッケージのインポートで違反が報告されないこと(
        self,
    ):
        # Arrange: compliant ディレクトリで consumer/app.py が rule パッケージをインポート
        compliant_dir = FIXTURES_DIR / "compliant"
        target = compliant_dir / "src" / "myapp" / "consumer" / "app.py"

        # Act: cwd を compliant_dir にして pyproject.toml を読み込ませる
        cmd = [sys.executable, "-m", "paladin.cli", "check", str(target)]
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=30, cwd=str(compliant_dir)
        )

        # Assert
        assert result.returncode == 0

    def test_check_違反検出_allow_dirs未設定で全ファイルの違反を検出すること(
        self,
    ):
        # Arrange: プロジェクトルートの pyproject.toml には allow-dirs 設定がないため
        # クロスパッケージインポートはすべて違反として検出される
        target = FIXTURES_DIR / "violation" / "src" / "myapp" / "view" / "handler.py"

        # Act: cwd 未指定でプロジェクトルートの pyproject.toml を読み込む
        cmd = [sys.executable, "-m", "paladin.cli", "check", str(target)]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        # Assert: allow-dirs 未設定なので no-cross-package-import ルールは全違反を報告する
        assert result.returncode == 1
        assert "no-cross-package-import" in result.stdout
