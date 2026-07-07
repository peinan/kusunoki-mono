# Kusunoki Mono build orchestration.
# Config knobs live in config.sh; Iosevka design in private-build-plans.toml.

.DEFAULT_GOAL := build
.PHONY: setup iosevka merge build variants package dist-all verify clean distclean help

help: ## Show this help
	@grep -E '^[a-z].*:.*##' $(MAKEFILE_LIST) | sed 's/:.*##/\t/' | sort

setup: ## Install deps, download font sources, npm install
	@bash scripts/setup.sh

iosevka: ## Build the custom Iosevka base (Latin/ASCII/ligatures)
	@bash scripts/build_iosevka.sh

merge: ## Merge Iosevka + BIZ UDGothic + Nerd Fonts -> dist/
	@bash scripts/merge_all.sh

build: iosevka merge ## Full build of one variant: Iosevka, then merge (local dev)

variants: ## Build all 4 release variants (NF x ligatures); run after `make iosevka`
	@bash scripts/build_variants.sh

package: ## Zip each built variant into dist/release-assets/
	@bash scripts/package.sh

dist-all: iosevka variants package ## Full release build: base + 4 variants + zips

verify: ## Metric assertions + specimen (HTML) for the current variant
	@bash scripts/verify.sh

clean: ## Remove build/ and dist/
	@rm -rf build dist

distclean: clean ## Also remove downloaded sources/
	@rm -rf sources
