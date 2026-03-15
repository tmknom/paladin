from pathlib import Path

import pytest

from paladin.check.context import CheckContext
from paladin.check.resolver import TargetResolver
from paladin.foundation.error.error import ApplicationError


class TestTargetResolver:
    def test_resolve_正常系_CLIターゲット指定ありの場合contextのtargetsを返すこと(self):
        # Arrange
        targets = (Path("src/"),)
        context = CheckContext(targets=targets)
        resolver = TargetResolver()

        # Act
        result = resolver.resolve(context)

        # Assert
        assert result == targets

    def test_resolve_正常系_CLIターゲット未指定でinclude指定ありの場合includeのパスを返すこと(self):
        # Arrange
        context = CheckContext(targets=(), include=("src/",))
        resolver = TargetResolver()

        # Act
        result = resolver.resolve(context)

        # Assert
        assert result == (Path("src/"),)

    def test_resolve_正常系_CLIターゲット指定ありでinclude指定ありの場合CLIターゲットが優先されること(
        self,
    ):
        # Arrange
        targets = (Path("lib/"),)
        context = CheckContext(targets=targets, include=("src/",))
        resolver = TargetResolver()

        # Act
        result = resolver.resolve(context)

        # Assert
        assert result == targets

    def test_resolve_正常系_複数のincludeパスをPathに変換して返すこと(self):
        # Arrange
        context = CheckContext(targets=(), include=("src/", "lib/"))
        resolver = TargetResolver()

        # Act
        result = resolver.resolve(context)

        # Assert
        assert result == (Path("src/"), Path("lib/"))

    def test_resolve_異常系_CLIターゲットもincludeも未指定の場合ApplicationErrorを送出すること(
        self,
    ):
        # Arrange
        context = CheckContext(targets=())
        resolver = TargetResolver()

        # Act / Assert
        with pytest.raises(ApplicationError):
            resolver.resolve(context)
