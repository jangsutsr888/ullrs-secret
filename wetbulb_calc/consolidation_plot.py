"""
Read standard weather JSON, compute wet bulb temperatures via .core, 
calculate melt-freeze structural consolidation, and plot the D_total curve.
"""

import click
import json
import math
from datetime import datetime, timedelta

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytz

# Import the physics functions from your core module
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


def plot_d_total_curve(times, adjusted_wbs, elevation_ft, days, h0_snow=20.0):
    """Generate a focused chart showing only the D_total progression."""
    fig, ax = plt.subplots(figsize=(16, 7))

    valid_data = [(t, w) for t, w in zip(times, adjusted_wbs) if w is not None]
    pt_zone = pytz.timezone("America/Los_Angeles")

    if not valid_data:
        print("No valid data to plot.")
        return fig

    v_times = [d[0] for d in valid_data]
    v_wbs = [d[1] for d in valid_data]

    # --- 1. Identify Crossings and Segments ---
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

    # --- 2. Calculate Integrals & Thermodynamic Model ---
    K_M = 0.5
    K_F = 2.5
    S_SOUTH = 20.0  

    current_Im = 0.0 
    current_If = 0.0 
    
    d_total_times = [v_times[0]]
    d_total_values = [0.0]
    current_d_total = 0.0

    for seg in segments:
        if len(seg) < 2:
            continue
        seg_times = [p[0] for p in seg]
        seg_wbs = [p[1] for p in seg]

        integral = 0.0
        for i in range(len(seg) - 1):
            dt_hours = (seg_times[i + 1] - seg_times[i]).total_seconds() / 3600.0
            integral += 0.5 * abs((seg_wbs[i] - 32) + (seg_wbs[i + 1] - 32)) * dt_hours

        mid_idx = len(seg) // 2
        is_melt = seg_wbs[mid_idx] > 32.0

        if is_melt:
            if current_If > 0:
                # ===== MOD 1: Freeze Failure (Energy Deficit) =====
                # If the nightly freeze integral is less than 30% of the daytime melt,
                # the free water acts as a lubricant rather than a bond. 
                # The existing consolidated base begins to disintegrate.
                if current_Im > 0 and current_If < (current_Im * 0.3):
                    degradation = (current_Im * 0.3 - current_If) * 0.5
                    current_d_total -= degradation
                    current_d_total = max(0, current_d_total) # Depth cannot be negative
                else:
                    # Normal refreeze and consolidation process
                    M_eff = current_Im + S_SOUTH
                    D_melt = K_M * M_eff
                    D_freeze = K_F * math.sqrt(current_If) 
                    D_cycle = min(D_melt, D_freeze)
                    current_d_total += D_cycle
                # ===================================================

                # Record the supportable state at the end of the morning freezing period
                d_total_times.append(seg_times[0]) 
                d_total_values.append(current_d_total)

                # Reset integrals for the new cycle
                current_Im = 0.0
                current_If = 0.0

            current_Im += integral

            # ===== MOD 2: Isothermal Collapse (Overheating) =====
            # If the snowpack experiences extreme, sustained melting without a refreeze 
            # (e.g., cumulative melt integral > 40 F-hrs), the isothermal structure 
            # becomes saturated with liquid water and rapidly collapses.
            if current_Im > 40.0 and current_d_total > 0:
                # Continuous decay proportional to the melt integral step
                current_d_total -= (integral * 0.2) 
                current_d_total = max(0, current_d_total)
                
                # Real-time recording of the decline in supportability during the daytime heat
                d_total_times.append(seg_times[-1])
                d_total_values.append(current_d_total)
            # ====================================================
        else:
            current_If += integral

    if current_If > 0 or current_Im > 0:
        d_total_times.append(v_times[-1])
        d_total_values.append(current_d_total)

    # --- 3. Plotting D_total Curve ---
    ax.step(d_total_times, d_total_values, where='post', color="purple", linewidth=3.5, 
             linestyle="-", label="Consolidated Depth ($D_{total}$)", zorder=5)
    
    ax.fill_between(d_total_times, d_total_values, step="post", color="purple", alpha=0.15, zorder=4)

    support_threshold = min(h0_snow, 15.0)
    ax.axhline(y=support_threshold, color="crimson", linestyle="--", linewidth=2.5, 
                label=f"Support Threshold ({support_threshold} cm)", zorder=6)

    for i, val in enumerate(d_total_values):
        if val >= support_threshold and d_total_values[i-1] < support_threshold:
            cross_time = d_total_times[i]
            ax.text(cross_time, support_threshold + 0.5, " Base Formed (Go!)", 
                    color="crimson", fontweight="bold", fontsize=12, zorder=7)
            ax.plot(cross_time, val, marker="*", color="gold", markersize=15, 
                    markeredgecolor="red", zorder=8)
            break

    # --- 4. Formatting & Layout ---
    ax.set_title(
        f"South Aspect Corn Base Consolidation ($D_{{total}}$)\n"
        f"Initial New Snow: {h0_snow} cm | Elev: {elevation_ft} ft",
        fontsize=18, fontweight="bold", pad=15
    )
    
    ax.set_ylabel("Cumulative Consolidated Depth (cm)", fontsize=14, color="purple")
    ax.set_xlabel("Time (Pacific Time)", fontsize=14)
    
    ax.xaxis.set_major_locator(mdates.HourLocator(interval=6, tz=pt_zone))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%d %H:00", tz=pt_zone))
    
    ax.grid(True, which="major", axis="x", color="gray", linestyle="-", alpha=0.3)
    ax.grid(True, which="major", axis="y", color="gray", linestyle="--", alpha=0.5)

    ax.set_ylim(bottom=0, top=max(20.0, max(d_total_values) + 5))
    ax.set_xlim(left=v_times[0], right=v_times[-1])

    plt.setp(ax.get_xticklabels(), rotation=45, ha="right", fontsize=12)
    ax.legend(loc="upper left", fontsize=13, framealpha=0.9, shadow=True)
    plt.tight_layout()

    # --- 5. Appended Mechanism Manual ---
    current_size = fig.get_size_inches()
    fig.set_size_inches(current_size[0], current_size[1] + 3.5)
    plt.subplots_adjust(bottom=0.35)

    manual_content = (
        "Thermodynamic Consolidation Model (South Aspect)\n"
        "----------------------------------------------------------------------------------------------------------------------\n"
        " * M_eff (Effective Melt) = Daily Melt Integral (°F·h) + South Solar Bonus (20 °F·h)\n"
        " * D_melt (Percolation) = 0.5 * M_eff   | Water drives settlement & destroys dendrites.\n"
        " * D_freeze (Refreeze) = 2.5 * sqrt(Nightly Freeze Integral) | Stefan's Law (Non-linear depth diffusion).\n"
        " * D_cycle = min(D_melt, D_freeze)      | The actual structural gain added at the end of each freeze cycle.\n"
        "----------------------------------------------------------------------------------------------------------------------\n"
        " Decision Matrix: \n"
        " - Wait until D_total crosses the Support Threshold before committing to steep lines.\n"
        " - The star icon (*) marks the exact morning the base locks in."
    )

    fig.text(
        0.5, 0.02, manual_content, ha="center", va="bottom", fontsize=12,
        family="monospace", linespacing=1.6,
        bbox=dict(facecolor="ghostwhite", alpha=0.9, edgecolor="lightgray", boxstyle="round,pad=1"),
    )

    plt.savefig("d_total_curve.png", dpi=150, bbox_inches="tight")
    print(f"Chart saved to: d_total_curve.png")
    return fig


def run_consolidation_model(json_path, days=3.0, h0_snow=20.0):
    """
    Load weather data, compute wet bulb temps via .core, generate D_total chart and CSV.
    """
    elevation_ft, times, temps_f, rh_values = load_weather_data(json_path)

    if not times:
        raise click.ClickException("No valid time series data found in JSON.")

    # 1. Use .core to calculate local pressure
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

    # 2. Use .core to calculate wet bulb temperatures
    adjusted_wbs = []
    for t_f, rh in zip(f_temps, f_rhs):
        if t_f is not None and rh is not None:
            t_c = (t_f - 32) * 5.0 / 9.0
            # Call the physics function from .core
            adjusted_wbs.append(wet_bulb_f(t_c, rh, p_hpa))
        else:
            adjusted_wbs.append(None)

    # 3. Pass the fully computed wet bulb data to the plotting logic
    plot_d_total_curve(f_times, adjusted_wbs, elevation_ft, days, h0_snow=h0_snow)

    # 4. Export the data to CSV for verification
    df = pd.DataFrame({
        "Time_PT": [t.strftime("%Y-%m-%d %H:%M:%S") for t in f_times],
        "Air_Temp_F": f_temps,
        "Relative_Humidity_Pct": f_rhs,
        "Adjusted_Wet_Bulb_F": adjusted_wbs,
    })
    df.to_csv("consolidation_forecast_data.csv", index=False)
    print("Data saved to: consolidation_forecast_data.csv")
