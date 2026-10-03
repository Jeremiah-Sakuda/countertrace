PYTHON ?= python3
VENV_PYTHON := .venv/bin/python

.PHONY: setup check test test-integration doctor image serve web

setup:
	$(PYTHON) -m venv .venv
	$(VENV_PYTHON) -m pip install --editable .
	$(VENV_PYTHON) -c 'from pathlib import Path; p = Path(".env"); p.exists() or p.write_bytes(Path(".env.example").read_bytes())'

check: test
	$(PYTHON) scripts/check_workspace.py
	PYTHONPATH=src $(PYTHON) -m countertrace --help > /dev/null
	git diff --check

# Unit tests and negative controls for trusted parsers; no Docker required.
test:
	PYTHONPATH=src $(PYTHON) -m unittest tests.test_contract tests.test_admission tests.test_evidence tests.test_model tests.test_audit tests.test_runner tests.test_recording

# Runs real RTL in the isolated verifier image. Requires Docker and `make image`.
test-integration:
	PYTHONPATH=src $(PYTHON) -m unittest -v tests.test_integration

doctor:
	PYTHONPATH=src $(PYTHON) -m countertrace doctor

image:
	PYTHONPATH=src $(PYTHON) -m countertrace build-image

web:
	cd apps/web && npm install && npm run build

serve:
	PYTHONPATH=src $(PYTHON) -m countertrace serve
