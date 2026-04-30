"""NWS XML data importer."""

import os
import urllib.request
import xml.etree.ElementTree as ET

import click

from . import register


def _download(url):
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    })
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.read().decode("utf-8")
    except Exception as e:
        raise click.ClickException(f"Download failed: {e}")


def _read_local(path):
    if not os.path.exists(path):
        raise click.ClickException(f"File not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _parse_xml(xml_data):
    xml_data = xml_data.replace("&lon=", "&amp;lon=").replace(
        "&FcstType=", "&amp;FcstType="
    )
    try:
        root = ET.fromstring(xml_data)
    except ET.ParseError as e:
        raise click.ClickException(f"XML parse failed: {e}")

    height_elem = root.find(".//location/height")
    elevation_ft = float(height_elem.text) if height_elem is not None else 0.0

    times = []
    time_layout_key = "k-p1h-n1-0"
    for tl in root.findall(".//time-layout"):
        if tl.find("layout-key").text == time_layout_key:
            for st in tl.findall("start-valid-time"):
                times.append(st.text)
            break

    temps_f = []
    for temp in root.findall(".//parameters/temperature"):
        if temp.get("type") == "hourly" and temp.get("time-layout") == time_layout_key:
            for v in temp.findall("value"):
                temps_f.append(float(v.text) if v.text is not None else None)
            break

    rh_values = []
    for rh in root.findall(".//parameters/humidity"):
        if rh.get("type") == "relative" and rh.get("time-layout") == time_layout_key:
            for v in rh.findall("value"):
                rh_values.append(float(v.text) if v.text is not None else None)
            break

    min_len = min(len(times), len(temps_f), len(rh_values))
    observations = []
    for i in range(min_len):
        observations.append({
            "time_iso": times[i],
            "air_temp_f": temps_f[i],
            "relative_humidity_pct": rh_values[i],
        })

    return {
        "source": "nws",
        "elevation_ft": elevation_ft,
        "observations": observations,
    }


NWS_DECORATORS = [
    click.argument("source"),
]


@register("nws", decorators=NWS_DECORATORS)
def fetch(source):
    """Fetch and parse NWS weather data from a URL or local XML file path."""
    if source.startswith(("http://", "https://")):
        xml_data = _download(source)
    else:
        xml_data = _read_local(source)
    return _parse_xml(xml_data)
