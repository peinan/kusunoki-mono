# Kusunoki Mono build orchestration.
# Config knobs live in config.sh; Iosevka design in private-build-plans.toml.

.DEFAULT_GOAL := build
.PHONY: setup iosevka merge build verify clean distclean help

help: ## Show this help
	@grep -E '^[a-z].*:.*##' $(MAKEFILE_LIST) | sed 's/:.*##/\t/' | sort

setup: ## Install deps, download font sources, npm install
	@bash scripts/setup.sh

iosevka: ## Build the custom Iosevka base (Latin/ASCII/ligatures)
	@bash scripts/build_iosevka.sh

merge: ## Merge Iosevka + BIZ UDGothic + Nerd Fonts -> dist/
	@bash scripts/merge_all.sh

build: iosevka merge ## Full build: Iosevka, then merge

verify: ## Metric assertions + specimen (HTML/PNG)
	@bash scripts/verify.sh

clean: ## Remove build/ and dist/
	@rm -rf build dist

distclean: clean ## Also remove downloaded sources/
	@rm -rf sources
