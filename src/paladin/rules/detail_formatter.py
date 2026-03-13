"""RulesDetailFormatterの実装"""

from paladin.check.rule.types import RuleMeta

_LABEL_RULE_ID = "Rule ID:"
_LABEL_NAME = "Name:"
_LABEL_SUMMARY = "Summary:"
_COL_WIDTH = len(_LABEL_SUMMARY) + 2


class RulesDetailFormatter:
    """RuleMeta を詳細表示用の text 形式に変換する"""

    def format(self, rule: RuleMeta) -> str:
        """RuleMeta をラベル付きの詳細テキストに変換する"""
        lines = [
            f"{_LABEL_RULE_ID:<{_COL_WIDTH}}{rule.rule_id}",
            f"{_LABEL_NAME:<{_COL_WIDTH}}{rule.rule_name}",
            f"{_LABEL_SUMMARY:<{_COL_WIDTH}}{rule.summary}",
        ]
        return "\n".join(lines)
