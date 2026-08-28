Effective-temperature model
===========================

The chart commands share one preparation pipeline. Each hourly observation is
converted into a snow-surface effective temperature, then consecutive samples
are split into melt and freeze segments at 32 degrees Fahrenheit.

Wet-bulb temperature
--------------------

Air temperature alone does not describe evaporative cooling. The code first
calculates saturation vapor pressure with the Magnus formula:

.. math::

   e_s(T) = 6.112 \exp\left(\frac{17.67T}{T + 243.5}\right)

It then solves the psychrometric equation for wet-bulb temperature
:math:`T_w` at the pressure corresponding to the working elevation:

.. math::

   e_s(T_w) - P A (1 + 0.00115T_w)(T - T_w) - e = 0

where :math:`A = 6.66 \times 10^{-4}` and pressure is in hectopascals.

Pressure at elevation
---------------------

The standard-atmosphere approximation is:

.. math::

   P(h) = 1013.25(1 - 2.25577 \times 10^{-5}h)^{5.25588}

where :math:`h` is elevation in meters. Pressure matters because the same air
temperature and relative humidity produce a different wet-bulb temperature at
high elevation.

Shortwave radiation
-------------------

The model estimates solar elevation and azimuth from UTC time, latitude, and
longitude. It projects direct shortwave radiation onto the requested slope and
aspect:

.. math::

   \cos(\theta_i) = \cos(\beta)\sin(\alpha) +
   \sin(\beta)\cos(\alpha)\cos(\gamma_s-\gamma_a)

Here :math:`\beta` is slope, :math:`\alpha` is solar elevation,
:math:`\gamma_s` is solar azimuth, and :math:`\gamma_a` is slope aspect. A
negative projection is treated as self-shade. Cloud cover attenuates the
remaining radiation and snow albedo is fixed at 0.7 by the chart pipeline.

Longwave radiation
------------------

Atmospheric emissivity is estimated from dew-point vapor pressure and cloud
fraction. A sky-view factor adjusts how much of the hemisphere is sky versus
surrounding terrain. The snow surface is assumed to be at 273.15 kelvin and
surrounding terrain at air temperature.

The net shortwave and longwave fluxes are divided by the model's radiative heat
transfer coefficient, ``K_rad = 8.0``, to produce equivalent temperature
shifts.

Total effective temperature
---------------------------

The final value is:

.. math::

   T_{eff} = T_w + T_{SW,eq} + T_{LW,eq}

This is an empirical decision variable, not a direct probe measurement of snow
temperature. It is intended to put humidity and radiative loading onto one
hourly curve.

Thermal integrals
-----------------

The implementation linearly interpolates each crossing of 32 degrees
Fahrenheit. Within every all-melt or all-freeze segment, it integrates the
absolute distance from 32 with the trapezoidal rule:

.. math::

   I = \int |T_{eff} - 32|\,dt

The result is in Fahrenheit-hours.

* **ETDH** is the melt integral where :math:`T_{eff} > 32`.
* **EFDH** is the absolute freeze integral where :math:`T_{eff} < 32`.

Physical melt and freeze helpers convert Fahrenheit-hours to Celsius degree
days by dividing by 43.2. Melt depth is linear in the converted integral;
freeze depth follows a square-root Stefan relationship. The three chart pages
explain how their command interprets these values.
