# no-deep-nesting

## メタ情報

| 項目 | 値 |
|------|-----|
| ルールID | no-deep-nesting |
| 対象 | 単一ファイル |

## 概要

単一のメソッド/関数内で3段階以上のネストを禁止するルールです。`if`/`for`/`while`/`with`/`try` などの複合文が3段階以上入れ子になっている場合に違反を検出します。

## 背景と意図

単一メソッドに深いネストが生じるのは、手続き的にロジックを持たせすぎているサインです。以下の問題を引き起こします。

- **テスタビリティの低下**: ネストが深くなるほど、分岐の組み合わせが爆発的に増加し、テストケースを網羅することが困難になる。ネスト3段階は最大8通りの分岐経路を生み出す可能性があり、それを単一のメソッドでテストするコストは高い
- **モデリングの問題**: 深いネストは、オブジェクトの責務が適切に分割されていないことの兆候である。メソッドが複数の関心事を一手に担い、手続き的な処理の連なりになっているとき、ネストは自然と深くなる
- **可読性の低下**: 複数段階のインデントが積み重なると、読み手がコードの「どの文脈で実行されているか」を追うのが難しくなる

理想的な改善の順序は次のとおりです。

1. **クラス設計を見直す**: 深いネストは、処理の一部を別のクラスや型に委譲するべき兆候である。新しいデータモデルや責務の分離によってネストそのものをなくすのが最善の解
2. **プライベートメソッドに切り出す**: クラス設計の見直しが難しい場合でも、深くなった部分をプライベートメソッドに抽出することは常にできる。これだけでもネスト深度を劇的に下げられる

## 診断メッセージ

| フィールド | 内容 |
|-----------|------|
| message | `{scope}` 内のネストが {depth} 段階に達している（最大: 3） |
| reason | 深いネストはテスタビリティを下げ、手続き的にロジックを持たせすぎている兆候である |
| suggestion | ネストの深い処理をプライベートメソッドに切り出すか、クラス設計を見直してください |

`{scope}` は `メソッド ClassName.method_name` または `関数 function_name` の形式です。`{depth}` は検出された最大ネスト深度です。

## 検出パターン

### 違反コード

```python
# src/paladin/rule/no_cross_package_reexport.py
class NoCrossPackageReexportRule:
    def check(self, source_file: SourceFile) -> tuple[Violation, ...]:
        # ...
        violations: list[Violation] = []
        for node in source_file.tree.body:               # depth 1
            if not isinstance(node, ast.Assign):         # depth 2
                continue
            for target in node.targets:                  # depth 2
                if not isinstance(target, ast.Name):     # depth 3 ← 違反
                    continue
                if not isinstance(node.value, ast.List): # depth 3 ← 違反
                    continue
                for elt in node.value.elts:              # depth 3 ← 違反
                    if not isinstance(elt, ast.Constant): # depth 4
                        continue
                    name = elt.value
                    if name not in import_mapping:        # depth 4
                        continue
                    if not self._is_same_package(...):    # depth 4
                        violations.append(...)            # depth 5
        return tuple(violations)
```

### 準拠コード（プライベートメソッドへの切り出し）

```python
class NoCrossPackageReexportRule:
    def check(self, source_file: SourceFile) -> tuple[Violation, ...]:
        # ...
        violations: list[Violation] = []
        for node in source_file.tree.body:           # depth 1
            if not isinstance(node, ast.Assign):     # depth 2
                continue
            violations.extend(self._check_assign(node, ...))  # depth 2
        return tuple(violations)

    def _check_assign(self, node: ast.Assign, ...) -> list[Violation]:
        violations: list[Violation] = []
        for target in node.targets:                  # depth 1
            if not isinstance(target, ast.Name):     # depth 2
                continue
            if not isinstance(node.value, ast.List): # depth 2
                continue
            violations.extend(self._check_elements(node.value.elts, ...))  # depth 2
        return violations

    def _check_elements(self, elts: list[ast.expr], ...) -> list[Violation]:
        violations: list[Violation] = []
        for elt in elts:                             # depth 1
            if not isinstance(elt, ast.Constant):   # depth 2
                continue
            name = elt.value
            if name not in import_mapping:           # depth 2
                continue
            if not self._is_same_package(...):       # depth 2
                violations.append(...)
        return violations
```

### 準拠コード（ガード節による改善）

```python
def process_nodes(self, nodes: list[ast.stmt]) -> list[Violation]:
    violations = []
    for node in nodes:                          # depth 1
        if not isinstance(node, ast.Assign):   # depth 2（ガード節）
            continue
        if not node.targets:                   # depth 2（ガード節）
            continue
        violations.extend(self._check_node(node))  # depth 2
    return violations
```

## 検出の補足

### ネストのカウント方法

関数/メソッドの `body` の直下をネスト深度0とします。以下の複合文の `body`（および `orelse`/`handlers`/`finalbody`）に入るたびに深度を1増やします。

- `if` / `elif` / `else`
- `for` / `else`
- `while` / `else`
- `with` / `async with`
- `try` / `except` / `else` / `finally`
- `match` / `case`（Python 3.10+）
- `async for`

ネスト深度が3以上に達した時点で、その関数/メソッドを違反として報告します。

### ネストとしてカウントしないもの

以下は深度を増やしません。

- **ネスト関数・ネストクラス**: 内部に定義された関数やクラスは独立したスコープとして扱い、外側の深度を引き継ぎません。ネスト関数自体の内部は深度0からカウントし直します
- **内包表記**: リスト・辞書・集合内包表記およびジェネレータ式は単一式として扱い、対象外です

### 報告の粒度

1つの関数/メソッドにつき1件の違反を報告します。関数/メソッドの `def` 文の行番号と、検出された最大ネスト深度を報告します。修正の単位が「この関数全体の設計」であるため、個々のネスト箇所を個別に報告しません。

### 適用範囲

- トップレベル関数（`def` / `async def`）とクラスメソッドの両方を対象とします
- `__init__.py` を含む全ての `.py` ファイルを対象とします
- テストファイル（`tests/` 配下）も対象とします

## 既存ツールとの関係

Ruff には `PLR1702`（`too-many-nested-blocks`）、Pylint には `R1702` という同種のルールが存在します。ただし、以下の差異から Paladin での独自実装が必要です。

| 観点 | Ruff PLR1702 / Pylint R1702 | Paladin no-deep-nesting |
|------|----------------------------|------------------------|
| ステータス | Ruff は Preview（不安定）、Pylint は安定 | 安定版として提供 |
| デフォルト閾値 | 5（ゆるい） | 3（設計品質を重視） |
| 設計意図の提示 | なし（汎用的な警告のみ） | reason でテスタビリティ・モデリング品質の観点を説明 |
| 修正方針の提示 | なし | suggestion でプライベートメソッド分割・クラス設計見直しを誘導 |

Paladin で独自に扱う主な理由は、閾値を3に設定することと、message/reason/suggestion の3フィールドで修正行動につながる情報を提供することです。特に、深いネストが「テスタビリティの問題」であり「モデリングの問題の兆候」であるという設計上の根拠を診断に含めることは、既存のリンターでは表現できない領域です。
