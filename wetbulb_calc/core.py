import math

from scipy.optimize import fsolve


def saturation_vapor_pressure(t_celsius):
    """Saturation vapor pressure (hPa) via Magnus formula."""
    return 6.112 * math.exp((17.67 * t_celsius) / (t_celsius + 243.5))


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
