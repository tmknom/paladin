"""PackageResolver のユニットテスト"""

from pathlib import Path

from paladin.rule.package_resolver import PackageResolver
from paladin.rule.types import SourceFiles
from tests.unit.test_rule.helper import make_source_file, make_source_files


class TestPackageResolverResolvePackageKey:
    """PackageResolver.resolve_package_key() のテスト"""

    def test_正常系_srcレイアウトのファイルから先頭2セグメントを返すこと(self):
        # Arrange
        resolver = PackageResolver()

        # Act
        result = resolver.resolve_package_key(Path("src/paladin/check/foo.py"))

        # Assert
        assert result == "paladin.check"

    def test_正常系_srcレイアウトのinit_pyから先頭2セグメントを返すこと(self):
        # Arrange
        resolver = PackageResolver()

        # Act
        result = resolver.resolve_package_key(Path("src/paladin/check/__init__.py"))

        # Assert
        assert result == "paladin.check"

    def test_正常系_絶対パスから先頭2セグメントを返すこと(self):
        # Arrange
        resolver = PackageResolver()

        # Act
        result = resolver.resolve_package_key(Path("/fake/project/src/paladin/check/foo.py"))

        # Assert
        assert result == "paladin.check"

    def test_正常系_testsレイアウトからtestsを先頭に含む2セグメントを返すこと(self):
        # Arrange
        resolver = PackageResolver()

        # Act
        result = resolver.resolve_package_key(Path("tests/unit/test_check/foo.py"))

        # Assert
        assert result == "tests.unit"

    def test_エッジケース_セグメントが2未満の場合はNoneを返すこと(self):
        # Arrange
        resolver = PackageResolver()

        # Act
        result = resolver.resolve_package_key(Path("src/paladin/foo.py"))

        # Assert
        # src アンカー後のパッケージ部分が1セグメントのみ
        assert result is None

    def test_エッジケース_アンカーなしのパスでフォールバック動作すること(self):
        # Arrange
        resolver = PackageResolver()

        # Act
        result = resolver.resolve_package_key(Path("myapp/module/foo.py"))

        # Assert
        assert result == "myapp.module"


class TestPackageResolverResolveExactPackagePath:
    """PackageResolver.resolve_exact_package_path() のテスト"""

    def test_正常系_深いパスから全セグメントを返すこと(self):
        # Arrange
        resolver = PackageResolver()

        # Act
        result = resolver.resolve_exact_package_path(
            Path("src/paladin/foundation/model/__init__.py")
        )

        # Assert
        assert result == "paladin.foundation.model"

    def test_正常系_2セグメントのパスから2セグメントを返すこと(self):
        # Arrange
        resolver = PackageResolver()

        # Act
        result = resolver.resolve_exact_package_path(Path("src/paladin/check/__init__.py"))

        # Assert
        assert result == "paladin.check"

    def test_正常系_testsレイアウトからtestsを先頭に含む全セグメントを返すこと(self):
        # Arrange
        resolver = PackageResolver()

        # Act
        result = resolver.resolve_exact_package_path(Path("tests/fake/__init__.py"))

        # Assert
        assert result == "tests.fake"

    def test_エッジケース_セグメントが2未満の場合はNoneを返すこと(self):
        # Arrange
        resolver = PackageResolver()

        # Act
        result = resolver.resolve_exact_package_path(Path("src/paladin/__init__.py"))

        # Assert
        # "paladin" の1セグメントのみ → None
        assert result is None

    def test_エッジケース_アンカーなしのパスでフォールバック動作すること(self):
        # Arrange
        resolver = PackageResolver()

        # Act
        result = resolver.resolve_exact_package_path(Path("myapp/module/sub/__init__.py"))

        # Assert
        assert result == "myapp.module.sub"


class TestPackageResolverIsSamePackageExact:
    """PackageResolver.is_same_package_exact() のテスト"""

    def test_正常系_同一パッケージキーのとき真を返すこと(self):
        # Act / Assert
        assert PackageResolver.is_same_package_exact("paladin.check", "paladin.check") is True

    def test_正常系_異なるパッケージキーのとき偽を返すこと(self):
        # Act / Assert
        assert PackageResolver.is_same_package_exact("paladin.check", "paladin.view") is False

    def test_エッジケース_片方がNoneのとき偽を返すこと(self):
        # Act / Assert
        assert PackageResolver.is_same_package_exact(None, "paladin.check") is False

    def test_エッジケース_両方Noneのとき偽を返すこと(self):
        # Act / Assert
        assert PackageResolver.is_same_package_exact(None, None) is False


class TestPackageResolverIsOwnPackage:
    """PackageResolver.is_own_package() のテスト"""

    def test_正常系_完全一致のとき真を返すこと(self):
        # Arrange
        own = frozenset({"paladin.check"})

        # Act / Assert
        assert PackageResolver.is_own_package("paladin.check", own) is True

    def test_正常系_ownが深い階層を持ちプレフィックス一致のとき真を返すこと(self):
        # Arrange
        own = frozenset({"paladin.foundation.error"})

        # Act / Assert
        assert PackageResolver.is_own_package("paladin.foundation", own) is True

    def test_正常系_無関係なパッケージのとき偽を返すこと(self):
        # Arrange
        own = frozenset({"paladin.check"})

        # Act / Assert
        assert PackageResolver.is_own_package("paladin.view", own) is False

    def test_エッジケース_空のown_packagesのとき偽を返すこと(self):
        # Act / Assert
        assert PackageResolver.is_own_package("paladin.check", frozenset()) is False


class TestPackageResolverResolveRootPackages:
    """PackageResolver.resolve_root_packages() のテスト"""

    def test_正常系_srcレイアウトからルートパッケージを導出すること(self):
        # Arrange
        resolver = PackageResolver()
        source_files = make_source_files(
            ("x = 1\n", "src/paladin/module.py"),
        )

        # Act
        result = resolver.resolve_root_packages(source_files)

        # Assert
        assert "paladin" in result

    def test_正常系_testsは常に含まれること(self):
        # Arrange
        resolver = PackageResolver()
        source_files = make_source_files(
            ("x = 1\n", "src/paladin/module.py"),
        )

        # Act
        result = resolver.resolve_root_packages(source_files)

        # Assert
        assert "tests" in result

    def test_正常系_複数のsrcパッケージを導出すること(self):
        # Arrange
        resolver = PackageResolver()
        source_files = make_source_files(
            ("x = 1\n", "src/paladin/module.py"),
            ("y = 1\n", "src/mylib/core.py"),
        )

        # Act
        result = resolver.resolve_root_packages(source_files)

        # Assert
        assert "paladin" in result
        assert "mylib" in result

    def test_正常系_空のSourceFilesではtestsのみを返すこと(self):
        # Arrange
        resolver = PackageResolver()
        source_files = SourceFiles(files=())

        # Act
        result = resolver.resolve_root_packages(source_files)

        # Assert
        assert result == ("tests",)

    def test_正常系_testsアンカーのファイルはルートパッケージに追加しないこと(self):
        # Arrange
        resolver = PackageResolver()
        # 相対パスの tests/ ファイル: FS フォールバックは CWD 基準となる
        source_files = make_source_files(
            ("x = 1\n", "tests/unit/test_something.py"),
        )

        # Act
        result = resolver.resolve_root_packages(source_files)

        # Assert
        # tests は常に含まれる
        assert "tests" in result

    def test_正常系_絶対パスのtestsアンカーはFSフォールバックでsrc配下パッケージを補完すること(
        self,
    ):
        # Arrange
        resolver = PackageResolver()
        # 実際のプロジェクトルートを使って FS フォールバックが発動することを確認
        project_root = Path(__file__).parents[3]  # paladin/
        tests_file = project_root / "tests" / "unit" / "test_something.py"
        source_files = SourceFiles(files=(make_source_file("x = 1\n", str(tests_file)),))

        # Act
        result = resolver.resolve_root_packages(source_files)

        # Assert
        # FS フォールバックで paladin が src/ 配下から補完される
        assert "paladin" in result
        assert "tests" in result

    def test_正常系_srcアンカーのみのパスは無視されること(self):
        # Arrange
        resolver = PackageResolver()
        # src/ の直下にファイルがある場合（src アンカー後のセグメントが空）
        source_files = make_source_files(
            ("x = 1\n", "src/module.py"),
        )

        # Act
        result = resolver.resolve_root_packages(source_files)

        # Assert
        # src の次が module.py（ファイル名除外後は空）なのでパッケージなし
        assert result == ("tests",)

    def test_正常系_絶対パスでもルートパッケージを導出すること(self):
        # Arrange
        resolver = PackageResolver()
        source_files = make_source_files(
            ("x = 1\n", "/fake/project/src/paladin/module.py"),
        )

        # Act
        result = resolver.resolve_root_packages(source_files)

        # Assert
        assert "paladin" in result
        assert "tests" in result

    def test_正常系_重複するパッケージは1件のみ返すこと(self):
        # Arrange
        resolver = PackageResolver()
        source_files = make_source_files(
            ("x = 1\n", "src/paladin/module.py"),
            ("y = 1\n", "src/paladin/check/foo.py"),
        )

        # Act
        result = resolver.resolve_root_packages(source_files)

        # Assert
        # paladin が複数ファイルから検出されても1件のみ
        assert result.count("paladin") == 1
