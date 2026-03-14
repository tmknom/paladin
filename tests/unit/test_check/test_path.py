from pathlib import Path

import pytest

from paladin.check.config import ProjectConfig, normalize_glob_pattern
from paladin.check.context import CheckContext
from paladin.check.path import PathExcluder, TargetResolver
from paladin.check.types import TargetFiles
from paladin.foundation.error.error import ApplicationError


class TestNormalizeGlobPattern:
    def test_normalize_glob_pattern_正常系_相対パターンにダブルスターを前置すること(self):
        # Arrange / Act
        result = normalize_glob_pattern("tests/**")

        # Assert
        assert result == "**/tests/**"

    def test_normalize_glob_pattern_エッジケース_ダブルスター始まりのパターンはそのまま返すこと(
        self,
    ):
        # Arrange / Act
        result = normalize_glob_pattern("**/tests/**")

        # Assert
        assert result == "**/tests/**"

    def test_normalize_glob_pattern_エッジケース_スラッシュ始まりのパターンはそのまま返すこと(self):
        # Arrange / Act
        result = normalize_glob_pattern("/abs/path")

        # Assert
        assert result == "/abs/path"

    def test_normalize_glob_pattern_正常系_ファイルパターンにダブルスターを前置すること(self):
        # Arrange / Act
        result = normalize_glob_pattern("*.py")

        # Assert
        assert result == "**/*.py"


class TestTargetResolver:
    def test_resolve_正常系_CLIターゲット指定ありの場合contextのtargetsを返すこと(self):
        # Arrange
        targets = (Path("src/"),)
        context = CheckContext(targets=targets, has_cli_targets=True)
        config = ProjectConfig()
        resolver = TargetResolver()

        # Act
        result = resolver.resolve(context, config)

        # Assert
        assert result == targets

    def test_resolve_正常系_CLIターゲット未指定でinclude指定ありの場合includeのパスを返すこと(self):
        # Arrange
        context = CheckContext(targets=(), has_cli_targets=False)
        config = ProjectConfig(include=("src/",))
        resolver = TargetResolver()

        # Act
        result = resolver.resolve(context, config)

        # Assert
        assert result == (Path("src/"),)

    def test_resolve_正常系_CLIターゲット指定ありでinclude指定ありの場合CLIターゲットが優先されること(
        self,
    ):
        # Arrange
        targets = (Path("lib/"),)
        context = CheckContext(targets=targets, has_cli_targets=True)
        config = ProjectConfig(include=("src/",))
        resolver = TargetResolver()

        # Act
        result = resolver.resolve(context, config)

        # Assert
        assert result == targets

    def test_resolve_正常系_複数のincludeパスをPathに変換して返すこと(self):
        # Arrange
        context = CheckContext(targets=(), has_cli_targets=False)
        config = ProjectConfig(include=("src/", "lib/"))
        resolver = TargetResolver()

        # Act
        result = resolver.resolve(context, config)

        # Assert
        assert result == (Path("src/"), Path("lib/"))

    def test_resolve_異常系_CLIターゲットもincludeも未指定の場合ApplicationErrorを送出すること(
        self,
    ):
        # Arrange
        context = CheckContext(targets=(), has_cli_targets=False)
        config = ProjectConfig()
        resolver = TargetResolver()

        # Act / Assert
        with pytest.raises(ApplicationError):
            resolver.resolve(context, config)


class TestPathExcluder:
    def test_exclude_正常系_excludeパターンにマッチするファイルを除外すること(self):
        # Arrange
        files = TargetFiles(files=(Path(".venv/lib/foo.py"),))
        excluder = PathExcluder()

        # Act
        result = excluder.exclude(files, patterns=(".venv/",))

        # Assert
        assert Path(".venv/lib/foo.py") not in result.files

    def test_exclude_正常系_マッチしないファイルは残ること(self):
        # Arrange
        files = TargetFiles(files=(Path("src/main.py"),))
        excluder = PathExcluder()

        # Act
        result = excluder.exclude(files, patterns=(".venv/",))

        # Assert
        assert Path("src/main.py") in result.files

    def test_exclude_正常系_globパターンでマッチするファイルを除外すること(self):
        # Arrange
        files = TargetFiles(files=(Path("src/foo_pb2.py"),))
        excluder = PathExcluder()

        # Act
        result = excluder.exclude(files, patterns=("**/*_pb2.py",))

        # Assert
        assert Path("src/foo_pb2.py") not in result.files

    def test_exclude_エッジケース_空のpatternsでファイルをそのまま返すこと(self):
        # Arrange
        files = TargetFiles(files=(Path("src/main.py"), Path("src/sub.py")))
        excluder = PathExcluder()

        # Act
        result = excluder.exclude(files, patterns=())

        # Assert
        assert result.files == files.files

    def test_exclude_エッジケース_空のTargetFilesで空を返すこと(self):
        # Arrange
        files = TargetFiles(files=())
        excluder = PathExcluder()

        # Act
        result = excluder.exclude(files, patterns=(".venv/",))

        # Assert
        assert result.files == ()

    def test_exclude_正常系_複数のexcludeパターンを適用できること(self):
        # Arrange
        files = TargetFiles(
            files=(
                Path(".venv/lib/foo.py"),
                Path("build/out.py"),
                Path("src/main.py"),
            )
        )
        excluder = PathExcluder()

        # Act
        result = excluder.exclude(files, patterns=(".venv/", "build/"))

        # Assert
        assert Path(".venv/lib/foo.py") not in result.files
        assert Path("build/out.py") not in result.files
        assert Path("src/main.py") in result.files

    def test_exclude_正常系_絶対パスに対してexcludeパターンがマッチすること(self):
        # Arrange
        files = TargetFiles(files=(Path("/abs/path/.venv/foo.py"),))
        excluder = PathExcluder()

        # Act
        result = excluder.exclude(files, patterns=(".venv/",))

        # Assert
        assert Path("/abs/path/.venv/foo.py") not in result.files

    def test_exclude_正常系_ディレクトリパスの末尾スラッシュの有無によらずマッチすること(self):
        # Arrange: 末尾スラッシュなし ".venv" でも除外される
        files = TargetFiles(files=(Path(".venv/lib/foo.py"),))
        excluder = PathExcluder()

        # Act
        result_with_slash = excluder.exclude(files, patterns=(".venv/",))
        result_without_slash = excluder.exclude(files, patterns=(".venv",))

        # Assert
        assert Path(".venv/lib/foo.py") not in result_with_slash.files
        assert Path(".venv/lib/foo.py") not in result_without_slash.files
