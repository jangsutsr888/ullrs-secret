"""Import weather data into standard JSON format."""

import json
from typing import Dict, Any

def write_weather_json(data: Dict[str, Any], output_path: str) -> None:
    """
    Write a standard weather data dict to JSON and print confirmation.
    
    :param data: The standard weather data dictionary to write.
    :type data: Dict[str, Any]
    :param output_path: Path to the output JSON file.
    :type output_path: str
    """
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    n = len(data.get("observations", []))
    print(f"Wrote {n} observations to {output_path}")
