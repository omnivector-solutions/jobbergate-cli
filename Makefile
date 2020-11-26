# SETTINGS
# Use one shell for all commands in a target recipe
.ONESHELL:
# Set default goal
.DEFAULT_GOAL := help
# Use bash shell in Make instead of sh
SHELL := /bin/bash

VERSION = $(python setup.py --version)


clean: # Remove .tox and build dirs
	rm -rf .tox/
	rm -rf venv/


lint: # Run linter
	tox -e lint


test:
	tox -e unit
	# TODO: tox -e functional?


help: # Display target comments in 'make help'
	grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'


requirements/requirements.txt: setup.py
	python3 -m venv _virtual_tmp
	. _virtual_tmp/bin/activate \
		&& pip install wheel \
		&& pip install . \
		&& pip freeze > requirements/requirements.txt
	rm -rf _virtual_tmp


format:
	isort setup.py jobbergate_cli
	black setup.py jobbergate_cli
