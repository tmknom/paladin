"""CheckReportFormatterの実装"""

from paladin.check.result import CheckReport, CheckResult, CheckStatus, CheckSummary


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
