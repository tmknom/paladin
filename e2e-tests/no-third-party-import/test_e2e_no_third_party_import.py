"""no-third-party-import ルールのE2Eテスト"""

import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestE2ENoThirdPartyImport:
    """no-third-party-import ルールのE2Eテスト"""

    def test_check_違反検出_許可ディレクトリ外のサードパーティインポートが違反として報告されること(
        self,
    ):
        # Arrange: violation ディレクトリに pyproject.toml を置いて allow-dirs を設定
        violation_dir = FIXTURES_DIR / "violation"
        target = violation_dir / "src" / "app" / "main.py"
        cmd = [sys.executable, "-m", "paladin.cli", "check", str(target)]

        # Act: cwd を violation_dir にして pyproject.toml を読み込ませる
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=30, cwd=str(violation_dir)
        )

        # Assert
        assert result.returncode == 1
        assert "no-third-party-import" in result.stdout

    def test_check_準拠確認_標準ライブラリのインポートで違反が報告されないこと(
        self,
        run_paladin_check: Callable[[Path], subprocess.CompletedProcess[str]],
    ):
        # Arrange
        target = FIXTURES_DIR / "compliant" / "stdlib_import.py"

        # Act
        result = run_paladin_check(target)

        # Assert
        assert result.returncode == 0

    def test_check_違反検出_allow_dirs未設定で全ファイルの違反を検出すること(
        self,
        run_paladin_check: Callable[[Path], subprocess.CompletedProcess[str]],
    ):
        # Arrange: プロジェクトルートの pyproject.toml には allow-dirs 設定がないため
        # allow-dirs 未設定 = すべてのファイルでサードパーティインポートを禁止
        target = FIXTURES_DIR / "violation" / "src" / "app" / "main.py"

        # Act: プロジェクトルートを cwd にして実行（conftest の run_paladin_check を使用）
        result = run_paladin_check(target)

        # Assert: allow-dirs 未設定なので no-third-party-import ルールは違反を報告する
        assert result.returncode == 1
        assert "no-third-party-import" in result.stdout
