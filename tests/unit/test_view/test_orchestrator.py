"""ViewOrchestratorクラスのテスト"""

import json

from paladin.foundation.output import OutputFormat
from paladin.rule import Rule, RuleSet
from paladin.view.context import ViewContext
from paladin.view.formatter import ViewFormatterFactory
from paladin.view.orchestrator import ViewOrchestrator
from tests.fake import FakeRule


class TestViewOrchestrator:
    """ViewOrchestratorクラスのテスト"""

    def _make_orchestrator(self, rules: tuple[Rule, ...]) -> ViewOrchestrator:
        rule_set = RuleSet(rules=rules)
        formatter = ViewFormatterFactory()
        return ViewOrchestrator(rule_set=rule_set, formatter=formatter)

    def test_orchestrate_正常系_rule_id指定で対象ルールの詳細を返すこと(self):
        # Arrange
        fake_rule = FakeRule(rule_id="PAL001", rule_name="fake-rule", summary="フェイク概要")
        orchestrator = self._make_orchestrator(rules=(fake_rule,))
        context = ViewContext(rule_id="PAL001")

        # Act
        result = orchestrator.orchestrate(context)

        # Assert
        assert "PAL001" in result
        assert "フェイク概要" in result

    def test_orchestrate_正常系_format_JSON指定でJSON形式を返すこと(self):
        # Arrange
        fake_rule = FakeRule(rule_id="PAL001", rule_name="fake-rule", summary="フェイク概要")
        orchestrator = self._make_orchestrator(rules=(fake_rule,))
        context = ViewContext(rule_id="PAL001", format=OutputFormat.JSON)

        # Act
        result = orchestrator.orchestrate(context)
        data = json.loads(result)

        # Assert
        assert data["rule_id"] == "PAL001"

    def test_orchestrate_エッジケース_存在しないrule_idでformat_TEXT指定時にエラーメッセージ文字列を返すこと(
        self,
    ):
        # Arrange
        fake_rule = FakeRule(rule_id="PAL001")
        orchestrator = self._make_orchestrator(rules=(fake_rule,))
        context = ViewContext(rule_id="nonexistent", format=OutputFormat.TEXT)

        # Act
        result = orchestrator.orchestrate(context)

        # Assert
        assert "Error" in result
        assert "nonexistent" in result

    def test_orchestrate_エッジケース_存在しないrule_idでformat_JSON指定時にerrorキーを含むJSONを返すこと(
        self,
    ):
        # Arrange
        fake_rule = FakeRule(rule_id="PAL001")
        orchestrator = self._make_orchestrator(rules=(fake_rule,))
        context = ViewContext(rule_id="nonexistent", format=OutputFormat.JSON)

        # Act
        result = orchestrator.orchestrate(context)
        data = json.loads(result)

        # Assert
        assert "error" in data
        assert "nonexistent" in data["error"]
