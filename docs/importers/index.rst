Weather importers
=================

Importers isolate source-specific APIs from the chart engine. Every importer
returns a ``WeatherData`` object and the CLI serializes it to the standard JSON
contract described in :doc:`../reference/weather-format`.

Choosing a source
-----------------

.. list-table::
   :header-rows: 1
   :widths: 18 24 20 18 20

   * - Source
     - Data type
     - Coverage
     - Credentials
     - Typical use
   * - :doc:`Open-Meteo <openmeteo>`
     - Multi-model forecast
     - Global; model-dependent
     - None
     - Normal current forecasting
   * - :doc:`National Weather Service <nws>`
     - NWS digital forecast
     - United States
     - None
     - US forecast comparison
   * - :doc:`ERA5 reanalysis <era5>`
     - Reanalysis
     - Global
     - Copernicus CDS
     - Historical reconstruction

Common CLI behavior
-------------------

.. code-block:: console

   $ ullrs-secret import SOURCE [SOURCE OPTIONS] --output weather_data.json

The output defaults to ``weather_data.json``. Latitude is positive north and
negative south; longitude is positive east and negative west.

Network results are cached in memory. Open-Meteo and ERA5 use caches of up to
32 argument combinations; NWS uses up to 128 URLs. Cached responses expire
after 1,800 seconds. The cache disappears when the process exits, so separate
CLI invocations do not share it.

Grid points and elevation
-------------------------

Forecast products describe model grid points rather than exact mountain
coordinates. Each importer stores the resolved grid coordinates and source
elevation in the JSON output. Inspect the logged distance from the requested
location. A nearby grid point can still represent different exposure or
topography.

Use chart ``--elevation`` only to project from the stored source elevation to
your target line. See :doc:`../getting-started` for the lapse-rate behavior.

.. toctree::
   :maxdepth: 1

   openmeteo
   nws
   era5
