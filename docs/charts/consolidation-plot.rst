``consolidation-plot``
========================

Purpose
-------

``consolidation-plot`` models how a new snow layer changes through repeated
melt-freeze cycles. Instead of drawing only a temperature curve, it draws a
vertical time-depth profile of dry snow, slush, and refrozen crust.

Principle
---------

The initial layer has physical depth ``--depth`` and either:

* density derived from ``SWE / (10 * depth)``; or
* density supplied directly with ``--density``.

Derived and supplied density are clamped to the range 0.05--0.60. When density
is supplied, the command recalculates SWE from density and depth for display.

Melt phase
~~~~~~~~~~

Melt ETDH is converted to Celsius degree-days. Energy is applied from the
surface downward, with a per-layer melt coefficient of ``2 * density + 0.1``.
Melted material becomes slush and its water equivalent percolates into deeper
non-slush layers. Existing slush presents zero additional holding resistance.

A newly created slush layer settles once: its thickness is multiplied by 0.8
and its density is raised to at least 0.45. Adjacent layers of the same type are
then merged with thickness-weighted density.

Freeze phase
~~~~~~~~~~~~

Freeze EFDH is also converted to Celsius degree-days. The freeze front advances
from the surface with a Stefan square-root relationship and a per-layer
coefficient of ``10 * density + 0.5``. Frozen slush becomes crust. Each freeze
cycle moves crust density halfway toward 0.55, modeling asymptotic
consolidation.

Usage
-----

.. code-block:: console

   $ ullrs-secret consolidation-plot [OPTIONS] FILE

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
   * - ``--swe FLOAT``
     - ``30.0``
     - Initial snow water equivalent in millimeters
   * - ``--depth FLOAT``
     - ``20.0``
     - Initial physical depth in centimeters
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
     - derived
     - Override density; this takes precedence over ``--swe``
   * - ``--no-show``
     - off
     - Save without opening a Matplotlib window
   * - ``-o, --output TEXT``
     - ``d_total_curve.png``
     - PNG output path

Example: track a 25 cm storm layer
-----------------------------------

.. code-block:: console

   $ ullrs-secret consolidation-plot weather_data.json \
       --start 0 --end 4.5 \
       --swe 40 --depth 25 \
       --slope 30 --aspect 180 --elevation 8500 \
       --no-show --output storm_layer_profile.png

If a field density estimate is more reliable than SWE, use it instead:

.. code-block:: console

   $ ullrs-secret consolidation-plot weather_data.json \
       --depth 25 --density 0.22 \
       --no-show --output density_override_profile.png

Reading the chart
-----------------

White
   Original dry snow that has not been wetted.

Blue
   Wet, settled slush with poor structural support.

Purple
   Refrozen crust.

Red dashed depth line
   The model's 15 cm support threshold, or the full initial depth when the
   layer is shallower than 15 cm.

The most concerning modeled pattern is a thin purple crust above a substantial
blue slush layer. The chart calls this a crust-over-slush structure. The 15 cm
line is a heuristic in this model, not a field stability test or a universal
skier-support threshold.

Real-world integration example
------------------------------

Time and place
~~~~~~~~~~~~~~

The JSON records the ERA5 grid cell used for weather. The integration test
then applies that weather to a higher target on Mount Rainier. Keeping those
locations separate makes the large elevation adjustment visible.

.. list-table::
   :header-rows: 1
   :widths: 24 76

   * - Field
     - Value
   * - Forecast shown
     - April 4, 2025 00:00 through April 8, 2025 23:00, UTC-07:00
       (Pacific Daylight Time)
   * - ERA5 fixture grid
     - 46.75000, -121.75000 at 3,968.1 feet
   * - Target terrain
     - `46.82629, -121.72638
       <https://www.openstreetmap.org/?mlat=46.82629&mlon=-121.72638#map=15/46.82629/-121.72638>`_
       at 8,986.2 feet; 24.5-degree slope; 138.7-degree aspect (southeast)
   * - Geographic setting
     - Upper Muir Snowfield near Moon Rocks and Anvil Rock on the
       Paradise--Camp Muir route, Mount Rainier National Park, Washington

The target is close to Moon Rocks on the official Camp Muir route, rather than
at the lower ERA5 grid elevation. This is a useful high-alpine spring example:
the model follows whether a recent layer remains dry, becomes slush, or
refreezes as repeated melt-freeze cycles cross the snowfield.

.. figure:: ../_generated/examples/integration-consolidation-profile.png
   :alt: Consolidation profile generated by the consolidation integration test.
   :width: 100%

   Output from ``integration_test/run_consolidation.py`` using the checked-in
   five-day ERA5 fixture and live terrain at 46.82629, -121.72638.

With the public function defaults of 30 mm SWE and 20 cm depth, alternating
melt and freeze periods produce a visible sequence of settled slush and crust
layers around the 15 cm support line.

Mountaineering and ski context
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The `National Park Service Camp Muir route map
<https://www.nps.gov/mora/planyourvisit/upload/camp-muir-route-with-get-your-bearings-map-oct11.pdf>`_
locates Moon Rocks, Anvil Rock, the Muir Snowfield, and the surrounding
glaciers. The NPS `Muir Snowfield safety guidance
<https://www.nps.gov/mora/planyourvisit/hiking-safety.htm#CP_JUMP_7333337>`_
describes a permanent snow-and-ice field between 7,000 and 10,000 feet, warns
that weather and visibility can deteriorate rapidly, and notes glacier ice and
small but deep crevasses. The `Northwest Avalanche Center zone guide
<https://nwac.us/updated-mountain-weather-locations-names/>`_ places Mount
Rainier National Park in its **West South** zone.

This profile is a layer-consolidation illustration, not a glacier-travel,
crevasse, avalanche, or navigation assessment. NPS specifically warns against
descending the snowfield on skis or a snowboard in limited visibility.
