"""Unified CLI for ullrs-secret."""

import click

from .import_data import write_weather_json
from .importers import get_registry
from .consolidation_plot import run_consolidation_model
from .pow_plot import run_pow_plot
from .corn_plot import run_corn_plot


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


# --- pow-plot command ---

@cli.command("pow-plot")
@click.argument("file", type=click.Path(exists=True))
@click.option("--start", type=float, default=None, help="Start day offset (e.g. 0.0 for start of data).")
@click.option("--end", type=float, default=None, help="End day offset (e.g. 3.0). Defaults to end of data.")
@click.option("--slope", type=float, default=0.0, help="Slope angle in degrees (0 = flat).")
@click.option("--aspect", type=float, default=180.0, help="Slope aspect in degrees (0=N, 90=E, 180=S, 270=W).")
@click.option("--elevation", type=float, default=None, help="Target elevation in ft (adjusts from data source elevation).")
def pow_plot(file, start, end, slope, aspect, elevation):
    """Read standard JSON, compute effective temps, generate powder preservation chart and CSV."""
    run_pow_plot(file, start_days=start, end_days=end, slope_deg=slope, aspect_deg=aspect, target_elevation_ft=elevation)


# --- corn-plot command ---

@cli.command("corn-plot")
@click.argument("file", type=click.Path(exists=True))
@click.option("--start", type=float, default=None, help="Start day offset (e.g. 0.0 for start of data).")
@click.option("--end", type=float, default=None, help="End day offset (e.g. 3.0). Defaults to end of data.")
@click.option("--slope", type=float, default=0.0, help="Slope angle in degrees (0 = flat).")
@click.option("--aspect", type=float, default=180.0, help="Slope aspect in degrees (0=N, 90=E, 180=S, 270=W).")
@click.option("--elevation", type=float, default=None, help="Target elevation in ft (adjusts from data source elevation).")
@click.option("--density", type=float, default=0.5, help="Estimated snow density (e.g. 0.35 for typical spring snow, 0.50 for firn).")
def corn_plot(file, start, end, slope, aspect, elevation, density):
    """Read standard JSON, compute effective temps, generate corn snow chart and CSV."""
    run_corn_plot(file, start_days=start, end_days=end, slope_deg=slope, aspect_deg=aspect, target_elevation_ft=elevation, snow_density=density)


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


# --- snotel commands ---

@cli.command("snotel-list")
@click.option("--lat", type=float, required=True, help="Latitude of the location (+ for North, - for South)")
@click.option("--lon", type=float, required=True, help="Longitude of the location (+ for East, - for West)")
def snotel_list(lat, lon):
    """List the 5 nearest SNOTEL stations to a given coordinate."""
    from .snotel import find_nearest_snotel_stations
    
    try:
        stations = find_nearest_snotel_stations(lat, lon, count=5)
        click.echo(f"Top 5 nearest SNOTEL stations to ({lat:.5f}, {lon:.5f}):")
        click.echo(f"{'Station Name':<25} | {'Elevation':<10} | {'Distance':<10} | {'Direction':<10} | {'Identifier'}")
        click.echo("-" * 80)
        
        for st in stations:
            name = st.get('name', 'Unknown')
            elev = f"{st.get('elevation', 0):.0f} ft"
            dist = f"{st.get('distance_miles', 0):.1f} mi"
            direction = st.get('direction', 'N/A')
            triplet = st.get('stationTriplet', 'N/A')
            
            click.echo(f"{name:<25} | {elev:<10} | {dist:<10} | {direction:<10} | {triplet}")
            
        click.echo("\nUse 'ullrs-secret snotel --site \"<Identifier or Name>\"' to fetch data for a specific station.")
    except Exception as e:
        click.echo(f"Error fetching nearest SNOTEL stations: {e}", err=True)

@cli.command("snotel")
@click.option("--site", type=str, required=True, help="SNOTEL station name or identifier (e.g., 'Thunder Basin' or '817:WA:SNTL')")
@click.option("--elevation", type=float, default=None, help="Target elevation in ft for snow depth inference.")
@click.option("--start", type=str, default=None, help="Start date (YYYY-MM-DD). Defaults to 7 days ago.")
@click.option("--end", type=str, default=None, help="End date (YYYY-MM-DD). Defaults to today.")
def snotel(site, elevation, start, end):
    """Fetch data for a specific SNOTEL station and infer snow depth at target elevation."""
    from .snotel import get_snotel_report
    from datetime import datetime
    
    try:
        start_date = datetime.strptime(start, "%Y-%m-%d") if start else None
        end_date = datetime.strptime(end, "%Y-%m-%d") if end else None
    except ValueError:
        raise click.BadParameter("Dates must be in YYYY-MM-DD format.")

    try:
        report = get_snotel_report(site, target_elev_ft=elevation, start_date=start_date, end_date=end_date)
        
        st = report['station']
        click.echo(f"SNOTEL Station: {st.get('name')} ({st.get('stationTriplet')})")
        
        st_elev = st.get('elevation')
        if st_elev:
            click.echo(f"  Elevation: {st_elev:.0f} ft")
        else:
            click.echo("  Elevation: Unknown")

        click.echo(f"\nData from {report['start_date']} to {report['end_date']}:")
        
        # Sort dates
        dates = sorted(report['data'].keys())
        if not dates:
            click.echo("  No data available for this period.")
            return

        click.echo(f"{'Date':<12} | {'Depth (cm)':<12} | {'SWE (mm)':<12} | {'Density':<12} | {'24h Snow (cm)':<15} | {'24h Density':<12}")
        click.echo("-" * 85)
        
        for i, d in enumerate(dates):
            if d < report['start_date']:
                continue
                
            metrics = report['data'][d]
            # AWDB uses inches. Convert to project units.
            # 1 inch = 2.54 cm
            snwd_in = metrics.get('SNWD')
            wteq_in = metrics.get('WTEQ')
            
            snwd_cm_str = f"{snwd_in * 2.54:.1f}" if snwd_in is not None else "N/A"
            wteq_mm_str = f"{wteq_in * 25.4:.1f}" if wteq_in is not None else "N/A"
            
            density_str = "N/A"
            if snwd_in is not None and wteq_in is not None and snwd_in > 0:
                density = wteq_in / snwd_in
                density_str = f"{density:.2f}"
                
            new_snow_str = "N/A"
            new_density_str = "N/A"
            
            if i > 0:
                prev_d = dates[i-1]
                # Ensure the previous date is actually yesterday
                from datetime import datetime, timedelta
                curr_date_obj = datetime.strptime(d, "%Y-%m-%d")
                prev_date_obj = datetime.strptime(prev_d, "%Y-%m-%d")
                
                if (curr_date_obj - prev_date_obj).days == 1:
                    prev_metrics = report['data'][prev_d]
                    prev_snwd = prev_metrics.get('SNWD')
                    prev_wteq = prev_metrics.get('WTEQ')
                    
                    if snwd_in is not None and prev_snwd is not None:
                        delta_snwd = snwd_in - prev_snwd
                        if delta_snwd > 0:
                            new_snow_str = f"{delta_snwd * 2.54:.1f}"
                            if wteq_in is not None and prev_wteq is not None:
                                delta_wteq = wteq_in - prev_wteq
                                if delta_wteq > 0:
                                    new_density = delta_wteq / delta_snwd
                                    new_density_str = f"{new_density:.2f}"
                                else:
                                    new_density_str = "0.00"
                        else:
                            new_snow_str = "0.0"
                            new_density_str = "-"
            
            click.echo(f"{d:<12} | {snwd_cm_str:<12} | {wteq_mm_str:<12} | {density_str:<12} | {new_snow_str:<15} | {new_density_str:<12}")

        if elevation and st_elev:
            # Inference logic
            click.echo(f"\nSnow Level Inference at {elevation:.0f} ft:")
            delta_ft = elevation - st_elev
            click.echo(f"  Elevation Difference: {delta_ft:+.0f} ft")
            
            # Simple inference: +/- 10% per 1000 ft
            multiplier = 1.0 + (delta_ft / 1000.0) * 0.10
            # Floor at 0
            multiplier = max(0.0, multiplier)
            
            latest_date = dates[-1]
            latest_metrics = report['data'][latest_date]
            latest_snwd = latest_metrics.get('SNWD')
            
            if latest_snwd is not None:
                inferred_snwd_cm = (latest_snwd * 2.54) * multiplier
                click.echo(f"  Latest SNOTEL Depth ({latest_date}): {latest_snwd * 2.54:.1f} cm")
                click.echo(f"  Inferred Target Depth (approx. 10%/1000ft): {inferred_snwd_cm:.1f} cm")
            else:
                 click.echo(f"  Cannot infer: Missing SNWD data on {latest_date}.")

    except Exception as e:
        click.echo(f"Error fetching SNOTEL data: {e}", err=True)


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
