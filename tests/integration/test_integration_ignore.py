"""Ignore 機能の統合テスト

ignore-file ディレクティブおよび per-file-ignores による違反抑制を実ファイルシステムで検証する。
"""

import os
from pathlib import Path

from paladin.check import CheckOrchestratorProvider
from paladin.check.context import CheckContext


class TestIntegrationIgnore:
    """ignore-file ディレクティブの統合テスト"""

    def test_check_正常系_ignore_fileで全ルール違反が無視されること(self, tmp_path: Path):
        # Arrange
        init_file = tmp_path / "__init__.py"
        init_file.write_text("# paladin: ignore-file\nfrom foo import bar\n", encoding="utf-8")
        context = CheckContext(targets=(tmp_path,), has_cli_targets=True)

        # Act
        report = CheckOrchestratorProvider().provide().orchestrate(context)

        # Assert
        assert report.exit_code == 0

    def test_check_正常系_ignore_file_with_ruleで特定ルール違反のみ無視されること(
        self, tmp_path: Path
    ):
        # Arrange: require-all-export のみ ignore し、require-qualified-third-party は適用されたまま
        init_file = tmp_path / "__init__.py"
        init_file.write_text(
            "# paladin: ignore-file[require-all-export]\nfrom foo import bar\n",
            encoding="utf-8",
        )
        context = CheckContext(targets=(tmp_path,), has_cli_targets=True)

        # Act
        report = CheckOrchestratorProvider().provide().orchestrate(context)

        # Assert: require-all-export は除外されたが他のルール違反は残るため exit_code == 1
        assert report.exit_code == 1
        assert "require-all-export" not in report.text

    def test_check_正常系_ディレクティブなしで通常通りルール適用されること(self, tmp_path: Path):
        # Arrange
        init_file = tmp_path / "__init__.py"
        init_file.write_text("from foo import bar\n", encoding="utf-8")
        context = CheckContext(targets=(tmp_path,), has_cli_targets=True)

        # Act
        report = CheckOrchestratorProvider().provide().orchestrate(context)

        # Assert
        assert report.exit_code == 1


class TestIntegrationDirectoryIgnore:
    """per-file-ignores によるディレクトリ単位 Ignore の統合テスト"""

    def test_check_正常系_per_file_ignoresでディレクトリ配下の違反が無視されること(
        self, tmp_path: Path
    ):
        # Arrange: tests/ 配下の require-all-export を ignore する設定
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            '[tool.paladin.per-file-ignores]\n"tests/**" = ["require-all-export"]\n',
            encoding="utf-8",
        )
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        init_file = tests_dir / "__init__.py"
        init_file.write_text('__all__ = ["tests"]\n', encoding="utf-8")
        test_file = tests_dir / "test_main.py"
        test_file.write_text("import paladin\n", encoding="utf-8")
        context = CheckContext(targets=(tests_dir,), has_cli_targets=True)

        # Act: pyproject.toml が読まれるよう CWD を tmp_path に変更
        original_cwd = Path.cwd()
        try:
            os.chdir(tmp_path)
            report = CheckOrchestratorProvider().provide().orchestrate(context)
        finally:
            os.chdir(original_cwd)

        # Assert: tests/test_main.py の require-all-export 違反は ignore される
        assert "require-all-export" not in report.text

    def test_check_正常系_per_file_ignoresでネストしたディレクトリの違反も無視されること(
        self, tmp_path: Path
    ):
        # Arrange: tests/ 配下のネストしたディレクトリも ignore される
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            '[tool.paladin.per-file-ignores]\n"tests/**" = ["require-all-export"]\n',
            encoding="utf-8",
        )
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        init_file = tests_dir / "__init__.py"
        init_file.write_text('__all__ = ["tests"]\n', encoding="utf-8")
        unit_dir = tests_dir / "unit"
        unit_dir.mkdir()
        unit_init = unit_dir / "__init__.py"
        unit_init.write_text('__all__ = ["unit"]\n', encoding="utf-8")
        test_file = unit_dir / "test_deep.py"
        test_file.write_text("import paladin\n", encoding="utf-8")
        context = CheckContext(targets=(tests_dir,), has_cli_targets=True)

        # Act
        original_cwd = Path.cwd()
        try:
            os.chdir(tmp_path)
            report = CheckOrchestratorProvider().provide().orchestrate(context)
        finally:
            os.chdir(original_cwd)

        # Assert: tests/unit/test_deep.py の require-all-export 違反も ignore される
        assert "require-all-export" not in report.text

    def test_check_正常系_per_file_ignoresで全ルールignoreが機能すること(self, tmp_path: Path):
        # Arrange: scripts/ 配下の全ルールを ignore する設定
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            '[tool.paladin.per-file-ignores]\n"scripts/**" = ["*"]\n',
            encoding="utf-8",
        )
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir()
        script_file = scripts_dir / "deploy.py"
        script_file.write_text("from foo import bar\n", encoding="utf-8")
        context = CheckContext(targets=(scripts_dir,), has_cli_targets=True)

        # Act
        original_cwd = Path.cwd()
        try:
            os.chdir(tmp_path)
            report = CheckOrchestratorProvider().provide().orchestrate(context)
        finally:
            os.chdir(original_cwd)

        # Assert: scripts/ 配下の全違反が ignore されるため exit_code == 0
        assert report.exit_code == 0

    def test_check_正常系_per_file_ignoresのパターンに一致しないディレクトリは通常適用されること(
        self, tmp_path: Path
    ):
        # Arrange: tests/ のみ ignore し、src/ は通常適用
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            '[tool.paladin.per-file-ignores]\n"tests/**" = ["*"]\n',
            encoding="utf-8",
        )
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        src_file = src_dir / "main.py"
        src_file.write_text("from foo import bar\n", encoding="utf-8")
        context = CheckContext(targets=(src_dir,), has_cli_targets=True)

        # Act
        original_cwd = Path.cwd()
        try:
            os.chdir(tmp_path)
            report = CheckOrchestratorProvider().provide().orchestrate(context)
        finally:
            os.chdir(original_cwd)

        # Assert: src/ 配下は ignore されないため違反が検出される
        assert report.exit_code == 1
