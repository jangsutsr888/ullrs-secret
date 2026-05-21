"""
Read standard weather JSON, compute effective temperatures via .core,
calculate melt-freeze structural consolidation, and plot the D_total curve.
"""

import math

import matplotlib.dates as mdates
import matplotlib.pyplot as plt

import matplotlib.patches as patches
from ullrs_secret.core import calculate_snow_density, get_consolidation_coefficients, calculate_melt_depth, calculate_freeze_depth, calculate_percolation_factor
from ullrs_secret.plot_utils import (
    PT_ZONE,
    compute_segment_integral,
    export_forecast_csv,
    find_crossings_and_segments,
    prepare_effective_temp_data,
)


def consolidate_layers(snowpack):
    """Merges adjacent snow layers of the same type and computes weight-averaged density."""
    consolidated = []
    for layer in snowpack:
        if layer['thickness'] <= 0:
            continue
        if not consolidated:
            consolidated.append(layer)
        elif consolidated[-1]['type'] == layer['type']:
            last = consolidated[-1]
            total_thick = last['thickness'] + layer['thickness']
            if total_thick > 0:
                last['density'] = (last['density'] * last['thickness'] + layer['density'] * layer['thickness']) / total_thick
                last['thickness'] = total_thick
                last['is_settled'] = last.get('is_settled', False) and layer.get('is_settled', False)
        else:
            consolidated.append(layer)
    return consolidated


def apply_melt_phase(snowpack, current_Im):
    """
    Finite Element Melt Phase: Push melt integral (Im) down layer by layer.
    Melted layers convert to slush, generating Water Equivalent (W_eq) which percolates down.
    Returns the updated snowpack.
    """
    remaining_Im_c_days = current_Im / 43.2
    W_eq = 0.0
    
    new_snowpack = []
    for layer in snowpack:
        if remaining_Im_c_days > 0:
            layer_K_M = (layer['density'] * 2.0) + 0.1
            c_days_needed = layer['thickness'] / layer_K_M if layer_K_M > 0 else float('inf')
            
            if remaining_Im_c_days >= c_days_needed:
                # Melt entire layer
                melted_part = layer.copy()
                melted_part['type'] = 'slush'
                new_snowpack.append(melted_part)
                
                W_eq += layer['thickness'] * layer['density']
                remaining_Im_c_days -= c_days_needed
            else:
                # Melt partial layer
                D_melt = remaining_Im_c_days * layer_K_M
                melted_part = layer.copy()
                melted_part['thickness'] = D_melt
                melted_part['type'] = 'slush'
                new_snowpack.append(melted_part)
                
                W_eq += D_melt * layer['density']
                
                unmelted_part = layer.copy()
                unmelted_part['thickness'] = layer['thickness'] - D_melt
                
                # Process percolation for the unmelted part immediately
                if unmelted_part['type'] == 'slush':
                    # Zero resistance in slush, water passes through
                    new_snowpack.append(unmelted_part)
                else:
                    theta_r = max(0.02, 0.06 - (unmelted_part['density'] - 0.1) * 0.1)
                    D_wet = W_eq / theta_r if theta_r > 0 else 0
                    if D_wet >= unmelted_part['thickness']:
                        wetted = unmelted_part.copy()
                        wetted['type'] = 'slush'
                        new_snowpack.append(wetted)
                        W_eq -= unmelted_part['thickness'] * theta_r
                    else:
                        if D_wet > 0:
                            wetted = unmelted_part.copy()
                            wetted['thickness'] = D_wet
                            wetted['type'] = 'slush'
                            new_snowpack.append(wetted)
                            W_eq = 0
                        dry = unmelted_part.copy()
                        dry['thickness'] = unmelted_part['thickness'] - D_wet
                        new_snowpack.append(dry)
                        
                remaining_Im_c_days = 0
        else:
            # Below thermal melt zone, strictly percolation
            if W_eq > 0:
                if layer['type'] == 'slush':
                    new_snowpack.append(layer)
                else:
                    theta_r = max(0.02, 0.06 - (layer['density'] - 0.1) * 0.1)
                    D_wet = W_eq / theta_r if theta_r > 0 else 0
                    if D_wet >= layer['thickness']:
                        wetted = layer.copy()
                        wetted['type'] = 'slush'
                        new_snowpack.append(wetted)
                        W_eq -= layer['thickness'] * theta_r
                    else:
                        if D_wet > 0:
                            wetted = layer.copy()
                            wetted['thickness'] = D_wet
                            wetted['type'] = 'slush'
                            new_snowpack.append(wetted)
                            W_eq = 0
                        dry = layer.copy()
                        dry['thickness'] = layer['thickness'] - D_wet
                        new_snowpack.append(dry)
            else:
                new_snowpack.append(layer)

    # Apply Physical Settlement and Density Update to new Slush
    for layer in new_snowpack:
        if layer['type'] == 'slush' and not layer.get('is_settled', False):
            layer['thickness'] *= 0.8
            layer['density'] = max(0.45, layer['density'])
            layer['is_settled'] = True

    return consolidate_layers(new_snowpack)


def apply_freeze_phase(snowpack, current_If):
    """
    Finite Element Freeze Phase: Push freeze integral (If) down layer by layer
    using the non-linear Stefan equation.
    Returns the updated snowpack.
    """
    remaining_If_c_days = current_If / 43.2
    current_z = 0.0
    
    new_snowpack = []
    for layer in snowpack:
        if remaining_If_c_days > 0:
            layer_K_F = (layer['density'] * 10.0) + 0.5
            
            # Integral needed to push the freeze front entirely through this layer
            # Based on Stefan's D = K_F * sqrt(t), time = D^2 / K_F^2
            # So time_needed = ((z_top + thickness)^2 - z_top^2) / K_F^2
            c_days_needed = ((current_z + layer['thickness'])**2 - current_z**2) / (layer_K_F**2) if layer_K_F > 0 else float('inf')
            
            if remaining_If_c_days >= c_days_needed:
                # Freeze entire layer
                frozen_layer = layer.copy()
                if frozen_layer['type'] == 'slush':
                    frozen_layer['type'] = 'crust'
                    frozen_layer['density'] = frozen_layer['density'] + 0.5 * (0.55 - frozen_layer['density'])
                    frozen_layer['is_settled'] = False
                elif frozen_layer['type'] == 'crust':
                    frozen_layer['density'] = frozen_layer['density'] + 0.5 * (0.55 - frozen_layer['density'])
                new_snowpack.append(frozen_layer)
                
                remaining_If_c_days -= c_days_needed
                current_z += layer['thickness']
            else:
                # Freeze partial layer using non-linear math
                # (z_top + h_partial)^2 = remaining_If * K_F^2 + z_top^2
                h_partial = math.sqrt(remaining_If_c_days * (layer_K_F**2) + current_z**2) - current_z
                
                frozen_part = layer.copy()
                frozen_part['thickness'] = h_partial
                if frozen_part['type'] == 'slush':
                    frozen_part['type'] = 'crust'
                    frozen_part['density'] = frozen_part['density'] + 0.5 * (0.55 - frozen_part['density'])
                    frozen_part['is_settled'] = False
                elif frozen_part['type'] == 'crust':
                    frozen_part['density'] = frozen_part['density'] + 0.5 * (0.55 - frozen_part['density'])
                new_snowpack.append(frozen_part)
                
                unfrozen_part = layer.copy()
                unfrozen_part['thickness'] = layer['thickness'] - h_partial
                new_snowpack.append(unfrozen_part)
                
                remaining_If_c_days = 0
                current_z += layer['thickness'] # End of thermal zone
        else:
            new_snowpack.append(layer)
            current_z += layer['thickness']

    return consolidate_layers(new_snowpack)


def plot_d_total_curve(times, effective_temps, elevation_ft, swe_mm=30.0, h0_snow_cm=20.0, slope_deg=0.0, aspect_deg=180.0, snow_density=None, lat=None, lon=None):
    """
    Generate a focused chart showing the multi-layer snowpack profile progression.
    Visualizes Crust, Slush, and Dry Snow layers over time in a stacked rectangle format.
    """
    
    fig, ax = plt.subplots(figsize=(20, 10))

    valid_data = [(t, e) for t, e in zip(times, effective_temps) if e is not None]

    if not valid_data:
        print("No valid data to plot.")
        return fig

    v_times = [d[0] for d in valid_data]
    v_effs = [d[1] for d in valid_data]

    # --- 1. Identify Crossings and Segments ---
    segments, crossing_times = find_crossings_and_segments(v_times, v_effs)

    # --- 2. Calculate Integrals & Dynamic Multi-Layer Model ---

    if snow_density is not None:
        real_density = max(0.05, min(0.60, snow_density))
        swe_mm = real_density * h0_snow_cm * 10.0
    else:
        real_density = calculate_snow_density(swe_mm, h0_snow_cm)

    K_M, K_F = get_consolidation_coefficients(real_density)
    percolation_factor = calculate_percolation_factor(real_density)

    # Initialize Snowpack Layers. Depth is relative to surface (0).
    # A layer is a dict tracking its physical properties over time.
    snowpack = [{'type': 'dry', 'thickness': float(h0_snow_cm), 'density': real_density, 'is_settled': False}]
    
    current_Im = 0.0
    current_If = 0.0

    # Store profile snapshots for plotting
    # Form: [(start_time, end_time, [layers]), ...]
    profile_history = []

    for i, seg in enumerate(segments):
        if len(seg) < 2:
            continue
        seg_times = [p[0] for p in seg]
        seg_effs = [p[1] for p in seg]

        integral = compute_segment_integral(seg_times, seg_effs)
        mid_idx = len(seg) // 2
        is_melt = seg_effs[mid_idx] > 32.0

        if is_melt:
            current_Im += integral
        else:
            current_If += integral

        if is_melt:
            snowpack = apply_melt_phase(snowpack, current_Im)
            current_Im = 0.0 # Reset melt after applying
        else: # Freeze phase
            snowpack = apply_freeze_phase(snowpack, current_If)
            current_If = 0.0 # Reset freeze after applying
            
        # Record profile for this segment
        current_top = 0.0
        plot_layers = []
        for layer in snowpack:
            bottom = current_top + layer['thickness']
            plot_layers.append({
                'type': layer['type'],
                'top': current_top,
                'bottom': bottom
            })
            current_top = bottom
            
        profile_history.append((seg_times[0], seg_times[-1], plot_layers))

    # --- 3. Plotting the Multi-Layer Profile ---
    # Depth is on Y axis (0 at top, h0_snow_cm at bottom), Time on X axis
    
    # Define colors
    COLORS = {
        'crust': 'purple',        # Solid, supportive
        'slush': 'deepskyblue',   # Wet, unsupportive
        'dry': 'whitesmoke'       # Original dry snow
    }
    
    for start_t, end_t, layers in profile_history:
        # Convert times to matplotlib date format
        start_md = mdates.date2num(start_t)
        end_md = mdates.date2num(end_t)
        width = end_md - start_md
        
        for layer in layers:
            height = layer['bottom'] - layer['top']
            # Draw rectangle: (x, y_bottom), width, height. Note y is inverted later, so plot normally
            rect = patches.Rectangle(
                (start_md, layer['top']), width, height,
                linewidth=0.5, edgecolor='black', facecolor=COLORS[layer['type']], alpha=0.8
            )
            ax.add_patch(rect)

    # Invert Y axis so 0 (surface) is at the top
    ax.invert_yaxis()
    
    # Draw vertical lines for phase transitions (Melt / Freeze)
    for seg in segments:
        if len(seg) > 0:
            ct = mdates.date2num(seg[0][0])
            ax.axvline(x=ct, color="gray", linestyle="-.", alpha=0.5, linewidth=1.5, zorder=2)
    
    # Support Threshold Line (15cm from surface)
    support_threshold = min(h0_snow_cm, 15.0)
    ax.axhline(y=support_threshold, color="crimson", linestyle="--", linewidth=2.5,
                label=f"Support Threshold ({support_threshold} cm)", zorder=6)

    # Legend patches
    legend_elements = [
        patches.Patch(facecolor=COLORS['crust'], edgecolor='black', label='Crust (Supportive Base)'),
        patches.Patch(facecolor=COLORS['slush'], edgecolor='black', label='Slush (Wet, Unsupportive)'),
        patches.Patch(facecolor=COLORS['dry'], edgecolor='black', label='Dry Snow (Original)')
    ]
    ax.legend(handles=legend_elements, loc="upper left", bbox_to_anchor=(1.02, 1), fontsize=13, framealpha=0.9, shadow=True)

    # --- 4. Formatting & Layout ---
    ASPECT_LABELS = {0: "N", 45: "NE", 90: "E", 135: "SE", 180: "S", 225: "SW", 270: "W", 315: "NW", 360: "N"}
    closest_cardinal = min(ASPECT_LABELS, key=lambda k: abs(k - aspect_deg % 360))
    aspect_label = ASPECT_LABELS[closest_cardinal]

    lat_str = f"{abs(lat):.4f}°{'N' if lat >= 0 else 'S'}" if lat is not None else "N/A"
    lon_str = f"{abs(lon):.4f}°{'W' if lon < 0 else 'E'}" if lon is not None else "N/A"

    ax.set_title(
        f"Corn Base Consolidation - Elev: {elevation_ft} ft | Initial Snow Density: {real_density*100:.0f}%\n"
        f"Location: {lat_str}, {lon_str} | Slope: {slope_deg:.0f}° {aspect_label} aspect | Timezone: US Pacific Time (PT)\n"
        f"SWE: {swe_mm} mm | Initial Depth: {h0_snow_cm} cm",
        fontsize=18, fontweight="bold", pad=15
    )

    ax.set_ylabel("Depth from Surface (cm)", fontsize=14)
    ax.set_xlabel("Time (Pacific Time)", fontsize=14)

    ax.xaxis.set_major_locator(mdates.HourLocator(interval=6, tz=PT_ZONE))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%d %H:00", tz=PT_ZONE))

    ax.set_ylim(bottom=h0_snow_cm, top=0) # Double check inversion, bottom is ground, top is surface
    ax.set_xlim(left=v_times[0], right=v_times[-1])
    
    # Ensure y-ticks make sense
    ax.yaxis.set_major_locator(plt.MaxNLocator(integer=True))

    plt.setp(ax.get_xticklabels(), rotation=45, ha="right", fontsize=12)
    
    # Use tight_layout with a rect to leave room for the bottom text
    # rect=[left, bottom, right, top]. Increase bottom to push the chart up.
    plt.tight_layout(rect=[0, 0.35, 1, 1])

    # --- 5. Appended Mechanism Manual ---
    manual_content = (
        "Multi-Layer Snowpack Profile [Thermodynamic Consolidation Engine]\n"
        "----------------------------------------------------------------------------------------------------------------------\n"
        f" * Dynamic Physics: The top surface layer dynamically dictates thermodynamic rates (K_M & K_F).\n"
        f" * Zero-Resistance Percolation: Meltwater instantly passes through slush layers without losing mass.\n"
        f" * Settlement: Snow converted to slush compacts by 20%, resulting in overall snowpack depth reduction.\n"
        " * The chart displays a vertical slice of the snowpack over time, tracking distinct physical layers.\n"
        "----------------------------------------------------------------------------------------------------------------------\n"
        " Layer Guide & Decision Matrix: \n"
        " - CRUST (Purple): Refrozen, consolidated ice lattice. Provides structural support. Density increases with cycles.\n"
        " - SLUSH (Blue): Unfrozen, water-saturated snow. Exhibits zero support and acts as a dangerous weak layer.\n"
        " - DRY SNOW (White): Unaffected original snow.\n"
        " - CAUTION: A continuous Crust layer MUST exceed the 15cm threshold line to safely support a skier.\n"
        "   If Crust < 15cm and overlies Slush (a 'Crust-over-slush' structure), expect sudden breakthrough and high danger."
    )

    fig.text(
        0.5, 0.02, manual_content, ha="center", va="bottom", fontsize=12,
        family="monospace", linespacing=1.6,
        bbox=dict(facecolor="ghostwhite", alpha=0.9, edgecolor="lightgray", boxstyle="round,pad=1"),
    )

    plt.savefig("d_total_curve.png", dpi=150, bbox_inches="tight")
    print(f"Chart saved to: d_total_curve.png")
    return fig


def run_consolidation_model(json_path, start_days=None, end_days=None, swe_mm=30.0, h0_snow_cm=20.0, slope_deg=0.0, aspect_deg=180.0, target_elevation_ft=None, snow_density=None):
    """Load weather data, compute effective temps via .core, generate D_total chart and CSV."""
    elevation_ft, lat, lon, f_times, f_temps, f_rhs, adjusted_wbs, effective_temps = prepare_effective_temp_data(
        json_path, start_days, end_days, slope_deg=slope_deg, aspect_deg=aspect_deg, target_elevation_ft=target_elevation_ft
    )

    plot_d_total_curve(f_times, effective_temps, elevation_ft, swe_mm=swe_mm, h0_snow_cm=h0_snow_cm, slope_deg=slope_deg, aspect_deg=aspect_deg, snow_density=snow_density, lat=lat, lon=lon)
    export_forecast_csv(f_times, f_temps, f_rhs, adjusted_wbs, "consolidation_forecast_data.csv", effective_temps=effective_temps)
