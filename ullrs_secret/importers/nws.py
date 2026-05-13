"""NWS XML data importer."""

import urllib.request
import xml.etree.ElementTree as ET

import click

from . import register
from ..plot_utils import calculate_distance_miles


def _download(url):
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    })
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.read().decode("utf-8")
    except Exception as e:
        raise click.ClickException(f"Download failed: {e}")


def _extract_values(parent, tag, attr_type, layout_key):
    for elem in parent.findall(tag):
        if elem.get("type") == attr_type and elem.get("time-layout") == layout_key:
            return [
                float(v.text) if v.text is not None and not v.get(
                    "{http://www.w3.org/2001/XMLSchema-instance}nil"
                ) else None
                for v in elem.findall("value")
            ]
    return []


def _parse_xml(xml_data, input_lat, input_lon):
    xml_data = xml_data.replace("&lon=", "&amp;lon=").replace(
        "&FcstType=", "&amp;FcstType="
    )
    try:
        root = ET.fromstring(xml_data)
    except ET.ParseError as e:
        raise click.ClickException(f"XML parse failed: {e}")

    point_elem = root.find(".//location/point")
    latitude = float(point_elem.get("latitude")) if point_elem is not None else None
    longitude = float(point_elem.get("longitude")) if point_elem is not None else None

    if latitude is not None and longitude is not None:
        distance_miles = calculate_distance_miles(input_lat, input_lon, latitude, longitude)
        click.echo(f"Matched nearest NWS grid point: Lat {latitude:.4f}, Lon {longitude:.4f}")
        click.echo(f"Distance from input location: {distance_miles:.2f} miles")

    height_elem = root.find(".//location/height")
    elevation_ft = float(height_elem.text) if height_elem is not None else 0.0

    times = []
    time_layout_key = "k-p1h-n1-0"
    for tl in root.findall(".//time-layout"):
        if tl.find("layout-key").text == time_layout_key:
            for st in tl.findall("start-valid-time"):
                times.append(st.text)
            break

    params = root.find(".//parameters")
    temps_f = _extract_values(params, "temperature", "hourly", time_layout_key)
    dew_points_f = _extract_values(params, "temperature", "dew point", time_layout_key)
    rh_values = _extract_values(params, "humidity", "relative", time_layout_key)
    cloud_cover_pct = _extract_values(params, "cloud-amount", "total", time_layout_key)

    min_len = min(len(times), len(temps_f), len(rh_values))
    observations = []
    for i in range(min_len):
        obs = {
            "time_iso": times[i],
            "air_temp_f": temps_f[i],
            "relative_humidity_pct": rh_values[i],
            "dew_point_f": dew_points_f[i] if i < len(dew_points_f) else None,
            "cloud_cover_pct": cloud_cover_pct[i] if i < len(cloud_cover_pct) else None,
        }
        observations.append(obs)

    return {
        "source": "nws",
        "latitude": latitude,
        "longitude": longitude,
        "elevation_ft": elevation_ft,
        "observations": observations,
    }


NWS_DECORATORS = [
    click.option("--lat", type=float, required=True, help="Latitude of the location (+ for North, - for South)"),
    click.option("--lon", type=float, required=True, help="Longitude of the location (+ for East, - for West)"),
]


@register("nws", decorators=NWS_DECORATORS)
def fetch(lat, lon):
    """Fetch and parse NWS weather data from the MapClick API."""
    url = f"https://forecast.weather.gov/MapClick.php?lat={lat}&lon={lon}&FcstType=digitalDWML"
    xml_data = _download(url)
    return _parse_xml(xml_data, lat, lon)
