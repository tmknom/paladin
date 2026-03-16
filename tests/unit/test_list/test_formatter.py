"""ListTextFormatterクラスのテスト"""

import json

from paladin.check import OutputFormat
from paladin.list.formatter import ListFormatterFactory, ListJsonFormatter, ListTextFormatter
from paladin.rule import RuleMeta


def _make_rule_meta(
    rule_id: str = "PAL001",
    rule_name: str = "rule-name",
    summary: str = "概要テキスト",
    intent: str = "意図",
    guidance: str = "見方",
    suggestion: str = "修正方向",
) -> RuleMeta:
    return RuleMeta(
        rule_id=rule_id,
        rule_name=rule_name,
        summary=summary,
        intent=intent,
        guidance=guidance,
        suggestion=suggestion,
    )


class TestListTextFormatter:
    """ListTextFormatterクラスのテスト"""

    def test_format_正常系_単一ルールのID名前概要をタブ区切り風に返すこと(self):
        # Arrange
        rules = (_make_rule_meta(rule_id="PAL001", rule_name="rule-name", summary="概要テキスト"),)

        # Act
        result = ListTextFormatter().format(rules)

        # Assert
        assert "PAL001" in result
        assert "rule-name" in result
        assert "概要テキスト" in result

    def test_format_正常系_複数ルールで各行が整列されること(self):
        # Arrange
        rules = (
            _make_rule_meta(rule_id="PAL001", rule_name="short", summary="概要1"),
            _make_rule_meta(rule_id="PAL002", rule_name="longer-rule-name", summary="概要2"),
        )

        # Act
        result = ListTextFormatter().format(rules)

        # Assert
        lines = result.splitlines()
        assert len(lines) == 2
        # rule_name 列がパディングで揃っているため、summary の開始位置が同じはず
        idx1 = lines[0].index("概要1")
        idx2 = lines[1].index("概要2")
        assert idx1 == idx2

    def test_format_エッジケース_ルール0件で空文字列を返すこと(self):
        # Arrange
        rules: tuple[()] = ()

        # Act
        result = ListTextFormatter().format(rules)

        # Assert
        assert result == ""


class TestListJsonFormatter:
    """ListJsonFormatterクラスのテスト"""

    def test_format_正常系_単一ルールのrule_idとrule_nameとsummaryがJSONに含まれること(self):
        # Arrange
        rules = (_make_rule_meta(rule_id="PAL001", rule_name="rule-name", summary="概要テキスト"),)

        # Act
        result = ListJsonFormatter().format(rules)
        data = json.loads(result)

        # Assert
        assert data["rules"][0]["rule_id"] == "PAL001"
        assert data["rules"][0]["rule_name"] == "rule-name"
        assert data["rules"][0]["summary"] == "概要テキスト"

    def test_format_正常系_複数ルールでrulesキー配下に全ルールが含まれること(self):
        # Arrange
        rules = (
            _make_rule_meta(rule_id="PAL001", rule_name="rule-one", summary="概要1"),
            _make_rule_meta(rule_id="PAL002", rule_name="rule-two", summary="概要2"),
        )

        # Act
        result = ListJsonFormatter().format(rules)
        data = json.loads(result)

        # Assert
        assert len(data["rules"]) == 2
        assert data["rules"][0]["rule_id"] == "PAL001"
        assert data["rules"][1]["rule_id"] == "PAL002"

    def test_format_正常系_出力がvalid_JSONであること(self):
        # Arrange
        rules = (_make_rule_meta(),)

        # Act
        result = ListJsonFormatter().format(rules)

        # Assert
        parsed = json.loads(result)
        assert isinstance(parsed, dict)

    def test_format_正常系_日本語を含むフィールドがエスケープされずに出力されること(self):
        # Arrange
        rules = (_make_rule_meta(summary="日本語の概要"),)

        # Act
        result = ListJsonFormatter().format(rules)

        # Assert
        assert "日本語の概要" in result

    def test_format_正常系_インデント付きで整形されること(self):
        # Arrange
        rules = (_make_rule_meta(),)

        # Act
        result = ListJsonFormatter().format(rules)

        # Assert
        assert "\n" in result

    def test_format_エッジケース_ルール0件でrulesキーが空配列のJSONを返すこと(self):
        # Arrange
        rules: tuple[()] = ()

        # Act
        result = ListJsonFormatter().format(rules)
        data = json.loads(result)

        # Assert
        assert data == {"rules": []}


class TestListFormatterFactory:
    """ListFormatterFactoryクラスのテスト"""

    def test_format_正常系_TEXT指定で列幅揃えテキスト形式を返すこと(self):
        # Arrange
        rules = (_make_rule_meta(rule_id="PAL001", rule_name="rule-name", summary="概要テキスト"),)

        # Act
        result = ListFormatterFactory().format(rules, OutputFormat.TEXT)

        # Assert
        assert "PAL001" in result
        assert "rule-name" in result
        assert "概要テキスト" in result
        # JSON ではないことを確認
        try:
            json.loads(result)
            raise AssertionError("TEXT 形式なのに valid JSON が返った")
        except json.JSONDecodeError:
            pass

    def test_format_正常系_JSON指定でrulesキーを含むJSON形式を返すこと(self):
        # Arrange
        rules = (_make_rule_meta(rule_id="PAL001", rule_name="rule-name", summary="概要テキスト"),)

        # Act
        result = ListFormatterFactory().format(rules, OutputFormat.JSON)
        data = json.loads(result)

        # Assert
        assert "rules" in data
        assert data["rules"][0]["rule_id"] == "PAL001"
