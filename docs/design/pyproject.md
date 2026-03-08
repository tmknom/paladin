# pyproject.toml 設計ガイドライン

## 目的

このドキュメントは `pyproject.toml` の設定における「設計意図の記録」として機能する。

各ツールの設定項目は公式ドキュメントを読まなければ意図が分からない。特に Ruff の `ignore/unfixable/per-file-ignores` や Pyright の診断レベル設定は「なぜその値なのか」がコードから読み取れない。本ドキュメントはその「なぜ」を補足する。

対象セクションは `[project]` の基本属性（`name`・`version`・`description`・`requires-python`・`dependencies`）を除く、`project.scripts`・ビルドシステム・テスト・Linter・型チェックの各設定とする。

## CLIエントリーポイント（project.scripts）

`project.scripts` はコマンド名とエントリーポイント関数のマッピングを定義する。

記法は `コマンド名 = "モジュールパス:関数名"` という形式を取る。`example.cli:main` は「`example.cli` モジュール内の `main` 関数をエントリーポイントとして登録する」という意味である。パッケージのインストール後、`example` コマンドを実行すると `example.cli.main()` が呼ばれる仕組みである。

`uv run example` のように実行できるのは、この設定によって実行可能スクリプトが生成されるためである。

## ビルドシステム（build-system / tool.hatch）

### hatchling を選んだ理由

`hatchling` は Hatch プロジェクトが提供するビルドバックエンドである。`setuptools` と比較して以下の点で優れている。

- 設定が `pyproject.toml` に完結する（`setup.py` や `setup.cfg` が不要）
- デフォルト動作が現代的なプロジェクト構成（`src` レイアウト）を前提としている
- 設定の学習コストが低く、最小限の記述で機能する

### packages の明示指定

`src` レイアウトを採用する場合、`packages = ["src/example"]` を明示的に指定している。

自動検出に任せると `src/` 配下の意図しないディレクトリ（`src/tool/` 等）を拾う可能性がある。明示することでビルド成果物に含まれるパッケージを確実に制御できる。

## 開発依存（dependency-groups）

`[dependency-groups]` は PEP 735 で標準化されたグループ定義である。`[project.optional-dependencies]` との違いは、インストール成果物（wheel/sdist）に含まれない点にある。開発・CI 専用のツールに使うのが意図された用途である。

`dev` グループに含まれるツールの役割を 3 軸で分類する。

| ツール | 役割 | 分類 |
|--------|------|------|
| pytest | テスト実行フレームワーク | テスト |
| pytest-mock | モックオブジェクト生成 | テスト |
| pytest-asyncio | 非同期テスト対応 | テスト |
| pytest-cov | カバレッジ計測 | テスト |
| vulture | 未使用コード検出 | 品質 |
| ruff | Linter・フォーマッタ | 品質 |
| pyright | 静的型チェッカー | 型 |

## テスト設定（tool.pytest / tool.coverage）

### pytest

`asyncio_mode = "strict"` と `asyncio_default_fixture_loop_scope = "function"` はセットで機能する設定である。

`strict` モードでは、非同期テストを `@pytest.mark.asyncio` デコレータで明示的に指定することを強制する。無指定の非同期関数を誤ってテストとして扱うことを防ぐ意図がある。

`asyncio_default_fixture_loop_scope = "function"` は、各テスト関数が独立したイベントループを使用することを保証する。テスト間の状態汚染を防ぎ、テストの独立性を高める。

| 設定 | 値 | 対応する方針 |
|------|-----|-------------|
| `pythonpath` | `["src", "."]` | `src/` 配下と `tests/` 配下を絶対 import で参照できるようにする |
| `testpaths` | `["tests"]` | テスト検索パス（Python import パスではない） |

`pythonpath` は pytest 7.0+ のビルトイン機能であり、追加プラグインは不要。プロジェクト標準は `pyproject.toml` の `[tool.pytest.ini_options]` セクションの設定を正とする。

`"."` （プロジェクトルート）を `pythonpath` に追加することで、`tests.unit.test_transform.fakes` のような絶対 import が解決できる。`__init__.py` によりテストディレクトリがパッケージとして認識されるため、各 `fakes.py` を絶対パスで参照できる。

### coverage

`source = ["src"]` はカバレッジ計測の対象を `src/` 配下に限定する設定で、テストコードやツール類がレポートに混入することを防ぐ。

`patch = ["subprocess"]` はサブプロセス内のコードをカバレッジ計測対象に含めるための設定である。

インテグレーションテスト（`tests/integration/`）では、CLI アプリを `subprocess.run()` で子プロセスとして起動して end-to-end の動作を検証する。この子プロセス内で実行されるアプリコード（`src/example/` 配下）は、通常の状態では pytest の計測範囲に含まれない。`patch = ["subprocess"]` を設定することで、この問題を解決する。

仕組みは以下のとおりである。

1. **環境変数の伝播**: coverage.py が `COVERAGE_PROCESS_CONFIG` 環境変数にカバレッジ設定をシリアライズして保存し、`subprocess.run()` で起動する子プロセスに自動的に引き継がれる。
2. **`.pth` ファイルによる自動ロード**: pytest-cov はインストール時に仮想環境の `site-packages/` に `.pth` ファイルを生成する。子プロセスの Python 起動時にこのファイルが自動読み込まれ、`COVERAGE_PROCESS_CONFIG` が存在すれば `coverage.process_startup()` を呼び出す。
3. **子プロセスでの計測開始**: `coverage.process_startup()` により、子プロセス内でも `src/example/` 配下のコードが計測対象になる。
4. **並列モードの自動有効化**: `patch = ["subprocess"]` を設定すると `parallel = true` が自動的に有効になる。各プロセスが独立した `.coverage.<pid>` ファイルに書き込み、pytest-cov がテスト終了後に全ファイルを統合してレポートを生成する。

`patch = ["subprocess"]` がない場合、`subprocess.run()` で起動した子プロセス内のアプリコードはカバレッジ計測対象外となる。インテグレーションテストが実行されても、その中で走ったコードパスがカバレッジレポートに反映されない。

`source = ["src"]` と `patch = ["subprocess"]` はセットで機能する。前者が「何を計測するか」を定義し、後者が「子プロセスを含めて計測する仕組みを有効にする」役割を担う。

| 設定 | 値 | 対応する方針 |
|------|-----|-------------|
| `source` | `["src"]` | `src/` 配下のみを計測対象とし、テストコードやツール類の混入を防ぐ |
| `patch` | `["subprocess"]` | `subprocess` 経由で起動した子プロセス内のコードも計測対象に含める |

## Linter設定（tool.ruff）

### 基本設定

`line-length = 100` は Python 標準の 79 文字より長い値を設定している。URL や日本語を含む行が 79 文字制限に引っかかりやすいため、現実的な長さとして 100 文字を採用した。行長オーバーの扱いはフォーマッタとコードレビューに委ねる（詳細は「無効化ルールの分類と理由」の「別ツールの責務」を参照）。

`target-version = "py313"` は Python 3.13 向けの構文・ルールを適用する設定である。`requires-python` と合わせることで、古い Python の互換性を気にした余計な提案が出ないようにする。

`exclude` は Ruff の検査対象から除外するディレクトリを指定する。`.git`・`.venv` はツールのメタデータや仮想環境のため除外する。`.vscode`・`.claude` は IDE・AI ツールの設定ファイルであり Lint 対象外とする。`tmp` は一時ファイルの置き場であり除外する。

Ruff はデフォルトで `build/` や `dist/` を除外するため、`exclude` への明示的な追加は不要である。Pyright はデフォルトで除外しないため、`[tool.pyright]` の `exclude` には `build` と `dist` を明示的に追加している（後述）。

### 有効化ルールの選定方針

有効化するルールを役割別に分類する。

| グループ | プレフィックス | 役割 |
|----------|---------------|------|
| バグ直結 | F, B | 未定義参照、未使用コード、バグの温床となるパターンを検出 |
| コードスタイル | E, W, I | 基本的なスタイル統一、import 順序整列 |
| モダン化 | UP, SIM, PTH | 現代的な Python 構文への移行促進、冗長な表現の簡素化 |
| ドキュメント | D | docstring の存在・形式チェック |
| Ruff 独自 | RUF | 実用的な補助検出（曖昧 Unicode など） |

### 無効化ルールの分類と理由

無効化ルールを 4 カテゴリに分類して意図を明示する。

**別ツールの責務** — E501

行長オーバーはフォーマッタ（ruff format）とコードレビューで対処するため、Linter での検出は除外する。URL や日本語を含む行は 100 文字を超えることがあるが、フォーマッタの自動整形に任せる運用とする。

**日本語対応** — RUF001, RUF002, RUF003, D400, D415

日本語文字列・コメント・docstring を許容するための無効化。英語前提のルールは日本語コードベースで大量に誤検知する。

| 設定 | 値 | 対応する方針 |
|------|-----|-------------|
| `D400` 無視 | 1行目末尾のピリオド不要 | 英語の `.` 終端を強制しない（日本語の「。」を許容） |
| `D415` 無視 | 1行目末尾の句読点不要 | 英語の句読点終端を強制しない（日本語の文末表現を許容） |
| `RUF001` 無視 | 文字列内の曖昧 Unicode | 日本語文字列を許容 |
| `RUF002` 無視 | docstring 内の曖昧 Unicode | 日本語 docstring を許容 |
| `RUF003` 無視 | コメント内の曖昧 Unicode | 日本語コメントを許容 |

**ルール競合（Google 方式）** — D203, D213

`D203/D211` と `D212/D213` はそれぞれ競合するペアである。両方を有効にすると ruff がエラーを返す構造になっており、Google 方式で採用した側（D211, D212）を活かし、競合する側（D203, D213）を無効化する。

| 設定 | 値 | 対応する方針 |
|------|-----|-------------|
| `D203` 無視 | D211 と競合 | クラス docstring 前に空行を要求しない（Google 方式では D211 優先） |
| `D213` 無視 | D212 と競合 | 要約行は 1 行目に書く（Google 方式では D212 採用） |

**可読性・移行コスト** — SIM105, SIM108, SIM116

提案の意図は理解できるが可読性への影響が大きく、コードベース全体の一貫性を壊す可能性があるため無効化する。

| 設定 | 値 | 対応する方針 |
|------|-----|-------------|
| `SIM105` 無視 | `try-except-pass` → `contextlib.suppress` | 画一的に適用すると読みにくくなる |
| `SIM108` 無視 | `if-else` → 三項演算子 | 画一的に適用すると読みにくくなる |
| `SIM116` 無視 | 連続 `if` → `dict` ルックアップ | 画一的に適用すると読みにくくなる |

### パス別の緩和（per-file-ignores）

本番コードは厳しめ、周辺コードは緩めの運用を `per-file-ignores` で実現する。

| パターン | 緩和するルール | 理由 |
|---------|--------------|------|
| `**/__init__.py` | F401 | re-export の未使用 import を許容 |
| `tests/**` | D100, D101, D102, D107 | テストでは docstring は不要 |
| `tests/**/__init__.py` | D104 | テストの `__init__.py` は空ファイルのためパッケージ docstring を免除 |

**`__init__.py` の F401 緩和について**

`__init__.py` での re-export は公開 API の定義手段であり、構文上「未使用」に見えても意図的なものである。

**`tests/**` の docstring 緩和について**

テストコードでは docstring を必須としない。テストクラスは 1 行 docstring を推奨するが lint では強制しない。テストメソッドはテスト名に情報を集約する方針のため、docstring は不要である。`tests/**/__init__.py` の D104 免除はテストの `__init__.py` が空ファイルで配置される方針によるものである。

### docstringスタイル（pydocstyle）

`convention = "google"` を指定すると、pydocstyle の Google スタイル準拠ルールセットが自動的に有効・無効になる。具体的には D212（要約行は 1 行目）が有効になり、その代わりに競合する D213 は自動的に無効扱いとなる。

| 設定 | 値 | 対応する方針 |
|------|-----|-------------|
| `convention` | `"google"` | Google 形式で docstring を記述 |

`convention` を指定することで、Google スタイルに合わないルールを個別に無効化する手間が省ける。

## 型チェック設定（tool.pyright）

### 検査対象とスコープ

`include = ["src", "tests"]` で本番コードとテストコードの両方を検査対象とする。`.git`・`.venv`・`.vscode`・`.claude`・`tmp` はツールや一時ファイルのため除外する。`build` と `dist` はビルド成果物のため除外する。Ruff はこれらをデフォルトで除外するが、Pyright はデフォルト除外ではないため `exclude` に明示している。

`pythonVersion = "3.13"` は型チェックに使用する Python バージョンを指定する。`requires-python` および `[tool.ruff]` の `target-version` と揃えることで、バージョン依存の型推論・ルール適用が一貫する。

`typeCheckingMode = "basic"` を採用した理由は、開発初期の速度優先である。`strict` モードにすると型アノテーションが不完全なコードでエラーが多発し、開発の流れが止まりやすい。`basic` モードで「バグに直結するものだけエラーにする」方針を取りつつ、個別設定で重要な項目を `error` に昇格させる二段構えを採用している。

### 実行環境の分離（executionEnvironments）

`executionEnvironments` は「どのディレクトリのコードがどの import パスを持つか」を pyright に伝える設定である。

| 設定 | 値 | 対応する方針 |
|------|-----|-------------|
| `executionEnvironments` の `src` | `extraPaths = ["src"]` | プロダクションコードの import 解決 |
| `executionEnvironments` の `tests` | `extraPaths = ["src", "."]` | テストから src 配下にアクセス |

- `root = "src"` の環境: `extraPaths = ["src"]` を設定し、`src/` 配下のモジュールを互いに import できるようにする
- `root = "tests"` の環境: `extraPaths = ["src", "."]` を設定し、テストから本番コードにアクセスできるようにする

テストパッケージの絶対 import（`from tests.unit.test_transform.fakes import ...`）は `__init__.py` によるパッケージ化と `"."` の追加で pyright が解決する。`"."` はプロジェクトルートを import パスに追加する設定であり、pytest の `pythonpath` 設定と対応する。ルート直下にプロダクション用モジュールは配置しないこと（プロダクションコードは `src/` 配下に限定する）。

### 診断レベルの設計思想

pyright の診断レベルは `"error"`, `"warning"`, `"none"` の 3 段階である。

| レベル | 意味 | 使いどころ |
|--------|------|-----------|
| `"error"` | CI を止める。コミット前に修正必須 | バグに直結する問題 |
| `"warning"` | 開発の流れを止めない。後で対処可能 | 重要だが初期に多発する問題 |
| `"none"` | 完全無効化。ノイズが多すぎる場合に使用 | 初期段階では情報量が多すぎるもの |

`typeCheckingMode = "basic"` はデフォルトで多くのチェックを `"warning"` 水準に設定するが、個別設定で重要度に応じて `"error"` または `"none"` に調整する。

### エラー昇格の判断基準

**エラーに昇格するもの（バグに直結する）**:

- `reportIncompatibleMethodOverride`, `reportIncompatibleVariableOverride`: オーバーライドの型不整合は実行時エラーに直結する
- `reportUnusedCoroutine`: `await` 忘れはコルーチンが実行されない実行不具合になる
- `reportMatchNotExhaustive`: `match` 文で網羅漏れがあると想定外のケースで処理が抜ける
- `reportOverlappingOverload`: オーバーロード定義の矛盾は型推論の誤動作を招く
- `reportUnknownVariableType`, `reportUnknownParameterType`, `reportMissingTypeArgument`: 型ヒント必須の方針を機械的に強制する

**警告に留めるもの（開発をブロックしたくない）**:

- `reportMissingImports`, `reportMissingModuleSource`: 依存ライブラリの導入前に import を書くことがある。エラーにすると新規ライブラリ追加の際に開発が止まる
- `reportCallIssue`, `reportAttributeAccessIssue`: 呼び出し不能・属性不在の検出は重要なため完全無効化せず最低限の安全網として残す
- `reportPrivateUsage`: `_private` な要素の外部使用を抑制するが、開発中は一時的に許容したい場面がある
- `reportUnknownArgumentType`, `reportUnknownLambdaType`: 生成コードに多いため開発をブロックしない
- `reportUnusedImport`, `reportUnusedVariable`: 未使用の import・変数は警告に留め、生成コードでの一時変数を許容する。Ruff との併用で自動修正と両立できる

**無効化するもの（ノイズが多すぎる）**:

- `reportMissingTypeStubs`: サードパーティの型スタブ不足は初期開発では無視してスピードを優先する
- `reportUnknownMemberType`: `list.append` などの基本操作で頻発するため無効化する。重要な属性エラーは `reportAttributeAccessIssue` で別途検出する

`useLibraryCodeForTypes = true` は型スタブが存在しない場合でも実装コードから型推論を行い、IDE 補完の精度を向上させる設定である。`reportMissingTypeStubs` を `"none"` にしつつも、型情報を最大限に活用する意図がある。
