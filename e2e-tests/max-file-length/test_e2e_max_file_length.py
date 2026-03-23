"""max-file-length ルールのE2Eテスト"""

import subprocess
import sys
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestE2EMaxFileLength:
    """max-file-length ルールのE2Eテスト"""

    def test_check_違反検出_上限超過のファイルが違反として報告されること(self):
        # Arrange: violation ディレクトリに pyproject.toml を置いて max-lines を設定
        violation_dir = FIXTURES_DIR / "violation"
        target = violation_dir / "long_file.py"
        cmd = [sys.executable, "-m", "paladin.cli", "check", str(target)]

        # Act: cwd を violation_dir にして pyproject.toml を読み込ませる
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=30, cwd=str(violation_dir)
        )

        # Assert
        assert result.returncode == 1
        assert "max-file-length" in result.stdout

    def test_check_準拠確認_上限以下のファイルで違反が報告されないこと(self):
        # Arrange: compliant の short_file.py は10行（上限10行以下）
        violation_dir = FIXTURES_DIR / "violation"
        target = FIXTURES_DIR / "compliant" / "short_file.py"
        cmd = [sys.executable, "-m", "paladin.cli", "check", str(target)]

        # Act: cwd を violation_dir にして pyproject.toml（max-lines=10）を読み込ませる
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=30, cwd=str(violation_dir)
        )

        # Assert
        assert result.returncode == 0
