"""設定ファイルによるルール制御の統合テスト

[tool.paladin.rules] セクションによるルールの有効/無効制御と
[tool.paladin] の include / exclude による解析対象パス制御を実ファイルシステムで検証する。
"""

import os
from pathlib import Path

import pytest

from paladin.check import CheckOrchestratorProvider
from paladin.check.context import CheckContext
from paladin.foundation.error.error import ApplicationError


class TestIntegrationRuleDisabling:
    """[tool.paladin.rules] セクションによるルール無効化の統合テスト"""

    def test_check_正常系_rulesセクションでfalseに設定されたルールが適用されないこと(
        self, tmp_path: Path
    ):
        # Arrange: __all__ なしの __init__.py（require-all-export 違反のみ発生するコード）
        init_file = tmp_path / "__init__.py"
        init_file.write_text("x = 1\n", encoding="utf-8")
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("[tool.paladin.rules]\nrequire-all-export = false\n", encoding="utf-8")
        context = CheckContext(targets=(tmp_path,))
        original_cwd = Path.cwd()
        os.chdir(tmp_path)

        try:
            # Act
            report = CheckOrchestratorProvider().provide().orchestrate(context)
        finally:
            os.chdir(original_cwd)

        # Assert: require-all-export が無効化されているため exit_code == 0
        assert report.exit_code == 0

    def test_check_正常系_rulesセクションが存在しない場合全ルールが適用されること(
        self, tmp_path: Path
    ):
        # Arrange: __all__ なしの __init__.py（require-all-export 違反のみ発生するコード）
        init_file = tmp_path / "__init__.py"
        init_file.write_text("x = 1\n", encoding="utf-8")
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("[tool.paladin]\n", encoding="utf-8")
        context = CheckContext(targets=(tmp_path,))
        original_cwd = Path.cwd()
        os.chdir(tmp_path)

        try:
            # Act
            report = CheckOrchestratorProvider().provide().orchestrate(context)
        finally:
            os.chdir(original_cwd)

        # Assert: rules セクションなしで全ルールが有効のため違反あり
        assert report.exit_code == 1

    def test_check_正常系_rulesセクションでtrueに設定されたルールが通常通り適用されること(
        self, tmp_path: Path
    ):
        # Arrange: __all__ なしの __init__.py、require-all-export = true（明示的に有効）
        init_file = tmp_path / "__init__.py"
        init_file.write_text("x = 1\n", encoding="utf-8")
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("[tool.paladin.rules]\nrequire-all-export = true\n", encoding="utf-8")
        context = CheckContext(targets=(tmp_path,))
        original_cwd = Path.cwd()
        os.chdir(tmp_path)

        try:
            # Act
            report = CheckOrchestratorProvider().provide().orchestrate(context)
        finally:
            os.chdir(original_cwd)

        # Assert: true 指定は通常通り有効のため違反あり
        assert report.exit_code == 1


class TestIntegrationIncludeExclude:
    """[tool.paladin] の include / exclude による解析対象パス制御の統合テスト"""

    def test_check_正常系_includeで指定したパスのみ解析されること(self, tmp_path: Path):
        # Arrange: src/ 配下のみ include に指定し、other/ は解析されない
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        src_file = src_dir / "main.py"
        src_file.write_text("x = 1\n", encoding="utf-8")
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(f'[tool.paladin]\ninclude = ["{src_dir}"]\n', encoding="utf-8")
        # CLI ターゲット未指定（include から解決）
        context = CheckContext(targets=())
        original_cwd = Path.cwd()
        os.chdir(tmp_path)

        try:
            # Act
            report = CheckOrchestratorProvider().provide().orchestrate(context)
        finally:
            os.chdir(original_cwd)

        # Assert: src/ の main.py が解析され、違反なし
        assert report.exit_code == 0

    def test_check_正常系_excludeで指定したパスが除外されること(self, tmp_path: Path):
        # Arrange: __init__.py は require-all-export 違反あり、exclude で除外する
        init_file = tmp_path / "__init__.py"
        init_file.write_text("x = 1\n", encoding="utf-8")
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[tool.paladin]\nexclude = ["__init__.py"]\n', encoding="utf-8")
        context = CheckContext(targets=(tmp_path,))
        original_cwd = Path.cwd()
        os.chdir(tmp_path)

        try:
            # Act
            report = CheckOrchestratorProvider().provide().orchestrate(context)
        finally:
            os.chdir(original_cwd)

        # Assert: __init__.py が除外されるため違反なし
        assert report.exit_code == 0

    def test_check_正常系_CLIターゲット指定時にincludeが無視されること(self, tmp_path: Path):
        # Arrange: include に存在しないパスを指定し、CLI ターゲットを優先させる
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        src_file = src_dir / "main.py"
        src_file.write_text("x = 1\n", encoding="utf-8")
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[tool.paladin]\ninclude = ["/nonexistent/path"]\n', encoding="utf-8")
        # CLI ターゲット指定 → include は無視される
        context = CheckContext(targets=(src_dir,))
        original_cwd = Path.cwd()
        os.chdir(tmp_path)

        try:
            # Act
            report = CheckOrchestratorProvider().provide().orchestrate(context)
        finally:
            os.chdir(original_cwd)

        # Assert: CLI ターゲット（src/）が解析され、違反なし
        assert report.exit_code == 0

    def test_check_正常系_CLIターゲット指定時にもexcludeが適用されること(self, tmp_path: Path):
        # Arrange: CLI ターゲット指定かつ exclude で __init__.py を除外
        init_file = tmp_path / "__init__.py"
        init_file.write_text("x = 1\n", encoding="utf-8")
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[tool.paladin]\nexclude = ["__init__.py"]\n', encoding="utf-8")
        context = CheckContext(targets=(tmp_path,))
        original_cwd = Path.cwd()
        os.chdir(tmp_path)

        try:
            # Act
            report = CheckOrchestratorProvider().provide().orchestrate(context)
        finally:
            os.chdir(original_cwd)

        # Assert: exclude が適用され、__init__.py が除外されるため違反なし
        assert report.exit_code == 0

    def test_check_異常系_CLIターゲットもincludeも未指定の場合エラーになること(
        self, tmp_path: Path
    ):
        # Arrange: pyproject.toml に include なし、CLI ターゲットも未指定
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("[tool.paladin]\n", encoding="utf-8")
        context = CheckContext(targets=())
        original_cwd = Path.cwd()
        os.chdir(tmp_path)

        try:
            # Act / Assert: ApplicationError が発生する
            with pytest.raises(ApplicationError):
                CheckOrchestratorProvider().provide().orchestrate(context)
        finally:
            os.chdir(original_cwd)
