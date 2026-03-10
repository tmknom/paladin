# check モジュール基本設計

[check モジュール要件定義](./requirements.md) に基づいた基本設計を説明します。

## 設計の目的と背景

### システム構成

check モジュールは「ファイル列挙 → AST 解析 → ルール適用」の3段階パイプラインを実装する。各段階は独立したコンポーネントが担い、Orchestrator がフロー全体を制御する。ルール実装は Protocol によって抽象化されており、ルールの追加が既存コンポーネントに影響を与えない構造になっている。

依存の組み立ては Provider が一元的に担い、外部（CLI 層）は `CheckOrchestratorProvider` と `CheckContext` のみを扱えばよい。

### 設計方針

- 各処理段階を独立したコンポーネントに分離し、単一責務を維持する
- ルール実装を Protocol で抽象化し、新しいルールを追加しやすくする
- エラーは Fail Fast で即座に伝播させ、曖昧な状態での処理継続を防ぐ
- データオブジェクトはすべて不変（`frozen=True`）とし、副作用を排除する
- 依存の組み立てを Provider に集約し、具象クラスへの依存を隠蔽する

## 設計の全体像

### アーキテクチャパターン

- **パイプラインパターン**: ファイル列挙 → AST 解析 → ルール適用の順に処理を連鎖させる
- **Orchestrator パターン**: 処理フロー全体の制御を Orchestrator に集約し、各コンポーネントはフローを知らない
- **Provider パターン（ファクトリー）**: 依存グラフの構築を Provider に集約し、外部から具象クラスを隠蔽する
- **Protocol 抽象化**: ルール実装を Protocol で定義し、Orchestrator・Runner から具象クラスへの依存を排除する
- **値オブジェクト**: 処理中のデータをすべて不変の値オブジェクトとして定義し、状態変化を防ぐ

### 外部システム依存

| 依存先 | 用途 |
|---|---|
| Python 標準ライブラリ `ast` | Python ソースコードの AST 生成・走査 |
| `paladin.foundation.fs` | ファイル読み込みの抽象化（`TextFileSystemReaderProtocol`） |
| `paladin.foundation.log` | ログ出力（`@log` デコレーター） |

### 主要コンポーネント

| コンポーネント | 責務 |
|---|---|
| `CheckOrchestratorProvider` | 依存グラフの組み立て（ファクトリー） |
| `CheckOrchestrator` | 処理フロー全体の制御 |
| `FileCollector` | 解析対象 `.py` ファイルの列挙 |
| `AstParser` | Python ファイルの読み込みと AST 生成 |
| `RuleRunner` | 全ルールを全ファイルへ適用し、違反を集約 |
| `RuleRegistry` | 登録済みルールのメタ情報一覧の管理 |
| `Rule`（Protocol） | ルール実装が満たすべき契約の定義 |
| `RequireAllExportRule` | `__init__.py` への `__all__` 定義を要求するルール実装 |
| `CheckContext` | 実行時パラメータ（解析対象パス群）を保持する値オブジェクト |

### 処理フロー概略

1. `CheckContext` に解析対象パス群を設定する
2. `FileCollector` が `.py` ファイルを再帰的に列挙する
3. `AstParser` が各ファイルの AST を生成する
4. `RuleRunner` が全ルールを全ファイルへ適用し、違反を集約する
5. `CheckResult` として結果を返す

## 重要な設計判断

### Protocol によるルール抽象化

**設計の意図**: `Rule` を Protocol として定義し、`RuleRunner` からルール具象クラスへの直接依存を排除する。

**なぜそう設計したか**: ルール実装が増えるたびに `RuleRunner` を修正すると、ルールの追加コストが高くなる。Protocol 抽象化により、新しいルールは `Rule` Protocol を満たす実装を追加するだけでよく、既存コンポーネントを変更しなくてよい。

**トレードオフ**: Protocol の型チェックはランタイム（`runtime_checkable`）で行われるため、Protocol に新しいメソッドを追加した場合は既存実装が即座にエラーとなる。これは意図的な設計で、インターフェース違反を早期に発見できる。

### Orchestrator による処理フロー集約

**設計の意図**: `CheckOrchestrator` がパイプライン全体のフロー制御を担い、`FileCollector`・`AstParser`・`RuleRunner` はそれぞれの処理のみに集中する。

**なぜそう設計したか**: 各コンポーネントが次のコンポーネントを直接呼び出すと、コンポーネント間の依存が連鎖し、変更が波及しやすくなる。Orchestrator にフロー制御を集約することで、各コンポーネントは独立してテスト・変更できる。

**トレードオフ**: Orchestrator がフロー全体を知っているため、処理ステップの順序変更は Orchestrator の修正で対応できる。一方、フロー変更のたびに Orchestrator を修正する必要がある。

### Provider によるファクトリー集約

**設計の意図**: `CheckOrchestratorProvider` が依存グラフ全体の組み立てを担い、外部（CLI 層）は具象クラスを知らなくてよい状態にする。

**なぜそう設計したか**: Orchestrator が自身の依存を生成すると、依存の差し替えが困難になる。Provider に生成責務を集約することで、将来の依存変更を Provider のみの修正で対応できる。

**トレードオフ**: 現在は Provider が具象クラスを直接組み立てるため、ルール実装の追加は Provider にも変更を加える必要がある。

### データオブジェクトの不変設計

**設計の意図**: `CheckContext`・`TargetFiles`・`ParsedFile`・`ParsedFiles`・`CheckResult`・`Violation`・`Violations`・`RuleMeta` をすべて `frozen=True` の dataclass として定義する。

**なぜそう設計したか**: パイプライン処理では、各ステージがデータを受け取り、次のステージへ渡す。データが不変であることで、あるステージがデータを変更して後続ステージへ影響を与えるリスクを排除できる。

**トレードオフ**: データの更新が必要な場合は新しいインスタンスを生成する必要があるが、check モジュールのパイプライン処理では更新の必要がなく、デメリットが顕在化しない。

### Fail Fast によるエラー伝播

**設計の意図**: 存在しないパス・ファイル読み込みエラー・構文エラーのいずれも、発生時点で即座に例外を送出し、呼び出し元へ伝播させる。

**なぜそう設計したか**: エラーを握りつぶして処理を継続すると、誤った解析結果を正常結果として返すリスクがある。生成 AI が診断結果を修正判断に使う用途では、不正確な結果より明確なエラーの方が有益である。

**トレードオフ**: 1ファイルのエラーで全体の処理が停止する。現在の設計ではエラーファイルをスキップして継続する選択をしていない。

### ルール定義の配置場所（check/rule/ vs 独立 rule/ パッケージ）

**設計の意図**: ルール定義を `src/paladin/check/rule/` サブパッケージに配置する。`src/paladin/rule/` として独立パッケージに分離する案も検討したが、現時点では現状維持を選択した。

**なぜそう設計したか**: `docs/intro/interface.md` では `rules` / `explain` コマンドの将来的な実装が想定されており、これらのコマンドがルール定義を参照する際に `check` パッケージ内部に依存することになる。しかし、現時点でルールを参照するのは `check` コマンドのみであり、他コマンドからの参照は発生していない。また `rules` / `explain` コマンドの具体的な設計が未確定で、Runner はルール適用の関心として `check` に残し Protocol・Registry・各ルール実装だけを共有にするなど、分離の粒度についての正確な判断ができない。移動は後からでも低コストで実施可能なため、具体的な要件が確定してから判断する。

**トレードオフ**: `rules` / `explain` コマンドを実装する際に、それらのコマンドが `check` パッケージに依存する形になる可能性がある。その時点でルール定義の分離が必要と判断した場合は、`src/paladin/rule/` への移動を検討する。**再検討のトリガーは `rules` / `explain` コマンドの設計・実装着手時とする。**

## アーキテクチャ概要

### レイヤー構造とファイルレイアウト

```
check モジュール
├── 公開 API 層
│   ├── __init__.py          # CheckContext / CheckOrchestratorProvider / 型を公開
│   └── provider.py          # CheckOrchestratorProvider（ファクトリー）
│
├── オーケストレーション層
│   └── orchestrator.py      # CheckOrchestrator（フロー制御）
│
├── 処理コンポーネント層
│   ├── collector.py         # FileCollector（ファイル列挙）
│   ├── parser.py            # AstParser（AST 生成）
│   └── context.py           # CheckContext（実行時パラメータ）
│
├── ドメインモデル層
│   └── types.py             # 値オブジェクト群（CheckResult / Violation / TargetFiles 等）
│
└── rule サブパッケージ（ルール実装層）
    ├── __init__.py           # Rule / RuleRegistry / RuleRunner / RequireAllExportRule を公開
    ├── protocol.py           # Rule Protocol（ルールのインターフェース定義）
    ├── registry.py           # RuleRegistry（ルールメタ情報の管理）
    ├── runner.py             # RuleRunner（全ルールの適用と違反集約）
    └── require_all_export.py # RequireAllExportRule（具体的なルール実装）
```

### 依存グラフ

```
CheckOrchestratorProvider
├── TextFileSystemReader        （paladin.foundation.fs）
├── AstParser(reader)
├── FileCollector
├── RequireAllExportRule
├── RuleRunner(rules=(RequireAllExportRule,))
└── CheckOrchestrator(collector, parser, runner)
```

### 処理フロー

```
外部呼び出し元（CLI 等）
  │
  ├─ CheckOrchestratorProvider.provide()
  │    └─ CheckOrchestrator を依存込みで生成して返す
  │
  └─ CheckOrchestrator.orchestrate(CheckContext)
       │
       ├─ FileCollector.collect(targets)
       │    ├─ 各パスの存在確認（FileNotFoundError で即停止）
       │    ├─ ファイル指定: .py のみ収集
       │    ├─ ディレクトリ指定: rglob("*.py") で再帰収集
       │    └─ 重複排除・ソート → TargetFiles
       │
       ├─ AstParser.parse_all(TargetFiles)
       │    └─ 各ファイルを順次 parse()
       │         ├─ TextFileSystemReader でソースを読み込む
       │         ├─ ast.parse() で AST を生成
       │         └─ ParsedFile（file_path + tree）を返す
       │    → ParsedFiles
       │
       ├─ RuleRunner.run(ParsedFiles)
       │    └─ 全 ParsedFile × 全 Rule を適用
       │         └─ Rule.check(parsed_file) → tuple[Violation, ...]
       │    → Violations（全違反を集約）
       │
       └─ CheckResult(target_files, parsed_files, violations) を返す
```

### ルール実装のインターフェース

`Rule` Protocol は次の契約を定義する。

```python
class Rule(Protocol):
    @property
    def meta(self) -> RuleMeta: ...
    def check(self, parsed_file: ParsedFile) -> tuple[Violation, ...]: ...
```

新しいルールは `Rule` Protocol を満たす実装クラスを追加し、`CheckOrchestratorProvider` に登録することで有効化される。

## 重要な制約と注意点

### ルール実装の追加手順

新しいルールを追加する際は、次の手順を踏むこと。

1. `rule/` サブパッケージに `Rule` Protocol を満たすクラスを実装する
2. `CheckOrchestratorProvider.provide()` の `rules` タプルに追加する

`RuleRunner` や `CheckOrchestrator` の変更は不要である。

### ファイル順序の安定性

`FileCollector` は重複排除後にソートを行い、実行ごとに同一の順序でファイルを処理する。この順序の安定性は、診断結果の再現性を保証するために重要である。順序変更が必要な場合は `FileCollector.collect()` の実装を変更すること。

### check パッケージの公開 API

外部（CLI 層等）は `paladin.check` からのみインポートすること。内部コンポーネント（`collector`・`parser`・`orchestrator` 等）を直接インポートしてはならない。`__init__.py` の `__all__` が互換性対象である。

## 将来の拡張性

### 想定される拡張ポイント

- **新しいルールの追加**: `Rule` Protocol を実装したクラスを `rule/` に追加し、`CheckOrchestratorProvider` に登録する
- **複数ファイルにまたがるルール**: `Rule.check()` のシグネチャを `ParsedFiles` を受け取る形に拡張するか、新しい Protocol を定義する
- **ルール選択機能**: `RuleRunner` が適用するルールを実行時に絞り込める仕組みを追加する
- **エラーファイルのスキップ**: `AstParser` でエラーを捕捉してスキップし、`CheckResult` に解析失敗情報を追加する

### 拡張時の注意点

- 新しいルールを追加する際、`Provider` が具象クラスを直接参照しているため、`provider.py` の修正も必要になる。将来的にルール数が増えた場合は、設定ファイルや自動検出によるルール登録の仕組みを検討する

## 関連ドキュメント

- [check モジュール要件定義](./requirements.md): check モジュールの機能要件や前提条件
- [Paladin 要件定義](../../intro/requirements.md): ツール全体の要件定義
- [Python アーキテクチャ設計](../../design/architecture.md): プロジェクト共通の設計思想
- [foundation/fs パッケージ基本設計](../foundation/fs/design.md): ファイル読み込み抽象化の設計
- [foundation/log パッケージ基本設計](../foundation/log/design.md): ログ出力の設計
