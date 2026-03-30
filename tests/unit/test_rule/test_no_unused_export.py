"""NoUnusedExportRule のテスト"""

import ast
from pathlib import Path

import pytest

from paladin.rule.all_exports_extractor import AllExportsExtractor
from paladin.rule.no_unused_export import (
    ExportCollector,
    NoUnusedExportRule,
    UnusedExportDetector,
    UsageCollector,
)
from paladin.rule.package_resolver import PackageResolver
from paladin.rule.types import RuleMeta, SourceFile, SourceFiles
from tests.unit.test_rule.helper import make_source_files


def _rule(root_packages: tuple[str, ...] = ("paladin",)) -> NoUnusedExportRule:
    """root_packages を prepare() で設定した NoUnusedExportRule を返す（テスト用）

    各パッケージ名を src/<pkg>/stub.py 形式の SourceFiles として渡し、
    PackageResolver.resolve_root_packages() に自動導出させる。
    """
    rule = NoUnusedExportRule()
    stub_files = tuple(
        SourceFile(
            file_path=Path(f"src/{pkg}/stub.py"),
            tree=ast.parse(""),
            source="",
        )
        for pkg in root_packages
        if pkg != "tests"  # tests は常に自動導出されるため不要
    )
    stub_source_files = SourceFiles(files=stub_files)
    rule.prepare(stub_source_files)
    return rule


class TestNoUnusedExportRuleMeta:
    """NoUnusedExportRule のメタ情報テスト"""

    def test_meta_正常系_ルールメタ情報を返すこと(self):
        # Arrange
        rule = NoUnusedExportRule()

        # Act
        meta = rule.meta

        # Assert
        assert isinstance(meta, RuleMeta)
        assert meta.rule_id == "no-unused-export"
        assert meta.rule_name != ""
        assert meta.summary != ""
        assert meta.intent != ""
        assert meta.guidance != ""
        assert meta.suggestion != ""


class TestNoUnusedExportRuleCheck:
    """NoUnusedExportRule のチェックテスト"""

    # -------------------------------------------------------------------------
    # A カテゴリ: フィールド値テスト・個別テスト
    # -------------------------------------------------------------------------

    def test_check_正常系_複数シンボルのうち利用されていないもののみ違反を検出すること(self):
        # Arrange: Used は利用されているが Unused は利用されていない
        init_source = '__all__ = ["Used", "Unused"]\n'
        cli_source = "from paladin.check import Used\n"
        source_files = make_source_files(
            (init_source, "src/paladin/check/__init__.py"),
            (cli_source, "src/paladin/cli.py"),
        )
        rule = _rule(("paladin",))

        # Act
        result = rule.check(source_files)

        # Assert
        assert len(result) == 1

    # -------------------------------------------------------------------------
    # prepare テスト: 個別維持
    # -------------------------------------------------------------------------

    def test_prepare_正常系_source_filesからルートパッケージが自動導出されること(self):
        # Arrange: src/paladin/module.py を含む SourceFiles を渡して prepare() を呼び出す
        # prepare() 後に check() でシンボルが検出されれば root_packages が設定されている
        init_source = '__all__ = ["Foo"]\n'
        stub_source = "x = 1\n"
        source_files = make_source_files(
            (init_source, "src/paladin/check/__init__.py"),
            (stub_source, "src/paladin/module.py"),  # paladin を自動導出するため
        )
        rule = NoUnusedExportRule()

        # prepare() 前は root_packages が空なので違反を検出しない
        result_before = rule.check(source_files)
        assert len(result_before) == 0

        # Act
        rule.prepare(source_files)

        # Assert: paladin が自動導出されるため違反を検出
        result_after = rule.check(source_files)
        assert len(result_after) == 1

    def test_check_エッジケース_root_packagesが空の場合は何も検出しないこと(self):
        # Arrange: prepare() を呼ばずに check() を呼び出すと早期リターン
        init_source = '__all__ = ["Foo"]\n'
        source_files = make_source_files((init_source, "src/paladin/check/__init__.py"))
        rule = NoUnusedExportRule()

        # Act
        result = rule.check(source_files)

        # Assert
        assert len(result) == 0

    # -------------------------------------------------------------------------
    # integration テスト: 個別維持
    # -------------------------------------------------------------------------

    # -------------------------------------------------------------------------
    # 複数ファイル違反: 個別維持（len==2）
    # -------------------------------------------------------------------------

    def test_check_正常系_複数ファイルの違反を集約して返すこと(self):
        # Arrange: 2つの __init__.py にそれぞれ未使用シンボル
        init1_source = '__all__ = ["Foo"]\n'
        init2_source = '__all__ = ["Bar"]\n'
        source_files = make_source_files(
            (init1_source, "src/paladin/check/__init__.py"),
            (init2_source, "src/paladin/rule/__init__.py"),
        )
        rule = _rule(("paladin",))

        # Act
        result = rule.check(source_files)

        # Assert
        assert len(result) == 2

    # -------------------------------------------------------------------------
    # C カテゴリ: 0件（違反なし）を parametrize
    # -------------------------------------------------------------------------

    @pytest.mark.parametrize(
        "sources_and_files",
        [
            pytest.param(
                None,
                id="空のSourceFiles",
            ),
            pytest.param(
                [
                    ('__all__ = ["FakeRule"]\n', "tests/unit/fake/__init__.py"),
                    (
                        "from tests.unit.fake import FakeRule\n",
                        "tests/unit/test_check/test_foo.py",
                    ),
                ],
                id="tests配下のinit_pyのFakeRuleがテストから利用されている",
            ),
            pytest.param(
                [
                    (
                        '__all__ = ["Foo"]\n',
                        "/fake/project/src/paladin/check/__init__.py",
                    ),
                    (
                        "from paladin.check import Foo\n",
                        "/fake/project/src/paladin/cli.py",
                    ),
                ],
                id="絶対パスでの別パッケージfrom_import利用あり",
            ),
        ],
    )
    def test_check_違反なしのケースで空を返すこと(
        self, sources_and_files: list[tuple[str, str]] | None
    ) -> None:
        # Arrange
        if sources_and_files is None:
            source_files = SourceFiles(files=())
        else:
            source_files = make_source_files(*sources_and_files)
        rule = _rule(("paladin",))

        # Act
        result = rule.check(source_files)

        # Assert
        assert len(result) == 0

    # -------------------------------------------------------------------------
    # B カテゴリ: 1件（違反あり）を parametrize
    # -------------------------------------------------------------------------

    @pytest.mark.parametrize(
        "sources_and_files",
        [
            pytest.param(
                [
                    ('__all__ = ["Foo"]\n', "src/paladin/check/__init__.py"),
                    ("from paladin.check import Foo\n", "src/paladin/check/bar.py"),
                ],
                id="同一パッケージからの利用は利用とみなさない",
            ),
            pytest.param(
                [
                    ('__all__ = ["Foo"]\n', "src/paladin/check/__init__.py"),
                    ("from paladin.check import Foo\n", "tests/unit/test_check/test_foo.py"),
                ],
                id="tests配下のファイルからの利用は利用とみなさない",
            ),
            pytest.param(
                [
                    ('__all__ = ["CheckOrchestrator"]\n', "src/paladin/check/__init__.py"),
                    ("import paladin.check\n", "src/paladin/cli.py"),
                ],
                id="import文のみで属性アクセスがない場合は利用とみなさない",
            ),
            pytest.param(
                [
                    ('__all__ = ["Foo"]\n', "src/paladin/check/__init__.py"),
                    ("from . import something\n", "src/paladin/rule/bar.py"),
                ],
                id="相対インポートは利用収集をスキップ",
            ),
            pytest.param(
                [
                    ('__all__ = ["Foo"]\n', "src/paladin/check/__init__.py"),
                    ("from paladin.rule import X\n", "src/paladin/cli.py"),
                ],
                id="all_exportsに一致しないインポートはスキップ",
            ),
            pytest.param(
                [
                    ('__all__ = ["Foo"]\n', "src/paladin/check/__init__.py"),
                    ("import paladin.rule\nx = paladin.rule.X\n", "src/paladin/cli.py"),
                ],
                id="属性アクセスのモジュール名がall_exportsに一致しない場合スキップ",
            ),
            pytest.param(
                [
                    ('__all__ = ["Foo"]\n', "src/paladin/check/__init__.py"),
                    (
                        "import paladin.check\nx = paladin.check.Foo\n",
                        "src/paladin/check/bar.py",
                    ),
                ],
                id="属性アクセスでの同一パッケージからの利用は利用とみなさない",
            ),
            pytest.param(
                [
                    ('__all__ = ["Foo"]\n', "src/paladin/check/__init__.py"),
                    ("import paladin.check\nfunc().Foo\n", "src/paladin/cli.py"),
                ],
                id="関数呼び出し結果の属性アクセスはスキップ",
            ),
            pytest.param(
                [
                    ('__all__ = ["Foo"]\n', "src/paladin/check/__init__.py"),
                    (
                        "import paladin.check\nx = paladin.check.Foo\n",
                        "tests/unit/test_check/test_foo.py",
                    ),
                ],
                id="テストから属性アクセス形式でプロダクションallを参照しても利用とみなさない",
            ),
        ],
    )
    def test_check_違反ありのケースで1件返すこと(
        self, sources_and_files: list[tuple[str, str]]
    ) -> None:
        # Arrange
        source_files = make_source_files(*sources_and_files)
        rule = _rule(("paladin",))

        # Act
        result = rule.check(source_files)

        # Assert
        assert len(result) == 1


class TestExportCollector:
    """ExportCollector のテスト"""

    def test_collect_正常系_init_pyのallシンボルを収集すること(self):
        # Arrange
        init_source = '__all__ = ["Foo", "Bar"]\n'
        source_files = make_source_files((init_source, "src/paladin/check/__init__.py"))
        resolver = PackageResolver()
        extractor = AllExportsExtractor()

        # Act
        result = ExportCollector.collect(source_files, resolver, extractor)

        # Assert
        assert "paladin.check" in result
        file_path, symbols = result["paladin.check"]
        assert file_path == Path("src/paladin/check/__init__.py")
        assert "Foo" in symbols
        assert "Bar" in symbols

    def test_collect_正常系_allが未定義のinit_pyはスキップすること(self):
        # Arrange
        init_source = "x = 1\n"
        source_files = make_source_files((init_source, "src/paladin/check/__init__.py"))
        resolver = PackageResolver()
        extractor = AllExportsExtractor()

        # Act
        result = ExportCollector.collect(source_files, resolver, extractor)

        # Assert
        assert result == {}

    def test_collect_正常系_init_py以外はスキップすること(self):
        # Arrange
        source_files = make_source_files(('__all__ = ["Foo"]\n', "src/paladin/check/module.py"))
        resolver = PackageResolver()
        extractor = AllExportsExtractor()

        # Act
        result = ExportCollector.collect(source_files, resolver, extractor)

        # Assert
        assert result == {}


class TestUsageCollector:
    """UsageCollector のテスト"""

    def test_collect_正常系_from_importでシンボルを収集すること(self):
        # Arrange
        init_source = '__all__ = ["Foo"]\n'
        cli_source = "from paladin.check import Foo\n"
        source_files = make_source_files(
            (init_source, "src/paladin/check/__init__.py"),
            (cli_source, "src/paladin/cli.py"),
        )
        resolver = PackageResolver()
        extractor = AllExportsExtractor()
        all_exports = ExportCollector.collect(source_files, resolver, extractor)

        # Act
        result = UsageCollector.collect(source_files, all_exports, resolver)

        # Assert
        assert "paladin.check" in result
        assert "Foo" in result["paladin.check"]

    def test_collect_正常系_属性アクセスでシンボルを収集すること(self):
        # Arrange
        init_source = '__all__ = ["Foo"]\n'
        cli_source = "import paladin.check\nx = paladin.check.Foo\n"
        source_files = make_source_files(
            (init_source, "src/paladin/check/__init__.py"),
            (cli_source, "src/paladin/cli.py"),
        )
        resolver = PackageResolver()
        extractor = AllExportsExtractor()
        all_exports = ExportCollector.collect(source_files, resolver, extractor)

        # Act
        result = UsageCollector.collect(source_files, all_exports, resolver)

        # Assert
        assert "paladin.check" in result
        assert "Foo" in result["paladin.check"]

    def test_collect_正常系_テストファイルからのプロダクションallはスキップすること(self):
        # Arrange
        init_source = '__all__ = ["Foo"]\n'
        test_source = "from paladin.check import Foo\n"
        source_files = make_source_files(
            (init_source, "src/paladin/check/__init__.py"),
            (test_source, "tests/unit/test_check/test_foo.py"),
        )
        resolver = PackageResolver()
        extractor = AllExportsExtractor()
        all_exports = ExportCollector.collect(source_files, resolver, extractor)

        # Act
        result = UsageCollector.collect(source_files, all_exports, resolver)

        # Assert: テストからのプロダクションallは利用としてカウントしない
        assert result.get("paladin.check", set()) == set()


class TestUnusedExportDetector:
    """UnusedExportDetector のテスト"""

    def test_detect_正常系_未使用シンボルのViolationを返すこと(self):
        # Arrange
        rule = NoUnusedExportRule()
        file_path = Path("src/paladin/check/__init__.py")
        symbols = {"Foo": 1, "Bar": 2}
        used_symbols: set[str] = set()

        # Act
        result = UnusedExportDetector.detect(file_path, symbols, used_symbols, rule.meta)

        # Assert
        assert len(result) == 2

    def test_detect_正常系_使用済みシンボルは違反を返さないこと(self):
        # Arrange
        rule = NoUnusedExportRule()
        file_path = Path("src/paladin/check/__init__.py")
        symbols = {"Foo": 1}
        used_symbols = {"Foo"}

        # Act
        result = UnusedExportDetector.detect(file_path, symbols, used_symbols, rule.meta)

        # Assert
        assert len(result) == 0

    def test_detect_正常系_Violationのフィールド値が正しいこと(self):
        # Arrange
        rule = NoUnusedExportRule()
        file_path = Path("src/paladin/check/__init__.py")
        symbols = {"Foo": 3}
        used_symbols: set[str] = set()

        # Act
        result = UnusedExportDetector.detect(file_path, symbols, used_symbols, rule.meta)

        # Assert
        assert len(result) == 1
        v = result[0]
        assert v.rule_id == "no-unused-export"
        assert v.line == 3
