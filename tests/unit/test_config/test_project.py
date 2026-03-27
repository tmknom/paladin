import pytest

from paladin.config import ProjectConfigLoader
from paladin.config.project import ProjectConfig
from paladin.foundation.fs import FileSystemError
from tests.fake import ErrorFsReader, InMemoryFsReader


class TestProjectConfigLoader:
    """ProjectConfigLoader クラスのテスト"""

    def test_load_正常系_per_file_ignoresを含むProjectConfigを返すこと(self):
        # Arrange
        toml_content = """\
[tool.paladin.per-file-ignores]
"tests/**" = ["R-001", "R-002"]
"""
        reader = InMemoryFsReader(contents={"pyproject.toml": toml_content})
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
        reader = InMemoryFsReader(contents={"pyproject.toml": toml_content})
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
        reader = InMemoryFsReader(contents={"pyproject.toml": toml_content})
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
        loader = ProjectConfigLoader(
            reader=ErrorFsReader(
                FileSystemError(message="ファイルが見つかりません", cause=Exception("not found"))
            )
        )

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
        reader = InMemoryFsReader(contents={"pyproject.toml": toml_content})
        loader = ProjectConfigLoader(reader=reader)

        # Act
        result = loader.load()

        # Assert
        assert result == ProjectConfig()

    def test_load_正常系_rulesセクションを含むProjectConfigを返すこと(self):
        # Arrange
        toml_content = """\
[tool.paladin.rules]
no-relative-import = false
"""
        reader = InMemoryFsReader(contents={"pyproject.toml": toml_content})
        loader = ProjectConfigLoader(reader=reader)

        # Act
        result = loader.load()

        # Assert
        assert result.rules == {"no-relative-import": False}

    def test_load_正常系_includeを含むProjectConfigを返すこと(self):
        # Arrange
        toml_content = """\
[tool.paladin]
include = ["src/"]
"""
        reader = InMemoryFsReader(contents={"pyproject.toml": toml_content})
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
        reader = InMemoryFsReader(contents={"pyproject.toml": toml_content})
        loader = ProjectConfigLoader(reader=reader)

        # Act
        result = loader.load()

        # Assert
        assert result.exclude == (".venv/",)

    def test_load_正常系_overridesセクションを含むProjectConfigを返すこと(self):
        # Arrange
        toml_content = """\
[[tool.paladin.overrides]]
files = ["tests/**"]

[tool.paladin.overrides.rules]
require-all-export = false
"""
        reader = InMemoryFsReader(contents={"pyproject.toml": toml_content})
        loader = ProjectConfigLoader(reader=reader)

        # Act
        result = loader.load()

        # Assert
        assert len(result.overrides) == 1
        entry = result.overrides[0]
        assert entry.files == ("tests/**",)
        assert entry.rules == {"require-all-export": False}

    def test_load_正常系_複数overridesエントリを読み込めること(self):
        # Arrange
        toml_content = """\
[[tool.paladin.overrides]]
files = ["tests/**"]

[tool.paladin.overrides.rules]
require-all-export = false

[[tool.paladin.overrides]]
files = ["scripts/**", "tools/**"]

[tool.paladin.overrides.rules]
no-relative-import = false
"""
        reader = InMemoryFsReader(contents={"pyproject.toml": toml_content})
        loader = ProjectConfigLoader(reader=reader)

        # Act
        result = loader.load()

        # Assert
        assert len(result.overrides) == 2
        assert result.overrides[0].files == ("tests/**",)
        assert result.overrides[0].rules == {"require-all-export": False}
        assert result.overrides[1].files == ("scripts/**", "tools/**")
        assert result.overrides[1].rules == {"no-relative-import": False}

    def test_load_エッジケース_overridesのfilesが空配列の場合も読み込めること(self):
        # Arrange
        toml_content = """\
[[tool.paladin.overrides]]
files = []

[tool.paladin.overrides.rules]
require-all-export = false
"""
        reader = InMemoryFsReader(contents={"pyproject.toml": toml_content})
        loader = ProjectConfigLoader(reader=reader)

        # Act
        result = loader.load()

        # Assert
        assert len(result.overrides) == 1
        assert result.overrides[0].files == ()
        assert result.overrides[0].rules == {"require-all-export": False}

    def test_load_エッジケース_overridesのrulesが空の場合も読み込めること(self):
        # Arrange
        toml_content = """\
[[tool.paladin.overrides]]
files = ["tests/**"]
"""
        reader = InMemoryFsReader(contents={"pyproject.toml": toml_content})
        loader = ProjectConfigLoader(reader=reader)

        # Act
        result = loader.load()

        # Assert
        assert len(result.overrides) == 1
        assert result.overrides[0].files == ("tests/**",)
        assert result.overrides[0].rules == {}

    def test_load_正常系_projectセクションのnameからproject_nameを取得すること(self):
        # Arrange
        toml_content = """\
[project]
name = "myapp"
"""
        reader = InMemoryFsReader(contents={"pyproject.toml": toml_content})
        loader = ProjectConfigLoader(reader=reader)

        # Act
        result = loader.load()

        # Assert
        assert result.project_name == "myapp"

    @pytest.mark.parametrize(
        ("raw_name", "expected"),
        [
            pytest.param("my-app", "my_app", id="ハイフンがアンダースコアに正規化される"),
            pytest.param("my.app", "my_app", id="ドットがアンダースコアに正規化される"),
            pytest.param("MyApp", "myapp", id="大文字が小文字に正規化される"),
            pytest.param(
                "my--app", "my_app", id="連続区切り文字が単一アンダースコアに正規化される"
            ),
        ],
    )
    def test_load_正常系_project_nameが正規化されること(self, raw_name: str, expected: str):
        # Arrange
        toml_content = f'[project]\nname = "{raw_name}"\n'
        reader = InMemoryFsReader(contents={"pyproject.toml": toml_content})
        loader = ProjectConfigLoader(reader=reader)

        # Act
        result = loader.load()

        # Assert
        assert result.project_name == expected

    def test_load_エッジケース_projectセクションにnameがない場合project_nameがNoneであること(self):
        # Arrange
        toml_content = """\
[project]
version = "1.0.0"
"""
        reader = InMemoryFsReader(contents={"pyproject.toml": toml_content})
        loader = ProjectConfigLoader(reader=reader)

        # Act
        result = loader.load()

        # Assert
        assert result.project_name is None

    def test_load_正常系_rule_optionsセクションを含むProjectConfigを返すこと(self):
        # Arrange
        toml_content = """\
[tool.paladin.rule.no-third-party-import]
allow-dirs = ["src/foundation/"]
"""
        reader = InMemoryFsReader(contents={"pyproject.toml": toml_content})
        loader = ProjectConfigLoader(reader=reader)

        # Act
        result = loader.load()

        # Assert
        assert result.rule_options == {"no-third-party-import": {"allow-dirs": ["src/foundation/"]}}

    def test_load_エッジケース_rule_optionsセクションがない場合空dictになること(self):
        # Arrange
        toml_content = """\
[tool.paladin]
other_key = "value"
"""
        reader = InMemoryFsReader(contents={"pyproject.toml": toml_content})
        loader = ProjectConfigLoader(reader=reader)

        # Act
        result = loader.load()

        # Assert
        assert result.rule_options == {}

    def test_load_エッジケース_tool_paladinがない場合rule_optionsが空dictになること(self):
        # Arrange
        toml_content = """\
[tool.other]
key = "value"
"""
        reader = InMemoryFsReader(contents={"pyproject.toml": toml_content})
        loader = ProjectConfigLoader(reader=reader)

        # Act
        result = loader.load()

        # Assert
        assert result.rule_options == {}
