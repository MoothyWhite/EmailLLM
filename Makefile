# Makefile for code quality checks

# 默认目标
.PHONY: help
help:
	@echo "Code Quality Checks"
	@echo "=================="
	@echo "make check      - Run all code quality checks"
	@echo "make ruff       - Run Ruff linting"
	@echo "make ruff-fix   - Run Ruff auto-fix"
	@echo "make mypy       - Run Mypy type checking"
	@echo "make format     - Format code with Ruff"
	@echo "make format-fix - Format code with Ruff"
	@echo "make tests      - Run all tests"
	@echo "make sync       - Sync dependencies"

# 运行所有代码质量检查
.PHONY: check
check: format ruff mypy tests

# 运行Ruff linting
.PHONY: ruff
ruff:
	@echo "Running Ruff linting..."
	uv run ruff check

# 运行Ruff自动修复
.PHONY: ruff-fix
ruff-fix:
	@echo "Running Ruff auto-fix..."
	uv run ruff check --fix 

# 运行Mypy类型检查
.PHONY: mypy
mypy:
	@echo "Running Mypy type checking..."
	uv run mypy . --exclude 'site'

# 格式化代码
.PHONY: format
format:
	@echo "Checking code format with Ruff..."
	uv run ruff format --check

# 格式化代码
.PHONY: format-fix
format-fix:
	@echo "Formatting code with Ruff..."
	uv run ruff format

# 运行所有测试
.PHONY: tests
tests: 
	@echo "Running all tests..."
	uv run pytest 

# 同步依赖
.PHONY: sync
sync:
	@echo "Syncing dependencies..."
	uv sync
