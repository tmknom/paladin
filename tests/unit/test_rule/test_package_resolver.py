"""PackageResolver のユニットテスト"""

import ast
from pathlib import Path

from paladin.rule.package_resolver import PackageResolver
from paladin.rule.types import SourceFile, SourceFiles


def _make_source_file(source: str, filename: str) -> SourceFile:
    return SourceFile(file_path=Path(filename), tree=ast.parse(source), source=source)


def _make_source_files(*pairs: tuple[str, str]) -> SourceFiles:
    return SourceFiles(files=tuple(_make_source_file(src, name) for src, name in pairs))


class TestPackageResolverResolvePackageKey:
    """PackageResolver.resolve_package_key() のテスト"""

    def test_正常系_srcレイアウトのファイルから先頭2セグメントを返すこと(self):
        resolver = PackageResolver()
        result = resolver.resolve_package_key(Path("src/paladin/check/foo.py"))
        assert result == "paladin.check"

    def test_正常系_srcレイアウトのinit_pyから先頭2セグメントを返すこと(self):
        resolver = PackageResolver()
        result = resolver.resolve_package_key(Path("src/paladin/check/__init__.py"))
        assert result == "paladin.check"

    def test_正常系_絶対パスから先頭2セグメントを返すこと(self):
        resolver = PackageResolver()
        result = resolver.resolve_package_key(
            Path("/Users/owner/code/paladin/src/paladin/check/foo.py")
        )
        assert result == "paladin.check"

    def test_正常系_testsレイアウトからtestsを先頭に含む2セグメントを返すこと(self):
        resolver = PackageResolver()
        result = resolver.resolve_package_key(Path("tests/unit/test_check/foo.py"))
        assert result == "tests.unit"

    def test_エッジケース_セグメントが2未満の場合はNoneを返すこと(self):
        resolver = PackageResolver()
        result = resolver.resolve_package_key(Path("src/paladin/foo.py"))
        # src アンカー後のパッケージ部分が1セグメントのみ
        assert result is None

    def test_エッジケース_アンカーなしのパスでフォールバック動作すること(self):
        resolver = PackageResolver()
        result = resolver.resolve_package_key(Path("myapp/module/foo.py"))
        assert result == "myapp.module"


class TestPackageResolverResolveExactPackagePath:
    """PackageResolver.resolve_exact_package_path() のテスト"""

    def test_正常系_深いパスから全セグメントを返すこと(self):
        resolver = PackageResolver()
        result = resolver.resolve_exact_package_path(
            Path("src/paladin/foundation/model/__init__.py")
        )
        assert result == "paladin.foundation.model"

    def test_正常系_2セグメントのパスから2セグメントを返すこと(self):
        resolver = PackageResolver()
        result = resolver.resolve_exact_package_path(Path("src/paladin/check/__init__.py"))
        assert result == "paladin.check"

    def test_正常系_testsレイアウトからtestsを先頭に含む全セグメントを返すこと(self):
        resolver = PackageResolver()
        result = resolver.resolve_exact_package_path(Path("tests/unit/fakes/__init__.py"))
        assert result == "tests.unit.fakes"

    def test_エッジケース_セグメントが2未満の場合はNoneを返すこと(self):
        resolver = PackageResolver()
        result = resolver.resolve_exact_package_path(Path("src/paladin/__init__.py"))
        # "paladin" の1セグメントのみ → None
        assert result is None

    def test_エッジケース_アンカーなしのパスでフォールバック動作すること(self):
        resolver = PackageResolver()
        result = resolver.resolve_exact_package_path(Path("myapp/module/sub/__init__.py"))
        assert result == "myapp.module.sub"


class TestPackageResolverExtractPackageKey:
    """PackageResolver.extract_package_key() のテスト"""

    def test_正常系_3セグメント以上から先頭2セグメントを返すこと(self):
        result = PackageResolver.extract_package_key("paladin.check.formatter")
        assert result == "paladin.check"

    def test_正常系_2セグメントのときそのまま返すこと(self):
        result = PackageResolver.extract_package_key("paladin.check")
        assert result == "paladin.check"

    def test_正常系_1セグメントのときそのまま返すこと(self):
        result = PackageResolver.extract_package_key("paladin")
        assert result == "paladin"


class TestPackageResolverIsSamePackageExact:
    """PackageResolver.is_same_package_exact() のテスト"""

    def test_正常系_同一パッケージキーのとき真を返すこと(self):
        assert PackageResolver.is_same_package_exact("paladin.check", "paladin.check") is True

    def test_正常系_異なるパッケージキーのとき偽を返すこと(self):
        assert PackageResolver.is_same_package_exact("paladin.check", "paladin.view") is False

    def test_エッジケース_片方がNoneのとき偽を返すこと(self):
        assert PackageResolver.is_same_package_exact(None, "paladin.check") is False

    def test_エッジケース_両方Noneのとき偽を返すこと(self):
        assert PackageResolver.is_same_package_exact(None, None) is False


class TestPackageResolverIsSubpackage:
    """PackageResolver.is_subpackage() のテスト"""

    def test_正常系_完全一致のとき真を返すこと(self):
        assert PackageResolver.is_subpackage("paladin.check", "paladin.check") is True

    def test_正常系_サブパッケージのとき真を返すこと(self):
        assert PackageResolver.is_subpackage("paladin.check.formatter", "paladin.check") is True

    def test_正常系_無関係なパッケージのとき偽を返すこと(self):
        assert PackageResolver.is_subpackage("paladin.view", "paladin.check") is False

    def test_エッジケース_プレフィックス一致でも別パッケージのとき偽を返すこと(self):
        # "paladin.check2" は "paladin.check" のサブパッケージではない
        assert PackageResolver.is_subpackage("paladin.check2", "paladin.check") is False


class TestPackageResolverIsOwnPackage:
    """PackageResolver.is_own_package() のテスト"""

    def test_正常系_完全一致のとき真を返すこと(self):
        own = frozenset({"paladin.check"})
        assert PackageResolver.is_own_package("paladin.check", own) is True

    def test_正常系_ownが深い階層を持ちプレフィックス一致のとき真を返すこと(self):
        own = frozenset({"paladin.foundation.error"})
        assert PackageResolver.is_own_package("paladin.foundation", own) is True

    def test_正常系_無関係なパッケージのとき偽を返すこと(self):
        own = frozenset({"paladin.check"})
        assert PackageResolver.is_own_package("paladin.view", own) is False

    def test_エッジケース_空のown_packagesのとき偽を返すこと(self):
        assert PackageResolver.is_own_package("paladin.check", frozenset()) is False


class TestPackageResolverResolveRootPackages:
    """PackageResolver.resolve_root_packages() のテスト"""

    def test_正常系_srcレイアウトからルートパッケージを導出すること(self):
        resolver = PackageResolver()
        source_files = _make_source_files(
            ("x = 1\n", "src/paladin/module.py"),
        )
        result = resolver.resolve_root_packages(source_files)
        assert "paladin" in result

    def test_正常系_testsは常に含まれること(self):
        resolver = PackageResolver()
        source_files = _make_source_files(
            ("x = 1\n", "src/paladin/module.py"),
        )
        result = resolver.resolve_root_packages(source_files)
        assert "tests" in result

    def test_正常系_複数のsrcパッケージを導出すること(self):
        resolver = PackageResolver()
        source_files = _make_source_files(
            ("x = 1\n", "src/paladin/module.py"),
            ("y = 1\n", "src/mylib/core.py"),
        )
        result = resolver.resolve_root_packages(source_files)
        assert "paladin" in result
        assert "mylib" in result

    def test_正常系_空のSourceFilesではtestsのみを返すこと(self):
        resolver = PackageResolver()
        source_files = SourceFiles(files=())
        result = resolver.resolve_root_packages(source_files)
        assert result == ("tests",)

    def test_正常系_testsアンカーのファイルはルートパッケージに追加しないこと(self):
        resolver = PackageResolver()
        # 相対パスの tests/ ファイル: FS フォールバックは CWD 基準となる
        source_files = _make_source_files(
            ("x = 1\n", "tests/unit/test_something.py"),
        )
        result = resolver.resolve_root_packages(source_files)
        # tests は常に含まれる
        assert "tests" in result

    def test_正常系_絶対パスのtestsアンカーはFSフォールバックでsrc配下パッケージを補完すること(
        self,
    ):
        resolver = PackageResolver()
        # 実際のプロジェクトルートを使って FS フォールバックが発動することを確認
        project_root = Path(__file__).parents[3]  # paladin/
        tests_file = project_root / "tests" / "unit" / "test_something.py"
        source_files = SourceFiles(files=(_make_source_file("x = 1\n", str(tests_file)),))
        result = resolver.resolve_root_packages(source_files)
        # FS フォールバックで paladin が src/ 配下から補完される
        assert "paladin" in result
        assert "tests" in result

    def test_正常系_srcアンカーのみのパスは無視されること(self):
        resolver = PackageResolver()
        # src/ の直下にファイルがある場合（src アンカー後のセグメントが空）
        source_files = _make_source_files(
            ("x = 1\n", "src/module.py"),
        )
        result = resolver.resolve_root_packages(source_files)
        # src の次が module.py（ファイル名除外後は空）なのでパッケージなし
        assert result == ("tests",)

    def test_正常系_絶対パスでもルートパッケージを導出すること(self):
        resolver = PackageResolver()
        source_files = _make_source_files(
            ("x = 1\n", "/Users/owner/code/paladin/src/paladin/module.py"),
        )
        result = resolver.resolve_root_packages(source_files)
        assert "paladin" in result
        assert "tests" in result

    def test_正常系_重複するパッケージは1件のみ返すこと(self):
        resolver = PackageResolver()
        source_files = _make_source_files(
            ("x = 1\n", "src/paladin/module.py"),
            ("y = 1\n", "src/paladin/check/foo.py"),
        )
        result = resolver.resolve_root_packages(source_files)
        # paladin が複数ファイルから検出されても1件のみ
        assert result.count("paladin") == 1
