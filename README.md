# Ullr's Secret

Ullr's Secret is a Python command-line tool for estimating backcountry snow
surface conditions from hourly weather data. It adjusts weather for elevation,
slope, aspect, humidity, and radiation, then produces charts for powder
preservation, corn timing, and melt-freeze consolidation.

> **Safety:** This is a snow-quality decision aid, not an avalanche forecast.
> It does not model buried weak layers, wind slabs, terrain traps, or local
> avalanche hazard.

The model derivation is available as
[English](https://github.com/jangsutsr888/ullrs-secret/blob/main/core_calc_en.pdf)
and
[Chinese](https://github.com/jangsutsr888/ullrs-secret/blob/main/core_calc_cn.pdf)
PDFs. Detailed usage and model documentation live on
[Read the Docs](https://ullrs-secret.readthedocs.io/).

## Commands

| Command | Purpose |
| --- | --- |
| `import openmeteo` | Import a current multi-model forecast without credentials |
| `import nws` | Import a US National Weather Service forecast |
| `import era5` | Import historical ERA5 reanalysis data using CDS credentials |
| `pow-plot` | Estimate when fresh powder degrades |
| `corn-plot` | Estimate the spring corn window |
| `consolidation-plot` | Model dry snow, slush, and crust through melt-freeze cycles |
| `terrain` | Query elevation, slope, and aspect for a coordinate |
| `snotel-list`, `snotel` | Find and inspect nearby SNOTEL stations |

Each importer writes the same standard weather JSON format, which any chart
command can consume.

## Install

Python 3.10 or newer is required.

```console
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install ullrs-secret
ullrs-secret --help
```

See the
[installation runbook](https://ullrs-secret.readthedocs.io/en/latest/installation.html)
for source installation, verification, updates, Windows activation, and
contributor setup.

## Quick start

Import a forecast and generate a corn chart for a southeast-facing slope:

```console
ullrs-secret import openmeteo \
    --lat 46.8523 --lon -121.7603 \
    --model best_match \
    --output weather_data.json

ullrs-secret corn-plot weather_data.json \
    --slope 35 --aspect 135 --elevation 9000 \
    --no-show --output corn_forecast_chart.png
```

Use `ullrs-secret COMMAND --help` for the current CLI options. The dedicated
documentation pages explain the algorithms and include output from the
integration tests:

- [Chart commands](https://ullrs-secret.readthedocs.io/en/latest/charts/index.html)
- [Weather importers](https://ullrs-secret.readthedocs.io/en/latest/importers/index.html)
- [Effective-temperature model](https://ullrs-secret.readthedocs.io/en/latest/model.html)
- [Limitations and field use](https://ullrs-secret.readthedocs.io/en/latest/limitations.html)

## Documentation

Build and validate the classic Sphinx site:

```console
make docs-check
```

Serve it at <http://127.0.0.1:8000/>:

```console
make docs-serve
```

## Tests

```console
make test
```

The integration tests query live terrain data and regenerate the three example
images. Run them without opening Matplotlib windows with:

```console
ULLRS_SECRET_NO_SHOW=1 make integration_test
```

## License

GNU Affero General Public License v3.0 or later. See
[LICENSE](https://github.com/jangsutsr888/ullrs-secret/blob/main/LICENSE).
