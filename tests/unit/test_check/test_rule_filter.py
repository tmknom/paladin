import pytest

from paladin.check.rule_filter import RuleFilter
from tests.unit.fakes import FakeRule


class TestRuleFilter:
    def test_resolve_disabled_rules_正常系_falseに設定されたルールIDを返すこと(self):
        # Arrange
        rules = {"no-relative-import": False, "require-all-export": True}
        known_rule_ids = frozenset({"no-relative-import", "require-all-export"})
        rule_filter = RuleFilter()

        # Act
        result = rule_filter.resolve_disabled_rules(rules, known_rule_ids)

        # Assert
        assert result == frozenset({"no-relative-import"})

    def test_resolve_disabled_rules_正常系_全ルールtrueの場合空のfrozensetを返すこと(self):
        # Arrange
        rules = {"no-relative-import": True, "require-all-export": True}
        known_rule_ids = frozenset({"no-relative-import", "require-all-export"})
        rule_filter = RuleFilter()

        # Act
        result = rule_filter.resolve_disabled_rules(rules, known_rule_ids)

        # Assert
        assert result == frozenset()

    def test_resolve_disabled_rules_エッジケース_空のrulesで空のfrozensetを返すこと(self):
        # Arrange
        rules: dict[str, bool] = {}
        known_rule_ids = frozenset({"no-relative-import", "require-all-export"})
        rule_filter = RuleFilter()

        # Act
        result = rule_filter.resolve_disabled_rules(rules, known_rule_ids)

        # Assert
        assert result == frozenset()

    def test_resolve_disabled_rules_エッジケース_存在しないルールIDで警告を出力して無視すること(
        self, caplog: pytest.LogCaptureFixture
    ):
        # Arrange
        rules = {"unknown-rule": False}
        known_rule_ids = frozenset({"require-all-export"})
        rule_filter = RuleFilter()

        # Act
        with caplog.at_level("WARNING"):
            result = rule_filter.resolve_disabled_rules(rules, known_rule_ids)

        # Assert
        assert "unknown-rule" not in result
        assert "unknown-rule" in caplog.text

    def test_resolve_disabled_rules_正常系_複数ルールをfalseに設定した場合すべて返すこと(self):
        # Arrange
        rules = {"no-relative-import": False, "require-all-export": False}
        known_rule_ids = frozenset({"no-relative-import", "require-all-export"})
        rule_filter = RuleFilter()

        # Act
        result = rule_filter.resolve_disabled_rules(rules, known_rule_ids)

        # Assert
        assert result == frozenset({"no-relative-import", "require-all-export"})

    def test_resolve_disabled_rules_正常系_select_rulesで指定されたルールのみ有効になること(self):
        # Arrange
        rules: dict[str, bool] = {}
        known_rule_ids = frozenset({"rule-a", "rule-b"})
        rule_filter = RuleFilter()

        # Act
        result = rule_filter.resolve_disabled_rules(
            rules, known_rule_ids, select_rules=frozenset({"rule-a"})
        )

        # Assert: rule-b が disabled に含まれる
        assert "rule-b" in result
        assert "rule-a" not in result

    def test_resolve_disabled_rules_正常系_select_rulesが空の場合既存動作と同じこと(self):
        # Arrange
        rules = {"rule-a": False}
        known_rule_ids = frozenset({"rule-a", "rule-b"})
        rule_filter = RuleFilter()

        # Act
        result = rule_filter.resolve_disabled_rules(rules, known_rule_ids, select_rules=frozenset())

        # Assert: select_rules 未指定と同等。rules dict のみで disabled が解決される
        assert result == frozenset({"rule-a"})

    def test_resolve_disabled_rules_正常系_select_rulesとrules_falseの両方が適用されること(self):
        # Arrange: rule-b は select_rules に含まれるが rules で False → disabled
        rules = {"rule-b": False}
        known_rule_ids = frozenset({"rule-a", "rule-b"})
        rule_filter = RuleFilter()

        # Act
        result = rule_filter.resolve_disabled_rules(
            rules, known_rule_ids, select_rules=frozenset({"rule-a", "rule-b"})
        )

        # Assert: AND 条件。rule-b が rules:false で disabled
        assert "rule-b" in result
        assert "rule-a" not in result

    def test_resolve_disabled_rules_エッジケース_select_rulesに存在しないルールIDで警告を出力すること(
        self, caplog: pytest.LogCaptureFixture
    ):
        # Arrange
        rules: dict[str, bool] = {}
        known_rule_ids = frozenset({"rule-a"})
        rule_filter = RuleFilter()

        # Act
        with caplog.at_level("WARNING"):
            rule_filter.resolve_disabled_rules(
                rules, known_rule_ids, select_rules=frozenset({"unknown-rule"})
            )

        # Assert: 未知ルールID の警告が出力される
        assert "unknown-rule" in caplog.text

    def test_resolve_disabled_rules_エッジケース_select_rulesで全ルールを指定した場合disabledが空であること(
        self,
    ):
        # Arrange
        rules: dict[str, bool] = {}
        known_rule_ids = frozenset({"rule-a", "rule-b"})
        rule_filter = RuleFilter()

        # Act
        result = rule_filter.resolve_disabled_rules(
            rules, known_rule_ids, select_rules=frozenset({"rule-a", "rule-b"})
        )

        # Assert: 全ルールが select_rules に含まれるため disabled は空
        assert result == frozenset()

    def test_resolve_disabled_rules_エッジケース_select_rulesに存在しないルールのみ指定した場合全ルールが無効になること(
        self,
    ):
        # Arrange: select_rules に unknown のみ指定 → known_rule_ids の全ルールが disabled
        rules: dict[str, bool] = {}
        known_rule_ids = frozenset({"rule-a"})
        rule_filter = RuleFilter()

        # Act
        result = rule_filter.resolve_disabled_rules(
            rules, known_rule_ids, select_rules=frozenset({"unknown"})
        )

        # Assert: rule-a が disabled に含まれる
        assert "rule-a" in result

    def test_filter_正常系_disabled_rule_idsに該当するルールを除外すること(self):
        # Arrange
        rule_a = FakeRule(rule_id="rule-a")
        rule_b = FakeRule(rule_id="rule-b")
        rules = (rule_a, rule_b)
        rule_filter = RuleFilter()

        # Act
        result = rule_filter.filter(rules, disabled_rule_ids=frozenset({"rule-a"}))

        # Assert
        assert len(result) == 1
        assert result[0].meta.rule_id == "rule-b"

    def test_filter_エッジケース_空のdisabled_rule_idsで全ルールを返すこと(self):
        # Arrange
        rule_a = FakeRule(rule_id="rule-a")
        rule_b = FakeRule(rule_id="rule-b")
        rules = (rule_a, rule_b)
        rule_filter = RuleFilter()

        # Act
        result = rule_filter.filter(rules, disabled_rule_ids=frozenset())

        # Assert
        assert len(result) == 2

    def test_filter_エッジケース_全ルールが無効の場合空タプルを返すこと(self):
        # Arrange
        rule_a = FakeRule(rule_id="rule-a")
        rule_b = FakeRule(rule_id="rule-b")
        rules = (rule_a, rule_b)
        rule_filter = RuleFilter()

        # Act
        result = rule_filter.filter(rules, disabled_rule_ids=frozenset({"rule-a", "rule-b"}))

        # Assert
        assert result == ()
