"""Listパッケージの出力フォーマッター

ルールメタ情報を列幅揃えの一覧テキストまたは JSON に変換する。
"""

import json

from paladin.foundation.output import OutputFormat
from paladin.rule import RuleMeta


class ListTextFormatter:
    """tuple[RuleMeta, ...] を text 形式の文字列に変換する"""

    def format(self, rules: tuple[RuleMeta, ...]) -> str:
        """ルール一覧を整列された text 形式に変換する

        rule_id・rule_name を最長に揃えてパディングし、summary を末尾に付けて行結合する。
        ルールが0件の場合は空文字列を返す。
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


class ListJsonFormatter:
    """tuple[RuleMeta, ...] を JSON 形式の文字列に変換する"""

    def format(self, rules: tuple[RuleMeta, ...]) -> str:
        """ルール一覧を {"rules": [...]} 形式の JSON 文字列に変換する

        ルールが0件の場合は {"rules": []} を返す。
        """
        data = {
            "rules": [
                {
                    "rule_id": rule.rule_id,
                    "rule_name": rule.rule_name,
                    "summary": rule.summary,
                }
                for rule in rules
            ]
        }
        return json.dumps(data, ensure_ascii=False, indent=2)


class ListFormatterFactory:
    """OutputFormat に応じたフォーマッターを選択する"""

    def __init__(self) -> None:
        """ListFormatterFactory を初期化する"""
        self._text_formatter = ListTextFormatter()
        self._json_formatter = ListJsonFormatter()

    def format(self, rules: tuple[RuleMeta, ...], output_format: OutputFormat) -> str:
        """OutputFormat に応じた形式で tuple[RuleMeta, ...] を文字列に変換する"""
        if output_format == OutputFormat.JSON:
            return self._json_formatter.format(rules)
        return self._text_formatter.format(rules)
