# Use the project virtualenv once `make setup` has created it.
PYTHON ?= $(shell [ -x .venv/bin/python ] && echo .venv/bin/python || echo python3)
VENV_PYTHON := .venv/bin/python
PYTHON_GUARD = $(PYTHON) -c 'import sys; sys.exit("Countertrace needs Python 3.11 or newer; found " + sys.version.split()[0] + ". Run: make setup PYTHON=python3.12") if sys.version_info < (3, 11) else None'

.PHONY: setup check test test-integration doctor image serve web static-demo

setup:
	@$(PYTHON_GUARD)
	$(PYTHON) -m venv .venv
	$(VENV_PYTHON) -m pip install --editable .
	$(VENV_PYTHON) -c 'from pathlib import Path; p = Path(".env"); p.exists() or p.write_bytes(Path(".env.example").read_bytes())'

check: test
	$(PYTHON) scripts/check_workspace.py
	PYTHONPATH=src $(PYTHON) -m countertrace --help > /dev/null
	git diff --check

# Unit tests and negative controls for trusted parsers; no Docker required.
test:
	@$(PYTHON_GUARD)
	PYTHONPATH=src $(PYTHON) -m unittest tests.test_contract tests.test_admission tests.test_evidence tests.test_model tests.test_audit tests.test_runner tests.test_recording tests.test_interface_map tests.test_server tests.test_repair tests.test_static_demo

# Runs real RTL in the isolated verifier image. Requires Docker and `make image`.
test-integration:
	PYTHONPATH=src $(PYTHON) -m unittest -v tests.test_integration

doctor:
	PYTHONPATH=src $(PYTHON) -m countertrace doctor

image:
	PYTHONPATH=src $(PYTHON) -m countertrace build-image

web:
	cd apps/web && npm install && npm run build

# Build only the curated recorded journey; no .env, local runs, or model calls.
static-demo:
	npm --prefix apps/web ci
	npm --prefix apps/web run build
	PYTHONPATH=src $(PYTHON) scripts/build_static_demo.py

serve:
	PYTHONPATH=src $(PYTHON) -m countertrace serve
