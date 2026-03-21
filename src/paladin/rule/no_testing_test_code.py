"""tests/ 配下のコードに対するテストコードの作成を禁止するルール

仕様は docs/rules/no-testing-test-code.md を参照。
"""

import ast
import re

from paladin.rule.types import RuleMeta, SourceFile, SourceFiles, Violation


class NoTestingTestCodeRule:
    """tests/ 配下で定義されたクラスや関数に対するテストコードを AST で検出するルール"""

    def __init__(self) -> None:
        """ルールを初期化する"""
        self._meta = RuleMeta(
            rule_id="no-testing-test-code",
            rule_name="No Testing Test Code",
            summary="tests/ 配下のコードに対するテストの作成を禁止する",
            intent="テスト用コードをテストすることは無駄。複雑なら src/ に移動すべき",
            guidance="tests/ からインポートしたシンボルにテストクラスや関数を作成していないか確認する",
            suggestion="テストを削除するか、複雑なロジックを src/ に移動する",
        )

    @property
    def meta(self) -> RuleMeta:
        """ルールのメタ情報を返す"""
        return self._meta

    def check(self, source_files: SourceFiles) -> tuple[Violation, ...]:
        """複数ファイルに対する違反判定を行う"""
        violations: list[Violation] = []
        for source_file in source_files:
            if not source_file.is_test_file:
                continue
            if source_file.file_path.name == "conftest.py":
                continue
            violations.extend(self._check_file(source_file))
        return tuple(violations)

    def _check_file(self, source_file: SourceFile) -> list[Violation]:
        """1ファイルの AST を走査して違反を返す"""
        test_imports = self._collect_test_imports(source_file)
        if not test_imports:
            return []

        violations: list[Violation] = []
        for node in source_file.tree.body:
            if (
                isinstance(node, ast.ClassDef)
                and (v := self._check_class_node(source_file, node, test_imports))
            ) or (
                isinstance(node, ast.FunctionDef)
                and (v := self._check_func_node(source_file, node, test_imports))
            ):
                violations.append(v)
        return violations

    def _check_class_node(
        self,
        source_file: SourceFile,
        node: ast.ClassDef,
        test_imports: dict[str, str],
    ) -> Violation | None:
        """TestXxx クラスが tests/ インポートと名前一致する場合に Violation を返す"""
        if not node.name.startswith("Test"):
            return None
        imported_name = node.name[len("Test") :]
        if imported_name not in test_imports:
            return None
        return self._make_violation(source_file, node, test_imports[imported_name])

    def _check_func_node(
        self,
        source_file: SourceFile,
        node: ast.FunctionDef,
        test_imports: dict[str, str],
    ) -> Violation | None:
        """test_xxx 関数が tests/ インポートの snake_case 名と一致する場合に Violation を返す"""
        if not node.name.startswith("test_"):
            return None
        func_suffix = node.name[len("test_") :]
        for bound_name, original_name in test_imports.items():
            snake = self._to_snake_case(bound_name)
            if func_suffix == snake or func_suffix.startswith(snake + "_"):
                return self._make_violation(source_file, node, original_name)
        return None

    def _collect_test_imports(self, source_file: SourceFile) -> dict[str, str]:
        """`from tests.xxx import Yyy` 形式のインポートを {bound_name: original_name} で返す"""
        result: dict[str, str] = {}
        for imp in source_file.absolute_from_imports:
            if imp.module.top_level != "tests":
                continue
            for imported_name in imp.names:
                result[imported_name.bound_name] = imported_name.name
        return result

    def _to_snake_case(self, name: str) -> str:
        """CamelCase を snake_case に変換する"""
        s = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", name)
        s = re.sub(r"([a-z\d])([A-Z])", r"\1_\2", s)
        return s.lower()

    def _make_violation(
        self, source_file: SourceFile, node: ast.ClassDef | ast.FunctionDef, name: str
    ) -> Violation:
        """診断メッセージ仕様に従い Violation を生成する"""
        return self._meta.create_violation_at(
            location=source_file.location(node.lineno, node.col_offset),
            message=f"`tests/` 配下のコード `{name}` に対するテストが定義されている",
            reason="テスト用コードをテストすることは無駄なメンテナンスコストを生む。テストが必要なほど複雑なコードを `tests/` 配下に置くべきではない",
            suggestion=f"`{name}` のテストを削除してください。テストが必要なほど複雑なら、そのロジックを `src/` 配下に移動することを検討してください",
        )
