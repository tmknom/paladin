"""Check向けドメインモデル定義"""

import ast
import enum
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Violation:
    """単一ルール違反の情報を保持する値オブジェクト"""

    file: Path
    line: int
    column: int
    rule_id: str
    rule_name: str
    message: str
    reason: str
    suggestion: str


@dataclass(frozen=True)
class Violations:
    """複数Violationを集約する値オブジェクト"""

    items: tuple[Violation, ...]

    def __len__(self) -> int:
        """違反件数を返す"""
        return len(self.items)

    def __iter__(self) -> Iterator[Violation]:
        """Violationをイテレーションする"""
        return iter(self.items)


@dataclass(frozen=True)
class RuleMeta:
    """ルールのメタ情報を保持する値オブジェクト"""

    rule_id: str
    rule_name: str
    summary: str


@dataclass(frozen=True)
class TargetFiles:
    """列挙された解析対象ファイル群を保持する不変な値オブジェクト

    Constraints:
        - インスタンス生成後は変更不可（frozen=True）
        - files は重複排除・ソート済みであることを前提とする
    """

    files: tuple[Path, ...]
    """重複排除・ソート済みの .py ファイルパス群"""

    def __len__(self) -> int:
        """ファイル数を返す

        Returns:
            列挙されたファイルの件数
        """
        return len(self.files)

    def __iter__(self) -> Iterator[Path]:
        """ファイルパスをイテレーションする

        Returns:
            ファイルパスのイテレータ
        """
        return iter(self.files)


@dataclass(frozen=True)
class ParsedFile:
    """単一ファイルのAST解析結果を保持する不変な値オブジェクト"""

    file_path: Path
    tree: ast.Module


@dataclass(frozen=True)
class ParsedFiles:
    """複数ファイルのAST解析結果を集約する不変な値オブジェクト"""

    files: tuple[ParsedFile, ...]

    def __len__(self) -> int:
        """解析済みファイル数を返す"""
        return len(self.files)

    def __iter__(self) -> Iterator[ParsedFile]:
        """解析済みファイルをイテレーションする"""
        return iter(self.files)


@dataclass(frozen=True)
class CheckResult:
    """Check処理の実行結果を保持する不変オブジェクト

    Constraints:
        - インスタンス生成後は変更不可（frozen=True）
    """

    target_files: TargetFiles
    """列挙された解析対象ファイル群"""

    parsed_files: ParsedFiles
    """AST解析結果群"""

    violations: Violations
    """ルール違反一覧"""


class CheckStatus(enum.Enum):
    """実行結果の状態を表す列挙型"""

    OK = "ok"
    VIOLATIONS = "violations"


@dataclass(frozen=True)
class CheckSummary:
    """Summary情報（status・total・by_rule・by_file）を保持する値オブジェクト"""

    status: CheckStatus
    total: int
    by_rule: dict[str, int]
    by_file: dict[str, int]

    @classmethod
    def from_check_result(cls, result: CheckResult) -> "CheckSummary":
        """CheckResultから集計してCheckSummaryを生成する"""
        violations = list(result.violations)
        total = len(violations)

        by_rule: dict[str, int] = {}
        by_file: dict[str, int] = {}
        for v in violations:
            by_rule[v.rule_id] = by_rule.get(v.rule_id, 0) + 1
            file_key = str(v.file)
            by_file[file_key] = by_file.get(file_key, 0) + 1

        status = CheckStatus.OK if total == 0 else CheckStatus.VIOLATIONS
        return cls(status=status, total=total, by_rule=by_rule, by_file=by_file)


@dataclass(frozen=True)
class CheckReport:
    """フォーマット済みレポート文字列と終了コードを保持する値オブジェクト"""

    text: str
    exit_code: int
