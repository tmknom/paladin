# list モジュール基本設計

[list モジュール要件定義](./requirements.md) に基づいた基本設計を説明します。

## アーキテクチャパターン

[Python アーキテクチャ設計](../../design/architecture.md) に記載のパターンを採用しています。

| パターン | 適用箇所 | 目的 |
|---|---|---|
| Composition Root + Orchestrator | `ListOrchestratorProvider` / `ListOrchestrator` | 依存関係の組み立てと処理フローの制御を分離する |
| Context | `ListContext` | CLI からの実行時パラメータをカプセル化して Orchestrator に渡す |

## コンポーネント構成

### 主要コンポーネント

| コンポーネント | クラス名 | 役割 |
|---|---|---|
| コンテキスト | `ListContext` | 実行時パラメータの保持 |
| プロバイダー | `ListOrchestratorProvider` | 依存関係の組み立て（Composition Root） |
| オーケストレーター | `ListOrchestrator` | ルール一覧取得とフォーマットの処理フロー制御 |
| テキストフォーマッター | `ListTextFormatter` | `tuple[RuleMeta, ...]` を整列テキストに変換 |
| JSON フォーマッター | `ListJsonFormatter` | `tuple[RuleMeta, ...]` を JSON 形式に変換 |
| フォーマッターファクトリー | `ListFormatterFactory` | `OutputFormat` に応じたフォーマッターを選択 |

### ファイルレイアウト

#### プロダクションコード

```bash
src/paladin/list/
├── __init__.py       # 公開 API の定義
├── context.py        # ListContext
├── formatter.py      # ListTextFormatter / ListJsonFormatter / ListFormatterFactory
├── orchestrator.py   # ListOrchestrator
└── provider.py       # ListOrchestratorProvider
```

#### テストコード

```bash
tests/unit/test_list/
├── __init__.py
├── test_formatter.py
├── test_orchestrator.py
└── test_provider.py
tests/integration/
└── test_integration_list.py
```

## 処理フロー

1. `RuleSet` からルールメタ情報の一覧を取得する
2. `ListFormatterFactory` が出力形式に応じて整形した文字列を返す

## 固有の設計判断

モジュール固有の設計判断はない。プロジェクト共通のアーキテクチャパターンに従っている。

## 制約と注意点

### ルール登録順序への依存

`ListFormatterFactory` が出力するルールの順序は `RuleSet` に登録された順序に依存する。ソートや並び替えの責務は `list` モジュールではなく `RuleSet` 側が持つ。

### 副作用

副作用はない。

## 外部依存

### 外部システムへの依存

外部システムへの依存はない。

### サードパーティライブラリへの依存

サードパーティライブラリへの依存はない。

## 関連ドキュメント

- [list モジュール要件定義](./requirements.md): list モジュールの機能要件や前提条件
- [Python アーキテクチャ設計](../../design/architecture.md): プロジェクト共通の設計思想
