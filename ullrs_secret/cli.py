"""Unified CLI for ullrs-secret."""

import click

from .import_data import write_weather_json
from .importers import get_registry
from .consolidation_plot import run_consolidation_model
from .plot import run_plot


@click.group()
def cli():
    """Ullr's Secret — backcountry ski snow conditions forecaster."""


# --- import subgroup ---

@cli.group("import")
def import_cmd():
    """Import weather data from a source into standard JSON."""


# --- consolidation-plot command ---

@cli.command("consolidation-plot")
@click.argument("file", type=click.Path(exists=True))
@click.option("--start", type=float, default=None, help="Start day offset (e.g. 0.0 for start of data).")
@click.option("--end", type=float, default=None, help="End day offset (e.g. 3.0). Defaults to end of data.")
@click.option("--swe", type=float, default=30.0, help="Snow water equivalent in mm.")
@click.option("--depth", type=float, default=20.0, help="Physical snow depth in cm.")
@click.option("--slope", type=float, default=0.0, help="Slope angle in degrees (0 = flat).")
@click.option("--aspect", type=float, default=180.0, help="Slope aspect in degrees (0=N, 90=E, 180=S, 270=W).")
@click.option("--elevation", type=float, default=None, help="Target elevation in ft (adjusts from data source elevation).")
def consolidation_plot(file, start, end, swe, depth, slope, aspect, elevation):
    """Compute melt-freeze consolidation model and plot D_total curve."""
    run_consolidation_model(file, start_days=start, end_days=end, swe_mm=swe, h0_snow_cm=depth, slope_deg=slope, aspect_deg=aspect, target_elevation_ft=elevation)


# --- plot command ---

@cli.command("plot")
@click.argument("file", type=click.Path(exists=True))
@click.option("--start", type=float, default=None, help="Start day offset (e.g. 0.0 for start of data).")
@click.option("--end", type=float, default=None, help="End day offset (e.g. 3.0). Defaults to end of data.")
@click.option("--slope", type=float, default=0.0, help="Slope angle in degrees (0 = flat).")
@click.option("--aspect", type=float, default=180.0, help="Slope aspect in degrees (0=N, 90=E, 180=S, 270=W).")
@click.option("--elevation", type=float, default=None, help="Target elevation in ft (adjusts from data source elevation).")
@click.option("--density", type=float, default=0.5, help="Estimated snow density (e.g. 0.35 for typical spring snow, 0.50 for firn).")
def plot(file, start, end, slope, aspect, elevation, density):
    """Read standard JSON, compute effective temps, generate chart and CSV."""
    run_plot(file, start_days=start, end_days=end, slope_deg=slope, aspect_deg=aspect, target_elevation_ft=elevation, snow_density=density)


# --- terrain command ---

@cli.command("terrain")
@click.option("--lat", type=float, required=True, help="Latitude of the location (+ for North, - for South)")
@click.option("--lon", type=float, required=True, help="Longitude of the location (+ for East, - for West)")
def terrain(lat, lon):
    """Calculate elevation, slope, and aspect for a coordinate."""
    from .terrain import get_terrain_data
    
    try:
        data = get_terrain_data(lat, lon)
        
        ASPECT_LABELS = {0: "N", 45: "NE", 90: "E", 135: "SE", 180: "S", 225: "SW", 270: "W", 315: "NW", 360: "N"}
        closest_cardinal = min(ASPECT_LABELS, key=lambda k: abs(k - data['aspect_deg'] % 360))
        aspect_label = ASPECT_LABELS[closest_cardinal]

        click.echo(f"Coordinates: {lat:.5f}, {lon:.5f}")
        click.echo(f"Elevation:   {data['elevation_ft']:.1f} ft ({data['elevation_m']:.1f} m)")
        click.echo(f"Slope:       {data['slope_deg']:.0f}°")
        click.echo(f"Aspect:      {data['aspect_deg']:.0f}° {aspect_label}")
    except Exception as e:
        click.echo(f"Error fetching terrain data: {e}", err=True)


# --- auto-register importer subcommands ---

def _build_import_command(name, entry):
    """Build a Click command for `ullrs-secret import <name>`."""
    decorators = entry["decorators"]
    fetch_fn = entry["fetch"]

    @click.option("-o", "--output", default="weather_data.json", help="Output JSON path.")
    def cmd(output, **kwargs):
        data = fetch_fn(**kwargs)
        write_weather_json(data, output)

    for dec in reversed(decorators):
        cmd = dec(cmd)

    cmd = click.command(name=name, help=fetch_fn.__doc__ or f"Import from {name}.")(cmd)
    return cmd


for _name, _entry in get_registry().items():
    import_cmd.add_command(_build_import_command(_name, _entry))


if __name__ == "__main__":
    cli()
