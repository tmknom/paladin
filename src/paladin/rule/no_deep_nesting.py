"""深いネスト禁止ルール"""

import ast

from paladin.rule.types import RuleMeta, SourceFile, Violation

_MAX_DEPTH = 3

# ast.TryStar は Python 3.11+ で存在する
_TRY_STAR_TYPE = getattr(ast, "TryStar", None)


class NoDeepNestingRule:
    """関数・メソッド内の深すぎるネストを AST で検出するルール"""

    def __init__(self) -> None:
        """ルールを初期化する"""
        self._meta = RuleMeta(
            rule_id="no-deep-nesting",
            rule_name="No Deep Nesting",
            summary="深いネストの使用を禁止する",
            intent="ネストを浅く保つことでテスタビリティと可読性を向上させる",
            guidance="関数・メソッド内のネスト深度が3段階以上の箇所を確認する",
            suggestion="ネストの深い処理をプライベートメソッドに切り出すか、クラス設計を見直してください",
        )

    @property
    def meta(self) -> RuleMeta:
        """ルールのメタ情報を返す"""
        return self._meta

    def check(self, source_file: SourceFile) -> tuple[Violation, ...]:
        """単一ファイルに対する違反判定を行う"""
        violations: list[Violation] = []
        self._visit_module(source_file.tree.body, violations=violations, source_file=source_file)
        return tuple(violations)

    def _visit_module(
        self,
        stmts: list[ast.stmt],
        violations: list[Violation],
        source_file: SourceFile,
    ) -> None:
        """ステートメントリストからトップレベルの関数・クラスを探索する"""
        for stmt in stmts:
            if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self._check_function(
                    stmt, class_name=None, violations=violations, source_file=source_file
                )
            elif isinstance(stmt, ast.ClassDef):
                self._visit_class(stmt, violations=violations, source_file=source_file)

    def _visit_class(
        self,
        class_node: ast.ClassDef,
        violations: list[Violation],
        source_file: SourceFile,
    ) -> None:
        """クラス内のメソッドを検査する"""
        for stmt in class_node.body:
            if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self._check_function(
                    stmt, class_name=class_node.name, violations=violations, source_file=source_file
                )
            elif isinstance(stmt, ast.ClassDef):
                # ネストクラスも独立スコープとして処理
                self._visit_class(stmt, violations=violations, source_file=source_file)

    def _check_function(
        self,
        func_node: ast.FunctionDef | ast.AsyncFunctionDef,
        class_name: str | None,
        violations: list[Violation],
        source_file: SourceFile,
    ) -> None:
        """関数/メソッドのネスト深度を計算し、超過していれば違反を追加する"""
        nested_funcs: list[ast.FunctionDef | ast.AsyncFunctionDef] = []
        nested_classes: list[ast.ClassDef] = []

        max_depth = _calc_max_depth(
            func_node.body, nested_funcs=nested_funcs, nested_classes=nested_classes
        )

        if max_depth >= _MAX_DEPTH:
            if class_name is not None:
                scope = f"メソッド {class_name}.{func_node.name}"
            else:
                scope = f"関数 {func_node.name}"
            message = f"{scope} 内のネストが {max_depth} 段階に達している（最大: {_MAX_DEPTH}）"
            violations.append(
                self._meta.create_violation_at(
                    location=source_file.location(func_node.lineno),
                    message=message,
                    reason="深いネストはテスタビリティを下げ、手続き的にロジックを持たせすぎている兆候である",
                    suggestion="ネストの深い処理をプライベートメソッドに切り出すか、クラス設計を見直してください",
                )
            )

        # ネスト関数を独立スコープとして検査
        for nested_func in nested_funcs:
            self._check_function(
                nested_func,
                class_name=None,
                violations=violations,
                source_file=source_file,
            )

        # ネストクラスを独立スコープとして検査
        for nested_class in nested_classes:
            self._visit_class(nested_class, violations=violations, source_file=source_file)


def _calc_max_depth(
    stmts: list[ast.stmt],
    nested_funcs: list[ast.FunctionDef | ast.AsyncFunctionDef],
    nested_classes: list[ast.ClassDef],
) -> int:
    """ステートメントリストを走査して最大ネスト深度を返す（body直下=depth0）"""
    max_depth = 0
    for stmt in stmts:
        depth = _walk_depth(stmt, nested_funcs=nested_funcs, nested_classes=nested_classes)
        if depth > max_depth:
            max_depth = depth
    return max_depth


def _collect_try_stmts(node: ast.AST, dest: list[list[ast.stmt]]) -> None:
    """Try 系ノード（ast.Try / ast.TryStar）から子 stmt リストを収集する。

    ast.TryStar は Python 3.11+ の try...except* 構文であり型スタブが存在しないため、
    ast.Try と共通の構造（body/handlers/orelse/finalbody）を getattr で動的にアクセスする。
    """
    dest.append(getattr(node, "body", []))
    for handler in getattr(node, "handlers", []):
        dest.append(handler.body)
    orelse: list[ast.stmt] = getattr(node, "orelse", [])
    if orelse:
        dest.append(orelse)
    finalbody: list[ast.stmt] = getattr(node, "finalbody", [])
    if finalbody:
        dest.append(finalbody)


def _walk_depth(
    node: ast.AST,
    nested_funcs: list[ast.FunctionDef | ast.AsyncFunctionDef],
    nested_classes: list[ast.ClassDef],
) -> int:
    """ノードを走査して「このノードを含めた最大ネスト深度の増加分」を返す。

    複合文の body に入るたびに +1 し、それ以下を再帰的に計算する。
    関数/クラス定義を見つけたら独立スコープとして nested_funcs/nested_classes に登録し、
    深度計算には加算しない（0を返す）。
    内包表記・ジェネレータ式はネスト深度に含めない（0を返す）。
    """
    # ネスト関数/クラスは独立スコープ → 深度に加算しない
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        nested_funcs.append(node)
        return 0
    if isinstance(node, ast.ClassDef):
        nested_classes.append(node)
        return 0

    # 複合文の body/orelse/handlers/finalbody を収集する
    child_stmt_lists: list[list[ast.stmt]] = []

    if isinstance(node, (ast.If, ast.For, ast.AsyncFor, ast.While)):
        child_stmt_lists.append(node.body)
        if node.orelse:
            child_stmt_lists.append(node.orelse)

    elif isinstance(node, (ast.With, ast.AsyncWith)):
        child_stmt_lists.append(node.body)

    elif isinstance(node, ast.Try) or (
        _TRY_STAR_TYPE is not None and isinstance(node, _TRY_STAR_TYPE)
    ):
        # ast.Try と ast.TryStar（Python 3.11+ の except*）は同じ構造を持つ
        _collect_try_stmts(node, child_stmt_lists)

    elif isinstance(node, ast.Match):
        for case in node.cases:
            child_stmt_lists.append(case.body)

    if not child_stmt_lists:
        # 複合文でない or 複合文だが子リストがない場合
        return 0

    # 各子リスト内の最大深度を計算し、+1（この複合文に入る分）する
    max_child_depth = 0
    for stmt_list in child_stmt_lists:
        for stmt in stmt_list:
            d = _walk_depth(stmt, nested_funcs=nested_funcs, nested_classes=nested_classes)
            if d > max_child_depth:
                max_child_depth = d

    return 1 + max_child_depth
