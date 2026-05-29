import json
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import List, Optional, Tuple

import pytz

PT_ZONE = pytz.timezone("America/Los_Angeles")

@dataclass
class Observation:
    time_iso: str
    air_temp_f: float
    relative_humidity_pct: Optional[float]
    dew_point_f: Optional[float]
    cloud_cover_pct: Optional[float]

    @property
    def time(self) -> datetime:
        dt_obj = datetime.fromisoformat(self.time_iso)
        return dt_obj.astimezone(PT_ZONE)

    @classmethod
    def from_dict(cls, data: dict) -> "Observation":
        return cls(
            time_iso=data["time_iso"],
            air_temp_f=data["air_temp_f"],
            relative_humidity_pct=data.get("relative_humidity_pct"),
            dew_point_f=data.get("dew_point_f"),
            cloud_cover_pct=data.get("cloud_cover_pct"),
        )

@dataclass
class WeatherData:
    source: str
    latitude: float
    longitude: float
    elevation_ft: float
    observations: List[Observation]

    @classmethod
    def from_dict(cls, data: dict) -> "WeatherData":
        return cls(
            source=data.get("source", "unknown"),
            latitude=data["latitude"],
            longitude=data["longitude"],
            elevation_ft=data.get("elevation_ft", 0.0),
            observations=[Observation.from_dict(obs) for obs in data.get("observations", [])],
        )

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_json_file(cls, filepath: str) -> "WeatherData":
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)

    def to_json_file(self, filepath: str) -> None:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
        print(f"Wrote {len(self.observations)} observations to {filepath}")

    def to_timeseries(self) -> Tuple[List[datetime], List[float], List[Optional[float]], List[Optional[float]], List[Optional[float]]]:
        times = []
        temps_f = []
        rh_values = []
        dew_points_f = []
        cloud_cover_pct = []

        for obs in self.observations:
            times.append(obs.time)
            temps_f.append(obs.air_temp_f)
            rh_values.append(obs.relative_humidity_pct)
            dew_points_f.append(obs.dew_point_f)
            cloud_cover_pct.append(obs.cloud_cover_pct)

        return times, temps_f, rh_values, dew_points_f, cloud_cover_pct
