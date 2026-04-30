.PHONY: install dev clean

VENV := venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

venv:
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip 2>/dev/null || true

install: venv
	$(PIP) install -e .

dev: venv
	$(PYTHON) setup.py develop

clean:
	rm -rf $(VENV) build/ dist/ *.egg-info
	rm -f downloaded_data.tmp weather_data.json
