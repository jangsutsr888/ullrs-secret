.PHONY: install test integration_test docs-install docs-assets docs-build docs-serve docs-check clean

VENV := venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

venv:
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip 2>/dev/null || true

install: venv
	$(PIP) install -e ".[test]"

test: install
	$(PYTHON) -m pytest tests/

integration_test: install
	$(PYTHON) integration_test/run_pow.py
	$(PYTHON) integration_test/run_consolidation.py
	$(PYTHON) integration_test/run_corn.py

$(VENV)/bin/sphinx-build: setup.py | venv
	$(PIP) install -e ".[docs]"

docs-install: $(VENV)/bin/sphinx-build

docs-assets: | venv
	$(PYTHON) scripts/prepare_docs_assets.py

docs-build: docs-install docs-assets
	$(VENV)/bin/sphinx-build -M html docs docs/_build -W --keep-going

docs-serve: docs-build
	$(PYTHON) -m http.server 8000 --directory docs/_build/html

docs-check: docs-build
	$(PYTHON) scripts/check_docs.py docs/_build/html

clean:
	rm -rf $(VENV) build/ dist/ *.egg-info
	rm -rf docs/_build/ docs/_generated/
	rm -f downloaded_data.tmp weather_data.json
