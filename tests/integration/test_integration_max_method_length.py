"""max-method-length ルールの統合テスト"""

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


class TestIntegrationMaxMethodLength:
    """max-method-length ルールの統合テスト"""

    def test_check_正常系_上限超過の関数で違反が報告されること(self, tmp_dir: Path):
        # Arrange: 51行の関数（デフォルト上限50行超え）
        src_dir = tmp_dir / "src"
        src_dir.mkdir()
        py_file = src_dir / "long_func.py"
        lines = ["def long_function():"]
        for i in range(49):
            lines.append(f"    x_{i} = {i}")
        lines.append("    pass")
        py_file.write_text("\n".join(lines) + "\n")

        # Act
        cmd = [sys.executable, "-m", "paladin.cli", "check", str(src_dir)]
        result = subprocess.run(cmd, cwd=tmp_dir, capture_output=True, text=True, timeout=10)

        # Assert
        assert result.returncode == 1
        assert "max-method-length" in result.stdout

    def test_check_正常系_上限以下の関数で違反が報告されないこと(self, tmp_dir: Path):
        # Arrange: 50行の関数（上限ちょうど）
        src_dir = tmp_dir / "src"
        src_dir.mkdir()
        py_file = src_dir / "short_func.py"
        lines = ["def short_function():"]
        for i in range(48):
            lines.append(f"    x_{i} = {i}")
        lines.append("    pass")
        py_file.write_text("\n".join(lines) + "\n")

        # Act
        cmd = [sys.executable, "-m", "paladin.cli", "check", str(src_dir)]
        result = subprocess.run(cmd, cwd=tmp_dir, capture_output=True, text=True, timeout=10)

        # Assert
        assert result.returncode == 0
        assert "max-method-length" not in result.stdout

    def test_check_正常系_rule_optionsでカスタム上限を指定できること(self, tmp_dir: Path):
        # Arrange: 11行の関数、設定で max-lines=10 に設定
        src_dir = tmp_dir / "src"
        src_dir.mkdir()
        py_file = src_dir / "mid_func.py"
        lines = ["def mid_function():"]
        for i in range(9):
            lines.append(f"    x_{i} = {i}")
        lines.append("    pass")
        py_file.write_text("\n".join(lines) + "\n")
        pyproject = tmp_dir / "pyproject.toml"
        pyproject.write_text('[tool.paladin.rule."max-method-length"]\nmax-lines = 10\n')

        # Act
        cmd = [sys.executable, "-m", "paladin.cli", "check", str(src_dir)]
        result = subprocess.run(cmd, cwd=tmp_dir, capture_output=True, text=True, timeout=10)

        # Assert: カスタム上限10行に対して11行の関数が違反として検出される
        assert result.returncode == 1
        assert "max-method-length" in result.stdout

    def test_check_正常系_テストファイルにはmax_test_linesが適用されること(self, tmp_dir: Path):
        # Arrange: 51行の関数をテストファイルに配置（テスト上限100行以内なので違反なし）
        tests_dir = tmp_dir / "tests"
        tests_dir.mkdir()
        py_file = tests_dir / "test_example.py"
        lines = ["def test_long_case():"]
        for i in range(49):
            lines.append(f"    x_{i} = {i}")
        lines.append("    assert True")
        py_file.write_text("\n".join(lines) + "\n")

        # Act
        cmd = [sys.executable, "-m", "paladin.cli", "check", str(tests_dir)]
        result = subprocess.run(cmd, cwd=tmp_dir, capture_output=True, text=True, timeout=10)

        # Assert: テストファイルには max-test-lines=100 が適用されるため違反なし
        assert "max-method-length" not in result.stdout
