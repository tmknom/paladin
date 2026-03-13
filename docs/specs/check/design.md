# check モジュール基本設計

[check モジュール要件定義](./requirements.md) に基づいた基本設計を説明します。

## アーキテクチャパターン

[Python アーキテクチャ設計](../../design/architecture.md) に記載のパターンを採用しています。

- **パイプラインパターン**: ファイル列挙 → AST 解析 → ルール適用の3段階パイプラインとして処理を構成する

## コンポーネント構成

### 主要コンポーネント

| コンポーネント | クラス名 | 役割 |
|---|---|---|
| プロバイダー | `CheckOrchestratorProvider` | 依存関係の組み立て（Composition Root） |
| オーケストレーター | `CheckOrchestrator` | パイプライン全体の処理フロー制御 |
| ファイル列挙 | `FileCollector` | 解析対象 `.py` ファイルの収集 |
| AST パーサー | `AstParser` | Python ファイルの読み込みと AST 生成 |
| ルール実行器 | `RuleRunner` | 全ルールを全ファイルへ適用し、違反を集約 |
| ルールレジストリ | `RuleRegistry` | 登録済みルールのメタ情報一覧の管理 |
| レポートフォーマッター | `CheckReportFormatter` | `CheckResult` を text 形式の `CheckReport` に変換 |
| ルール Protocol | `Rule` | ルール実装が満たすべき契約の定義 |
| 全エクスポート要求ルール | `RequireAllExportRule` | `__init__.py` への `__all__` 定義を要求する |
| 相対インポート禁止ルール | `NoRelativeImportRule` | 相対インポートの使用を禁止する |
| ローカルインポート禁止ルール | `NoLocalImportRule` | 関数・クラス・メソッド内の import を禁止する |
| サードパーティ修飾インポート要求ルール | `RequireQualifiedThirdPartyRule` | サードパーティの直接インポートとエイリアスインポートを禁止する |
| 実行コンテキスト | `CheckContext` | 実行時パラメータ（解析対象パス群）を保持する値オブジェクト |

### ファイルレイアウト

#### プロダクションコード

```bash
src/paladin/check/
├── __init__.py           # 公開 API の定義
├── context.py            # CheckContext
├── orchestrator.py       # CheckOrchestrator
├── provider.py           # CheckOrchestratorProvider
├── collector.py          # FileCollector
├── parser.py             # AstParser
├── formatter.py          # CheckReportFormatter
├── types.py              # 値オブジェクト群（CheckResult / Violation / CheckReport 等）
└── rule/
    ├── __init__.py                          # rule サブパッケージの公開 API
    ├── protocol.py                          # Rule Protocol
    ├── registry.py                          # RuleRegistry
    ├── runner.py                            # RuleRunner
    ├── require_all_export.py                # RequireAllExportRule
    ├── no_relative_import.py                # NoRelativeImportRule
    ├── no_local_import.py                   # NoLocalImportRule
    └── require_qualified_third_party.py     # RequireQualifiedThirdPartyRule
```

#### テストコード

```bash
tests/unit/test_check/
├── __init__.py
├── fakes.py                    # テスト用 Fake（FakeRule / InMemoryFsReader）
├── test_collector.py
├── test_context.py
├── test_formatter.py
├── test_orchestrator.py
├── test_parser.py
├── test_provider.py
├── test_types.py
└── test_rule/
    ├── __init__.py
    ├── test_protocol.py
    ├── test_registry.py
    ├── test_runner.py
    ├── test_require_all_export.py
    ├── test_no_relative_import.py
    ├── test_no_local_import.py
    └── test_require_qualified_third_party.py
```

## 処理フロー

### 全体フロー

全体の処理フローは `CheckOrchestrator` が担います。

1. `FileCollector` が解析対象パス群から `.py` ファイルを収集する（`TargetFiles`）
2. `AstParser` が各ファイルを読み込み AST を生成する（`ParsedFiles`）
3. `RuleRunner` が全ルールを全ファイルへ適用し、違反を集約する（`Violations`）
4. `CheckResult`（`TargetFiles` + `ParsedFiles` + `Violations`）を組み立てる
5. `CheckReportFormatter` が `CheckResult` を text 形式の `CheckReport` に変換して返す

### ルール適用ロジック

`RuleRunner` は全 `ParsedFile` × 全 `Rule` のすべての組み合わせに対してルールを適用し、得られた違反をフラットに集約して `Violations` として返します。

## 固有の設計判断

### Rule Protocol によるルール抽象化

**設計の意図**: ルール実装を `Rule` Protocol として定義し、`RuleRunner` からルール具象クラスへの直接依存を排除する。

**なぜそう設計したか**: 新しいルールは `Rule` Protocol を満たす実装を追加し、`CheckOrchestratorProvider` に登録するだけで有効化される。`RuleRunner` や `CheckOrchestrator` の変更は不要である。

**Rule インターフェース**:

```python
class Rule(Protocol):
    @property
    def meta(self) -> RuleMeta: ...
    def check(self, parsed_file: ParsedFile) -> tuple[Violation, ...]: ...
```

**トレードオフ**: Protocol に新しいメソッドを追加した場合、既存の全ルール実装がランタイムエラーになる。これは意図的な設計で、インターフェース違反を早期に発見できる。

### ルール定義の配置場所

**設計の意図**: ルール定義を `src/paladin/check/rule/` サブパッケージに配置する。`src/paladin/rule/` として独立パッケージに分離する案も検討したが、現時点では現状維持を選択した。

**なぜそう設計したか**: `docs/intro/interface.md` では `rules` / `explain` コマンドの将来的な実装が想定されており、これらのコマンドがルール定義を参照する際に `check` パッケージ内部に依存することになる。しかし、現時点でルールを参照するのは `check` コマンドのみであり、他コマンドからの参照は発生していない。また `rules` / `explain` コマンドの具体的な設計が未確定で、分離の粒度についての正確な判断ができない。移動は後からでも低コストで実施可能なため、具体的な要件が確定してから判断する。

**トレードオフ**: `rules` / `explain` コマンドを実装する際に、それらのコマンドが `check` パッケージに依存する形になる可能性がある。**再検討のトリガーは `rules` / `explain` コマンドの設計・実装着手時とする。**

### CheckReportFormatter の責務分離

**設計の意図**: `CheckOrchestrator` のパイプライン処理とテキストフォーマットの責務を `CheckReportFormatter` に分離する。

**なぜそう設計したか**: フォーマット形式（text / JSON 等）は出力先によって異なりうる関心事であり、パイプライン処理とは変更理由が異なる。`CheckReportFormatter` を別クラスに分離することで、フォーマット変更を `formatter.py` のみに局所化できる。

**呼び出し場所**: `CheckReportFormatter` は `CheckOrchestrator.orchestrate()` の末尾で呼び出される。CLI 層が直接依存するのは `CheckOrchestratorProvider` のみであり、`CheckReportFormatter` は check パッケージ内部の詳細となる。

**トレードオフ**: `CheckOrchestrator` が `CheckReportFormatter` に依存するため、フォーマット形式の切り替えには `CheckOrchestrator` または `CheckOrchestratorProvider` の変更が必要になる。

### テストコード: Fake による副作用の分離

**設計の意図**: テストでは実際のファイルシステムにアクセスせず、`fakes.py` に定義された Fake（`FakeRule` / `InMemoryFsReader`）を使用する。

**なぜそう設計したか**: ファイルシステムへのアクセスは副作用であり、テストに含めると実行速度の低下・環境依存・テスト間の干渉が生じる。Protocol でファイルシステムと Rule が抽象化されているため、テスト時は Fake に差し替えることで各コンポーネントを副作用なしに検証できる。

**制約**: 新規テストを追加する場合は `fakes.py` の Fake を使うこと。独自のモックやパッチを使ってファイルシステムをスタブにしてはならない。Fake の実装を変更・拡張する場合も `fakes.py` に集約する。

## 制約と注意点

### 公開 API の制限

外部（CLI 層等）は `paladin.check` からのみインポートすること。内部コンポーネント（`collector`・`parser`・`orchestrator` 等）を直接インポートしてはならない。`__init__.py` の `__all__` が互換性対象である。

現在の公開 API: `CheckContext`, `CheckOrchestratorProvider`, `CheckReport`, `CheckStatus`, `CheckSummary`, `RuleMeta`, `Violation`, `Violations`

### ファイル順序の安定性

`FileCollector` は重複排除後にソートを行い、実行ごとに同一の順序でファイルを処理する。この順序の安定性は診断結果の再現性を保証するために重要である。順序変更が必要な場合は `FileCollector.collect()` の実装を変更すること。

### ルール実装の追加手順

新しいルールを追加する際は、次の手順を踏むこと。

1. `rule/` サブパッケージに `Rule` Protocol を満たすクラスを実装する
2. `CheckOrchestratorProvider.provide()` の `rules` タプルに追加する

`RuleRunner` や `CheckOrchestrator` の変更は不要である。

## 外部依存と拡張性

### 外部システム依存

| 依存先 | 用途 |
|---|---|
| Python 標準ライブラリ `ast` | Python ソースコードの AST 生成・走査 |
| Python 標準ライブラリ `sys.stdlib_module_names` | 標準ライブラリモジュール名の判定（`RequireQualifiedThirdPartyRule` が使用） |
| `paladin.foundation.fs` | ファイル読み込みの抽象化（`TextFileSystemReaderProtocol`） |
| `paladin.foundation.log` | ログ出力（`@log` デコレーター） |

### 想定される拡張ポイント

- **新しいルールの追加**: `Rule` Protocol を実装したクラスを `rule/` に追加し、`CheckOrchestratorProvider` に登録する
- **複数ファイルにまたがるルール**: `Rule.check()` のシグネチャを `ParsedFiles` を受け取る形に拡張するか、新しい Protocol を定義する
- **ルール選択機能**: `RuleRunner` が適用するルールを実行時に絞り込める仕組みを追加する
- **エラーファイルのスキップ**: `AstParser` でエラーを捕捉してスキップし、`CheckResult` に解析失敗情報を追加する

### 拡張時の注意点

- 新しいルールを追加する際、`Provider` が具象クラスを直接参照しているため、`provider.py` の修正も必要になる。将来的にルール数が増えた場合は、設定ファイルや自動検出によるルール登録の仕組みを検討する

## 変更パターン別ガイド

よくある変更ケースと、対応するファイルの道筋を示す。

| 変更内容 | 主な変更対象 | 備考 |
|---|---|---|
| 新しいルールを追加 | `rule/` に新ファイル、`provider.py` | `RuleRunner` / `CheckOrchestrator` の変更は不要 |
| ルールのチェックロジックを変更 | 対象ルールの `.py` | 他コンポーネントへの影響なし |
| 実行時パラメータを追加 | `context.py`（`CheckContext`） | 追加フィールドは呼び出し元（CLI 層）が組み立てて渡す |
| レポート出力形式を変更 | `formatter.py`（`CheckReportFormatter`） | `CheckOrchestrator` の変更は不要 |
| 値オブジェクトにフィールドを追加 | `types.py` | 参照元のコンポーネントも合わせて更新する |
| 公開 API を追加 | `__init__.py` の `__all__` | 内部コンポーネントの公開は原則行わない |

## 影響範囲

check パッケージを変更した場合、以下の呼び出し元に影響が及ぶ。

| 呼び出し元 | ファイル | 影響する変更 |
|---|---|---|
| CLI の check コマンド | `src/paladin/cli.py` | `CheckContext` のフィールド追加・変更、`CheckOrchestratorProvider` のインターフェース変更 |

## 関連ドキュメント

- [check モジュール要件定義](./requirements.md): check モジュールの機能要件や前提条件
- [Paladin 要件定義](../../intro/requirements.md): ツール全体の要件定義
- [Python アーキテクチャ設計](../../design/architecture.md): プロジェクト共通の設計思想
- [foundation/fs パッケージ基本設計](../foundation/fs/design.md): ファイル読み込み抽象化の設計
- [foundation/log パッケージ基本設計](../foundation/log/design.md): ログ出力の設計
