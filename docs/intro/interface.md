# Paladin CLI インターフェイス

本文書は [基本方針](concept.md) および [全体仕様](specifications.md) を前提とし、実装済み CLI インターフェイスの仕様を記述します。

## 1. コマンド体系

```text
uv run paladin check [TARGET ...] [OPTIONS]
uv run paladin list [OPTIONS]
uv run paladin view <RULE_ID> [OPTIONS]
uv run paladin version
```

`check` が主コマンドです。`list` / `view` は、診断結果を理解しやすくし、ルールを継続的に育てるための補助コマンドとして位置づけます。

## 2. グローバルオプション

全コマンドで共通して使用できるオプションです。

| オプション | デフォルト | 説明 |
|---|---|---|
| `--log-level <LEVEL>` | `WARNING` | ログレベルを指定する（`CRITICAL` / `ERROR` / `WARNING` / `INFO` / `DEBUG`） |

```text
uv run paladin --log-level DEBUG check src/
```

## 3. check コマンド

解析対象に対して静的解析を実行し、ルール違反を診断する主コマンドです。

### 3.1 構文

```text
uv run paladin check [TARGET ...] [OPTIONS]
```

`TARGET` は 1 個以上のファイルまたはディレクトリを受け付けます。省略した場合は設定ファイルの `include` に従います。

```text
uv run paladin check src/
uv run paladin check src/foo.py tests/test_bar.py
```

### 3.2 オプション

| オプション | デフォルト | 説明 |
|---|---|---|
| `--format <text\|json>` | `text` | 出力形式を指定する |
| `--ignore-rule <RULE_ID>` | なし | 指定ルールの違反を抑制する（複数回指定可） |

```text
uv run paladin check src/ --format json
uv run paladin check src/ --ignore-rule PAL001 --ignore-rule PAL003
```

### 3.3 text 出力

```text
src/foo.py:10:0 PAL001 public-boundary
  概要: 非公開要素が公開境界に含まれています
  理由: 公開 API の意図が曖昧になり、利用側の依存が不安定になるためです
  修正方向: 公開対象を明確にするか、公開境界から除外してください

Summary:
  status: violations
  total: 3
  by_rule: PAL001=2, PAL003=1
  by_file: src/foo.py=2, src/bar.py=1
```

#### 違反がない場合

```text
Summary:
  status: ok
  total: 0
```

### 3.4 JSON 出力

```json
{
  "status": "violations",
  "summary": {
    "total_violations": 3,
    "by_rule": {
      "PAL001": 2,
      "PAL003": 1
    },
    "by_file": {
      "src/foo.py": 2,
      "src/bar.py": 1
    }
  },
  "diagnostics": [
    {
      "file": "src/foo.py",
      "line": 10,
      "column": 0,
      "rule_id": "PAL001",
      "rule_name": "public-boundary",
      "message": "非公開要素が公開境界に含まれています",
      "reason": "公開 API の意図が曖昧になり、利用側の依存が不安定になるためです",
      "suggestion": "公開対象を明確にするか、公開境界から除外してください"
    }
  ]
}
```

#### 違反がない場合

```json
{
  "status": "ok",
  "summary": {
    "total_violations": 0,
    "by_rule": {},
    "by_file": {}
  },
  "diagnostics": []
}
```

違反の有無にかかわらず `summary` の全フィールドを出力します。

## 4. list コマンド

利用可能なルールの一覧を表示するコマンドです。

### 4.1 構文

```text
uv run paladin list [OPTIONS]
```

### 4.2 オプション

| オプション | デフォルト | 説明 |
|---|---|---|
| `--format <text\|json>` | `text` | 出力形式を指定する |

### 4.3 text 出力

```text
PAL001  public-boundary        公開境界に関するルール
PAL002  import-direction       import 方向に関するルール
PAL003  declaration-order      宣言順に関するルール
```

rule_id と rule_name は最長に合わせて整列されます。

### 4.4 JSON 出力

```json
{
  "rules": [
    {
      "rule_id": "PAL001",
      "rule_name": "public-boundary",
      "summary": "公開境界に関するルール"
    },
    {
      "rule_id": "PAL002",
      "rule_name": "import-direction",
      "summary": "import 方向に関するルール"
    }
  ]
}
```

## 5. view コマンド

指定したルールの詳細情報を表示するコマンドです。

### 5.1 構文

```text
uv run paladin view <RULE_ID> [OPTIONS]
```

### 5.2 オプション

| オプション | デフォルト | 説明 |
|---|---|---|
| `--format <text\|json>` | `text` | 出力形式を指定する |

### 5.3 text 出力

```text
Rule ID:     PAL001
Name:        public-boundary
Summary:     公開境界に関するルール
Intent:      モジュールの公開 API を明確に定義する
Guidance:    非公開要素が公開境界に含まれていないかを検査する
Suggestion:  公開対象を明確にするか、公開境界から除外してください
```

### 5.4 JSON 出力

```json
{
  "rule_id": "PAL001",
  "rule_name": "public-boundary",
  "summary": "公開境界に関するルール",
  "intent": "モジュールの公開 API を明確に定義する",
  "guidance": "非公開要素が公開境界に含まれていないかを検査する",
  "suggestion": "公開対象を明確にするか、公開境界から除外してください"
}
```

### 5.5 エラー時の出力

存在しないルール ID を指定した場合、エラーメッセージを出力して終了コード `0` で終了します。

#### text 形式

```text
Error: Rule 'PAL999' not found.
```

#### JSON 形式

```json
{
  "error": "Error: Rule 'PAL999' not found."
}
```

## 6. version コマンド

パッケージのバージョン文字列を返すコマンドです。

### 6.1 構文

```text
uv run paladin version
```

#### 出力例

```text
0.1.0
```

## 7. 終了コード

全コマンド共通の終了コード体系です。

| 終了コード | 意味 |
|---|---|
| `0` | 正常終了（`check` は違反なし） |
| `1` | 違反あり（`check` のみ） |
| `2` | エラー（不正な引数、解析失敗、予期しない例外） |
