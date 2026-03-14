"""ルール詳細のテキスト整形

単一ルールのメタ情報をラベル付き詳細テキストに変換する。
"""

from paladin.lint import RuleMeta

_LABEL_RULE_ID = "Rule ID:"
_LABEL_NAME = "Name:"
_LABEL_SUMMARY = "Summary:"
_LABEL_INTENT = "Intent:"
_LABEL_GUIDANCE = "Guidance:"
_LABEL_SUGGESTION = "Suggestion:"
_COL_WIDTH = len(_LABEL_SUGGESTION) + 2


class RulesDetailFormatter:
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
