import pytest

from paladin.check.rule_filter import RuleFilter
from paladin.config.project import ProjectConfig
from tests.unit.fakes import FakeRule


class TestRuleFilter:
    def test_resolve_disabled_rules_正常系_falseに設定されたルールIDを返すこと(self):
        # Arrange
        config = ProjectConfig(rules={"no-relative-import": False, "require-all-export": True})
        known_rule_ids = frozenset({"no-relative-import", "require-all-export"})
        rule_filter = RuleFilter()

        # Act
        result = rule_filter.resolve_disabled_rules(config.rules, known_rule_ids)

        # Assert
        assert result == frozenset({"no-relative-import"})

    def test_resolve_disabled_rules_正常系_全ルールtrueの場合空のfrozensetを返すこと(self):
        # Arrange
        config = ProjectConfig(rules={"no-relative-import": True, "require-all-export": True})
        known_rule_ids = frozenset({"no-relative-import", "require-all-export"})
        rule_filter = RuleFilter()

        # Act
        result = rule_filter.resolve_disabled_rules(config.rules, known_rule_ids)

        # Assert
        assert result == frozenset()

    def test_resolve_disabled_rules_エッジケース_空のrulesで空のfrozensetを返すこと(self):
        # Arrange
        config = ProjectConfig(rules={})
        known_rule_ids = frozenset({"no-relative-import", "require-all-export"})
        rule_filter = RuleFilter()

        # Act
        result = rule_filter.resolve_disabled_rules(config.rules, known_rule_ids)

        # Assert
        assert result == frozenset()

    def test_resolve_disabled_rules_エッジケース_存在しないルールIDで警告を出力して無視すること(
        self, caplog: pytest.LogCaptureFixture
    ):
        # Arrange
        config = ProjectConfig(rules={"unknown-rule": False})
        known_rule_ids = frozenset({"require-all-export"})
        rule_filter = RuleFilter()

        # Act
        with caplog.at_level("WARNING"):
            result = rule_filter.resolve_disabled_rules(config.rules, known_rule_ids)

        # Assert
        assert "unknown-rule" not in result
        assert "unknown-rule" in caplog.text

    def test_resolve_disabled_rules_正常系_複数ルールをfalseに設定した場合すべて返すこと(self):
        # Arrange
        config = ProjectConfig(rules={"no-relative-import": False, "require-all-export": False})
        known_rule_ids = frozenset({"no-relative-import", "require-all-export"})
        rule_filter = RuleFilter()

        # Act
        result = rule_filter.resolve_disabled_rules(config.rules, known_rule_ids)

        # Assert
        assert result == frozenset({"no-relative-import", "require-all-export"})

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
