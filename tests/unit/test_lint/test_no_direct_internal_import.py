"""NoDirectInternalImportRule のテスト"""

import ast
from pathlib import Path

from paladin.lint.no_direct_internal_import import NoDirectInternalImportRule
from paladin.lint.types import RuleMeta, SourceFile, SourceFiles


def _make_source_file(source: str, filename: str = "example.py") -> SourceFile:
    return SourceFile(file_path=Path(filename), tree=ast.parse(source), source=source)


def _make_source_files(*files: tuple[str, str]) -> SourceFiles:
    return SourceFiles(files=tuple(_make_source_file(src, name) for src, name in files))


class TestNoDirectInternalImportRuleMeta:
    """NoDirectInternalImportRule のメタ情報テスト"""

    def test_meta_正常系_ルールメタ情報を返すこと(self):
        rule = NoDirectInternalImportRule(root_packages=("paladin",))
        meta = rule.meta

        assert isinstance(meta, RuleMeta)
        assert meta.rule_id == "no-direct-internal-import"
        assert meta.rule_name == "No Direct Internal Import"
        assert meta.summary != ""
        assert meta.intent != ""
        assert meta.guidance != ""
        assert meta.suggestion != ""


class TestNoDirectInternalImportRuleCheck:
    """NoDirectInternalImportRule のヒューリスティック検出テスト（__init__.py なし）"""

    def test_check_正常系_3階層以上のインポートで違反を検出すること(self):
        # Arrange: paladin.check.orchestrator は3階層（paladin, check, orchestrator）
        # __init__.py が SourceFiles に含まれない場合はヒューリスティック検出
        source = "from paladin.check.orchestrator import CheckOrchestrator\n"
        source_files = _make_source_files((source, "src/other/module.py"))
        rule = NoDirectInternalImportRule(root_packages=("paladin",))

        # Act
        result = rule.check(source_files)

        # Assert
        assert len(result) == 1
        assert result[0].rule_id == "no-direct-internal-import"

    def test_check_正常系_2階層のインポートは検出しないこと(self):
        # Arrange: paladin.check は2階層（セグメント数2）
        source = "from paladin.check import CheckOrchestrator\n"
        source_files = _make_source_files((source, "src/other/module.py"))
        rule = NoDirectInternalImportRule(root_packages=("paladin",))

        # Act
        result = rule.check(source_files)

        # Assert
        assert len(result) == 0

    def test_check_正常系_root_packages以外のインポートは検出しないこと(self):
        # Arrange: requests は root_packages に含まれない
        source = "from requests.adapters import HTTPAdapter\n"
        source_files = _make_source_files((source, "src/other/module.py"))
        rule = NoDirectInternalImportRule(root_packages=("paladin",))

        # Act
        result = rule.check(source_files)

        # Assert
        assert len(result) == 0

    def test_check_正常系_相対インポートは検出しないこと(self):
        # Arrange: 相対インポートは no-relative-import で検出するため対象外
        source = "from .module import Foo\n"
        source_files = _make_source_files((source, "src/paladin/check/module.py"))
        rule = NoDirectInternalImportRule(root_packages=("paladin",))

        # Act
        result = rule.check(source_files)

        # Assert
        assert len(result) == 0

    def test_check_正常系_同一パッケージ内のインポートは検出しないこと(self):
        # Arrange: paladin/check/foo.py から from paladin.check.bar import Baz
        # 先頭2セグメントが同じ（paladin.check）なので対象外
        source = "from paladin.check.bar import Baz\n"
        source_files = _make_source_files((source, "src/paladin/check/foo.py"))
        rule = NoDirectInternalImportRule(root_packages=("paladin",))

        # Act
        result = rule.check(source_files)

        # Assert
        assert len(result) == 0

    def test_check_正常系_異なるサブパッケージのインポートは検出すること(self):
        # Arrange: paladin/check/foo.py から from paladin.lint.types import SourceFile
        # 先頭2セグメントが異なる（paladin.check vs paladin.lint）なので対象
        source = "from paladin.lint.types import SourceFile\n"
        source_files = _make_source_files((source, "src/paladin/check/foo.py"))
        rule = NoDirectInternalImportRule(root_packages=("paladin",))

        # Act
        result = rule.check(source_files)

        # Assert
        assert len(result) == 1

    def test_check_正常系_違反メッセージが仕様どおりであること(self):
        # Arrange
        source = "from paladin.check.orchestrator import CheckOrchestrator\n"
        source_files = _make_source_files((source, "src/other/module.py"))
        rule = NoDirectInternalImportRule(root_packages=("paladin",))

        # Act
        result = rule.check(source_files)

        # Assert: メッセージ形式の確認
        assert len(result) == 1
        v = result[0]
        assert (
            "`from paladin.check.orchestrator import CheckOrchestrator` は内部モジュールへの直接参照である"
            in v.message
        )
        assert (
            "`paladin.check` の内部実装に直接依存しており、パッケージの公開 API を経由していない"
            in v.reason
        )
        assert (
            "`from paladin.check import CheckOrchestrator` のように、パッケージの `__init__.py` を経由するインポートに書き換える"
            in v.suggestion
        )


class TestNoDirectInternalImportRuleInitPy:
    """NoDirectInternalImportRule の __init__.py 解析テスト"""

    def test_check_正常系_init_pyのall_exportsに含まれるシンボルのインポートを検出すること(self):
        # Arrange: paladin/check/__init__.py に __all__ = ["Foo"] がある
        init_source = '__all__ = ["Foo"]\n'
        import_source = "from paladin.check.orchestrator import Foo\n"
        source_files = _make_source_files(
            (init_source, "src/paladin/check/__init__.py"),
            (import_source, "src/other/module.py"),
        )
        rule = NoDirectInternalImportRule(root_packages=("paladin",))

        # Act
        result = rule.check(source_files)

        # Assert: Foo は __all__ で公開されているため違反
        assert len(result) == 1

    def test_check_正常系_init_pyの再エクスポートに含まれるシンボルのインポートを検出すること(self):
        # Arrange: paladin/check/__init__.py に from .orchestrator import Foo がある
        init_source = "from .orchestrator import Foo\n"
        import_source = "from paladin.check.orchestrator import Foo\n"
        source_files = _make_source_files(
            (init_source, "src/paladin/check/__init__.py"),
            (import_source, "src/other/module.py"),
        )
        rule = NoDirectInternalImportRule(root_packages=("paladin",))

        # Act
        result = rule.check(source_files)

        # Assert: Foo は再エクスポートで公開されているため違反
        assert len(result) == 1

    def test_check_正常系_init_pyで公開されていないシンボルは検出しないこと(self):
        # Arrange: __init__.py に Foo は含まれない（Barのみ）
        init_source = '__all__ = ["Bar"]\n'
        import_source = "from paladin.check.orchestrator import Foo\n"
        source_files = _make_source_files(
            (init_source, "src/paladin/check/__init__.py"),
            (import_source, "src/other/module.py"),
        )
        rule = NoDirectInternalImportRule(root_packages=("paladin",))

        # Act
        result = rule.check(source_files)

        # Assert: Foo は __init__.py で公開されていないため対象外
        assert len(result) == 0

    def test_check_エッジケース_init_pyが空の場合はヒューリスティック検出にフォールバックすること(
        self,
    ):
        # Arrange: __init__.py が存在するが __all__ も再エクスポートもない
        init_source = "# empty\n"
        import_source = "from paladin.check.orchestrator import CheckOrchestrator\n"
        source_files = _make_source_files(
            (init_source, "src/paladin/check/__init__.py"),
            (import_source, "src/other/module.py"),
        )
        rule = NoDirectInternalImportRule(root_packages=("paladin",))

        # Act
        result = rule.check(source_files)

        # Assert: フォールバックで3階層以上のインポートを検出
        assert len(result) == 1


class TestNoDirectInternalImportRuleEdgeCases:
    """NoDirectInternalImportRule のエッジケーステスト"""

    def test_check_エッジケース_空のSourceFilesで空タプルを返すこと(self):
        rule = NoDirectInternalImportRule(root_packages=("paladin",))
        result = rule.check(SourceFiles(files=()))
        assert result == ()

    def test_check_エッジケース_インポート文がないファイルで空タプルを返すこと(self):
        source = "x = 1\n"
        source_files = _make_source_files((source, "src/paladin/check/foo.py"))
        rule = NoDirectInternalImportRule(root_packages=("paladin",))

        result = rule.check(source_files)

        assert result == ()

    def test_check_正常系_複数ファイルの違反を集約して返すこと(self):
        # Arrange: 2ファイルそれぞれから違反
        source1 = "from paladin.check.orchestrator import CheckOrchestrator\n"
        source2 = "from paladin.lint.types import SourceFile\n"
        source_files = _make_source_files(
            (source1, "src/other/module1.py"),
            (source2, "src/other/module2.py"),
        )
        rule = NoDirectInternalImportRule(root_packages=("paladin",))

        result = rule.check(source_files)

        assert len(result) == 2

    def test_check_正常系_import文は検出しないこと(self):
        # Arrange: from ... import ではなく import 文
        source = "import paladin.check.orchestrator\n"
        source_files = _make_source_files((source, "src/other/module.py"))
        rule = NoDirectInternalImportRule(root_packages=("paladin",))

        result = rule.check(source_files)

        assert len(result) == 0

    def test_check_エッジケース_root_packagesが空の場合は何も検出しないこと(self):
        source = "from paladin.check.orchestrator import CheckOrchestrator\n"
        source_files = _make_source_files((source, "src/other/module.py"))
        rule = NoDirectInternalImportRule(root_packages=())

        result = rule.check(source_files)

        assert len(result) == 0


class TestNoDirectInternalImportRuleTestFiles:
    """tests/ 配下のファイルに対するテスト対応パッケージの同一視テスト"""

    def test_check_正常系_テストファイルが対応パッケージの内部モジュールをインポートしても違反しないこと(
        self,
    ):
        # Arrange: tests/unit/test_view/test_provider.py から from paladin.view.formatter import X
        # test_view → paladin.view として同一視するため対象外
        source = "from paladin.view.formatter import ViewFormatter\n"
        source_files = _make_source_files(
            (source, "tests/unit/test_view/test_provider.py"),
        )
        rule = NoDirectInternalImportRule(root_packages=("paladin",))

        result = rule.check(source_files)

        assert len(result) == 0

    def test_check_正常系_テストファイルが別パッケージの内部モジュールをインポートすると違反すること(
        self,
    ):
        # Arrange: tests/unit/test_view/test_provider.py から from paladin.check.orchestrator import X
        # test_view → paladin.view であり paladin.check は別パッケージなので違反
        source = "from paladin.check.orchestrator import CheckOrchestrator\n"
        source_files = _make_source_files(
            (source, "tests/unit/test_view/test_provider.py"),
        )
        rule = NoDirectInternalImportRule(root_packages=("paladin",))

        result = rule.check(source_files)

        assert len(result) == 1

    def test_check_正常系_絶対パスのテストファイルも対応パッケージを同一視すること(self):
        # Arrange: 絶対パス tests/unit/test_transform/test_transformer.py
        # test_transform → paladin.transform として同一視
        source = "from paladin.transform.types import TransformedDatetime\n"
        source_files = _make_source_files(
            (source, "/Users/owner/code/paladin/tests/unit/test_transform/test_transformer.py"),
        )
        rule = NoDirectInternalImportRule(root_packages=("paladin",))

        result = rule.check(source_files)

        assert len(result) == 0

    def test_check_正常系_テストファイルが複数のroot_packagesに対して対応パッケージを同一視すること(
        self,
    ):
        # Arrange: root_packages=("myapp", "tests") のとき
        # tests/unit/test_view/test_provider.py → myapp.view も同一視
        source = "from myapp.view.formatter import ViewFormatter\n"
        source_files = _make_source_files(
            (source, "tests/unit/test_view/test_provider.py"),
        )
        rule = NoDirectInternalImportRule(root_packages=("myapp", "tests"))

        result = rule.check(source_files)

        assert len(result) == 0


class TestNoDirectInternalImportRuleAbsolutePath:
    """NoDirectInternalImportRule の絶対パスでの動作テスト"""

    def test_check_正常系_絶対パスで3階層以上のインポートで違反を検出すること(self):
        source = "from paladin.check.orchestrator import CheckOrchestrator\n"
        source_files = _make_source_files(
            (source, "/Users/owner/code/paladin/src/other/module.py"),
        )
        rule = NoDirectInternalImportRule(root_packages=("paladin",))

        result = rule.check(source_files)

        assert len(result) == 1

    def test_check_正常系_絶対パスで同一パッケージ内のインポートは検出しないこと(self):
        # Arrange: 絶対パスの paladin/check/foo.py から from paladin.check.bar import Baz
        source = "from paladin.check.bar import Baz\n"
        source_files = _make_source_files(
            (source, "/Users/owner/code/paladin/src/paladin/check/foo.py"),
        )
        rule = NoDirectInternalImportRule(root_packages=("paladin",))

        result = rule.check(source_files)

        assert len(result) == 0

    def test_check_正常系_絶対パスで異なるサブパッケージのインポートは検出すること(self):
        # Arrange: 絶対パスの paladin/check/foo.py から from paladin.lint.types import SourceFile
        source = "from paladin.lint.types import SourceFile\n"
        source_files = _make_source_files(
            (source, "/Users/owner/code/paladin/src/paladin/check/foo.py"),
        )
        rule = NoDirectInternalImportRule(root_packages=("paladin",))

        result = rule.check(source_files)

        assert len(result) == 1

    def test_check_正常系_絶対パスでinit_pyのパッケージキーが正しく解決されること(self):
        # Arrange: __all__ に Foo がある絶対パスの __init__.py
        init_source = '__all__ = ["Foo"]\n'
        import_source = "from paladin.check.orchestrator import Foo\n"
        source_files = _make_source_files(
            (init_source, "/Users/owner/code/paladin/src/paladin/check/__init__.py"),
            (import_source, "/Users/owner/code/paladin/src/other/module.py"),
        )
        rule = NoDirectInternalImportRule(root_packages=("paladin",))

        result = rule.check(source_files)

        assert len(result) == 1

    def test_check_正常系_絶対パスでinit_pyに公開されていないシンボルは検出しないこと(self):
        # Arrange: __init__.py に Foo は含まれない（Bar のみ）
        init_source = '__all__ = ["Bar"]\n'
        import_source = "from paladin.check.orchestrator import Foo\n"
        source_files = _make_source_files(
            (init_source, "/Users/owner/code/paladin/src/paladin/check/__init__.py"),
            (import_source, "/Users/owner/code/paladin/src/other/module.py"),
        )
        rule = NoDirectInternalImportRule(root_packages=("paladin",))

        result = rule.check(source_files)

        assert len(result) == 0
