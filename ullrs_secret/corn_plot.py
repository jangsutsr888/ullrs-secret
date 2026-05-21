"""Read standard weather JSON, compute effective temperatures, plot and export corn snow forecast."""

import matplotlib.dates as mdates
import matplotlib.pyplot as plt

from ullrs_secret.core import get_consolidation_coefficients, calculate_melt_depth, calculate_freeze_depth, calculate_dynamic_corn_window
from ullrs_secret.plot_utils import (
    PT_ZONE,
    compute_segment_integral,
    export_forecast_csv,
    find_crossings_and_segments,
    prepare_effective_temp_data,
)


def plot_corn_forecast(times, adjusted_wbs, effective_temps, elevation_ft, lat, lon,
                           slope_deg=0.0, aspect_deg=180.0, snow_density=0.5):
    """Generate the effective temperature forecast chart with melt/freeze integral annotations for corn snow."""
    fig, ax = plt.subplots(figsize=(20, 7))

    # Assume typical spring snow (density ~0.35) for depth annotations
    K_M, K_F = get_consolidation_coefficients(snow_density)
    
    min_fhrs, max_fhrs = calculate_dynamic_corn_window(snow_density)

    valid_data = [(t, e) for t, e in zip(times, effective_temps) if e is not None]

    if valid_data:
        v_times = [d[0] for d in valid_data]
        v_eff = [d[1] for d in valid_data]

        segments, crossing_times = find_crossings_and_segments(v_times, v_eff)

        trans = ax.get_xaxis_transform()

        corn_zones = []

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
                    d_melt = calculate_melt_depth(integral, K_M)
                    ax.fill_between(
                        seg_times, seg_vals, 32, color="red", alpha=0.15, zorder=1
                    )
                    ax.text(
                        mid_time, 0.96, f"melting\n+{integral:.1f}\n{d_melt:.2f} cm",
                        transform=trans, color="darkred", ha="center", va="top",
                        fontsize=12, fontweight="bold",
                        bbox=dict(facecolor="white", alpha=0.6, edgecolor="none", pad=2),
                        zorder=6,
                    )
                else:
                    d_freeze = calculate_freeze_depth(integral, K_F)
                    ax.fill_between(
                        seg_times, seg_vals, 32, color="dodgerblue", alpha=0.15, zorder=1
                    )
                    ax.text(
                        mid_time, 0.04, f"freezing\n-{integral:.1f}\n{d_freeze:.2f} cm",
                        transform=trans, color="darkblue", ha="center", va="bottom",
                        fontsize=12, fontweight="bold",
                        bbox=dict(facecolor="white", alpha=0.6, edgecolor="none", pad=2),
                        zorder=6,
                    )

            if is_melt and integral >= min_fhrs:
                cumulative_melt = 0.0
                zone_times = []
                zone_vals = []

                for i in range(len(seg_times) - 1):
                    dt_hours = (seg_times[i + 1] - seg_times[i]).total_seconds() / 3600.0
                    incr = 0.5 * ((seg_vals[i] - 32.0) + (seg_vals[i + 1] - 32.0)) * dt_hours
                    prev_cum = cumulative_melt
                    cumulative_melt += incr

                    if prev_cum < min_fhrs and cumulative_melt >= min_fhrs:
                        frac = (min_fhrs - prev_cum) / incr if incr > 0 else 0
                        t_cross = seg_times[i] + (seg_times[i + 1] - seg_times[i]) * frac
                        v_cross = seg_vals[i] + (seg_vals[i + 1] - seg_vals[i]) * frac
                        zone_times.append(t_cross)
                        zone_vals.append(v_cross)

                    if cumulative_melt >= max_fhrs:
                        frac = (max_fhrs - prev_cum) / incr if incr > 0 else 0
                        t_cross = seg_times[i] + (seg_times[i + 1] - seg_times[i]) * frac
                        v_cross = seg_vals[i] + (seg_vals[i + 1] - seg_vals[i]) * frac
                        zone_times.append(t_cross)
                        zone_vals.append(v_cross)
                        break

                    if cumulative_melt >= min_fhrs:
                        zone_times.append(seg_times[i + 1])
                        zone_vals.append(seg_vals[i + 1])

                if cumulative_melt < max_fhrs and len(zone_times) >= 2:
                    zone_times.append(seg_times[-1])
                    zone_vals.append(seg_vals[-1])

                if len(zone_times) >= 2:
                    corn_zones.append((zone_times, zone_vals))

        for idx, (zone_t, zone_v) in enumerate(corn_zones):
            ax.fill_between(
                zone_t, zone_v, 32, color="green", alpha=0.3, zorder=2,
                label=f"Prime Corn Window ({min_fhrs:.0f}-{max_fhrs:.0f} F-hrs)" if idx == 0 else None,
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
        f"Corn Snow Forecast - Elev: {elevation_ft} ft | Snow Density: {snow_density:.2f}\n"
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

    d_max_corn = calculate_melt_depth(max_fhrs, K_M)
    d_poor_reset = calculate_freeze_depth(60, K_F)
    d_full_reset = calculate_freeze_depth(100, K_F)

    manual_content = (
        f"Effective Temperature Reference Manual (Universal Radiative Model)\n"
        f"----------------------------------------------------------------------------------------------------------------------\n"
        f"  Effective Temp = Wet Bulb + Shortwave Radiative Equiv (+T) + Longwave Radiative Equiv (-T)\n"
        f"  * NOTE: This model explicitly calculates slope/aspect. Thresholds below apply universally to ANY slope.\n"
        f"----------------------------------------------------------------------------------------------------------------------\n"
        f"[The Corn Cycle (Melt-Freeze)]  * Dynamically scaled for snow density {snow_density:.2f}\n"
        f" * Crust Break-through: Daily ETDH 40 ~ {min_fhrs:.0f} F-hrs. (DANGEROUS: Weak surface, 'breakable' crust, high ACL risk)\n"
        f" * PRIME CORN WINDOW: Daily ETDH {min_fhrs:.0f} ~ {max_fhrs:.0f} F-hrs. (Optimal melt depth up to {d_max_corn:.1f} cm)\n"
        f" * Sticky/Grabby (Overcooked): Daily ETDH {max_fhrs + 10:.0f} ~ {max_fhrs + 40:.0f} F-hrs. (Deep melt, suction effect, high drag)\n"
        f"----------------------------------------------------------------------------------------------------------------------\n"
        f"[Danger & Reset Protocol (Isothermal/Wet)]\n"
        f" * Overnight Reset Requirements (to clear heat debt & form crust):\n"
        f"    - Poor Reset (Supportable? No): Night EFDH < 60 F-hrs. (Thin crust < {d_poor_reset:.1f} cm, base remains unstable)\n"
        f"    - Full Reset (Structure Restored): Night EFDH > 100 F-hrs (Solid crust > {d_full_reset:.1f} cm).\n"
        f"    - Structural Check: Freeze Depth MUST exceed previous day's Melt Depth to prevent Breakable Crust.\n"
        f"    - Thermal Check: Night EFDH MUST be >= 0.7 * Previous Day ETDH to clear deep heat debt and prevent Wet Avalanches.\n"
        f"----------------------------------------------------------------------------------------------------------------------\n"
        f"Note: ETDH = Melt Integral (T_eff > 32 F)  |  EFDH = Freeze Integral (T_eff < 32 F, absolute value)\n"
    )

    fig.text(
        0.5, 0.01, manual_content, ha="center", va="bottom", fontsize=11,
        family="monospace", linespacing=1.6,
        bbox=dict(facecolor="ghostwhite", alpha=0.9, edgecolor="lightgray", boxstyle="round,pad=1"),
    )

    plt.savefig("corn_forecast_chart.png", dpi=150, bbox_inches="tight")
    print(f"Chart saved to: corn_forecast_chart.png")
    return fig


def run_corn_plot(json_path, start_days=None, end_days=None, slope_deg=0.0, aspect_deg=180.0, target_elevation_ft=None, snow_density=0.5):
    """Load weather data, compute effective temps, generate corn forecast chart and CSV."""
    elevation_ft, lat, lon, f_times, f_temps, f_rhs, adjusted_wbs, effective_temps = (
        prepare_effective_temp_data(json_path, start_days=start_days, end_days=end_days, slope_deg=slope_deg, aspect_deg=aspect_deg,
                                   target_elevation_ft=target_elevation_ft)
    )

    plot_corn_forecast(f_times, adjusted_wbs, effective_temps, elevation_ft, lat, lon,
                           slope_deg=slope_deg, aspect_deg=aspect_deg, snow_density=snow_density)
    export_forecast_csv(
        f_times, f_temps, f_rhs, adjusted_wbs, "corn_forecast_data.csv",
        effective_temps=effective_temps,
    )
