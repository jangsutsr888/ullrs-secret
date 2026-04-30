"""Read standard weather JSON, compute wet bulb temperatures, plot and export."""

import click
import json
from datetime import datetime, timedelta

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
import pytz

from .core import pressure_at_elevation, wet_bulb_f


def load_weather_data(json_path):
    """Load standard weather JSON, returning (elevation_ft, times, temps_f, rh_values)."""
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    elevation_ft = data.get("elevation_ft", 0.0)
    pt_zone = pytz.timezone("America/Los_Angeles")

    times, temps_f, rh_values = [], [], []
    for obs in data.get("observations", []):
        dt_obj = datetime.fromisoformat(obs["time_iso"])
        times.append(dt_obj.astimezone(pt_zone))
        temps_f.append(obs["air_temp_f"])
        rh_values.append(obs["relative_humidity_pct"])

    return elevation_ft, times, temps_f, rh_values


def plot_forecast(times, temps_f, adjusted_wbs, elevation_ft, days):
    """Generate the forecast chart with melt/freeze integral annotations."""
    fig, ax = plt.subplots(figsize=(20, 7))

    valid_data = [(t, w) for t, w in zip(times, adjusted_wbs) if w is not None]
    pt_zone = pytz.timezone("America/Los_Angeles")

    if valid_data:
        v_times = [d[0] for d in valid_data]
        v_wbs = [d[1] for d in valid_data]

        segments = []
        current_segment = [(v_times[0], v_wbs[0])]
        crossing_times = []

        for i in range(len(v_wbs) - 1):
            t1, w1 = v_times[i], v_wbs[i]
            t2, w2 = v_times[i + 1], v_wbs[i + 1]

            if (w1 - 32) * (w2 - 32) < 0:
                ratio = (32 - w1) / (w2 - w1)
                t_cross = t1 + (t2 - t1) * ratio
                crossing_times.append(t_cross)
                current_segment.append((t_cross, 32.0))
                segments.append(current_segment)
                current_segment = [(t_cross, 32.0), (t2, w2)]
            else:
                current_segment.append((t2, w2))
        segments.append(current_segment)

        trans = ax.get_xaxis_transform()

        for seg in segments:
            if len(seg) < 2:
                continue
            seg_times = [p[0] for p in seg]
            seg_wbs = [p[1] for p in seg]

            integral = 0.0
            for i in range(len(seg) - 1):
                dt_hours = (seg_times[i + 1] - seg_times[i]).total_seconds() / 3600.0
                integral += (
                    0.5 * abs((seg_wbs[i] - 32) + (seg_wbs[i + 1] - 32)) * dt_hours
                )

            mid_idx = len(seg) // 2
            is_melt = seg_wbs[mid_idx] > 32.0
            mid_time = seg_times[0] + (seg_times[-1] - seg_times[0]) / 2

            if integral > 0.5:
                if is_melt:
                    ax.fill_between(
                        seg_times, seg_wbs, 32, color="red", alpha=0.15, zorder=1
                    )
                    ax.text(
                        mid_time, 0.96, f"melting\n+{integral:.1f}",
                        transform=trans, color="darkred", ha="center", va="top",
                        fontsize=12, fontweight="bold",
                        bbox=dict(facecolor="white", alpha=0.6, edgecolor="none", pad=2),
                        zorder=6,
                    )
                else:
                    ax.fill_between(
                        seg_times, seg_wbs, 32, color="dodgerblue", alpha=0.15, zorder=1
                    )
                    ax.text(
                        mid_time, 0.04, f"freezing\n-{integral:.1f}",
                        transform=trans, color="darkblue", ha="center", va="bottom",
                        fontsize=12, fontweight="bold",
                        bbox=dict(facecolor="white", alpha=0.6, edgecolor="none", pad=2),
                        zorder=6,
                    )

        for ct in crossing_times:
            ax.axvline(x=ct, color="gray", linestyle="-.", alpha=0.8, linewidth=1.5, zorder=2)

    ax.plot(times, adjusted_wbs, marker="o", markersize=5, linestyle="-", color="teal",
            label="Altitude-Adjusted Wet Bulb Temp", zorder=4)
    ax.plot(times, temps_f, marker=".", markersize=4, linestyle="-", color="orange",
            alpha=0.6, label="Air Temp", zorder=3)
    ax.axhline(y=32, color="red", linestyle="--", linewidth=2,
               label="Freezing Point (32°F)", zorder=5)

    ax.set_title(
        f"Hourly Wet Bulb vs Air Temp ({days} Days Forecast) - Elev: {elevation_ft} ft\n"
        f"Timezone: US Pacific Time (PT)",
        fontsize=18,
    )
    ax.set_ylabel("Temperature (°F)", fontsize=14)

    ax.xaxis.set_major_locator(mdates.HourLocator(interval=6, tz=pt_zone))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%d %H:00", tz=pt_zone))
    ax.xaxis.set_minor_locator(mdates.HourLocator(interval=1, tz=pt_zone))
    ax.grid(True, which="major", axis="x", color="gray", linestyle="-", alpha=0.6)
    ax.grid(True, which="minor", axis="x", color="gray", linestyle=":", alpha=0.4)
    ax.grid(True, which="major", axis="y", color="gray", linestyle="--", alpha=0.5)

    if valid_data:
        ax.set_ylim(
            bottom=min(v_wbs + [t for t in temps_f if t is not None]) - 4,
            top=max(v_wbs + [t for t in temps_f if t is not None]) + 4,
        )

    plt.xticks(rotation=45, ha="right", fontsize=12)
    plt.yticks(fontsize=12)
    plt.legend(fontsize=14, loc="upper left")
    plt.tight_layout()

    current_size = fig.get_size_inches()
    fig.set_size_inches(current_size[0], current_size[1] + 4.5)
    plt.subplots_adjust(bottom=0.45)
    ax.legend(loc="upper left", bbox_to_anchor=(0, -0.25), fontsize=12, frameon=True)

    manual_content = (
        "Snow Quality Reference Manual\n"
        "----------------------------------------------------------------------------------------------------------------------\n"
        "[North Aspect Powder]                                   [South Aspect Corn Cycle]\n"
        " * Top Tier: WBTDH 0 ~ 5 F-hrs                           * Target: Snow Depth(inch) x K (PNW K=3, Rockies K=5)\n"
        " * Critical: WBTDH 15 ~ 20 F-hrs                         * Prime Corn: Current Day WBTDH 0 ~ 3 F-hrs\n"
        " * Isothermal (Ruined): WBTDH > 35 F-hrs                 * Sticky/Grabby Warning: Current Day WBTDH 5 ~ 8 F-hrs\n"
        "----------------------------------------------------------------------------------------------------------------------\n"
        "[Overnight Recovery & Safety]                           [Reset Protocol (Isothermal State)]\n"
        " * Freeze Failure: Night WBFDH < 10 F-hrs (Unsafe)       * False Recovery: Night WBFDH < 20 F-hrs (Breakable crust)\n"
        " * Energy Deficit: WBFDH < 0.5 * WBTDH (Deteriorating)   * Initial Stabilization: Night WBFDH 30 ~ 40 F-hrs\n"
        "                                                         * Full Reset: Night WBFDH > 50 F-hrs (Structure restored)\n"
        "----------------------------------------------------------------------------------------------------------------------\n"
        "Note: WBTDH = Melt Integral (T > 32 F)  |  WBFDH = Freeze Integral (T < 32 F)"
    )

    fig.text(
        0.5, 0.01, manual_content, ha="center", va="bottom", fontsize=11,
        family="monospace", linespacing=1.6,
        bbox=dict(facecolor="ghostwhite", alpha=0.9, edgecolor="lightgray", boxstyle="round,pad=1"),
    )

    plt.savefig("forecast_chart.png", dpi=150, bbox_inches="tight")
    print(f"图表已成功保存为: forecast_chart.png")
    return fig


def run_plot(json_path, days=3.0):
    """Load weather data, compute wet bulb temps, generate chart and CSV."""
    elevation_ft, times, temps_f, rh_values = load_weather_data(json_path)

    if not times:
        raise click.ClickException("No valid time series data found in JSON.")

    p_hpa = pressure_at_elevation(elevation_ft)
    print(f"Elevation: {elevation_ft} ft. Local pressure: {p_hpa:.2f} hPa")

    start_time = times[0]
    cutoff_date = start_time + timedelta(days=days)

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

    plot_forecast(f_times, f_temps, adjusted_wbs, elevation_ft, days)

    df = pd.DataFrame({
        "Time_PT": [t.strftime("%Y-%m-%d %H:%M:%S") for t in f_times],
        "Air_Temp_F": f_temps,
        "Relative_Humidity_Pct": f_rhs,
        "Adjusted_Wet_Bulb_F": adjusted_wbs,
    })
    df.to_csv("forecast_data.csv", index=False)
    print("Data saved to: forecast_data.csv")
