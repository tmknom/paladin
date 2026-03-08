# Include: minimum
-include .makefiles/minimum/Makefile
.makefiles/minimum/Makefile:
	@git clone https://github.com/tmknom/makefiles.git .makefiles >/dev/null 2>&1

# ==============================================================================
# Pythonローカル開発
# ==============================================================================

.PHONY: all
all: sync fmt lint typecheck test-unit ## 一括実行

.PHONY: sync-online
sync-online:
		uv sync

.PHONY: sync
sync:
		uv sync --offline

.PHONY: upgrade
upgrade: ## 依存パッケージを最新版に更新（uv.lockを更新）
		uv sync --upgrade

.PHONY: test
test: ## テスト実行
		uv run pytest

.PHONY: test-unit
test-unit: ## ユニットテスト実行
		uv run pytest tests/unit/

.PHONY: test-integration
test-integration: ## インテグレーションテスト実行
		uv run pytest tests/integration/

.PHONY: coverage
coverage: ## カバレッジの取得
		uv run pytest --cov=src --cov-report=html --cov-report=term --cov-report=term-missing

.PHONY: fmt
fmt: sync ## Ruffによるコードフォーマット
		uv run ruff format . --config=pyproject.toml

.PHONY: lint
lint: ## Ruffによる静的解析
		uv run ruff check . --fix --config=pyproject.toml

.PHONY: typecheck
typecheck: ## Pyrightによる型チェック
		uv run pyright --warnings

.PHONY: clean
clean: ## 中間ファイルを削除
		find . -type d -name "__pycache__" -exec rm -rf {} +
		find . -type f -name "*.pyc" -delete
		find . -type d -name ".pytest_cache" -exec rm -rf {} +
		find . -type d -name ".mypy_cache" -exec rm -rf {} +
		find . -type d -name ".ruff_cache" -exec rm -rf {} +
		find . -type d -name "htmlcov" -exec rm -rf {} +
		find . -type f -name ".coverage" -delete
