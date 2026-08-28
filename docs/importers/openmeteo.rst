Open-Meteo
==========

Summary
-------

The Open-Meteo importer requests 240 hours of hourly forecast data and needs
no API key. It is the simplest default for current forecasts and offers a
choice of global and regional model families.

Usage
-----

.. code-block:: console

   $ ullrs-secret import openmeteo [OPTIONS]

.. list-table::
   :header-rows: 1
   :widths: 25 20 55

   * - Option
     - Default
     - Meaning
   * - ``--lat FLOAT``
     - required
     - Requested latitude
   * - ``--lon FLOAT``
     - required
     - Requested longitude
   * - ``--model CHOICE``
     - ``best_match``
     - ``best_match``, ``ecmwf``, ``gfs``, ``gem``, or ``hrrr``
   * - ``--timezone TEXT``
     - ``America/Los_Angeles``
     - IANA time-zone name used for stored timestamps
   * - ``-o, --output TEXT``
     - ``weather_data.json``
     - Output JSON path

.. code-block:: console

   $ ullrs-secret import openmeteo \
       --lat 45.9765 --lon 7.6584 \
       --model ecmwf --timezone Europe/Zurich \
       --output alps_weather.json

Model mapping
-------------

The friendly CLI values map to Open-Meteo API model identifiers as follows.

.. list-table::
   :header-rows: 1
   :widths: 30 40 30

   * - CLI value
     - API value
     - Scope
   * - ``best_match``
     - ``best_match``
     - Automatic model selection
   * - ``ecmwf``
     - ``ecmwf_ifs025``
     - ECMWF IFS global forecast
   * - ``gfs``
     - ``gfs_seamless``
     - NOAA GFS family
   * - ``gem``
     - ``gem_seamless``
     - Canadian GEM family
   * - ``hrrr``
     - ``gfs_hrrr``
     - NOAA HRRR, North America only

What the importer requests
--------------------------

The API is asked for hourly 2 m air temperature, relative humidity, 2 m dew
point, and total cloud cover. Temperature is requested in Fahrenheit. API
timestamps are requested in UTC and converted to ``--timezone`` before being
written.

The importer stores the coordinates resolved by Open-Meteo, which may differ
from the requested point. It also stores the elevation returned by Open-Meteo.
That elevation is the downscaling baseline for later ``--elevation``
adjustment; replacing it with a separate summit elevation would double-count
the correction.

Missing data and provenance
---------------------------

Rows with missing air temperature are skipped. Relative humidity is taken from
the API when available and otherwise derived from air temperature and dew
point. Dew point and cloud cover remain null if the API omits them.

The JSON ``source`` field includes the resolved API model identifier, for
example ``openmeteo_ecmwf_ifs025``.

Limitations
-----------

``best_match`` may change its model blend by location and forecast lead time.
Specific models have different grids and update schedules, and HRRR is not a
global option. The implementation requests a fixed 240-hour horizon even when
a model offers a shorter reliable range.
