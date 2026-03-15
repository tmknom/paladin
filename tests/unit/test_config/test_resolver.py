from pathlib import Path

import pytest

from paladin.config.resolver import TargetResolver
from paladin.foundation.error.error import ApplicationError


class TestTargetResolver:
    def test_resolve_正常系_CLIターゲット指定ありの場合targetsを返すこと(self):
        # Arrange
        targets = (Path("src/"),)
        resolver = TargetResolver()

        # Act
        result = resolver.resolve(targets=targets, include=())

        # Assert
        assert result == targets

    def test_resolve_正常系_CLIターゲット未指定でinclude指定ありの場合includeのパスを返すこと(self):
        # Arrange
        resolver = TargetResolver()

        # Act
        result = resolver.resolve(targets=(), include=("src/",))

        # Assert
        assert result == (Path("src/"),)

    def test_resolve_正常系_CLIターゲット指定ありでinclude指定ありの場合CLIターゲットが優先されること(
        self,
    ):
        # Arrange
        targets = (Path("lib/"),)
        resolver = TargetResolver()

        # Act
        result = resolver.resolve(targets=targets, include=("src/",))

        # Assert
        assert result == targets

    def test_resolve_正常系_複数のincludeパスをPathに変換して返すこと(self):
        # Arrange
        resolver = TargetResolver()

        # Act
        result = resolver.resolve(targets=(), include=("src/", "lib/"))

        # Assert
        assert result == (Path("src/"), Path("lib/"))

    def test_resolve_異常系_CLIターゲットもincludeも未指定の場合ApplicationErrorを送出すること(
        self,
    ):
        # Arrange
        resolver = TargetResolver()

        # Act / Assert
        with pytest.raises(ApplicationError):
            resolver.resolve(targets=(), include=())
