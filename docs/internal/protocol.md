# protocol パッケージ設計

## ファイルレイアウト

### プロダクションコード

```
src/paladin/protocol/
├── __init__.py    # 公開 API の定義（TextFileSystemReaderProtocol, TextFileSystemWriterProtocol）
└── fs.py          # TextFileSystemReaderProtocol / TextFileSystemWriterProtocol
```

### テストコード

Protocol 定義自体の独立したテストは不要。Adapter 側のテスト（`tests/unit/test_foundation/test_fs/`）で、Adapter が各 Protocol を明示継承していることによって継承関係の整合性が担保される。

## Protocol の配置ルール

Protocol の定義場所は用途によって決まる。

| Protocol の種別 | 定義する場所 | 具体例 |
|---|---|---|
| 機能固有 Protocol（特定機能の Orchestrator だけが使う） | 機能パッケージ（`<feature>/protocol.py`） | 機能依存のカスタム IF |
| 複数機能で共有する Protocol | `protocol/` パッケージ | `TextFileSystemReaderProtocol` |
| Adapter（具象実装） | 常に `<foundation>/` | `TextFileSystemReader`（`foundation/fs/text.py`） |

## 設計判断

### 独立パッケージとして切り出した理由

`protocol/` を `foundation/` や `feature/` から独立したパッケージとして配置している。

**理由**: 利用する機能パッケージが 1 つであっても、fs の Protocol 所有者はその機能パッケージではない。`foundation/` に置くと Onion の方向性（ビジネスロジック → 基盤）が逆転する。`protocol/` を独立させることで「依存される側」として明確に位置づけられる。

**トレードオフ**: パッケージ数が増える。ただし、配置の意図が明確になるためコードベースの理解しやすさが向上する。

### Adapter が明示継承する設計判断

`TextFileSystemReader` と `TextFileSystemWriter`（`foundation/fs/text.py`）は `TextFileSystemReaderProtocol` / `TextFileSystemWriterProtocol` を明示的に継承する。

**理由**: Python の構造的部分型では明示継承なしでも準拠できるが、明示継承することで IDE や型チェッカーが継承関係を直接検証でき、シグネチャのずれを即座に検出できる。

**トレードオフ**: `foundation/` → `protocol/` の依存が生まれる。ただし `protocol/` は標準ライブラリのみ使う軽量な定義なので許容する。

## ガードレール

| 置くもの | 置かないもの |
|---|---|
| 複数機能パッケージから共有される Protocol 定義 | 機能固有の Protocol（`<feature>/protocol.py` に置く） |
| 標準ライブラリのみを使ったインターフェース定義 | Adapter 実装（`<foundation>/` に置く） |

- `protocol/` は `foundation/` ・ `feature/` のいずれにも依存しない。Python 標準ライブラリ（`typing`、`pathlib`）のみを使用すること
- 公開 API は `TextFileSystemReaderProtocol` と `TextFileSystemWriterProtocol` のみ。`paladin.protocol` パッケージから import すること
