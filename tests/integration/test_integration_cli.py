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
        cmd = [sys.executable, "-m", "paladin.cli", "transform", str(input_file)]
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
            "paladin.cli",
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


class TestIntegrationRulesCLI:
    """rules サブコマンドの統合テスト"""

    def test_rules_正常系_ルール一覧をtext形式で出力しexit_code_0で終了すること(self):
        # Act
        cmd = [sys.executable, "-m", "paladin.cli", "rules"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

        # Assert
        assert result.returncode == 0
        assert "require-all-export" in result.stdout
        assert "no-relative-import" in result.stdout
        assert "no-local-import" in result.stdout
        assert "require-qualified-third-party" in result.stdout


class TestIntegrationCheckCLI:
    """check サブコマンドの統合テスト"""

    def test_check_正常系_違反なしでexit_code_0とOKサマリーを出力すること(self, tmp_dir: Path):
        # Arrange
        src_dir = tmp_dir / "src"
        src_dir.mkdir()
        py_file = src_dir / "main.py"
        py_file.write_text("x = 1\n")

        # Act
        cmd = [sys.executable, "-m", "paladin.cli", "check", str(src_dir)]
        result = subprocess.run(cmd, cwd=tmp_dir, capture_output=True, text=True, timeout=10)

        # Assert
        assert result.returncode == 0
        assert "status: ok" in result.stdout

    def test_check_正常系_違反ありでexit_code_1と診断レポートを出力すること(self, tmp_dir: Path):
        # Arrange: __init__.py に __all__ なし（require-all-export 違反）
        src_dir = tmp_dir / "src"
        src_dir.mkdir()
        init_file = src_dir / "__init__.py"
        init_file.write_text("x = 1\n")

        # Act
        cmd = [sys.executable, "-m", "paladin.cli", "check", str(src_dir)]
        result = subprocess.run(cmd, cwd=tmp_dir, capture_output=True, text=True, timeout=10)

        # Assert
        assert result.returncode == 1
        assert "require-all-export" in result.stdout
        assert "概要:" in result.stdout
        assert "理由:" in result.stdout
        assert "修正方向:" in result.stdout
        assert "status: violations" in result.stdout

    def test_check_異常系_構文エラーのPythonファイルでexit_code_2を返すこと(self, tmp_dir: Path):
        # Arrange
        invalid_file = tmp_dir / "invalid.py"
        invalid_file.write_text("def :\n")

        # Act
        cmd = [sys.executable, "-m", "paladin.cli", "check", str(invalid_file)]
        result = subprocess.run(cmd, cwd=tmp_dir, capture_output=True, text=True, timeout=10)

        # Assert
        assert result.returncode == 2

    def test_check_異常系_存在しないパスでexit_code_2を返すこと(self, tmp_dir: Path):
        # Arrange
        non_existent = tmp_dir / "does_not_exist"

        # Act
        cmd = [sys.executable, "-m", "paladin.cli", "check", str(non_existent)]
        result = subprocess.run(cmd, cwd=tmp_dir, capture_output=True, text=True, timeout=10)

        # Assert
        assert result.returncode == 2

    # このテストは main() の ErrorHandler が例外を捕捉して sys.exit(2) に変換する経路を検証する。
    # 未知のサブコマンドでは Typer が先に exit code 2 で終了し ErrorHandler に到達しないため、
    # 実在するサブコマンド経由で例外を発生させる必要がある。
    # 使用するサブコマンド自体のロジックは、このテストの関心事ではない。
    def test_例外発生時_ErrorHandlerがexit_code_2で終了すること(self, tmp_dir: Path):
        # Arrange
        non_existent_file = tmp_dir / "non_existent.txt"

        # Act
        cmd = [sys.executable, "-m", "paladin.cli", "transform", str(non_existent_file)]
        result = subprocess.run(cmd, cwd=tmp_dir, capture_output=True, text=True, timeout=10)

        # Assert
        assert result.returncode == 2
        # エラーメッセージが出力されることを確認（標準エラー出力に表示される）
        assert result.stderr or "Error" in result.stdout
