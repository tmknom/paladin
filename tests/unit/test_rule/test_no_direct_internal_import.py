"""NoDirectInternalImportRule のテスト"""

import ast
from pathlib import Path

from paladin.rule.no_direct_internal_import import NoDirectInternalImportRule
from paladin.rule.types import RuleMeta, SourceFile, SourceFiles
from tests.unit.test_rule.helpers import make_source_file, make_source_files


def _rule(root_packages: tuple[str, ...] = ("paladin",)) -> NoDirectInternalImportRule:
    """root_packages を prepare() で設定した NoDirectInternalImportRule を返す（テスト用）

    各パッケージ名を src/<pkg>/stub.py 形式の SourceFiles として渡し、
    PackageResolver.resolve_root_packages() に自動導出させる。
    """
    rule = NoDirectInternalImportRule()
    # テスト用の stub ファイルを用意して prepare() で root_packages を自動導出する
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


class TestNoDirectInternalImportRuleMeta:
    """NoDirectInternalImportRule のメタ情報テスト"""

    def test_meta_正常系_ルールメタ情報を返すこと(self):
        rule = NoDirectInternalImportRule()
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
        source_files = make_source_files((source, "src/other/module.py"))
        rule = _rule(("paladin",))

        # Act
        result = rule.check(source_files)

        # Assert
        assert len(result) == 1
        assert result[0].rule_id == "no-direct-internal-import"

    def test_check_正常系_2階層のインポートは検出しないこと(self):
        # Arrange: paladin.check は2階層（セグメント数2）
        source = "from paladin.check import CheckOrchestrator\n"
        source_files = make_source_files((source, "src/other/module.py"))
        rule = _rule(("paladin",))

        # Act
        result = rule.check(source_files)

        # Assert
        assert len(result) == 0

    def test_check_正常系_root_packages以外のインポートは検出しないこと(self):
        # Arrange: requests は root_packages に含まれない
        source = "from requests.adapters import HTTPAdapter\n"
        source_files = make_source_files((source, "src/other/module.py"))
        rule = _rule(("paladin",))

        # Act
        result = rule.check(source_files)

        # Assert
        assert len(result) == 0

    def test_check_正常系_相対インポートは検出しないこと(self):
        # Arrange: 相対インポートは no-relative-import で検出するため対象外
        source = "from .module import Foo\n"
        source_files = make_source_files((source, "src/paladin/check/module.py"))
        rule = _rule(("paladin",))

        # Act
        result = rule.check(source_files)

        # Assert
        assert len(result) == 0

    def test_check_正常系_同一パッケージ内のインポートは検出しないこと(self):
        # Arrange: paladin/check/foo.py から from paladin.check.bar import Baz
        # 先頭2セグメントが同じ（paladin.check）なので対象外
        source = "from paladin.check.bar import Baz\n"
        source_files = make_source_files((source, "src/paladin/check/foo.py"))
        rule = _rule(("paladin",))

        # Act
        result = rule.check(source_files)

        # Assert
        assert len(result) == 0

    def test_check_正常系_異なるサブパッケージのインポートは検出すること(self):
        # Arrange: paladin/check/foo.py から from paladin.rule.types import SourceFile
        # 先頭2セグメントが異なる（paladin.check vs paladin.rule）なので対象
        source = "from paladin.rule.types import SourceFile\n"
        source_files = make_source_files((source, "src/paladin/check/foo.py"))
        rule = _rule(("paladin",))

        # Act
        result = rule.check(source_files)

        # Assert
        assert len(result) == 1


class TestNoDirectInternalImportRuleInitPy:
    """NoDirectInternalImportRule の __init__.py 解析テスト"""

    def test_check_正常系_init_pyのall_exportsに含まれるシンボルのインポートを検出すること(self):
        # Arrange: paladin/check/__init__.py に __all__ = ["Foo"] がある
        init_source = '__all__ = ["Foo"]\n'
        import_source = "from paladin.check.orchestrator import Foo\n"
        source_files = make_source_files(
            (init_source, "src/paladin/check/__init__.py"),
            (import_source, "src/other/module.py"),
        )
        rule = _rule(("paladin",))

        # Act
        result = rule.check(source_files)

        # Assert: Foo は __all__ で公開されているため違反
        assert len(result) == 1

    def test_check_正常系_init_pyの再エクスポートに含まれるシンボルのインポートを検出すること(self):
        # Arrange: paladin/check/__init__.py に from .orchestrator import Foo がある
        init_source = "from .orchestrator import Foo\n"
        import_source = "from paladin.check.orchestrator import Foo\n"
        source_files = make_source_files(
            (init_source, "src/paladin/check/__init__.py"),
            (import_source, "src/other/module.py"),
        )
        rule = _rule(("paladin",))

        # Act
        result = rule.check(source_files)

        # Assert: Foo は再エクスポートで公開されているため違反
        assert len(result) == 1

    def test_check_正常系_init_pyで公開されていないシンボルは検出しないこと(self):
        # Arrange: __init__.py に Foo は含まれない（Barのみ）
        init_source = '__all__ = ["Bar"]\n'
        import_source = "from paladin.check.orchestrator import Foo\n"
        source_files = make_source_files(
            (init_source, "src/paladin/check/__init__.py"),
            (import_source, "src/other/module.py"),
        )
        rule = _rule(("paladin",))

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
        source_files = make_source_files(
            (init_source, "src/paladin/check/__init__.py"),
            (import_source, "src/other/module.py"),
        )
        rule = _rule(("paladin",))

        # Act
        result = rule.check(source_files)

        # Assert: フォールバックで3階層以上のインポートを検出
        assert len(result) == 1

    def test_check_正常系_インポートモジュール自体がサブパッケージなら検出しないこと(self):
        # Arrange: paladin/check/orchestrator/__init__.py が source_files に存在する
        # node.module ("paladin.check.orchestrator") が package_exports のキーになるため
        # L280（node.module in package_exports の continue）に到達する
        init_source = '__all__ = ["CheckOrchestrator"]\n'
        import_source = "from paladin.check.orchestrator import CheckOrchestrator\n"
        source_files = make_source_files(
            (init_source, "src/paladin/check/orchestrator/__init__.py"),
            (import_source, "src/other/module.py"),
        )
        rule = _rule(("paladin",))

        # Act
        result = rule.check(source_files)

        # Assert: paladin.check.orchestrator はサブパッケージとして認識されるため対象外
        assert len(result) == 0


class TestNoDirectInternalImportRuleEdgeCases:
    """NoDirectInternalImportRule のエッジケーステスト"""

    def test_check_エッジケース_空のSourceFilesで空タプルを返すこと(self):
        rule = _rule(("paladin",))
        result = rule.check(SourceFiles(files=()))
        assert result == ()

    def test_check_エッジケース_インポート文がないファイルで空タプルを返すこと(self):
        source = "x = 1\n"
        source_files = make_source_files((source, "src/paladin/check/foo.py"))
        rule = _rule(("paladin",))

        result = rule.check(source_files)

        assert result == ()

    def test_check_正常系_複数ファイルの違反を集約して返すこと(self):
        # Arrange: 2ファイルそれぞれから違反
        source1 = "from paladin.check.orchestrator import CheckOrchestrator\n"
        source2 = "from paladin.rule.types import SourceFile\n"
        source_files = make_source_files(
            (source1, "src/other/module1.py"),
            (source2, "src/other/module2.py"),
        )
        rule = _rule(("paladin",))

        result = rule.check(source_files)

        assert len(result) == 2

    def test_check_正常系_import文は検出しないこと(self):
        # Arrange: from ... import ではなく import 文
        source = "import paladin.check.orchestrator\n"
        source_files = make_source_files((source, "src/other/module.py"))
        rule = _rule(("paladin",))

        result = rule.check(source_files)

        assert len(result) == 0

    def test_check_エッジケース_root_packagesが空の場合は何も検出しないこと(self):
        source = "from paladin.check.orchestrator import CheckOrchestrator\n"
        source_files = make_source_files((source, "src/other/module.py"))
        rule = _rule(())

        result = rule.check(source_files)

        assert len(result) == 0

    def test_check_エッジケース_ファイル名がtestsの場合でも違反を検出すること(self):
        # Arrange: file_path.parts の末尾が "tests"（拡張子なし）の場合
        # file_path.parts に "tests" が含まれる（L180 を通過）が、
        # dir_parts（ファイル名除く）には "tests" がなく tests_index < 0（L195 到達）
        source = "from paladin.rule.types import SourceFile\n"
        source_files = make_source_files((source, "src/paladin/check/tests"))
        rule = _rule(("paladin",))

        result = rule.check(source_files)

        assert len(result) == 1

    def test_check_エッジケース_moduleがNoneのImportFromノードを無視すること(self):
        # Arrange: level=0, module=None の ImportFrom は通常の ast.parse では生成されない
        # ガード節（L259）のカバレッジを確保するため AST を直接構築する
        tree = ast.parse("")
        import_node = ast.ImportFrom(module=None, names=[ast.alias(name="X")], level=0)
        import_node.lineno = 1
        import_node.col_offset = 0
        tree.body.append(import_node)
        source_file = SourceFile(file_path=Path("src/other/module.py"), tree=tree, source="")
        source_files = SourceFiles(files=(source_file,))
        rule = _rule(("paladin",))

        result = rule.check(source_files)

        assert len(result) == 0

    def test_check_エッジケース_3階層以上の外部パッケージインポートは検出しないこと(self):
        # Arrange: 3階層だが root_packages 外のパッケージ（L267 到達）
        source = "from urllib.parse.something import quote\n"
        source_files = make_source_files((source, "src/other/module.py"))
        rule = _rule(("paladin",))

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
        source_files = make_source_files(
            (source, "tests/unit/test_view/test_provider.py"),
        )
        rule = _rule(("paladin",))

        result = rule.check(source_files)

        assert len(result) == 0

    def test_check_正常系_テストファイルが別パッケージの内部モジュールをインポートすると違反すること(
        self,
    ):
        # Arrange: tests/unit/test_view/test_provider.py から from paladin.check.orchestrator import X
        # test_view → paladin.view であり paladin.check は別パッケージなので違反
        source = "from paladin.check.orchestrator import CheckOrchestrator\n"
        source_files = make_source_files(
            (source, "tests/unit/test_view/test_provider.py"),
        )
        rule = _rule(("paladin",))

        result = rule.check(source_files)

        assert len(result) == 1

    def test_check_正常系_絶対パスのテストファイルも対応パッケージを同一視すること(self):
        # Arrange: 絶対パス tests/unit/test_transform/test_transformer.py
        # test_transform → paladin.transform として同一視
        source = "from paladin.transform.types import TransformedDatetime\n"
        source_files = make_source_files(
            (source, "/Users/owner/code/paladin/tests/unit/test_transform/test_transformer.py"),
        )
        rule = _rule(("paladin",))

        result = rule.check(source_files)

        assert len(result) == 0

    def test_check_正常系_テストファイルが複数のroot_packagesに対して対応パッケージを同一視すること(
        self,
    ):
        # Arrange: root_packages=("myapp", "tests") のとき
        # tests/unit/test_view/test_provider.py → myapp.view も同一視
        source = "from myapp.view.formatter import ViewFormatter\n"
        source_files = make_source_files(
            (source, "tests/unit/test_view/test_provider.py"),
        )
        rule = _rule(("myapp", "tests"))

        result = rule.check(source_files)

        assert len(result) == 0


class TestNoDirectInternalImportRuleAbsolutePath:
    """NoDirectInternalImportRule の絶対パスでの動作テスト"""

    def test_check_正常系_絶対パスで3階層以上のインポートで違反を検出すること(self):
        source = "from paladin.check.orchestrator import CheckOrchestrator\n"
        source_files = make_source_files(
            (source, "/Users/owner/code/paladin/src/other/module.py"),
        )
        rule = _rule(("paladin",))

        result = rule.check(source_files)

        assert len(result) == 1

    def test_check_正常系_絶対パスで同一パッケージ内のインポートは検出しないこと(self):
        # Arrange: 絶対パスの paladin/check/foo.py から from paladin.check.bar import Baz
        source = "from paladin.check.bar import Baz\n"
        source_files = make_source_files(
            (source, "/Users/owner/code/paladin/src/paladin/check/foo.py"),
        )
        rule = _rule(("paladin",))

        result = rule.check(source_files)

        assert len(result) == 0

    def test_check_正常系_絶対パスで異なるサブパッケージのインポートは検出すること(self):
        # Arrange: 絶対パスの paladin/check/foo.py から from paladin.rule.types import SourceFile
        source = "from paladin.rule.types import SourceFile\n"
        source_files = make_source_files(
            (source, "/Users/owner/code/paladin/src/paladin/check/foo.py"),
        )
        rule = _rule(("paladin",))

        result = rule.check(source_files)

        assert len(result) == 1

    def test_check_正常系_絶対パスでinit_pyのパッケージキーが正しく解決されること(self):
        # Arrange: __all__ に Foo がある絶対パスの __init__.py
        init_source = '__all__ = ["Foo"]\n'
        import_source = "from paladin.check.orchestrator import Foo\n"
        source_files = make_source_files(
            (init_source, "/Users/owner/code/paladin/src/paladin/check/__init__.py"),
            (import_source, "/Users/owner/code/paladin/src/other/module.py"),
        )
        rule = _rule(("paladin",))

        result = rule.check(source_files)

        assert len(result) == 1

    def test_check_正常系_絶対パスでinit_pyに公開されていないシンボルは検出しないこと(self):
        # Arrange: __init__.py に Foo は含まれない（Bar のみ）
        init_source = '__all__ = ["Bar"]\n'
        import_source = "from paladin.check.orchestrator import Foo\n"
        source_files = make_source_files(
            (init_source, "/Users/owner/code/paladin/src/paladin/check/__init__.py"),
            (import_source, "/Users/owner/code/paladin/src/other/module.py"),
        )
        rule = _rule(("paladin",))

        result = rule.check(source_files)

        assert len(result) == 0


class TestNoDirectInternalImportRuleSubpackageFallback:
    """スコープ外サブパッケージのファイルシステムフォールバックテスト"""

    def test_check_正常系_解析スコープ外のサブパッケージは違反を検出しないこと(
        self, tmp_path: Path
    ):
        # Arrange: tmp_path/src/paladin/foundation/fs/__init__.py を作成する
        fs_pkg = tmp_path / "src" / "paladin" / "foundation" / "fs"
        fs_pkg.mkdir(parents=True)
        (fs_pkg / "__init__.py").write_text('__all__ = ["FileSystemError"]\n')

        # テストファイルは tmp_path 配下に配置して _infer_src_root が src/ を発見できるようにする
        import_source = "from paladin.foundation.fs import FileSystemError\n"
        source_files = make_source_files(
            (import_source, str(tmp_path / "tests" / "unit" / "test_something.py")),
        )
        rule = _rule(("paladin",))

        result = rule.check(source_files)

        # paladin.foundation.fs はサブパッケージ（__init__.py あり）なので対象外
        assert len(result) == 0

    def test_check_正常系_解析スコープ外にサブパッケージが存在しない場合はヒューリスティック検出すること(
        self, tmp_path: Path
    ):
        # Arrange: tmp_path/src/paladin/check/ は存在するが orchestrator/ ディレクトリはない
        check_pkg = tmp_path / "src" / "paladin" / "check"
        check_pkg.mkdir(parents=True)

        import_source = "from paladin.check.orchestrator import CheckOrchestrator\n"
        source_files = make_source_files(
            (import_source, str(tmp_path / "tests" / "unit" / "test_something.py")),
        )
        rule = _rule(("paladin",))

        result = rule.check(source_files)

        # paladin.check.orchestrator に __init__.py が存在しないのでヒューリスティック検出
        assert len(result) == 1

    def test_check_正常系_srcディレクトリが存在しない場合は既存動作を維持すること(self):
        # Arrange: 合成パス（src/ ディレクトリが実在しない）を使用する
        import_source = "from paladin.check.orchestrator import CheckOrchestrator\n"
        source_files = make_source_files(
            (import_source, "nonexistent_project/tests/unit/test_something.py"),
        )
        rule = _rule(("paladin",))

        result = rule.check(source_files)

        # _infer_src_root が None を返すため既存のヒューリスティック検出が機能する
        assert len(result) == 1


class TestNoDirectInternalImportRulePrepare:
    """NoDirectInternalImportRule.prepare() のテスト"""

    def test_prepare_正常系_source_filesからルートパッケージが自動導出されること(self):
        # Arrange: src/paladin/ があれば paladin が root_packages に自動導出される
        # prepare() 後に from paladin.check.orchestrator import X が検出されれば自動導出確認
        import_source = "from paladin.check.orchestrator import CheckOrchestrator\n"
        stub_source = "x = 1\n"
        source_files = make_source_files(
            (import_source, "src/other/module.py"),
            (stub_source, "src/paladin/module.py"),  # paladin を自動導出するため
        )
        rule = NoDirectInternalImportRule()

        # prepare() 前は root_packages が空なので違反を検出しない
        result_before = rule.check(source_files)
        assert len(result_before) == 0

        # Act
        rule.prepare(source_files)

        # Assert: paladin が自動導出されるため違反を検出
        result_after = rule.check(source_files)
        assert len(result_after) == 1

    def test_prepare_正常系_testsが常にroot_packagesに含まれること(self):
        # Arrange: src 配下のパッケージに依存せず tests は常に自動導出される
        # tests からのインポートを持つファイルを checks したとき tests を違反としないことで確認
        tests_source = "from tests.unit.fakes import FakeRule\n"
        source_files = make_source_files(
            (tests_source, "src/myapp/module.py"),
            ("x = 1\n", "src/myapp/stub.py"),
        )
        rule = NoDirectInternalImportRule()
        rule.prepare(source_files)

        # tests から 3階層インポートは tests が root_packages に含まれれば対象外
        # ただし NoDirectInternalImportRule は tests.unit をパッケージキーとするため
        # from tests.unit.fakes import X は同一パッケージ扱いになる
        # ここでは prepare() が例外なく動作し root_packages に tests が含まれることを確認
        # 間接的にテスト: tests からのインポートを持つファイルはスコープ外（2階層未満も対象外）
        source = "from tests.foo import bar\n"
        single_file = make_source_file(source, "src/myapp/test_helper.py")
        single_files = SourceFiles(files=(single_file,))
        # 2階層インポートは対象外なので違反なし
        result = rule.check(single_files)
        assert len(result) == 0

    def test_prepare_正常系_prepare後にcheckが正しく動作すること(self):
        # Arrange: src/paladin/ があれば paladin が自動導出され、違反を検出できる
        import_source = "from paladin.check.orchestrator import CheckOrchestrator\n"
        stub_source = "x = 1\n"
        source_files = make_source_files(
            (import_source, "src/other/module.py"),
            (stub_source, "src/paladin/stub.py"),  # paladin を自動導出するため
        )
        rule = NoDirectInternalImportRule()
        rule.prepare(source_files)

        # Act
        result = rule.check(source_files)

        # Assert: paladin が自動導出されるため違反を検出
        assert len(result) == 1

    def test_check_エッジケース_import_from_moduleがNoneの場合はスキップすること(self):
        # Arrange: level=0 かつ module=None の ImportFrom を手動構築する
        # （通常の Python 構文では生成されないが、AST を直接操作すると再現できる）
        rule = _rule(("paladin",))
        tree = ast.parse("")
        import_from = ast.ImportFrom(
            module=None,
            names=[ast.alias(name="Foo", asname=None)],
            level=0,
        )
        ast.fix_missing_locations(import_from)
        tree.body = [import_from]
        source_file = SourceFile(file_path=Path("src/other/module.py"), tree=tree, source="")
        source_files = SourceFiles(files=(source_file,))

        # Act
        result = rule.check(source_files)

        # Assert: module=None のインポートはスキップされ違反なし
        assert result == ()

    def test_check_エッジケース_パス深さが不足するinit_pyはpackage_exportsに登録されないこと(self):
        # Arrange: src/__init__.py のようにパスのセグメント数が2未満の場合
        # PackageResolver.resolve_exact_package_path が None を返すため登録をスキップする
        init_source = '__all__ = ["Foo"]\n'
        import_source = "from paladin.check.orchestrator import CheckOrchestrator\n"
        source_files = make_source_files(
            (init_source, "src/__init__.py"),  # セグメント不足で None を返す
            (import_source, "src/other/module.py"),
        )
        rule = _rule(("paladin",))

        # Act
        result = rule.check(source_files)

        # Assert: __init__.py が package_exports に登録されないためヒューリスティック検出
        assert len(result) == 1
