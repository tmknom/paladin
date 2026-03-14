"""設定ファイルによるルール制御の統合テスト

[tool.paladin.rules] セクションによるルールの有効/無効制御を実ファイルシステムで検証する。
"""

import os
from pathlib import Path

from paladin.check import CheckOrchestratorProvider
from paladin.check.context import CheckContext


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
