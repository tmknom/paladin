"""Rule 層の静的解析ルール。別パッケージのシンボルを __all__ で再エクスポートすることを禁止するルール。

仕様は docs/rules/no-cross-package-reexport.md を参照。
"""

from dataclasses import dataclass

from paladin.rule.all_exports_extractor import AllExportsExtractor
from paladin.rule.import_statement import ModulePath
from paladin.rule.package_resolver import PackageResolver
from paladin.rule.types import DetectionContext, RuleMeta, SourceFile, Violation


@dataclass(frozen=True)
class ReexportSymbol:
    """クロスパッケージ再エクスポート検出に必要なシンボル情報を集約する"""

    line: int
    name: str
    source_package: str
    current_package: str


class ImportMappingCollector:
    """トップレベルのインポートマッピングを収集する"""

    @staticmethod
    def collect(source_file: SourceFile) -> dict[str, str]:
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


class CrossPackageReexportDetector:
    """クロスパッケージ再エクスポートの Violation を生成する"""

    @staticmethod
    def detect(ctx: DetectionContext, symbol: ReexportSymbol) -> Violation:
        """診断メッセージ仕様に従い Violation を生成する"""
        return ctx.meta.create_violation_at(
            location=ctx.source_file.location(symbol.line),
            message=f"__all__ に別パッケージのシンボル `{symbol.name}` が含まれている（定義元: `{symbol.source_package}`）",
            reason=f"`{symbol.source_package}` で定義されたシンボルを `{symbol.current_package}` の公開 API として再エクスポートすると、パッケージ境界が曖昧になる",
            suggestion=f"`{symbol.name}` を __all__ から削除し、利用者が `from {symbol.source_package} import {symbol.name}` を直接使用するよう誘導してください",
        )


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
            background=(
                "__init__.py の __all__ はそのパッケージの公開インタフェースを定義するものです。"
                "別パッケージのシンボルを __all__ に含めると、パッケージ利用者が実際の定義元を知らずに"
                "誤ったパッケージに依存したり、依存関係グラフが不必要に複雑になります。"
            ),
            steps=(
                "__all__ に含まれている別パッケージのシンボルを特定する",
                "そのシンボルを __all__ から削除する",
                "利用者が定義元パッケージから直接インポートするよう誘導する",
            ),
            detection_example=(
                "# 違反: 別パッケージのシンボルを __all__ に含めている\n"
                "# myapp/services/__init__.py\n"
                "from myapp.models import UserModel  # 別パッケージからのインポート\n"
                '__all__ = ["UserModel"]  # 違反\n'
                "\n"
                "# 準拠: 自パッケージのシンボルのみを __all__ に含める\n"
                '__all__ = ["UserService", "OrderService"]'
            ),
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

        import_mapping = ImportMappingCollector.collect(source_file)

        ctx = DetectionContext(meta=self._meta, source_file=source_file)
        current_module = ModulePath(current_package)
        violations: list[Violation] = []
        for name in all_exports:
            if name not in import_mapping:
                continue
            import_module = ModulePath(import_mapping[name])
            if not import_module.is_subpackage_of(current_module):
                symbol = ReexportSymbol(
                    line=all_exports.lineno,
                    name=name,
                    source_package=import_module.package_key,
                    current_package=current_package,
                )
                violations.append(CrossPackageReexportDetector.detect(ctx, symbol))
        return tuple(violations)
