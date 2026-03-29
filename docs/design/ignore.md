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
- ブロック単位の disable/enable

## 2. 設計方針

### 2.1 全体方針

Ignore 機能は以下の方針に従って設計する。

- **明示的であること**: Ignore は暗黙の除外ではなく、コメントや設定として明示的に記述する
- **追跡可能であること**: どの Ignore がどのルールに影響しているかを事後に確認できる
- **AI が安定して扱えること**: 書式が単純で、生成 AI が正確に生成・解釈できる

### 2.2 Paladin 固有の考慮事項

Paladin のルール ID はハイフン区切りの名前（例: `require-all-export`）であり、Ruff のような短い英数字コード（例: `E501`）ではない。この特性から以下の判断を行う。

- コメント書式ではルール ID をそのまま使用する（別途短縮コードは設けない）
- 直前コメントと行末コメントの両方を採用する
- 全ルール一括 Ignore はルール ID を省略する書式で実現する

## 3. インラインコメントによる Ignore

### 3.1 直前コメント

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

### 3.2 行末コメント

#### 書式

```python
violating_code_here  # paladin: ignore
```

特定ルールを指定する場合。

```python
violating_code_here  # paladin: ignore[rule-id]
```

複数ルールを指定する場合。

```python
violating_code_here  # paladin: ignore[rule-a, rule-b]
```

#### 仕様

- コメントは Ignore 対象行の **末尾** に記述する
- コメント直前に1つ以上の空白が必要である（空白なしは検出されない）
- `# paladin: ignore` のみで、その行に対する全ルールの Ignore となる
- `# paladin: ignore[rule-id]` で、その行に対する特定ルールのみを Ignore する
- 角括弧内に複数ルール ID をカンマ区切りで列挙できる
- 直前コメントと行末コメントが同一行を対象とする場合、**累積的**に適用される

#### 具体例

全ルール Ignore。

```python
from . import utils  # paladin: ignore
```

特定ルール Ignore。

```python
from . import utils  # paladin: ignore[no-relative-import]
```

直前コメントと行末コメントの累積適用。

```python
# paladin: ignore[no-local-import]
from . import utils  # paladin: ignore[no-relative-import]
```

上記の例では、`no-local-import` と `no-relative-import` の両方が Ignore される。

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

ディレクトリ単位やパスパターン単位の Ignore を実現するには設定ファイルが必要である。Paladin の設定ファイルは Ignore 専用ではなく、ルール ON/OFF や解析対象制御など汎用的な設定を含む。本文書では Ignore に関連する設定のみを定義する。

### 5.2 設定ファイル形式

`pyproject.toml` の `[tool.paladin]` セクションを使用する。

Python エコシステムでは `pyproject.toml` への統合が標準的な手法である。Ruff（`[tool.ruff]`）、Pyright（`[tool.pyright]`）、mypy（`[tool.mypy]`）のいずれも `pyproject.toml` をサポートしており、Paladin も同じ慣例に従う。

### 5.3 設定ファイルの探索

設定ファイルの探索は以下の順序で行う。

1. カレントディレクトリの `pyproject.toml` を探索する
2. 見つかった場合、`[tool.paladin]` セクションの有無を確認する
3. セクションが存在すれば、その内容を設定として読み込む
4. `pyproject.toml` が存在しない場合、または `[tool.paladin]` セクションがない場合は、全てデフォルト値を使用する

親ディレクトリへの再帰的な探索は行わない。

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

Ignore に関連する設定の完全な例を示す。

```toml
[tool.paladin.per-file-ignores]
"tests/**" = ["require-all-export"]
"tests/**/__init__.py" = ["*"]
"scripts/**" = ["no-relative-import", "require-qualified-third-party"]
```

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

#### `--ignore-rule` を採用した理由

CLI オプション名として `--exclude-rule` ではなく `--ignore-rule` を採用した理由を示す。

- `--exclude-rule` は「ルールを実行対象から除外する」というニュアンスが強い。ルール ON/OFF 設定（`[tool.paladin.rules]`）と混同される恐れがある
- `--ignore-rule` は「ルール違反を無視する」というセマンティクスが明確で、Ignore 機能の文脈と一貫している
- `--rule`（適用ルールの限定）や `--exclude-rule`（ルール適用からの除外）が別途導入された場合にも、`--ignore-rule` はそれらと意味的に区別できる

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
| `# paladin: ignore` | 直後の1行または同一行末 × 指定ルール（または全ルール） | その行で指定ルールの違反を無視する |

各レベルの Ignore は **累積的** に作用する。CLI で `--ignore-rule A` を指定し、設定ファイルで特定ファイルに対してルール B を Ignore し、インラインコメントでルール C を Ignore した場合、そのファイルのその行ではルール A、B、C のすべてが Ignore される。

「特定のレベルで Ignore を解除する」仕組みは提供しない。

## 8. 既存 Linter との比較

### 8.1 インラインコメント書式の比較

| ツール | 行末コメント | 直前コメント | ファイル単位 |
|--------|-------------|-------------|-------------|
| Ruff | `# noqa: CODE` | （なし） | `# ruff: noqa` / `# ruff: noqa: CODE` |
| Pylint | `# pylint: disable=name` | `# pylint: disable-next=name` | `# pylint: skip-file` |
| ESLint | `// eslint-disable-line rule` | `// eslint-disable-next-line rule` | `/* eslint-disable */` |
| **Paladin** | `code  # paladin: ignore[rule-id]` | `# paladin: ignore[rule-id]` | `# paladin: ignore-file` |

### 8.2 設定ファイルの per-file-ignores 比較

| ツール | 設定ファイル | per-file-ignores の書式 |
|--------|-------------|------------------------|
| Ruff | `pyproject.toml` / `ruff.toml` | `[tool.ruff.lint.per-file-ignores]` に glob → ルール配列 |
| ESLint | `eslint.config.js` | flat config の `files` + `rules` |
| **Paladin** | `pyproject.toml` | `[tool.paladin.per-file-ignores]` に glob → ルール配列 |

Paladin は Ruff の per-file-ignores と同様の構造を採用する。Python エコシステムに馴染みがあり、TOML の表現力で十分に記述できるためである。
