# プロジェクト構造

## リポジトリ直下

```
.
├── docs/          # ドキュメント（設計・仕様・イントロダクション）
├── src/           # Python ソースコード
├── tests/         # Python テストコード
├── CLAUDE.md      # Claude Code プロジェクトメモリ
├── llms.txt       # ドキュメントインデックス（AI エージェント向け）
├── Makefile       # 開発タスク定義
├── pyproject.toml # Python プロジェクト設定
├── README.md      # リポジトリ説明
└── uv.lock        # 依存関係ロックファイル
```

## src/

ソースコードのリファレンス実装。`example/` パッケージがメインパッケージとして機能する。

```
src/
└── example/                      # メインパッケージ（リファレンス実装）
    ├── cli.py                    # CLI エントリポイント（Typer ベース）
    ├── config/                   # 設定パッケージ
    │   ├── app.py                # AppConfig（設定の統合）
    │   ├── env_var.py            # EnvVarConfig（環境変数ロード）
    │   └── path.py               # PathConfig（パス構築）
    ├── foundation/               # 基盤パッケージ（Shared Kernel・横断的共通部品）
    │   ├── error/                # エラーハンドリング
    │   ├── fs/                   # ファイルシステム抽象化
    │   ├── log/                  # ロギング
    │   └── model/                # 基底モデル
    └── transform/                # Transform 機能パッケージ（アーキテクチャパターンの雛形）
        ├── context.py            # TransformContext（実行コンテキスト）
        ├── orchestrator.py       # Orchestrator（処理フロー制御）
        ├── provider.py           # OrchestratorProvider（Composition Root）
        ├── reader.py             # Reader（テキストファイル読み込み）
        ├── transformer.py        # Transformer（行番号付与・ヘッダー挿入）
        ├── types.py              # SrcText / DstText / Result 型定義
        └── writer.py             # Writer（テキストファイル書き出し）
```

## tests/

テストコードのリファレンス実装。`src/example/` の各パッケージに対応したテストを備える。

```
tests/
├── conftest.py                   # pytest 共通設定・フィクスチャ
├── unit/                         # ユニットテスト
│   ├── test_config/              # config パッケージのテスト
│   │   ├── test_app.py
│   │   ├── test_env_var.py
│   │   └── test_path.py
│   ├── test_foundation/          # foundation パッケージのテスト
│   │   ├── test_error/
│   │   ├── test_fs/
│   │   ├── test_log/
│   │   └── test_model/
│   └── test_transform/           # transform パッケージのテスト
│       ├── fakes.py              # テスト用 Fake 実装
│       ├── test_context.py
│       ├── test_orchestrator.py
│       ├── test_provider.py
│       ├── test_reader.py
│       ├── test_transformer.py
│       ├── test_types.py
│       └── test_writer.py
└── integration/                  # 統合テスト
    └── test_integration_cli.py   # CLI 統合テスト
```

## docs/

ドキュメントのリファレンス実装。設計・仕様・イントロダクションの3カテゴリで構成される。

```
docs/
├── design/                       # 設計ドキュメント
│   ├── architecture.md           # レイヤードアーキテクチャ・設計パターン
│   ├── pyproject.md              # pyproject.toml 設定の根拠
│   ├── specs.md                  # specs/ ドキュメントの設計方針
│   └── workflow.md               # 技術スタック・開発コマンド・開発規律・開発フロー
├── intro/                        # イントロダクション（オンボーディング用）
│   ├── README.md                 # ドキュメント索引・推奨読書順序
│   ├── concept.md                # 設計コンセプト
│   ├── glossary.md               # 用語集
│   ├── overview.md               # テンプレート概要
│   └── structure.md              # プロジェクト構造（本ドキュメント）
└── specs/                        # モジュール別仕様書
    ├── cli/                      # CLI モジュール仕様
    ├── config/                   # config パッケージ仕様
    ├── foundation/               # foundation パッケージ仕様
    │   ├── error/                # エラーハンドリング仕様
    │   ├── fs/                   # ファイルシステム仕様
    │   ├── log/                  # ロギング仕様
    │   └── model/                # 基底モデル仕様
    └── transform/                # transform パッケージ仕様
        ├── design.md             # 基本設計書
        └── requirements.md       # 要件定義書
```

## 主要な設定ファイル

| ファイル | 役割 |
| --- | --- |
| `CLAUDE.md` | Claude Code のプロジェクトメモリ。Plan Mode の制約や AI エージェント向けの行動規範を定義する |
| `llms.txt` | ドキュメントインデックス。AI エージェントがタスクに関連するドキュメントを素早く発見するためのナビゲーションガイド |
| `Makefile` | 開発タスクの定義。`sync`・`fmt`・`lint`・`typecheck`・`test-unit`・`coverage` 等のコマンドを提供する |
| `pyproject.toml` | Python プロジェクト設定。ビルドシステム・依存関係・ruff（リンター/フォーマッター）・pyright（型チェッカー）の設定を一元管理する |
