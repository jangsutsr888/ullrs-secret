Getting started
===============

Requirements
------------

Ullr's Secret requires Python 3.10 or newer. Follow the
:doc:`installation` runbook to create an isolated environment, install from
the public source repository, and verify the CLI. The project has been tested
primarily on Python 3.10.

The normal workflow
-------------------

The CLI is designed as a two-step pipeline:

1. Import hourly weather from NWS, Open-Meteo, or ERA5 into a standard JSON
   file.
2. Pass that JSON file to one of the three chart commands.

For a current forecast outside the United States, Open-Meteo is the simplest
starting point because it does not require credentials:

.. code-block:: console

   $ ullrs-secret import openmeteo \
       --lat 45.9765 --lon 7.6584 \
       --model ecmwf \
       --timezone Europe/Zurich \
       --output weather_data.json

Then choose a chart according to the decision you need to make:

.. list-table::
   :header-rows: 1
   :widths: 24 36 40

   * - Command
     - Question
     - Primary output
   * - :doc:`charts/pow-plot`
     - When does fresh powder degrade?
     - Effective-temperature curve with melt and freeze integrals
   * - :doc:`charts/corn-plot`
     - When does a supportable surface enter the corn window?
     - Density-dependent corn window and melt/freeze depth estimates
   * - :doc:`charts/consolidation-plot`
     - How do repeated cycles alter the snow structure?
     - Time-depth profile of dry snow, slush, and crust

Slope inputs
------------

``--slope`` is the slope angle in degrees. ``--aspect`` is clockwise from
north: north is 0, east is 90, south is 180, and west is 270. A flat baseline
uses slope 0; in that case aspect has no practical effect.

Use the actual line rather than a nearby weather-station aspect. Solar loading
can move a corn window by hours between east-, south-, and west-facing slopes.

Elevation adjustment
--------------------

``--elevation`` projects the imported series from its source elevation to a
target elevation. The implementation applies these lapse rates:

* air temperature: 3.56 degrees Fahrenheit per 1,000 feet;
* dew point: 1.0 degree Fahrenheit per 1,000 feet.

Relative humidity is recalculated from the adjusted temperature and dew point,
and pressure is recalculated at the target elevation before wet-bulb
temperature is solved. Do not pre-adjust the weather file and also pass
``--elevation``; that would apply an elevation correction twice.

Time windows and output
-----------------------

``--start`` and ``--end`` are offsets in days from the first observation. They
may be fractional. For example, ``--start 1.5 --end 4`` selects the period from
36 hours through 96 hours after the first observation.

All chart commands accept ``--no-show`` for non-interactive operation and
``--output`` for the PNG path. The current plotting code formats chart times in
US Pacific Time, even when an importer stores another time-zone offset.

.. code-block:: console

   $ ullrs-secret pow-plot weather_data.json \
       --start 0 --end 3 --slope 35 --aspect 0 \
       --no-show --output north_powder.png

Next steps
----------

Read :doc:`model` before interpreting the thermal integrals. Then use the
dedicated page for :doc:`charts/pow-plot`, :doc:`charts/corn-plot`, or
:doc:`charts/consolidation-plot`.
