"""Rule 層の静的解析ルール。ファイル行数の上限超過を検出する。"""

from paladin.rule.types import DetectionContext, RuleMeta, SourceFile, Violation

_DEFAULT_MAX_LINES = 400
_DEFAULT_MAX_TEST_LINES = 800


class FileLengthCalculator:
    """ファイルの行数を計算するクラス"""

    @staticmethod
    def calc(source: str) -> int:
        """ファイルの行数を返す"""
        if not source:
            return 0
        return len(source.splitlines())


class FileLengthDetector:
    """ファイル行数の閾値判定と Violation 生成を行う"""

    @staticmethod
    def detect(
        length: int,
        limit: int,
        ctx: DetectionContext,
    ) -> Violation | None:
        """Length が limit を超えていれば Violation を返す。そうでなければ None を返す"""
        if length <= limit:
            return None
        source_file = ctx.source_file
        file_path = source_file.file_path.name
        message = f"ファイル `{file_path}` は `{length}` 行です。上限は `{limit}` 行です"
        if source_file.is_test_file:
            suggestion = "parametrize やフィクスチャで重複を排除し、必要に応じてテストファイルを分割してください"
        else:
            suggestion = "不要なコードを削除し、クラスや関数の責務を見直したうえで、必要に応じてファイルを分割してください"
        location = source_file.location(length)
        return ctx.meta.create_violation_at(
            location=location,
            message=message,
            reason="ファイルが長すぎることは、責務の肥大化や設計上の問題を示す兆候です",
            suggestion=suggestion,
        )


class MaxFileLengthRule:
    """ファイルの行数が設定された上限を超えた場合に違反を検出するルール"""

    def __init__(
        self, max_lines: int = _DEFAULT_MAX_LINES, max_test_lines: int = _DEFAULT_MAX_TEST_LINES
    ) -> None:
        """ルールを初期化する"""
        self._max_lines = max_lines
        self._max_test_lines = max_test_lines
        self._meta = RuleMeta(
            rule_id="max-file-length",
            rule_name="Max File Length",
            summary="単一ファイルの行数が設定された上限を超えた場合に違反を検出する",
            intent="ファイルの肥大化を防ぎ、単一責任原則を促進する",
            guidance="各ファイルの行数を確認し、上限を超えていないか検査する",
            suggestion="不要なコードを削除し、責務を見直したうえで、必要に応じてファイルを分割してください",
            background=(
                "ファイルの行数は、コードの健全性を示すシンプルかつ信頼性の高い指標です。"
                "100行のファイルと1万行のファイルでは、変更容易性もテスタビリティも根本的に異なります。\n"
                "行数が増加するほど、責務の肥大化・変更容易性の低下・テスタビリティの低下・認知負荷の増大を招きます。"
            ),
            steps=(
                "不要なコード（未使用の関数・変数・import等）を削除する",
                "クラスや関数の責務を見直し、単一責任原則を満たしているか確認する",
                "責務を分割できる場合は、クラスを分け、それに合わせてファイルを分割する",
            ),
            config_example=(
                "[tool.paladin.rule.max-file-length]\nmax-lines = 400\nmax-test-lines = 800"
            ),
            detection_example=(
                "# 違反: ファイルの行数が上限を超えている\n"
                "# src/myapp/services/user.py（上限400行に対して401行以上の場合）\n\n"
                "# 準拠: ファイルの行数が上限内に収まっている\n"
                "# src/myapp/services/user.py（400行以内）"
            ),
        )

    @property
    def meta(self) -> RuleMeta:
        """ルールのメタ情報を返す"""
        return self._meta

    def check(self, source_file: SourceFile) -> tuple[Violation, ...]:
        """単一ファイルに対する違反判定を行う"""
        limit = self._max_test_lines if source_file.is_test_file else self._max_lines
        length = FileLengthCalculator.calc(source_file.source)
        ctx = DetectionContext(meta=self._meta, source_file=source_file)
        violation = FileLengthDetector.detect(length, limit, ctx)
        if violation is None:
            return ()
        return (violation,)
