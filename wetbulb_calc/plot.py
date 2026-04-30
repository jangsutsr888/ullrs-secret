"""Read standard weather JSON, compute wet bulb temperatures, plot and export."""

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pytz

from .plot_utils import (
    PT_ZONE,
    compute_segment_integral,
    export_forecast_csv,
    find_crossings_and_segments,
    prepare_forecast_data,
)


def plot_forecast(times, temps_f, adjusted_wbs, elevation_ft, days):
    """Generate the forecast chart with melt/freeze integral annotations."""
    fig, ax = plt.subplots(figsize=(20, 7))

    valid_data = [(t, w) for t, w in zip(times, adjusted_wbs) if w is not None]

    if valid_data:
        v_times = [d[0] for d in valid_data]
        v_wbs = [d[1] for d in valid_data]

        segments, crossing_times = find_crossings_and_segments(v_times, v_wbs)

        trans = ax.get_xaxis_transform()

        for seg in segments:
            if len(seg) < 2:
                continue
            seg_times = [p[0] for p in seg]
            seg_wbs = [p[1] for p in seg]

            integral = compute_segment_integral(seg_times, seg_wbs)

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

    ax.xaxis.set_major_locator(mdates.HourLocator(interval=6, tz=PT_ZONE))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%d %H:00", tz=PT_ZONE))
    ax.xaxis.set_minor_locator(mdates.HourLocator(interval=1, tz=PT_ZONE))
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
    print(f"Chart saved to: forecast_chart.png")
    return fig


def run_plot(json_path, days=3.0):
    """Load weather data, compute wet bulb temps, generate chart and CSV."""
    elevation_ft, f_times, f_temps, f_rhs, adjusted_wbs = prepare_forecast_data(json_path, days)

    plot_forecast(f_times, f_temps, adjusted_wbs, elevation_ft, days)
    export_forecast_csv(f_times, f_temps, f_rhs, adjusted_wbs, "forecast_data.csv")
