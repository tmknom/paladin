# Paladin

Python ソースコードを静的解析し、プロジェクトで定義された設計ルールへの違反を検出する CLI ツールです。

## 特徴

- Ruff や Pyright では扱いにくいプロジェクト固有の設計ルールを検出する
- 生成 AI が安定して解釈し、修正判断に利用できる構造化された診断情報を返す
- 違反箇所・ルール識別子・違反理由・修正の方向性を含む診断を提供する

## ドキュメント

| ディレクトリ | 内容 |
|------------|------|
| [docs/intro/](docs/intro/README.md) | 基本方針・要件定義・CLI 設計草案・ロードマップ |
| [docs/design/](docs/design/) | アーキテクチャ・コーディング規約 |
| [docs/specs/](docs/specs/) | モジュール別の要件定義・基本設計 |

[`llms.txt`](llms.txt) は AI エージェント向けのドキュメントインデックスです。

## 開発

```bash
make all          # format + lint + typecheck + ユニットテスト
make test         # 全テスト実行（ユニット + インテグレーション）
make fmt          # ruff でフォーマット
make lint         # ruff で静的解析
make typecheck    # pyright で型チェック
make coverage     # カバレッジ計測
```

## 動作要件

- Python 3.13+
- [uv](https://docs.astral.sh/uv/)（パッケージマネージャ）
