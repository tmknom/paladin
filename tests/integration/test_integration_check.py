import json
import subprocess
import sys
from pathlib import Path


class TestIntegrationCheck:
    """check サブコマンドの基本動作のインテグレーションテスト"""

    def test_check_正常系_違反なしでexit_code_0とOKサマリーを出力すること(self, tmp_dir: Path):
        # Arrange
        src_dir = tmp_dir / "src"
        src_dir.mkdir()
        py_file = src_dir / "main.py"
        py_file.write_text('"""メインモジュール"""\n\nx = 1\n')

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


class TestIntegrationCheckRuleOption:
    """check コマンドの --rule オプションのインテグレーションテスト"""

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
        pyproject.write_text("[tool.paladin.rule.max-method-length]\nmax-lines = 10\n")

        # Act
        cmd = [sys.executable, "-m", "paladin.cli", "check", str(src_dir)]
        result = subprocess.run(cmd, cwd=tmp_dir, capture_output=True, text=True, timeout=10)

        # Assert: カスタム上限10行に対して11行の関数が違反として検出される
        assert result.returncode == 1
        assert "max-method-length" in result.stdout


class TestIntegrationCheckConfig:
    """check コマンドの設定ファイル連携のインテグレーションテスト"""

    def test_check_正常系_rulesセクションでfalseに設定されたルールが無効化されること(
        self, tmp_dir: Path
    ):
        # Arrange: __init__.py に __all__ なし（require-all-export 違反）
        # pyproject.toml で require-all-export = false / require-docstring = false に設定
        init_file = tmp_dir / "__init__.py"
        init_file.write_text("x = 1\n")
        pyproject = tmp_dir / "pyproject.toml"
        pyproject.write_text(
            "[tool.paladin.rules]\nrequire-all-export = false\nrequire-docstring = false\n"
        )

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
        src_file.write_text('"""メインモジュール"""\n\nx = 1\n')
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
        # overrides で tests/** に require-all-export = false と require-empty-test-init = false を設定
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
            "require-empty-test-init = false\n"
        )

        # Act: cwd=tmp_dir で pyproject.toml が読まれる
        cmd = [sys.executable, "-m", "paladin.cli", "check", str(tmp_dir)]
        result = subprocess.run(cmd, cwd=tmp_dir, capture_output=True, text=True, timeout=10)

        # Assert: tests/ 配下の require-all-export が無効化されるため exit_code=0
        assert result.returncode == 0
        assert "status: ok" in result.stdout


class TestIntegrationCheckIgnore:
    """check コマンドの Ignore 機能のインテグレーションテスト"""

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
        # Arrange: tests/ 配下の require-all-export と require-empty-test-init を per-file-ignores で ignore
        tests_dir = tmp_dir / "tests"
        tests_dir.mkdir()
        init_file = tests_dir / "__init__.py"
        init_file.write_text("x = 1\n")
        pyproject = tmp_dir / "pyproject.toml"
        pyproject.write_text(
            '[tool.paladin.per-file-ignores]\n"tests/**" = ["require-all-export", "require-empty-test-init"]\n'
        )

        # Act: cwd=tmp_dir で pyproject.toml が読まれる
        cmd = [sys.executable, "-m", "paladin.cli", "check", str(tests_dir)]
        result = subprocess.run(cmd, cwd=tmp_dir, capture_output=True, text=True, timeout=10)

        # Assert: require-all-export が per-file-ignores で除外されるため exit_code=0
        assert result.returncode == 0
        assert "status: ok" in result.stdout

    def test_check_正常系_ignore_ruleで指定ルールの違反が除外されること(self, tmp_dir: Path):
        # Arrange: __init__.py に __all__ なし（require-all-export 違反）
        src_dir = tmp_dir / "src"
        src_dir.mkdir()
        init_file = src_dir / "__init__.py"
        init_file.write_text('"""パッケージ"""\n\nx = 1\n')

        # Act: require-all-export を ignore
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

        # Assert: require-all-export が除外されて exit_code=0
        assert result.returncode == 0
        assert "status: ok" in result.stdout

    def test_check_正常系_行末ignoreコメントで違反が除外されること(self, tmp_dir: Path):
        # Arrange: __init__.py に __all__ なし（require-all-export 違反）を行末コメントで ignore
        src_dir = tmp_dir / "src"
        src_dir.mkdir()
        init_file = src_dir / "__init__.py"
        init_file.write_text("x = 1  # paladin: ignore\n")

        # Act
        cmd = [sys.executable, "-m", "paladin.cli", "check", str(src_dir)]
        result = subprocess.run(cmd, cwd=tmp_dir, capture_output=True, text=True, timeout=10)

        # Assert: 行末コメントにより違反が除外されて exit_code=0
        assert result.returncode == 0
        assert "status: ok" in result.stdout

    def test_check_正常系_直前コメントと行末コメントの累積適用で違反が除外されること(
        self, tmp_dir: Path
    ):
        # Arrange: 同一行（line 3）に no-local-import と no-relative-import の2つの違反を発生させ、
        #          直前コメントで no-local-import を、行末コメントで no-relative-import をそれぞれ ignore する
        src_dir = tmp_dir / "src"
        src_dir.mkdir()
        py_file = src_dir / "main.py"
        py_file.write_text(
            '"""メインモジュール"""\n'
            "\n"
            "def foo():\n"
            "    # paladin: ignore[no-local-import]\n"
            "    from .foo import bar  # paladin: ignore[no-relative-import]\n"
        )

        # Act
        cmd = [sys.executable, "-m", "paladin.cli", "check", str(src_dir)]
        result = subprocess.run(cmd, cwd=tmp_dir, capture_output=True, text=True, timeout=10)

        # Assert: 直前コメントと行末コメントが累積適用されて両違反が除外され exit_code=0
        assert result.returncode == 0
        assert "status: ok" in result.stdout

    def test_check_正常系_未使用ignoreコメントがunused_ignoreとして報告されること(
        self, tmp_dir: Path
    ):
        # Arrange: 違反が存在しない行に ignore コメントを記述
        src_dir = tmp_dir / "src"
        src_dir.mkdir()
        py_file = src_dir / "main.py"
        py_file.write_text('"""メインモジュール"""\n\n# paladin: ignore[no-local-import]\nx = 1\n')

        # Act
        cmd = [sys.executable, "-m", "paladin.cli", "check", str(src_dir)]
        result = subprocess.run(cmd, cwd=tmp_dir, capture_output=True, text=True, timeout=10)

        # Assert: 未使用の ignore コメントが unused-ignore として報告される
        assert result.returncode == 1
        assert "unused-ignore" in result.stdout

    def test_check_正常系_使用中のignoreコメントはunused_ignoreとして報告されないこと(
        self, tmp_dir: Path
    ):
        # Arrange: no-local-import 違反のある行に対して ignore コメントを記述
        src_dir = tmp_dir / "src"
        src_dir.mkdir()
        py_file = src_dir / "main.py"
        py_file.write_text(
            '"""メインモジュール"""\n'
            "\n"
            "def foo():\n"
            "    import os  # paladin: ignore[no-local-import]\n"
            "    return os.getcwd()\n"
        )

        # Act
        cmd = [sys.executable, "-m", "paladin.cli", "check", str(src_dir)]
        result = subprocess.run(cmd, cwd=tmp_dir, capture_output=True, text=True, timeout=10)

        # Assert: 使用中の ignore コメントは unused-ignore として報告されない
        assert result.returncode == 0
        assert "unused-ignore" not in result.stdout
