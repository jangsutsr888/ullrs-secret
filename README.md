# Wet Bulb Temperature Calculator

Calculates altitude-adjusted wet bulb temperature from weather forecast data for backcountry ski conditions assessment. Supports NWS (weather.gov XML) data source.

## Install

```bash
pip install -e .
```

## Usage

### Quick start (auto-detect source)

```bash
./scripts/run.sh "https://forecast.weather.gov/..." 3
```

### Direct commands

```bash
wetbulb-nws downloaded_weather.xml --days 3
```

### Makefile

```bash
make run-nws FILE=downloaded_weather.xml DAYS=3
```

## Output

- `forecast_chart.png` — temperature chart with melt/freeze integrals
- `forecast_data.csv` — hourly data export

## Snow Quality Reference

| Condition | Threshold |
|-----------|-----------|
| Top tier powder | WBTDH 0–5 F-hrs |
| Critical degradation | WBTDH 15–20 F-hrs |
| Isothermal (ruined) | WBTDH > 35 F-hrs |
| Freeze failure (unsafe) | Night WBFDH < 10 F-hrs |
| Full reset | Night WBFDH > 50 F-hrs |

WBTDH = Melt Integral (T > 32°F), WBFDH = Freeze Integral (T < 32°F)
