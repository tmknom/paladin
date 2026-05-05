"""Rule 層の静的解析ルール。モジュールレベル関数を AST で検出する。"""

import ast

from paladin.rule.types import RuleMeta, SourceFile, Violation

_DEFAULT_ALLOW_DECORATORS: tuple[str, ...] = ("pytest.fixture", "fixture")

_REASON = "モジュールレベル関数は責務の所在が不明確であり、テスト時の差し替えが困難です"
_CONFIG_EXAMPLE = (
    '[tool.paladin.rule.no-module-level-function]\nallow-decorators = ["pytest.fixture", "fixture"]'
)
_DETECTION_EXAMPLE = (
    "# 違反: モジュールレベルに関数が定義されている\n"
    "def calc_file_length(source: str) -> int:\n"
    "    ...\n\n"
    "# 準拠: クラスの静的メソッドとして定義されている\n"
    "class FileLengthCalculator:\n"
    "    @staticmethod\n"
    "    def calc(source: str) -> int:\n"
    "        ..."
)


class ModuleLevelFunctionCollector:
    """ast.Module.body 直下の関数定義を収集する。

    collect() は ast.Module.body を直接走査する（ast.walk は使わない）。
    戻り値は FunctionDef | AsyncFunctionDef のタプルである。
    """

    @staticmethod
    def collect(tree: ast.Module) -> tuple[ast.FunctionDef | ast.AsyncFunctionDef, ...]:
        """tree.body を線形走査し FunctionDef / AsyncFunctionDef のみ抽出する"""
        result: list[ast.FunctionDef | ast.AsyncFunctionDef] = []
        for stmt in tree.body:
            if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
                result.append(stmt)
        return tuple(result)


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


class ModuleLevelFunctionDetector:
    """モジュールレベル関数の Violation を生成する。

    detect() は ast.FunctionDef / ast.AsyncFunctionDef ノードを受け取り、
    対応する Violation を生成して返す。
    """

    @staticmethod
    def detect(
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        source_file: SourceFile,
        meta: RuleMeta,
    ) -> Violation:
        """関数ノードから Violation を生成する"""
        return meta.create_violation_at(
            location=source_file.location(node.lineno, node.col_offset),
            message=f"モジュールレベルに関数 `{node.name}` が定義されています",
            reason=_REASON,
            suggestion=(
                f"`{node.name}` をクラスの `@staticmethod` / `@classmethod` / "
                "インスタンスメソッドとして再定義してください"
            ),
        )


class NoModuleLevelFunctionRule:
    """Rule Protocol を実装するオーケストレーター。モジュール直下に定義された関数を AST で検出する。

    デフォルト許可デコレータ: ``pytest.fixture``, ``fixture``
    """

    def __init__(self, allow_decorators: tuple[str, ...] = _DEFAULT_ALLOW_DECORATORS) -> None:
        """ルールを初期化する"""
        self._allow = frozenset(allow_decorators)
        self._meta = RuleMeta(
            rule_id="no-module-level-function",
            rule_name="No Module Level Function",
            summary="モジュールの直下に定義された関数（モジュールレベル関数）を禁止する",
            intent="振る舞いをクラスに所属させることで責務の所在を明確にし、テスト時の差し替えを容易にする",
            guidance="ast.Module.body 直下の FunctionDef / AsyncFunctionDef を確認する",
            suggestion=(
                "関数をクラスの `@staticmethod` / `@classmethod` / "
                "インスタンスメソッドとして再定義してください"
            ),
            background=(
                "Paladin はオブジェクト指向スタイルを徹底しており、振る舞いをクラスに所属させることを設計原則としています。"
                "クラスに属さない関数は「誰の振る舞いか」が不明確であり、関連するデータと振る舞いが分離してしまいます。"
            ),
            steps=(
                "クラス設計を見直し、関数がどのデータや状態と関わるかを特定する",
                "関数を適切なクラスの @staticmethod / @classmethod / インスタンスメソッドとして移動する",
                "移動先クラスが存在しない場合は新しいクラスを作成する",
            ),
            config_example=_CONFIG_EXAMPLE,
            detection_example=_DETECTION_EXAMPLE,
        )

    @property
    def meta(self) -> RuleMeta:
        """ルールのメタ情報を返す"""
        return self._meta

    def check(self, source_file: SourceFile) -> tuple[Violation, ...]:
        """単一ファイルに対する違反判定を行う。

        Flow:
            1. ModuleLevelFunctionCollector でモジュール直下の関数ノードを収集する
            2. DecoratorAllowChecker で許可デコレータを持つノードをスキップする
            3. ModuleLevelFunctionDetector で Violation を生成する
        """
        violations: list[Violation] = []
        for node in ModuleLevelFunctionCollector.collect(source_file.tree):
            if DecoratorAllowChecker.is_allowed(node, self._allow):
                continue
            violations.append(ModuleLevelFunctionDetector.detect(node, source_file, self._meta))
        return tuple(violations)
