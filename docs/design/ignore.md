# Ignore 機能インターフェイス設計

## 1. この文書の目的

この文書は、Paladin の Ignore 機能について **ユーザー向けインターフェイス** を定義するものである。ここでいう「ユーザー」とは、主に生成 AI と、補助的に人間の開発者を指す。

定義する内容は以下の通りである。

- インラインコメントによる Ignore の書式と仕様
- ファイル先頭コメントによるファイル単位 Ignore の書式と仕様
- 設定ファイルによる Ignore の書式と仕様（設定ファイルの基本方針を含む）
- CLI オプションによるルール除外の書式と仕様
- 各 Ignore 方式間の優先順序

定義しない内容は以下の通りである。

- Ignore 機能の内部実装方式（コメントの解析方法、フィルタリングパイプラインの設計など）
- 設定ファイルの読み込みモジュールの内部アーキテクチャ
- Ignore 以外の設定項目の詳細仕様（ルール ON/OFF、include/exclude など）
- ブロック単位の disable/enable（将来拡張として扱う）

## 2. 設計方針

### 2.1 全体方針

Ignore 機能は以下の方針に従って設計する。

- **明示的であること** — Ignore は暗黙の除外ではなく、コメントや設定として明示的に記述する
- **追跡可能であること** — どの Ignore がどのルールに影響しているかを事後に確認できる
- **AI が安定して扱えること** — 書式が単純で、生成 AI が正確に生成・解釈できる
- **段階的に導入できること** — 初期スコープでは最小限のインターフェイスを提供し、将来拡張で機能を追加する

### 2.2 Paladin 固有の考慮事項

Paladin のルール ID はハイフン区切りの名前（例: `require-all-export`）であり、Ruff のような短い英数字コード（例: `E501`）ではない。この特性から以下の判断を行う。

- コメント書式ではルール ID をそのまま使用する（別途短縮コードは設けない）
- ルール ID が長いため、行末コメントは将来拡張とし、初期スコープでは直前コメントのみを採用する
- 全ルール一括 Ignore はルール ID を省略する書式で実現する

### 2.3 初期スコープと将来拡張の境界

初期スコープに含めるもの。

- 直前コメントによる行単位 Ignore
- ファイル先頭コメントによるファイル単位 Ignore
- 設定ファイルによる per-file-ignores（パスパターン + ルール ID）
- CLI オプション `--ignore-rule` による実行時のルール除外

将来拡張として残すもの。

- 行末コメント（`code  # paladin: ignore[rule-id]`）
- ブロック単位の disable/enable ペア
- 理由コメント（`-- 理由` 形式）
- 未使用 Ignore コメントの検出ルール
- 独立設定ファイル（`paladin.toml`）のサポート

## 3. インラインコメントによる Ignore

### 3.1 直前コメント（初期スコープ）

#### 書式

```python
# paladin: ignore
violating_code_here
```

特定ルールを指定する場合。

```python
# paladin: ignore[rule-id]
violating_code_here
```

複数ルールを指定する場合。

```python
# paladin: ignore[rule-a, rule-b]
violating_code_here
```

#### 仕様

- コメントは Ignore 対象行の **直前の行** に記述する
- `# paladin: ignore` のみで、直後の1行に対する全ルールの Ignore となる
- `# paladin: ignore[rule-id]` で、直後の1行に対する特定ルールのみを Ignore する
- 角括弧内に複数ルール ID をカンマ区切りで列挙できる
- コメント行と対象行の間に空行を挟んではならない
- 1つのコメントが影響する範囲は直後の1行のみである

#### 具体例

全ルール Ignore。

```python
# paladin: ignore
from . import utils
```

特定ルール Ignore。

```python
# paladin: ignore[no-relative-import]
from . import utils
```

複数ルール Ignore。

```python
# paladin: ignore[no-relative-import, no-local-import]
from . import utils
```

### 3.2 行末コメント（将来拡張）

行末コメントは初期スコープでは実装しない。将来拡張として以下の書式を想定する。

```python
violating_code_here  # paladin: ignore[rule-id]
```

行末コメントを後回しにする理由は以下の通りである。

- Paladin のルール ID はハイフン区切りの名前であり、行末に付けると行が過度に長くなる
- 直前コメント方式は、コメントと対象行が明確に分離されるため AI が生成・解釈しやすい
- ESLint の `eslint-disable-next-line` や Pylint の `disable-next`（2.10+）でも直前コメント方式が確立されており、実績がある

### 3.3 コメント接頭辞の選定理由

`# paladin:` という接頭辞を採用した理由を示す。

| 候補 | 評価 |
|------|------|
| `# noqa:` | Ruff / Flake8 と競合し、ツール間の混乱を招く |
| `# type: ignore` | mypy / Pyright と競合する |
| `# paladin: ignore` | ツール名が明示的で他ツールと衝突しない。Ruff の `# ruff: noqa` と同じ命名規則に従う |
| `# paladin-ignore` | コロン区切りの方が「ツール名: ディレクティブ」という構造が明確で AI が解析しやすい |

## 4. ファイル単位 Ignore

### 4.1 ファイル先頭コメント

#### 書式

全ルール Ignore。

```python
# paladin: ignore-file
```

特定ルールのみ Ignore する場合。

```python
# paladin: ignore-file[rule-id]
```

#### 仕様

- ファイルの先頭部分に記述する
- shebang 行（`#!/usr/bin/env python3`）やエンコーディング宣言（`# -*- coding: utf-8 -*-`）よりも後に配置できるが、最初の import 文や実行コードよりも前に配置しなければならない
- `# paladin: ignore-file` で、そのファイルの全ルール違反を無視する
- `# paladin: ignore-file[rule-id]` で、特定ルールの違反のみを無視する
- 角括弧内に複数ルール ID をカンマ区切りで列挙できる

#### 具体例

ファイル全体の全ルール Ignore。

```python
# paladin: ignore-file
"""レガシーモジュール（段階的に移行予定）"""
from . import legacy_utils
```

ファイル全体の特定ルール Ignore。

```python
# paladin: ignore-file[no-relative-import]
"""このモジュールは相対インポートを意図的に使用する"""
from . import sibling_module
```

### 4.2 設定ファイルによるファイル単位 Ignore

設定ファイルの `per-file-ignores` でも、ファイルやディレクトリ単位の Ignore を実現できる。セクション5で定義する。

## 5. 設定ファイル

### 5.1 設定ファイルの位置づけ

ディレクトリ単位やパスパターン単位の Ignore を実現するには設定ファイルが必要である。Paladin の設定ファイルは Ignore 専用ではなく、将来的にルール ON/OFF や解析対象制御など汎用的な設定を受け入れる器として設計する。ただし、初期スコープでは Ignore に必要な設定のみを定義する。

### 5.2 設定ファイル形式

`pyproject.toml` の `[tool.paladin]` セクションを使用する。

Python エコシステムでは `pyproject.toml` への統合が標準的な手法である。Ruff（`[tool.ruff]`）、Pyright（`[tool.pyright]`）、mypy（`[tool.mypy]`）のいずれも `pyproject.toml` をサポートしており、Paladin も同じ慣例に従う。

独立ファイル（`paladin.toml`）のサポートは将来拡張として残し、初期スコープでは `pyproject.toml` のみを対象とする。

### 5.3 設定ファイルの探索

設定ファイルの探索は以下の順序で行う。

1. カレントディレクトリの `pyproject.toml` を探索する
2. 見つかった場合、`[tool.paladin]` セクションの有無を確認する
3. セクションが存在すれば、その内容を設定として読み込む
4. `pyproject.toml` が存在しない場合、または `[tool.paladin]` セクションがない場合は、全てデフォルト値を使用する

親ディレクトリへの再帰的な探索は初期スコープでは行わない。

### 5.4 `per-file-ignores` の書式

パスパターン（glob）とルール ID のマッピングを定義する。

```toml
[tool.paladin.per-file-ignores]
"tests/**" = ["require-all-export"]
"scripts/**" = ["no-relative-import", "require-qualified-third-party"]
"src/legacy/**" = ["*"]
```

仕様は以下の通りである。

- キーは glob パターンで、`pyproject.toml` からの相対パスとして解釈する
- 値はルール ID の配列である
- `["*"]` を指定すると、そのパターンに一致するファイルの全ルール違反を無視する
- 複数のパターンが同一ファイルにマッチした場合、Ignore 対象のルールは **和集合** として扱う

### 5.5 設定ファイルの完全な例

初期スコープで有効な設定の完全な例を示す。

```toml
[tool.paladin]

[tool.paladin.per-file-ignores]
"tests/**" = ["require-all-export"]
"tests/**/__init__.py" = ["*"]
"scripts/**" = ["no-relative-import", "require-qualified-third-party"]
```

### 5.6 将来用の予約セクション名

以下のセクションは将来拡張として予約する。初期スコープでは定義しないが、設計上の衝突を避けるために名前を確保しておく。

- `[tool.paladin.rules]` — ルールの有効/無効の制御
- `[tool.paladin.rule."<rule-id>"]` — ルール個別設定
- `[[tool.paladin.overrides]]` — ディレクトリ別設定

なお、解析対象パスの制御（R-091）は当初 `[tool.paladin.include]` / `[tool.paladin.exclude]` として予約していたが、設定ファイルインターフェイス設計（`docs/design/configuration.md`）の検討の結果、 `[tool.paladin]` セクション直下のトップレベルキー `include` / `exclude` として定義する方式に変更した。Ruff / Pyright と同じ命名・配置に合わせることで、学習コストを低減するためである。

## 6. CLI オプション

### 6.1 `--ignore-rule`

#### 書式

```text
uv run paladin check src/ --ignore-rule no-relative-import
uv run paladin check src/ --ignore-rule no-relative-import --ignore-rule no-local-import
```

#### 仕様

- 指定されたルール ID の違反を、全ファイルに対して無視する
- 複数回指定することで、複数ルールを同時に除外できる
- 存在しないルール ID を指定した場合は警告を出力し、無視する

#### `--ignore-rule` を採用した理由

CLI オプション名として `--exclude-rule` ではなく `--ignore-rule` を採用した理由を示す。

- `--exclude-rule` は「ルールを実行対象から除外する」というニュアンスが強い。将来的にルール ON/OFF 設定が入った場合、「ルールの無効化」と混同される恐れがある
- `--ignore-rule` は「ルール違反を無視する」というセマンティクスが明確で、Ignore 機能の文脈と一貫している
- 将来、`--rule`（適用ルールの限定）や `--exclude-rule`（ルール適用からの除外）を別途導入する可能性があり、`--ignore-rule` はそれらと意味的に区別できる

## 7. 優先順序

複数の Ignore 機構が同時に存在する場合、以下の優先順序で適用する。

```text
CLI オプション（最優先）
  ↓
設定ファイル（per-file-ignores）
  ↓
ファイル・行コメント（ignore-file / ignore）
  ↓
デフォルト（全ルール適用）
```

各レベルの意味を示す。

| レベル | スコープ | 効果 |
|--------|----------|------|
| CLI `--ignore-rule` | 全ファイル × 指定ルール | 実行全体で指定ルールの違反を無視する |
| `per-file-ignores` | glob パターンに一致するファイル × 指定ルール | パターンに一致するファイルで指定ルールの違反を無視する |
| `# paladin: ignore-file` | 単一ファイル × 指定ルール（または全ルール） | そのファイルで指定ルールの違反を無視する |
| `# paladin: ignore` | 直後の1行 × 指定ルール（または全ルール） | その行で指定ルールの違反を無視する |

各レベルの Ignore は **累積的** に作用する。CLI で `--ignore-rule A` を指定し、設定ファイルで特定ファイルに対してルール B を Ignore し、インラインコメントでルール C を Ignore した場合、そのファイルのその行ではルール A、B、C のすべてが Ignore される。

「特定のレベルで Ignore を解除する」仕組みは初期スコープでは提供しない。

## 8. 未使用 Ignore コメントの検出

未使用の Ignore コメント（実際には違反が発生していないルールに対する Ignore）を検出する機能は、Ignore 機能の信頼性を維持するために重要である。Ruff の `RUF100` や ESLint の `reportUnusedDisableDirectives` に相当する機能として、将来的に専用ルール（仮称: `unused-ignore`）の導入を想定する。

初期スコープでは実装しない。

## 9. 既存 Linter との比較

### 9.1 インラインコメント書式の比較

| ツール | 行末コメント | 直前コメント | ファイル単位 |
|--------|-------------|-------------|-------------|
| Ruff | `# noqa: CODE` | （なし） | `# ruff: noqa` / `# ruff: noqa: CODE` |
| Pylint | `# pylint: disable=name` | `# pylint: disable-next=name` | `# pylint: skip-file` |
| ESLint | `// eslint-disable-line rule` | `// eslint-disable-next-line rule` | `/* eslint-disable */` |
| **Paladin（初期）** | （将来拡張） | `# paladin: ignore[rule-id]` | `# paladin: ignore-file` |

Paladin は初期スコープでは行末コメントを採用しない。ルール ID が長いことと、AI が生成しやすい書式を優先した結果である。

### 9.2 設定ファイルの per-file-ignores 比較

| ツール | 設定ファイル | per-file-ignores の書式 |
|--------|-------------|------------------------|
| Ruff | `pyproject.toml` / `ruff.toml` | `[tool.ruff.lint.per-file-ignores]` に glob → ルール配列 |
| ESLint | `eslint.config.js` | flat config の `files` + `rules` |
| **Paladin** | `pyproject.toml` | `[tool.paladin.per-file-ignores]` に glob → ルール配列 |

Paladin は Ruff の per-file-ignores と同様の構造を採用する。Python エコシステムに馴染みがあり、TOML の表現力で十分に記述できるためである。

## 10. 将来拡張

### 10.1 行末コメント

```python
from . import utils  # paladin: ignore[no-relative-import]
```

### 10.2 ブロック単位の disable/enable

```python
# paladin: disable[no-relative-import]
from . import module_a
from . import module_b
# paladin: enable[no-relative-import]
```

`ignore` ではなく `disable` / `enable` を使うのは、行指向の `ignore` とブロック指向の制御を意味的に区別するためである。

### 10.3 理由コメント

ESLint の `-- 理由` 形式に相当する機能。

```python
# paladin: ignore[no-relative-import] -- レガシーコードのため一時的に許可
from . import legacy
```

### 10.4 未使用 Ignore 検出ルール

`unused-ignore` ルールとして実装し、Ignore コメントが不要になった場合に警告を出す機能。

### 10.5 独立設定ファイル

`paladin.toml` を探索対象に追加する。優先順序は `paladin.toml` > `pyproject.toml` とする。

### 10.6 CLI からの設定ファイルパス指定

```text
uv run paladin check src/ --config path/to/pyproject.toml
```

## 11. ロードマップとの対応

本設計は、既存ロードマップの以下の項目に対応する。

| ロードマップ項目 | 本設計での対応 |
|----------------|-------------|
| R-080 ファイル単位の Ignore | セクション4（ファイル先頭コメント）+ セクション5（per-file-ignores の基盤） |
| R-081 直前コメントによる Ignore | セクション3.1（直前コメント） |
| R-082 設定ファイルによる全体 Ignore | セクション5（設定ファイル）+ セクション6（CLI オプション） |
| R-083 ディレクトリ単位の Ignore | セクション5.4（per-file-ignores の glob パターン） |

実装順序としては R-081（直前コメント）→ R-080（ファイル先頭コメント）→ R-082（設定ファイル基盤 + CLI）→ R-083（per-file-ignores）の順が自然である。設定ファイルの読み込み基盤（`pyproject.toml` の `[tool.paladin]` セクションのパーサー）は R-082 の時点で導入し、R-083 以降で per-file-ignores を追加する流れとなる。
