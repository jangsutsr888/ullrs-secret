"""
Read standard weather JSON, compute wet bulb temperatures via .core,
calculate melt-freeze structural consolidation, and plot the D_total curve.
"""

import math

import matplotlib.dates as mdates
import matplotlib.pyplot as plt

from .plot_utils import (
    PT_ZONE,
    compute_segment_integral,
    export_forecast_csv,
    find_crossings_and_segments,
    prepare_forecast_data,
)


def plot_d_total_curve(times, adjusted_wbs, elevation_ft, swe_mm=30.0, h0_snow_cm=20.0):
    """
    Generate a focused chart showing the D_total progression.
    Uses pure physics: calculates density directly from SWE and physical depth to derive
    dynamic heat transfer (K_F) and percolation (K_M) coefficients.
    """
    fig, ax = plt.subplots(figsize=(16, 7))

    valid_data = [(t, w) for t, w in zip(times, adjusted_wbs) if w is not None]

    if not valid_data:
        print("No valid data to plot.")
        return fig

    v_times = [d[0] for d in valid_data]
    v_wbs = [d[1] for d in valid_data]

    # --- 1. Identify Crossings and Segments ---
    segments, crossing_times = find_crossings_and_segments(v_times, v_wbs)

    # --- 2. Calculate Integrals & Dynamic Thermodynamic Model ---

    # Calculate real physical density (water is 1.0)
    # SWE (mm) / 10 = SWE (cm). Density = SWE (cm) / Depth (cm)
    real_density = (swe_mm / 10.0) / h0_snow_cm

    # Constrain density to realistic snow bounds (5% to 60%)
    real_density = max(0.05, min(0.60, real_density))

    # Continuous functions for coefficients based on density
    # e.g., Density 0.10 (Dry) -> K_M ~0.3, K_F ~1.5
    # e.g., Density 0.35 (Wet) -> K_M ~0.8, K_F ~4.0
    K_M = (real_density * 2.0) + 0.1
    K_F = (real_density * 10.0) + 0.5

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

        integral = compute_segment_integral(seg_times, seg_wbs)

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

    support_threshold = min(h0_snow_cm, 15.0)
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
        f"SWE: {swe_mm} mm | Depth: {h0_snow_cm} cm | Density: {real_density*100:.0f}% | Elev: {elevation_ft} ft",
        fontsize=18, fontweight="bold", pad=15
    )

    ax.set_ylabel("Cumulative Consolidated Depth (cm)", fontsize=14, color="purple")
    ax.set_xlabel("Time (Pacific Time)", fontsize=14)

    ax.xaxis.set_major_locator(mdates.HourLocator(interval=6, tz=PT_ZONE))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%d %H:00", tz=PT_ZONE))

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
        "Thermodynamic Model [Dynamic Density Engine]\n"
        "----------------------------------------------------------------------------------------------------------------------\n"
        f" * Real-time Density: {real_density*100:.1f}% (Derived from {swe_mm} mm SWE and {h0_snow_cm} cm Depth)\n"
        f" * Dynamic Percolation (K_M) = {K_M:.2f}  | Dynamic Freeze Conductivity (K_F) = {K_F:.2f}\n"
        " * D_melt = K_M * Effective Melt      | D_freeze = K_F * sqrt(Freeze Integral)\n"
        " * Degradation Penalties applied for Freeze Failures (If < 30% Im) and Isothermal Overheating (Im > 40).\n"
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


def run_consolidation_model(json_path, start_days=None, end_days=None, swe_mm=30.0, h0_snow_cm=20.0):
    """Load weather data, compute wet bulb temps via .core, generate D_total chart and CSV."""
    elevation_ft, f_times, f_temps, f_rhs, adjusted_wbs = prepare_forecast_data(json_path, start_days, end_days)

    plot_d_total_curve(f_times, adjusted_wbs, elevation_ft, swe_mm=swe_mm, h0_snow_cm=h0_snow_cm)
    export_forecast_csv(f_times, f_temps, f_rhs, adjusted_wbs, "consolidation_forecast_data.csv")
