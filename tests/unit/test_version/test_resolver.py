"""VersionResolverクラスのテスト"""

import importlib.metadata

from paladin.version.resolver import VersionResolver


class TestVersionResolver:
    """VersionResolverクラスのテスト"""

    def test_resolve_正常系_paladinパッケージのバージョン文字列を返すこと(self):
        # Arrange
        resolver = VersionResolver(package_name="paladin")

        # Act
        result = resolver.resolve()

        # Assert
        assert result == importlib.metadata.version("paladin")
