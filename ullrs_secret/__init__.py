"""
Ullr's Secret — backcountry ski snow conditions forecaster.
Public API Module
"""

from ullrs_secret.core import (
    wet_bulb_f,
    calculate_radiative_equivalent_temps,
    effective_temperature_f,
    calculate_snow_density,
    calculate_dynamic_corn_window,
)
from ullrs_secret.terrain import get_terrain_data
from ullrs_secret.snotel import find_nearest_snotel_stations, get_snotel_report
from ullrs_secret.import_data import write_weather_json
from ullrs_secret.pow_plot import plot_pow_forecast
from ullrs_secret.corn_plot import plot_corn_forecast
from ullrs_secret.consolidation_plot import plot_d_total_curve
from ullrs_secret.importers import get_importer, list_importers, fetch_weather
from ullrs_secret.plot_utils import prepare_effective_temp_data

__all__ = [
    # Core physics & math
    "wet_bulb_f",
    "calculate_radiative_equivalent_temps",
    "effective_temperature_f",
    "calculate_snow_density",
    "calculate_dynamic_corn_window",
    
    # Terrain
    "get_terrain_data",
    
    # SNOTEL Data
    "find_nearest_snotel_stations",
    "get_snotel_report",
    
    # Utilities
    "write_weather_json",
    
    # Importers
    "get_importer",
    "list_importers",
    "fetch_weather",
    
    # Data Preparation
    "prepare_effective_temp_data",
    
    # Plotting
    "plot_pow_forecast",
    "plot_corn_forecast",
    "plot_d_total_curve",
]
