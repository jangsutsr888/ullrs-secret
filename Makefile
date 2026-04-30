.PHONY: install dev clean import plot run

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

import: install
	@test -n "$(TYPE)" || (echo "Usage: make import TYPE=nws SOURCE=<url_or_file> [OUTPUT=weather_data.json]" && exit 1)
	@test -n "$(SOURCE)" || (echo "Usage: make import TYPE=nws SOURCE=<url_or_file> [OUTPUT=weather_data.json]" && exit 1)
	$(PYTHON) -m wetbulb_calc.import_data $(TYPE) "$(SOURCE)" -o $(or $(OUTPUT),weather_data.json)

plot: install
	@test -n "$(FILE)" || (echo "Usage: make plot FILE=weather_data.json [DAYS=3]" && exit 1)
	$(PYTHON) -m wetbulb_calc.plot $(FILE) --days $(or $(DAYS),3)

run: install
	@test -n "$(TYPE)" || (echo "Usage: make run TYPE=nws SOURCE=<url_or_file> [DAYS=3]" && exit 1)
	@test -n "$(SOURCE)" || (echo "Usage: make run TYPE=nws SOURCE=<url_or_file> [DAYS=3]" && exit 1)
	$(PYTHON) -m wetbulb_calc.import_data $(TYPE) "$(SOURCE)" -o weather_data.json
	$(PYTHON) -m wetbulb_calc.plot weather_data.json --days $(or $(DAYS),3)
