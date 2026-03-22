# バックログ

## 1. この文書の役割

実装が想定されているが、まだ実装されていない機能を一覧化した文書です。

## 2. check コマンドのオプション

| オプション | 備考 |
|---|---|
| `--rule <RULE_ID>` | 特定ルールのみ実行する |
| `--exclude-rule <RULE_ID>` | 特定ルールを除外して実行する（`--ignore-rule` は違反を抑制するもので用途が異なる） |
| `--output <FILE>` | 結果をファイルに書き出す |
| `--quiet` | 違反がない場合は出力を抑制する |

## 3. 各オプションの詳細

### 3.1 --rule <RULE_ID>

適用ルールを明示的に限定するオプションです。複数回指定可能とします。

```text
uv run paladin check src/ --rule PAL001 --rule PAL003
```

想定される用途

- 新規ルールを単体で試す
- AI が特定観点だけ再確認する
- 誤検出調査時に対象を絞る

### 3.2 --exclude-rule <RULE_ID>

指定ルールを解析対象から除外するオプションです。複数回指定可能とします。

```text
uv run paladin check src/ --exclude-rule PAL099
```

想定される用途

- 特定ルールの一時無効化
- ルール適用前後の比較検証

### 3.3 --output <FILE>

出力結果をファイルに保存するオプションです。

```text
uv run paladin check src/ --format json --output .paladin/result.json
```

想定される用途

- CI での実行結果の保存
- AI が後続処理で読み込む
- 違反履歴の比較検証

### 3.4 --quiet

最小限の出力に抑えるオプションです。違反がない場合は出力を抑制し、終了コードのみを返します。

```text
uv run paladin check src/ --quiet
```

想定される用途

- CI での成功/失敗判定のみ取得する
- スクリプトから終了コードを利用する

## 4. 設定ファイルの機能

| 機能 | 備考 |
|---|---|
| `paladin.toml` 独立設定ファイル | `pyproject.toml` の `[tool.paladin]` より優先する |
| `--config` オプション | CLI から設定ファイルパスを指定する |
| ルール重大度の制御 | `true` / `false` を `"warning"` / `"error"` / `"off"` に拡張する |
| `paladin config validate` コマンド | 設定ファイルの構文チェックと未知ルール ID の検出 |
| `overrides` でのルール個別設定 | `[[tool.paladin.overrides]]` 内でルール個別設定を上書きする |

## 5. 各設定機能の詳細

### 5.1 paladin.toml 独立設定ファイル

`paladin.toml` が存在する場合、`pyproject.toml` の `[tool.paladin]` より優先します。`paladin.toml` ではトップレベルの `[paladin]` プレフィックスは不要です。

```toml
# paladin.toml
include = ["src/"]

[rules]
no-relative-import = false
```

### 5.2 --config オプション

設定ファイルのパスを CLI から指定するオプションです。

```text
uv run paladin check src/ --config path/to/pyproject.toml
```

### 5.3 ルール重大度の制御

ルールの違反を `"error"` / `"warning"` / `"off"` で制御する方式です。現在の `true` / `false` を拡張する形で導入できます。

```toml
[tool.paladin.rules]
no-relative-import = "warning"
```

### 5.4 設定のバリデーションコマンド

設定ファイルの構文チェックと、存在しないルール ID への参照の検出を行うコマンドです。

```text
uv run paladin config validate
```

### 5.5 overrides でのルール個別設定

`[[tool.paladin.overrides]]` 内でルール個別設定（`rule` サブセクション）を上書きする機能です。

```toml
[[tool.paladin.overrides]]
files = ["tests/"]

[tool.paladin.overrides.rules]
max-file-length = false
```

## 6. Ignore 機能の拡張

| 機能 | 備考 |
|---|---|
| 行末コメント | `code  # paladin: ignore[rule-id]` 形式 |
| ブロック単位の disable/enable | `# paladin: disable` / `# paladin: enable` ペア |
| 理由コメント | `-- 理由` 形式による Ignore 理由の記録 |
| 未使用 Ignore 検出ルール | 不要な Ignore コメントを検出する `unused-ignore` ルール |

## 7. 各 Ignore 機能の詳細

### 7.1 行末コメント

直前コメント（`# paladin: ignore[rule-id]`）の行末バリアントです。

```python
violating_code_here  # paladin: ignore[rule-id]
```

行末コメントを採用しなかった理由は以下の通りです。

- Paladin のルール ID はハイフン区切りの名前であり、行末に付けると行が過度に長くなる
- 直前コメント方式は、コメントと対象行が明確に分離されるため AI が生成・解釈しやすい
- ESLint の `eslint-disable-next-line` や Pylint の `disable-next`（2.10+）でも直前コメント方式が確立されており、実績がある

### 7.2 ブロック単位の disable/enable

複数行をまとめて Ignore するためのブロック単位制御です。

```python
# paladin: disable[no-relative-import]
from . import module_a
from . import module_b
# paladin: enable[no-relative-import]
```

`ignore` ではなく `disable` / `enable` を使うのは、行指向の `ignore` とブロック指向の制御を意味的に区別するためです。

### 7.3 理由コメント

ESLint の `-- 理由` 形式に相当する機能です。Ignore の理由をコメントとして記録できます。

```python
# paladin: ignore[no-relative-import] -- レガシーコードのため一時的に許可
from . import legacy
```

### 7.4 未使用 Ignore 検出ルール

実際には違反が発生していないルールに対する Ignore コメント（未使用 Ignore）を検出する機能です。Ruff の `RUF100` や ESLint の `reportUnusedDisableDirectives` に相当します。専用ルール（仮称: `unused-ignore`）として実装する想定です。
