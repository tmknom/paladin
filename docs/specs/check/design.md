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
| ファイル除外 | `PathExcluder` | exclude パターンに合致するファイルをパスから除外する |
| AST パーサー | `AstParser` | Python ファイルの読み込みと AST 生成 |
| ルール管理・実行 | `RuleSet` | 全ルールを束ねて管理し、ファイルへの適用と違反集約を担当 |
| ルールフィルター | `RuleFilter` | 設定ファイルの rules セクションに基づいてルールの有効/無効を解決する |
| ファイル ignore ディレクティブ | `FileIgnoreDirective` | 単一ファイルの ignore-file ディレクティブ情報を保持する値オブジェクト |
| ファイル ignore パーサー | `FileIgnoreParser` | ソーステキストのヘッダー領域から ignore-file ディレクティブを抽出する |
| 行単位 ignore ディレクティブ | `LineIgnoreDirective` | 行単位の ignore ディレクティブ情報（対象行番号・ルール ID）を保持する値オブジェクト |
| 行単位 ignore パーサー | `LineIgnoreParser` | ソーステキストの直前コメントから行単位 ignore ディレクティブを抽出する |
| 設定 ignore リゾルバー | `ConfigIgnoreResolver` | 設定ファイルの per-file-ignores パターンを照合して `FileIgnoreDirective` を生成する |
| ignore 統合メソッド | `FileIgnoreDirective.merge` | 設定ファイル由来とコメント由来の `FileIgnoreDirective` を統合する（同一ファイルは `ignore_all` の論理和・`ignored_rules` の集合和） |
| 違反フィルター | `ViolationFilter` | ファイル・行・CLI・設定の各 ignore ディレクティブに基づいて違反を除外する |
| ignore ファサード | `IgnoreProcessor` | ignore ディレクティブの解析・統合・フィルタリングを一括実行するファサード |
| レポートフォーマッター（text） | `CheckReportFormatter` | `CheckResult` を text 形式の `CheckReport` に変換 |
| レポートフォーマッター（JSON） | `CheckJsonFormatter` | `CheckResult` を JSON 形式の `CheckReport` に変換 |
| フォーマッターファクトリー | `CheckFormatterFactory` | `OutputFormat` に応じたフォーマッターへ委譲する |
| 出力形式 | `OutputFormat` | `text` / `json` を表す列挙型 |
| ルール Protocol | `Rule` | ルール実装が満たすべき契約の定義 |
| 実行コンテキスト | `CheckContext` | 実行時パラメータ（解析対象パス群・出力形式・適用ルール限定・ignore 設定・exclude・ルール設定）を保持する値オブジェクト |

### ファイルレイアウト

#### プロダクションコード

```bash
src/paladin/check/
├── __init__.py           # 公開 API の定義
├── context.py            # CheckContext
├── orchestrator.py       # CheckOrchestrator
├── provider.py           # CheckOrchestratorProvider
├── collector.py          # FileCollector / PathExcluder
├── ignore/               # Ignore 機能サブパッケージ
│   ├── __init__.py       # 公開シンボルの re-export
│   ├── directive.py      # FileIgnoreDirective / LineIgnoreDirective
│   ├── filter.py         # ViolationFilter
│   ├── parser.py         # FileIgnoreParser / LineIgnoreParser
│   ├── processor.py      # IgnoreProcessor
│   └── resolver.py       # ConfigIgnoreResolver
├── parser.py             # AstParser
├── rule_filter.py        # RuleFilter
├── formatter.py          # CheckReportFormatter / CheckJsonFormatter / CheckFormatterFactory
├── result.py             # CheckResult / CheckStatus / CheckSummary / CheckReport
└── types.py              # TargetFiles / OutputFormat
```

#### テストコード

```bash
tests/unit/test_check/
├── __init__.py
├── test_collector.py
├── test_context.py
├── test_formatter.py
├── test_ignore/
│   ├── __init__.py
│   ├── test_directive.py
│   ├── test_filter.py
│   ├── test_parser.py
│   ├── test_processor.py
│   └── test_resolver.py
├── test_orchestrator.py
├── test_parser.py
├── test_provider.py
├── test_result.py
├── test_rule_filter.py
└── test_types.py
```

## 処理フロー

### 全体フロー

全体の処理フローは `CheckOrchestrator` が担います。

1. `FileCollector` が `context.targets` から `.py` ファイルを収集する（`TargetFiles`）
2. `PathExcluder` が `context.exclude` パターンを適用し、対象外ファイルを除外する（`TargetFiles`）
3. `AstParser` が各ファイルを読み込み AST とソーステキストを生成する（`SourceFiles`）
4. `RuleFilter` が `context.rules` と `context.select_rules` に基づいて無効ルール ID を解決する（`frozenset[str]`）
5. `RuleSet` が有効ルールを全ファイルへ適用し、違反を集約する（`Violations`）
6. `IgnoreProcessor` が ignore ディレクティブの解析・統合・フィルタリングを一括実行する（`Violations`）
    - `ConfigIgnoreResolver` が `context.per_file_ignores` パターンを照合し、設定由来の `FileIgnoreDirective` を生成する
    - `FileIgnoreParser` がソーステキストのヘッダー領域を走査し、コメント由来の `FileIgnoreDirective` を抽出する
    - 両 `FileIgnoreDirective` を統合する（同一ファイルは `ignore_all` と `ignored_rules` の和集合）
    - `LineIgnoreParser` がソーステキストの直前コメントから `LineIgnoreDirective` を抽出する
    - `ViolationFilter` がファイル・行・CLI の各 ignore 情報に基づいて違反をフィルタリングする
7. `CheckResult`（`TargetFiles` + `SourceFiles` + フィルタリング済み `Violations`）を組み立てる
8. `CheckFormatterFactory` が `CheckContext.format`（`OutputFormat`）に応じて `CheckReportFormatter`（text）または `CheckJsonFormatter`（JSON）へ委譲し、`CheckReport` を生成して返す

### ルール適用ロジック

`RuleSet` は全 `SourceFile` × 全有効 `Rule` のすべての組み合わせに対してルールを適用し、得られた違反をフラットに集約して `Violations` として返します。

## 固有の設計判断

### Rule Protocol によるルール抽象化

**設計の意図**: ルール実装を `Rule` Protocol として定義し、`RuleSet` からルール具象クラスへの直接依存を排除する。

**なぜそう設計したか**: 新しいルールは `Rule` Protocol を満たす実装を追加し、`RuleSet.default()` に登録するだけで有効化される。`RuleSet` や `CheckOrchestrator` の変更は不要である。

**Rule インターフェース**:

```python
class Rule(Protocol):
    @property
    def meta(self) -> RuleMeta: ...
    def check(self, source_file: SourceFile) -> tuple[Violation, ...]: ...
```

**トレードオフ**: Protocol に新しいメソッドを追加した場合、既存の全ルール実装がランタイムエラーになる。これは意図的な設計で、インターフェース違反を早期に発見できる。

### ルール定義の独立パッケージ化

**設計の意図**: ルール定義を `check/rule/` サブパッケージから独立した `rule` パッケージへ切り出し、`check` / `list` / `view` が対等に `rule` へ依存する構造にする。

**なぜそう設計したか**: `check/rule/` を `check` パッケージのサブパッケージとして置くと、`list` / `view` パッケージが `paladin.check.rule.*` へ直接依存することになり、各コマンドを独立した概念として分離した設計意図に反する。ルールドメインを独立パッケージ `rule` として切り出すことで、`check` / `list` / `view` が対等に `rule` に依存する構造が実現できる。

**依存グラフ**:

```
check/ → rule/ (Rule, RuleSet, SourceFile, SourceFiles, Violation, Violations, RuleMeta)
list/  → rule/ (RuleSet, RuleMeta)
view/  → rule/ (RuleSet, RuleMeta)
```

**トレードオフ**: `SourceFile` / `SourceFiles` は rule ドメインの型だが、check 層の ignore 機能（`source` フィールド）でも利用している。rule の関心事でないフィールドを含む点はトレードオフだが、型を分離するより凝集度を優先した。

### フォーマッター群の責務分離

**設計の意図**: `CheckOrchestrator` のパイプライン処理とフォーマットの責務を分離し、`CheckFormatterFactory` が `OutputFormat` に応じて `CheckReportFormatter`（text）または `CheckJsonFormatter`（JSON）へ委譲する。

**なぜそう設計したか**: フォーマット形式は出力先によって異なりうる関心事であり、パイプライン処理とは変更理由が異なる。`CheckFormatterFactory` を DI で注入することで、フォーマット変更を `formatter.py` のみに局所化できる。

**呼び出し場所**: `CheckFormatterFactory` は `CheckOrchestrator.orchestrate()` の末尾で `self.formatter.format(result, context.format)` として呼び出される。CLI 層が直接依存するのは `CheckOrchestratorProvider` のみであり、フォーマッター群は check パッケージ内部の詳細となる。

**トレードオフ**: 新しい出力形式を追加する場合は、`OutputFormat` への値追加・新しいフォーマッタークラスの実装・`CheckFormatterFactory` の `format()` メソッド拡張の3箇所を変更する必要がある。

### SourceFile へのソーステキスト保持

**設計の意図**: `SourceFile` に `source: str` フィールドを追加し、AST と合わせてソーステキストを保持する。

**なぜそう設計したか**: Python の `ast` モジュールはコメントを AST ノードとして保持しない。ignore ディレクティブはコメントであるため、AST からは抽出できない。`AstParser.parse` がソーステキストを既に保持しているため、`SourceFile` にそのまま含めるのが最もシンプルな手段である。ファイル先頭の ignore-file ディレクティブと直前コメントの行単位 ignore ディレクティブのいずれも、同じ `source` フィールドを入力として利用している。

**トレードオフ**: 全 `SourceFile` がソーステキストをメモリ上に保持し続けるため、大量ファイル解析時のメモリ消費が増加する。現時点では対象ファイル数が限定的で問題にならないが、将来パフォーマンスが問題になった場合は遅延読み込みや ignore 解析後のソース破棄を検討する。

### ヘッダー領域のみを走査する ignore パーサー

**設計の意図**: `FileIgnoreParser` は、ファイル先頭から走査しヘッダー領域（空行・shebang・エンコーディング宣言・通常コメント・docstring）をスキップしながら ignore ディレクティブを探す。import 文などの実行コードに到達した時点で走査を打ち切る。

**なぜそう設計したか**: ファイル全体を走査すると、本文中に偶然含まれる `# paladin: ignore-file` 形式の文字列（コメントや文字列リテラル）を誤検出するリスクがある。「ファイル先頭のヘッダー領域のみ有効」という制約により誤検出を防ぎ、ディレクティブの記述位置を明確に規定できる。

**トレードオフ**: ディレクティブを後から追加する場合、import 文の前に移動しなければならない。ただしこれは意図的な制約であり、ignore の影響範囲を明確にするためのものである。

### RuleSet によるルール管理と実行の統合

**設計の意図**: `RuleRunner`（実行）と `RuleRegistry`（メタ情報管理）を `RuleSet` 一つに統合し、ルール群に関するすべての操作（実行・一覧・検索）を一つのクラスに集約する。

**なぜそう設計したか**: 実行と管理は同じルール集合に対する操作であり、分離する理由が乏しかった。単一クラスに集約することで `check` / `list` / `view` の各モジュールが共通の `RuleSet` インスタンスを使用でき、ルール登録の一元化が実現できる。`RuleSetFactory.create()` メソッドがプロダクション用のルール一式を生成するファクトリーを担い、登録ロジックを `rule` パッケージに集約している。

**トレードオフ**: `RuleSet` が実行・一覧・検索の複数の責務を持つが、これらはすべて同一ルール集合に対する操作であり凝集度は高い。新しいルールを追加する際は `RuleSetFactory.create()` の変更が必要になる。

### RuleFilter によるルール有効/無効の解決

**設計の意図**: 設定ファイルの `[tool.paladin.rules]` セクションおよび CLI の `--rule` オプションに基づいてルールを無効化する責務を `RuleFilter` として分離し、`RuleSet.run()` の呼び出し前に無効ルール ID を解決する。

**なぜそう設計したか**: ルール有効/無効の解決ロジック（未知 ID の警告処理を含む）を `RuleSet` や `CheckOrchestrator` から切り出すことで、設定ファイルや CLI オプションの変更に伴うロジック修正を `rule_filter.py` に局所化できる。

**`--rule` と `[tool.paladin.rules]` の AND 条件**: `--rule` は「ポジティブセレクション」として機能し、指定されたルール ID 以外を無効化する。`[tool.paladin.rules]` の `false` 設定はその後に適用されるため、`--rule` で選択されていても `rules: false` なら無効になる。空の `select_rules`（`--rule` 未指定）は全ルール適用を意味し、既存動作と後方互換である。

**トレードオフ**: 未知のルール ID に対する警告は実行時のログ出力のみで、エラーとして停止しない。設定ミスを早期発見しにくい反面、新旧バージョン間でのルール ID の不一致に対しても解析を継続できる。

### PathExcluder によるファイル除外の分離

**設計の意図**: `FileCollector` がすべての `.py` ファイルを列挙した後、`PathExcluder` が exclude パターンを適用して対象外ファイルを除外する二段階構成にする。

**なぜそう設計したか**: 列挙と除外を分離することで、各コンポーネントの責務が明確になり単体テストが容易になる。exclude パターンの正規化ロジック（末尾スラッシュ・単純名のディレクトリ解釈）は `PathExcluder` に集約されている。

**パターン正規化の規則**: 末尾スラッシュ付きのパターンや、拡張子・パス区切り・ワイルドカードを含まない単純名は、ディレクトリとして扱い配下すべてにマッチする `**/<name>/**` 形式へ変換される。

### IgnoreProcessor をパイプラインの独立ステップとして配置

**設計の意図**: ignore フィルタリングを `RuleSet.run` の後・`CheckResult` 生成の前に独立したステップとして挿入する。`IgnoreProcessor` は `CheckOrchestrator` にコンストラクタ注入し、ignore パッケージ内部の詳細（各パーサー・リゾルバー・フィルター）を隠蔽するファサードとして機能する。

**なぜそう設計したか**: `RuleSet` の責務を「全ルールを全ファイルへ適用する」に限定し、ignore の関心事を分離することで、各コンポーネントのテスタビリティと拡張性を維持できる。`IgnoreProcessor`・`ViolationFilter`・`FileIgnoreParser`・`LineIgnoreParser`・`ConfigIgnoreResolver` はすべて純粋計算であり副作用を持たないため、Protocol による抽象化は YAGNI に該当する。`CheckOrchestrator` は ignore パッケージの内部詳細（6クラス）を知る必要がなく、`IgnoreProcessor.apply()` を呼び出すだけでよい。

**ignore の統合ロジック**: コメント由来（`FileIgnoreParser`）と設定ファイル由来（`ConfigIgnoreResolver`）の `FileIgnoreDirective` は `FileIgnoreDirective.merge()` で統合される。同一ファイルに両方が存在する場合は `ignore_all` の論理和・`ignored_rules` の集合和として扱われる。

**トレードオフ**: `IgnoreProcessor` 内部の各パーサー・リゾルバーは `apply()` 内で都度生成している。将来状態を持つ必要が生じた場合はコンストラクタ注入に変更する必要があるが、現時点では状態なしで十分なため直接生成とする。

### テストコード: Fake による副作用の分離

**設計の意図**: テストでは実際のファイルシステムにアクセスせず、`tests/fake/` に定義された Fake（`FakeRule` / `InMemoryFsReader`）を使用する。

**なぜそう設計したか**: ファイルシステムへのアクセスは副作用であり、テストに含めると実行速度の低下・環境依存・テスト間の干渉が生じる。Protocol でファイルシステムと Rule が抽象化されているため、テスト時は Fake に差し替えることで各コンポーネントを副作用なしに検証できる。

**制約**: 新規テストを追加する場合は `tests/fake/` の Fake を使うこと。独自のモックやパッチを使ってファイルシステムをスタブにしてはならない。Fake の実装を変更・拡張する場合も `tests/fake/` に集約する。

## 制約と注意点

### 公開 API の制限

外部（CLI 層等）は `paladin.check` からのみインポートすること。内部コンポーネント（`collector`・`parser`・`orchestrator` 等）を直接インポートしてはならない。`__init__.py` の `__all__` が互換性対象である。

現在の公開 API: `CheckContext`, `CheckOrchestratorProvider`, `CheckReport`, `CheckStatus`, `CheckSummary`, `OutputFormat`, `RuleMeta`, `Violation`, `Violations`

`RuleMeta`・`Violation`・`Violations` は `paladin.rule` からの再エクスポートであり、利用者は `paladin.check` からのみインポートすること。

### ファイル順序の安定性

`FileCollector` は重複排除後にソートを行い、実行ごとに同一の順序でファイルを処理する。この順序の安定性は診断結果の再現性を保証するために重要である。順序変更が必要な場合は `FileCollector.collect()` の実装を変更すること。

### ルール実装の追加手順

新しいルールを追加する際は、次の手順を踏むこと。

1. `rule/` パッケージに `Rule` Protocol を満たすクラスを実装する
2. `rule/__init__.py` の `__all__` にクラス名を追加する
3. `rule/rule_set_factory.py` の `RuleSetFactory.create()` の `rules` タプルに追加する

`RuleSet` や `CheckOrchestrator` の変更は不要である。`RuleSetFactory.create()` を共有しているため、`list` / `view` コマンドにも自動的に反映される。

## 外部依存と拡張性

### 外部システム依存

| 依存先 | 用途 |
|---|---|
| Python 標準ライブラリ `ast` | Python ソースコードの AST 生成・走査 |
| `paladin.rule` | ルールドメイン（`Rule`, `RuleSet`, `SourceFile`, `SourceFiles`, `Violation`, `Violations`, `RuleMeta`） |
| `paladin.config` | プロジェクト設定（`PerFileIgnoreEntry`） |
| `paladin.foundation.fs` | ファイル読み込みの抽象化（`TextFileSystemReaderProtocol`） |
| `paladin.foundation.log` | ログ出力（`@log` デコレーター） |

### 想定される拡張ポイント

- **新しいルールの追加**: `Rule` Protocol を実装したクラスを `rule/` に追加し、`RuleSetFactory.create()` に登録する
- **複数ファイルにまたがるルール**: `Rule.check()` のシグネチャを `SourceFiles` を受け取る形に拡張するか、新しい Protocol を定義する
- **エラーファイルのスキップ**: `AstParser` でエラーを捕捉してスキップし、`CheckResult` に解析失敗情報を追加する

### 拡張時の注意点

- 新しいルールを追加する際は `rule/rule_set_factory.py` の `RuleSetFactory.create()` の変更が必要になる。将来的にルール数が大幅に増えた場合は、設定ファイルや自動検出によるルール登録の仕組みを検討する

## 変更パターン別ガイド

よくある変更ケースと、対応するファイルの道筋を示す。

| 変更内容 | 主な変更対象 | 備考 |
|---|---|---|
| 新しいルールを追加 | `rule/` に新ファイル、`rule/__init__.py`（`__all__`）、`rule/rule_set_factory.py`（`RuleSetFactory.create()`） | `RuleSet` / `CheckOrchestrator` の変更は不要 |
| ルールのチェックロジックを変更 | 対象ルールの `.py` | 他コンポーネントへの影響なし |
| ルール有効/無効ロジックを変更 | `rule_filter.py`（`RuleFilter`） | `CheckOrchestrator` の変更は不要 |
| ファイル ignore の解析ロジックを変更 | `ignore/parser.py`（`FileIgnoreParser`） | `IgnoreProcessor` / `CheckOrchestrator` の変更は不要 |
| 行単位 ignore の解析ロジックを変更 | `ignore/parser.py`（`LineIgnoreParser`） | `IgnoreProcessor` / `CheckOrchestrator` の変更は不要 |
| 設定ファイル ignore のロジックを変更 | `ignore/resolver.py`（`ConfigIgnoreResolver`） | `IgnoreProcessor` / `CheckOrchestrator` の変更は不要 |
| ignore のフィルタリングロジックを変更 | `ignore/filter.py`（`ViolationFilter`） | `IgnoreProcessor` / `CheckOrchestrator` の変更は不要 |
| exclude パターンの正規化ロジックを変更 | `collector.py`（`PathExcluder`） | `FileCollector` / `CheckOrchestrator` の変更は不要 |
| `--rule` の選択ロジックを変更 | `rule_filter.py`（`RuleFilter._resolve_select_disabled`） | `CheckOrchestrator` の変更は不要 |
| 実行時パラメータを追加 | `context.py`（`CheckContext`） | 追加フィールドは呼び出し元（CLI 層）が組み立てて渡す |
| レポート出力形式を変更 | `formatter.py`（`CheckReportFormatter` / `CheckJsonFormatter`） | `CheckOrchestrator` の変更は不要 |
| 新しい出力形式を追加 | `types.py`（`OutputFormat`）、`formatter.py`（新フォーマッタークラス・`CheckFormatterFactory`） | `CheckOrchestrator` の変更は不要 |
| 値オブジェクトにフィールドを追加 | `check/types.py` / `check/result.py` / `rule/types.py` | 参照元のコンポーネントも合わせて更新する |
| 公開 API を追加 | `__init__.py` の `__all__` | 内部コンポーネントの公開は原則行わない |

## 影響範囲

check パッケージを変更した場合、以下の呼び出し元に影響が及ぶ。

| 呼び出し元 | ファイル | 影響する変更 |
|---|---|---|
| CLI の check コマンド | `src/paladin/cli.py` | `CheckContext` のフィールド追加・変更、`CheckOrchestratorProvider` のインターフェース変更 |

## 関連ドキュメント

- [check モジュール要件定義](./requirements.md): check モジュールの機能要件や前提条件
- [Paladin 全体仕様](../../intro/specifications.md): ツール全体の仕様
- [Python アーキテクチャ設計](../../design/architecture.md): プロジェクト共通の設計思想
- [foundation/fs パッケージ基本設計](../foundation/fs/design.md): ファイル読み込み抽象化の設計
- [foundation/log パッケージ基本設計](../foundation/log/design.md): ログ出力の設計
