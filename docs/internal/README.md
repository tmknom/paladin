# 基盤モジュール設計ドキュメント

## 概要

本ディレクトリでは、変更頻度が低い基盤モジュールの設計ドキュメントを管理します。
各ファイルは requirements.md と design.md を統合した単一ファイル形式です。

## ドキュメント一覧

| ファイル | モジュール | 内容 |
|---|---|---|
| [error.md](error.md) | `foundation/error` | アプリケーション例外とエラーハンドラーの設計 |
| [fs.md](fs.md) | `foundation/fs` | ファイルシステム操作 Adapter の設計 |
| [log.md](log.md) | `foundation/log` | ログ設定とトレースデコレータの設計 |
| [model.md](model.md) | `foundation/model` | 共通基底モデルの設計 |
| [protocol.md](protocol.md) | `protocol` | Onion アーキテクチャの Port 定義の設計 |
| [cli.md](cli.md) | `cli` | CLI エントリーポイントの設計 |
