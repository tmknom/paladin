"""RulesFormatterの実装"""

from paladin.check.rule.types import RuleMeta


class RulesFormatter:
    """tuple[RuleMeta, ...] を text 形式の文字列に変換する"""

    def format(self, rules: tuple[RuleMeta, ...]) -> str:
        """ルール一覧を整列された text 形式に変換する

        rule_id は固定幅（6文字 + 2スペース）、rule_name は最長に合わせてパディング、
        summary はそのまま出力する。ルールが0件の場合は空文字列を返す。
        """
        if not rules:
            return ""

        max_id_len = max(len(r.rule_id) for r in rules)
        max_name_len = max(len(r.rule_name) for r in rules)
        lines: list[str] = []
        for rule in rules:
            rule_id_col = f"{rule.rule_id:<{max_id_len}}"
            rule_name_col = f"{rule.rule_name:<{max_name_len}}"
            lines.append(f"{rule_id_col}  {rule_name_col}  {rule.summary}")
        return "\n".join(lines)
