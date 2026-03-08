# 仕様ドキュメント

## 概要

本ディレクトリでは、各モジュールの要件定義と設計仕様を提供します。
要件（requirements.md）と設計（design.md）をセットで管理し、実装の意図を明示しています。

## ドキュメント一覧

### Feature

| ファイル | 内容 |
|---------|------|
| [Transform要件定義](transform/requirements.md) | 変換機能の要件定義 |
| [Transform設計](transform/design.md) | テキスト変換の基本設計 |

### Application

| ファイル | 内容 |
|---------|------|
| [CLI要件定義](cli/requirements.md) | CLI機能の要件定義 |
| [CLI設計](cli/design.md) | CLIアーキテクチャ設計 |
| [Config要件定義](config/requirements.md) | 環境設定の要件定義 |
| [Config設計](config/design.md) | 設定構造の基本設計 |
| [Protocol要件定義](protocol/requirements.md) | Protocol定義の要件 |
| [Protocol設計](protocol/design.md) | Port定義の設計 |

### Foundation

| ファイル | 内容 |
|---------|------|
| [Errorパッケージ要件定義](foundation/error/requirements.md) | エラー処理の要件定義 |
| [Errorパッケージ設計](foundation/error/design.md) | エラー処理の基本設計 |
| [Fsパッケージ要件定義](foundation/fs/requirements.md) | ファイルI/O要件定義 |
| [Fsパッケージ設計](foundation/fs/design.md) | ファイルシステムの基本設計 |
| [Logパッケージ要件定義](foundation/log/requirements.md) | ログ機能の要件定義 |
| [Logパッケージ設計](foundation/log/design.md) | ログ設定の基本設計 |
| [Modelパッケージ要件定義](foundation/model/requirements.md) | モデル基盤の要件定義 |
| [Modelパッケージ設計](foundation/model/design.md) | データモデル基盤の設計 |
