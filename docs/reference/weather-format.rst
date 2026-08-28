Standard weather JSON
=====================

The standard JSON file is the contract between importers and the calculation
pipeline. Keeping this boundary stable allows a new data source to feed every
chart command without changing the physics code.

Example
-------

.. code-block:: json

   {
     "source": "nws",
     "latitude": 45.3668,
     "longitude": -121.6867,
     "elevation_ft": 9167.0,
     "observations": [
       {
         "time_iso": "2026-04-29T21:00:00-07:00",
         "air_temp_f": 26.0,
         "relative_humidity_pct": 54.0,
         "dew_point_f": 12.0,
         "cloud_cover_pct": 40.0
       }
     ]
   }

Top-level fields
----------------

.. list-table::
   :header-rows: 1
   :widths: 27 18 55

   * - Field
     - Type
     - Meaning
   * - ``source``
     - string
     - Provenance label; defaults to ``unknown`` when read
   * - ``latitude``
     - number
     - Resolved grid latitude; required by ``WeatherData.from_dict``
   * - ``longitude``
     - number
     - Resolved grid longitude; required by ``WeatherData.from_dict``
   * - ``elevation_ft``
     - number
     - Source elevation in feet; defaults to 0 when read
   * - ``observations``
     - array
     - Chronological hourly observations; defaults to an empty array

Observation fields
------------------

.. list-table::
   :header-rows: 1
   :widths: 32 18 50

   * - Field
     - Type
     - Meaning
   * - ``time_iso``
     - string
     - ISO 8601 timestamp; required and expected to include an offset
   * - ``air_temp_f``
     - number
     - Air temperature in Fahrenheit; required by the dataclass
   * - ``relative_humidity_pct``
     - number or null
     - Relative humidity from 0 to 100
   * - ``dew_point_f``
     - number or null
     - Dew point in Fahrenheit
   * - ``cloud_cover_pct``
     - number or null
     - Total cloud cover from 0 to 100

Practical completeness requirements
-----------------------------------

The dataclass permits null humidity, dew point, and cloud cover. The current
chart pipeline is stricter in practice:

* wet-bulb temperature requires air temperature and relative humidity;
* effective temperature requires wet bulb, air temperature, dew point, and
  cloud cover;
* a missing dew point is synthesized from humidity only while applying an
  elevation adjustment;
* there is no fallback for missing cloud cover.

Therefore, a robust custom importer should provide all five observation fields
for every row. Otherwise the corresponding effective-temperature value may be
``None`` and will be omitted from chart integration.

Time behavior
-------------

``Observation.time`` parses the ISO timestamp and converts it to
``America/Los_Angeles``. The chart axes also use that zone. Store valid,
offset-aware timestamps even if the source is elsewhere; do not write naive
local times.

Adding an importer
------------------

An importer is a registered function that returns ``WeatherData``. Define its
Click decorators, register the function, and import the module from
``ullrs_secret.importers.__init__``.

.. code-block:: python

   import click

   from ullrs_secret.importers import register
   from ullrs_secret.models import Observation, WeatherData


   EXAMPLE_DECORATORS = [
       click.option("--lat", type=float, required=True),
       click.option("--lon", type=float, required=True),
   ]


   @register("example", decorators=EXAMPLE_DECORATORS)
   def fetch(lat, lon):
       return WeatherData(
           source="example",
           latitude=lat,
           longitude=lon,
           elevation_ft=5000.0,
           observations=[
               Observation(
                   time_iso="2026-01-01T12:00:00-08:00",
                   air_temp_f=28.0,
                   relative_humidity_pct=70.0,
                   dew_point_f=20.0,
                   cloud_cover_pct=25.0,
               )
           ],
       )

After the module is imported during package initialization, the CLI constructs
``ullrs-secret import example`` automatically.
