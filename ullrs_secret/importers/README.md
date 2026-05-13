# Weather Data Importers

This directory contains the data importers for `ullrs-secret`. Importers are responsible for fetching weather data from various sources and converting it into the standard JSON format required by the core calculation engine.

## Supported Importers

### National Weather Service (NWS)
NWS provides forecast data for locations in the US.

```bash
$ ullrs-secret import nws --help
Usage: ullrs-secret import nws [OPTIONS]

  Fetch and parse NWS weather data from the MapClick API.

Options:
  --lat FLOAT        Latitude of the location (+ for North, - for South)  [required]
  --lon FLOAT        Longitude of the location (+ for East, - for West)  [required]
  -o, --output TEXT  Output JSON path.
  --help             Show this message and exit.
```

Example:
```bash
# Weather data of Newton Clark Glacier of Mt Hood
$ ullrs-secret import nws --lat 45.3668 --lon -121.6867 -o weather_data.json
Matched nearest NWS grid point: Lat 45.3668, Lon -121.6867
Distance from input location: 0.00 miles
Wrote 168 observations to weather_data.json
```

### ERA5 Reanalysis
Copernicus CDS API for ERA5 global reanalysis data.

```bash
$ ullrs-secret import era5 --help
Usage: ullrs-secret import era5 [OPTIONS]

  Fetch and parse ERA5 reanalysis data via Copernicus CDS API.

Options:
  --lat FLOAT          Latitude of the location (+ for North, - for South)  [required]
  --lon FLOAT          Longitude of the location (+ for East, - for West)  [required]
  --start-date TEXT    Start date (YYYY-MM-DD)  [required]
  --end-date TEXT      End date (YYYY-MM-DD)  [required]
  --timezone TEXT      Timezone (default: America/Los_Angeles)
  -o, --output TEXT    Output JSON path.
  --help               Show this message and exit.
```

## Standard Weather Data Format

All importers produce the same JSON format. This is the contract between data sources and the plotting/calculation engine:

```json
{
  "source": "nws",
  "latitude": 45.3668,
  "longitude": -121.6867,
  "elevation_ft": 9167.0,
  "observations": [
    {
      "time_iso": "2026-04-29T21:00:00-07:00",
      "air_temp_f": 26.0,
      "relative_humidity_pct": 54.0,
      "dew_point_f": 12.0,
      "cloud_cover_pct": 40.0
    }
  ]
}
```

| Field | Description |
|-------|-------------|
| `source` | Importer name (for provenance tracking) |
| `latitude` | Station latitude in decimal degrees. Can be `null` if unavailable. |
| `longitude` | Station longitude in decimal degrees. Can be `null` if unavailable. |
| `elevation_ft` | Station elevation in feet above sea level. Used to calculate local atmospheric pressure, which affects the psychrometric wet bulb equation. |
| `observations[].time_iso` | ISO-8601 timestamp with timezone offset. Hourly resolution is expected. |
| `observations[].air_temp_f` | Air temperature in Fahrenheit. Can be `null` if missing. |
| `observations[].relative_humidity_pct` | Relative humidity as a percentage (0-100). Can be `null` if missing. Together with air temperature, these are the two physical inputs needed to solve for wet bulb temperature. |
| `observations[].dew_point_f` | Dew point temperature in Fahrenheit. Can be `null` if missing or unavailable from the data source. |
| `observations[].cloud_cover_pct` | Total cloud cover as a percentage (0-100). Can be `null` if missing or unavailable from the data source. |

Elevation, air temperature, and relative humidity are the only physical values your data source needs to provide. Everything else (atmospheric pressure, saturation vapor pressure, wet bulb temperature) is derived. Dew point, cloud cover, and lat/long are optional supplementary fields.

## Adding a New Importer

NWS only covers US locations. If you ski in Canada, Europe, Japan, or anywhere else, you need a different weather data source. Adding an importer makes this tool work for your mountains.

To add a new data source, create a file in `ullrs_secret/importers/` (e.g., `spotwx.py`):

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
        "latitude": 49.0,
        "longitude": -122.5,
        "elevation_ft": 6500.0,
        "observations": [
            {
                "time_iso": "2026-04-29T12:00:00-07:00",
                "air_temp_f": 28.0,
                "relative_humidity_pct": 72.0,
                "dew_point_f": 20.0,
                "cloud_cover_pct": 55.0,
            },
            # ...
        ],
    }
```

Then register it in `ullrs_secret/importers/__init__.py`:

```python
from . import nws  # noqa: E402, F401
from . import spotwx  # noqa: E402, F401
```

That's it. Your importer automatically appears under `ullrs-secret import spotwx`.