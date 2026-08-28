Chart commands
==============

All three chart commands read the same :doc:`../reference/weather-format` and
use the :doc:`../model`. Their difference is the snow-state question asked
after the effective-temperature series has been calculated.

.. list-table::
   :header-rows: 1
   :widths: 22 28 25 25

   * - Command
     - Best used for
     - Main model state
     - Default output
   * - :doc:`Powder preservation <pow-plot>`
     - A recent storm and powder preservation
     - Melt ETDH and overnight recovery
     - ``pow_forecast_chart.png``
   * - :doc:`Corn timing <corn-plot>`
     - Timing a daily spring softening window
     - Density-dependent ETDH range
     - ``corn_forecast_chart.png``
   * - :doc:`Consolidation profile <consolidation-plot>`
     - Following a new layer through repeated cycles
     - Dry, slush, and crust layers through depth
     - ``d_total_curve.png``

Shared command behavior
-----------------------

Every command accepts an input JSON path, ``--start``, ``--end``, ``--slope``,
``--aspect``, ``--elevation``, ``--no-show``, and ``--output``. ``--start`` and
``--end`` are day offsets from the first observation, not calendar dates.

The plot is shown interactively unless ``--no-show`` is supplied. Use
``--no-show`` in scripts, CI, and remote shells.

The charts are comparative decision tools. A useful practice is to render the
same weather file for several aspects or elevations, give every file a
descriptive ``--output`` name, and compare transition timing rather than rely
on a single line.

.. toctree::
   :maxdepth: 1

   pow-plot
   corn-plot
   consolidation-plot
