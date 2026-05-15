"""
=============================================================================
Prerequisites
=============================================================================
1. Install required Python libraries:
   Run the following in your terminal or virtual environment:
   pip install cdsapi xarray netCDF4 pandas numpy pytz

2. Configure the Copernicus CDS API Key:
   - Register and log in to the Copernicus Climate Data Store: https://cds.climate.copernicus.eu/
   - Get your API Key: Visit https://cds.climate.copernicus.eu/how-to-api
   - Create a configuration file: Create a plain text file named `.cdsapirc` in your user home directory 
     (Mac/Linux: `~/.cdsapirc`, Windows: `C:\\Users\\<YourUsername>\\.cdsapirc`).
   - Add the following content to the file (replace with your UID and Key):
     url: https://cds.climate.copernicus.eu/api/v2
     key: <YOUR-UID>:<YOUR-API-KEY>
=============================================================================
"""

import math
import os
import tempfile
from datetime import datetime, timedelta

import click
import pytz
import cdsapi
import pandas as pd
import xarray as xr

from . import register
from .. import core
from ..plot_utils import calculate_distance_miles, calculate_bearing


def _fetch_era5(lat, lon, start_date_str, end_date_str, tz_name):
    # Setup timezone and dates
    local_tz = pytz.timezone(tz_name)
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    
    # We need to cover the local time range with UTC data. 
    # To be safe, fetch from start_date UTC to end_date + 1 day UTC.
    current_date = start_date
    dates_to_fetch = set()
    while current_date <= end_date + timedelta(days=1):
        dates_to_fetch.add(current_date)
        current_date += timedelta(days=1)
        
    years = list(set([d.strftime('%Y') for d in dates_to_fetch]))
    months = list(set([d.strftime('%m') for d in dates_to_fetch]))
    days = list(set([d.strftime('%d') for d in dates_to_fetch]))
    
    # Calculate bounding box
    # API requires: North, West, South, East
    # Expand by 0.2 degrees from target coordinate
    north = round(lat + 0.2, 2)
    south = round(lat - 0.2, 2)
    east = round(lon + 0.2, 2)
    west = round(lon - 0.2, 2)
    
    c = cdsapi.Client()
    
    grid_lat, grid_lon = lat, lon
    
    with tempfile.NamedTemporaryFile(suffix='.nc', delete=False) as tmp_file:
        filename = tmp_file.name

    try:
        c.retrieve(
            'reanalysis-era5-single-levels',
            {
                'product_type': 'reanalysis',
                'format': 'netcdf',
                'variable': [
                    '2m_temperature',
                    '2m_dewpoint_temperature',
                    'total_cloud_cover',
                    'geopotential',
                ],
                'year': years,
                'month': months,
                'day': days,
                'time': [f'{i:02d}:00' for i in range(24)],
                'area': [north, west, south, east],
            },
            filename)
        
        ds = xr.open_dataset(filename)
        point_data = ds.sel(latitude=lat, longitude=lon, method='nearest')
        
        grid_lat = float(point_data.latitude.values)
        grid_lon = float(point_data.longitude.values)

        distance_miles = calculate_distance_miles(lat, lon, grid_lat, grid_lon)
        bearing = calculate_bearing(lat, lon, grid_lat, grid_lon)
        click.echo(f"Matched nearest ERA5 grid point: Lat {grid_lat:.2f}, Lon {grid_lon:.2f}")
        click.echo(f"Distance from input location: {distance_miles:.2f} miles ({bearing})")
        
        # Geopotential z = m^2/s^2, z / 9.80665 = m
        z_val = float(point_data['z'].values.flatten()[0])
        elevation_ft = (z_val / 9.80665) * 3.28084
        
        df = point_data.to_dataframe().reset_index()
        time_col = 'valid_time' if 'valid_time' in df.columns else 'time'
        df = df.dropna(subset=['t2m'])
        
        df[time_col] = pd.to_datetime(df[time_col])
        df['local_time'] = df[time_col].dt.tz_localize('UTC').dt.tz_convert(local_tz)
        
        # Filter strictly within the start_date to end_date bounds locally
        mask = (df['local_time'].dt.date >= start_date) & (df['local_time'].dt.date <= end_date)
        df = df[mask].copy()
        
        observations = []
        for _, row in df.iterrows():
            temp_c = row['t2m'] - 273.15
            dew_point_c = row['d2m'] - 273.15
            
            temp_f = temp_c * 9.0/5.0 + 32.0
            dew_point_f = dew_point_c * 9.0/5.0 + 32.0
            
            # Use core.py for RH calculation
            rh_percent = core.get_rh_from_dew_point(temp_f, dew_point_f)
            
            cloud_cover_pct = row['tcc'] * 100.0 if not pd.isna(row['tcc']) else None
            
            time_iso = row['local_time'].isoformat()
            
            observations.append({
                "time_iso": time_iso,
                "air_temp_f": round(temp_f, 2),
                "relative_humidity_pct": round(rh_percent, 2) if rh_percent is not None else None,
                "dew_point_f": round(dew_point_f, 2),
                "cloud_cover_pct": round(cloud_cover_pct, 2) if cloud_cover_pct is not None else None,
            })
            
    finally:
        if os.path.exists(filename):
            os.remove(filename)
            
    return {
        "source": "era5",
        "latitude": grid_lat,
        "longitude": grid_lon,
        "elevation_ft": elevation_ft,
        "observations": observations,
    }


ERA5_DECORATORS = [
    click.option("--lat", type=float, required=True, help="Latitude of the location (+ for North, - for South)"),
    click.option("--lon", type=float, required=True, help="Longitude of the location (+ for East, - for West)"),
    click.option("--start-date", type=str, required=True, help="Start date (YYYY-MM-DD)"),
    click.option("--end-date", type=str, required=True, help="End date (YYYY-MM-DD)"),
    click.option("--timezone", type=str, default="America/Los_Angeles", help="Timezone (default: America/Los_Angeles)"),
]

@register("era5", decorators=ERA5_DECORATORS)
def fetch(lat, lon, start_date, end_date, timezone):
    """Fetch and parse ERA5 reanalysis data via Copernicus CDS API."""
    return _fetch_era5(lat, lon, start_date, end_date, timezone)
