# max-function-parameter

## メタ情報

| 項目 | 値 |
|------|-----|
| ルールID | max-function-parameter |
| 対象 | 単一ファイル |

## 概要

単一のメソッド/関数が受け取る引数の数が設定された上限を超えた場合に違反を検出します。`self` / `cls` は除外し、`*args` / `**kwargs` はそれぞれ1つとしてカウントします。

引数の数を制限することは単なる数の削減が目的ではありません。4つ以上の引数が並ぶ箇所は、ライフサイクルが近いプリミティブな値が裸のまま渡されている兆候です。このルールは、そうした箇所をバリューオブジェクトやエンティティへ集約する設計機会として開発者に提示します。

## 背景と意図

引数の数は、関数/メソッドの設計品質を示すシンプルかつ機械的に検出可能な指標です。

- **プリミティブな値の氾濫の検出** — 4つ以上の引数が並ぶときは、ライフサイクルが近いプリミティブな値が裸のまま受け渡されている兆候である。`name: str, email: str, age: int, role: str` のように並んでいれば、それらは同じ概念の一部として束ねられるべき候補である
- **凝集度の高いクラスへの誘導** — 関連する値をバリューオブジェクトやエンティティにまとめることは、設計の凝集度を高め、変更の局所化につながる。このルールは、その設計機会を見落とさないための指標として機能する
- **メンテナンス性の向上** — 引数が増えるほど呼び出し側のコードは長くなり、シグネチャ変更の影響範囲が広がる。引数の順序ミスや型の混同といったバグが起きやすくなり、修正コストが増大する
- **検出指標としての引数数** — 引数の数は AST から機械的に取得でき、偽陰性が少ない指標である。複雑な意味解析を必要とせず、安定した検出が可能である

検出ロジックは引数の数という単純な指標ですが、このルールの意図は凝集度の高いクラスを増やすことにあります。引数上限の超過を「カプセル化機会の発見」として捉えてください。

## 診断メッセージ

| フィールド | 内容 |
|-----------|------|
| message | メソッド/関数 `{function_name}` の引数は `{count}` 個です。上限は `{limit}` 個です |
| reason | 引数が多い関数はプリミティブな値をそのまま受け渡している兆候であり、関連する値をまとめたクラスへのカプセル化機会を逃しています |
| suggestion | ライフサイクルが近い引数を束ねるバリューオブジェクトやエンティティを定義し、それを単一の引数として受け取るよう変更してください |

## 検出パターン

### 違反コード

```python
# src/paladin/service/user_service.py
class UserService:
    def create_user(
        self,
        name: str,
        email: str,
        age: int,
        role: str,  # 違反: self を除いた引数が4つで上限3を超えている
    ) -> User:
        ...
```

### 準拠コード（バリューオブジェクトに集約）

```python
# src/paladin/service/user_service.py
@dataclass(frozen=True)
class UserProfile:
    name: str
    email: str
    age: int
    role: str

class UserService:
    def create_user(self, profile: UserProfile) -> User:  # 準拠: 引数は1つ
        ...
```

### 準拠コード（@pytest.fixture は対象外）

```python
# tests/conftest.py
@pytest.fixture
def user_service(
    db: Database,
    cache: Cache,
    mailer: Mailer,
    logger: Logger,  # 準拠: @pytest.fixture は許可リストに含まれる
) -> UserService:
    return UserService(db=db, cache=cache, mailer=mailer, logger=logger)
```

## 検出の補足

### 検出ロジック

1. 対象ファイルの AST を走査し、すべての `ast.FunctionDef` および `ast.AsyncFunctionDef` ノードを取得する
2. 親ノードが `ast.ClassDef` で、かつ第1引数名が `self` または `cls` の場合、その第1引数をカウントから除外する
3. `posonlyargs` + `args` + `kwonlyargs` の長さに、`vararg` があれば +1、`kwarg` があれば +1 を加算する
4. デコレータリスト（`node.decorator_list`）に許可リスト（`@pytest.fixture` 等）が含まれる場合はスキップする
5. 算出した引数数がしきい値を超えた場合に違反を報告する

### カウント方法

`self` / `cls` は引数数に含めません。クラスの `FunctionDef` かどうかは親ノードが `ast.ClassDef` であるかで判定し、その場合のみ第1引数を除外します。

`*args`（`vararg`）と `**kwargs`（`kwarg`）はそれぞれ1つとしてカウントします。存在しない場合は加算しません。

### 対象外のパターン

以下は違反として報告しません。

- **`@pytest.fixture` デコレータ付き関数**: フィクスチャは依存オブジェクトを注入する構造上、引数が多くなることが多い。設定の許可リストで管理する
- **ラムダ**: `ast.Lambda` は `FunctionDef` ではないため対象外
- **内包表記**: リスト・辞書・集合内包表記およびジェネレータ式は対象外
- **`@dataclass` 自動生成 `__init__`**: `@dataclass` が生成する `__init__` は AST に出現しないため、自動的に対象外となる

ダンダーメソッド（`__init__` を含む）、ネスト関数、`async def` は対象に含みます。

### 適用範囲

`src/` と `tests/` の両方の `.py` ファイルを対象とします。プロダクションコードとテストコードで異なるしきい値は設けず、単一の `max-parameters` を使用します。

### 報告の粒度

1ファイル内の各メソッド/関数を個別にチェックします。上限を超えたメソッド/関数ごとに1件の違反を報告します。違反の行番号は `def` キーワードのある行とします。

### 設定ファイル

```toml
[tool.paladin.rule.max-function-parameter]
max-parameters = 3
```

| パラメータ | 説明 | デフォルト値 |
|-----------|------|------------|
| `max-parameters` | `self` / `cls` を除いた引数数の上限 | `3` |

### max-method-length との関係

`max-method-length` が「メソッドの行数」という指標で処理の肥大化を検出するのに対し、`max-function-parameter` は「引数の数」という指標でインタフェースの複雑化を検出します。行数が少なくても引数が多い場合は `max-function-parameter` のみが違反を報告し、引数が少なくても処理が長い場合は `max-method-length` のみが違反を報告します。2つのルールは補完的な指標として機能し、異なる角度から設計問題を検出します。

## 既存ツールとの関係

Ruff は `PLR0913`（`too-many-arguments`）、Pylint は `R0913` として同種のルールを提供しており、検出ロジックとしては既存ツールでも実現可能です。

| 観点 | Ruff PLR0913 / Pylint R0913 | Paladin max-function-parameter |
|------|----------------------------|-------------------------------|
| デフォルト上限 | 5 | 3（設計品質を重視） |
| 設計意図の提示 | なし（汎用的な警告のみ） | reason でプリミティブ値のカプセル化機会を説明 |
| 修正方針の提示 | なし | suggestion でバリューオブジェクト化を具体的に誘導 |

Paladin でこのルールを独自に扱う理由は3点です。デフォルト値を業界標準の5ではなく3に設定すること、reason フィールドで「カプセル化機会の発見」という設計意図を明示すること、suggestion フィールドでバリューオブジェクトやエンティティへの集約という具体的な修正行動を誘導することです。
