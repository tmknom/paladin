"""NoUnusedExportRule のテスト"""

import ast
from pathlib import Path

from paladin.rule.no_unused_export import NoUnusedExportRule
from paladin.rule.types import RuleMeta, SourceFile, SourceFiles


def _make_source_file(source: str, filename: str = "example.py") -> SourceFile:
    return SourceFile(file_path=Path(filename), tree=ast.parse(source), source=source)


def _make_source_files(*files: tuple[str, str]) -> SourceFiles:
    return SourceFiles(files=tuple(_make_source_file(src, name) for src, name in files))


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
        rule = NoUnusedExportRule()
        meta = rule.meta

        assert isinstance(meta, RuleMeta)
        assert meta.rule_id == "no-unused-export"
        assert meta.rule_name != ""
        assert meta.summary != ""
        assert meta.intent != ""
        assert meta.guidance != ""
        assert meta.suggestion != ""


class TestNoUnusedExportRulePrepare:
    """NoUnusedExportRule.prepare() のテスト"""

    def test_prepare_正常系_source_filesからルートパッケージが自動導出されること(self):
        # Arrange: src/paladin/module.py を含む SourceFiles を渡して prepare() を呼び出す
        # prepare() 後に check() でシンボルが検出されれば root_packages が設定されている
        init_source = '__all__ = ["Foo"]\n'
        stub_source = "x = 1\n"
        source_files = _make_source_files(
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
        # prepare() を呼ばずに check() を呼び出すと早期リターン
        init_source = '__all__ = ["Foo"]\n'
        source_files = _make_source_files((init_source, "src/paladin/check/__init__.py"))
        rule = NoUnusedExportRule()

        result = rule.check(source_files)

        assert result == ()


class TestNoUnusedExportRuleCheck:
    """NoUnusedExportRule の基本的な違反検出テスト"""

    def test_check_正常系_allのシンボルが別パッケージから利用されていない場合に違反を検出すること(
        self,
    ):
        # Arrange: src/paladin/check/__init__.py に __all__ = ["Foo"]、別パッケージからの利用なし
        init_source = '__all__ = ["Foo"]\n'
        source_files = _make_source_files((init_source, "src/paladin/check/__init__.py"))
        rule = _rule(("paladin",))

        result = rule.check(source_files)

        assert len(result) == 1
        assert result[0].rule_id == "no-unused-export"

    def test_check_正常系_init_py以外のファイルのallは対象外であること(self):
        # Arrange: src/paladin/check/module.py に __all__ = ["Foo"] があっても対象外
        source = '__all__ = ["Foo"]\n'
        source_files = _make_source_files((source, "src/paladin/check/module.py"))
        rule = _rule(("paladin",))

        result = rule.check(source_files)

        assert len(result) == 0

    def test_check_正常系_allが未定義の場合は空タプルを返すこと(self):
        # Arrange: __init__.py に __all__ がない
        source = "x = 1\n"
        source_files = _make_source_files((source, "src/paladin/check/__init__.py"))
        rule = _rule(("paladin",))

        result = rule.check(source_files)

        assert result == ()

    def test_check_エッジケース_空のSourceFilesで空タプルを返すこと(self):
        rule = _rule(("paladin",))
        result = rule.check(SourceFiles(files=()))
        assert result == ()

    def test_check_正常系_from_import形式で別パッケージから利用されていれば違反しないこと(self):
        # Arrange: paladin.check の CheckOrchestrator が cli.py（別パッケージ）で利用されている
        init_source = '__all__ = ["CheckOrchestrator"]\n'
        cli_source = "from paladin.check import CheckOrchestrator\n"
        source_files = _make_source_files(
            (init_source, "src/paladin/check/__init__.py"),
            (cli_source, "src/paladin/cli.py"),
        )
        rule = _rule(("paladin",))

        result = rule.check(source_files)

        assert len(result) == 0

    def test_check_正常系_同一パッケージからの利用は利用とみなさないこと(self):
        # Arrange: paladin.check.bar から paladin.check の Foo を利用しても違反
        init_source = '__all__ = ["Foo"]\n'
        bar_source = "from paladin.check import Foo\n"
        source_files = _make_source_files(
            (init_source, "src/paladin/check/__init__.py"),
            (bar_source, "src/paladin/check/bar.py"),
        )
        rule = _rule(("paladin",))

        result = rule.check(source_files)

        assert len(result) == 1

    def test_check_正常系_複数シンボルのうち利用されていないもののみ違反を検出すること(self):
        # Arrange: Used は利用されているが Unused は利用されていない
        init_source = '__all__ = ["Used", "Unused"]\n'
        cli_source = "from paladin.check import Used\n"
        source_files = _make_source_files(
            (init_source, "src/paladin/check/__init__.py"),
            (cli_source, "src/paladin/cli.py"),
        )
        rule = _rule(("paladin",))

        result = rule.check(source_files)

        assert len(result) == 1
        assert result[0].message is not None
        assert "Unused" in result[0].message

    def test_check_正常系_tests配下のファイルからの利用は利用とみなさないこと(self):
        # Arrange: tests/ 配下からの利用はカウントしない
        init_source = '__all__ = ["Foo"]\n'
        test_source = "from paladin.check import Foo\n"
        source_files = _make_source_files(
            (init_source, "src/paladin/check/__init__.py"),
            (test_source, "tests/unit/test_check/test_foo.py"),
        )
        rule = _rule(("paladin",))

        result = rule.check(source_files)

        assert len(result) == 1

    def test_check_正常系_import後の属性アクセスで利用されていれば違反しないこと(self):
        # Arrange: import paladin.check + paladin.check.CheckOrchestrator 形式
        init_source = '__all__ = ["CheckOrchestrator"]\n'
        usage_source = "import paladin.check\nx = paladin.check.CheckOrchestrator()\n"
        source_files = _make_source_files(
            (init_source, "src/paladin/check/__init__.py"),
            (usage_source, "src/paladin/cli.py"),
        )
        rule = _rule(("paladin",))

        result = rule.check(source_files)

        assert len(result) == 0

    def test_check_エッジケース_import文のみで属性アクセスがない場合は利用とみなさないこと(self):
        # Arrange: import paladin.check のみで属性アクセスなし
        init_source = '__all__ = ["CheckOrchestrator"]\n'
        usage_source = "import paladin.check\n"
        source_files = _make_source_files(
            (init_source, "src/paladin/check/__init__.py"),
            (usage_source, "src/paladin/cli.py"),
        )
        rule = _rule(("paladin",))

        result = rule.check(source_files)

        assert len(result) == 1

    def test_check_正常系_init_pyにall以外の文がある場合もallを正しく抽出すること(self):
        # Arrange: import os が L87 の continue を通過し、__all__ は正しく抽出される
        init_source = 'import os\n__all__ = ["Foo"]\n'
        source_files = _make_source_files((init_source, "src/paladin/check/__init__.py"))
        rule = _rule(("paladin",))

        result = rule.check(source_files)

        assert len(result) == 1
        assert "Foo" in result[0].message

    def test_check_正常系_プロダクションファイルの相対インポートは利用収集をスキップすること(self):
        # Arrange: from . import something は relative import（level != 0）なので除外
        init_source = '__all__ = ["Foo"]\n'
        rel_import_source = "from . import something\n"
        source_files = _make_source_files(
            (init_source, "src/paladin/check/__init__.py"),
            (rel_import_source, "src/paladin/rule/bar.py"),
        )
        rule = _rule(("paladin",))

        result = rule.check(source_files)

        assert len(result) == 1

    def test_check_正常系_all_exportsに一致しないインポートは利用収集をスキップすること(self):
        # Arrange: from paladin.rule import X は all_exports のキー paladin.check と一致しない
        init_source = '__all__ = ["Foo"]\n'
        other_import_source = "from paladin.rule import X\n"
        source_files = _make_source_files(
            (init_source, "src/paladin/check/__init__.py"),
            (other_import_source, "src/paladin/cli.py"),
        )
        rule = _rule(("paladin",))

        result = rule.check(source_files)

        assert len(result) == 1

    def test_check_正常系_属性アクセスのモジュール名がall_exportsに一致しない場合スキップすること(
        self,
    ):
        # Arrange: import paladin.rule + paladin.rule.X は all_exports（paladin.check）に存在しない
        init_source = '__all__ = ["Foo"]\n'
        usage_source = "import paladin.rule\nx = paladin.rule.X\n"
        source_files = _make_source_files(
            (init_source, "src/paladin/check/__init__.py"),
            (usage_source, "src/paladin/cli.py"),
        )
        rule = _rule(("paladin",))

        result = rule.check(source_files)

        assert len(result) == 1

    def test_check_正常系_属性アクセスでの同一パッケージからの利用は利用とみなさないこと(self):
        # Arrange: paladin.check パッケージ内ファイルからの属性アクセスは除外
        init_source = '__all__ = ["Foo"]\n'
        same_pkg_source = "import paladin.check\nx = paladin.check.Foo\n"
        source_files = _make_source_files(
            (init_source, "src/paladin/check/__init__.py"),
            (same_pkg_source, "src/paladin/check/bar.py"),
        )
        rule = _rule(("paladin",))

        result = rule.check(source_files)

        assert len(result) == 1


class TestNoUnusedExportRuleViolationFields:
    """違反メッセージフィールドのテスト"""

    def test_check_正常系_違反のフィールド値が正しいこと(self):
        # Arrange: line 1 に __all__ が定義されている
        init_source = '__all__ = ["Foo"]\n'
        source_files = _make_source_files((init_source, "src/paladin/check/__init__.py"))
        rule = _rule(("paladin",))

        result = rule.check(source_files)

        assert len(result) == 1
        violation = result[0]
        assert violation.file == Path("src/paladin/check/__init__.py")
        assert violation.line == 1
        assert violation.column == 0
        assert violation.rule_id == "no-unused-export"
        assert violation.rule_name != ""
        assert "Foo" in violation.message
        assert violation.reason != ""
        assert "Foo" in violation.suggestion

    def test_check_正常系_複数ファイルの違反を集約して返すこと(self):
        # Arrange: 2つの __init__.py にそれぞれ未使用シンボル
        init1_source = '__all__ = ["Foo"]\n'
        init2_source = '__all__ = ["Bar"]\n'
        source_files = _make_source_files(
            (init1_source, "src/paladin/check/__init__.py"),
            (init2_source, "src/paladin/rule/__init__.py"),
        )
        rule = _rule(("paladin",))

        result = rule.check(source_files)

        assert len(result) == 2


class TestNoUnusedExportRuleEdgeCases:
    """NoUnusedExportRule のエッジケーステスト"""

    def test_check_エッジケース_多重代入ターゲットのAssignはスキップすること(self):
        # Arrange: a = b = 1 は len(node.targets) != 1 で continue される
        init_source = 'a = b = 1\n__all__ = ["Foo"]\n'
        source_files = _make_source_files((init_source, "src/paladin/check/__init__.py"))
        rule = _rule(("paladin",))

        result = rule.check(source_files)

        assert len(result) == 1
        assert "Foo" in result[0].message

    def test_check_エッジケース_関数呼び出し結果の属性アクセスは利用収集をスキップすること(self):
        # Arrange: func().Foo は _reconstruct_module_name が None を返すため除外
        init_source = '__all__ = ["Foo"]\n'
        usage_source = "import paladin.check\nfunc().Foo\n"
        source_files = _make_source_files(
            (init_source, "src/paladin/check/__init__.py"),
            (usage_source, "src/paladin/cli.py"),
        )
        rule = _rule(("paladin",))

        result = rule.check(source_files)

        assert len(result) == 1

    def test_check_エッジケース_allの要素に非定数が含まれる場合はスキップすること(self):
        # Arrange: __all__ = [variable] のように変数を含む場合は対象外
        init_source = "__all__ = [variable]\n"
        source_files = _make_source_files((init_source, "src/paladin/check/__init__.py"))
        rule = _rule(("paladin",))

        result = rule.check(source_files)

        assert len(result) == 0

    def test_check_エッジケース_allの値がリスト以外の場合はスキップすること(self):
        # Arrange: __all__ = "Foo" のように値がリストでない場合はスキップ
        init_source = '__all__ = "Foo"\n'
        source_files = _make_source_files((init_source, "src/paladin/check/__init__.py"))
        rule = _rule(("paladin",))

        result = rule.check(source_files)

        assert len(result) == 0

    def test_check_エッジケース_パス深さが不足するinit_pyはスキップされること(self):
        # Arrange: src/__init__.py のようにセグメント不足で resolve_exact_package_path が None を返す
        init_source = '__all__ = ["Foo"]\n'
        source_files = _make_source_files((init_source, "src/__init__.py"))
        rule = _rule(("paladin",))

        result = rule.check(source_files)

        assert len(result) == 0


class TestNoUnusedExportRuleIntegration:
    """NoUnusedExportRule の統合テスト"""

    def test_check_正常系_prepare後にcheckが正しく動作すること(self):
        # Arrange: prepare() で root_packages を自動導出してから check() で違反を検出
        init_source = '__all__ = ["Foo"]\n'
        stub_source = "x = 1\n"
        source_files = _make_source_files(
            (init_source, "src/paladin/check/__init__.py"),
            (stub_source, "src/paladin/stub.py"),
        )
        rule = NoUnusedExportRule()
        rule.prepare(source_files)

        result = rule.check(source_files)

        assert len(result) == 1
        assert result[0].rule_id == "no-unused-export"

    def test_check_正常系_絶対パスのファイルでも正しく動作すること(self):
        # Arrange: 絶対パス形式の SourceFile でもパッケージ解決が正常に機能する
        init_source = '__all__ = ["Foo"]\n'
        cli_source = "from paladin.check import Foo\n"
        source_files = _make_source_files(
            (init_source, "/Users/owner/code/paladin/src/paladin/check/__init__.py"),
            (cli_source, "/Users/owner/code/paladin/src/paladin/cli.py"),
        )
        rule = _rule(("paladin",))

        result = rule.check(source_files)

        assert len(result) == 0

    def test_check_正常系_RuleSetを通じた場合に防御的に動作すること(self):
        # Arrange: NoUnusedExportRule は prepare() なしでも check() が安全に動作する
        init_source = '__all__ = ["Foo"]\n'
        source_files = _make_source_files((init_source, "src/paladin/check/__init__.py"))
        rule = NoUnusedExportRule()
        # prepare() を呼ばない（RuleSet.run() が _multi_file_rules に prepare() を呼ばない現状を再現）

        result = rule.check(source_files)

        # _root_packages が空のため早期リターンし、空タプルを返す
        assert result == ()
