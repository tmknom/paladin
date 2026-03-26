"""ListOrchestratorクラスのテスト"""

import json

from paladin.foundation.output import OutputFormat
from paladin.list.context import ListContext
from paladin.list.formatter import ListFormatterFactory
from paladin.list.orchestrator import ListOrchestrator
from paladin.rule import Rule, RuleSet
from tests.unit.fakes import FakeRule


class TestListOrchestrator:
    """ListOrchestratorクラスのテスト"""

    def _make_orchestrator(self, rules: tuple[Rule, ...]) -> ListOrchestrator:
        rule_set = RuleSet(rules=rules)
        formatter = ListFormatterFactory()
        return ListOrchestrator(rule_set=rule_set, formatter=formatter)

    def test_orchestrate_正常系_既存の全ルール一覧を返すこと(self):
        # Arrange
        fake_rule = FakeRule(rule_id="PAL001", rule_name="fake-rule", summary="フェイク概要")
        orchestrator = self._make_orchestrator(rules=(fake_rule,))
        context = ListContext()

        # Act
        result = orchestrator.orchestrate(context)

        # Assert
        assert "PAL001" in result
        assert "fake-rule" in result
        assert "フェイク概要" in result

    def test_orchestrate_エッジケース_ルール未登録のとき空文字列を返すこと(self):
        # Arrange
        orchestrator = self._make_orchestrator(rules=())
        context = ListContext()

        # Act
        result = orchestrator.orchestrate(context)

        # Assert
        assert result == ""

    def test_orchestrate_正常系_format_JSON指定でrulesキーを含むJSON形式を返すこと(self):
        # Arrange
        fake_rule = FakeRule(rule_id="PAL001", rule_name="fake-rule", summary="フェイク概要")
        orchestrator = self._make_orchestrator(rules=(fake_rule,))
        context = ListContext(format=OutputFormat.JSON)

        # Act
        result = orchestrator.orchestrate(context)

        # Assert
        data = json.loads(result)
        assert "rules" in data
        assert len(data["rules"]) == 1
        assert data["rules"][0]["rule_id"] == "PAL001"
        assert data["rules"][0]["rule_name"] == "fake-rule"
        assert data["rules"][0]["summary"] == "フェイク概要"

    def test_orchestrate_エッジケース_ルール未登録でformat_JSON指定時に空配列のJSONを返すこと(self):
        # Arrange
        orchestrator = self._make_orchestrator(rules=())
        context = ListContext(format=OutputFormat.JSON)

        # Act
        result = orchestrator.orchestrate(context)

        # Assert
        data = json.loads(result)
        assert "rules" in data
        assert data["rules"] == []
