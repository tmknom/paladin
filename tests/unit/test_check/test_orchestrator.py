import json
from pathlib import Path

import pytest

from paladin.check.collector import FileCollector
from paladin.check.config import ProjectConfigLoader, RuleFilter
from paladin.check.context import CheckContext
from paladin.check.formatter import CheckFormatterFactory
from paladin.check.ignore import ViolationFilter
from paladin.check.orchestrator import CheckOrchestrator
from paladin.check.parser import AstParser
from paladin.check.path import PathExcluder, TargetResolver
from paladin.check.result import CheckReport
from paladin.check.types import OutputFormat
from paladin.foundation.error.error import ApplicationError
from paladin.foundation.fs.error import FileSystemError
from paladin.lint import RequireAllExportRule, RuleSet
from paladin.lint.types import Violation
from tests.unit.test_check.fakes import FakeRule, InMemoryFsReader


class TestCheckOrchestrator:
    """CheckOrchestratorクラスのテスト"""

    def test_orchestrate_正常系_列挙とAST生成の結果をCheckReportとして返すこと(
        self, tmp_path: Path
    ):
        # Arrange
        py_file = tmp_path / "main.py"
        py_file.write_text("x = 1\n")
        reader = InMemoryFsReader(contents={str(py_file.resolve()): "x = 1\n"})
        parser = AstParser(reader=reader)
        rule_set = RuleSet(rules=(RequireAllExportRule(),))
        config_loader = ProjectConfigLoader(
            reader=InMemoryFsReader(
                error=FileSystemError(message="not found", cause=Exception("not found"))
            )
        )
        orchestrator = CheckOrchestrator(
            collector=FileCollector(),
            parser=parser,
            rule_set=rule_set,
            formatter=CheckFormatterFactory(),
            violation_filter=ViolationFilter(),
            config_loader=config_loader,
            rule_filter=RuleFilter(),
            target_resolver=TargetResolver(),
            path_excluder=PathExcluder(),
        )
        context = CheckContext(targets=(tmp_path,))

        # Act
        result = orchestrator.orchestrate(context)

        # Assert
        assert isinstance(result, CheckReport)
        assert result.exit_code == 0

    def test_orchestrate_正常系_ルール適用結果をCheckReportに含めること(self, tmp_path: Path):
        # Arrange
        init_file = tmp_path / "__init__.py"
        init_file.write_text("from foo import bar\n")
        reader = InMemoryFsReader(contents={str(init_file.resolve()): "from foo import bar\n"})
        parser = AstParser(reader=reader)
        rule_set = RuleSet(rules=(RequireAllExportRule(),))
        config_loader = ProjectConfigLoader(
            reader=InMemoryFsReader(
                error=FileSystemError(message="not found", cause=Exception("not found"))
            )
        )
        orchestrator = CheckOrchestrator(
            collector=FileCollector(),
            parser=parser,
            rule_set=rule_set,
            formatter=CheckFormatterFactory(),
            violation_filter=ViolationFilter(),
            config_loader=config_loader,
            rule_filter=RuleFilter(),
            target_resolver=TargetResolver(),
            path_excluder=PathExcluder(),
        )
        context = CheckContext(targets=(tmp_path,))

        # Act
        result = orchestrator.orchestrate(context)

        # Assert
        assert isinstance(result, CheckReport)
        assert result.exit_code == 1

    def test_orchestrate_正常系_JSON形式でCheckReportを返すこと(self, tmp_path: Path):
        # Arrange
        py_file = tmp_path / "main.py"
        py_file.write_text("x = 1\n")
        reader = InMemoryFsReader(contents={str(py_file.resolve()): "x = 1\n"})
        parser = AstParser(reader=reader)
        rule_set = RuleSet(rules=(RequireAllExportRule(),))
        config_loader = ProjectConfigLoader(
            reader=InMemoryFsReader(
                error=FileSystemError(message="not found", cause=Exception("not found"))
            )
        )
        orchestrator = CheckOrchestrator(
            collector=FileCollector(),
            parser=parser,
            rule_set=rule_set,
            formatter=CheckFormatterFactory(),
            violation_filter=ViolationFilter(),
            config_loader=config_loader,
            rule_filter=RuleFilter(),
            target_resolver=TargetResolver(),
            path_excluder=PathExcluder(),
        )
        context = CheckContext(targets=(tmp_path,), format=OutputFormat.JSON)

        # Act
        report = orchestrator.orchestrate(context)

        # Assert
        assert isinstance(report, CheckReport)
        parsed = json.loads(report.text)
        assert "status" in parsed

    def test_orchestrate_正常系_TEXT形式でCheckReportを返すこと(self, tmp_path: Path):
        # Arrange
        py_file = tmp_path / "main.py"
        py_file.write_text("x = 1\n")
        reader = InMemoryFsReader(contents={str(py_file.resolve()): "x = 1\n"})
        parser = AstParser(reader=reader)
        rule_set = RuleSet(rules=(RequireAllExportRule(),))
        config_loader = ProjectConfigLoader(
            reader=InMemoryFsReader(
                error=FileSystemError(message="not found", cause=Exception("not found"))
            )
        )
        orchestrator = CheckOrchestrator(
            collector=FileCollector(),
            parser=parser,
            rule_set=rule_set,
            formatter=CheckFormatterFactory(),
            violation_filter=ViolationFilter(),
            config_loader=config_loader,
            rule_filter=RuleFilter(),
            target_resolver=TargetResolver(),
            path_excluder=PathExcluder(),
        )
        context = CheckContext(targets=(tmp_path,), format=OutputFormat.TEXT)

        # Act
        report = orchestrator.orchestrate(context)

        # Assert
        assert isinstance(report, CheckReport)
        assert "status: ok" in report.text

    def test_orchestrate_正常系_ignore_fileディレクティブで違反が除外されること(
        self, tmp_path: Path
    ):
        # Arrange
        init_file = tmp_path / "__init__.py"
        init_file.write_text("# paladin: ignore-file\nfrom foo import bar\n")
        reader = InMemoryFsReader(
            contents={str(init_file.resolve()): "# paladin: ignore-file\nfrom foo import bar\n"}
        )
        parser = AstParser(reader=reader)
        rule_set = RuleSet(rules=(RequireAllExportRule(),))
        config_loader = ProjectConfigLoader(
            reader=InMemoryFsReader(
                error=FileSystemError(message="not found", cause=Exception("not found"))
            )
        )
        orchestrator = CheckOrchestrator(
            collector=FileCollector(),
            parser=parser,
            rule_set=rule_set,
            formatter=CheckFormatterFactory(),
            violation_filter=ViolationFilter(),
            config_loader=config_loader,
            rule_filter=RuleFilter(),
            target_resolver=TargetResolver(),
            path_excluder=PathExcluder(),
        )
        context = CheckContext(targets=(tmp_path,))

        # Act
        result = orchestrator.orchestrate(context)

        # Assert
        assert isinstance(result, CheckReport)
        assert result.exit_code == 0

    def test_orchestrate_正常系_特定ルールignoreで該当ルールのみ除外されること(
        self, tmp_path: Path
    ):
        # Arrange
        init_file = tmp_path / "__init__.py"
        init_file.write_text("# paladin: ignore-file[require-all-export]\nfrom foo import bar\n")
        reader = InMemoryFsReader(
            contents={
                str(init_file.resolve()): (
                    "# paladin: ignore-file[require-all-export]\nfrom foo import bar\n"
                )
            }
        )
        parser = AstParser(reader=reader)
        rule_set = RuleSet(rules=(RequireAllExportRule(),))
        config_loader = ProjectConfigLoader(
            reader=InMemoryFsReader(
                error=FileSystemError(message="not found", cause=Exception("not found"))
            )
        )
        orchestrator = CheckOrchestrator(
            collector=FileCollector(),
            parser=parser,
            rule_set=rule_set,
            formatter=CheckFormatterFactory(),
            violation_filter=ViolationFilter(),
            config_loader=config_loader,
            rule_filter=RuleFilter(),
            target_resolver=TargetResolver(),
            path_excluder=PathExcluder(),
        )
        context = CheckContext(targets=(tmp_path,))

        # Act
        result = orchestrator.orchestrate(context)

        # Assert
        assert isinstance(result, CheckReport)
        assert result.exit_code == 0

    def test_orchestrate_正常系_直前コメントignoreで違反が除外されること(self, tmp_path: Path):
        # Arrange: FakeRule で line=2 の違反を返すよう設定する
        py_file = tmp_path / "example.py"
        source = "# paladin: ignore\nsome_code = 1\n"
        py_file.write_text(source)
        reader = InMemoryFsReader(contents={str(py_file.resolve()): source})
        parser = AstParser(reader=reader)
        violation = Violation(
            file=py_file.resolve(),
            line=2,
            column=0,
            rule_id="fake-rule",
            rule_name="Fake Rule",
            message="violation",
            reason="reason",
            suggestion="suggestion",
        )
        rule = FakeRule(violations=(violation,))
        rule_set = RuleSet(rules=(rule,))
        config_loader = ProjectConfigLoader(
            reader=InMemoryFsReader(
                error=FileSystemError(message="not found", cause=Exception("not found"))
            )
        )
        orchestrator = CheckOrchestrator(
            collector=FileCollector(),
            parser=parser,
            rule_set=rule_set,
            formatter=CheckFormatterFactory(),
            violation_filter=ViolationFilter(),
            config_loader=config_loader,
            rule_filter=RuleFilter(),
            target_resolver=TargetResolver(),
            path_excluder=PathExcluder(),
        )
        context = CheckContext(targets=(tmp_path,))

        # Act
        result = orchestrator.orchestrate(context)

        # Assert: # paladin: ignore の直後行 (line=2) の違反が除外される
        assert isinstance(result, CheckReport)
        assert result.exit_code == 0

    def test_orchestrate_正常系_特定ルール直前コメントignoreで該当ルールのみ除外されること(
        self, tmp_path: Path
    ):
        # Arrange: FakeRule で line=2 の違反を返すよう設定する
        py_file = tmp_path / "example.py"
        source = "# paladin: ignore[fake-rule]\nsome_code = 1\n"
        py_file.write_text(source)
        reader = InMemoryFsReader(contents={str(py_file.resolve()): source})
        parser = AstParser(reader=reader)
        violation = Violation(
            file=py_file.resolve(),
            line=2,
            column=0,
            rule_id="fake-rule",
            rule_name="Fake Rule",
            message="violation",
            reason="reason",
            suggestion="suggestion",
        )
        rule = FakeRule(violations=(violation,))
        rule_set = RuleSet(rules=(rule,))
        config_loader = ProjectConfigLoader(
            reader=InMemoryFsReader(
                error=FileSystemError(message="not found", cause=Exception("not found"))
            )
        )
        orchestrator = CheckOrchestrator(
            collector=FileCollector(),
            parser=parser,
            rule_set=rule_set,
            formatter=CheckFormatterFactory(),
            violation_filter=ViolationFilter(),
            config_loader=config_loader,
            rule_filter=RuleFilter(),
            target_resolver=TargetResolver(),
            path_excluder=PathExcluder(),
        )
        context = CheckContext(targets=(tmp_path,))

        # Act
        result = orchestrator.orchestrate(context)

        # Assert: # paladin: ignore[fake-rule] の直後行 (line=2) の該当ルール違反が除外される
        assert isinstance(result, CheckReport)
        assert result.exit_code == 0

    def test_orchestrate_正常系_設定ファイルのper_file_ignoresで違反が除外されること(
        self, tmp_path: Path
    ):
        # Arrange
        py_file = tmp_path / "example.py"
        py_file.write_text("x = 1\n")
        reader = InMemoryFsReader(contents={str(py_file.resolve()): "x = 1\n"})
        parser = AstParser(reader=reader)
        violation = Violation(
            file=py_file.resolve(),
            line=1,
            column=0,
            rule_id="fake-rule",
            rule_name="Fake Rule",
            message="violation",
            reason="reason",
            suggestion="suggestion",
        )
        rule = FakeRule(violations=(violation,))
        rule_set = RuleSet(rules=(rule,))
        toml_content = '[tool.paladin.per-file-ignores]\n"example.py" = ["fake-rule"]\n'
        config_loader = ProjectConfigLoader(reader=InMemoryFsReader(content=toml_content))
        orchestrator = CheckOrchestrator(
            collector=FileCollector(),
            parser=parser,
            rule_set=rule_set,
            formatter=CheckFormatterFactory(),
            violation_filter=ViolationFilter(),
            config_loader=config_loader,
            rule_filter=RuleFilter(),
            target_resolver=TargetResolver(),
            path_excluder=PathExcluder(),
        )
        context = CheckContext(targets=(tmp_path,))

        # Act
        result = orchestrator.orchestrate(context)

        # Assert: 設定ファイルの per-file-ignores で違反が除外される
        assert isinstance(result, CheckReport)
        assert result.exit_code == 0

    def test_orchestrate_正常系_ignore_rulesで指定ルールの違反が除外されること(
        self, tmp_path: Path
    ):
        # Arrange
        py_file = tmp_path / "example.py"
        py_file.write_text("x = 1\n")
        reader = InMemoryFsReader(contents={str(py_file.resolve()): "x = 1\n"})
        parser = AstParser(reader=reader)
        violation = Violation(
            file=py_file.resolve(),
            line=1,
            column=0,
            rule_id="fake-rule",
            rule_name="Fake Rule",
            message="violation",
            reason="reason",
            suggestion="suggestion",
        )
        rule = FakeRule(violations=(violation,))
        rule_set = RuleSet(rules=(rule,))
        config_loader = ProjectConfigLoader(
            reader=InMemoryFsReader(
                error=FileSystemError(message="not found", cause=Exception("not found"))
            )
        )
        orchestrator = CheckOrchestrator(
            collector=FileCollector(),
            parser=parser,
            rule_set=rule_set,
            formatter=CheckFormatterFactory(),
            violation_filter=ViolationFilter(),
            config_loader=config_loader,
            rule_filter=RuleFilter(),
            target_resolver=TargetResolver(),
            path_excluder=PathExcluder(),
        )
        context = CheckContext(targets=(tmp_path,), ignore_rules=frozenset({"fake-rule"}))

        # Act
        result = orchestrator.orchestrate(context)

        # Assert: ignore_rules で指定したルールの違反が除外される
        assert isinstance(result, CheckReport)
        assert result.exit_code == 0

    def test_orchestrate_正常系_設定ファイルignoreとコメントignoreが同時に適用されること(
        self, tmp_path: Path
    ):
        # Arrange
        py_file1 = tmp_path / "config_ignored.py"
        py_file1.write_text("x = 1\n")
        py_file2 = tmp_path / "comment_ignored.py"
        py_file2.write_text("# paladin: ignore-file\nx = 1\n")
        reader = InMemoryFsReader(
            contents={
                str(py_file1.resolve()): "x = 1\n",
                str(py_file2.resolve()): "# paladin: ignore-file\nx = 1\n",
            }
        )
        parser = AstParser(reader=reader)
        violation1 = Violation(
            file=py_file1.resolve(),
            line=1,
            column=0,
            rule_id="fake-rule",
            rule_name="Fake Rule",
            message="violation",
            reason="reason",
            suggestion="suggestion",
        )
        violation2 = Violation(
            file=py_file2.resolve(),
            line=1,
            column=0,
            rule_id="fake-rule",
            rule_name="Fake Rule",
            message="violation",
            reason="reason",
            suggestion="suggestion",
        )
        rule = FakeRule(violations=(violation1, violation2))
        rule_set = RuleSet(rules=(rule,))
        toml_content = '[tool.paladin.per-file-ignores]\n"config_ignored.py" = ["fake-rule"]\n'
        config_loader = ProjectConfigLoader(reader=InMemoryFsReader(content=toml_content))
        orchestrator = CheckOrchestrator(
            collector=FileCollector(),
            parser=parser,
            rule_set=rule_set,
            formatter=CheckFormatterFactory(),
            violation_filter=ViolationFilter(),
            config_loader=config_loader,
            rule_filter=RuleFilter(),
            target_resolver=TargetResolver(),
            path_excluder=PathExcluder(),
        )
        context = CheckContext(targets=(tmp_path,))

        # Act
        result = orchestrator.orchestrate(context)

        # Assert: 設定ファイル由来と コメント由来の両方の ignore が適用されて両違反が除外される
        assert isinstance(result, CheckReport)
        assert result.exit_code == 0

    def test_orchestrate_正常系_rulesセクションでfalseに設定されたルールの違反が出力されないこと(
        self, tmp_path: Path
    ):
        # Arrange
        py_file = tmp_path / "example.py"
        py_file.write_text("x = 1\n")
        reader = InMemoryFsReader(contents={str(py_file.resolve()): "x = 1\n"})
        parser = AstParser(reader=reader)
        violation = Violation(
            file=py_file.resolve(),
            line=1,
            column=0,
            rule_id="fake-rule",
            rule_name="Fake Rule",
            message="violation",
            reason="reason",
            suggestion="suggestion",
        )
        rule = FakeRule(rule_id="fake-rule", violations=(violation,))
        rule_set = RuleSet(rules=(rule,))
        toml_content = "[tool.paladin.rules]\nfake-rule = false\n"
        config_loader = ProjectConfigLoader(reader=InMemoryFsReader(content=toml_content))
        orchestrator = CheckOrchestrator(
            collector=FileCollector(),
            parser=parser,
            rule_set=rule_set,
            formatter=CheckFormatterFactory(),
            violation_filter=ViolationFilter(),
            config_loader=config_loader,
            rule_filter=RuleFilter(),
            target_resolver=TargetResolver(),
            path_excluder=PathExcluder(),
        )
        context = CheckContext(targets=(tmp_path,))

        # Act
        result = orchestrator.orchestrate(context)

        # Assert: ルール自体がスキップされるため違反なし
        assert isinstance(result, CheckReport)
        assert result.exit_code == 0

    def test_orchestrate_正常系_rulesセクションが存在しない場合全ルールが実行されること(
        self, tmp_path: Path
    ):
        # Arrange
        init_file = tmp_path / "__init__.py"
        init_file.write_text("from foo import bar\n")
        reader = InMemoryFsReader(contents={str(init_file.resolve()): "from foo import bar\n"})
        parser = AstParser(reader=reader)
        rule_set = RuleSet(rules=(RequireAllExportRule(),))
        config_loader = ProjectConfigLoader(
            reader=InMemoryFsReader(
                error=FileSystemError(message="not found", cause=Exception("not found"))
            )
        )
        orchestrator = CheckOrchestrator(
            collector=FileCollector(),
            parser=parser,
            rule_set=rule_set,
            formatter=CheckFormatterFactory(),
            violation_filter=ViolationFilter(),
            config_loader=config_loader,
            rule_filter=RuleFilter(),
            target_resolver=TargetResolver(),
            path_excluder=PathExcluder(),
        )
        context = CheckContext(targets=(tmp_path,))

        # Act
        result = orchestrator.orchestrate(context)

        # Assert: rules セクションなしで全ルールが実行され、違反あり
        assert isinstance(result, CheckReport)
        assert result.exit_code == 1

    def test_orchestrate_正常系_存在しないルールIDを指定しても処理が継続すること(
        self, tmp_path: Path
    ):
        # Arrange
        py_file = tmp_path / "main.py"
        py_file.write_text("x = 1\n")
        reader = InMemoryFsReader(contents={str(py_file.resolve()): "x = 1\n"})
        parser = AstParser(reader=reader)
        rule_set = RuleSet(rules=(RequireAllExportRule(),))
        toml_content = "[tool.paladin.rules]\nunknown-rule = false\n"
        config_loader = ProjectConfigLoader(reader=InMemoryFsReader(content=toml_content))
        orchestrator = CheckOrchestrator(
            collector=FileCollector(),
            parser=parser,
            rule_set=rule_set,
            formatter=CheckFormatterFactory(),
            violation_filter=ViolationFilter(),
            config_loader=config_loader,
            rule_filter=RuleFilter(),
            target_resolver=TargetResolver(),
            path_excluder=PathExcluder(),
        )
        context = CheckContext(targets=(tmp_path,))

        # Act: 警告が出るが処理は完了する
        result = orchestrator.orchestrate(context)

        # Assert: 処理が正常に完了する
        assert isinstance(result, CheckReport)

    def test_orchestrate_正常系_includeで指定したパスを解析対象とすること(self, tmp_path: Path):
        # Arrange
        py_file = tmp_path / "main.py"
        py_file.write_text("x = 1\n")
        reader = InMemoryFsReader(contents={str(py_file.resolve()): "x = 1\n"})
        parser = AstParser(reader=reader)
        rule_set = RuleSet(rules=(RequireAllExportRule(),))
        toml_content = f'[tool.paladin]\ninclude = ["{tmp_path}"]\n'
        config_loader = ProjectConfigLoader(reader=InMemoryFsReader(content=toml_content))
        orchestrator = CheckOrchestrator(
            collector=FileCollector(),
            parser=parser,
            rule_set=rule_set,
            formatter=CheckFormatterFactory(),
            violation_filter=ViolationFilter(),
            config_loader=config_loader,
            rule_filter=RuleFilter(),
            target_resolver=TargetResolver(),
            path_excluder=PathExcluder(),
        )
        # CLIターゲット未指定
        context = CheckContext(targets=())

        # Act
        result = orchestrator.orchestrate(context)

        # Assert: include のパスが解析対象になり、違反なしで終了
        assert isinstance(result, CheckReport)
        assert result.exit_code == 0

    def test_orchestrate_正常系_excludeパターンでファイルが除外されること(self, tmp_path: Path):
        # Arrange: 違反ファイルを exclude パターンで除外する
        py_file = tmp_path / "example.py"
        py_file.write_text("x = 1\n")
        reader = InMemoryFsReader(contents={str(py_file.resolve()): "x = 1\n"})
        parser = AstParser(reader=reader)
        violation = Violation(
            file=py_file.resolve(),
            line=1,
            column=0,
            rule_id="fake-rule",
            rule_name="Fake Rule",
            message="violation",
            reason="reason",
            suggestion="suggestion",
        )
        rule = FakeRule(rule_id="fake-rule", violations=(violation,))
        rule_set = RuleSet(rules=(rule,))
        toml_content = f'[tool.paladin]\nexclude = ["{py_file.name}"]\n'
        config_loader = ProjectConfigLoader(reader=InMemoryFsReader(content=toml_content))
        orchestrator = CheckOrchestrator(
            collector=FileCollector(),
            parser=parser,
            rule_set=rule_set,
            formatter=CheckFormatterFactory(),
            violation_filter=ViolationFilter(),
            config_loader=config_loader,
            rule_filter=RuleFilter(),
            target_resolver=TargetResolver(),
            path_excluder=PathExcluder(),
        )
        context = CheckContext(targets=(tmp_path,))

        # Act
        result = orchestrator.orchestrate(context)

        # Assert: exclude パターンで example.py が除外されるため違反なし
        assert isinstance(result, CheckReport)
        assert result.exit_code == 0

    def test_orchestrate_正常系_CLIターゲット指定時にincludeが無視されること(self, tmp_path: Path):
        # Arrange: include に存在しないパスを指定し、CLI ターゲットが有効なことを確認
        py_file = tmp_path / "main.py"
        py_file.write_text("x = 1\n")
        reader = InMemoryFsReader(contents={str(py_file.resolve()): "x = 1\n"})
        parser = AstParser(reader=reader)
        rule_set = RuleSet(rules=(RequireAllExportRule(),))
        toml_content = '[tool.paladin]\ninclude = ["/nonexistent/path"]\n'
        config_loader = ProjectConfigLoader(reader=InMemoryFsReader(content=toml_content))
        orchestrator = CheckOrchestrator(
            collector=FileCollector(),
            parser=parser,
            rule_set=rule_set,
            formatter=CheckFormatterFactory(),
            violation_filter=ViolationFilter(),
            config_loader=config_loader,
            rule_filter=RuleFilter(),
            target_resolver=TargetResolver(),
            path_excluder=PathExcluder(),
        )
        # CLI ターゲットが指定されているため include は無視される
        context = CheckContext(targets=(tmp_path,))

        # Act
        result = orchestrator.orchestrate(context)

        # Assert: CLI ターゲット（tmp_path）が解析され、違反なし
        assert isinstance(result, CheckReport)
        assert result.exit_code == 0

    def test_orchestrate_正常系_excludeはCLIターゲット指定時にも適用されること(
        self, tmp_path: Path
    ):
        # Arrange: CLI ターゲットを指定し、exclude で特定ファイルを除外する
        py_file = tmp_path / "excluded.py"
        py_file.write_text("x = 1\n")
        reader = InMemoryFsReader(contents={str(py_file.resolve()): "x = 1\n"})
        parser = AstParser(reader=reader)
        violation = Violation(
            file=py_file.resolve(),
            line=1,
            column=0,
            rule_id="fake-rule",
            rule_name="Fake Rule",
            message="violation",
            reason="reason",
            suggestion="suggestion",
        )
        rule = FakeRule(rule_id="fake-rule", violations=(violation,))
        rule_set = RuleSet(rules=(rule,))
        toml_content = f'[tool.paladin]\nexclude = ["{py_file.name}"]\n'
        config_loader = ProjectConfigLoader(reader=InMemoryFsReader(content=toml_content))
        orchestrator = CheckOrchestrator(
            collector=FileCollector(),
            parser=parser,
            rule_set=rule_set,
            formatter=CheckFormatterFactory(),
            violation_filter=ViolationFilter(),
            config_loader=config_loader,
            rule_filter=RuleFilter(),
            target_resolver=TargetResolver(),
            path_excluder=PathExcluder(),
        )
        context = CheckContext(targets=(tmp_path,))

        # Act
        result = orchestrator.orchestrate(context)

        # Assert: CLI ターゲット指定でも exclude が適用され、違反なし
        assert isinstance(result, CheckReport)
        assert result.exit_code == 0

    def test_orchestrate_異常系_CLIターゲットもincludeも未指定の場合ApplicationErrorを送出すること(
        self, tmp_path: Path
    ):
        # Arrange
        rule_set = RuleSet(rules=(RequireAllExportRule(),))
        config_loader = ProjectConfigLoader(
            reader=InMemoryFsReader(
                error=FileSystemError(message="not found", cause=Exception("not found"))
            )
        )
        parser = AstParser(reader=InMemoryFsReader(content=""))
        orchestrator = CheckOrchestrator(
            collector=FileCollector(),
            parser=parser,
            rule_set=rule_set,
            formatter=CheckFormatterFactory(),
            violation_filter=ViolationFilter(),
            config_loader=config_loader,
            rule_filter=RuleFilter(),
            target_resolver=TargetResolver(),
            path_excluder=PathExcluder(),
        )
        context = CheckContext(targets=())

        # Act / Assert: TargetResolver が ApplicationError を送出する
        with pytest.raises(ApplicationError):
            orchestrator.orchestrate(context)
