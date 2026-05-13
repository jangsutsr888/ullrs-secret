"""Terrain calculations using Open Topo Data."""

import math
import requests

def get_terrain_data(lat, lon):
    """
    Fetch a 3x3 grid of elevations around (lat, lon) and calculate
    center elevation, slope, and aspect using Horn's Method.
    """
    # SRTM30M resolution is approximately 30m at the equator.
    # 1 degree latitude is ~111,111 meters.
    dy_m = 30.0
    dx_m = 30.0

    d_lat = dy_m / 111111.0
    d_lon = dx_m / (111111.0 * math.cos(math.radians(lat)))

    # Create a 3x3 grid
    # NW, N, NE
    # W,  C, E
    # SW, S, SE
    points = [
        (lat + d_lat, lon - d_lon), # NW
        (lat + d_lat, lon),         # N
        (lat + d_lat, lon + d_lon), # NE
        (lat, lon - d_lon),         # W
        (lat, lon),                 # C
        (lat, lon + d_lon),         # E
        (lat - d_lat, lon - d_lon), # SW
        (lat - d_lat, lon),         # S
        (lat - d_lat, lon + d_lon), # SE
    ]

    locations_str = "|".join([f"{p[0]:.6f},{p[1]:.6f}" for p in points])
    url = f"https://api.opentopodata.org/v1/srtm30m?locations={locations_str}"
    
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()

    if data.get('status') != 'OK':
        raise ValueError(f"Open Topo Data API Error: {data.get('status')}")

    results = data.get('results', [])
    if len(results) != 9:
        raise ValueError("Did not receive 9 elevation points from API.")

    elevations = [r['elevation'] for r in results]
    
    # Handle cases where elevation might be None (e.g. over ocean)
    if any(e is None for e in elevations):
        raise ValueError("One or more elevation points returned None (ocean or out of bounds).")

    nw, n, ne, w, c, e, sw, s, se = elevations

    elev_m = c
    elev_ft = elev_m * 3.28084

    # Calculate slope and aspect using Horn's Method
    # dz_dx is West to East rate of change
    # dz_dy is South to North rate of change
    dz_dx = ((ne + 2*e + se) - (nw + 2*w + sw)) / (8 * dx_m)
    dz_dy = ((nw + 2*n + ne) - (sw + 2*s + se)) / (8 * dy_m)

    slope_rad = math.atan(math.sqrt(dz_dx**2 + dz_dy**2))
    slope_deg = math.degrees(slope_rad)

    # Aspect is the downhill direction
    aspect_rad = math.atan2(-dz_dx, -dz_dy)
    aspect_deg = math.degrees(aspect_rad)
    if aspect_deg < 0:
        aspect_deg += 360.0

    return {
        "elevation_m": elev_m,
        "elevation_ft": elev_ft,
        "slope_deg": slope_deg,
        "aspect_deg": aspect_deg
    }
