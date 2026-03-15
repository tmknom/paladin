# list / view モジュール基本設計

[list / view モジュール要件定義](./requirements.md) に基づいた基本設計を説明します。

## 設計の目的と背景

### システム構成

- **list モジュール**: `list` コマンドに対応するビジネスロジック層。CLI から呼び出されると、登録済みルールのメタ情報一覧を `RuleRegistry` から取得し、`ListFormatter` でテキスト形式に整形して返す
- **view モジュール**: `view` コマンドに対応するビジネスロジック層。CLI から指定された `rule_id` に対応するルールの詳細を `RuleRegistry` から取得し、`ViewFormatter` でテキスト形式に整形して返す

両モジュールとも外部 I/O は持たず、純粋な取得・整形処理のみを担う。

### 設計方針

- **Composition Root パターン**: `ListOrchestratorProvider` / `ViewOrchestratorProvider` が依存関係を一箇所で組み立て、CLI 層はプロバイダーのみに依存する
- **責務分離**: 処理フロー制御（Orchestrator）とテキスト整形（Formatter）を別クラスに分離する
- **lint モジュールへの依存**: ルール定義とレジストリは `lint` パッケージに置き、list / view モジュールは参照するだけにとどめる
- **副作用なし**: ファイル I/O やネットワークアクセスを持たない純粋な処理として実装する

## 設計の全体像

### アーキテクチャパターン

[Python アーキテクチャ設計](../../design/architecture.md) に記載のパターンを採用しています。

- **Composition Root + Orchestrator パターン**: `ListOrchestratorProvider` / `ViewOrchestratorProvider` が依存関係を組み立て、`ListOrchestrator` / `ViewOrchestrator` が処理フローを制御する

### 外部システム依存

| 依存先 | 用途 |
|---|---|
| `paladin.lint.RuleRegistry` | 登録済みルールのメタ情報一覧の管理・単一ルール検索 |
| `paladin.lint.Rule` | ルール実装が満たすべき契約の参照 |
| `paladin.lint.RuleMeta` | ルールメタ情報の型定義 |
| `paladin.lint` （具象ルール群） | `RequireAllExportRule` / `NoRelativeImportRule` / `NoLocalImportRule` / `RequireQualifiedThirdPartyRule` |
| `paladin.foundation.log` | ログ出力（`@log` デコレーター） |

### 主要コンポーネント（list モジュール）

| コンポーネント | クラス名 | 役割 |
|---|---|---|
| コンテキスト | `ListContext` | 実行時パラメータの保持（現時点ではフィールドなし） |
| プロバイダー | `ListOrchestratorProvider` | 依存関係の組み立て（Composition Root） |
| オーケストレーター | `ListOrchestrator` | ルール一覧取得とフォーマットの処理フロー制御 |
| フォーマッター | `ListFormatter` | `tuple[RuleMeta, ...]` をテキスト形式の文字列に変換 |

### 主要コンポーネント（view モジュール）

| コンポーネント | クラス名 | 役割 |
|---|---|---|
| コンテキスト | `ViewContext` | 実行時パラメータの保持（`rule_id: str`） |
| プロバイダー | `ViewOrchestratorProvider` | 依存関係の組み立て（Composition Root） |
| オーケストレーター | `ViewOrchestrator` | ルール詳細取得とフォーマットの処理フロー制御 |
| フォーマッター | `ViewFormatter` | `RuleMeta` をラベル付き詳細テキストに変換 |

### 処理フロー概略

**list コマンド**

1. `ListOrchestratorProvider.provide()` が `RuleRegistry`・`ListFormatter` を組み立てて `ListOrchestrator` を返す
2. CLI が `ListContext` を組み立て `ListOrchestrator.orchestrate(context)` を呼び出す
3. `RuleRegistry.list_rules()` → `ListFormatter.format()` で一覧テキストを返す

**view コマンド**

1. `ViewOrchestratorProvider.provide()` が `RuleRegistry`・`ViewFormatter` を組み立てて `ViewOrchestrator` を返す
2. CLI が `ViewContext(rule_id=...)` を組み立て `ViewOrchestrator.orchestrate(context)` を呼び出す
3. `RuleRegistry.find_rule()` → 存在すれば `ViewFormatter.format()` で詳細テキストを返す、存在しなければエラーメッセージを返す

## 重要な設計判断

### list / view を別コマンド・別パッケージに分割する

**設計の意図**: 一覧表示（`list`）と詳細表示（`view`）を独立したトップレベルコマンドとして分割する。

**なぜそう設計したか**: `rules --rule <ID>` のような単一コマンドでのオプション分岐は、コマンドの意図が不明確になる。`list` / `view` に分割することで各コマンドの責務が明確になり、それぞれのコンテキストにフィールドを追加しやすくなる。

**トレードオフ**: パッケージ数が増えるが、各パッケージの責務が単純になる。

### Formatter の責務分離

**設計の意図**: テキスト整形ロジックを Orchestrator から切り出し、Formatter として独立させる。

**なぜそう設計したか**: 整形形式（text / JSON 等）は出力先によって異なりうる関心事であり、処理フロー制御とは変更理由が異なる。check モジュールの `CheckReportFormatter` と同様の設計方針である。

**トレードオフ**: 現状は text 形式のみのためクラス分離の恩恵が小さいが、JSON 形式等が追加された際に変更コストを抑えられる。

### lint パッケージのルール定義を利用する

**設計の意図**: ルール定義（`Rule` Protocol・`RuleRegistry`・`RuleMeta` 等）は独立した `lint` パッケージに置き、list / view モジュールはそれらを参照するだけにとどめる。

**なぜそう設計したか**: `check` コマンドが適用するルール群と `list` コマンドが一覧表示するルール群は同一である。重複管理を避けるために、ルール定義の単一の情報源として `lint` パッケージを利用する。

**トレードオフ**: `check`・`list`・`view` がどちらも `lint` に依存する構造になるため、全体の依存グラフの把握が必要になる。

## アーキテクチャ概要

### レイヤー構造とファイルレイアウト

```
CLI層
  cli.py          ← list_rules() / view() コマンド関数
      ↓ provide() → orchestrate(context)
ビジネスロジック層
  list/
    __init__.py              # 公開 API（ListContext / ListOrchestrator / ListOrchestratorProvider）
    context.py               # ListContext（実行時パラメータ）
    provider.py              # ListOrchestratorProvider（Composition Root）
    orchestrator.py          # ListOrchestrator
    formatter.py             # ListFormatter（一覧表示）
  view/
    __init__.py              # 公開 API（ViewContext / ViewOrchestrator / ViewOrchestratorProvider）
    context.py               # ViewContext（実行時パラメータ）
    provider.py              # ViewOrchestratorProvider（Composition Root）
    orchestrator.py          # ViewOrchestrator
    formatter.py             # ViewFormatter（詳細表示）
      ↓ list_rules() / find_rule() / format()
lint パッケージ（ルールドメイン）
  lint/
    registry.py              # RuleRegistry（list_rules / find_rule）
    types.py                 # RuleMeta
    protocol.py              # Rule Protocol
    require_all_export.py    # RequireAllExportRule
    no_relative_import.py    # NoRelativeImportRule
    no_local_import.py       # NoLocalImportRule
    require_qualified_third_party.py  # RequireQualifiedThirdPartyRule
```

### 処理フロー

```
CLI層
  list_rules()
    ├─ ListContext()
      ↓
ListOrchestratorProvider.provide()
    ├─ RuleRegistry(rules=(...4つのルール...))
    └─ ListFormatter()
      ↓ ListOrchestrator を返す
ListOrchestrator.orchestrate(context)
    └─ RuleRegistry.list_rules() → ListFormatter.format() → str（一覧）
      ↓
CLI層
  typer.echo(text)  ← テキストを標準出力へ表示

---

CLI層
  view(rule_id=...)
    ├─ ViewContext(rule_id=rule_id)
      ↓
ViewOrchestratorProvider.provide()
    ├─ RuleRegistry(rules=(...4つのルール...))
    └─ ViewFormatter()
      ↓ ViewOrchestrator を返す
ViewOrchestrator.orchestrate(context)
    ├─ [見つかった] RuleRegistry.find_rule() → ViewFormatter.format() → str（詳細）
    └─ [未発見] エラーメッセージ → str
      ↓
CLI層
  typer.echo(text)  ← テキストを標準出力へ表示
```

## 重要な制約と注意点

### 公開 API の制限

外部（CLI 層等）は `paladin.list` / `paladin.view` からのみインポートすること。各 `__init__.py` の `__all__` が互換性対象である。

- `paladin.list` の公開 API: `ListContext`, `ListOrchestrator`, `ListOrchestratorProvider`
- `paladin.view` の公開 API: `ViewContext`, `ViewOrchestrator`, `ViewOrchestratorProvider`

### ルール登録の変更手順

list / view モジュールが表示するルール一覧は、`ListOrchestratorProvider._create_rules()` と `ViewOrchestratorProvider._create_rules()` のタプルで管理されている。新しいルールを追加する場合は、以下の手順を踏むこと。

1. `lint/` パッケージに `Rule` Protocol を満たすクラスを実装する
2. `lint/__init__.py` の `__all__` にクラス名を追加する
3. `ListOrchestratorProvider._create_rules()` のタプルに追加する
4. `ViewOrchestratorProvider._create_rules()` のタプルに追加する
5. `check` の `CheckOrchestratorProvider._create_runner()` にも同様に追加する

`check`・`list`・`view` コマンドの3箇所の Provider 変更が必要である。

## 将来の拡張性

### 想定される拡張ポイント

- **出力形式の追加（JSON 等）**: `ListFormatter` / `ViewFormatter` を複数実装し、`*OrchestratorProvider` で切り替えるか、フォーマット引数を `orchestrate()` に追加する
- **ルール絞り込み機能**: `ListContext` にフィルタ条件を追加する
- **ルール定義の拡充**: `lint` パッケージへ新しいルールを追加する

### 拡張時の注意点

- 出力形式を追加した場合、`ListFormatter` / `ViewFormatter` を差し替えるか拡張するかを各 `provider.py` で制御する
- `check`・`list`・`view` コマンドで登録ルールの乖離が生じないよう、ルール追加時は3箇所の Provider を更新すること

## 変更パターン別ガイド

| 変更内容 | 主な変更対象 | 備考 |
|---|---|---|
| 新しいルールを追加 | `lint/` に新ファイル、`lint/__init__.py`（`__all__`）、`list/provider.py`・`view/provider.py`・`check` の `CheckOrchestratorProvider` も変更 | 3箇所の Provider 変更が必要 |
| 一覧のテキスト整形ロジックを変更 | `list/formatter.py`（`ListFormatter`） | `ListOrchestrator` の変更は不要 |
| 詳細のテキスト整形ロジックを変更 | `view/formatter.py`（`ViewFormatter`） | `ViewOrchestrator` の変更は不要 |
| 出力形式（JSON 等）を追加 | 新 formatter ファイル、`provider.py` | `orchestrate()` のシグネチャ変更が必要になる場合あり |
| 公開 API を追加 | `__init__.py` の `__all__` | 内部コンポーネントの公開は原則行わない |

## 影響範囲

list / view パッケージを変更した場合、以下の呼び出し元に影響が及ぶ。

| 呼び出し元 | ファイル | 影響する変更 |
|---|---|---|
| CLI の list コマンド | `src/paladin/cli.py` | `ListOrchestratorProvider` のインターフェース変更、`ListOrchestrator.orchestrate()` のシグネチャ変更 |
| CLI の view コマンド | `src/paladin/cli.py` | `ViewOrchestratorProvider` のインターフェース変更、`ViewOrchestrator.orchestrate()` のシグネチャ変更 |

## 関連ドキュメント

- [list / view モジュール要件定義](./requirements.md): list / view モジュールの機能要件や前提条件
- [check モジュール基本設計](../check/design.md): check パイプラインの設計
- [Paladin 全体仕様](../../intro/specifications.md): ツール全体の仕様
- [Python アーキテクチャ設計](../../design/architecture.md): プロジェクト共通の設計思想
- [foundation/log パッケージ基本設計](../foundation/log/design.md): ログ出力の設計
