"""CheckReportFormatterの実装"""

import json

from paladin.check.result import CheckReport, CheckResult, CheckStatus, CheckSummary
from paladin.check.types import OutputFormat


class CheckReportFormatter:
    """CheckResultをtext形式のCheckReportに変換するフォーマッター"""

    def format(self, result: CheckResult) -> CheckReport:
        """CheckResultをtext形式の診断レポートに変換する"""
        summary = CheckSummary.from_check_result(result)

        lines: list[str] = []
        for v in result.violations:
            lines.append(f"{v.file}:{v.line}:{v.column} {v.rule_id} {v.rule_name}")
            lines.append(f"  概要: {v.message}")
            lines.append(f"  理由: {v.reason}")
            lines.append(f"  修正方向: {v.suggestion}")
            lines.append("")

        lines.append("Summary:")
        lines.append(f"  status: {summary.status.value}")
        lines.append(f"  total: {summary.total}")

        if summary.status == CheckStatus.VIOLATIONS:
            by_rule_str = ", ".join(f"{k}={v}" for k, v in summary.by_rule.items())
            by_file_str = ", ".join(f"{k}={v}" for k, v in summary.by_file.items())
            lines.append(f"  by_rule: {by_rule_str}")
            lines.append(f"  by_file: {by_file_str}")

        text = "\n".join(lines)
        exit_code = 0 if summary.status == CheckStatus.OK else 1
        return CheckReport(text=text, exit_code=exit_code)


class CheckJsonFormatter:
    """CheckResultをJSON形式のCheckReportに変換するフォーマッター"""

    def format(self, result: CheckResult) -> CheckReport:
        """CheckResultをJSON形式の診断レポートに変換する"""
        summary = CheckSummary.from_check_result(result)

        diagnostics: list[dict[str, str | int]] = [
            {
                "file": str(v.file),
                "line": v.line,
                "column": v.column,
                "rule_id": v.rule_id,
                "rule_name": v.rule_name,
                "message": v.message,
                "reason": v.reason,
                "suggestion": v.suggestion,
            }
            for v in result.violations
        ]

        summary_dict: dict[str, int | dict[str, int]] = {
            "total_violations": summary.total,
            "by_rule": summary.by_rule,
            "by_file": summary.by_file,
        }

        data: dict[str, object] = {
            "status": summary.status.value,
            "summary": summary_dict,
            "diagnostics": diagnostics,
        }

        text = json.dumps(data, ensure_ascii=False, indent=2)
        exit_code = 0 if summary.status == CheckStatus.OK else 1
        return CheckReport(text=text, exit_code=exit_code)


class CheckFormatterFactory:
    """OutputFormatに応じたフォーマッターを選択し、CheckReportを生成するファクトリー"""

    def __init__(self) -> None:
        """フォーマッターを初期化する"""
        self._text_formatter = CheckReportFormatter()
        self._json_formatter = CheckJsonFormatter()

    def format(self, result: CheckResult, output_format: OutputFormat) -> CheckReport:
        """OutputFormatに応じたフォーマッターに委譲してCheckReportを返す"""
        if output_format == OutputFormat.JSON:
            return self._json_formatter.format(result)
        return self._text_formatter.format(result)
