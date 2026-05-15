"""SNOTEL data fetching and processing."""

import math
import requests
import click
from datetime import datetime, timedelta

from .plot_utils import calculate_distance_miles, calculate_bearing

def find_nearest_snotel_stations(lat, lon, count=5, bbox_deg=2.0):
    """
    Finds the nearest SNOTEL stations within a bounding box.
    """
    min_lat = lat - bbox_deg
    max_lat = lat + bbox_deg
    min_lon = lon - bbox_deg
    max_lon = lon + bbox_deg

    url = f"https://wcc.sc.egov.usda.gov/awdbRestApi/services/v1/stations?activeOnly=true&networks=SNTL&minLatitude={min_lat}&maxLatitude={max_lat}&minLongitude={min_lon}&maxLongitude={max_lon}"
    
    response = requests.get(url, headers={"accept": "application/json"})
    response.raise_for_status()
    stations = response.json()

    if not stations:
        raise ValueError(f"No SNOTEL stations found within +/- {bbox_deg} degrees of {lat}, {lon}.")

    valid_stations = []

    for meta in stations:
        if meta.get('networkCode') != 'SNTL':
            continue

        st_lat = meta.get('latitude')
        st_lon = meta.get('longitude')
        if st_lat is None or st_lon is None:
            continue
            
        dist = calculate_distance_miles(lat, lon, st_lat, st_lon)
        bearing = calculate_bearing(lat, lon, st_lat, st_lon)
        meta['distance_miles'] = dist
        meta['direction'] = bearing
        valid_stations.append(meta)
            
    if not valid_stations:
        raise ValueError("Could not determine any nearby SNOTEL stations.")
        
    valid_stations.sort(key=lambda x: x['distance_miles'])
    return valid_stations[:count]

def get_station_by_identifier(identifier):
    """Finds a station by its triplet or name."""
    # If it looks like a triplet
    if ":" in identifier:
        url = f"https://wcc.sc.egov.usda.gov/awdbRestApi/services/v1/stations?stationTriplets={identifier}"
        response = requests.get(url, headers={"accept": "application/json"})
        if response.status_code == 200 and response.json():
            return response.json()[0]
            
    # Fallback to fetching all SNTL stations and matching by name
    url = "https://wcc.sc.egov.usda.gov/awdbRestApi/services/v1/stations?activeOnly=true&networks=SNTL"
    response = requests.get(url, headers={"accept": "application/json"})
    response.raise_for_status()
    stations = response.json()
    
    for meta in stations:
        if meta.get('name', '').lower() == identifier.lower():
            return meta
            
    raise ValueError(f"Could not find a SNOTEL station matching '{identifier}'.")

def fetch_snotel_data(station_triplet, start_date_str, end_date_str):
    """
    Fetches daily SNWD and WTEQ data for a given station and time range.
    """
    url = f"https://wcc.sc.egov.usda.gov/awdbRestApi/services/v1/data?stationTriplets={station_triplet}&elements=SNWD,WTEQ&duration=DAILY&beginDate={start_date_str}&endDate={end_date_str}"
    
    response = requests.get(url, headers={"accept": "application/json"})
    response.raise_for_status()
    data = response.json()
    
    results = {}
    if not data or len(data) == 0:
        return results

    station_data = data[0].get('data', [])
    for entry in station_data:
        elem = entry.get('stationElement', {}).get('elementCode')
        if elem not in ['SNWD', 'WTEQ']:
            continue
            
        values_list = entry.get('values', [])
        for v in values_list:
            date = v.get('date')
            val = v.get('value')
            if not date or val is None:
                continue
                
            if date not in results:
                results[date] = {}
            results[date][elem] = val
            
    return results

def get_snotel_report(identifier, target_elev_ft=None, start_date=None, end_date=None):
    """
    Full pipeline to get and process SNOTEL data for a specific station.
    """
    if not end_date:
        end_date = datetime.now()
    if not start_date:
        start_date = end_date - timedelta(days=7)
        
    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")
    
    # Fetch from 1 day earlier to calculate 24h deltas for the first date
    fetch_start_date = start_date - timedelta(days=1)
    fetch_start_str = fetch_start_date.strftime("%Y-%m-%d")
    
    station_meta = get_station_by_identifier(identifier)
    station_triplet = station_meta['stationTriplet']
    
    station_elev_ft = station_meta.get('elevation')
    
    data = fetch_snotel_data(station_triplet, fetch_start_str, end_str)
    
    return {
        "station": station_meta,
        "target_elev_ft": target_elev_ft,
        "data": data,
        "start_date": start_str,
        "end_date": end_str
    }
