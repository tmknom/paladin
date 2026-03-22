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

想定される用途:

- 新規ルールを単体で試す
- AI が特定観点だけ再確認する
- 誤検出調査時に対象を絞る

### 3.2 --exclude-rule <RULE_ID>

指定ルールを解析対象から除外するオプションです。複数回指定可能とします。

```text
uv run paladin check src/ --exclude-rule PAL099
```

想定される用途:

- 特定ルールの一時無効化
- ルール適用前後の比較検証

`--ignore-rule` は違反を抑制するオプションであり、ルールそのものを実行対象から除外する本オプションとは用途が異なります。

### 3.3 --output <FILE>

出力結果をファイルに保存するオプションです。

```text
uv run paladin check src/ --format json --output .paladin/result.json
```

想定される用途:

- CI での実行結果の保存
- AI が後続処理で読み込む
- 違反履歴の比較検証

### 3.4 --quiet

最小限の出力に抑えるオプションです。主として終了コードや簡易結果だけを使いたい場面向けです。

## 4. 設定ファイルの機能

| 機能 | 備考 |
|---|---|
| `paladin.toml` 独立設定ファイル | `pyproject.toml` の `[tool.paladin]` より優先する |
| `--config` オプション | CLI から設定ファイルパスを指定する |
| ルール重大度の制御 | `true` / `false` を `"warning"` / `"error"` / `"off"` に拡張する |
| `paladin config validate` コマンド | 設定ファイルの構文チェックと未知ルール ID の検出 |
| `overrides` でのルール個別設定 | `[[tool.paladin.overrides]]` 内でルール個別設定を上書きする |

## 5. 各機能の詳細

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
