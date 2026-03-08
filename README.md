# template-python

本リポジトリでは、Pythonアプリケーション開発向けのテンプレートを提供します。
AI駆動開発ワークフローを前提に設計されています。

## 概要

本リポジトリでは次のテンプレートを提供しています。

- **リファレンス実装** (`src/example/`) — Onion Architecture と Composition Root + Orchestrator パターンを適用した動作するサンプル実装
- **設計ドキュメント** (`docs/design/`) — アーキテクチャ設計・コーディング規約
- **仕様ドキュメント** (`docs/specs/`) — モジュール別の要件定義と基本設計。AIエージェントへのコンテキスト提供が主目的
- **開発ワークフロー** — すぐに使えるツール設定（ruff, pyright, pytest, uv）

背景と目的の詳細は[プロジェクト概要](docs/intro/overview.md)を参照してください。

## アーキテクチャ

**Onion Architecture** と **Composition Root + Orchestrator パターン**を採用しています。

```
        ┌───────────────────────┐
        │ CLI層                 │ ← 最外殻
        │  ┌─────────────────┐  │
        │  │ ビジネスロジック層│  │ ← 最内殻（中核）
        │  └─────────────────┘  │
        └───────────────────────┘
              ↑ 両層から参照
        ┌───────────────────────┐
        │ protocol              │ ← Shared Kernel（OnionのPort定義）
        └───────────────────────┘
              ↑ foundation も参照（実装のため）
        ┌───────────────────────┐
        │ foundation            │ ← Shared Kernel（横断的共通部品・Adapter実装）
        │（FS・エラー・ログ等）  │
        └───────────────────────┘
```

依存は常に外側から内側へ一方向です。`protocol/` はPort（抽象インターフェース）を定義する Shared Kernel です。`foundation/` はAdapter実装と横断的共通部品を提供する Shared Kernel として、全層から参照されます。

詳細は[アーキテクチャ設計](docs/design/architecture.md)を参照してください。

## はじめに

### Step 1: コンセプトを理解する

以下の順序でオンボーディングドキュメントを読んでください。

| ドキュメント | 内容 |
|-------------|------|
| [プロジェクト概要](docs/intro/overview.md) | テンプレートが提供するものと背景 |
| [設計コンセプト](docs/intro/concept.md) | AI駆動開発のアプローチとアーキテクチャの設計思想 |
| [リポジトリ構造](docs/intro/structure.md) | ファイルレイアウトと各ディレクトリの役割 |
| [用語集](docs/intro/glossary.md) | プロジェクト固有の用語 |

### Step 2: リファレンス実装を確認する

`src/example/transform/` がアーキテクチャパターン全体の規範的な例です。
新しい機能パッケージを追加する際は、ここから始めてください。

詳細なコンポーネント一覧は[リポジトリ構造](docs/intro/structure.md)を参照してください。

### Step 3: 開発ワークフローを実行する

```bash
make all          # format + lint + typecheck + ユニットテスト（CI相当の一括実行）
make test         # 全テスト実行（ユニット + インテグレーション）
make fmt          # ruff でフォーマット
make lint         # ruff で静的解析
make typecheck    # pyright で型チェック
make coverage     # カバレッジ計測
```

## ドキュメント

ドキュメントは3層構造で整理されています。

| 層 | ディレクトリ | 目的 |
|----|------------|------|
| オンボーディング | [`docs/intro/`](docs/intro/README.md) | Why: コンセプト・構造・用語集 |
| 設計 | [`docs/design/`](docs/design/) | What: アーキテクチャ・コーディング規約 |
| 仕様 | [`docs/specs/`](docs/specs/) | How: モジュール別の要件定義・基本設計 |

[`llms.txt`](llms.txt) はAIエージェント向けのドキュメントインデックスです。タスクと関連ドキュメントの対応を示します。

## 動作要件

- Python 3.13+
- [uv](https://docs.astral.sh/uv/)（パッケージマネージャ）
