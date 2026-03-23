# 設定ファイルインターフェイス設計

## 1. この文書の目的

この文書は、Paladin の設定ファイル（`pyproject.toml` の `[tool.paladin]` セクション）について **ユーザー向けインターフェイス** を定義するものである。ここでいう「ユーザー」とは、主に生成 AI と、補助的に人間の開発者を指す。

定義する内容は以下の通りである。

- ルールの有効化・無効化の書式と仕様
- 解析対象パスの include/exclude の書式と仕様
- ルール個別設定の書式と仕様
- ディレクトリ別設定の書式と仕様
- 各設定項目間の関係と適用順序
- 既存の Ignore 設計との統合方針

定義しない内容は以下の通りである。

- 設定ファイルの読み込みモジュールの内部アーキテクチャ
- 設定値のバリデーション実装方式
- CLI オプションとの優先順序の詳細な解決アルゴリズム
- `paladin.toml` 独立設定ファイルの仕様

## 2. 設計方針

### 2.1 全体方針

設定ファイルのインターフェイスは以下の方針に従って設計する。

- **明示的であること**: 暗黙の挙動を避け、設定の意味が読んで分かる
- **最小限であること**: Paladin のルール数は少なく個人用ツールであるため、過度な汎用性よりシンプルさを優先する
- **AI が安定して扱えること**: 書式が単純で、生成 AI が正確に生成・解釈できる
- **既存 Linter ユーザーが直感的に使えること**: Python エコシステムの慣例に沿った設計にする

### 2.2 既存 Linter から学んだこと

主要 Linter の設定インターフェイスを調査した結果、以下の知見を得た。

- **Ruff の `extend-*` パターンは強力だが複雑**: `select` / `extend-select` / `ignore` / `extend-ignore` の組み合わせは、ルール数が多い汎用 Linter では有用だが、Paladin のように少数のルールを扱うツールでは不要な複雑さになる
- **mypy の `[[tool.mypy.overrides]]` はディレクトリ別設定に適する**: 1つの設定ファイル内で完結し、TOML の配列テーブルとして自然に表現できる
- **Ruff / Pyright の `include` / `exclude` は直感的**: 解析対象パスの制御として広く理解されており、同じ命名を採用することで学習コストを下げられる
- **Ruff のルール個別設定はサブセクション方式**: `[tool.ruff.lint.pydocstyle]` のようにルールごとのサブセクションを使う方式は、TOML の構造と相性が良い

### 2.3 Paladin 固有の判断

Paladin の特性に基づき、以下の設計判断を行う。

- **全ルールがデフォルトで有効**: Paladin のルール数は少なく、すべてのルールに実用的な価値がある。設定ファイルは「一部を無効化する」ために使う
- **`extend-*` 系は導入しない**: ルール数が少なく個人用であるため、`extend-select` / `extend-ignore` / `extend-exclude` は不要な複雑さを持ち込む
- **ディレクトリ別設定はネストした設定ファイルではなく、1つの `pyproject.toml` 内で完結する**: mypy の `[[tool.mypy.overrides]]` パターンを参考にする
- **ルールの有効/無効は `true` / `false` で指定する**: Ruff のように `select` / `ignore` リストで管理する方式は採用しない。ルール数が少ないため、各ルールの状態を個別に宣言する方が一目で分かりやすく、`select` と `ignore` の優先順序による混乱も生じない

## 3. ルールの有効化・無効化

### 3.1 セクション名

```toml
[tool.paladin.rules]
```

### 3.2 書式

各ルール ID をキーとし、`true`（有効）/ `false`（無効）の真偽値を指定する。

```toml
[tool.paladin.rules]
no-relative-import = false
no-local-import = false
```

### 3.3 デフォルト

- 全ルールがデフォルトで有効である
- `[tool.paladin.rules]` セクションが存在しない場合、全ルールが有効として動作する
- セクション内に記載されていないルールも有効として扱う

この方式は「明示的に無効化したルールだけを書く」というシンプルな運用になる。ルール数が少ない Paladin では、有効なルールを列挙するよりも、無効化するルールだけを書く方が簡潔である。

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

## 4. 解析対象パスの制御

### 4.1 書式

`[tool.paladin]` セクション直下に `include` と `exclude` をリストとして定義する。

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
| 指定なし | 未指定 | `src/` / `tests/` が存在すればフォールバック、いずれも存在しなければエラー |

`exclude` は上記のいずれの場合にも適用される。

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

デフォルトの `exclude` リスト（`.git`, `.venv` など）は設けない。Paladin は CLI の `TARGET` 引数で解析対象を明示的に指定する運用を基本としており、暗黙の除外リストは混乱を招く可能性があるためである。

## 5. ルール個別設定

### 5.1 セクション名

```toml
[tool.paladin.rule.<rule-id>]
```

ルール ID はハイフン区切りの名前であるが、TOML v1.0 ではハイフンがベアキーに使用可能であるため、クォートは不要である。

### 5.2 書式

ルール固有のパラメータをキー・値の形式で指定する。

```toml
[tool.paladin.rule.<rule-id>]
param-name = value
```

### 5.3 現在のルール個別設定

以下のルールが個別設定を持っている。

| ルール ID | パラメータ | 型 | 説明 |
|-----------|-----------|-----|------|
| `no-third-party-import` | `allow-dirs` | 文字列の配列 | サードパーティインポートを許可するディレクトリ |
| `no-cross-package-import` | `allow-dirs` | 文字列の配列 | パッケージ間インポートを許可するディレクトリ |
| `max-method-length` | `max-lines` | 整数 | メソッドの最大行数 |
| `max-method-length` | `max-test-lines` | 整数 | テストメソッドの最大行数 |
| `max-class-length` | `max-lines` | 整数 | クラスの最大行数 |
| `max-class-length` | `max-test-lines` | 整数 | テストクラスの最大行数 |
| `max-file-length` | `max-lines` | 整数 | ファイルの最大行数 |
| `max-file-length` | `max-test-lines` | 整数 | テストファイルの最大行数 |

具体例を示す。

```toml
[tool.paladin.rule.no-third-party-import]
allow-dirs = ["src/paladin/foundation/", "src/paladin/transform/", "tests/", "e2e-tests/"]

[tool.paladin.rule.no-cross-package-import]
allow-dirs = ["src/paladin/foundation/", "src/paladin/protocol/", "src/paladin/rule/"]

[tool.paladin.rule.max-method-length]
max-lines = 100
max-test-lines = 100

[tool.paladin.rule.max-class-length]
max-lines = 225
max-test-lines = 800
```

### 5.4 仕様の詳細

- 各ルールが受け付けるパラメータは、そのルールの仕様で定義される
- 存在しないルール ID をセクション名に使用した場合、警告を出力して無視する
- ルールが認識しないパラメータが含まれている場合、警告を出力して無視する
- パラメータ名は TOML の慣例に従いハイフン区切り（kebab-case）とする。Python 側のフィールド名（snake_case）との変換は実装層が担当する

### 5.5 `[tool.paladin.rules]` との関係

`[tool.paladin.rules]` はルールの有効/無効を制御し、`[tool.paladin.rule.<rule-id>]` はルールの挙動パラメータを制御する。両者は独立した設定である。

- `[tool.paladin.rules]` でルールを `false` にしている場合、そのルールの設定は読み込まれるが適用されない
- `[tool.paladin.rule.<rule-id>]` を定義しても、そのルールは自動的に有効にはならない（デフォルトで有効であるため）

## 6. ディレクトリ別設定

### 6.1 方式の選択

2.3 節の方針に従い、mypy の `[[tool.mypy.overrides]]` パターンを参考にした TOML 配列テーブル（`[[...]]`）を使用する。

### 6.2 セクション名

```toml
[[tool.paladin.overrides]]
```

### 6.3 書式

各オーバーライドエントリは `files` キーで対象パスパターンを指定し、そのスコープ内でルールの有効/無効を上書きする。

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

前のオーバーライドの設定は引き継がれない。意図した通りに動作させるには、より具体的なオーバーライドに必要な設定をすべて含める必要がある。

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

スクリプトディレクトリでルールを緩和する場合。

```toml
[[tool.paladin.overrides]]
files = ["scripts/**"]

[tool.paladin.overrides.rules]
no-relative-import = false
require-qualified-third-party = false
```

## 7. Ignore 設計との統合

### 7.1 設定ファイル構造の全体像

Ignore 設計（`docs/design/ignore.md`）で定義された `per-file-ignores` と、本設計で定義する設定項目は、同じ `[tool.paladin]` セクション内に共存する。

```toml
[tool.paladin]
include = [...]                              # 解析対象パス
exclude = [...]                              # 除外パス

[tool.paladin.rules]                         # ルールの有効/無効
...

[tool.paladin.per-file-ignores]              # Ignore 設計: パスパターン別の違反無視
...

[[tool.paladin.overrides]]                   # ディレクトリ別設定
...
```

### 7.2 設定の適用順序

設定ファイル内の各設定は、以下の順序で解決される。

1. `exclude` でファイルを除外する
2. ルールの有効/無効を決定する（トップレベル → `overrides` で上書き）
3. 有効なルールに対してルール判定を実行する
4. `per-file-ignores` で違反を除外する
5. CLI `--ignore-rule` で違反を除外する

### 7.3 `per-file-ignores` と `overrides` の使い分け

| 設定 | 目的 | 効果 |
|------|------|------|
| `per-file-ignores` | 特定ファイルで特定ルールの **違反を無視** する | 違反は検出されるが報告されない |
| `[[tool.paladin.overrides]]` | 特定ディレクトリでルールを **無効化** する | ルール自体が適用されない |

使い分けの指針を以下に示す。

- テストディレクトリで `require-all-export` を最初から適用しない場合は `[[tool.paladin.overrides]]` を使う
- テストの特定ファイルで例外的に違反を許容したい場合は `per-file-ignores` を使う
- 広範囲のルール無効化には `overrides` が適する。少数の例外的な許容には `per-file-ignores` が適する

## 8. 設定ファイルの完全な例

全設定項目を含む実用的な例を示す。

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
[tool.paladin.rule.no-third-party-import]
allow-dirs = ["src/foundation/", "tests/"]

[tool.paladin.rule.max-file-length]
max-lines = 500
max-test-lines = 1000

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
[tool.paladin.rules]
no-relative-import = false
```

この例では、`no-relative-import` だけを無効化している。全ルールがデフォルトで有効なため、無効化したいルールのみ記述する。

## 9. 既存 Linter との比較

| 設定項目 | Ruff | mypy | Pyright | **Paladin** |
|---------|------|------|---------|---------|
| ルール ON/OFF | `select` / `ignore` リスト | 個別設定を bool | 診断レベルを文字列 | `[tool.paladin.rules]` で bool |
| 解析対象 | `include` / `exclude` リスト | `files` / `exclude` | `include` / `exclude` | `include` / `exclude` リスト |
| ルール個別設定 | `[tool.ruff.lint.<category>]` | 個別キー | 個別キー | `[tool.paladin.rule.<id>]` |
| ディレクトリ別 | ネストした `ruff.toml` | `[[tool.mypy.overrides]]` | `executionEnvironments` | `[[tool.paladin.overrides]]` |
| per-file-ignores | `[tool.ruff.lint.per-file-ignores]` | `overrides` で代替 | なし | `[tool.paladin.per-file-ignores]` |
| `extend-*` 系 | あり | なし | なし | **なし** |
