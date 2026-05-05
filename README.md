# Paladin

Python ソースコードを静的解析し、プロジェクトで定義された設計ルールへの違反を検出する CLI ツールです。

## 特徴

- Ruff や Pyright が扱わないプロジェクト固有の設計ルール（モジュール境界・import 方針・公開境界など）を検出する
- 生成 AI が安定して解釈できるよう、違反箇所・ルール識別子・理由・修正方向を含む構造化診断を返す

設計思想の詳細は [docs/intro/concept.md](docs/intro/concept.md) を参照してください。

## インストール

Python 3.13+ と [uv](https://docs.astral.sh/uv/) が必要です。

```bash
uv sync
```

## 使い方

```bash
uv run paladin check [TARGET ...]   # 静的解析を実行する（主コマンド）
uv run paladin list                 # 利用可能なルール一覧を表示する
uv run paladin view <RULE_ID>       # ルールの詳細を表示する
uv run paladin version              # バージョンを表示する
```

プロジェクトごとの設定は `pyproject.toml` の `[tool.paladin]` セクションで行います。コマンド仕様は [docs/intro/interface.md](docs/intro/interface.md)、設定項目は [docs/design/configuration.md](docs/design/configuration.md) を参照してください。

## ドキュメント

| ディレクトリ | 内容 |
|------------|------|
| [docs/intro/](docs/intro/README.md) | 基本方針・全体仕様・CLI インターフェイス・プロジェクト構造 |
| [docs/design/](docs/design/README.md) | アーキテクチャ・コーディング規約・開発ワークフロー |
| [docs/specs/](docs/specs/README.md) | モジュール別の要件定義・基本設計 |

[`llms.txt`](llms.txt) は AI エージェント向けのドキュメントインデックスです。

## 開発

```bash
make all       # format + lint + typecheck + ユニットテスト
make test      # 全テスト実行（ユニット + インテグレーション）
make coverage  # カバレッジ計測
```

開発フローと各ターゲットの詳細は [docs/design/workflow.md](docs/design/workflow.md) を参照してください。

## ライセンス

Apache License 2.0 — 詳細は [LICENSE](LICENSE) を参照してください。
