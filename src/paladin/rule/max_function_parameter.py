"""Rule 層の静的解析ルール。メソッド/関数の引数数が上限を超えた場合に違反を検出する。"""

import ast
from dataclasses import dataclass

from paladin.rule.types import RuleMeta, SourceFile, Violation

_DEFAULT_MAX_PARAMETERS: int = 3
_DEFAULT_ALLOW_DECORATORS: tuple[str, ...] = ("pytest.fixture", "fixture")

_REASON = "引数が多い関数はプリミティブな値をそのまま受け渡している兆候であり、関連する値をまとめたクラスへのカプセル化機会を逃しています"
_CONFIG_EXAMPLE = (
    "[tool.paladin.rule.max-function-parameter]\n"
    "max-parameters = 3\n"
    'allow-decorators = ["pytest.fixture", "fixture"]'
)
_DETECTION_EXAMPLE = (
    "# 違反: self を除いた引数が4つで上限3を超えている\n"
    "class UserService:\n"
    "    def create_user(self, name: str, email: str, age: int, role: str) -> None:\n"
    "        ...\n\n"
    "# 準拠: バリューオブジェクトに集約して引数を1つに削減\n"
    "class UserService:\n"
    "    def create_user(self, profile: UserProfile) -> None:\n"
    "        ..."
)


@dataclass(frozen=True)
class FunctionScope:
    """検査対象関数の中間表現"""

    node: ast.FunctionDef | ast.AsyncFunctionDef
    is_method: bool


class FunctionCollector:
    """AST から検査対象関数を再帰的に収集する"""

    @staticmethod
    def collect(tree: ast.Module) -> tuple[FunctionScope, ...]:
        """AST から全関数/メソッドノードを再帰的に収集して返す。"""
        result: list[FunctionScope] = []
        FunctionCollector._collect_from_stmts(tree.body, is_method=False, result=result)
        return tuple(result)

    @staticmethod
    def _collect_from_stmts(
        stmts: list[ast.stmt], is_method: bool, result: list[FunctionScope]
    ) -> None:
        for stmt in stmts:
            if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
                FunctionCollector._collect_from_function(stmt, is_method=is_method, result=result)
            elif isinstance(stmt, ast.ClassDef):
                FunctionCollector._collect_from_class(stmt, result=result)

    @staticmethod
    def _collect_from_class(class_node: ast.ClassDef, result: list[FunctionScope]) -> None:
        for stmt in class_node.body:
            if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
                FunctionCollector._collect_from_function(stmt, is_method=True, result=result)
            elif isinstance(stmt, ast.ClassDef):
                FunctionCollector._collect_from_class(stmt, result=result)

    @staticmethod
    def _collect_from_function(
        func_node: ast.FunctionDef | ast.AsyncFunctionDef,
        is_method: bool,
        result: list[FunctionScope],
    ) -> None:
        result.append(FunctionScope(node=func_node, is_method=is_method))
        for stmt in func_node.body:
            if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
                FunctionCollector._collect_from_function(stmt, is_method=False, result=result)
            elif isinstance(stmt, ast.ClassDef):
                FunctionCollector._collect_from_class(stmt, result=result)


class DecoratorAllowChecker:
    """デコレータが許可リストに含まれるかを判定する。

    ast.Name / ast.Attribute / ast.Call を再帰的にドット記法文字列に変換し、
    許可リストと照合することで許可デコレータを識別する。
    """

    @staticmethod
    def decorator_name(decorator: ast.expr) -> str | None:
        """ast.expr をドット記法文字列に変換する。解決不能な場合は None を返す。"""
        if isinstance(decorator, ast.Name):
            return decorator.id
        if isinstance(decorator, ast.Attribute):
            parent = DecoratorAllowChecker.decorator_name(decorator.value)
            if parent is None:
                return None
            return f"{parent}.{decorator.attr}"
        if isinstance(decorator, ast.Call):
            return DecoratorAllowChecker.decorator_name(decorator.func)
        return None

    @staticmethod
    def is_allowed(
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        allow_decorators: frozenset[str],
    ) -> bool:
        """デコレータリストに許可リスト内の名前があれば True を返す。"""
        for decorator in node.decorator_list:
            name = DecoratorAllowChecker.decorator_name(decorator)
            if name is not None and name in allow_decorators:
                return True
        return False


class ParameterCounter:
    """FunctionScope から引数数を算出する。

    is_method=True かつ @staticmethod でない場合、第1引数名が self/cls であれば除外する。
    @classmethod の場合も cls が第1引数名になるため除外対象に含む。
    vararg / kwarg はそれぞれ +1 として加算する。
    """

    @staticmethod
    def count(scope: FunctionScope) -> int:
        """引数数を算出する"""
        args = scope.node.args
        base = len(args.posonlyargs) + len(args.args) + len(args.kwonlyargs)
        if args.vararg is not None:
            base += 1
        if args.kwarg is not None:
            base += 1
        if scope.is_method and not ParameterCounter.is_static(scope.node):
            first_name = ParameterCounter._first_positional_name(args)
            if first_name in ("self", "cls"):
                base -= 1
        return base

    @staticmethod
    def is_static(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
        """@staticmethod デコレータが付いていれば True を返す"""
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name) and decorator.id == "staticmethod":
                return True
        return False

    @staticmethod
    def _first_positional_name(args: ast.arguments) -> str | None:
        """先頭の位置引数名を返す。存在しない場合は None を返す"""
        if args.posonlyargs:
            return args.posonlyargs[0].arg
        if args.args:
            return args.args[0].arg
        return None


class ParameterLimitDetector:
    """引数数と上限の閾値判定を行う"""

    @staticmethod
    def detect(
        scope: FunctionScope,
        count: int,
        limit: int,
        meta: RuleMeta,
        source_file: SourceFile,
    ) -> Violation | None:
        """Count が limit を超えた場合に Violation を返す。そうでなければ None を返す"""
        if count <= limit:
            return None
        message = (
            f"メソッド/関数 `{scope.node.name}` の引数は `{count}` 個です。上限は `{limit}` 個です"
        )
        return meta.create_violation_at(
            location=source_file.location(scope.node.lineno, scope.node.col_offset),
            message=message,
            reason=_REASON,
            suggestion=meta.suggestion,
        )


class MaxFunctionParameterRule:
    """メソッド/関数の引数数が設定された上限を超えた場合に違反を検出するルール

    デフォルト許可デコレータ: ``pytest.fixture``, ``fixture``
    """

    def __init__(
        self,
        max_parameters: int = _DEFAULT_MAX_PARAMETERS,
        allow_decorators: tuple[str, ...] = _DEFAULT_ALLOW_DECORATORS,
    ) -> None:
        """``max_parameters`` と ``allow_decorators`` を受け取り、ルールを初期化する。"""
        self._max = max_parameters
        self._allow = frozenset(allow_decorators)
        self._meta = RuleMeta(
            rule_id="max-function-parameter",
            rule_name="Max Function Parameter",
            summary="メソッド/関数の引数の数が設定された上限を超えた場合に違反を検出する",
            intent="プリミティブな値の氾濫を検出し、バリューオブジェクト/エンティティへのカプセル化機会として開発者へ提示する",
            guidance="各メソッド/関数の引数数を算出し、self/cls を除いた数が上限を超えていないか検査する",
            suggestion="ライフサイクルが近い引数を束ねるバリューオブジェクトやエンティティを定義し、それを単一の引数として受け取るよう変更してください",
            background=(
                "引数の数は、関数/メソッドの設計品質を示すシンプルかつ機械的に検出可能な指標です。"
                "4つ以上の引数が並ぶときは、ライフサイクルが近いプリミティブな値が裸のまま受け渡されている兆候です。"
                "このルールは、そうした箇所をバリューオブジェクトやエンティティへ集約する設計機会として開発者に提示します。"
            ),
            steps=(
                "4つ以上の引数があるシグネチャを抽出する",
                "ライフサイクルや責務が近い引数の束を見つける",
                "バリューオブジェクト/エンティティを定義し、引数を集約する",
            ),
            config_example=_CONFIG_EXAMPLE,
            detection_example=_DETECTION_EXAMPLE,
        )

    @property
    def meta(self) -> RuleMeta:
        """このルールのメタ情報を返す。"""
        return self._meta

    def check(self, source_file: SourceFile) -> tuple[Violation, ...]:
        """単一ファイルに対する違反判定を行う。

        Flow:
            1. FunctionCollector で全関数/メソッドノードを収集する
            2. DecoratorAllowChecker で許可デコレータを持つノードをスキップする
            3. ParameterCounter で引数数を算出する
            4. ParameterLimitDetector で上限超過を判定し Violation を生成する
        """
        violations: list[Violation] = []
        for scope in FunctionCollector.collect(source_file.tree):
            if DecoratorAllowChecker.is_allowed(scope.node, self._allow):
                continue
            count = ParameterCounter.count(scope)
            violation = ParameterLimitDetector.detect(
                scope, count, self._max, self._meta, source_file
            )
            if violation is not None:
                violations.append(violation)
        return tuple(violations)
