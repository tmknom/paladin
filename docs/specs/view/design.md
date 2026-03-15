# view モジュール 設計書

[view モジュール 要件定義書](./requirements.md) に基づいた基本設計を説明します。

## 1. 設計の目的と背景

### システム構成

`view` モジュールは `paladin view <RULE_ID>` コマンドに対応するビジネスロジック層です。CLI から指定された RULE_ID に対応するルールの詳細メタ情報を `RuleSet` から検索し、`ViewFormatter` でラベル付きテキスト形式に整形して返します。

外部 I/O は持たず、ルール検索とテキスト整形のみを担う純粋な処理として実装されています。

### 設計方針

- **Composition Root パターン**: `ViewOrchestratorProvider` が依存関係を一箇所で組み立て、CLI 層はプロバイダーのみに依存する
- **責務分離**: 処理フロー制御（`ViewOrchestrator`）とテキスト整形（`ViewFormatter`）を別クラスに分離する
- **lint モジュールへの依存**: ルール定義とルール管理は `lint` パッケージに置き、`view` モジュールは参照するだけにとどめる
- **副作用なし**: ファイル I/O やネットワークアクセスを持たない純粋な処理として実装する

## 2. 設計の全体像

### 2.1 アーキテクチャパターン

- **Composition Root + Orchestrator パターン**: `ViewOrchestratorProvider` が依存関係を組み立て、`ViewOrchestrator` が処理フローを制御する

### 2.2 外部システム依存

| 依存先 | 用途 |
|---|---|
| `paladin.lint.RuleSet` | 登録済みルールの管理と単一ルール検索（`find_rule`） |
| `paladin.lint.RuleMeta` | ルールメタ情報の型定義 |
| `paladin.foundation.log` | ログ出力（`@log` デコレーター） |

### 2.3 主要コンポーネント

| コンポーネント | クラス名 | 役割 |
|---|---|---|
| コンテキスト | `ViewContext` | 実行時パラメータの保持（`rule_id: str`） |
| プロバイダー | `ViewOrchestratorProvider` | 依存関係の組み立て（Composition Root） |
| オーケストレーター | `ViewOrchestrator` | ルール検索とフォーマットの処理フロー制御 |
| フォーマッター | `ViewFormatter` | `RuleMeta` をラベル付き詳細テキストに変換 |

### 2.4 処理フロー概略

1. `ViewOrchestratorProvider.provide()` が `RuleSet`・`ViewFormatter` を組み立てて `ViewOrchestrator` を返す
2. CLI が `ViewContext(rule_id=...)` を組み立て `ViewOrchestrator.orchestrate(context)` を呼び出す
3. `RuleSet.find_rule(rule_id)` でルールを検索する
4. ルールが見つかれば `ViewFormatter.format(rule)` で詳細テキストを返し、見つからなければエラーメッセージを返す

## 3. 重要な設計判断

### 3.1 list / view を別コマンド・別パッケージに分割する

**設計の意図**: 一覧表示（`list`）と詳細表示（`view`）を独立したトップレベルコマンドとして分割する。

**なぜそう設計したか**: `rules --rule <ID>` のような単一コマンドでのオプション分岐は、コマンドの意図が不明確になる。`list` / `view` に分割することで各コマンドの責務が明確になり、それぞれのコンテキストにフィールドを追加しやすくなる。

**トレードオフ**: パッケージ数が増えるが、各パッケージの責務が単純になる。

### 3.2 Formatter の責務分離

**設計の意図**: テキスト整形ロジックを `ViewOrchestrator` から切り出し、`ViewFormatter` として独立させる。

**なぜそう設計したか**: 整形形式（text / JSON 等）は出力先によって異なりうる関心事であり、処理フロー制御とは変更理由が異なる。`check` モジュールの `CheckFormatterFactory` と同様の設計方針で、将来の出力形式追加に備える。

**トレードオフ**: 現状は text 形式のみのためクラス分離の恩恵が小さいが、JSON 形式等が追加された際に変更コストを抑えられる。

### 3.3 存在しないルール ID はエラーメッセージで返す（例外を投げない）

**設計の意図**: 不正な RULE_ID が指定された場合、例外を発生させずにエラーメッセージ文字列を返す。

**なぜそう設計したか**: `paladin view` は対話的なルール確認コマンドであり、タイプミスのような軽微な入力誤りで異常終了するよりも、案内メッセージを表示して終了コード 0 で返す方がユーザー体験が良い。エラーハンドリングを `ViewOrchestrator` 内に閉じることで、CLI 層は返り値をそのまま出力するだけで済む。

**トレードオフ**: プログラム的に「エラーか否か」を判定しにくくなるが、このコマンドはユーザー向け表示のみを目的とするため問題にならない。

### 3.4 RuleSet を lint パッケージに集約する

**設計の意図**: ルール定義（`Rule` Protocol・`RuleSet`・`RuleMeta` 等）は独立した `lint` パッケージに置き、`view` モジュールはそれらを参照するだけにとどめる。

**なぜそう設計したか**: `check` コマンドが適用するルール群と `view` コマンドが詳細表示するルール群は同一である。重複管理を避けるために `lint` パッケージを単一の情報源として利用する。`RuleSet.default()` を呼ぶだけでプロダクション用のルール一式が得られるため、`ViewOrchestratorProvider` での組み立てが簡潔になる。

**トレードオフ**: `check`・`list`・`view` がすべて `lint` に依存する構造になるため、依存グラフの把握が必要になる。

## 4. アーキテクチャ概要

### 4.1 レイヤー構造とファイルレイアウト

```
CLI 層
  cli.py              ← view() コマンド関数
      ↓ provide() → orchestrate(context)
ビジネスロジック層
  view/
    __init__.py       # 公開 API（ViewContext / ViewOrchestrator / ViewOrchestratorProvider）
    context.py        # ViewContext（実行時パラメータ: rule_id）
    provider.py       # ViewOrchestratorProvider（Composition Root）
    orchestrator.py   # ViewOrchestrator（処理フロー制御）
    formatter.py      # ViewFormatter（ラベル付き詳細テキスト生成）
      ↓ find_rule() / format()
lint パッケージ（ルールドメイン）
  lint/
    rule_set.py       # RuleSet（find_rule / list_rules / run）
    types.py          # RuleMeta
    protocol.py       # Rule Protocol
    *.py              # 各ルール実装
```

### 4.2 処理フロー

```
CLI 層
  view(rule_id=...)
    └─ ViewContext(rule_id=rule_id)
         ↓
ViewOrchestratorProvider.provide()
    ├─ RuleSet.default()   ← 登録済みルール一式を生成
    └─ ViewFormatter()
         ↓ ViewOrchestrator を返す
ViewOrchestrator.orchestrate(context)
    ├─ RuleSet.find_rule(context.rule_id)
    │    ├─ [見つかった] ViewFormatter.format(rule) → str（詳細テキスト）
    │    └─ [未発見]    エラーメッセージ → str
         ↓
CLI 層
  typer.echo(text)   ← テキストを標準出力へ表示
```

## 5. 重要な制約と注意点

### 5.1 公開 API の制限

外部（CLI 層等）は `paladin.view` からのみインポートすること。`__init__.py` の `__all__` が互換性対象である。

- 公開 API: `ViewContext`, `ViewOrchestrator`, `ViewOrchestratorProvider`

### 5.2 ルール登録の変更手順

`view` モジュールが表示するルール一覧は `RuleSet.default()` が一元管理している。新しいルールを追加する場合は以下の手順を踏むこと。

1. `lint/` パッケージに `Rule` Protocol を満たすクラスを実装する
2. `lint/__init__.py` の `__all__` にクラス名を追加する
3. `lint/rule_set.py` の `RuleSet.default()` のタプルに追加する

`check`・`list`・`view` はすべて `RuleSet.default()` を共有するため、1 箇所の変更で全コマンドに反映される。

## 6. 将来の拡張性

### 想定される拡張ポイント

- **出力形式の追加（JSON 等）**: `ViewFormatter` を複数実装し、`ViewOrchestratorProvider` で切り替えるか、フォーマット引数を `orchestrate()` に追加する
- **フィルタ・検索機能**: `ViewContext` に追加フィールドを設けることで対応できる

### 拡張時の注意点

- 出力形式を追加した場合、`ViewFormatter` を差し替えるか拡張するかを `provider.py` で制御する
- `ViewOrchestrator.orchestrate()` のシグネチャを変更すると CLI 層の呼び出し箇所も変更が必要になる

## 7. 関連ドキュメント

- [要件定義書](./requirements.md): view モジュールの機能要件や前提条件
- [list モジュール 要件定義書](../list/requirements.md): 一覧表示の要件定義
- [check モジュール基本設計](../check/design.md): check パイプラインの設計
