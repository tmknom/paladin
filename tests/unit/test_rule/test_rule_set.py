import ast
from pathlib import Path

from paladin.rule.rule_set import RuleSet
from paladin.rule.types import RuleMeta, SourceFile, SourceFiles, Violation, Violations
from tests.unit.fakes import FakeMultiFileRule, FakeRule


def _make_source_file(source: str, filename: str = "__init__.py") -> SourceFile:
    return SourceFile(file_path=Path(filename), tree=ast.parse(source), source=source)


def _make_source_files(*sources_and_names: tuple[str, str]) -> SourceFiles:
    return SourceFiles(files=tuple(_make_source_file(src, name) for src, name in sources_and_names))


def _make_violation(file: str = "src/paladin/__init__.py") -> Violation:
    return Violation(
        file=Path(file),
        line=1,
        column=0,
        rule_id="fake-rule",
        rule_name="Fake Rule",
        message="fake message",
        reason="fake reason",
        suggestion="fake suggestion",
    )


class TestRuleSet:
    """RuleSetクラスのテスト"""

    def test_run_正常系_単一ルールの違反をViolationsとして返すこと(self):
        # Arrange
        violation = _make_violation()
        rule = FakeRule(violations=(violation,))
        rule_set = RuleSet(rules=(rule,))
        source_files = _make_source_files(("x = 1\n", "__init__.py"))

        # Act
        result = rule_set.run(source_files)

        # Assert
        assert isinstance(result, Violations)
        assert len(result) == 1

    def test_run_正常系_違反なしの場合に空のViolationsを返すこと(self):
        # Arrange
        rule = FakeRule(violations=())
        rule_set = RuleSet(rules=(rule,))
        source_files = _make_source_files(("x = 1\n", "__init__.py"))

        # Act
        result = rule_set.run(source_files)

        # Assert
        assert isinstance(result, Violations)
        assert len(result) == 0

    def test_run_エッジケース_空のSourceFilesで空のViolationsを返すこと(self):
        # Arrange
        rule = FakeRule(violations=(_make_violation(),))
        rule_set = RuleSet(rules=(rule,))
        source_files = SourceFiles(files=())

        # Act
        result = rule_set.run(source_files)

        # Assert
        assert isinstance(result, Violations)
        assert len(result) == 0

    def test_run_正常系_複数ファイルに同じルールを適用して違反を集約すること(self):
        # Arrange
        violation = _make_violation()
        rule = FakeRule(violations=(violation,))
        rule_set = RuleSet(rules=(rule,))
        source_files = _make_source_files(
            ("x = 1\n", "a/__init__.py"),
            ("y = 2\n", "b/__init__.py"),
        )

        # Act
        result = rule_set.run(source_files)

        # Assert
        assert isinstance(result, Violations)
        assert len(result) == 2

    def test_run_正常系_disabled_rule_idsに該当するルールの違反をスキップすること(self):
        # Arrange
        violation_a = Violation(
            file=Path("src/__init__.py"),
            line=1,
            column=0,
            rule_id="rule-a",
            rule_name="Rule A",
            message="msg",
            reason="reason",
            suggestion="suggestion",
        )
        violation_b = Violation(
            file=Path("src/__init__.py"),
            line=1,
            column=0,
            rule_id="rule-b",
            rule_name="Rule B",
            message="msg",
            reason="reason",
            suggestion="suggestion",
        )
        rule_a = FakeRule(rule_id="rule-a", violations=(violation_a,))
        rule_b = FakeRule(rule_id="rule-b", violations=(violation_b,))
        rule_set = RuleSet(rules=(rule_a, rule_b))
        source_files = _make_source_files(("x = 1\n", "__init__.py"))

        # Act
        result = rule_set.run(source_files, disabled_rule_ids=frozenset({"rule-a"}))

        # Assert
        assert len(result) == 1
        assert result.items[0].rule_id == "rule-b"

    def test_run_エッジケース_disabled_rule_idsが空の場合全ルール実行すること(self):
        # Arrange
        violation = _make_violation()
        rule_a = FakeRule(rule_id="rule-a", violations=(violation,))
        rule_b = FakeRule(rule_id="rule-b", violations=(violation,))
        rule_set = RuleSet(rules=(rule_a, rule_b))
        source_files = _make_source_files(("x = 1\n", "__init__.py"))

        # Act
        result = rule_set.run(source_files, disabled_rule_ids=frozenset())

        # Assert: 両ルールが実行される
        assert len(result) == 2

    def test_run_正常系_disabled_rule_idsのデフォルト値で全ルール実行すること(self):
        # Arrange
        violation = _make_violation()
        rule = FakeRule(violations=(violation,))
        rule_set = RuleSet(rules=(rule,))
        source_files = _make_source_files(("x = 1\n", "__init__.py"))

        # Act: デフォルト引数（引数なし）で呼び出す
        result = rule_set.run(source_files)

        # Assert
        assert len(result) == 1

    def test_rule_ids_正常系_登録ルールのIDセットを返すこと(self):
        # Arrange
        rule_a = FakeRule(rule_id="rule-a")
        rule_b = FakeRule(rule_id="rule-b")
        rule_set = RuleSet(rules=(rule_a, rule_b))

        # Act
        result = rule_set.rule_ids

        # Assert
        assert result == frozenset({"rule-a", "rule-b"})

    def test_list_rules_正常系_登録済みルールのメタ情報を返すこと(self):
        # Arrange
        rule = FakeRule()
        rule_set = RuleSet(rules=(rule,))

        # Act
        result = rule_set.list_rules()

        # Assert
        assert len(result) == 1
        assert isinstance(result[0], RuleMeta)
        assert result[0].rule_id == "fake-rule"
        assert result[0].rule_name == "Fake Rule"

    def test_list_rules_エッジケース_ルール未登録で空タプルを返すこと(self):
        # Arrange
        rule_set = RuleSet(rules=())

        # Act
        result = rule_set.list_rules()

        # Assert
        assert result == ()

    def test_find_rule_正常系_登録済みrule_idに一致するRuleMetaを返すこと(self):
        # Arrange
        rule = FakeRule(rule_id="PAL001", rule_name="Fake Rule", summary="Fake summary")
        rule_set = RuleSet(rules=(rule,))

        # Act
        result = rule_set.find_rule("PAL001")

        # Assert
        assert result is not None
        assert isinstance(result, RuleMeta)
        assert result.rule_id == "PAL001"
        assert result.rule_name == "Fake Rule"

    def test_find_rule_エッジケース_存在しないrule_idでNoneを返すこと(self):
        # Arrange
        rule = FakeRule(rule_id="PAL001")
        rule_set = RuleSet(rules=(rule,))

        # Act
        result = rule_set.find_rule("nonexistent")

        # Assert
        assert result is None


class TestRuleSetPerFileDisabled:
    """RuleSet.run の per_file_disabled パラメータのテスト"""

    def test_run_正常系_per_file_disabledでファイル別にルールを無効化できること(self):
        # Arrange: file_a.py では rule-a を無効化、file_b.py では有効
        # FakeRule は全ファイルに violations を返すため、per_file_disabled によってファイル別に
        # ルールの実行自体がスキップされる（違反数 = ファイル数 - 無効化ファイル数）
        file_a = Path("file_a.py")
        violation = Violation(
            file=Path("any.py"),
            line=1,
            column=0,
            rule_id="rule-a",
            rule_name="Rule A",
            message="msg",
            reason="reason",
            suggestion="suggestion",
        )
        rule_a = FakeRule(rule_id="rule-a", violations=(violation,))
        rule_b = FakeRule(rule_id="rule-b", violations=(violation,))
        rule_set = RuleSet(rules=(rule_a, rule_b))
        source_files = _make_source_files(("x = 1\n", "file_a.py"), ("y = 2\n", "file_b.py"))

        # Act: file_a.py では rule-a を無効化。file_b.py では全ルール有効
        result = rule_set.run(
            source_files,
            per_file_disabled={file_a: frozenset({"rule-a"})},
        )

        # Assert:
        # file_a.py: rule-a 無効 → rule-b のみ実行 → 1件
        # file_b.py: 全有効 → rule-a + rule-b → 2件
        # 合計: 3件
        assert len(result) == 3

    def test_run_正常系_per_file_disabledに含まれないファイルはdisabled_rule_idsを使用すること(
        self,
    ):
        # Arrange: file_a.py は per_file_disabled で全有効（frozenset()）、
        # file_b.py は per_file_disabled にエントリなし → disabled_rule_ids にフォールバック
        file_a = Path("file_a.py")
        violation = Violation(
            file=Path("any.py"),
            line=1,
            column=0,
            rule_id="rule-a",
            rule_name="Rule A",
            message="msg",
            reason="reason",
            suggestion="suggestion",
        )
        rule_a = FakeRule(rule_id="rule-a", violations=(violation,))
        rule_set = RuleSet(rules=(rule_a,))
        source_files = _make_source_files(("x = 1\n", "file_a.py"), ("y = 2\n", "file_b.py"))

        # Act: file_a.py は空 set（全有効）、file_b.py はフォールバックで rule-a 無効
        result = rule_set.run(
            source_files,
            disabled_rule_ids=frozenset({"rule-a"}),
            per_file_disabled={file_a: frozenset()},
        )

        # Assert: file_a.py の rule-a が実行されて1件、file_b.py はフォールバックで無効化されて0件
        assert len(result) == 1

    def test_run_エッジケース_per_file_disabledがNoneの場合既存動作と同じこと(self):
        # Arrange
        violation = _make_violation()
        rule_a = FakeRule(rule_id="rule-a", violations=(violation,))
        rule_set = RuleSet(rules=(rule_a,))
        source_files = _make_source_files(("x = 1\n", "__init__.py"))

        # Act: per_file_disabled=None（デフォルト）
        result = rule_set.run(
            source_files,
            disabled_rule_ids=frozenset({"rule-a"}),
            per_file_disabled=None,
        )

        # Assert: rule-a が disabled されるため違反なし
        assert len(result) == 0

    def test_run_エッジケース_per_file_disabledが空dictの場合disabled_rule_idsを使用すること(
        self,
    ):
        # Arrange: per_file_disabled が空 dict の場合、全ファイルが disabled_rule_ids にフォールバック
        violation = _make_violation()
        rule_a = FakeRule(rule_id="rule-a", violations=(violation,))
        rule_set = RuleSet(rules=(rule_a,))
        source_files = _make_source_files(("x = 1\n", "__init__.py"))

        # Act: 空 dict → フォールバックして disabled_rule_ids が使われる
        result = rule_set.run(
            source_files,
            disabled_rule_ids=frozenset({"rule-a"}),
            per_file_disabled={},
        )

        # Assert: フォールバックで rule-a が disabled されるため違反なし
        assert len(result) == 0


class TestRuleSetMultiFileRules:
    """RuleSet の multi_file_rules 対応テスト"""

    def test_run_正常系_multi_file_rulesの違反をViolationsとして返すこと(self):
        # Arrange
        violation = _make_violation()
        multi_rule = FakeMultiFileRule(violations=(violation,))
        rule_set = RuleSet(rules=(), multi_file_rules=(multi_rule,))
        source_files = _make_source_files(("x = 1\n", "__init__.py"))

        # Act
        result = rule_set.run(source_files)

        # Assert
        assert isinstance(result, Violations)
        assert len(result) == 1

    def test_run_正常系_単一ファイルルールと複数ファイルルールの違反が集約されること(self):
        # Arrange
        violation = _make_violation()
        rule = FakeRule(violations=(violation,))
        multi_rule = FakeMultiFileRule(violations=(violation,))
        rule_set = RuleSet(rules=(rule,), multi_file_rules=(multi_rule,))
        source_files = _make_source_files(("x = 1\n", "__init__.py"))

        # Act
        result = rule_set.run(source_files)

        # Assert: 単一ファイルルール1件 + 複数ファイルルール1件 = 2件
        assert len(result) == 2

    def test_run_エッジケース_multi_file_rulesが空タプルの場合に既存動作と同じこと(self):
        # Arrange
        violation = _make_violation()
        rule = FakeRule(violations=(violation,))
        rule_set = RuleSet(rules=(rule,), multi_file_rules=())
        source_files = _make_source_files(("x = 1\n", "__init__.py"))

        # Act
        result = rule_set.run(source_files)

        # Assert: 単一ファイルルールのみ実行
        assert len(result) == 1

    def test_run_正常系_multi_file_rulesがdisabled_rule_idsでスキップされること(self):
        # Arrange
        violation = _make_violation()
        multi_rule = FakeMultiFileRule(rule_id="multi-rule", violations=(violation,))
        rule_set = RuleSet(rules=(), multi_file_rules=(multi_rule,))
        source_files = _make_source_files(("x = 1\n", "__init__.py"))

        # Act
        result = rule_set.run(source_files, disabled_rule_ids=frozenset({"multi-rule"}))

        # Assert: multi-rule がスキップされるため違反なし
        assert len(result) == 0

    def test_run_エッジケース_multi_file_rulesにper_file_disabledが適用されないこと(self):
        # Arrange: per_file_disabled で multi-rule を無効化しようとしても効果なし
        violation = _make_violation()
        multi_rule = FakeMultiFileRule(rule_id="multi-rule", violations=(violation,))
        rule_set = RuleSet(rules=(), multi_file_rules=(multi_rule,))
        source_files = _make_source_files(("x = 1\n", "__init__.py"))

        # Act: per_file_disabled に multi-rule を指定しても multi_file_rules には影響しない
        result = rule_set.run(
            source_files,
            per_file_disabled={Path("__init__.py"): frozenset({"multi-rule"})},
        )

        # Assert: per_file_disabled は単一ファイルルール専用なので multi-rule は実行される
        assert len(result) == 1

    def test_rule_ids_正常系_multi_file_rulesのIDも含むこと(self):
        # Arrange
        multi_rule = FakeMultiFileRule(rule_id="multi-rule")
        rule_set = RuleSet(rules=(), multi_file_rules=(multi_rule,))

        # Act
        result = rule_set.rule_ids

        # Assert
        assert "multi-rule" in result

    def test_list_rules_正常系_multi_file_rulesのメタ情報も含むこと(self):
        # Arrange
        multi_rule = FakeMultiFileRule(rule_id="multi-rule", rule_name="Multi Rule")
        rule_set = RuleSet(rules=(), multi_file_rules=(multi_rule,))

        # Act
        result = rule_set.list_rules()

        # Assert
        assert len(result) == 1
        assert isinstance(result[0], RuleMeta)
        assert result[0].rule_id == "multi-rule"
        assert result[0].rule_name == "Multi Rule"

    def test_find_rule_正常系_multi_file_rulesのrule_idで検索できること(self):
        # Arrange
        multi_rule = FakeMultiFileRule(rule_id="multi-rule", rule_name="Multi Rule")
        rule_set = RuleSet(rules=(), multi_file_rules=(multi_rule,))

        # Act
        result = rule_set.find_rule("multi-rule")

        # Assert
        assert result is not None
        assert isinstance(result, RuleMeta)
        assert result.rule_id == "multi-rule"
