# 設定ファイルインターフェイス設計

## 1. この文書の目的

この文書は、Paladin の設定ファイル（`pyproject.toml` の `[tool.paladin]` セクション）について **ユーザー向けインターフェイス** を定義するものです。ここでいう「ユーザー」とは、主に生成 AI と、補助的に人間の開発者を指します。

定義する内容は以下の通りです。

- ルールの有効化・無効化の書式と仕様（R-090）
- 解析対象パスの include/exclude の書式と仕様（R-091）
- ルール個別設定の書式と仕様（R-092）
- ディレクトリ別設定の書式と仕様（R-093）
- 各設定項目間の関係と適用順序
- 既存の Ignore 設計との統合方針

定義しない内容は以下の通りです。

- 設定ファイルの読み込みモジュールの内部アーキテクチャ
- 設定値のバリデーション実装方式
- CLI オプションとの優先順序の詳細な解決アルゴリズム
- `paladin.toml` 独立設定ファイルの仕様（将来拡張として扱う）

## 2. 設計方針

### 2.1 全体方針

設定ファイルのインターフェイスは以下の方針に従って設計します。

- **明示的であること** — 暗黙の挙動を避け、設定の意味が読んで分かる
- **最小限であること** — Paladin のルール数は少なく個人用ツールであるため、過度な汎用性よりシンプルさを優先する
- **AI が安定して扱えること** — 書式が単純で、生成 AI が正確に生成・解釈できる
- **既存 Linter ユーザーが直感的に使えること** — Python エコシステムの慣例に沿った設計にする

### 2.2 既存 Linter から学んだこと

主要 Linter の設定インターフェイスを調査した結果、以下の知見を得ました。

- **Ruff の `extend-*` パターンは強力だが複雑** — `select` / `extend-select` / `ignore` / `extend-ignore` の組み合わせは、ルール数が多い汎用 Linter では有用だが、Paladin のように少数のルールを扱うツールでは不要な複雑さになる
- **mypy の `[[tool.mypy.overrides]]` はディレクトリ別設定に適する** — 1つの設定ファイル内で完結し、TOML の配列テーブルとして自然に表現できる
- **Ruff / Pyright の `include` / `exclude` は直感的** — 解析対象パスの制御として広く理解されており、同じ命名を採用することで学習コストを下げられる
- **Ruff のルール個別設定はサブセクション方式** — `[tool.ruff.lint.pydocstyle]` のようにルールごとのサブセクションを使う方式は、TOML の構造と相性が良い

### 2.3 Paladin 固有の判断

Paladin の特性に基づき、以下の設計判断を行います。

- **全ルールがデフォルトで有効** — Paladin のルール数は少なく、すべてのルールに実用的な価値がある。設定ファイルは「一部を無効化する」ために使う
- **`extend-*` 系は導入しない** — ルール数が少なく個人用であるため、`extend-select` / `extend-ignore` / `extend-exclude` は不要な複雑さを持ち込む
- **ディレクトリ別設定はネストした設定ファイルではなく、1つの `pyproject.toml` 内で完結する** — mypy の `[[tool.mypy.overrides]]` パターンを参考にする
- **ルールの有効/無効は `true` / `false` で指定する** — Ruff のように `select` / `ignore` リストで管理する方式は採用しない。ルール数が少ないため、各ルールの状態を個別に宣言する方が一目で分かりやすい

## 3. ルールの有効化・無効化（R-090）

### 3.1 セクション名

```toml
[tool.paladin.rules]
```

### 3.2 書式

各ルール ID をキーとし、`true`（有効）/ `false`（無効）の真偽値を指定します。

```toml
[tool.paladin.rules]
no-relative-import = false
no-local-import = false
```

### 3.3 デフォルト

- 全ルールがデフォルトで有効である
- `[tool.paladin.rules]` セクションが存在しない場合、全ルールが有効として動作する
- セクション内に記載されていないルールも有効として扱う

この方式は「明示的に無効化したルールだけを書く」というシンプルな運用になります。ルール数が少ない Paladin では、有効なルールを列挙するよりも、無効化するルールだけを書く方が簡潔です。

### 3.4 仕様の詳細

- キーはルール ID（ハイフン区切りの名前）を使用する
- 値は TOML の真偽値（`true` / `false`）のみを受け付ける
- 存在しないルール ID を指定した場合、警告を出力して無視する
- `true` を明示的に書くことも許容する（可読性のため）

### 3.5 具体例

特定ルールを無効化する場合。

```toml
[tool.paladin.rules]
no-relative-import = false
```

全ルールの状態を明示的に示す場合（可読性重視）。

```toml
[tool.paladin.rules]
require-all-export = true
no-relative-import = false
no-local-import = true
require-qualified-third-party = true
```

### 3.6 `select` / `ignore` 方式を採用しない理由

Ruff のように `select = [...]` / `ignore = [...]` でルールを指定する方式も検討しましたが、以下の理由で採用しません。

- Ruff は数百のルールを持ち、カテゴリプレフィックス（`E4`, `E7`）で一括指定する必要があるため `select` / `ignore` が有用である。Paladin はルール数が少なく、個別に `true` / `false` を指定する方が分かりやすい
- `select` と `ignore` の両方が存在すると、どちらが優先されるかの混乱が生じる。真偽値方式なら各ルールの状態が一目で分かる
- 真偽値方式は TOML の構造として素直であり、AI が生成・解釈しやすい

## 4. 解析対象パスの制御（R-091）

### 4.1 書式

`[tool.paladin]` セクション直下に `include` と `exclude` をリストとして定義します。

```toml
[tool.paladin]
include = ["src/", "lib/"]
exclude = [".venv/", "build/", "dist/"]
```

### 4.2 デフォルト

- `include` が未指定の場合、CLI で渡された `TARGET` 引数がそのまま解析対象になる（現行の動作と同じ）
- `exclude` が未指定の場合、除外パスはない
- `include` が指定されている場合、CLI で `TARGET` を省略しても `include` のパスが解析対象になる

### 4.3 仕様の詳細

- `include` / `exclude` の値は文字列の配列であり、各要素は `pyproject.toml` からの相対パスとして解釈する
- ディレクトリパスは末尾の `/` の有無によらず、ディレクトリとして扱う
- glob パターン（`*`, `**`）を使用できる
- `exclude` は `include` で指定された範囲内から除外するパスを指定する
- CLI で `TARGET` 引数が明示的に指定された場合、`include` の値は無視し、`TARGET` 引数を解析対象とする。ただし `exclude` は CLI 指定時にも適用される

### 4.4 CLI 引数との関係

| CLI `TARGET` | `include` | 解析対象 |
|--------------|-----------|---------|
| 指定あり | 指定あり | CLI の `TARGET` を使用（`include` は無視） |
| 指定あり | 未指定 | CLI の `TARGET` を使用 |
| 指定なし | 指定あり | `include` のパスを使用 |
| 指定なし | 未指定 | エラー（解析対象が不明） |

`exclude` は上記のいずれの場合にも適用されます。

### 4.5 具体例

基本的な使用例。

```toml
[tool.paladin]
include = ["src/"]
exclude = [".venv/", "build/", "dist/"]
```

glob パターンを使う場合。

```toml
[tool.paladin]
include = ["src/", "lib/"]
exclude = ["**/generated/**", "**/*_pb2.py"]
```

### 4.6 設計の選択理由

Ruff と Pyright はいずれも `include` / `exclude` をトップレベルセクション直下に配置しています。Paladin も同じ命名・配置を採用することで、既存ツールのユーザーが直感的に設定できるようにします。

デフォルトの `exclude` リスト（`.git`, `.venv` など）は設けません。Paladin は CLI の `TARGET` 引数で解析対象を明示的に指定する運用を基本としており、暗黙の除外リストは混乱を招く可能性があるためです。

## 5. ルール個別設定（R-092）

### 5.1 セクション名

```toml
[tool.paladin.rule."<rule-id>"]
```

ルール ID がハイフン区切りの名前であるため、TOML ではクォートが必要です。

```toml
[tool.paladin.rule."require-qualified-third-party"]
```

### 5.2 書式

ルール固有のパラメータをキー・値の形式で指定します。

```toml
[tool.paladin.rule."require-qualified-third-party"]
root-packages = ["paladin", "myapp"]
```

### 5.3 現在のルール個別設定

ルール個別設定を持つルールは `require-qualified-third-party` の `root-packages` のみです。このパラメータは「プロジェクトのルートパッケージ名」を指定し、サードパーティ判定の対象外とするために使用します。

### 5.4 仕様の詳細

- 各ルールが受け付けるパラメータは、そのルールの仕様で定義される
- 存在しないルール ID をセクション名に使用した場合、警告を出力して無視する
- ルールが認識しないパラメータが含まれている場合、警告を出力して無視する
- パラメータ名は TOML の慣例に従いハイフン区切り（kebab-case）とする。Python 側のフィールド名（snake_case）との変換は実装層が担当する

### 5.5 `[tool.paladin.rules]` との関係

`[tool.paladin.rules]` はルールの有効/無効を制御し、`[tool.paladin.rule."<rule-id>"]` はルールの挙動パラメータを制御します。両者は独立した設定です。

- `[tool.paladin.rules]` でルールを `false` にしている場合、そのルールの設定は読み込まれるが適用されない
- `[tool.paladin.rule."<rule-id>"]` を定義しても、そのルールは自動的に有効にはならない（デフォルトで有効であるため）

### 5.6 `rules` と `rule` の命名について

`[tool.paladin.rules]` は複数ルールの有効/無効を一覧的に管理するセクションであるため、複数形の `rules` を使用します。`[tool.paladin.rule."<rule-id>"]` は特定の1つのルールの設定を管理するセクションであるため、単数形の `rule` を使用します。この使い分けにより、セクション名から役割が読み取れるようになります。

## 6. ディレクトリ別設定（R-093）

### 6.1 方式の選択

ネストした設定ファイル（ディレクトリごとに `paladin.toml` を配置する方式）は採用しません。1つの `pyproject.toml` 内で完結する方式を採用します。

mypy の `[[tool.mypy.overrides]]` パターンを参考にし、TOML の配列テーブル（`[[...]]`）を使用します。

### 6.2 セクション名

```toml
[[tool.paladin.overrides]]
```

### 6.3 書式

各オーバーライドエントリは `files` キーで対象パスパターンを指定し、そのスコープ内でルールの有効/無効を上書きします。

```toml
[[tool.paladin.overrides]]
files = ["tests/**"]

[tool.paladin.overrides.rules]
require-all-export = false
```

### 6.4 仕様の詳細

- `files` は必須キーであり、glob パターンの配列を指定する
- glob パターンは `pyproject.toml` からの相対パスとして解釈する
- オーバーライド内で指定できる設定は `rules`（ルールの有効/無効）のみである
- 複数のオーバーライドが同一ファイルにマッチした場合、 **後に定義されたオーバーライドが優先** される（後勝ち）
- オーバーライドで指定されていない設定項目は、トップレベルの設定値を引き継ぐ
- `include` / `exclude` はオーバーライド内では指定できない（解析対象の制御はトップレベルでのみ行う）

### 6.5 後勝ちの注意点

前のオーバーライドの設定は引き継がれません。意図した通りに動作させるには、より具体的なオーバーライドに必要な設定をすべて含めてください。

```toml
# tests/** にマッチする 1 つ目のオーバーライド
[[tool.paladin.overrides]]
files = ["tests/**"]

[tool.paladin.overrides.rules]
require-all-export = false

# tests/integration/** にもマッチする 2 つ目のオーバーライド
# tests/integration/ 配下のファイルには、この設定のみが適用される
[[tool.paladin.overrides]]
files = ["tests/integration/**"]

[tool.paladin.overrides.rules]
require-all-export = false   # 1 つ目の設定は引き継がれないため再掲する
no-relative-import = false
```

### 6.6 具体例

テストディレクトリで `require-all-export` を無効化する場合。

```toml
[[tool.paladin.overrides]]
files = ["tests/**"]

[tool.paladin.overrides.rules]
require-all-export = false
```

スクリプトディレクトリでルールを緩和する場合。

```toml
[[tool.paladin.overrides]]
files = ["scripts/**"]

[tool.paladin.overrides.rules]
no-relative-import = false
require-qualified-third-party = false
```

### 6.7 `per-file-ignores` との関係

`per-file-ignores`（Ignore 設計で定義済み）と `[[tool.paladin.overrides]]` はスコープが似ていますが、目的が異なります。

| 設定 | 目的 | 効果 |
|------|------|------|
| `per-file-ignores` | 特定ファイルで特定ルールの **違反を無視** する | 違反は検出されるが報告されない |
| `[[tool.paladin.overrides]]` | 特定ディレクトリでルールを **無効化** する | ルール自体が適用されない |

`per-file-ignores` は「例外的に違反を許容する」ためのものであり、`[[tool.paladin.overrides]]` は「そもそもルールを適用しない」ためのものです。意図を明確にするために、両者を使い分けてください。

## 7. 設定ファイルの完全な例

全設定項目を含む実用的な例を示します。

```toml
[tool.paladin]
# 解析対象パスの制御
include = ["src/", "lib/"]
exclude = [".venv/", "build/", "dist/", "**/generated/**"]

# ルールの有効/無効
[tool.paladin.rules]
require-all-export = true
no-relative-import = true
no-local-import = true
require-qualified-third-party = true

# ルール個別設定
[tool.paladin.rule."require-qualified-third-party"]
root-packages = ["paladin", "myapp"]

# Ignore（Ignore 設計で定義済み）
[tool.paladin.per-file-ignores]
"tests/**/__init__.py" = ["*"]
"scripts/**" = ["no-relative-import"]

# ディレクトリ別設定
[[tool.paladin.overrides]]
files = ["tests/**"]

[tool.paladin.overrides.rules]
require-all-export = false

[[tool.paladin.overrides]]
files = ["scripts/**"]

[tool.paladin.overrides.rules]
no-relative-import = false
require-qualified-third-party = false
```

最小限の設定例。

```toml
[tool.paladin.rule."require-qualified-third-party"]
root-packages = ["myapp"]
```

この例では、全ルールが有効（デフォルト）のまま、`require-qualified-third-party` のルートパッケージだけを設定しています。

## 8. 既存 Ignore 設計との統合

### 8.1 設定ファイル構造の全体像

Ignore 設計（`docs/design/ignore.md`）で定義された `per-file-ignores` と、本設計で定義する設定項目は、同じ `[tool.paladin]` セクション内に共存します。

```toml
[tool.paladin]
include = [...]                              # R-091: 解析対象パス
exclude = [...]                              # R-091: 除外パス

[tool.paladin.rules]                         # R-090: ルールの有効/無効
...

[tool.paladin.rule."<rule-id>"]              # R-092: ルール個別設定
...

[tool.paladin.per-file-ignores]              # Ignore 設計: パスパターン別の違反無視
...

[[tool.paladin.overrides]]                   # R-093: ディレクトリ別設定
...
```

### 8.2 設定の適用順序

設定ファイル内の各設定は、以下の順序で解決されます。

1. `exclude` でファイルを除外する
2. ルールの有効/無効を決定する（トップレベル → `overrides` で上書き）
3. 有効なルールに対して、ルール個別設定を適用する
4. ルール判定を実行する
5. `per-file-ignores` で違反を除外する
6. CLI `--ignore-rule` で違反を除外する

### 8.3 使い分けの指針

設定方式の使い分けを以下に示します。

- テストディレクトリで `require-all-export` を最初から適用しない場合は `[[tool.paladin.overrides]]` を使う
- テストの特定ファイルで例外的に違反を許容したい場合は `per-file-ignores` を使う
- 広範囲のルール無効化には `overrides` が適する。少数の例外的な許容には `per-file-ignores` が適する

## 9. 既存 Linter との比較

### 9.1 設定方式の比較表

| 設定項目 | Ruff | mypy | Pyright | **Paladin** |
|---------|------|------|---------|---------|
| ルール ON/OFF | `select` / `ignore` リスト | 個別設定を bool | 診断レベルを文字列 | `[tool.paladin.rules]` で bool |
| 解析対象 | `include` / `exclude` リスト | `files` / `exclude` | `include` / `exclude` | `include` / `exclude` リスト |
| ルール個別設定 | `[tool.ruff.lint.<category>]` | 個別キー | 個別キー | `[tool.paladin.rule."<id>"]` |
| ディレクトリ別 | ネストした `ruff.toml` | `[[tool.mypy.overrides]]` | `executionEnvironments` | `[[tool.paladin.overrides]]` |
| per-file-ignores | `[tool.ruff.lint.per-file-ignores]` | `overrides` で代替 | なし | `[tool.paladin.per-file-ignores]` |
| `extend-*` 系 | あり | なし | なし | **なし** |

### 9.2 設計判断の根拠

| 判断 | 根拠 |
|------|------|
| `select` / `ignore` ではなく bool 方式 | ルール数が少なく、個別に有効/無効を指定する方が明確である |
| `extend-*` 系を導入しない | ルール数が少なく、ベースセットの概念が不要である |
| mypy 方式の `overrides` を採用 | 1ファイルで完結し、ネストした設定ファイルの複雑さを避けられる |
| Ruff / Pyright と同じ `include` / `exclude` 命名 | Python エコシステムで広く使われており、学習コストが低い |
| `overrides` は後勝ち方式 | 最終的にどの設定が有効かを予測しやすい |

## 10. 将来拡張

現時点で導入しないが、将来対応を想定するものを示します。

### 10.1 `paladin.toml` 独立設定ファイル

Ignore 設計で予約済みです。`paladin.toml` が存在する場合、`pyproject.toml` の `[tool.paladin]` より優先します。`paladin.toml` ではトップレベルの `[paladin]` プレフィックスは不要です。

```toml
# paladin.toml（将来拡張）
include = ["src/"]

[rules]
no-relative-import = false

[rule."require-qualified-third-party"]
root-packages = ["myapp"]
```

### 10.2 CLI からの設定ファイルパス指定

```text
uv run paladin check src/ --config path/to/pyproject.toml
```

### 10.3 ルール重大度の制御

ルールの違反を `error` / `warning` / `off` で制御する方式です。現在の `true` / `false` を拡張する形で導入できます。

```toml
[tool.paladin.rules]
no-relative-import = "warning"   # 将来拡張
```

現時点では全ルールの違反が等しく「違反」として扱われるため、重大度の区別は不要です。

### 10.4 設定のバリデーションコマンド

```text
uv run paladin config validate
```

設定ファイルの構文チェックと、存在しないルール ID への参照の検出を行うコマンドです。

### 10.5 `overrides` でのルール個別設定

`[[tool.paladin.overrides]]` 内でルール個別設定（`rule` サブセクション）を上書きする機能は、将来の必要性に応じて追加します。初期実装では `rules`（有効/無効）のみを対象とします。

## 11. ロードマップとの対応

本設計は、既存ロードマップの以下の項目に対応します。

| ロードマップ項目 | 本設計での対応 |
|----------------|-------------|
| R-090 ルール ON/OFF の設定ファイル実装 | セクション3（`[tool.paladin.rules]` で bool 方式） |
| R-091 解析対象パスの include/exclude 実装 | セクション4（`include` / `exclude` リスト） |
| R-092 ルール個別設定の実装 | セクション5（`[tool.paladin.rule."<rule-id>"]` セクション） |
| R-093 ディレクトリ別設定の実装 | セクション6（`[[tool.paladin.overrides]]` 配列テーブル） |

実装順序としては R-090（ルール ON/OFF）→ R-092（ルール個別設定）→ R-091（include/exclude）→ R-093（overrides）が自然です。R-090 が設定ファイル読み込みの基盤を構築し、R-092 は既存のハードコード（`root_packages`）を設定ファイルに移行する実用的な価値が高いためです。R-091 と R-093 はそれぞれ独立した機能であり、R-090 の基盤の上に構築します。

なお、R-082（設定ファイルによる全体 Ignore）で `pyproject.toml` の読み込み基盤が先に構築される前提であり、R-090 以降はその基盤を再利用します。
