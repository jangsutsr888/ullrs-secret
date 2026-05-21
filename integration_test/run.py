import os
import matplotlib.pyplot as plt
import ullrs_secret as ullrs

def main():
    lat = 46.19080
    lon = -121.49325

    print(f"Fetching terrain data for {lat}, {lon}...")
    terrain = ullrs.get_terrain_data(lat=lat, lon=lon)
    print(f"Terrain: Elevation: {terrain['elevation_ft']:.1f} ft, Slope: {terrain['slope_deg']:.1f}°, Aspect: {terrain['aspect_deg']:.1f}°")

    print("Fetching weather data from Open-Meteo...")
    weather_data = ullrs.fetch_weather("openmeteo", lat=lat, lon=lon, model="best_match", timezone="America/Los_Angeles")
    
    temp_json = "temp_integration_weather.json"
    ullrs.write_weather_json(weather_data, temp_json)

    print("Preparing effective temperature data...")
    # By default, openmeteo provides about 7 days of forecast. The prompt asks for 5 days.
    # We can pass end_days=5.0 to prepare_effective_temp_data
    elevation_ft, data_lat, data_lon, times, temps, rhs, wbs, eff_temps = ullrs.prepare_effective_temp_data(
        json_path=temp_json,
        end_days=5.0,
        slope_deg=terrain['slope_deg'],
        aspect_deg=terrain['aspect_deg'],
        target_elevation_ft=terrain['elevation_ft']
    )

    print("Generating corn plot...")
    fig = ullrs.plot_corn_forecast(
        times=times,
        adjusted_wbs=wbs,
        effective_temps=eff_temps,
        elevation_ft=elevation_ft,
        lat=lat,
        lon=lon,
        slope_deg=terrain['slope_deg'],
        aspect_deg=terrain['aspect_deg']
    )

    print("Opening plot...")
    plt.show()

    # Clean up the temporary json file and the saved plot
    if os.path.exists(temp_json):
        os.remove(temp_json)
    if os.path.exists("corn_forecast_chart.png"):
        os.remove("corn_forecast_chart.png")

if __name__ == "__main__":
    main()
