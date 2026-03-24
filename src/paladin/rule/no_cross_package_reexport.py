"""別パッケージのシンボルを __all__ で再エクスポートすることを禁止するルール

仕様は docs/rules/no-cross-package-reexport.md を参照。
"""

from paladin.rule.all_exports_extractor import AllExportsExtractor
from paladin.rule.import_statement import ModulePath
from paladin.rule.package_resolver import PackageResolver
from paladin.rule.types import RuleMeta, SourceFile, Violation


class NoCrossPackageReexportRule:
    """__init__.py の __all__ に別パッケージのシンボルが含まれていないかを AST で検出するルール"""

    def __init__(self) -> None:
        """ルールを初期化する"""
        self._resolver = PackageResolver()
        self._extractor = AllExportsExtractor()
        self._meta = RuleMeta(
            rule_id="no-cross-package-reexport",
            rule_name="No Cross Package Reexport",
            summary="別パッケージのシンボルを自パッケージの __all__ で再エクスポートすることを禁止する",
            intent="__all__ には自パッケージ内で定義したシンボルのみを列挙することで、パッケージ境界を明確に保つ",
            guidance="__init__.py の __all__ に含まれる別パッケージ由来のシンボルを確認する",
            suggestion="別パッケージのシンボルを __all__ から削除し、利用者が各パッケージから直接インポートするよう誘導してください",
        )

    @property
    def meta(self) -> RuleMeta:
        """ルールのメタ情報を返す"""
        return self._meta

    def check(self, source_file: SourceFile) -> tuple[Violation, ...]:
        """単一ファイルに対する違反判定を行う"""
        if not source_file.is_init_py:
            return ()

        current_package = self._resolver.resolve_exact_package_path(source_file.file_path)
        if current_package is None:
            return ()

        all_exports = self._extractor.extract(source_file)
        if not all_exports.has_exports:
            return ()

        import_mapping = NoCrossPackageReexportRule._collect_import_mapping(source_file)

        current_module = ModulePath(current_package)
        violations: list[Violation] = []
        for name in all_exports:
            if name not in import_mapping:
                continue
            import_module = ModulePath(import_mapping[name])
            if not import_module.is_subpackage_of(current_module):
                source_package = import_module.package_key
                violations.append(
                    NoCrossPackageReexportRule._make_violation(
                        source_file=source_file,
                        line=all_exports.lineno,
                        name=name,
                        source_package=source_package,
                        current_package=current_package,
                        meta=self._meta,
                    )
                )
        return tuple(violations)

    @staticmethod
    def _collect_import_mapping(source_file: SourceFile) -> dict[str, str]:
        """トップレベルの from X import Y 文を収集し {シンボル名: インポート元} を返す。

        - as エイリアスがある場合は asname をキーとする
        - 相対インポート（level >= 1）はスキップする
        """
        mapping: dict[str, str] = {}
        for stmt in source_file.top_level_imports:
            if not stmt.is_absolute_from_import:
                continue
            for imported in stmt.names:
                mapping[imported.bound_name] = stmt.module_str
        return mapping

    @staticmethod
    def _make_violation(
        source_file: SourceFile,
        line: int,
        name: str,
        source_package: str,
        current_package: str,
        meta: RuleMeta,
    ) -> Violation:
        """診断メッセージ仕様に従い Violation を生成する"""
        return meta.create_violation_at(
            location=source_file.location(line),
            message=f"__all__ に別パッケージのシンボル `{name}` が含まれている（定義元: `{source_package}`）",
            reason=f"`{source_package}` で定義されたシンボルを `{current_package}` の公開 API として再エクスポートすると、パッケージ境界が曖昧になる",
            suggestion=f"`{name}` を __all__ から削除し、利用者が `from {source_package} import {name}` を直接使用するよう誘導してください",
        )
