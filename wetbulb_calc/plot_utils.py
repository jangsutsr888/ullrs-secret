"""Shared helpers for forecast and consolidation plot modules."""

import json
from datetime import datetime, timedelta

import click
import pandas as pd
import pytz

from .core import effective_temperature_f, pressure_at_elevation, wet_bulb_f

PT_ZONE = pytz.timezone("America/Los_Angeles")


def load_weather_data(json_path):
    """Load standard weather JSON into a dict of parsed arrays."""
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    times, temps_f, rh_values, dew_points_f, cloud_cover_pct = [], [], [], [], []
    for obs in data.get("observations", []):
        dt_obj = datetime.fromisoformat(obs["time_iso"])
        times.append(dt_obj.astimezone(PT_ZONE))
        temps_f.append(obs["air_temp_f"])
        rh_values.append(obs["relative_humidity_pct"])
        dew_points_f.append(obs.get("dew_point_f"))
        cloud_cover_pct.append(obs.get("cloud_cover_pct"))

    return {
        "elevation_ft": data.get("elevation_ft", 0.0),
        "latitude": data.get("latitude"),
        "longitude": data.get("longitude"),
        "times": times,
        "temps_f": temps_f,
        "rh_values": rh_values,
        "dew_points_f": dew_points_f,
        "cloud_cover_pct": cloud_cover_pct,
    }


def prepare_forecast_data(json_path, days):
    """Load weather JSON, filter to the time window, and compute wet bulb temps.

    Returns (elevation_ft, f_times, f_temps, f_rhs, adjusted_wbs, p_hpa).
    """
    wd = load_weather_data(json_path)
    elevation_ft = wd["elevation_ft"]
    times = wd["times"]
    temps_f = wd["temps_f"]
    rh_values = wd["rh_values"]

    if not times:
        raise click.ClickException("No valid time series data found in JSON.")

    p_hpa = pressure_at_elevation(elevation_ft)
    print(f"Elevation: {elevation_ft} ft. Local pressure: {p_hpa:.2f} hPa")

    cutoff_date = times[0] + timedelta(days=days)

    f_times, f_temps, f_rhs = [], [], []
    for t, temp, rh in zip(times, temps_f, rh_values):
        if t <= cutoff_date:
            f_times.append(t)
            f_temps.append(temp)
            f_rhs.append(rh)

    adjusted_wbs = []
    for t_f, rh in zip(f_temps, f_rhs):
        if t_f is not None and rh is not None:
            t_c = (t_f - 32) * 5.0 / 9.0
            adjusted_wbs.append(wet_bulb_f(t_c, rh, p_hpa))
        else:
            adjusted_wbs.append(None)

    return elevation_ft, f_times, f_temps, f_rhs, adjusted_wbs


def find_crossings_and_segments(v_times, v_wbs, threshold=32.0):
    """Split a time series into segments at threshold crossings.

    Returns (segments, crossing_times) where each segment is a list of
    (time, value) tuples.
    """
    segments = []
    current_segment = [(v_times[0], v_wbs[0])]
    crossing_times = []

    for i in range(len(v_wbs) - 1):
        t1, w1 = v_times[i], v_wbs[i]
        t2, w2 = v_times[i + 1], v_wbs[i + 1]

        if (w1 - threshold) * (w2 - threshold) < 0:
            ratio = (threshold - w1) / (w2 - w1)
            t_cross = t1 + (t2 - t1) * ratio
            crossing_times.append(t_cross)
            current_segment.append((t_cross, threshold))
            segments.append(current_segment)
            current_segment = [(t_cross, threshold), (t2, w2)]
        else:
            current_segment.append((t2, w2))
    segments.append(current_segment)

    return segments, crossing_times


def compute_segment_integral(seg_times, seg_wbs, threshold=32.0):
    """Compute the trapezoidal integral of |value - threshold| over a segment."""
    integral = 0.0
    for i in range(len(seg_times) - 1):
        dt_hours = (seg_times[i + 1] - seg_times[i]).total_seconds() / 3600.0
        integral += 0.5 * abs((seg_wbs[i] - threshold) + (seg_wbs[i + 1] - threshold)) * dt_hours
    return integral


def export_forecast_csv(f_times, f_temps, f_rhs, adjusted_wbs, filename, effective_temps=None):
    """Export forecast data to CSV."""
    data = {
        "Time_PT": [t.strftime("%Y-%m-%d %H:%M:%S") for t in f_times],
        "Air_Temp_F": f_temps,
        "Relative_Humidity_Pct": f_rhs,
        "Adjusted_Wet_Bulb_F": adjusted_wbs,
    }
    if effective_temps is not None:
        data["Effective_Temp_F"] = effective_temps
    df = pd.DataFrame(data)
    df.to_csv(filename, index=False)
    print(f"Data saved to: {filename}")


def prepare_effective_temp_data(json_path, days, slope_deg=0.0, aspect_deg=180.0):
    """Load weather JSON, compute wet bulb and effective temperatures.

    Returns (elevation_ft, lat, lon, f_times, f_temps, f_rhs, adjusted_wbs, effective_temps).
    """
    wd = load_weather_data(json_path)
    elevation_ft = wd["elevation_ft"]
    times = wd["times"]
    temps_f = wd["temps_f"]
    rh_values = wd["rh_values"]
    dew_points_f = wd["dew_points_f"]
    cloud_cover_pct = wd["cloud_cover_pct"]
    lat = wd["latitude"]
    lon = wd["longitude"]

    if not times:
        raise click.ClickException("No valid time series data found in JSON.")

    p_hpa = pressure_at_elevation(elevation_ft)
    print(f"Elevation: {elevation_ft} ft. Local pressure: {p_hpa:.2f} hPa")

    cutoff_date = times[0] + timedelta(days=days)

    f_times, f_temps, f_rhs, f_dew, f_cloud = [], [], [], [], []
    for t, temp, rh, dew, cloud in zip(times, temps_f, rh_values, dew_points_f, cloud_cover_pct):
        if t <= cutoff_date:
            f_times.append(t)
            f_temps.append(temp)
            f_rhs.append(rh)
            f_dew.append(dew)
            f_cloud.append(cloud)

    adjusted_wbs = []
    for t_f, rh in zip(f_temps, f_rhs):
        if t_f is not None and rh is not None:
            t_c = (t_f - 32) * 5.0 / 9.0
            adjusted_wbs.append(wet_bulb_f(t_c, rh, p_hpa))
        else:
            adjusted_wbs.append(None)

    effective_temps = []
    for wb, t_f, dew, cloud, t in zip(adjusted_wbs, f_temps, f_dew, f_cloud, f_times):
        if wb is not None and t_f is not None and dew is not None and cloud is not None:
            effective_temps.append(
                effective_temperature_f(wb, t_f, dew, cloud, lat, lon, t,
                                        slope_deg=slope_deg, aspect_deg=aspect_deg)
            )
        else:
            effective_temps.append(None)

    return elevation_ft, lat, lon, f_times, f_temps, f_rhs, adjusted_wbs, effective_temps
