Python API
==========

The package exports its main calculation, importer, utility, and plotting
functions from ``ullrs_secret``.

End-to-end example
------------------

.. code-block:: python

   import ullrs_secret as ullrs


   weather = ullrs.fetch_weather(
       "openmeteo",
       lat=46.8523,
       lon=-121.7603,
       model="best_match",
       timezone="America/Los_Angeles",
   )

   elevation, lat, lon, times, effective = ullrs.prepare_effective_temp_data(
       weather_data=weather,
       slope_deg=35.0,
       aspect_deg=135.0,
       target_elevation_ft=9000.0,
   )

   figure = ullrs.plot_corn_forecast(
       times=times,
       effective_temps=effective,
       elevation_ft=elevation,
       lat=lat,
       lon=lon,
       slope_deg=35.0,
       aspect_deg=135.0,
       snow_density=0.45,
   )
   figure.savefig("custom_corn.png", dpi=150, bbox_inches="tight")

Core calculations
-----------------

``wet_bulb_f(t_celsius, rh_pct, p_hpa)``
   Solve wet-bulb temperature and return Fahrenheit, or ``None`` on solver
   failure.

``calculate_radiative_equivalent_temps(...)``
   Return shortwave and longwave equivalent temperature shifts.

``effective_temperature_f(...)``
   Combine wet bulb with the two radiative shifts.

``calculate_snow_density(swe_mm, h0_snow_cm)``
   Derive density and clamp it to 0.05--0.60.

``calculate_dynamic_corn_window(real_density)``
   Return the lower and upper ETDH thresholds for a density.

Import and preparation
----------------------

``fetch_weather(source, **kwargs)``
   Call a registered importer and return ``WeatherData``.

``get_importer(name)`` and ``list_importers()``
   Inspect the importer registry.

``prepare_effective_temp_data(...)``
   Filter a date-offset window, optionally adjust elevation, calculate wet-bulb
   temperature, and return ``(elevation, latitude, longitude, times,
   effective_temperatures)``.

Plotting
--------

``plot_pow_forecast(...)``
   Return a Matplotlib figure for powder preservation.

``plot_corn_forecast(...)``
   Return a Matplotlib figure for the density-dependent corn window.

``plot_d_total_curve(...)``
   Return a Matplotlib figure for the multi-layer consolidation profile.

Terrain and snow data
---------------------

``get_terrain_data(lat, lon)``
   Return elevation, slope, and aspect from Open Topo Data.

``find_nearest_snotel_stations(lat, lon, count=5)``
   Return nearby SNOTEL metadata sorted by distance.

``get_snotel_report(site, target_elev_ft=None, start_date=None, end_date=None)``
   Return station metadata and daily SNWD/WTEQ records.

Data classes
------------

The serialized boundary is implemented by
``ullrs_secret.models.WeatherData`` and ``Observation``. See
:doc:`weather-format` for required fields and null behavior.
