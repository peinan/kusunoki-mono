# Kusunoki Mono (SF Mono Square edition) — build orchestration.
# A personal build recipe; the output embeds Apple SF Mono and is not
# redistributable. See README.md.
.DEFAULT_GOAL := build
.PHONY: setup build clean help

help: ## Show this help
	@grep -E '^[a-z].*:.*##' $(MAKEFILE_LIST) | sed 's/:.*##/\t/' | sort

setup: ## Fetch sources (SF Mono, Migu 1M, nerd-fonts patcher, LINE Seed JP, Google Sans Code)
	@bash scripts/sfmono/setup.sh

build: ## Build the 4 styles into build/sfms/dist/
	@bash scripts/sfmono/build.sh

clean: ## Remove build artifacts (keeps fetched sources/)
	@rm -rf build
