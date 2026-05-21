"""Open-Meteo data importer (fast, high-resolution, multi-model)."""

import click
import requests
import pytz
from datetime import datetime

from ullrs_secret.importers import register
from ullrs_secret import core
from ullrs_secret.plot_utils import calculate_distance_miles, calculate_bearing


def _fetch_openmeteo(lat, lon, model, tz_name):
    local_tz = pytz.timezone(tz_name)

    # Fetch forecast from Open-Meteo
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "temperature_2m,relative_humidity_2m,dew_point_2m,cloud_cover",
        "temperature_unit": "fahrenheit",
        "wind_speed_unit": "mph",
        "precipitation_unit": "inch",
        "timezone": "UTC",
        "past_days": 0,
        "forecast_days": 10,
        "models": model
    }

    click.echo(f"Fetching forecast from Open-Meteo API (model: {model}) for {lat:.4f}, {lon:.4f}...")
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()
    
    # Open-Meteo returns the actual resolved coordinates based on the model's grid
    grid_lat = data.get("latitude", lat)
    grid_lon = data.get("longitude", lon)

    distance_miles = calculate_distance_miles(lat, lon, grid_lat, grid_lon)
    bearing = calculate_bearing(lat, lon, grid_lat, grid_lon)
    click.echo(f"Matched nearest grid point: Lat {grid_lat:.4f}, Lon {grid_lon:.4f}")
    click.echo(f"Distance from input location: {distance_miles:.2f} miles ({bearing})")
    # Open-Meteo automatically applies statistical downscaling to correct temperatures
    # and dew points to a high-resolution 90m Digital Elevation Model (DEM).
    # We must use THIS elevation as our baseline to prevent double-dipping on lapse rates.
    elevation_m = data.get("elevation", 0.0)
    elevation_ft = elevation_m * 3.28084
    click.echo(f"Open-Meteo downscaled elevation: {elevation_ft:.1f} ft ({elevation_m:.1f} m)")
    
    hourly = data.get("hourly", {})
    times = hourly.get("time", [])
    temps = hourly.get("temperature_2m", [])
    rhs = hourly.get("relative_humidity_2m", [])
    dews = hourly.get("dew_point_2m", [])
    clouds = hourly.get("cloud_cover", [])

    observations = []
    
    for i in range(len(times)):
        if temps[i] is None:
            continue
            
        # Parse UTC time: '2023-01-01T00:00' -> timezone aware -> target tz
        dt_naive = datetime.strptime(times[i], "%Y-%m-%dT%H:%M")
        dt_utc = pytz.utc.localize(dt_naive)
        dt_local = dt_utc.astimezone(local_tz)
        
        temp_f = float(temps[i])
        
        # Dew point might be None
        dew_f = float(dews[i]) if dews[i] is not None else None
        
        # Use provided RH if available, otherwise calculate from dew point
        if rhs[i] is not None:
            rh_pct = float(rhs[i])
        elif dew_f is not None:
            rh_pct = core.get_rh_from_dew_point(temp_f, dew_f)
        else:
            rh_pct = None
            
        cloud_pct = float(clouds[i]) if clouds[i] is not None else None

        observations.append({
            "time_iso": dt_local.isoformat(),
            "air_temp_f": round(temp_f, 2),
            "relative_humidity_pct": round(rh_pct, 2) if rh_pct is not None else None,
            "dew_point_f": round(dew_f, 2) if dew_f is not None else None,
            "cloud_cover_pct": round(cloud_pct, 2) if cloud_pct is not None else None,
        })

    return {
        "source": f"openmeteo_{model}",
        "latitude": grid_lat,
        "longitude": grid_lon,
        "elevation_ft": elevation_ft,
        "observations": observations,
    }


# Map user-friendly names to Open-Meteo's API model strings
MODEL_MAP = {
    "best_match": "best_match",
    "ecmwf": "ecmwf_ifs025",
    "gfs": "gfs_seamless",
    "gem": "gem_seamless",
    "hrrr": "gfs_hrrr",
}

OPENMETEO_DECORATORS = [
    click.option("--lat", type=float, required=True, help="Latitude of the location (+ for North, - for South)"),
    click.option("--lon", type=float, required=True, help="Longitude of the location (+ for East, - for West)"),
    click.option(
        "--model", 
        type=click.Choice(list(MODEL_MAP.keys()), case_sensitive=False), 
        default="best_match", 
        help="Weather model to use. Default: best_match"
    ),
    click.option("--timezone", type=str, default="America/Los_Angeles", help="Timezone (default: America/Los_Angeles)"),
]

@register("openmeteo", decorators=OPENMETEO_DECORATORS)
def fetch(lat, lon, model, timezone):
    """Fetch high-resolution forecast via Open-Meteo API."""
    api_model = MODEL_MAP[model.lower()]
    return _fetch_openmeteo(lat, lon, api_model, timezone)
