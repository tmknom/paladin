# 依存ライブラリ一覧

## 目的

このドキュメントは、`pyproject.toml` の `dependencies` および `dependency-groups` に列挙された全 11 ライブラリの「信頼性プロファイル」を記録する。

バージョンアップ PR をレビューする際に、メンテナの素性・リリース傾向・推移的依存の変化を踏まえた判断ができるようにすることが目的である。

対策レイヤー（uv 設定・Dependabot 運用）の全体像は [サプライチェーンセキュリティ設計](supply-chain.md) を参照。

## 利用上の注意

Dependabot のアップグレード PR が届いたら、本ドキュメントを参照して以下を確認する。

- 推移的依存の増減（新しい間接依存が増えていないか）
- Organization やメンテナに変化がないか（買収・移管など）
- リリースからの経過時間（`--exclude-newer "1 week"` により1週間未満のリリースは Dependabot が提案しない）
- 過去の CVE 傾向との整合性

## サマリ

サプライチェーンの観点では、`runtime` / `dev` の区別は二次的である。どちらも開発者のマシンで `uv sync` が実行される際に取得される。個別の信頼性プロファイルは各節を参照。

| ライブラリ | 用途 | 分類 | 現バージョン | リリース日 |
|----------|------|------|------------|----------|
| colorlog | ログ出力のカラー化 | runtime | 6.10.1 | 2025-10-16 |
| pydantic | データバリデーション・型強制 | runtime | 2.12.5 | 2025-11-26 |
| pydantic-settings | 環境変数・設定ファイル読み込み | runtime | 2.13.1 | 2026-02-19 |
| typer | CLI フレームワーク | runtime | 0.24.0 | 2026-02-16 |
| pytest | テストフレームワーク | dev | 9.0.2 | 2025-12-06 |
| pytest-mock | モックユーティリティ | dev | 3.15.1 | 2025-09-16 |
| pytest-asyncio | 非同期テスト対応 | dev | 1.3.0 | 2025-11-10 |
| pytest-cov | カバレッジ計測 | dev | 7.0.0 | 2025-09-09 |
| vulture | 未使用コード検出 | dev | 2.14 | 2024-12-08 |
| ruff | Linter・フォーマッタ | dev | 0.15.2 | 2026-02-19 |
| pyright | 静的型チェッカー | dev | 1.1.408 | 2025-01-08 |

---

## colorlog

### 概要

Python 標準の `logging` モジュールにカラー出力を追加するラッパーライブラリ

### バージョン

[6.10.1](https://github.com/borntyping/python-colorlog/releases/tag/v6.10.1) — 2025-10-16

### コミット

[68b10149ffdaf3e4f7798d8050cc66c3da53c8e0](https://github.com/borntyping/python-colorlog/commit/68b10149ffdaf3e4f7798d8050cc66c3da53c8e0)

### Organization

個人メンテナ (borntyping) によるメンテナンスモードプロジェクト。活発な機能開発はなく、バグ修正のみ対応している状態である。

### 信頼性指標

- PyPI Trusted Publishing: 有（Sigstore 署名検証対応）
- GitHub Verified Organization: 無（個人アカウント）

### 推移的依存

直接依存 1 / 推移的依存 0（依存なし）

### ライセンス

MIT

### 脆弱性開示

SECURITY.md なし。CVE 報告の実績はない。

### 参照

- [リリースノート](https://github.com/borntyping/python-colorlog/releases/tag/v6.10.1)
- [リポジトリ](https://github.com/borntyping/python-colorlog)

---

## pydantic

### 概要

Python の型ヒントを用いたデータバリデーションとシリアライゼーションライブラリ

### バージョン

[2.12.5](https://github.com/pydantic/pydantic/releases/tag/v2.12.5) — 2025-11-26

### コミット

[bd2d0dd0137dfa1a8fdff2529b9dfb1547980150](https://github.com/pydantic/pydantic/commit/bd2d0dd0137dfa1a8fdff2529b9dfb1547980150)

### Organization

Pydantic Organization が管理。Pydantic Services Inc. による商用サポート（Pydantic Logfire 等）を基盤とした持続的な開発体制が整っている。

### 信頼性指標

- PyPI Trusted Publishing: 有
- GitHub Verified Organization: 有

### 推移的依存

直接依存 1 / 推移的依存 4（annotated-types, pydantic-core, typing-extensions, typing-inspection）

pydantic-core は Rust 実装の C 拡張モジュールであり、コンパイル済みバイナリが wheel に含まれる。ソース配布では Rust ツールチェーンが必要になる。

### ライセンス

MIT

### 脆弱性開示

SECURITY.md あり（責任ある開示プロセス確立）。過去に ReDoS・SSRF・入力検証関連の CVE が複数報告されているが、いずれも修正済みである。アクティブな開発規模に対してリスク管理が機能している状態といえる。

### 参照

- [リリースノート](https://github.com/pydantic/pydantic/releases/tag/v2.12.5)
- [CHANGELOG](https://docs.pydantic.dev/latest/changelog/)
- [リポジトリ](https://github.com/pydantic/pydantic)

---

## pydantic-settings

### 概要

pydantic を基盤とした設定管理ライブラリ。環境変数・`.env` ファイル・設定ファイルから設定値を読み込む

### バージョン

[2.13.1](https://github.com/pydantic/pydantic-settings/releases/tag/v2.13.1) — 2026-02-19

### コミット

[e87d12df0f42f7f72a3eb6d830cfbfb1d68b4496](https://github.com/pydantic/pydantic-settings/commit/e87d12df0f42f7f72a3eb6d830cfbfb1d68b4496)

### Organization

Pydantic Organization が管理。pydantic 本体と同一の Organization・開発体制下にある。

### 信頼性指標

- PyPI Trusted Publishing: 有（Sigstore attestations）
- GitHub Verified Organization: 有

### 推移的依存

直接依存 1 / 推移的依存 7（pydantic およびその依存 + python-dotenv, typing-inspection）

python-dotenv が間接的に含まれる。

### ライセンス

MIT

### 脆弱性開示

SECURITY.md あり（pydantic と同一の開示プロセス）。CVE 報告の実績はない。

### 参照

- [リリースノート](https://github.com/pydantic/pydantic-settings/releases/tag/v2.13.1)
- [CHANGELOG](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- [リポジトリ](https://github.com/pydantic/pydantic-settings)

---

## typer

### 概要

Click をベースにした CLI 構築フレームワーク。Python 型ヒントからコマンドラインインターフェースを自動生成する

### バージョン

[0.24.0](https://github.com/fastapi/typer/releases/tag/v0.24.0) — 2026-02-16

### コミット

[71bf168861558dff0944ab4d8cb7686f509d6e96](https://github.com/fastapi/typer/commit/71bf168861558dff0944ab4d8cb7686f509d6e96)

### Organization

FastAPI Organization (fastapi) が管理。FastAPI と同じ作者 (Sebastián Ramírez) が主導し、組織的に管理されている。

### 信頼性指標

- PyPI Trusted Publishing: 有
- GitHub Verified Organization: 確認不可

### 推移的依存

直接依存 1 / 推移的依存 6（annotated-doc, click, rich, shellingham, markdown-it-py, mdurl, pygments）

rich が間接的に含まれ、さらに markdown-it-py・pygments を引き込む。

### ライセンス

MIT

### 脆弱性開示

SECURITY.md あり（最新バージョンのみサポート）。CVE 報告の実績はない。

### 参照

- [リリースノート](https://github.com/fastapi/typer/releases/tag/v0.24.0)
- [CHANGELOG](https://github.com/fastapi/typer/blob/master/CHANGELOG.md)
- [リポジトリ](https://github.com/fastapi/typer)

---

## pytest

### 概要

Python のデファクトスタンダードなテストフレームワーク

### バージョン

[9.0.2](https://github.com/pytest-dev/pytest/releases/tag/9.0.2) — 2025-12-06

### コミット

[3d10b5148e03eb82b3ee29181dbdc73cf82699e2](https://github.com/pytest-dev/pytest/commit/3d10b5148e03eb82b3ee29181dbdc73cf82699e2)

### Organization

pytest-dev Organization がコミュニティ主導で管理。複数のメンテナによる分散管理体制である。

### 信頼性指標

- PyPI Trusted Publishing: 有（Sigstore attestation）
- GitHub Verified Organization: 無

### 推移的依存

直接依存 1 / 推移的依存 4（iniconfig, packaging, pluggy, pygments）

### ライセンス

MIT

### 脆弱性開示

SECURITY.md なし。過去に tmpdir 処理関連の中程度の脆弱性が 1 件報告されているが修正済みである (GHSA-6w46-j5rx-g56g)。「pytest」名を悪用した偽造パッケージ（pytest-tt-ddriven 等）が継続的に検出されており、名前の類似性に注意が必要である。

### 参照

- [リリースノート](https://docs.pytest.org/en/latest/changelog.html)
- [リポジトリ](https://github.com/pytest-dev/pytest)

---

## pytest-mock

### 概要

pytest プラグインとして `unittest.mock` をフィクスチャ経由で提供するライブラリ

### バージョン

[3.15.1](https://github.com/pytest-dev/pytest-mock/releases/tag/3.15.1) — 2025-09-16

### コミット

[e1b5c62a38c5a05cae614aef3847f240ba50d269](https://github.com/pytest-dev/pytest-mock/commit/e1b5c62a38c5a05cae614aef3847f240ba50d269)

### Organization

pytest-dev Organization が管理。pytest 本体と同一の Organization 下にある。

### 信頼性指標

- PyPI Trusted Publishing: 有（Sigstore attestation）
- GitHub Verified Organization: 無

### 推移的依存

直接依存 1 / 推移的依存 5（pytest およびその依存）

### ライセンス

MIT

### 脆弱性開示

SECURITY.md あり（Tidelift 経由での報告受付）。CVE 報告の実績はない。テスト専用ライブラリであり、本番環境では動作しないため攻撃面は限定的である。

### 参照

- [リリースノート](https://pytest-mock.readthedocs.io/en/latest/changelog.html)
- [リポジトリ](https://github.com/pytest-dev/pytest-mock)

---

## pytest-asyncio

### 概要

pytest で asyncio を用いた非同期テストを実行するためのプラグイン

### バージョン

[1.3.0](https://github.com/pytest-dev/pytest-asyncio/releases/tag/1.3.0) — 2025-11-10

### コミット

[2e9695fcf8c5c514f30f57b7d14ab83846357b96](https://github.com/pytest-dev/pytest-asyncio/commit/2e9695fcf8c5c514f30f57b7d14ab83846357b96)

### Organization

pytest-dev Organization が管理。pytest 本体と同一の Organization 下にある。

### 信頼性指標

- PyPI Trusted Publishing: 有（Sigstore attestation）
- GitHub Verified Organization: 無

### 推移的依存

直接依存 1 / 推移的依存 5（pytest およびその依存）

### ライセンス

Apache-2.0

### 脆弱性開示

SECURITY.md なし。CVE 報告の実績はない。

### 参照

- [リリースノート](https://pytest-asyncio.readthedocs.io/en/latest/)
- [リポジトリ](https://github.com/pytest-dev/pytest-asyncio)

---

## pytest-cov

### 概要

pytest プラグインとして `coverage.py` を統合し、カバレッジ計測を自動化するライブラリ

### バージョン

[7.0.0](https://github.com/pytest-dev/pytest-cov/releases/tag/7.0.0) — 2025-09-09

### コミット

[224d8964caad90074a8cf6dc8720b8f70f31629b](https://github.com/pytest-dev/pytest-cov/commit/224d8964caad90074a8cf6dc8720b8f70f31629b)

### Organization

pytest-dev Organization が管理。pytest 本体と同一の Organization 下にある。

### 信頼性指標

- PyPI Trusted Publishing: 有
- GitHub Verified Organization: 無

### 推移的依存

直接依存 1 / 推移的依存 6（coverage, pluggy, pytest およびその依存）

coverage が間接的に含まれる。

### ライセンス

MIT

### 脆弱性開示

SECURITY.md あり（Tidelift 経由での報告受付）。CVE 報告の実績はない。

### 参照

- [リリースノート](https://pytest-cov.readthedocs.io/en/latest/changelog.html)
- [リポジトリ](https://github.com/pytest-dev/pytest-cov)

---

## vulture

### 概要

Python コードの未使用コード（変数・関数・クラス・import 等）を静的に検出するツール

### バージョン

[2.14](https://github.com/jendrikseipp/vulture/releases/tag/v2.14) — 2024-12-08

### コミット

[e454d2ef39fc23e72549ff23a1a14e31c3a75605](https://github.com/jendrikseipp/vulture/commit/e454d2ef39fc23e72549ff23a1a14e31c3a75605)

### Organization

個人開発者 (Jendrik Seipp) によるメンテナンス。スウェーデン在住の研究者・開発者が主体であり、商用サポートはない。

### 信頼性指標

- PyPI Trusted Publishing: 確認不可
- GitHub Verified Organization: 無（個人アカウント）

### 推移的依存

直接依存 1 / 推移的依存 0（依存なし）

### ライセンス

MIT

### 脆弱性開示

SECURITY.md なし。CVE 報告の実績はない。

### 参照

- [CHANGELOG](https://github.com/jendrikseipp/vulture/blob/main/CHANGELOG.md)
- [リポジトリ](https://github.com/jendrikseipp/vulture)

---

## ruff

### 概要

Rust 実装の高速な Python Linter・フォーマッタ。pycodestyle・pyflakes・isort 等の機能を統合する

### バージョン

[0.15.2](https://github.com/astral-sh/ruff/releases/tag/0.15.2) — 2026-02-19

### コミット

[9d18ee9115f9cbb4c21478baa7c1fa2b46e0759c](https://github.com/astral-sh/ruff/commit/9d18ee9115f9cbb4c21478baa7c1fa2b46e0759c)

### Organization

Astral Software Inc. (USA) が管理。商用企業バックの組織的な開発体制を持ち、astral.sh ドメインで GitHub Verified Organization の認証を取得している。

### 信頼性指標

- PyPI Trusted Publishing: 確認不可（GitHub Artifact Attestations を提供）
- GitHub Verified Organization: 有（astral.sh ドメイン認証）

### 推移的依存

直接依存 1 / 推移的依存 0（依存なし）

Rust 実装のため Python 推移的依存がない。wheel にコンパイル済みバイナリが含まれる。

### ライセンス

MIT

### 脆弱性開示

SECURITY.md あり（security@astral.sh への報告）。CVE 報告の実績はない。

### 参照

- [CHANGELOG](https://github.com/astral-sh/ruff/blob/main/CHANGELOG.md)
- [リポジトリ](https://github.com/astral-sh/ruff)

---

## pyright

### 概要

Microsoft が開発した Python 静的型チェッカー。LSP サーバーとしても機能する

### バージョン

[1.1.408](https://github.com/microsoft/pyright/releases/tag/1.1.408) — 2025-01-08

### コミット

[ad444cc7a0923cb6127279fb95fe0b576d96d0d7](https://github.com/microsoft/pyright/commit/ad444cc7a0923cb6127279fb95fe0b576d96d0d7)

### Organization

Microsoft Corporation が管理。microsoft.com および opensource.microsoft.com ドメインで GitHub Verified Organization 認証を取得している。PyPI パッケージ (`pyright`) のラッパー管理は RobertCraigie 個人が担当しており、Microsoft の本体リポジトリと PyPI 配布者が異なる点に注意が必要である。

### 信頼性指標

- PyPI Trusted Publishing: 確認不可（PyPI 版は個人が管理）
- GitHub Verified Organization: 有（Microsoft）

### 推移的依存

直接依存 1 / 推移的依存 2（nodeenv, typing-extensions）

nodeenv を通じて Node.js 実行環境を構成する。pyright 本体は Node.js バイナリとして動作するため、Python ラッパーが nodeenv 経由で Node.js を管理する構造になっている。

### ライセンス

MIT

### 脆弱性開示

SECURITY.md あり（MSRC: https://msrc.microsoft.com/create-report 経由）。Bug Bounty Program あり。CVE 報告の実績はない。

### 参照

- [リリースノート](https://github.com/microsoft/pyright/releases)
- [リポジトリ](https://github.com/microsoft/pyright)
