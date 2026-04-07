"""ローカルインポート禁止ルール

仕様は docs/rules/no-local-import.md を参照。
"""

import ast
from dataclasses import dataclass

from paladin.rule.types import RuleMeta, SourceFile, Violation


@dataclass(frozen=True)
class LocalImport:
    """検出されたローカルインポートの中間表現"""

    node: ast.Import | ast.ImportFrom
    scope: str


class LocalImportCollector:
    """AST からローカルインポートを再帰的に収集する"""

    @staticmethod
    def collect(tree: ast.Module) -> tuple[LocalImport, ...]:
        """ast.Module からローカルインポートを再帰的に収集する"""
        result: list[LocalImport] = []
        LocalImportCollector._collect_top_level(tree.body, result)
        return tuple(result)

    @staticmethod
    def _collect_top_level(body: list[ast.stmt], result: list[LocalImport]) -> None:
        """TYPE_CHECKING ブロックを除外してトップレベルを走査する"""
        for node in body:
            if LocalImportCollector._is_type_checking_block(node):
                continue
            LocalImportCollector._visit(node, class_name=None, result=result)

    @staticmethod
    def _is_type_checking_block(node: ast.AST) -> bool:
        """ast.If ノードが TYPE_CHECKING ガードかどうかを判定する"""
        if not isinstance(node, ast.If):
            return False
        test = node.test
        if isinstance(test, ast.Name) and test.id == "TYPE_CHECKING":
            return True
        return isinstance(test, ast.Attribute) and test.attr == "TYPE_CHECKING"

    @staticmethod
    def _visit(
        node: ast.AST,
        class_name: str | None,
        result: list[LocalImport],
    ) -> None:
        if isinstance(node, ast.ClassDef):
            LocalImportCollector._visit_class(node, result)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            LocalImportCollector._visit_function(node, class_name=class_name, result=result)

    @staticmethod
    def _visit_class(class_node: ast.ClassDef, result: list[LocalImport]) -> None:
        for node in class_node.body:
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                scope = f"クラス {class_node.name}"
                result.append(LocalImport(node=node, scope=scope))
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                LocalImportCollector._visit_function(
                    node, class_name=class_node.name, result=result
                )

    @staticmethod
    def _visit_function(
        func_node: ast.FunctionDef | ast.AsyncFunctionDef,
        class_name: str | None,
        result: list[LocalImport],
    ) -> None:
        if class_name is not None:
            scope = f"メソッド {class_name}.{func_node.name}"
        else:
            scope = f"関数 {func_node.name}"
        LocalImportCollector._collect_in_body(func_node.body, scope, result)

    @staticmethod
    def _collect_in_body(
        body: list[ast.stmt],
        scope: str,
        result: list[LocalImport],
    ) -> None:
        for node in body:
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                result.append(LocalImport(node=node, scope=scope))
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                inner_scope = f"関数 {node.name}"
                LocalImportCollector._collect_in_body(node.body, inner_scope, result)


class LocalImportDetector:
    """ローカルインポートから Violation を生成する"""

    @staticmethod
    def detect(
        local_import: LocalImport,
        meta: RuleMeta,
        source_file: SourceFile,
    ) -> Violation:
        """ローカルインポートから常に Violation を返す"""
        import_text = source_file.get_line(local_import.node.lineno)
        return meta.create_violation_at(
            location=source_file.location(local_import.node.lineno, local_import.node.col_offset),
            message=f"{local_import.scope} 内に import 文があります",
            reason="import 文はモジュールのトップレベルに配置することで依存関係を明示し、インポートのタイミングを予測可能にします",
            suggestion=f"`{import_text}` をファイル冒頭のインポートセクションに移動し、{local_import.scope} 内から削除してください",
        )


class NoLocalImportRule:
    """関数・クラス・メソッド内のローカルインポートを AST で検出するルール"""

    def __init__(self) -> None:
        """ルールを初期化する"""
        self._meta = RuleMeta(
            rule_id="no-local-import",
            rule_name="No Local Import",
            summary="ローカルインポートの使用を禁止する",
            intent="import 文をモジュールのトップレベルに集約し、依存関係の一覧性を確保する",
            guidance="関数・メソッド・クラス内に import 文が書かれている箇所を確認する",
            suggestion="ファイル冒頭のインポートセクションに import 文を移動する",
            background=(
                "import 文をファイル冒頭のトップレベルに集約することで、依存関係が明示化され、"
                "コードレビューや依存関係分析が容易になります。また、トップレベルにまとめることで"
                "インポートのタイミングが明確になり、起動時に依存モジュールの不在を早期検出できます。"
            ),
            steps=(
                "ローカルインポートが依存している理由（循環インポートなど）を確認する",
                "循環インポートがある場合は型アノテーション専用の `if TYPE_CHECKING:` ブロックを利用する",
                "問題がなければ import 文をファイル冒頭のインポートセクションに移動する",
            ),
            detection_example=(
                "# 違反: 関数内に import 文がある\n"
                "def some_function():\n"
                "    import requests  # 違反\n"
                "    response = requests.get(...)\n"
                "\n"
                "# 準拠: ファイルのトップレベルに import する\n"
                "import requests\n"
                "\n"
                "def some_function():\n"
                "    response = requests.get(...)"
            ),
        )

    @property
    def meta(self) -> RuleMeta:
        """ルールのメタ情報を返す"""
        return self._meta

    def check(self, source_file: SourceFile) -> tuple[Violation, ...]:
        """単一ファイルに対する違反判定を行う"""
        violations: list[Violation] = []
        for local_import in LocalImportCollector.collect(source_file.tree):
            violations.append(LocalImportDetector.detect(local_import, self._meta, source_file))
        return tuple(violations)
