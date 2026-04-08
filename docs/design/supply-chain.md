# サプライチェーンセキュリティ設計

## 目的

このドキュメントは、サードパーティライブラリを安全に運用するための方針とその設計意図を記録する。

「何をしているか」だけでなく「何を検討した上でやらないと決めたか」を残すことで、将来の判断基準とする。

## 脅威モデル

本ツールは Web サービスではなく **CLI ツール** である。この前提は脅威モデルに大きく影響する。

Web サービスでは「本番サーバで継続的に依存を更新する」場面が主な攻撃面になるが、CLI ツールでは以下の場面が優先される。

- **開発時**: 開発者のマシンで `uv sync` を実行する
- **ビルド時**: `make upgrade` で依存を更新し `uv.lock` を再生成する
- **利用者のインストール時**: `pip install paladin` や `uv tool install paladin` を実行する

したがって、CI/CD パイプラインの保護より「依存解決・インストール時に余計なコードを動かさない」ことを最優先に置く。

## 実施している対策

### 依存の最小化

runtime 依存を 4 個に絞っている (`colorlog`, `pydantic`, `pydantic-settings`, `typer`)。

攻撃面は依存の個数に比例する。「便利だから」で追加する小物ライブラリは、ローカル実行の攻撃面を増やす割に得るものが小さい。新しい依存を追加する際は、標準ライブラリで代替できないか必ず検討する。

### `uv.lock` のコミットとオフライン sync

`uv.lock` を `.gitignore` から除外し、リポジトリにコミットしている。すべてのパッケージが SHA-256 ハッシュ付きで固定されるため、再現性が保証される。

`make sync` は `uv sync --offline` を実行し、ネットワークアクセスなしで既存の lock から環境を再構成する。日常の開発では意図しない依存解決が発生しない。

### `no-sources = true` (`pyproject.toml`)

```toml
[tool.uv]
no-sources = true
```

`tool.uv.sources` を無視し、standards-compliant な依存のみで解決する設定である。Git/path 依存が `uv.lock` に混入することを防ぐガードレールとして機能する。

uv の公式ドキュメントでは `--no-sources` を CLI フラグとして説明しており、`uv build --no-sources` による release check 用途として推奨している。

現在 `[tool.uv.sources]` を使用していないため、`pyproject.toml` への常設でも開発フロー (`uv sync`) は壊れない。`[tool.uv.sources]` を使わない限り、設定ファイルに書いても CLI フラグとして実行しても効果は同等である。

使い始める場面が生じた場合は、この設定を外し、理由をコミットすること。

### `required-version` (`pyproject.toml`)

```toml
[tool.uv]
required-version = ">=0.11.0,<0.12"
```

uv 自体のバージョン範囲を固定する。範囲外の uv で操作しようとすると実行時エラーになる。

lockfile のフォーマットは uv のメジャーバージョンをまたぐ変更で非互換になる場合がある。バージョン範囲を明示することで、意図しない lockfile 形式の変化を防ぐ。上限は `<0.12` に設定し、メジャーバージョン更新時は意識的に更新する運用とする。

### `--exclude-newer "1 week"` (`make upgrade`)

```makefile
upgrade:
    uv sync --upgrade --exclude-newer "1 week"
```

`make upgrade` 実行時のみ、1 週間以内にリリースされたパッケージを候補から除外する。

リリース直後の悪意あるパッケージが検出・削除されるまでの猶予期間を確保する。通常の `uv sync` / `uv sync --offline` には適用されず、既存の lock から install する場合には影響しない。

`pyproject.toml` の `[tool.uv]` に `exclude-newer` を書かないのは、`uv sync --offline` が再解決を試みてオフラインで失敗するためである (後述「採用しなかった対策」参照)。

### `make lock-check`

```makefile
lock-check:
    uv lock --check
```

`pyproject.toml` を編集した後に `uv.lock` の再生成を忘れていないかを検証する。`pyproject.toml` と `uv.lock` が乖離している状態を検出できる。

`make all` には含めていない。`make all` が依存する `make sync` (`uv sync --offline`) が暗黙的に同等の検証を行うためである。

### `make audit`

```makefile
audit:
    uv tool run pip-audit
```

pip-audit を ephemeral 環境で実行し、OSV データベースを使って既知の脆弱性を持つパッケージを検出する。プロジェクトの依存に追加する必要はなく、`uv tool run` で都度ダウンロードして実行できる。

pip-audit の README に「悪意あるパッケージそのものを防ぐものではない」と明記されている。`make audit` は補助ツールであり、これ単体で安全性を担保するものではない。

### `.python-version`

Python 3.13 を明示したファイルをコミットし、uv が Python インタープリタを自動選択できるようにする。パッチバージョンは固定せず、`3.13.x` の範囲内でのセキュリティ修正を受け入れる。

### Dependabot uv エコシステム (weekly)

```yaml
- package-ecosystem: uv
  directory: /
  schedule:
    interval: weekly
  open-pull-requests-limit: 5
```

依存更新を週次の PR として提案させ、人手レビューを挟む。`--exclude-newer "1 week"` と組み合わせることで二重の遅延防御を形成する。`open-pull-requests-limit: 5` で PR が氾濫しないようにする。

## 採用しなかった対策

### `no-build = true` (`[tool.uv]`)

`no-build = true` は依存解決時に source distribution をビルドせず、任意の Python コード実行を防ぐ設定である。CLI ツールとして有効な防御層だが、**editable install との非互換** があり採用しなかった。

`uv sync` はプロジェクト自体 (`paladin`) を editable モードでインストールするが、`no-build = true` はこれにも適用される。`no-build-package = ["paladin"]` による除外を試みたが、現行バージョンでは editable パッケージの除外が機能せず、`uv sync` が常にエラーになった。

なお、現時点の全依存はすべて wheel を持つため、`no-build = true` がなくとも source build は発生していない。

第三者依存の解決だけをプロジェクト自身の editable install と切り離して検証したい場合は、`uv sync --no-install-project` が使える。これはプロジェクト本体を仮想環境に入れず、外部依存だけを同期するオプションである。

### `exclude-newer` を `[tool.uv]` に書く

```toml
# 採用しなかった設定
[tool.uv]
exclude-newer = "7 days"
```

`[tool.uv]` に書くと `uv sync --offline` も再解決を試みる。`uv.lock` にキャッシュされていないパッケージを要求するため、オフラインモードでエラーになる。`make sync` はオフライン sync であるため、この設定はデフォルトの開発フローを壊す。

回避策として `make upgrade` の引数として `--exclude-newer "1 week"` を渡す形を採用した。

### `index-strategy = "first-index"` の明示

uv のデフォルト値は `first-index` で、最初に見つかった index のみを使う。dependency confusion 対策として機能するが、本リポジトリは PyPI 一本であり追加 index を持たない。デフォルト値を明示することは設定のノイズになる。追加 index を導入するときに、その設計判断と合わせて記述する。

### `package = true` の明示

uv のデフォルト値が `true` であり、`[build-system]` が存在する本リポジトリは既に package として扱われている。デフォルト値の明示は不要。

### `[tool.uv.pip]` セクション

`[tool.uv.pip]` の設定 (`only-binary`, `generate-hashes` 等) は `uv pip install` / `uv pip compile` 専用で、`uv sync` / `uv lock` には適用されない。本リポジトリは `uv sync` を使うため、このセクションは開発フローに影響しない。

hash 付き requirements の副生成物 (`uv pip compile --generate-hashes`) は、利用者に厳格なインストール経路を提供する場合に有効だが、現段階では PyPI 配布自体を行っていないため時期尚早である。

### `uv sync` から `uv pip` 系コマンドへの移行

`uv pip` 系に移行すれば `[tool.uv.pip]` の `no-build` 等が設定でき、`uv sync` で断念した設定を有効にできる。しかし、失うものが大きすぎるため採用しなかった。

失われる機能は以下のとおりである。

- `uv.lock` の自動管理: `uv pip compile` による手動生成が必要になる
- ユニバーサル解決: `requirements.txt` はプラットフォーム固有で、`uv.lock` の上位互換ではない
- `uv run` との統合: `uv run pytest`、`uv run ruff` 等、Makefile の大半のコマンドがプロジェクトインターフェース前提
- editable install の自動化: `uv pip install -e .` の手動実行が必要になる
- exact sync: 仮想環境から不要パッケージを自動削除する機能がなくなる

uv の公式ドキュメントでも `uv pip` は「pip/pip-tools からの移行途中のプロジェクト向け」と位置づけられており、新規プロジェクトにはプロジェクトインターフェース (`uv sync` / `uv lock` / `uv run`) が推奨されている。

`uv sync` で断念した設定 (`no-build`, `exclude-newer` 常設) は既に別の回避策でカバーされており、`uv pip` 系に移行してまで解決すべき問題ではない。

### SBOM / attestation

uv は `uv.lock` から CycloneDX SBOM を export できる。PyPI の digital attestation は「どこから publish されたか」の保証を強める手段である。ただし、どちらもコード自体の安全性を保証するものではなく、現段階の CLI ツールで導入するには過剰である。

### `required-environments`

sdist がないパッケージについて、指定したプラットフォーム向け wheel の存在を lock 時に保証する設定である。クロスプラットフォーム配布を行う際に有効だが、現在は PyPI 配布を行っておらず、リリースは GitHub Releases のみである。配布戦略が確定してから検討する。
