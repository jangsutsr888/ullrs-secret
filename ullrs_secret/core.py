import math
import pytz

from datetime import datetime
from scipy.optimize import fsolve


def saturation_vapor_pressure(t_celsius):
    """Saturation vapor pressure (hPa) via Magnus formula."""
    return 6.112 * math.exp((17.67 * t_celsius) / (t_celsius + 243.5))


def get_dew_point_from_rh(temp_f, rh):
    """Calculate dew point (F) from temperature (F) and relative humidity (%)."""
    if temp_f is None or rh is None:
        return None
    t_c = (temp_f - 32) * 5.0 / 9.0
    es = 6.112 * math.exp((17.67 * t_c) / (t_c + 243.5))
    e = es * (rh / 100.0)
    if e <= 0:
        return None
    ln_e = math.log(e / 6.112)
    td_c = (243.5 * ln_e) / (17.67 - ln_e)
    return td_c * 9.0 / 5.0 + 32.0


def get_rh_from_dew_point(temp_f, dew_point_f):
    """Calculate relative humidity (%) from temperature (F) and dew point (F)."""
    if temp_f is None or dew_point_f is None:
        return None
    t_c = (temp_f - 32) * 5.0 / 9.0
    td_c = (dew_point_f - 32) * 5.0 / 9.0
    es = 6.112 * math.exp((17.67 * t_c) / (t_c + 243.5))
    e = 6.112 * math.exp((17.67 * td_c) / (td_c + 243.5))
    rh = (e / es) * 100.0
    return max(0.0, min(100.0, rh))


def psychrometric_equation(tw_c, t_c, e, p_hpa):
    """Psychrometric equation for fsolve root-finding."""
    A = 6.66e-4
    return (
        saturation_vapor_pressure(tw_c)
        - p_hpa * A * (1 + 0.00115 * tw_c) * (t_c - tw_c)
        - e
    )


def pressure_at_elevation(elevation_ft):
    """Standard atmospheric pressure (hPa) at a given elevation in feet."""
    elevation_m = elevation_ft * 0.3048
    return 1013.25 * (1 - 2.25577e-5 * elevation_m) ** 5.25588


def wet_bulb_f(t_celsius, rh_pct, p_hpa):
    """Compute wet bulb temperature in Fahrenheit.

    Returns None if solver fails.
    """
    e_actual = saturation_vapor_pressure(t_celsius) * (rh_pct / 100.0)
    try:
        tw_c = fsolve(psychrometric_equation, t_celsius, args=(t_celsius, e_actual, p_hpa))[0]
        return tw_c * 9.0 / 5.0 + 32
    except Exception:
        return None


def estimate_solar_position(lat, lon, dt_aware):
    """
    Estimate solar elevation and azimuth angles (in degrees) for a given datetime.
    Azimuth is measured clockwise from North (0° = North, 90° = East, 180° = South, 270° = West).
    """
    dt_utc = dt_aware.astimezone(pytz.utc)
    day_of_year = dt_utc.timetuple().tm_yday
    hour_utc = dt_utc.hour + dt_utc.minute / 60.0 + dt_utc.second / 3600.0

    b = (2 * math.pi / 365.0) * (day_of_year - 81)
    declination_rad = math.radians(23.45 * math.sin(b))
    lat_rad = math.radians(lat)

    eot = 9.87 * math.sin(2 * b) - 7.53 * math.cos(b) - 1.5 * math.sin(b)
    local_solar_time = (hour_utc + lon / 15.0 + eot / 60.0) % 24
    hour_angle_rad = math.radians(15.0 * (local_solar_time - 12.0))

    # Calculate solar elevation
    sin_elevation = (math.sin(lat_rad) * math.sin(declination_rad) +
                     math.cos(lat_rad) * math.cos(declination_rad) * math.cos(hour_angle_rad))
    elevation_rad = math.asin(sin_elevation)
    elevation_deg = math.degrees(elevation_rad)

    # Calculate solar azimuth
    if math.cos(elevation_rad) == 0:
        azimuth_deg = 180.0
    else:
        cos_azimuth = (math.sin(declination_rad) - sin_elevation * math.sin(lat_rad)) / (math.cos(elevation_rad) * math.cos(lat_rad))
        # Clamp to avoid floating point errors out of arccos domain [-1, 1]
        cos_azimuth = max(-1.0, min(1.0, cos_azimuth))
        azimuth_rad = math.acos(cos_azimuth)
        azimuth_deg = math.degrees(azimuth_rad)

        # If it's afternoon (hour angle > 0), azimuth is in the western hemisphere (180-360)
        if math.degrees(hour_angle_rad) > 0:
            azimuth_deg = 360.0 - azimuth_deg

    return elevation_deg, azimuth_deg


def calculate_radiative_equivalent_temps(t_air_f, t_dew_f, cloud_pct, lat, lon, dt_aware, 
                                         albedo=0.7, slope_deg=0.0, aspect_deg=180.0):
    """
    Calculate Shortwave and Longwave equivalent temperature shifts considering complex terrain.
    
    Args:
        slope_deg (float): Slope angle in degrees (0 = flat).
        aspect_deg (float): Slope aspect in degrees (0 = North, 90 = East, 180 = South).
    """
    K_rad = 8.0  
    cloud_frac = cloud_pct / 100.0

    slope_rad = math.radians(slope_deg)
    aspect_rad = math.radians(aspect_deg)

    # Get Sun Position
    solar_elevation, solar_azimuth = estimate_solar_position(lat, lon, dt_aware)
    elevation_rad = math.radians(solar_elevation)
    azimuth_rad = math.radians(solar_azimuth)

    # --- 1. Shortwave Equivalent (T_SW_eq) ---
    if solar_elevation > 0:
        # Calculate cosine of the angle of incidence on the sloped surface
        cos_theta_i = (math.cos(slope_rad) * math.sin(elevation_rad) +
                       math.sin(slope_rad) * math.cos(elevation_rad) * math.cos(azimuth_rad - aspect_rad))
        
        # If cos_theta_i is <= 0, the slope is in its own shadow (self-shading)
        if cos_theta_i > 0:
            sw_toa_slope = 1361.0 * cos_theta_i
            sw_net = sw_toa_slope * (1.0 - 0.65 * (cloud_frac ** 2)) * (1.0 - albedo)
        else:
            sw_net = 0.0  # Ignoring minor diffuse radiation for simplicity in self-shadow
    else:
        sw_net = 0.0
        
    t_sw_eq = sw_net / K_rad

    # --- 2. Longwave Equivalent (T_LW_eq) ---
    t_air_k = (t_air_f - 32) * 5.0 / 9.0 + 273.15
    t_dew_c = (t_dew_f - 32) * 5.0 / 9.0
    t_snow_k = 273.15  

    e_a = saturation_vapor_pressure(t_dew_c)
    epsilon_clear = 0.51 + 0.066 * math.sqrt(e_a)
    epsilon_atm = (1.0 - cloud_frac) * epsilon_clear + cloud_frac

    # Terrain View Corrections
    svf = math.cos(slope_rad / 2.0) ** 2  # Sky View Factor
    epsilon_terrain = 0.98  # Typical emissivity for rocks/trees
    
    # Total incoming longwave = (Sky contribution) + (Terrain contribution)
    # We assume surrounding terrain is roughly at air temperature
    lw_in_total = (svf * epsilon_atm * (t_air_k ** 4)) + ((1.0 - svf) * epsilon_terrain * (t_air_k ** 4))

    sigma = 5.67e-8
    lw_net = sigma * (lw_in_total - (t_snow_k ** 4))

    t_lw_eq = lw_net / K_rad

    return t_sw_eq, t_lw_eq


def effective_temperature_f(t_wet_f, t_air_f, t_dew_f, cloud_pct, lat, lon, dt_aware, 
                            albedo=0.7, slope_deg=0.0, aspect_deg=180.0):
    """
    Computes the Total Effective Temperature combining wet-bulb and radiative effects.
    Defaults to flat terrain (slope_deg=0.0).
    """
    if t_wet_f is None:
        return None

    t_sw_eq, t_lw_eq = calculate_radiative_equivalent_temps(
        t_air_f, t_dew_f, cloud_pct, lat, lon, dt_aware, 
        albedo, slope_deg, aspect_deg
    )

    return t_wet_f + t_sw_eq + t_lw_eq

def calculate_snow_density(swe_mm, h0_snow_cm):
    """Calculate realistic snow density from SWE and physical depth."""
    if h0_snow_cm <= 0:
        return 0.05
    real_density = (swe_mm / 10.0) / h0_snow_cm
    return max(0.05, min(0.60, real_density))

def get_consolidation_coefficients(real_density):
    """Return dynamic percolation (K_M) and freeze conductivity (K_F) coefficients based on density."""
    K_M = (real_density * 2.0) + 0.1
    K_F = (real_density * 10.0) + 0.5
    return K_M, K_F

def fhrs_to_c_days(fhrs):
    """Convert degree-hours Fahrenheit to degree-days Celsius."""
    return fhrs / (1.8 * 24.0)

def calculate_melt_depth(im_fhrs, K_M):
    """Calculate physical melt depth (cm) from melt integral (F-hrs)."""
    return K_M * fhrs_to_c_days(im_fhrs)

def calculate_freeze_depth(if_fhrs, K_F):
    """Calculate physical freeze depth (cm) from freeze integral (F-hrs)."""
    if if_fhrs <= 0:
        return 0.0
    return K_F * math.sqrt(fhrs_to_c_days(if_fhrs))

def calculate_dynamic_corn_window(real_density):
    """Calculate dynamic corn window thresholds based on snow density.
    
    Args:
        real_density (float): Estimated physical snow density (e.g., 0.35 for typical spring snow, 0.50 for firn).
        
    Returns:
        tuple: (min_fhrs, max_fhrs) representing the dynamic corn window thresholds.
    """
    # Start: Energy required to overcome cold content (EFDH) and albedo.
    min_fhrs = 133.33 * real_density + 13.34
    
    # End: Energy capacity before structural collapse. 
    # Based on max allowable melt depth D_max(rho) = 9.27 * rho - 1.58
    # and melt coefficient K_M(rho) = 2.0 * rho + 0.1
    # Max F-hrs = D_max * 43.2 / K_M
    d_max = 9.27 * real_density - 1.58
    k_m = (real_density * 2.0) + 0.1
    max_fhrs = (d_max * 43.2) / k_m if k_m > 0 else 90.0
    
    return min_fhrs, max_fhrs
