# ifeq ($(OS),Windows_NT)
# SHELL := powershell.exe
# .SHELLFLAGS := -Command
# endif

# Sources to run type-checkers / linters against
sources = src tests examples
# Default commit message with `make commit`
m = fix(lazy): Various fixes & updates

default: help

define HELP_BODY
Usage:
	make <command>

Commands:
	setup               Setup the repository - recommended to use right after cloning
	sync                Install dependencies
	update              Update dependencies
	run                 Run the bot
	lint                Run the linter
	format              Format the code
	format-check        Check code formatting
	tests               Run the tests
	pages               Locally run the github pages website
	ty                  Run ty (beta testing ty typechecker)
	basedpyright        Run basedpyright
	commit              Lazy git commit and push+
	com                 This creates and pushes commits to IreBot repository
	echo                Testing stuff with make, why don't we test it with echo
endef

.PHONY: help
.SILENT: help
# TODO: Look into ways to automatically gather output for this command.
# The struggle is that Windows Terminal doesn't have any normal working `grep`; 
# and vice-versa windows grep-like tools won't work for linux
help:  # Help
	$(info $(HELP_BODY))


.PHONY: setup
.SILENT: setup
setup:  # Setup the repository - recommended to use right after cloning
	git submodule update --init --recursive
	uv sync
	prek install


.PHONY: sync
.SILENT: sync
sync:  # Install dependencies
	uv sync

.PHONY: update
.SILENT: update
update:  # Update dependencies
	uv lock --upgrade
	uv sync
	prek autoupdate

.PHONY: run
.SILENT: run
run:  # Run the bot
	uv run src/main.py --subset-mode

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

.PHONY: tests
.SILENT: tests
tests:  # Run the tests
	uv run pytest

.PHONY: pages
.SILENT: pages
pages:  # Run the pages
	cd docs && \
	bundle exec jekyll serve

.PHONY: ty
.SILENT: ty
ty:  # Run ty (beta testing ty typechecker)
	uv run ty check .

.PHONY: basedpyright
.SILENT: basedpyright
basedpyright:  # Run basedpyright
	uv run basedpyright $(sources)

.PHONY: commit
.SILENT: commit
# Lazy git commit commands, use make commit m="Fix this and that" for custom commit messages.
# This creates and pushes commits to both IreBot and Shared-Bot-Utilities repositories.
commit:  
	cd src/shared && git add .
	chcp 65001>nul && cd src/shared && git commit -a -m "$(m)"
	cd src/shared && git push
	git add .
	chcp 65001>nul && git commit -a -m "$(m)"
	git push

.PHONY: com
.SILENT: com
# This creates and pushes commits to IreBot repository
com:  
	git add .
	git commit -a -m "$(m)"
	git push

.PHONY: echo
.SILENT: echo
echo:  # Testing stuff with make, why don't we test it with echo
	echo $(SHELL)
	chcp 65001>nul && echo "$(m)"
# 	@Write-Output $(m)
# 	printf '%s\n' "$sample"
