# ルール実装設計

`src/paladin/rule/` パッケージにおけるルール実装の設計方針を文書化する。新規ルール追加時・既存ルール改修時に参照する設計指針をまとめる。

## 目的とスコープ

対象: Rule クラスの内部構造パターン、AST 走査の設計方針、純粋関数の切り出し方針、リファクタリング計画

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

## 現状分析

### check() メソッドの3類型

全16ルールの `check()` 実装は以下の3類型に分類できる。

| 類型 | 説明 | 該当ルール | 課題 |
|------|------|-----------|------|
| **A: 早期リターン** | 条件チェック + `()` か `(violation,)` を直接返す | MaxFileLength, NoNonInitAll, RequireAllExport | なし（最もシンプル） |
| **B: ローカルリスト蓄積** | `check()` 内で `violations: list` を宣言し、ループ内で append/extend | NoRelativeImport, NoCrossPackageReexport, NoMockUsage, RequireQualifiedThirdParty, NoThirdPartyImport, NoCrossPackageImport | ヘルパーメソッドの戻り値スタイルが統一されていない |
| **C: 引数伝搬** | `violations` を再帰メソッドに引数として渡し、各メソッドが直接 append | NoDeepNesting, MaxMethodLength, MaxClassLength, NoLocalImport | 副作用が深部まで伝搬し、純粋関数の範囲が不明瞭 |

類型 A はシンプルで問題ない。類型 B・C は機能的には問題ないが、責務の境界が曖昧で、ロジックの局所テストが難しい。

### 純粋関数の切り出し状況

現状、純粋関数をモジュールレベル関数として切り出しているのは5ルールのみである。

| ファイル | 切り出されている関数 | 切り出し形式 |
|---------|---------------------|------------|
| `max_file_length.py` | `calc_file_length()` | モジュールレベル public 関数 |
| `max_class_length.py` | `_calc_class_length()`, `_calc_class_docstring_lines()` | モジュールレベル private 関数 |
| `max_method_length.py` | `_calc_length()`, `_calc_docstring_lines()` | モジュールレベル private 関数 |
| `no_deep_nesting.py` | `_calc_max_depth()` 他7関数 | モジュールレベル private 関数（ただし `nested_funcs` / `nested_classes` の可変リスト引数あり） |
| `no_local_import.py` | `_get_top_level_nodes()`, `_is_type_checking_block()` | モジュールレベル private 関数 |

残り11ルールは判定ロジックがクラスメソッド内に閉じている。理想形では、これらを **クラス + スタティックメソッド** の形式に整理する（後述）。

### ヘルパーメソッドの戻り値スタイル

現状、ヘルパーメソッドの戻り値スタイルが統一されていない。同じルール内で複数のスタイルが混在するケースもある。

| スタイル | 説明 | 問題 |
|---------|------|------|
| void（引数変異） | `violations` を引数で受け取って直接 append | 副作用の範囲が不明瞭 |
| `list[Violation]` を返す | 結果を新しいリストで返し、呼び出し元が extend | 毎回リスト生成が発生する |
| `Violation \| None` を返す | 違反があれば Violation, なければ None を返す | 最も純粋だが、現状は一部ルールのみで採用 |

### 中間データ構造の使用状況

現状、ルール間で共有される専用の中間値オブジェクトは `AllExports`（`all_exports_extractor.py`）のみである。他はすべて `dict[str, str]` や `set[str]` などのプリミティブコレクションで中間状態を表現している。`import_statement.py` の値オブジェクト群（`ModulePath`, `ImportStatement` 等）は複数ルールで共有されている。

## 理想形の設計

### 責務の分離モデル

AST 走査を伴うルールには4つの独立した責務がある。これらを分離することで、純粋関数化・テスタビリティ向上・変更容易性向上が実現できる。

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

`no_deep_nesting` を例にした理想形のイメージ:

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

### 可変状態と副作用の分離

- `violations` への append は `check()` メソッド内に閉じ込める。ヘルパーメソッドに `violations` を引数として渡して変異させるパターン（類型C）は **採用しない**
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

## リファクタリング計画

### 方針

- 既存の `check()` 経由テストはリファクタリング中の安全ネットとして **維持する**
- 純粋関数クラスを切り出した後、スタティックメソッドを直接テストするケースを追加する
- 全ルールを一度にリファクタリングしない。**変更が必要になったルールから漸進的に揃える**
- 新規ルール追加は最初から理想形パターンで実装する

### 優先度

| 優先度 | 対象ルール | 理由 |
|--------|-----------|------|
| 高 | `no_deep_nesting` | 最も複雑な類型C。純粋関数が多数あるが `nested_funcs` / `nested_classes` の可変リスト引数が混入しており、責務分離のモデルケースとして整理価値が高い |
| 高 | `max_method_length`, `max_class_length` | 類型C の引数伝搬パターン。`_visit_module` / `_visit_class` / `_check_function` の3層が `violations` を受け渡している |
| 中 | `no_local_import` | 類型C。`_visit` / `_visit_class` / `_visit_function` / `_collect_in_body` の4層が `violations` を引数で受け渡している |
| 低 | インポート系ルール（類型B） | 既にフラットなループで violations を蓄積するシンプルな構造。機能的に問題ない |

### 具体的なリファクタリングステップ（no_deep_nesting を例に）

**Before（現状）**:

```
NoDeepNestingRule.check()
    → _visit_module(violations=[], ...)  # violations を引数で渡す
        → _check_function(violations, ...)  # violations に直接 append
            → _calc_max_depth(nested_funcs=[], ...)  # ネスト関数も可変リストで収集
```

**After（理想形）**:

```
NoDeepNestingRule.check()
    → FunctionCollector.collect(tree)  # → tuple[FunctionScope, ...]（副作用なし）
    → for scope in scopes:
        → NestingCalculator.calc_max_depth(scope.node.body)  # → int（副作用なし）
        → NestingDetector.detect(scope, depth, threshold, meta, source_file)  # → Violation | None
    → tuple(violations)  # violations の蓄積は check() 内に閉じ込める
```

**ステップ**:

1. `FunctionCollector` クラスを定義し、`collect()` スタティックメソッドを実装する（`nested_funcs` の可変リスト引数をなくし、再帰結果を tuple で返す）
2. `NestingCalculator` クラスを定義し、ネスト深度計算の純粋関数群をスタティックメソッドとして移行する
3. `NestingDetector` クラスを定義し、`detect()` スタティックメソッドを実装する（判定 + Violation 生成を一か所に集約）
4. `NoDeepNestingRule.check()` を上記3クラスを呼ぶ薄い orchestrator に書き直す
5. 各クラスの直接テストを追加し、`check()` 経由テストも維持されることを確認する

## 新規ルール追加ガイド

### 追加手順

1. ルール仕様を `docs/rules/<rule-id>.md` に作成する
2. 下表を参照して Protocol の組み合わせを選択する
3. `src/paladin/rule/<rule_id_snake>.py` にルールクラスを実装する（理想形パターンに従う）
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

新規ルールは **理想形パターン** に従い実装する。

- AST 走査が不要なシンプルなルールは類型 A（早期リターン + 直接タプル返却）
- インポート文リストのフラットな走査は類型 B（`check()` 内ローカルリスト蓄積）
- AST 再帰走査が必要なルールは責務別クラス（`FunctionCollector` 等）をスタティックメソッドで実装し、`check()` を薄い orchestrator にする

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
