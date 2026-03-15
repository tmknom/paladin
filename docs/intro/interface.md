# Paladin CLI インターフェイス設計草案

## 1. 設計方針

本 CLI は、次の方針で設計する。

- 中核コマンドは `check` とする
- 出力は人間向け表示を持ちつつ、機械処理しやすい構造を重視する
- ルールを継続的に育てやすいよう、ルール一覧や個別説明を取得できる入口を持つ
- 初期スコープに必要な責務だけを前面に出し、将来拡張は余白として残す
- 自動修正や IDE 統合は CLI の責務に含めない

## 2. コマンド体系

初期草案では、以下のトップレベル構成を採用する。

```text
uv run paladin check [TARGET ...] [OPTIONS]
uv run paladin list [OPTIONS]
uv run paladin view <RULE_ID>
uv run paladin version
```

このうち、MVP の中心は `check` である。`list` / `view` は、診断結果を理解しやすくし、ルールを継続的に育てるための補助コマンドとして位置づける。

## 3. 各コマンドの役割

### 3.1 `check`

解析対象に対して静的解析を実行し、ルール違反を診断する主コマンド。

想定例:

```text
uv run paladin check src/
uv run paladin check src/foo.py
uv run paladin check src/ tests/test_bar.py
uv run paladin check src/ --rule PAL001 --rule PAL003
uv run paladin check src/ --exclude-rule PAL099
uv run paladin check src/ --format json
```

責務は次の通り。

- ファイルまたはディレクトリを対象に解析する
- 指定ルール群に基づいて違反を検出する
- 結果を構造化された診断情報として返す
- 実行結果を機械的に判別できる状態で返す

### 3.2 `list`

利用可能なルールの一覧を表示するコマンド。

想定例:

```text
uv run paladin list
uv run paladin list --format json
```

責務は次の通り。

- ルール ID とルール名の一覧を返す
- 必要に応じて、各ルールの概要や対象範囲を返す
- AI や人間が「今どのルールが有効な世界か」を確認できるようにする

### 3.3 `view`

指定したルールの詳細情報を表示するコマンド。

想定例:

```text
uv run paladin view PAL001
```

責務は次の通り。

- 指定された単一ルールの詳細情報を返す
- ルール ID・ルール名・概要・対象範囲など、ルールを理解するための情報を提供する
- AI や人間が特定ルールの意図や適用条件を確認できるようにする

### 3.4 `version`

バージョン情報を返すコマンド。

想定例:

```text
uv run paladin version
```

責務は単純である。

- 実行中の Paladin のバージョンを返す
- 将来的には出力フォーマットのバージョンや互換性情報を併記できるようにする

## 4. `check` コマンドの詳細草案

### 4.1 基本構文

```text
uv run paladin check [TARGET ...] [OPTIONS]
```

`TARGET` は 1 個以上のファイルまたはディレクトリを受け付ける。

例:

```text
uv run paladin check src/
uv run paladin check src/foo.py tests/test_bar.py
```

### 4.2 オプション草案

```text
--rule <RULE_ID>
--exclude-rule <RULE_ID>
--format <text|json|ndjson>
--output <FILE>
--summary
--no-summary
--quiet
--verbose
```

### 4.3 各オプションの意味

#### `--rule <RULE_ID>`

適用ルールを明示的に限定する。複数回指定可能とする。

```text
uv run paladin check src/ --rule PAL001 --rule PAL003
```

用途は次の通り。

- 新規ルールを単体で試す
- AI が特定観点だけ再確認する
- 誤検出調査時に対象を絞る

#### `--exclude-rule <RULE_ID>`

指定ルールを解析対象から除外する。複数回指定可能とする。

```text
uv run paladin check src/ --exclude-rule PAL099
```

初期要件の必須ではないが、実運用では有用性が高い。特定ルールの一時無効化や比較検証に使いやすい。

#### `--format <text|json|ndjson>`

出力形式を指定する。

- `text`: 人間のローカル確認向け
- `json`: AI や他ツール連携向け
- `ndjson`: ストリーム処理や行単位処理向け

Paladin は生成 AI が主要利用者であり、構造化出力が中核要件であるため、`json` を第一級の形式として扱うべきである

#### `--output <FILE>`

出力結果をファイルに保存する。

```text
uv run paladin check src/ --format json --output .paladin/result.json
```

用途は次の通り。

- CI 的な利用
- AI が後続処理で読み込む
- 違反履歴の比較検証

#### `--summary` / `--no-summary`

出力末尾または出力全体に、集計情報を含めるかを制御する。

集計情報としては、少なくとも次を表現できるようにする。

- 総違反件数
- ルール別違反件数
- ファイル別違反件数
- 実行結果の要約

これは要件に明示されている

#### `--quiet`

最小限の出力に抑える。主として終了コードや簡易結果だけを使いたい場面向け。

#### `--verbose`

処理対象数、適用ルール一覧、処理時間など、補助的情報を増やす。ただし診断本体の意味や構造は変えない。

## 5. `check` の出力契約

### 5.1 実行結果の状態

`check` の実行結果は、少なくとも以下の 3 状態を区別できるようにする。

- 違反なし
- 違反あり
- 実行失敗

これは要件上の必須事項であり、生成 AI や他の自動処理が機械的に判別できる必要がある

### 5.2 終了コード草案

終了コードは次のように固定する。

```text
0 = 違反なし
1 = 違反あり
2 = 実行失敗
```

この仕様は単純で、AI やシェルから扱いやすい。初期段階では、これをオプションで切り替え可能にはしないほうがよい。契約を固定したほうが、診断器としての安定性が高い。

### 5.3 各診断に含める情報

各違反診断には、少なくとも次の情報を含める。

- 対象ファイル
- 行番号
- 必要に応じて列番号
- ルール識別子
- ルール名
- 違反概要
- 違反理由
- 修正の方向性

これは要件に一致する

### 5.4 出力全体に含める情報

出力全体として、少なくとも次を表現できるようにする。

- 総違反件数
- ルール別違反件数
- ファイル別違反件数
- 実行結果の要約

これも要件に一致する

## 6. JSON 出力のイメージ

正式仕様ではなく、インターフェイス草案としてのイメージは次の通り。

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
      "column": 1,
      "rule_id": "PAL001",
      "rule_name": "public-boundary",
      "message": "非公開要素が公開境界に含まれています",
      "reason": "公開 API の意図が曖昧になり、利用側の依存が不安定になるためです",
      "suggestion": "公開対象を明確にするか、公開境界から除外してください"
    }
  ]
}
```

ポイントは次の通り。

- `status` は必須
- `summary` は機械集計しやすい構造を持つ
- `diagnostics` は局所的で、修正可能な粒度で返す
- `message` だけで終わらず、`reason` と `suggestion` を持つ

これは、Paladin が単なる違反表示ではなく、修正のための入力を返す診断器であるという基本思想に沿う

## 7. text 出力のイメージ

人間向け表示は補助的な位置づけとしつつ、最低限読みやすい形は持たせる。

```text
src/foo.py:10:1 PAL001 public-boundary
  概要: 非公開要素が公開境界に含まれています
  理由: 公開 API の意図が曖昧になり、利用側の依存が不安定になるためです
  修正方向: 公開対象を明確にするか、公開境界から除外してください

Summary:
  status: violations
  total: 3
  by_rule: PAL001=2, PAL003=1
  by_file: src/foo.py=2, src/bar.py=1
```

ただし、主契約はあくまで構造化出力側に置く。

## 8. `list` コマンドの出力草案

### 8.1 text 例

```text
PAL001  public-boundary        公開境界に関するルール
PAL002  import-direction       import 方向に関するルール
PAL003  declaration-order      宣言順に関するルール
```

### 8.2 json 例

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

## 9. `view` コマンドの出力草案

### 9.1 text 例

```text
PAL001  public-boundary
  概要: 公開境界に関するルール
  対象: モジュール・パッケージの公開インターフェイス定義
  説明: 非公開要素が公開境界に含まれていないかを検査する
```

### 9.2 json 例

```json
{
  "rule_id": "PAL001",
  "rule_name": "public-boundary",
  "summary": "公開境界に関するルール",
  "target": "モジュール・パッケージの公開インターフェイス定義",
  "description": "非公開要素が公開境界に含まれていないかを検査する"
}
```

## 10. 初期リリースに含める範囲

初期リリースでは、次を含めるのが妥当である。

- `check`
- `list`
- `view`
- `version`

理由は次の通り。

- 必須要件の中心は `check` に集約されている
- ルールを継続的に育てる運用上、`list` / `view` は早期に価値がある

## 11. 初期リリースで入れないもの

初期段階では、次は CLI の前面に出さない。

- `fix`
- `serve`
- `lsp`
- `watch`
- `baseline`
- `ignore`
- `config validate`

理由は次の通り。

- 自動修正はスコープ外である
- IDE/LSP はスコープ外である
- 例外許容や設定ファイル管理は将来拡張である
- 初期価値は「安定した診断器」であり、周辺機能は後回しでよい

この判断は、Paladin が最初から完成形を目指すのではなく、小さく始めて段階的に育てる前提に沿っている

## 12. 最終提案

現時点のインターフェイス設計草案としては、以下を推奨する。

```text
uv run paladin check [TARGET ...]
  [--rule <RULE_ID> ...]
  [--exclude-rule <RULE_ID> ...]
  [--format <text|json|ndjson>]
  [--output <FILE>]
  [--summary | --no-summary]
  [--quiet]
  [--verbose]

uv run paladin list
  [--format <text|json>]

uv run paladin view <RULE_ID>

uv run paladin version
```

終了コードは次の固定仕様とする。

```text
0 = 違反なし
1 = 違反あり
2 = 実行失敗
```

この草案は、Paladin の中核価値である「生成 AI が扱いやすい設計ルール診断器」という位置づけと整合しており、初期スコープを守りつつ、将来の拡張余地も残せる構成です

次は、この草案をベースに「CLI 仕様書っぽい体裁」に整えて、コマンドごとの入出力契約をもう少し厳密に書き下ろすのがよいです。
