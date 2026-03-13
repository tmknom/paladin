"""VersionResolverクラスのテスト"""

import importlib.metadata

import pytest

from paladin.version.resolver import VersionResolver


class TestVersionResolver:
    """VersionResolverクラスのテスト"""

    def test_resolve_正常系_paladinパッケージのバージョン文字列を返すこと(self):
        # Arrange
        resolver = VersionResolver(package_name="paladin")

        # Act
        result = resolver.resolve()

        # Assert
        assert result == "0.1.0"

    def test_resolve_異常系_存在しないパッケージ名でPackageNotFoundErrorを送出すること(self):
        # Arrange
        resolver = VersionResolver(package_name="no-such-package-xyz")

        # Act / Assert
        with pytest.raises(importlib.metadata.PackageNotFoundError):
            resolver.resolve()
