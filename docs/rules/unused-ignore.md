# unused-ignore

## メタ情報

| 項目 | 値 |
|------|-----|
| ルールID | unused-ignore |
| 対象 | 単一ファイル |

## 概要

ルール ID を指定した Ignore コメントのうち、対応する違反が実際には存在しないものを検出するルールです。`# paladin: ignore[rule-id]` および `# paladin: ignore-file[rule-id]` を対象とします。

## 背景と意図

コードを修正して違反が解消された後も、Ignore コメントが残存するケースがあります。こうした未使用の Ignore コメントは以下の問題を引き起こします。

- **コードの可読性の低下** — Ignore コメントは「この行には意図的な違反がある」というシグナルです。実際には違反がないにもかかわらず Ignore コメントが存在すると、読み手は存在しない問題を探し続ける
- **保守コストの増大** — 違反を修正するたびに Ignore コメントを手動で削除しなければ、コードベース全体に不要な Ignore コメントが蓄積する
- **ルール ID の誤記の見落とし** — `# paladin: ignore[no-relativ-import]` のようなタイポは、違反を抑制せずに残り続ける。未使用 Ignore を検出することで誤記を早期に発見できる
- **Ignore 機構の信頼性の低下** — 不要な Ignore コメントが多いと、正当な Ignore コメントも形式的なものとみなされ、Ignore 全体の信頼性が下がる

未使用の Ignore コメントを検出することで、Ignore コメントが「実際に抑制すべき違反が存在する」という意味を常に持つようになります。

## 診断メッセージ

### インライン Ignore が未使用の場合

| フィールド | 内容 |
|-----------|------|
| message | `# paladin: ignore` コメントで指定されたルール `{rule_id}` は、対象行で違反を検出していません |
| reason | 未使用の Ignore コメントはコードの可読性を低下させ、存在しない違反があるという誤解を招きます |
| suggestion | 不要なルール ID `{rule_id}` を Ignore コメントから削除してください |

### ファイル単位 Ignore が未使用の場合

| フィールド | 内容 |
|-----------|------|
| message | `# paladin: ignore-file` コメントで指定されたルール `{rule_id}` は、ファイル内で違反を検出していません |
| reason | 未使用の Ignore コメントはコードの可読性を低下させ、存在しない違反があるという誤解を招きます |
| suggestion | 不要なルール ID `{rule_id}` を Ignore コメントから削除してください |

## 検出パターン

### 違反コード

```python
# 違反パターン1: インライン Ignore にルール違反が存在しない
# paladin: ignore[no-relative-import]  # 違反: 次行に no-relative-import の違反がない
from mypackage import utils
```

```python
# 違反パターン2: ファイル単位 Ignore にルール違反が存在しない
# paladin: ignore-file[no-relative-import]  # 違反: ファイル内に no-relative-import の違反がない
"""モジュールのdocstringです。"""

from mypackage import utils
```

```python
# 違反パターン3: 複数ルール指定のうち一部が未使用
# paladin: ignore[no-relative-import, require-all-export]  # 違反: require-all-export の違反がない
from . import sibling  # no-relative-import の違反は存在するが require-all-export は違反しない
```

```python
# 違反パターン4: ルール ID のタイポ（違反を抑制していない）
# paladin: ignore[no-relativ-import]  # 違反: 存在しないルール ID のため違反を抑制できていない
from . import sibling
```

### 準拠コード

```python
# 準拠: インライン Ignore の次行に実際の違反が存在する
# paladin: ignore[no-relative-import]  # 準拠: 次行に no-relative-import の違反がある
from . import sibling
```

```python
# 準拠: ファイル単位 Ignore の対象ルールがファイル内に存在する
# paladin: ignore-file[no-relative-import]  # 準拠: ファイル内に no-relative-import の違反がある
"""モジュールのdocstringです。"""

from . import sibling
from . import utils
```

```python
# 準拠: ルール ID を指定しないワイルドカード Ignore は検出対象外
# paladin: ignore  # 準拠: ワイルドカード Ignore は未使用かどうかを判定しない
from . import sibling
```

## 検出の補足

### 検出ロジック

1. ファイル内のすべての `# paladin: ignore[...]` コメントおよび `# paladin: ignore-file[...]` コメントを収集し、ルール ID と行番号を記録する
2. 他のすべてのルールを実行し、Ignore フィルタリング適用前の生の違反リストを取得する
3. インライン Ignore（`# paladin: ignore[rule-id]`）について、次行に該当ルール ID の違反が存在するか確認する
4. ファイル単位 Ignore（`# paladin: ignore-file[rule-id]`）について、ファイル内に該当ルール ID の違反が存在するか確認する
5. 対応する違反が存在しないルール ID を持つ Ignore コメントを違反として報告する
6. ルール ID を指定しないワイルドカード Ignore（`# paladin: ignore`）は検出対象外とする

### 適用範囲

解析対象のすべての `.py` ファイルを対象とします。テストファイルか否かを問いません。

### 報告の粒度

違反はルール ID 単位で報告します。`# paladin: ignore[rule-a, rule-b]` のうち `rule-a` のみが未使用の場合、`rule-a` について1件の違反を報告します。報告する行番号は、Ignore コメント自体の行番号とします。

### 検出の前提

このルールは他のすべてのルールが実行された後に評価します。Ignore フィルタリング適用前の生の違反リストを参照する必要があるため、チェックパイプラインの最終段階で動作します。無効化されたルールに対応する Ignore コメントは未使用とみなしません。

## 既存ツールとの関係

Ruff は `RUF100`（`unused-noqa`）として `# noqa` コメントの未使用を検出します。ただし `RUF100` の対象は Ruff 固有の `# noqa` 書式であり、Paladin の `# paladin: ignore` 書式は対象外です。

ESLint は `reportUnusedDisableDirectives` オプションで同等の機能を提供します。

Pylint には同等のルールはありません。

Paladin の `# paladin: ignore` 書式に対する未使用 Ignore 検出は他ツールではカバーされないため、Paladin で独自に提供します。
