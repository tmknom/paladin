"""統合CLIツールの統合テスト

CLIの共通動作を検証
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path


class TestIntegrationCLI:
    """CLI共通動作の統合テスト"""

    def test_transform_正常系_変換結果のjsonとファイルが出力されること(self, tmp_dir: Path):
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
            env={**os.environ, "EXAMPLE_TMP_DIR": str(env_tmp_dir)},
        )

        # Assert
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert "src_length" in data
        assert (cli_tmp_dir / "input.txt").exists()
        assert not (env_tmp_dir / "input.txt").exists()


class TestIntegrationListCLI:
    """list サブコマンドの統合テスト"""

    def test_list_正常系_ルール一覧をtext形式で出力しexit_code_0で終了すること(self):
        # Act
        cmd = [sys.executable, "-m", "paladin.cli", "list"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

        # Assert
        assert result.returncode == 0
        assert result.stdout != ""


class TestIntegrationViewCLI:
    """view サブコマンドの統合テスト"""

    def test_view_正常系_rule_id指定で対象ルールの詳細を出力しexit_code_0で終了すること(self):
        # Act
        cmd = [sys.executable, "-m", "paladin.cli", "view", "require-all-export"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

        # Assert
        assert result.returncode == 0
        assert result.stdout != ""
        assert "require-all-export" in result.stdout


class TestIntegrationVersionCLI:
    """version サブコマンドの統合テスト"""

    def test_version_正常系_バージョン文字列を出力しexit_code_0で終了すること(self):
        # Act
        cmd = [sys.executable, "-m", "paladin.cli", "version"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

        # Assert
        assert result.returncode == 0
        assert re.search(r"\d+\.\d+\.\d+", result.stdout) is not None


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

    def test_check_正常系_format_json指定で違反ありのJSON出力とexit_code_1を返すこと(
        self, tmp_dir: Path
    ):
        # Arrange: __init__.py に __all__ なし（require-all-export 違反）
        src_dir = tmp_dir / "src"
        src_dir.mkdir()
        init_file = src_dir / "__init__.py"
        init_file.write_text("x = 1\n")

        # Act
        cmd = [sys.executable, "-m", "paladin.cli", "check", str(src_dir), "--format", "json"]
        result = subprocess.run(cmd, cwd=tmp_dir, capture_output=True, text=True, timeout=10)

        # Assert
        assert result.returncode == 1
        data = json.loads(result.stdout)
        assert data["status"] == "violations"
        assert isinstance(data["diagnostics"], list)
        assert len(data["diagnostics"]) > 0

    def test_check_正常系_ignore_ruleで指定ルールの違反が除外されること(self, tmp_dir: Path):
        # Arrange: __init__.py に __all__ なし（require-all-export 違反）
        src_dir = tmp_dir / "src"
        src_dir.mkdir()
        init_file = src_dir / "__init__.py"
        init_file.write_text("x = 1\n")

        # Act
        cmd = [
            sys.executable,
            "-m",
            "paladin.cli",
            "check",
            str(src_dir),
            "--ignore-rule",
            "require-all-export",
        ]
        result = subprocess.run(cmd, cwd=tmp_dir, capture_output=True, text=True, timeout=10)

        # Assert: 違反が除外されて exit_code=0
        assert result.returncode == 0
        assert "status: ok" in result.stdout


class TestIntegrationCheckRuleOption:
    """check コマンドの --rule オプションの統合テスト"""

    def test_check_正常系_ruleオプションで指定ルールのみ実行されること(self, tmp_dir: Path):
        # Arrange: __init__.py に __all__ なし（require-all-export 違反）
        # --rule no-relative-import を指定 → require-all-export がスキップされる
        src_dir = tmp_dir / "src"
        src_dir.mkdir()
        init_file = src_dir / "__init__.py"
        init_file.write_text("x = 1\n")

        # Act
        cmd = [
            sys.executable,
            "-m",
            "paladin.cli",
            "check",
            str(src_dir),
            "--rule",
            "no-relative-import",
        ]
        result = subprocess.run(cmd, cwd=tmp_dir, capture_output=True, text=True, timeout=10)

        # Assert: require-all-export がスキップされるため exit_code=0
        assert result.returncode == 0
        assert "status: ok" in result.stdout

    def test_check_正常系_ruleオプション複数指定で指定ルールのみ実行されること(self, tmp_dir: Path):
        # Arrange: __init__.py に __all__ なし（require-all-export 違反）
        # --rule require-all-export --rule no-relative-import → require-all-export が実行される
        src_dir = tmp_dir / "src"
        src_dir.mkdir()
        init_file = src_dir / "__init__.py"
        init_file.write_text("x = 1\n")

        # Act
        cmd = [
            sys.executable,
            "-m",
            "paladin.cli",
            "check",
            str(src_dir),
            "--rule",
            "require-all-export",
            "--rule",
            "no-relative-import",
        ]
        result = subprocess.run(cmd, cwd=tmp_dir, capture_output=True, text=True, timeout=10)

        # Assert: require-all-export が実行され違反あり → exit_code=1
        assert result.returncode == 1
        assert "require-all-export" in result.stdout


class TestIntegrationCheckConfig:
    """check コマンドの設定ファイル連携の統合テスト"""

    def test_check_正常系_rulesセクションでfalseに設定されたルールが無効化されること(
        self, tmp_dir: Path
    ):
        # Arrange: __init__.py に __all__ なし（require-all-export 違反）
        # pyproject.toml で require-all-export = false に設定
        init_file = tmp_dir / "__init__.py"
        init_file.write_text("x = 1\n")
        pyproject = tmp_dir / "pyproject.toml"
        pyproject.write_text("[tool.paladin.rules]\nrequire-all-export = false\n")

        # Act: cwd=tmp_dir で pyproject.toml が読まれる
        cmd = [sys.executable, "-m", "paladin.cli", "check", str(tmp_dir)]
        result = subprocess.run(cmd, cwd=tmp_dir, capture_output=True, text=True, timeout=10)

        # Assert: require-all-export が無効化されているため exit_code=0
        assert result.returncode == 0
        assert "status: ok" in result.stdout

    def test_check_正常系_includeで対象ディレクトリを制御できること(self, tmp_dir: Path):
        # Arrange: src/ 配下のみ include に指定（CLI ターゲット未指定）
        src_dir = tmp_dir / "src"
        src_dir.mkdir()
        src_file = src_dir / "main.py"
        src_file.write_text("x = 1\n")
        pyproject = tmp_dir / "pyproject.toml"
        pyproject.write_text(f'[tool.paladin]\ninclude = ["{src_dir}"]\n')

        # Act: ターゲット未指定、include から解決
        cmd = [sys.executable, "-m", "paladin.cli", "check"]
        result = subprocess.run(cmd, cwd=tmp_dir, capture_output=True, text=True, timeout=10)

        # Assert: src/main.py が解析され違反なし
        assert result.returncode == 0
        assert "status: ok" in result.stdout

    def test_check_正常系_overridesでディレクトリ別にルールを無効化できること(self, tmp_dir: Path):
        # Arrange: tests/ の __init__.py は require-all-export 違反あり
        # overrides で tests/** に require-all-export = false を設定
        tests_dir = tmp_dir / "tests"
        tests_dir.mkdir()
        init_file = tests_dir / "__init__.py"
        init_file.write_text("x = 1\n")
        pyproject = tmp_dir / "pyproject.toml"
        pyproject.write_text(
            "[[tool.paladin.overrides]]\n"
            'files = ["tests/**"]\n'
            "\n"
            "[tool.paladin.overrides.rules]\n"
            "require-all-export = false\n"
        )

        # Act: cwd=tmp_dir で pyproject.toml が読まれる
        cmd = [sys.executable, "-m", "paladin.cli", "check", str(tmp_dir)]
        result = subprocess.run(cmd, cwd=tmp_dir, capture_output=True, text=True, timeout=10)

        # Assert: tests/ 配下の require-all-export が無効化されるため exit_code=0
        assert result.returncode == 0
        assert "status: ok" in result.stdout


class TestIntegrationCheckIgnore:
    """check コマンドの Ignore 機能の統合テスト"""

    def test_check_正常系_ignore_fileコメントで違反が無視されること(self, tmp_dir: Path):
        # Arrange: # paladin: ignore-file コメントで全ルール違反を無視
        init_file = tmp_dir / "__init__.py"
        init_file.write_text("# paladin: ignore-file\nx = 1\n")

        # Act
        cmd = [sys.executable, "-m", "paladin.cli", "check", str(tmp_dir)]
        result = subprocess.run(cmd, cwd=tmp_dir, capture_output=True, text=True, timeout=10)

        # Assert: ignore-file により違反が無視されて exit_code=0
        assert result.returncode == 0
        assert "status: ok" in result.stdout

    def test_check_正常系_per_file_ignoresで設定パターンの違反が無視されること(self, tmp_dir: Path):
        # Arrange: tests/ 配下の require-all-export を per-file-ignores で ignore
        tests_dir = tmp_dir / "tests"
        tests_dir.mkdir()
        init_file = tests_dir / "__init__.py"
        init_file.write_text("x = 1\n")
        pyproject = tmp_dir / "pyproject.toml"
        pyproject.write_text(
            '[tool.paladin.per-file-ignores]\n"tests/**" = ["require-all-export"]\n'
        )

        # Act: cwd=tmp_dir で pyproject.toml が読まれる
        cmd = [sys.executable, "-m", "paladin.cli", "check", str(tests_dir)]
        result = subprocess.run(cmd, cwd=tmp_dir, capture_output=True, text=True, timeout=10)

        # Assert: require-all-export が per-file-ignores で除外されるため exit_code=0
        assert result.returncode == 0
        assert "status: ok" in result.stdout
