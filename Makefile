PYTHON ?= python3
VENV_PYTHON := .venv/bin/python

.PHONY: setup check doctor

setup:
	$(PYTHON) -m venv .venv
	$(VENV_PYTHON) -m pip install --editable .
	$(VENV_PYTHON) -c 'from pathlib import Path; p = Path(".env"); p.exists() or p.write_bytes(Path(".env.example").read_bytes())'

check:
	$(PYTHON) scripts/check_workspace.py
	PYTHONPATH=src $(PYTHON) -m countertrace --help
	git diff --check

doctor:
	PYTHONPATH=src $(PYTHON) -m countertrace doctor
