Terrain and SNOTEL utilities
============================

Terrain lookup
--------------

The ``terrain`` command queries a 3 by 3 SRTM30M elevation grid from Open Topo
Data and applies Horn's method to estimate center elevation, slope, and downhill
aspect.

.. code-block:: console

   $ ullrs-secret terrain --lat 46.8523 --lon -121.7603
   Coordinates: 46.85230, -121.76030
   Elevation:   9167.0 ft (2794.1 m)
   Slope:       28°
   Aspect:      135° SE

.. code-block:: console

   $ ullrs-secret terrain --help

The 30 m grid smooths narrow couloirs, cliffs, gullies, and small rollovers.
Use it for an approximate chart input, then replace the values with a trusted
topographic measurement when available.

Find nearby SNOTEL stations
----------------------------

``snotel-list`` searches active USDA NRCS SNOTEL sites inside a two-degree
bounding box and returns the five nearest stations by great-circle distance.

.. code-block:: console

   $ ullrs-secret snotel-list --lat 48.4826 --lon -121.04877

The result includes station name, elevation, distance, compass direction, and
station triplet.

Read a SNOTEL station
----------------------

The current CLI command is named ``snotel``:

.. code-block:: console

   $ ullrs-secret snotel --site "606:WA:SNTL" \
       --start 2026-05-07 --end 2026-05-14 \
       --elevation 7000

``--site`` accepts a station triplet or an exact station name. The default time
range is the latest seven days. The command reports daily depth, SWE, bulk
density, 24-hour new snow, and new-snow density when consecutive data are
available.

AWDB values are received in inches. The display converts depth to centimeters
and water equivalent to millimeters.

Target-elevation inference
--------------------------

When ``--elevation`` is supplied, the command applies a simple depth multiplier
of 10 percent per 1,000 feet of elevation difference, floored at zero. This is
a rough heuristic. It does not model wind redistribution, orographic gradients,
rain shadows, or a snow-line transition.

Coverage and caching
--------------------

SNOTEL coverage is concentrated in the western United States and Alaska. The
station and metadata lookups are cached in memory; daily data is cached for
1,800 seconds within one process.
