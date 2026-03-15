from paladin.config import PerFileIgnoreEntry, ProjectConfig, ProjectConfigLoader
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
        assert config.rules == {}

    def test_ProjectConfig_正常系_デフォルト値でrulesが空dictであること(self):
        # Arrange / Act
        config = ProjectConfig()

        # Assert
        assert config.rules == {}

    def test_ProjectConfig_正常系_includeフィールドを保持できること(self):
        # Arrange / Act
        config = ProjectConfig(include=("src/",))

        # Assert
        assert config.include == ("src/",)

    def test_ProjectConfig_正常系_excludeフィールドを保持できること(self):
        # Arrange / Act
        config = ProjectConfig(exclude=(".venv/",))

        # Assert
        assert config.exclude == (".venv/",)

    def test_ProjectConfig_正常系_デフォルトでincludeとexcludeが空タプルであること(self):
        # Arrange / Act
        config = ProjectConfig()

        # Assert
        assert config.include == ()
        assert config.exclude == ()

    def test_ProjectConfig_正常系_rulesフィールドを保持できること(self):
        # Arrange / Act
        config = ProjectConfig(rules={"no-relative-import": False})

        # Assert
        assert config.rules == {"no-relative-import": False}

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
        assert result.per_file_ignores == ()
        assert result.rules == {}

    def test_load_正常系_rulesセクションを含むProjectConfigを返すこと(self):
        # Arrange
        toml_content = """\
[tool.paladin.rules]
no-relative-import = false
"""
        reader = InMemoryFsReader(content=toml_content)
        loader = ProjectConfigLoader(reader=reader)

        # Act
        result = loader.load()

        # Assert
        assert result.rules == {"no-relative-import": False}

    def test_load_正常系_rulesとper_file_ignoresの両方を読み込めること(self):
        # Arrange
        toml_content = """\
[tool.paladin.per-file-ignores]
"tests/**" = ["R-001"]

[tool.paladin.rules]
no-relative-import = false
"""
        reader = InMemoryFsReader(content=toml_content)
        loader = ProjectConfigLoader(reader=reader)

        # Act
        result = loader.load()

        # Assert
        assert len(result.per_file_ignores) == 1
        assert result.rules == {"no-relative-import": False}

    def test_load_正常系_trueを明示指定したルールも読み込めること(self):
        # Arrange
        toml_content = """\
[tool.paladin.rules]
require-all-export = true
"""
        reader = InMemoryFsReader(content=toml_content)
        loader = ProjectConfigLoader(reader=reader)

        # Act
        result = loader.load()

        # Assert
        assert result.rules == {"require-all-export": True}

    def test_load_エッジケース_rulesセクションがない場合空dictになること(self):
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
        assert result.rules == {}

    def test_load_エッジケース_rulesセクションが空の場合空dictになること(self):
        # Arrange
        toml_content = """\
[tool.paladin.rules]
"""
        reader = InMemoryFsReader(content=toml_content)
        loader = ProjectConfigLoader(reader=reader)

        # Act
        result = loader.load()

        # Assert
        assert result.rules == {}

    def test_load_エッジケース_per_file_ignoresがなくてもrulesは読み込めること(self):
        # Arrange: per-file-ignores なし、rules あり
        toml_content = """\
[tool.paladin.rules]
no-relative-import = false
"""
        reader = InMemoryFsReader(content=toml_content)
        loader = ProjectConfigLoader(reader=reader)

        # Act
        result = loader.load()

        # Assert: rules が正しく読み込まれている
        assert result.rules == {"no-relative-import": False}
        assert result.per_file_ignores == ()

    def test_load_正常系_includeを含むProjectConfigを返すこと(self):
        # Arrange
        toml_content = """\
[tool.paladin]
include = ["src/"]
"""
        reader = InMemoryFsReader(content=toml_content)
        loader = ProjectConfigLoader(reader=reader)

        # Act
        result = loader.load()

        # Assert
        assert result.include == ("src/",)

    def test_load_正常系_excludeを含むProjectConfigを返すこと(self):
        # Arrange
        toml_content = """\
[tool.paladin]
exclude = [".venv/"]
"""
        reader = InMemoryFsReader(content=toml_content)
        loader = ProjectConfigLoader(reader=reader)

        # Act
        result = loader.load()

        # Assert
        assert result.exclude == (".venv/",)

    def test_load_正常系_includeとexcludeの両方を読み込めること(self):
        # Arrange
        toml_content = """\
[tool.paladin]
include = ["src/"]
exclude = [".venv/"]
"""
        reader = InMemoryFsReader(content=toml_content)
        loader = ProjectConfigLoader(reader=reader)

        # Act
        result = loader.load()

        # Assert
        assert result.include == ("src/",)
        assert result.exclude == (".venv/",)

    def test_load_正常系_複数のincludeパスを読み込めること(self):
        # Arrange
        toml_content = """\
[tool.paladin]
include = ["src/", "lib/"]
"""
        reader = InMemoryFsReader(content=toml_content)
        loader = ProjectConfigLoader(reader=reader)

        # Act
        result = loader.load()

        # Assert
        assert result.include == ("src/", "lib/")

    def test_load_エッジケース_includeが未指定の場合空タプルになること(self):
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
        assert result.include == ()

    def test_load_エッジケース_excludeが未指定の場合空タプルになること(self):
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
        assert result.exclude == ()

    def test_load_エッジケース_tool_paladinセクションがない場合includeとexcludeが空タプルになること(
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
        assert result.include == ()
        assert result.exclude == ()
