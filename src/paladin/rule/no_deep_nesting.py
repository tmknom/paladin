"""深いネスト禁止ルール"""

import ast
from dataclasses import dataclass

from paladin.rule.types import RuleMeta, SourceFile, Violation

_MAX_DEPTH = 3

# ast.TryStar は Python 3.11+ で存在する
_TRY_STAR_TYPE = getattr(ast, "TryStar", None)


@dataclass(frozen=True)
class FunctionScope:
    """検査対象関数/メソッドの中間表現"""

    node: ast.FunctionDef | ast.AsyncFunctionDef
    class_name: str | None


class FunctionCollector:
    """AST から検査対象関数/メソッドを再帰的に収集する"""

    @staticmethod
    def collect(tree: ast.Module) -> tuple[FunctionScope, ...]:
        """ast.Module から全 FunctionDef / AsyncFunctionDef を再帰的に収集する"""
        result: list[FunctionScope] = []
        FunctionCollector._collect_from_stmts(tree.body, class_name=None, result=result)
        return tuple(result)

    @staticmethod
    def _collect_from_stmts(
        stmts: list[ast.stmt], class_name: str | None, result: list[FunctionScope]
    ) -> None:
        for stmt in stmts:
            if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
                FunctionCollector._collect_from_function(stmt, class_name=class_name, result=result)
            elif isinstance(stmt, ast.ClassDef):
                FunctionCollector._collect_from_class(stmt, result=result)

    @staticmethod
    def _collect_from_class(class_node: ast.ClassDef, result: list[FunctionScope]) -> None:
        for stmt in class_node.body:
            if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
                FunctionCollector._collect_from_function(
                    stmt, class_name=class_node.name, result=result
                )
            elif isinstance(stmt, ast.ClassDef):
                FunctionCollector._collect_from_class(stmt, result=result)

    @staticmethod
    def _collect_from_function(
        func_node: ast.FunctionDef | ast.AsyncFunctionDef,
        class_name: str | None,
        result: list[FunctionScope],
    ) -> None:
        result.append(FunctionScope(node=func_node, class_name=class_name))
        FunctionCollector._collect_nested_from_stmts(func_node.body, result=result)

    @staticmethod
    def _collect_nested_from_stmts(stmts: list[ast.stmt], result: list[FunctionScope]) -> None:
        """ステートメントリストを再帰的に走査してネスト関数/クラスを収集する"""
        for stmt in stmts:
            FunctionCollector._collect_nested_from_stmt(stmt, result=result)

    @staticmethod
    def _collect_nested_from_stmt(stmt: ast.stmt, result: list[FunctionScope]) -> None:
        """単一ステートメントからネスト関数/クラスを収集する"""
        if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
            FunctionCollector._collect_from_function(stmt, class_name=None, result=result)
        elif isinstance(stmt, ast.ClassDef):
            FunctionCollector._collect_from_class(stmt, result=result)
        else:
            for child_stmts in FunctionCollector._iter_child_stmt_lists(stmt):
                FunctionCollector._collect_nested_from_stmts(child_stmts, result=result)

    @staticmethod
    def _iter_child_stmt_lists(node: ast.stmt) -> list[list[ast.stmt]]:
        """複合文ノードの子 stmt リストを返す"""
        result: list[list[ast.stmt]] = []
        if isinstance(node, (ast.If, ast.For, ast.AsyncFor, ast.While)):
            result.append(node.body)
            if node.orelse:
                result.append(node.orelse)
        elif isinstance(node, (ast.With, ast.AsyncWith)):
            result.append(node.body)
        elif isinstance(node, ast.Try) or (
            _TRY_STAR_TYPE is not None and isinstance(node, _TRY_STAR_TYPE)
        ):
            result.append(getattr(node, "body", []))
            for handler in getattr(node, "handlers", []):
                result.append(handler.body)
            orelse: list[ast.stmt] = getattr(node, "orelse", [])
            if orelse:
                result.append(orelse)
            finalbody: list[ast.stmt] = getattr(node, "finalbody", [])
            if finalbody:
                result.append(finalbody)
        elif isinstance(node, ast.Match):
            for case in node.cases:
                result.append(case.body)
        return result


class NestingCalculator:
    """関数 body のネスト深度を副作用なしで算出する"""

    @staticmethod
    def calc_max_depth(stmts: list[ast.stmt]) -> int:
        """ステートメントリストを走査して最大ネスト深度を返す（body直下=depth0）"""
        return NestingCalculator._max_depth_in_stmts(stmts)

    @staticmethod
    def _walk_depth(node: ast.AST) -> int:
        """ノードを走査して「このノードを含めた最大ネスト深度の増加分」を返す。

        複合文の body に入るたびに +1 し、それ以下を再帰的に計算する。
        関数/クラス定義を見つけたら深度 0 を返すだけにする（収集は FunctionCollector が担う）。
        内包表記・ジェネレータ式はネスト深度に含めない（0を返す）。
        """
        # ネスト関数/クラスは独立スコープ → 深度に加算しない
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return 0
        if isinstance(node, ast.ClassDef):
            return 0

        child_stmt_lists: list[list[ast.stmt]] = []
        NestingCalculator._collect_child_stmt_lists(node, child_stmt_lists)

        if not child_stmt_lists:
            return 0

        max_child_depth = NestingCalculator._max_depth_in_lists(child_stmt_lists)
        return 1 + max_child_depth

    @staticmethod
    def _max_depth_in_lists(stmt_lists: list[list[ast.stmt]]) -> int:
        """複数の stmt リストを走査して最大深度を返す"""
        max_depth = 0
        for stmt_list in stmt_lists:
            d = NestingCalculator._max_depth_in_stmts(stmt_list)
            if d > max_depth:
                max_depth = d
        return max_depth

    @staticmethod
    def _max_depth_in_stmts(stmts: list[ast.stmt]) -> int:
        """Stmt リストを走査して最大深度を返す"""
        max_depth = 0
        for stmt in stmts:
            d = NestingCalculator._walk_depth(stmt)
            if d > max_depth:
                max_depth = d
        return max_depth

    @staticmethod
    def _collect_child_stmt_lists(node: ast.AST, dest: list[list[ast.stmt]]) -> None:
        """複合文ノードの body 系リストを dest に収集する"""
        if isinstance(node, ast.If):
            NestingCalculator._collect_if_branches(node, dest)
        elif isinstance(node, (ast.For, ast.AsyncFor, ast.While)):
            dest.append(node.body)
            if node.orelse:
                dest.append(node.orelse)
        elif isinstance(node, (ast.With, ast.AsyncWith)):
            dest.append(node.body)
        elif isinstance(node, ast.Try) or (
            _TRY_STAR_TYPE is not None and isinstance(node, _TRY_STAR_TYPE)
        ):
            NestingCalculator._collect_try_stmts(node, dest)
        elif isinstance(node, ast.Match):
            for case in node.cases:
                dest.append(case.body)

    @staticmethod
    def _collect_if_branches(node: ast.If, dest: list[list[ast.stmt]]) -> None:
        """if/elif/else チェーンの全分岐 body を同一深度として収集する"""
        dest.append(node.body)
        if node.orelse:
            if len(node.orelse) == 1 and isinstance(node.orelse[0], ast.If):
                NestingCalculator._collect_if_branches(node.orelse[0], dest)
            else:
                dest.append(node.orelse)

    @staticmethod
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


class NestingDetector:
    """ネスト深度の閾値判定と Violation 生成を行う"""

    @staticmethod
    def detect(
        scope: FunctionScope,
        depth: int,
        threshold: int,
        meta: RuleMeta,
        source_file: SourceFile,
    ) -> Violation | None:
        """Depth が threshold 以上なら Violation を返す。そうでなければ None を返す"""
        if depth < threshold:
            return None
        if scope.class_name is not None:
            scope_label = f"メソッド {scope.class_name}.{scope.node.name}"
        else:
            scope_label = f"関数 {scope.node.name}"
        message = f"{scope_label} 内のネストが {depth} 段階に達している（最大: {threshold}）"
        return meta.create_violation_at(
            location=source_file.location(scope.node.lineno),
            message=message,
            reason="深いネストはテスタビリティを下げ、手続き的にロジックを持たせすぎている兆候である",
            suggestion="ネストの深い処理をプライベートメソッドに切り出すか、クラス設計を見直してください",
        )


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
            background=(
                "単一メソッドに深いネストが生じるのは、手続き的にロジックを持たせすぎているサインです。"
                "ネストが深くなるほどテスタビリティが低下し、オブジェクトの責務が適切に分割されていないことの兆候でもあります。"
            ),
            steps=(
                "クラス設計を見直し、処理の一部を別のクラスや型に委譲できないか検討する",
                "深くなった部分をプライベートメソッドに抽出してネスト深度を下げる",
                "ガード節（早期リターン）を活用してネストを浅くする",
            ),
            detection_example=(
                "# 違反: ネストが3段階以上\n"
                "for node in source_file.tree.body:    # depth 1\n"
                "    if isinstance(node, ast.Assign):  # depth 2\n"
                "        for target in node.targets:   # depth 3 ← 違反\n"
                "            ...\n\n"
                "# 準拠: プライベートメソッドに切り出してネストを浅くする\n"
                "for node in source_file.tree.body:    # depth 1\n"
                "    if isinstance(node, ast.Assign):  # depth 2\n"
                "        self._check_assign(node, ...)"
            ),
        )

    @property
    def meta(self) -> RuleMeta:
        """ルールのメタ情報を返す"""
        return self._meta

    def check(self, source_file: SourceFile) -> tuple[Violation, ...]:
        """単一ファイルに対する違反判定を行う"""
        violations: list[Violation] = []
        for scope in FunctionCollector.collect(source_file.tree):
            depth = NestingCalculator.calc_max_depth(scope.node.body)
            violation = NestingDetector.detect(scope, depth, _MAX_DEPTH, self._meta, source_file)
            if violation is not None:
                violations.append(violation)
        return tuple(violations)
