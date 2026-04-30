# Wet Bulb Temperature Calculator

Calculates altitude-adjusted wet bulb temperature from weather forecast data for backcountry ski conditions assessment.

## Install

```bash
pip install -e .
```

## Commands

### Import weather data

Fetch forecast data from a source and save as standardized JSON.

```bash
wetbulb-calc import nws <url_or_file> -o weather_data.json
```

### Generate forecast chart

Read the JSON, compute wet bulb temps, and produce a chart and CSV.

```bash
wetbulb-calc plot weather_data.json --days 3
```

### Import and plot in one step

```bash
wetbulb-calc run nws <url_or_file> --days 3
```

### One-off wet bulb calculation

```bash
wetbulb-calc calc --temp 32 --rh 65 --elevation 9000
```

### Help

```bash
wetbulb-calc --help
wetbulb-calc import --help
wetbulb-calc import nws --help
```

## Output

- `forecast_chart.png` — temperature chart with melt/freeze integrals
- `forecast_data.csv` — hourly data export

## Snow Quality Reference

| Condition | Threshold |
|-----------|-----------|
| Top tier powder | WBTDH 0-5 F-hrs |
| Critical degradation | WBTDH 15-20 F-hrs |
| Isothermal (ruined) | WBTDH > 35 F-hrs |
| Freeze failure (unsafe) | Night WBFDH < 10 F-hrs |
| Full reset | Night WBFDH > 50 F-hrs |

WBTDH = Melt Integral (T > 32 F), WBFDH = Freeze Integral (T < 32 F)
