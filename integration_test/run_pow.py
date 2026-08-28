import os
import time

import matplotlib.pyplot as plt

import ullrs_secret as ullrs
from ullrs_secret.models import WeatherData


def main():
    # Construct path to the test data
    current_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(current_dir, "pow_weather_data.json")

    print(f"Loading weather data from {json_path}...")
    weather_data = WeatherData.from_json_file(json_path)

    # Specific coordinates for the integration test
    lat = 48.85868
    lon = -121.69884

    print(f"Fetching terrain data for {lat}, {lon}...")
    start_time = time.time()
    terrain = ullrs.get_terrain_data(lat=lat, lon=lon)
    fetch_time = time.time() - start_time
    print(f"Terrain: Elevation: {terrain['elevation_ft']:.1f} ft, Slope: {terrain['slope_deg']:.1f}°, Aspect: {terrain['aspect_deg']:.1f}°")
    print(f"Terrain fetch took {fetch_time:.4f} seconds")

    print("Preparing effective temperature data...")
    # Using data from March 14th (day 2 relative to start date) to the end of the dataset
    elevation_ft, data_lat, data_lon, times, eff_temps = ullrs.prepare_effective_temp_data(
        weather_data=weather_data,
        start_days=2.0,
        slope_deg=terrain['slope_deg'],
        aspect_deg=terrain['aspect_deg'],
        target_elevation_ft=terrain['elevation_ft']
    )

    print("Generating powder preservation plot...")
    fig = ullrs.plot_pow_forecast(
        times=times,
        effective_temps=eff_temps,
        elevation_ft=elevation_ft,
        lat=lat,
        lon=lon,
        slope_deg=terrain['slope_deg'],
        aspect_deg=terrain['aspect_deg']
    )

    output_path = os.path.abspath(os.path.join(current_dir, "..", "example", "integration-pow-forecast.png"))
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    print(f"Saved integration chart to {output_path}")

    if os.environ.get("ULLRS_SECRET_NO_SHOW") != "1":
        print("Opening plot...")
        plt.show()


if __name__ == "__main__":
    main()
