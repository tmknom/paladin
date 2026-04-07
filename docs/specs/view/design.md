# view モジュール基本設計

[view モジュール要件定義](./requirements.md) に基づいた基本設計を説明します。

## アーキテクチャパターン

[Python アーキテクチャ設計](../../design/architecture.md) に記載のパターンを採用しています。

| パターン | 適用箇所 | 目的 |
|---|---|---|
| Composition Root + Orchestrator | `ViewOrchestratorProvider` / `ViewOrchestrator` | 依存関係の組み立てと処理フローの制御を分離する |
| Context | `ViewContext` | CLI からの実行時パラメータをカプセル化して Orchestrator に渡す |

## コンポーネント構成

### 主要コンポーネント

| コンポーネント | クラス名 | 役割 |
|---|---|---|
| コンテキスト | `ViewContext` | 実行時パラメータの保持 |
| プロバイダー | `ViewOrchestratorProvider` | 依存関係の組み立て（Composition Root） |
| オーケストレーター | `ViewOrchestrator` | ルール検索とフォーマットの処理フロー制御 |
| テキストフォーマッター | `ViewTextFormatter` | `RuleMeta` をラベル付き詳細テキストに変換 |
| JSON フォーマッター | `ViewJsonFormatter` | `RuleMeta` を JSON 形式に変換 |
| フォーマッターファクトリー | `ViewFormatterFactory` | `OutputFormat` に応じたフォーマッターを選択 |

### ファイルレイアウト

#### プロダクションコード

```bash
src/paladin/view/
├── __init__.py       # 公開 API の定義
├── context.py        # ViewContext
├── formatter.py      # ViewTextFormatter / ViewJsonFormatter / ViewFormatterFactory
├── orchestrator.py   # ViewOrchestrator
└── provider.py       # ViewOrchestratorProvider
```

#### テストコード

```bash
tests/unit/test_view/
├── __init__.py
├── test_context.py
├── test_formatter.py
├── test_orchestrator.py
└── test_provider.py
tests/integration/
└── test_integration_view.py
```

## 処理フロー

1. `RuleSet` から指定されたルールを検索する
2. ルールが見つかれば `ViewFormatterFactory` が出力形式に応じて整形する。見つからなければエラーメッセージを返す
3. フォーマッターは必須フィールドを常に出力し、任意フィールドは値が存在する場合のみ出力に含める

## 固有の設計判断

### 存在しないルール ID はエラーメッセージで返す

**設計の意図**: 不正な RULE_ID が指定された場合、例外を発生させずにエラーメッセージ文字列を返す。

**なぜそう設計したか**: `paladin view` は対話的なルール確認コマンドであり、タイプミスのような軽微な入力誤りで異常終了するよりも、案内メッセージを表示して終了コード 0 で返す方がユーザー体験が良い。エラーハンドリングを `ViewOrchestrator` 内に閉じることで、CLI 層は返り値をそのまま出力するだけで済む。

**トレードオフ**: プログラム的に「エラーか否か」を判定しにくくなるが、このコマンドはユーザー向け表示のみを目的とするため問題にならない。

## 制約と注意点

### 副作用

副作用はない。

## 外部依存

### 外部システムへの依存

外部システムへの依存はない。

### サードパーティライブラリへの依存

サードパーティライブラリへの依存はない。

## 関連ドキュメント

- [view モジュール要件定義](./requirements.md): view モジュールの機能要件や前提条件
- [Python アーキテクチャ設計](../../design/architecture.md): プロジェクト共通の設計思想
