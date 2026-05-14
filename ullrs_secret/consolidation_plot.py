"""
Read standard weather JSON, compute effective temperatures via .core,
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
    prepare_effective_temp_data,
)


def plot_d_total_curve(times, effective_temps, elevation_ft, swe_mm=30.0, h0_snow_cm=20.0, slope_deg=0.0, aspect_deg=180.0):
    """
    Generate a focused chart showing the D_total progression.
    Uses pure physics: calculates density directly from SWE and physical depth to derive
    dynamic heat transfer (K_F) and percolation (K_M) coefficients.
    """
    fig, ax = plt.subplots(figsize=(16, 7))

    valid_data = [(t, e) for t, e in zip(times, effective_temps) if e is not None]

    if not valid_data:
        print("No valid data to plot.")
        return fig

    v_times = [d[0] for d in valid_data]
    v_effs = [d[1] for d in valid_data]

    # --- 1. Identify Crossings and Segments ---
    segments, crossing_times = find_crossings_and_segments(v_times, v_effs)

    # --- 2. Calculate Integrals & Dynamic Thermodynamic Model ---
    from .core import calculate_snow_density, get_consolidation_coefficients, calculate_melt_depth, calculate_freeze_depth

    # Calculate real physical density (water is 1.0)
    real_density = calculate_snow_density(swe_mm, h0_snow_cm)

    # Continuous functions for coefficients based on density
    K_M, K_F = get_consolidation_coefficients(real_density)

    current_Im = 0.0
    current_If = 0.0

    d_total_times = [v_times[0]]
    d_total_values = [0.0]
    current_d_total = 0.0
    current_d_wet = 0.0  # Tracks un-frozen liquid water penetration depth

    for seg in segments:
        if len(seg) < 2:
            continue
        seg_times = [p[0] for p in seg]
        seg_effs = [p[1] for p in seg]

        integral = compute_segment_integral(seg_times, seg_effs)

        mid_idx = len(seg) // 2
        is_melt = seg_effs[mid_idx] > 32.0

        if is_melt:
            if current_If > 0:
                D_melt = calculate_melt_depth(current_Im, K_M)
                D_freeze = calculate_freeze_depth(current_If, K_F)

                # ===== FIXED: Two-State (Crust / Wet Layer) Mass Balance =====
                # 1. Melt phase: daytime heat first attacks existing crust, turning it into wet snow
                melt_from_crust = min(current_d_total, D_melt)
                current_d_total -= melt_from_crust
                current_d_wet += D_melt  # Total wet snow generated
                
                # Constrain total wet depth to available snow depth
                current_d_wet = min(h0_snow_cm - current_d_total, current_d_wet)

                # ===== MOD 1: Freeze Failure (Energy Deficit) =====
                # If the nightly freeze integral is less than 70% of the daytime melt,
                # the free water acts as a lubricant rather than a bond.
                if current_Im > 0 and current_If < (current_Im * 0.7):
                    # FIX: Dimensionality - Convert energy deficit to physical depth using K_M
                    energy_deficit = (current_Im * 0.7) - current_If
                    degradation = calculate_melt_depth(energy_deficit, K_M) * 0.5
                    
                    current_d_total -= degradation
                    current_d_total = max(0, current_d_total)
                    
                    # Partial freeze still converts some wet snow to crust
                    freeze_amount = min(current_d_wet, D_freeze)
                    current_d_total += freeze_amount
                    current_d_wet -= freeze_amount
                    current_d_wet = max(0, current_d_wet)
                else:
                    # Normal refreeze and consolidation process
                    freeze_amount = min(current_d_wet, D_freeze)
                    current_d_total += freeze_amount
                    current_d_wet -= freeze_amount
                    current_d_wet = max(0, current_d_wet)
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
            # (e.g., cumulative melt integral > 120 F-hrs), the isothermal structure
            # becomes saturated with liquid water and rapidly collapses.
            if current_Im > 120.0 and current_d_total > 0:
                # FIX: Dimensionality - Use K_M to convert integral step to depth
                current_d_total -= calculate_melt_depth(integral, K_M) * 0.2
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

    # --- Thin Snowpack: Bottoming Out Effect ---
    thin_snow_limit = 8.0  # cm. Below this, breakable crust is skiable via bottoming out.
    is_thin_snow = h0_snow_cm <= thin_snow_limit

    if is_thin_snow:
        ax.axhspan(0, support_threshold, color="darkorange", alpha=0.1, zorder=3,
                   label="Skiable (Bottoming Out)")
        
        # Place text in the first quarter of the graph
        text_x_idx = min(len(d_total_times) // 4, len(d_total_times) - 1)
        if text_x_idx >= 0:
            ax.text(d_total_times[text_x_idx], support_threshold / 2,
                    "⚠️ Skiable (Bottoming Out)\nExpect Scratchy/Chattery Feel",
                    color="darkorange", fontsize=11, fontweight="bold", zorder=7,
                    bbox=dict(facecolor="white", alpha=0.7, edgecolor="none", pad=2))

    for i, val in enumerate(d_total_values):
        if val >= support_threshold and (i == 0 or d_total_values[i-1] < support_threshold):
            cross_time = d_total_times[i]
            msg = " Base Formed (Smooth Corn!)" if is_thin_snow else " Base Formed (Go!)"
            ax.text(cross_time, support_threshold + 0.5, msg,
                    color="crimson", fontweight="bold", fontsize=12, zorder=7)
            ax.plot(cross_time, val, marker="*", color="gold", markersize=15,
                    markeredgecolor="red", zorder=8)
            break

    # --- 4. Formatting & Layout ---
    ASPECT_LABELS = {0: "N", 45: "NE", 90: "E", 135: "SE", 180: "S", 225: "SW", 270: "W", 315: "NW", 360: "N"}
    closest_cardinal = min(ASPECT_LABELS, key=lambda k: abs(k - aspect_deg % 360))
    aspect_label = ASPECT_LABELS[closest_cardinal]

    ax.set_title(
        f"{aspect_label} Aspect ({slope_deg}°) Corn Base Consolidation ($D_{{total}}$)\n"
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

    thin_snow_instruction = (
        "\n - THIN SNOW (< 8cm): Breakable crust won't trap skis. Skiable before fully frozen via 'Bottoming Out' (scratchy)."
    ) if is_thin_snow else ""

    manual_content = (
        "Thermodynamic Model [Dynamic Density Engine]\n"
        "----------------------------------------------------------------------------------------------------------------------\n"
        f" * Real-time Density: {real_density*100:.1f}% (Derived from {swe_mm} mm SWE and {h0_snow_cm} cm Depth)\n"
        f" * Dynamic Percolation (K_M) = {K_M:.2f}  | Dynamic Freeze Conductivity (K_F) = {K_F:.2f}\n"
        " * D_melt = K_M * Effective Melt      | D_freeze = K_F * sqrt(Freeze Integral)\n"
        " * Degradation Penalties applied for Freeze Failures (If < 70% Im) and Isothermal Overheating (Im > 120).\n"
        "----------------------------------------------------------------------------------------------------------------------\n"
        " Decision Matrix: \n"
        " - Wait until D_total crosses the Support Threshold before committing to steep lines.\n"
        f" - The star icon (*) marks the exact morning the base locks in.{thin_snow_instruction}"
    )

    fig.text(
        0.5, 0.02, manual_content, ha="center", va="bottom", fontsize=12,
        family="monospace", linespacing=1.6,
        bbox=dict(facecolor="ghostwhite", alpha=0.9, edgecolor="lightgray", boxstyle="round,pad=1"),
    )

    plt.savefig("d_total_curve.png", dpi=150, bbox_inches="tight")
    print(f"Chart saved to: d_total_curve.png")
    return fig


def run_consolidation_model(json_path, start_days=None, end_days=None, swe_mm=30.0, h0_snow_cm=20.0, slope_deg=0.0, aspect_deg=180.0, target_elevation_ft=None):
    """Load weather data, compute effective temps via .core, generate D_total chart and CSV."""
    elevation_ft, lat, lon, f_times, f_temps, f_rhs, adjusted_wbs, effective_temps = prepare_effective_temp_data(
        json_path, start_days, end_days, slope_deg=slope_deg, aspect_deg=aspect_deg, target_elevation_ft=target_elevation_ft
    )

    plot_d_total_curve(f_times, effective_temps, elevation_ft, swe_mm=swe_mm, h0_snow_cm=h0_snow_cm, slope_deg=slope_deg, aspect_deg=aspect_deg)
    export_forecast_csv(f_times, f_temps, f_rhs, adjusted_wbs, "consolidation_forecast_data.csv", effective_temps=effective_temps)
