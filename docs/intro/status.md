# Paladin 実装ステータス

## 現在地

- Active milestone: M4 (ルール資産の拡充)
- Current item: R-081
- Updated: 2026-03-14

## 状態一覧

| ID | タイトル | 状態 | 備考 |
| --- | --- | --- | --- |
| R-000 | 契約モデルを定義する | Done | |
| R-010 | Python ファイルを再帰列挙する | Done | |
| R-020 | AST を生成する | Done | |
| R-030 | ルール実行基盤を作る | Done | コミット 7526a43 |
| R-040 | `check` コマンドの text 出力と終了コードを実装する | Done | |
| R-050 | `no-relative-import` を実装する | Done | |
| R-051 | 単一ファイルルールを追加する (2本目) | Done | no-local-import |
| R-052 | 単一ファイルルールを追加する (3本目) | Done | require-qualified-third-party |
| R-060 | `rules` コマンドの最小実装 | Done | |
| R-061 | `version` コマンドの実装 | Done | |
| R-062 | `rules --rule <RULE_ID>` の対応 | Done | |
| R-065 | `rules --rule` の詳細出力を拡張する | Done | |
| R-070 | `--format json` を正式対応する | Done | |
| R-080 | ファイル単位の Ignore を実装する | Done | |
| R-081 | 直前コメントによる Ignore を実装する | Done | |
| R-082 | 設定ファイルによる全体 Ignore を実装する | Not Started | |
| R-083 | ディレクトリ単位の Ignore を実装する | Not Started | |
| R-090 | ルール ON/OFF の設定ファイルを実装する | Not Started | |
| R-091 | 解析対象パスの include/exclude を実装する | Not Started | |
| R-092 | ルール個別設定を実装する | Not Started | `root_packages` の上書き。デフォルト値は R-094 |
| R-093 | ディレクトリ別設定を実装する | Not Started | |
| R-094 | `root_packages` のデフォルト値を動的に取得する | Not Started | 現在は Provider でハードコード暫定対応済み |
| R-100 | 複数ファイル解析基盤と `no-direct-internal-import` を実装する | Not Started | |
| R-103 | 広域解析時のエラーハンドリングを設計する | Not Started | |
| R-110 | `suggestion` の品質を高める | Not Started | |
| R-111 | AI 向け修正指示文を整備する | Not Started | |
| R-112 | 限定的自動修正を検討・導入する | Not Started | |
