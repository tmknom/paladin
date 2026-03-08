"""統合CLIツールの統合テスト

CLIの共通動作を検証
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.fixture
def tmp_dir(tmp_path: Path) -> Path:
    """統合テスト用ワークスペース"""
    test_dir = tmp_path / "integration_test"
    test_dir.mkdir()
    return test_dir


class TestIntegrationCLI:
    """統合テスト"""

    def test_transform_正常系_ファイル変換を実行(self, tmp_dir: Path):
        # Arrange
        input_file = tmp_dir / "input.txt"
        input_file.write_text("test line", encoding="utf-8")
        tmp_output_dir = tmp_dir / "tmp"
        tmp_output_dir.mkdir()

        # Act
        cmd = [sys.executable, "-m", "example.cli", "transform", str(input_file)]
        result = subprocess.run(cmd, cwd=tmp_dir, capture_output=True, text=True, timeout=10)

        # Assert
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert "src_length" in data
        assert "dst_length" in data

        # 出力ファイルが作成されていることを確認
        output_file = tmp_output_dir / "input.txt"
        assert output_file.exists()
        content = output_file.read_text(encoding="utf-8")
        assert "1: test line" in content

    def test_transform_正常系_tmp_dirオプションが環境変数より優先される(self, tmp_dir: Path):
        # Arrange
        input_file = tmp_dir / "input.txt"
        input_file.write_text("test line", encoding="utf-8")
        env_tmp_dir = tmp_dir / "env_tmp"
        env_tmp_dir.mkdir()
        cli_tmp_dir = tmp_dir / "cli_tmp"
        cli_tmp_dir.mkdir()

        # Act
        cmd = [
            sys.executable,
            "-m",
            "example.cli",
            "transform",
            str(input_file),
            "--tmp-dir",
            str(cli_tmp_dir),
        ]
        result = subprocess.run(
            cmd,
            cwd=tmp_dir,
            capture_output=True,
            text=True,
            timeout=10,
            env={**__import__("os").environ, "EXAMPLE_TMP_DIR": str(env_tmp_dir)},
        )

        # Assert
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert "src_length" in data
        assert (cli_tmp_dir / "input.txt").exists()
        assert not (env_tmp_dir / "input.txt").exists()

    # このテストは main() の ErrorHandler が例外を捕捉して sys.exit(1) に変換する経路を検証する。
    # 未知のサブコマンドでは Typer が先に exit code 2 で終了し ErrorHandler に到達しないため、
    # 実在するサブコマンド経由で例外を発生させる必要がある。
    # 使用するサブコマンド自体のロジックは、このテストの関心事ではない。
    def test_例外発生時_ErrorHandlerがexit_code_1で終了すること(self, tmp_dir: Path):
        # Arrange
        non_existent_file = tmp_dir / "non_existent.txt"

        # Act
        cmd = [sys.executable, "-m", "example.cli", "transform", str(non_existent_file)]
        result = subprocess.run(cmd, cwd=tmp_dir, capture_output=True, text=True, timeout=10)

        # Assert
        assert result.returncode == 1
        # エラーメッセージが出力されることを確認（標準エラー出力に表示される）
        assert result.stderr or "Error" in result.stdout
