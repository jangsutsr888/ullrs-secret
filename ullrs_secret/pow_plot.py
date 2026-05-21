"""Read standard weather JSON, compute effective temperatures, plot and export powder snow preservation forecast."""

import matplotlib.dates as mdates
import matplotlib.pyplot as plt

from ullrs_secret.plot_utils import (
    PT_ZONE,
    compute_segment_integral,
    export_forecast_csv,
    find_crossings_and_segments,
    prepare_effective_temp_data,
)


def plot_pow_forecast(times, adjusted_wbs, effective_temps, elevation_ft, lat, lon,
                           slope_deg=0.0, aspect_deg=180.0):
    """Generate the effective temperature forecast chart with melt/freeze integral annotations for powder preservation."""
    fig, ax = plt.subplots(figsize=(20, 7))

    valid_data = [(t, e) for t, e in zip(times, effective_temps) if e is not None]

    if valid_data:
        v_times = [d[0] for d in valid_data]
        v_eff = [d[1] for d in valid_data]

        segments, crossing_times = find_crossings_and_segments(v_times, v_eff)

        trans = ax.get_xaxis_transform()

        powder_degraded = False
        prev_day_etdh = None

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
                        mid_time, 0.96, f"melting\n+{integral:.1f} F-hrs",
                        transform=trans, color="darkred", ha="center", va="top",
                        fontsize=12, fontweight="bold",
                        bbox=dict(facecolor="white", alpha=0.6, edgecolor="none", pad=2),
                        zorder=6,
                    )
                    prev_day_etdh = integral
                    
                    if not powder_degraded:
                        cumulative_melt = 0.0
                        for i in range(len(seg_times) - 1):
                            dt_hours = (seg_times[i + 1] - seg_times[i]).total_seconds() / 3600.0
                            incr = 0.5 * ((seg_vals[i] - 32.0) + (seg_vals[i + 1] - 32.0)) * dt_hours
                            prev_cum = cumulative_melt
                            cumulative_melt += incr
                            if cumulative_melt >= 15.0:
                                frac = (15.0 - prev_cum) / incr if incr > 0 else 0
                                t_cross = seg_times[i] + (seg_times[i + 1] - seg_times[i]) * frac
                                ax.axvline(x=t_cross, color="purple", linestyle="--", linewidth=2, zorder=5, label="Powder Degraded (15 F-hrs)")
                                ax.text(t_cross, 0.5, " Powder\n Degraded", transform=ax.get_xaxis_text1_transform(0)[0], rotation=90, va='center', ha='right', color='purple', fontsize=12, fontweight='bold')
                                powder_degraded = True
                                break

                else:
                    ax.fill_between(
                        seg_times, seg_vals, 32, color="dodgerblue", alpha=0.15, zorder=1
                    )
                    ax.text(
                        mid_time, 0.04, f"freezing\n-{integral:.1f} F-hrs",
                        transform=trans, color="darkblue", ha="center", va="bottom",
                        fontsize=12, fontweight="bold",
                        bbox=dict(facecolor="white", alpha=0.6, edgecolor="none", pad=2),
                        zorder=6,
                    )
                    
                    if not powder_degraded and prev_day_etdh is not None:
                        if integral <= 30.0 or integral <= 0.8 * prev_day_etdh:
                            # Failed recovery, mark at end of segment
                            t_cross = seg_times[-1]
                            ax.axvline(x=t_cross, color="purple", linestyle="--", linewidth=2, zorder=5, label="Powder Settled (Recovery Failed)")
                            powder_degraded = True

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
        f"Powder Preservation Forecast - Elev: {elevation_ft} ft\n"
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
    
    # Avoid duplicate labels in legend
    handles, labels = ax.get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    plt.legend(by_label.values(), by_label.keys(), fontsize=14, loc="upper left")
    
    plt.tight_layout()

    current_size = fig.get_size_inches()
    fig.set_size_inches(current_size[0], current_size[1] + 4)
    plt.subplots_adjust(bottom=0.45)
    ax.legend(by_label.values(), by_label.keys(), loc="upper left", bbox_to_anchor=(0, -0.2), fontsize=12, frameon=True)

    manual_content = (
        f"Effective Temperature Reference Manual (Universal Radiative Model)\n"
        f"----------------------------------------------------------------------------------------------------------------------\n"
        f"  Effective Temp = Wet Bulb + Shortwave Radiative Equiv (+T) + Longwave Radiative Equiv (-T)\n"
        f"  * NOTE: This model explicitly calculates slope/aspect. Thresholds below apply universally to ANY slope.\n"
        f"----------------------------------------------------------------------------------------------------------------------\n"
        f"[Powder Preservation (Dry Snow)]\n"
        f" * Pristine Powder: Single Melt ETDH < 15 F-hrs. (Minimal energy to maintain crystal structure)\n"
        f" * Powder Recovery Check (Nightly): \n"
        f"    - Must meet EFDH > 30 F-hrs AND EFDH > 0.8 * Prev_Melt_ETDH to prevent settlement.\n"
        f" * Settlement / Getting Heavy: Single Melt ETDH >= 15 F-hrs or failed recovery. (Irreversible degradation)\n"
        f" * IMPORTANT: New snowfall acts as a 'Hard Reset'. Even if previous days had high melt integrals (e.g. 20-40 F-hrs),\n"
        f"   fresh accumulation overrides past heat debt. The 15 F-hrs timer starts fresh on the new surface layer.\n"
        f"----------------------------------------------------------------------------------------------------------------------\n"
        f"Note: ETDH = Melt Integral (T_eff > 32 F)  |  EFDH = Freeze Integral (T_eff < 32 F, absolute value)\n"
    )

    fig.text(
        0.5, 0.01, manual_content, ha="center", va="bottom", fontsize=11,
        family="monospace", linespacing=1.6,
        bbox=dict(facecolor="ghostwhite", alpha=0.9, edgecolor="lightgray", boxstyle="round,pad=1"),
    )

    plt.savefig("pow_forecast_chart.png", dpi=150, bbox_inches="tight")
    print(f"Chart saved to: pow_forecast_chart.png")
    return fig


def run_pow_plot(json_path, start_days=None, end_days=None, slope_deg=0.0, aspect_deg=180.0, target_elevation_ft=None):
    """Load weather data, compute effective temps, generate pow forecast chart and CSV."""
    elevation_ft, lat, lon, f_times, f_temps, f_rhs, adjusted_wbs, effective_temps = (
        prepare_effective_temp_data(json_path, start_days=start_days, end_days=end_days, slope_deg=slope_deg, aspect_deg=aspect_deg,
                                   target_elevation_ft=target_elevation_ft)
    )

    plot_pow_forecast(f_times, adjusted_wbs, effective_temps, elevation_ft, lat, lon,
                           slope_deg=slope_deg, aspect_deg=aspect_deg)
    export_forecast_csv(
        f_times, f_temps, f_rhs, adjusted_wbs, "pow_forecast_data.csv",
        effective_temps=effective_temps,
    )
