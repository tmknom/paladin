"""ルール詳細のテキスト整形

単一ルールのメタ情報をラベル付き詳細テキストまたは JSON に変換する。
"""

import json

from paladin.check import OutputFormat
from paladin.rule import RuleMeta

_LABEL_RULE_ID = "Rule ID:"
_LABEL_NAME = "Name:"
_LABEL_SUMMARY = "Summary:"
_LABEL_INTENT = "Intent:"
_LABEL_GUIDANCE = "Guidance:"
_LABEL_SUGGESTION = "Suggestion:"
_COL_WIDTH = len(_LABEL_SUGGESTION) + 2


class ViewTextFormatter:
    """RuleMeta を詳細表示用の text 形式に変換する"""

    def format(self, rule: RuleMeta) -> str:
        """RuleMeta をラベル付きの詳細テキストに変換する"""
        lines = [
            f"{_LABEL_RULE_ID:<{_COL_WIDTH}}{rule.rule_id}",
            f"{_LABEL_NAME:<{_COL_WIDTH}}{rule.rule_name}",
            f"{_LABEL_SUMMARY:<{_COL_WIDTH}}{rule.summary}",
            f"{_LABEL_INTENT:<{_COL_WIDTH}}{rule.intent}",
            f"{_LABEL_GUIDANCE:<{_COL_WIDTH}}{rule.guidance}",
            f"{_LABEL_SUGGESTION:<{_COL_WIDTH}}{rule.suggestion}",
        ]
        return "\n".join(lines)


class ViewJsonFormatter:
    """RuleMeta を JSON 形式に変換する"""

    def format(self, rule: RuleMeta) -> str:
        """RuleMeta の全 6 フィールドを JSON オブジェクトに変換する"""
        data = {
            "rule_id": rule.rule_id,
            "rule_name": rule.rule_name,
            "summary": rule.summary,
            "intent": rule.intent,
            "guidance": rule.guidance,
            "suggestion": rule.suggestion,
        }
        return json.dumps(data, ensure_ascii=False, indent=2)


class ViewFormatterFactory:
    """OutputFormat に応じたフォーマッターを選択する"""

    def __init__(self) -> None:
        """ViewFormatterFactoryを初期化する"""
        self._text_formatter = ViewTextFormatter()
        self._json_formatter = ViewJsonFormatter()

    def format(self, rule: RuleMeta, output_format: OutputFormat) -> str:
        """OutputFormat に応じた形式で RuleMeta を文字列に変換する"""
        if output_format == OutputFormat.JSON:
            return self._json_formatter.format(rule)
        return self._text_formatter.format(rule)

    def format_error(self, message: str, output_format: OutputFormat) -> str:
        """OutputFormat に応じた形式でエラーメッセージを文字列に変換する"""
        if output_format == OutputFormat.JSON:
            return json.dumps({"error": message}, ensure_ascii=False, indent=2)
        return message
