"""Rule 層の単一ルール実装。ASTベースの静的解析で実装するルールはこの層に配置する。

仕様は docs/rules/no-nested-test-class.md を参照。
"""

import ast

from paladin.rule.types import RuleMeta, SourceFile, Violation

_REASON = "テストクラスのネストは可読性を下げます。テストはフラットな構造に保ってください"
_SUGGESTION = "ネストされたクラスをトップレベルのテストクラスとして独立させてください"


class NestedClassDetector:
    """ネストされたクラス定義から Violation を生成するヘルパー。検出ロジックは呼び出し側が担う"""

    @staticmethod
    def detect(
        outer_class: ast.ClassDef,
        inner_class: ast.ClassDef,
        meta: RuleMeta,
        source_file: SourceFile,
    ) -> Violation:
        """ネストされたクラスに対して Violation を返す"""
        return meta.create_violation_at(
            location=source_file.location(line=inner_class.lineno),
            message=f"テストクラス `{outer_class.name}` の中にクラス `{inner_class.name}` がネストされています",
            reason=_REASON,
            suggestion=_SUGGESTION,
        )


class NestedTestClassCollector:
    """トップレベルクラスの body を走査し、ネストされたクラス定義を収集するヘルパー"""

    @staticmethod
    def collect(tree: ast.Module) -> tuple[tuple[ast.ClassDef, ast.ClassDef], ...]:
        """モジュールのトップレベルクラスからネストされたクラスを (outer, inner) ペアで返す"""
        pairs: list[tuple[ast.ClassDef, ast.ClassDef]] = []
        for outer_class in tree.body:
            if not isinstance(outer_class, ast.ClassDef):
                continue
            pairs.extend(NestedTestClassCollector._collect_inner(outer_class))
        return tuple(pairs)

    @staticmethod
    def _collect_inner(outer_class: ast.ClassDef) -> list[tuple[ast.ClassDef, ast.ClassDef]]:
        """トップレベルクラスの body からネストされた ClassDef を収集する"""
        return [
            (outer_class, inner_node)
            for inner_node in outer_class.body
            if isinstance(inner_node, ast.ClassDef)
        ]


class NoNestedTestClassRule:
    """テストクラス内にネストされたクラス定義を禁止するルール"""

    def __init__(self) -> None:
        """ルールを初期化する"""
        self._meta = RuleMeta(
            rule_id="no-nested-test-class",
            rule_name="No Nested Test Class",
            summary="テストクラス内へのクラスのネストを禁止する",
            intent="テストクラスのネストは可読性を下げるため、フラットな構造を維持する",
            guidance="テストファイル内のトップレベルクラスの body に ClassDef が存在する場合に違反を検出する",
            suggestion=_SUGGESTION,
            background="テストクラスのネストは認知負荷を増大させ、pytest との摩擦を生みます。テストクラスをフラットな構造にすることで、テストの所在が一目で把握でき、pytest との統合も単純になります。",
            steps=(
                "ネストされたクラスをトップレベルのテストクラスとして独立させる",
                "クラス名で旧外側クラスとの関係を表現する（例: TestMyClassCreate, TestMyClassValidate）",
            ),
            detection_example="# 違反: テストクラスがネストされている\nclass TestUserService:\n    class TestExecute:  # 違反\n        def test_正常系(self) -> None:\n            ...\n\n# 準拠: テストクラスをフラットな構造にする\nclass TestUserServiceExecute:\n    def test_正常系(self) -> None:\n        ...",
        )

    @property
    def meta(self) -> RuleMeta:
        """ルールのメタ情報を返す"""
        return self._meta

    def check(self, source_file: SourceFile) -> tuple[Violation, ...]:
        """テストファイルのみを対象にネストされたクラスを検査する"""
        if not source_file.is_test_file:
            return ()
        violations: list[Violation] = []
        for outer_class, inner_class in NestedTestClassCollector.collect(source_file.tree):
            violations.append(
                NestedClassDetector.detect(outer_class, inner_class, self._meta, source_file)
            )
        return tuple(violations)
