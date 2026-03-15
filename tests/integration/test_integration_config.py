"""設定ファイルによるルール制御の統合テスト

[tool.paladin.rules] セクションによるルールの有効/無効制御と
[tool.paladin] の include / exclude による解析対象パス制御を実ファイルシステムで検証する。
"""

import os
from pathlib import Path

import pytest

from paladin.check import CheckOrchestratorProvider
from paladin.check.context import CheckContext
from paladin.config import ProjectConfigLoader, TargetResolver
from paladin.foundation.error.error import ApplicationError
from paladin.foundation.fs.text import TextFileSystemReader


def _load_context(targets: tuple[Path, ...]) -> CheckContext:
    """pyproject.toml を読み込み CheckContext を構築するヘルパー"""
    config = ProjectConfigLoader(reader=TextFileSystemReader()).load()
    resolved_targets = TargetResolver().resolve(targets=targets, include=config.include)
    return CheckContext(
        targets=resolved_targets,
        exclude=config.exclude,
        rules=config.rules,
        per_file_ignores=config.per_file_ignores,
        rule_options=config.rule_options,
    )


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
        original_cwd = Path.cwd()
        os.chdir(tmp_path)

        try:
            context = _load_context((tmp_path,))
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
        original_cwd = Path.cwd()
        os.chdir(tmp_path)

        try:
            context = _load_context((tmp_path,))
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
        original_cwd = Path.cwd()
        os.chdir(tmp_path)

        try:
            context = _load_context((tmp_path,))
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
        original_cwd = Path.cwd()
        os.chdir(tmp_path)

        try:
            # CLI ターゲット未指定（include から解決）
            context = _load_context(())
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
        original_cwd = Path.cwd()
        os.chdir(tmp_path)

        try:
            context = _load_context((tmp_path,))
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
        original_cwd = Path.cwd()
        os.chdir(tmp_path)

        try:
            # CLI ターゲット指定 → include は無視される
            context = _load_context((src_dir,))
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
        original_cwd = Path.cwd()
        os.chdir(tmp_path)

        try:
            context = _load_context((tmp_path,))
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
        original_cwd = Path.cwd()
        os.chdir(tmp_path)

        try:
            # Act / Assert: TargetResolver が ApplicationError を送出する
            with pytest.raises(ApplicationError):
                _load_context(())
        finally:
            os.chdir(original_cwd)


class TestIntegrationRuleOptions:
    """[tool.paladin.rule."<rule-id>"] セクションによるルール個別設定の統合テスト"""

    def test_check_正常系_ruleセクションのroot_packagesでサードパーティ判定が変更されること(
        self, tmp_path: Path
    ):
        # Arrange: custom_pkg からのインポートを含む .py ファイル
        src_file = tmp_path / "main.py"
        src_file.write_text("from custom_pkg import something\n", encoding="utf-8")
        # custom_pkg を root_packages に追加する設定
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            '[tool.paladin.rule."require-qualified-third-party"]\n'
            'root-packages = ["paladin", "tests", "custom_pkg"]\n',
            encoding="utf-8",
        )
        original_cwd = Path.cwd()
        os.chdir(tmp_path)

        try:
            context = _load_context((tmp_path,))
            config = ProjectConfigLoader(reader=TextFileSystemReader()).load()
            # Act
            report = (
                CheckOrchestratorProvider()
                .provide(rule_options=config.rule_options)
                .orchestrate(context)
            )
        finally:
            os.chdir(original_cwd)

        # Assert: custom_pkg が root_packages に含まれるため違反なし
        assert report.exit_code == 0

    def test_check_正常系_ruleセクション未指定時にデフォルトのroot_packagesが使われること(
        self, tmp_path: Path
    ):
        # Arrange: typer からのインポートを含む .py ファイル（サードパーティ違反）
        src_file = tmp_path / "main.py"
        src_file.write_text("from typer import Typer\n", encoding="utf-8")
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("[tool.paladin]\n", encoding="utf-8")
        original_cwd = Path.cwd()
        os.chdir(tmp_path)

        try:
            config = ProjectConfigLoader(reader=TextFileSystemReader()).load()
            context = _load_context((tmp_path,))
            # Act
            report = (
                CheckOrchestratorProvider()
                .provide(rule_options=config.rule_options)
                .orchestrate(context)
            )
        finally:
            os.chdir(original_cwd)

        # Assert: デフォルトの root_packages では typer がサードパーティ扱いのため違反あり
        assert report.exit_code == 1

    def test_check_正常系_存在しないルールIDのruleセクションが警告のみで無視されること(
        self, tmp_path: Path
    ):
        # Arrange: 違反なしのシンプルな .py ファイル
        src_file = tmp_path / "main.py"
        src_file.write_text("x = 1\n", encoding="utf-8")
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            '[tool.paladin.rule."nonexistent-rule"]\nsome-param = "value"\n',
            encoding="utf-8",
        )
        original_cwd = Path.cwd()
        os.chdir(tmp_path)

        try:
            config = ProjectConfigLoader(reader=TextFileSystemReader()).load()
            context = _load_context((tmp_path,))
            # Act: 未知ルール ID は警告のみで処理は続行される
            report = (
                CheckOrchestratorProvider()
                .provide(rule_options=config.rule_options)
                .orchestrate(context)
            )
        finally:
            os.chdir(original_cwd)

        # Assert: 処理が正常に完了していること
        assert report.exit_code == 0
