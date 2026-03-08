# protocol パッケージ基本設計

[protocol パッケージ要件定義](./requirements.md) に基づいた基本設計を説明します。

## アーキテクチャパターン

- **Protocol パターン**: Python の `typing.Protocol` を使って構造的部分型（ダックタイピング）ベースのインターフェースを定義する。実装クラスへの明示的な継承なしに型安全な依存性注入を実現する
- **読み書き分離パターン**: 読み取り専用・書き込み専用のProtocolを独立して定義し、呼び出し元が必要な操作のみに依存できるようにする

## コンポーネント構成

### 主要コンポーネント

| コンポーネント | クラス名 | 役割 |
|---|---|---|
| 読み取りプロトコル | `TextFileSystemReaderProtocol` | 読み取り操作の型安全なインターフェース定義 |
| 書き込みプロトコル | `TextFileSystemWriterProtocol` | 書き込み操作の型安全なインターフェース定義 |

### ファイルレイアウト

#### プロダクションコード

```text
src/example/protocol/
├── __init__.py    # 公開 API の定義（TextFileSystemReaderProtocol / TextFileSystemWriterProtocol を __all__ で明示）
└── fs.py          # TextFileSystemReaderProtocol / TextFileSystemWriterProtocol
```

#### テストコード

Protocol定義自体の独立したテストは不要。Adapter側のテスト（`tests/unit/test_foundation/test_fs/`）で、Adapterが各Protocolを明示継承していることによって継承関係の整合性が担保される。

## Protocolの配置ルール

Protocolの定義場所は用途によって決まる:

| Protocol の種別 | 定義する場所 | 具体例 |
|---|---|---|
| **機能固有Protocol**（特定機能のOrchestratorだけが使う） | 機能パッケージ（`<feature>/protocol.py`） | 機能依存のカスタムIF |
| **複数機能で共有するProtocol** | `protocol/` パッケージ | `TextFileSystemReaderProtocol` |
| **Adapter（具象実装）** | 常に `<foundation>/` | `TextFileSystemReader`（`foundation/fs/text.py`） |

## 固有の設計判断

### 独立パッケージとして切り出した理由

**設計の意図**: `protocol/` を `foundation/` や `feature/` から独立したパッケージとして配置する。

**なぜそう設計したか**: 利用する機能パッケージが1つであっても、fsのProtocol所有者はその機能パッケージではない。`foundation/` に置くとOnionの方向性（ビジネスロジック → 基盤）が逆転する。`protocol/` を独立させることで「依存される側」として明確に位置づけられる。

**トレードオフ**: パッケージ数が増える。ただし、配置の意図が明確になるためコードベースの理解しやすさが向上する。

### Adapterが明示継承する設計判断

**設計の意図**: `TextFileSystemReader` と `TextFileSystemWriter`（`foundation/fs/text.py`）は `TextFileSystemReaderProtocol` / `TextFileSystemWriterProtocol` を明示的に継承する。

**なぜそう設計したか**: Pythonの構造的部分型では明示継承なしでも準拠できるが、明示継承することでIDEや型チェッカーが継承関係を直接検証できる。「意図的にこのProtocolを実装した」という設計意図がコードに現れる。

**トレードオフ**: `foundation/` → `protocol/` の依存が生まれる。ただし `protocol/` は標準ライブラリのみ使う軽量な定義なので許容する。

## 制約と注意点

### protocol/ に置くもの・置かないもの

| 置くもの | 置かないもの |
|---|---|
| 複数機能パッケージから共有されるProtocol定義 | 機能固有のProtocol（`<feature>/protocol.py` に置く） |
| 標準ライブラリのみを使ったインターフェース定義 | Adapter実装（`<foundation>/` に置く） |

### 依存方向の制約

`protocol/` は `foundation/` ・ `feature/` のいずれにも依存しない。Python標準ライブラリ（`typing`、`pathlib`）のみを使用する。この独立性により、`protocol/` はコードベース内で最も依存される安定した層として機能する。

## 外部依存と拡張性

### 外部システム依存

| 依存先 | 用途 |
|---|---|
| Python `typing.Protocol` 標準ライブラリ | 構造的部分型によるインターフェース定義 |
| Python `pathlib.Path` 標準ライブラリ | ファイルパスの型表現 |

### 想定される拡張ポイント

- 新たな横断的Protocolが必要になった場合（例: `BinaryFileSystemReaderProtocol`）、同パッケージに追加または新規モジュールとして定義できる
- 新機能から共有Protocolが必要になった場合、まず `<feature>/protocol.py` に定義し、複数機能での共有が必要になった時点で `protocol/` に移管する

## 変更パターン別ガイド

よくある変更ケースと、対応するファイルの道筋を示す。

| 変更内容 | 主な変更対象 | 備考 |
|---|---|---|
| Protocolのシグネチャを変更 | `fs.py`（対象Protocol） | Adapterの実装（`foundation/fs/text.py`）も合わせて更新する |
| 新しいProtocolを追加 | `fs.py` または新規ファイル | `__init__.py` の `__all__` への追加も忘れずに |
| Protocolを機能固有から共有に移管 | `<feature>/protocol.py` → `protocol/` | 移管後は元ファイルの定義を削除する |

## 影響範囲

`protocol/` パッケージへの変更はProtocolのシグネチャに依存するすべてのパッケージ（`foundation/fs/`、利用する `<feature>/`）に影響する。Protocolシグネチャを変更する場合は全依存パッケージへの影響を確認すること。

## 関連ドキュメント

- [protocol パッケージ要件定義](./requirements.md): protocol パッケージの機能要件や前提条件
- [foundation/fs パッケージ基本設計](../foundation/fs/design.md): Adapter実装の設計（明示継承の詳細）
- [Python アーキテクチャ設計](../../design/architecture.md): プロジェクト共通の設計思想
