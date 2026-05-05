# no-module-level-function

## メタ情報

| 項目 | 値 |
|------|-----|
| ルールID | no-module-level-function |
| 対象 | 単一ファイル |

## 概要

モジュールの直下に定義された関数（モジュールレベル関数）を禁止するルールです。関数はクラスのメソッドとして定義することを要求します。`@pytest.fixture` など許可リストに含まれるデコレータが付いた関数は対象外とします。

## 背景と意図

Paladin はオブジェクト指向スタイルを徹底しており、振る舞いをクラスに所属させることを設計原則としています。モジュールレベル関数を禁止する理由は次の4点です。

- **責務の所在を明確にする**: クラスに属さない関数は「誰の振る舞いか」が不明確である。クラスのメソッドとして定義することで、関数がどのデータや状態と関わるかが構造として表現できる
- **データと振る舞いを近接させる**: 関連するデータ（フィールド）と振る舞い（メソッド）を同じクラスにまとめることで、凝集度が上がり、変更が局所化する
- **テスト時の差し替えを容易にする**: クラスのメソッドとして定義された振る舞いは、依存注入やサブクラス化によって差し替えやすい。モジュールレベル関数は直接呼び出しになるため、テストでの置換が難しい
- **コードベース全体の一貫性**: モジュールレベル関数とメソッドが混在すると、どちらを選ぶかの判断コストが増える。クラスに統一することで、迷いなくスタイルを揃えられる

Paladin の実装においても、`calc_file_length(source)` というモジュールレベル関数を `FileLengthCalculator.calc()` という静的メソッドへ移行した実績があります。このルールはその設計方針をコードベース全体で機械的に保証します。

## 診断メッセージ

| フィールド | 内容 |
|-----------|------|
| message | モジュールレベルに関数 `{function_name}` が定義されています |
| reason | モジュールレベル関数は責務の所在が不明確であり、テスト時の差し替えが困難です |
| suggestion | `{function_name}` をクラスの `@staticmethod` / `@classmethod` / インスタンスメソッドとして再定義してください |

## 検出パターン

### 違反コード

```python
# src/paladin/rule/max_file_length.py
def calc_file_length(source: str) -> int:  # 違反: モジュールレベルに関数が定義されている
    if not source:
        return 0
    return len(source.splitlines())
```

### 準拠コード（@staticmethod を使った実装）

```python
# src/paladin/rule/max_file_length.py
class FileLengthCalculator:
    """ファイルの行数を計算するクラス"""

    @staticmethod
    def calc(source: str) -> int:  # 準拠: クラスの静的メソッドとして定義されている
        if not source:
            return 0
        return len(source.splitlines())
```

### 準拠コード（@classmethod を使った実装）

```python
# src/paladin/rule/types.py
@dataclass(frozen=True)
class RuleMeta:
    """ルールのメタ情報を保持する値オブジェクト"""

    rule_id: str
    rule_name: str

    @classmethod
    def from_dict(cls, data: dict[str, str]) -> RuleMeta:  # 準拠: クラスメソッドとして定義されている
        return cls(rule_id=data["rule_id"], rule_name=data["rule_name"])
```

### 準拠コード（インスタンスメソッドとしての実装）

```python
# src/paladin/check/orchestrator.py
class CheckOrchestrator:
    """対象列挙と AST 生成の処理フローを制御するオーケストレーター"""

    def orchestrate(self, context: CheckContext) -> CheckReport:  # 準拠: インスタンスメソッドとして定義されている
        target_files = self.collector.collect(context.targets)
        ...
```

### 準拠コード（pytest フィクスチャは対象外）

```python
# tests/conftest.py
@pytest.fixture
def tmp_source_file(tmp_path: Path) -> SourceFile:  # 準拠: @pytest.fixture は許可リストに含まれる
    py_file = tmp_path / "main.py"
    py_file.write_text("x = 1\n")
    return SourceFile(file_path=py_file, tree=ast.parse("x = 1\n"), source="x = 1\n")
```

## 検出の補足

### 検出ロジック

1. `ast.Module.body` を走査し、`ast.FunctionDef` および `ast.AsyncFunctionDef` ノードを収集する
2. 各ノードのデコレータリスト（`node.decorator_list`）を確認し、許可リストに含まれるデコレータが付いている場合はスキップする
3. 上記フィルタを通過したノードを違反として報告する

### 対象外のパターン

以下は違反として報告しません。

- **クラスメソッド**: `ast.ClassDef.body` 内の `FunctionDef` はモジュールレベルではないため対象外
- **ネスト関数**: 別の関数やメソッドの `body` 内に定義された `FunctionDef` は対象外（`ast.Module.body` の直下にあるものだけを検査する）
- **許可デコレータ**: `@pytest.fixture` など設定で指定した許可リストに含まれるデコレータが付いている関数は対象外
- **内包表記・ラムダ**: `ast.ListComp` / `ast.Lambda` 等は `FunctionDef` ではないため対象外
- **`if __name__ == "__main__":` ブロック内の関数**: `ast.Module.body` 直下ではなく `ast.If` の `body` 内に定義された場合は対象外

### 適用範囲

`src/` と `tests/` の両方の `.py` ファイルを対象とします。`conftest.py` も対象に含みますが、`@pytest.fixture` デコレータを持つ関数は許可リストにより除外されます。

### 報告の粒度

違反1件につき `def` 文の行番号を報告します。同一ファイルに複数のモジュールレベル関数がある場合、それぞれ個別に報告します。

## 既存ツールとの関係

Ruff・Pylint のいずれも「モジュールレベル関数の禁止」に相当するルールは提供していません。

| 観点 | Ruff / Pylint | Paladin no-module-level-function |
|------|--------------|----------------------------------|
| モジュールレベル関数の検出 | 該当ルールなし | `ast.Module.body` を走査して検出 |
| デコレータによる許可リスト | 該当ルールなし | 設定で拡張可能な許可リストを持つ |
| 設計意図の提示 | なし | reason でオブジェクト指向設計の観点を説明 |

「関数をクラスに所属させる」という設計方針の強制は既存リンターでは扱われていない領域であり、Paladin で独自に実装します。
