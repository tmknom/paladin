from pathlib import Path

from paladin.check.config import (
    ConfigIgnoreResolver,
    PerFileIgnoreEntry,
    ProjectConfig,
    ProjectConfigLoader,
)
from paladin.foundation.fs.error import FileSystemError
from tests.unit.test_check.fakes import InMemoryFsReader


class TestPerFileIgnoreEntry:
    def test_PerFileIgnoreEntry_正常系_インスタンスを生成できること(self):
        # Arrange / Act
        entry = PerFileIgnoreEntry(
            pattern="tests/**",
            rule_ids=frozenset({"R-001", "R-002"}),
            ignore_all=False,
        )

        # Assert
        assert entry.pattern == "tests/**"
        assert entry.rule_ids == frozenset({"R-001", "R-002"})
        assert entry.ignore_all is False


class TestProjectConfig:
    def test_ProjectConfig_正常系_デフォルト値でインスタンスを生成できること(self):
        # Arrange / Act
        config = ProjectConfig()

        # Assert
        assert config.per_file_ignores == ()

    def test_ProjectConfig_正常系_per_file_ignoresを保持できること(self):
        # Arrange
        entry = PerFileIgnoreEntry(
            pattern="tests/**",
            rule_ids=frozenset({"R-001"}),
            ignore_all=False,
        )

        # Act
        config = ProjectConfig(per_file_ignores=(entry,))

        # Assert
        assert len(config.per_file_ignores) == 1
        assert config.per_file_ignores[0] == entry


class TestProjectConfigLoader:
    def test_load_正常系_per_file_ignoresを含むProjectConfigを返すこと(self):
        # Arrange
        toml_content = """\
[tool.paladin.per-file-ignores]
"tests/**" = ["R-001", "R-002"]
"""
        reader = InMemoryFsReader(content=toml_content)
        loader = ProjectConfigLoader(reader=reader)

        # Act
        result = loader.load()

        # Assert
        assert len(result.per_file_ignores) == 1
        entry = result.per_file_ignores[0]
        assert entry.pattern == "tests/**"
        assert entry.rule_ids == frozenset({"R-001", "R-002"})
        assert entry.ignore_all is False

    def test_load_正常系_複数パターンを読み込めること(self):
        # Arrange
        toml_content = """\
[tool.paladin.per-file-ignores]
"tests/**" = ["R-001"]
"scripts/**" = ["R-002", "R-003"]
"""
        reader = InMemoryFsReader(content=toml_content)
        loader = ProjectConfigLoader(reader=reader)

        # Act
        result = loader.load()

        # Assert
        assert len(result.per_file_ignores) == 2
        patterns = {e.pattern for e in result.per_file_ignores}
        assert patterns == {"tests/**", "scripts/**"}

    def test_load_正常系_ワイルドカード指定でignore_allがTrueになること(self):
        # Arrange
        toml_content = """\
[tool.paladin.per-file-ignores]
"tests/**" = ["*"]
"""
        reader = InMemoryFsReader(content=toml_content)
        loader = ProjectConfigLoader(reader=reader)

        # Act
        result = loader.load()

        # Assert
        assert len(result.per_file_ignores) == 1
        entry = result.per_file_ignores[0]
        assert entry.ignore_all is True
        assert entry.rule_ids == frozenset()

    def test_load_エッジケース_pyproject_tomlが存在しない場合デフォルトProjectConfigを返すこと(
        self,
    ):
        # Arrange
        reader = InMemoryFsReader(
            error=FileSystemError(message="ファイルが見つかりません", cause=Exception("not found"))
        )
        loader = ProjectConfigLoader(reader=reader)

        # Act
        result = loader.load()

        # Assert
        assert result == ProjectConfig()
        assert result.per_file_ignores == ()

    def test_load_エッジケース_tool_paladinセクションがない場合デフォルトProjectConfigを返すこと(
        self,
    ):
        # Arrange
        toml_content = """\
[tool.other]
key = "value"
"""
        reader = InMemoryFsReader(content=toml_content)
        loader = ProjectConfigLoader(reader=reader)

        # Act
        result = loader.load()

        # Assert
        assert result == ProjectConfig()

    def test_load_エッジケース_per_file_ignoresがない場合デフォルトProjectConfigを返すこと(self):
        # Arrange
        toml_content = """\
[tool.paladin]
other_key = "value"
"""
        reader = InMemoryFsReader(content=toml_content)
        loader = ProjectConfigLoader(reader=reader)

        # Act
        result = loader.load()

        # Assert
        assert result == ProjectConfig()


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
        result = resolver.resolve(config=config, file_paths=file_paths)

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
        result = resolver.resolve(config=config, file_paths=file_paths)

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
        result = resolver.resolve(config=config, file_paths=file_paths)

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
        result = resolver.resolve(config=config, file_paths=file_paths)

        # Assert
        assert result == ()

    def test_resolve_エッジケース_空のProjectConfigで空タプルを返すこと(self):
        # Arrange
        config = ProjectConfig()
        file_paths = (Path("tests/test_main.py"),)
        resolver = ConfigIgnoreResolver()

        # Act
        result = resolver.resolve(config=config, file_paths=file_paths)

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
        result = resolver.resolve(config=config, file_paths=file_paths)

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
        result = resolver.resolve(config=config, file_paths=file_paths)

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
        result = resolver.resolve(config=config, file_paths=file_paths)

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
        result = resolver.resolve(config=config, file_paths=file_paths)

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
        result = resolver.resolve(config=config, file_paths=file_paths)

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
        result = resolver.resolve(config=config, file_paths=file_paths)

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
        result = resolver.resolve(config=config, file_paths=file_paths)

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
        result = resolver.resolve(config=config, file_paths=file_paths)

        # Assert
        assert len(result) == 1
        assert result[0].ignored_rules == frozenset({"R-001"})
