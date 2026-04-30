"""Unified CLI for wetbulb-calc."""

import click

from .core import pressure_at_elevation, wet_bulb_f
from .import_data import write_weather_json
from .importers import get_registry
from .plot import run_plot


@click.group()
def cli():
    """Wet bulb temperature calculator for backcountry ski forecasting."""


# --- import subgroup ---

@cli.group("import")
def import_cmd():
    """Import weather data from a source into standard JSON."""


# --- plot command ---

@cli.command()
@click.argument("file", type=click.Path(exists=True))
@click.option("--days", type=float, default=3.0, help="Number of forecast days.")
def plot(file, days):
    """Read standard JSON, compute wet bulb temps, generate chart and CSV."""
    run_plot(file, days)


# --- calc command ---

@cli.command()
@click.option("--temp", type=float, required=True, help="Air temperature in Fahrenheit.")
@click.option("--rh", type=float, required=True, help="Relative humidity percentage.")
@click.option("--elevation", type=float, default=0, help="Elevation in feet.")
def calc(temp, rh, elevation):
    """One-off wet bulb temperature calculation."""
    t_celsius = (temp - 32) * 5.0 / 9.0
    p_hpa = pressure_at_elevation(elevation)
    wb = wet_bulb_f(t_celsius, rh, p_hpa)
    if wb is None:
        raise click.ClickException("Solver failed to converge.")
    click.echo(f"Wet bulb temperature: {wb:.1f}°F")


# --- run subgroup ---

@cli.group()
def run():
    """Import data and plot in one step."""


# --- auto-register importer subcommands for both import and run ---

def _build_import_command(name, entry):
    """Build a Click command for `wetbulb-calc import <name>`."""
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


def _build_run_command(name, entry):
    """Build a Click command for `wetbulb-calc run <name>`."""
    decorators = entry["decorators"]
    fetch_fn = entry["fetch"]

    @click.option("-o", "--output", default="weather_data.json", help="Output JSON path.")
    @click.option("--days", type=float, default=3.0, help="Number of forecast days.")
    def cmd(output, days, **kwargs):
        data = fetch_fn(**kwargs)
        write_weather_json(data, output)
        run_plot(output, days)

    for dec in reversed(decorators):
        cmd = dec(cmd)

    cmd = click.command(name=name, help=f"Import from {name} and plot.")(cmd)
    return cmd


for _name, _entry in get_registry().items():
    import_cmd.add_command(_build_import_command(_name, _entry))
    run.add_command(_build_run_command(_name, _entry))


if __name__ == "__main__":
    cli()
