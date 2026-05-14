sources = src tests

default: help

.PHONY: help
# ToDo: Look into ways to automatically gather output for this command.
# The struggle is that Windows Terminal doesn't have `grep` and vice-versa, windows grep-like tools won't work for linux
help:  # Help
	@echo IreBot Makefile
	@echo ---------------
	@echo * make sync: Install dependencies
	@echo * make update: Update dependencies
	@echo * make run: Run the bot
	@echo * make lint: Run the linter
	@echo * make format: Format the code
	@echo * make format-check: Check code formatting
	@echo * make tests: Run the tests

.PHONY: sync
.SILENT: sync
sync:  # Install dependencies
	uv sync --all-extras --all-packages --group dev

.PHONY: update
.SILENT: update
update:  # Update dependencies
	uv lock --upgrade
	uv sync --all-extras --all-packages --group dev

.PHONY: run
.SILENT: run
run:  # Run the bot
	uv run src/main.py

.PHONY: lint
.SILENT: lint
lint:  # Run the linter
	uv run ruff check $(sources)
	uv run ruff format --check $(sources)

.PHONY: format
.SILENT: format
format:  # Format the code
	uv run ruff check $(sources) --fix
	uv run ruff format $(sources)

.PHONY: format-check
.SILENT: format-check
format-check:  # Check code formatting
	uv run ruff format --check $(sources)

.PHONY: tests
.SILENT: tests
tests:  # Run the tests
	uv run pytest