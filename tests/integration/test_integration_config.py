"""設定ファイルによるルール制御の統合テスト

[tool.paladin.rules] セクションによるルールの有効/無効制御と
[tool.paladin] の include / exclude による解析対象パス制御を実ファイルシステムで検証する。
"""

import os
from pathlib import Path

import pytest

from paladin.check import CheckOrchestratorProvider
from paladin.check.context import CheckContext
from paladin.config import ProjectConfig, ProjectConfigLoader, TargetResolver
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
        overrides=config.overrides,
    )


def _load_config_and_context(
    targets: tuple[Path, ...],
) -> tuple[CheckContext, ProjectConfig]:
    """pyproject.toml を読み込み CheckContext と ProjectConfig を返すヘルパー

    rule_options / project_name を provide() に渡す必要があるテストで使用する。
    """
    config = ProjectConfigLoader(reader=TextFileSystemReader()).load()
    resolved_targets = TargetResolver().resolve(targets=targets, include=config.include)
    context = CheckContext(
        targets=resolved_targets,
        exclude=config.exclude,
        rules=config.rules,
        per_file_ignores=config.per_file_ignores,
        rule_options=config.rule_options,
        overrides=config.overrides,
    )
    return context, config


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
            context, config = _load_config_and_context((tmp_path,))
            # Act
            report = (
                CheckOrchestratorProvider()
                .provide(rule_options=config.rule_options, project_name=config.project_name)
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
            context, config = _load_config_and_context((tmp_path,))
            # Act
            report = (
                CheckOrchestratorProvider()
                .provide(rule_options=config.rule_options, project_name=config.project_name)
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
            context, config = _load_config_and_context((tmp_path,))
            # Act: 未知ルール ID は警告のみで処理は続行される
            report = (
                CheckOrchestratorProvider()
                .provide(rule_options=config.rule_options, project_name=config.project_name)
                .orchestrate(context)
            )
        finally:
            os.chdir(original_cwd)

        # Assert: 処理が正常に完了していること
        assert report.exit_code == 0

    def test_check_正常系_project_nameからデフォルトroot_packagesが動的に解決されること(
        self, tmp_path: Path
    ):
        # Arrange: myapp からのインポートを含む .py ファイル
        src_file = tmp_path / "main.py"
        src_file.write_text("from myapp.foo import bar\n", encoding="utf-8")
        # [project] name = "myapp" → root_packages = ("myapp", "tests")
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            '[project]\nname = "myapp"\n\n[tool.paladin]\n',
            encoding="utf-8",
        )
        original_cwd = Path.cwd()
        os.chdir(tmp_path)

        try:
            context, config = _load_config_and_context((tmp_path,))
            # Act
            report = (
                CheckOrchestratorProvider()
                .provide(rule_options=config.rule_options, project_name=config.project_name)
                .orchestrate(context)
            )
        finally:
            os.chdir(original_cwd)

        # Assert: myapp が動的に root_packages に含まれるため違反なし
        assert report.exit_code == 0

    def test_check_正常系_project_nameのハイフンが正規化されてroot_packagesに使われること(
        self, tmp_path: Path
    ):
        # Arrange: [project] name = "my-app" → 正規化後 "my_app" が root_packages に入る
        src_file = tmp_path / "main.py"
        src_file.write_text("from my_app.foo import bar\n", encoding="utf-8")
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            '[project]\nname = "my-app"\n\n[tool.paladin]\n',
            encoding="utf-8",
        )
        original_cwd = Path.cwd()
        os.chdir(tmp_path)

        try:
            context, config = _load_config_and_context((tmp_path,))
            # Act
            report = (
                CheckOrchestratorProvider()
                .provide(rule_options=config.rule_options, project_name=config.project_name)
                .orchestrate(context)
            )
        finally:
            os.chdir(original_cwd)

        # Assert: my_app（正規化後）が root_packages に含まれるため違反なし
        assert report.exit_code == 0

    def test_check_正常系_rule_optionsのroot_packagesがproject_nameより優先されること(
        self, tmp_path: Path
    ):
        # Arrange: [project] name = "myapp" だが rule_options で root-packages を明示指定
        src_file = tmp_path / "main.py"
        src_file.write_text("from explicit_pkg.foo import bar\n", encoding="utf-8")
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            '[project]\nname = "myapp"\n\n'
            '[tool.paladin.rule."require-qualified-third-party"]\n'
            'root-packages = ["explicit_pkg"]\n',
            encoding="utf-8",
        )
        original_cwd = Path.cwd()
        os.chdir(tmp_path)

        try:
            context, config = _load_config_and_context((tmp_path,))
            # Act
            report = (
                CheckOrchestratorProvider()
                .provide(rule_options=config.rule_options, project_name=config.project_name)
                .orchestrate(context)
            )
        finally:
            os.chdir(original_cwd)

        # Assert: rule_options の root-packages が優先されるため explicit_pkg は違反なし
        assert report.exit_code == 0

    def test_check_正常系_projectセクションがない場合testsのみがデフォルトroot_packagesになること(
        self, tmp_path: Path
    ):
        # Arrange: [project] セクションなし → root_packages = ("tests",)
        src_file = tmp_path / "main.py"
        src_file.write_text("from tests.foo import bar\n", encoding="utf-8")
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("[tool.paladin]\n", encoding="utf-8")
        original_cwd = Path.cwd()
        os.chdir(tmp_path)

        try:
            context, config = _load_config_and_context((tmp_path,))
            # Act
            report = (
                CheckOrchestratorProvider()
                .provide(rule_options=config.rule_options, project_name=config.project_name)
                .orchestrate(context)
            )
        finally:
            os.chdir(original_cwd)

        # Assert: tests は root_packages に含まれるため違反なし
        assert report.exit_code == 0


class TestIntegrationOverrides:
    """[[tool.paladin.overrides]] セクションによるディレクトリ別ルール設定の統合テスト"""

    def test_check_正常系_overridesでテストディレクトリのルールを無効化できること(
        self, tmp_path: Path
    ):
        # Arrange: tests/ 配下の __init__.py は require-all-export 違反あり
        # overrides で tests/** に require-all-export = false を設定
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        init_file = tests_dir / "__init__.py"
        init_file.write_text("x = 1\n", encoding="utf-8")
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            "[[tool.paladin.overrides]]\n"
            'files = ["tests/**"]\n'
            "\n"
            "[tool.paladin.overrides.rules]\n"
            "require-all-export = false\n",
            encoding="utf-8",
        )
        original_cwd = Path.cwd()
        os.chdir(tmp_path)

        try:
            context = _load_context((tmp_path,))
            # Act
            report = CheckOrchestratorProvider().provide().orchestrate(context)
        finally:
            os.chdir(original_cwd)

        # Assert: tests/ 配下の require-all-export が無効化されるため exit_code == 0
        assert report.exit_code == 0

    def test_check_正常系_overridesでマッチしないファイルにはトップレベル設定が適用されること(
        self, tmp_path: Path
    ):
        # Arrange: src/ の __init__.py は require-all-export 違反あり（overrides の対象外）
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        src_init = src_dir / "__init__.py"
        src_init.write_text("x = 1\n", encoding="utf-8")
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        tests_init = tests_dir / "__init__.py"
        tests_init.write_text("x = 1\n", encoding="utf-8")
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            "[[tool.paladin.overrides]]\n"
            'files = ["tests/**"]\n'
            "\n"
            "[tool.paladin.overrides.rules]\n"
            "require-all-export = false\n",
            encoding="utf-8",
        )
        original_cwd = Path.cwd()
        os.chdir(tmp_path)

        try:
            context = _load_context((tmp_path,))
            # Act
            report = CheckOrchestratorProvider().provide().orchestrate(context)
        finally:
            os.chdir(original_cwd)

        # Assert: src/ の __init__.py は overrides 対象外のため違反あり
        assert report.exit_code == 1

    def test_check_正常系_overridesが未定義の場合全ファイルにトップレベル設定が適用されること(
        self, tmp_path: Path
    ):
        # Arrange: overrides セクションなし → 全ファイルにトップレベルのルールが適用される
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

        # Assert: require-all-export が有効のため違反あり
        assert report.exit_code == 1

    def test_check_正常系_複数overridesで後勝ちが正しく動作すること(self, tmp_path: Path):
        # Arrange: tests/unit/ 配下のファイルに2つのオーバーライドが適用される
        # override1: tests/** で require-all-export = false
        # override2: tests/unit/** で require-all-export = true（後勝ち）
        unit_dir = tmp_path / "tests" / "unit"
        unit_dir.mkdir(parents=True)
        unit_init = unit_dir / "__init__.py"
        unit_init.write_text("x = 1\n", encoding="utf-8")
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            "[[tool.paladin.overrides]]\n"
            'files = ["tests/**"]\n'
            "\n"
            "[tool.paladin.overrides.rules]\n"
            "require-all-export = false\n"
            "\n"
            "[[tool.paladin.overrides]]\n"
            'files = ["tests/unit/**"]\n'
            "\n"
            "[tool.paladin.overrides.rules]\n"
            "require-all-export = true\n",
            encoding="utf-8",
        )
        original_cwd = Path.cwd()
        os.chdir(tmp_path)

        try:
            context = _load_context((tmp_path,))
            # Act
            report = CheckOrchestratorProvider().provide().orchestrate(context)
        finally:
            os.chdir(original_cwd)

        # Assert: override2 が後勝ちで require-all-export = true → 違反あり
        assert report.exit_code == 1
