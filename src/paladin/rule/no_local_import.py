"""ローカルインポート禁止ルール

仕様は docs/rules/no-local-import.md を参照。
"""

import ast

from paladin.rule.types import RuleMeta, SourceFile, Violation


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
        )

    @property
    def meta(self) -> RuleMeta:
        """ルールのメタ情報を返す"""
        return self._meta

    def check(self, source_file: SourceFile) -> tuple[Violation, ...]:
        """単一ファイルに対する違反判定を行う"""
        violations: list[Violation] = []
        top_level_nodes = _get_top_level_nodes(source_file.tree)
        for node in top_level_nodes:
            self._visit(node, class_name=None, violations=violations, source_file=source_file)
        return tuple(violations)

    def _visit(
        self,
        node: ast.AST,
        class_name: str | None,
        violations: list[Violation],
        source_file: SourceFile,
    ) -> None:
        if isinstance(node, ast.ClassDef):
            self._visit_class(node, violations, source_file)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            self._visit_function(
                node, class_name=class_name, violations=violations, source_file=source_file
            )

    def _visit_class(
        self,
        class_node: ast.ClassDef,
        violations: list[Violation],
        source_file: SourceFile,
    ) -> None:
        for node in class_node.body:
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                scope = f"クラス {class_node.name}"
                violations.append(self._make_violation(node, scope, source_file))
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self._visit_function(
                    node, class_name=class_node.name, violations=violations, source_file=source_file
                )

    def _visit_function(
        self,
        func_node: ast.FunctionDef | ast.AsyncFunctionDef,
        class_name: str | None,
        violations: list[Violation],
        source_file: SourceFile,
    ) -> None:
        if class_name is not None:
            scope = f"メソッド {class_name}.{func_node.name}"
        else:
            scope = f"関数 {func_node.name}"
        self._collect_in_body(func_node.body, scope, violations, source_file)

    def _collect_in_body(
        self,
        body: list[ast.stmt],
        scope: str,
        violations: list[Violation],
        source_file: SourceFile,
    ) -> None:
        for node in body:
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                violations.append(self._make_violation(node, scope, source_file))
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                inner_scope = f"関数 {node.name}"
                self._collect_in_body(node.body, inner_scope, violations, source_file)

    def _make_violation(
        self,
        node: ast.Import | ast.ImportFrom,
        scope: str,
        source_file: SourceFile,
    ) -> Violation:
        import_text = source_file.source.splitlines()[node.lineno - 1].strip()
        return self._meta.create_violation(
            file=source_file.file_path,
            line=node.lineno,
            column=node.col_offset,
            message=f"{scope} 内に import 文があります",
            reason="import 文はモジュールのトップレベルに配置することで依存関係を明示し、インポートのタイミングを予測可能にします",
            suggestion=f"`{import_text}` をファイル冒頭のインポートセクションに移動し、{scope} 内から削除してください",
        )


def _get_top_level_nodes(tree: ast.Module) -> list[ast.AST]:
    """TYPE_CHECKING ブロックを除いたトップレベルノードを返す"""
    result: list[ast.AST] = []
    for node in tree.body:
        if _is_type_checking_block(node):
            continue
        result.append(node)
    return result


def _is_type_checking_block(node: ast.AST) -> bool:
    """ast.If ノードが TYPE_CHECKING ガードかどうかを判定する"""
    if not isinstance(node, ast.If):
        return False
    test = node.test
    if isinstance(test, ast.Name) and test.id == "TYPE_CHECKING":
        return True
    return isinstance(test, ast.Attribute) and test.attr == "TYPE_CHECKING"
