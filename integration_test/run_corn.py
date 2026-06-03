import os
import time

import matplotlib.pyplot as plt

import ullrs_secret as ullrs
from ullrs_secret.models import WeatherData


def main():
    # Construct path to the test data
    current_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(current_dir, "corn_weather_data.json")

    print(f"Loading weather data from {json_path}...")
    weather_data = WeatherData.from_json_file(json_path)

    # Specific coordinates for the integration test
    lat = 47.45686
    lon = -120.94978

    print(f"Fetching terrain data for {lat}, {lon}...")
    start_time = time.time()
    terrain = ullrs.get_terrain_data(lat=lat, lon=lon)
    fetch_time = time.time() - start_time
    print(f"Terrain: Elevation: {terrain['elevation_ft']:.1f} ft, Slope: {terrain['slope_deg']:.1f}°, Aspect: {terrain['aspect_deg']:.1f}°")
    print(f"Terrain fetch took {fetch_time:.4f} seconds")

    print("Preparing effective temperature data...")
    # Using all available data without specifying start_days or end_days
    elevation_ft, data_lat, data_lon, times, eff_temps = ullrs.prepare_effective_temp_data(
        weather_data=weather_data,
        slope_deg=terrain['slope_deg'],
        aspect_deg=terrain['aspect_deg'],
        target_elevation_ft=terrain['elevation_ft']
    )

    print("Generating corn plot...")
    fig = ullrs.plot_corn_forecast(
        times=times,
        effective_temps=eff_temps,
        elevation_ft=elevation_ft,
        lat=lat,
        lon=lon,
        slope_deg=terrain['slope_deg'],
        aspect_deg=terrain['aspect_deg']
    )

    print("Opening plot...")
    plt.show()


if __name__ == "__main__":
    main()
