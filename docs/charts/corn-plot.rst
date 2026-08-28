``corn-plot``
=============

Purpose
-------

``corn-plot`` estimates the period when a previously refrozen spring surface
has softened enough to ski well but has not yet become deep, sticky slush.

Principle
---------

Like ``pow-plot``, this command integrates effective temperature above and
below 32 degrees Fahrenheit. It additionally converts each complete melt or
freeze integral into a depth estimate using density-dependent coefficients:

.. math::

   K_M = 2\rho + 0.1

.. math::

   K_F = 10\rho + 0.5

where :math:`\rho` is the ``--density`` value. Fahrenheit-hours are divided by
43.2 to obtain Celsius degree-days. Melt depth is linear in that value, while
freeze depth uses a square-root Stefan relationship.

Dynamic corn window
-------------------

The lower threshold represents the energy required to overcome overnight cold
content:

.. math::

   I_{start}(\rho) = 133.33\rho + 13.34

The upper threshold represents the modeled loss of structural integrity:

.. math::

   I_{end}(\rho) =
   \frac{(9.27\rho - 1.58)43.2}{2\rho + 0.1}

At density 0.35, the intended empirical range is approximately 60--90 F-hrs.
At the default density 0.50, it is approximately 80--120 F-hrs. The plot
interpolates the times when cumulative ETDH within each melt segment crosses
these thresholds and shades the interval green.

.. warning::

   The green band is calculated from daytime ETDH alone. The chart prints
   overnight-reset guidance, but the implementation does not suppress the
   green band after a poor reset. Confirm that a supportable crust exists before
   using the highlighted time.

Usage
-----

.. code-block:: console

   $ ullrs-secret corn-plot [OPTIONS] FILE

.. list-table::
   :header-rows: 1
   :widths: 24 20 56

   * - Option
     - Default
     - Meaning
   * - ``FILE``
     - required
     - Standard weather JSON produced by an importer
   * - ``--start FLOAT``
     - first sample
     - Start offset in days from the first observation
   * - ``--end FLOAT``
     - last sample
     - End offset in days from the first observation
   * - ``--slope FLOAT``
     - ``0.0``
     - Slope angle in degrees
   * - ``--aspect FLOAT``
     - ``180.0``
     - Aspect clockwise from north
   * - ``--elevation FLOAT``
     - source elevation
     - Target elevation in feet
   * - ``--density FLOAT``
     - ``0.5``
     - Estimated snow density in g/cm3-equivalent ratio
   * - ``--no-show``
     - off
     - Save without opening a Matplotlib window
   * - ``-o, --output TEXT``
     - ``corn_forecast_chart.png``
     - PNG output path

Example: a southeast spring line
--------------------------------

.. code-block:: console

   $ ullrs-secret corn-plot weather_data.json \
       --start 0 --end 4.5 \
       --slope 35 --aspect 135 --elevation 9000 \
       --density 0.45 \
       --no-show --output corn_se_9000.png

Density choice
--------------

Use 0.35 as a starting estimate for typical consolidated spring snow and 0.50
for dense high-alpine firn. Density affects both the corn thresholds and the
depth annotations. The CLI currently accepts any floating-point value without
validation, so physically implausible inputs can produce implausible windows.

Reading the chart
-----------------

The teal curve, 32-degree line, segment shading, and gray crossing lines have
the same meaning as in :doc:`pow-plot`. A green fill marks the modeled prime
corn interval. Segment labels also show melt or freeze depth in centimeters.

The reference text below the chart describes two overnight indicators: less
than 60 EFDH as a poor reset and more than 100 EFDH as a full reset. It also
recommends that freeze depth exceed the previous melt depth and that EFDH reach
at least 70 percent of the preceding ETDH. These are interpretation checks,
not gates in the green-band calculation.

Real-world integration example
------------------------------

Time and place
~~~~~~~~~~~~~~

The integration test combines a checked-in ERA5 grid record with a separate
terrain query. This distinction matters in the Teanaway, where elevation and
solar exposure change quickly over a short horizontal distance.

.. list-table::
   :header-rows: 1
   :widths: 24 76

   * - Field
     - Value
   * - Forecast shown
     - April 24, 2026 00:00 through April 26, 2026 23:00, UTC-07:00
       (Pacific Daylight Time)
   * - ERA5 fixture grid
     - 47.50000, -121.00000 at 4,130.4 feet
   * - Target terrain
     - `47.45686, -120.94978
       <https://www.openstreetmap.org/?mlat=47.45686&mlon=-120.94978#map=15/47.45686/-120.94978>`_
       at 6,273.0 feet; 33.5-degree slope; 143.2-degree aspect (southeast)
   * - Geographic setting
     - South side of the Fortune Peak--Ingalls area above the North Fork
       Teanaway River, near the Ingalls Way and Esmeralda Basin trail system in
       Kittitas County, Washington

The place name is inferred from the target coordinate and surrounding mapped
features; it is not embedded in the JSON. The southeast aspect makes this a
representative spring-touring example because it receives strong morning sun
and can move through refreeze, corn, and wet-snow conditions earlier than a
shaded aspect.

.. figure:: ../_generated/examples/integration-corn-forecast.png
   :alt: Corn forecast chart generated by the corn integration test.
   :width: 100%

   Output from ``integration_test/run_corn.py`` using the checked-in 72-hour
   ERA5 fixture and live terrain at 47.45686, -120.94978.

At the default 0.50 density, the green bands represent the current 80--120
F-hr corn window.

Mountaineering and ski context
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The `Lake Ingalls access description from Washington Trails Association
<https://www.wta.org/go-hiking/hikes/lake-ingalls>`_ identifies Ingalls Way
Trail 1390, the Esmeralda Basin trailhead, and the North Fork Teanaway approach.
The `Northwest Avalanche Center zone guide
<https://nwac.us/updated-mountain-weather-locations-names/>`_ includes the
Teanaway River drainage in its **East Central** zone.

Late-April road access and trail closures cannot be inferred from a weather
fixture. Check the `current Okanogan-Wenatchee National Forest alerts
<https://www.fs.usda.gov/r06/okanogan-wenatchee/alerts>`_ and the current NWAC
forecast before a trip. The green interval estimates surface softening; it
does not assess wet-loose avalanche timing, cornice exposure, route access, or
whether an overnight crust is actually supportable.
