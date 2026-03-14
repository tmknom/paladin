# rules モジュール基本設計

[rules モジュール要件定義](./requirements.md) に基づいた基本設計を説明します。

## 設計の目的と背景

### システム構成

rules モジュールは `rules` コマンドに対応するビジネスロジック層である。CLI から呼び出されると、登録済みルールのメタ情報一覧を `RuleRegistry` から取得し、`RulesFormatter` でテキスト形式に整形して返す。外部 I/O は持たず、純粋な取得・整形処理のみを担う。

### 設計方針

- **Composition Root パターン**: `RulesOrchestratorProvider` が依存関係を一箇所で組み立て、CLI 層はプロバイダーのみに依存する
- **責務分離**: 処理フロー制御（`RulesOrchestrator`）とテキスト整形（`RulesFormatter`）を別クラスに分離する
- **lint モジュールへの依存**: ルール定義とレジストリは `lint` パッケージに置き、rules モジュールは参照するだけにとどめる
- **副作用なし**: ファイル I/O やネットワークアクセスを持たない純粋な処理として実装する

## 設計の全体像

### アーキテクチャパターン

[Python アーキテクチャ設計](../../design/architecture.md) に記載のパターンを採用しています。

- **Composition Root + Orchestrator パターン**: `RulesOrchestratorProvider` が依存関係を組み立て、`RulesOrchestrator` が処理フローを制御する

### 外部システム依存

| 依存先 | 用途 |
|---|---|
| `paladin.lint.RuleRegistry` | 登録済みルールのメタ情報一覧の管理・単一ルール検索 |
| `paladin.lint.Rule` | ルール実装が満たすべき契約の参照 |
| `paladin.lint.RuleMeta` | ルールメタ情報の型定義 |
| `paladin.lint` （具象ルール群） | `RequireAllExportRule` / `NoRelativeImportRule` / `NoLocalImportRule` / `RequireQualifiedThirdPartyRule` |
| `paladin.foundation.log` | ログ出力（`@log` デコレーター） |

### 主要コンポーネント

| コンポーネント | クラス名 | 役割 |
|---|---|---|
| コンテキスト | `RulesContext` | 実行時パラメータの保持（`rule_id`） |
| プロバイダー | `RulesOrchestratorProvider` | 依存関係の組み立て（Composition Root） |
| オーケストレーター | `RulesOrchestrator` | ルール一覧・詳細取得とフォーマットの処理フロー制御 |
| フォーマッター | `RulesFormatter` | `tuple[RuleMeta, ...]` をテキスト形式の文字列に変換 |
| 詳細フォーマッター | `RulesDetailFormatter` | `RuleMeta` をラベル付き詳細テキストに変換 |

### 処理フロー概略

1. `RulesOrchestratorProvider.provide()` が `RuleRegistry`・`RulesFormatter`・`RulesDetailFormatter` を組み立てて `RulesOrchestrator` を返す
2. CLI が `RulesContext` を組み立て `RulesOrchestrator.orchestrate(context)` を呼び出す
3. `context.rule_id` が `None` の場合: `RuleRegistry.list_rules()` → `RulesFormatter.format()` で一覧テキストを返す
4. `context.rule_id` が指定されている場合: `RuleRegistry.find_rule()` → 存在すれば `RulesDetailFormatter.format()` で詳細テキストを返す、存在しなければエラーメッセージを返す

## 重要な設計判断

### RulesFormatter の責務分離

**設計の意図**: テキスト整形ロジックを `RulesOrchestrator` から切り出し、`RulesFormatter` として独立させる。

**なぜそう設計したか**: 整形形式（text / JSON 等）は出力先によって異なりうる関心事であり、処理フロー制御とは変更理由が異なる。`RulesFormatter` を分離することで、整形ロジックの変更を `formatter.py` のみに局所化できる。check モジュールの `CheckReportFormatter` と同様の設計方針である。

**トレードオフ**: 現状は text 形式のみのためクラス分離の恩恵が小さいが、JSON 形式等が追加された際に変更コストを抑えられる。

### lint パッケージのルール定義を利用する

**設計の意図**: ルール定義（`Rule` Protocol・`RuleRegistry`・`RuleMeta` 等）は独立した `lint` パッケージに置き、rules モジュールはそれらを参照するだけにとどめる。

**なぜそう設計したか**: `check` コマンドが適用するルール群と `rules` コマンドが一覧表示するルール群は同一である。重複管理を避けるために、ルール定義の単一の情報源として `lint` パッケージを利用する。`check` パッケージのサブパッケージとしてルール定義を置くと、`rules` パッケージが `check` パッケージの内部に依存することになり、`check` と `rules` を別概念として分離した設計意図に反する。

**トレードオフ**: `check` と `rules` がどちらも `lint` に依存する構造になるため、全体の依存グラフの把握が必要になる。

### RulesContext による Context パターン

**設計の意図**: `--rule <RULE_ID>` オプションの導入に伴い、実行時パラメータを `RulesContext` 値オブジェクトで保持する。

**なぜそう設計したか**: `check` コマンドの `CheckContext` と同様のパターンで、CLI 引数を `RulesOrchestrator` へ受け渡す。`rule_id` が `None` のときは一覧表示、指定時は詳細表示とフロー分岐を `orchestrate()` 内で制御する。

**トレードオフ**: `rule_id` が `None` のデフォルト値で後方互換性を維持するため、一覧表示の既存動作は変わらない。

## アーキテクチャ概要

### レイヤー構造とファイルレイアウト

```
CLI層
  cli.py          ← rules() コマンド関数
      ↓ provide() → orchestrate(context)
ビジネスロジック層
  rules/
    __init__.py              # 公開 API（RulesContext / RulesOrchestrator / RulesOrchestratorProvider）
    context.py               # RulesContext（実行時パラメータ）
    provider.py              # RulesOrchestratorProvider（Composition Root）
    orchestrator.py          # RulesOrchestrator
    formatter.py             # RulesFormatter（一覧表示）
    detail_formatter.py      # RulesDetailFormatter（詳細表示）
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
  rules(rule=...)
    ├─ RulesContext(rule_id=rule)
      ↓
RulesOrchestratorProvider.provide()
    ├─ RuleRegistry(rules=(...4つのルール...))
    ├─ RulesFormatter()
    └─ RulesDetailFormatter()
      ↓ RulesOrchestrator を返す
RulesOrchestrator.orchestrate(context)
    ├─ [rule_id=None] RuleRegistry.list_rules() → RulesFormatter.format() → str（一覧）
    └─ [rule_id指定] RuleRegistry.find_rule() → RulesDetailFormatter.format() → str（詳細）
                                               └─ [未発見] エラーメッセージ → str
      ↓
CLI層
  typer.echo(text)  ← テキストを標準出力へ表示
```

## 重要な制約と注意点

### 公開 API の制限

外部（CLI 層等）は `paladin.rules` からのみインポートすること。`__init__.py` の `__all__` が互換性対象である。

現在の公開 API: `RulesContext`, `RulesOrchestrator`, `RulesOrchestratorProvider`

### ルール登録の変更手順

rules モジュールが表示するルール一覧は、`RulesOrchestratorProvider._create_rules()` のタプルで管理されている。新しいルールを追加する場合は、以下の手順を踏むこと。

1. `lint/` パッケージに `Rule` Protocol を満たすクラスを実装する
2. `lint/__init__.py` の `__all__` にクラス名を追加する
3. `RulesOrchestratorProvider._create_rules()` のタプルに追加する
4. `check` の `CheckOrchestratorProvider._create_runner()` にも同様に追加する

`check` コマンドと `rules` コマンドの両方に影響するため、2箇所の Provider 変更が必要である。

## 将来の拡張性

### 想定される拡張ポイント

- **出力形式の追加（JSON 等）**: `RulesFormatter` を複数実装し、`RulesOrchestratorProvider` で切り替えるか、フォーマット引数を `orchestrate()` に追加する
- **ルール絞り込み機能**: `orchestrate()` に Context を導入し、フィルタ条件を渡せるようにする
- **ルール定義の拡充**: `lint` パッケージへ新しいルールを追加する

### 拡張時の注意点

- 出力形式を追加した場合、`RulesFormatter` を差し替えるか拡張するかを `provider.py` で制御する
- `check` コマンドと `rules` コマンドで登録ルールの乖離が生じないよう、ルール追加時は両方の Provider を更新すること

## 変更パターン別ガイド

| 変更内容 | 主な変更対象 | 備考 |
|---|---|---|
| 新しいルールを追加 | `lint/` に新ファイル、`lint/__init__.py`（`__all__`）、`provider.py`（`_create_rules()`）、`check` の `CheckOrchestratorProvider` も同様に変更 | 2箇所の Provider 変更が必要 |
| テキスト整形ロジックを変更 | `formatter.py`（`RulesFormatter`） | `RulesOrchestrator` の変更は不要 |
| 出力形式（JSON 等）を追加 | `formatter.py` または新 formatter ファイル、`provider.py` | orchestrate() のシグネチャ変更が必要になる場合あり |
| 公開 API を追加 | `__init__.py` の `__all__` | 内部コンポーネントの公開は原則行わない |

## 影響範囲

rules パッケージを変更した場合、以下の呼び出し元に影響が及ぶ。

| 呼び出し元 | ファイル | 影響する変更 |
|---|---|---|
| CLI の rules コマンド | `src/paladin/cli.py` | `RulesOrchestratorProvider` のインターフェース変更、`RulesOrchestrator.orchestrate()` のシグネチャ変更 |

## 関連ドキュメント

- [rules モジュール要件定義](./requirements.md): rules モジュールの機能要件や前提条件
- [check モジュール基本設計](../check/design.md): check パイプラインの設計
- [Paladin 要件定義](../../intro/requirements.md): ツール全体の要件定義
- [Python アーキテクチャ設計](../../design/architecture.md): プロジェクト共通の設計思想
- [foundation/log パッケージ基本設計](../foundation/log/design.md): ログ出力の設計
