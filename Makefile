# SETTINGS
# Use one shell for all commands in a target recipe
.ONESHELL:
.DEFAULT_GOAL:=help
SHELL:=/bin/bash
.PHONY:=clean lint test help format snap qa install release
PACKAGE_NAME:=jobbergate_cli

include	snap.mk

install:
	poetry install

test: install
	poetry run pytest

lint: install
	poetry run black --check ${PACKAGE_NAME}
	poetry run isort --check ${PACKAGE_NAME}
	poetry run flake8 --max-line-length=120 --max-complexity=40 ${PACKAGE_NAME}

qa: test lint
	echo "All tests pass! Ready for deployment"

format: install
	poetry run black ${PACKAGE_NAME}
	poetry run isort ${PACKAGE_NAME}

clean: clean-eggs clean-build
	@find . -iname '*.pyc' -delete
	@find . -iname '*.pyo' -delete
	@find . -iname '*~' -delete
	@find . -iname '*.swp' -delete
	@find . -iname '__pycache__' -delete
	@rm -r .mypy_cache
	@rm -r .pytest_cache
	@find . -name '*.egg' -print0|xargs -0 rm -rf --
	@rm -rf .eggs/
	@rm -fr build/
	@rm -fr dist/
	@rm -fr *.egg-info

release-%:
	scripts/release.sh $(subst release-,,$@)

help: # Display target comments in 'make help'
	grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

snap: $(SNAP_TARGET)

$(SNAP_TARGET):
	sg lxd -c 'snapcraft --use-lxd'
