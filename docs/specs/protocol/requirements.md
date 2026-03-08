# protocol パッケージ要件定義

## 概要

### 目的

OnionアーキテクチャのPort定義を独立したパッケージとして提供し、複数の機能パッケージから共有されるProtocolを一元管理する。

### 解決する課題

機能固有のProtocolは `<feature>/protocol.py` に置けるが、複数の機能パッケージから共有されるProtocolは置き場所の判断が難しい。

- `<feature>/` に置くと所有者が曖昧になる（どの機能がそのProtocolを「所有」するかが不明確）
- `<foundation>/` に置くとOnionの方向性（ビジネスロジック → 基盤）が逆転する（PortはビジネスロジックのものであってShared Kernelではない）

`protocol/` パッケージを独立させることで、Portとして「依存される側」に明確に位置づけられる。

### コンポーネントの概要

ファイルシステム操作の読み取りと書き込みを抽象化したProtocolを提供する。

## 機能要件

### ファイルシステム読み取りインターフェースの定義

テキストファイルを読み込む操作の契約を定義する。

- `TextFileSystemReaderProtocol.read(file_path: Path) -> str`
- ファイルパスを受け取り、ファイルの内容を文字列として返す
- ファイル操作失敗時は `FileSystemError`（`foundation/fs` で定義）を送出する

### ファイルシステム書き込みインターフェースの定義

テキストファイルへ書き込む操作の契約を定義する。

- `TextFileSystemWriterProtocol.write(text: str, file_path: Path) -> None`
- 文字列と書き込み先ファイルパスを受け取り、ファイルへ書き込む
- ファイル操作失敗時は `FileSystemError`（`foundation/fs` で定義）を送出する

## 品質要件

### 依存の独立性（protocol/ は他パッケージに依存しない）

`protocol/` パッケージは外部ライブラリに依存せず、`foundation/` や `feature/` にも依存しない独立性を維持すること。Python標準ライブラリ（`typing`、`pathlib`）のみを使用する。

### テスト容易性（Fake実装が軽量に書ける）

`typing.Protocol` の構造的部分型を活用し、明示継承なしでProtocolに準拠したインメモリ実装（Fake）を作成できる。テスト時にモックフレームワーク固有の知識なしに差し替えが可能であること。

## 関連ドキュメント

- [protocol パッケージ基本設計](./design.md): protocol パッケージのアーキテクチャ設計やコンポーネント構成
- [foundation/fs パッケージ要件定義](../foundation/fs/requirements.md): Adapter実装の要件定義
