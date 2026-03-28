# check モジュール基本設計

[check モジュール要件定義](./requirements.md) に基づいた基本設計を説明します。

## アーキテクチャパターン

[Python アーキテクチャ設計](../../design/architecture.md) に記載のパターンを採用しています。

| パターン | 適用箇所 | 目的 |
|---|---|---|
| Composition Root + Orchestrator | `CheckOrchestratorProvider` / `CheckOrchestrator` | 依存関係の組み立てと処理フローの制御を分離する |
| パイプライン | ファイル列挙 → AST 解析 → ルール適用 | 段階的な処理ステップとして構成し、各ステップの責務を明確にする |
| Context | `CheckContext` | CLI からの実行時パラメータをカプセル化して Orchestrator に渡す |

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
| オーバーライドリゾルバー | `OverrideResolver` | `[[tool.paladin.overrides]]` のパターンを照合し、ファイルごとのルール有効/無効を解決する |
| ignore ファサード | `IgnoreProcessor` | ignore ディレクティブの解析・統合・フィルタリングを一括実行するファサード |
| フォーマッターファクトリー | `CheckFormatterFactory` | `OutputFormat` に応じたフォーマッターへ委譲する |
| 実行コンテキスト | `CheckContext` | 実行時パラメータを保持する値オブジェクト |

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
├── override.py           # OverrideResolver
├── formatter.py          # CheckReportFormatter / CheckJsonFormatter / CheckFormatterFactory
├── result.py             # CheckResult / CheckStatus / CheckSummary / CheckReport
└── types.py              # TargetFiles
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
│   ├── helpers.py
│   ├── test_directive.py
│   ├── test_filter.py
│   ├── test_parser.py
│   ├── test_processor.py
│   └── test_resolver.py
├── test_orchestrator.py
├── test_override.py
├── test_parser.py
├── test_provider.py
├── test_result.py
├── test_rule_filter.py
└── test_types.py
tests/integration/
└── test_integration_check.py
```

## 処理フロー

### 全体フロー

1. `FileCollector` と `PathExcluder` が解析対象の `.py` ファイルを収集・除外する
2. `AstParser` が各ファイルの AST とソーステキストを生成する
3. ルールの有効/無効を解決し、`RuleSet` が有効ルールを全ファイルへ適用する
4. `IgnoreProcessor` が ignore ディレクティブの解析・統合・フィルタリングを一括実行する
5. `CheckFormatterFactory` が出力形式に応じたレポートを生成して返す

## 固有の設計判断

### Rule Protocol を介したルールへの依存

**設計の意図**: check モジュールはルール具象クラスに直接依存せず、`Rule` Protocol を介して `RuleSet` 経由でルールを実行する。

**なぜそう設計したか**: ルールの追加・変更が check モジュールのコード変更を必要としない。check モジュールの責務はパイプライン制御に限定される。

**トレードオフ**: check モジュールはルール実行の詳細（どのルールがどの検査を行うか）を知らないため、特定ルール固有の振る舞いに check 側で対応することはできない。

### ヘッダー領域のみを走査する ignore パーサー

**設計の意図**: `FileIgnoreParser` は、ファイル先頭から走査しヘッダー領域をスキップしながら ignore ディレクティブを探す。import 文などの実行コードに到達した時点で走査を打ち切る。

**なぜそう設計したか**: ファイル全体を走査すると、本文中に偶然含まれる `# paladin: ignore-file` 形式の文字列（コメントや文字列リテラル）を誤検出するリスクがある。「ファイル先頭のヘッダー領域のみ有効」という制約により誤検出を防ぎ、ディレクティブの記述位置を明確に規定できる。

**トレードオフ**: ディレクティブを後から追加する場合、import 文の前に移動しなければならない。ただしこれは意図的な制約であり、ignore の影響範囲を明確にするためのものである。

### IgnoreProcessor をパイプラインの独立ステップとして配置

**設計の意図**: ignore フィルタリングを `RuleSet.run` の後・`CheckResult` 生成の前に独立したステップとして挿入する。`IgnoreProcessor` は `CheckOrchestrator` にコンストラクタ注入し、ignore パッケージの内部処理を隠蔽するファサードとして機能する。

**なぜそう設計したか**: `RuleSet` の責務を「全ルールを全ファイルへ適用する」に限定し、ignore の関心事を分離することで、各コンポーネントのテスタビリティと拡張性を維持できる。ignore パッケージ内部のコンポーネントはすべて純粋計算であり副作用を持たないため、Protocol による抽象化は YAGNI に該当する。なお、ignore ディレクティブはコメントに記述されるため AST からは抽出できず、`SourceFile.source` を入力として利用している。

**トレードオフ**: `IgnoreProcessor` 内部の各コンポーネントは状態を持たないため直接生成としている。将来状態を持つ必要が生じた場合はコンストラクタ注入に変更する必要がある。

### OverrideResolver によるディレクトリ別ルール設定の解決

**設計の意図**: `[[tool.paladin.overrides]]` で定義されたディレクトリ別のルール有効/無効設定を、ファイルパスに対して照合し最終的な rules を返す純粋計算クラスとして実装する。

**なぜそう設計したか**: オーバーライド解決ロジックを `CheckOrchestrator` から分離することで、glob パターン照合と後勝ちマージのロジックを単体テスト可能にする。

**トレードオフ**: オーバーライドが存在する場合、全 `SourceFile` に対してパターン照合を実行するためファイル数に比例したコストがかかる。オーバーライドが未設定の場合は早期リターンで回避している。

## 制約と注意点

### ファイル順序の安定性

`FileCollector` は重複排除後にソートを行い、実行ごとに同一の順序でファイルを処理する。この順序の安定性は診断結果の再現性を保証するために重要である。

### 副作用

- `FileCollector` がファイルシステムを走査してディレクトリ内の `.py` ファイルを列挙する
- `AstParser` が `TextFileSystemReaderProtocol` を介してファイルシステムからソースコードを読み込む

副作用は `TextFileSystemReaderProtocol` で抽象化されており、テスト時は Fake に差し替え可能である。

## 外部依存

### 外部システムへの依存

外部システムへの依存はない。

### サードパーティライブラリへの依存

サードパーティライブラリへの依存はない。

## 関連ドキュメント

- [check モジュール要件定義](./requirements.md): check モジュールの機能要件や前提条件
- [Python アーキテクチャ設計](../../design/architecture.md): プロジェクト共通の設計思想
