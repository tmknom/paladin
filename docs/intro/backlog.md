# バックログ

## 1. この文書の役割

他のイントロドキュメントで言及されているが、未実装の機能を一覧化した文書です。

## 2. CLI オプション

### check コマンド

| オプション | 出典 | 備考 |
|---|---|---|
| `--rule <RULE_ID>` | interface.md 4.3 | 特定ルールのみ実行する |
| `--exclude-rule <RULE_ID>` | interface.md 4.3 | 特定ルールを除外して実行する（`--ignore-rule` は違反を抑制するもので用途が異なる） |
| `--format ndjson` | interface.md 4.3 | text / json のみ対応済み |
| `--output <FILE>` | interface.md 4.3 | 結果をファイルに書き出す |
| `--summary` / `--no-summary` | interface.md 4.3 | サマリーは現在常に出力される |
| `--quiet` | interface.md 4.3 | 違反がない場合は出力を抑制する |
| `--verbose` | interface.md 4.3 | `--log-level` がグローバルオプションとして存在するため、必要性は低い可能性がある |

### list / view コマンド

| オプション | 出典 | 備考 |
|---|---|---|
| `list --format json` | interface.md 8.2 | text のみ対応済み |
| `view --format json` | interface.md 9.2 | text のみ対応済み |
