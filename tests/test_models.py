import os
import json
from datetime import datetime
import pytest
import pytz

from ullrs_secret.models import Observation, WeatherData

# Use the existing JSON file in the project directory for testing
TEST_JSON_FILE = os.path.join(os.path.dirname(__file__), "data", "weather_data.json")

@pytest.fixture
def sample_weather_data() -> dict:
    """Load the sample weather data directly as a dict for comparison."""
    if not os.path.exists(TEST_JSON_FILE):
        pytest.skip(f"Test file {TEST_JSON_FILE} not found. Ensure it exists in tests/data.")
    with open(TEST_JSON_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def test_observation_from_dict():
    data = {
        "time_iso": "2026-06-02T16:00:00-07:00",
        "air_temp_f": 51.0,
        "relative_humidity_pct": 60.0,
        "dew_point_f": 38.0,
        "cloud_cover_pct": 34.0
    }
    obs = Observation.from_dict(data)
    assert obs.time_iso == "2026-06-02T16:00:00-07:00"
    assert obs.air_temp_f == 51.0
    assert obs.relative_humidity_pct == 60.0
    assert obs.dew_point_f == 38.0
    assert obs.cloud_cover_pct == 34.0
    
    # Check timezone parsing
    dt = obs.time
    assert dt.year == 2026
    assert dt.month == 6
    assert dt.day == 2
    assert dt.hour == 16
    assert dt.minute == 0
    assert dt.tzinfo is not None

def test_weather_data_from_json_file(sample_weather_data):
    if not os.path.exists(TEST_JSON_FILE):
        pytest.skip(f"Test file {TEST_JSON_FILE} not found.")
        
    wd = WeatherData.from_json_file(TEST_JSON_FILE)
    
    assert wd.source == sample_weather_data.get("source", "unknown")
    assert wd.latitude == sample_weather_data["latitude"]
    assert wd.longitude == sample_weather_data["longitude"]
    assert wd.elevation_ft == sample_weather_data.get("elevation_ft", 0.0)
    assert len(wd.observations) == len(sample_weather_data["observations"])
    
    # Spot check first observation
    if wd.observations:
        first_obs = wd.observations[0]
        sample_obs = sample_weather_data["observations"][0]
        assert first_obs.time_iso == sample_obs["time_iso"]
        assert first_obs.air_temp_f == sample_obs["air_temp_f"]

def test_weather_data_to_dict(sample_weather_data):
    wd = WeatherData.from_dict(sample_weather_data)
    serialized = wd.to_dict()
    
    assert serialized["source"] == wd.source
    assert serialized["latitude"] == wd.latitude
    assert serialized["longitude"] == wd.longitude
    assert serialized["elevation_ft"] == wd.elevation_ft
    
    # Check that observations are also serialized
    assert len(serialized["observations"]) == len(wd.observations)
    if wd.observations:
        assert serialized["observations"][0]["time_iso"] == wd.observations[0].time_iso

def test_weather_data_to_timeseries(sample_weather_data):
    wd = WeatherData.from_dict(sample_weather_data)
    
    times, temps_f, rh_values, dew_points_f, cloud_cover_pct = wd.to_timeseries()
    
    assert len(times) == len(wd.observations)
    assert len(temps_f) == len(wd.observations)
    assert len(rh_values) == len(wd.observations)
    assert len(dew_points_f) == len(wd.observations)
    assert len(cloud_cover_pct) == len(wd.observations)
    
    if wd.observations:
        assert times[0] == wd.observations[0].time
        assert temps_f[0] == wd.observations[0].air_temp_f
        assert rh_values[0] == wd.observations[0].relative_humidity_pct
        assert dew_points_f[0] == wd.observations[0].dew_point_f
        assert cloud_cover_pct[0] == wd.observations[0].cloud_cover_pct

def test_weather_data_to_json_file(tmp_path, sample_weather_data):
    wd = WeatherData.from_dict(sample_weather_data)
    
    out_file = tmp_path / "test_output.json"
    wd.to_json_file(str(out_file))
    
    assert out_file.exists()
    
    # Read back and compare
    wd_read = WeatherData.from_json_file(str(out_file))
    assert wd_read.source == wd.source
    assert wd_read.latitude == wd.latitude
    assert len(wd_read.observations) == len(wd.observations)
