from pathlib import Path

import pytest

from paladin.check.config import ConfigIgnoreResolver, RuleFilter
from paladin.config import PerFileIgnoreEntry, ProjectConfig
from tests.unit.test_check.fakes import FakeRule


class TestRuleFilter:
    def test_resolve_disabled_rules_正常系_falseに設定されたルールIDを返すこと(self):
        # Arrange
        config = ProjectConfig(rules={"no-relative-import": False, "require-all-export": True})
        known_rule_ids = frozenset({"no-relative-import", "require-all-export"})
        rule_filter = RuleFilter()

        # Act
        result = rule_filter.resolve_disabled_rules(config.rules, known_rule_ids)

        # Assert
        assert result == frozenset({"no-relative-import"})

    def test_resolve_disabled_rules_正常系_全ルールtrueの場合空のfrozensetを返すこと(self):
        # Arrange
        config = ProjectConfig(rules={"no-relative-import": True, "require-all-export": True})
        known_rule_ids = frozenset({"no-relative-import", "require-all-export"})
        rule_filter = RuleFilter()

        # Act
        result = rule_filter.resolve_disabled_rules(config.rules, known_rule_ids)

        # Assert
        assert result == frozenset()

    def test_resolve_disabled_rules_エッジケース_空のrulesで空のfrozensetを返すこと(self):
        # Arrange
        config = ProjectConfig(rules={})
        known_rule_ids = frozenset({"no-relative-import", "require-all-export"})
        rule_filter = RuleFilter()

        # Act
        result = rule_filter.resolve_disabled_rules(config.rules, known_rule_ids)

        # Assert
        assert result == frozenset()

    def test_resolve_disabled_rules_エッジケース_存在しないルールIDで警告を出力して無視すること(
        self, caplog: pytest.LogCaptureFixture
    ):
        # Arrange
        config = ProjectConfig(rules={"unknown-rule": False})
        known_rule_ids = frozenset({"require-all-export"})
        rule_filter = RuleFilter()

        # Act
        with caplog.at_level("WARNING"):
            result = rule_filter.resolve_disabled_rules(config.rules, known_rule_ids)

        # Assert
        assert "unknown-rule" not in result
        assert "unknown-rule" in caplog.text

    def test_resolve_disabled_rules_正常系_複数ルールをfalseに設定した場合すべて返すこと(self):
        # Arrange
        config = ProjectConfig(rules={"no-relative-import": False, "require-all-export": False})
        known_rule_ids = frozenset({"no-relative-import", "require-all-export"})
        rule_filter = RuleFilter()

        # Act
        result = rule_filter.resolve_disabled_rules(config.rules, known_rule_ids)

        # Assert
        assert result == frozenset({"no-relative-import", "require-all-export"})

    def test_filter_正常系_disabled_rule_idsに該当するルールを除外すること(self):
        # Arrange
        rule_a = FakeRule(rule_id="rule-a")
        rule_b = FakeRule(rule_id="rule-b")
        rules = (rule_a, rule_b)
        rule_filter = RuleFilter()

        # Act
        result = rule_filter.filter(rules, disabled_rule_ids=frozenset({"rule-a"}))

        # Assert
        assert len(result) == 1
        assert result[0].meta.rule_id == "rule-b"

    def test_filter_エッジケース_空のdisabled_rule_idsで全ルールを返すこと(self):
        # Arrange
        rule_a = FakeRule(rule_id="rule-a")
        rule_b = FakeRule(rule_id="rule-b")
        rules = (rule_a, rule_b)
        rule_filter = RuleFilter()

        # Act
        result = rule_filter.filter(rules, disabled_rule_ids=frozenset())

        # Assert
        assert len(result) == 2

    def test_filter_エッジケース_全ルールが無効の場合空タプルを返すこと(self):
        # Arrange
        rule_a = FakeRule(rule_id="rule-a")
        rule_b = FakeRule(rule_id="rule-b")
        rules = (rule_a, rule_b)
        rule_filter = RuleFilter()

        # Act
        result = rule_filter.filter(rules, disabled_rule_ids=frozenset({"rule-a", "rule-b"}))

        # Assert
        assert result == ()


class TestConfigIgnoreResolver:
    def test_resolve_正常系_glob_パターンにマッチするファイルのFileIgnoreDirectiveを返すこと(self):
        # Arrange
        entry = PerFileIgnoreEntry(
            pattern="tests/**",
            rule_ids=frozenset({"R-001"}),
            ignore_all=False,
        )
        config = ProjectConfig(per_file_ignores=(entry,))
        file_paths = (Path("tests/test_main.py"),)
        resolver = ConfigIgnoreResolver()

        # Act
        result = resolver.resolve(per_file_ignores=config.per_file_ignores, file_paths=file_paths)

        # Assert
        assert len(result) == 1
        directive = result[0]
        assert directive.file_path == Path("tests/test_main.py")
        assert directive.ignored_rules == frozenset({"R-001"})
        assert directive.ignore_all is False

    def test_resolve_正常系_ignore_allパターンで全ルールignoreのDirectiveを返すこと(self):
        # Arrange
        entry = PerFileIgnoreEntry(
            pattern="tests/**",
            rule_ids=frozenset(),
            ignore_all=True,
        )
        config = ProjectConfig(per_file_ignores=(entry,))
        file_paths = (Path("tests/test_main.py"),)
        resolver = ConfigIgnoreResolver()

        # Act
        result = resolver.resolve(per_file_ignores=config.per_file_ignores, file_paths=file_paths)

        # Assert
        assert len(result) == 1
        directive = result[0]
        assert directive.file_path == Path("tests/test_main.py")
        assert directive.ignore_all is True

    def test_resolve_正常系_複数パターンが同一ファイルにマッチした場合ルールの和集合になること(
        self,
    ):
        # Arrange
        entry1 = PerFileIgnoreEntry(
            pattern="tests/**",
            rule_ids=frozenset({"R-001"}),
            ignore_all=False,
        )
        entry2 = PerFileIgnoreEntry(
            pattern="tests/test_main.py",
            rule_ids=frozenset({"R-002"}),
            ignore_all=False,
        )
        config = ProjectConfig(per_file_ignores=(entry1, entry2))
        file_paths = (Path("tests/test_main.py"),)
        resolver = ConfigIgnoreResolver()

        # Act
        result = resolver.resolve(per_file_ignores=config.per_file_ignores, file_paths=file_paths)

        # Assert
        assert len(result) == 1
        directive = result[0]
        assert directive.ignored_rules == frozenset({"R-001", "R-002"})
        assert directive.ignore_all is False

    def test_resolve_正常系_マッチしないファイルはDirectiveに含まれないこと(self):
        # Arrange
        entry = PerFileIgnoreEntry(
            pattern="tests/**",
            rule_ids=frozenset({"R-001"}),
            ignore_all=False,
        )
        config = ProjectConfig(per_file_ignores=(entry,))
        file_paths = (Path("src/main.py"),)
        resolver = ConfigIgnoreResolver()

        # Act
        result = resolver.resolve(per_file_ignores=config.per_file_ignores, file_paths=file_paths)

        # Assert
        assert result == ()

    def test_resolve_エッジケース_空のProjectConfigで空タプルを返すこと(self):
        # Arrange
        config = ProjectConfig()
        file_paths = (Path("tests/test_main.py"),)
        resolver = ConfigIgnoreResolver()

        # Act
        result = resolver.resolve(per_file_ignores=config.per_file_ignores, file_paths=file_paths)

        # Assert
        assert result == ()

    def test_resolve_エッジケース_空のfile_pathsで空タプルを返すこと(self):
        # Arrange
        entry = PerFileIgnoreEntry(
            pattern="tests/**",
            rule_ids=frozenset({"R-001"}),
            ignore_all=False,
        )
        config = ProjectConfig(per_file_ignores=(entry,))
        file_paths: tuple[Path, ...] = ()
        resolver = ConfigIgnoreResolver()

        # Act
        result = resolver.resolve(per_file_ignores=config.per_file_ignores, file_paths=file_paths)

        # Assert
        assert result == ()

    def test_resolve_正常系_ディレクトリパターンが絶対パスにマッチすること(self):
        # Arrange
        entry = PerFileIgnoreEntry(
            pattern="tests/**",
            rule_ids=frozenset({"R-001"}),
            ignore_all=False,
        )
        config = ProjectConfig(per_file_ignores=(entry,))
        file_paths = (Path("/Users/owner/code/project/tests/test_main.py"),)
        resolver = ConfigIgnoreResolver()

        # Act
        result = resolver.resolve(per_file_ignores=config.per_file_ignores, file_paths=file_paths)

        # Assert
        assert len(result) == 1
        directive = result[0]
        assert directive.file_path == Path("/Users/owner/code/project/tests/test_main.py")
        assert directive.ignored_rules == frozenset({"R-001"})

    def test_resolve_正常系_ディレクトリパターンがネストした絶対パスにマッチすること(self):
        # Arrange
        entry = PerFileIgnoreEntry(
            pattern="tests/**",
            rule_ids=frozenset({"R-001"}),
            ignore_all=False,
        )
        config = ProjectConfig(per_file_ignores=(entry,))
        file_paths = (Path("/Users/owner/code/project/tests/unit/test_check/test_main.py"),)
        resolver = ConfigIgnoreResolver()

        # Act
        result = resolver.resolve(per_file_ignores=config.per_file_ignores, file_paths=file_paths)

        # Assert
        assert len(result) == 1
        directive = result[0]
        assert directive.file_path == Path(
            "/Users/owner/code/project/tests/unit/test_check/test_main.py"
        )
        assert directive.ignored_rules == frozenset({"R-001"})

    def test_resolve_正常系_ディレクトリパターンが絶対パスのマッチしないファイルを除外すること(
        self,
    ):
        # Arrange
        entry = PerFileIgnoreEntry(
            pattern="tests/**",
            rule_ids=frozenset({"R-001"}),
            ignore_all=False,
        )
        config = ProjectConfig(per_file_ignores=(entry,))
        file_paths = (Path("/Users/owner/code/project/src/main.py"),)
        resolver = ConfigIgnoreResolver()

        # Act
        result = resolver.resolve(per_file_ignores=config.per_file_ignores, file_paths=file_paths)

        # Assert
        assert result == ()

    def test_resolve_正常系_複数ディレクトリパターンが異なる絶対パスにマッチすること(self):
        # Arrange
        entry1 = PerFileIgnoreEntry(
            pattern="tests/**",
            rule_ids=frozenset({"R-001"}),
            ignore_all=False,
        )
        entry2 = PerFileIgnoreEntry(
            pattern="scripts/**",
            rule_ids=frozenset({"R-002"}),
            ignore_all=False,
        )
        config = ProjectConfig(per_file_ignores=(entry1, entry2))
        file_paths = (
            Path("/abs/tests/unit/test_main.py"),
            Path("/abs/scripts/deploy.py"),
            Path("/abs/src/main.py"),
        )
        resolver = ConfigIgnoreResolver()

        # Act
        result = resolver.resolve(per_file_ignores=config.per_file_ignores, file_paths=file_paths)

        # Assert
        assert len(result) == 2
        paths = {d.file_path for d in result}
        assert paths == {
            Path("/abs/tests/unit/test_main.py"),
            Path("/abs/scripts/deploy.py"),
        }

    def test_resolve_正常系_ディレクトリパターンのignore_allが絶対パスで機能すること(self):
        # Arrange
        entry = PerFileIgnoreEntry(
            pattern="tests/**",
            rule_ids=frozenset(),
            ignore_all=True,
        )
        config = ProjectConfig(per_file_ignores=(entry,))
        file_paths = (Path("/abs/tests/unit/test_main.py"),)
        resolver = ConfigIgnoreResolver()

        # Act
        result = resolver.resolve(per_file_ignores=config.per_file_ignores, file_paths=file_paths)

        # Assert
        assert len(result) == 1
        assert result[0].ignore_all is True

    def test_resolve_正常系_init_py固有パターンが絶対パスでマッチすること(self):
        # Arrange
        entry = PerFileIgnoreEntry(
            pattern="tests/**/__init__.py",
            rule_ids=frozenset({"R-001"}),
            ignore_all=False,
        )
        config = ProjectConfig(per_file_ignores=(entry,))
        file_paths = (
            Path("/abs/tests/__init__.py"),
            Path("/abs/tests/unit/__init__.py"),
            Path("/abs/tests/unit/test_main.py"),
        )
        resolver = ConfigIgnoreResolver()

        # Act
        result = resolver.resolve(per_file_ignores=config.per_file_ignores, file_paths=file_paths)

        # Assert
        assert len(result) == 2
        paths = {d.file_path for d in result}
        assert paths == {
            Path("/abs/tests/__init__.py"),
            Path("/abs/tests/unit/__init__.py"),
        }

    def test_resolve_正常系_ダブルスター始まりのパターンが絶対パスにマッチすること(self):
        # Arrange: パターンが既に **/ で始まっている場合もマッチすること
        entry = PerFileIgnoreEntry(
            pattern="**/tests/**",
            rule_ids=frozenset({"R-001"}),
            ignore_all=False,
        )
        config = ProjectConfig(per_file_ignores=(entry,))
        file_paths = (Path("/abs/tests/unit/test_main.py"),)
        resolver = ConfigIgnoreResolver()

        # Act
        result = resolver.resolve(per_file_ignores=config.per_file_ignores, file_paths=file_paths)

        # Assert
        assert len(result) == 1
        assert result[0].ignored_rules == frozenset({"R-001"})
