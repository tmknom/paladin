# ルール実装設計

`src/paladin/rule/` パッケージにおけるルール実装の設計方針を文書化する。新規ルール追加時・既存ルール改修時に参照する設計指針をまとめる。

## 目的とスコープ

対象: Rule クラスの内部構造パターン、AST 走査の設計方針、純粋関数の設計方針、新規ルール追加ガイド

以下は他ドキュメントに委譲する。

| 関心事 | 参照先 |
|--------|--------|
| Protocol / Composition Root / Orchestrator の一般原則 | [Pythonアーキテクチャ設計](architecture.md) |
| テストの書き方・Fake パターン・テスト命名規則 | [Pythonテスト設計](testing.md) |
| ルール設定の書式（max-lines, allow-dirs 等） | [設定ファイルインターフェイス設計](configuration.md) |
| 個別ルールの仕様・検出パターン・診断メッセージ | `docs/rules/<rule-id>.md` |

## パッケージ構成

### ファイル配置

| カテゴリ | ファイル | 役割 |
|----------|---------|------|
| **Protocol** | `protocol.py` | Rule / MultiFileRule / PreparableRule Protocol 定義 |
| **型定義** | `types.py` | SourceFile / SourceFiles / Violation / Violations / RuleMeta 等 |
| **値オブジェクト** | `import_statement.py` | ModulePath / ImportStatement / AbsoluteFromImport / SourceLocation |
| **ドメインサービス** | `all_exports_extractor.py` | `__all__` シンボル抽出（AllExports 値オブジェクトを含む） |
| **ドメインサービス** | `package_resolver.py` | ファイルパス -> パッケージ名解決 |
| **ドメインサービス** | `own_package_resolver.py` | 自パッケージ解決（テスト <-> プロダクション対応を含む） |
| **インフラ** | `rule_set.py` | 複数ルールの管理・実行・一覧・検索 |
| **インフラ** | `rule_set_factory.py` | プロダクション用ルール群の構築（Composition Root） |
| **ルール実装** | `<rule_id>.py` × 16 | 個別ルール（13 単一ファイル + 3 複数ファイル） |

### 公開 API

`paladin.rule` の `__all__` が唯一の互換性対象となる。個別ルールクラスは公開 API に含まれず、すべて `RuleSetFactory` 経由で利用する。

```python
# 公開: Rule, RuleSet, RuleSetFactory, SourceFile, SourceFiles,
#       Violation, Violations, RuleMeta, OverrideEntry, PerFileIgnoreEntry
from paladin.rule import RuleSetFactory

# 禁止: 個別ルールクラスへの直接 import
from paladin.rule.no_deep_nesting import NoDeepNestingRule  # NG
```

## check() メソッドの構造パターン

### 3類型

全16ルールの `check()` 実装は以下の3類型に分類できる。

| 類型 | 説明 | 該当ルール |
|------|------|-----------|
| **早期リターン型** | 条件チェック後に `()` か `(violation,)` を直接返す | `max_file_length`, `no_non_init_all`, `require_all_export` |
| **ローカルリスト蓄積型** | `check()` 内で `violations: list` を宣言し、Detector クラスへ委譲しながら蓄積する | `no_relative_import`, `no_mock_usage`, `no_cross_package_reexport`, `require_qualified_third_party`, `no_third_party_import`, `no_cross_package_import` |
| **責務別クラス orchestrator 型** | Collector / Calculator / Detector の責務別クラスを呼び出す薄い orchestrator | `max_class_length`, `max_method_length`, `no_deep_nesting`, `no_local_import`, `no_testing_test_code`, `no_direct_internal_import`, `no_unused_export` |

各類型の選択基準:

- 検査ロジックがシンプルで分岐のみ → 早期リターン型
- import 文やノードをフラットに走査して判定 → ローカルリスト蓄積型
- AST 再帰走査 + 意味情報算出 + 閾値判定が必要 → 責務別クラス orchestrator 型

### 責務別クラスの配置状況

責務別クラスを持つルールの一覧。

| ファイル | 責務別クラス | 役割 |
|---------|-------------|------|
| `no_deep_nesting.py` | `FunctionScope`, `FunctionCollector`, `NestingCalculator`, `NestingDetector` | スコープ列挙・深度算出・閾値判定 |
| `max_class_length.py` | `ClassScope`, `ClassCollector`, `ClassLengthCalculator`, `ClassLengthDetector` | クラス列挙・行数算出・閾値判定 |
| `max_method_length.py` | `FunctionScope`, `FunctionCollector`, `MethodLengthCalculator`, `MethodLengthDetector` | 関数列挙・行数算出・閾値判定 |
| `no_local_import.py` | `LocalImport`, `LocalImportCollector`, `LocalImportDetector` | ローカルインポート収集・違反生成 |
| `max_file_length.py` | `FileLengthCalculator`, `FileLengthDetector` | ファイル行数算出・閾値判定 |
| `no_mock_usage.py` | `MockUsageDetector` | モックインポートの違反生成 |
| `no_third_party_import.py` | `ThirdPartyChecker`, `ThirdPartyImportDetector` | サードパーティ判定・違反生成 |
| `require_qualified_third_party.py` | `QualifiedThirdPartyDetector` | 修飾インポート違反の生成 |
| `no_cross_package_import.py` | `EntrypointChecker`, `CrossPackageImportChecker`, `CrossPackageImportDetector` | エントリポイント判定・クロスパッケージ判定・違反生成 |
| `no_cross_package_reexport.py` | `ImportMappingCollector`, `CrossPackageReexportDetector` | インポートマッピング収集・違反生成 |
| `no_relative_import.py` | `RelativeImportDetector` | 相対インポート違反の生成 |
| `no_non_init_all.py` | `NonInitAllDetector` | __init__.py 外 __all__ 違反の生成 |
| `require_all_export.py` | `PublicSymbolCollector`, `AllExportDetector` | 公開シンボル収集・違反生成 |
| `no_testing_test_code.py` | `TestImportCollector`, `TestTargetDetector` | テストインポート収集・テスト対象検出 |
| `no_direct_internal_import.py` | `SrcRootResolver`, `SubpackageChecker`, `PackageExportCollector`, `InternalImportDetector` | src ルート推定・サブパッケージ確認・エクスポート収集・違反生成 |
| `no_unused_export.py` | `ExportCollector`, `UsageCollector`, `UnusedExportDetector` | エクスポート収集・利用収集・未使用判定 |

ルール実装ファイル内のモジュールレベル関数（`_` プレフィックス）は廃止済み。ヘルパーロジックは責務別クラスの `@staticmethod` か、Rule クラス自身の `@staticmethod` / インスタンスメソッドとして配置されている。

### 中間データ構造の使用状況

ルール間で共有される専用の中間値オブジェクトは `AllExports`（`all_exports_extractor.py`）のみである。他はすべて `dict[str, str]` や `set[str]` などのプリミティブコレクションで中間状態を表現している。`import_statement.py` の値オブジェクト群（`ModulePath`, `ImportStatement` 等）は複数ルールで共有されている。

## 設計方針

AST 走査を伴う複雑なルールに対する設計方針を定める。全ルールがこのモデルを完全に実装する必要はなく、ルールの複雑さに応じて適切な構造パターンを選択する。

### 責務の分離モデル

AST 走査を伴うルールには4つの独立した責務がある。これらを分離することで、純粋関数化・テスタビリティ向上・変更容易性向上を実現する。

| 責務 | 入力 | 出力 | 性質 |
|------|------|------|------|
| **検査対象の列挙** | `ast.Module` | `Iterable[対象ノード]` | 純粋関数 |
| **意味情報の抽出** | 対象ノード | 測定値（`int`, `bool` 等） | 純粋関数 |
| **判定** | 測定値 + 閾値 | `Violation \| None` | 純粋関数 |
| **Violation 生成** | 判定結果 + `RuleMeta` + `SourceFile` | `Violation` | 純粋（`RuleMeta.create_violation_at()` 呼び出し） |

Rule クラスはこれら4責務をつなぐ **薄い orchestrator** として残す。

```
Rule.check()
    ↓ 検査対象の列挙
    ↓ for 対象ノード in 検査対象:
    │   意味情報の抽出
    │   判定
    │   Violation 生成（違反時のみ）
    └→ tuple(violations)
```

### 純粋関数の設計方針

**クラスを「パッケージ以外の名前空間」として活用し、純粋関数をスタティックメソッドとして責務別クラスに配置する。**

理由:

- モジュールレベル関数（`_` プレフィックス）は数が増えると名前空間がフラットになり、どの関数がどの責務に属するか不明瞭になる
- クラスを名前空間とすることで責務の境界が明示される（`NestingCalculator.calc_max_depth()` vs `NestingDetector.detect()`）
- `@staticmethod` により `self` への依存がなく、副作用なしが型レベルで保証される
- テスト時にクラス単位で import できるため、テスト対象の特定が容易になる

`no_deep_nesting` を例にした実装イメージ:

```python
class FunctionScope:
    """検査対象関数のスコープ情報（中間表現）"""
    node: ast.FunctionDef | ast.AsyncFunctionDef
    class_name: str | None


class FunctionCollector:
    """AST から検査対象の関数スコープを列挙する純粋関数群"""

    @staticmethod
    def collect(tree: ast.Module) -> tuple[FunctionScope, ...]:
        """モジュールから全関数スコープを再帰的に収集する"""
        ...


class NestingCalculator:
    """AST からネスト深度を算出する純粋関数群"""

    @staticmethod
    def calc_max_depth(stmts: list[ast.stmt]) -> int:
        """関数 body のステートメントリストから最大ネスト深度を返す"""
        ...


class NestingDetector:
    """ネスト深度の閾値判定を行う純粋関数群"""

    @staticmethod
    def detect(
        scope: FunctionScope,
        depth: int,
        threshold: int,
        meta: RuleMeta,
        source_file: SourceFile,
    ) -> Violation | None:
        """深度が閾値以上なら Violation を返す"""
        ...


class NoDeepNestingRule:
    """Rule クラスは薄い orchestrator"""

    def check(self, source_file: SourceFile) -> tuple[Violation, ...]:
        violations: list[Violation] = []
        for scope in FunctionCollector.collect(source_file.tree):
            depth = NestingCalculator.calc_max_depth(scope.node.body)
            violation = NestingDetector.detect(scope, depth, _MAX_DEPTH, self._meta, source_file)
            if violation is not None:
                violations.append(violation)
        return tuple(violations)
```

### ヘルパーメソッドの戻り値スタイル

| 戻り値型 | 採用場面 | 例 |
|---------|---------|-----|
| `Violation \| None` | Detector の `detect()` / Rule 内の `_detect_*()` | `NestingDetector.detect()` |
| `Violation` | 違反確定後の `_make_violation()` 系 | `NoNonInitAllRule._make_violation()` |
| `list[Violation]` | 1要素から複数違反が展開されうるヘルパー | `NoCrossPackageImportRule._check_from_import()` |
| `int` / `bool` / `tuple[T, ...]` | Calculator / Collector の補助データ返却 | `FileLengthCalculator.calc()` |

設計規範:

- void スタイル（引数変異）は使わない
- `Violation | None` を基本とし、1要素から複数違反が展開される場合は `list[Violation]` を使う

### 可変状態と副作用の分離

- `violations` への append は `check()` メソッド内に閉じ込める。ヘルパーメソッドに `violations` を引数として渡して変異させるパターンは **採用しない**
- 検査対象の列挙は `Iterable[T]` または `tuple[T, ...]` を返す純粋関数として実装する
- 判定ロジックは `Violation | None` を返す純粋関数として実装する（`bool` + 別途 Violation 生成は分割しすぎ）

### 中間表現の設計基準

AST ノードをそのまま使うケースと中間表現（値オブジェクト）を導入するケースの判断基準:

| 状況 | 方針 |
|------|------|
| 単一の AST ノードから直接情報が取れる | AST ノードをそのまま渡す |
| 複数の AST ノードや付随情報（スコープ名等）をまとめて扱う | `@dataclass(frozen=True)` の中間値オブジェクトを定義する |
| 同一の中間構造を2ルール以上で構築する | 共有値オブジェクトとして `types.py` または専用ファイルに切り出す（YAGNI） |
| 1ルール内のみで使う中間構造 | そのルールのファイル内にプライベートクラスとして定義する |

### AST 走査の設計方針

**AST 走査そのものの手続き性は許容する。** 無理に関数型スタイルへ寄せると可読性が下がる。

| 判断 | 方針 |
|------|------|
| `ast.walk` vs 手動再帰 | ノード種別でフィルタするだけなら `ast.walk`。スコープ境界や深度を追跡するなら手動再帰 |
| `ast` モジュールの型の抽象化 | 行わない。Python 標準ライブラリの安定した API であり、Protocol で隔離する理由がない（YAGNI） |
| Python バージョン依存ノード（`ast.TryStar` 等） | `getattr(ast, "TryStar", None)` でランタイムチェックし、`None` ガードを置く |

## 新規ルール追加ガイド

### 追加手順

1. ルール仕様を `docs/rules/<rule-id>.md` に作成する
2. 下表を参照して Protocol の組み合わせを選択する
3. `src/paladin/rule/<rule_id_snake>.py` にルールクラスを実装する（設計方針に従う）
4. `rule_set_factory.py` にルールインスタンスを追加する
5. `tests/unit/test_rule/test_<rule_id_snake>.py` にテストを追加する
6. `test_list/test_provider.py` と `test_view/test_provider.py` のルール数を更新する
7. E2E テストを `e2e-tests/<rule-id>/` に追加する

### Protocol の選択基準

| 条件 | 採用する Protocol |
|------|-----------------|
| 単一ファイルを検査する | `Rule` |
| 全ファイルを横断して検査する（未使用 export 検出等） | `MultiFileRule` |
| `check()` の前に全ファイル情報から事前計算が必要（ルートパッケージ解決等） | `Rule` または `MultiFileRule` に加えて `PreparableRule` も実装する |

### 新規ルールの実装パターン

新規ルールは設計方針に従い実装する。

- 検査ロジックがシンプルで分岐のみ → 早期リターン型（条件チェック + 直接タプル返却）
- import 文やノードをフラットに走査して判定 → ローカルリスト蓄積型（`check()` 内ローカルリスト蓄積）
- AST 再帰走査が必要なルール → 責務別クラス orchestrator 型（Collector / Calculator / Detector を `@staticmethod` で実装し、`check()` を薄い orchestrator にする）

## ガードレール

| ルール | 理由 |
|-------|------|
| `check()` と `meta` 以外にパブリックメソッドを持たせない | Rule Protocol の契約を保つ。呼び出し元は `check()` のみで完結する |
| ルール間で直接参照しない（ルール A がルール B を import しない） | ルール間の疎結合を維持し、独立した追加・削除を可能にする |
| 共有ロジックはドメインサービスまたは共有値オブジェクトに切り出す | ルール間の重複は DRY 原則で共通化する。ただし2ルール以上で使う場合に限る（YAGNI） |
| `ast` モジュールの型を Protocol で抽象化しない | Python 標準ライブラリの安定した API であり、隔離は YAGNI |
| テストは `check()` 経由を基本とし、切り出した純粋関数クラスの直接テストも追加する | `check()` の契約がルールの公開インターフェース。純粋関数の単独テストは責務分離の恩恵 |
| 診断メッセージ（message / reason / suggestion）は日本語で統一する | ユーザー向け出力の一貫性 |
| `check()` は例外を raise せず、常に `tuple[Violation, ...]` を返す | `RuleSet` が全ルールを安全に実行できることを保証する |
| `violations` への append は `check()` メソッド内に閉じ込める | 副作用の局所化。純粋関数クラスのスタティックメソッドには `violations` を渡さない |
