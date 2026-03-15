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
| ignore ディレクティブ | `FileIgnoreDirective` | 単一ファイルの ignore-file ディレクティブ情報を保持する値オブジェクト |
| ignore パーサー | `FileIgnoreParser` | ソーステキストのヘッダー領域から ignore-file ディレクティブを抽出する |
| 違反フィルター | `ViolationFilter` | `FileIgnoreDirective` に基づいて Violations から ignore 対象の違反を除外する |
| レポートフォーマッター（text） | `CheckReportFormatter` | `CheckResult` を text 形式の `CheckReport` に変換 |
| レポートフォーマッター（JSON） | `CheckJsonFormatter` | `CheckResult` を JSON 形式の `CheckReport` に変換 |
| フォーマッターファクトリー | `CheckFormatterFactory` | `OutputFormat` に応じたフォーマッターへ委譲する |
| 出力形式 | `OutputFormat` | `text` / `json` を表す列挙型 |
| ルール Protocol | `Rule` | ルール実装が満たすべき契約の定義 |
| 全エクスポート要求ルール | `RequireAllExportRule` | `__init__.py` への `__all__` 定義を要求する |
| 相対インポート禁止ルール | `NoRelativeImportRule` | 相対インポートの使用を禁止する |
| ローカルインポート禁止ルール | `NoLocalImportRule` | 関数・クラス・メソッド内の import を禁止する |
| サードパーティ修飾インポート要求ルール | `RequireQualifiedThirdPartyRule` | サードパーティの直接インポートとエイリアスインポートを禁止する |
| 実行コンテキスト | `CheckContext` | 実行時パラメータ（解析対象パス群・出力形式）を保持する値オブジェクト |

### ファイルレイアウト

#### プロダクションコード

```bash
src/paladin/check/
├── __init__.py           # 公開 API の定義
├── context.py            # CheckContext
├── orchestrator.py       # CheckOrchestrator
├── provider.py           # CheckOrchestratorProvider
├── collector.py          # FileCollector
├── ignore.py             # FileIgnoreDirective / FileIgnoreParser / ViolationFilter
├── parser.py             # AstParser
├── formatter.py          # CheckReportFormatter / CheckJsonFormatter / CheckFormatterFactory
├── result.py             # CheckResult / CheckStatus / CheckSummary / CheckReport
└── types.py              # TargetFiles / OutputFormat
```

#### テストコード

```bash
tests/unit/test_check/
├── __init__.py
├── fakes.py              # テスト用 Fake（FakeRule / InMemoryFsReader）
├── test_collector.py
├── test_context.py
├── test_formatter.py
├── test_ignore.py
├── test_orchestrator.py
├── test_parser.py
├── test_provider.py
├── test_result.py
└── test_types.py
```

## 処理フロー

### 全体フロー

全体の処理フローは `CheckOrchestrator` が担います。

1. `FileCollector` が解析対象パス群から `.py` ファイルを収集する（`TargetFiles`）
2. `AstParser` が各ファイルを読み込み AST とソーステキストを生成する（`SourceFiles`）
3. `RuleRunner` が全ルールを全ファイルへ適用し、違反を集約する（`Violations`）
4. `FileIgnoreParser` がソーステキストのヘッダー領域を走査し、ignore ディレクティブを抽出する（`tuple[FileIgnoreDirective, ...]`）
5. `ViolationFilter` が ignore ディレクティブに基づいて違反をフィルタリングする（`Violations`）
6. `CheckResult`（`TargetFiles` + `SourceFiles` + フィルタリング済み `Violations`）を組み立てる
7. `CheckFormatterFactory` が `CheckContext.format`（`OutputFormat`）に応じて `CheckReportFormatter`（text）または `CheckJsonFormatter`（JSON）へ委譲し、`CheckReport` を生成して返す

### ルール適用ロジック

`RuleRunner` は全 `SourceFile` × 全 `Rule` のすべての組み合わせに対してルールを適用し、得られた違反をフラットに集約して `Violations` として返します。

## 固有の設計判断

### Rule Protocol によるルール抽象化

**設計の意図**: ルール実装を `Rule` Protocol として定義し、`RuleRunner` からルール具象クラスへの直接依存を排除する。

**なぜそう設計したか**: 新しいルールは `Rule` Protocol を満たす実装を追加し、`CheckOrchestratorProvider` に登録するだけで有効化される。`RuleRunner` や `CheckOrchestrator` の変更は不要である。

**Rule インターフェース**:

```python
class Rule(Protocol):
    @property
    def meta(self) -> RuleMeta: ...
    def check(self, source_file: SourceFile) -> tuple[Violation, ...]: ...
```

**トレードオフ**: Protocol に新しいメソッドを追加した場合、既存の全ルール実装がランタイムエラーになる。これは意図的な設計で、インターフェース違反を早期に発見できる。

### ルール定義の独立パッケージ化

**設計の意図**: ルール定義を `check/rule/` サブパッケージから独立した `lint` パッケージへ切り出し、`check` と `rules` が対等に `lint` へ依存する構造にする。

**なぜそう設計したか**: `check/rule/` を `check` パッケージのサブパッケージとして置くと、`rules` パッケージが `paladin.check.rule.*` へ直接依存することになり、`check` と `rules` を別概念として分離した設計意図に反する。`rules` コマンドが実装済みとなった現在、ルールドメインを独立パッケージ `lint` として切り出すことで、`check` と `rules` が対等に `lint` に依存する構造が実現できる。

**依存グラフ**:

```
check/ → lint/ (Rule, RuleRunner, SourceFile, SourceFiles, Violation, Violations, RuleMeta)
rules/ → lint/ (Rule, RuleRegistry, RuleMeta, 具象ルール)
```

**トレードオフ**: `SourceFile` / `SourceFiles` は lint ドメインの型だが、check 層の ignore 機能（`source` フィールド）でも利用している。lint の関心事でないフィールドを含む点はトレードオフだが、型を分離するより凝集度を優先した。

### フォーマッター群の責務分離

**設計の意図**: `CheckOrchestrator` のパイプライン処理とフォーマットの責務を分離し、`CheckFormatterFactory` が `OutputFormat` に応じて `CheckReportFormatter`（text）または `CheckJsonFormatter`（JSON）へ委譲する。

**なぜそう設計したか**: フォーマット形式は出力先によって異なりうる関心事であり、パイプライン処理とは変更理由が異なる。`CheckFormatterFactory` を DI で注入することで、フォーマット変更を `formatter.py` のみに局所化できる。

**呼び出し場所**: `CheckFormatterFactory` は `CheckOrchestrator.orchestrate()` の末尾で `self.formatter.format(result, context.format)` として呼び出される。CLI 層が直接依存するのは `CheckOrchestratorProvider` のみであり、フォーマッター群は check パッケージ内部の詳細となる。

**トレードオフ**: 新しい出力形式を追加する場合は、`OutputFormat` への値追加・新しいフォーマッタークラスの実装・`CheckFormatterFactory` の `format()` メソッド拡張の3箇所を変更する必要がある。

### SourceFile へのソーステキスト保持

**設計の意図**: `SourceFile` に `source: str` フィールドを追加し、AST と合わせてソーステキストを保持する。

**なぜそう設計したか**: Python の `ast` モジュールはコメントを AST ノードとして保持しない。ignore ディレクティブはコメントであるため、AST からは抽出できない。`AstParser.parse` がソーステキストを既に保持しているため、`SourceFile` にそのまま含めるのが最もシンプルな手段である。将来の直前コメント ignore（R-081）でも同じ `source` を流用できる。

**トレードオフ**: 全 `SourceFile` がソーステキストをメモリ上に保持し続けるため、大量ファイル解析時のメモリ消費が増加する。現時点では対象ファイル数が限定的で問題にならないが、将来パフォーマンスが問題になった場合は遅延読み込みや ignore 解析後のソース破棄を検討する。

### ヘッダー領域のみを走査する ignore パーサー

**設計の意図**: `FileIgnoreParser` は、ファイル先頭から走査しヘッダー領域（空行・shebang・エンコーディング宣言・通常コメント・docstring）をスキップしながら ignore ディレクティブを探す。import 文などの実行コードに到達した時点で走査を打ち切る。

**なぜそう設計したか**: ファイル全体を走査すると、本文中に偶然含まれる `# paladin: ignore-file` 形式の文字列（コメントや文字列リテラル）を誤検出するリスクがある。「ファイル先頭のヘッダー領域のみ有効」という制約により誤検出を防ぎ、ディレクティブの記述位置を明確に規定できる。

**トレードオフ**: ディレクティブを後から追加する場合、import 文の前に移動しなければならない。ただしこれは意図的な制約であり、ignore の影響範囲を明確にするためのものである。

### ViolationFilter をパイプラインの独立ステップとして配置

**設計の意図**: ignore フィルタリングを `RuleRunner.run` の後・`CheckResult` 生成の前に独立したステップとして挿入する。`ViolationFilter` は `CheckOrchestrator` にコンストラクタ注入し、`FileIgnoreParser` は `orchestrate()` 内で直接生成する。

**なぜそう設計したか**: `RuleRunner` の責務を「全ルールを全ファイルへ適用する」に限定し、ignore の関心事を分離することで、各コンポーネントのテスタビリティと拡張性を維持できる。`ViolationFilter` と `FileIgnoreParser` は純粋計算であり副作用を持たないため、Protocol による抽象化は YAGNI に該当する。

**トレードオフ**: `FileIgnoreParser` を `orchestrate()` 内で都度生成しているため、将来状態を持つ必要が生じた場合はコンストラクタ注入に変更する必要がある。現時点では状態なしで十分なため直接生成とする。

### テストコード: Fake による副作用の分離

**設計の意図**: テストでは実際のファイルシステムにアクセスせず、`fakes.py` に定義された Fake（`FakeRule` / `InMemoryFsReader`）を使用する。

**なぜそう設計したか**: ファイルシステムへのアクセスは副作用であり、テストに含めると実行速度の低下・環境依存・テスト間の干渉が生じる。Protocol でファイルシステムと Rule が抽象化されているため、テスト時は Fake に差し替えることで各コンポーネントを副作用なしに検証できる。

**制約**: 新規テストを追加する場合は `fakes.py` の Fake を使うこと。独自のモックやパッチを使ってファイルシステムをスタブにしてはならない。Fake の実装を変更・拡張する場合も `fakes.py` に集約する。

## 制約と注意点

### 公開 API の制限

外部（CLI 層等）は `paladin.check` からのみインポートすること。内部コンポーネント（`collector`・`parser`・`orchestrator` 等）を直接インポートしてはならない。`__init__.py` の `__all__` が互換性対象である。

現在の公開 API: `CheckContext`, `CheckOrchestratorProvider`, `CheckReport`, `CheckStatus`, `CheckSummary`, `OutputFormat`, `RuleMeta`, `Violation`, `Violations`

### ファイル順序の安定性

`FileCollector` は重複排除後にソートを行い、実行ごとに同一の順序でファイルを処理する。この順序の安定性は診断結果の再現性を保証するために重要である。順序変更が必要な場合は `FileCollector.collect()` の実装を変更すること。

### ルール実装の追加手順

新しいルールを追加する際は、次の手順を踏むこと。

1. `lint/` パッケージに `Rule` Protocol を満たすクラスを実装する
2. `lint/__init__.py` の `__all__` にクラス名を追加する
3. `CheckOrchestratorProvider._create_runner()` の `rules` タプルに追加する
4. `RulesOrchestratorProvider._create_rules()` のタプルにも追加する

`RuleRunner` や `CheckOrchestrator` の変更は不要である。

## 外部依存と拡張性

### 外部システム依存

| 依存先 | 用途 |
|---|---|
| Python 標準ライブラリ `ast` | Python ソースコードの AST 生成・走査 |
| `paladin.lint` | ルールドメイン（`Rule`, `RuleRunner`, `SourceFile`, `SourceFiles`, `Violation`, `Violations`, `RuleMeta`, 具象ルール） |
| `paladin.foundation.fs` | ファイル読み込みの抽象化（`TextFileSystemReaderProtocol`） |
| `paladin.foundation.log` | ログ出力（`@log` デコレーター） |

### 想定される拡張ポイント

- **新しいルールの追加**: `Rule` Protocol を実装したクラスを `lint/` に追加し、`CheckOrchestratorProvider._create_runner()` に登録する
- **複数ファイルにまたがるルール**: `Rule.check()` のシグネチャを `SourceFiles` を受け取る形に拡張するか、新しい Protocol を定義する
- **ルール選択機能**: `RuleRunner` が適用するルールを実行時に絞り込める仕組みを追加する
- **エラーファイルのスキップ**: `AstParser` でエラーを捕捉してスキップし、`CheckResult` に解析失敗情報を追加する
- **直前コメント ignore（R-081）**: `# paladin: ignore[rule-id]` をサポートする。`ignore.py` に `LineIgnoreParser` / `LineIgnoreDirective` を追加し、`SourceFile.source` を入力として利用する
- **CLI --ignore-rule（R-082）**: 実行時に全ファイルへ適用するルール除外を `ViolationFilter` に追加する。`CheckContext` に `ignored_rules` フィールドを追加して受け渡す

### 拡張時の注意点

- 新しいルールを追加する際、`Provider` が具象クラスを直接参照しているため、`provider.py` の修正も必要になる。将来的にルール数が増えた場合は、設定ファイルや自動検出によるルール登録の仕組みを検討する

## 変更パターン別ガイド

よくある変更ケースと、対応するファイルの道筋を示す。

| 変更内容 | 主な変更対象 | 備考 |
|---|---|---|
| 新しいルールを追加 | `lint/` に新ファイル、`lint/__init__.py`（`__all__`）、`provider.py`（`_create_runner()`）、`rules/provider.py`（`_create_rules()`） | `RuleRunner` / `CheckOrchestrator` の変更は不要 |
| ルールのチェックロジックを変更 | 対象ルールの `.py` | 他コンポーネントへの影響なし |
| ignore の解析ロジックを変更 | `ignore.py`（`FileIgnoreParser`） | `ViolationFilter` / `CheckOrchestrator` の変更は不要 |
| ignore のフィルタリングロジックを変更 | `ignore.py`（`ViolationFilter`） | `FileIgnoreParser` / `CheckOrchestrator` の変更は不要 |
| 実行時パラメータを追加 | `context.py`（`CheckContext`） | 追加フィールドは呼び出し元（CLI 層）が組み立てて渡す |
| レポート出力形式を変更 | `formatter.py`（`CheckReportFormatter` / `CheckJsonFormatter`） | `CheckOrchestrator` の変更は不要 |
| 新しい出力形式を追加 | `types.py`（`OutputFormat`）、`formatter.py`（新フォーマッタークラス・`CheckFormatterFactory`） | `CheckOrchestrator` の変更は不要 |
| 値オブジェクトにフィールドを追加 | `check/types.py` / `check/result.py` / `lint/types.py` / `source/types.py` | 参照元のコンポーネントも合わせて更新する |
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
