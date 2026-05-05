"""Import weather data into standard JSON format."""

import json


def write_weather_json(data, output_path):
    """Write a standard weather data dict to JSON and print confirmation."""
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    n = len(data.get("observations", []))
    print(f"Wrote {n} observations to {output_path}")
