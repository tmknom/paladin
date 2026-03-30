"""モジュールおよびクラスの docstring 存在を要求するルール

仕様は docs/rules/require-docstring.md を参照。
"""

import ast

from paladin.rule.types import RuleMeta, SourceFile, Violation

_MODULE_REASON = "モジュールの設計上の位置づけや制約を表明する手段がなくなります"
_MODULE_SUGGESTION = "ファイル冒頭にモジュール docstring を追加してください"
_CLASS_REASON = "クラスの責務・契約を表明する手段がなくなります"
_CLASS_SUGGESTION = "クラス定義の直後に docstring を追加してください"


class DocstringChecker:
    """AST ノードの docstring 有無を判定する純粋関数群"""

    @staticmethod
    def has_docstring(body: list[ast.stmt]) -> bool:
        """Body の先頭要素が docstring (ast.Expr + ast.Constant(str)) なら True を返す"""
        if not body:
            return False
        first = body[0]
        return (
            isinstance(first, ast.Expr)
            and isinstance(first.value, ast.Constant)
            and isinstance(first.value.value, str)
        )

    @staticmethod
    def is_empty_source(source: str) -> bool:
        """Source が空または空白のみなら True を返す"""
        return source.strip() == ""


class ModuleDocstringDetector:
    """モジュール docstring 欠如の Violation 生成"""

    @staticmethod
    def detect(source_file: SourceFile, meta: RuleMeta) -> Violation | None:
        """モジュール docstring がなければ Violation を返す。空ファイルはスキップする"""
        if DocstringChecker.is_empty_source(source_file.source):
            return None
        if DocstringChecker.has_docstring(source_file.tree.body):
            return None
        return meta.create_violation_at(
            location=source_file.location(line=1),
            message=f"{source_file.file_path.name} にモジュール docstring がありません",
            reason=_MODULE_REASON,
            suggestion=_MODULE_SUGGESTION,
        )


class ClassDocstringDetector:
    """クラス docstring 欠如の Violation 生成"""

    @staticmethod
    def detect(
        class_node: ast.ClassDef, source_file: SourceFile, meta: RuleMeta
    ) -> Violation | None:
        """クラス docstring がなければ Violation を返す"""
        if DocstringChecker.has_docstring(class_node.body):
            return None
        return meta.create_violation_at(
            location=source_file.location(line=class_node.lineno),
            message=f"クラス {class_node.name} に docstring がありません",
            reason=_CLASS_REASON,
            suggestion=_CLASS_SUGGESTION,
        )


class RequireDocstringRule:
    """モジュールおよびクラスに docstring の存在を要求するルール"""

    def __init__(self) -> None:
        """ルールを初期化する"""
        self._meta = RuleMeta(
            rule_id="require-docstring",
            rule_name="Require Docstring",
            summary="モジュールおよびクラスに docstring の存在を要求する",
            intent="モジュールの設計意図やクラスの責務・契約を表明する手段を確保する",
            guidance="モジュール先頭の docstring とクラス定義直後の docstring を確認する",
            suggestion="docstring を追加して、モジュールやクラスの責務を記述してください",
        )

    @property
    def meta(self) -> RuleMeta:
        """ルールのメタ情報を返す"""
        return self._meta

    def check(self, source_file: SourceFile) -> tuple[Violation, ...]:
        """単一ファイルに対する違反判定を行う"""
        violations: list[Violation] = []

        if not source_file.is_test_file:
            module_violation = ModuleDocstringDetector.detect(source_file, self._meta)
            if module_violation:
                violations.append(module_violation)
            violations.extend(self._check_classes(source_file))

        return tuple(violations)

    def _check_classes(self, source_file: SourceFile) -> list[Violation]:
        """全 ClassDef を走査してクラス docstring 違反を収集する"""
        class_nodes = [n for n in ast.walk(source_file.tree) if isinstance(n, ast.ClassDef)]
        results = [ClassDocstringDetector.detect(n, source_file, self._meta) for n in class_nodes]
        return [v for v in results if v is not None]
