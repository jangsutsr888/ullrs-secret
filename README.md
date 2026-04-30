# Wet Bulb Temperature Calculator

Calculates altitude-adjusted wet bulb temperature from weather forecast data for backcountry ski conditions assessment.

Ask AI this question to start with: What is Wet Bulb Temprature, and what it means for powder preservation & corn formation.

## Prerequisite

py3.10+ (only tested in py3.10)

## Install

Use make target `make install` will install the CLI in a venv, then
```bash
venv/bin/activate
```

## Usage

```
$ wetbulb-calc --help
Usage: wetbulb-calc [OPTIONS] COMMAND [ARGS]...

  Wet bulb temperature calculator for backcountry ski forecasting.

Options:
  --help  Show this message and exit.

Commands:
  calc                One-off wet bulb temperature calculation.
  consolidation-plot  Compute melt-freeze consolidation model and plot...
  import              Import weather data from a source into standard JSON.
  plot                Read standard JSON, compute wet bulb temps, generate...
  run                 Import data and plot in one step.
```

### Import weather data

```
$ wetbulb-calc import --help
Usage: wetbulb-calc import [OPTIONS] COMMAND [ARGS]...

  Import weather data from a source into standard JSON.

Options:
  --help  Show this message and exit.

Commands:
  nws  Fetch and parse NWS weather data from a URL or local XML file path.
```

```
$ wetbulb-calc import nws --help
Usage: wetbulb-calc import nws [OPTIONS] SOURCE

  Fetch and parse NWS weather data from a URL or local XML file path.

Options:
  -o, --output TEXT  Output JSON path.
  --help             Show this message and exit.
```

```
# Weather data of Newton Clark Glacier of Mt Hood
$ wetbulb-calc import nws "https://forecast.weather.gov/MapClick.php?lat=45.3668&lon=-121.6867&FcstType=digitalDWML"
Wrote 168 observations to weather_data.json
```

### Generate forecast chart

```
$ wetbulb-calc plot --help
Usage: wetbulb-calc plot [OPTIONS] FILE

  Read standard JSON, compute wet bulb temps, generate chart and CSV.

Options:
  --days FLOAT  Number of forecast days.
  --help        Show this message and exit.
```

```
$ wetbulb-calc plot --days 4.5 weather_data.json
Elevation: 9167.0 ft. Local pressure: 719.64 hPa
Chart saved to: forecast_chart.png
Data saved to: forecast_data.csv
```

### Import and plot in one step

```
$ wetbulb-calc run nws --help
Usage: wetbulb-calc run nws [OPTIONS] SOURCE

  Import from nws and plot.

Options:
  -o, --output TEXT  Output JSON path.
  --days FLOAT       Number of forecast days.
  --help             Show this message and exit.
```

```
# Weather data of Nisqually Glacier of Mt Rainier
$ wetbulb-calc run nws --days 3 "https://forecast.weather.gov/MapClick.php?lat=46.829&lon=-121.7431&FcstType=digitalDWML"
Wrote 168 observations to weather_data.json
Elevation: 9485.0 ft. Local pressure: 710.86 hPa
Chart saved to: forecast_chart.png
Data saved to: forecast_data.csv
```

### Consolidation model (melt-freeze structural analysis)

```
$ wetbulb-calc consolidation-plot --help
Usage: wetbulb-calc consolidation-plot [OPTIONS] FILE

  Compute melt-freeze consolidation model and plot D_total curve.

Options:
  --days FLOAT  Number of forecast days.
  --snow FLOAT  Initial new snow depth in cm.
  --help        Show this message and exit.
```

```
$ wetbulb-calc consolidation-plot --days 4.5 --snow 25 weather_data.json
Elevation: 9167.0 ft. Local pressure: 719.64 hPa
Chart saved to: d_total_curve.png
Data saved to: consolidation_forecast_data.csv
```

This models how melt-freeze cycles structurally consolidate new snow into a supportable corn base. The chart tracks cumulative consolidated depth (D_total) and marks when it crosses the support threshold — the point where the base locks in and steep lines become viable.

### One-off wet bulb calculation

```bash
wetbulb-calc calc --temp 32 --rh 65 --elevation 9000
```

## Output

- `forecast_chart.png` — temperature chart with melt/freeze integrals
- `forecast_data.csv` — hourly data export
- `d_total_curve.png` — consolidation model chart (from `consolidation-plot`)
- `consolidation_forecast_data.csv` — consolidation model data export

## Standard Weather Data Format

All importers produce the same JSON format. This is the contract between data sources and the plotting/calculation engine:

```json
{
  "source": "nws",
  "elevation_ft": 9167.0,
  "observations": [
    {
      "time_iso": "2026-04-29T21:00:00-07:00",
      "air_temp_f": 26.0,
      "relative_humidity_pct": 54.0
    }
  ]
}
```

| Field | Description |
|-------|-------------|
| `source` | Importer name (for provenance tracking) |
| `elevation_ft` | Station elevation in feet above sea level. Used to calculate local atmospheric pressure, which affects the psychrometric wet bulb equation. |
| `observations[].time_iso` | ISO-8601 timestamp with timezone offset. Hourly resolution is expected. |
| `observations[].air_temp_f` | Air temperature in Fahrenheit. Can be `null` if missing. |
| `observations[].relative_humidity_pct` | Relative humidity as a percentage (0-100). Can be `null` if missing. Together with air temperature, these are the two physical inputs needed to solve for wet bulb temperature. |

Elevation, air temperature, and relative humidity are the only physical values your data source needs to provide. Everything else (atmospheric pressure, saturation vapor pressure, wet bulb temperature) is derived.

## Adding a New Importer

NWS only covers US locations. If you ski in Canada, Europe, Japan, or anywhere else, you need a different weather data source. Adding an importer makes this tool work for your mountains.

To add a new data source, create a file in `wetbulb_calc/importers/` (e.g., `spotwx.py`):

```python
"""SpotWx data importer."""

import click

from . import register


# Define whatever Click arguments/options your source needs.
# NWS just takes a URL, but yours might need an API key, coordinates, etc.
SPOTWX_DECORATORS = [
    click.option("--api-key", required=True, help="SpotWx API key."),
    click.option("--lat", type=float, required=True, help="Latitude."),
    click.option("--lon", type=float, required=True, help="Longitude."),
]


@register("spotwx", decorators=SPOTWX_DECORATORS)
def fetch(api_key, lat, lon):
    """Fetch weather data from SpotWx API."""
    # Your fetch logic here — must return the standard dict:
    return {
        "source": "spotwx",
        "elevation_ft": 6500.0,
        "observations": [
            {
                "time_iso": "2026-04-29T12:00:00-07:00",
                "air_temp_f": 28.0,
                "relative_humidity_pct": 72.0,
            },
            # ...
        ],
    }
```

Then register it in `wetbulb_calc/importers/__init__.py`:

```python
from . import nws  # noqa: E402, F401
from . import spotwx  # noqa: E402, F401
```

That's it. Your importer automatically appears under both `wetbulb-calc import spotwx` and `wetbulb-calc run spotwx`.
