"""Read standard weather JSON, compute effective temperatures, plot and export."""

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pytz

from .plot_utils import (
    PT_ZONE,
    compute_segment_integral,
    export_forecast_csv,
    find_crossings_and_segments,
    prepare_effective_temp_data,
)


def plot_effective_forecast(times, adjusted_wbs, effective_temps, elevation_ft, lat, lon, days,
                           slope_deg=0.0, aspect_deg=180.0):
    """Generate the effective temperature forecast chart with melt/freeze integral annotations."""
    fig, ax = plt.subplots(figsize=(20, 7))

    valid_data = [(t, e) for t, e in zip(times, effective_temps) if e is not None]

    if valid_data:
        v_times = [d[0] for d in valid_data]
        v_eff = [d[1] for d in valid_data]

        segments, crossing_times = find_crossings_and_segments(v_times, v_eff)

        trans = ax.get_xaxis_transform()

        for seg in segments:
            if len(seg) < 2:
                continue
            seg_times = [p[0] for p in seg]
            seg_vals = [p[1] for p in seg]

            integral = compute_segment_integral(seg_times, seg_vals)

            mid_idx = len(seg) // 2
            is_melt = seg_vals[mid_idx] > 32.0
            mid_time = seg_times[0] + (seg_times[-1] - seg_times[0]) / 2

            if integral > 0.5:
                if is_melt:
                    ax.fill_between(
                        seg_times, seg_vals, 32, color="red", alpha=0.15, zorder=1
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
                        seg_times, seg_vals, 32, color="dodgerblue", alpha=0.15, zorder=1
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

    ax.plot(times, effective_temps, marker="o", markersize=5, linestyle="-", color="teal",
            label="Effective Temperature", zorder=4)
    ax.plot(times, adjusted_wbs, marker=".", markersize=4, linestyle="-", color="orange",
            alpha=0.6, label="Wet Bulb Temp", zorder=3)
    ax.axhline(y=32, color="red", linestyle="--", linewidth=2,
               label="Freezing Point (32°F)", zorder=5)

    ASPECT_LABELS = {0: "N", 45: "NE", 90: "E", 135: "SE", 180: "S", 225: "SW", 270: "W", 315: "NW", 360: "N"}
    closest_cardinal = min(ASPECT_LABELS, key=lambda k: abs(k - aspect_deg % 360))
    aspect_label = ASPECT_LABELS[closest_cardinal]

    lat_str = f"{abs(lat):.4f}°{'N' if lat >= 0 else 'S'}" if lat is not None else "N/A"
    lon_str = f"{abs(lon):.4f}°{'W' if lon < 0 else 'E'}" if lon is not None else "N/A"

    ax.set_title(
        f"Hourly Effective Temp vs Wet Bulb Temp ({days} Days Forecast) - Elev: {elevation_ft} ft\n"
        f"Location: {lat_str}, {lon_str} | Slope: {slope_deg:.0f}° {aspect_label} aspect | Timezone: US Pacific Time (PT)",
        fontsize=18,
    )
    ax.set_ylabel("Temperature (°F)", fontsize=14)

    ax.xaxis.set_major_locator(mdates.HourLocator(interval=6, tz=PT_ZONE))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%d %H:00", tz=PT_ZONE))
    ax.xaxis.set_minor_locator(mdates.HourLocator(interval=1, tz=PT_ZONE))
    ax.grid(True, which="major", axis="x", color="gray", linestyle="-", alpha=0.6)
    ax.grid(True, which="minor", axis="x", color="gray", linestyle=":", alpha=0.4)
    ax.grid(True, which="major", axis="y", color="gray", linestyle="--", alpha=0.5)

    if valid_data:
        all_vals = v_eff + [w for w in adjusted_wbs if w is not None]
        ax.set_ylim(
            bottom=min(all_vals) - 4,
            top=max(all_vals) + 4,
        )

    plt.xticks(rotation=45, ha="right", fontsize=12)
    plt.yticks(fontsize=12)
    plt.legend(fontsize=14, loc="upper left")
    plt.tight_layout()

    current_size = fig.get_size_inches()
    fig.set_size_inches(current_size[0], current_size[1] + 6)
    plt.subplots_adjust(bottom=0.52)
    ax.legend(loc="upper left", bbox_to_anchor=(0, -0.25), fontsize=12, frameon=True)

    manual_content = (
        "Effective Temperature Reference Manual (Universal Radiative Model)\n"
        "----------------------------------------------------------------------------------------------------------------------\n"
        "  Effective Temp = Wet Bulb + Shortwave Radiative Equiv (+T) + Longwave Radiative Equiv (-T)\n"
        "  * NOTE: This model explicitly calculates slope/aspect. Thresholds below apply universally to ANY slope.\n"
        "----------------------------------------------------------------------------------------------------------------------\n"
        "[Phase 1: Powder Preservation (Dry Snow)]\n"
        " * Pristine Powder (Daily): Daily ETDH < 15 F-hrs. (Minimal energy to maintain crystal structure)\n"
        " * Powder Recovery Check (Nightly): \n"
        "    - Must meet EFDH > 30 F-hrs AND EFDH > 0.8 * Prev_Day_ETDH to prevent settlement.\n"
        " * Settlement / Getting Heavy: Daily ETDH 20 ~ 40 F-hrs. (Snow begins to round and densify)\n"
        "----------------------------------------------------------------------------------------------------------------------\n"
        "[Phase 2: The Corn Cycle (Melt-Freeze)]\n"
        " * Crust Break-through: Daily ETDH 40 ~ 60 F-hrs. (DANGEROUS: Weak surface, 'breakable' crust, high ACL risk)\n"
        " * PRIME CORN WINDOW: Daily ETDH 60 ~ 90 F-hrs. (Perfect 2-3cm soft surface over supportable base)\n"
        " * Sticky/Grabby (Overcooked): Daily ETDH 100 ~ 130 F-hrs. (Deep melt, suction effect, high drag)\n"
        "----------------------------------------------------------------------------------------------------------------------\n"
        "[Phase 3: Danger & Reset Protocol (Isothermal/Wet)]\n"
        " * Wet Avalanche Warning: Daily ETDH > 150 F-hrs. (Water percolating deep into snowpack)\n"
        " * Overnight Reset Requirements (to clear heat debt):\n"
        "    - Poor Reset (Supportable? No): Night EFDH < 60 F-hrs. (Surface may refreeze, but base remains unstable)\n"
        "    - Full Reset (Structure Restored): Night EFDH 100 ~ 150 F-hrs.\n"
        "    - Energy Deficit Alert: Night EFDH must be >= 0.7 * Previous Day ETDH for slope stabilization.\n"
        "----------------------------------------------------------------------------------------------------------------------\n"
        "Note: ETDH = Melt Integral (T_eff > 32 F)  |  EFDH = Freeze Integral (T_eff < 32 F, absolute value)\n"
    )

    fig.text(
        0.5, 0.01, manual_content, ha="center", va="bottom", fontsize=11,
        family="monospace", linespacing=1.6,
        bbox=dict(facecolor="ghostwhite", alpha=0.9, edgecolor="lightgray", boxstyle="round,pad=1"),
    )

    plt.savefig("effective_temp_chart.png", dpi=150, bbox_inches="tight")
    print(f"Chart saved to: effective_temp_chart.png")
    return fig


def run_effective_plot(json_path, days=3.0, slope_deg=0.0, aspect_deg=180.0):
    """Load weather data, compute effective temps, generate chart and CSV."""
    elevation_ft, lat, lon, f_times, f_temps, f_rhs, adjusted_wbs, effective_temps = (
        prepare_effective_temp_data(json_path, days, slope_deg=slope_deg, aspect_deg=aspect_deg)
    )

    plot_effective_forecast(f_times, adjusted_wbs, effective_temps, elevation_ft, lat, lon, days,
                           slope_deg=slope_deg, aspect_deg=aspect_deg)
    export_forecast_csv(
        f_times, f_temps, f_rhs, adjusted_wbs, "effective_temp_data.csv",
        effective_temps=effective_temps,
    )
