# foundation/fs パッケージ設計

## ファイルレイアウト

### プロダクションコード

```
src/paladin/foundation/fs/
├── __init__.py    # 公開 API の定義（FileSystemError, TextFileSystemReader, TextFileSystemWriter）
├── error.py       # FileSystemError（ファイルシステム固有の業務例外）
└── text.py        # TextFileSystemReader / TextFileSystemWriter（実装クラス）
```

### テストコード

```
tests/unit/test_foundation/test_fs/
└── test_text.py    # TextFileSystemReader / TextFileSystemWriter のテスト
```

## 設計判断

### 読み取りと書き込みの分離

`TextFileSystemReader` と `TextFileSystemWriter` を 1 つのクラスにまとめず、読み取り専用・書き込み専用として独立して定義している。

**理由**: 呼び出し元のコンポーネントが必要とするのは多くの場合、読み取りか書き込みのどちらか一方である。単一クラスに集約すると、最小権限の原則に反する。Protocol も読み取り・書き込みで個別に定義することで、呼び出し元が必要な機能のみに依存できる。

**トレードオフ**: 両方の操作が必要な呼び出し元では 2 つのオブジェクトを管理する必要がある。読み書きを同時に必要とするケースは、そのコンポーネント自体が 2 つの責務を持っている可能性があり、責務の分離を検討すべきシグナルとなる。

### Adapter による Protocol 実装

`TextFileSystemReader` と `TextFileSystemWriter` は `protocol/fs.py` の `TextFileSystemReaderProtocol` / `TextFileSystemWriterProtocol` を明示的に継承する。

**理由**: Python の構造的部分型ではシグネチャが一致していれば Protocol に準拠できるが、明示継承することで IDE や型チェッカーが継承関係を直接検証でき、シグネチャのずれを即座に検出できる。また「意図的にこの Protocol を実装した」という設計意図がコードに現れる。

**トレードオフ**: `foundation/` → `protocol/` の依存が生まれる。ただし `protocol/` は標準ライブラリのみに依存する純粋な型定義であるため、この依存は軽量である。

### OS 例外の FileSystemError への変換

`FileNotFoundError`, `PermissionError`, `IsADirectoryError` などの OS 由来の例外を catch し、`FileSystemError` に変換して送出している。

**理由**: 呼び出し元が処理すべき例外が複数の OS 固有例外に分散すると抜け漏れが起きやすい。`FileSystemError` という単一の型に統一することで、呼び出し元は 1 種類の例外を処理するだけで済む。また `FileSystemError` は `ApplicationError` を継承しているため、`ErrorHandler` でそのまま処理できる。

**トレードオフ**: OS 例外の種類に応じて異なる回復処理を行いたい場合、`FileSystemError` のメッセージから種別を判断する必要がある。現状は例外の種別をサブクラスで分離していない。

### 書き込み時の親ディレクトリ自動作成

`TextFileSystemWriter.write()` は書き込み前に親ディレクトリを再帰的に作成する（`parents=True, exist_ok=True`）。

**理由**: 書き込み先ディレクトリの確認と作成を呼び出し元が毎回実装するのは定型的な前処理であり、ファイル書き込みの責務に含めるのが自然である。

**トレードオフ**: 意図しないディレクトリが自動作成される可能性がある。書き込みパスは呼び出し元が明示的に指定するため、リスクは呼び出し元の責任範囲となる。

## ガードレール

- エンコーディングは UTF-8 固定。UTF-8 以外が必要な場合は別途実装を用意すること
- 書き込みは上書きモード（追記が必要な場合は別途実装を用意すること）
- 公開 API は `FileSystemError`, `TextFileSystemReader`, `TextFileSystemWriter` のみ。`paladin.foundation.fs` パッケージから import すること
- `FileSystemError` 送出時には元の OS 例外を `from e` 構文で例外チェーンに保持すること
